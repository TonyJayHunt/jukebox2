import sys
import importlib
from unittest.mock import MagicMock, patch, mock_open
import pytest
import allure

@pytest.fixture(scope="module")
def main_module():
    # 1. Create Mocks for Kivy and Local Modules
    mock_kivy = MagicMock()
    mock_gui = MagicMock()
    mock_dialogs = MagicMock()
    
    # 2. Patch sys.modules safely using a dictionary
    modules_to_patch = {
        'kivy': mock_kivy,
        'kivy.config': MagicMock(),
        'kivy.app': MagicMock(),
        'kivy.core.window': MagicMock(),
        'kivy.uix.floatlayout': MagicMock(),
        'kivy.uix.image': MagicMock(),
        'kivy.uix.button': MagicMock(),
        'gui': mock_gui,
        'dialogs': mock_dialogs
    }

    with patch.dict(sys.modules, modules_to_patch):
        if 'main' in sys.modules:
            import main
            importlib.reload(main)
        else:
            import main
        yield main

# --- Tests ---

@pytest.fixture
def reset_globals(main_module):
    """Reset main.player and main.gui before every test."""
    main_module.player = MagicMock()
    main_module.gui = MagicMock()
    main_module.player.primary_playlist = []
    main_module.player.Special_playlist = []
    main_module.player.default_playlist = []
    main_module.player.played_songs = set()
    main_module.player.selected_songs = set()
    main_module.player.song_counter = 1
    yield
    main_module.player = None
    main_module.gui = None

@allure.epic("Main Application")
@allure.suite("Playlist Display Logic")
@allure.feature("Upcoming Songs Generation")
class TestUpcomingSongsDisplay:

    @allure.story("Queue Mixing")
    @allure.title("Interleave Primary and Default playlists")
    def test_upcoming_interleaving(self, main_module, reset_globals):
        main_module.player.primary_playlist = [{'title': 'P1', 'id': 1}]
        main_module.player.default_playlist = [{'title': 'D1', 'id': 3}]
        
        result = main_module.get_upcoming_songs_for_display()
        titles = [s['title'] for s in result]
        assert 'P1' in titles
        assert 'D1' in titles

    @allure.story("Empty State")
    @allure.title("Handle empty player gracefully")
    def test_no_player_instance(self, main_module, reset_globals):
        main_module.player = None
        assert main_module.get_upcoming_songs_for_display() == []

@allure.epic("Main Application")
@allure.suite("User Interaction")
@allure.feature("Song Selection")
class TestSongSelection:

    @allure.story("Validation")
    @allure.title("Prevent selecting already played songs")
    def test_prevent_played_song(self, main_module, reset_globals):
        main_module.player.played_songs = {'Already Played'}
        song = {'title': 'Already Played', 'key': 1}
        
        # Mock confirm_dialog_error inside main
        with patch('main.confirm_dialog_error') as mock_dialog:
            main_module.select_song(song)
            mock_dialog.assert_called_once()
            assert "already been played" in mock_dialog.call_args[0][1]

@allure.epic("Main Application")
@allure.suite("Data Management")
@allure.feature("File Loading")
class TestDataLoading:

    @allure.story("JSON Parsing")
    @allure.title("Load filenames from JSON")
    def test_load_json(self, main_module):
        json_content = '["song1.mp3", "song2.mp3"]'
        with patch("builtins.open", mock_open(read_data=json_content)):
            with patch("json.load", return_value=["song1.mp3", "song2.mp3"]):
                result = main_module.load_song_filenames_from_json("dummy.json")
                assert result == ["song1.mp3", "song2.mp3"]