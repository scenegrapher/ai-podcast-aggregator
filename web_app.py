from flask import Flask, render_template, jsonify
from openai import OpenAI
from app import fetch_rss_episodes, fetch_apple_podcasts
import os
from dotenv import load_dotenv
import logging
import sys

# Configure logging based on environment
if "--debug" in sys.argv:
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
    )
else:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Debug log to check API key
if not os.getenv("OPENAI_API_KEY"):
    logging.error("OpenAI API key not found!")
else:
    logging.debug("OpenAI API key loaded successfully")

app = Flask(__name__)


def process_episode_with_gpt(episode):
    """Process episode description with GPT-4 to extract key insights."""
    try:
        prompt = (
            "Please provide a brief summary and key insights from this "
            f"podcast episode: {episode['description']}"
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant that summarizes "
                    "podcast episodes.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error processing episode with GPT: {str(e)}")
        return "Unable to process with AI at this time."


@app.route("/")
def index():
    """Main page that displays all podcast episodes."""
    try:
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OpenAI API key not configured")

        # Fetch episodes from both sources
        logging.debug("Fetching RSS episodes...")
        rss_episodes = fetch_rss_episodes()
        logging.debug(f"Found {len(rss_episodes)} RSS episodes")

        logging.debug("Fetching Apple Podcasts episodes...")
        apple_episodes = fetch_apple_podcasts()
        logging.debug(f"Found {len(apple_episodes)} Apple Podcasts episodes")

        all_episodes = rss_episodes + apple_episodes
        logging.debug(f"Total episodes before deduplication: {len(all_episodes)}")

        # Remove duplicates
        unique_episodes = []
        seen = set()
        for ep in all_episodes:
            key = (ep["title"], ep["podcast_title"])
            if key not in seen:
                seen.add(key)
                logging.debug(f"Processing episode with GPT: {ep['title']}")
                ep["ai_summary"] = process_episode_with_gpt(ep)
                unique_episodes.append(ep)

        logging.debug(f"Total unique episodes after processing: {len(unique_episodes)}")
        return render_template("index.html", episodes=unique_episodes)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logging.error(error_msg)
        return render_template("error.html", error=error_msg)


@app.route("/api/episodes")
def get_episodes():
    """API endpoint to get all episodes in JSON format."""
    try:
        rss_episodes = fetch_rss_episodes()
        apple_episodes = fetch_apple_podcasts()
        all_episodes = rss_episodes + apple_episodes

        # Remove duplicates
        unique_episodes = []
        seen = set()
        for ep in all_episodes:
            key = (ep["title"], ep["podcast_title"])
            if key not in seen:
                seen.add(key)
                ep["ai_summary"] = process_episode_with_gpt(ep)
                unique_episodes.append(ep)

        return jsonify(unique_episodes)
    except Exception as e:
        logging.error(f"Error in API route: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    debug_mode = "--debug" in sys.argv
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
