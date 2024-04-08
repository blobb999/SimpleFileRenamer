import os
import re
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.dom import minidom
from urllib.parse import quote
from natsort import natsorted
from bs4 import BeautifulSoup
import requests


def get_series_title(html):
    soup = BeautifulSoup(html, "html.parser")
    serie = soup.find("section", {"class": "serie"})
    h2 = serie.h2
    title = list(h2.children)[0].strip()
    return title


def get_episodes(html):
    soup = BeautifulSoup(html, "html.parser")
    episodes = soup.find("table", {"class": "episodes"}).find_all("tr")

    def episode(tr):
        id = tr.find("a").text.strip()
        title = tr.find("strong").text.strip()
        hosts = list(tr.children)[5]
        hosts = hosts.find_all("a")
        hosts = list(map(
            lambda host: (host["title"], host["href"]), hosts))

        return {
            "id": id,
            "title": title,
            "hosts": hosts
        }

    return list(map(episode, episodes))



def fetch_and_save_titles():
    url = url_entry.get()
    if not url:
        status_text.config(text="Error: Please enter a valid URL.")  # Update status text
        return

    directory = folder_path.get()
    try:
        fetch_button.config(text="Fetching...", state="disabled", bg="green")  # Update button properties
        root.update()  # Update GUI to show button change
        season_html = requests.get(url).text
        series_title = get_series_title(season_html)
        episodes = get_episodes(season_html)

        with open(os.path.join(directory, 'names.txt'), 'w', encoding='utf-8') as file:
            for i, episode in enumerate(episodes, start=1):
                file.write(f"{i:02d} - {episode['title']}\n")

        fetch_button.config(text="Fetch Titles", state="normal", bg="SystemButtonFace")  # Restore button properties
        status_text.config(text="Titles fetched successfully!")  # Update status text
    except Exception as e:
        fetch_button.config(text="Fetch Titles", state="normal", bg="SystemButtonFace")  # Restore button properties
        status_text.config(text=f"Error: {str(e)}")  # Update status text

def rename_files_in_directory(directory, episode_pattern, title_pattern, use_names_txt):
    count = 0
    special_chars = r'[^A-Za-z0-9_. ()-äöüÄÖÜß]+'  # Define special characters here

    with open(os.path.join(directory, 'rename_log.txt'), 'w', encoding='utf-8') as log_file:
        if use_names_txt:
            with open(os.path.join(directory, 'names.txt'), 'r', encoding='utf-8') as f:
                names = [re.split(r'\s+', line.strip(), maxsplit=1) for line in f.readlines()]

        for i, filename in enumerate(natsorted(os.listdir(directory))):
            if filename.endswith('.mp4') or filename.endswith('.mkv') or filename.endswith('.avi'):
                file_extension = os.path.splitext(filename)[-1]
                if use_names_txt and i < len(names):
                    new_name = names[i][0] + " - " + re.sub(r'\s+\(.*\)', '', names[i][1]) + file_extension
                else:
                    episode_search = re.search(episode_pattern, filename)
                    title_search = re.search(title_pattern, filename)
                    if episode_search and title_search:
                        episode_number = episode_search.group(1)
                        title = title_search.group(1)
                        new_name = f"{episode_number:02d} - {title}{file_extension}"
                    else:
                        # Extract filename without episode number
                        file_name_without_episode = re.sub(r'^(\d+)(\s*-\s*)', '', filename)
                        new_name = f"{i+1:02d} - {file_name_without_episode}{file_extension}"

                # Replace special characters
                new_name = re.sub(special_chars, '', new_name)

                # Remove extra hyphens after episode number
                new_name = re.sub(r'(\d+) - - ', r'\1 - ', new_name)

                # Move the file with the new name
                try:
                    os.rename(os.path.join(directory, filename), os.path.join(directory, new_name))
                    count += 1
                    status_var.set(f"Renamed: {count} files")
                    log_file.write(f"{filename} -> {new_name}\n")
                    root.update()
                except OSError as e:
                    messagebox.showerror("Error", f"Failed to rename {filename}: {e}")

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
        new_name_without_extension, extension = os.path.splitext(new_name)
        # Remove ".mp4" extension if it's present in the original name
        old_name_without_extension = old_name.replace('.mp4', '')
        os.rename(os.path.join(directory, new_name), os.path.join(directory, old_name_without_extension + extension))
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

# URL input
url_label = tk.Label(root, text="URL: ")
url_label.grid(row=1, column=0)
url_entry = tk.Entry(root, width=50)
url_entry.grid(row=1, column=1)

# Fetch titles button
fetch_button = tk.Button(root, text="Fetch Titles", command=fetch_and_save_titles)
fetch_button.grid(row=1, column=2)

# Episode pattern input
episode_label = tk.Label(root, text="Episode pattern: ")
episode_label.grid(row=2, column=0)
episode_entry = tk.Entry(root, width=50)
episode_entry.insert(0, default_episode_pattern)
episode_entry.grid(row=2, column=1)

# Title pattern input
title_label = tk.Label(root, text="Title pattern: ")
title_label.grid(row=3, column=0)
title_entry = tk.Entry(root, width=50)
title_entry.insert(0, default_title_pattern)
title_entry.grid(row=3, column=1)

# Start renaming button
start_button = tk.Button(root, text="Start Renaming", command=start_renaming)
start_button.grid(row=4, column=1)

# Status bar
status_var = tk.StringVar()
status_bar = tk.Label(root, textvariable=status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_var.set("Ready")
status_bar.grid(row=7, column=0, columnspan=3, sticky=tk.W + tk.E)


# Checkbox for using names.txt
use_names_txt_var = tk.BooleanVar()
names_txt_checkbox = ttk.Checkbutton(root, text="Use names.txt", variable=use_names_txt_var, command=toggle_input_fields)
names_txt_checkbox.grid(row=6, column=1)

# Status text
status_text = tk.Label(root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_text.grid(row=8, column=0, columnspan=3, sticky=tk.W + tk.E)

# Add the "Undo" button after the "Create Playlist" button
undo_button = tk.Button(root, text="Undo", command=undo_renaming)
undo_button.grid(row=5, column=2)

# Run the GUI
root.mainloop()
