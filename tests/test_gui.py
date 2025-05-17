import pytest
import os
import tkinter as tk
from gui import JukeboxGUI

@pytest.fixture
def root():
    root = tk.Tk()
    yield root
    root.destroy()

def test_hidden_song_key_prevents_button(root):
    # Mocks
    def dummy_select(song): pass
    def dummy_special(): pass
    class DummyPlayer:
        played_songs = set()
    gui = JukeboxGUI(root, dummy_select, dummy_special, DummyPlayer())
    gui.all_songs = [{'key': 1, 'title': 'T', 'artist': 'A', 'genres': ['pop']}]
    gui.hidden_song_keys.add(1)
    gui.display_songs()
    assert 1 not in gui.song_buttons
