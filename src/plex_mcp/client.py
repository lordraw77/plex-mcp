from __future__ import annotations

import logging
import os

from plexapi.server import PlexServer

logger = logging.getLogger(__name__)

_instance: PlexServer | None = None


def get_plex() -> PlexServer:
    """Return the singleton PlexServer connection, creating it on first call."""
    global _instance
    if _instance is None:
        url = os.environ["PLEX_SERVER_URL"].rstrip("/")
        token = os.environ["PLEX_TOKEN"]
        _instance = PlexServer(url, token)
        logger.info("Connected to Plex: %s (v%s)", _instance.friendlyName, _instance.version)
    return _instance


def movie_sections(plex: PlexServer):
    return [s for s in plex.library.sections() if s.type == "movie"]


def show_sections(plex: PlexServer):
    return [s for s in plex.library.sections() if s.type == "show"]


def music_sections(plex: PlexServer):
    return [s for s in plex.library.sections() if s.type == "artist"]


def _find_movie(plex: PlexServer, title: str):
    for section in movie_sections(plex):
        results = section.search(title=title)
        if results:
            return results[0]
    return None


def _find_show(plex: PlexServer, title: str):
    for section in show_sections(plex):
        results = section.search(title=title)
        if results:
            return results[0]
    return None


def _find_client(plex: PlexServer, name: str):
    clients = plex.clients()
    for c in clients:
        if c.title.lower() == name.lower():
            return c
    return None
