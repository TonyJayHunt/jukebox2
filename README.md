# 🎶 Jukebox Party Solution

## Overview

This project is an **interactive, touch-friendly jukebox and music manager** for events and parties, designed especially for weddings.  
It allows guests to browse, filter, and select songs (from local MP3s with metadata), and manages a “smart queue” with rules for fairness and event structure (e.g., special “first dance” song, Christmas song every 5 tracks, no double-picks).

The system runs on Python and uses a modern Tkinter GUI with album art display, scrollable genre and song selection, and a robust backend for managing song metadata and queue logic.

---

## Features

- 🖼 **Modern GUI:** Album art, scrollable song/genre/artist lists, and touch-friendly layout.
- 🎤 **Filters:** By artist and genre with instant "clear filter" support.
- ❌ **No Double-Picks:** Each song can only be picked once.
- 🎄 **Christmas Rule:** Every 5th song is a Christmas track, if available.
- 👩‍❤️‍👨 **Special Song:** Automatically play a “first dance” song before the queue.
- 🎵 **Album Art:** Shown in Now Playing from embedded MP3 images.
- 🎹 **Batch Tools:** Scripts to fetch/download/clean up mp3 metadata and tags.
- 🧪 **Tests:** Unit-tested with `pytest` for core and helper modules.

---

## How It Works

1. **Place all your MP3 files in an `mp3/` directory**.  
   Each MP3 should have `title`, `artist`, and `genre` tags (album art optional).
2. **Run the program:**  
   - The app scans all MP3s and extracts metadata.
   - GUI displays all available songs.  
   - Users select songs to queue them; each song can be picked only once.
   - The system ensures no repeats, plays a Christmas song every 5th track, and manages the queue and special moments (like the first dance).
   - Album art and song details are shown in the Now Playing panel.
   - Everything is designed for full-screen/touch usage at an event.

---

## Setup & Requirements

- **Python 3.9+**
- **Dependencies:**  
  Install required libraries:
  ```bash
  pip install pillow mutagen pygame requests pandas
  ```
- **Music:**  
  Place your MP3s in the `mp3/` directory in the project root.  
  Each file **must** have correct metadata (ID3 tags for title, artist, genre, and album art if possible).
  Use a tag editor like [Mp3tag](https://www.mp3tag.de/en/) for best results.

---

## How to Run

```bash
python main.py
```
The app will open in fullscreen. Use the on-screen controls to filter, pick, and queue music.

---

## Batch Tools

- **`download_playlist_mp3.py`**: Downloads a YouTube playlist, auto-tags songs, and saves as MP3s.
- **`update_genre.py`**: Batch updates genre tags and embeds album art, pulling info from online sources.
- **`update_genre_file.py`**: Cleans up genre fields for consistency.

---

## Directory Structure

```
jukebox2/
│
├── main.py
├── gui.py
├── player.py
├── song_library.py
├── dialogs.py
├── utils.py
├── download_playlist_mp3.py
├── update_genre.py
├── update_genre_file.py
├── mp3/
│   ├── *.mp3      # Your music files here
├── tests/
│   ├── test_*.py  # All pytest unit tests
```

---

## File-by-File Breakdown

### `main.py`
- **Role:** Application entry point; loads library, initializes player, launches GUI.
- **Key logic:** Reads metadata, builds song lists, manages playlists, ties together player and GUI.

### `gui.py`
- **Role:** All GUI code (Tkinter). Lays out filter sidebar, now playing, queue, and song selection.
- **Major classes/functions:**  
  - `JukeboxGUI`: Main GUI class.  
  - Handles album art resizing, dynamic filter buttons, scrollbar logic, and event callbacks.

### `player.py`
- **Role:** Manages playback, enforces event rules, runs audio via `pygame`.
- **Key functions:**  
  - `play_songs()`: Handles main queue loop, Christmas rule, special songs.
  - `skip_current_song()`: Allows skipping current song from GUI.

### `song_library.py`
- **Role:** Reads the `mp3/` folder, extracts ID3 metadata and album art using `mutagen`.
- **Functions:**  
  - `load_library()`: Scans files, builds the full song list.
  - `is_abba_song()`: Helper for special rules (e.g., ABBA handling).

### `dialogs.py`
- **Role:** Provides custom dialogs (Tk popups) for confirmations, password, and errors.
- **Functions:**  
  - `ask_password()`, `ask_confirm()`, etc.

### `utils.py`
- **Role:** Miscellaneous utilities, e.g., `center_window()` to center popups on screen.

### `download_playlist_mp3.py`
- **Role:** Script for downloading and tagging MP3s from a YouTube playlist using `yt-dlp` and online APIs.
- **Functions:**  
  - `sanitize_title()`, `parse_artist_title()`, `tag_mp3()`, plus main workflow for download and tagging.

### `update_genre.py`
- **Role:** Batch-update genres and embed album art for many MP3s, optionally fetching covers from APIs.
- **Functions:**  
  - `fetch_itunes_art()`, `fetch_caa_art()`, `fetch_deezer_art()`, `embed_album_art()`, `write_genre_tag()`, etc.

### `update_genre_file.py`
- **Role:** Cleans up genre fields for consistency and uniqueness.
- **Function:**  
  - `clean_genre()`: Splits, dedups, and cleans genre strings.

---

## Tests

- Run all tests with:
  ```bash
  pytest
  ```
- Tests cover GUI logic (with mocks), file utilities, metadata handling, and batch tools.

---

## Example Workflow

1. Prepare your MP3s in the `mp3/` folder with correct tags and album art.
2. (Optional) Run batch tools to clean genres or add album art.
3. Launch the main program with `python main.py`.
4. Guests select music using the touch-friendly GUI.
5. Music plays in order, with event rules enforced, and beautiful Now Playing/up-next displays.

---

## Troubleshooting

- **Album art not showing:** Ensure the MP3 has embedded art.
- **Songs missing:** Confirm your mp3 files are tagged and in the `mp3/` directory.
- **Playback errors:** Check your Python and dependency versions, and that `pygame` audio works on your OS.

---

**Enjoy your event!**  
For code support, see comments in each file, or reach out with issues or suggestions.
