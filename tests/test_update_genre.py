import useful_tools.update_genre as update_genre
import pytest

def test_sanitize_filename():
    raw = "Hello! Song #1 (feat. O'Neill)&"
    sanitized = update_genre.sanitize_filename(raw)
    assert "#" not in sanitized
    assert "!" in sanitized
    assert "&" in sanitized
    assert "(" in sanitized and ")" in sanitized

def test_find_mp3_file(tmp_path, monkeypatch):
    # Setup dummy directory and file
    d = tmp_path / "mp3"
    d.mkdir()
    f = d / "My Song.mp3"
    f.write_text("dummy")
    monkeypatch.setattr(update_genre, "MP3_DIRECTORY", str(d))
    name = "My Song"
    found = update_genre.find_mp3_file(name)
    assert found is not None and found.endswith("My Song.mp3")
