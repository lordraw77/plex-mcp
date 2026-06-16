from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from ..client import _find_movie, _find_show, get_plex, music_sections

logger = logging.getLogger(__name__)


def _find_playlist(plex, name: str):
    for pl in plex.playlists():
        if pl.title.lower() == name.lower():
            return pl
    return None


def _resolve_media(plex, title: str, media_type: str):
    """Resolve a title to a Plex media object."""
    if media_type == "movie":
        return _find_movie(plex, title)
    if media_type in ("show", "episode"):
        return _find_show(plex, title)
    if media_type == "music":
        for section in music_sections(plex):
            results = section.searchTracks(title=title)
            if results:
                return results[0]
    return None


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def list_playlists(playlist_type: str = "") -> str:
        """List all playlists on the Plex server.

        Args:
            playlist_type: Optional filter — "video", "audio", or "photo". Leave empty for all.
        """
        def _list():
            plex = get_plex()
            playlists = plex.playlists()
            if playlist_type:
                playlists = [p for p in playlists if p.playlistType == playlist_type]
            return playlists

        try:
            playlists = await asyncio.to_thread(_list)
        except Exception as e:
            logger.error("list_playlists: %s", e)
            return f"Error: {e}"

        if not playlists:
            return "No playlists found."

        lines = [f"Found {len(playlists)} playlist(s):\n"]
        for pl in playlists:
            count = pl.leafCount or 0
            lines.append(f"  • {pl.title} [{pl.playlistType}] — {count} item(s)")
        return "\n".join(lines)

    @mcp.tool()
    async def get_playlist_items(playlist_name: str) -> str:
        """Get all items in a playlist.

        Args:
            playlist_name: Exact playlist name
        """
        def _get():
            plex = get_plex()
            pl = _find_playlist(plex, playlist_name)
            if not pl:
                return None, []
            return pl.title, pl.items()

        try:
            name, items = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_playlist_items: %s", e)
            return f"Error: {e}"

        if not name:
            return f"Playlist '{playlist_name}' not found."
        if not items:
            return f"Playlist '{name}' is empty."

        lines = [f"Playlist: {name} ({len(items)} items)\n"]
        for i, item in enumerate(items, 1):
            kind = item.TYPE
            if kind == "movie":
                lines.append(f"  {i:>3}. 🎬 {item.title} ({item.year})")
            elif kind == "episode":
                lines.append(
                    f"  {i:>3}. 📺 {item.grandparentTitle} "
                    f"S{item.parentIndex or '?':02}E{item.episodeNumber or '?':02}: {item.title}"
                )
            elif kind == "track":
                lines.append(f"  {i:>3}. ♪ {item.grandparentTitle} — {item.title}")
            else:
                lines.append(f"  {i:>3}. {item.title}")
        return "\n".join(lines)

    @mcp.tool()
    async def create_playlist(
        name: str,
        media_titles: list[str],
        media_type: str = "movie",
    ) -> str:
        """Create a new playlist with the specified media items.

        Args:
            name: Playlist name
            media_titles: List of media titles to include
            media_type: Type of media — "movie", "show", or "music" (default "movie")
        """
        def _create():
            plex = get_plex()
            items = []
            not_found = []
            for title in media_titles:
                item = _resolve_media(plex, title, media_type)
                if item:
                    items.append(item)
                else:
                    not_found.append(title)
            if not items:
                return None, not_found
            playlist = plex.createPlaylist(name, items=items)
            return playlist.title, not_found

        try:
            created, not_found = await asyncio.to_thread(_create)
        except Exception as e:
            logger.error("create_playlist: %s", e)
            return f"Error: {e}"

        if not created:
            return f"Could not find any of the specified titles: {', '.join(not_found)}"

        msg = f"Created playlist '{created}'"
        if not_found:
            msg += f"\nNot found (skipped): {', '.join(not_found)}"
        return msg

    @mcp.tool()
    async def add_to_playlist(playlist_name: str, media_title: str, media_type: str = "movie") -> str:
        """Add a media item to an existing playlist.

        Args:
            playlist_name: Exact playlist name
            media_title: Title of the media to add
            media_type: Type of media — "movie", "show", or "music" (default "movie")
        """
        def _add():
            plex = get_plex()
            pl = _find_playlist(plex, playlist_name)
            if not pl:
                return f"Playlist '{playlist_name}' not found."
            item = _resolve_media(plex, media_title, media_type)
            if not item:
                return f"'{media_title}' not found."
            pl.addItems([item])
            return f"Added '{item.title}' to playlist '{pl.title}'."

        try:
            result = await asyncio.to_thread(_add)
        except Exception as e:
            logger.error("add_to_playlist: %s", e)
            return f"Error: {e}"

        return result

    @mcp.tool()
    async def remove_from_playlist(playlist_name: str, media_title: str) -> str:
        """Remove a media item from a playlist.

        Args:
            playlist_name: Exact playlist name
            media_title: Title of the item to remove (partial match)
        """
        def _remove():
            plex = get_plex()
            pl = _find_playlist(plex, playlist_name)
            if not pl:
                return f"Playlist '{playlist_name}' not found."
            items = pl.items()
            target = next((i for i in items if media_title.lower() in i.title.lower()), None)
            if not target:
                return f"'{media_title}' not found in playlist '{pl.title}'."
            pl.removeItems([target])
            return f"Removed '{target.title}' from playlist '{pl.title}'."

        try:
            result = await asyncio.to_thread(_remove)
        except Exception as e:
            logger.error("remove_from_playlist: %s", e)
            return f"Error: {e}"

        return result

    @mcp.tool()
    async def delete_playlist(playlist_name: str) -> str:
        """Delete a playlist permanently.

        Args:
            playlist_name: Exact playlist name
        """
        def _delete():
            plex = get_plex()
            pl = _find_playlist(plex, playlist_name)
            if not pl:
                return f"Playlist '{playlist_name}' not found."
            pl.delete()
            return f"Deleted playlist '{playlist_name}'."

        try:
            result = await asyncio.to_thread(_delete)
        except Exception as e:
            logger.error("delete_playlist: %s", e)
            return f"Error: {e}"

        return result
