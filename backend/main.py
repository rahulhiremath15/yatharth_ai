import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Load Env
load_dotenv()

# --- THE FIX: Use Tavily instead of DuckDuckGo ---
# Tavily API Key must be set in Render Environment Variables
search_tool = TavilySearchResults(max_results=5)

llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"), 
    model_name="llama-3.1-8b-instant", 
    temperature=0.2
)

class AgentState(TypedDict):
    query: str
    research_data: str
    final_verdict: str

def researcher_node(state: AgentState):
    query = state["query"]
    print(f"\n🔎 Researching: {query}")
    try:
        # Tavily search
        results = search_tool.invoke({"query": query})
        return {"research_data": str(results)}
    except Exception as e:
        print(f"Search Error: {e}")
        return {"research_data": f"Search failed: {str(e)}"}

def synthesizer_node(state: AgentState):
    data = state["research_data"]
    query = state["query"]
    
    prompt = f"""
    You are an expert fact-checker. Analyze this claim based *only* on the search results provided below.
    
    Claim: "{query}"
    Search Results: "{data}"
    
    Respond with a raw JSON object (no markdown, no backticks) with this structure:
    {{
        "verdict": "Verified", "False", or "Unverified",
        "explanation": "A short, clear reason citing the sources.",
        "mood": "calm" (if true/neutral) or "spikey" (if false/alarmist)
    }}
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_verdict": response.content}

workflow = StateGraph(AgentState)
workflow.add_node("researcher", researcher_node)
workflow.add_node("synthesizer", synthesizer_node)
workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "synthesizer")
workflow.add_edge("synthesizer", END)

app_graph = workflow.compile()

def run_agent(claim: str):
    result = app_graph.invoke({"query": claim})
    return result["final_verdict"]