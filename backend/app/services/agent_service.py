import json
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai

from app.config import settings
from app.services.realty_api import realty_api

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

# Define tool schemas for Gemini
REALTY_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "auto_complete",
                "description": "Resolves suburb names, cities, regions, and property addresses. Use whenever user references a location.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"]
                }
            },
            {
                "name": "properties_list",
                "description": "Search properties for buying/renting/investment. Example params: searchLocation, searchLocationSubtext, type, minimumPrice, maximumPrice, minimumBedrooms.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer"},
                        "pageSize": {"type": "integer"},
                        "sortType": {"type": "string", "description": "e.g., relevance, price-asc"},
                        "channel": {"type": "string", "description": "buy or rent"},
                        "searchLocation": {"type": "string"},
                        "searchLocationSubtext": {"type": "string"},
                        "type": {"type": "string"},
                        "minimumBedrooms": {"type": "integer"},
                        "minimumBathroom": {"type": "integer"},
                        "minimumPrice": {"type": "integer"},
                        "maximumPrice": {"type": "integer"},
                        "propertyTypes": {"type": "string", "description": "e.g., house,townhouse"}
                    }
                }
            },
            {
                "name": "properties_detail",
                "description": "Get full property information, features, listing metadata given a listingId.",
                "parameters": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"]
                }
            },
            {
                "name": "properties_v3_lookup",
                "description": "Historical sales information, off-market property data.",
                "parameters": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"]
                }
            },
            {
                "name": "schools_list",
                "description": "Get nearby schools based on latitude and longitude.",
                "parameters": {
                    "type": "object",
                    "properties": {"lat": {"type": "number"}, "lon": {"type": "number"}},
                    "required": ["lat", "lon"]
                }
            },
            {
                "name": "agency_list",
                "description": "Find and compare top agencies by suburb or performance.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer"},
                        "sort": {"type": "string"},
                        "channelType": {"type": "string"},
                        "locationType": {"type": "string"},
                        "suburb": {"type": "string"}
                    }
                }
            },
            {
                "name": "agency_detail",
                "description": "Agency profile and performance metrics.",
                "parameters": {
                    "type": "object",
                    "properties": {"agencyId": {"type": "string"}},
                    "required": ["agencyId"]
                }
            },
            {
                "name": "agency_get_listings",
                "description": "Properties currently listed by an agency.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer"},
                        "pageSize": {"type": "integer"},
                        "channel": {"type": "string"},
                        "agencyId": {"type": "string"}
                    },
                    "required": ["agencyId"]
                }
            },
            {
                "name": "agents_v2_list",
                "description": "Find top-performing agents.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "locationSlug": {"type": "string"},
                        "page": {"type": "integer"},
                        "pageSize": {"type": "integer"},
                        "sort": {"type": "string"},
                        "propertyType": {"type": "string"},
                        "timeFrame": {"type": "string"}
                    }
                }
            },
            {
                "name": "agents_detail",
                "description": "Agent profile, experience, and performance.",
                "parameters": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"]
                }
            },
            {
                "name": "agents_get_listings",
                "description": "Properties represented by specific agents.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer"},
                        "pageSize": {"type": "integer"},
                        "channel": {"type": "string"},
                        "linkedSalespeopleIds": {"type": "string"}
                    },
                    "required": ["linkedSalespeopleIds"]
                }
            }
        ]
    }
]

SYSTEM_INSTRUCTION = """
You are a highly capable Real Estate AI Agent for the Australian market.
You have access to a suite of Realty In AU tools. 
When a user asks for property recommendations, market analysis, or suburb insights, you should:
1. Use the 'auto_complete' tool to resolve locations first.
2. Use 'properties_list', 'agency_list', etc., to fetch relevant data.
3. Call details tools if specific property/agent details are needed.
4. Call 'schools_list' for family-oriented queries.
5. Synthesize the tool responses into a comprehensive, markdown-formatted report or chat response.
Always execute tools when data is needed. Do not invent data.
"""

class AgentService:
    def __init__(self):
        self.model = genai.GenerativeModel(
            # gemini-1.5-pro has been retired by Google; use a current model that
            # supports function calling (the report generator uses gemini-2.5-flash-lite).
            model_name="gemini-2.5-flash",
            tools=REALTY_TOOLS,
            system_instruction=SYSTEM_INSTRUCTION
        )

    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Maps tool name to RealtyApiService method."""
        try:
            if tool_name == "auto_complete":
                return await realty_api.auto_complete(args.get("query"))
            elif tool_name == "properties_list":
                return await realty_api.properties_list(args)
            elif tool_name == "properties_detail":
                return await realty_api.properties_detail(args.get("id"))
            elif tool_name == "properties_v3_lookup":
                return await realty_api.properties_v3_lookup(args.get("id"))
            elif tool_name == "schools_list":
                return await realty_api.schools_list(args.get("lat"), args.get("lon"))
            elif tool_name == "agency_list":
                return await realty_api.agency_list(args)
            elif tool_name == "agency_detail":
                return await realty_api.agency_detail(args.get("agencyId"))
            elif tool_name == "agency_get_listings":
                return await realty_api.agency_get_listings(args)
            elif tool_name == "agents_v2_list":
                return await realty_api.agents_v2_list(args)
            elif tool_name == "agents_detail":
                return await realty_api.agents_detail(args.get("id"))
            elif tool_name == "agents_get_listings":
                return await realty_api.agents_get_listings(args)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            return {"error": str(e)}

    async def chat(self, user_message: str, history: List[Dict[str, Any]]) -> str:
        """
        Executes a multi-turn chat with tool calling loop.
        history is a list of {"role": "user"|"model", "parts": [...]}
        """
        # Initialize chat session with history
        chat_session = self.model.start_chat(history=history)

        response = await chat_session.send_message_async(user_message)

        # Tool execution loop. Guard on .name so plain text responses (whose
        # function_call is an empty proto) don't get mistaken for a tool call.
        while response.parts and response.parts[0].function_call and response.parts[0].function_call.name:
            fc = response.parts[0].function_call
            tool_name = fc.name
            args = {k: v for k, v in fc.args.items()}
            logger.info(f"Executing tool: {tool_name} with args: {args}")

            tool_result = await self.execute_tool(tool_name, args)

            # Send the tool result back to Gemini. Use genai.protos (stable across
            # google-generativeai versions); content_types has no Part.from_function_response.
            response = await chat_session.send_message_async(
                genai.protos.Content(
                    parts=[
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tool_name,
                                response={"result": tool_result},
                            )
                        )
                    ]
                )
            )

        return response.text

agent_service = AgentService()
