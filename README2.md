# 📦 Jukebox Additional Tools & Utilities

This document covers **additional tools** provided alongside the main Jukebox event solution.  
These scripts help with **music batch processing, metadata clean-up, quiz card creation, and more**—ideal for preparing your music library and event printables!

---

## Table of Contents

- [Overview](#overview)
- [Tool List](#tool-list)
  - [1. CreateQuestions.py](#1-createquestionspy)
  - [2. download_playlist_mp3.py](#2-download_playlist_mp3py)
  - [3. front.py](#3-frontpy)
  - [4. get_files.py](#4-get_filespy)
  - [5. jukebox.py](#5-jukeboxpy)
  - [6. update_genre.py](#6-update_genrepy)
  - [7. update_genre_file.py](#7-update_genre_filepy)
- [General Requirements](#general-requirements)
- [Code-by-Code Breakdown](#code-by-code-breakdown)

---

## Overview

These tools extend the Jukebox system with powerful utilities for:
- **Bulk music tagging and album art embedding**
- **Generating printable game/quiz cards for your event**
- **Fetching, cleaning, and exporting song metadata**
- **Batch downloading MP3s from YouTube with tags**

---

## Tool List

### 1. **CreateQuestions.py**

- **Purpose:**  
  Generates printable "quest cards" for guests (e.g., for a wedding game) as DOCX files.
- **How to Use:**  
  - Prepare CSV files with question pools (one for pictures, one for questions).
  - Run `python CreateQuestions.py`
  - Outputs a formatted Word document ready to print (A5 landscape, 68 variations).

### 2. **download_playlist_mp3.py**

- **Purpose:**  
  Download a YouTube playlist, convert to MP3, auto-tag songs (artist, title, album, genre).
- **How to Use:**  
  - Install [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [mutagen](https://mutagen.readthedocs.io/en/latest/).
  - Run:
    ```bash
    python download_playlist_mp3.py "<playlist_url>" [output_dir]
    ```
  - MP3s are saved and tagged for use in the Jukebox system.

### 3. **front.py**

- **Purpose:**  
  Create high-quality, printable PNG covers (A5 portrait) with custom images and centered text, for event printouts (e.g., quest cards).
- **How to Use:**  
  - Place your top/bottom images in your working directory.
  - Edit the text in the script as needed.
  - Run the script, outputs an A5 PNG (front_a5.png).

### 4. **get_files.py**

- **Purpose:**  
  Scan a folder of MP3s, extract file, title, and artist metadata, and output to a CSV.
- **How to Use:**  
  - Run:
    ```bash
    python get_files.py
    ```
  - Edits output filename and directory as needed in the script.
  - CSV can be used in Excel or batch tools below.

### 5. **jukebox.py**

- **Purpose:**  
  (Alternative or simple version) GUI Jukebox for selecting and playing songs, similar to main app but may offer a simpler interface or for rapid prototyping.
- **How to Use:**  
  - Ensure you have MP3 files with tags in a `mp3/` directory.
  - Run:
    ```bash
    python jukebox.py
    ```
  - Follow the on-screen instructions.

### 6. **update_genre.py**

- **Purpose:**  
  Batch-update genre tags and embed album art into MP3s using a CSV file (exported from get_files or by hand).
- **How to Use:**  
  - Prepare a CSV with columns for filename and genre.
  - Run:
    ```bash
    python update_genre.py --csv your_file.csv --dir mp3/
    ```
  - Will auto-fetch and embed album art from iTunes, Deezer, or MusicBrainz if available.

### 7. **update_genre_file.py**

- **Purpose:**  
  Use Wikipedia to fill in missing genres in your CSV metadata file. Cleans up genres, removes duplicates, and normalizes for batch processing.
- **How to Use:**  
  - Run:
    ```bash
    python update_genre_file.py
    ```
  - Edits input/output CSV file paths in the script as needed.
  - Fills in missing genres using Wikipedia and saves the result.

---

## General Requirements

- **Python 3.9+**
- **pip install**:
  ```bash
  pip install pandas requests mutagen python-docx pillow wikipedia beautifulsoup4 yt-dlp
  ```
- For MP3 work, all tools expect files in a `/mp3` directory, with as much metadata as possible.
- Some tools use network APIs—ensure you have an internet connection.

---

## Code-by-Code Breakdown

### CreateQuestions.py

- **get_data_from_csv(path):** Reads CSV of questions, returns usable questions and allowed uses.
- **pick_question(pool, used):** Randomly picks unique questions, decrements uses.
- **main():** Builds a DOCX document, creates 68 variations, each with a left "welcome" and right column of 7 tasks/questions.

---

### download_playlist_mp3.py

- **sanitize_title(title):** Removes "(Official Video)" etc. and formats nicely.
- **parse_artist_title(title):** Splits "Artist - Title".
- **get_genre_from_musicbrainz(artist, title):** Tries to fetch genre from MusicBrainz API.
- **tag_mp3(file, artist, title, genre):** Adds metadata to MP3.
- **download_and_set_tags(url, dir):** Downloads all videos in playlist, tags each with artist/title/genre/album.

---

### front.py

- **draw_centered_multiline_text(...):** Draws multiline text centered on the image.
- **create_a5_png_with_line_and_centered_text(...):**  
  - Rotates and adds two images (top/bottom).
  - Draws a dividing line.
  - Adds centered event text in both halves.
  - Saves to PNG for print.

---

### get_files.py

- **extract_files_to_csv(dir, csv):**  
  - Scans a directory for files.
  - For MP3s, extracts title/artist from tags.
  - Writes all info to a CSV for later batch operations.

---

### jukebox.py

- **get_all_mp3_files_with_metadata(dir):** Reads all MP3s, extracts full metadata including genres and album art.
- **play_song_immediately(song):** Interrupts queue, plays selected song.
- **play_songs():** Main play loop, enforces rules (e.g., Christmas song every 5).
- **select_song(song):** Handles user selection, disables buttons, updates state.

---

### update_genre.py

- **fetch_itunes_art, fetch_caa_art, fetch_deezer_art:** Fetch cover art from online music databases.
- **embed_album_art(file, url):** Download and attach cover art to MP3.
- **write_genre_tag(file, genre):** Update genre tag in MP3.
- **process_csv(csv, dir):**  
  - For each file in CSV, update genre.
  - Try to embed album art from online sources.
  - Print status for each track.

---

### update_genre_file.py

- **clean_genre(raw):**  
  - Cleans up genre string, removes footnotes/duplicates, splits on common separators.
- **fetch_genre(search):**  
  - Uses Wikipedia to find likely genre for a search query.
- **main section:**  
  - Loads CSV, fills missing genres, saves new CSV.

---

**For more info, read code comments or run with `--help` (if available)!**  
These tools are ideal for wedding/event prep, quiz/game card generation, and making your Jukebox library shine.
