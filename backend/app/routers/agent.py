from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.chat import AgentChat, ChatMessage
from app.services.agent_service import agent_service
from app.services.document_service import document_service

router = APIRouter()

@router.post("/chat")
async def process_chat(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start or continue a chat session."""
    chat_id = payload.get("chat_id")
    message = payload.get("message")

    if not message:
        raise HTTPException(status_code=400, detail="Message is required.")

    if chat_id:
        # Fetch existing chat
        result = await db.execute(select(AgentChat).where(AgentChat.id == chat_id, AgentChat.user_id == current_user.id).options(selectinload(AgentChat.messages)))
        chat = result.scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found.")
    else:
        # Create new chat
        title = message[:50] + "..." if len(message) > 50 else message
        chat = AgentChat(user_id=current_user.id, title=title)
        db.add(chat)
        await db.commit()
        await db.refresh(chat)

    # Store user message
    user_msg = ChatMessage(chat_id=chat.id, role="user", content=message)
    db.add(user_msg)
    await db.commit()

    # Reconstruct history for Gemini
    history = []
    # Fetch all messages ordered by created_at
    result = await db.execute(select(ChatMessage).where(ChatMessage.chat_id == chat.id).order_by(ChatMessage.created_at.asc()))
    messages = result.scalars().all()
    
    for msg in messages[:-1]: # exclude the current user message which is passed directly
        if msg.role in ["user", "model"]:
            history.append({"role": msg.role, "parts": [{"text": msg.content}]})

    try:
        response_text = await agent_service.chat(message, history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    # Store assistant message
    assistant_msg = ChatMessage(chat_id=chat.id, role="model", content=response_text)
    db.add(assistant_msg)
    await db.commit()

    return {"chat_id": chat.id, "response": response_text}

@router.get("/chats")
async def list_chats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(AgentChat).where(AgentChat.user_id == current_user.id).order_by(AgentChat.updated_at.desc()))
    return result.scalars().all()

@router.get("/chats/{chat_id}")
async def get_chat_history(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(AgentChat).where(AgentChat.id == chat_id, AgentChat.user_id == current_user.id).options(selectinload(AgentChat.messages)))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found.")
    return {"chat": chat, "messages": chat.messages}

@router.post("/upload")
async def upload_document(
    chat_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Extracts text from uploaded file and injects it into the chat context as a system/user context message."""
    content = await file.read()
    extracted_text = document_service.extract_text(file.filename, content)

    if not extracted_text or "Unsupported" in extracted_text:
         raise HTTPException(status_code=400, detail="Could not extract text from file.")
    
    # Store the extracted text as a context message in the chat
    context_msg = f"--- UPLOADED DOCUMENT: {file.filename} ---\n{extracted_text}\n--- END DOCUMENT ---"
    
    # Save as a user message so the model sees it
    msg = ChatMessage(chat_id=chat_id, role="user", content=context_msg)
    db.add(msg)
    await db.commit()

    return {"detail": "Document uploaded and context injected.", "chat_id": chat_id}

@router.post("/report")
async def generate_chat_report(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates a comprehensive report based on chat history and extracted data."""
    chat_id = payload.get("chat_id")
    report_type = payload.get("report_type", "Comprehensive Analysis")
    
    if not chat_id:
        raise HTTPException(status_code=400, detail="chat_id is required.")

    result = await db.execute(select(AgentChat).where(AgentChat.id == chat_id, AgentChat.user_id == current_user.id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found.")

    # Reconstruct history to ask the agent to generate a report
    history = []
    messages_result = await db.execute(select(ChatMessage).where(ChatMessage.chat_id == chat.id).order_by(ChatMessage.created_at.asc()))
    for msg in messages_result.scalars().all():
        if msg.role in ["user", "model"]:
            history.append({"role": msg.role, "parts": [{"text": msg.content}]})

    prompt = f"Based on the conversation history above, please generate a structured {report_type} Report in Markdown format. Make sure to combine all property data, historical data, and uploaded context we discussed. Cite the underlying Realty In AU data sources."
    
    try:
        report_text = await agent_service.chat(prompt, history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")

    # Store report as assistant message
    assistant_msg = ChatMessage(chat_id=chat.id, role="model", content=report_text)
    db.add(assistant_msg)
    await db.commit()

    return {"chat_id": chat.id, "report_content": report_text}
