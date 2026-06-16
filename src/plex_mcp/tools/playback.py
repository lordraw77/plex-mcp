from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from ..client import _find_client, _find_movie, _find_show, get_plex, music_sections

logger = logging.getLogger(__name__)


def _resolve_playable(plex, title: str, media_type: str):
    """Return a playable Plex media object."""
    if media_type == "movie":
        return _find_movie(plex, title)
    if media_type in ("show", "episode"):
        show = _find_show(plex, title)
        if show:
            # Return first unwatched episode, or first episode
            episodes = show.episodes()
            unwatched = [e for e in episodes if not e.isWatched]
            return unwatched[0] if unwatched else (episodes[0] if episodes else None)
    if media_type == "music":
        for section in music_sections(plex):
            tracks = section.searchTracks(title=title)
            if tracks:
                return tracks[0]
    return None


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def get_active_sessions() -> str:
        """Get all currently active Plex streaming sessions."""
        def _get():
            plex = get_plex()
            return plex.sessions()

        try:
            sessions = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_active_sessions: %s", e)
            return f"Error: {e}"

        if not sessions:
            return "No active sessions."

        lines = [f"Active sessions ({len(sessions)}):\n"]
        for s in sessions:
            user = s.usernames[0] if s.usernames else "Unknown"
            player = s.players[0] if s.players else None
            client = player.title if player else "Unknown client"
            state = player.state if player else "?"

            if s.TYPE == "movie":
                media_info = f"🎬 {s.title} ({s.year})"
            elif s.TYPE == "episode":
                media_info = (
                    f"📺 {s.grandparentTitle} "
                    f"S{s.parentIndex or '?':02}E{s.episodeNumber or '?':02}: {s.title}"
                )
            elif s.TYPE == "track":
                media_info = f"♪ {s.grandparentTitle} — {s.title}"
            else:
                media_info = s.title

            progress = ""
            if s.viewOffset and s.duration:
                pct = int(s.viewOffset / s.duration * 100)
                offset_min = s.viewOffset // 60000
                total_min = s.duration // 60000
                progress = f" ({offset_min}/{total_min}min, {pct}%)"

            lines.append(f"  [{state}] {user} on {client}: {media_info}{progress}")
        return "\n".join(lines)

    @mcp.tool()
    async def get_clients() -> str:
        """List all available Plex clients (players) on the network."""
        def _get():
            plex = get_plex()
            return plex.clients()

        try:
            clients = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_clients: %s", e)
            return f"Error: {e}"

        if not clients:
            return "No Plex clients found on the network."

        lines = [f"Available clients ({len(clients)}):\n"]
        for c in clients:
            lines.append(f"  • {c.title} [{c.product}] — {c.address}")
        return "\n".join(lines)

    @mcp.tool()
    async def play_media(client_name: str, title: str, media_type: str = "movie") -> str:
        """Play a media item on a specific Plex client.

        Args:
            client_name: Name of the Plex client (use get_clients to list available ones)
            title: Title of the movie, show, or track to play
            media_type: Type of media — "movie", "show", or "music" (default "movie")
        """
        def _play():
            plex = get_plex()
            client = _find_client(plex, client_name)
            if not client:
                return f"Client '{client_name}' not found. Use get_clients() to list available clients."
            item = _resolve_playable(plex, title, media_type)
            if not item:
                return f"'{title}' not found."
            client.playMedia(item)
            return f"Playing '{item.title}' on '{client.title}'."

        try:
            result = await asyncio.to_thread(_play)
        except Exception as e:
            logger.error("play_media: %s", e)
            return f"Error: {e}"

        return result

    @mcp.tool()
    async def pause_playback(client_name: str) -> str:
        """Pause playback on a Plex client.

        Args:
            client_name: Name of the Plex client
        """
        def _pause():
            plex = get_plex()
            client = _find_client(plex, client_name)
            if not client:
                return f"Client '{client_name}' not found."
            client.pause()
            return f"Paused playback on '{client.title}'."

        try:
            result = await asyncio.to_thread(_pause)
        except Exception as e:
            logger.error("pause_playback: %s", e)
            return f"Error: {e}"

        return result

    @mcp.tool()
    async def resume_playback(client_name: str) -> str:
        """Resume paused playback on a Plex client.

        Args:
            client_name: Name of the Plex client
        """
        def _resume():
            plex = get_plex()
            client = _find_client(plex, client_name)
            if not client:
                return f"Client '{client_name}' not found."
            client.play()
            return f"Resumed playback on '{client.title}'."

        try:
            result = await asyncio.to_thread(_resume)
        except Exception as e:
            logger.error("resume_playback: %s", e)
            return f"Error: {e}"

        return result

    @mcp.tool()
    async def stop_playback(client_name: str) -> str:
        """Stop playback on a Plex client.

        Args:
            client_name: Name of the Plex client
        """
        def _stop():
            plex = get_plex()
            client = _find_client(plex, client_name)
            if not client:
                return f"Client '{client_name}' not found."
            client.stop()
            return f"Stopped playback on '{client.title}'."

        try:
            result = await asyncio.to_thread(_stop)
        except Exception as e:
            logger.error("stop_playback: %s", e)
            return f"Error: {e}"

        return result

    @mcp.tool()
    async def seek_to(client_name: str, position_ms: int) -> str:
        """Seek to a specific position in the currently playing media.

        Args:
            client_name: Name of the Plex client
            position_ms: Position in milliseconds (e.g. 90000 = 1 minute 30 seconds)
        """
        def _seek():
            plex = get_plex()
            client = _find_client(plex, client_name)
            if not client:
                return f"Client '{client_name}' not found."
            client.seekTo(position_ms)
            mins = position_ms // 60000
            secs = (position_ms % 60000) // 1000
            return f"Seeked to {mins}:{secs:02d} on '{client.title}'."

        try:
            result = await asyncio.to_thread(_seek)
        except Exception as e:
            logger.error("seek_to: %s", e)
            return f"Error: {e}"

        return result

    @mcp.tool()
    async def set_volume(client_name: str, level: int) -> str:
        """Set the volume on a Plex client.

        Args:
            client_name: Name of the Plex client
            level: Volume level from 0 (mute) to 100 (max)
        """
        if not 0 <= level <= 100:
            return "Volume level must be between 0 and 100."

        def _set():
            plex = get_plex()
            client = _find_client(plex, client_name)
            if not client:
                return f"Client '{client_name}' not found."
            client.setVolume(level)
            return f"Set volume to {level}% on '{client.title}'."

        try:
            result = await asyncio.to_thread(_set)
        except Exception as e:
            logger.error("set_volume: %s", e)
            return f"Error: {e}"

        return result

    @mcp.tool()
    async def skip_next(client_name: str) -> str:
        """Skip to the next item in the queue on a Plex client.

        Args:
            client_name: Name of the Plex client
        """
        def _skip():
            plex = get_plex()
            client = _find_client(plex, client_name)
            if not client:
                return f"Client '{client_name}' not found."
            client.skipNext()
            return f"Skipped to next on '{client.title}'."

        try:
            result = await asyncio.to_thread(_skip)
        except Exception as e:
            logger.error("skip_next: %s", e)
            return f"Error: {e}"

        return result
