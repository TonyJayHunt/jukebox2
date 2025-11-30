import pytest
import allure
import pandas as pd
from unittest.mock import MagicMock, patch
from useful_tools.update_genre_file import clean_genre, fetch_genre, fill_missing_genres, process_file
import wikipedia

# --- Fixtures ---

@pytest.fixture
def mock_wiki_page():
    """Returns a mock object mimicking a wikipedia.WikipediaPage."""
    mock_page = MagicMock()
    # Default HTML with a clear Genre infobox
    mock_page.html.return_value = """
    <html>
        <table class="infobox">
            <tr><th>Origin</th><td>London</td></tr>
            <tr><th>Genre</th><td>Britpop, Rock</td></tr>
            <tr><th>Label</th><td>EMI</td></tr>
        </table>
    </html>
    """
    return mock_page

# --- Tests ---

@allure.epic("Metadata Enrichment")
@allure.suite("Data Cleaning")
@allure.feature("String Normalization")
class TestCleanGenre:

    @allure.story("Separators")
    @allure.title("Split on commas, pipes, slashes, and 'and'")
    @pytest.mark.parametrize("raw_input, expected", [
        ("Rock / Pop", "Rock;Pop"),
        ("Jazz, Blues", "Jazz;Blues"),
        ("Techno | House", "Techno;House"),
        ("R&B and Soul", "R&B;Soul"),
    ])
    def test_separators(self, raw_input, expected):
        """Verify various delimiters are normalized to semicolons."""
        assert clean_genre(raw_input) == expected

    @allure.story("Noise Removal")
    @allure.title("Remove citation brackets and whitespace")
    def test_remove_citations(self):
        raw = "Indie Rock[1][citation needed], Lo-fi[2]"
        expected = "Indie Rock;Lo-Fi"
        assert clean_genre(raw) == expected

    @allure.story("Deduplication")
    @allure.title("Remove duplicate genres while preserving order")
    def test_deduplication(self):
        raw = "Pop, Rock, Pop, Dance"
        expected = "Pop;Rock;Dance"
        assert clean_genre(raw) == expected

    @allure.story("Edge Cases")
    @allure.title("Handle empty or non-string inputs")
    def test_bad_input(self):
        assert clean_genre(None) == ""
        assert clean_genre("") == ""
        assert clean_genre(123) == ""


@allure.epic("Metadata Enrichment")
@allure.suite("Wikipedia Integration")
@allure.feature("Genre Fetching")
class TestFetchGenre:

    @allure.story("Success Path")
    @allure.title("Parse genre from Infobox")
    @patch('update_genre_file.wikipedia.page')
    def test_fetch_success(self, mock_page_func, mock_wiki_page):
        """
        Scenario: Wikipedia page exists and has a 'Genre' row in the infobox.
        Expectation: Returns cleaned genre string.
        """
        mock_page_func.return_value = mock_wiki_page
        
        result = fetch_genre("Blur Band")
        
        assert result == "Britpop;Rock"
        mock_page_func.assert_called_with("Blur Band", auto_suggest=True, redirect=True)

    @allure.story("Missing Data")
    @allure.title("Return None if 'Genre' th is missing")
    @patch('update_genre_file.wikipedia.page')
    def test_no_genre_in_infobox(self, mock_page_func):
        """
        Scenario: Page exists, but infobox has no 'Genre' field.
        Expectation: Returns None.
        """
        mock_page = MagicMock()
        mock_page.html.return_value = "<html><table><tr><th>Name</th><td>Bob</td></tr></table></html>"
        mock_page_func.return_value = mock_page
        
        assert fetch_genre("Bob") is None

    @allure.story("API Errors")
    @allure.title("Handle PageError and DisambiguationError")
    @patch('update_genre_file.wikipedia.page')
    def test_wiki_errors(self, mock_page_func):
        """
        Scenario: Wikipedia raises an error (page not found or ambiguous).
        Expectation: Returns None gracefully.
        """
        # Test PageError
        mock_page_func.side_effect = wikipedia.PageError("pageid")
        assert fetch_genre("UnknownThing") is None
        
        # Test DisambiguationError
        mock_page_func.side_effect = wikipedia.DisambiguationError("Title", ["Option1", "Option2"])
        assert fetch_genre("AmbiguousThing") is None


@allure.epic("Metadata Enrichment")
@allure.suite("Data Processing")
@allure.feature("DataFrame Updates")
class TestFillMissingGenres:

    @allure.story("Iterative Update")
    @allure.title("Only fill missing rows")
    @patch('update_genre_file.fetch_genre')
    @patch('update_genre_file.time.sleep') # Mock sleep to speed up test
    def test_fill_logic(self, mock_sleep, mock_fetch):
        """
        Scenario: DataFrame has 3 rows: one with genre, two without.
        Expectation: fetch_genre called only for rows with NaN genres.
        """
        # Setup Data
        data = {
            'Search_Query': ['Oasis', 'Beatles', 'Blur'],
            'Genre': ['Britpop', None, None],
            'Title': ['Wonderwall', 'Hey Jude', 'Song 2']
        }
        df = pd.DataFrame(data)

        # Mock responses for the 2 missing calls
        mock_fetch.side_effect = ["Rock", None] # Beatles -> Rock, Blur -> None (failed fetch)

        # Run function
        result_df = fill_missing_genres(df, verbose=False, sleep_time=0)

        # Verification
        assert result_df.at[0, 'Genre'] == "Britpop" # Untouched
        assert result_df.at[1, 'Genre'] == "Rock"    # Filled
        assert pd.isna(result_df.at[2, 'Genre'])     # Still NaN (fetch failed)

        # Ensure fetch was only called twice (for Beatles and Blur)
        assert mock_fetch.call_count == 2
        mock_fetch.assert_any_call('Beatles')
        mock_fetch.assert_any_call('Blur')


@allure.epic("Metadata Enrichment")
@allure.suite("Workflow")
@allure.feature("File I/O")
class TestProcessFile:

    @allure.story("End-to-End")
    @allure.title("Read CSV, process, and write CSV")
    @patch('update_genre_file.pd.read_csv')
    @patch('update_genre_file.fill_missing_genres')
    def test_process_file_flow(self, mock_fill, mock_read):
        """
        Scenario: process_file is called.
        Expectation: Reads input, calls filler, writes to output.
        """
        # Mock DataFrame
        mock_df = MagicMock()
        mock_read.return_value = mock_df
        mock_fill.return_value = mock_df # Return the same mock after processing

        process_file("input.csv", "output.csv")

        mock_read.assert_called_once_with("input.csv")
        mock_fill.assert_called_once_with(mock_df)
        mock_df.to_csv.assert_called_once_with("output.csv", index=False)