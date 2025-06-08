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
import os
import random
import json
from kivy.core.window import Window
Window.clearcolor = (1, 0.99, 0.9, 1)  # A nice cream color (RGBA)

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from utils import normalize_genre, MAIN_GENRES

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
    """Simulates the player's logic to generate a list of the next 10 upcoming songs."""
    global player
    if not player:
        return []
    
    # Create copies of playlists to simulate without affecting the actual player state
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
        elif sim_special_playlist: # In case we run out of primary/default songs
            next_song_candidate = sim_special_playlist.pop(0)
        else:
            break # No more songs available

        if next_song_candidate not in upcoming_list_for_gui:
            upcoming_list_for_gui.append(next_song_candidate)
        sim_song_counter += 1

    return upcoming_list_for_gui

def select_song(song_to_select):
    """Handles the logic for when a user selects a song from the GUI."""
    global player, gui
    song_name = song_to_select['title']

    if song_name in player.played_songs:
        confirm_dialog_error(None, f"'{song_name}' has already been played.")
        gui.clear_filter()
        return

    is_already_in_primary = any(s['key'] == song_to_select['key'] for s in player.primary_playlist)
    if is_already_in_primary:
        confirm_dialog_error(None, f"'{song_name}' is already in the upcoming song queue.")
        gui.clear_filter()
        return

    confirmation_message = f"Are you sure you want to select '{song_name}'?"
    if is_abba_song(song_to_select):
        confirmation_message = "Are you really sure you want to play Abba at this wedding?"

    def after_confirm(user_confirmed):
        if user_confirmed:
            if is_abba_song(song_to_select):
                threading.Thread(target=player.play_song_immediately, args=(song_to_select,)).start()
            else:
                # Insert after all other user-selected songs
                selected_count = sum(1 for s in player.primary_playlist if s['title'] in player.selected_songs)
                player.primary_playlist.insert(selected_count, song_to_select)
                player.selected_songs.add(song_name)

            # Hide the song from future selections and remove from other playlists
            gui.hidden_song_keys.append(song_to_select['key'])
            if song_to_select in player.default_playlist:
                player.default_playlist.remove(song_to_select)
            if song_to_select in player.Special_playlist:
                player.Special_playlist.remove(song_to_select)
            
            # *** CRITICAL: Clear filters and update GUI only after confirmation ***
            gui.clear_filter() 
            gui.update_upcoming_songs(get_upcoming_songs_for_display())

    confirm_dialog(None, confirmation_message, after_confirm)

def start_playback_thread():
    """Starts the main audio playback thread if it's not already running."""
    global player
    if player and (not hasattr(player, 'play_thread') or not player.play_thread.is_alive()):
        main_play_method = getattr(player, 'play_songs', None)
        if main_play_method:
            player.play_thread = threading.Thread(target=main_play_method, daemon=True)
            player.play_thread.start()
        else:
            print("Error: Could not find main playback method in player.")

def load_song_filenames_from_json(playlist_filename):
    """Loads a list of song filenames from a JSON playlist file."""
    filepath = os.path.join(PLAYLISTS_DIR, playlist_filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load playlist '{filepath}'. Reason: {e}")
    return []

def map_filenames_to_song_objects(filenames, song_path_map):
    """Maps a list of filenames to their corresponding full song data objects."""
    loaded_songs = []
    for fname in filenames:
        # First, try a direct lookup with the expected path structure
        normalized_path = os.path.join(MUSIC_DIR, fname).replace("\\", "/")
        if normalized_path in song_path_map:
            loaded_songs.append(song_path_map[normalized_path])
        else:
            # Fallback: search for the base filename in all song objects
            found_song = next((s for s in song_path_map.values() if os.path.basename(s['path']) == fname), None)
            if found_song:
                loaded_songs.append(found_song)
            else:
                print(f"Warning: Song '{fname}' from playlist not found in music library.")
    return loaded_songs

class JukeboxKivyApp(App):
    def build(self):
        global gui, player, all_songs_list, all_songs_path_map
        
        # 1. Load all songs from disk and process metadata
        all_songs_list = get_all_mp3_files_with_metadata(MUSIC_DIR)
        for idx, song in enumerate(all_songs_list):
            song['key'] = idx
            song['genres'] = [normalize_genre(g) for g in song.get('genres', [])] or ['Pop']
            all_songs_path_map[song['path'].replace("\\", "/")] = song

        # 2. Load playlists and map filenames to song objects
        special_playlist_filenames = load_song_filenames_from_json('Special_playlist.json')
        songs_from_special_json = map_filenames_to_song_objects(special_playlist_filenames, all_songs_path_map)
        for s in songs_from_special_json: # Ensure correct genre tagging
            s['genres'] = ['Special']
        
        default_playlist_filenames = load_song_filenames_from_json('default_playlist.json')
        initial_primary_queue_songs = map_filenames_to_song_objects(default_playlist_filenames, all_songs_path_map)

        # 3. Initialize the player with the loaded playlists
        player = JukeboxPlayer(
            gui_update_now_playing=lambda song_data: gui.update_now_playing(song_data) if gui else None,
            update_upcoming_songs_callback=lambda: gui.update_upcoming_songs(get_upcoming_songs_for_display()) if gui else None,
            start_playback_callback=start_playback_thread
        )
        player.Special_playlist = list(songs_from_special_json)
        player.primary_playlist = list(initial_primary_queue_songs)
        
        # Create the default/fallback playlist from all remaining songs
        played_paths = {s['path'] for s in player.Special_playlist + player.primary_playlist}
        player.default_playlist = [s for s in all_songs_list if s['path'] not in played_paths]
        random.shuffle(player.default_playlist)

        # 4. Initialize the GUI and link it to the player and song data
        gui = JukeboxGUI(
            all_songs=all_songs_list,
            player=player,
            select_song_cb=select_song,
            dance_cb=lambda: [player.play_special_song(), start_playback_thread()]
        )
        
        # --- Populate GUI filters with available artists and genres ---
        
        # First, determine which song titles are currently unavailable.
        played_titles = player.played_songs
        primary_queued_titles = {song['title'] for song in player.primary_playlist}
        special_queued_titles = {song['title'] for song in player.Special_playlist}
        unavailable_titles = played_titles.union(primary_queued_titles, special_queued_titles)

        # Get all unique artists from the entire library.
        all_artists_in_library = set()
        for song in all_songs_list:
            all_artists_in_library.update(song.get('artists', []))

        # Now, filter this list to include only artists with at least one available song.
        available_artists = []
        for artist in all_artists_in_library:
            # Check if this artist has any song that is NOT in the unavailable list.
            has_available_song = any(
                song['title'] not in unavailable_titles 
                for song in all_songs_list if artist in song.get('artists', [])
            )
            if has_available_song:
                available_artists.append(artist)
        
        # Populate the GUI with the filtered list of artists and all main genres.
        gui.populate_artists(sorted(available_artists))
        gui.populate_genres(MAIN_GENRES)

        # 5. Perform initial GUI updates
        gui.display_songs()
        gui.update_upcoming_songs(get_upcoming_songs_for_display())

        return RootWidget(gui)

if __name__ == "__main__":
    JukeboxKivyApp().run()