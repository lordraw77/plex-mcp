from __future__ import annotations

import logging

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

mcp = FastMCP(
    name="plex-mcp",
    instructions=(
        "MCP server for Plex Media Server. "
        "Provides tools for movies, TV shows, music, playlists, "
        "playback control, and library management."
    ),
)

from .tools import movies, tv, music, playlists, playback, library  # noqa: E402

movies.register(mcp)
tv.register(mcp)
music.register(mcp)
playlists.register(mcp)
playback.register(mcp)
library.register(mcp)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
