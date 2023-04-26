import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.dom import minidom
from urllib.parse import quote
from natsort import natsorted

def rename_files_in_directory(directory, episode_pattern, title_pattern, use_names_txt):
    count = 0

    with open(os.path.join(directory, 'rename_log.txt'), 'w', encoding='utf-8') as log_file:
        if use_names_txt:
            with open(os.path.join(directory, 'names.txt'), 'r', encoding='utf-8') as f:
                names = [re.split(r'\s+', line.strip(), maxsplit=1) for line in f.readlines()]

        for i, filename in enumerate(natsorted(os.listdir(directory))):
            if filename.endswith('.mp4'):
                if use_names_txt and i < len(names):
                    file_extension = os.path.splitext(filename)[-1]
                    new_name = names[i][0] + " - " + re.sub(r'\s+\(.*\)', '', names[i][1]) + file_extension
                else:
                    episode_search = re.search(episode_pattern, filename)
                    title_search = re.search(title_pattern, filename)
                    if episode_search and title_search:
                        episode_number = episode_search.group(1)
                        title = title_search.group(1)
                        new_name = f"{episode_number} - {title}{file_extension}"
                    else:
                        new_name = f"{i+1:02d} - {os.path.splitext(filename)[0]}{file_extension}"
                os.rename(os.path.join(directory, filename), os.path.join(directory, new_name))
                count += 1
                status_var.set(f"Renamed: {count} files")
                log_file.write(f"{filename} -> {new_name}\n")
                root.update()
    return count


def undo_renaming():
    directory = folder_path.get()
    log_path = os.path.join(directory, 'rename_log.txt')

    if not os.path.exists(log_path):
        messagebox.showerror("Error", "rename_log.txt not found")
        return

    with open(log_path, 'r', encoding='utf-8') as log_file:
        lines = log_file.readlines()

    count = 0
    for line in lines:
        old_name, new_name = line.strip().split(' -> ')
        os.rename(os.path.join(directory, new_name), os.path.join(directory, old_name))
        count += 1

    messagebox.showinfo("Result", f"Undid renaming of {count} files")

def toggle_input_fields():
    use_names_txt = use_names_txt_var.get()
    if use_names_txt:
        episode_entry.configure(state='disabled')
        title_entry.configure(state='disabled')
    else:
        episode_entry.configure(state='normal')
        title_entry.configure(state='normal')

def browse_directory():
    folder_selected = filedialog.askdirectory()
    folder_path.set(folder_selected)

def start_renaming():
    directory = folder_path.get()
    episode_pattern = episode_entry.get()
    title_pattern = title_entry.get()
    use_names_txt = use_names_txt_var.get()

    count = rename_files_in_directory(directory, episode_pattern, title_pattern, use_names_txt)
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

# Checkbox for using names.txt
use_names_txt_var = tk.BooleanVar()
names_txt_checkbox = ttk.Checkbutton(root, text="Use names.txt", variable=use_names_txt_var, command=toggle_input_fields)
names_txt_checkbox.grid(row=6, column=1)

# Add the "Undo" button after the "Create Playlist" button
undo_button = tk.Button(root, text="Undo", command=undo_renaming)
undo_button.grid(row=4, column=2)


# Run the GUI
root.mainloop()
