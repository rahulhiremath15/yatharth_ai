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
    Returns a summary of where this image has appeared before.
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
        visual_matches = results.get("visual_matches", [])[:3]
        knowledge_graph = results.get("knowledge_graph", {})
        
        summary = []
        if knowledge_graph.get("title"):
            summary.append(f"Image Subject: {knowledge_graph.get('title')}")
            
        for match in visual_matches:
            title = match.get("title", "Unknown")
            source = match.get("source", "Unknown")
            date = match.get("date", "Unknown date") # SerpApi sometimes provides dates
            link = match.get("link", "")
            summary.append(f"Found on {source}: '{title}' ({link})")
            
        return "\n".join(summary) if summary else "No exact visual matches found."
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
    image_url: Optional[str] # <--- NEW FIELD
    research_data: str
    final_verdict: str

# --- 4. Define Nodes ---
def researcher_node(state: AgentState):
    query = state["query"]
    image_url = state.get("image_url")
    
    findings = []
    
    # A. Text Research (Tavily)
    if query:
        print(f"\n🔎 Researching Text: {query}")
        try:
            text_results = tavily_tool.invoke({"query": query})
            findings.append(f"TEXT EVIDENCE:\n{str(text_results)}")
        except:
            findings.append("Text search failed.")

    # B. Image Research (SerpApi)
    if image_url:
        image_results = reverse_image_search(image_url)
        findings.append(f"IMAGE CONTEXT:\n{image_results}")
        
    return {"research_data": "\n\n".join(findings)}

def synthesizer_node(state: AgentState):
    data = state["research_data"]
    query = state["query"]
    image_url = state.get("image_url")
    
    # We tweak the prompt to be stricter about Image Context
    prompt = f"""
    You are an expert Multi-Modal Fact Checker. 
    
    USER INPUT:
    - Text: "{query}"
    - Image Provided: {"Yes" if image_url else "No"}
    
    RESEARCH DATA:
    {data}
    
    CRITICAL INSTRUCTIONS:
    1. IF AN IMAGE IS PROVIDED: The text is a QUESTION about the image (e.g. "Is this real?" refers to the image). 
       - Do NOT verify the text string itself as a topic (e.g. do not talk about albums/movies named "Is this real").
       - Only look at the 'IMAGE CONTEXT' data.
       - If the 'IMAGE CONTEXT' says "No visual matches" or identifies it as "Stock Photo" or "AI Generated", the verdict should be "False" or "Unverified".
    
    2. IF NO IMAGE IS PROVIDED: Verify the text claim directly.
    
    Respond with a raw JSON object:
    {{
        "verdict": "Verified", "False", "Misleading", or "Unverified",
        "explanation": "Start by stating clearly what the image shows based on the research.",
        "mood": "calm" (true), "spikey" (false/misleading), or "thinking" (unclear)
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