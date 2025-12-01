# collectors.py
import os
import requests
from dotenv import load_dotenv
import praw  # Reddit client

load_dotenv()

# --- Load API Keys ---
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET = os.getenv("REDDIT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "CrisisConnect/1.0")
INSTAGRAM_RAPIDAPI_KEY = os.getenv("INSTAGRAM_RAPIDAPI_KEY")
INSTAGRAM_RAPIDAPI_HOST = os.getenv("INSTAGRAM_RAPIDAPI_HOST", "instagram-data1.p.rapidapi.com")
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")

# -----------------------------------------------------
# 📰 1. NewsAPI — fetch latest headlines
# -----------------------------------------------------
def fetch_news_headlines(query="fake news", page_size=5):
    url = f"https://newsapi.org/v2/everything"
    params = {"q": query, "pageSize": page_size, "apiKey": NEWS_API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return [f"{a['title']} - {a['url']}" for a in data.get("articles", [])]
    except Exception as e:
        print("Error fetching news:", e)
        return []

# -----------------------------------------------------
# 🎥 2. YouTube Data API — fetch recent videos
# -----------------------------------------------------
def fetch_youtube_videos(query="breaking news", max_results=5):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return [f"{v['snippet']['title']} - https://youtube.com/watch?v={v['id']['videoId']}" 
                for v in data.get("items", [])]
    except Exception as e:
        print("Error fetching YouTube:", e)
        return []

# -----------------------------------------------------
# 🦋 3. Reddit API — trending subreddit posts
# -----------------------------------------------------
def fetch_reddit_posts(subreddit_name="news", limit=5):
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        subreddit = reddit.subreddit(subreddit_name)
        return [f"{post.title} (r/{subreddit_name})" for post in subreddit.hot(limit=limit)]
    except Exception as e:
        print("Error fetching Reddit:", e)
        return []

# -----------------------------------------------------
# 📸 4. Instagram (RapidAPI free)
# -----------------------------------------------------
def fetch_instagram_hashtag(tag="breakingnews", count=5):
    url = f"https://{INSTAGRAM_RAPIDAPI_HOST}/hashtag"
    headers = {
        "X-RapidAPI-Key": INSTAGRAM_RAPIDAPI_KEY,
        "X-RapidAPI-Host": INSTAGRAM_RAPIDAPI_HOST
    }
    params = {"hashtag": tag, "count": str(count)}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return [f"{p.get('username', '')}: {p.get('caption', '')}" for p in data.get("posts", [])[:count]]
    except Exception as e:
        print("Error fetching Instagram:", e)
        return []

# -----------------------------------------------------
# 📘 5. Facebook (Graph API, once Meta unlocks)
# -----------------------------------------------------
def fetch_facebook_page_posts(page_id="bbcnews", limit=5):
    if not FACEBOOK_ACCESS_TOKEN:
        return ["Facebook token not available yet."]
    url = f"https://graph.facebook.com/v20.0/{page_id}/posts"
    params = {
        "fields": "id,message,permalink_url,created_time",
        "limit": limit,
        "access_token": FACEBOOK_ACCESS_TOKEN
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return [f"{p.get('message', '')} - {p.get('permalink_url', '')}" for p in data.get("data", [])]
    except Exception as e:
        print("Error fetching Facebook:", e)
        return []

# -----------------------------------------------------
# 🌍 6. Combined Fetcher — dynamic all-sources
# -----------------------------------------------------
def get_all_sources():
    results = []
    print("\n🔎 Collecting data from multiple sources...")
    
    # --- Active Sources ---
    results += fetch_news_headlines()   # Works (if API key is valid)
    results += fetch_youtube_videos()   # Works (if API key is valid)
    
    # --- Disabled/Broken Sources (Commented out for Demo) ---
    # results += fetch_reddit_posts()
    # results += fetch_instagram_hashtag()
    # results += fetch_facebook_page_posts()
    
    # If everything fails, add a fallback item so the feed isn't empty
    if not results:
        results = ["Breaking News: Local hackathon team invents AI that sees the future."]
        
    print(f"✅ Collected {len(results)} items from active sources.")
    return results


if __name__ == "__main__":
    for item in get_all_sources():
        print("-", item)
