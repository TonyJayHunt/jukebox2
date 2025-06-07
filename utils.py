
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
    'Special': 'Special',
    'hip hop' : 'Hip-Hop',
    'x-mas'   : 'Christmas',
    'alt rock': 'Rock'
}
MAIN_GENRES = ['Britpop', 'Christmas', 'Country', 'Dance', 'Hip-Hop', 'Indie', 'Pop', 'Rock']

def normalize_genre(genre):
    """Map any genre to your canonical display genre or 'Pop'."""
    genre_clean = genre.strip().lower()
    return GENRE_MAPPING.get(genre_clean, 'Pop')

def _index_after_last_user_pick(pl):
    for idx, s in enumerate(pl):
        if s.get('source') != 'user':   # your code may use a flag/key; use any test you like
            return idx
    return len(pl)