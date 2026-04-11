import os
import requests
from langchain.tools import tool
from typing import List, Dict, Any

@tool
def search_properties(location: str, property_type: str = "house", min_price: int = None) -> str:
    """
    Search for properties in Australia using available listings data.
    Targets Domain.com.au and Realestate.com.au via search.
    """
    # In a real scenario, this would call an API or a specific scraper.
    # Here we use Tavily to simulate site-specific search.
    from langchain_community.tools.tavily_search import TavilySearchResults
    
    search = TavilySearchResults(max_results=5)
    query = f"site:realestate.com.au OR site:domain.com.au properties for sale in {location} {property_type}"
    if min_price:
        query += f" from {min_price}"
    
    results = search.run(query)
    return f"Search results for properties in {location}:\n{results}"

@tool
def calculate_feasibility(site_area: float, zoning: str, purchase_price: float) -> Dict[str, Any]:
    """
    Calculate development feasibility for a property in Australia.
    Considers subdivision potential, duplex feasibility, and build costs.
    """
    # Logic inspired by Feasly and Archistar
    potential = "High" if site_area > 600 and zoning.lower() in ["r2", "r3", "low density"] else "Low"
    
    # Simple AU development cost estimate (very rough)
    build_cost_per_sqm = 2500
    estimated_units = 2 if site_area > 600 else 1
    total_build_cost = estimated_units * 350000 # Rough duplex build cost
    
    # Expected end value (simulated)
    expected_value_per_unit = purchase_price * 0.8 # Assume each unit worth 80% of original land+house
    total_revenue = estimated_units * expected_value_per_unit
    
    profit = total_revenue - (purchase_price + total_build_cost)
    roi = (profit / (purchase_price + total_build_cost)) * 100
    
    return {
        "subdivision_potential": potential,
        "estimated_units": estimated_units,
        "total_build_cost": total_build_cost,
        "expected_total_revenue": total_revenue,
        "estimated_profit": profit,
        "roi_percentage": round(roi, 2),
        "zoning_notes": f"Zoning {zoning} analysis based on council standards."
    }

@tool
def analyze_suburb_growth(suburb: str) -> Dict[str, Any]:
    """
    Analyze growth potential for an Australian suburb based on ABS data trends, 
    infrastructure projects, and vacancy rates.
    """
    from langchain_community.tools.tavily_search import TavilySearchResults
    search = TavilySearchResults(max_results=3)
    
    infra_query = f"infrastructure projects and population growth in {suburb} Australia 2024 2025"
    vacancy_query = f"rental vacancy rate in {suburb} Australia"
    
    infra_data = search.run(infra_query)
    vacancy_data = search.run(vacancy_query)
    
    # Heuristic scoring
    score = 7 # Default
    if "new rail" in str(infra_data).lower() or "hospital" in str(infra_data).lower():
        score += 2
    if "low vacancy" in str(vacancy_data).lower():
        score += 1
        
    return {
        "suburb": suburb,
        "growth_score": min(score, 10),
        "infrastructure_highlights": infra_data,
        "market_sentiment": "Strong" if score > 7 else "Stable",
        "vacancy_insight": vacancy_data
    }

@tool
def portfolio_advisor(properties: List[Dict[str, Any]]) -> str:
    """
    Provide advice on an existing property portfolio.
    Analyze equity growth, loan-to-value (LVR) ratios, and refinance suggestions.
    """
    advice = []
    for prop in properties:
        addr = prop.get("address", "Unknown")
        current_val = prop.get("current_value", 0)
        loan_amt = prop.get("loan_amount", 0)
        
        lvr = (loan_amt / current_val) * 100 if current_val > 0 else 0
        if lvr < 60:
            advice.append(f" - {addr}: Low LVR ({round(lvr, 1)}%). Consider equity release for next investment.")
        elif lvr > 80:
            advice.append(f" - {addr}: High LVR ({round(lvr, 1)}%). Monitor market fluctuations closely.")
        else:
            advice.append(f" - {addr}: Stable LVR ({round(lvr, 1)}%). Good candidate for refinance if rates dropped.")
            
    return "\n".join(advice)

@tool
def analyze_document(doc_text: str, doc_type: str = "contract") -> str:
    """
    Analyze a real estate document (Contract of Sale, Building & Pest Report, Strata Report).
    Extracts key conditions, risks, and dates.
    """
    summary = f"Analysis of {doc_type}:\n"
    if "cooling off" in doc_text.lower():
        summary += "- Cooling off period identified.\n"
    if "asbestos" in doc_text.lower():
        summary += "- WARNING: Potential asbestos mentioned in report.\n"
    if "settlement" in doc_text.lower():
        summary += "- Settlement terms detected.\n"
        
    return summary if len(summary) > 20 else "Document read but no major red flags found."
