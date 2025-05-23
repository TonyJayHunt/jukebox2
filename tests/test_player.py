import pytest
from unittest.mock import MagicMock, patch
import player

@pytest.fixture
def jukebox_player():
    p = player.JukeboxPlayer(None, lambda x: None, lambda: None, lambda x: None)
    p.primary_playlist = [{'title': 'A', 'path': 'a.mp3', 'genres': ['pop']}]
    p.default_playlist = [{'title': 'B', 'path': 'b.mp3', 'genres': ['pop']}]
    p.Special_playlist = [{'title': 'C', 'path': 'c.mp3', 'genres': ['christmas']}]
    p.song_counter = 4
    return p

def test_get_next_song_primary(jukebox_player):
    next_song = jukebox_player._get_next_song()
    assert next_song['title'] == 'A'

def test_get_next_song_christmas():
    p = player.JukeboxPlayer(None, lambda x: None, lambda: None, lambda x: None)
    p.primary_playlist = []
    p.default_playlist = []
    p.Special_playlist = [{'title': 'C', 'path': 'c.mp3', 'genres': ['christmas']}]
    p.song_counter = 5
    assert p._get_next_song()['title'] == 'C'

def test_skip_current_song(monkeypatch):
    p = player.JukeboxPlayer(None, lambda x: None, lambda: None, lambda x: None)
    with patch("player.pygame.mixer.music.stop") as stop:
        p.skip_current_song()
        stop.assert_called()
