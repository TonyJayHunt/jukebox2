import io
from PIL import Image as PILImage
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivy.core.text import LabelBase
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from kivy.uix.widget import Widget

LabelBase.register(name="EmojiFont", fn_regular=".\\assets\\font\\seguiemj.ttf")

class CreamLabel(BoxLayout):
    """A custom label with a solid cream-colored background."""
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, height=30)
        with self.canvas.before:
            Color(1, 0.99, 0.9, 1)  # Cream
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.label = Label(
            text=kwargs.get('text', ''),
            font_size=kwargs.get('font_size', 30),
            markup=True,
            color=kwargs.get('color', (0.15, 0.15, 0.15, 1)),
            valign='middle',
            halign='center'
        )
        self.add_widget(self.label)
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        
class JukeboxGUI(BoxLayout):
    all_songs = ListProperty()
    hidden_song_keys = ListProperty()
    played_songs = ListProperty()
    selected_songs = ListProperty()
    artist_filter = StringProperty('All')
    genre_filter = StringProperty('All')
    player = ObjectProperty()
    select_song_cb = ObjectProperty()
    dance_cb = ObjectProperty()
    # NEW:
    test_cb = ObjectProperty()
    play_ambient_cb = ObjectProperty()
    stop_ambient_cb = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', padding=10, spacing=10, **kwargs)

        # --- Left Column: Filters ---
        self.filter_box = BoxLayout(orientation='vertical', size_hint=(.2, 1), spacing=10)
        self.filter_box.add_widget(Label(text='[b]Select An Artist[/b]', markup=True, color=(0.15, 0.15, 0.15, 1), font_size=30, size_hint_y=None, height=30))
        self.artist_spinner = Spinner(text='All', values=['All'], size_hint_y=None, height=44, background_color=(0.5, 1, 0.5, 1))
        self.artist_spinner.bind(text=self.on_artist_selected)
        self.filter_box.add_widget(self.artist_spinner)

        self.filter_box.add_widget(Label(text='[b]Select A Genre[/b]', markup=True, color=(0.15, 0.15, 0.15, 1), font_size=30, size_hint_y=None, height=30))
        self.genre_scroll = ScrollView(size_hint=(1, 0.6))
        self.genre_buttons_box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.genre_buttons_box.bind(minimum_height=self.genre_buttons_box.setter('height'))
        self.genre_scroll.add_widget(self.genre_buttons_box)
        self.filter_box.add_widget(self.genre_scroll)

        self.clear_btn = Button(text='Clear Artist Filter', size_hint_y=None, height=40, on_press=lambda x: self.set_artist_filter('All'), background_color=(1,0.4,0.4,1), opacity=0, disabled=True)
        self.filter_box.add_widget(self.clear_btn)
        self.add_widget(self.filter_box)

        # --- Middle Column: Now Playing / Upcoming ---
        self.middle_box = BoxLayout(orientation='vertical', size_hint=(.6, 1), spacing=10)
        self.middle_box.add_widget(Label(text='NOW PLAYING', font_size=40, color=(0.15, 0.15, 0.15, 1), size_hint_y=None, height=50))
        self.album_art = KivyImage(size_hint_y=None, height=200)
        self.middle_box.add_widget(self.album_art)
        self.info_label = Label(text='No song playing', size_hint_y=None, height=40, font_name="EmojiFont", font_size=30, color=(0.15, 0.15, 0.15, 1))
        self.middle_box.add_widget(self.info_label)
        
        self.ctl_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=110,
            spacing=10
        )

        # ----------------- ROW 1 -----------------
        self.row1 = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            spacing=10
        )

        self.dance_btn = Button(
            text="Let's Dance!",
            size_hint=(None, None),
            width=160,
            height=44,
            on_press=self.handle_dance,
            background_color=(0.5, 1, 0.5, 1),
        )
        # Hide this physical button – it will be triggered by the bauble hotspot instead.
        self.dance_btn.opacity = 0
        self.dance_btn.disabled = True

        self.test_btn = Button(
            text="Test Music",
            size_hint=(None, None),
            width=140,
            height=44,
            on_press=self.handle_test,
            background_color=(1, 0.8, 0.4, 1),
        )

        # Don't add the Let’s Dance button to row1; only Test Music is visible
        # self.row1.add_widget(self.dance_btn)
        self.row1.add_widget(self.test_btn)

        # ----------------- ROW 2 -----------------
        self.row2 = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            spacing=10
        )

        self.play_ambient_btn = Button(
            text="Play Ambient Music",
            size_hint=(None, None),
            width=180,
            height=44,
            on_press=self.handle_play_ambient,
            background_color=(0.6, 0.8, 1, 1),
        )

        self.stop_ambient_btn = Button(
            text="Stop Ambient Music",
            size_hint=(None, None),
            width=180,
            height=44,
            on_press=self.handle_stop_ambient,
            background_color=(1, 0.6, 0.6, 1),
        )

        self.row2.add_widget(self.play_ambient_btn)
        self.row2.add_widget(self.stop_ambient_btn)

        # Add rows to main control layout
        self.ctl_box.add_widget(self.row1)
        self.ctl_box.add_widget(self.row2)

        # Add control box to UI
        self.middle_box.add_widget(self.ctl_box)

        self.middle_box.add_widget(Label(text='UP NEXT:', font_size=30, color=(0.15, 0.15, 0.15, 1), size_hint_y=None, height=30))
        self.middle_box.add_widget(Widget(size_hint_y=None, height=10))
        self.upcoming_scroll = ScrollView(size_hint=(1, .3))
        self.upcoming_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.upcoming_grid.bind(minimum_height=self.upcoming_grid.setter('height'))
        self.upcoming_scroll.add_widget(self.upcoming_grid)
        self.middle_box.add_widget(self.upcoming_scroll)
        self.add_widget(self.middle_box)

        # --- Right Column: Song Selection ---
        self.select_box = BoxLayout(orientation='vertical', size_hint=(.2, 1), spacing=10)
        self.select_box.add_widget(CreamLabel(text='[b]SELECT A SONG[/b]', font_size=30, markup=True))
        self.songs_scroll = ScrollView()
        self.songs_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.songs_grid.bind(minimum_height=self.songs_grid.setter('height'))
        self.songs_scroll.add_widget(self.songs_grid)
        self.select_box.add_widget(self.songs_scroll)
        self.add_widget(self.select_box)

    def emoji_for(self, genres):
        EMOJI_BY_GENRE = {"christmas":"🎄", "special":"🎅", "britpop":"🕶️", "country":"🤠", "dance":"💃", "disco":"🪩", "edm":"🎧", "hip-hop":"🎤", "indie":"🎸", "pop":"🎙️", "r&b":"🎷", "rock":"🤘", "ska":"🎺", "reggae":"🌴"}
        gset = {g.strip().lower() for g in genres or []}
        if "hip hop" in gset or "hiphop" in gset: gset.add("hip-hop")
        if "rnb" in gset: gset.add("r&b")
        return next((emoji for genre, emoji in EMOJI_BY_GENRE.items() if genre in gset), "🎵")

    def _get_joined_artists(self, song):
        """Returns a comma-separated string of artists for a song."""
        return ", ".join(song.get('artists', ['Unknown Artist']))

    def clear_filter(self):
        self.artist_filter = 'All'
        self.genre_filter = 'All'
        self.artist_spinner.text = 'All'
        for btn in self.genre_buttons_box.children:
            btn.background_color = (1,0.4,0.4,1) # Reset to normal color
        self.clear_btn.opacity = 0
        self.clear_btn.disabled = True
        self.display_songs()

    def populate_artists(self, artists):
        self.artist_spinner.values = ['All'] + artists

    def populate_genres(self, genres):
        self.genre_buttons_box.clear_widgets()
        all_btn = Button(text="🎵 ALL", size_hint_y=None, font_name="EmojiFont", height=40, background_color=(1,0.4,0.4,1), on_press=lambda x: self.set_genre_filter('All'))
        self.genre_buttons_box.add_widget(all_btn)
        for genre in genres:
            btn = Button(text=f"{self.emoji_for([genre])} {genre.title()}", font_name="EmojiFont", background_color=(1,0.4,0.4,1), size_hint_y=None, height=40, on_press=lambda instance, g=genre: self.set_genre_filter(g))
            self.genre_buttons_box.add_widget(btn)

    def set_artist_filter(self, artist):
        self.genre_filter = 'All' # Reset genre filter when artist changes
        self.artist_filter = artist
        self.artist_spinner.text = artist
        self.clear_btn.opacity = 1 if artist != 'All' else 0
        self.clear_btn.disabled = artist == 'All'
        for btn in self.genre_buttons_box.children: # Reset visual highlight on genre buttons
            btn.background_color = (1,0.4,0.4,1)
        self.display_songs()

    def set_genre_filter(self, genre):
        self.genre_filter = genre
        self.artist_filter = 'All' # Reset artist filter when genre changes
        self.artist_spinner.text = 'All'
        # Visual feedback: highlight selected genre button
        for btn in self.genre_buttons_box.children:
            is_selected = btn.text.strip().endswith(genre.title()) or (genre == 'All' and btn.text.endswith('ALL'))
            btn.background_color = (0.5, 1, 0.5, 1) if is_selected else (1,0.4,0.4,1)
        self.display_songs()

    def on_artist_selected(self, spinner, text):
        self.set_artist_filter(text)

    def display_songs(self):
        self.songs_grid.clear_widgets()

        # --- Create a comprehensive set of all song titles to hide ---
        # 1. Get titles of songs already played.
        played_titles = self.player.played_songs

        # 2. Get titles of songs in the active queues (user-selected, and special).
        primary_queued_titles = {song['title'] for song in self.player.primary_playlist}
        special_queued_titles = {song['title'] for song in self.player.Special_playlist}
        
        # 3. Combine them all into a single set for an efficient lookup.
        titles_to_hide = played_titles.union(primary_queued_titles, special_queued_titles)

        for song in self.all_songs:
            # --- Apply all filters ---

            # 1. Hide songs that are played or already in an active queue.
            if song.get('title') in titles_to_hide:
                continue

            # 2. Exclude songs from the 'Special' genre from the main list.
            if 'Special' in song.get('genres', []):
                continue
            
            # 3. Apply the user-selected genre and artist filters.
            if not (self.genre_filter == 'All' or self.genre_filter in song.get('genres', [])):
                continue
            if not (self.artist_filter == 'All' or self.artist_filter in song.get('artists', [])):
                continue

            # If the song passes all filters, create and add its button.
            btn = Button(
                text=f"{self.emoji_for(song.get('genres', []))} {song.get('title')}\n{self._get_joined_artists(song)}",
                font_name="EmojiFont", background_color=(0.53, 0.81, 0.98, 1),
                size_hint_y=None, height=60, halign='center', valign='middle', color=(1, 1, 1, 1), # <-- This is now white
                on_press=lambda instance, s=song: self.handle_song_selection(s)
            )
            # Enable multi-line center alignment by binding text_size
            btn.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
            self.songs_grid.add_widget(btn)

    def handle_song_selection(self, song):
        if self.select_song_cb:
            self.select_song_cb(song)
        # DO NOT update display here. The callback in main.py will handle it after confirmation.
    
    def update_now_playing(self, song=None):
        if not song:
            self.info_label.text = "No song playing"
            self.album_art.texture = None
            return
        
        self.info_label.text = f"{self.emoji_for(song.get('genres', []))} {self._get_joined_artists(song)} – {song.get('title', 'N/A')}"
        self.info_label.font_size = 35 if len(self.info_label.text) < 50 else 25
        
        # Try to load embedded album art first
        if song.get('album_art'):
            try:
                data = io.BytesIO(song['album_art'])
                core_img = CoreImage(data, ext='png') # Assume png, but can be autodetected
                self.album_art.texture = core_img.texture
                return
            except Exception as e:
                print(f"Album art error: {e}")
        
        # Fallback to a random image if no art is found
        import glob, random
        paths = glob.glob("assets/images/us/*")
        if paths:
            try:
                with open(random.choice(paths), "rb") as f:
                    data = io.BytesIO(f.read())
                    core_img = CoreImage(data, ext='png')
                    self.album_art.texture = core_img.texture
            except Exception as e:
                print(f"Fallback art error: {e}")
                self.album_art.texture = None
        else:
            self.album_art.texture = None

    def update_upcoming_songs(self, upcoming):
        self.upcoming_grid.clear_widgets()
        if not upcoming:
            self.upcoming_grid.add_widget(Label(text="No upcoming songs.", font_name="EmojiFont", font_size=20, color=(0.15, 0.15, 0.15, 1)))
            return
        for i, song in enumerate(upcoming):
            self.upcoming_grid.add_widget(Label(
                text=f"{i+1}. {self.emoji_for(song.get('genres', []))} {self._get_joined_artists(song)} - {song.get('title','N/A')}",
                size_hint_y=None, font_size=35, color=(0.15, 0.15, 0.15, 1), height=30, font_name="EmojiFont" 
            ))

    def handle_dance(self, instance):
        # Remove from row1 after it's pressed
        if self.dance_btn.parent:
            self.row1.remove_widget(self.dance_btn)
        if self.dance_cb:
            self.dance_cb()

    # Test button → plays 2 random songs via callback, then disappears
    def handle_test(self, instance):
        # Remove from row1 after it's pressed
        if self.test_btn.parent:
            self.row1.remove_widget(self.test_btn)
        if self.test_cb:
            self.test_cb()

    # Play Ambient button
    def handle_play_ambient(self, instance):
        # Remove from row2 after it's pressed
        if self.play_ambient_btn.parent:
            self.row2.remove_widget(self.play_ambient_btn)
        if self.play_ambient_cb:
            self.play_ambient_cb()

    # Stop Ambient button
    def handle_stop_ambient(self, instance):
        # Remove from row2 after it's pressed
        if self.stop_ambient_btn.parent:
            self.row2.remove_widget(self.stop_ambient_btn)
        if self.stop_ambient_cb:
            self.stop_ambient_cb()


    def handle_skip(self, instance):
        if self.player:
            self.player.skip_current_song()