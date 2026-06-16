from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.asyncio
async def test_list_playlists_empty(mock_plex):
    mock_plex.playlists.return_value = []

    with patch("plex_mcp.tools.playlists.get_plex", return_value=mock_plex):
        from plex_mcp.tools.playlists import register
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register(mcp)

        tool = next(t for t in mcp._tools.values() if t.name == "list_playlists")
        result = await tool.fn()

        assert "No playlists" in result


@pytest.mark.asyncio
async def test_list_playlists_with_items(mock_plex):
    pl = MagicMock()
    pl.title = "My Movies"
    pl.playlistType = "video"
    pl.leafCount = 5
    mock_plex.playlists.return_value = [pl]

    with patch("plex_mcp.tools.playlists.get_plex", return_value=mock_plex):
        from plex_mcp.tools.playlists import register
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register(mcp)

        tool = next(t for t in mcp._tools.values() if t.name == "list_playlists")
        result = await tool.fn()

        assert "My Movies" in result
        assert "5" in result


@pytest.mark.asyncio
async def test_delete_playlist_not_found(mock_plex):
    mock_plex.playlists.return_value = []

    with patch("plex_mcp.tools.playlists.get_plex", return_value=mock_plex):
        from plex_mcp.tools.playlists import register
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register(mcp)

        tool = next(t for t in mcp._tools.values() if t.name == "delete_playlist")
        result = await tool.fn(playlist_name="Ghost Playlist")

        assert "not found" in result
