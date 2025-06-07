
from kivy.config import Config
Config.set('graphics', 'fullscreen', 'auto')
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '800')

from kivy.app import App
from gui import JukeboxGUI
from player import JukeboxPlayer
from song_library import get_all_mp3_files_with_metadata, is_abba_song
from dialogs import confirm_dialog, confirm_dialog_error
import threading
import time
import os
import random
import json
from kivy.core.window import Window
Window.clearcolor = (1, 0.99, 0.9, 1)  # A nice cream color (RGBA)

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from utils import normalize_genre, MAIN_GENRES, _index_after_last_user_pick

class RootWidget(FloatLayout):
    def __init__(self, gui, **kwargs):
        super().__init__(**kwargs)
        self.bg_image = Image(
            source="assets/images/background.png",
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.add_widget(self.bg_image)
        self.add_widget(gui)

MUSIC_DIR = 'mp3/'
PLAYLISTS_DIR = 'playlists'

all_songs_list = []
all_songs_path_map = {}
gui = None
player = None

def get_upcoming_songs_for_display():
    global player
    if not player:
        return []
    sim_primary_playlist = list(player.primary_playlist)
    sim_special_playlist = list(player.Special_playlist)
    sim_default_playlist = list(player.default_playlist)
    sim_song_counter = player.song_counter 

    upcoming_list_for_gui = []

    while len(upcoming_list_for_gui) < 10:
        is_special_slot = (sim_song_counter % 5 == 0 and sim_song_counter != 0)
        next_song_candidate = None

        if is_special_slot and sim_special_playlist:
            next_song_candidate = sim_special_playlist.pop(0)
        elif sim_primary_playlist:
            next_song_candidate = sim_primary_playlist.pop(0)
        elif sim_default_playlist:
            next_song_candidate = sim_default_playlist.pop(0)
        elif sim_special_playlist:
            next_song_candidate = sim_special_playlist.pop(0)
        else:
            break

        # Optional: just to be safe, don't queue duplicates (can be omitted if already managed)
        if next_song_candidate in upcoming_list_for_gui:
            continue

        upcoming_list_for_gui.append(next_song_candidate)
        sim_song_counter += 1

    return upcoming_list_for_gui

def select_song(song_to_select):
    global player, gui
    song_name = song_to_select['title']

    if song_name in player.played_songs:
        confirm_dialog_error(None, f"'{song_name}' has already been played.")
        return

    if song_name in player.selected_songs and song_to_select not in player.primary_playlist:
        is_already_in_primary = any(s['key'] == song_to_select['key'] for s in player.primary_playlist)
        if is_already_in_primary:
            confirm_dialog_error(None, f"'{song_name}' is already in the upcoming song queue.")
            return

    confirmation_message = f"Are you sure you want to select '{song_name}'?"
    if is_abba_song(song_to_select):
        confirmation_message = "Are you really sure you want to play Abba at this wedding?"

    def after_confirm(user_confirmed):
        if user_confirmed:
            if is_abba_song(song_to_select):
                threading.Thread(target=player.play_song_immediately, args=(song_to_select,)).start()
            else:
                # Insert at the right place: after all previously selected songs
                selected_count = sum(1 for s in player.primary_playlist if s['title'] in player.selected_songs)
                player.primary_playlist.insert(selected_count, song_to_select)
                player.selected_songs.add(song_name)
            if hasattr(gui, 'hidden_song_keys'):
                gui.hidden_song_keys.append(song_to_select['key'])
            if song_to_select in player.default_playlist:
                player.default_playlist.remove(song_to_select)
            if song_to_select in player.Special_playlist:
                player.Special_playlist.remove(song_to_select)
            if hasattr(gui, 'display_songs'):
                gui.display_songs()
            gui.update_upcoming_songs(get_upcoming_songs_for_display())

    confirm_dialog(None, confirmation_message, after_confirm)



def start_playback_thread():
    global player
    if player and (not hasattr(player, 'play_thread') or not player.play_thread.is_alive()):
        main_play_method = getattr(player, 'play_songs', None)
        if main_play_method:
            player.play_thread = threading.Thread(target=main_play_method, daemon=True)
            player.play_thread.start()
        else:
            print("Error: Could not find main playback method in player.")

def load_song_filenames_from_json(playlist_filename):
    filepath = os.path.join(PLAYLISTS_DIR, playlist_filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Playlist file '{filepath}' not found.")
    except json.JSONDecodeError:
        print(f"Warning: Error decoding JSON from '{filepath}'.")
    return []

def map_filenames_to_song_objects(filenames, song_path_map):
    loaded_songs = []
    for fname_in_playlist in filenames:
        normalized_playlist_fname = os.path.join(MUSIC_DIR, fname_in_playlist).replace("\\", "/")
        if normalized_playlist_fname in song_path_map:
            loaded_songs.append(song_path_map[normalized_playlist_fname])
        else:
            found_song = None
            for song_obj in song_path_map.values():
                if os.path.basename(song_obj['path']) == fname_in_playlist:
                    found_song = song_obj
                    break
            if found_song:
                loaded_songs.append(found_song)
            else:
                print(f"Warning: Song '{fname_in_playlist}' from playlist not found in music library.")
    return loaded_songs

class JukeboxKivyApp(App):
    def build(self):
        global gui, player, all_songs_list, all_songs_path_map
        all_songs_list.clear()
        all_songs_path_map.clear()
        raw_songs_from_library = get_all_mp3_files_with_metadata(MUSIC_DIR)
        for idx, song_data in enumerate(raw_songs_from_library):
            song_data['key'] = idx
            # Normalize all genres
            if 'genres' in song_data:
                song_data['genres'] = [normalize_genre(g) for g in song_data['genres']]
            else:
                song_data['genres'] = ['Pop']
            all_songs_list.append(song_data)
            normalized_path = song_data['path'].replace("\\", "/")
            all_songs_path_map[normalized_path] = song_data
        default_playlist_filenames = load_song_filenames_from_json('default_playlist.json')
        special_playlist_filenames = load_song_filenames_from_json('Special_playlist.json')
       # print(f"special_playlist_filenames loaded: {special_playlist_filenames}")
        songs_from_special_json = map_filenames_to_song_objects(special_playlist_filenames, all_songs_path_map)
        for s in songs_from_special_json:
            s['genres'] = ['Special']
       # print(f"Mapped songs_from_special_json: {[s['title'] for s in songs_from_special_json]}")
        special_song_paths = {s['path'] for s in songs_from_special_json}
        for song_obj in all_songs_list:
            if 'special' in [g.lower() for g in song_obj.get('genres', [])]:
                special_song_paths.add(song_obj['path'])
                is_already_in_special_list = any(s_obj['key'] == song_obj['key'] for s_obj in songs_from_special_json)
                if not is_already_in_special_list:
                    songs_from_special_json.append(song_obj)
        initial_primary_queue_songs_raw = map_filenames_to_song_objects(default_playlist_filenames, all_songs_path_map)
        initial_primary_queue_final = [
            s for s in initial_primary_queue_songs_raw if s['path'] not in special_song_paths
        ]
        def gui_update_now_playing(song_data):
            if gui:
                gui.update_now_playing(song_data)
        def gui_update_upcoming_songs_display():
            if gui:
                gui.update_upcoming_songs(get_upcoming_songs_for_display())
        player_instance = JukeboxPlayer(
            gui_update_now_playing,
            gui_update_upcoming_songs_display,
            gui_update_upcoming_songs_display,
            start_playback_callback=start_playback_thread
        )
        player_instance.primary_playlist = list(initial_primary_queue_final)
        player_instance.Special_playlist = list(songs_from_special_json)
        # print("\n---- Special_playlist after init ----")
        # for s in player_instance.Special_playlist:
        #     print(f"  [Special] {s['title']} | genres: {s['genres']} | path: {s['path']}")
        # print("-------------------------------------\n")
        paths_in_initial_primary = {s['path'] for s in player_instance.primary_playlist}
        fallback_candidate_songs = [
            s for s in all_songs_list
            if s['path'] not in special_song_paths and s['path'] not in paths_in_initial_primary
        ]
        random.shuffle(fallback_candidate_songs)
        player_instance.default_playlist = fallback_candidate_songs
        dance_button_callback = getattr(player_instance, 'play_special_song', None)
        if dance_button_callback is None:
            print("Warning: player.play_special_song method not found! 'Let's Dance' button may not work.")
            dance_button_callback = lambda: print("'Let's Dance' callback missing in player.")
        global player
        player = player_instance
        global gui
        gui = JukeboxGUI()
        gui.all_songs = all_songs_list
        gui.select_song_cb = select_song
        gui.dance_cb = lambda: [dance_button_callback(), start_playback_thread()]
        gui.player = player
        all_genres_in_library = set()
        for song in all_songs_list:
            all_genres_in_library.update(g.lower() for g in song.get('genres', []))
        all_genres_in_library.discard('unknown genre')
        all_genres_in_library.discard('special')
        gui.populate_genres(MAIN_GENRES)
        all_artists_in_library = sorted(list(set(s.get('artist', 'Unknown Artist') for s in all_songs_list)))
        gui.populate_artists(all_artists_in_library)
        gui.display_songs()
        gui.update_upcoming_songs(get_upcoming_songs_for_display())
        # Do NOT start playback thread here
        return RootWidget(gui)

if __name__ == "__main__":
    JukeboxKivyApp().run()
