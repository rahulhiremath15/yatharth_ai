import os
import time
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# 1. Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "yatharth-vault"
index = pc.Index(index_name)

# 2. Load LIGHTWEIGHT Embedding Model (384 Dimensions)
print("🧠 Loading Embedding Model (384 dims)...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text):
    return embedder.encode(text).tolist()

def check_vault(query, threshold=0.85):
    print(f"🧠 Checking Vault for: '{query}'...")
    try:
        vector = get_embedding(query)
        results = index.query(vector=vector, top_k=1, include_metadata=True)
        if results['matches']:
            match = results['matches'][0]
            if match['score'] >= threshold:
                print(f"✅ Found in Vault! (Similarity: {match['score']:.2f})")
                return match['metadata']
        return None
    except Exception as e:
        print(f"⚠️ Vault Error: {e}")
        return None

def save_to_vault(query, result_data):
    print(f"💾 Saving to Vault: '{query}'")
    try:
        vector = get_embedding(query)
        doc_id = str(hash(query))
        metadata = {
            "query": query,
            "verdict": result_data.get("verdict", "Unverified"),
            "explanation": result_data.get("explanation", ""),
            "mood": result_data.get("mood", "calm"),
            "timestamp": time.time()
        }
        index.upsert(vectors=[(doc_id, vector, metadata)])
    except Exception as e:
        print(f"⚠️ Save Failed: {e}")