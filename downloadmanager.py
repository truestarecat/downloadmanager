#!/usr/bin/env python3

from threading import Thread
from urllib.request import Request, urlopen
from enum import Enum
import tkinter as tk
from tkinter import ttk


class Download:
    MAX_CHUNK_SIZE = 1024

    def __init__(self, url):
        super().__init__()
        self._url = url
        self._size = -1  # size of download in bytes
        self._downloaded = 0  # number of bytes downloaded
        self._status = self.Status.DOWNLOADING
        self._download()

    @property
    def url(self):
        return self._url

    @property
    def size(self):
        return self._size

    @property
    def progress(self):
        return int(self._downloaded / self.size * 100)

    @property
    def status(self):
        return self._status

    def _download(self):
        download_thread = Thread(target=self._run, daemon=True)
        download_thread.start()

    def pause(self):
        self._status = self.Status.PAUSED

    def resume(self):
        self._status = self.Status.DOWNLOADING
        self._download()

    def cancel(self):
        self._status = self.Status.CANCELLED

    def _error(self):
        self._status = self.Status.ERROR

    def _run(self):
        try:
            request = Request(self._url)
            request.add_header("Range", f"bytes={self._downloaded}-")
            with urlopen(request) as response:
                content_length = int(response.headers["content-length"])

                if self._size == -1:
                    self._size = content_length

                filename = self._url.split('/')[-1]
                with open(filename, 'wb') as file:
                    file.seek(self._downloaded)
                    while self._status == self.Status.DOWNLOADING:
                        chunk_size = self._size - self._downloaded
                        if chunk_size > self.MAX_CHUNK_SIZE:
                            chunk_size = self.MAX_CHUNK_SIZE

                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        file.write(chunk)

                        self._downloaded += chunk_size

            if self._status == self.Status.DOWNLOADING:
                self._status = self.Status.COMPLETE
        except:
            self._error()

    class Status(Enum):
        DOWNLOADING = "Downloading",
        PAUSED = "Paused",
        COMPLETE = "Complete",
        CANCELLED = "Cancelled",
        ERROR = "Error"


class DownloadManager(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master, padding=5)
        self._downloads = []
        self._selected_download = None
        # Flag for whether or not table selection is being cleared.
        self._clearing = False
        self._create_widgets()
        self.master.after(100, self._update_downloads)

    def _create_widgets(self):
        self.master.title("Download manager")
        self.master.geometry("640x400")
        self.master.config(menu=self._create_menu_bar())
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self._create_download_add_frame().grid(row=0, column=0)
        self._create_downloads_frame().grid(
            row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self._create_download_buttons_frame().grid(row=2, column=0)

    def _create_menu_bar(self):
        menubar = tk.Menu(self.master)
        filemenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", underline=0, menu=filemenu)
        filemenu.add_command(label="Exit", underline=1, command=self.quit)
        return menubar

    def _create_download_add_frame(self):
        download_add_frame = ttk.Frame(self)
        self._download_url_entry = ttk.Entry(download_add_frame, width=50)
        self._download_url_entry.grid(row=0, column=0, padx=5)
        download_add_button = ttk.Button(
            download_add_frame, text="Add download", command=self._add_download)
        download_add_button.grid(row=0, column=1)
        return download_add_frame

    def _create_downloads_frame(self):
        downloads_frame = ttk.LabelFrame(self, text="Downloads", padding=5)
        self._downloads_treeview = self._create_downloads_treeview(
            downloads_frame)
        self._downloads_treeview.grid(
            row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self._create_vertical_scrollbar(downloads_frame, self._downloads_treeview).grid(
            row=0, column=1, sticky=(tk.N, tk.S))
        downloads_frame.rowconfigure(0, weight=1)
        downloads_frame.columnconfigure(0, weight=1)
        return downloads_frame

    def _create_downloads_treeview(self, parent):
        downloads_treeview = ttk.Treeview(parent, selectmode="browse", show="headings", columns=(
            "URL", "Size", "Progress", "Status"))
        downloads_treeview.heading("URL", text="URL")
        downloads_treeview.heading("Size", text="Size")
        downloads_treeview.heading("Progress", text="Progress")
        downloads_treeview.heading("Status", text="Status")
        downloads_treeview.column("URL", stretch=True, width=10)
        downloads_treeview.column("Size", stretch=True, width=10)
        downloads_treeview.column("Progress", stretch=True, width=10)
        downloads_treeview.column("Status", stretch=True, width=10)
        downloads_treeview.bind("<<TreeviewSelect>>",
                                self._selected_download_changed)
        return downloads_treeview

    def _create_vertical_scrollbar(self, parent, scrollable_widget):
        scrollbar = ttk.Scrollbar(
            parent, orient=tk.VERTICAL, command=scrollable_widget.yview)
        scrollable_widget.configure(yscrollcommand=scrollbar.set)
        return scrollbar

    def _create_download_buttons_frame(self):
        download_buttons_frame = ttk.Frame(self, padding=(0, 5, 0, 0))
        self._pause_button = ttk.Button(
            download_buttons_frame, text="Pause", command=self._pause_download)
        self._pause_button.grid(row=0, column=0, padx=5)
        self._resume_button = ttk.Button(
            download_buttons_frame, text="Resume", command=self._resume_download)
        self._resume_button.grid(row=0, column=1, padx=0)
        self._cancel_button = ttk.Button(
            download_buttons_frame, text="Cancel", command=self._cancel_download)
        self._cancel_button.grid(row=0, column=2, padx=5)
        self._clear_button = ttk.Button(
            download_buttons_frame, text="Clear", command=self._clear_download)
        self._clear_button.grid(row=0, column=3, padx=0)
        self._update_download_buttons()
        return download_buttons_frame

    def _add_download(self):
        download = Download(self._download_url_entry.get())

        self._downloads.append(download)
        self._downloads_treeview.insert(parent="", index=tk.END, iid=id(download), values=(
            download.url, download.size, download.progress, download.status.value))

        self._download_url_entry.delete(0, tk.END)

    def _selected_download_changed(self, event):
        # If not in the middle of clearing a download, set the selected download.
        if not self._clearing and self._downloads_treeview.selection() is not None:
            selected_index = self._downloads_treeview.index(
                self._downloads_treeview.selection()[0])
            self._selected_download = self._downloads[selected_index]
            self._update_download_buttons()

    def _update_downloads(self):
        for download in self._downloads:
            self._downloads_treeview.item(id(download), values=(
                download.url, download.size, download.progress, download.status.value))

            if (download is self._selected_download):
                self._update_download_buttons()

        self.master.after(100, self._update_downloads)

    def _pause_download(self):
        self._selected_download.pause()
        self._update_download_buttons()

    def _resume_download(self):
        self._selected_download.resume()
        self._update_download_buttons()

    def _cancel_download(self):
        self._selected_download.cancel()
        self._update_download_buttons()

    def _clear_download(self):
        self._clearing = True

        selected_item = self._downloads_treeview.selection()[0]
        del self._downloads[self._downloads_treeview.index(selected_item)]
        self._downloads_treeview.delete(selected_item)

        self._clearing = False
        self._selected_download = None
        self._update_download_buttons()

    def _update_download_buttons(self):
        if self._selected_download is not None:
            if self._selected_download.status == Download.Status.DOWNLOADING:
                self._pause_button.state(["!disabled"])
                self._resume_button.state(["disabled"])
                self._cancel_button.state(["!disabled"])
                self._clear_button.state(["disabled"])
            elif self._selected_download.status == Download.Status.PAUSED:
                self._pause_button.state(["disabled"])
                self._resume_button.state(["!disabled"])
                self._cancel_button.state(["!disabled"])
                self._clear_button.state(["disabled"])
            elif self._selected_download.status == Download.Status.ERROR:
                self._pause_button.state(["disabled"])
                self._resume_button.state(["!disabled"])
                self._cancel_button.state(["disabled"])
                self._clear_button.state(["!disabled"])
            else:  # COMPLETE or CANCELLED
                self._pause_button.state(["disabled"])
                self._resume_button.state(["disabled"])
                self._cancel_button.state(["disabled"])
                self._clear_button.state(["!disabled"])
        else:
            self._pause_button.state(["disabled"])
            self._resume_button.state(["disabled"])
            self._cancel_button.state(["disabled"])
            self._clear_button.state(["disabled"])


if __name__ == "__main__":
    root = tk.Tk()
    app = DownloadManager(master=root)
    app.mainloop()
