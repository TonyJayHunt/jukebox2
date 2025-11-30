import pytest
import allure
from unittest.mock import MagicMock, patch
from song_library import get_all_mp3_files_with_metadata, is_abba_song, _extract_album_art

# --- Fixtures for Mocking Mutagen/ID3 ---

@pytest.fixture
def mock_id3_tags():
    """
    Creates a mock ID3 object that behaves like a dictionary.
    We need to mock .get() methods and .values() for the art extractor.
    """
    mock_tags = MagicMock()
    
    def get_side_effect(key, default=None):
        # Create a mock object that has a .text attribute (list)
        # similar to how mutagen tags work (e.g., TIT2.text[0])
        val_mock = MagicMock()
        if key == 'TIT2':
            val_mock.text = ['Dancing Queen']
        elif key == 'TPE1':
            val_mock.text = ['ABBA']
        elif key == 'TCON':
            val_mock.text = ['Pop;Disco']
        else:
            return default
        return val_mock

    mock_tags.get.side_effect = get_side_effect
    
    # Mock .values() for _extract_album_art iteration
    # We'll default to no art usually, or set it specifically in tests
    mock_tags.values.return_value = []
    
    return mock_tags


@allure.epic("Song Library Management")
@allure.suite("Helper Logic")
@allure.feature("Artist Verification")
class TestIsAbbaSong:

    @allure.story("Positive Matching")
    @allure.title("Detect ABBA in artist list (Case Insensitive)")
    @pytest.mark.parametrize("artists_list", [
        ['ABBA'],
        ['abba'],
        ['Queen', 'Abba'],
        ['Bjorn', 'Benny', 'ABBA']
    ])
    def test_is_abba_true(self, artists_list):
        """Verify returns True if ABBA is present in any casing."""
        song = {'artists': artists_list}
        assert is_abba_song(song) is True

    @allure.story("Negative Matching")
    @allure.title("Return False when ABBA is absent")
    @pytest.mark.parametrize("artists_list", [
        ['Queen'],
        ['Black Sabbath'],
        [],
        ['AbbaCoverBand'] # Partial match shouldn't trigger exact match logic
    ])
    def test_is_abba_false(self, artists_list):
        """Verify returns False if ABBA is not strictly in the list."""
        song = {'artists': artists_list}
        assert is_abba_song(song) is False


@allure.epic("Song Library Management")
@allure.suite("Metadata Extraction")
@allure.feature("Album Art Extraction")
class TestAlbumArtExtraction:

    @allure.story("Art Exists")
    @allure.title("Extract APIC frame data when present")
    def test_extract_art_success(self):
        """Verify that binary data is returned if an APIC frame exists."""
        # Create a mock tag specifically for APIC
        mock_apic = MagicMock()
        mock_apic.FrameID = 'APIC'
        mock_apic.data = b'\x89PNG\r\n...'
        
        # Create a mock tag that is NOT APIC (noise)
        mock_other = MagicMock()
        mock_other.FrameID = 'TIT2'

        # Mock the dictionary .values() iterator
        mock_tags = MagicMock()
        mock_tags.values.return_value = [mock_other, mock_apic]

        result = _extract_album_art(mock_tags)
        assert result == b'\x89PNG\r\n...'

    @allure.story("No Art")
    @allure.title("Return None when no APIC frame exists")
    def test_extract_art_none(self):
        """Verify returns None if no tags have FrameID == 'APIC'."""
        mock_other = MagicMock()
        mock_other.FrameID = 'TIT2'
        
        mock_tags = MagicMock()
        mock_tags.values.return_value = [mock_other]

        result = _extract_album_art(mock_tags)
        assert result is None


@allure.epic("Song Library Management")
@allure.suite("File System Scanning")
@allure.feature("MP3 Discovery & Parsing")
class TestGetMp3Files:

    @allure.story("File Filtering")
    @allure.title("Ignore non-MP3 files")
    @patch('song_library.os.walk')
    def test_ignores_non_mp3(self, mock_walk):
        """
        Scenario: Directory contains .txt and .jpg files.
        Expectation: Result list should be empty.
        """
        # Mock directory structure: root, folders, files
        mock_walk.return_value = [
            ('/music', [], ['lyrics.txt', 'cover.jpg', 'notes.doc'])
        ]
        
        results = get_all_mp3_files_with_metadata('/music')
        assert len(results) == 0

    @allure.story("Valid MP3 Parsing")
    @allure.title("Parse metadata from valid MP3 file")
    @patch('song_library.ID3')
    @patch('song_library.os.walk')
    def test_valid_mp3_metadata(self, mock_walk, mock_id3_class, mock_id3_tags):
        """
        Scenario: Valid MP3 exists.
        Expectation: ID3 tags are read and structured correctly.
        """
        mock_walk.return_value = [('/music', [], ['song.mp3'])]
        
        # When ID3('path') is called, return our fixture mock
        mock_id3_class.return_value = mock_id3_tags

        results = get_all_mp3_files_with_metadata('/music')
        
        assert len(results) == 1
        song = results[0]
        assert song['title'] == 'Dancing Queen'
        assert song['artists'] == ['ABBA']
        # The fixture sets TCON to 'Pop;Disco', code splits and lowers it:
        assert song['genres'] == ['pop', 'disco'] 
        assert song['path'] == '/music/song.mp3'

    @allure.story("Complex Artists")
    @allure.title("Split multiple artists by separators")
    @patch('song_library.ID3')
    @patch('song_library.os.walk')
    def test_split_artists(self, mock_walk, mock_id3_class):
        """
        Scenario: Artist tag is 'Queen / David Bowie'.
        Expectation: Parsed into ['Queen', 'David Bowie'].
        """
        mock_walk.return_value = [('/music', [], ['under_pressure.mp3'])]
        
        # Custom mock for this specific test
        mock_tags = MagicMock()
        def get_side_effect(key, default=None):
            val_mock = MagicMock()
            if key == 'TPE1':
                val_mock.text = ['Queen / David Bowie'] # The slash separator
            elif key == 'TIT2':
                val_mock.text = ['Under Pressure']
            elif key == 'TCON':
                val_mock.text = ['Rock']
            else:
                return default
            return val_mock
            
        mock_tags.get.side_effect = get_side_effect
        mock_tags.values.return_value = []
        mock_id3_class.return_value = mock_tags

        results = get_all_mp3_files_with_metadata('/music')
        
        assert results[0]['artists'] == ['Queen', 'David Bowie']

    @allure.story("Error Handling")
    @allure.title("Graceful fallback on corrupt metadata")
    @patch('song_library.ID3')
    @patch('song_library.os.walk')
    def test_corrupt_metadata_fallback(self, mock_walk, mock_id3_class):
        """
        Scenario: mutagen raises an exception (e.g., corrupt header).
        Expectation: Fallback to filename as title, 'Unknown Artist', 'unknown genre'.
        """
        mock_walk.return_value = [('/music', [], ['bad_file.mp3'])]
        
        # ID3 instantiation raises Exception
        mock_id3_class.side_effect = Exception("Corrupt ID3 Header")

        results = get_all_mp3_files_with_metadata('/music')
        
        assert len(results) == 1
        song = results[0]
        assert song['title'] == 'bad_file' # Derived from filename
        assert song['artists'] == ['Unknown Artist']
        assert song['genres'] == ['unknown genre']
        assert song['album_art'] is None