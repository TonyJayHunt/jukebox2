import sys
from unittest.mock import MagicMock, patch

# --- Pre-Import Mocking of Kivy ---
# We mock the Kivy modules so we can import 'gui.py' without a window/display.

mock_kivy = MagicMock()
sys.modules['kivy'] = mock_kivy
sys.modules['kivy.uix.boxlayout'] = MagicMock()
sys.modules['kivy.uix.label'] = MagicMock()
sys.modules['kivy.uix.button'] = MagicMock()
sys.modules['kivy.uix.image'] = MagicMock()
sys.modules['kivy.uix.scrollview'] = MagicMock()
sys.modules['kivy.uix.spinner'] = MagicMock()
sys.modules['kivy.uix.gridlayout'] = MagicMock()
sys.modules['kivy.core.text'] = MagicMock()
sys.modules['kivy.core.image'] = MagicMock()
sys.modules['kivy.graphics'] = MagicMock()
sys.modules['kivy.uix.widget'] = MagicMock()

# Mock Properties specifically so they behave somewhat like Kivy properties
# (Holding a value we can check)
def MockProperty(default=None):
    return default

sys.modules['kivy.properties'] = MagicMock()
sys.modules['kivy.properties'].StringProperty = MockProperty
sys.modules['kivy.properties'].ListProperty = lambda: []
sys.modules['kivy.properties'].ObjectProperty = lambda: None

# Mock PIL and io used in gui.py
sys.modules['PIL'] = MagicMock()
sys.modules['io'] = MagicMock()

# Now we can safely import the module under test
import gui
from gui import JukeboxGUI

import pytest
import allure

# --- Fixtures ---

@pytest.fixture
def mock_player():
    player = MagicMock()
    player.played_songs = set()
    player.primary_playlist = []
    player.Special_playlist = []
    return player

@pytest.fixture
def jukebox_gui(mock_player):
    # Mock the internal widgets created in __init__ so we can inspect them
    with patch('gui.BoxLayout'):
        with patch('gui.Button') as MockButton:
            with patch('gui.Label'):
                with patch('gui.Spinner'):
                    with patch('gui.GridLayout') as MockGrid:
                        gui_instance = JukeboxGUI()
                        
                        # Manually attach our mock player
                        gui_instance.player = mock_player
                        
                        # Mock the internal grid for songs so we can check if buttons are added
                        gui_instance.songs_grid = MagicMock()
                        gui_instance.songs_grid.children = []
                        gui_instance.songs_grid.add_widget = MagicMock()
                        
                        # Mock genre buttons box
                        gui_instance.genre_buttons_box = MagicMock()
                        gui_instance.genre_buttons_box.children = []

                        return gui_instance

# --- Tests ---

@allure.epic("GUI Logic")
@allure.suite("Filtering System")
@allure.feature("Artist Filter")
class TestArtistFilter:

    @allure.story("Selection")
    @allure.title("Set artist filter updates state and display")
    def test_set_artist_filter(self, jukebox_gui):
        """
        Scenario: User selects 'ABBA'.
        Expectation: Filter set, Genre reset to All, display refreshed.
        """
        jukebox_gui.display_songs = MagicMock()
        
        jukebox_gui.set_artist_filter('ABBA')
        
        assert jukebox_gui.artist_filter == 'ABBA'
        assert jukebox_gui.genre_filter == 'All'
        # Spinner text should update
        assert jukebox_gui.artist_spinner.text == 'ABBA'
        # Display refresh triggered
        jukebox_gui.display_songs.assert_called_once()

    @allure.story("Clearing")
    @allure.title("Clear button resets filter to All")
    def test_clear_filter(self, jukebox_gui):
        jukebox_gui.display_songs = MagicMock()
        jukebox_gui.artist_filter = 'Queen'
        
        jukebox_gui.clear_filter()
        
        assert jukebox_gui.artist_filter == 'All'
        assert jukebox_gui.artist_spinner.text == 'All'
        jukebox_gui.display_songs.assert_called()


@allure.epic("GUI Logic")
@allure.suite("Song Display")
@allure.feature("Grid Generation")
class TestSongDisplay:

    @allure.story("Filtering")
    @allure.title("Do not display played songs")
    @patch('gui.Button')
    def test_hide_played_songs(self, MockButton, jukebox_gui, mock_player):
        """
        Scenario: 'Song A' is in played_songs.
        Expectation: No button created for 'Song A'.
        """
        # Setup data
        song_a = {'title': 'Song A', 'artists': ['A'], 'genres': ['Pop']}
        song_b = {'title': 'Song B', 'artists': ['B'], 'genres': ['Rock']}
        
        jukebox_gui.all_songs = [song_a, song_b]
        mock_player.played_songs = {'Song A'}
        
        jukebox_gui.display_songs()
        
        # We expect add_widget to be called only once (for Song B)
        # MockButton() creates the instance passed to add_widget
        assert jukebox_gui.songs_grid.add_widget.call_count == 1
        
        # Verify the text of the button created contains Song B info
        call_args = MockButton.call_args[1] # kwargs
        assert 'Song B' in call_args['text']

    @allure.story("Filtering")
    @allure.title("Apply Genre Filter")
    @patch('gui.Button')
    def test_genre_filter_logic(self, MockButton, jukebox_gui):
        """
        Scenario: Filter is 'Rock'.
        Expectation: Only Rock songs displayed.
        """
        jukebox_gui.genre_filter = 'Rock'
        
        song_pop = {'title': 'Pop Song', 'genres': ['Pop']}
        song_rock = {'title': 'Rock Song', 'genres': ['Rock']}
        
        jukebox_gui.all_songs = [song_pop, song_rock]
        
        jukebox_gui.display_songs()
        
        assert jukebox_gui.songs_grid.add_widget.call_count == 1
        call_args = MockButton.call_args[1]
        assert 'Rock Song' in call_args['text']

    @allure.story("Visuals")
    @allure.title("Emoji Mapping")
    def test_emoji_mapping(self, jukebox_gui):
        assert jukebox_gui.emoji_for(['rock']) == '🤘'
        assert jukebox_gui.emoji_for(['unknown']) == '🎵'
        assert jukebox_gui.emoji_for(['christmas', 'pop']) == '🎄' # Priority check if any match


@allure.epic("GUI Logic")
@allure.suite("Interactions")
@allure.feature("Event Handlers")
class TestEventHandlers:

    @allure.story("Song Selection")
    @allure.title("Clicking song triggers callback")
    def test_song_click_callback(self, jukebox_gui):
        """
        Scenario: Button pressed.
        Expectation: select_song_cb is fired with song data.
        """
        mock_cb = MagicMock()
        jukebox_gui.select_song_cb = mock_cb
        song_data = {'title': 'Test Song'}
        
        jukebox_gui.handle_song_selection(song_data)
        
        mock_cb.assert_called_once_with(song_data)

    @allure.story("Control Buttons")
    @allure.title("Dance button triggers callback and removes widget")
    def test_dance_button(self, jukebox_gui):
        mock_cb = MagicMock()
        jukebox_gui.dance_cb = mock_cb
        
        # Mock the button existence in row1
        jukebox_gui.dance_btn = MagicMock()
        jukebox_gui.dance_btn.parent = True # Simulate it is attached
        jukebox_gui.row1 = MagicMock()
        
        jukebox_gui.handle_dance(None)
        
        mock_cb.assert_called_once()
        jukebox_gui.row1.remove_widget.assert_called_with(jukebox_gui.dance_btn)

    @allure.story("Control Buttons")
    @allure.title("Ambient controls trigger callbacks")
    def test_ambient_controls(self, jukebox_gui):
        jukebox_gui.play_ambient_cb = MagicMock()
        jukebox_gui.stop_ambient_cb = MagicMock()
        
        jukebox_gui.handle_play_ambient(None)
        jukebox_gui.play_ambient_cb.assert_called_once()
        
        jukebox_gui.handle_stop_ambient(None)
        jukebox_gui.stop_ambient_cb.assert_called_once()


@allure.epic("GUI Logic")
@allure.suite("Status Display")
@allure.feature("Now Playing")
class TestNowPlaying:

    @allure.story("Updates")
    @allure.title("Update labels with song info")
    def test_update_now_playing_text(self, jukebox_gui):
        song = {'title': 'Halo', 'artists': ['Beyonce'], 'genres': ['Pop']}
        
        jukebox_gui.update_now_playing(song)
        
        assert "Beyonce" in jukebox_gui.info_label.text
        assert "Halo" in jukebox_gui.info_label.text

    @allure.story("Reset")
    @allure.title("Handle 'None' (stop state)")
    def test_update_now_playing_none(self, jukebox_gui):
        jukebox_gui.update_now_playing(None)
        assert jukebox_gui.info_label.text == "No song playing"
        assert jukebox_gui.album_art.texture is None