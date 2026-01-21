import os
import json
import logging
import sys
import requests
import time
from pathlib import Path
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Initialization ---
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

LOG_FILE = DATA_DIR / "sync.log"
STATE_FILE = DATA_DIR / "sync_state.json"

TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
TRAKT_ACCESS_TOKEN = os.getenv("TRAKT_ACCESS_TOKEN")
JF_URL = os.getenv("JELLYFIN_URL", "").rstrip('/')
JF_API_KEY = os.getenv("JELLYFIN_API_KEY")
JF_USER_ID = os.getenv("JELLYFIN_USER_ID")

TIMEOUT = 15 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Trakt2Jelly")

# --- Session Management ---
def get_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))
    return session

session = get_session()

# --- State Management ---
def load_state():
    default_state = {"lists": {}, "id_map": {}, "selected_slugs": []}
    if not STATE_FILE.exists():
        return default_state
    
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            content = json.load(f)
            if not content: return default_state
            for key in default_state:
                if key not in content: content[key] = default_state[key]
            return content
    except (json.JSONDecodeError, Exception):
        logger.error("State file corrupted. Using defaults.")
        return default_state

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)

# --- Jellyfin Helper Functions ---
def get_jellyfin_playlist_id(slug):
    url = f"{JF_URL}/Items?Recursive=true&IncludeItemTypes=Playlist&api_key={JF_API_KEY}"
    try:
        res = session.get(url, timeout=TIMEOUT).json()
        for item in res.get('Items', []):
            if item['Name'] == slug: return item['Id']
    except Exception: pass
    return None

def find_jellyfin_item(tmdb_id, title, id_map):
    tmdb_str = str(tmdb_id)
    if tmdb_str in id_map: return id_map[tmdb_str]

    url = f"{JF_URL}/Items?Recursive=true&IncludeItemTypes=Movie&Fields=ProviderIds&api_key={JF_API_KEY}"
    try:
        response = session.get(url, timeout=TIMEOUT)
        for item in response.json().get('Items', []):
            if item.get('ProviderIds', {}).get('Tmdb') == tmdb_str:
                id_map[tmdb_str] = item['Id']
                return item['Id']
    except Exception: pass
    return None

def clear_jellyfin_playlist(playlist_id):
    url = f"{JF_URL}/Playlists/{playlist_id}/Items?api_key={JF_API_KEY}"
    try:
        res = session.get(url, timeout=TIMEOUT).json()
        item_ids = [i['Id'] for i in res.get('Items', [])]
        if item_ids:
            del_url = f"{JF_URL}/Playlists/{playlist_id}/Items?EntryIds={','.join(item_ids)}&api_key={JF_API_KEY}"
            session.delete(del_url, timeout=TIMEOUT)
    except Exception: pass

# --- Sync Logic ---
def main_sync():
    logger.info("Starting sync cycle...")
    state = load_state()
    selected_slugs = state.get("selected_slugs", [])

    if not selected_slugs:
        logger.warning("No playlists selected. Please run tools/select_lists.py.")
        return

    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": TRAKT_CLIENT_ID,
        "Authorization": f"Bearer {TRAKT_ACCESS_TOKEN}"
    }

    try:
        res = session.get("https://api.trakt.tv/users/me/lists", headers=headers, timeout=TIMEOUT)
        trakt_lists = [l for l in res.json() if l['ids']['slug'] in selected_slugs]
    except Exception as e:
        logger.error(f"Trakt API error: {e}")
        return

    for t_list in trakt_lists:
        slug, display_name, updated_at = t_list['ids']['slug'], t_list['name'], t_list.get('updated_at')
        jf_id = get_jellyfin_playlist_id(slug)

        if state["lists"].get(slug) == updated_at and jf_id:
            logger.info(f"List '{display_name}': Up to date.")
            continue

        logger.info(f"List '{display_name}': Synchronizing...")
        try:
            items = session.get(f"https://api.trakt.tv/users/me/lists/{slug}/items", headers=headers, timeout=TIMEOUT).json()
            jf_item_ids = []
            for item in items:
                if item['type'] != 'movie': continue
                media = item.get('movie')
                tmdb_id = media.get('ids', {}).get('tmdb')
                if tmdb_id:
                    matched_id = find_jellyfin_item(tmdb_id, media.get('title'), state["id_map"])
                    if matched_id: jf_item_ids.append(matched_id)

            if jf_item_ids:
                jf_item_ids = list(dict.fromkeys(jf_item_ids))
                if jf_id: clear_jellyfin_playlist(jf_id)
                else:
                    res = session.post(f"{JF_URL}/Playlists?Name={slug}&UserId={JF_USER_ID}&api_key={JF_API_KEY}", timeout=TIMEOUT)
                    jf_id = res.json()['Id']

                update_url = f"{JF_URL}/Playlists/{jf_id}/Items?Ids={','.join(jf_item_ids)}&UserId={JF_USER_ID}&api_key={JF_API_KEY}"
                if session.post(update_url, timeout=TIMEOUT).status_code in [200, 204]:
                    logger.info(f"  Success: {len(jf_item_ids)} movies -> '{slug}'.")
                    state["lists"][slug] = updated_at
                    save_state(state)
        except Exception as e:
            logger.error(f"Error processing {display_name}: {e}")
    logger.info("Sync cycle finished.")

if __name__ == "__main__":
    raw_interval = os.getenv("SYNC_INTERVAL_MINS", "").strip("'").strip('"').strip()
    
    if raw_interval.isdigit():
        mins = int(raw_interval)
        logger.info(f"Service mode: Syncing every {mins} minutes.")
        while True:
            try:
                main_sync()
            except Exception as e:
                logger.error(f"Loop error: {e}")
            time.sleep(mins * 60)
    else:
        logger.info("Single run mode.")
        main_sync()