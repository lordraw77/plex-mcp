from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_movie():
    m = MagicMock()
    m.TYPE = "movie"
    m.title = "Inception"
    m.year = 2010
    m.duration = 8880000  # 148 min
    m.isWatched = False
    m.viewCount = 0
    m.userRating = 9.0
    m.audienceRating = 8.8
    m.contentRating = "PG-13"
    m.studio = "Warner Bros"
    m.summary = "A thief who steals corporate secrets through dream-sharing technology."
    m.addedAt = None
    m.genres = [MagicMock(tag="Action"), MagicMock(tag="Sci-Fi")]
    m.directors = [MagicMock(tag="Christopher Nolan")]
    m.writers = [MagicMock(tag="Christopher Nolan")]
    m.roles = [MagicMock(tag="Leonardo DiCaprio"), MagicMock(tag="Ellen Page")]
    return m


@pytest.fixture
def mock_show():
    s = MagicMock()
    s.TYPE = "show"
    s.title = "Breaking Bad"
    s.year = 2008
    s.childCount = 5
    s.leafCount = 62
    s.viewedLeafCount = 0
    s.summary = "A chemistry teacher turned drug lord."
    s.genres = [MagicMock(tag="Drama"), MagicMock(tag="Crime")]
    s.roles = [MagicMock(tag="Bryan Cranston")]
    s.contentRating = "TV-MA"
    s.studio = "AMC"
    s.userRating = None
    s.addedAt = None
    return s


@pytest.fixture
def mock_plex(mock_movie, mock_show):
    plex = MagicMock()

    movie_section = MagicMock()
    movie_section.type = "movie"
    movie_section.search.return_value = [mock_movie]
    movie_section.all.return_value = [mock_movie]
    movie_section.recentlyAdded.return_value = [mock_movie]

    show_section = MagicMock()
    show_section.type = "show"
    show_section.search.return_value = [mock_show]
    show_section.all.return_value = [mock_show]

    plex.library.sections.return_value = [movie_section, show_section]
    return plex
