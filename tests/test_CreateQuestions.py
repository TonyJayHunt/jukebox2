import io
import csv
import tempfile
import pytest
import useful_tools.CreateQuestions as CreateQuestions

def test_get_data_from_csv(tmp_path):
    # Create a CSV file with 2 questions
    content = "Question,Number of Uses\nQ1,2\nQ2,1\n"
    csvfile = tmp_path / "q.csv"
    csvfile.write_text(content)
    data = CreateQuestions.get_data_from_csv(str(csvfile))
    assert len(data) == 2
    assert data[0]["question"] == "Q1"
    assert data[0]["remaining_uses"] == 2

def test_pick_question_decrements_and_avoids_used():
    pool = [
        {"question": "A", "remaining_uses": 1},
        {"question": "B", "remaining_uses": 2},
    ]
    used = {"A"}
    q = CreateQuestions.pick_question(pool, used)
    assert q == "B"
    assert pool[1]["remaining_uses"] == 1

def test_pick_question_none_left():
    pool = [{"question": "A", "remaining_uses": 0}]
    assert CreateQuestions.pick_question(pool, set()) is None
