import pytest
from kivy.base import EventLoop
from gui import JukeboxGUI

@pytest.fixture
def gui():
    # Make sure Kivy is initialized for widget creation
    if not EventLoop.event_listeners:
        EventLoop.ensure_window()
    # Create dummy callbacks and player
    class DummyPlayer: played_songs = []
    def dummy_select(song): pass
    def dummy_special(): pass
    jukebox_gui = JukeboxGUI()
    jukebox_gui.select_song_cb = dummy_select
    jukebox_gui.dance_cb = dummy_special
    jukebox_gui.player = DummyPlayer()
    return jukebox_gui

def test_hidden_song_key_prevents_button(gui):
    # Setup
    gui.all_songs = [{'key': 1, 'title': 'T', 'artist': 'A', 'genres': ['pop']}]
    gui.hidden_song_keys = [1]
    gui.display_songs()
    # After display, the grid should have no children since the only song is hidden
    assert len(gui.songs_grid.children) == 0