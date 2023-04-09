import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.dom import minidom
from urllib.parse import quote

def rename_files_in_directory(directory, episode_pattern, title_pattern):
    count = 0
    for filename in os.listdir(directory):
        if filename.endswith('.mp4'):
            new_name = reformat_name(filename, episode_pattern, title_pattern)
            os.rename(os.path.join(directory, filename), os.path.join(directory, new_name))
            count += 1
            status_var.set(f"Renamed: {count} files")
            root.update()
    return count

def reformat_name(filename, episode_pattern, title_pattern):
    episode_number = re.search(episode_pattern, filename)
    title = re.search(title_pattern, filename)
    
    if episode_number and title:
        episode_number = episode_number.group(1)
        title = title.group(1).replace('.', ' ')
        new_name = f"{episode_number} - {title}.mp4"
        return new_name
    else:
        return filename

def browse_directory():
    folder_selected = filedialog.askdirectory()
    folder_path.set(folder_selected)

def start_renaming():
    directory = folder_path.get()
    episode_pattern = episode_entry.get()
    title_pattern = title_entry.get()

    count = rename_files_in_directory(directory, episode_pattern, title_pattern)
    messagebox.showinfo("Result", f"Renamed {count} files")

def show_help():
    help_text = ("Episode pattern: Regular expression pattern to extract the episode number.\n"
                 "For example: E(\\d+) extracts the episode number after 'E'.\n\n"
                 "Title pattern: Regular expression pattern to extract the title.\n"
                 "For example: \\.(\\D+)\\.German extracts the title between the first period and 'German'.")
    messagebox.showinfo("Help", help_text)

def create_playlist():
    directory = folder_path.get()
    mp4_files = sorted([f for f in os.listdir(directory) if f.endswith('.mp4')])

    playlist = Element('playlist', {'version': '1', 'xmlns': 'http://xspf.org/ns/0/'})
    title = SubElement(playlist, 'title')
    title.text = 'Playlist'

    track_list = SubElement(playlist, 'trackList')

    for mp4_file in mp4_files:
        track = SubElement(track_list, 'track')
        location = SubElement(track, 'location')
        file_path = os.path.join(directory, mp4_file).replace('\\', '/')
        encoded_path = quote(file_path, safe=":/")
        location.text = f'file:///{encoded_path}'

    xml_string = tostring(playlist, 'utf-8')
    pretty_xml = minidom.parseString(xml_string).toprettyxml(indent='  ')

    # Use the folder name for the playlist file
    folder_name = os.path.basename(directory)
    playlist_filename = os.path.join(directory, f'{folder_name}.xspf')

    with open(playlist_filename, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)

    messagebox.showinfo("Result", f"Playlist created as {folder_name}.xspf")

# Default patterns
default_episode_pattern = r'E(\d+)'
default_title_pattern = r'\.(\D+)\.German'

# Create the main window
root = tk.Tk()
root.title("File Renamer")

# Folder selection
folder_path = tk.StringVar()
folder_label = tk.Label(root, text="Folder: ")
folder_label.grid(row=0, column=0)
folder_entry = tk.Entry(root, textvariable=folder_path, width=50)
folder_entry.grid(row=0, column=1)
folder_button = tk.Button(root, text="Browse", command=browse_directory)
folder_button.grid(row=0, column=2)

# Episode pattern input
episode_label = tk.Label(root, text="Episode pattern: ")
episode_label.grid(row=1, column=0)
episode_entry = tk.Entry(root, width=50)
episode_entry.insert(0, default_episode_pattern)
episode_entry.grid(row=1, column=1)

# Title pattern input
title_label = tk.Label(root, text="Title pattern: ")
title_label.grid(row=2, column=0)
title_entry = tk.Entry(root, width=50)
title_entry.insert(0, default_title_pattern)
title_entry.grid(row=2, column=1)

# Start renaming button
start_button = tk.Button(root, text="Start Renaming", command=start_renaming)
start_button.grid(row=3, column=1)

# Help button
help_button = tk.Button(root, text="Help", command=show_help)
help_button.grid(row=3, column=2)

# Create playlist button
create_playlist_button = tk.Button(root, text="Create Playlist", command=create_playlist)
create_playlist_button.grid(row=4, column=1)

# Status bar
status_var = tk.StringVar()
status_bar = tk.Label(root, textvariable=status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_var.set("Ready")
status_bar.grid(row=5, column=0, columnspan=3, sticky=tk.W + tk.E)

# Run the GUI
root.mainloop()
