import os
if os.environ.get("GITHUB_ACTIONS", "") == "true":
    os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
import threading
import time

pygame.mixer.init()

class JukeboxPlayer:
    def __init__(
        self,
        root,
        update_now_playing_callback,
        update_up_next_callback,
        update_upcoming_songs_callback,
        start_playback_callback=None
    ):
        self.root = root
        self.update_now_playing = update_now_playing_callback
        self.update_up_next = update_up_next_callback
        self.update_upcoming_songs = update_upcoming_songs_callback
        self.default_playlist = []
        self.Special_playlist = []
        self.primary_playlist = []
        self.played_songs = set()
        self.selected_songs = set()
        self.immediate_playback = False
        self.immediate_lock = threading.Lock()
        self.song_counter = 1
        self.current_song = None
        self.next_song = None
        self.start_playback_callback = start_playback_callback

    def load_playlists(self, all_songs):
        self.default_playlist = [song for song in all_songs if 'christmas' not in song['genres']]
        self.Special_playlist = [song for song in all_songs if 'special' in song['genres']]

    def play_song_immediately(self, song):
        song_path = song['path']
        with self.immediate_lock:
            self.immediate_playback = True
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play(fade_ms=2000)
            self.current_song = song
            self.update_now_playing(song)
            while pygame.mixer.music.get_busy():
                time.sleep(1)
        except Exception as e:
            print(f"Error playing song '{song['title']}': {e}")
        finally:
            with self.immediate_lock:
                self.immediate_playback = False
        self.update_up_next()
        self.update_upcoming_songs()

    def play_songs(self):
        while True:
            with self.immediate_lock:
                if self.immediate_playback:
                    time.sleep(1)
                    continue
            if not pygame.mixer.music.get_busy():
                song = self._get_next_song()
                if song:
                    self._play_next_song(song)
                else:
                    time.sleep(1)
            else:
                time.sleep(0.1)

    def _get_next_song(self):
        if self.primary_playlist:
            return self.primary_playlist.pop(0)
        elif self.song_counter % 5 == 0 and self.song_counter != 0 and self.Special_playlist:
            return self.Special_playlist.pop(0)
        elif self.default_playlist:
            return self.default_playlist.pop(0)
        else:
            return None

    def _play_next_song(self, song):
        song_path = song['path']
        try:
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play(fade_ms=2000)
            if not self.immediate_playback:
                self.song_counter += 1
            self.played_songs.add(song['title'])
            self.current_song = song
            # Remove from playlists if present
            if song in self.default_playlist:
                self.default_playlist.remove(song)
            if song in self.Special_playlist:
                self.Special_playlist.remove(song)
            self.root.after(0, self.update_now_playing, song)
            self.root.after(0, self.update_up_next)
            self.root.after(0, self.update_upcoming_songs)
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as e:
            print(f"Error playing song '{song['title']}': {e}")

    def play_special_song(self):
        threading.Thread(target=self._handle_special_song).start()

    def skip_current_song(self):
        try:
            pygame.mixer.music.stop()  # This stops the current song immediately.
        except Exception as e:
            print(f"Error skipping song: {e}")

    def _handle_special_song(self):
        import os
        with self.immediate_lock:
            self.immediate_playback = True
        pygame.mixer.music.fadeout(5000)
        time.sleep(5)
        # Load album art as bytes
        album_art_path = '0R3A0809.jpg'
        album_art_bytes = None
        if os.path.exists(album_art_path):
            with open(album_art_path, "rb") as imgf:
                album_art_bytes = imgf.read()
        song = {
            'path': 'I_am_a_test.mp3',
            'title': 'The First Dance',
            'artist': "Nicki's Mix",
            'genres': ['Pop','Christmas'],
            'album_art': album_art_bytes,
            'key': 'start_song'
        }
        try:
            pygame.mixer.music.load(song['path'])
            pygame.mixer.music.play()
            self.current_song = song
            self.root.after(0, self.update_now_playing, song)
            while pygame.mixer.music.get_busy():
                time.sleep(1)
        except Exception as e:
            print(f"Error playing special song: {e}")
        finally:
            with self.immediate_lock:
                self.immediate_playback = False
        self.played_songs.add(song['title'])
        self.root.after(0, self.update_up_next)
        self.root.after(0, self.update_upcoming_songs)
        if self.start_playback_callback:
            self.start_playback_callback()

