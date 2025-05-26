import tkinter as tk


GENRE_MAPPING = {
    'britpop': 'Britpop',
    'christmas': 'Christmas',
    'country': 'Country',
    'dance': 'Dance',
    'disco': 'Dance',
    'edm': 'Dance',
    'funk': 'Hip-Hop',
    'hip-hop': 'Hip-Hop',
    'rap': 'Hip-Hop',
    'folk': 'Indie',
    'indie': 'Indie',
    'ska': 'Indie',
    'k-pop': 'Pop',
    'pop': 'Pop',
    'r&b': 'Pop',
    'reggae': 'Pop',
    'punk': 'Rock',
    'rock': 'Rock',
    'alternative rock': 'Rock',
    'Special': 'Special'
}
MAIN_GENRES = ['Britpop', 'Christmas', 'Country', 'Dance', 'Hip-Hop', 'Indie', 'Pop', 'Rock', 'Special']

def normalize_genre(genre):
    """Map any genre to your canonical display genre or 'Pop'."""
    genre_clean = genre.strip().lower()
    return GENRE_MAPPING.get(genre_clean, 'Pop')

def center_window(window):
    """Centers a Tkinter window."""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')