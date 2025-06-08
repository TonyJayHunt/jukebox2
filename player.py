import os
if os.environ.get("GITHUB_ACTIONS", "") == "true":
    os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
from kivy.clock import Clock
import threading
import time

pygame.mixer.init()

class JukeboxPlayer:
    def __init__(self, gui_update_now_playing, update_upcoming_songs_callback, start_playback_callback=None):
        self.update_now_playing = gui_update_now_playing
        self.update_upcoming_songs = update_upcoming_songs_callback
        self.start_playback_callback = start_playback_callback

        self.default_playlist = []
        self.Special_playlist = []
        self.primary_playlist = []
        
        self.played_songs = set()
        self.selected_songs = set()

        self.current_song = None
        self.song_counter = 1
        
        self.immediate_playback = False
        self.immediate_lock = threading.Lock()
        self.skip_flag = threading.Event()

    def play_song_immediately(self, song):
        """Stops the current queue to play a specified song right away (e.g., ABBA)."""
        with self.immediate_lock:
            self.immediate_playback = True
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(song['path'])
            pygame.mixer.music.play(fade_ms=2000)
            self.current_song = song
            Clock.schedule_once(lambda dt: self.update_now_playing(song))
            while pygame.mixer.music.get_busy() and not self.skip_flag.is_set():
                time.sleep(0.1)
        except Exception as e:
            print(f"Error playing immediate song '{song['title']}': {e}")
        finally:
            pygame.mixer.music.stop()
            self.skip_flag.clear()
            with self.immediate_lock:
                self.immediate_playback = False
            # Refresh GUI after immediate playback finishes
            Clock.schedule_once(lambda dt: self.update_now_playing(self.current_song))
            Clock.schedule_once(lambda dt: self.update_upcoming_songs())

    def play_songs(self):
        """The main playback loop, runs in a separate thread."""
        while True:
            try:
                with self.immediate_lock:
                    if self.immediate_playback:
                        time.sleep(1)
                        continue
                
                if not pygame.mixer.music.get_busy():
                    next_song_to_play = self._get_next_song()
                    if next_song_to_play:
                        self._play_song_from_queue(next_song_to_play)
                    else:
                        time.sleep(1) # No songs left, wait
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"FATAL Error in play_songs loop: {e}")

    def _get_next_song(self):
        """Determines the next song to play based on the queueing logic."""
        is_special_slot = (self.song_counter % 5 == 0 and self.song_counter != 0)
        
        if is_special_slot and self.Special_playlist:
            return self.Special_playlist.pop(0)
        if self.primary_playlist:
            return self.primary_playlist.pop(0)
        if self.default_playlist:
            return self.default_playlist.pop(0)
        if self.Special_playlist: # Fallback to special if others are empty
             return self.Special_playlist.pop(0)
        return None

    def _play_song_from_queue(self, song):
        """Loads and plays a single song from one of the queues."""
        try:
            pygame.mixer.music.load(song['path'])
            pygame.mixer.music.play(fade_ms=2000)
            
            self.song_counter += 1
            self.played_songs.add(song['title'])
            self.current_song = song

            # Schedule GUI updates on the main Kivy thread
            Clock.schedule_once(lambda dt: self.update_now_playing(song))
            Clock.schedule_once(lambda dt: self.update_upcoming_songs())

            while pygame.mixer.music.get_busy() and not self.skip_flag.is_set():
                time.sleep(0.1)
        except Exception as e:
            print(f"Error playing song '{song['title']}': {e}")
        finally:
            pygame.mixer.music.stop()
            self.skip_flag.clear()
            
    def play_special_song(self):
        """Initiates the special 'First Dance' song in its own thread."""
        threading.Thread(target=self._handle_special_song_playback, daemon=True).start()

    def skip_current_song(self):
        self.skip_flag.set()

    def _handle_special_song_playback(self):
        """The playback logic for the special song, handling audio and GUI updates."""
        with self.immediate_lock:
            self.immediate_playback = True
        pygame.mixer.music.stop()

        album_art_bytes = None
        if os.path.exists('0R3A0809.jpg'):
            with open('0R3A0809.jpg', "rb") as f:
                album_art_bytes = f.read()

        song = {
            'path': 'I_am_a_test.mp3',
            'title': 'The First Dance',
            'artists': ["Nicki's Mix"], # Use list for consistency
            'genres': ['Pop', 'Christmas'],
            'album_art': album_art_bytes,
            'key': 'start_song'
        }
        
        try:
            pygame.mixer.music.load(song['path'])
            pygame.mixer.music.play()
            self.current_song = song
            Clock.schedule_once(lambda dt: self.update_now_playing(song))

            while pygame.mixer.music.get_busy() and not self.skip_flag.is_set():
                time.sleep(0.1)
        except Exception as e:
            print(f"Error playing special song: {e}")
        finally:
            pygame.mixer.music.stop()
            self.skip_flag.clear()
            with self.immediate_lock:
                self.immediate_playback = False
        
        self.played_songs.add(song['title'])
        Clock.schedule_once(lambda dt: self.update_upcoming_songs())
        if self.start_playback_callback:
            Clock.schedule_once(lambda dt: self.start_playback_callback())