import os
import csv
import sys
import requests
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError, APIC, error

# Path to the directory containing your MP3 files
MP3_DIRECTORY = './mp3/'

# Path to your CSV file
CSV_FILE = './songs_genres.csv'

def sanitize_filename(name):
    # Function to sanitize song names to match filenames
    # Retain alphanumeric characters, spaces, underscores, hyphens, ampersands, and commas
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-&,().'!")
    return ''.join(c for c in name if c in allowed_chars).rstrip()

def update_genre_and_art(mp3_path, genre):
    try:
        audio = EasyID3(mp3_path)
    except ID3NoHeaderError:
        audio = EasyID3()
        audio.save(mp3_path)

    audio['genre'] = genre
    audio.save(mp3_path)
    print(f"Updated genre for: {os.path.basename(mp3_path)} to '{genre}'")

    # Fetch and add album art
    add_album_art(mp3_path)

def wipe_tags(mp3_path):
    try:
        audio = ID3(mp3_path)
    except ID3NoHeaderError:
        # If there's no ID3 tag, nothing to remove
        print(f"No ID3 tag found in: {os.path.basename(mp3_path)}")
        return

    # Remove genre and comments
    tags_to_remove = ['TCON', 'COMM']
    for tag in tags_to_remove:
        if tag in audio:
            del audio[tag]
            print(f"Removed {tag} tag from: {os.path.basename(mp3_path)}")

    audio.save(mp3_path)

def find_mp3_file(song_name):
    sanitized_name = sanitize_filename(song_name).lower()
    for root, dirs, files in os.walk(MP3_DIRECTORY):
        for file in files:
            if file.lower().endswith('.mp3'):
                filename_without_ext = os.path.splitext(file)[0].lower()
                if sanitized_name == filename_without_ext:
                    return os.path.join(root, file)
    return None

def wipe_all_tags():
    for root, dirs, files in os.walk(MP3_DIRECTORY):
        for file in files:
            if file.lower().endswith('.mp3'):
                mp3_path = os.path.join(root, file)
                wipe_tags(mp3_path)

def fetch_album_art(song_name, artist_name=None):
    # Use MusicBrainz API to fetch album art
    base_url = 'https://musicbrainz.org/ws/2/recording/'
    headers = {'User-Agent': 'YourAppName/1.0 (your-email@example.com)'}
    params = {
        'query': f'"{song_name}"',
        'fmt': 'json',
        'limit': 1
    }
    if artist_name:
        params['query'] += f' AND artist:"{artist_name}"'

    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if data['recordings']:
            recording = data['recordings'][0]
            # Get the release ID
            if 'releases' in recording and recording['releases']:
                release_id = recording['releases'][0]['id']
                # Fetch cover art from Cover Art Archive
                cover_art_url = f'http://coverartarchive.org/release/{release_id}/front'
                return cover_art_url
            else:
                print(f"No releases found for: {song_name}")
        else:
            print(f"No recordings found for: {song_name}")
    except Exception as e:
        print(f"Error fetching album art for {song_name}: {e}")
    return None

def add_album_art(mp3_path):
    song_name = os.path.splitext(os.path.basename(mp3_path))[0]
    # Optional: Extract artist name if your filename includes it, e.g., 'Artist - Song Title'
    if ' - ' in song_name:
        artist_name, song_title = song_name.split(' - ', 1)
    else:
        artist_name, song_title = None, song_name

    artwork_url = fetch_album_art(song_title, artist_name)
    if artwork_url:
        try:
            response = requests.get(artwork_url)
            if response.status_code == 200:
                img_data = response.content

                audio = ID3(mp3_path)
                # Remove existing album art if any
                audio.delall('APIC')
                audio.add(APIC(
                    encoding=3,  # 3 is for UTF-8
                    mime='image/jpeg',  # or 'image/png'
                    type=3,  # 3 is for the cover(front) image
                    desc='Cover',
                    data=img_data
                ))
                audio.save(mp3_path)
                print(f"Added album art to: {os.path.basename(mp3_path)}")
            else:
                print(f"No album art found at URL: {artwork_url}")
        except Exception as e:
            print(f"Error adding album art to {os.path.basename(mp3_path)}: {e}")
    else:
        print(f"No album art added for: {os.path.basename(mp3_path)}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'wipe':
        wipe_all_tags()
    else:
        with open(CSV_FILE, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                song_name = row[0].strip()
                genre = row[1].strip()
                mp3_file = find_mp3_file(song_name)
                if mp3_file:
                    update_genre_and_art(mp3_file, genre)
                else:
                    print(f"MP3 file not found for song: {song_name}")

if __name__ == '__main__':
    main()
