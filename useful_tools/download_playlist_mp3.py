import yt_dlp
import os
import re
import requests
from mutagen.easyid3 import EasyID3

# Patterns to remove from title
SUFFIXES = [
    r"\(official music video\)", r"\(clean version\)", r"\(official video\)",
    r"\(official hd video\)", r"\(official movie\)", r"\[4k remaster\]", r"\(stereo\)"
]
SUFFIX_RE = re.compile(r"(\s*(" + "|".join(SUFFIXES) + r"))\s*$", re.IGNORECASE)

def sanitize_title(title):
    # Lowercase for matching/removal
    raw_title = title.lower()
    # Remove unwanted suffixes at end (even if surrounded by spaces)
    raw_title = SUFFIX_RE.sub("", raw_title)
    # Remove trailing dashes, underscores, or whitespace
    raw_title = raw_title.strip().rstrip("-–—_").strip()
    # Title case for pretty output
    cleaned_title = raw_title.title()
    return cleaned_title

def parse_artist_title(clean_title):
    # Everything before first "-" is artist, after is title
    if '-' in clean_title:
        artist, title = clean_title.split('-', 1)
        return artist.strip(), title.strip()
    return None, clean_title.strip()

def get_genre_from_musicbrainz(artist, title):
    try:
        print(f"Looking up genre on MusicBrainz for: Artist='{artist}' Title='{title}'")
        query = f'artist:"{artist}" AND recording:"{title}"'
        url = f'https://musicbrainz.org/ws/2/recording/?query={query}&fmt=json'
        headers = {'User-Agent': 'jukebox-app/1.0 (email@example.com)'}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            recs = data.get('recordings', [])
            for rec in recs:
                tags = rec.get('tags')
                if tags:
                    sorted_tags = sorted(tags, key=lambda t: t.get('count', 1), reverse=True)
                    genre = sorted_tags[0]['name'].capitalize()
                    print(f"Found genre: {genre}")
                    return genre
    except Exception as e:
        print(f"MusicBrainz lookup failed: {e}")
    return "Wedding"

def tag_mp3(mp3_filename, artist, title, genre):
    try:
        audio = EasyID3(mp3_filename)
    except Exception as e:
        print(f"Error opening mp3 for tagging: {e}")
        return
    audio['album'] = "Nicki & Tony's Wedding"
    audio['title'] = title
    audio['artist'] = artist
    audio['albumartist'] = artist
    audio['genre'] = genre
    audio.save()
    print(f"Tagged: {mp3_filename}\n  Artist: {artist}\n  Title: {title}\n  Genre: {genre}\n")

def download_and_set_tags(playlist_url, output_dir='./mp3_1'):
    # Use sanitized title for output filename template
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'ignoreerrors': True,
        'noplaylist': False,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
        ],
        'quiet': False,
        'extractaudio': True,
        'nocheckcertificate': True,
        'skip_download': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(playlist_url, download=True)

    entries = info_dict['entries'] if 'entries' in info_dict else [info_dict]

    for entry in entries:
        if entry is None:
            continue
        yt_title = entry.get('title', '')
        uploader = entry.get('uploader', '')

        print(f"\nOriginal title: {yt_title}")

        # Sanitize the title as soon as we get it
        clean_title = sanitize_title(yt_title)
        print(f"Sanitized title: {clean_title}")

        # Find the mp3 using sanitized title as the filename
        mp3_filename = os.path.join(output_dir, f"{clean_title}.mp3")
        if not os.path.exists(mp3_filename):
            # Fallback: try to find a partial match in the output_dir
            for f in os.listdir(output_dir):
                if f.lower().endswith('.mp3') and clean_title.lower().replace(" ", "") in f.lower().replace(" ", ""):
                    mp3_filename = os.path.join(output_dir, f)
                    break
            else:
                print(f"Couldn't find MP3 for '{yt_title}' (sanitized as '{clean_title}'). Skipping.")
                continue

        # Parse artist/title from the sanitized title
        artist, title = parse_artist_title(clean_title)
        if not artist or not title:
            artist = uploader or "Unknown Artist"
            title = clean_title

        # Fetch genre
        genre = "Christmas" # get_genre_from_musicbrainz(artist, title)
        if not genre or genre.lower() == "unknown":
            genre = "Wedding"

        # Set tags immediately after download
        tag_mp3(mp3_filename, artist, title, genre)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python download_playlist_mp3.py <playlist_url> [output_dir]")
        sys.exit(1)
    url = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else './mp3_1'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    download_and_set_tags(url, outdir)
    print(f"All done! MP3 files saved to: {os.path.abspath(outdir)}")
