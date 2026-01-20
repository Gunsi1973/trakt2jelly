import os
import requests
from dotenv import load_dotenv

# Calculate path to .env in the parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration from .env
JF_URL = os.getenv("JELLYFIN_URL").rstrip('/')
JF_API_KEY = os.getenv("JELLYFIN_API_KEY")

def verify_jellyfin():
    # Endpoint to get public server info
    url = f"{JF_URL}/System/Info/Public"
    headers = {
        "X-Emby-Token": JF_API_KEY,
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Jellyfin Connection Successful!")
            print(f"Server Name: {data.get('ServerName')}")
            print(f"Version:     {data.get('Version')}")
        elif response.status_code == 401:
            print("❌ Authentication Failed: Invalid API Key.")
        else:
            print(f"❌ Connection Error: Status Code {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: Could not connect to {JF_URL}")
        print(f"Details: {e}")

if __name__ == "__main__":
    verify_jellyfin()