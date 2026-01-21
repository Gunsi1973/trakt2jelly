# Trakt2Jelly

Trakt2Jelly is a synchronization tool designed to mirror your personal Trakt.tv lists to Jellyfin playlists. It ensures high accuracy by matching media using TMDB IDs and focuses exclusively on movies.

## Features

* **Precise Matching**: Uses TMDB IDs to find the correct media in your Jellyfin library.
* **Movie-Only Filter**: Specifically filters for movies to maintain clean playlists.
* **State Management**: Tracks sync state and ID mappings in a `data/sync_state.json` file.
* **Service Mode**: Runs as a background service with a configurable sync interval.
* **Interactive Selection**: Includes a CLI tool to select which Trakt lists should be synchronized.

## Setup

### 1. Environment Configuration
Create a `.env` file in the root directory and fill in your credentials:

```env
TRAKT_CLIENT_ID=your_id
TRAKT_CLIENT_SECRET=your_secret
JELLYFIN_URL=[https://your-jellyfin-server.com](https://your-jellyfin-server.com)
JELLYFIN_API_KEY=your_api_key
JELLYFIN_USER_ID=your_user_id
SYNC_INTERVAL_MINS=60
```

### 2. Trakt Authentication
Run the authentication tool to generate your access tokens:
```bash
python tools/auth_trakt.py
```
Follow the instructions in your browser and paste the PIN.

### 3. Verify Connections
Check if the Jellyfin connection is working:
```bash
python tools/verify_jf.py
```

### 4. Build and Start Docker
```bash
docker compose build
docker compose up -d
```

## Usage

### Select Playlists
Run the interactive selection tool within the running container to choose your playlists:
```bash
docker exec -it trakt2jelly python tools/select_lists.py
```

### Monitor Sync
Check the logs to see the synchronization progress:
```bash
docker logs -f trakt2jelly
```

## File Structure

* `main.py`: Main service logic and loop.
* `data/`: Persistent storage (mapped volume).
    * `sync_state.json`: ID cache and sync timestamps.
    * `sync.log`: Application logs.
* `tools/`: Helper scripts for setup and configuration.
    * `auth_trakt.py`: OAuth flow for Trakt.
    * `verify_jf.py`: Connection test for Jellyfin.
    * `select_lists.py`: Interactive playlist selector.

## Docker Compse Example

```yaml
services:
  trakt2jelly:
    build: .
    container_name: trakt2jelly
    env_file: .env
    restart: unless-stopped
    volumes:
      - ./data:/app/data
```