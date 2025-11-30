import pytest
import allure
import os
from unittest.mock import MagicMock, patch, call

# Import the module to test
import useful_tools.download_playlist_mp3 as downloader

# --- Fixtures ---

@pytest.fixture
def mock_yt_dlp():
    """Mocks the YoutubeDL context manager and extract_info."""
    with patch('download_playlist_mp3.yt_dlp.YoutubeDL') as mock_ydl_cls:
        mock_instance = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_mutagen():
    """Mocks EasyID3 for tagging."""
    with patch('download_playlist_mp3.EasyID3') as mock_id3:
        # Create a dict-like mock object for audio tags
        mock_audio = MagicMock()
        mock_id3.return_value = mock_audio
        yield mock_id3

@pytest.fixture
def mock_requests():
    """Mocks requests for MusicBrainz lookups."""
    with patch('download_playlist_mp3.requests.get') as mock_get:
        yield mock_get

@pytest.fixture
def mock_fs():
    """Mocks file system checks."""
    with patch('download_playlist_mp3.os.path.exists') as m_exists, \
         patch('download_playlist_mp3.os.listdir') as m_listdir:
        yield m_exists, m_listdir

# --- Tests ---

@allure.epic("Downloader")
@allure.suite("String Processing")
@allure.feature("Title Sanitization")
class TestSanitization:

    @allure.story("Suffix Removal")
    @allure.title("Remove video suffixes (Official Video, etc)")
    @pytest.mark.parametrize("raw, expected", [
        ("Song Name (Official Video)", "Song Name"),
        ("Track [4k Remaster]", "Track"),
        ("Cool Song (Official Music Video)", "Cool Song"),
        ("Clean Track (Clean Version)", "Clean Track"),
        ("  Messy Title  (Stereo)  ", "Messy Title"),
    ])
    def test_clean_suffixes(self, raw, expected):
        assert downloader.sanitize_title(raw) == expected

    @allure.story("Formatting")
    @allure.title("Ensure Title Case and strip separators")
    def test_formatting(self, raw="artist - title_"):
        # "Artist - Title" (Title case)
        assert downloader.sanitize_title("my song -") == "My Song"
        assert downloader.sanitize_title("LOUD NOISES") == "Loud Noises"


@allure.epic("Downloader")
@allure.suite("String Processing")
@allure.feature("Artist Parsing")
class TestArtistParsing:

    @allure.story("Separation")
    @allure.title("Split Artist - Title correctly")
    def test_split_artist(self):
        artist, title = downloader.parse_artist_title("Queen - Bohemian Rhapsody")
        assert artist == "Queen"
        assert title == "Bohemian Rhapsody"

    @allure.story("Fallback")
    @allure.title("Return None for artist if separator missing")
    def test_no_separator(self):
        artist, title = downloader.parse_artist_title("Just A Song Title")
        assert artist is None
        assert title == "Just A Song Title"


@allure.epic("Downloader")
@allure.suite("Metadata")
@allure.feature("Genre Lookup")
class TestMusicBrainz:

    @allure.story("Success")
    @allure.title("Extract genre from valid MB response")
    def test_mb_lookup_success(self, mock_requests):
        """
        Scenario: MusicBrainz returns valid JSON with tags.
        Expectation: Returns the most frequent tag.
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'recordings': [{
                'tags': [
                    {'name': 'rock', 'count': 100},
                    {'name': 'pop', 'count': 5}
                ]
            }]
        }
        mock_requests.return_value = mock_resp

        genre = downloader.get_genre_from_musicbrainz("Band", "Song")
        assert genre == "Rock"

    @allure.story("Failure")
    @allure.title("Fallback to 'Wedding' on failure")
    def test_mb_lookup_fail(self, mock_requests):
        mock_requests.side_effect = Exception("Network Down")
        genre = downloader.get_genre_from_musicbrainz("Band", "Song")
        assert genre == "Wedding"


@allure.epic("Downloader")
@allure.suite("File Operations")
@allure.feature("Tagging")
class TestTagging:

    @allure.story("ID3 Writes")
    @allure.title("Apply metadata to MP3 file")
    def test_tag_mp3(self, mock_mutagen):
        """
        Scenario: tag_mp3 called with info.
        Expectation: EasyID3 opened, fields set, saved.
        """
        mock_audio = mock_mutagen.return_value
        
        downloader.tag_mp3("test.mp3", "Artist", "Title", "Genre")
        
        assert mock_audio['artist'] == "Artist"
        assert mock_audio['title'] == "Title"
        assert mock_audio['genre'] == "Genre"
        assert mock_audio['album'] == "Nicki & Tony's Wedding"
        mock_audio.save.assert_called_once()

    @allure.story("Error Handling")
    @allure.title("Handle corrupt MP3 gracefully")
    def test_tag_mp3_error(self, mock_mutagen):
        mock_mutagen.side_effect = Exception("Corrupt")
        # Should simply print error and return, not crash
        downloader.tag_mp3("bad.mp3", "A", "T", "G")


@allure.epic("Downloader")
@allure.suite("Workflow")
@allure.feature("Download Loop")
class TestDownloadWorkflow:

    @allure.story("Processing")
    @allure.title("Process playlist entries and tag files")
    @patch('download_playlist_mp3.tag_mp3')
    def test_workflow_success(self, mock_tag_func, mock_yt_dlp, mock_fs):
        """
        Scenario: 1 item in playlist. File exists (simulated download).
        Expectation: Sanitization -> File Check -> Tagging.
        """
        mock_exists, mock_listdir = mock_fs
        
        # 1. Setup YoutubeDL mock data
        mock_yt_dlp.extract_info.return_value = {
            'entries': [{
                'title': 'The Beatles - Hey Jude (Official Video)',
                'uploader': 'TheBeatlesVEVO'
            }]
        }
        
        # 2. Simulate that the file "downloaded" successfully (exists on disk)
        # The script checks: os.path.exists("The Beatles - Hey Jude.mp3")
        mock_exists.return_value = True 
        
        # 3. Run
        downloader.download_and_set_tags("http://playlist.url")
        
        # 4. Verification
        # Should sanitize "The Beatles - Hey Jude (Official Video)" -> "The Beatles - Hey Jude"
        # Should parse Artist="The Beatles", Title="Hey Jude"
        mock_tag_func.assert_called_once()
        args = mock_tag_func.call_args[0]
        
        # args: filename, artist, title, genre
        assert "The Beatles - Hey Jude.mp3" in args[0]
        assert args[1] == "The Beatles"
        assert args[2] == "Hey Jude"
        # Genre fallback logic in script relies on hardcoded checks or MB
        assert args[3] in ["Christmas", "Wedding", "Unknown"]

    @allure.story("Fallback Logic")
    @allure.title("Find partial match if exact filename missing")
    @patch('download_playlist_mp3.tag_mp3')
    def test_fuzzy_file_match(self, mock_tag_func, mock_yt_dlp, mock_fs):
        """
        Scenario: yt-dlp saves 'Song.mp3', but sanitization expects 'Song Name.mp3'.
        Expectation: Script iterates listdir to find 'Song.mp3' via partial match.
        """
        mock_exists, mock_listdir = mock_fs
        
        # Title that cleans to "My Song"
        mock_yt_dlp.extract_info.return_value = {'entries': [{'title': 'My Song'}]}
        
        # Exact match fails
        mock_exists.return_value = False
        
        # listdir returns a file that looks similar (case insensitive, no spaces)
        mock_listdir.return_value = ["mysong.mp3", "other.mp3"]
        
        downloader.download_and_set_tags("url")
        
        # Should find "mysong.mp3" and tag it
        mock_tag_func.assert_called()
        assert "mysong.mp3" in mock_tag_func.call_args[0][0]