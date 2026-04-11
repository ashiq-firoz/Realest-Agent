from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PropertyRequest(BaseModel):
    query: str = Field(..., description="The user's query about real estate (e.g., 'Find duplex potential in Blacktown')")
    location: Optional[str] = Field(None, description="Specific suburb or area")

class ChatHistory(BaseModel):
    role: str
    content: str

class AgentChatRequest(BaseModel):
    message: str
    history: List[ChatHistory] = []
    location_context: Optional[Dict[str, Any]] = None

class PropertyDeal(BaseModel):
    address: str
    price: str
    rental_yield: float
    growth_probability: float
    feasibility_score: float
    notes: str

class PredictionResponse(BaseModel):
    suburb: str
    growth_forecast: str
    infrastructure_projects: List[str]
    investment_score: int
