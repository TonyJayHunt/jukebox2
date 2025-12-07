import os
import csv
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

def extract_files_to_csv(directory_path, csv_filename):
    """
    Extracts a list of files from the specified directory and writes them into a CSV file.
    For MP3 files, attempts to extract title and artist metadata.

    Parameters:
        directory_path (str): The path to the directory.
        csv_filename (str): The name of the CSV file to write.
    """
    entries = os.listdir(directory_path)
    files_only = [entry for entry in entries if os.path.isfile(os.path.join(directory_path, entry))]

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Filename', 'Title', 'Artist'])  # Write headers

        for filename in files_only:
            full_path = os.path.join(directory_path, filename)
            title = ''
            artist = ''

            if filename.lower().endswith('.mp3'):
                try:
                    audio = EasyID3(full_path)
                    title = audio.get('title', [''])[0]
                    artist = audio.get('artist', [''])[0]
                except Exception:
                    # fallback if ID3 tags can't be read
                    pass

            csvwriter.writerow([filename, title, artist])

# Example usage
if __name__ == '__main__':
    directory = "./mp3_1"  # Replace with your directory path
    csv_output = './file_list.csv'
    extract_files_to_csv(directory, csv_output)
    print(f"File list extracted to {csv_output}")
