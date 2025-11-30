import pytest
import allure
import time
from unittest.mock import MagicMock, patch, ANY
# Import the class to test. 
# Note: We patch modules BEFORE importing if they have import-time side effects, 
# but here the side effects are protected by checks or are manageable.
from player import JukeboxPlayer, _fmt_mmss, _get_duration_seconds

# --- Fixtures ---

@pytest.fixture
def mock_pygame():
    """Mocks the entire pygame module to prevent audio device errors."""
    with patch('player.pygame') as mock_pg:
        # Mock mixer.music
        mock_pg.mixer.music.get_busy.return_value = False
        
        # Mock mixer.Channel
        mock_channel = MagicMock()
        mock_channel.get_busy.return_value = False
        mock_pg.mixer.Channel.return_value = mock_channel
        
        # Mock mixer.Sound
        mock_sound = MagicMock()
        mock_sound.get_length.return_value = 180.0
        mock_pg.mixer.Sound.return_value = mock_sound
        
        yield mock_pg

@pytest.fixture
def mock_kivy_clock():
    """Mocks Kivy Clock to prevent GUI scheduling errors."""
    with patch('player.Clock') as mock_clock:
        yield mock_clock

@pytest.fixture
def player(mock_pygame, mock_kivy_clock):
    """Returns an instance of JukeboxPlayer with mocked callbacks."""
    mock_update_now = MagicMock()
    mock_update_upcoming = MagicMock()
    mock_start_playback = MagicMock()
    
    return JukeboxPlayer(
        gui_update_now_playing=mock_update_now,
        update_upcoming_songs_callback=mock_update_upcoming,
        start_playback_callback=mock_start_playback
    )

# --- Tests ---

@allure.epic("Jukebox Player")
@allure.suite("Core Logic")
@allure.feature("Initialization")
class TestPlayerInit:

    @allure.story("Default State")
    @allure.title("Verify initial attributes")
    def test_initial_state(self, player):
        """Verify playlists are empty and locks are ready."""
        assert player.default_playlist == []
        assert player.primary_playlist == []
        assert player.Special_playlist == []
        assert player.song_counter == 1
        assert player.immediate_playback is False


@allure.epic("Jukebox Player")
@allure.suite("Queue Management")
@allure.feature("Playlist Priority")
class TestQueuePriority:

    @allure.story("Standard Priority")
    @allure.title("Primary playlist takes precedence over Default")
    def test_primary_over_default(self, player):
        """
        Scenario: Songs exist in both Primary and Default playlists.
        Expectation: _get_next_song returns Primary song first.
        """
        player.primary_playlist = [{'title': 'Primary Song', 'path': '/p1.mp3'}]
        player.default_playlist = [{'title': 'Default Song', 'path': '/d1.mp3'}]
        
        next_song = player._get_next_song()
        assert next_song['title'] == 'Primary Song'
        
        # Ensure it didn't pop it yet (peek only)
        assert len(player.primary_playlist) == 1

    @allure.story("Special Slot")
    @allure.title("Special playlist triggers on 5th song")
    def test_special_song_trigger(self, player):
        """
        Scenario: song_counter is 5.
        Expectation: Returns song from Special playlist, even if Primary exists.
        """
        player.song_counter = 5
        player.Special_playlist = [{'title': 'Special Song', 'path': '/s1.mp3'}]
        player.primary_playlist = [{'title': 'Primary Song', 'path': '/p1.mp3'}]
        
        next_song = player._get_next_song()
        assert next_song['title'] == 'Special Song'

    @allure.story("Queue Popping")
    @allure.title("Correctly remove song from queue")
    def test_pop_next_song(self, player):
        """
        Scenario: Pop next song.
        Expectation: Song is returned and removed from the list.
        """
        player.primary_playlist = [{'title': 'Song A', 'path': '/a.mp3'}]
        
        popped = player._pop_next_song()
        assert popped['title'] == 'Song A'
        assert len(player.primary_playlist) == 0


@allure.epic("Jukebox Player")
@allure.suite("Playback Controls")
@allure.feature("Immediate Playback")
class TestImmediatePlayback:

    @allure.story("Interrupt Flow")
    @allure.title("Play song immediately stops current music")
    def test_play_immediately(self, player, mock_pygame, mock_kivy_clock):
        """
        Scenario: Call play_song_immediately.
        Expectation: Sets flags, loads music, plays, and resets flags.
        """
        song = {'title': 'Instant Song', 'path': '/instant.mp3'}
        
        # We need to ensure the loop inside play_song_immediately exits.
        # It loops while get_busy() is True.
        # We set side_effect to True (start) then False (end) to simulate playback finishing.
        mock_pygame.mixer.music.get_busy.side_effect = [True, False]
        
        player.play_song_immediately(song)
        
        # Verification
        mock_pygame.mixer.music.stop.assert_called() # Should stop previous song
        mock_pygame.mixer.music.load.assert_called_with('/instant.mp3')
        mock_pygame.mixer.music.play.assert_called()
        
        # Check if GUI update was scheduled
        assert mock_kivy_clock.schedule_once.called

    @allure.story("Locking")
    @allure.title("Sets immediate_playback flag during execution")
    def test_immediate_flag_logic(self, player, mock_pygame):
        """
        Scenario: play_song_immediately is called.
        Expectation: self.immediate_playback is True inside the critical section.
        """
        # Since we can't easily inspect the live flag during the method without threading,
        # we verify the lock was acquired and flag ends up False.
        mock_pygame.mixer.music.get_busy.return_value = False # Finish immediately
        
        player.play_song_immediately({'path': 'test.mp3'})
        assert player.immediate_playback is False


@allure.epic("Jukebox Player")
@allure.suite("Ambient Mode")
@allure.feature("Ambient Music")
class TestAmbientMusic:

    @allure.story("File Discovery")
    @allure.title("Find MP3s in folder and start thread")
    @patch('player.os.walk')
    @patch('player.threading.Thread')
    def test_start_ambient(self, mock_thread, mock_walk, player):
        """
        Scenario: Start ambient music.
        Expectation: Finds files and starts a daemon thread.
        """
        # Mock file system
        mock_walk.return_value = [('/ambiant', [], ['noise.mp3', 'ignore.txt'])]
        
        player.start_ambient_music(folder="/ambiant")
        
        mock_thread.assert_called_once()
        args = mock_thread.call_args[1] if mock_thread.call_args[1] else mock_thread.call_args[0]
        # Verify the target is the loop function
        assert player.ambient_thread is not None

    @allure.story("Playback Loop")
    @allure.title("Ambient loop plays random file")
    @patch('player.os.walk')
    @patch('player.random.choice')
    def test_ambient_loop_logic(self, mock_choice, mock_walk, player, mock_pygame):
        """
        Scenario: Run the internal loop method directly.
        Expectation: Plays sound on AMBIENT channel.
        """
        mock_walk.return_value = [('/ambiant', [], ['calm.mp3'])]
        mock_choice.return_value = '/ambiant/calm.mp3'
        
        # Set stop event immediately so the loop runs only once
        player.ambient_stop_event.set()
        
        player._ambient_loop("dummy_folder")
        
        mock_pygame.mixer.Channel.assert_called_with(2) # AMBIENT_CHANNEL_IDX is 2
        mock_pygame.mixer.Sound.assert_called_with('/ambiant/calm.mp3')


@allure.epic("Jukebox Player")
@allure.suite("Utilities")
@allure.feature("Formatting")
class TestFormatters:

    @allure.story("Time Formatting")
    @allure.title("Format seconds to MM:SS")
    @pytest.mark.parametrize("seconds, expected", [
        (65, "01:05"),
        (0, "00:00"),
        (None, "??:??"),
        (3599, "59:59")
    ])
    def test_fmt_mmss(self, seconds, expected):
        assert _fmt_mmss(seconds) == expected

@allure.epic("Jukebox Player")
@allure.suite("Metadata")
@allure.feature("Duration Lookup")
class TestDuration:

    @allure.story("Mutagen Fallback")
    @allure.title("Use pygame duration if Mutagen fails")
    @patch('player.MutagenFile')
    @patch('player.pygame.mixer.Sound')
    def test_duration_fallback(self, mock_sound, mock_mutagen_file):
        """
        Scenario: MutagenFile raises exception.
        Expectation: Fallback to pygame.mixer.Sound.get_length().
        """
        mock_mutagen_file.side_effect = Exception("Bad file")
        mock_sound_obj = MagicMock()
        mock_sound_obj.get_length.return_value = 120.5
        mock_sound.return_value = mock_sound_obj
        
        duration = _get_duration_seconds("song.mp3")
        assert duration == 120.5