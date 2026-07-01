# plex-mcp

A comprehensive [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for [Plex Media Server](https://www.plex.tv).

Exposes **38 tools** covering movies, TV shows, music, playlists, playback control, and library management — all accessible from any MCP-compatible AI client.

**Transport:** stdio (default) · SSE · streamable-http  
**Protocol:** MCP 2024-11-05  
**Auth:** credentials loaded from `.env` via python-dotenv

---

## Features

| Category | Tools |
|---|---|
| 🎬 Movies | Search, details, recent, unwatched, mark watched/unwatched, rate |
| 📺 TV Shows | Search, details, seasons, episodes, mark episode watched, rate |
| 🎵 Music | Search artists/albums/tracks, artist details, album tracklist, recently added |
| 📋 Playlists | List, view items, create, add/remove items, delete |
| ▶️ Playback | Active sessions, clients, play, pause, resume, stop, seek, volume, skip |
| 📚 Library | List libraries, stats, refresh, On Deck, recently added |

---

## Requirements

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`
- A running Plex Media Server with network access

---

## Installation

```bash
git clone https://github.com/lordraw77/plex-mcp.git
cd plex-mcp

# create virtual environment and install
uv sync

# or with pip
pip install -e .
```

---

## Configuration

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

```env
# Plex server connection
PLEX_SERVER_URL=http://192.168.1.100:32400
PLEX_TOKEN=your_plex_token_here
```

**How to find your Plex token:**  
Sign in at plex.tv → open any media item → click the `···` menu → "Get Info" → "View XML" → look for `X-Plex-Token` in the URL.

---

## Usage

### Run the MCP server

```bash
# stdio (default — for Claude Desktop / MCP clients that spawn the process)
uv run plex-mcp

# SSE — HTTP server on port 8000
MCP_TRANSPORT=sse uv run plex-mcp

# streamable-http — stateless HTTP on port 8000
MCP_TRANSPORT=streamable-http uv run plex-mcp
```

---

## Docker

The image is published on Docker Hub: [`lordraw77/plex-mcp`](https://hub.docker.com/r/lordraw77/plex-mcp)

### stdio transport (default)

The server speaks JSON-RPC 2.0 over stdin/stdout. The `-i` flag is required to keep stdin open.

```bash
docker run --rm -i \
  -e PLEX_SERVER_URL=http://192.168.1.100:32400 \
  -e PLEX_TOKEN=your_token_here \
  lordraw77/plex-mcp:latest
```

### SSE transport (HTTP)

Set `MCP_TRANSPORT=sse` to start an HTTP server. The SSE endpoint is exposed on port 8000.

```bash
docker run --rm \
  -e PLEX_SERVER_URL=http://192.168.1.100:32400 \
  -e PLEX_TOKEN=your_token_here \
  -e MCP_TRANSPORT=sse \
  -p 8000:8000 \
  lordraw77/plex-mcp:latest
```

Connect your MCP client to `http://localhost:8000/sse`.

### streamable-http transport

```bash
docker run --rm \
  -e PLEX_SERVER_URL=http://192.168.1.100:32400 \
  -e PLEX_TOKEN=your_token_here \
  -e MCP_TRANSPORT=streamable-http \
  -p 8000:8000 \
  lordraw77/plex-mcp:latest
```

Connect your MCP client to `http://localhost:8000/mcp`.

### Use with Claude Desktop (stdio via Docker)

```json
{
  "mcpServers": {
    "plex": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "PLEX_SERVER_URL=http://192.168.1.100:32400",
        "-e", "PLEX_TOKEN=your_token_here",
        "lordraw77/plex-mcp:latest"
      ]
    }
  }
}
```

### Use with Claude Desktop (SSE — long-running container)

Start the container once:

```bash
docker run -d --name plex-mcp \
  -e PLEX_SERVER_URL=http://192.168.1.100:32400 \
  -e PLEX_TOKEN=your_token_here \
  -e MCP_TRANSPORT=sse \
  -p 8000:8000 \
  lordraw77/plex-mcp:latest
```

Then add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "plex": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

### Docker Compose

**stdio** (`docker-compose.stdio.yml`) — one-shot, used by MCP clients that spawn the process:

```bash
PLEX_SERVER_URL=http://192.168.1.100:32400 PLEX_TOKEN=your_token \
  docker compose -f docker-compose.stdio.yml run --rm plex-mcp
```

**SSE** (`docker-compose.sse.yml`) — long-running HTTP server, starts automatically on reboot:

```bash
# copy and fill in your values
cp .env.example .env

docker compose -f docker-compose.sse.yml up -d
```

The SSE endpoint will be available at `http://localhost:8000/sse`.  
Override the port: `MCP_PORT=9000 docker compose -f docker-compose.sse.yml up -d`

To use `streamable-http` instead of `sse` with the same compose file:

```bash
MCP_TRANSPORT=streamable-http docker compose -f docker-compose.sse.yml up -d
# endpoint: http://localhost:8000/mcp
```

### Build locally

```bash
make build          # build image
make release        # build + push to Docker Hub
make run            # stdio transport
make run-sse        # SSE transport on port 8000
make run-http       # streamable-http transport on port 8000
make test           # run test suite
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `PLEX_SERVER_URL` | — | Base URL of your Plex server |
| `PLEX_TOKEN` | — | Your Plex authentication token |
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio`, `sse`, or `streamable-http` |
| `MCP_HOST` | `0.0.0.0` | Bind address (SSE / streamable-http only) |
| `MCP_PORT` | `8000` | Bind port (SSE / streamable-http only) |

---

### Use with Claude Desktop

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "plex": {
      "command": "uv",
      "args": ["--directory", "/path/to/plex-mcp", "run", "plex-mcp"],
      "env": {
        "PLEX_SERVER_URL": "http://192.168.1.100:32400",
        "PLEX_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Use with the included AI agent

See [`../plex_agent.py`](../plex_agent.py) — an interactive CLI agent powered by NVIDIA NIM that uses this MCP server.

```bash
cd ..
cp .env.example .env   # fill in PLEX_* and NVIDIA_* values
python plex_agent.py
```

---

## Tool Reference

### Movies

#### `search_movies`
Search for movies in the Plex library.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | string | `""` | Title substring |
| `genre` | string | `""` | Filter by genre (e.g. "Action") |
| `year` | integer | `null` | Filter by release year |
| `director` | string | `""` | Filter by director name |
| `actor` | string | `""` | Filter by actor/cast member |
| `unwatched_only` | boolean | `false` | Return only unwatched |
| `limit` | integer | `20` | Max results |

#### `get_movie_details`
Get full details for a movie: cast, crew, ratings, summary.

| Parameter | Type | Description |
|---|---|---|
| `title` | string | Movie title (partial match) |

#### `get_movie_genres`
Get genres for a movie.

| Parameter | Type | Description |
|---|---|---|
| `title` | string | Movie title |

#### `get_recent_movies`
Get recently added movies.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | `10` | Max results |

#### `get_unwatched_movies`
Get unwatched movies in the library.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | `20` | Max results |

#### `mark_movie_watched`
Mark a movie as watched.

| Parameter | Type | Description |
|---|---|---|
| `title` | string | Movie title |

#### `mark_movie_unwatched`
Mark a movie as unwatched.

| Parameter | Type | Description |
|---|---|---|
| `title` | string | Movie title |

#### `rate_movie`
Rate a movie on a 1–10 scale.

| Parameter | Type | Description |
|---|---|---|
| `title` | string | Movie title |
| `rating` | float | Rating 1.0–10.0 |

---

### TV Shows

#### `search_shows`
Search for TV shows.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | string | `""` | Title substring |
| `genre` | string | `""` | Filter by genre |
| `actor` | string | `""` | Filter by actor |
| `year` | integer | `null` | Filter by first air year |
| `unwatched_only` | boolean | `false` | Shows with unwatched episodes |
| `limit` | integer | `20` | Max results |

#### `get_show_details`
Get full details for a TV show.

| Parameter | Type | Description |
|---|---|---|
| `title` | string | Show title |

#### `get_show_seasons`
List all seasons of a show with episode counts.

| Parameter | Type | Description |
|---|---|---|
| `title` | string | Show title |

#### `get_season_episodes`
List all episodes of a season.

| Parameter | Type | Description |
|---|---|---|
| `show_title` | string | Show title |
| `season_number` | integer | Season number |

#### `get_recent_episodes`
Get recently added TV episodes.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | `10` | Max results |

#### `mark_episode_watched`
Mark a specific episode as watched.

| Parameter | Type | Description |
|---|---|---|
| `show_title` | string | Show title |
| `season_number` | integer | Season number |
| `episode_number` | integer | Episode number |

#### `rate_show`
Rate a TV show on a 1–10 scale.

| Parameter | Type | Description |
|---|---|---|
| `title` | string | Show title |
| `rating` | float | Rating 1.0–10.0 |

---

### Music

#### `search_music`
Search for artists, albums, or tracks. At least one parameter required.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `artist` | string | `""` | Filter by artist name |
| `album` | string | `""` | Filter by album title |
| `track` | string | `""` | Filter by track title |
| `limit` | integer | `20` | Max results |

#### `get_artist_details`
Get artist info and album list.

| Parameter | Type | Description |
|---|---|---|
| `artist_name` | string | Artist name |

#### `get_album_details`
Get album info and full tracklist.

| Parameter | Type | Description |
|---|---|---|
| `artist_name` | string | Artist name |
| `album_title` | string | Album title |

#### `get_recent_music`
Get recently added music albums or tracks.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | `10` | Max results |

---

### Playlists

#### `list_playlists`
List all playlists.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `playlist_type` | string | `""` | `"video"`, `"audio"`, `"photo"`, or empty for all |

#### `get_playlist_items`
View all items in a playlist.

| Parameter | Type | Description |
|---|---|---|
| `playlist_name` | string | Exact playlist name |

#### `create_playlist`
Create a new playlist with specified media items.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | string | — | Playlist name |
| `media_titles` | array[string] | — | List of titles to include |
| `media_type` | string | `"movie"` | `"movie"`, `"show"`, or `"music"` |

#### `add_to_playlist`
Add a media item to an existing playlist.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `playlist_name` | string | — | Exact playlist name |
| `media_title` | string | — | Title to add |
| `media_type` | string | `"movie"` | `"movie"`, `"show"`, or `"music"` |

#### `remove_from_playlist`
Remove a media item from a playlist.

| Parameter | Type | Description |
|---|---|---|
| `playlist_name` | string | Exact playlist name |
| `media_title` | string | Title to remove (partial match) |

#### `delete_playlist`
Permanently delete a playlist.

| Parameter | Type | Description |
|---|---|---|
| `playlist_name` | string | Exact playlist name |

---

### Playback Control

> Playback control requires Plex clients to be on the same local network as the server and to support remote control (most official Plex apps do).

#### `get_active_sessions`
Get all currently active streaming sessions with progress info.

#### `get_clients`
List available Plex clients (players) on the network.

#### `play_media`
Play a media item on a specific client.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `client_name` | string | — | Client name from `get_clients` |
| `title` | string | — | Media title |
| `media_type` | string | `"movie"` | `"movie"`, `"show"`, or `"music"` |

#### `pause_playback`
Pause playback on a client.

| Parameter | Type | Description |
|---|---|---|
| `client_name` | string | Client name |

#### `resume_playback`
Resume paused playback on a client.

| Parameter | Type | Description |
|---|---|---|
| `client_name` | string | Client name |

#### `stop_playback`
Stop playback on a client.

| Parameter | Type | Description |
|---|---|---|
| `client_name` | string | Client name |

#### `seek_to`
Seek to a specific position in the currently playing media.

| Parameter | Type | Description |
|---|---|---|
| `client_name` | string | Client name |
| `position_ms` | integer | Position in milliseconds (e.g. `90000` = 1:30) |

#### `set_volume`
Set the volume on a client.

| Parameter | Type | Description |
|---|---|---|
| `client_name` | string | Client name |
| `level` | integer | Volume 0–100 |

#### `skip_next`
Skip to the next item in the queue.

| Parameter | Type | Description |
|---|---|---|
| `client_name` | string | Client name |

---

### Library Management

#### `list_libraries`
List all Plex library sections with type info.

#### `get_library_stats`
Get statistics for a specific library (item count, last scan, etc.).

| Parameter | Type | Description |
|---|---|---|
| `library_name` | string | Library name from `list_libraries` |

#### `refresh_library`
Trigger a metadata refresh/scan on a library. Runs in background on the Plex server.

| Parameter | Type | Description |
|---|---|---|
| `library_name` | string | Library name from `list_libraries` |

#### `get_on_deck`
Get On Deck items — media in progress or up next.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | `10` | Max results |

#### `get_recently_added`
Get recently added items across all (or filtered) libraries.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | `15` | Max results |
| `media_type` | string | `""` | `"movie"`, `"show"`, `"artist"`, or empty for all |

---

## Development

```bash
# install with dev dependencies
uv sync --extra dev

# run tests
uv run pytest

# run tests with coverage
uv run pytest --tb=short -v
```

---

## License

MIT
