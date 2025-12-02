from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from main import run_agent
from collectors import get_all_sources

app = Flask(__name__)
CORS(app)

import re

def parse_response(raw_response):
    """
    Robust extraction of JSON from 'chatty' LLM responses.
    Finds the first '{' and the last '}' to extract the valid JSON object.
    """
    try:
        # 1. Try simple clean (remove markdown)
        clean_text = raw_response.replace("```json", "").replace("```", "").strip()
        
        # 2. Use Regex to find the main JSON block: { ... }
        match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        
        # 3. Fallback: If no brackets found, try parsing the whole thing
        return json.loads(clean_text)
        
    except Exception as e:
        print(f"❌ JSON Parse Error: {e}")
        print(f"📄 Raw Output was: {raw_response}")
        return {
            "verdict": "Unverified", 
            "explanation": "The AI provided an analysis but the format was unclear.",
            "mood": "spikey"
        }

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    claim = data.get("claim", "")
    image_url = data.get("imageUrl", None)
    print(f"🔮 Orb analyzing: {claim}")
    
    # Call the Agent
    raw_response = run_agent(claim)
    return jsonify(parse_response(raw_response))

@app.route("/feed", methods=["GET"])
def feed():
    """
    Fetches trending news and auto-verifies the top 2 items.
    """
    print("🛰️  Scanning global frequencies...")
    raw_sources = get_all_sources() 
    
    # Take only top 2 unique items to prevent Ollama timeout during demo
    # (Ensure collectors.py returns strings, or handle objects appropriately)
    sources = list(set(raw_sources))[:2]
    
    results = []
    
    for source in sources:
        # source might be "Headline - URL", so we just verify that text
        print(f"⚡ Verifying: {source[:30]}...")
        verdict_raw = run_agent(source)
        parsed = parse_response(verdict_raw)
        results.append({
            "claim": source,
            "verdict": parsed.get("verdict", "Unverified"),
            "mood": parsed.get("mood", "calm")
        })
        
    return jsonify(results)

if __name__ == "__main__":
    print("🚀 Yatharth Server Online at http://127.0.0.1:5000")
    app.run(port=5000, debug=True)