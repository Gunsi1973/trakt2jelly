# Trakt2Jelly

Trakt2Jelly is a synchronization tool designed to mirror your personal Trakt.tv lists to Jellyfin playlists. It ensures high accuracy by matching media using TMDB IDs and focuses exclusively on movies.

## Features

* **Precise Matching**: Uses TMDB IDs to find the correct media in your Jellyfin library.
* **Movie-Only Filter**: Specifically filters for movies to maintain clean playlists.
* **State Management**: Tracks sync state and ID mappings in a `data/sync_state.json` file.
* **Service Mode**: Runs as a background service with a configurable sync interval.
* **Interactive Selection**: Includes a CLI tool to select which Trakt lists should be synchronized.

## Setup

1. Create a `.env` file in the root directory:

```env
TRAKT_CLIENT_ID=your_trakt_client_id
TRAKT_ACCESS_TOKEN=your_trakt_access_token
JELLYFIN_URL=[https://your-jellyfin-server.com](https://your-jellyfin-server.com)
JELLYFIN_API_KEY=your_jellyfin_api_key
JELLYFIN_USER_ID=your_jellyfin_user_id
SYNC_INTERVAL_MINS=60
```

2. Build and start the container:

```bash
docker compose build
docker compose up -d
```

## Usage

### Configuration

To select the lists for synchronization, run the interactive tool:

```bash
docker exec -it trakt2jelly python tools/select_lists.py
```

### Logs

Monitor the synchronization process:

```bash
docker logs -f trakt2jelly
```

## File Structure

* `main.py`: Main service logic.
* `data/`: Directory for persistent data (auto-created).
    * `sync_state.json`: Stores sync timestamps and ID cache.
    * `sync.log`: Detailed application logs.
* `tools/select_lists.py`: CLI configuration utility.

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