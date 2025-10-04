import os
import re
import csv
import json
import unicodedata
import requests
from mutagen.easyid3 import EasyID3
from rapidfuzz import fuzz

# --- CONFIGURATION ---

# Public Google Sheet ID and GID (tab ID)
SHEET_ID = '12qeqYJKwox0EVfomHB7aYhKE03nqjY5II6asQkAWmTY'
GID = '0'  # Usually 0 for the first sheet

# Sheet columns (0-based): 0 = first column, 1 = second column
# Per request: column 1 = Song (Title), column 2 = Artist
SONG_COL_INDEX = 1
ARTIST_COL_INDEX = 2

MP3_DIR = './mp3'

# Output files
MATCHED_JSON = 'matched_songs.json'   # simple array of best-match filenames
MATCH_RATIO_JSON = 'match_ratio.json' # detailed match info per row

# --- HELPERS ---

SEP_PAT = re.compile(r'\s*[-–—|:]\s*', re.UNICODE)

def normalize(s: str) -> str:
    """Lowercase, strip accents, remove extra punctuation/whitespace, collapse features."""
    if not s:
        return ''
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower().strip()

    # remove common noise like brackets, feat., ft., prod., remaster notes, etc.
    s = re.sub(r'\((?:feat\.?|ft\.?|with|prod\.?|remaster(?:ed)?|live|edit|version|mix)[^)]*\)', '', s)
    s = re.sub(r'\[(?:feat\.?|ft\.?|with|prod\.?|remaster(?:ed)?|live|edit|version|mix)[^\]]*\]', '', s)
    s = re.sub(r'\b(feat\.?|ft\.?|with|prod\.?|remaster(?:ed)?|live|edit|version|mix)\b', '', s)
    s = re.sub(r'\s+', ' ', s)
    s = s.strip('-–—|:; ')
    return s.strip()

def score_pair(q_artist, q_title, m_artist, m_title):
    """
    Weighted blend of multiple fuzz metrics.
    If artist missing in the query, rely more on title and a full-string comparison.
    """
    # Title scores
    title_scores = [
        fuzz.token_set_ratio(q_title, m_title),
        fuzz.partial_ratio(q_title, m_title),
        fuzz.ratio(q_title, m_title),
    ]
    title_score = 0.55 * title_scores[0] + 0.30 * title_scores[1] + 0.15 * title_scores[2]

    if q_artist:
        artist_scores = [
            fuzz.token_set_ratio(q_artist, m_artist),
            fuzz.partial_ratio(q_artist, m_artist),
            fuzz.ratio(q_artist, m_artist),
        ]
        artist_score = 0.55 * artist_scores[0] + 0.30 * artist_scores[1] + 0.15 * artist_scores[2]
        combined = 0.6 * title_score + 0.4 * artist_score
        return combined
    else:
        q_full = normalize(q_title)
        m_full = normalize((m_artist + ' - ' + m_title).strip(' -'))
        full_scores = [
            fuzz.token_set_ratio(q_full, m_full),
            fuzz.partial_ratio(q_full, m_full),
            fuzz.ratio(q_full, m_full),
        ]
        full_score = 0.55 * full_scores[0] + 0.30 * full_scores[1] + 0.15 * full_scores[2]
        return 0.7 * title_score + 0.3 * full_score

def safe_read_easyid3(file_path):
    """Read EasyID3 safely; fall back to filename parsing."""
    try:
        audio = EasyID3(file_path)
        title = audio.get('title', [''])[0]
        artist = audio.get('artist', [''])[0]
    except Exception:
        title = ''
        artist = ''

    # Fall back to filename if necessary
    if not (artist and title):
        base = os.path.splitext(os.path.basename(file_path))[0]
        # Try to split "Artist - Title" from filename if present
        parts = SEP_PAT.split(base, maxsplit=1)
        if len(parts) == 2:
            f_artist, f_title = parts
        else:
            f_artist, f_title = '', base
        artist = artist or f_artist
        title = title or f_title

    return normalize(artist), normalize(title)

# --- FETCH SHEET DATA VIA CSV EXPORT ---

csv_url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}'
resp = requests.get(csv_url)
resp.raise_for_status()

rows = list(csv.reader(resp.text.splitlines()))
# Skip header row; keep original row number for reporting (Google Sheets rows are 1-indexed)
data_rows = rows[1:]

# Build (artist, title) queries from two columns
queries = []
for r in data_rows:
    song = r[SONG_COL_INDEX].strip() if len(r) > SONG_COL_INDEX else ''
    artist = r[ARTIST_COL_INDEX].strip() if len(r) > ARTIST_COL_INDEX else ''
    # Normalize but keep raw too for reporting if needed
    q_title = normalize(song)
    q_artist = normalize(artist)
    if q_title or q_artist:
        queries.append((q_artist, q_title))  # (artist, title)

# --- READ MP3 METADATA ---

if not os.path.isdir(MP3_DIR):
    raise FileNotFoundError(f"MP3 directory not found: {MP3_DIR}")

mp3_files = [f for f in os.listdir(MP3_DIR) if f.lower().endswith('.mp3')]

metadata_list = []
for f in mp3_files:
    fpath = os.path.join(MP3_DIR, f)
    m_artist, m_title = safe_read_easyid3(fpath)
    metadata_list.append({
        'filename': f,
        'artist': m_artist,
        'title': m_title
    })

# --- MATCHING ---

matched_filenames = []  # for matched_songs.json (strings only)
match_ratio = []        # for match_ratio.json (detailed)

for idx, (q_artist, q_title) in enumerate(queries):
    sheet_row_number = idx + 2  # account for header row at 1

    # Score every track
    scored = []
    for m in metadata_list:
        s = score_pair(q_artist, q_title, m['artist'], m['title'])
        scored.append((s, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[0] if scored else (0, None)
    next_best = scored[1] if len(scored) > 1 else (None, None)

    top_score = round(float(top[0]), 2) if top[1] else 0.0
    top_meta = top[1] if top[1] else {'filename': '', 'artist': '', 'title': ''}

    next_score = round(float(next_best[0]), 2) if next_best[1] else None
    next_meta = next_best[1] if next_best[1] else None

    # Append just the filename (string) to matched_songs.json output
    if top_meta.get('filename'):
        matched_filenames.append(top_meta['filename'])

    # Build detailed entry for match_ratio.json
    ratio_obj = {
        "row_number": sheet_row_number,
        "query": {
            "artist": q_artist,
            "title": q_title
        },
        "top_match": {
            "filename": top_meta.get('filename', ''),
            "artist": top_meta.get('artist', ''),
            "title": top_meta.get('title', ''),
            "match_percent": top_score
        }
    }
    if top_score < 99 and next_meta:
        ratio_obj["next_best"] = {
            "filename": next_meta.get('filename', ''),
            "artist": next_meta.get('artist', ''),
            "title": next_meta.get('title', ''),
            "match_percent": next_score
        }

    match_ratio.append(ratio_obj)

# --- OUTPUT JSON ---

with open(MATCHED_JSON, 'w', encoding='utf-8') as f:
    json.dump(matched_filenames, f, indent=4, ensure_ascii=False)

with open(MATCH_RATIO_JSON, 'w', encoding='utf-8') as f:
    json.dump(match_ratio, f, indent=4, ensure_ascii=False)

print(f"✅ JSON written to {MATCHED_JSON} and {MATCH_RATIO_JSON}")
