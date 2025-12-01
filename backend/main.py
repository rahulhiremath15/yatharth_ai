import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from duckduckgo_search import DDGS
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict

# --- 1. Load Environment Variables ---
load_dotenv()  # This loads variables from the .env file

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    # Fallback or error if key is missing
    print("⚠️ WARNING: GROQ_API_KEY not found in .env file.")

# --- 2. Real Search Tool ---
def search_web(query: str):
    """Performs a real web search using DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region='wt-wt', safesearch='moderate', max_results=5))
            if not results:
                return "No results found."
            return str(results)
    except Exception as e:
        return f"Search failed: {str(e)}"

# --- 3. Define the LLM (Groq) ---
# Using Llama-3-8b for blazing fast speed
llm = ChatGroq(
    groq_api_key=api_key, 
    model_name="llama3-8b-8192", 
    temperature=0.2
)

# --- 4. Define State ---
class AgentState(TypedDict):
    query: str
    research_data: str
    final_verdict: str

# --- 5. Define Nodes ---
def researcher_node(state: AgentState):
    query = state["query"]
    print(f"\n🔎 Researching: {query}")
    results = search_web(query)
    return {"research_data": results}

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

# --- 6. Build Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("researcher", researcher_node)
workflow.add_node("synthesizer", synthesizer_node)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "synthesizer")
workflow.add_edge("synthesizer", END)

app_graph = workflow.compile()

# Function to be called by API
def run_agent(claim: str):
    result = app_graph.invoke({"query": claim})
    return result["final_verdict"]