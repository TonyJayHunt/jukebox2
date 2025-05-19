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


# ------- main ---------------------------------------------------------------

df = pd.read_csv("./useful_tools/file_list_updated.csv")

for idx, row in df[df["Genre"].isna()].iterrows():
    genre = fetch_genre(row["Search_Query"])
    if genre:
        df.at[idx, "Genre"] = genre
        print(f"✓ {row['Title']}  →  {genre}")
    else:
        print(f"✗ {row['Title']}  (no genre found)")

    time.sleep(0.5)        # stay friendly to Wikipedia

df.to_csv("file_list_updated_with_genre.csv", index=False)
print("\nSaved → file_list_updated_with_genre.csv")
