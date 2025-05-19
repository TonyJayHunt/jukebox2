import pytest
import pandas as pd
from useful_tools.update_genre_file import clean_genre, fill_missing_genres

def test_clean_genre_basic():
    s = "Pop, Rock / Dance|Electro and Disco"
    assert clean_genre(s) == "Pop;Rock;Dance;Electro;Disco"

def test_clean_genre_with_refs():
    s = "Rock [citation needed], Blues [1] / Funk"
    assert clean_genre(s) == "Rock;Blues;Funk"

def test_clean_genre_duplicates():
    s = "Pop, Pop / Pop"
    assert clean_genre(s) == "Pop"

def test_fill_missing_genres(monkeypatch):
    # Create a dummy dataframe with missing genre
    df = pd.DataFrame({
        "Title": ["Test Song"],
        "Search_Query": ["Adele (singer)"],
        "Genre": [None]
    })
    # Patch fetch_genre to always return "Soul;Pop"
    monkeypatch.setattr("useful_tools.update_genre_file.fetch_genre", lambda q: "Soul;Pop")
    df2 = fill_missing_genres(df.copy(), verbose=False, sleep_time=0)
    assert df2.loc[0, "Genre"] == "Soul;Pop"
