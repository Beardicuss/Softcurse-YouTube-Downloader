"""
player.py - Softcurse // Mini Audio Player
Built-in player for MP3/FLAC/WAV files with:
  - Cyberpunk waveform visualizer (FFT bars)
  - Play/Pause/Stop/Prev/Next
  - Seek bar, volume, file browser
  - Playlist (auto-loads folder)
Requires: pygame (for audio) — gracefully disabled if missing.
"""
import tkinter as tk
from tkinter import filedialog
import threading
import os
import random
import math
import time

# ── Palette ───────────────────────────────────────────────────────────────────
BG          = "#020202"
CYAN        = "#00ffff"
CYAN_DIM    = "#007a7a"
CYAN_DARK   = "#003333"
DARK_PANEL  = "#050f0f"
MAGENTA     = "#ff00ff"
MAGENTA_DIM = "#660066"
WHITE       = "#e0f7f7"
TEXT_DIM    = "#407070"
SUCCESS     = "#00ff88"
ERROR       = "#ff3355"
BLUE        = "#0088ff"
ORANGE      = "#ff8800"
GRID_COLOR  = "#0a2a2a"
FONT_MONO   = "Courier New"

AUDIO_EXTS = (".mp3", ".flac", ".wav", ".ogg", ".opus", ".m4a", ".aac")


def check_pygame() -> bool:
    try:
        import pygame
        return True
    except ImportError:
        return False


def install_pygame(log_cb=None):
    import subprocess, sys
    def log(m):
        if log_cb: log_cb(m)
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pygame"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        log("✅ pygame installed! Restart to enable player.")
        return True
    except Exception as e:
        log(f"❌ pygame install failed: {e}")
        return False


class AudioPlayer:
    """Thin wrapper around pygame.mixer."""

    def __init__(self):
        self._loaded   = False
        self._duration = 0.0
        self._path     = ""
        self._paused   = False
        self._mixer    = None

    def _ensure_init(self):
        if self._mixer is None:
            import pygame
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            self._mixer = pygame.mixer

    def load(self, path: str) -> bool:
        try:
            self._ensure_init()
            self._mixer.music.load(path)
            self._path   = path
            self._loaded = True
            self._paused = False
            # Try mutagen for duration
            self._duration = self._get_duration(path)
            return True
        except Exception as e:
            print(f"[Player] Load failed: {e}")
            return False

    def play(self):
        if not self._loaded: return
        try:
            self._ensure_init()
            if self._paused:
                self._mixer.music.unpause()
                self._paused = False
            else:
                self._mixer.music.play()
        except Exception as e:
            print(f"[Player] Play failed: {e}")

    def pause(self):
        try:
            self._ensure_init()
            self._mixer.music.pause()
            self._paused = True
        except Exception:
            pass

    def stop(self):
        try:
            self._ensure_init()
            self._mixer.music.stop()
            self._paused = False
            self._loaded = False
        except Exception:
            pass

    def set_volume(self, vol: float):
        """vol: 0.0 – 1.0"""
        try:
            self._ensure_init()
            self._mixer.music.set_volume(max(0.0, min(1.0, vol)))
        except Exception:
            pass

    def seek(self, pos_secs: float):
        try:
            self._ensure_init()
            self._mixer.music.set_pos(pos_secs)
        except Exception:
            pass

    def get_pos(self) -> float:
        """Current playback position in seconds."""
        try:
            self._ensure_init()
            ms = self._mixer.music.get_pos()
            return ms / 1000.0 if ms >= 0 else 0.0
        except Exception:
            return 0.0

    def is_playing(self) -> bool:
        try:
            self._ensure_init()
            return self._mixer.music.get_busy() and not self._paused
        except Exception:
            return False

    def is_paused(self) -> bool:
        return self._paused

    @property
    def duration(self) -> float:
        return self._duration

    def _get_duration(self, path: str) -> float:
        try:
            from mutagen import File as MFile
            audio = MFile(path)
            if audio and audio.info:
                return float(audio.info.length)
        except Exception:
            pass
        return 0.0


class PlayerPanel(tk.Frame):
    """
    Self-contained player widget — embed it in any frame.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self._pygame_ok = check_pygame()
        self._player    = AudioPlayer() if self._pygame_ok else None
        self._playlist  = []   # list of file paths
        self._pl_index  = -1
        self._poll_id   = None
        self._vol       = 0.8
        self._waveform_anim = []  # current bar heights for animation
        self._waveform_target = []
        self._wave_id   = None
        self._playing_title = tk.StringVar(value="// NO TRACK LOADED //")
        self._pos_var   = tk.DoubleVar(value=0)
        self._vol_var   = tk.DoubleVar(value=80)
        self._seeking   = False

        self._build()
        if self._pygame_ok:
            self._start_poll()
        self._init_waveform()
        self._animate_wave()

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", pady=(0,6))
        tk.Label(hdr, text="▸ MINI PLAYER", fg=CYAN_DIM, bg=BG,
                 font=(FONT_MONO,8)).pack(side="left")
        if not self._pygame_ok:
            tk.Label(hdr, text="[ pygame not installed — see Settings ]",
                     fg=ERROR, bg=BG, font=(FONT_MONO,7)).pack(side="right")

        # Waveform canvas
        self.wave_canvas = tk.Canvas(self, height=80, bg=DARK_PANEL,
                                     highlightthickness=1,
                                     highlightbackground=CYAN_DARK)
        self.wave_canvas.pack(fill="x", pady=(0,6))

        # Now playing
        np_frame = tk.Frame(self, bg=DARK_PANEL, pady=4, padx=8)
        np_frame.pack(fill="x", pady=(0,4))
        self.np_label = tk.Label(np_frame, textvariable=self._playing_title,
                                 fg=CYAN, bg=DARK_PANEL,
                                 font=(FONT_MONO,9,"bold"),
                                 wraplength=560, anchor="w", justify="left")
        self.np_label.pack(fill="x")
        self.np_meta  = tk.Label(np_frame, text="",
                                 fg=TEXT_DIM, bg=DARK_PANEL,
                                 font=(FONT_MONO,7), anchor="w")
        self.np_meta.pack(fill="x")

        # Seek bar
        seek_row = tk.Frame(self, bg=BG)
        seek_row.pack(fill="x", pady=(0,4))
        self.time_cur = tk.Label(seek_row, text="0:00", fg=TEXT_DIM, bg=BG,
                                  font=(FONT_MONO,7), width=5)
        self.time_cur.pack(side="left")

        sty = self._make_scale_style("Seek.Horizontal.TScale", CYAN)
        self.seek_bar = ttk.Scale(seek_row, from_=0, to=100,
                                   orient="horizontal",
                                   variable=self._pos_var,
                                   style="Seek.Horizontal.TScale",
                                   command=self._on_seek_drag)
        self.seek_bar.pack(side="left", fill="x", expand=True, padx=6)
        self.seek_bar.bind("<ButtonPress-1>",   lambda e: setattr(self, "_seeking", True))
        self.seek_bar.bind("<ButtonRelease-1>", self._on_seek_release)

        self.time_tot = tk.Label(seek_row, text="0:00", fg=TEXT_DIM, bg=BG,
                                  font=(FONT_MONO,7), width=5)
        self.time_tot.pack(side="left")

        # Controls row
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(fill="x", pady=(0,4))

        btn_specs = [
            ("⏮",  self._prev,        CYAN),
            ("▶",   self._play_pause,  CYAN),
            ("⏹",  self._stop,        CYAN),
            ("⏭",  self._next,        CYAN),
            ("🔀",  self._shuffle,     MAGENTA_DIM),
        ]
        self._play_btn = None
        for sym, cmd, color in btn_specs:
            b = tk.Button(ctrl, text=sym, command=cmd,
                          fg=color, bg=DARK_PANEL,
                          activeforeground=BG, activebackground=color,
                          font=(FONT_MONO,12), relief="flat", bd=0,
                          width=3, cursor="hand2",
                          highlightthickness=1, highlightbackground=color)
            b.bind("<Enter>", lambda e,b=b,c=color: b.config(bg=c,fg=BG))
            b.bind("<Leave>", lambda e,b=b,c=color: b.config(bg=DARK_PANEL,fg=c))
            b.pack(side="left", padx=3)
            if sym == "▶":
                self._play_btn = b

        # Volume
        tk.Label(ctrl, text="  VOL:", fg=TEXT_DIM, bg=BG,
                 font=(FONT_MONO,7)).pack(side="left", padx=(12,0))
        sty2 = self._make_scale_style("Vol.Horizontal.TScale", ORANGE)
        vol_bar = ttk.Scale(ctrl, from_=0, to=100,
                             orient="horizontal",
                             variable=self._vol_var,
                             style="Vol.Horizontal.TScale",
                             command=self._on_vol_change)
        vol_bar.pack(side="left", fill="x", expand=True, padx=6)
        self._vol_var.set(80)
        self.vol_lbl = tk.Label(ctrl, text="80%", fg=ORANGE, bg=BG,
                                 font=(FONT_MONO,7), width=4)
        self.vol_lbl.pack(side="left")

        # Playlist
        pl_outer = tk.Frame(self, bg=CYAN_DIM, padx=1, pady=1)
        pl_outer.pack(fill="both", expand=True, pady=(4,0))
        pl_inner = tk.Frame(pl_outer, bg=DARK_PANEL)
        pl_inner.pack(fill="both", expand=True)

        pl_hdr = tk.Frame(pl_inner, bg=DARK_PANEL)
        pl_hdr.pack(fill="x", padx=6, pady=(4,2))
        tk.Label(pl_hdr, text="▸ PLAYLIST", fg=CYAN_DIM, bg=DARK_PANEL,
                 font=(FONT_MONO,8)).pack(side="left")

        for lbl, cmd, col in [
            ("[ + FOLDER ]", self._open_folder, CYAN),
            ("[ + FILES ]",  self._open_files,  CYAN),
            ("[ CLR ]",      self._clear_pl,    TEXT_DIM),
        ]:
            b = tk.Button(pl_hdr, text=lbl, command=cmd,
                          fg=col, bg=DARK_PANEL,
                          activeforeground=BG, activebackground=col,
                          font=(FONT_MONO,7,"bold"), relief="flat", bd=0,
                          cursor="hand2", highlightthickness=1,
                          highlightbackground=col)
            b.bind("<Enter>", lambda e,b=b,c=col: b.config(bg=c,fg=BG))
            b.bind("<Leave>", lambda e,b=b,c=col: b.config(bg=DARK_PANEL,fg=c))
            b.pack(side="right", padx=(4,0))

        pl_list_frame = tk.Frame(pl_inner, bg="#0a1a1a")
        pl_list_frame.pack(fill="both", expand=True, padx=6, pady=(0,6))
        self.pl_listbox = tk.Listbox(pl_list_frame,
            bg="#0a1a1a", fg=CYAN_DIM,
            selectbackground="#0a3333", selectforeground=CYAN,
            font=(FONT_MONO,8), relief="flat", bd=0,
            highlightthickness=0, activestyle="none",
            height=7)
        pl_sb = tk.Scrollbar(pl_list_frame, orient="vertical",
                              command=self.pl_listbox.yview)
        pl_sb.pack(side="right", fill="y")
        self.pl_listbox.config(yscrollcommand=pl_sb.set)
        self.pl_listbox.pack(fill="both", expand=True)
        self.pl_listbox.bind("<Double-Button-1>", self._on_pl_double_click)

    # ── Scale style helper ────────────────────────────────────────────────────
    def _make_scale_style(self, name: str, color: str):
        from tkinter import ttk
        sty = ttk.Style()
        sty.configure(name, background=BG, troughcolor=DARK_PANEL,
                      sliderthickness=12, sliderrelief="flat")
        return name

    # ── Waveform ──────────────────────────────────────────────────────────────
    def _init_waveform(self, n_bars=48):
        self._waveform_anim   = [0.05] * n_bars
        self._waveform_target = [0.05] * n_bars

    def _animate_wave(self):
        self.wave_canvas.delete("wave")
        w = self.wave_canvas.winfo_width() or 600
        h = 80
        n = len(self._waveform_anim)
        bar_w = max(2, (w - n) // n)
        gap   = 1

        playing = self._player and self._player.is_playing() if self._pygame_ok else False

        # Update targets
        for i in range(n):
            if playing:
                # Animate based on sine wave + randomness (fake spectrum)
                t     = time.time()
                phase = i / n * math.pi * 4
                base  = (math.sin(t * 3 + phase) + 1) / 2
                noise = random.gauss(0, 0.12)
                self._waveform_target[i] = max(0.05, min(1.0, base * 0.7 + noise))
            else:
                self._waveform_target[i] = 0.05

        # Smooth towards targets
        for i in range(n):
            diff = self._waveform_target[i] - self._waveform_anim[i]
            self._waveform_anim[i] += diff * 0.25

        # Draw bars
        for i, amp in enumerate(self._waveform_anim):
            x1 = i * (bar_w + gap) + 2
            x2 = x1 + bar_w
            bar_h = max(3, int(amp * (h - 8)))
            y1 = h - bar_h - 4
            y2 = h - 4

            # Color gradient: cyan at bottom, magenta at peak
            if amp > 0.7:
                color = MAGENTA
            elif amp > 0.4:
                color = CYAN
            else:
                color = CYAN_DIM

            self.wave_canvas.create_rectangle(
                x1, y1, x2, y2, fill=color, outline="", tags="wave")

        self._wave_id = self.after(50, self._animate_wave)

    # ── Playback controls ─────────────────────────────────────────────────────
    def _play_pause(self):
        if not self._pygame_ok:
            return
        if self._player.is_playing():
            self._player.pause()
            self._play_btn.config(text="▶")
        elif self._player.is_paused():
            self._player.play()
            self._play_btn.config(text="⏸")
        else:
            if self._pl_index < 0 and self._playlist:
                self._load_index(0)
            elif self._pl_index >= 0:
                self._player.play()
                self._play_btn.config(text="⏸")

    def _stop(self):
        if not self._pygame_ok: return
        self._player.stop()
        self._play_btn.config(text="▶")
        self._pos_var.set(0)
        self.time_cur.config(text="0:00")

    def _prev(self):
        if self._playlist and self._pl_index > 0:
            self._load_index(self._pl_index - 1)

    def _next(self):
        if self._playlist and self._pl_index < len(self._playlist) - 1:
            self._load_index(self._pl_index + 1)

    def _shuffle(self):
        if self._playlist:
            random.shuffle(self._playlist)
            self._refresh_listbox()
            self._load_index(0)

    def _load_index(self, idx: int):
        if not self._pygame_ok: return
        if idx < 0 or idx >= len(self._playlist): return
        self._pl_index = idx
        path = self._playlist[idx]
        if self._player.load(path):
            self._player.set_volume(self._vol)
            self._player.play()
            self._play_btn.config(text="⏸")
            name = os.path.splitext(os.path.basename(path))[0]
            self._playing_title.set(name)
            # Try metadata
            meta = self._read_meta(path)
            self.np_meta.config(text=meta)
            # Update total time
            dur = self._player.duration
            self.time_tot.config(text=self._fmt_time(dur))
            self.seek_bar.config(to=max(1, dur))
            # Highlight in listbox
            self.pl_listbox.selection_clear(0, "end")
            self.pl_listbox.selection_set(idx)
            self.pl_listbox.see(idx)

    def _read_meta(self, path: str) -> str:
        try:
            from mutagen import File as MFile
            audio = MFile(path, easy=True)
            if audio is None:
                return ""
            parts = []
            for key in ["artist","album","date"]:
                val = audio.get(key)
                if val:
                    parts.append(str(val[0]))
            return "  ·  ".join(parts)
        except Exception:
            return ""

    def _on_seek_drag(self, val):
        if self._seeking:
            secs = float(val)
            self.time_cur.config(text=self._fmt_time(secs))

    def _on_seek_release(self, event):
        self._seeking = False
        if self._pygame_ok and self._player._loaded:
            secs = self._pos_var.get()
            try:
                self._player.seek(secs)
            except Exception:
                pass

    def _on_vol_change(self, val):
        v = float(val) / 100.0
        self._vol = v
        self.vol_lbl.config(text=f"{int(float(val))}%")
        if self._pygame_ok:
            self._player.set_volume(v)

    # ── Playlist management ───────────────────────────────────────────────────
    def _open_folder(self):
        folder = filedialog.askdirectory(title="Open Audio Folder")
        if folder:
            files = sorted([
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith(AUDIO_EXTS)
            ])
            self._add_to_playlist(files)

    def _open_files(self):
        files = filedialog.askopenfilenames(
            title="Open Audio Files",
            filetypes=[("Audio Files",
                        "*.mp3 *.flac *.wav *.ogg *.opus *.m4a *.aac"),
                       ("All Files", "*.*")]
        )
        if files:
            self._add_to_playlist(list(files))

    def _add_to_playlist(self, paths: list):
        self._playlist.extend(paths)
        self._refresh_listbox()
        if self._pl_index < 0 and self._playlist:
            self._load_index(0)

    def load_file(self, path: str):
        """Load a single file from external code (e.g. after download)."""
        if os.path.exists(path):
            self._playlist.append(path)
            self._refresh_listbox()
            if self._pl_index < 0:
                self._load_index(len(self._playlist) - 1)

    def load_folder(self, folder: str):
        """Load all audio files from a folder (called after playlist download)."""
        if os.path.exists(folder):
            files = sorted([
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith(AUDIO_EXTS)
            ])
            self._add_to_playlist(files)

    def _clear_pl(self):
        self._player and self._player.stop()
        self._playlist  = []
        self._pl_index  = -1
        self.pl_listbox.delete(0, "end")
        self._playing_title.set("// NO TRACK LOADED //")
        self.np_meta.config(text="")
        self.time_cur.config(text="0:00")
        self.time_tot.config(text="0:00")
        self._pos_var.set(0)
        if self._play_btn:
            self._play_btn.config(text="▶")

    def _refresh_listbox(self):
        self.pl_listbox.delete(0, "end")
        for p in self._playlist:
            name = os.path.splitext(os.path.basename(p))[0]
            self.pl_listbox.insert("end", f"  {name}")

    def _on_pl_double_click(self, event):
        sel = self.pl_listbox.curselection()
        if sel:
            self._load_index(sel[0])

    # ── Poll (update seek bar while playing) ──────────────────────────────────
    def _start_poll(self):
        self._poll()

    def _poll(self):
        if self._pygame_ok and self._player:
            if self._player.is_playing() and not self._seeking:
                pos = self._player.get_pos()
                self._pos_var.set(pos)
                self.time_cur.config(text=self._fmt_time(pos))
                # Auto-advance
                dur = self._player.duration
                if dur > 0 and pos >= dur - 0.5:
                    self._next()
        self._poll_id = self.after(250, self._poll)

    @staticmethod
    def _fmt_time(secs: float) -> str:
        secs = max(0, int(secs))
        m, s = divmod(secs, 60)
        return f"{m}:{s:02d}"

    def destroy(self):
        if self._wave_id:
            self.after_cancel(self._wave_id)
        if self._poll_id:
            self.after_cancel(self._poll_id)
        if self._player:
            self._player.stop()
        super().destroy()


# Need to import ttk inside the file
from tkinter import ttk
