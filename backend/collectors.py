import os
import requests
from dotenv import load_dotenv

load_dotenv()

# --- Load API Keys ---
# (Only keeping the ones we might use or are safe to leave null)
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# -----------------------------------------------------
# 📰 1. NewsAPI — fetch latest headlines
# -----------------------------------------------------
def fetch_news_headlines(query="misinformation", page_size=2):
    if not NEWS_API_KEY:
        return []
    url = f"https://newsapi.org/v2/everything"
    params = {"q": query, "pageSize": page_size, "apiKey": NEWS_API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return [f"{a['title']} - {a['url']}" for a in data.get("articles", [])]
    except Exception as e:
        print(f"NewsAPI Error: {e}")
    return []

# -----------------------------------------------------
# 🎥 2. YouTube Data API — fetch recent videos
# -----------------------------------------------------
def fetch_youtube_videos(query="breaking news", max_results=2):
    if not YOUTUBE_API_KEY:
        return []
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return [f"{v['snippet']['title']} - https://youtube.com/watch?v={v['id']['videoId']}" 
                    for v in data.get("items", [])]
    except Exception as e:
        print(f"YouTube Error: {e}")
    return []

# -----------------------------------------------------
# 🌍 6. Combined Fetcher — dynamic all-sources
# -----------------------------------------------------
def get_all_sources():
    results = []
    print("\n🔎 Collecting data from multiple sources...")
    
    # Try to fetch real news
    results += fetch_news_headlines()
    results += fetch_youtube_videos()

    # Fallback if no keys are present or calls fail
    if not results:
        results = [
            "Global internet traffic slows down as AI agents take over.",
            "Scientists discover new bacteria that eats plastic in the ocean.",
            "Breaking: Hackathon team builds entire AI infrastructure in 24 hours."
        ]
        
    print(f"✅ Collected {len(results)} items.")
    return results

if __name__ == "__main__":
    for item in get_all_sources():
        print("-", item)