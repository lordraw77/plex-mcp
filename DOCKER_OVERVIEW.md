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

## Quick Start

```bash
docker run --rm -i \
  -e PLEX_SERVER_URL=http://192.168.1.100:32400 \
  -e PLEX_TOKEN=your_token_here \
  lordraw77/plex-mcp:latest
```

## Use with Claude Desktop

Add to `claude_desktop_config.json`:

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

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PLEX_SERVER_URL` | Yes | Base URL of your Plex server (e.g. `http://192.168.1.100:32400`) |
| `PLEX_TOKEN` | Yes | Your Plex authentication token |

**How to find your Plex token:** sign in at plex.tv → open any media item → `···` menu → Get Info → View XML → look for `X-Plex-Token` in the URL.

## Transport

stdio (JSON-RPC 2.0) — the `-i` flag is required to keep stdin open.

## Source

[github.com/lordraw77/plex-mcp](https://github.com/lordraw77/plex-mcp)
