import os
import json
import logging
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# --- Initialization ---
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "sync.log"
STATE_FILE = BASE_DIR / "sync_state.json"

TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
TRAKT_ACCESS_TOKEN = os.getenv("TRAKT_ACCESS_TOKEN")
JF_URL = os.getenv("JELLYFIN_URL", "").rstrip('/')
JF_API_KEY = os.getenv("JELLYFIN_API_KEY")
JF_USER_ID = os.getenv("JELLYFIN_USER_ID")

SYNC_ONLY = os.getenv("SYNC_ONLY_LISTS", "").strip()
SYNC_LISTS = [s.strip() for s in SYNC_ONLY.split(",")] if SYNC_ONLY else []

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Trakt2Jelly")

HEADERS_TRAKT = {
    "Content-Type": "application/json",
    "trakt-api-version": "2",
    "trakt-api-key": TRAKT_CLIENT_ID,
    "Authorization": f"Bearer {TRAKT_ACCESS_TOKEN}"
}

# --- Functions ---

def load_state():
    default_state = {"lists": {}, "id_map": {}}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                content = json.load(f)
                if isinstance(content, dict) and "lists" in content:
                    return content
        except Exception as e:
            logger.error(f"State load error: {e}")
    return default_state

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)

def get_jellyfin_playlist_id(slug):
    """
    Finds a playlist by its exact name (which we set to the slug).
    """
    url = f"{JF_URL}/Items?Recursive=true&IncludeItemTypes=Playlist&api_key={JF_API_KEY}"
    try:
        res = requests.get(url).json()
        for item in res.get('Items', []):
            if item['Name'] == slug:
                return item['Id']
    except Exception as e:
        logger.error(f"Error checking JF playlists: {e}")
    return None

def find_jellyfin_item(tmdb_id, title, id_map):
    tmdb_str = str(tmdb_id)
    if tmdb_str in id_map:
        return id_map[tmdb_str]

    # Recursive search with TMDB filter
    url = f"{JF_URL}/Items?Recursive=true&IncludeItemTypes=Movie,Series&Fields=ProviderIds&api_key={JF_API_KEY}"
    try:
        response = requests.get(url, timeout=15)
        for item in response.json().get('Items', []):
            if item.get('ProviderIds', {}).get('Tmdb') == tmdb_str:
                id_map[tmdb_str] = item['Id']
                return item['Id']
    except Exception:
        pass
    return None

def clear_jellyfin_playlist(playlist_id):
    url = f"{JF_URL}/Playlists/{playlist_id}/Items?api_key={JF_API_KEY}"
    res = requests.get(url).json()
    item_ids = [i['Id'] for i in res.get('Items', [])]
    if item_ids:
        del_url = f"{JF_URL}/Playlists/{playlist_id}/Items?EntryIds={','.join(item_ids)}&api_key={JF_API_KEY}"
        requests.delete(del_url)

def main():
    logger.info("Starting Sync Process...")
    state = load_state()
    
    try:
        lists_url = "https://api.trakt.tv/users/me/lists"
        trakt_lists = requests.get(lists_url, headers=HEADERS_TRAKT).json()
    except Exception as e:
        logger.error(f"Trakt API Error: {e}")
        return

    if SYNC_LISTS:
        trakt_lists = [l for l in trakt_lists if l['ids']['slug'] in SYNC_LISTS]

    for t_list in trakt_lists:
        slug = t_list['ids']['slug']
        display_name = t_list['name']
        updated_at = t_list.get('updated_at')
        
        # Explicitly check if the playlist exists in JF
        jf_id = get_jellyfin_playlist_id(slug)

        # Skip if timestamp matches AND it exists in JF
        if state["lists"].get(slug) == updated_at and jf_id:
            logger.info(f"List '{display_name}': Up to date.")
            continue

        logger.info(f"List '{display_name}': Syncing items...")

        # Fetch Items
        items_url = f"https://api.trakt.tv/users/me/lists/{slug}/items"
        trakt_items = requests.get(items_url, headers=HEADERS_TRAKT).json()
        
        jf_item_ids = []
        for item in trakt_items:
            media = item.get(item['type'])
            if not media: continue
            
            tmdb_id = media.get('ids', {}).get('tmdb')
            if tmdb_id:
                matched_id = find_jellyfin_item(tmdb_id, media.get('title'), state["id_map"])
                if matched_id: jf_item_ids.append(matched_id)

        if jf_item_ids:
            jf_item_ids = list(dict.fromkeys(jf_item_ids))
            
            if jf_id:
                clear_jellyfin_playlist(jf_id)
                pl_id = jf_id
            else:
                create_url = f"{JF_URL}/Playlists?Name={slug}&UserId={JF_USER_ID}&api_key={JF_API_KEY}"
                pl_id = requests.post(create_url).json()['Id']

            update_url = f"{JF_URL}/Playlists/{pl_id}/Items?Ids={','.join(jf_item_ids)}&UserId={JF_USER_ID}&api_key={JF_API_KEY}"
            res = requests.post(update_url)
            
            if res.status_code in [200, 204]:
                logger.info(f"  Done: {len(jf_item_ids)} items -> '{slug}'.")
                state["lists"][slug] = updated_at
                save_state(state)

    logger.info("Sync Finished.")

if __name__ == "__main__":
    main()