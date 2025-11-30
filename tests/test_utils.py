import pytest
import allure
from utils import normalize_genre, _index_after_last_user_pick

@allure.epic("Core Utilities")
@allure.suite("Data Normalization")
@allure.feature("Genre Normalization")
class TestGenreNormalization:

    @allure.story("Standard Mappings")
    @allure.title("Map known genres to canonical categories")
    @pytest.mark.parametrize("input_genre, expected_genre", [
        ("britpop", "Britpop"),
        ("country", "Country"),
        ("dance", "Dance"),
        ("disco", "Dance"),
        ("edm", "Dance"),
        ("funk", "Hip-Hop"),
        ("hip-hop", "Hip-Hop"),
        ("rap", "Hip-Hop"),
        ("folk", "Indie"),
        ("punk", "Rock"),
        ("alternative rock", "Rock"),
    ])
    def test_standard_genre_mappings(self, input_genre, expected_genre):
        """Verify that standard genres map to their defined main categories."""
        with allure.step(f"Normalizing genre '{input_genre}'"):
            result = normalize_genre(input_genre)
        
        with allure.step(f"Checking if result is '{expected_genre}'"):
            assert result == expected_genre

    @allure.story("String Sanitization")
    @allure.title("Handle whitespace and casing")
    @pytest.mark.parametrize("dirty_input, expected", [
        ("  rock  ", "Rock"),
        ("RoCk", "Rock"),
        ("  HIP-HOP", "Hip-Hop"),
        ("K-POP  ", "Pop"),
    ])
    def test_genre_sanitization(self, dirty_input, expected):
        """Verify that input is trimmed and lowercased before mapping."""
        assert normalize_genre(dirty_input) == expected

    @allure.story("Edge Cases & Defaults")
    @allure.title("Unknown genres default to Pop")
    def test_unknown_genre_defaults_to_pop(self):
        """Verify that any genre not in the mapping returns 'Pop'."""
        unknown_genre = "psychedelic-trance-fusion"
        assert normalize_genre(unknown_genre) == "Pop"

    @allure.story("Alias Handling")
    @allure.title("Map specific aliases like x-mas and alt rock")
    @pytest.mark.parametrize("alias, expected", [
        ("x-mas", "Christmas"),
        ("alt rock", "Rock"),
        ("hip hop", "Hip-Hop"), 
    ])
    def test_genre_aliases(self, alias, expected):
        """Verify that specific shorthand aliases map correctly."""
        assert normalize_genre(alias) == expected


@allure.epic("Core Utilities")
@allure.suite("Playlist Logic")
@allure.feature("Playlist Indexing")
class TestPlaylistIndexing:

    @allure.story("Mixed Content")
    @allure.title("Find index when user picks are at the start")
    def test_mixed_playlist_start(self):
        """
        Scenario: User picks are at the top, followed by bot picks.
        Expectation: Returns the index of the first non-user item.
        """
        playlist = [
            {'source': 'user', 'track': 'A'},
            {'source': 'user', 'track': 'B'},
            {'source': 'bot', 'track': 'C'},
            {'source': 'recommendation', 'track': 'D'}
        ]
        
        index = _index_after_last_user_pick(playlist)
        assert index == 2, "Should return index 2 (first non-user item)"

    @allure.story("User Picks Only")
    @allure.title("Return list length when all items are user picks")
    def test_all_user_picks(self):
        """
        Scenario: All items in playlist are from 'user'.
        Expectation: Returns length of playlist (append to end).
        """
        playlist = [
            {'source': 'user', 'track': 'A'},
            {'source': 'user', 'track': 'B'}
        ]
        
        index = _index_after_last_user_pick(playlist)
        assert index == 2, "Should return len(playlist) if all are user picks"

    @allure.story("No User Picks")
    @allure.title("Return 0 when no user picks exist")
    def test_no_user_picks(self):
        """
        Scenario: First item is not from user.
        Expectation: Returns 0 (insert at start).
        """
        playlist = [
            {'source': 'bot', 'track': 'A'},
            {'source': 'user', 'track': 'B'} # Logic stops at first non-user
        ]
        
        index = _index_after_last_user_pick(playlist)
        assert index == 0, "Should return 0 if first item is not user"

    @allure.story("Empty Playlist")
    @allure.title("Handle empty playlist gracefully")
    def test_empty_playlist(self):
        """
        Scenario: Playlist is empty.
        Expectation: Returns 0.
        """
        playlist = []
        index = _index_after_last_user_pick(playlist)
        assert index == 0, "Empty playlist should return index 0"

    @allure.story("Data Integrity")
    @allure.title("Handle missing source keys safely")
    def test_missing_source_key(self):
        """
        Scenario: Items might lack the 'source' key.
        Expectation: .get() returns None, which != 'user', so it treats as non-user.
        """
        playlist = [
            {'source': 'user', 'track': 'A'},
            {'track': 'B'}, # Missing source
            {'source': 'user', 'track': 'C'}
        ]
        
        index = _index_after_last_user_pick(playlist)
        assert index == 1, "Missing source should be treated as non-user pick"
