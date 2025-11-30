import pytest
import allure
import pandas as pd
from unittest.mock import MagicMock, patch, mock_open
import requests
from mutagen.id3 import ID3NoHeaderError

# Import the module to test
import useful_tools.update_genre as update_genre

# --- Fixtures ---

@pytest.fixture
def mock_requests():
    with patch('update_genre.requests') as mock_req:
        yield mock_req

@pytest.fixture
def mock_id3():
    with patch('update_genre.ID3') as mock_id3_cls:
        # Create a mock instance that ID3() returns
        mock_audio = MagicMock()
        mock_id3_cls.return_value = mock_audio
        yield mock_id3_cls

# --- Tests ---

@allure.epic("MP3 Tagger")
@allure.suite("Artwork Providers")
@allure.feature("iTunes Search")
class TestItunesProvider:

    @allure.story("Success")
    @allure.title("Parse iTunes JSON response correctly")
    def test_itunes_found(self, mock_requests):
        """
        Scenario: iTunes API returns a result with artwork.
        Expectation: Returns high-res (600x600) URL.
        """
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "resultCount": 1,
            "results": [{"artworkUrl100": "http://example.com/100x100.jpg"}]
        }
        mock_requests.get.return_value = mock_resp

        url = update_genre.fetch_itunes_art("Song Title", "Artist")

        assert url == "http://example.com/600x600.jpg"
        mock_requests.get.assert_called_once()
        # Verify params
        args, kwargs = mock_requests.get.call_args
        assert kwargs['params']['term'] == "Artist Song Title"

    @allure.story("Failure")
    @allure.title("Return None on empty results or error")
    def test_itunes_not_found(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"resultCount": 0, "results": []}
        mock_requests.get.return_value = mock_resp

        assert update_genre.fetch_itunes_art("Unknown") is None


@allure.epic("MP3 Tagger")
@allure.suite("Artwork Providers")
@allure.feature("MusicBrainz / CAA")
class TestCAAProvider:

    @allure.story("Success")
    @allure.title("Navigate MBID -> Release -> Cover Art")
    def test_caa_flow(self, mock_requests):
        """
        Scenario: MB search finds recording -> release. CAA has image.
        Expectation: Returns CAA URL.
        """
        # 1. Search response
        mock_mb_resp = MagicMock()
        mock_mb_resp.json.return_value = {
            "recordings": [{
                "releases": [{"id": "rel-123"}]
            }]
        }
        
        # 2. Head check response (CAA existence check)
        mock_head_resp = MagicMock()
        mock_head_resp.status_code = 200

        # Configure side_effect for different URLs
        def side_effect(url, **kwargs):
            if "musicbrainz" in url:
                return mock_mb_resp
            if "coverartarchive" in url:
                return mock_head_resp
            return MagicMock()

        mock_requests.get.side_effect = side_effect
        mock_requests.head.return_value = mock_head_resp

        url = update_genre.fetch_caa_art("Song", "Artist")
        
        assert "rel-123" in url
        assert "front-500" in url

    @allure.story("Failure")
    @allure.title("Handle missing release ID")
    def test_caa_no_release(self, mock_requests):
        mock_mb_resp = MagicMock()
        # Recording exists but has no releases info
        mock_mb_resp.json.return_value = {"recordings": [{"title": "Song"}]}
        mock_requests.get.return_value = mock_mb_resp

        assert update_genre.fetch_caa_art("Song") is None


@allure.epic("MP3 Tagger")
@allure.suite("File Operations")
@allure.feature("Tag Embedding")
class TestEmbedding:

    @allure.story("Genre Tagging")
    @allure.title("Write TCON frame to ID3")
    def test_write_genre(self, mock_id3):
        """
        Scenario: write_genre_tag called.
        Expectation: TCON frame added and saved.
        """
        mock_audio = mock_id3.return_value
        
        update_genre.write_genre_tag("song.mp3", "Pop")
        
        # Verify cleaning old tags
        mock_audio.delall.assert_called_with("TCON")
        # Verify adding new tag
        assert mock_audio.add.called
        # Verify save
        mock_audio.save.assert_called_with("song.mp3")

    @allure.story("Genre Tagging")
    @allure.title("Handle ID3NoHeaderError (create new tags)")
    def test_write_genre_no_header(self, mock_id3):
        """
        Scenario: File has no ID3 tags yet.
        Expectation: ID3() constructor fails, so it instantiates empty ID3(), adds tag, saves.
        """
        # First call raises error, Second call (empty constructor) returns mock
        mock_audio = MagicMock()
        mock_id3.side_effect = [ID3NoHeaderError("No tags"), mock_audio]
        
        update_genre.write_genre_tag("clean.mp3", "Rock")
        
        mock_audio.add.assert_called()
        mock_audio.save.assert_called_with("clean.mp3")

    @allure.story("Album Art")
    @allure.title("Download and embed APIC frame")
    def test_embed_art_success(self, mock_requests, mock_id3):
        """
        Scenario: Image URL is valid.
        Expectation: Download image -> Embed APIC -> Save.
        """
        # Mock Image Download
        mock_img_resp = MagicMock()
        mock_img_resp.content = b"fake_image_data"
        mock_requests.get.return_value = mock_img_resp
        
        success = update_genre.embed_album_art("song.mp3", "http://art.jpg")
        
        assert success is True
        mock_audio = mock_id3.return_value
        mock_audio.delall.assert_called_with("APIC")
        mock_audio.add.assert_called()


@allure.epic("MP3 Tagger")
@allure.suite("Batch Processing")
@allure.feature("CSV Logic")
class TestCSVProcessing:

    @allure.story("Validation")
    @allure.title("Detect required columns case-insensitively")
    def test_detect_columns(self):
        df = pd.DataFrame(columns=["File Name", "Genre"])
        fn, gn = update_genre.detect_columns(df)
        assert fn == "File Name"
        assert gn == "Genre"

    @allure.story("Validation")
    @allure.title("Raise error if columns missing")
    def test_detect_columns_fail(self):
        df = pd.DataFrame(columns=["Name", "Age"]) # No 'genre' or 'file'
        with pytest.raises(ValueError):
            update_genre.detect_columns(df)

    @allure.story("Workflow")
    @allure.title("Process Loop ignores missing files")
    @patch('update_genre.os.path.isfile')
    @patch('update_genre.pd.read_csv')
    def test_process_skip_missing(self, mock_read_csv, mock_isfile):
        """
        Scenario: CSV has 1 row, but file does not exist on disk.
        Expectation: Skips processing for that row.
        """
        mock_df = pd.DataFrame([{"filename": "missing.mp3", "genre": "Pop"}])
        mock_read_csv.return_value = mock_df
        mock_isfile.return_value = False # File missing
        
        # We patch write_genre_tag to ensure it's NOT called
        with patch('update_genre.write_genre_tag') as mock_write:
            update_genre.process_csv("list.csv", "mp3_dir")
            mock_write.assert_not_called()

    @allure.story("Workflow")
    @allure.title("Provider Chain Fallback")
    @patch('update_genre.provider_chain')
    @patch('update_genre.embed_album_art')
    @patch('update_genre.write_genre_tag')
    @patch('update_genre.pd.read_csv')
    @patch('update_genre.os.path.isfile', return_value=True)
    def test_provider_fallback(self, mock_isfile, mock_read, mock_write_tag, mock_embed, mock_providers):
        """
        Scenario: 1st provider fails (returns None), 2nd succeeds.
        Expectation: Loop breaks after 2nd provider.
        """
        # Setup Data
        mock_read.return_value = pd.DataFrame([{"filename": "song.mp3", "genre": "Pop"}])
        
        # Setup Providers
        prov1 = MagicMock(return_value=None)      # Fails
        prov2 = MagicMock(return_value="url2")    # Succeeds
        prov3 = MagicMock(return_value="url3")    # Should not be called
        mock_providers.return_value = [prov1, prov2, prov3]
        
        mock_embed.return_value = True # Embedding succeeds
        
        # Run
        with patch('update_genre.time.sleep'): # Skip sleep
            update_genre.process_csv("dummy.csv", "mp3")
        
        # Verify
        prov1.assert_called()
        prov2.assert_called()
        prov3.assert_not_called() # Should break early
        mock_embed.assert_called_with(pytest.any, "url2")