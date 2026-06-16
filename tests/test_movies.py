from __future__ import annotations

import pytest
from unittest.mock import patch

from plex_mcp.client import movie_sections


@pytest.mark.asyncio
async def test_search_movies_returns_results(mock_plex, mock_movie):
    with patch("plex_mcp.tools.movies.get_plex", return_value=mock_plex):
        from plex_mcp.tools.movies import register
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register(mcp)

        # Access the registered tool directly
        tool = next(t for t in mcp._tools.values() if t.name == "search_movies")
        result = await tool.fn(query="Inception")

        assert "Inception" in result
        assert "2010" in result


@pytest.mark.asyncio
async def test_search_movies_no_results(mock_plex):
    mock_plex.library.sections.return_value[0].search.return_value = []
    mock_plex.library.sections.return_value[0].all.return_value = []

    with patch("plex_mcp.tools.movies.get_plex", return_value=mock_plex):
        from plex_mcp.tools.movies import register
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register(mcp)

        tool = next(t for t in mcp._tools.values() if t.name == "search_movies")
        result = await tool.fn(query="Nonexistent Movie")

        assert "No movies found" in result


@pytest.mark.asyncio
async def test_rate_movie_invalid_rating(mock_plex):
    with patch("plex_mcp.tools.movies.get_plex", return_value=mock_plex):
        from plex_mcp.tools.movies import register
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register(mcp)

        tool = next(t for t in mcp._tools.values() if t.name == "rate_movie")
        result = await tool.fn(title="Inception", rating=11.0)

        assert "between 1 and 10" in result
