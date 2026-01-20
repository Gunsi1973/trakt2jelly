import os
import requests
from dotenv import load_dotenv, set_key

# Calculate path to .env in the parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configuration
CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
CLIENT_SECRET = os.getenv("TRAKT_CLIENT_SECRET")
# Standard redirect for CLI applications
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

def run_oauth_flow():
    # 1. Generate the authorization URL
    auth_url = (
        f"https://trakt.tv/oauth/authorize"
        f"?common=1"
        f"&response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
    )
    
    print("1. Open this URL in your browser:")
    print(f"\n{auth_url}\n")
    print("2. Login to Trakt and click 'Authorize'.")
    print("3. You will see a PIN code on the screen.")
    
    pin = input("\nEnter the PIN code from Trakt: ").strip()

    # 2. Exchange the PIN for tokens
    token_url = "https://api.trakt.tv/oauth/token"
    payload = {
        "code": pin,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    response = requests.post(token_url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        
        # Save tokens to the .env file
        set_key(".env", "TRAKT_ACCESS_TOKEN", access_token)
        set_key(".env", "TRAKT_REFRESH_TOKEN", refresh_token)
        
        print("\n✅ Success! Tokens saved to .env file.")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Please add TRAKT_CLIENT_ID and TRAKT_CLIENT_SECRET to your .env file.")
    else:
        run_oauth_flow()