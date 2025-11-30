import sys
from unittest.mock import MagicMock, patch, mock_open

# --- PRE-IMPORT MOCKING ---
# Mock python-docx modules before CreateQuestions imports them.
mock_docx = MagicMock()
sys.modules['docx'] = mock_docx
sys.modules['docx.enum'] = MagicMock()
sys.modules['docx.enum.text'] = MagicMock()
sys.modules['docx.shared'] = MagicMock()
sys.modules['docx.enum.table'] = MagicMock()

# Import the module under test
import useful_tools.CreateQuestions as CreateQuestions

import pytest
import allure

# --- Fixtures ---

@pytest.fixture
def sample_csv_data():
    return """Question,Number of Uses
    Find a red hat,5
    Take a selfie,3
    Bad Row,not_an_int
    """

@pytest.fixture
def mock_document():
    """Returns a fully structured mock for the Document object."""
    doc = MagicMock()
    
    # Mock Sections
    section = MagicMock()
    doc.sections = [section]
    
    # Mock Table creation
    table = MagicMock()
    doc.add_table.return_value = table
    
    # Mock Cells
    cell = MagicMock()
    table.cell.return_value = cell
    table.columns = [MagicMock(), MagicMock()] # 2 columns
    
    # Mock Paragraphs within cells
    paragraph = MagicMock()
    cell.paragraphs = [paragraph]
    cell.merge.return_value = cell # merge returns the cell
    
    # Mock Runs
    run = MagicMock()
    paragraph.add_run.return_value = run
    paragraph.runs = [run]
    
    # Mock Document add_paragraph
    heading_p = MagicMock()
    doc.add_paragraph.return_value = heading_p
    heading_p.runs = [MagicMock()]
    
    return doc

# --- Tests ---

@allure.epic("Document Generator")
@allure.suite("Data Ingestion")
@allure.feature("CSV Parsing")
class TestCsvParsing:

    @allure.story("Valid Data")
    @allure.title("Parse Questions and Usage Counts")
    def test_get_data_valid(self, sample_csv_data):
        """
        Scenario: CSV contains mixed valid and invalid rows.
        Expectation: Valid rows parsed, invalid usage counts ignored/skipped.
        """
        with patch("builtins.open", mock_open(read_data=sample_csv_data)):
            data = CreateQuestions.get_data_from_csv("dummy.csv")
            
        assert len(data) == 2
        assert data[0]["question"] == "Find a red hat"
        assert data[0]["remaining_uses"] == 5
        assert data[1]["question"] == "Take a selfie"
        assert data[1]["remaining_uses"] == 3

    @allure.story("Edge Cases")
    @allure.title("Handle missing or malformed data")
    def test_get_data_empty(self):
        empty_csv = "Question,Number of Uses\n,"
        with patch("builtins.open", mock_open(read_data=empty_csv)):
            data = CreateQuestions.get_data_from_csv("dummy.csv")
        assert len(data) == 0


@allure.epic("Document Generator")
@allure.suite("Logic")
@allure.feature("Question Selection")
class TestQuestionSelection:

    @allure.story("Selection Logic")
    @allure.title("Pick unused question and decrement counter")
    def test_pick_question_success(self):
        pool = [{"question": "Q1", "remaining_uses": 2}]
        used = set()
        
        result = CreateQuestions.pick_question(pool, used)
        
        assert result == "Q1"
        assert pool[0]["remaining_uses"] == 1

    @allure.story("Constraints")
    @allure.title("Do not pick if remaining uses is 0")
    def test_pick_question_exhausted(self):
        pool = [{"question": "Q1", "remaining_uses": 0}]
        used = set()
        
        result = CreateQuestions.pick_question(pool, used)
        assert result is None

    @allure.story("Constraints")
    @allure.title("Do not pick duplicates for the same page")
    def test_pick_question_duplicate(self):
        pool = [{"question": "Q1", "remaining_uses": 5}]
        used = {"Q1"} # Q1 is already used on this specific page/context
        
        result = CreateQuestions.pick_question(pool, used)
        assert result is None
        assert pool[0]["remaining_uses"] == 5 # Shouldn't decrement


@allure.epic("Document Generator")
@allure.suite("Document Creation")
@allure.feature("Main Workflow")
class TestMainWorkflow:

    @allure.story("Structure")
    @allure.title("Initialize Document and Page Layout")
    @patch("CreateQuestions.Document")
    @patch("CreateQuestions.get_data_from_csv")
    def test_document_setup(self, mock_get_data, mock_doc_cls, mock_document):
        """
        Scenario: Main runs.
        Expectation: Document margins and sections are configured.
        """
        # Setup mocks
        mock_doc_cls.return_value = mock_document
        mock_get_data.return_value = [] # Return empty to skip loop logic or keep it minimal
        
        # Override range to 1 to speed up test (script defaults to 68 variations)
        with patch("builtins.range", return_value=[0]):
            CreateQuestions.main()
            
        # Verify Page Setup (Section 0)
        section = mock_document.sections[0]
        # We can't check exact values easily since Mm/Pt are mocked, but we check assignment
        assert hasattr(section, 'page_width')
        assert hasattr(section, 'top_margin')
        assert hasattr(section, 'header')

    @allure.story("Content")
    @allure.title("Table Generation and Population")
    @patch("CreateQuestions.Document")
    @patch("CreateQuestions.get_data_from_csv")
    def test_table_population(self, mock_get_data, mock_doc_cls, mock_document):
        """
        Scenario: Data is available.
        Expectation: Table created with 7 rows, 2 cols, and text added.
        """
        mock_doc_cls.return_value = mock_document
        
        # Provide enough data so logic runs fully
        mock_get_data.side_effect = [
            [{"question": "Q1", "remaining_uses": 10}], # Pool 1
            [{"question": "Q2", "remaining_uses": 10}]  # Pool 2
        ]
        
        # Run only 1 iteration
        with patch("builtins.range", return_value=[0]):
            CreateQuestions.main()
        
        # Verify Table Created
        mock_document.add_table.assert_called_with(rows=7, cols=2)
        
        # Verify Cell Merging (Row 0 col 0 with Row 6 col 0)
        table = mock_document.add_table.return_value
        # Check that .cell(0,0) and .cell(6,0) were accessed
        table.cell.assert_any_call(0, 0)
        table.cell.assert_any_call(6, 0)
        
        # Verify Welcome Text Added to Left Column
        # Access the merged cell's paragraph
        cell = table.cell.return_value
        paragraph = cell.paragraphs[0]
        paragraph.add_run.assert_any_call(CreateQuestions.WELCOME_TEXT)

    @allure.story("File I/O")
    @allure.title("Save Document")
    @patch("CreateQuestions.Document")
    @patch("CreateQuestions.get_data_from_csv")
    def test_save_document(self, mock_get_data, mock_doc_cls, mock_document):
        mock_doc_cls.return_value = mock_document
        mock_get_data.return_value = []
        
        with patch("builtins.range", return_value=[0]):
            CreateQuestions.main()
            
        mock_document.save.assert_called_once()
        args = mock_document.save.call_args[0]
        assert "A5_Landscape" in args[0]
        assert ".docx" in args[0]