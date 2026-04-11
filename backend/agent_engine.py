import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from tools_realestate import search_properties, calculate_feasibility, analyze_suburb_growth, portfolio_advisor, analyze_document

load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# Defaulting to gemini-1.5-flash as the requested "model 3 flash preview" likely refers to the latest flash.
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-flash")

def get_real_estate_agent():
    """
    Initializes and returns the Real Estate Agent for Australian market.
    """
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2
    )

    tools = [
        search_properties, 
        calculate_feasibility, 
        analyze_suburb_growth, 
        portfolio_advisor,
        analyze_document
    ]

    system_message = (
        "You are 'Aussie Real Estate Agent AI', a premium proptech assistant for the Australian property market. "
        "Your goal is to provide high-value data insights on properties, suburbs, and development feasibility. "
        "\n\n"
        "Guidance:\n"
        "- Use property data tools to find on-market listings or suburb stats.\n"
        "- For feasibility requests, gather site area, zoning, and price to calculate duplex or subdivision potential.\n"
        "- Provide 'Rental Yield' estimates and 'Capital Growth' probabilities based on the data you find.\n"
        "- Always be professional and use Australian real estate terminology (e.g., 'suburb', 'strata', 'FSR', 'LVR').\n"
        "- If asked about the 'next hot suburb', use the growth analyzer tool to look for infrastructure and low vacancy rates.\n"
        "- IMPORTANT: When asked for a prediction based on an area, heavily incorporate current domestic and international news, economic reports, interest rates, and global trends that might have an impact on the real estate market in your reasoning.\n"
        "\n"
        "When responding, format your answer beautifully with markdown headers and bullet points."
    )

    agent = create_react_agent(llm, tools, prompt=system_message)
    return agent

async def run_agent_query(message: str, history=None):
    """
    Runner for the agent.
    """
    agent = get_real_estate_agent()
    
    # Simple history formatting for the agent if needed
    # (LangGraph react agent takes a list of messages)
    inputs = {"messages": [HumanMessage(content=message)]}
    
    result = await agent.ainvoke(inputs)
    return result["messages"][-1].content
