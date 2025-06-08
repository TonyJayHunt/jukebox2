import os
import re
from mutagen.id3 import ID3, TIT2, TPE1, TCON, APIC

def get_all_mp3_files_with_metadata(directory):
    """
    Fetches all MP3 files from a directory, extracts their metadata,
    and correctly handles multiple artists in a single tag.
    """
    mp3_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if not file.lower().endswith('.mp3'):
                continue

            full_path = os.path.join(root, file)
            try:
                tags = ID3(full_path)
                title = tags.get('TIT2', TIT2(text=[os.path.splitext(file)[0]])).text[0]
                
                # Handle single or multiple artists (split by common separators)
                artist_str = tags.get('TPE1', TPE1(text=['Unknown Artist'])).text[0]
                artists = [a.strip() for a in re.split(';|,|/', artist_str) if a.strip()]

                genre_str = tags.get('TCON', TCON(text=['Unknown Genre'])).text[0]
                genres = [g.strip().lower() for g in genre_str.split(';')]
                
                album_art_data = _extract_album_art(tags)

            except Exception as e:
                print(f"Metadata error for '{full_path}': {e}")
                title = os.path.splitext(file)[0]
                artists = ['Unknown Artist']
                genres = ['unknown genre']
                album_art_data = None
            
            mp3_files.append({
                'path': full_path,
                'title': title,
                'artists': artists, # Use 'artists' (plural) to store the list
                'genres': genres,
                'album_art': album_art_data
            })
    return mp3_files

def _extract_album_art(tags):
    """Helper to extract album art data (APIC frame) from ID3 tags."""
    return next((tag.data for tag in tags.values() if tag.FrameID == 'APIC'), None)

def is_abba_song(song):
    """Checks if 'ABBA' is one of the artists for the given song."""
    return any(artist.strip().lower() == 'abba' for artist in song.get('artists', []))