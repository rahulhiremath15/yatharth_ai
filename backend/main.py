import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from serpapi import GoogleSearch
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from vault import check_vault, save_to_vault

load_dotenv()

# --- 1. Tools ---
tavily_tool = TavilySearchResults(max_results=5)

def reverse_image_search(image_url: str):
    if not image_url: return "No image."
    print(f"👁️  Scanning Image: {image_url}")
    try:
        params = {
            "api_key": os.getenv("SERPAPI_API_KEY"),
            "engine": "google_lens",
            "url": image_url
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        visual_matches = results.get("visual_matches", [])[:5]
        knowledge_graph = results.get("knowledge_graph", {})
        
        summary = []
        if knowledge_graph.get("title"):
            summary.append(f"Subject: {knowledge_graph.get('title')}")
        for match in visual_matches:
            summary.append(f"Found on {match.get('source')}: '{match.get('title')}'")
            
        return "\n".join(summary) if summary else "No exact visual matches found (Likely AI/Unique)."
    except Exception as e:
        return f"Image Search Error: {str(e)}"

# --- 2. LLM ---
llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"), 
    model_name="llama-3.1-8b-instant", 
    temperature=0.2
)

# --- 3. State ---
class AgentState(TypedDict):
    query: str
    image_url: Optional[str]
    research_data: str
    final_verdict: str

# --- 4. Nodes (STRICT TEXT BLOCKER) ---
def researcher_node(state: AgentState):
    query = state["query"]
    image_url = state.get("image_url")
    findings = []
    
    # A. Image Search
    if image_url:
        findings.append(f"IMAGE CONTEXT:\n{reverse_image_search(image_url)}")
    
    # B. Text Search (BLOCK GENERIC QUERIES)
    run_text_search = True
    if image_url:
        # Block generic questions completely
        triggers = ["is this real", "real?", "fake", "verify", "check", "truth", "what is this", "true?"]
        clean_q = query.lower()
        if len(clean_q.split()) < 8 or any(t in clean_q for t in triggers):
            run_text_search = False
            findings.append("NOTE: Text search skipped to prevent false positives on generic queries.")

    if run_text_search:
        print(f"\n🔎 Researching Text: {query}")
        try:
            res = tavily_tool.invoke({"query": query})
            findings.append(f"TEXT EVIDENCE:\n{str(res)}")
        except:
            findings.append("Text search failed.")
            
    return {"research_data": "\n\n".join(findings)}

def synthesizer_node(state: AgentState):
    prompt = f"""
    You are an expert Fact Checker.
    
    USER CLAIM: "{state['query']}"
    EVIDENCE: {state['research_data']}
    
    RULES:
    1. IF IMAGE IS PRESENT: 
       - IGNORE text evidence about "Albums", "Songs" or "Definitions" (e.g. Wipers Album).
       - Look ONLY at Image Context.
       - If Image Context says "No exact visual matches" or "Stock Photo" -> Verdict: UNVERIFIED or FALSE.
       
    2. IF NO IMAGE: Verify text claim normally.
    
    Respond JSON: {{ "verdict": "...", "explanation": "...", "mood": "calm/spikey" }}
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_verdict": response.content}

# --- 5. Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("researcher", researcher_node)
workflow.add_node("synthesizer", synthesizer_node)
workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "synthesizer")
workflow.add_edge("synthesizer", END)
app_graph = workflow.compile()

# --- 6. Execution ---
def run_agent(claim: str, image_url: str = None):
    # Check Vault (Text Only)
    if not image_url:
        cached = check_vault(claim)
        if cached:
            return json.dumps({
                "verdict": cached["verdict"], 
                "explanation": cached["explanation"], 
                "mood": cached["mood"], 
                "source": "Vault Memory"
            })

    res = app_graph.invoke({"query": claim, "image_url": image_url})
    final = res["final_verdict"]
    
    # Save to Vault (Text Only)
    if not image_url:
        try:
            save_to_vault(claim, json.loads(final))
        except: pass
        
    return final