import sys
import importlib
from unittest.mock import MagicMock, patch
import pytest
import allure

@pytest.fixture(scope="module")
def gui_module():
    mock_kivy = MagicMock()
    # Mock Properties specifically
    def MockProperty(default=None): return default

    modules = {
        'kivy': mock_kivy,
        'kivy.uix.boxlayout': MagicMock(),
        'kivy.uix.label': MagicMock(),
        'kivy.uix.button': MagicMock(),
        'kivy.uix.image': MagicMock(),
        'kivy.uix.scrollview': MagicMock(),
        'kivy.uix.spinner': MagicMock(),
        'kivy.uix.gridlayout': MagicMock(),
        'kivy.core.text': MagicMock(),
        'kivy.core.image': MagicMock(),
        'kivy.graphics': MagicMock(),
        'kivy.uix.widget': MagicMock(),
        'kivy.properties': MagicMock(),
        'PIL': MagicMock(),
        'io': MagicMock()
    }
    modules['kivy.properties'].StringProperty = MockProperty
    modules['kivy.properties'].ListProperty = lambda: []
    modules['kivy.properties'].ObjectProperty = lambda: None

    with patch.dict(sys.modules, modules):
        if 'gui' in sys.modules:
            import gui
            importlib.reload(gui)
        else:
            import gui
        yield gui

@pytest.fixture
def jukebox_gui(gui_module):
    # Mock player
    mock_player = MagicMock()
    mock_player.played_songs = set()
    mock_player.primary_playlist = []
    mock_player.Special_playlist = []

    # Mock widgets during init
    with patch('gui.BoxLayout'), patch('gui.Button'), patch('gui.Label'), \
         patch('gui.Spinner'), patch('gui.GridLayout'):
        gui_instance = gui_module.JukeboxGUI()
        gui_instance.player = mock_player
        gui_instance.songs_grid = MagicMock()
        gui_instance.songs_grid.children = []
        gui_instance.genre_buttons_box = MagicMock()
        gui_instance.genre_buttons_box.children = []
        return gui_instance

@allure.epic("GUI Logic")
@allure.suite("Filtering System")
class TestArtistFilter:
    @allure.story("Selection")
    def test_set_artist_filter(self, jukebox_gui):
        jukebox_gui.display_songs = MagicMock()
        jukebox_gui.set_artist_filter('ABBA')
        assert jukebox_gui.artist_filter == 'ABBA'
        jukebox_gui.display_songs.assert_called_once()

@allure.epic("GUI Logic")
@allure.suite("Visuals")
class TestVisuals:
    @allure.story("Emoji Mapping")
    def test_emoji_mapping(self, jukebox_gui):
        assert jukebox_gui.emoji_for(['rock']) == '🤘'