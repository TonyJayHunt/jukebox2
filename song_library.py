import os
from mutagen.id3 import ID3, TIT2, TPE1, TCON, APIC

def get_all_mp3_files_with_metadata(directory):
    """Fetches MP3 files and extracts metadata."""

    mp3_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.mp3'):
                full_path = os.path.join(root, file)
                try:
                    tags = ID3(full_path)
                    title = tags.get('TIT2', TIT2(text=[os.path.splitext(file)[0]])).text[0]
                    artist = tags.get('TPE1', TPE1(text=['Unknown Artist'])).text[0]
                    genre_str = tags.get('TCON', TCON(text=['Unknown Genre'])).text[0]
                    genres = [g.strip().lower() for g in genre_str.split(';')]
                    album_art_data = _extract_album_art(tags)
                except Exception as e:
                    print(f"Error reading metadata from '{full_path}': {e}")
                    title = os.path.splitext(file)[0]
                    artist = 'Unknown Artist'
                    genres = ['unknown genre']
                    album_art_data = None
                mp3_files.append({
                    'path': full_path,
                    'title': title,
                    'artist': artist,
                    'genres': genres,
                    'album_art': album_art_data
                })
    return mp3_files

def _extract_album_art(tags):
    """Helper to extract album art data."""
    for tag in tags.values():
        if tag.FrameID == 'APIC':
            return tag.data
    return None

def is_abba_song(song):
    """Checks if the song is by ABBA."""
    return song['artist'].strip().lower() == 'abba'