import sys
from unittest.mock import MagicMock, patch, mock_open

# --- Pre-Test Setup: Mock GUI & Kivy Dependencies ---
# We must mock these BEFORE importing main, otherwise the import will fail
# if Kivy is not installed or if a display is not found.
mock_kivy = MagicMock()
sys.modules['kivy'] = mock_kivy
sys.modules['kivy.config'] = MagicMock()
sys.modules['kivy.app'] = MagicMock()
sys.modules['kivy.core.window'] = MagicMock()
sys.modules['kivy.uix.floatlayout'] = MagicMock()
sys.modules['kivy.uix.image'] = MagicMock()
sys.modules['kivy.uix.button'] = MagicMock()

# Mock local UI modules that might be missing in the test env
sys.modules['gui'] = MagicMock()
sys.modules['dialogs'] = MagicMock()

# Now we can safely import main
import main
import pytest
import allure

# --- Fixtures ---

@pytest.fixture(autouse=True)
def reset_globals():
    """Reset main.player and main.gui before every test."""
    main.player = MagicMock()
    main.gui = MagicMock()
    # Setup default list structures for the player mock
    main.player.primary_playlist = []
    main.player.Special_playlist = []
    main.player.default_playlist = []
    main.player.played_songs = set()
    main.player.selected_songs = set()
    main.player.song_counter = 1
    yield
    main.player = None
    main.gui = None

# --- Tests ---

@allure.epic("Main Application")
@allure.suite("Playlist Display Logic")
@allure.feature("Upcoming Songs Generation")
class TestUpcomingSongsDisplay:

    @allure.story("Queue Mixing")
    @allure.title("Interleave Primary and Default playlists")
    def test_upcoming_interleaving(self):
        """
        Scenario: Player has songs in primary and default playlists.
        Expectation: Function simulates logic (primary first) and returns list.
        """
        main.player.primary_playlist = [{'title': 'P1', 'id': 1}, {'title': 'P2', 'id': 2}]
        main.player.default_playlist = [{'title': 'D1', 'id': 3}, {'title': 'D2', 'id': 4}]
        
        # main.py logic: Primary takes precedence unless special slot
        result = main.get_upcoming_songs_for_display()
        
        titles = [s['title'] for s in result]
        # Depending on song_counter, it typically pulls from primary first
        assert titles[:2] == ['P1', 'P2']
        assert 'D1' in titles

    @allure.story("Special Slot")
    @allure.title("Insert Special song at 5th position")
    def test_special_song_slot(self):
        """
        Scenario: song_counter increments. Every 5th song should be special.
        """
        main.player.song_counter = 4 # Next will be 4 (normal), then 5 (special)
        main.player.primary_playlist = [{'title': 'P1'}, {'title': 'P2'}]
        main.player.Special_playlist = [{'title': 'Special1'}]
        
        result = main.get_upcoming_songs_for_display()
        
        # Logic: 
        # Loop 1 (cnt=4): P1
        # Loop 2 (cnt=5): Special1 (Because counter%5==0)
        # Loop 3 (cnt=6): P2
        assert result[0]['title'] == 'P1'
        assert result[1]['title'] == 'Special1'
        assert result[2]['title'] == 'P2'

    @allure.story("Empty State")
    @allure.title("Handle empty player gracefully")
    def test_no_player_instance(self):
        main.player = None
        assert main.get_upcoming_songs_for_display() == []


@allure.epic("Main Application")
@allure.suite("User Interaction")
@allure.feature("Song Selection")
class TestSongSelection:

    @allure.story("Validation")
    @allure.title("Prevent selecting already played songs")
    @patch('main.confirm_dialog_error')
    def test_prevent_played_song(self, mock_dialog):
        """
        Scenario: User selects a song that is in played_songs.
        Expectation: Error dialog shown, no playlist change.
        """
        main.player.played_songs = {'Already Played'}
        song = {'title': 'Already Played', 'key': 1}
        
        main.select_song(song)
        
        mock_dialog.assert_called_once()
        assert "already been played" in mock_dialog.call_args[0][1]
        main.gui.clear_filter.assert_called()

    @allure.story("Validation")
    @allure.title("Prevent duplicates in queue")
    @patch('main.confirm_dialog_error')
    def test_prevent_duplicate_queue(self, mock_dialog):
        """
        Scenario: Song is already in primary_playlist.
        Expectation: Error dialog shown.
        """
        main.player.primary_playlist = [{'title': 'Queue Song', 'key': 99}]
        song = {'title': 'Queue Song', 'key': 99}
        
        main.select_song(song)
        
        mock_dialog.assert_called_once()
        assert "already in the upcoming" in mock_dialog.call_args[0][1]

    @allure.story("Confirmation Flow")
    @allure.title("Add song to queue after user confirms")
    @patch('main.confirm_dialog')
    @patch('main.is_abba_song', return_value=False)
    def test_select_song_success(self, mock_is_abba, mock_confirm):
        """
        Scenario: Valid song selection. User clicks 'Yes' in dialog.
        Expectation: Song added to primary_playlist, removed from default.
        """
        song = {'title': 'New Song', 'key': 100}
        main.player.default_playlist = [song]
        
        # Run function
        main.select_song(song)
        
        # Simulate User Clicking "Yes" in the dialog
        # The app passes a callback `after_confirm` to `confirm_dialog`.
        # We assume confirm_dialog(widget, text, callback) signature.
        args, _ = mock_confirm.call_args
        callback = args[2] 
        callback(True) # User confirmed
        
        # Assertions
        assert song in main.player.primary_playlist
        assert song not in main.player.default_playlist
        assert 'New Song' in main.player.selected_songs
        main.gui.update_upcoming_songs.assert_called()

    @allure.story("ABBA Logic")
    @allure.title("Trigger immediate playback for ABBA")
    @patch('main.confirm_dialog')
    @patch('main.is_abba_song', return_value=True)
    @patch('main.threading.Thread')
    def test_abba_immediate_play(self, mock_thread, mock_is_abba, mock_confirm):
        """
        Scenario: User selects an ABBA song and confirms special warning.
        Expectation: Song plays immediately via threading (doesn't go to queue).
        """
        song = {'title': 'Dancing Queen', 'key': 777}
        
        main.select_song(song)
        
        # Check special warning text
        args, _ = mock_confirm.call_args
        assert "really sure" in args[1]
        
        # Simulate Confirm
        callback = args[2]
        callback(True)
        
        # Should start thread to play immediately
        mock_thread.assert_called_once()
        # Ensure we didn't just add it to the standard playlist
        assert song not in main.player.primary_playlist


@allure.epic("Main Application")
@allure.suite("Data Management")
@allure.feature("File Loading")
class TestDataLoading:

    @allure.story("JSON Parsing")
    @allure.title("Load filenames from JSON")
    def test_load_json(self):
        json_content = '["song1.mp3", "song2.mp3"]'
        with patch("builtins.open", mock_open(read_data=json_content)):
            with patch("json.load", return_value=["song1.mp3", "song2.mp3"]):
                result = main.load_song_filenames_from_json("dummy.json")
                assert result == ["song1.mp3", "song2.mp3"]

    @allure.story("Mapping Logic")
    @allure.title("Map filenames to Song Objects")
    def test_map_filenames(self):
        """
        Scenario: JSON has 'song1.mp3'. Library has full paths.
        Expectation: Return the object matching the filename.
        """
        # Mock global MUSIC_DIR locally for the test logic if needed, 
        # but the function uses os.path.basename fallback which we test here.
        
        mock_library = {
            'c:/music/song1.mp3': {'path': 'c:/music/song1.mp3', 'title': 'S1'},
            'c:/music/song2.mp3': {'path': 'c:/music/song2.mp3', 'title': 'S2'}
        }
        
        filenames = ['song1.mp3']
        
        # Should find song1 despite full path difference due to basename fallback check
        result = main.map_filenames_to_song_objects(filenames, mock_library)
        
        assert len(result) == 1
        assert result[0]['title'] == 'S1'


@allure.epic("Main Application")
@allure.suite("Controls")
@allure.feature("Test & Ambient")
class TestAuxiliaryControls:

    @allure.story("Test Mode")
    @allure.title("Play test songs picks random sample")
    @patch('main.random.sample')
    def test_play_test_songs(self, mock_sample):
        main.all_songs_list = ['s1', 's2', 's3']
        mock_sample.return_value = ['s1', 's3']
        
        main.play_test_songs()
        
        main.player.play_test_songs.assert_called_with(['s1', 's3'])

    @allure.story("Ambient Music")
    @allure.title("Start ambient music delegates to player")
    def test_start_ambient(self):
        main.start_ambient_music()
        main.player.start_ambient_music.assert_called_with("ambiant")