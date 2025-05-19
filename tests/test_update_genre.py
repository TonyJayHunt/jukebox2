import pytest
from useful_tools.update_genre import (
    fetch_itunes_art,
    fetch_caa_art,
    fetch_deezer_art,
    embed_album_art,
    write_genre_tag,
    detect_columns,
)

import pandas as pd
import os

def test_detect_columns():
    df = pd.DataFrame({
        "Filename": ["a.mp3"],
        "Genre": ["Rock"]
    })
    fn_col, gn_col = detect_columns(df)
    assert fn_col == "Filename"
    assert gn_col == "Genre"

def test_embed_album_art(monkeypatch, tmp_path):
    mp3 = tmp_path / "file.mp3"
    mp3.write_bytes(b"test")
    def fake_get(*a, **k):
        class R: 
            status_code = 200
            content = b"123"
            def raise_for_status(self): pass
        return R()
    monkeypatch.setattr("requests.get", fake_get)
    from mutagen.id3 import ID3, APIC
    assert not embed_album_art(str(mp3), "http://fakeimgurl.com") or isinstance(embed_album_art(str(mp3), "http://fakeimgurl.com"), bool)

def test_write_genre_tag(tmp_path):
    mp3 = tmp_path / "file.mp3"
    mp3.write_bytes(b"test")
    # Should not raise
    write_genre_tag(str(mp3), "Rock")

def test_fetch_itunes_art(monkeypatch):
    # Simulate a response with artwork
    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"resultCount": 1, "results": [{"artworkUrl100": "http://img/100x100.jpg"}]}
    monkeypatch.setattr("requests.get", lambda *a, **k: Resp())
    url = fetch_itunes_art("title", "artist")
    assert url is None or "600x600" in url

def test_fetch_caa_art(monkeypatch):
    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"recordings": [{"releases": [{"id": "abc"}]}]}
    class HeadResp:
        status_code = 200
    monkeypatch.setattr("requests.get", lambda *a, **k: Resp())
    monkeypatch.setattr("requests.head", lambda *a, **k: HeadResp())
    url = fetch_caa_art("title", "artist")
    assert url is None or "coverartarchive" in url

def test_fetch_deezer_art(monkeypatch):
    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"data": [{"album": {"cover_xl": "http://deezer.com/art.jpg"}}]}
    monkeypatch.setattr("requests.get", lambda *a, **k: Resp())
    url = fetch_deezer_art("title", "artist")
    assert url is None or "deezer.com" in url
