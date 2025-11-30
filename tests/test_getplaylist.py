import sys
import json
from unittest.mock import MagicMock, patch, mock_open

# --- PRE-IMPORT SETUP ---
# We must mock external dependencies BEFORE importing 'getplaylist',
# otherwise the script will execute immediately and try to hit real APIs/files.

# 1. Mock Requests (Google Sheets)
mock_response = MagicMock()
# Simulate a CSV with Header + 2 data rows
mock_response.text = "Header,Song,Artist\n1,Wonderwall,Oasis\n2,Song 2,Blur"
mock_response.raise_for_status = MagicMock()

patcher_requests = patch('requests.get', return_value=mock_response)
patcher_requests.start()

# 2. Mock OS (File System)
patcher_isdir = patch('os.path.isdir', return_value=True) # Pretend ./mp3 exists
patcher_isdir.start()

patcher_listdir = patch('os.listdir', return_value=['Oasis - Wonderwall.mp3', 'Blur - Song 2.mp3'])
patcher_listdir.start()

# 3. Mock File Writing (Prevent creating JSON files)
patcher_open = patch('builtins.open', new_callable=mock_open)
mock_file_open = patcher_open.start()

# 4. Mock Mutagen (Metadata) - We patch the EasyID3 class import inside the module logic
# Since we haven't imported the module yet, we patch where it WILL be looking or sys.modules
# But easier: we let it fail or use a simple mock if the script allows. 
# The script imports EasyID3. We can mock it in sys.modules.
mock_mutagen = MagicMock()
sys.modules['mutagen'] = mock_mutagen
sys.modules['mutagen.easyid3'] = mock_mutagen

# Now we can safely import the script. 
# It will run its "main" logic against our mocks immediately.
import useful_tools.getplaylist as getplaylist
import pytest
import allure

# --- HELPERS FOR TESTS ---
# Since the script ran on import, 'getplaylist' now contains the functions we want to test.

@allure.epic("Playlist Sync")
@allure.suite("Data Cleaning")
@allure.feature("Normalization")
class TestNormalization:

    @allure.story("Cleanup")
    @allure.title("Remove feats, parens, and accents")
    @pytest.mark.parametrize("input_str, expected", [
        ("Oasis (Remastered 2009)", "oasis"),
        ("Jay-Z feat. Alicia Keys", "jay-z"),
        ("Beyoncé", "beyonce"),
        ("Linkin Park [Live]", "linkin park"),
        ("   MESSY   String   ", "messy string"),
        ("Artist - Title", "artist - title"),
    ])
    def test_normalize_logic(self, input_str, expected):
        """Verify the normalize function cleans strings as expected."""
        assert getplaylist.normalize(input_str) == expected

    @allure.story("Edge Cases")
    @allure.title("Handle empty or None inputs")
    def test_normalize_empty(self):
        assert getplaylist.normalize(None) == ""
        assert getplaylist.normalize("") == ""


@allure.epic("Playlist Sync")
@allure.suite("Matching Logic")
@allure.feature("Fuzzy Scoring")
class TestScoring:

    @allure.story("Perfect Matches")
    @allure.title("High score for identical pairs")
    def test_perfect_match(self):
        # Using real matching logic from the script
        score = getplaylist.score_pair(
            "oasis", "wonderwall", 
            "oasis", "wonderwall"
        )
        assert score >= 90  # Should be very high

    @allure.story("Partial Matches")
    @allure.title("Good score for partial matches")
    def test_partial_match(self):
        score = getplaylist.score_pair(
            "oasis", "wonderwall", 
            "oasis", "wonderwall (remastered)"
        )
        assert score > 80

    @allure.story("Missing Artist")
    @allure.title("Fallback logic when query artist is missing")
    def test_missing_query_artist(self):
        """
        Scenario: Sheet has no artist, just title.
        Logic should compare Title vs (Artist - Title) filename fallback.
        """
        score = getplaylist.score_pair(
            "", "wonderwall", 
            "oasis", "wonderwall"
        )
        # It shouldn't be zero, it should try to match title against the full string
        assert score > 50

    @allure.story("Mismatch")
    @allure.title("Low score for different songs")
    def test_mismatch(self):
        score = getplaylist.score_pair(
            "blur", "song 2", 
            "oasis", "wonderwall"
        )
        assert score < 50


@allure.epic("Playlist Sync")
@allure.suite("File System")
@allure.feature("Metadata Extraction")
class TestMetadataReader:

    @allure.story("EasyID3 Success")
    @allure.title("Read tags from file")
    def test_safe_read_tags(self):
        """
        We need to patch EasyID3 strictly for this function call 
        to simulate a valid ID3 tag response.
        """
        with patch('getplaylist.EasyID3') as MockID3:
            # Setup a mock tag dictionary
            mock_tags = MagicMock()
            mock_tags.get.side_effect = lambda k, d: [['Test Artist']] if k == 'artist' else [['Test Title']]
            MockID3.return_value = mock_tags

            artist, title = getplaylist.safe_read_easyid3("dummy.mp3")
            
            # The function normalizes the output
            assert artist == "test artist"
            assert title == "test title"

    @allure.story("Fallback")
    @allure.title("Parse filename if ID3 fails")
    def test_safe_read_fallback(self):
        """
        Scenario: EasyID3 raises exception.
        Expectation: Parse 'Artist - Title.mp3' from filename.
        """
        with patch('getplaylist.EasyID3', side_effect=Exception("No tags")):
            # Path ending in filename
            path = "/music/Abba - Dancing Queen.mp3"
            
            artist, title = getplaylist.safe_read_easyid3(path)
            
            assert artist == "abba"
            assert title == "dancing queen"


@allure.epic("Playlist Sync")
@allure.suite("Integration")
@allure.feature("Script Execution")
class TestScriptWorkflow:

    @allure.story("Output Generation")
    @allure.title("Verify JSON files were written")
    def test_output_written(self):
        """
        Since importing the module executed the main loop, 
        we check if the mocked 'open' was called to write the JSONs.
        """
        # The script writes MATCHED_JSON and MATCH_RATIO_JSON
        # We expect calls to open(..., 'w', ...)
        
        # Filter calls for write mode
        write_calls = [
            call for call in mock_file_open.call_args_list 
            if call[0][0] in ['matched_songs.json', 'match_ratio.json']
        ]
        
        assert len(write_calls) >= 2, "Should attempt to write both JSON files"