"""
metadata_editor.py - Softcurse // Metadata Editor
Pre-download metadata editor: set artist, album, genre, year, track, comment.
Uses mutagen to write ID3/FLAC/MP4 tags after download.
mutagen is optional — editor shows but tags silently skipped if missing.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Palette (matches main app) ─────────────────────────────────────────────────
BG          = "#020202"
CYAN        = "#00ffff"
CYAN_DIM    = "#007a7a"
DARK_PANEL  = "#050f0f"
MAGENTA     = "#ff00ff"
MAGENTA_DIM = "#660066"
WHITE       = "#e0f7f7"
TEXT_DIM    = "#407070"
SUCCESS     = "#00ff88"
ERROR       = "#ff3355"
BLUE        = "#0088ff"
ORANGE      = "#ff8800"
FONT_MONO   = "Courier New"

GENRE_LIST = [
    "", "Alternative", "Ambient", "Blues", "Classical", "Country",
    "Dance", "Electronic", "Folk", "Funk", "Gospel", "Hip-Hop",
    "House", "Indie", "Jazz", "Latin", "Metal", "New Age",
    "Opera", "Pop", "Punk", "R&B", "Rap", "Reggae", "Rock",
    "Soul", "Soundtrack", "Techno", "Trance", "World",
]


def check_mutagen() -> bool:
    try:
        import mutagen
        return True
    except ImportError:
        return False


def install_mutagen(log_cb=None):
    import subprocess, sys
    def log(m):
        if log_cb: log_cb(m)
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "mutagen"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        log("✅ mutagen installed!")
        return True
    except Exception as e:
        log(f"❌ mutagen install failed: {e}")
        return False


def write_tags(filepath: str, tags: dict) -> str:
    """
    Write metadata tags to an audio file.
    Supports MP3 (ID3), FLAC, MP4/M4A, OGG.
    Returns "" on success, error string on failure.
    """
    if not tags or not any(v for v in tags.values()):
        return ""  # Nothing to write
    try:
        import mutagen
        from mutagen import File as MutaFile
        from mutagen.id3 import (ID3NoHeaderError, ID3, TIT2, TPE1, TALB,
                                  TCON, TDRC, TRCK, COMM)
        from mutagen.flac import FLAC
        from mutagen.mp4 import MP4
        from mutagen.oggvorbis import OggVorbis

        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".mp3":
            try:
                audio = ID3(filepath)
            except ID3NoHeaderError:
                audio = ID3()
            if tags.get("title"):
                audio["TIT2"] = TIT2(encoding=3, text=tags["title"])
            if tags.get("artist"):
                audio["TPE1"] = TPE1(encoding=3, text=tags["artist"])
            if tags.get("album"):
                audio["TALB"] = TALB(encoding=3, text=tags["album"])
            if tags.get("genre"):
                audio["TCON"] = TCON(encoding=3, text=tags["genre"])
            if tags.get("year"):
                audio["TDRC"] = TDRC(encoding=3, text=tags["year"])
            if tags.get("track"):
                audio["TRCK"] = TRCK(encoding=3, text=tags["track"])
            if tags.get("comment"):
                audio["COMM"] = COMM(encoding=3, lang="eng",
                                     desc="", text=tags["comment"])
            audio.save(filepath)

        elif ext == ".flac":
            audio = FLAC(filepath)
            mapping = {
                "title": "title", "artist": "artist", "album": "album",
                "genre": "genre", "year": "date", "track": "tracknumber",
                "comment": "comment",
            }
            for key, tag in mapping.items():
                if tags.get(key):
                    audio[tag] = tags[key]
            audio.save()

        elif ext in (".mp4", ".m4a", ".m4v"):
            audio = MP4(filepath)
            mapping = {
                "title":   "\xa9nam",
                "artist":  "\xa9ART",
                "album":   "\xa9alb",
                "genre":   "\xa9gen",
                "year":    "\xa9day",
                "comment": "\xa9cmt",
            }
            for key, tag in mapping.items():
                if tags.get(key):
                    audio[tag] = [tags[key]]
            if tags.get("track"):
                try:
                    t = int(tags["track"])
                    audio["trkn"] = [(t, 0)]
                except Exception:
                    pass
            audio.save()

        elif ext in (".ogg", ".opus"):
            audio = OggVorbis(filepath)
            mapping = {
                "title": "title", "artist": "artist", "album": "album",
                "genre": "genre", "year": "date", "track": "tracknumber",
                "comment": "comment",
            }
            for key, tag in mapping.items():
                if tags.get(key):
                    audio[tag] = [tags[key]]
            audio.save()

        else:
            return f"Unsupported format for tag writing: {ext}"

        return ""

    except ImportError:
        return "mutagen not installed — tags skipped"
    except Exception as e:
        return str(e)


def write_tags_to_folder(folder: str, tags: dict, extensions=(".mp3",".flac",".m4a",".ogg",".opus")):
    """Write tags to all matching audio files in a folder."""
    errors = []
    count = 0
    try:
        for fname in os.listdir(folder):
            if any(fname.lower().endswith(ext) for ext in extensions):
                err = write_tags(os.path.join(folder, fname), tags)
                if err:
                    errors.append(f"{fname}: {err}")
                else:
                    count += 1
    except Exception as e:
        errors.append(str(e))
    return count, errors


class MetadataEditorDialog:
    """
    Modal popup for editing metadata tags before/after download.
    Call .show() and it returns the tags dict (or None if cancelled).
    """
    def __init__(self, parent, prefill: dict = None):
        self.parent  = parent
        self.prefill = prefill or {}
        self.result  = None
        self._vars   = {}

    def show(self) -> dict:
        self.win = tk.Toplevel(self.parent)
        self.win.title("Softcurse // Metadata Editor")
        self.win.geometry("520x540")
        self.win.configure(bg=BG)
        self.win.resizable(False, False)
        self.win.grab_set()
        self.win.focus_set()

        # Center relative to parent
        self.win.update_idletasks()
        px = self.parent.winfo_x() + (self.parent.winfo_width()  - 520) // 2
        py = self.parent.winfo_y() + (self.parent.winfo_height() - 540) // 2
        self.win.geometry(f"520x540+{px}+{py}")

        self._build(self.win)
        self.win.wait_window()
        return self.result

    def _build(self, win):
        # Header
        hdr = tk.Canvas(win, bg=BG, height=52, highlightthickness=0)
        hdr.pack(fill="x")
        hdr.create_text(260, 16, text="◈  S O F T C U R S E  ◈",
                        font=(FONT_MONO,8,"bold"), fill=MAGENTA, anchor="center")
        hdr.create_text(260, 36, text="[ METADATA EDITOR ]",
                        font=(FONT_MONO,16,"bold"), fill=CYAN, anchor="center")

        # Outer neon border
        outer = tk.Frame(win, bg=CYAN, padx=1, pady=1)
        outer.pack(fill="both", expand=True, padx=12, pady=(0,12))
        inner = tk.Frame(outer, bg=DARK_PANEL, padx=14, pady=12)
        inner.pack(fill="both", expand=True)

        if not check_mutagen():
            tk.Label(inner,
                text="⚠️  mutagen not installed\nTags will be skipped.\nInstall via: pip install mutagen",
                fg=ORANGE, bg=DARK_PANEL, font=(FONT_MONO,9),
                justify="center").pack(pady=(0,8))

        # Style combobox
        sty = ttk.Style()
        sty.configure("Meta.TCombobox",
            fieldbackground="#0a1a1a", background=DARK_PANEL,
            foreground=CYAN, bordercolor=CYAN_DIM, arrowcolor=CYAN,
            selectbackground="#0a3333", selectforeground=CYAN)

        # Fields
        fields = [
            ("Title",   "title",   False),
            ("Artist",  "artist",  False),
            ("Album",   "album",   False),
            ("Genre",   "genre",   True),   # True = combobox
            ("Year",    "year",    False),
            ("Track #", "track",   False),
            ("Comment", "comment", False),
        ]

        entry_kw = dict(
            font=(FONT_MONO, 9), fg=WHITE, bg="#0a1a1a",
            insertbackground=CYAN, relief="flat", bd=4,
            highlightthickness=1, highlightbackground=CYAN_DIM,
            highlightcolor=CYAN,
        )

        for label, key, is_combo in fields:
            row = tk.Frame(inner, bg=DARK_PANEL)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{label}:", width=10, anchor="e",
                     fg=CYAN_DIM, bg=DARK_PANEL,
                     font=(FONT_MONO, 8)).pack(side="left")

            var = tk.StringVar(value=self.prefill.get(key, ""))
            self._vars[key] = var

            if is_combo:
                cb = ttk.Combobox(row, textvariable=var, values=GENRE_LIST,
                                  style="Meta.TCombobox", font=(FONT_MONO,9))
                cb.pack(side="left", fill="x", expand=True, padx=(6,0))
            else:
                e = tk.Entry(row, textvariable=var, **entry_kw)
                e.pack(side="left", fill="x", expand=True, padx=(6,0))
                e.bind("<FocusIn>",  lambda ev,w=e: w.config(highlightbackground=CYAN))
                e.bind("<FocusOut>", lambda ev,w=e: w.config(highlightbackground=CYAN_DIM))

        # Separator
        tk.Frame(inner, bg=CYAN_DIM, height=1).pack(fill="x", pady=(12,8))

        # Buttons
        btn_row = tk.Frame(inner, bg=DARK_PANEL)
        btn_row.pack(fill="x")

        def save():
            self.result = {k: v.get().strip() for k, v in self._vars.items()}
            self.win.destroy()

        def clear():
            for v in self._vars.values():
                v.set("")

        def cancel():
            self.result = None
            self.win.destroy()

        for text, cmd, color in [
            ("[ ✔ APPLY TAGS ]", save,   CYAN),
            ("[ CLR ]",          clear,  TEXT_DIM),
            ("[ CANCEL ]",       cancel, ERROR),
        ]:
            b = tk.Button(btn_row, text=text, command=cmd,
                          fg=color, bg=DARK_PANEL,
                          activeforeground=BG, activebackground=color,
                          font=(FONT_MONO, 9, "bold"),
                          relief="flat", bd=0, cursor="hand2",
                          highlightthickness=1, highlightbackground=color)
            b.bind("<Enter>", lambda e,b=b,c=color: b.config(bg=c, fg=BG))
            b.bind("<Leave>", lambda e,b=b,c=color,bg=DARK_PANEL: b.config(bg=bg, fg=c))
            b.pack(side="left", padx=(0,8), ipady=4, ipadx=6)

        tk.Label(inner,
            text="Tags are embedded into downloaded files after conversion.",
            fg=TEXT_DIM, bg=DARK_PANEL, font=(FONT_MONO,7)
        ).pack(anchor="w", pady=(8,0))
