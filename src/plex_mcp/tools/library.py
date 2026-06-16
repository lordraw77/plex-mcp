from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from ..client import get_plex

logger = logging.getLogger(__name__)

_SECTION_ICONS = {"movie": "🎬", "show": "📺", "artist": "🎵", "photo": "🖼️"}


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def list_libraries() -> str:
        """List all Plex library sections with their type and item count."""
        def _get():
            return get_plex().library.sections()

        try:
            sections = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("list_libraries: %s", e)
            return f"Error: {e}"

        if not sections:
            return "No libraries found."

        lines = ["Plex Libraries:\n"]
        for s in sections:
            icon = _SECTION_ICONS.get(s.type, "📁")
            lines.append(f"  {icon} {s.title} [{s.type}]")
        return "\n".join(lines)

    @mcp.tool()
    async def get_library_stats(library_name: str) -> str:
        """Get statistics for a specific library section.

        Args:
            library_name: Library name as shown in list_libraries
        """
        def _get():
            plex = get_plex()
            section = plex.library.section(library_name)
            total = section.totalSize if hasattr(section, "totalSize") else len(section.all())
            return section, total

        try:
            section, total = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_library_stats: %s", e)
            return f"Error: {e}"

        icon = _SECTION_ICONS.get(section.type, "📁")
        updated = section.updatedAt.strftime("%Y-%m-%d %H:%M") if section.updatedAt else "N/A"
        scanned = section.scannedAt.strftime("%Y-%m-%d %H:%M") if hasattr(section, "scannedAt") and section.scannedAt else "N/A"

        return (
            f"{icon} Library: {section.title}\n"
            f"Type:         {section.type}\n"
            f"Total items:  {total}\n"
            f"Last updated: {updated}\n"
            f"Last scanned: {scanned}\n"
            f"Language:     {section.language or 'N/A'}"
        )

    @mcp.tool()
    async def refresh_library(library_name: str) -> str:
        """Trigger a metadata refresh/scan on a library section.

        Args:
            library_name: Library name as shown in list_libraries
        """
        def _refresh():
            plex = get_plex()
            section = plex.library.section(library_name)
            section.refresh()
            return section.title

        try:
            name = await asyncio.to_thread(_refresh)
        except Exception as e:
            logger.error("refresh_library: %s", e)
            return f"Error: {e}"

        return f"Refresh triggered for library '{name}'. This runs in the background on the Plex server."

    @mcp.tool()
    async def get_on_deck(limit: int = 10) -> str:
        """Get On Deck items — media the user is currently watching or should watch next.

        Args:
            limit: Maximum number of results (default 10)
        """
        def _get():
            plex = get_plex()
            return plex.library.onDeck()[:limit]

        try:
            items = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_on_deck: %s", e)
            return f"Error: {e}"

        if not items:
            return "Nothing on deck."

        lines = [f"On Deck ({len(items)} items):\n"]
        for item in items:
            if item.TYPE == "episode":
                progress = ""
                if item.viewOffset and item.duration:
                    pct = int(item.viewOffset / item.duration * 100)
                    progress = f" ({pct}% watched)"
                lines.append(
                    f"  📺 {item.grandparentTitle} "
                    f"S{item.parentIndex or '?':02}E{item.episodeNumber or '?':02}: "
                    f"{item.title}{progress}"
                )
            elif item.TYPE == "movie":
                progress = ""
                if item.viewOffset and item.duration:
                    pct = int(item.viewOffset / item.duration * 100)
                    progress = f" ({pct}% watched)"
                lines.append(f"  🎬 {item.title} ({item.year}){progress}")
            else:
                lines.append(f"  {item.title}")
        return "\n".join(lines)

    @mcp.tool()
    async def get_recently_added(limit: int = 15, media_type: str = "") -> str:
        """Get recently added items across all libraries.

        Args:
            limit: Maximum number of results (default 15)
            media_type: Optional filter — "movie", "show", "artist", or "photo". Leave empty for all.
        """
        def _get():
            plex = get_plex()
            sections = plex.library.sections()
            if media_type:
                sections = [s for s in sections if s.type == media_type]
            results = []
            for section in sections:
                results.extend(section.recentlyAdded(maxresults=limit))
            results.sort(key=lambda x: x.addedAt or 0, reverse=True)
            return results[:limit]

        try:
            results = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_recently_added: %s", e)
            return f"Error: {e}"

        if not results:
            return "No recently added items found."

        lines = [f"Recently added ({len(results)} items):\n"]
        for item in results:
            added = item.addedAt.strftime("%Y-%m-%d") if item.addedAt else "?"
            icon = _SECTION_ICONS.get(item.TYPE, "•") if item.TYPE != "artist" else "🎤"
            if item.TYPE == "movie":
                lines.append(f"  {icon} {item.title} ({item.year}) — {added}")
            elif item.TYPE == "episode":
                lines.append(
                    f"  {icon} {item.grandparentTitle} "
                    f"S{item.parentIndex or '?':02}E{item.episodeNumber or '?':02}: {item.title} — {added}"
                )
            elif item.TYPE == "album":
                lines.append(f"  💿 {item.parentTitle} — {item.title} ({item.year or '?'}) — {added}")
            else:
                lines.append(f"  {icon} {item.title} — {added}")
        return "\n".join(lines)
