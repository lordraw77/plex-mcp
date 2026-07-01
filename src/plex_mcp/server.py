from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio").lower()
_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
_PORT = int(os.environ.get("MCP_PORT", "8000"))

mcp = FastMCP(
    name="plex-mcp",
    instructions=(
        "MCP server for Plex Media Server. "
        "Provides tools for movies, TV shows, music, playlists, "
        "playback control, and library management."
    ),
    host=_HOST,
    port=_PORT,
)

from .tools import movies, tv, music, playlists, playback, library  # noqa: E402

movies.register(mcp)
tv.register(mcp)
music.register(mcp)
playlists.register(mcp)
playback.register(mcp)
library.register(mcp)


def main() -> None:
    if _TRANSPORT not in ("stdio", "sse", "streamable-http"):
        raise ValueError(f"Unknown MCP_TRANSPORT: {_TRANSPORT!r}. Use 'stdio', 'sse', or 'streamable-http'.")
    if _TRANSPORT != "stdio":
        logging.getLogger(__name__).info("Starting plex-mcp with %s transport on %s:%s", _TRANSPORT, _HOST, _PORT)
    mcp.run(transport=_TRANSPORT)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
