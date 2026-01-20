import os
from pathlib import Path
import requests
from dotenv import load_dotenv

# Path setup
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
TRAKT_ACCESS_TOKEN = os.getenv("TRAKT_ACCESS_TOKEN")

def list_playlists():
    url = "https://api.trakt.tv/users/me/lists"
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_CLIENT_ID,
        "Authorization": f"Bearer {TRAKT_ACCESS_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        playlists = response.json()
        print(f"\n{'Name':<30} | {'Slug (Use this for SYNC_ONLY_LISTS)':<30}")
        print("-" * 65)
        for pl in playlists:
            print(f"{pl['name']:<30} | {pl['ids']['slug']:<30}")
    else:
        print(f"❌ Failed to fetch lists: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    list_playlists()