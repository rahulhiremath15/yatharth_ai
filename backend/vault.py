import os
import time
import json
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Initialize Pinecone
# We expect PINECONE_API_KEY in environment variables
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "yatharth-vault"

# Connect to the index
# (Ensure you created the index 'yatharth-vault' in Pinecone console first!)
index = pc.Index(index_name)

# Load Embedding Model (Downloads once, runs locally)
# 'all-mpnet-base-v2' is the industry standard for semantic search speed/quality balance
print("🧠 Loading Embedding Model (This may take a moment)...")
# 'all-MiniLM-L6-v2' is 5x smaller (80MB)
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text):
    """Converts text into a list of 768 numbers."""
    return embedder.encode(text).tolist()

def check_vault(query, threshold=0.80):
    """
    Checks if a similar query exists in the Vault.
    Returns the cached result if similarity > threshold.
    """
    print(f"🧠 Checking Vault for: '{query}'...")
    try:
        vector = get_embedding(query)
        
        # Query Pinecone
        results = index.query(
            vector=vector,
            top_k=1,
            include_metadata=True
        )
        
        # Check if we have a match
        if results['matches']:
            match = results['matches'][0]
            score = match['score']
            if score >= threshold:
                print(f"✅ Found in Vault! (Similarity: {score:.2f})")
                return match['metadata'] # Returns dictionary with verdict, explanation, etc.
        
        print("❌ Not found in Vault.")
        return None
    except Exception as e:
        print(f"⚠️ Vault Error: {e}")
        return None

def save_to_vault(query, result_data):
    """
    Saves a new verification result to the Vault.
    """
    print(f"💾 Saving to Vault: '{query}'")
    try:
        vector = get_embedding(query)
        
        # Create a unique ID (hash of the query)
        doc_id = str(hash(query))
        
        # Prepare metadata (This is what we retrieve later)
        # Pinecone metadata values must be strings, numbers, booleans, or lists of strings
        metadata = {
            "query": query,
            "verdict": result_data.get("verdict", "Unverified"),
            "explanation": result_data.get("explanation", "No explanation cached."),
            "mood": result_data.get("mood", "calm"),
            "timestamp": time.time()
        }
        
        # Upsert (Update or Insert) to Pinecone
        index.upsert(vectors=[(doc_id, vector, metadata)])
        print("✅ Saved successfully.")
    except Exception as e:
        print(f"⚠️ Failed to save to Vault: {e}")