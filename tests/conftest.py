"""Pytest configuration and shared fixtures."""
import pytest


@pytest.fixture
def sample_stop_words():
    """Fixture providing a sample list of stop words."""
    return ["the", "is", "a", "an", "and", "or", "but", "in", "on", "at", "to"]


@pytest.fixture
def sample_movie_data():
    """Fixture providing sample movie dataset."""
    return {
        "movies": [
            {"title": "The Shawshank Redemption", "year": 1994},
            {"title": "The Godfather", "year": 1972},
            {"title": "The Dark Knight", "year": 2008},
            {"title": "Pulp Fiction", "year": 1994},
            {"title": "Forrest Gump", "year": 1994},
            {"title": "Inception", "year": 2010},
            {"title": "The Matrix", "year": 1999},
            {"title": "Goodfellas", "year": 1990},
            {"title": "The Silence of the Lambs", "year": 1991},
            {"title": "Interstellar", "year": 2014}
        ]
    }


@pytest.fixture
def sample_tokens():
    """Fixture providing sample tokens for testing."""
    return ["running", "quickly", "jumped", "over", "fence"]


@pytest.fixture
def sample_text_with_punctuation():
    """Fixture providing text with various punctuation marks."""
    return "Hello, world! How are you? I'm fine. #Testing @mentions & symbols."
