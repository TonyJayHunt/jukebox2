import re
import time
import pandas as pd
import wikipedia
from bs4 import BeautifulSoup
import requests

# ------- helpers -------------------------------------------------------------

def clean_genre(raw: str) -> str:
    """
    Strip bracketed references, split on commas / pipes / slashes / 'and',
    normalise whitespace, and join with ';'.
    """
    if not isinstance(raw, str):
        return ""
    # drop “[citation needed]”, foot-note refs, etc.
    raw = re.sub(r"\[[^]]+\]", "", raw)
    # unify separators
    parts = re.split(r"\s*(?:/|,|;|\band\b|\|)\s*", raw.strip(), flags=re.I)
    parts = [p.title().strip() for p in parts if p]
    return ";".join(dict.fromkeys(parts))        # keep order, drop dups

def fetch_genre(search_query: str) -> str | None:
    """
    1. Ask the Wikipedia API for the top page that matches the query string.
    2. Look in the infobox for 'Genre'.
    3. If no page or no genre, return None.
    """
    try:
        page = wikipedia.page(search_query, auto_suggest=True, redirect=True)
        html = page.html()
    except (wikipedia.DisambiguationError, wikipedia.PageError):
        return None

    soup = BeautifulSoup(html, "html.parser")
    # in most infoboxes, the 'th' cell literally says "Genre"
    cell = soup.find("th", string=re.compile(r"\bGenre\b", re.I))
    if cell and cell.find_next_sibling("td"):
        raw = cell.find_next_sibling("td").get_text(" ", strip=True)
        return clean_genre(raw)
    return None

def fill_missing_genres(df: pd.DataFrame, query_col="Search_Query", genre_col="Genre", title_col="Title", verbose=True, sleep_time=0.5) -> pd.DataFrame:
    """
    For every row with a missing genre, try to fill it in using Wikipedia.
    """
    for idx, row in df[df[genre_col].isna()].iterrows():
        genre = fetch_genre(row[query_col])
        if genre:
            df.at[idx, genre_col] = genre
            if verbose:
                print(f"✓ {row[title_col]}  →  {genre}")
        else:
            if verbose:
                print(f"✗ {row[title_col]}  (no genre found)")
        time.sleep(sleep_time)  # Be nice to Wikipedia
    return df

def process_file(input_path: str, output_path: str):
    """
    Loads a CSV, fills missing genres, saves the result.
    """
    df = pd.read_csv(input_path)
    df = fill_missing_genres(df)
    df.to_csv(output_path, index=False)
    print(f"\nSaved → {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python update_genre_file.py <input_csv> [output_csv]")
        sys.exit(1)
    in_csv = sys.argv[1]
    out_csv = sys.argv[2] if len(sys.argv) > 2 else "file_list_updated_with_genre.csv"
    process_file(in_csv, out_csv)
