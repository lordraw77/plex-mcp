# plex-mcp

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that connects any MCP-compatible AI client (Claude, etc.) to your Plex Media Server.

Exposes **38 tools** across 6 categories — search, browse, control playback, manage playlists, and refresh libraries, all through natural language.

## Features

| Category | Capabilities |
|---|---|
| Movies | Search, details, recent, unwatched, mark watched, rate |
| TV Shows | Search, seasons, episodes, mark watched, rate |
| Music | Search artists/albums/tracks, details, recently added |
| Playlists | List, view, create, add/remove items, delete |
| Playback | Sessions, clients, play/pause/resume/stop, seek, volume, skip |
| Library | List, stats, refresh, On Deck, recently added |

## Quick Start — stdio (default)

```bash
docker run --rm -i \
  -e PLEX_SERVER_URL=http://192.168.1.100:32400 \
  -e PLEX_TOKEN=your_token_here \
  lordraw77/plex-mcp:latest
```

The `-i` flag keeps stdin open for JSON-RPC 2.0 communication.

## Quick Start — SSE (HTTP)

```bash
docker run --rm \
  -e PLEX_SERVER_URL=http://192.168.1.100:32400 \
  -e PLEX_TOKEN=your_token_here \
  -e MCP_TRANSPORT=sse \
  -p 8000:8000 \
  lordraw77/plex-mcp:latest
```

Connect your MCP client to `http://localhost:8000/sse`.

## Use with Claude Desktop

**stdio (ephemeral container per request):**

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

**SSE (long-running container — start it once, then reference the URL):**

```json
{
  "mcpServers": {
    "plex": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PLEX_SERVER_URL` | Yes | — | Base URL of your Plex server (e.g. `http://192.168.1.100:32400`) |
| `PLEX_TOKEN` | Yes | — | Your Plex authentication token |
| `MCP_TRANSPORT` | No | `stdio` | Transport: `stdio`, `sse`, or `streamable-http` |
| `MCP_HOST` | No | `0.0.0.0` | Bind address for HTTP transports |
| `MCP_PORT` | No | `8000` | Bind port for HTTP transports |

**How to find your Plex token:** sign in at plex.tv → open any media item → `···` menu → Get Info → View XML → look for `X-Plex-Token` in the URL.

## Docker Compose

Two compose files are included:

**`docker-compose.stdio.yml`** — one-shot stdio container (used by MCP clients that spawn the process):

```bash
PLEX_SERVER_URL=http://192.168.1.100:32400 PLEX_TOKEN=your_token \
  docker compose -f docker-compose.stdio.yml run --rm plex-mcp
```

**`docker-compose.sse.yml`** — persistent HTTP server with health check and auto-restart:

```bash
# create a .env file with PLEX_SERVER_URL and PLEX_TOKEN, then:
docker compose -f docker-compose.sse.yml up -d
```

SSE endpoint: `http://localhost:8000/sse`  
streamable-http: `MCP_TRANSPORT=streamable-http docker compose -f docker-compose.sse.yml up -d` → `http://localhost:8000/mcp`

## Transport

| Mode | How | Endpoint |
|---|---|---|
| stdio | `-i` / `docker-compose.stdio.yml` | — |
| SSE | `-e MCP_TRANSPORT=sse` / `docker-compose.sse.yml` | `http://host:8000/sse` |
| streamable-http | `-e MCP_TRANSPORT=streamable-http` | `http://host:8000/mcp` |

## Source

[github.com/lordraw77/plex-mcp](https://github.com/lordraw77/plex-mcp)
