
import io
import os
from PIL import Image as PILImage
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivy.core.text import LabelBase
LabelBase.register(name="EmojiFont", fn_regular=".\\assets\\font\\seguiemj.ttf")
from kivy.core.image import Image as CoreImage
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle

class CreamLabel(BoxLayout):
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
            size_hint=(1, 1),
            valign='middle',
            halign='center'
        )
        self.add_widget(self.label)
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        
class JukeboxGUI(BoxLayout):
    def emoji_for(self, genres):
        EMOJI_BY_GENRE = {
            "christmas": "🎄",
            "special":   "🎅",
            "britpop":   "🕶️",
            "country":   "🤠",
            "dance":     "💃",
            "disco":     "🪩",
            "edm":       "🎧",
            "hip-hop":   "🎤",
            "indie":     "🎸",
            "pop":       "🎙️",
            "r&b":       "🎷",
            "rock":      "🤘",
            "ska":       "🎺",
            "reggae":    "🌴"
        }
        gset = {g.strip().casefold() for g in genres or []}
        if "hip hop" in gset or "hiphop" in gset:
            gset.add("hip-hop")
        if "rnb" in gset:
            gset.add("r&b")
        for genre, emoji in EMOJI_BY_GENRE.items():
            if genre in gset:
                return emoji
        return "🎵"

    all_songs = ListProperty()
    hidden_song_keys = ListProperty()
    played_songs = ListProperty()
    selected_songs = ListProperty()
    artist_filter = StringProperty('All')
    genre_filter = StringProperty('All')
    player = ObjectProperty()
    select_song_cb = ObjectProperty()
    dance_cb = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)
        self.padding = 10
        self.spacing = 10

        # Filter/Selection area
        self.filter_box = BoxLayout(orientation='vertical', size_hint=(.2, 1), spacing=10)
        self.add_widget(self.filter_box)

        self.artist_spinner = Spinner(
                                    text='All',
                                    values=['All'],
                                    size_hint_y=None,
                                    height=44,
                                    background_color=(0.5, 1, 0.5, 1)  # <--- Green!
                                )
        self.artist_spinner.bind(text=self.on_artist_selected)
        self.filter_box.add_widget(Label(text='[b]Select AN Artist[/b]', 
                                            size_hint_y=None,
                                            markup=True,
                                            color= (0.15, 0.15, 0.15, 1), 
                                            font_size=30, 
                                            height=30))
        self.filter_box.add_widget(self.artist_spinner)

        
        self.filter_box.add_widget(Label(text='[b]Select A Genre[/b]',
                                            size_hint_y=None,
                                            markup=True,
                                            color= (0.15, 0.15, 0.15, 1), 
                                            font_size=30, 
                                            height=30))
        from kivy.uix.scrollview import ScrollView
        self.genre_scroll = ScrollView(size_hint=(1, 0.6))
        self.genre_buttons_box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.genre_buttons_box.bind(minimum_height=self.genre_buttons_box.setter('height'))
        self.genre_scroll.add_widget(self.genre_buttons_box)
        self.filter_box.add_widget(self.genre_scroll)

        self.clear_btn = Button(
            text='Clear Artist Filter', 
            size_hint_y=None, height=40,
            on_press=lambda x: self.set_artist_filter('All'), 
            background_color=(1,0.4,0.4,1))
        self.clear_btn.opacity = 0  # Start hidden
        self.clear_btn.disabled = True
        self.filter_box.add_widget(self.clear_btn)

        # Now Playing / Upcoming area
        self.middle_box = BoxLayout(orientation='vertical', size_hint=(.6, 1), spacing=10)
        self.add_widget(self.middle_box)
        self.now_playing_label = Label(text='NOW PLAYING', 
                                            font_size=40, 
                                            color=(0.15, 0.15, 0.15, 1),
                                            size_hint_y=None, 
                                            height=50)
        self.middle_box.add_widget(self.now_playing_label)
        self.album_art = KivyImage(size_hint_y=None, height=200)
        self.middle_box.add_widget(self.album_art)
        self.info_label = Label(text='', size_hint_y=None, height=40)
        self.middle_box.add_widget(self.info_label)
        self.ctl_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        self.dance_btn = Button(text="Let's Dance!", 
                                size_hint=(None, None), 
                                width=160, 
                                height=44,
                                on_press=self.handle_dance, 
                                background_color=(0.5,1,0.5,1))
        self.skip_btn = Button(text="Skip Song", 
                               size_hint=(None, None), 
                               width=120, 
                               height=44,
                               on_press=self.handle_skip, 
                               background_color=(1,0.4,0.4,1))
        self.ctl_row.add_widget(self.dance_btn)
        self.ctl_row.add_widget(self.skip_btn)
        self.middle_box.add_widget(self.ctl_row)

        self.middle_box.add_widget(Label(text='UP NEXT:', 
                                         font_size=30, 
                                         color=(0.15, 0.15, 0.15, 1),
                                         size_hint_y=None, 
                                         height=30))
        self.upcoming_scroll = ScrollView(size_hint=(1, .3))
        self.upcoming_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.upcoming_grid.bind(minimum_height=self.upcoming_grid.setter('height'))
        self.upcoming_scroll.add_widget(self.upcoming_grid)
        self.middle_box.add_widget(self.upcoming_scroll)

        # Song selection area
        self.select_box = BoxLayout(orientation='vertical', size_hint=(.2, 1), spacing=10)
        self.add_widget(self.select_box)
        self.select_box.add_widget(CreamLabel(text='[b]SELECT A SONG[/b]', 
                                        font_size=30,
                                        markup=True,
                                        color=(0.15, 0.15, 0.15, 1),
                                        size_hint_y=None, 
                                        height=30))
        self.songs_scroll = ScrollView()
        self.songs_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.songs_grid.bind(minimum_height=self.songs_grid.setter('height'))
        self.songs_scroll.add_widget(self.songs_grid)
        self.select_box.add_widget(self.songs_scroll)

    def populate_artists(self, artists):
        self.artist_spinner.values = ['All'] + artists

    def populate_genres(self, genres):
        self.genre_buttons_box.clear_widgets()
        all_btn = Button(
            text="🎵 ALL", 
            size_hint_y=None,
            font_name="EmojiFont", 
            height=40,
            background_color=(1,0.4,0.4,1),
            on_press=lambda x: self.set_genre_filter('All'))
        self.genre_buttons_box.add_widget(all_btn)
        for genre in genres:
            emoji = self.emoji_for([genre])
            btn = Button(
                text=f"{emoji} {genre.title()}",
                font_name="EmojiFont",
                background_color=(1,0.4,0.4,1),
                size_hint_y=None, 
                height=40,
                on_press=lambda instance, 
                g=genre: self.set_genre_filter(g))
            self.genre_buttons_box.add_widget(btn)

    def set_artist_filter(self, artist):
        self.genre_filter = 'All'
        self.artist_filter = artist
        self.artist_spinner.text = artist

        if hasattr(self, 'clear_btn'):
            if artist != 'All':
                self.clear_btn.opacity = 1
                self.clear_btn.disabled = False
            else:
                self.clear_btn.opacity = 0
                self.clear_btn.disabled = True

        self.genre_buttons_box.children.background_color = (1,0.4,0.4,1)

        self.display_songs()

    def set_genre_filter(self, genre):
        self.genre_filter = genre
        self.artist_filter = 'All'
        self.artist_spinner.text = 'All'
        # Visual feedback: highlight selected genre button
        for btn in self.genre_buttons_box.children:
            btn.background_color = (1,0.4,0.4,1)  
            if btn.text.strip().endswith(genre.title()):
                btn.background_color = (0.5, 1, 0.5, 1)  # Highlight color
            else:
                btn.background_color = (1,0.4,0.4,1)      # Normal color
        self.display_songs()

    def on_artist_selected(self, spinner, text):
        self.set_artist_filter(text)
        

    def on_genre_selected(self, spinner, text):
        self.set_genre_filter(text)
        

    def display_songs(self):
        self.songs_grid.clear_widgets()
        for song in self.all_songs:
            if 'Special' in song.get('genres', []): continue
            if song.get('key') in self.hidden_song_keys: continue
            if song.get('title') in self.played_songs: continue
            if song.get('title') in self.selected_songs: continue
            if not (self.genre_filter == 'All' or self.genre_filter in song.get('genres', [])):
                continue
            if not (self.artist_filter == 'All' or song.get('artist') == self.artist_filter):
                continue
            btn = Button(
                text=f"{self.emoji_for(song.get('genres', []))} {song.get('title')}\n{song.get('artist')}",
                font_name="EmojiFont",
                background_color=(0.53, 0.81, 0.98, 1),
                size_hint_y=None,
                height=60,
                halign='center',   # <--- horizontal center
                valign='middle',   # <--- vertical center (optional)
                color=(1, 1, 1, 1),
                on_press=lambda instance, s=song: self.handle_song_selection(s)
            )
            # Enable multi-line center alignment by setting text_size and binding width
            btn.text_size = (btn.width, None)
            btn.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
            self.songs_grid.add_widget(btn)

    def handle_song_selection(self, song):
        if self.select_song_cb:
            self.select_song_cb(song)
        self.artist_filter = 'All'
        self.genre_filter = 'All'
        self.artist_spinner.text = 'All'
        for btn in self.genre_buttons_box.children:
            btn.background_color = (1,0.4,0.4,1)
        self.display_songs()
    
    
    
    
    def update_now_playing(self, song=None):
        if not song:
            self.info_label.text = "No song playing"
            self.album_art.texture = None
            return
        self.info_label.text = f"{self.emoji_for(song.get('genres', []))} {song.get('artist', 'N/A')} – {song.get('title', 'N/A')}"
        self.info_label.color = (0.15, 0.15, 0.15, 1)
        self.info_label.font_name="EmojiFont"
        self.info_label.font_size=30
        # --- Try direct album art first ---
        if song.get('album_art'):
            try:
                pil_img = PILImage.open(io.BytesIO(song['album_art']))
                data = io.BytesIO()
                pil_img.save(data, format='png')
                data.seek(0)
                core_img = CoreImage(data, ext='png')
                self.album_art.texture = core_img.texture
                return
            except Exception as e:
                print(f"Album art error: {e}")
                # Fallback below
        # --- Fallback to a random image from assets/images/us/ ---
        import glob, random
        paths = glob.glob("assets/images/us/*")
        if paths:
            try:
                with open(random.choice(paths), "rb") as f:
                    pil_img = PILImage.open(f)
                    data = io.BytesIO()
                    pil_img.save(data, format='png')
                    data.seek(0)
                    core_img = CoreImage(data, ext='png')
                    self.album_art.texture = core_img.texture
            except Exception as e:
                print("Fallback art error:", e)
                self.album_art.texture = None
        else:
            self.album_art.texture = None


    def update_upcoming_songs(self, upcoming):
        self.upcoming_grid.clear_widgets()
        if not upcoming:
            self.upcoming_grid.add_widget(Label(text="No upcoming songs.", font_name="EmojiFont", font_size=20,color=(0.15, 0.15, 0.15, 1) ))
            return
        for i, song in enumerate(upcoming):
            self.upcoming_grid.add_widget(Label(
                text=f"{i+1}. {self.emoji_for(song.get('genres', []))} {song.get('artist','N/A')} - {song.get('title','N/A')}",
                size_hint_y=None, 
                font_size=20,
                color=(0.15, 0.15, 0.15, 1),
                height=30,
                font_name="EmojiFont" 
            ))

    def handle_dance(self, instance):
        # Remove button after pressed
        if hasattr(self, 'ctl_row') and hasattr(self, 'dance_btn'):
            self.ctl_row.remove_widget(self.dance_btn)

        if self.dance_cb:
            self.dance_cb()

    def handle_skip(self, instance):
        if hasattr(self.player, 'skip_current_song'):
            self.player.skip_current_song()