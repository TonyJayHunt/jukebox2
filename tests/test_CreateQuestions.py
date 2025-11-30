import sys
import importlib
from unittest.mock import MagicMock, patch, mock_open
import pytest
import allure

@pytest.fixture(scope="module")
def questions_module():
    mock_docx = MagicMock()
    modules = {
        'docx': mock_docx,
        'docx.enum': MagicMock(),
        'docx.enum.text': MagicMock(),
        'docx.shared': MagicMock(),
        'docx.enum.table': MagicMock()
    }
    with patch.dict(sys.modules, modules):
        if 'CreateQuestions' in sys.modules:
            import useful_tools.CreateQuestions as CreateQuestions
            importlib.reload(CreateQuestions)
        else:
            import useful_tools.CreateQuestions as CreateQuestions
        yield CreateQuestions

@allure.epic("Document Generator")
@allure.suite("Data Ingestion")
class TestCsvParsing:
    @allure.story("Valid Data")
    def test_get_data_valid(self, questions_module):
        csv_data = "Question,Number of Uses\nFind a red hat,5"
        with patch("builtins.open", mock_open(read_data=csv_data)):
            data = questions_module.get_data_from_csv("dummy.csv")
        assert len(data) == 1
        assert data[0]["remaining_uses"] == 5

@allure.epic("Document Generator")
@allure.suite("Logic")
class TestQuestionSelection:
    @allure.story("Selection Logic")
    def test_pick_question_success(self, questions_module):
        pool = [{"question": "Q1", "remaining_uses": 2}]
        used = set()
        result = questions_module.pick_question(pool, used)
        assert result == "Q1"
        assert pool[0]["remaining_uses"] == 1