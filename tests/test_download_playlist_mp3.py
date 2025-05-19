import pytest
import os
from useful_tools.download_playlist_mp3 import (
    sanitize_title,
    parse_artist_title,
    tag_mp3,
)

def test_sanitize_title_removes_suffixes():
    raw = "Daft Punk - One More Time (Official Music Video)"
    assert sanitize_title(raw) == "Daft Punk - One More Time"

def test_sanitize_title_handles_trailing_dash():
    raw = "Hello - (Official Video) -"
    assert sanitize_title(raw) == "Hello"

def test_parse_artist_title_artist_and_title():
    s = "Daft Punk - One More Time"
    artist, title = parse_artist_title(s)
    assert artist == "Daft Punk"
    assert title == "One More Time"

def test_parse_artist_title_no_dash():
    s = "Lonely Song"
    artist, title = parse_artist_title(s)
    assert artist is None
    assert title == "Lonely Song"

def test_tag_mp3(tmp_path):
    # Create a dummy mp3 file
    mp3_path = tmp_path / "song.mp3"
    mp3_path.write_bytes(b"\x00" * 100)  # not a valid mp3 but enough for test
    tag_mp3(str(mp3_path), "ART", "TITLE", "GENRE")
    # Should not raise
