
"""
using Gemini 3.1 Flash Lite and groq llama 3.1 instant with rate limit can help generate tasks

"""


# -*- coding: utf-8 -*-
"""
FastAPI wrapper for the Meta-Controller Agentic Architecture.
Based on 11_meta_controller.py

Run with:
    uvicorn app:app --reload
"""

import os
from typing import Optional, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# LangChain LLM providers
from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter
from langchain_anthropic import ChatAnthropic
from langchain_xai import ChatXAI
from langchain_mistralai import ChatMistralAI
from langchain_deepseek import ChatDeepSeek
from langchain_groq import ChatGroq

# LangChain / LangGraph components
from langchain_tavily import TavilySearch
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField


# ---------------------------------------------------------------------------
# FastAPI App Setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Meta-Controller Agent API",
    description="""
## Meta-Controller Multi-Agent System

This API exposes the **Meta-Controller** agentic architecture as a REST endpoint.

### How it works
1. You supply your LLM **provider credentials** and a **user request** in the request body.
2. The **Meta-Controller** (powered by your chosen LLM) analyses the incoming request and routes it to the best specialist:
   - **Generalist** — casual conversation & simple questions
   - **Researcher** — recent events & web-search-backed answers (requires a Tavily key)
   - **Coder** — Python code generation
3. The chosen specialist executes the task and returns the result.

### Smart Provider Selection
The API now automatically detects the best provider based on your `model_name`:
- Models with `gpt` -> `openai`
- Models with `llama` -> `groq`
- Models with `mistral` -> `mistral`
- Models with `claude` -> `anthropic`
- Models with `grok` -> `xai`
- Models with `deepseek` -> `deepseek`
- **Default** -> `openrouter` (if no keyword matches or provider is unknown)

### Supported providers (Manual selection)
| `model_provider` value | Notes |
|---|---|
| `openrouter` | (Default Fallback) |
| `openai` | Required for `gpt` models |
| `anthropic` | Required for `claude` models |
| `xai` | Required for `grok` models |
| `mistral` | Required for `mistral` / `pixtral` models |
| `deepseek` | Required for `deepseek` models |
| `groq` | Required for `llama` models |
    """,
   
)

# Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response Pydantic Models
# ---------------------------------------------------------------------------

class ProviderInput(BaseModel):
    """Input model that mirrors the `provider_input` dict in 11_meta_controller.py."""

    model_provider: Literal["openrouter", "openai", "anthropic", "xai", "mistral", "deepseek", "groq"] = Field(
        ...,
        description="The LLM provider to use.",
        examples=["openrouter"],
    )
    model_name: str = Field(
        ...,
        description="The specific model name/ID for the chosen provider.",
        examples=["stepfun/step-3.5-flash:free"],
    )
    model_api_key: str = Field(
        ...,
        description="API key for the chosen LLM provider.",
        examples=["sk-or-v1-xxxxxxxxxxxxxxxx"],
    )
    TAVILY_API_KEY: str = Field(
        ...,
        description="Tavily Search API key — required for the Researcher specialist.",
        examples=["tvly-xxxxxxxxxxxxxxxx"],
    )
    user_request: str = Field(
        ...,
        description="The user query / task to route through the Meta-Controller.",
        examples=["Write a Python function that calculates the nth Fibonacci number."],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "model_provider": "openrouter",
                    "model_name": "stepfun/step-3.5-flash:free",
                    "model_api_key": "sk-or-v1-your-key-here",
                    "TAVILY_API_KEY": "tvly-your-key-here",
                    "user_request": "Write a Python function to check if a number is prime.",
                }
            ]
        }
    }


class AgentResponse(BaseModel):
    """Response returned by the Meta-Controller agent."""

    routed_to: str = Field(description="The specialist agent that handled the request.")
    reasoning: str = Field(description="The Meta-Controller's reasoning for the routing decision.")
    reply: str = Field(description="The final response generated by the specialist agent.")


# ---------------------------------------------------------------------------
# LLM Factory
# ---------------------------------------------------------------------------

def build_llm(provider: str, model_name: str, api_key: str):
    """
    Instantiate the correct LangChain chat model based on `provider`.
    The API key is injected via the corresponding environment variable so
    that LangChain's standard credential lookup works for every provider.

    Includes auto-detection logic:
    - Keywords in model_name override the provider (e.g., 'gpt' -> 'openai').
    - If the provider is not in the recognized labs, it defaults to 'openrouter'.
    """
    # 1. Normalize name and provider
    provider = provider.lower()
    model_lower = model_name.lower()

    # 2. Smart Provider Detection based on keywords
    if "gpt" in model_lower:
        provider = "openai"
    elif "llama" in model_lower:
        provider = "groq"
    elif "mistral" in model_lower:
        provider = "mistral"
    elif "claude" in model_lower:
        provider = "anthropic"
    elif "grok" in model_lower:
        provider = "xai"
    elif "deepseek" in model_lower:
        provider = "deepseek"

    # 3. Default to openrouter if not in the official lab list
    official_labs = ["openai", "anthropic", "xai", "mistral", "deepseek", "groq"]
    if provider not in official_labs:
        provider = "openrouter"

    # 4. Environment variable mapping
    env_key_map = {
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "xai": "XAI_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "groq": "GROQ_API_KEY",
    }

    # Set the API key in the environment for LangChain to pick up
    os.environ[env_key_map[provider]] = api_key

    # 5. Return the corresponding LangChain chat model
    if provider == "openrouter":
        return ChatOpenRouter(model=model_name, temperature=0)
    elif provider == "openai":
        return ChatOpenAI(model=model_name, temperature=0)
    elif provider == "anthropic":
        return ChatAnthropic(model=model_name, temperature=0)
    elif provider == "xai":
        return ChatXAI(model=model_name, temperature=0)
    elif provider == "mistral":
        return ChatMistralAI(model=model_name, temperature=0)
    elif provider == "deepseek":
        return ChatDeepSeek(model=model_name, temperature=0)
    elif provider == "groq":
        return ChatGroq(model=model_name, temperature=0)


# ---------------------------------------------------------------------------
# LangGraph State
# ---------------------------------------------------------------------------

class MetaAgentState(TypedDict):
    user_request: str
    next_agent_to_call: Optional[str]
    routing_reasoning: str
    generation: str


# ---------------------------------------------------------------------------
# Routing Decision Model (used by the Meta-Controller with structured output)
# ---------------------------------------------------------------------------

class ControllerDecision(PydanticBaseModel):
    next_agent: str = PydanticField(
        description="The name of the specialist agent to call next. Must be one of ['Generalist', 'Researcher', 'Coder']."
    )
    reasoning: str = PydanticField(
        description="A brief reason for choosing the next agent."
    )


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------

def build_meta_agent(llm, tavily_api_key: str):
    """
    Build and compile the Meta-Controller LangGraph for a single request.
    A fresh graph is created per request so that the LLM/key swap is clean.
    """

    # Set Tavily key for this request
    os.environ["TAVILY_API_KEY"] = tavily_api_key
    search_tool = TavilySearch(max_results=3)

    # --- Specialist node factory ---
    def create_specialist_node(persona: str, tools: list = None):
        system_prompt = (
            f"You are a specialist agent with the following persona: {persona}. "
            "Respond directly and concisely to the user's request based on your role."
        )
        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", "{user_request}")]
        )
        chain = prompt | (llm.bind_tools(tools) if tools else llm)

        def specialist_node(state: MetaAgentState):
            result = chain.invoke({"user_request": state["user_request"]})
            return {"generation": result.content}

        return specialist_node

    # Specialist nodes
    generalist_node = create_specialist_node(
        "You are a friendly and helpful generalist AI assistant. "
        "You handle casual conversation and simple questions."
    )
    research_agent_node = create_specialist_node(
        "You are an expert researcher. You must use your search tool to find "
        "information to answer the user's question.",
        tools=[search_tool],
    )
    coding_agent_node = create_specialist_node(
        "You are an expert Python programmer. Your task is to write clean, "
        "efficient Python code based on the user's request. Provide only the code, "
        "wrapped in markdown code blocks, with minimal explanation."
    )

    # --- Meta-Controller node ---
    def meta_controller_node(state: MetaAgentState):
        specialists = {
            "Generalist": "Handles casual conversation, greetings, and simple questions.",
            "Researcher": "Answers questions about recent events, complex topics, or anything requiring up-to-date information from the web.",
            "Coder": "Writes Python code based on a user's specification.",
        }
        specialist_descriptions = "\n".join(
            [f"- {name}: {desc}" for name, desc in specialists.items()]
        )

        prompt = ChatPromptTemplate.from_template(
            f"""You are the meta-controller for a multi-agent AI system. Your job is to analyze the user's request and route it to the most appropriate specialist agent.

Here are the available specialists:
{specialist_descriptions}

Analyze the following user request and choose the best specialist to handle it. Provide your decision in the required format.

User Request: "{{user_request}}\""""
        )

        controller_llm = llm.with_structured_output(ControllerDecision)
        chain = prompt | controller_llm

        decision: ControllerDecision = chain.invoke({"user_request": state["user_request"]})

        return {
            "next_agent_to_call": decision.next_agent,
            "routing_reasoning": decision.reasoning,
        }

    # --- Routing function ---
    def route_to_specialist(state: MetaAgentState) -> str:
        return state["next_agent_to_call"]

    # --- Build graph ---
    workflow = StateGraph(MetaAgentState)
    workflow.add_node("meta_controller", meta_controller_node)
    workflow.add_node("Generalist", generalist_node)
    workflow.add_node("Researcher", research_agent_node)
    workflow.add_node("Coder", coding_agent_node)

    workflow.set_entry_point("meta_controller")

    workflow.add_conditional_edges(
        "meta_controller",
        route_to_specialist,
        {
            "Generalist": "Generalist",
            "Researcher": "Researcher",
            "Coder": "Coder",
        },
    )

    workflow.add_edge("Generalist", END)
    workflow.add_edge("Researcher", END)
    workflow.add_edge("Coder", END)

    return workflow.compile()


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"], summary="Health check")
def root():
    """Simple health-check endpoint."""
    return {"status": "ok", "message": "Meta-Controller Agent API is running. Visit /docs for Swagger UI."}


@app.post(
    "/run-agent",
    response_model=AgentResponse,
    tags=["Agent"],
    summary="Run the Meta-Controller agent",
    response_description="The agent's routing decision and final reply.",
)
def run_agent(provider_input: ProviderInput):
    """
    Run the **Meta-Controller** multi-agent pipeline.

    Supply your provider credentials and a user query.
    The system will:
    1. Build a fresh LLM client with your credentials.
    2. Route your query to the correct specialist (Generalist / Researcher / Coder).
    3. Return the specialist's response along with the routing metadata.

    **Example providers:** `openrouter`, `openai`, `anthropic`, `groq`, `mistral`, `deepseek`, `xai`
    """
    try:
        # Build the LLM from the supplied provider input
        llm = build_llm(
            provider=provider_input.model_provider,
            model_name=provider_input.model_name,
            api_key=provider_input.model_api_key,
        )

        # Build and run the Meta-Controller graph
        meta_agent = build_meta_agent(llm, provider_input.TAVILY_API_KEY)

        result = meta_agent.invoke(
            {
                "user_request": provider_input.user_request,
                "next_agent_to_call": None,
                "routing_reasoning": "",
                "generation": "",
            }
        )

        return AgentResponse(
            routed_to=result.get("next_agent_to_call", "Unknown"),
            reasoning=result.get("routing_reasoning", ""),
            reply=result.get("generation", ""),
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
