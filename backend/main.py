import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import AgentChatRequest, PropertyRequest, PredictionResponse
from agent_engine import run_agent_query
from tools_realestate import analyze_suburb_growth, calculate_feasibility
import uvicorn

app = FastAPI(
    title="AU Real Estate Agent API",
    description="Backend for the AI-powered Australian Real Estate Agent."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Australian Real Estate Agent Backend is active."}

@app.post("/chat")
async def chat(request: AgentChatRequest):
    """
    Main chat endpoint to interact with the Real Estate Agent.
    """
    try:
        response = await run_agent_query(request.message)
        return {"reply": response}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-growth")
async def predict_growth(request: PropertyRequest):
    """
    Direct endpoint for suburb growth predictions.
    """
    if not request.location:
        raise HTTPException(status_code=400, detail="Location is required for predictions.")
    
    try:
        result = analyze_suburb_growth.run(request.location)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feasibility")
async def check_feasibility(site_area: float, zoning: str, price: float):
    """
    Direct endpoint for development feasibility checks.
    """
    try:
        result = calculate_feasibility.run(site_area=site_area, zoning=zoning, purchase_price=price)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
