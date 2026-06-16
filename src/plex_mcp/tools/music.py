from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from ..client import get_plex, music_sections

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def search_music(
        artist: str = "",
        album: str = "",
        track: str = "",
        limit: int = 20,
    ) -> str:
        """Search for music in the Plex library. At least one parameter is required.

        Args:
            artist: Filter by artist name
            album: Filter by album name
            track: Filter by track/song title
            limit: Maximum number of results (default 20)
        """
        if not any([artist, album, track]):
            return "Provide at least one of: artist, album, or track."

        def _search():
            plex = get_plex()
            results = []
            for section in music_sections(plex):
                if track:
                    found = section.searchTracks(title=track)
                    if artist:
                        a = artist.lower()
                        found = [t for t in found if t.grandparentTitle.lower() == a]
                    results.extend(found[:limit])
                elif album:
                    found = section.searchAlbums(title=album)
                    if artist:
                        a = artist.lower()
                        found = [al for al in found if al.parentTitle.lower() == a]
                    results.extend(found[:limit])
                elif artist:
                    found = section.search(title=artist)
                    results.extend(found[:limit])
            return results[:limit]

        try:
            results = await asyncio.to_thread(_search)
        except Exception as e:
            logger.error("search_music: %s", e)
            return f"Error searching music: {e}"

        if not results:
            return "No music found matching your criteria."

        lines = [f"Found {len(results)} result(s):\n"]
        for item in results:
            kind = item.TYPE
            if kind == "track":
                duration = f"{item.duration // 60000}:{(item.duration % 60000) // 1000:02d}" if item.duration else "?"
                lines.append(f"  ♪ {item.grandparentTitle} — {item.parentTitle} — {item.title} ({duration})")
            elif kind == "album":
                lines.append(f"  💿 {item.parentTitle} — {item.title} ({item.year or '?'})")
            elif kind == "artist":
                lines.append(f"  🎤 {item.title}")
        return "\n".join(lines)

    @mcp.tool()
    async def get_artist_details(artist_name: str) -> str:
        """Get detailed information about a music artist.

        Args:
            artist_name: Artist name (exact or partial match)
        """
        def _get():
            plex = get_plex()
            for section in music_sections(plex):
                results = section.search(title=artist_name)
                if results:
                    artist = results[0]
                    albums = artist.albums()
                    return artist, albums
            return None, []

        try:
            artist, albums = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_artist_details: %s", e)
            return f"Error: {e}"

        if not artist:
            return f"Artist '{artist_name}' not found."

        genres = ", ".join(g.tag for g in (artist.genres or []))
        lines = [
            f"Artist:  {artist.title}",
            f"Genre:   {genres or 'N/A'}",
            f"Albums:  {len(albums)}\n",
        ]
        for album in albums:
            lines.append(f"  💿 {album.title} ({album.year or '?'}) — {album.leafCount or '?'} tracks")
        if artist.summary:
            lines.append(f"\nBio:\n{artist.summary}")
        return "\n".join(lines)

    @mcp.tool()
    async def get_album_details(artist_name: str, album_title: str) -> str:
        """Get detailed information about an album including its tracklist.

        Args:
            artist_name: Artist name (exact or partial match)
            album_title: Album title (exact or partial match)
        """
        def _get():
            plex = get_plex()
            for section in music_sections(plex):
                albums = section.searchAlbums(title=album_title)
                for album in albums:
                    if artist_name.lower() in album.parentTitle.lower():
                        return album, album.tracks()
            return None, []

        try:
            album, tracks = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_album_details: %s", e)
            return f"Error: {e}"

        if not album:
            return f"Album '{album_title}' by '{artist_name}' not found."

        genres = ", ".join(g.tag for g in (album.genres or []))
        lines = [
            f"Album:   {album.title}",
            f"Artist:  {album.parentTitle}",
            f"Year:    {album.year or 'N/A'}",
            f"Genre:   {genres or 'N/A'}",
            f"Tracks:  {len(tracks)}\n",
        ]
        for track in tracks:
            duration = (
                f"{track.duration // 60000}:{(track.duration % 60000) // 1000:02d}"
                if track.duration else "?"
            )
            lines.append(f"  {track.trackNumber or '?':>2}. {track.title} ({duration})")
        return "\n".join(lines)

    @mcp.tool()
    async def get_recent_music(limit: int = 10) -> str:
        """Get recently added music (albums or tracks).

        Args:
            limit: Maximum number of results (default 10)
        """
        def _get():
            plex = get_plex()
            results = []
            for section in music_sections(plex):
                results.extend(section.recentlyAdded(maxresults=limit))
            results.sort(key=lambda x: x.addedAt or 0, reverse=True)
            return results[:limit]

        try:
            results = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_recent_music: %s", e)
            return f"Error: {e}"

        if not results:
            return "No recently added music found."

        lines = [f"Recently added music ({len(results)}):\n"]
        for item in results:
            added = item.addedAt.strftime("%Y-%m-%d") if item.addedAt else "?"
            if item.TYPE == "album":
                lines.append(f"  💿 {item.parentTitle} — {item.title} ({item.year or '?'}) — added {added}")
            else:
                lines.append(f"  ♪ {item.title} — added {added}")
        return "\n".join(lines)
