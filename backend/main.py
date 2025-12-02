import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from serpapi import GoogleSearch
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional

load_dotenv()

# --- 1. Define Tools ---
tavily_tool = TavilySearchResults(max_results=5)

def reverse_image_search(image_url: str):
    """
    Uses Google Lens (via SerpApi) to find the original context of an image.
    """
    if not image_url:
        return "No image provided."
    
    print(f"👁️  Scanning Image: {image_url}")
    try:
        params = {
            "api_key": os.getenv("SERPAPI_API_KEY"),
            "engine": "google_lens",
            "url": image_url
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Extract meaningful context
        visual_matches = results.get("visual_matches", [])[:5] # Get top 5
        knowledge_graph = results.get("knowledge_graph", {})
        
        summary = []
        if knowledge_graph.get("title"):
            summary.append(f"Subject Identified: {knowledge_graph.get('title')}")
            
        for match in visual_matches:
            title = match.get("title", "Unknown")
            source = match.get("source", "Unknown")
            link = match.get("link", "")
            summary.append(f"Found on {source}: '{title}'")
            
        if not summary:
            return "No exact visual matches found. This often indicates the image is unique, new, or AI-generated."
            
        return "\n".join(summary)
    except Exception as e:
        return f"Image Search Failed: {str(e)}"

# --- 2. Define LLM ---
llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"), 
    model_name="llama-3.1-8b-instant", 
    temperature=0.2
)

# --- 3. Define State ---
class AgentState(TypedDict):
    query: str
    image_url: Optional[str]
    research_data: str
    final_verdict: str

# --- 4. Define Nodes (WITH THE FIX) ---
def researcher_node(state: AgentState):
    query = state["query"]
    image_url = state.get("image_url")
    
    findings = []
    
    # 1. Image Research (ALWAYS RUN IF IMAGE EXISTS)
    if image_url:
        image_results = reverse_image_search(image_url)
        findings.append(f"IMAGE CONTEXT (Primary Evidence):\n{image_results}")
    
    # 2. Text Research (CONDITIONAL)
    # The Fix: If an image exists, and the user asks a generic question, SKIP text search.
    # This prevents the "Wipers Album" error.
    skip_text = False
    if image_url:
        generic_triggers = ["is this real", "is this fake", "real or fake", "verify", "check this", "true?", "real?"]
        # Check if the query is short and contains a generic trigger
        if len(query.split()) < 10 and any(trigger in query.lower() for trigger in generic_triggers):
            skip_text = True
            findings.append("TEXT SEARCH SKIPPED: Query is generic; verifying based on Image Context only.")

    if query and not skip_text:
        print(f"\n🔎 Researching Text: {query}")
        try:
            text_results = tavily_tool.invoke({"query": query})
            findings.append(f"TEXT EVIDENCE:\n{str(text_results)}")
        except:
            findings.append("Text search failed.")
            
    return {"research_data": "\n\n".join(findings)}

def synthesizer_node(state: AgentState):
    data = state["research_data"]
    query = state["query"]
    image_url = state.get("image_url")
    
    # We update the prompt to handle "No matches" correctly
    prompt = f"""
    You are an expert Multi-Modal Fact Checker.
    
    USER INPUT:
    - Claim: "{query}"
    - Image Analysis: {data}
    
    CRITICAL RULES:
    1. IF IMAGE IS PROVIDED: 
       - Ignore any text evidence about albums, songs, or dictionary definitions (e.g. "Wipers - Is This Real").
       - Focus ONLY on the "IMAGE CONTEXT".
       - If "IMAGE CONTEXT" says "No exact visual matches found", it means the image is likely AI-generated or Fake. Verdict: "Unverified" or "False".
       - If "IMAGE CONTEXT" lists stock photo sites (Freepik, Shutterstock) or AI art sites, Verdict: "False" (It is not a real event).
    
    2. IF NO IMAGE:
       - Verify the claim using the Text Evidence.

    Respond with this JSON structure:
    {{
        "verdict": "Verified", "False", "Misleading", or "Unverified",
        "explanation": "State clearly: 'This image appears to be...' (Cite the source found or lack of matches).",
        "mood": "calm" (if true), "spikey" (if false/fake), or "thinking" (if unsure)
    }}
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_verdict": response.content}

# --- 5. Build Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("researcher", researcher_node)
workflow.add_node("synthesizer", synthesizer_node)
workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "synthesizer")
workflow.add_edge("synthesizer", END)

app_graph = workflow.compile()

def run_agent(claim: str, image_url: str = None):
    result = app_graph.invoke({"query": claim, "image_url": image_url})
    return result["final_verdict"]