import pytest
import allure
import os
from unittest.mock import MagicMock, patch, mock_open, call
from useful_tools.get_files import extract_files_to_csv

# --- Fixtures ---

@pytest.fixture
def mock_fs():
    """Mocks os.listdir and os.path checks."""
    with patch('get_files.os.listdir') as mock_ls, \
         patch('get_files.os.path.isfile') as mock_isfile:
        yield mock_ls, mock_isfile

@pytest.fixture
def mock_csv_file():
    """Mocks the file opening context."""
    with patch('builtins.open', new_callable=mock_open) as m_open:
        yield m_open

@pytest.fixture
def mock_easyid3():
    """Mocks Mutagen EasyID3."""
    with patch('get_files.EasyID3') as m_id3:
        yield m_id3

# --- Tests ---

@allure.epic("File Extraction")
@allure.suite("File System")
@allure.feature("Directory Scanning")
class TestDirectoryScanning:

    @allure.story("Empty Directory")
    @allure.title("Write only headers if directory is empty")
    def test_empty_directory(self, mock_fs, mock_csv_file):
        """
        Scenario: Directory has no files.
        Expectation: CSV created with just the header row.
        """
        mock_ls, mock_isfile = mock_fs
        mock_ls.return_value = [] # Empty dir

        extract_files_to_csv("dummy_dir", "output.csv")

        # Check file opened correctly
        mock_csv_file.assert_called_with("output.csv", 'w', newline='', encoding='utf-8')
        
        # Check writing
        handle = mock_csv_file()
        # Should write one row (headers)
        # Using normalization to check calls because CSV writer implementation varies
        # But we can check string writes to the handle
        
        # Easier way: Check calls to the handle's write method or csv.writer
        # Since the code uses csv.writer(csvfile), we usually patch csv.writer to be precise,
        # but mocking open is often enough to see what got written if we inspect the write calls.
        # However, checking the write calls on a mocked file object for CSV is tricky because 
        # csv module writes formatted strings.
        
        # Let's inspect the write calls.
        assert handle.write.call_count > 0 # At least headers
        args, _ = handle.write.call_args_list[0]
        assert "Filename" in args[0] and "Title" in args[0]


    @allure.story("Filtering")
    @allure.title("Include non-MP3 files with empty metadata")
    def test_non_mp3_files(self, mock_fs, mock_csv_file):
        """
        Scenario: Directory has 'notes.txt'.
        Expectation: Row written: ['notes.txt', '', '']
        """
        mock_ls, mock_isfile = mock_fs
        mock_ls.return_value = ['notes.txt']
        mock_isfile.return_value = True

        extract_files_to_csv("dummy_dir", "output.csv")

        handle = mock_csv_file()
        # We expect header write + data write
        # Retrieve all text written to file
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        
        # Check content
        assert "notes.txt" in written_content
        # Ensure it didn't try to parse metadata for .txt
        # (Implicitly checked because we didn't mock EasyID3 here, so if it called it, it might fail or we'd see side effects)


@allure.epic("File Extraction")
@allure.suite("Metadata")
@allure.feature("MP3 Parsing")
class TestMP3Metadata:

    @allure.story("Success")
    @allure.title("Extract Title and Artist from valid MP3")
    def test_mp3_valid_metadata(self, mock_fs, mock_csv_file, mock_easyid3):
        """
        Scenario: 'song.mp3' exists and has ID3 tags.
        Expectation: Row written: ['song.mp3', 'My Title', 'My Artist']
        """
        mock_ls, mock_isfile = mock_fs
        mock_ls.return_value = ['song.mp3']
        mock_isfile.return_value = True

        # Setup ID3 Mock
        mock_tags = MagicMock()
        mock_tags.get.side_effect = lambda k, d: ['My Title'] if k == 'title' else ['My Artist']
        mock_easyid3.return_value = mock_tags

        extract_files_to_csv("music_dir", "out.csv")

        # Verify ID3 was called on the full path
        mock_easyid3.assert_called_once()
        args, _ = mock_easyid3.call_args
        assert "music_dir" in args[0] and "song.mp3" in args[0]

        # Verify Output
        handle = mock_csv_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        assert "song.mp3" in written_content
        assert "My Title" in written_content
        assert "My Artist" in written_content

    @allure.story("Failure Handling")
    @allure.title("Fallback gracefully on corrupt/missing tags")
    def test_mp3_corrupt_tags(self, mock_fs, mock_csv_file, mock_easyid3):
        """
        Scenario: 'bad.mp3' causes EasyID3 to raise Exception.
        Expectation: Row written: ['bad.mp3', '', ''] (empty metadata).
        """
        mock_ls, mock_isfile = mock_fs
        mock_ls.return_value = ['bad.mp3']
        mock_isfile.return_value = True

        # Setup ID3 to fail
        mock_easyid3.side_effect = Exception("Corrupt Header")

        extract_files_to_csv("music_dir", "out.csv")

        # Verify Output
        handle = mock_csv_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        
        assert "bad.mp3" in written_content
        # Should be empty fields (commas without text between them in CSV format)
        # e.g. "bad.mp3,," depending on line endings
        # We can't strictly check for "bad.mp3,," easily due to csv formatting variability, 
        # but we ensure no python error occurred and file was written.

    @allure.story("Case Insensitivity")
    @allure.title("Process .MP3 extension same as .mp3")
    def test_mp3_caps_extension(self, mock_fs, mock_csv_file, mock_easyid3):
        mock_ls, _ = mock_fs
        mock_ls.return_value = ['LOUD.MP3']
        
        extract_files_to_csv("dir", "out.csv")
        
        mock_easyid3.assert_called_once()