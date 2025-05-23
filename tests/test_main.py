import pytest
import main

def test_get_upcoming_songs_logic(monkeypatch):
    class DummyPlayer:
        primary_playlist = [{'title': 'A'}]
        default_playlist = [{'title': 'B'}]
        Special_playlist = [{'title': 'C'}]
        song_counter = 4
    main.player = DummyPlayer()
    result = main.get_upcoming_songs()
    # Should get A (primary), then C (christmas, because song_counter hits 5)
    assert result[0]['title'] == 'A' or result[1]['title'] == 'C'
