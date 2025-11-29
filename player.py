import os
if os.environ.get("GITHUB_ACTIONS", "") == "true":
    os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
from kivy.clock import Clock
import threading
import time
from mutagen import File as MutagenFile  # for duration lookup
import random  # NEW

pygame.mixer.init()
CROSSFADE_CHANNEL_IDX = 1
AMBIENT_CHANNEL_IDX = 2  # NEW
TEST_CHANNEL_IDX = 3
pygame.mixer.set_num_channels(max(8, CROSSFADE_CHANNEL_IDX + 1, AMBIENT_CHANNEL_IDX + 1, TEST_CHANNEL_IDX + 1))

def _fmt_mmss(seconds):
    if seconds is None:
        return "??:??"
    m = int(seconds // 60)
    s = int(round(seconds % 60))
    return f"{m:02d}:{s:02d}"

def _fmt_clock(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts))

def _get_duration_seconds(path):
    try:
        mf = MutagenFile(path)
        if mf and mf.info and getattr(mf.info, "length", None):
            return float(mf.info.length)
    except Exception:
        pass
    # Fallback to pygame Sound length (may be inaccurate for some formats)
    try:
        snd = pygame.mixer.Sound(path)
        return float(snd.get_length())
    except Exception:
        return None

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
        self.current_start_ts = None
        self.current_duration = None

        self.song_counter = 1

        # NEW: protects access to the 3 playlists and song_counter
        self.queue_lock = threading.Lock()
        
        self.immediate_playback = False
        self.immediate_lock = threading.Lock()
        self.skip_flag = threading.Event()

        # Crossfade state
        self.crossfade_lock = threading.Lock()
        self.crossfade_active = False
        self.crossfade_duration = 5.0  # seconds
        self.crossfade_thread = None

        # NEW: Ambient playback state
        self.ambient_thread = None
        self.ambient_stop_event = threading.Event()        

    # -------- PRINT HELPERS --------
    def _print_now_playing(self, song):
        title = song.get('title') or os.path.basename(song.get('path', ''))
        print(f"Now playing: {title} ({_fmt_mmss(self.current_duration)})")
        self._print_next_eta()

    def _print_crossfade_start(self, next_song):
        title = next_song.get('title') or os.path.basename(next_song.get('path', ''))
        print(f"Crossfading for {int(self.crossfade_duration)}s "
              f"→ Next: {title} (@ {_fmt_clock(time.time())})")

    def _print_next_eta(self):
        nxt = self._get_next_song()
        if not nxt:
            return
        if self.current_start_ts is None or self.current_duration is None:
            print(f"Next up (start time unknown): {nxt.get('title') or os.path.basename(nxt.get('path',''))}")
            return
        est_start = self.current_start_ts + max(0.0, self.current_duration - self.crossfade_duration)
        title = nxt.get('title') or os.path.basename(nxt.get('path', ''))
        print(f"Next up at {_fmt_clock(est_start)}: {title}")

    # -------- PUBLIC CONTROLS --------
    def play_song_immediately(self, song):
        """Stops the queue and plays a specified song right away."""
        with self.immediate_lock:
            self.immediate_playback = True
        self._cancel_crossfade_if_any()

        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(song['path'])
            pygame.mixer.music.set_volume(1.0)
            self.current_duration = _get_duration_seconds(song['path'])
            self.current_start_ts = time.time()
            pygame.mixer.music.play(fade_ms=2000)

            self.current_song = song
            self._print_now_playing(song)

            Clock.schedule_once(lambda dt: self.update_now_playing(song))
            while pygame.mixer.music.get_busy() and not self.skip_flag.is_set():
                time.sleep(0.1)
        except Exception as e:
            print(f"Error playing immediate song '{song.get('title','?')}': {e}")
        finally:
            pygame.mixer.music.stop()
            self.skip_flag.clear()
            with self.immediate_lock:
                self.immediate_playback = False
            Clock.schedule_once(lambda dt: self.update_now_playing(self.current_song))
            Clock.schedule_once(lambda dt: self.update_upcoming_songs())

    def play_songs(self):
        """Main playback loop, runs in a separate thread."""
        while True:
            try:
                # If mixer has been shut down, exit this thread cleanly
                if not pygame.mixer.get_init():
                    print("Mixer not initialized; exiting play_songs loop.")
                    break

                with self.immediate_lock:
                    if self.immediate_playback:
                        time.sleep(0.2)
                        continue
                    
                if (not pygame.mixer.music.get_busy()) and (not self._crossfade_channel().get_busy()):
                    next_song_to_play = self._get_next_song()
                    if next_song_to_play:
                        self._play_or_crossfade(next_song_to_play)
                    else:
                        time.sleep(0.5)
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"FATAL Error in play_songs loop: {e}")


    def play_special_song(self):
        """Initiates the special 'First Dance' song in its own thread."""
        threading.Thread(target=self._handle_special_song_playback, daemon=True).start()

    def skip_current_song(self):
        """Skip anything currently playing (music or crossfade channel)."""
        self.skip_flag.set()
        self._cancel_crossfade_if_any()
        pygame.mixer.music.stop()
        self._crossfade_channel().stop()

    # -------- AMBIENT MUSIC (separate from jukebox queues) --------
    def start_ambient_music(self, folder="ambiant"):
        """
        Start looping random mp3 files from the given folder on a dedicated
        mixer channel. This does NOT touch any jukebox playlists.
        """
        # Don't start twice
        if self.ambient_thread and self.ambient_thread.is_alive():
            return

        self.ambient_stop_event.clear()
        self.ambient_thread = threading.Thread(
            target=self._ambient_loop, args=(folder,), daemon=True
        )
        self.ambient_thread.start()

    def stop_ambient_music(self):
        """Stop any ambient music currently playing."""
        self.ambient_stop_event.set()
        try:
            pygame.mixer.Channel(AMBIENT_CHANNEL_IDX).stop()
        except Exception:
            pass

    def _ambient_loop(self, folder):
        """Internal loop that plays random ambient tracks until stopped."""
        files = []
        for root, _, fs in os.walk(folder):
            for f in fs:
                if f.lower().endswith(".mp3"):
                    files.append(os.path.join(root, f))

        if not files:
            print(f"[Ambient] No mp3 files found in folder '{folder}'")
            return

        ch = pygame.mixer.Channel(AMBIENT_CHANNEL_IDX)

        while not self.ambient_stop_event.is_set():
            path = random.choice(files)
            try:
                snd = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"[Ambient] Error loading '{path}': {e}")
                continue

            ch.play(snd)
            # Wait until this track finishes or stop is requested
            while ch.get_busy() and not self.ambient_stop_event.is_set():
                time.sleep(0.1)

        ch.stop()

    # -------- TEST MUSIC (separate from jukebox queues) --------
    def play_test_songs(self, songs):
        """
        Play the given list of songs (dicts with 'path') one after another
        on a dedicated mixer channel, without touching any jukebox queues.
        Does NOT trigger or resume main playback when finished.
        """
        threading.Thread(
            target=self._play_test_songs_worker,
            args=(songs,),
            daemon=True,
        ).start()

    def _play_test_songs_worker(self, songs):
        # Use a dedicated channel so it doesn't interfere with pygame.mixer.music
        ch = pygame.mixer.Channel(TEST_CHANNEL_IDX)

        # Make sure nothing is playing on this channel before starting
        ch.stop()

        for song in songs:
            path = song.get("path")
            if not path:
                continue

            try:
                snd = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"[TEST] Error loading '{path}': {e}")
                continue

            title = song.get("title") or os.path.basename(path)
            print(f"[TEST] Playing: {title}")

            ch.play(snd)

            # Wait until this test track finishes
            while ch.get_busy():
                time.sleep(0.1)

        # When done, stop the test channel and DO NOTHING ELSE.
        ch.stop()
        print("[TEST] Finished 2-song test playback; jukebox NOT resumed.")


    # -------- CORE LOGIC --------
    def _get_next_song(self):
        """Peek the next song WITHOUT removing it (thread-safe)."""
        with self.queue_lock:
            is_special_slot = (self.song_counter % 5 == 0 and self.song_counter != 0)
            if is_special_slot and self.Special_playlist:
                return self.Special_playlist[0]
            if self.primary_playlist:
                return self.primary_playlist[0]
            if self.default_playlist:
                return self.default_playlist[0]
            if self.Special_playlist:
                return self.Special_playlist[0]
            return None

    def _pop_next_song(self):
        """Pop and return the next song according to queueing rules (thread-safe)."""
        with self.queue_lock:
            is_special_slot = (self.song_counter % 5 == 0 and self.song_counter != 0)
            if is_special_slot and self.Special_playlist:
                return self.Special_playlist.pop(0)
            if self.primary_playlist:
                return self.primary_playlist.pop(0)
            if self.default_playlist:
                return self.default_playlist.pop(0)
            if self.Special_playlist:
                return self.Special_playlist.pop(0)
            return None


    def _play_or_crossfade(self, song):
        """
        If something is already on the music channel, crossfade to the new song.
        Otherwise, just play it immediately on the music channel.
        """
        try:
            # Actually consume the head of the queue for playback now
            song = self._pop_next_song() or song

            if pygame.mixer.music.get_busy():
                # Start crossfade to 'song' in a separate thread
                if not self.crossfade_active:
                    self._print_crossfade_start(song)
                    self.crossfade_thread = threading.Thread(
                        target=self._crossfade_to, args=(song, self.crossfade_duration), daemon=True
                    )
                    self.crossfade_thread.start()
            else:
                # No music playing: normal start
                pygame.mixer.music.load(song['path'])
                pygame.mixer.music.set_volume(1.0)
                self.current_duration = _get_duration_seconds(song['path'])
                self.current_start_ts = time.time()
                pygame.mixer.music.play(fade_ms=2000)

                self.song_counter += 1
                self.played_songs.add(song.get('title', song.get('path', '')))
                self.current_song = song

                self._print_now_playing(song)

                Clock.schedule_once(lambda dt: self.update_now_playing(song))
                Clock.schedule_once(lambda dt: self.update_upcoming_songs())

                while pygame.mixer.music.get_busy() and not self.skip_flag.is_set():
                    time.sleep(0.1)
        except Exception as e:
            print(f"Error playing song '{song.get('title','?')}': {e}")
        finally:
            if not self.crossfade_active:
                pygame.mixer.music.stop()
                self.skip_flag.clear()

    def _crossfade_to(self, next_song, duration):
        """
        Crossfade from current pygame.mixer.music (out) to next_song (in) over `duration` seconds.
        """
        with self.crossfade_lock:
            if self.crossfade_active:
                return
            self.crossfade_active = True

        try:
            # Prepare next song as a Sound on a dedicated channel
            try:
                next_sound = pygame.mixer.Sound(next_song['path'])
            except Exception as e:
                print(f"[Crossfade] Could not load as Sound; falling back: {e}")
                pygame.mixer.music.fadeout(int(duration * 2000))  # gentle but shorter
                pygame.mixer.music.stop()
                pygame.mixer.music.load(next_song['path'])
                self.current_duration = _get_duration_seconds(next_song['path'])
                self.current_start_ts = time.time()
                pygame.mixer.music.set_volume(1.0)
                pygame.mixer.music.play(fade_ms=2000)
                self._mark_now_playing(next_song)
                self._print_now_playing(next_song)
                while pygame.mixer.music.get_busy() and not self.skip_flag.is_set():
                    time.sleep(0.1)
                return

            out_start_vol = pygame.mixer.music.get_volume()
            in_start_vol = 0.0

            ch = self._crossfade_channel()
            ch.stop()
            ch.set_volume(in_start_vol)
            ch.play(next_sound, loops=0)

            # set track timing for the incoming song
            self.current_duration = _get_duration_seconds(next_song['path'])
            self.current_start_ts = time.time()

            self._mark_now_playing(next_song)
            self._print_now_playing(next_song)

            steps = max(1, int(duration / 0.05))  # 50 ms per step
            for i in range(steps):
                if self.skip_flag.is_set():
                    break
                t = (i + 1) / steps
                pygame.mixer.music.set_volume(max(0.0, out_start_vol * (1.0 - t)))
                ch.set_volume(min(1.0, t))
                time.sleep(0.05)

            pygame.mixer.music.set_volume(0.0)
            ch.set_volume(1.0)

            pygame.mixer.music.stop()
            pygame.mixer.music.set_volume(1.0)

            while ch.get_busy() and not self.skip_flag.is_set():
                time.sleep(0.1)

        except Exception as e:
            print(f"[Crossfade] Error: {e}")
        finally:
            if self.skip_flag.is_set():
                self._crossfade_channel().stop()
            self.skip_flag.clear()
            with self.crossfade_lock:
                self.crossfade_active = False

    def _crossfade_channel(self):
        return pygame.mixer.Channel(CROSSFADE_CHANNEL_IDX)

    def _mark_now_playing(self, song):
        """Bookkeeping + GUI updates when switching to a new song."""
        self.song_counter += 1
        self.played_songs.add(song.get('title', song.get('path', '')))
        self.current_song = song
        Clock.schedule_once(lambda dt: self.update_now_playing(song))
        Clock.schedule_once(lambda dt: self.update_upcoming_songs())

    def _handle_special_song_playback(self):
        """Playback logic for the special song."""
        with self.immediate_lock:
            self.immediate_playback = True
        self._cancel_crossfade_if_any()
        pygame.mixer.music.stop()
        self._crossfade_channel().stop()

        album_art_bytes = None
        if os.path.exists('0R3A0809.jpg'):
            with open('0R3A0809.jpg', "rb") as f:
                album_art_bytes = f.read()

        song = {
            'path': 'I_am_a_test.mp3',
            'title': 'The First Dance',
            'artists': ["Nicki's Mix"],
            'genres': ['Pop', 'Christmas'],
            'album_art': album_art_bytes,
            'key': 'start_song'
        }
        
        try:
            pygame.mixer.music.load(song['path'])
            pygame.mixer.music.set_volume(1.0)
            self.current_duration = _get_duration_seconds(song['path'])
            self.current_start_ts = time.time()
            pygame.mixer.music.play()
            self.current_song = song

            self._print_now_playing(song)
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

    def _cancel_crossfade_if_any(self):
        with self.crossfade_lock:
            if self.crossfade_active:
                self.skip_flag.set()

def _fmt_mmss(seconds):
    if seconds is None:
        return "??:??"
    m = int(seconds // 60)
    s = int(round(seconds % 60))
    return f"{m:02d}:{s:02d}"

def _fmt_clock(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts))

def _get_duration_seconds(path):
    try:
        mf = MutagenFile(path)
        if mf and mf.info and getattr(mf.info, "length", None):
            return float(mf.info.length)
    except Exception:
        pass
    # Fallback to pygame Sound length (may be inaccurate for some formats)
    try:
        snd = pygame.mixer.Sound(path)
        return float(snd.get_length())
    except Exception:
        return None

