import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from InquirerPy import inquirer

# --- Paths ---
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
env_path = BASE_DIR / ".env"
state_path = DATA_DIR / "sync_state.json"

load_dotenv(dotenv_path=env_path)

TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
TRAKT_ACCESS_TOKEN = os.getenv("TRAKT_ACCESS_TOKEN")

def fetch_trakt_lists():
    url = "https://api.trakt.tv/users/me/lists"
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_CLIENT_ID,
        "Authorization": f"Bearer {TRAKT_ACCESS_TOKEN}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching lists: {e}")
        return []

def load_selected_from_state():
    if state_path.exists():
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("selected_slugs", [])
        except Exception: pass
    return []

def save_selected_to_state(selected_slugs):
    DATA_DIR.mkdir(exist_ok=True)
    state = {"lists": {}, "id_map": {}, "selected_slugs": []}
    if state_path.exists():
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except Exception: pass
    
    state["selected_slugs"] = selected_slugs
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)

def main():
    print("Loading playlists from Trakt...")
    lists = fetch_trakt_lists()
    if not lists: return

    current_selection = load_selected_from_state()

    choices = [
        {
            "name": f"{l['name']} ({l['ids']['slug']}) - {l.get('item_count', 0)} items", 
            "value": l['ids']['slug'],
            "enabled": l['ids']['slug'] in current_selection
        }
        for l in lists
    ]

    selected_slugs = inquirer.checkbox(
        message="Select playlists to sync:",
        choices=choices,
        pointer=">",
        enabled_symbol="[x] ",
        disabled_symbol="[ ] ",
        instruction="(Space: Toggle, Enter: Confirm)"
    ).execute()

    if selected_slugs is not None:
        save_selected_to_state(selected_slugs)
        print(f"Selection saved to {state_path}")

if __name__ == "__main__":
    main()