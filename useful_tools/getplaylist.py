import os
import csv
import json
import requests
from mutagen.easyid3 import EasyID3
from rapidfuzz import fuzz

# --- CONFIGURATION ---

# Public Google Sheet ID and GID (tab ID)
SHEET_ID = '12qeqYJKwox0EVfomHB7aYhKE03nqjY5II6asQkAWmTY'
GID = '0'  # Usually 0 for the first sheet
COLUMN_INDEX = 1  # Which column to use (0 = first column)
MP3_DIR = '../mp3'

# --- FETCH SHEET DATA VIA CSV EXPORT ---

csv_url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}'
response = requests.get(csv_url)
response.raise_for_status()  # Raise an error if the sheet isn't accessible

rows = list(csv.reader(response.text.splitlines()))
queries = [row[COLUMN_INDEX] for row in rows[1:] if len(row) > COLUMN_INDEX]  # Skip header row

# --- READ MP3 METADATA ---

def get_mp3_metadata(file_path):
    try:
        audio = EasyID3(file_path)
        title = audio.get('title', [''])[0]
        artist = audio.get('artist', [''])[0]
        return f"{artist} - {title}".strip()
    except Exception:
        return ""

mp3_files = [f for f in os.listdir(MP3_DIR) if f.lower().endswith('.mp3')]
mp3_metadata = {f: get_mp3_metadata(os.path.join(MP3_DIR, f)) for f in mp3_files}

# --- MATCHING ---

def find_best_match(query, metadata_dict):
    best_score = 0
    best_file = None
    for filename, metadata in metadata_dict.items():
        score = fuzz.ratio(query.lower(), metadata.lower())
        if score > best_score:
            best_score = score
            best_file = filename
    return best_file

matched_files = []

for query in queries:
    match = find_best_match(query, mp3_metadata)
    if match:
        matched_files.append(match)

# --- OUTPUT JSON ---

with open('matched_songs.json', 'w') as f:
    json.dump(matched_files, f, indent=4)

print("✅ JSON written to matched_songs.json")
