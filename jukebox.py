import os
import io
import tkinter as tk
from tkinter import ttk
import pygame
import threading
import time
import random
from mutagen.id3 import ID3, TIT2, TPE1, TCON, APIC
from PIL import Image, ImageTk

# Initialize pygame mixer
pygame.mixer.init()

def center_window(window):
    window.update_idletasks()
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    window.geometry(f'{window_width}x{window_height}+{x}+{y}')

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
    # Load and play the song with fade-in
    try:
        pygame.mixer.music.load(song_path)
        pygame.mixer.music.play(fade_ms=2000)
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
    root.after(0, update_upcoming_songs)

def confirm_selection(message):
    response = [False]  # Using list to allow modification in nested function
    dialog = tk.Toplevel(root)
    dialog.title("Confirm Selection")
    dialog.geometry("400x200")
    tk.Label(dialog, text=message, font=('Helvetica', 14), wraplength=350, justify='center').pack(pady=20)
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=10)
    def on_yes():
        response[0] = True
        dialog.destroy()
    def on_no():
        dialog.destroy()
    yes_btn = tk.Button(btn_frame, text="Yes", command=on_yes, width=10)
    yes_btn.pack(side='left', padx=10)
    no_btn = tk.Button(btn_frame, text="No", command=on_no, width=10)
    no_btn.pack(side='left', padx=10)
    dialog.transient(root)
    dialog.grab_set()
    center_window(dialog)
    root.wait_window(dialog)
    return response[0]

def select_song(song):
    song_name = song['title']
    if song_name in played_songs:
        tk.messagebox.showinfo("Selection Error", f"'{song_name}' has already been played.")
        return
    if song_name in selected_songs:
        tk.messagebox.showinfo("Selection Error", f"'{song_name}' has already been selected.")
        return

    confirm = confirm_selection(f"Are you sure you want to select '{song_name}'?")
    if confirm:
        if is_abba_song(song):
            confirm_abba = confirm_selection("Are you really sure you want to play Abba at this wedding?")
            if confirm_abba:
                threading.Thread(target=play_song_immediately, args=(song,)).start()
                # Mark as selected and played
                selected_songs.add(song_name)
                played_songs.add(song_name)
                # Disable the button
                def disable_button():
                    if song['key'] in song_buttons:
                        song_buttons[song['key']].config(state=tk.DISABLED)
                root.after(0, disable_button)
                # Remove from playlists if present
                if song in default_playlist:
                    default_playlist.remove(song)
                if song in christmas_playlist:
                    christmas_playlist.remove(song)
                # Update up next
                root.after(0, update_up_next)
                root.after(0, update_upcoming_songs)
        else:
            primary_playlist.append(song)
            selected_songs.add(song_name)
            # Disable the button
            def disable_button():
                if song['key'] in song_buttons:
                    song_buttons[song['key']].config(state=tk.DISABLED)
            root.after(0, disable_button)
            # Remove from playlists if present
            if song in default_playlist:
                default_playlist.remove(song)
            if song in christmas_playlist:
                christmas_playlist.remove(song)
            # If this is the first song selected, update up next
            if len(primary_playlist) == 1:
                update_up_next()
            # Reset filters
            artist_filter_var.set('All')
            genre_filter_var.set('All')
            update_song_list()
            update_upcoming_songs()

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
                song = christmas_playlist.pop(0)
            elif default_playlist:
                song = default_playlist.pop(0)
            else:
                song = None

            if song:
                song_path = song['path']
                try:
                    pygame.mixer.music.load(song_path)
                    pygame.mixer.music.play(fade_ms=2000)
                    if not immediate_playback:
                        song_counter += 1
                    song_name = song['title']
                    played_songs.add(song_name)
                    # Disable the button safely
                    def disable_button():
                        if song['key'] in song_buttons:
                            try:
                                song_buttons[song['key']].config(state=tk.DISABLED)
                            except tk.TclError:
                                pass  # Button might have been destroyed
                    root.after(0, disable_button)
                    # Update now playing info
                    root.after(0, update_now_playing, song)
                    # Update up next info
                    root.after(0, update_up_next)
                    root.after(0, update_upcoming_songs)
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
        'album_art': None,
        'key': 'start_song'
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
    root.after(0, update_upcoming_songs)

def skip_song():
    password = custom_password_dialog("Enter password to skip song:")
    if password == 'jonathan':
        pygame.mixer.music.stop()
        # Update up next after skipping in the main thread
        root.after(0, update_up_next)
        root.after(0, update_upcoming_songs)
    else:
        tk.messagebox.showerror("Incorrect Password", "The password you entered is incorrect.")

def custom_password_dialog(prompt):
    response = [None]
    dialog = tk.Toplevel(root)
    dialog.title("Password")
    dialog.geometry("400x200")
    tk.Label(dialog, text=prompt, font=('Helvetica', 14), wraplength=350, justify='center').pack(pady=20)
    entry_var = tk.StringVar()
    entry = tk.Entry(dialog, textvariable=entry_var, show='*', font=('Helvetica', 14))
    entry.pack(pady=10)
    def on_ok():
        response[0] = entry_var.get()
        dialog.destroy()
    ok_btn = tk.Button(dialog, text="OK", command=on_ok, width=10)
    ok_btn.pack(pady=10)
    dialog.transient(root)
    dialog.grab_set()
    center_window(dialog)
    root.wait_window(dialog)
    return response[0]

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
    """
    Determine the next song to play based on the current playback state and playlists.

    This function checks if an immediate song is playing, then prioritizes songs from the 
    primary playlist, followed by Christmas songs (every 5th song), and finally the default playlist.
    """
    if immediate_playback:
        return None  # Immediate song is playing, next song is not determined yet
    if primary_playlist:
        return primary_playlist[0]
    elif (song_counter) % 5 == 0 and song_counter != 0 and christmas_playlist:
        return christmas_playlist[0]
    elif default_playlist:
        return default_playlist[0]
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
    genre_filter = genre_filter_var.get()
    artist_filter = artist_filter_var.get()
    filtered_songs = []
    for song in all_songs:
        if ((genre_filter == 'All' or genre_filter.lower() in song['genres']) and
            song['title'] not in played_songs and
            'christmas' not in song['genres'] and
            (artist_filter == 'All' or song['artist'] == artist_filter)):
            filtered_songs.append(song)

    for song in filtered_songs:
        song_name = f"{song['title']}\n{song['artist']}"
        btn = tk.Button(button_frame, text=song_name,
                        font=('Garamond', 14, 'bold'),
                        fg='black', bg='white',
                        command=lambda s=song: select_song(s),
                        relief='flat',
                        anchor='center', justify='center', wraplength=300)
        btn.pack(pady=5, padx=5, fill='both', expand=True)
        song_buttons[song['key']] = btn

    # Update the scroll region
    button_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

def update_upcoming_songs():
    global song_counter
    # Initialize song_counter if not defined
    try:
        song_counter
    except NameError:
        song_counter = 1

    # Clear the frame
    for widget in upcoming_list_frame.winfo_children():
        widget.destroy()
    # Get the upcoming songs
    upcoming_songs = []
    # Add primary_playlist
    upcoming_songs.extend(primary_playlist)
    # Determine upcoming songs based on play order
    temp_song_counter = song_counter
    default_playlist_copy = default_playlist.copy()
    christmas_playlist_copy = christmas_playlist.copy()
    while len(upcoming_songs) < 10 and (default_playlist_copy or christmas_playlist_copy):
        if (temp_song_counter % 5 == 0 and temp_song_counter != 0 and christmas_playlist_copy):
            # Add a Christmas song
            song = christmas_playlist_copy.pop(0)
            upcoming_songs.append(song)
        elif default_playlist_copy:
            song = default_playlist_copy.pop(0)
            upcoming_songs.append(song)
        temp_song_counter += 1
    # Display the upcoming songs
    for song in upcoming_songs:
        song_info = f"{song['artist']} - {song['title']}"
        if 'christmas' in song['genres']:
            song_info += " 🎄"
        label = tk.Label(upcoming_list_frame, text=song_info, font=('Helvetica', 12), anchor='center', justify='center')
        label.pack(anchor='center')

# Set up GUI
root = tk.Tk()
root.title("Jukebox")
root.attributes('-fullscreen', True)

# Function to exit full screen
def exit_fullscreen(event=None):
    root.attributes('-fullscreen', False)

# Bind the Esc key to exit full screen
root.bind('<Escape>', exit_fullscreen)

# Variable for genre filter
genre_filter_var = tk.StringVar()

# Variable for artist filter
artist_filter_var = tk.StringVar()

# Load all songs
all_songs = get_all_mp3_files_with_metadata('mp3/')

# Assign a unique key to each song
for idx, song in enumerate(all_songs):
    song['key'] = idx

# Create default and Christmas playlists
default_playlist = [song for song in all_songs if 'christmas' not in song['genres']]
christmas_playlist = [song for song in all_songs if 'christmas' in song['genres']]
primary_playlist = []

selected_songs = set()
played_songs = set()
immediate_playback = False
immediate_lock = threading.Lock()

# Initialize song_counter at global scope
song_counter = 1  # Start at 1 to avoid playing a Christmas song first

# Collect all genres for the buttons
all_genres = set()
for song in all_songs:
    all_genres.update(song['genres'])
if 'unknown genre' in all_genres:
    all_genres.remove('unknown genre')
if 'christmas' in all_genres:
    all_genres.remove('christmas')
genre_list = sorted(all_genres)
genre_list.insert(0, 'All')  # Add 'All' option

# Collect all artists for the dropdown, excluding artists with only Christmas songs
artist_songs = {}
for song in all_songs:
    artist = song['artist']
    if artist not in artist_songs:
        artist_songs[artist] = []
    artist_songs[artist].append(song)

# Filter artists to include only those with non-Christmas songs
valid_artists = [artist for artist, songs in artist_songs.items()
                 if any('christmas' not in song['genres'] for song in songs)]

artist_list = sorted(valid_artists)
artist_list.insert(0, 'All')  # Add 'All' option
artist_filter_var.set('All')

# Set background image and resize it to fit the screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Background for the song selection area (middle frame)
song_selection_bg = None
try:
    selection_image = Image.open('christmastree.jpg')  
    selection_image = selection_image.resize((int(screen_width * 0.3), screen_height), Image.LANCZOS)
    song_selection_bg = ImageTk.PhotoImage(selection_image)
except Exception as e:
    print(f"Error loading selection background image: {e}")

# Background for the now playing section (right frame)
now_playing_bg = None
try:
    now_playing_image = Image.open('fairylights.jpg')  # Ensure correct path to image
    now_playing_image = now_playing_image.resize((int(screen_width * 0.5), screen_height), Image.LANCZOS)
    now_playing_bg = ImageTk.PhotoImage(now_playing_image)
except Exception as e:
    print(f"Error loading now playing background image: {e}")

# Background for the filter section (left frame)
filter_bg = None
try:
    filter_image = Image.open('bauble.jpg')  # Ensure correct path to image
    filter_image = filter_image.resize((int(screen_width * 0.2), screen_height), Image.LANCZOS)
    filter_bg = ImageTk.PhotoImage(filter_image)
except Exception as e:
    print(f"Error loading filter background image: {e}")

# Left frame for filters
filter_frame = tk.Frame(root, bd=2)
filter_frame.place(relx=0, rely=0, relwidth=0.2, relheight=1)

if filter_bg:
    filter_bg_label = tk.Label(filter_frame, image=filter_bg)
    filter_bg_label.place(relwidth=1, relheight=1)
    filter_bg_label.lower()

filter_label_font = ('Helvetica', 16, 'bold')
filter_entry_font = ('Helvetica', 14)

tk.Label(filter_frame, text='Who Is Your Fave', font=('Helvetica', 18, 'bold'), bg=filter_frame['background']).pack(pady=10)

artist_combobox = ttk.Combobox(filter_frame, textvariable=artist_filter_var, values=artist_list, font=('Helvetica', 14))
artist_combobox.pack(pady=5)

tk.Label(filter_frame, text='Select Genre', font=('Helvetica', 18, 'bold')).pack(pady=10)

# Create a frame for genre buttons
genre_button_frame = tk.Frame(filter_frame)
genre_button_frame.pack(pady=5)

def set_genre_filter(selected_genre):
    genre_filter_var.set(selected_genre)
    update_song_list()

for genre in genre_list:
    btn = tk.Button(genre_button_frame, text=genre.title(),
                    command=lambda g=genre: set_genre_filter(g),
                    font=('Helvetica', 12), fg='gold', bg='black',
                    relief='flat', padx=5, pady=5)
    btn.pack(pady=5, fill='x')

genre_filter_var.set('All')

# Middle frame for song buttons
buttons_frame = tk.Frame(root)
buttons_frame.place(relx=0.2, rely=0, relwidth=0.3, relheight=1)


if song_selection_bg:
    selection_bg_label = tk.Label(buttons_frame, image=song_selection_bg)
    selection_bg_label.place(relwidth=1, relheight=1)
    selection_bg_label.lower()
else:
    buttons_frame.config(bg='') 

# Create a canvas and scrollbar
canvas = tk.Canvas(buttons_frame)
scrollbar = ttk.Scrollbar(buttons_frame, orient='vertical', command=canvas.yview)
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

if now_playing_bg:
    now_playing_bg_label = tk.Label(now_playing_frame, image=now_playing_bg)
    now_playing_bg_label.place(relwidth=1, relheight=1)
    now_playing_bg_label.lower()

# Create a frame inside now_playing_frame to center elements
now_playing_inner_frame = tk.Frame(now_playing_frame)
now_playing_inner_frame.place(relx=0.5, rely=0.3, anchor='center')

# Widgets in now playing frame
now_playing_label = tk.Label(now_playing_inner_frame, text='Now Playing', font=('Helvetica', 18, 'bold'))
now_playing_label.pack(pady=10)

album_art_label = tk.Label(now_playing_inner_frame)
album_art_label.pack(pady=10)

song_info_label = tk.Label(now_playing_inner_frame, text='', font=('Helvetica', 14))
song_info_label.pack(pady=10)

# Add Up Next label
up_next_header = tk.Label(now_playing_inner_frame, text='Up Next', font=('Helvetica', 18, 'bold'))
up_next_header.pack(pady=10)

up_next_label = tk.Label(now_playing_inner_frame, text='', font=('Helvetica', 14))
up_next_label.pack(pady=10)

# Upcoming Songs section
upcoming_songs_label = tk.Label(now_playing_frame, text='Upcoming Songs', font=('Helvetica', 18, 'bold'))
upcoming_songs_label.place(relx=0.5, rely=0.55, anchor='n')

# Create a frame for upcoming songs list
upcoming_frame = tk.Frame(now_playing_frame)
upcoming_frame.place(relx=0.5, rely=0.6, anchor='n', relwidth=1, relheight=0.25)

# Create a canvas and scrollbar for upcoming songs
upcoming_canvas = tk.Canvas(upcoming_frame, highlightthickness=0)
upcoming_scrollbar = ttk.Scrollbar(upcoming_frame, orient='vertical', command=upcoming_canvas.yview)
upcoming_scrollbar.pack(side='right', fill='y')
upcoming_canvas.pack(side='left', fill='both', expand=True)
upcoming_canvas.configure(yscrollcommand=upcoming_scrollbar.set)

# Create a frame inside the canvas
upcoming_list_frame = tk.Frame(upcoming_canvas)
upcoming_canvas.create_window((0, 0), window=upcoming_list_frame, anchor='nw')

# Bind the configure event
def on_upcoming_frame_configure(event):
    upcoming_canvas.configure(scrollregion=upcoming_canvas.bbox('all'))

upcoming_list_frame.bind('<Configure>', on_upcoming_frame_configure)

# Skip and Mr Jogin Buttons placed at the bottom of now_playing_frame
button_frame_np = tk.Frame(now_playing_frame)
button_frame_np.place(relx=0.5, rely=0.9, anchor='center')

mr_jogin_button = tk.Button(button_frame_np, text='Mr Jogin', font=('Helvetica', 12),
                            command=play_start_song, bg='lightgrey', fg='grey', relief='flat')
mr_jogin_button.pack(side='left', padx=20)

skip_button = tk.Button(button_frame_np, text='Skip', font=('Helvetica', 12),
                        command=skip_song, bg='lightgrey', fg='grey', relief='flat')
skip_button.pack(side='left', padx=20)

# Trace changes to filters
genre_filter_var.trace('w', update_song_list)
artist_filter_var.trace('w', update_song_list)

# Display songs initially
display_songs()
update_upcoming_songs()

# Start playback thread
play_thread = threading.Thread(target=play_songs)
play_thread.daemon = True
play_thread.start()

root.mainloop()
