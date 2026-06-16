from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

from ..client import _find_movie, get_plex, movie_sections

logger = logging.getLogger(__name__)


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def search_movies(
        query: str = "",
        genre: str = "",
        year: int | None = None,
        director: str = "",
        actor: str = "",
        unwatched_only: bool = False,
        limit: int = 20,
    ) -> str:
        """Search for movies in the Plex library.

        Args:
            query: Title substring to search for
            genre: Filter by genre (e.g. "Action", "Drama", "Comedy")
            year: Filter by release year
            director: Filter by director name
            actor: Filter by actor/cast member name
            unwatched_only: Return only unwatched movies
            limit: Maximum number of results (default 20)
        """
        def _search() -> list:
            plex = get_plex()
            results = []
            for section in movie_sections(plex):
                kwargs: dict = {}
                if query:
                    kwargs["title"] = query
                if genre:
                    kwargs["genre"] = genre
                if year:
                    kwargs["year"] = year
                if director:
                    kwargs["director"] = director
                found = section.search(**kwargs) if kwargs else section.all()
                if actor:
                    a = actor.lower()
                    found = [m for m in found if any(r.tag.lower() == a for r in (m.roles or []))]
                if unwatched_only:
                    found = [m for m in found if not m.isWatched]
                results.extend(found)
            return results[:limit]

        try:
            results = await asyncio.to_thread(_search)
        except Exception as e:
            logger.error("search_movies: %s", e)
            return f"Error searching movies: {e}"

        if not results:
            return "No movies found matching your criteria."

        lines = [f"Found {len(results)} movie(s):\n"]
        for m in results:
            watched = "✓" if m.isWatched else "○"
            rating = f" | ★ {m.userRating}/10" if m.userRating else ""
            duration = f" | {m.duration // 60000}min" if m.duration else ""
            lines.append(f"  {watched} {m.title} ({m.year}){duration}{rating}")
        return "\n".join(lines)

    @mcp.tool()
    async def get_movie_details(title: str) -> str:
        """Get detailed information about a specific movie.

        Args:
            title: Movie title (exact or partial match)
        """
        def _get():
            return _find_movie(get_plex(), title)

        try:
            movie = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_movie_details: %s", e)
            return f"Error: {e}"

        if not movie:
            return f"Movie '{title}' not found."

        directors = ", ".join(d.tag for d in (movie.directors or []))
        writers = ", ".join(w.tag for w in (movie.writers or []))
        cast = ", ".join(r.tag for r in (movie.roles or [])[:8])
        genres = ", ".join(g.tag for g in (movie.genres or []))
        duration = f"{movie.duration // 60000}min" if movie.duration else "N/A"
        user_rating = f"{movie.userRating}/10" if movie.userRating else "Not rated"
        audience_rating = f"{movie.audienceRating}/10" if movie.audienceRating else "N/A"
        added = movie.addedAt.strftime("%Y-%m-%d") if movie.addedAt else "N/A"

        return (
            f"Title:           {movie.title}\n"
            f"Year:            {movie.year}\n"
            f"Duration:        {duration}\n"
            f"Genre:           {genres or 'N/A'}\n"
            f"Director:        {directors or 'N/A'}\n"
            f"Writers:         {writers or 'N/A'}\n"
            f"Cast:            {cast or 'N/A'}\n"
            f"User Rating:     {user_rating}\n"
            f"Audience Rating: {audience_rating}\n"
            f"Watched:         {'Yes' if movie.isWatched else 'No'} (×{movie.viewCount or 0})\n"
            f"Added:           {added}\n"
            f"Content Rating:  {movie.contentRating or 'N/A'}\n"
            f"Studio:          {movie.studio or 'N/A'}\n"
            f"\nSummary:\n{movie.summary or 'N/A'}"
        )

    @mcp.tool()
    async def get_movie_genres(title: str) -> str:
        """Get the genres for a specific movie.

        Args:
            title: Movie title (exact or partial match)
        """
        def _get():
            movie = _find_movie(get_plex(), title)
            if not movie:
                return None, []
            return movie.title, [g.tag for g in (movie.genres or [])]

        try:
            movie_title, genres = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_movie_genres: %s", e)
            return f"Error: {e}"

        if not movie_title:
            return f"Movie '{title}' not found."
        return f"{movie_title} — Genres: {', '.join(genres) or 'None'}"

    @mcp.tool()
    async def get_recent_movies(limit: int = 10) -> str:
        """Get recently added movies across all movie libraries.

        Args:
            limit: Maximum number of results (default 10)
        """
        def _get():
            plex = get_plex()
            results = []
            for section in movie_sections(plex):
                results.extend(section.recentlyAdded(maxresults=limit))
            results.sort(key=lambda m: m.addedAt or 0, reverse=True)
            return results[:limit]

        try:
            results = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_recent_movies: %s", e)
            return f"Error: {e}"

        if not results:
            return "No recently added movies found."

        lines = [f"Recently added movies ({len(results)}):\n"]
        for m in results:
            added = m.addedAt.strftime("%Y-%m-%d") if m.addedAt else "?"
            lines.append(f"  {m.title} ({m.year}) — added {added}")
        return "\n".join(lines)

    @mcp.tool()
    async def get_unwatched_movies(limit: int = 20) -> str:
        """Get unwatched movies from the library.

        Args:
            limit: Maximum number of results (default 20)
        """
        def _get():
            plex = get_plex()
            results = []
            for section in movie_sections(plex):
                results.extend(m for m in section.all() if not m.isWatched)
            return results[:limit]

        try:
            results = await asyncio.to_thread(_get)
        except Exception as e:
            logger.error("get_unwatched_movies: %s", e)
            return f"Error: {e}"

        if not results:
            return "No unwatched movies found."

        lines = [f"Unwatched movies ({len(results)}):\n"]
        for m in results:
            lines.append(f"  ○ {m.title} ({m.year})")
        return "\n".join(lines)

    @mcp.tool()
    async def mark_movie_watched(title: str) -> str:
        """Mark a movie as watched.

        Args:
            title: Movie title (exact or partial match)
        """
        def _mark():
            movie = _find_movie(get_plex(), title)
            if not movie:
                return None
            movie.markWatched()
            return movie.title

        try:
            marked = await asyncio.to_thread(_mark)
        except Exception as e:
            logger.error("mark_movie_watched: %s", e)
            return f"Error: {e}"

        return f"Marked '{marked}' as watched." if marked else f"Movie '{title}' not found."

    @mcp.tool()
    async def mark_movie_unwatched(title: str) -> str:
        """Mark a movie as unwatched.

        Args:
            title: Movie title (exact or partial match)
        """
        def _mark():
            movie = _find_movie(get_plex(), title)
            if not movie:
                return None
            movie.markUnwatched()
            return movie.title

        try:
            marked = await asyncio.to_thread(_mark)
        except Exception as e:
            logger.error("mark_movie_unwatched: %s", e)
            return f"Error: {e}"

        return f"Marked '{marked}' as unwatched." if marked else f"Movie '{title}' not found."

    @mcp.tool()
    async def rate_movie(title: str, rating: float) -> str:
        """Rate a movie on a 1–10 scale.

        Args:
            title: Movie title (exact or partial match)
            rating: Rating from 1.0 to 10.0
        """
        if not 1.0 <= rating <= 10.0:
            return "Rating must be between 1 and 10."

        def _rate():
            movie = _find_movie(get_plex(), title)
            if not movie:
                return None
            movie.rate(rating)
            return movie.title

        try:
            rated = await asyncio.to_thread(_rate)
        except Exception as e:
            logger.error("rate_movie: %s", e)
            return f"Error: {e}"

        return f"Rated '{rated}' {rating}/10." if rated else f"Movie '{title}' not found."
