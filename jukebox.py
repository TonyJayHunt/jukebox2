import os
import io
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk, simpledialog
import pygame
import threading
import time
import random
from mutagen.id3 import ID3, TIT2, TPE1, TCON, APIC
from PIL import Image, ImageTk

# Initialize pygame mixer
pygame.mixer.init()

# Function to get all MP3 files with metadata
def get_all_mp3_files_with_metadata(directory):
    mp3_files = []
    for root_dir, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.mp3'):
                full_path = os.path.join(root_dir, file)
                try:
                    tags = ID3(full_path)
                    title = tags.get('TIT2', TIT2(text=[os.path.splitext(file)[0]])).text[0]
                    artist = tags.get('TPE1', TPE1(text=['Unknown Artist'])).text[0]
                    genre_str = tags.get('TCON', TCON(text=['Unknown Genre'])).text[0]
                    # Split genres by ';'
                    genres = [g.strip().lower() for g in genre_str.split(';')]
                    # Extract album art if available
                    album_art_data = None
                    for tag in tags.values():
                        if tag.FrameID == 'APIC':
                            album_art_data = tag.data
                            break
                except Exception as e:
                    print(f"Error reading metadata from '{full_path}': {e}")
                    title = os.path.splitext(file)[0]
                    artist = 'Unknown Artist'
                    genres = ['unknown genre']
                    album_art_data = None
                mp3_files.append({
                    'path': full_path,
                    'title': title,
                    'artist': artist,
                    'genres': genres,
                    'album_art': album_art_data
                })
    return mp3_files

def is_abba_song(song):
    return song['artist'].strip().lower() == 'abba'

def play_song_immediately(song):
    global immediate_playback
    song_path = song['path']
    with immediate_lock:
        immediate_playback = True
    # Stop any currently playing song
    pygame.mixer.music.stop()
    # Load and play the song
    try:
        pygame.mixer.music.load(song_path)
        pygame.mixer.music.play()
        # Update now playing info
        root.after(0, update_now_playing, song)
        # Wait for the song to finish before resuming playlist
        while pygame.mixer.music.get_busy():
            time.sleep(1)
    except Exception as e:
        print(f"Error playing song '{song['title']}': {e}")
    finally:
        with immediate_lock:
            immediate_playback = False
    # After immediate playback, update up next
    root.after(0, update_up_next)

def select_song(song):
    song_name = song['title']
    if song_name in played_songs:
        messagebox.showinfo("Selection Error", f"'{song_name}' has already been played.")
        return
    if song_name in selected_songs:
        messagebox.showinfo("Selection Error", f"'{song_name}' has already been selected.")
        return

    confirm = messagebox.askyesno("Confirm Selection", f"Are you sure you want to select '{song_name}'?")
    if confirm:
        primary_playlist.append(song)
        selected_songs.add(song_name)
        # Disable the button
        if song_name in song_buttons:
            song_buttons[song_name].config(state=tk.DISABLED)
        # Remove from playlists if present
        if song in default_playlist:
            default_playlist.remove(song)
        if song in christmas_playlist:
            christmas_playlist.remove(song)
        if is_abba_song(song):
            confirm = messagebox.askyesno("Really??!!", f"Are you really sure you want to play Abba, at this wedding?")
            if confirm:
                threading.Thread(target=play_song_immediately, args=(song,)).start()


def play_songs():
    global immediate_playback, song_counter
    song_counter = 1  # Start at 1 to avoid playing a Christmas song first
    while True:
        with immediate_lock:
            if immediate_playback:
                time.sleep(1)
                continue
        if not pygame.mixer.music.get_busy():
            if primary_playlist:
                song = primary_playlist.pop(0)
            elif song_counter % 5 == 0 and song_counter != 0 and christmas_playlist:
                song = random.choice(christmas_playlist)
                christmas_playlist.remove(song)
            elif default_playlist:
                song = random.choice(default_playlist)
                default_playlist.remove(song)
            else:
                song = None

            if song:
                song_path = song['path']
                try:
                    pygame.mixer.music.load(song_path)
                    pygame.mixer.music.play()
                    if not immediate_playback:
                        song_counter += 1
                    song_name = song['title']
                    played_songs.add(song_name)
                    if song_name in song_buttons:
                        song_buttons[song_name].config(state=tk.DISABLED)
                    # Update now playing info
                    root.after(0, update_now_playing, song)
                    # Update up next info
                    root.after(0, update_up_next)
                    # Wait for the song to finish playing
                    while pygame.mixer.music.get_busy():
                        time.sleep(1)
                except Exception as e:
                    print(f"Error playing song '{song['title']}': {e}")
                    continue  # Move on to the next song
            else:
                time.sleep(1)
        else:
            time.sleep(1)

def play_start_song():
    threading.Thread(target=handle_start_song).start()

def handle_start_song():
    global immediate_playback
    with immediate_lock:
        immediate_playback = True
    # Fade out current song over 5 seconds
    pygame.mixer.music.fadeout(5000)
    # Wait for fadeout to complete
    time.sleep(5)
    # Wait additional 20 seconds
    time.sleep(20)
    # Play the start song
    song_path = 'mp3/Feeder - Buck Rogers.mp3'  # Replace with your start song path
    song = {
        'path': song_path,
        'title': 'Start Song',
        'artist': 'Artist',
        'genres': ['Genre'],
        'album_art': None
    }
    try:
        pygame.mixer.music.load(song_path)
        pygame.mixer.music.play()
        # Update now playing info in the main thread
        root.after(0, update_now_playing, song)
        # Wait for the song to finish playing
        while pygame.mixer.music.get_busy():
            time.sleep(1)
    except Exception as e:
        print(f"Error playing start song: {e}")
    finally:
        with immediate_lock:
            immediate_playback = False
    # Add the start song to played_songs
    played_songs.add(song['title'])
    # Disable the Mr Jogin button in the main thread
    root.after(0, lambda: mr_jogin_button.config(state=tk.DISABLED))
    # Update up next after immediate song in the main thread
    root.after(0, update_up_next)

def skip_song():
    password = simpledialog.askstring("Password", "Enter password to skip song:", show='*')
    if password == 'jonathan':
        pygame.mixer.music.stop()
        # Update up next after skipping in the main thread
        root.after(0, update_up_next)
    else:
        messagebox.showerror("Incorrect Password", "The password you entered is incorrect.")

def update_now_playing(song):
    # Update song info
    song_info = f"{song['artist']} - {song['title']}"
    song_info_label.config(text=song_info)
    # Update album art
    if song['album_art']:
        image_data = song['album_art']
        try:
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((400, 400), Image.LANCZOS)
            album_art = ImageTk.PhotoImage(image)
            album_art_label.config(image=album_art)
            album_art_label.image = album_art  # Keep a reference
            album_art_label.config(text='')  # Clear text if previously set
        except Exception as e:
            print(f"Error loading album art: {e}")
            album_art_label.config(image='', text='No Album Art')
            album_art_label.image = None  # Remove reference to the image
    else:
        # Display a placeholder image or text
        album_art_label.config(image='', text='No Album Art')
        album_art_label.image = None  # Remove reference to the image
    # Update up next info
    update_up_next()

def get_next_song():
    # Determine the next song
    if immediate_playback:
        return None  # Immediate song is playing, next song is not determined yet
    if primary_playlist:
        return primary_playlist[0]
    elif (song_counter + 1) % 5 == 0 and christmas_playlist:
        return random.choice(christmas_playlist)
    elif default_playlist:
        return random.choice(default_playlist)
    else:
        return None

def update_up_next():
    next_song = get_next_song()
    if next_song:
        up_next_info = f"{next_song['artist']} - {next_song['title']}"
        up_next_label.config(text=up_next_info)
    else:
        up_next_label.config(text="")

def update_song_list(*args):
    display_songs()

def display_songs():
    for widget in button_frame.winfo_children():
        widget.destroy()
    song_filter = song_filter_var.get().lower()
    artist_filter = artist_filter_var.get().lower()
    genre_filter = genre_filter_var.get()

    filtered_songs = []
    for song in all_songs:
        if (song_filter in song['title'].lower() and
            artist_filter in song['artist'].lower() and
            (genre_filter == 'All' or genre_filter.lower() in song['genres']) and
            song['title'] not in played_songs):
            filtered_songs.append(song)

    for song in filtered_songs:
        song_name = song['title']
        # Dynamically adjust the button width based on text
        max_chars_per_line = 30
        if len(song_name) > max_chars_per_line:
            song_name_wrapped = '\n'.join([song_name[i:i + max_chars_per_line] for i in range(0, len(song_name), max_chars_per_line)])
        else:
            song_name_wrapped = song_name

        btn = tk.Button(button_frame, text=song_name_wrapped, bg='black', fg='gold',
                        font=('Garamond', 14, 'bold'), width=30, height=2,
                        command=lambda s=song: select_song(s), relief='raised')
        btn.pack(pady=5)
        song_buttons[song_name] = btn

    # Update the scroll region
    button_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

# Set up GUI
root = tk.Tk()
root.title("Jukebox")
root.attributes('-fullscreen', True)

# Function to exit full screen
def exit_fullscreen(event=None):
    root.attributes('-fullscreen', False)

# Bind the Esc key to exit full screen
root.bind('<Escape>', exit_fullscreen)

# Variables for filters
song_filter_var = tk.StringVar()
artist_filter_var = tk.StringVar()
genre_filter_var = tk.StringVar()

# Load all songs
all_songs = get_all_mp3_files_with_metadata('mp3/')
default_playlist = all_songs.copy()
christmas_playlist = [song for song in all_songs if 'christmas' in song['genres']]
primary_playlist = []

selected_songs = set()
played_songs = set()
immediate_playback = False
immediate_lock = threading.Lock()

# Collect all genres for the dropdown
all_genres = set()
for song in all_songs:
    all_genres.update(song['genres'])
if 'unknown genre' in all_genres:
    all_genres.remove('unknown genre')
genre_list = sorted(all_genres)
genre_list.insert(0, 'All')  # Add 'All' option

# Set background image and resize it to fit the screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
background_image = Image.open('fairylights.jpg')  # Ensure correct path to image
background_image = background_image.resize((screen_width, screen_height), Image.LANCZOS)
background_photo = ImageTk.PhotoImage(background_image)
background_label = tk.Label(root, image=background_photo)
background_label.place(relwidth=1, relheight=1)

# Left frame for filters
filter_frame = tk.Frame(root, bd=2)
filter_frame.place(relx=0, rely=0, relwidth=0.2, relheight=1)

filter_label_font = ('Helvetica', 16, 'bold')
filter_entry_font = ('Helvetica', 14)

tk.Label(filter_frame, text='Filters', font=('Helvetica', 18, 'bold')).pack(pady=10)

tk.Label(filter_frame, text='Song:', font=filter_label_font).pack(pady=5)
tk.Entry(filter_frame, textvariable=song_filter_var, font=filter_entry_font).pack(pady=5)

tk.Label(filter_frame, text='Artist:', font=filter_label_font).pack(pady=5)
tk.Entry(filter_frame, textvariable=artist_filter_var, font=filter_entry_font).pack(pady=5)

tk.Label(filter_frame, text='Genre:', font=filter_label_font).pack(pady=5)
genre_filter_var.set('All')
genre_combobox = ttk.Combobox(filter_frame, textvariable=genre_filter_var, values=genre_list, font=filter_entry_font)
genre_combobox.pack(pady=5)

song_filter_var.trace('w', update_song_list)
artist_filter_var.trace('w', update_song_list)
genre_filter_var.trace('w', update_song_list)

# Middle frame for song buttons
buttons_frame = tk.Frame(root)
buttons_frame.place(relx=0.2, rely=0, relwidth=0.3, relheight=1)

# Create a style for the scrollbar
style = ttk.Style()
style.theme_use('default')
style.configure('Vertical.TScrollbar', background='gray', troughcolor='lightgray', bordercolor='black', arrowcolor='black')

# Create a canvas and styled scrollbar
canvas = tk.Canvas(buttons_frame)
scrollbar = ttk.Scrollbar(buttons_frame, orient='vertical', command=canvas.yview, style='Vertical.TScrollbar')
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
canvas.configure(yscrollcommand=scrollbar.set)

# Create a frame inside the canvas
button_frame = tk.Frame(canvas)
canvas.create_window((0, 0), window=button_frame, anchor='nw')

# Bind the configure event
def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox('all'))

button_frame.bind('<Configure>', on_frame_configure)

song_buttons = {}

# Now Playing frame on the right
now_playing_frame = tk.Frame(root, bd=2)
now_playing_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)

# Widgets in now playing frame
now_playing_label = tk.Label(now_playing_frame, text='Now Playing', font=('Helvetica', 18, 'bold'))
now_playing_label.pack(pady=10)

album_art_label = tk.Label(now_playing_frame)
album_art_label.pack(pady=10)

song_info_label = tk.Label(now_playing_frame, text='', font=('Helvetica', 14))
song_info_label.pack(pady=10)

# Add Up Next label
up_next_header = tk.Label(now_playing_frame, text='Up Next', font=('Helvetica', 18, 'bold'))
up_next_header.pack(pady=10)

up_next_label = tk.Label(now_playing_frame, text='', font=('Helvetica', 14))
up_next_label.pack(pady=10)

# Mr Jogin Button (formerly Start) placed at the bottom-right
mr_jogin_button = tk.Button(root, text='Mr Jogin', font=('Helvetica', 12),
                            command=play_start_song, bg='lightgrey', fg='grey', relief='flat')
mr_jogin_button.place(relx=0.9, rely=0.9, anchor='center')

# Skip Button placed next to Mr Jogin in the bottom-right
skip_button = tk.Button(root, text='Skip', font=('Helvetica', 12),
                        command=skip_song, bg='lightgrey', fg='grey', relief='flat')
skip_button.place(relx=0.75, rely=0.9, anchor='center')

# Display songs initially
display_songs()

# Lower the background label to ensure it's at the back
background_label.lower()

# Start playback thread
play_thread = threading.Thread(target=play_songs)
play_thread.daemon = True
play_thread.start()

root.mainloop()
