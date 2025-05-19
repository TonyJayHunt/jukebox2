import pytest
from useful_tools.update_genre_file import clean_genre

def test_clean_genre_basic():
    s = "Pop, Rock / Dance|Electro and Disco"
    assert clean_genre(s) == "Pop;Rock;Dance;Electro;Disco"

def test_clean_genre_with_refs():
    s = "Rock [citation needed], Blues [1] / Funk"
    assert clean_genre(s) == "Rock;Blues;Funk"

def test_clean_genre_duplicates():
    s = "Pop, Pop / Pop"
    assert clean_genre(s) == "Pop"
