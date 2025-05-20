
# -*- coding: utf-8 -*-
"""Jukebox GUI – Christmas theme, v3.5
Fully corrected: all scrollbars use classic tk.Scrollbar (supporting width=50).
"""
import tkinter as tk
from tkinter import ttk, font as tkfont
from PIL import Image, ImageTk
import io
from typing import List

COLOUR = {
    'background':  '#b22020',
    'accent':      '#d4af37',
    'button_bg':   '#f6f1e4',
    'button_fg':   '#0d5727',
    'positive':    '#5fe273',
    'negative':    '#fc8181',
}

SCROLLBAR_KWARGS = dict(
    orient='vertical',
    width=50,
    bg=COLOUR['button_bg'],
    troughcolor='#f6f1e4',
    activebackground=COLOUR['button_fg'],
)


class JukeboxGUI:
    BASE_WIDTH = 1280
    def __init__(self, root, select_song_cb, dance_cb, player):
        self.root = root
        self.root.configure(bg=COLOUR['background'])
        self.select_song = select_song_cb
        self.play_special_song = dance_cb
        self.player = player

        self.all_songs: List[dict] = []
        self.hidden_song_keys = set()
        self.song_buttons = {}
        self.playback_started = False

        self.genre_var = tk.StringVar(value='All')
        self.artist_var = tk.StringVar(value='All')
        self.genre_filter_var = self.genre_var
        # alias for legacy code
        self.artist_filter_var = self.artist_var

        self._create_frames()
        self._define_fonts()
        self._create_widgets()
        self._setup_bindings()
        self._on_resize()

    # frames
    def _create_frames(self):
        self.filter_frame = tk.Frame(self.root, bg=COLOUR['background'])
        self.filter_frame.place(relx=0, rely=0, relwidth=0.2, relheight=1)
        self.now_frame = tk.Frame(self.root, bg=COLOUR['background'])
        self.now_frame.place(relx=0.2, rely=0, relwidth=0.6, relheight=1)
        self.select_frame = tk.Frame(self.root, bg=COLOUR['background'])
        self.select_frame.place(relx=0.8, rely=0, relwidth=0.2, relheight=1)

    # fonts + scaling
    def _define_fonts(self):
        self.fonts = {
            'header': tkfont.Font(family='Times', size=40, weight='bold'),
            'label': tkfont.Font(family='Helvetica', size=18),
            'button': tkfont.Font(family='Garamond', size=16, weight='bold'),
        }

    def _scale(self, pts):
        w = max(self.root.winfo_width(), self.BASE_WIDTH)
        return int(pts * w / self.BASE_WIDTH)
    def _on_resize(self, *_):
        self.fonts['header']['size'] = self._scale(40)
        self.fonts['label']['size'] = self._scale(18)
        self.fonts['button']['size'] = self._scale(16)

    # widgets
    def _create_widgets(self):
        self._create_filter_widgets()
        self._create_now_widgets()
        self._create_song_widgets()

    def _style_button(self, widget, kind='normal'):
        bg = COLOUR['button_bg']; fg = COLOUR['button_fg']
        if kind=='positive': bg = COLOUR['positive']; fg='black'
        if kind=='negative': bg = COLOUR['negative']; fg='black'
        widget.config(font=self.fonts['button'], bg=bg, fg=fg,
                      activebackground=bg, relief=tk.RAISED, bd=4,
                      padx=14, pady=6, highlightthickness=0)

    # filter column
    def _create_filter_widgets(self):
        outer = tk.Frame(self.filter_frame, bg=COLOUR['background'])
        outer.pack(fill='both', expand=True, padx=(16,0))
        tk.Label(outer,text='Select an Artist',font=self.fonts['label'],
                 bg=COLOUR['background'],fg=COLOUR['accent']).pack(pady=(20,5))
        style = ttk.Style(); style.configure('Juke.TCombobox', fieldbackground=COLOUR['button_bg'], background=COLOUR['button_bg'], foreground=COLOUR['button_fg']);
        self.artist_combo = ttk.Combobox(outer, textvariable=self.artist_var,
                                         state='readonly', height=10,
                                         font=self.fonts['button'], style='Juke.TCombobox')
        self.artist_combo.pack(fill='x', pady=(0,5))
        self.artist_combo.bind('<<ComboboxSelected>>',
                               lambda e: self.genre_var.set('All'))

        self.clear_btn = tk.Button(outer, text='Clear Filter',
                                   command=lambda: self.artist_var.set('All'))
        self._style_button(self.clear_btn, 'negative')
        self.clear_btn.pack_forget()

        # genre list
        container = tk.Frame(outer, bg=COLOUR['background'])
        container.pack(fill='both', expand=True, pady=(10,30))
        self.genre_canvas = tk.Canvas(container, bg=COLOUR['background'],
                                      highlightthickness=0)
        gbar = tk.Scrollbar(container, command=self.genre_canvas.yview, **SCROLLBAR_KWARGS)
        self.genre_canvas.configure(yscrollcommand=gbar.set)
        gbar.pack(side='right', fill='y')
        self.genre_canvas.pack(side='left', fill='both', expand=True)
        self.genre_frame = tk.Frame(self.genre_canvas, bg=COLOUR['background'])
        self.genre_canvas.create_window((0,0), window=self.genre_frame, anchor='nw')

    # now playing
    def _create_now_widgets(self):
        ctl = tk.Frame(self.now_frame, bg=COLOUR['background'])
        ctl.pack(side='top', pady=10)
        self.dance_btn = tk.Button(ctl, text="Let's Dance",
                                   command=self._handle_dance)
        self._style_button(self.dance_btn,'positive'); self.dance_btn.pack(side='left',padx=10)
        self.skip_btn = tk.Button(ctl,text='Skip',command=self._handle_skip)
        self._style_button(self.skip_btn,'negative'); self.skip_btn.pack(side='left',padx=10)

        inner = tk.Frame(self.now_frame, bg=COLOUR['background'])
        inner.pack(fill='both', expand=True)
        tk.Label(inner,text='Now Playing',font=self.fonts['header'],
                 bg=COLOUR['background'],fg=COLOUR['accent']).pack(pady=10)
        self.art_label = tk.Label(inner,bg='#E4E2E2')
        self.art_label.pack(pady=(0,10),ipadx=10,ipady=10)
        self.info_label = tk.Label(inner,text='',font=self.fonts['label'],
                                   bg=COLOUR['background'],fg=COLOUR['accent'])
        self.info_label.pack()

        self.up_canvas = tk.Canvas(inner,bg=COLOUR['background'],highlightthickness=0)
        ubar = tk.Scrollbar(inner, command=self.up_canvas.yview, **SCROLLBAR_KWARGS)
        self.up_canvas.configure(yscrollcommand=ubar.set)
        ubar.pack(side='right',fill='y'); self.up_canvas.pack(side='left',fill='both',expand=True)
        self.up_frame = tk.Frame(self.up_canvas, bg=COLOUR['background'])
        self.up_canvas.create_window((0,0),window=self.up_frame,anchor='nw')

    # song selection
    def _create_song_widgets(self):
        outer = tk.Frame(self.select_frame, bg=COLOUR['background'])
        outer.pack(fill='both', expand=True, padx=(0,16))
        self.sel_canvas = tk.Canvas(outer,bg=COLOUR['background'],highlightthickness=0)
        sbar = tk.Scrollbar(outer, command=self.sel_canvas.yview, **SCROLLBAR_KWARGS)
        self.sel_canvas.configure(yscrollcommand=sbar.set)
        sbar.pack(side='right',fill='y'); self.sel_canvas.pack(side='left',fill='both',expand=True)
        self.button_frame = tk.Frame(self.sel_canvas,bg=COLOUR['background'])
        self.sel_canvas.create_window((0,0),window=self.button_frame,anchor='nw')

    # bindings
    def _setup_bindings(self):
        self.root.bind('<Configure>', self._on_resize)
        self.genre_frame.bind('<Configure>', lambda e: self.genre_canvas.configure(scrollregion=self.genre_canvas.bbox('all')))
        self.up_frame.bind('<Configure>', lambda e: self.up_canvas.configure(scrollregion=self.up_canvas.bbox('all')))
        self.button_frame.bind('<Configure>', lambda e: self.sel_canvas.configure(scrollregion=self.sel_canvas.bbox('all')))
        self.genre_var.trace_add('write', self._filters_changed)
        self.artist_var.trace_add('write', self._filters_changed)

    # filter helpers
    def _filters_changed(self,*_):
        self.clear_btn.pack(pady=(0,10),fill='x') if self.artist_var.get()!='All' else self.clear_btn.pack_forget()
        self.display_songs()

    def populate_artist_combobox(self, artists):
        self.artist_combo['values'] = ['All'] + artists; self.artist_var.set('All')
    def populate_genre_buttons(self, genres):
        for w in self.genre_frame.winfo_children(): w.destroy()
        for genre in ['All']+genres:
            b=tk.Button(self.genre_frame,text=genre.upper(),command=lambda g=genre:self.set_genre_filter(g))
            self._style_button(b); b.pack(pady=3,fill='x')
        self.set_genre_filter('All')
    def set_genre_filter(self, genre):
        self.artist_var.set('All')
        self.genre_var.set(genre)

    # song list display
    def display_songs(self):
        for w in self.button_frame.winfo_children(): w.destroy()
        self.song_buttons.clear()
        gfilter=self.genre_var.get().lower(); afilter=self.artist_var.get()
        for song in self.all_songs:
            if song['key'] in self.hidden_song_keys: continue
            if song['title'] in self.player.played_songs: continue
            if song['title'] in getattr(self.player,'selected_songs',set()): continue
            if not (gfilter=='all' or gfilter in [g.lower() for g in song['genres']]): continue
            if not(afilter=='All' or song['artist']==afilter): continue
            lbl=f"{song['title']}\n{song['artist']}"
            btn=tk.Button(self.button_frame,text=lbl,
                          command=lambda s=song:self._select_song(s), wraplength=260, justify='center')
            self._style_button(btn); btn.pack(pady=6,fill='x')
            self.song_buttons[song['key']]=btn
        self.button_frame.update_idletasks()
        self.sel_canvas.configure(scrollregion=self.sel_canvas.bbox('all'))
        self.sel_canvas.yview_moveto(0)
        
    def _select_song(self,song):
        self.select_song(song); self.hidden_song_keys.add(song['key'])
        b=self.song_buttons.pop(song['key'],None)
        if b: b.destroy()
        
    def update_song_buttons(self):
        for k,b in list(self.song_buttons.items()):
            if k in self.player.played_songs:
                b.destroy(); self.song_buttons.pop(k,None)
    # upcoming + now playing placeholders

    def update_upcoming_songs(self, upcoming):
        for w in self.up_frame.winfo_children():
            w.destroy()
        for song in upcoming:
            txt = f"{song['artist']} - {song['title']}"
            tk.Label(self.up_frame, text=txt, font=self.fonts['label'],
                        bg=COLOUR['background'], fg=COLOUR['accent']).pack(anchor='n', padx=20, pady=2)
        # refresh scrollregion
        self.up_frame.update_idletasks()
        self.up_canvas.configure(scrollregion=self.up_canvas.bbox('all'))


    def update_now_playing(self, song):
        """Display album art (max 300 px) and song/artist title."""
        self.info_label.config(text=f"{song['artist']} – {song['title']}")
        max_px = 300
        if song.get('album_art'):
            try:
                img = Image.open(io.BytesIO(song['album_art']))
                img.thumbnail((max_px, max_px), Image.LANCZOS)
                ph = ImageTk.PhotoImage(img)
                self.art_label.config(image=ph, text='')
                self.art_label.image = ph
            except Exception:
                self.art_label.config(image='', text='[No art]')
        else:
            self.art_label.config(image='', text='[No art]')

    def update_up_next(self): pass

    # handlers
    def _handle_dance(self):
        if not self.playback_started:
            self.playback_started=True; self.dance_btn.pack_forget(); self.play_special_song()
    def _handle_skip(self):
        if hasattr(self.player,'skip_current_song'): self.player.skip_current_song()
