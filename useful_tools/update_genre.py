from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Callable, Optional, Sequence

import pandas as pd
import requests
from mutagen.id3 import APIC, ID3, ID3NoHeaderError, TCON

###############################################################################
# Configuration
###############################################################################

FILENAME_HEADERS = {"filename", "file_name", "file", "track", "song"}
GENRE_HEADERS = {"genre", "style"}
DEFAULT_CSV = "file_list_updated_with_genre.csv"
DEFAULT_DIR = "mp3_1"

REQUEST_DELAY = 0.2  # seconds between external requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}

###############################################################################
# Artwork provider functions – each returns a URL or None
###############################################################################

def fetch_itunes_art(title: str, artist: Optional[str] = None) -> Optional[str]:
    query = f"{artist} {title}" if artist else title
    try:
        resp = requests.get(
            "https://itunes.apple.com/search",
            params={"term": query, "media": "music", "limit": 1},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("resultCount"):
            return data["results"][0]["artworkUrl100"].replace("100x100", "600x600")
    except Exception as exc:
        print(f"[iTunes] {exc}")
    return None


def fetch_caa_art(title: str, artist: Optional[str] = None) -> Optional[str]:
    query = f"{artist} {title}" if artist else title
    try:
        mb = requests.get(
            "https://musicbrainz.org/ws/2/recording/",
            params={"query": query, "limit": 1, "fmt": "json"},
            headers=HEADERS,
            timeout=10,
        )
        mb.raise_for_status()
        recs = mb.json().get("recordings", [])
        if not recs:
            return None
        rel = recs[0].get("releases", [{}])[0]
        rel_id = rel.get("id")
        if not rel_id:
            return None
        cover_url = f"https://coverartarchive.org/release/{rel_id}/front-500"
        if requests.head(cover_url, headers=HEADERS, timeout=10).status_code == 200:
            return cover_url
    except Exception as exc:
        print(f"[CAA] {exc}")
    return None


def fetch_deezer_art(title: str, artist: Optional[str] = None) -> Optional[str]:
    parts = []
    if artist:
        parts.append(f"artist:\"{artist}\"")
    parts.append(f"track:\"{title}\"")
    query = " ".join(parts)
    try:
        resp = requests.get(
            "https://api.deezer.com/search",
            params={"q": query, "limit": 1},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if data:
            return data[0]["album"].get("cover_xl")  # 1000×1000
    except Exception as exc:
        print(f"[Deezer] {exc}")
    return None

###############################################################################
# Embedding helpers
###############################################################################

def embed_album_art(mp3_path: str, url: str) -> bool:
    """Attempt to download *url* and embed it. Returns True on success."""
    try:
        img = requests.get(url, headers=HEADERS, timeout=10)
        img.raise_for_status()
    except Exception as exc:
        print(f"[art] download fail ({url[:60]}…): {exc}")
        return False

    try:
        try:
            audio = ID3(mp3_path)
        except ID3NoHeaderError:
            audio = ID3()
        audio.delall("APIC")
        audio.add(
            APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=img.content,
            )
        )
        audio.save(mp3_path)
        print(f"[art] embedded → {os.path.basename(mp3_path)}")
        return True
    except Exception as exc:
        print(f"[art] embed error: {exc}")
        return False


def write_genre_tag(mp3_path: str, genre: str) -> None:
    try:
        try:
            audio = ID3(mp3_path)
        except ID3NoHeaderError:
            audio = ID3()
        audio.delall("TCON")
        audio.add(TCON(encoding=3, text=genre))
        audio.save(mp3_path)
        print(f"[tag] genre → {os.path.basename(mp3_path)} = {genre}")
    except Exception as exc:
        print(f"[tag] genre error: {exc}")

###############################################################################
# CSV + processing
###############################################################################

def detect_columns(df: pd.DataFrame) -> tuple[str, str]:
    lower = {c.lower().strip(): c for c in df.columns}
    fn_col = next((lower[c] for c in FILENAME_HEADERS if c in lower), None)
    gn_col = next((lower[c] for c in GENRE_HEADERS if c in lower), None)
    if not fn_col or not gn_col:
        raise ValueError("CSV must include filename and genre columns (case‑insensitive)")
    return fn_col, gn_col


def provider_chain() -> list[Callable[[str, Optional[str]], Optional[str]]]:
    return [fetch_itunes_art, fetch_caa_art, fetch_deezer_art]


def process_csv(csv_path: str, mp3_dir: str) -> None:
    df = pd.read_csv(csv_path)
    fn_col, gn_col = detect_columns(df)

    providers = provider_chain()
    updated = 0

    for _, row in df.iterrows():
        mp3_path = os.path.join(mp3_dir, str(row[fn_col]))
        if not os.path.isfile(mp3_path):
            print(f"[skip] missing → {mp3_path}")
            continue

        # 1) genre tag
        write_genre_tag(mp3_path, str(row[gn_col]))

        # 2) artwork – iterate providers until one embeds successfully
        base = os.path.splitext(os.path.basename(mp3_path))[0]
        artist, _, title = base.partition(" - ") if " - " in base else (None, None, base)

        for fetch in providers:
            url = fetch(title, artist)
            if not url:
                continue
            if embed_album_art(mp3_path, url):
                break  # success
        else:
            print(f"[art] no art found for {base}")

        updated += 1
        time.sleep(REQUEST_DELAY)

    print(f"\nDone! {updated}/{len(df)} track(s) processed.")

###############################################################################
# CLI entry‑point
###############################################################################

def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Update MP3 genre tags and artwork from CSV list.")
    p.add_argument("--csv", default=DEFAULT_CSV, help="CSV file (default: %(default)s)")
    p.add_argument("--dir", default=DEFAULT_DIR, help="MP3 directory (default: %(default)s)")
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if not os.path.isfile(args.csv):
        sys.exit(f"CSV not found: {args.csv}")
    if not os.path.isdir(args.dir):
        sys.exit(f"MP3 directory not found: {args.dir}")
    process_csv(args.csv, args.dir)


if __name__ == "__main__":
    main()
