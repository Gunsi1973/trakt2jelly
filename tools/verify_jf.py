import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Calculate paths
BASE_DIR = Path(__file__).parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

JF_URL = os.getenv("JELLYFIN_URL", "").rstrip('/')
JF_API_KEY = os.getenv("JELLYFIN_API_KEY")

def verify_jellyfin():
    url = f"{JF_URL}/System/Info/Public"
    headers = {
        "X-Emby-Token": JF_API_KEY,
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Jellyfin connection successful!")
            print(f"Server Name: {data.get('ServerName')}")
            print(f"Version:     {data.get('Version')}")
        elif response.status_code == 401:
            print("Authentication failed: Invalid API Key.")
        else:
            print(f"Error: Status Code {response.status_code}")
            
    except Exception as e:
        print(f"Network Error: Unable to connect to {JF_URL}")
        print(f"Details: {e}")

if __name__ == "__main__":
    verify_jellyfin()