import tkinter as tk
from tkinter import messagebox
import threading
import time
import os
import random
import json

from gui import JukeboxGUI
from player import JukeboxPlayer
from song_library import get_all_mp3_files_with_metadata, is_abba_song
from dialogs import confirm_dialog, confirm_dialog_error
from utils import center_window

# Global Variables
all_songs = []
song_buttons = {}
root = None
gui = None
player = None

def gui_update_now_playing(song):
    global root, gui
    if root and gui:
        root.after(0, gui.update_now_playing, song)

def gui_update_up_next():
    global root, gui
    if root and gui:
        root.after(0, gui.update_up_next)

def gui_update_upcoming_songs():
    global root, gui
    if root and gui:
        root.after(0, gui.update_upcoming_songs, get_upcoming_songs())

def select_song(song):
    global all_songs, player, gui, root
    song_name = song['title']
    if song_name in player.played_songs:
        confirm = confirm_dialog_error(root, f"'{song_name}' has already been played.")
        return
    if song_name in player.selected_songs:
        confirm = confirm_dialog_error(root, f"'{song_name}' has already been selected.")
        return

    confirm = confirm_dialog(root, f"Are you sure you want to select '{song_name}'?")
    if confirm:
        if is_abba_song(song):
            confirm_abba = confirm_dialog(
                root, "Are you really sure you want to play Abba at this wedding?")
            if confirm_abba:
                threading.Thread(target=player.play_song_immediately, args=(song,)).start()
                player.selected_songs.add(song_name)
                player.played_songs.add(song_name)
                def remove_button():
                    gui.hidden_song_keys.add(song['key'])
                    btn = gui.song_buttons.pop(song['key'], None)
                    if btn: btn.destroy()
                root.after(0, remove_button)
                if song in player.default_playlist:
                    player.default_playlist.remove(song)
                if song in player.christmas_playlist:
                    player.christmas_playlist.remove(song)
                gui.update_up_next()
                gui.update_upcoming_songs(get_upcoming_songs())
        else:
            player.primary_playlist.append(song)
            player.selected_songs.add(song_name)
            def remove_button():
                btn = gui.song_buttons.pop(song['key'], None)
                if btn: btn.destroy()
            root.after(0, remove_button)
            if song in player.default_playlist:
                player.default_playlist.remove(song)
            if song in player.christmas_playlist:
                player.christmas_playlist.remove(song)
            if len(player.primary_playlist) == 1:
                gui.update_up_next()
            gui.artist_filter_var.set('All')
            gui.genre_filter_var.set('All')
            gui.display_songs()
            gui.update_upcoming_songs(get_upcoming_songs())

def get_upcoming_songs():
    global player
    primary = list(player.primary_playlist)
    default = list(player.default_playlist)
    christmas = list(player.christmas_playlist)
    out = []
    song_counter = player.song_counter
    while len(out) < 10 and (primary or default or christmas):
        if primary:
            song = primary.pop(0)
            out.append(song)
            song_counter += 1
        elif song_counter % 5 == 0 and song_counter != 0 and christmas:
            song = christmas.pop(0)
            out.append(song)
            song_counter += 1
        elif default:
            song = default.pop(0)
            out.append(song)
            song_counter += 1
        else:
            break
    return out

def start_playback():
    global player
    if not hasattr(player, 'play_thread') or not player.play_thread.is_alive():
        player.play_thread = threading.Thread(target=player.play_songs)
        player.play_thread.daemon = True
        player.play_thread.start()

def main():
    global root, gui, player, all_songs

    root = tk.Tk()
    root.title("Jukebox")
    root.attributes('-fullscreen', True)
    def exit_fullscreen(event=None):
        root.attributes('-fullscreen', False)
    root.bind('<Escape>', exit_fullscreen)

    all_songs = get_all_mp3_files_with_metadata('mp3/')
    for idx, song in enumerate(all_songs):
        song['key'] = idx

    # --- Load Christmas playlist from file ---
    with open("playlists/christmas_playlist.json", "r", encoding="utf-8") as f:
        xmas_files = set(json.load(f))
    # Find matching songs (by filename)
    auto_christmas_songs = [s for s in all_songs if os.path.basename(s['path']) in xmas_files]
    # The rest of the songs (including other christmas-tagged) are normal
    non_christmas = [s for s in all_songs if os.path.basename(s['path']) not in xmas_files]

    # You can still shuffle non-christmas playlist if you want
    random.shuffle(non_christmas)

    player = JukeboxPlayer(
        root,
        gui_update_now_playing,
        gui_update_up_next,
        gui_update_upcoming_songs,
        start_playback_callback=start_playback
    )
    player.default_playlist = non_christmas
    player.christmas_playlist = auto_christmas_songs

    # The rest of your setup...
    gui = JukeboxGUI(root, select_song, player.play_special_song, player)
    gui.all_songs = all_songs

    # Populate genres and artists as before, but do NOT filter out 'christmas'
    all_genres = set()
    for song in all_songs:
        all_genres.update(song['genres'])
    all_genres.discard('unknown genre')
    gui.populate_genre_buttons(sorted(list(all_genres)))

    artist_songs = {}
    for song in all_songs:
        artist = song['artist']
        if artist not in artist_songs:
            artist_songs[artist] = []
        artist_songs[artist].append(song)
    valid_artists = [artist for artist, songs in artist_songs.items()
                     if any('christmas' not in song['genres'] for song in songs)]
    gui.populate_artist_combobox(sorted(valid_artists))

    gui.display_songs()
    gui.update_upcoming_songs(get_upcoming_songs())
    root.mainloop()

if __name__ == "__main__":
    main()
