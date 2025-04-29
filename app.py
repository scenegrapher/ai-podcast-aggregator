import feedparser
import requests
import datetime
from datetime import date
import pandas as pd
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.blocking import BlockingScheduler
import logging
import json
from typing import List, Dict
import time

# Set up logging
logging.basicConfig(
    filename="podcast_agent.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load environment variables
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# RSS feeds for AI podcasts
RSS_FEEDS = [
    "https://feeds.buzzsprout.com/1705129.rss",  # AI Today
    "https://thisdayinai.libsyn.com/rss",  # This Day in AI
    "https://feeds.simplecast.com/w6CWz6jN",  # The AI Podcast (NVIDIA)
    "https://feeds.buzzsprout.com/2023029.rss",  # Eye on AI
    "https://feeds.feedburner.com/twit/mlat",  # TWIML AI Podcast
    "https://feeds.simplecast.com/2nGuZx3N",  # Lex Fridman Podcast
    "https://feeds.simplecast.com/4rOoJ6EJ",  # Machine Learning Guide
    "https://feeds.simplecast.com/7gYrJt2Y",  # Data Skeptic
    "https://feeds.redcircle.com/3b99e8d2-5b43-4d76-a502-18db2263c2e0",  # The Artificial Intelligence Show
    "https://feeds.simplecast.com/1T_k2WZo",  # AI in Business
    "https://feeds.buzzsprout.com/2040639.rss",  # AI Breakdown
    "https://api.pod.co/podcasts/gradient-dissent/feed",  # Gradient Dissent
    "https://feeds.buzzsprout.com/2084645.rss",  # The AI Daily Brief
]

# Trending keywords for AI content
TRENDING_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "generative ai",
    "llm",
    "large language model",
    "gpt",
    "chatgpt",
    "claude",
    "gemini",
    "ethics",
    "robotics",
    "healthcare",
    "marketing",
    "computer vision",
    "nlp",
    "natural language processing",
    "machine learning",
    "deep learning",
    "neural networks",
    "ai safety",
    "responsible ai",
    "ai regulation",
]


def fetch_rss_episodes() -> List[Dict]:
    episodes = []
    today = date.today().strftime("%Y-%m-%d")
    # For testing: today = "2025-04-01"  # Uncomment to test with past date

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                pub_date = entry.get("published", "")
                if today in pub_date:
                    description = entry.get("summary", "").lower()
                    if any(keyword in description for keyword in TRENDING_KEYWORDS):
                        episodes.append(
                            {
                                "title": entry.get("title"),
                                "description": entry.get("summary"),
                                "podcast_title": feed.feed.get("title", "Unknown"),
                                "audio_url": entry.get("link", ""),
                                "pub_date": today,
                                "link": entry.get("link", ""),
                                "source": "RSS",
                                "duration": entry.get("itunes_duration", "Unknown"),
                                "author": entry.get("author", "Unknown"),
                                "image_url": entry.get("image", {}).get("href", ""),
                            }
                        )
            logging.info(f"Fetched {len(episodes)} episodes from RSS feed: {feed_url}")
        except Exception as e:
            logging.error(f"Error parsing RSS feed {feed_url}: {str(e)}")
            time.sleep(1)
    return episodes


def fetch_apple_podcasts() -> List[Dict]:
    episodes = []
    today = date.today().strftime("%Y-%m-%d")
    # For testing: today = "2025-04-01"  # Uncomment to test with past date
    url = "https://itunes.apple.com/search"
    params = {
        "term": "artificial intelligence",
        "media": "podcast",
        "entity": "podcastEpisode",
        "limit": 50,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])

        for item in results:
            release_date = item.get("releaseDate", "")[:10]
            description = item.get("description", "").lower()
            if release_date == today and any(
                keyword in description for keyword in TRENDING_KEYWORDS
            ):
                episodes.append(
                    {
                        "title": item.get("trackName"),
                        "description": item.get("description"),
                        "podcast_title": item.get("collectionName"),
                        "audio_url": item.get("episodeUrl", ""),
                        "pub_date": release_date,
                        "link": item.get("trackViewUrl", ""),
                        "source": "Apple Podcasts",
                        "duration": item.get("trackTimeMillis", "Unknown"),
                        "author": item.get("artistName", "Unknown"),
                        "image_url": item.get("artworkUrl600", ""),
                    }
                )
        logging.info(f"Fetched {len(episodes)} episodes from Apple Podcasts")
        return episodes
    except Exception as e:
        logging.error(f"Error fetching from Apple Podcasts: {str(e)}")
        return []


def save_results(episodes: List[Dict]) -> None:
    if not episodes:
        logging.info("No AI podcasts published today.")
        return
    df = pd.DataFrame(episodes)
    csv_file = f"ai_podcasts_{date.today().strftime('%Y%m%d')}.csv"
    # For testing: csv_file = "ai_podcasts_test_20250401.csv"  # Uncomment for past date
    df.to_csv(csv_file, index=False)
    logging.info(f"Saved {len(episodes)} podcasts to {csv_file}")
    with open(f"ai_podcasts_{date.today().strftime('%Y%m%d')}.json", "w") as f:
        # For testing: with open("ai_podcasts_test_20250401.json", "w") as f:  # Uncomment
        json.dump(episodes, f, indent=2)
    logging.info(f"Saved {len(episodes)} podcasts to JSON")


def send_email(episodes: List[Dict]) -> None:
    try:
        msg = MIMEMultipart()
        msg["Subject"] = f"Daily AI Podcasts - {date.today()}"
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER
        html_content = "<html><body><h2>Today's AI Podcasts</h2>"
        if not episodes:
            html_content += "<p>No AI podcasts published today.</p>"
        else:
            for episode in episodes:
                html_content += f"""
                <div style='margin-bottom: 20px; padding: 10px; border: 1px solid #ddd;'>
                    <h3>{episode['title']}</h3>
                    <p><strong>Podcast:</strong> {episode['podcast_title']}</p>
                    <p><strong>Duration:</strong> {episode['duration']}</p>
                    <p><strong>Source:</strong> {episode['source']}</p>
                    <p><a href='{episode['link']}'>Listen Here</a></p>
                </div>
                """
        html_content += "</body></html>"
        msg.attach(MIMEText(html_content, "html"))
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(msg["From"], msg["To"], msg.as_string())
        logging.info("Email sent successfully")
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")


def main():
    try:
        print("Fetching RSS episodes...")
        rss_episodes = fetch_rss_episodes()
        print(f"Found {len(rss_episodes)} RSS episodes")
        print("Fetching Apple Podcasts...")
        apple_episodes = fetch_apple_podcasts()
        print(f"Found {len(apple_episodes)} Apple Podcasts episodes")
        all_episodes = rss_episodes + apple_episodes
        print(f"Total episodes before deduplication: {len(all_episodes)}")
        unique_episodes = []
        seen = set()
        for ep in all_episodes:
            key = (ep["title"], ep["podcast_title"])
            if key not in seen:
                seen.add(key)
                unique_episodes.append(ep)
        print(f"Total unique episodes: {len(unique_episodes)}")
        save_results(unique_episodes)
        send_email(unique_episodes)
    except Exception as e:
        logging.error(f"Main function error: {str(e)}")


if __name__ == "__main__":
    main()  # Run immediately for testing
    scheduler = BlockingScheduler()
    scheduler.add_job(main, "interval", days=1, start_date="2025-04-26 08:00:00")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler stopped")
