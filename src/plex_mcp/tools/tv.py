from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from ..client import _find_show, get_plex, show_sections

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def search_shows(
        query: str = "",
        genre: str = "",
        actor: str = "",
        year: int | None = None,
        unwatched_only: bool = False,
        limit: int = 20,
    ) -> str:
        """Search for TV shows in the Plex library.

        Args:
            query: Title substring to search for
            genre: Filter by genre (e.g. "Drama", "Comedy")
            actor: Filter by actor/cast member name
            year: Filter by first air year
            unwatched_only: Return only shows with unwatched episodes
            limit: Maximum number of results (default 20)
        """
        def _search():
            plex = get_plex()
            results = []
            for section in show_sections(plex):
                kwargs: dict = {}
                if query:
                    kwargs["title"] = query
                if genre:
                    kwargs["genre"] = genre
                if year:
                    kwargs["year"] = year
                found = section.search(**kwargs) if kwargs else section.all()
                if actor:
                    a = actor.lower()
                    found = [s for s in found if any(r.tag.lower() == a for r in (s.roles or []))]
                if unwatched_only:
                    found = [s for s in found if s.viewedLeafCount < s.leafCount]
                results.extend(found)
            return results[:limit]

        try:
            results = await asyncio.to_thread(_search)
        except Exception as e:
            logger.error("search_shows: %s", e)
            return f"Error searching shows: {e}"

        if not results:
            return "No TV shows found matching your criteria."

        lines = [f"Found {len(results)} show(s):\n"]
        for s in results:
            watched = s.viewedLeafCount or 0
            total = s.leafCount or 0
            seasons = s.childCount or 0
            genres = ", ".join(g.tag for g in (s.genres or []))
            lines.append(
                f"  {s.title} ({s.year}) — {seasons} season(s) | "
                f"{watched}/{total} episodes watched | {genres}"
            )
        return "\n".join(lines)

    @mcp.tool()
    async def get_show_details(title: str) -> str:
        """Get detailed information about a specific TV show.

        Args:
            title: Show title (exact or partial match)
        """
        def _get():
            return _find_show(get_plex(), title)

        try:
            show = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_show_details: %s", e)
            return f"Error: {e}"

        if not show:
            return f"Show '{title}' not found."

        genres = ", ".join(g.tag for g in (show.genres or []))
        cast = ", ".join(r.tag for r in (show.roles or [])[:8])
        watched = show.viewedLeafCount or 0
        total = show.leafCount or 0
        added = show.addedAt.strftime("%Y-%m-%d") if show.addedAt else "N/A"

        return (
            f"Title:        {show.title}\n"
            f"Year:         {show.year}\n"
            f"Seasons:      {show.childCount or 'N/A'}\n"
            f"Episodes:     {total} total | {watched} watched\n"
            f"Genre:        {genres or 'N/A'}\n"
            f"Cast:         {cast or 'N/A'}\n"
            f"Rating:       {show.userRating}/10" if show.userRating else f"Rating:       Not rated\n"
            f"Content:      {show.contentRating or 'N/A'}\n"
            f"Studio:       {show.studio or 'N/A'}\n"
            f"Added:        {added}\n"
            f"\nSummary:\n{show.summary or 'N/A'}"
        )

    @mcp.tool()
    async def get_show_seasons(title: str) -> str:
        """List all seasons of a TV show.

        Args:
            title: Show title (exact or partial match)
        """
        def _get():
            show = _find_show(get_plex(), title)
            if not show:
                return None, []
            return show.title, show.seasons()

        try:
            show_title, seasons = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_show_seasons: %s", e)
            return f"Error: {e}"

        if not show_title:
            return f"Show '{title}' not found."

        lines = [f"{show_title} — {len(seasons)} season(s):\n"]
        for season in seasons:
            watched = season.viewedLeafCount or 0
            total = season.leafCount or 0
            lines.append(f"  Season {season.seasonNumber}: {total} episodes ({watched} watched)")
        return "\n".join(lines)

    @mcp.tool()
    async def get_season_episodes(show_title: str, season_number: int) -> str:
        """List all episodes of a specific season.

        Args:
            show_title: Show title (exact or partial match)
            season_number: Season number (e.g. 1, 2, 3)
        """
        def _get():
            show = _find_show(get_plex(), show_title)
            if not show:
                return None, None, []
            season = show.season(season_number)
            return show.title, season.seasonNumber, season.episodes()

        try:
            title, season_num, episodes = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_season_episodes: %s", e)
            return f"Error: {e}"

        if not title:
            return f"Show '{show_title}' not found."
        if not episodes:
            return f"Season {season_number} not found for '{show_title}'."

        lines = [f"{title} — Season {season_num} ({len(episodes)} episodes):\n"]
        for ep in episodes:
            watched = "✓" if ep.isWatched else "○"
            duration = f"{ep.duration // 60000}min" if ep.duration else "?"
            lines.append(f"  {watched} E{ep.episodeNumber:02d}: {ep.title} ({duration})")
        return "\n".join(lines)

    @mcp.tool()
    async def get_recent_episodes(limit: int = 10) -> str:
        """Get recently added TV episodes.

        Args:
            limit: Maximum number of results (default 10)
        """
        def _get():
            plex = get_plex()
            results = []
            for section in show_sections(plex):
                results.extend(section.recentlyAdded(maxresults=limit))
            results.sort(key=lambda e: e.addedAt or 0, reverse=True)
            return results[:limit]

        try:
            results = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_recent_episodes: %s", e)
            return f"Error: {e}"

        if not results:
            return "No recently added episodes found."

        lines = [f"Recently added episodes ({len(results)}):\n"]
        for ep in results:
            added = ep.addedAt.strftime("%Y-%m-%d") if ep.addedAt else "?"
            show = ep.grandparentTitle or "?"
            lines.append(
                f"  {show} S{ep.parentIndex or '?':02}E{ep.episodeNumber or '?':02}: "
                f"{ep.title} — added {added}"
            )
        return "\n".join(lines)

    @mcp.tool()
    async def mark_episode_watched(show_title: str, season_number: int, episode_number: int) -> str:
        """Mark a specific episode as watched.

        Args:
            show_title: Show title (exact or partial match)
            season_number: Season number
            episode_number: Episode number within the season
        """
        def _mark():
            show = _find_show(get_plex(), show_title)
            if not show:
                return None
            episode = show.episode(season=season_number, episode=episode_number)
            episode.markWatched()
            return f"{show.title} S{season_number:02}E{episode_number:02}: {episode.title}"

        try:
            result = await asyncio.to_thread(_mark)
        except Exception as e:
            logger.error("mark_episode_watched: %s", e)
            return f"Error: {e}"

        return f"Marked as watched: {result}" if result else f"Show '{show_title}' not found."

    @mcp.tool()
    async def rate_show(title: str, rating: float) -> str:
        """Rate a TV show on a 1–10 scale.

        Args:
            title: Show title (exact or partial match)
            rating: Rating from 1.0 to 10.0
        """
        if not 1.0 <= rating <= 10.0:
            return "Rating must be between 1 and 10."

        def _rate():
            show = _find_show(get_plex(), title)
            if not show:
                return None
            show.rate(rating)
            return show.title

        try:
            rated = await asyncio.to_thread(_rate)
        except Exception as e:
            logger.error("rate_show: %s", e)
            return f"Error: {e}"

        return f"Rated '{rated}' {rating}/10." if rated else f"Show '{title}' not found."
