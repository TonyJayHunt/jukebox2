import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io
import os

class JukeboxGUI:
    def __init__(self, root, select_song_callback, play_special_song_callback, player):
        self.root = root
        self.select_song = select_song_callback
        self.play_special_song = play_special_song_callback
        self.player = player
        self.all_songs = []
        self.genre_filter_var = tk.StringVar(value='All')
        self.artist_filter_var = tk.StringVar(value='All')
        self.song_buttons = {}
        self.hidden_song_keys = set()
        self._setup_styles()
        self._create_frames()
        self._create_widgets()
        self._setup_bindings()
        self.filter_bg = None
        self.song_selection_bg = None
        self.now_playing_bg = None
        self.filter_image = None
        self.selection_image = None
        self.now_playing_image = None
        self.filter_bg_label = None
        self.song_selection_bg_label = None
        self.now_playing_bg_label = None
        self.playback_started = False

    def _setup_styles(self):
        self.filter_label_font = ('Helvetica', 16, 'bold')
        self.filter_entry_font = ('Helvetica', 14)
        self.button_font = ('Garamond', 14, 'bold')
        self.info_font = ('Helvetica', 14)
        self.header_font = ('Helvetica', 18, 'bold')

    def _create_frames(self):
        self.filter_frame = tk.Frame(self.root, bd=2)
        self.filter_frame.place(relx=0, rely=0, relwidth=0.2, relheight=1)
        self.now_playing_frame = tk.Frame(self.root, bd=2)
        self.now_playing_frame.place(relx=0.2, rely=0, relwidth=0.5, relheight=1)
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.place(relx=0.7, rely=0, relwidth=0.3, relheight=1)

    def _create_widgets(self):
        self._create_filter_widgets()
        self._create_now_playing_widgets()
        self._create_song_list_widgets()

    def _create_filter_widgets(self):
        self._load_filter_background()
        tk.Label(self.filter_frame, text='Select An Artist',
                 font=self.header_font, bg=self.filter_frame.cget('bg')).pack(pady=10)
        self.artist_combobox = ttk.Combobox(
            self.filter_frame,
            textvariable=self.artist_filter_var,
            values=[],
            font=self.filter_entry_font)
        self.artist_combobox.pack(pady=5)

        # Clear Filter Button - not packed initially
        self.clear_artist_filter_btn = tk.Button(
            self.filter_frame,
            text='Clear Filter',
            font=('Helvetica', 12, 'bold'),
            command=self._clear_artist_filter,
            bg='#ffcccc',
            fg='black'
        )
        self.clear_artist_filter_btn.pack_forget()

        tk.Label(self.filter_frame, text='Select A Genre',
                 font=self.header_font, bg=self.filter_frame.cget('bg')).pack(pady=10)

        # This frame will take up all remaining space
        self.genre_canvas_frame = tk.Frame(self.filter_frame)
        self.genre_canvas_frame.pack(fill='both', expand=True)
        self.genre_canvas = tk.Canvas(self.genre_canvas_frame, bg=self.filter_frame.cget('bg'), highlightthickness=0)
        self.genre_scrollbar = tk.Scrollbar(
            self.genre_canvas_frame, orient='vertical', command=self.genre_canvas.yview)
        self.genre_scrollbar.pack(side='right', fill='y')
        self.genre_canvas.pack(side='left', fill='both', expand=True)
        self.genre_canvas.configure(yscrollcommand=self.genre_scrollbar.set)
        self.genre_button_frame = tk.Frame(self.genre_canvas, bg=self.filter_frame.cget('bg'))
        self.genre_canvas.create_window((0, 0), window=self.genre_button_frame, anchor='nw')
        self.genre_button_frame.bind('<Configure>', lambda e: self.genre_canvas.configure(
            scrollregion=self.genre_canvas.bbox("all")
        ))

    def _create_now_playing_widgets(self):
        self._load_now_playing_background()
        self.now_playing_inner_frame = tk.Frame(self.now_playing_frame, bg=self.now_playing_frame.cget('bg'))
        self.now_playing_inner_frame.place(relx=0.5, rely=0.3, anchor='center')
        tk.Label(self.now_playing_inner_frame, text='Now Playing',
                 font=self.header_font, bg=self.now_playing_inner_frame.cget('bg')).pack(pady=10)
        # Album art and song info in a vertical box
        self.art_and_info_frame = tk.Frame(self.now_playing_inner_frame, bg=self.now_playing_inner_frame.cget('bg'))
        self.art_and_info_frame.pack()
        self.album_art_label = tk.Label(self.art_and_info_frame, bg=self.now_playing_inner_frame.cget('bg'))
        self.album_art_label.pack(pady=(0, 10))
        self.song_info_label = tk.Label(self.art_and_info_frame, text='',
                                        font=self.info_font, bg=self.now_playing_inner_frame.cget('bg'))
        self.song_info_label.pack(pady=0)
        self.up_next_label = tk.Label(self.now_playing_inner_frame, text='',
                                      font=self.info_font, bg=self.now_playing_inner_frame.cget('bg'))
        self.up_next_label.pack(pady=10)
        # Spacer
        self.spacer = tk.Frame(self.now_playing_frame, height=30, bg=self.now_playing_frame.cget('bg'))
        self.spacer.place(relx=0.5, rely=0.55, anchor='n', relwidth=1)
        self.upcoming_songs_label = tk.Label(
            self.now_playing_frame,
            text='Upcoming Songs',
            font=self.header_font,
            bg=self.now_playing_frame.cget('bg')
        )
        self.upcoming_songs_label.place(relx=0.5, rely=0.57, anchor='n')
        self.upcoming_songs_label.config(pady=10)
        self.upcoming_frame = tk.Frame(self.now_playing_frame, bg=self.now_playing_frame.cget('bg'))
        self.upcoming_frame.place(relx=0.5, rely=0.62, anchor='n',
                                  relwidth=1, relheight=0.23)
        self.upcoming_canvas = tk.Canvas(self.upcoming_frame, highlightthickness=0, bg=self.upcoming_frame.cget('bg'))
        self.upcoming_scrollbar = tk.Scrollbar(
            self.upcoming_frame,
            orient='vertical',
            command=self.upcoming_canvas.yview,
            width=25,
            troughcolor="#bbbbbb",
            bg="#333333",
            activebackground="#222222"
        )
        self.upcoming_scrollbar.pack(side='right', fill='y')
        self.upcoming_canvas.pack(side='left', fill='both', expand=True)
        self.upcoming_canvas.configure(yscrollcommand=self.upcoming_scrollbar.set)
        self.upcoming_list_frame = tk.Frame(self.upcoming_canvas, bg=self.upcoming_canvas.cget('bg'))
        self.upcoming_canvas.create_window((0, 0), window=self.upcoming_list_frame, anchor='nw')
        self.button_frame_np = tk.Frame(self.now_playing_frame, bg=self.now_playing_frame.cget('bg'))
        self.button_frame_np.place(relx=0.5, rely=0.9, anchor='center')
        self.dance_button = tk.Button(
            self.button_frame_np,
            text="Let's Dance",
            font=self.info_font,
            command=self._handle_dance_button,
            bg='lightgreen',
            fg='black',
            relief='raised',
            padx=20,
            pady=10)
        self.dance_button.pack(pady=10)
        # Add the Skip button if needed
        self.skip_button = tk.Button(
            self.button_frame_np,
            text="Skip",
            font=self.info_font,
            command=self._handle_skip_button if hasattr(self, '_handle_skip_button') else None,
            bg='#ffcccc',
            fg='black',
            relief='raised',
            padx=20,
            pady=10)
        self.skip_button.pack(pady=10)

    def _create_song_list_widgets(self):
        self._load_song_selection_background()
        self.canvas = tk.Canvas(self.buttons_frame, bg=self.buttons_frame.cget('bg'))
        self.scrollbar = tk.Scrollbar(
            self.buttons_frame,
            orient='vertical',
            command=self.canvas.yview,
            width=25,
            troughcolor="#bbbbbb",
            bg="#333333",
            activebackground="#222222"
        )
        self.scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.button_frame = tk.Frame(self.canvas, bg=self.canvas.cget('bg'))
        self.canvas.create_window((0, 0), window=self.button_frame, anchor='nw')

    def _setup_bindings(self):
        self.button_frame.bind('<Configure>', self._on_frame_configure)
        self.upcoming_list_frame.bind('<Configure>', self._on_upcoming_frame_configure)
        self.genre_filter_var.trace_add('write', self._on_filter_change)
        self.artist_filter_var.trace_add('write', self._on_filter_change)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_upcoming_frame_configure(self, event):
        self.upcoming_canvas.configure(scrollregion=self.upcoming_canvas.bbox('all'))

    def _on_filter_change(self, *args):
        self.clear_artist_filter_btn.pack_forget()
        if self.artist_filter_var.get() != 'All':
            self.clear_artist_filter_btn.pack(pady=(5, 5))
        self.display_songs()

    def _clear_artist_filter(self):
        self.artist_filter_var.set('All')
        self.display_songs()

    def _handle_dance_button(self):
        if not self.playback_started:
            self.playback_started = True
            self.dance_button.destroy()
            self.play_special_song()

    def update_song_buttons(self):
        for song_key, button in self.song_buttons.items():
            if song_key in self.player.played_songs:
                button.config(state=tk.DISABLED)
            else:
                button.config(state=tk.NORMAL)

    def display_songs(self):
        for widget in self.button_frame.winfo_children():
            widget.destroy()
        self.song_buttons.clear()
        genre_filter = self.genre_filter_var.get()
        artist_filter = self.artist_filter_var.get()
        filtered_songs = []
        for song in self.all_songs:
            if song['key'] in self.hidden_song_keys:
                continue
            if ((genre_filter == 'All' or
                 genre_filter.lower() in song['genres']) and
                song['title'] not in self.player.played_songs and
                'christmas' not in song['genres'] and
                (artist_filter == 'All' or
                 song['artist'] == artist_filter)):
                filtered_songs.append(song)
        for song in filtered_songs:
            song_name = f"{song['title']}\n{song['artist']}"
            btn = tk.Button(self.button_frame, text=song_name,
                            font=self.button_font,
                            fg='black',
                            bg='white',
                            command=lambda s=song: self.select_song(s),
                            relief='raised',
                            anchor='center',
                            justify='center',
                            wraplength=300,
                            padx=10,
                            pady=10)
            btn.pack(pady=5, padx=5, fill='both', expand=True)
            self.song_buttons[song['key']] = btn
        self.update_song_buttons()
        self.button_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def update_upcoming_songs(self, upcoming_songs):
        for widget in self.upcoming_list_frame.winfo_children():
            widget.destroy()
        for song in upcoming_songs:
            song_info = f"{song['artist']} - {song['title']}"
            if 'christmas' in song['genres']:
                song_info += " 🎄"
            label = tk.Label(
                self.upcoming_list_frame, text=song_info,
                font=self.info_font,
                anchor='center',
                justify='center',
                bg=self.upcoming_list_frame.cget('bg'),
                padx=5, pady=5)
            label.pack(anchor='center', fill='x', padx=20)
        self.upcoming_list_frame.update_idletasks()
        self.upcoming_canvas.config(scrollregion=self.upcoming_canvas.bbox('all'))

    def update_now_playing(self, song):
        song_info = f"{song['artist']} - {song['title']}"
        self.song_info_label.config(text=song_info)
        # Set a max size for album art
        max_size = 320  # px
        if song['album_art']:
            image_data = song['album_art']
            try:
                image = Image.open(io.BytesIO(image_data))
                image.thumbnail((max_size, max_size), Image.LANCZOS)
                album_art = ImageTk.PhotoImage(image)
                self.album_art_label.config(image=album_art)
                self.album_art_label.image = album_art
                self.album_art_label.config(text='')
            except Exception as e:
                print(f"Error loading album art: {e}")
                self.album_art_label.config(image='', text='No Album Art')
                self.album_art_label.image = None
        else:
            self.album_art_label.config(image='', text='No Album Art')
            self.album_art_label.image = None

    def populate_genre_buttons(self, genres):
        for widget in self.genre_button_frame.winfo_children():
            widget.destroy()
        genres.insert(0, 'All')
        for genre in genres:
            btn = tk.Button(self.genre_button_frame, text=genre.title(),
                            command=lambda g=genre: self.set_genre_filter(g),
                            font=('Helvetica', 12),
                            fg='gold',
                            bg='black',
                            relief='flat',
                            padx=10,
                            pady=5,
                            height=1,
                            width=18)
            btn.pack(pady=3, fill='x')
        self.genre_filter_var.set('All')

    def populate_artist_combobox(self, artists):
        self.artist_combobox['values'] = artists
        self.artist_filter_var.set('All')

    def set_genre_filter(self, genre):
        self.genre_filter_var.set(genre)
        self.display_songs()

    def _load_song_selection_background(self):
        try:
            img_path = './christmastree.jpg'
            if not os.path.exists(img_path):
                self.buttons_frame.config(bg='red')
                return
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.selection_image = Image.open(img_path)
            self.selection_image = self.selection_image.resize(
                (int(screen_width * 0.3), screen_height), Image.LANCZOS)
            self.song_selection_bg = ImageTk.PhotoImage(self.selection_image)
            if hasattr(self, 'song_selection_bg_label') and self.song_selection_bg_label:
                self.song_selection_bg_label.destroy()
            self.song_selection_bg_label = tk.Label(
                self.buttons_frame, image=self.song_selection_bg)
            self.song_selection_bg_label.place(relwidth=1, relheight=1)
            self.song_selection_bg_label.lower()
        except Exception as e:
            print(f"Error loading selection background image: {e}")
            self.buttons_frame.config(bg='SystemButtonFace')

    def _load_now_playing_background(self):
        try:
            img_path = './fairylights.jpg'
            if not os.path.exists(img_path):
                self.now_playing_frame.config(bg='red')
                return
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.now_playing_image = Image.open(img_path)
            self.now_playing_image = self.now_playing_image.resize(
                (int(screen_width * 0.5), screen_height), Image.LANCZOS)
            self.now_playing_bg = ImageTk.PhotoImage(self.now_playing_image)
            if hasattr(self, 'now_playing_bg_label') and self.now_playing_bg_label:
                self.now_playing_bg_label.destroy()
            self.now_playing_bg_label = tk.Label(
                self.now_playing_frame, image=self.now_playing_bg)
            self.now_playing_bg_label.place(relwidth=1, relheight=1)
            self.now_playing_bg_label.lower()
        except Exception as e:
            print(f"Error loading now playing background image: {e}")
            self.now_playing_frame.config(bg='SystemButtonFace')

    def _load_filter_background(self):
        try:
            img_path = './bauble.jpg'
            if not os.path.exists(img_path):
                self.filter_frame.config(bg='red')
                return
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.filter_image = Image.open(img_path)
            self.filter_image = self.filter_image.resize(
                (int(screen_width * 0.2), screen_height), Image.LANCZOS)
            self.filter_bg = ImageTk.PhotoImage(self.filter_image)
            if hasattr(self, 'filter_bg_label') and self.filter_bg_label:
                self.filter_bg_label.destroy()
            self.filter_bg_label = tk.Label(
                self.filter_frame, image=self.filter_bg)
            self.filter_bg_label.place(relwidth=1, relheight=1)
            self.filter_bg_label.lower()
        except Exception as e:
            print(f"Error loading filter background image: {e}")
            self.filter_frame.config(bg='SystemButtonFace')

    def update_up_next(self):
        pass

    # Optionally add skip support
    def _handle_skip_button(self):
        if hasattr(self.player, "skip_current_song"):
            self.player.skip_current_song()
