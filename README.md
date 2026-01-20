# Trakt2Jelly

Trakt2Jelly is a synchronization tool designed to mirror your personal Trakt.tv lists to Jellyfin playlists. It ensures high accuracy by matching media using TMDB IDs and focuses exclusively on movies to prevent Jellyfin from automatically expanding collections into individual episodes.

## Features

* **Precise Matching**: Uses TMDB IDs to find the correct media in your Jellyfin library.
* **Movie-Only Filter**: Specifically filters for movies to maintain clean playlists.
* **State Management**: Tracks sync state and ID mappings in a local JSON file to reduce API calls and handle deleted playlists.
* **Service Mode**: Can run as a background service with a configurable sync interval.
* **Interactive Selection**: Includes a CLI tool to select which Trakt lists should be synchronized.

## Prerequisites

* Trakt.tv API credentials (Client ID and Access Token).
* Jellyfin API Key and User ID.
* Docker and Docker Compose installed.

## Setup

1. Create a `.env` file in the root directory with the following variables:

```env
TRAKT_CLIENT_ID=your_trakt_client_id
TRAKT_ACCESS_TOKEN=your_trakt_access_token
JELLYFIN_URL=[https://your-jellyfin-server.com](https://your-jellyfin-server.com)
JELLYFIN_API_KEY=your_jellyfin_api_key
JELLYFIN_USER_ID=your_jellyfin_user_id
SYNC_INTERVAL_MINS=60
```

2. Ensure `sync_state.json` and `sync.log` exist in the root directory or will be created by the service.

## Usage

### Docker Commands

Build the image:
```bash
docker compose build
```

Start the synchronization service in the background:
```bash
docker compose up -d
```

View the logs:
```bash
docker logs -f trakt2jelly
```

### Configuration

To select or update the lists you want to synchronize, run the interactive tool within the running container:

```bash
docker exec -it trakt2jelly python tools/select_lists.py
```

## How it works

1. **Initialization**: The script loads configuration from the `.env` file and the current sync state from `sync_state.json`.
2. **Playlist Selection**: It retrieves the list of Trakt slugs stored in the state file.
3. **Liveness Check**: For each list, it checks if a corresponding playlist already exists in Jellyfin.
4. **Syncing**: 
    * If the Trakt list has been updated or the Jellyfin playlist is missing, it fetches all items from Trakt.
    * It matches movies against the Jellyfin library via TMDB IDs.
    * It clears the existing Jellyfin playlist (if any) and adds the identified items.
5. **Interval**: If `SYNC_INTERVAL_MINS` is set, the script enters a loop and waits for the specified duration before starting the next cycle.

## Docker Compose Example

```yaml
services:
  trakt2jelly:
    build: .
    container_name: trakt2jelly
    env_file: .env
    restart: unless-stopped
    volumes:
      - ./sync_state.json:/app/sync_state.json
      - ./sync.log:/app/sync.log```
