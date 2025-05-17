import os
import pytest
import song_library

def test_is_abba_song():
    song = {'artist': 'ABBA'}
    not_abba = {'artist': 'Queen'}
    assert song_library.is_abba_song(song) is True
    assert song_library.is_abba_song(not_abba) is False

def test_extract_album_art_none():
    class DummyTag:
        def __init__(self, FrameID): self.FrameID = FrameID
        data = b'data'
    tags = {'x': DummyTag('NOTAPIC')}
    assert song_library._extract_album_art(tags) is None

def test_extract_album_art_found():
    class DummyTag:
        FrameID = 'APIC'
        data = b'img'
    tags = {'apic': DummyTag()}
    assert song_library._extract_album_art(tags) == b'img'
