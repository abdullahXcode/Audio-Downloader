#!/usr/bin/env python3
"""
Local Music Downloader for Arch Linux
Downloads audio from a URL you are authorized to download, converts it to MP3,
embeds thumbnail artwork and saves a separate JPG cover image.
"""

import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class MusicDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Downloader")
        self.root.geometry("620x440")
        self.root.minsize(560, 400)
        self.events = queue.Queue()
        self.downloading = False

        main = ttk.Frame(root, padding=22)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Music Downloader", font=("Sans", 20, "bold")).pack(anchor="w")
        ttk.Label(
            main,
            text="Save authorized audio as MP3 with embedded artwork and a separate JPG.",
            wraplength=560
        ).pack(anchor="w", pady=(5, 18))

        ttk.Label(main, text="Audio URL").pack(anchor="w")
        self.url_var = tk.StringVar(value="")
        self.url_entry = ttk.Entry(main, textvariable=self.url_var)
        self.url_entry.pack(fill="x", pady=(5, 14))

        ttk.Label(main, text="Save folder").pack(anchor="w")
        folder_row = ttk.Frame(main)
        folder_row.pack(fill="x", pady=(5, 14))
        self.folder_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        ttk.Entry(folder_row, textvariable=self.folder_var).pack(side="left", fill="x", expand=True)
        ttk.Button(folder_row, text="Browse…", command=self.choose_folder).pack(side="left", padx=(8, 0))

        self.download_btn = ttk.Button(main, text="Download MP3 + artwork", command=self.start_download)
        self.download_btn.pack(fill="x", ipady=7, pady=(2, 12))

        self.progress = ttk.Progressbar(main, mode="indeterminate")
        self.progress.pack(fill="x", pady=(0, 10))

        self.status_var = tk.StringVar(value="Ready. Paste a URL and click Download.")
        ttk.Label(main, textvariable=self.status_var, wraplength=560).pack(anchor="w")

        ttk.Label(
            main,
            text="Note: Only download material you own or have permission to download. "
                 "The source must provide an accessible thumbnail for the JPG.",
            wraplength=560,
            foreground="#777777"
        ).pack(anchor="w", side="bottom", pady=(20, 0))

        self.root.after(100, self.process_events)

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get() or os.path.expanduser("~"))
        if folder:
            self.folder_var.set(folder)

    def start_download(self):
        if self.downloading:
            return
        url = self.url_var.get().strip()
        folder = os.path.expanduser(self.folder_var.get().strip())
        if not url:
            messagebox.showwarning("Missing URL", "Please paste an audio URL.")
            return
        if not folder:
            messagebox.showwarning("Missing folder", "Please choose a save folder.")
            return
        if yt_dlp is None:
            messagebox.showerror(
                "yt-dlp Python module missing",
                "Install it with:\n  sudo pacman -S yt-dlp ffmpeg\n"
                "Then launch this app again."
            )
            return
        os.makedirs(folder, exist_ok=True)
        self.downloading = True
        self.download_btn.configure(state="disabled")
        self.progress.start(12)
        self.status_var.set("Starting download…")

        thread = threading.Thread(target=self.download_worker, args=(url, folder), daemon=True)
        thread.start()

    def download_worker(self, url, folder):
        def hook(data):
            status = data.get("status")
            if status == "downloading":
                percent = data.get("_percent_str", "").strip()
                speed = data.get("_speed_str", "").strip()
                eta = data.get("_eta_str", "").strip()
                message = "Downloading"
                if percent:
                    message += f" {percent}"
                if speed:
                    message += f" • {speed}"
                if eta:
                    message += f" • ETA {eta}"
                self.events.put(("status", message))
            elif status == "finished":
                self.events.put(("status", "Audio downloaded; converting and embedding artwork…"))

        options = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(folder, "%(title).180B.%(ext)s"),
            "noplaylist": True,
            "cookiesfrombrowser": ("chrome",),
            "writethumbnail": True,
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"},
                {"key": "FFmpegThumbnailsConvertor", "format": "jpg"},
                {"key": "EmbedThumbnail"},
                {"key": "FFmpegMetadata"},
            ],
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title") or "Downloaded audio"
            self.events.put(("done", title))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def process_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "status":
                    self.status_var.set(payload)
                elif kind == "done":
                    self.progress.stop()
                    self.downloading = False
                    self.download_btn.configure(state="normal")
                    self.status_var.set(f"Finished: {payload}")
                    messagebox.showinfo(
                        "Download complete",
                        f"Saved MP3 with embedded artwork and a separate JPG (if provided):\n\n"
                        f"{self.folder_var.get()}"
                    )
                elif kind == "error":
                    self.progress.stop()
                    self.downloading = False
                    self.download_btn.configure(state="normal")
                    self.status_var.set("Download failed.")
                    messagebox.showerror("Download failed", payload)
        except queue.Empty:
            pass
        self.root.after(100, self.process_events)


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicDownloader(root)
    root.mainloop()

