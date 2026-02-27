"""
gui.py - Softcurse // YouTube Downloader v4
New: MP3 Mini Player tab, Metadata Editor, FLAC/WAV formats, SponsorBlock
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, time, random, os, math

from config import load_config, save_config
from downloader import Downloader, check_ytdlp, install_ytdlp, get_ffmpeg_path
import history as hist
from tray import TrayManager, send_notification, check_tray_deps, install_tray_deps
from thumbnail import fetch_info_and_thumb, check_pil, install_pil
from metadata_editor import MetadataEditorDialog, check_mutagen, install_mutagen
from player import PlayerPanel, check_pygame, install_pygame
from sponsorblock import CATEGORY_LABELS, DEFAULT_CATEGORIES

# ── Palette ───────────────────────────────────────────────────────────────────
BG          = "#020202"
CYAN        = "#00ffff"
CYAN_DIM    = "#007a7a"
CYAN_DARK   = "#003333"
BLUE        = "#0088ff"
MAGENTA     = "#ff00ff"
MAGENTA_DIM = "#660066"
WHITE       = "#e0f7f7"
DARK_PANEL  = "#050f0f"
GRID_COLOR  = "#0a2a2a"
SUCCESS     = "#00ff88"
WARNING     = "#ffaa00"
ERROR       = "#ff3355"
TEXT_DIM    = "#407070"
ORANGE      = "#ff8800"
ORANGE_DIM  = "#7a3a00"
FONT_MONO   = "Courier New"

TAB_DL=0; TAB_PLAYER=1; TAB_HISTORY=2; TAB_SETTINGS=3


class SoftcurseApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.cfg  = load_config()
        self.dl   = Downloader()
        self._downloading   = False
        self._mode          = tk.StringVar(value="mp3")   # mp3/flac/wav/mp4
        self._active_tab    = TAB_DL
        self._thumb_photo   = None
        self._pending_info  = None
        self._info_fetch_url= ""
        self._crt_after     = None
        self._glitch_after  = None
        self._pulse_after   = None
        self._tray          = None
        self._dl_metadata   = {}      # metadata set in editor
        self._dl_url = self._dl_mode = self._dl_folder = ""

        self._setup_window()
        self._build_ui()
        self._start_effects()
        self._check_deps_async()
        self._maybe_start_tray()

    def _setup_window(self):
        self.root.title("Softcurse // YouTube Downloader v4")
        self.root.geometry("840x820")
        self.root.minsize(760, 700)
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        
        # Strip the maximize button using ctypes while keeping WS_THICKFRAME so
        # the user can still manually resize by dragging edges.
        def disable_maximize():
            try:
                import ctypes
                GWL_STYLE = -16
                WS_MAXIMIZEBOX = 0x00010000
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style & ~WS_MAXIMIZEBOX)
            except Exception:
                pass
        self.root.after(10, disable_maximize)
        try: self.root.iconbitmap("assets/yt.ico")
        except: pass
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - 840) // 2
        y = (self.root.winfo_screenheight() - 820) // 2
        self.root.geometry(f"840x820+{x}+{y}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.bg_canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._draw_grid()

        # CRT scanline overlay reuses bg_canvas to avoid the need for a
        # transparent canvas (bg="" is invalid on Windows / some Tcl/Tk builds).
        self.crt_canvas = self.bg_canvas

        self.main_frame = tk.Frame(self.root, bg=BG)
        self.main_frame.place(x=16, y=16, relwidth=1, relheight=1, width=-32, height=-32)

        self._build_header()
        self._build_nav_tabs()
        self._build_tab_download()
        self._build_tab_player()
        self._build_tab_history()
        self._build_tab_settings()
        self._build_status_bar()
        self._show_tab(TAB_DL)

    def _draw_grid(self):
        self.bg_canvas.delete("grid")
        w = self.root.winfo_width()  or 840
        h = self.root.winfo_height() or 820
        for x in range(0,w,40):
            self.bg_canvas.create_line(x,0,x,h, fill=GRID_COLOR, width=1, tags="grid")
        for y in range(0,h,40):
            self.bg_canvas.create_line(0,y,w,y, fill=GRID_COLOR, width=1, tags="grid")
        for i,c in enumerate([CYAN_DARK,"#0a3333","#083030","#062828","#041e1e"]):
            self.bg_canvas.create_line(0,h//2+i*3,w,h//2+i*3, fill=c, tags="grid")
        self.root.bind("<Configure>", lambda e: self._draw_grid())

    # ── Widget helpers ────────────────────────────────────────────────────────
    def _nf(self, parent, color=CYAN, pad=8):
        o = tk.Frame(parent, bg=color, padx=1, pady=1)
        i = tk.Frame(o, bg=DARK_PANEL, padx=pad, pady=pad)
        i.pack(fill="both", expand=True)
        return o, i

    def _lbl(self, p, text, size=8, color=CYAN, bold=False, bg=DARK_PANEL):
        return tk.Label(p, text=text, fg=color, bg=bg,
                        font=(FONT_MONO, size, "bold" if bold else "normal"))

    def _btn(self, p, text, cmd, color=CYAN, w=16, h=1, bg=DARK_PANEL, size=9):
        b = tk.Button(p, text=text, command=cmd, fg=color, bg=bg,
                      activeforeground=BG, activebackground=color,
                      font=(FONT_MONO,size,"bold"), relief="flat", bd=0,
                      width=w, height=h, cursor="hand2",
                      highlightthickness=1, highlightbackground=color)
        b.bind("<Enter>", lambda e: b.config(bg=color, fg=BG))
        b.bind("<Leave>", lambda e: b.config(bg=bg, fg=color))
        return b

    def _entry(self, p, var, width=None):
        kw = dict(font=(FONT_MONO,9), fg=WHITE, bg="#0a1a1a",
                  insertbackground=CYAN, relief="flat", bd=4,
                  highlightthickness=1, highlightbackground=CYAN_DIM,
                  highlightcolor=CYAN)
        if width: kw["width"] = width
        e = tk.Entry(p, textvariable=var, **kw)
        e.bind("<FocusIn>",  lambda ev: e.config(highlightbackground=CYAN))
        e.bind("<FocusOut>", lambda ev: e.config(highlightbackground=CYAN_DIM))
        return e

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        f = tk.Frame(self.main_frame, bg=BG)
        f.pack(fill="x", pady=(0,6))
        self.title_canvas = tk.Canvas(f, bg=BG, height=68, highlightthickness=0)
        self.title_canvas.pack(fill="x")
        self.t1 = self.title_canvas.create_text(420,11,
            text="◈  S O F T C U R S E  ◈",
            font=(FONT_MONO,8,"bold"), fill=MAGENTA, anchor="center")
        self.title_shadow = self.title_canvas.create_text(422,38,
            text="[ YT DOWNLOADER // SOFTCURSE ]",
            font=(FONT_MONO,20,"bold"), fill=MAGENTA_DIM, anchor="center")
        self.title_id = self.title_canvas.create_text(420,36,
            text="[ YT DOWNLOADER // SOFTCURSE ]",
            font=(FONT_MONO,20,"bold"), fill=CYAN, anchor="center")
        self.t4 = self.title_canvas.create_text(420,58,
            text="▸ MP3 · FLAC · WAV · MP4  ·  PLAYER  ·  SPONSORBLOCK  ·  METADATA ◂",
            font=(FONT_MONO,7), fill=BLUE, anchor="center")
        self.title_canvas.bind("<Configure>", lambda e: self._center_header(e.width))

    def _center_header(self, w):
        cx = w // 2
        self.title_canvas.coords(self.t1, cx, 11)
        self.title_canvas.coords(self.title_shadow, cx + 2, 38)
        self.title_canvas.coords(self.title_id, cx, 36)
        self.title_canvas.coords(self.t4, cx, 58)

    # ── Nav tabs ──────────────────────────────────────────────────────────────
    def _build_nav_tabs(self):
        f = tk.Frame(self.main_frame, bg=BG)
        f.pack(fill="x", pady=(0,6))
        row = tk.Frame(f, bg=BG)
        row.pack(anchor="center")
        self._tab_btns = {}
        for label, idx, color in [
            ("⬇  DOWNLOAD", TAB_DL,       CYAN),
            ("♪  PLAYER",   TAB_PLAYER,    MAGENTA),
            ("📋  HISTORY",  TAB_HISTORY,   BLUE),
            ("⚙  SETTINGS", TAB_SETTINGS,  ORANGE),
        ]:
            b = tk.Button(row, text=label,
                          command=lambda i=idx: self._show_tab(i),
                          font=(FONT_MONO,9,"bold"), relief="flat", bd=0,
                          padx=12, pady=5, cursor="hand2")
            b.pack(side="left", padx=2)
            self._tab_btns[idx] = (b, color)
        self._tab_ind = tk.Label(f, text="", fg=TEXT_DIM, bg=BG, font=(FONT_MONO,7))
        self._tab_ind.pack(pady=(3,0))

    def _show_tab(self, idx):
        self._active_tab = idx
        for i,(b,color) in self._tab_btns.items():
            if i == idx: b.config(fg=BG, bg=color, highlightthickness=1, highlightbackground=color)
            else:        b.config(fg=color, bg=DARK_PANEL, highlightthickness=1, highlightbackground=TEXT_DIM)
        frames = {TAB_DL:self.tab_dl, TAB_PLAYER:self.tab_player,
                  TAB_HISTORY:self.tab_hist, TAB_SETTINGS:self.tab_settings}
        labels = {TAB_DL:"// DOWNLOAD //", TAB_PLAYER:"// MINI PLAYER //",
                  TAB_HISTORY:"// HISTORY //", TAB_SETTINGS:"// SETTINGS //"}
        for i,fr in frames.items():
            (fr.pack if i==idx else fr.pack_forget)(fill="both", expand=True) if i==idx else fr.pack_forget()
        self._tab_ind.config(text=labels.get(idx,""))
        if idx == TAB_HISTORY: self._refresh_history()

    # ════════════════════════════════════════════════════════════════════════════
    # DOWNLOAD TAB
    # ════════════════════════════════════════════════════════════════════════════
    def _build_tab_download(self):
        self.tab_dl = tk.Frame(self.main_frame, bg=BG)
        self._build_format_tabs(self.tab_dl)
        self._build_url_section(self.tab_dl)
        self._build_thumb_section(self.tab_dl)
        self._build_options_section(self.tab_dl)
        self._build_sb_section(self.tab_dl)
        self._build_clip_section(self.tab_dl)
        self._build_progress_section(self.tab_dl)
        self._build_log_section(self.tab_dl)

    # ── Format tabs ───────────────────────────────────────────────────────────
    def _build_format_tabs(self, parent):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=(0,5))
        row = tk.Frame(f, bg=BG)
        row.pack(anchor="center")
        self._fmt_btns = {}
        formats = [
            ("♪ MP3",  "mp3",  CYAN),
            ("◆ FLAC", "flac", SUCCESS),
            ("◇ WAV",  "wav",  BLUE),
            ("▶ MP4",  "mp4",  ORANGE),
        ]
        for label, mode, color in formats:
            b = tk.Button(row, text=f"  {label}  ",
                          command=lambda m=mode: self._set_mode(m),
                          font=(FONT_MONO,9,"bold"), relief="flat", bd=0,
                          cursor="hand2", padx=8, pady=5,
                          highlightthickness=1)
            b.pack(side="left", padx=2)
            self._fmt_btns[mode] = (b, color)
        self.mode_lbl = tk.Label(f, text="", fg=CYAN_DIM, bg=BG, font=(FONT_MONO,7))
        self.mode_lbl.pack(pady=(3,0))
        self._set_mode("mp3")

    def _set_mode(self, mode: str):
        self._mode.set(mode)
        colors = {"mp3":CYAN, "flac":SUCCESS, "wav":BLUE, "mp4":ORANGE}
        labels = {
            "mp3":  "// MODE: MP3 — AUDIO (lossy, universal) //",
            "flac": "// MODE: FLAC — LOSSLESS AUDIO (audiophile quality) //",
            "wav":  "// MODE: WAV — UNCOMPRESSED AUDIO (studio/DAW) //",
            "mp4":  "// MODE: MP4 — VIDEO WITH AUDIO //",
        }
        for m,(b,c) in self._fmt_btns.items():
            if m == mode: b.config(fg=BG, bg=c, highlightbackground=c)
            else:         b.config(fg=c, bg=DARK_PANEL, highlightbackground=TEXT_DIM)
        self.mode_lbl.config(text=labels.get(mode,""), fg=colors.get(mode,CYAN_DIM))

        # Show/hide quality panels if they exist
        try:
            is_audio = mode in ("mp3","flac","wav")
            is_mp3   = mode == "mp3"
            if is_audio:
                self.mp4_q_frame.pack_forget()
                self.audio_q_frame.pack(side="left")
                # Show kbps only for MP3
                self.kbps_lbl.config(text=" kbps" if is_mp3 else " (lossless)")
            else:
                self.audio_q_frame.pack_forget()
                self.mp4_q_frame.pack(side="left")
            # Show/hide SB (audio only)
            if hasattr(self, "sb_outer"):
                if is_audio: self.sb_outer.pack(fill="x", pady=(0,5), before=self.clip_outer)
                else:        self.sb_outer.pack_forget()
            # Update folder default
            if mode == "mp4":
                self.folder_var.set(self.cfg.get("mp4_output_folder",""))
            else:
                self.folder_var.set(self.cfg.get("output_folder",""))
            # Update download button
            icon = {"mp3":"♪","flac":"◆","wav":"◇","mp4":"▶"}.get(mode,"⬇")
            c = colors.get(mode, CYAN)
            self.dl_btn.config(text=f"[ {icon} DOWNLOAD {mode.upper()} ]",
                               fg=c, highlightbackground=c)
            self.dl_btn.bind("<Enter>", lambda e,c=c: self.dl_btn.config(bg=c,fg=BG))
            self.dl_btn.bind("<Leave>", lambda e,c=c: self.dl_btn.config(bg="#0a1a1a",fg=c))
        except AttributeError:
            pass  # panels not built yet

    # ── URL ───────────────────────────────────────────────────────────────────
    def _build_url_section(self, parent):
        o,i = self._nf(parent, CYAN)
        o.pack(fill="x", pady=(0,5))
        self._lbl(i, "▸ TARGET URL", color=CYAN_DIM).pack(anchor="w")
        row = tk.Frame(i, bg=DARK_PANEL); row.pack(fill="x", pady=(4,0))
        self.url_var = tk.StringVar(value=self.cfg.get("last_url",""))
        self.url_entry = self._entry(row, self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>",   lambda e: self._trigger_fetch())
        self.url_entry.bind("<FocusOut>", lambda e: self._trigger_fetch())
        self._btn(row,"[ PASTE ]",  self._paste_url,     CYAN,    10).pack(side="left",padx=(6,0))
        self._btn(row,"[ CLR ]",    lambda:(self.url_var.set(""),self._clear_preview()), MAGENTA_DIM,6).pack(side="left",padx=(4,0))
        self._btn(row,"[ ↺ FETCH ]",self._trigger_fetch, BLUE,     9).pack(side="left",padx=(4,0))

    # ── Thumbnail ─────────────────────────────────────────────────────────────
    def _build_thumb_section(self, parent):
        o,i = self._nf(parent, CYAN_DIM, pad=6)
        o.pack(fill="x", pady=(0,5))
        row = tk.Frame(i, bg=DARK_PANEL); row.pack(fill="x")
        self.thumb_canvas = tk.Canvas(row, width=164, height=94, bg="#0a1a1a",
            highlightthickness=1, highlightbackground=CYAN_DARK)
        self.thumb_canvas.pack(side="left", padx=(0,10))
        self.thumb_canvas.create_text(82,47, text="NO PREVIEW", fill=TEXT_DIM,
                                      font=(FONT_MONO,8))
        col = tk.Frame(row, bg=DARK_PANEL); col.pack(side="left", fill="both", expand=True)
        self.info_title = tk.Label(col, text="// PASTE A URL TO PREVIEW //",
            fg=TEXT_DIM, bg=DARK_PANEL, font=(FONT_MONO,9,"bold"),
            wraplength=400, justify="left", anchor="w")
        self.info_title.pack(anchor="w")
        self.info_meta = tk.Label(col, text="", fg=BLUE, bg=DARK_PANEL,
            font=(FONT_MONO,8), justify="left", anchor="w")
        self.info_meta.pack(anchor="w", pady=(4,0))
        self.info_status = tk.Label(col, text="", fg=CYAN_DIM, bg=DARK_PANEL,
            font=(FONT_MONO,7), justify="left", anchor="w")
        self.info_status.pack(anchor="w", pady=(2,0))
        # Metadata editor button (appears after fetch)
        self.meta_btn = self._btn(col, "[ ✎ EDIT METADATA ]", self._open_metadata_editor,
                                  MAGENTA_DIM, 20, 1, DARK_PANEL, 8)
        self.meta_btn.pack(anchor="w", pady=(6,0))
        self.meta_btn.pack_forget()

    def _trigger_fetch(self):
        url = self.url_var.get().strip()
        if not url or not url.startswith("http"): return
        if url == self._info_fetch_url: return
        self._info_fetch_url = url
        self._clear_preview(keep_url=True)
        self.info_status.config(text="⟳ Fetching...", fg=WARNING)
        fetch_info_and_thumb(url,
            on_info=lambda d: self.root.after(0, lambda: self._on_info(d)),
            on_thumb=lambda p: self.root.after(0, lambda: self._on_thumb(p)),
            on_error=lambda e: self.root.after(0, lambda: self.info_status.config(
                text=f"⚠ {e[:60]}", fg=WARNING)),
            thumb_size=(160,90))

    def _on_info(self, d):
        self._pending_info = d
        title = d.get("title","")
        if d.get("type") == "playlist":
            count = d.get("count",0)
            meta  = f"📂 Playlist · {count} items"
            ch    = d.get("channel","")
            if ch: meta += f" · {ch}"
            self.info_status.config(text="✅ Playlist — enable PLAYLIST MODE below", fg=SUCCESS)
        else:
            parts = []
            if d.get("duration"): parts.append(f"⏱ {d['duration']}")
            if d.get("channel"):  parts.append(f"👤 {d['channel']}")
            if d.get("view_count"): parts.append(f"👁 {d['view_count']:,}")
            meta = "  ·  ".join(parts)
            self.info_status.config(text="✅ Ready to download", fg=SUCCESS)
        self.info_title.config(text=title[:70]+("..." if len(title)>70 else ""), fg=WHITE)
        self.info_meta.config(text=meta)
        # Prefill metadata editor with fetched info
        self._dl_metadata = {"title": title, "artist": d.get("channel",""),
                              "album": "", "genre": "", "year": "", "track": "", "comment": ""}
        self.meta_btn.pack(anchor="w", pady=(6,0))

    def _on_thumb(self, photo):
        self._thumb_photo = photo
        self.thumb_canvas.delete("all")
        if photo:
            self.thumb_canvas.create_image(82,47, image=photo, anchor="center")
        else:
            self.thumb_canvas.create_text(82,47, text="NO THUMB", fill=TEXT_DIM, font=(FONT_MONO,8))

    def _clear_preview(self, keep_url=False):
        if not keep_url: self._info_fetch_url = ""
        self._pending_info = None
        self._thumb_photo  = None
        self.thumb_canvas.delete("all")
        self.thumb_canvas.create_text(82,47, text="NO PREVIEW", fill=TEXT_DIM, font=(FONT_MONO,8))
        self.info_title.config(text="// PASTE A URL TO PREVIEW //", fg=TEXT_DIM)
        self.info_meta.config(text="")
        self.info_status.config(text="", fg=CYAN_DIM)
        self.meta_btn.pack_forget()

    def _open_metadata_editor(self):
        dialog = MetadataEditorDialog(self.root, prefill=self._dl_metadata)
        result = dialog.show()
        if result is not None:
            self._dl_metadata = result
            filled = [f"{k}: {v}" for k,v in result.items() if v]
            if filled:
                self._log(f"🏷️  Metadata staged: {', '.join(filled[:3])}"
                          + ("..." if len(filled)>3 else ""), "magenta")
            self.meta_btn.config(text="[ ✎ METADATA SET ✔ ]",
                                 fg=SUCCESS, highlightbackground=SUCCESS)

    # ── Options ───────────────────────────────────────────────────────────────
    def _build_options_section(self, parent):
        o,i = self._nf(parent, BLUE)
        o.pack(fill="x", pady=(0,5))
        cols = tk.Frame(i, bg=DARK_PANEL); cols.pack(fill="x")

        # Folder
        left = tk.Frame(cols, bg=DARK_PANEL); left.pack(side="left", fill="x", expand=True)
        self._lbl(left,"▸ OUTPUT FOLDER", color=CYAN_DIM).pack(anchor="w")
        fr = tk.Frame(left, bg=DARK_PANEL); fr.pack(fill="x", pady=(4,0))
        self.folder_var = tk.StringVar(value=self.cfg.get("output_folder",""))
        self._entry(fr, self.folder_var).pack(side="left", fill="x", expand=True)
        self._btn(fr,"[ BROWSE ]", self._browse_folder, BLUE, 10).pack(side="left",padx=(6,0))

        tk.Frame(cols, bg=DARK_PANEL, width=16).pack(side="left")

        # Quality + playlist
        right = tk.Frame(cols, bg=DARK_PANEL); right.pack(side="left")
        self._lbl(right,"▸ QUALITY", color=CYAN_DIM).pack(anchor="w")
        q_row = tk.Frame(right, bg=DARK_PANEL); q_row.pack(fill="x", pady=(4,0))

        sty = ttk.Style(); sty.theme_use("clam")
        for name, fg, bg_c in [
            ("C.TCombobox", CYAN, "#0a3333"),
            ("O.TCombobox", ORANGE, "#1a0900"),
            ("G.TCombobox", SUCCESS, "#001a09"),
        ]:
            sty.configure(name, fieldbackground="#0a1a1a", background=DARK_PANEL,
                foreground=fg, bordercolor=CYAN_DIM, arrowcolor=fg,
                selectbackground=bg_c, selectforeground=fg)

        self.quality_var = tk.StringVar(value=self.cfg.get("quality","320"))
        self.audio_q_frame = tk.Frame(q_row, bg=DARK_PANEL)
        ttk.Combobox(self.audio_q_frame, textvariable=self.quality_var,
            values=["128","192","256","320"], state="readonly",
            width=7, style="C.TCombobox").pack(side="left")
        self.kbps_lbl = tk.Label(self.audio_q_frame, text=" kbps",
            fg=TEXT_DIM, bg=DARK_PANEL, font=(FONT_MONO,8))
        self.kbps_lbl.pack(side="left")
        self.audio_q_frame.pack(side="left")

        self.video_quality_var = tk.StringVar(value=self.cfg.get("video_quality","best"))
        self.mp4_q_frame = tk.Frame(q_row, bg=DARK_PANEL)
        ttk.Combobox(self.mp4_q_frame, textvariable=self.video_quality_var,
            values=["best","1080","720","480","360"], state="readonly",
            width=7, style="O.TCombobox").pack(side="left")
        tk.Label(self.mp4_q_frame, text=" res", fg=TEXT_DIM, bg=DARK_PANEL,
                 font=(FONT_MONO,8)).pack(side="left")

        self.playlist_var = tk.BooleanVar(value=False)
        pr = tk.Frame(right, bg=DARK_PANEL); pr.pack(fill="x", pady=(8,0))
        tk.Checkbutton(pr, text=" PLAYLIST MODE",
            variable=self.playlist_var, fg=CYAN, bg=DARK_PANEL,
            activeforeground=MAGENTA, activebackground=DARK_PANEL,
            selectcolor="#0a1a1a", font=(FONT_MONO,8,"bold"), cursor="hand2"
        ).pack(side="left")

    # ── SponsorBlock ──────────────────────────────────────────────────────────
    def _build_sb_section(self, parent):
        o,i = self._nf(parent, SUCCESS, pad=7)
        self.sb_outer = o
        o.pack(fill="x", pady=(0,5))

        hdr = tk.Frame(i, bg=DARK_PANEL); hdr.pack(fill="x")
        self.sb_var = tk.BooleanVar(value=self.cfg.get("sponsorblock",False))
        tk.Checkbutton(hdr, text=" SPONSORBLOCK — Skip sponsors & unwanted segments",
            variable=self.sb_var, onvalue=True, offvalue=False,
            fg=SUCCESS, bg=DARK_PANEL,
            activeforeground=WHITE, activebackground=DARK_PANEL,
            selectcolor="#0a1a1a", font=(FONT_MONO,9,"bold"), cursor="hand2",
            command=self._toggle_sb_cats
        ).pack(side="left")

        self.sb_cats_frame = tk.Frame(i, bg=DARK_PANEL)
        self.sb_cats_frame.pack(fill="x", pady=(6,0))
        self.sb_cat_vars = {}
        saved_cats = set(self.cfg.get("sb_categories", DEFAULT_CATEGORIES))
        cats_display = [
            ("sponsor","💰 Sponsor"),("intro","🎬 Intro"),("outro","🔚 Outro"),
            ("selfpromo","📣 Self-Promo"),("interaction","👍 Interaction"),
            ("music_offtopic","🎵 Non-Music"),("filler","💬 Filler"),
        ]
        for idx,(key, label) in enumerate(cats_display):
            var = tk.BooleanVar(value=(key in saved_cats))
            self.sb_cat_vars[key] = var
            if idx == 0:
                row1 = tk.Frame(self.sb_cats_frame, bg=DARK_PANEL)
                row1.pack(fill="x")
            
            if idx == 4:
                row2 = tk.Frame(self.sb_cats_frame, bg=DARK_PANEL)
                row2.pack(fill="x", pady=(2,0))

            target_row = row1 if idx < 4 else row2

            tk.Checkbutton(target_row, text=f" {label}",
                variable=var, fg=SUCCESS, bg=DARK_PANEL,
                activeforeground=WHITE, activebackground=DARK_PANEL,
                selectcolor="#0a1a1a", font=(FONT_MONO,7), cursor="hand2"
            ).pack(side="left", padx=(0,12))

        self._toggle_sb_cats()

    def _toggle_sb_cats(self):
        state = "normal" if self.sb_var.get() else "disabled"
        for w in self.sb_cats_frame.winfo_children():
            for ww in w.winfo_children():
                try: ww.config(state=state)
                except: pass

    # ── Clip ──────────────────────────────────────────────────────────────────
    def _build_clip_section(self, parent):
        o,i = self._nf(parent, MAGENTA_DIM, pad=6)
        self.clip_outer = o
        o.pack(fill="x", pady=(0,5))
        hdr = tk.Frame(i, bg=DARK_PANEL); hdr.pack(fill="x")
        self._lbl(hdr,"▸ CLIP / TRIM  (optional)", color=MAGENTA_DIM).pack(side="left")
        self._lbl(hdr,"MM:SS or HH:MM:SS", size=7, color=TEXT_DIM).pack(side="right")
        row = tk.Frame(i, bg=DARK_PANEL); row.pack(fill="x", pady=(5,0))
        self._lbl(row,"START:", size=8, color=TEXT_DIM).pack(side="left")
        self.clip_start_var = tk.StringVar()
        self._entry(row, self.clip_start_var, 10).pack(side="left", padx=(4,12))
        self._lbl(row,"END:", size=8, color=TEXT_DIM).pack(side="left")
        self.clip_end_var = tk.StringVar()
        self._entry(row, self.clip_end_var, 10).pack(side="left", padx=(4,12))
        self._btn(row,"[ CLR ]",
            lambda:(self.clip_start_var.set(""),self.clip_end_var.set("")),
            MAGENTA_DIM, 7).pack(side="left")

    # ── Progress ──────────────────────────────────────────────────────────────
    def _build_progress_section(self, parent):
        o,i = self._nf(parent, CYAN)
        o.pack(fill="x", pady=(0,5))
        hdr = tk.Frame(i, bg=DARK_PANEL); hdr.pack(fill="x")
        self._lbl(hdr,"▸ STATUS", color=CYAN_DIM).pack(side="left")
        self.status_track = tk.Label(hdr, text="// STANDBY //",
            fg=TEXT_DIM, bg=DARK_PANEL, font=(FONT_MONO,8))
        self.status_track.pack(side="right")
        self.prog_canvas = tk.Canvas(i, height=24, bg="#0a1a1a",
            highlightthickness=1, highlightbackground=CYAN_DIM)
        self.prog_canvas.pack(fill="x", pady=(6,4))
        self._draw_progress(0)
        stats = tk.Frame(i, bg=DARK_PANEL); stats.pack(fill="x")
        self.pct_lbl   = tk.Label(stats, text="0%",      fg=CYAN,    bg=DARK_PANEL, font=(FONT_MONO,9,"bold"))
        self.speed_lbl = tk.Label(stats, text="-- KB/s", fg=BLUE,    bg=DARK_PANEL, font=(FONT_MONO,8))
        self.eta_lbl   = tk.Label(stats, text="ETA: --", fg=TEXT_DIM,bg=DARK_PANEL, font=(FONT_MONO,8))
        self.pl_lbl    = tk.Label(stats, text="",        fg=MAGENTA, bg=DARK_PANEL, font=(FONT_MONO,8))
        self.pct_lbl.pack(side="left")
        self.speed_lbl.pack(side="left",padx=(12,0))
        self.eta_lbl.pack(side="left",padx=(12,0))
        self.pl_lbl.pack(side="right")
        btn_row = tk.Frame(i, bg=DARK_PANEL); btn_row.pack(fill="x", pady=(8,0))
        self.dl_btn = tk.Button(btn_row, text="[ ♪ DOWNLOAD MP3 ]",
            command=self._start_download, fg=CYAN, bg="#0a1a1a",
            activeforeground=BG, activebackground=CYAN,
            font=(FONT_MONO,10,"bold"), relief="flat", bd=0,
            width=24, height=2, cursor="hand2",
            highlightthickness=2, highlightbackground=CYAN)
        self.dl_btn.pack(side="left")
        self.dl_btn.bind("<Enter>", lambda e: self.dl_btn.config(bg=CYAN,fg=BG))
        self.dl_btn.bind("<Leave>", lambda e: self.dl_btn.config(bg="#0a1a1a",fg=CYAN))
        self.cancel_btn = self._btn(btn_row,"[ ■ CANCEL ]",
            self._cancel_download, ERROR, 13, 2, "#0a1a1a")
        self.cancel_btn.pack(side="left", padx=(8,0))
        self.cancel_btn.config(state="disabled")
        self._btn(btn_row,"[ OPEN FOLDER ]", self._open_folder,
            SUCCESS, 15, 2, "#0a1a1a").pack(side="right")

    def _draw_progress(self, pct, color=CYAN):
        self.prog_canvas.delete("bar")
        w = self.prog_canvas.winfo_width() or 760
        filled = int(w * pct / 100)
        for x in range(0,w,8):
            self.prog_canvas.create_rectangle(x+1,2,x+6,22,fill=CYAN_DARK,outline="",tags="bar")
        for x in range(0,filled,8):
            self.prog_canvas.create_rectangle(x+1,2,min(x+6,filled),22,fill=color,outline="",tags="bar")
        if filled > 4:
            self.prog_canvas.create_rectangle(filled-3,1,filled+2,23,fill=WHITE,outline="",tags="bar")

    # ── Log ───────────────────────────────────────────────────────────────────
    def _build_log_section(self, parent):
        o,i = self._nf(parent, CYAN_DIM)
        o.pack(fill="both", expand=True, pady=(0,5))
        hdr = tk.Frame(i, bg=DARK_PANEL); hdr.pack(fill="x")
        self._lbl(hdr,"▸ SYSTEM LOG", color=CYAN_DIM).pack(side="left")
        self._btn(hdr,"[ CLR ]", self._clear_log, TEXT_DIM, 6).pack(side="right")
        lf = tk.Frame(i, bg="#0a1a1a", highlightthickness=1,
                      highlightbackground=CYAN_DARK)
        lf.pack(fill="both", expand=True, pady=(4,0))
        self.log_text = tk.Text(lf, font=(FONT_MONO,8), fg=CYAN, bg="#0a1a1a",
            insertbackground=CYAN, relief="flat", bd=6, wrap="word",
            state="disabled", height=6)
        sb = tk.Scrollbar(lf, orient="vertical", command=self.log_text.yview)
        sb.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=sb.set)
        self.log_text.pack(fill="both", expand=True)
        for tag, fg in [("success",SUCCESS),("error",ERROR),("warn",WARNING),
                        ("info",CYAN),("dim",TEXT_DIM),("magenta",MAGENTA),("orange",ORANGE)]:
            self.log_text.tag_configure(tag, foreground=fg)
        self._log("SYSTEM BOOT... SOFTCURSE v4", "magenta")
        self._log("Initialising...", "dim")

    # ════════════════════════════════════════════════════════════════════════════
    # PLAYER TAB
    # ════════════════════════════════════════════════════════════════════════════
    def _build_tab_player(self):
        self.tab_player = tk.Frame(self.main_frame, bg=BG)
        if not check_pygame():
            o,i = self._nf(self.tab_player, MAGENTA_DIM)
            o.pack(fill="x", pady=(0,8))
            self._lbl(i,"⚠️  pygame not installed", size=11, color=WARNING, bold=True).pack(pady=(4,4))
            self._lbl(i,"pygame is required for audio playback.", color=TEXT_DIM).pack()
            self._btn(i,"[ INSTALL PYGAME ]",
                lambda: threading.Thread(target=lambda: install_pygame(
                    log_cb=self._log), daemon=True).start(),
                ORANGE, 22, 2, DARK_PANEL
            ).pack(pady=(8,4))
            self._lbl(i,"After installing, restart the application.", size=7, color=TEXT_DIM).pack()

        self.player_panel = PlayerPanel(self.tab_player)
        self.player_panel.pack(fill="both", expand=True)

    # ════════════════════════════════════════════════════════════════════════════
    # HISTORY TAB
    # ════════════════════════════════════════════════════════════════════════════
    def _build_tab_history(self):
        self.tab_hist = tk.Frame(self.main_frame, bg=BG)
        o,i = self._nf(self.tab_hist, BLUE)
        o.pack(fill="both", expand=True)
        hdr = tk.Frame(i, bg=DARK_PANEL); hdr.pack(fill="x", pady=(0,6))
        self._lbl(hdr,"▸ DOWNLOAD HISTORY", color=BLUE, bold=True).pack(side="left")
        self._btn(hdr,"[ CLEAR ALL ]", self._clear_history, ERROR, 12).pack(side="right")
        self._btn(hdr,"[ ↻ REFRESH ]", self._refresh_history, CYAN_DIM, 12).pack(side="right",padx=(0,6))
        sty = ttk.Style()
        sty.configure("H.Treeview", background="#0a1a1a", foreground=CYAN,
            fieldbackground="#0a1a1a", rowheight=22, font=(FONT_MONO,8))
        sty.configure("H.Treeview.Heading", background=DARK_PANEL,
            foreground=BLUE, font=(FONT_MONO,8,"bold"))
        sty.map("H.Treeview", background=[("selected","#0a3333")],
                foreground=[("selected",CYAN)])
        tf = tk.Frame(i, bg="#0a1a1a"); tf.pack(fill="both", expand=True)
        cols = ("date","title","mode","status","folder")
        self.hist_tree = ttk.Treeview(tf, columns=cols, show="headings",
            style="H.Treeview", selectmode="browse")
        for col,w,stretch in [("date",120,False),("title",260,True),
                               ("mode",60,False),("status",70,False),("folder",180,True)]:
            self.hist_tree.heading(col, text=col.upper())
            self.hist_tree.column(col, width=w, stretch=stretch)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.hist_tree.yview)
        vsb.pack(side="right", fill="y")
        self.hist_tree.config(yscrollcommand=vsb.set)
        self.hist_tree.pack(fill="both", expand=True)
        self.hist_tree.tag_configure("success", foreground=SUCCESS)
        self.hist_tree.tag_configure("failed",  foreground=ERROR)
        act = tk.Frame(i, bg=DARK_PANEL); act.pack(fill="x", pady=(8,0))
        self._btn(act,"[ ↺ RE-DOWNLOAD ]", self._retry_selected, CYAN,   18).pack(side="left")
        self._btn(act,"[ ♪ PLAY FOLDER ]", self._play_from_hist, MAGENTA,16).pack(side="left",padx=(8,0))
        self._btn(act,"[ OPEN FOLDER ]",   self._open_hist_folder,SUCCESS,15).pack(side="left",padx=(8,0))
        self._btn(act,"[ DELETE ]",         self._delete_hist,    ERROR,  10).pack(side="left",padx=(8,0))
        self.hist_entry_ids = []

    def _refresh_history(self):
        for r in self.hist_tree.get_children(): self.hist_tree.delete(r)
        self.hist_entry_ids = []
        for e in hist.load_history():
            tag = "success" if e.get("status")=="success" else "failed"
            m   = {"mp3":"♪ MP3","flac":"◆ FLAC","wav":"◇ WAV","mp4":"▶ MP4"}.get(e.get("mode",""),e.get("mode",""))
            t   = e.get("title","")
            if e.get("count",1)>1: t=f"[{e['count']}] {t}"
            self.hist_tree.insert("","end",values=(
                e.get("timestamp",""), t[:80], m,
                e.get("status","").upper(), e.get("folder","")
            ),tags=(tag,))
            self.hist_entry_ids.append(e.get("id"))

    def _get_hist_entry(self):
        sel = self.hist_tree.selection()
        if not sel: messagebox.showinfo("History","Select an entry first."); return None,None
        idx = self.hist_tree.index(sel[0])
        entries = hist.load_history()
        if idx >= len(entries): return None,None
        return entries[idx], self.hist_entry_ids[idx] if idx<len(self.hist_entry_ids) else None

    def _retry_selected(self):
        entry,_ = self._get_hist_entry()
        if not entry: return
        self.url_var.set(entry.get("url",""))
        mode = entry.get("mode","mp3")
        self._set_mode(mode)
        self._show_tab(TAB_DL)
        self._trigger_fetch()
        self._log(f"↺ Re-queued: {entry.get('title','')[:50]}", "magenta")

    def _play_from_hist(self):
        entry,_ = self._get_hist_entry()
        if not entry: return
        folder = entry.get("folder","")
        if os.path.exists(folder):
            self.player_panel.load_folder(folder)
            self._show_tab(TAB_PLAYER)
        else:
            messagebox.showwarning("Not Found", f"Folder not found:\n{folder}")

    def _open_hist_folder(self):
        entry,_ = self._get_hist_entry()
        if not entry: return
        folder = entry.get("folder","")
        if os.path.exists(folder): os.startfile(folder)
        else: messagebox.showwarning("Not Found", f"Folder not found:\n{folder}")

    def _delete_hist(self):
        entry,eid = self._get_hist_entry()
        if not entry or eid is None: return
        hist.delete_entry(eid); self._refresh_history()

    def _clear_history(self):
        if messagebox.askyesno("Clear History","Delete all history?"):
            hist.clear_history(); self._refresh_history()

    # ════════════════════════════════════════════════════════════════════════════
    # SETTINGS TAB
    # ════════════════════════════════════════════════════════════════════════════
    def _build_tab_settings(self):
        self.tab_settings = tk.Frame(self.main_frame, bg=BG)
        c = tk.Canvas(self.tab_settings, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self.tab_settings, orient="vertical", command=c.yview)
        self._settings_frame = tk.Frame(c, bg=BG)
        self._settings_frame.bind("<Configure>",
            lambda e: c.configure(scrollregion=c.bbox("all")))
        c.create_window((0,0), window=self._settings_frame, anchor="nw")
        c.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); c.pack(side="left", fill="both", expand=True)
        self._build_settings_content(self._settings_frame)

    def _build_settings_content(self, parent):
        # Folders
        o,i = self._nf(parent, CYAN, 10); o.pack(fill="x", pady=(0,8))
        self._lbl(i,"▸ DEFAULT FOLDERS", color=CYAN_DIM, bold=True).pack(anchor="w",pady=(0,6))
        self._setting_folder_vars = {}
        for label,key,default in [
            ("MP3/FLAC/WAV Output:","output_folder",  os.path.join(os.path.expanduser("~"),"Music")),
            ("MP4 Output:",         "mp4_output_folder",os.path.join(os.path.expanduser("~"),"Videos")),
        ]:
            row = tk.Frame(i, bg=DARK_PANEL); row.pack(fill="x", pady=3)
            lbl = self._lbl(row,label,size=8,color=TEXT_DIM); lbl.config(width=22); lbl.pack(side="left",anchor="w")
            var = tk.StringVar(value=self.cfg.get(key,default))
            self._setting_folder_vars[key] = var
            self._entry(row,var).pack(side="left",fill="x",expand=True)
            self._btn(row,"[ BRW ]",
                lambda k=key,v=var: self._browse_setting_folder(k,v),
                BLUE,6).pack(side="left",padx=(4,0))

        # Filename template
        o2,i2 = self._nf(parent, MAGENTA_DIM, 10); o2.pack(fill="x", pady=(0,8))
        self._lbl(i2,"▸ FILENAME TEMPLATE", color=MAGENTA_DIM, bold=True).pack(anchor="w")
        self._lbl(i2,"%(title)s  %(uploader)s  %(upload_date)s  %(id)s  %(track)s",
            size=7,color=TEXT_DIM).pack(anchor="w",pady=(2,6))
        self.tmpl_var = tk.StringVar(value=self.cfg.get("filename_template","%(title)s"))
        self._entry(i2,self.tmpl_var).pack(fill="x")
        pr = tk.Frame(i2, bg=DARK_PANEL); pr.pack(fill="x", pady=(6,0))
        self._lbl(pr,"Presets:",size=7,color=TEXT_DIM).pack(side="left")
        for lbl,tmpl in [("Title only","%(title)s"),("Artist-Title","%(uploader)s - %(title)s"),
                          ("Date-Title","%(upload_date)s - %(title)s"),("ID-Title","%(id)s - %(title)s")]:
            self._btn(pr,lbl,lambda t=tmpl:self.tmpl_var.set(t),
                CYAN_DIM,len(lbl)+2,1,DARK_PANEL,7).pack(side="left",padx=(6,0))

        # Visual
        o3,i3 = self._nf(parent, ORANGE_DIM, 10); o3.pack(fill="x", pady=(0,8))
        self._lbl(i3,"▸ VISUAL EFFECTS", color=ORANGE_DIM, bold=True).pack(anchor="w",pady=(0,6))
        self.crt_var = tk.BooleanVar(value=self.cfg.get("crt_effects",True))
        tk.Checkbutton(i3,text=" CRT Scanline Effect",variable=self.crt_var,
            fg=ORANGE,bg=DARK_PANEL,activeforeground=WHITE,activebackground=DARK_PANEL,
            selectcolor="#0a1a1a",font=(FONT_MONO,9,"bold"),cursor="hand2").pack(anchor="w")

        # Tray
        o4,i4 = self._nf(parent, BLUE, 10); o4.pack(fill="x", pady=(0,8))
        self._lbl(i4,"▸ SYSTEM TRAY & NOTIFICATIONS", color=BLUE, bold=True).pack(anchor="w",pady=(0,6))
        self.tray_var   = tk.BooleanVar(value=self.cfg.get("minimize_to_tray",False))
        self.notify_var = tk.BooleanVar(value=self.cfg.get("notify_on_complete",True))
        for text,var in [
            ("Minimize to tray on close", self.tray_var),
            ("Desktop notification on complete", self.notify_var),
        ]:
            tk.Checkbutton(i4,text=f" {text}",variable=var,
                fg=CYAN,bg=DARK_PANEL,activeforeground=WHITE,activebackground=DARK_PANEL,
                selectcolor="#0a1a1a",font=(FONT_MONO,9),cursor="hand2").pack(anchor="w",pady=2)
        deps = check_tray_deps()
        dl = tk.Label(i4,
            text=f"  pystray: {'✅' if deps['pystray'] else '❌'}   plyer: {'✅' if deps['plyer'] else '❌'}",
            fg=TEXT_DIM,bg=DARK_PANEL,font=(FONT_MONO,7))
        dl.pack(anchor="w",pady=(4,0))
        if not deps["pystray"] or not deps["plyer"]:
            self._btn(i4,"[ INSTALL TRAY DEPS ]",
                lambda:threading.Thread(target=lambda:install_tray_deps(
                    log_callback=self._log),daemon=True).start(),
                BLUE,22,1,DARK_PANEL,8).pack(anchor="w",pady=(6,0))

        # Optional deps
        o5,i5 = self._nf(parent, CYAN_DIM, 10); o5.pack(fill="x", pady=(0,8))
        self._lbl(i5,"▸ OPTIONAL DEPENDENCIES", color=CYAN_DIM, bold=True).pack(anchor="w",pady=(0,6))
        for label,check_fn,install_fn,pkg in [
            ("Pillow (thumbnail preview)", check_pil, install_pil, "Pillow"),
            ("mutagen (metadata writing)", check_mutagen, install_mutagen, "mutagen"),
            ("pygame (mini player)",       check_pygame, install_pygame, "pygame"),
        ]:
            row = tk.Frame(i5, bg=DARK_PANEL); row.pack(fill="x", pady=3)
            ok = check_fn()
            tk.Label(row, text=f"{'✅' if ok else '❌'} {label}",
                fg=SUCCESS if ok else WARNING, bg=DARK_PANEL,
                font=(FONT_MONO,8)).pack(side="left")
            if not ok:
                self._btn(row,f"[ INSTALL ]",
                    lambda f=install_fn: threading.Thread(
                        target=lambda:f(log_cb=self._log),daemon=True).start(),
                    CYAN_DIM,12,1,DARK_PANEL,7).pack(side="right")

        # yt-dlp update
        o6,i6 = self._nf(parent, SUCCESS, 10); o6.pack(fill="x", pady=(0,8))
        self._lbl(i6,"▸ yt-dlp UPDATER", color=SUCCESS, bold=True).pack(anchor="w",pady=(0,6))
        self._lbl(i6,"Keep yt-dlp current to fix YouTube download issues.",
            size=7, color=TEXT_DIM).pack(anchor="w",pady=(0,6))
        self._btn(i6,"[ ↺ UPDATE yt-dlp NOW ]",
            lambda:threading.Thread(target=lambda:self._run_ytdlp_update(),
                daemon=True).start(),
            SUCCESS, 24, 2, DARK_PANEL
        ).pack(anchor="w")

        # Save
        sr = tk.Frame(parent, bg=BG); sr.pack(fill="x", pady=(4,8))
        self._btn(sr,"[ ✔ SAVE SETTINGS ]", self._save_settings, CYAN, 26, 2, BG, 10
                  ).pack(anchor="center")

    def _run_ytdlp_update(self):
        from downloader import update_ytdlp
        update_ytdlp(log_callback=self._log)

    def _browse_setting_folder(self, key, var):
        f = filedialog.askdirectory(title=f"Select {key}", initialdir=var.get())
        if f: var.set(f)

    def _save_settings(self):
        for key, var in self._setting_folder_vars.items():
            self.cfg[key] = var.get()
        self.cfg["filename_template"]  = self.tmpl_var.get() or "%(title)s"
        self.cfg["crt_effects"]        = self.crt_var.get()
        self.cfg["minimize_to_tray"]   = self.tray_var.get()
        self.cfg["notify_on_complete"] = self.notify_var.get()
        save_config(self.cfg)
        if not self.cfg["crt_effects"] and self.crt_canvas:
            self.crt_canvas.delete("all")
        self._log("✅ Settings saved!", "success")
        messagebox.showinfo("Softcurse","Settings saved!")

    # ── Status bar ────────────────────────────────────────────────────────────
    def _build_status_bar(self):
        self.status_bar = tk.Label(self.main_frame,
            text="// SOFTCURSE SYSTEMS ONLINE //",
            fg=TEXT_DIM, bg=BG, font=(FONT_MONO,7), anchor="w")
        self.status_bar.pack(fill="x", pady=(0,2))

    # ════════════════════════════════════════════════════════════════════════════
    # EFFECTS
    # ════════════════════════════════════════════════════════════════════════════
    def _start_effects(self):
        self._glitch_loop()
        self._pulse_loop()
        if self.cfg.get("crt_effects", True):
            self._crt_loop()

    def _glitch_loop(self):
        def glitch():
            chars = "█▓▒░╔╗╚╝║═╠╣╦╩╬▸◂▴▾"
            orig  = "[ YT DOWNLOADER // SOFTCURSE ]"
            def flicker(n=0):
                w = self.title_canvas.winfo_width()
                cx = (w // 2) if w > 10 else 420
                if n>=4:
                    self.title_canvas.itemconfig(self.title_id,text=orig,fill=CYAN)
                    self.title_canvas.itemconfig(self.title_shadow,text=orig,fill=MAGENTA_DIM)
                    self.title_canvas.coords(self.title_shadow, cx + 2, 38)
                    self.title_canvas.coords(self.title_id, cx, 36)
                    return
                g = "".join(random.choice(chars) if random.random()<0.18 else c for c in orig)
                self.title_canvas.itemconfig(self.title_id,text=g,
                    fill=MAGENTA if n%2==0 else CYAN)
                self.title_canvas.coords(self.title_shadow, cx + random.randint(-4,4), 38)
                self.title_canvas.coords(self.title_id, cx + random.randint(-2,2), 36)
                self.root.after(55,lambda:flicker(n+1))
            flicker()
        iv = random.randint(5000,14000)
        self._glitch_after = self.root.after(iv,lambda:(glitch(),self._glitch_loop()))

    def _crt_loop(self):
        if not self.cfg.get("crt_effects",True): return
        self.crt_canvas.delete("scanline")
        h = self.root.winfo_height() or 820
        w = self.root.winfo_width()  or 840
        off = int(time.time()*30)%6
        for y in range(off,h,4):
            self.crt_canvas.create_line(0,y,w,y,fill="#001a1a",width=1,
                tags="scanline",stipple="gray50")
        if random.random()<0.04:
            gy = random.randint(0,h)
            self.crt_canvas.create_line(0,gy,w,gy,fill=MAGENTA,width=1,tags="scanline")
        self.crt_canvas.lower("scanline")
        self._crt_after = self.root.after(80,self._crt_loop)

    def _pulse_loop(self):
        mode = self._mode.get()
        palettes = {
            "mp3":  [CYAN,"#00dddd","#00bbbb","#00aaaa","#00bbbb","#00dddd"],
            "flac": [SUCCESS,"#00dd77","#00bb55","#00aa44","#00bb55","#00dd77"],
            "wav":  [BLUE,"#0077dd","#0055bb","#0044aa","#0055bb","#0077dd"],
            "mp4":  [ORANGE,"#dd7700","#bb6600","#dd7700"],
        }
        palette = palettes.get(mode, palettes["mp3"])
        idx=[0]
        def pulse():
            try: self.dl_btn.config(highlightbackground=palette[idx[0]%len(palette)])
            except: pass
            idx[0]+=1
            self._pulse_after = self.root.after(160,pulse)
        pulse()

    # ════════════════════════════════════════════════════════════════════════════
    # DEPS
    # ════════════════════════════════════════════════════════════════════════════
    def _check_deps_async(self):
        def check():
            if not check_ytdlp():
                self._log("⚠️  yt-dlp missing — installing...","warn")
                ok = install_ytdlp(log_callback=lambda m:self._log(m,"warn"))
                self._log("✅ yt-dlp ready!" if ok else "❌ pip install yt-dlp",
                          "success" if ok else "error")
            else:
                self._log("✅ yt-dlp: ONLINE","success")
            ffmpeg = get_ffmpeg_path()
            self._log("✅ ffmpeg: ONLINE" if ffmpeg else "⚠️  ffmpeg NOT FOUND",
                      "success" if ffmpeg else "warn")
            if not ffmpeg:
                self._log("   Install: winget install ffmpeg","dim")
            for label,ok in [
                ("Pillow",  check_pil()),
                ("mutagen", check_mutagen()),
                ("pygame",  check_pygame()),
            ]:
                self._log(f"{'✅' if ok else 'ℹ️ '} {label}: {'ONLINE' if ok else 'not installed (optional)'}",
                          "success" if ok else "dim")
            self._log("─"*46,"dim")
            self._log("READY — Softcurse v4 // All systems nominal","info")
            self._update_status("READY")
        threading.Thread(target=check,daemon=True).start()

    # ════════════════════════════════════════════════════════════════════════════
    # TRAY
    # ════════════════════════════════════════════════════════════════════════════
    def _maybe_start_tray(self):
        from tray import TRAY_AVAILABLE
        if TRAY_AVAILABLE:
            self._tray = TrayManager(
                on_show=lambda:self.root.after(0,self._restore_window),
                on_quit=lambda:self.root.after(0,self._force_quit))
            self._tray.start()

    def _restore_window(self):
        self.root.deiconify(); self.root.lift()

    def _force_quit(self):
        if self._tray: self._tray.stop()
        self.root.destroy()

    def _on_close(self):
        if self.cfg.get("minimize_to_tray",False) and self._tray:
            self.root.withdraw()
        else:
            self._force_quit()

    # ════════════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ════════════════════════════════════════════════════════════════════════════
    def _paste_url(self):
        try:
            self.url_var.set(self.root.clipboard_get().strip())
            self.root.after(200,self._trigger_fetch)
        except: pass

    def _browse_folder(self):
        f = filedialog.askdirectory(title="Select Output Folder",
                                    initialdir=self.folder_var.get())
        if f:
            self.folder_var.set(f)
            key = "mp4_output_folder" if self._mode.get()=="mp4" else "output_folder"
            self.cfg[key] = f; save_config(self.cfg)

    def _open_folder(self):
        f = self.folder_var.get()
        if os.path.exists(f): os.startfile(f)
        else: messagebox.showwarning("Not Found",f"Folder not found:\n{f}")

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0","end")
        self.log_text.config(state="disabled")

    def _start_download(self):
        url = self.url_var.get().strip()
        if not url or not url.startswith("http"):
            self._log("❌ Invalid URL!","error"); return
        folder = self.folder_var.get().strip()
        if not folder:
            self._log("❌ No output folder!","error"); return

        mode    = self._mode.get()
        quality = self.quality_var.get()
        vq      = self.video_quality_var.get()
        pl      = self.playlist_var.get()
        tmpl    = self.cfg.get("filename_template","%(title)s")
        cs      = self.clip_start_var.get().strip()
        ce      = self.clip_end_var.get().strip()
        meta    = self._dl_metadata if self._dl_metadata else {}
        sb_cats = None
        if self.sb_var.get():
            sb_cats = [k for k,v in self.sb_cat_vars.items() if v.get()]
            if not sb_cats: sb_cats = DEFAULT_CATEGORIES
            self._log(f"🛡  SponsorBlock: {', '.join(sb_cats)}","orange")

        self._downloading = True
        self.dl_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self._draw_progress(0)
        self.pct_lbl.config(text="0%",fg=CYAN)
        self.speed_lbl.config(text="-- KB/s")
        self.eta_lbl.config(text="ETA: --")
        self.pl_lbl.config(text="")
        self.status_track.config(text="// CONNECTING //",fg=BLUE)

        self._dl_url=url; self._dl_mode=mode; self._dl_folder=folder
        ext=mode.upper()
        self._log("─"*46,"dim")
        self._log(f"▸ {url[:65]}{'...' if len(url)>65 else ''}","info")
        self._log(f"▸ Mode: {ext}  |  Folder: {folder}","dim")
        if cs or ce: self._log(f"✂️  Clip: {cs or 'start'} → {ce or 'end'}","magenta")
        if meta and any(meta.values()):
            self._log(f"🏷️  Metadata: {', '.join(f'{k}={v}' for k,v in meta.items() if v)[:60]}","magenta")
        self._log(f"INITIATING {ext} DOWNLOAD...","magenta")
        self._save_cfg_quick()

        self.dl.download(
            url=url, output_folder=folder, mode=mode,
            quality=quality, video_quality=vq,
            is_playlist=pl, filename_template=tmpl,
            clip_start=cs, clip_end=ce,
            sponsorblock_cats=sb_cats,
            metadata=meta,
            on_progress=self._on_progress,
            on_log=self._on_dl_log,
            on_complete=self._on_complete,
            on_error=self._on_error,
        )

    def _cancel_download(self):
        self.dl.cancel()
        self._log("⛔ Cancelling...","warn")
        self._reset_ui()

    def _on_progress(self,data):
        self.root.after(0,lambda:self._update_progress(data))

    def _update_progress(self,data):
        status=data.get("status",""); mode=data.get("mode",self._mode.get())
        colors={"mp3":CYAN,"flac":SUCCESS,"wav":BLUE,"mp4":ORANGE}
        bc=colors.get(mode,CYAN)
        if status=="downloading":
            pct=data.get("percent",0)
            self._draw_progress(pct,bc)
            self.pct_lbl.config(text=f"{pct:.1f}%",fg=bc)
            self.speed_lbl.config(text=data.get("speed","--"))
            self.eta_lbl.config(text=f"ETA: {data.get('eta','--')}")
            fn=data.get("filename","")
            self.status_track.config(text=f"⬇ {fn[:48]}{'...' if len(fn)>48 else ''}",fg=BLUE)
            if self._tray: self._tray.update_tooltip(f"{pct:.0f}% {fn[:30]}")
        elif status=="converting":
            cc=MAGENTA if mode=="mp3" else bc
            self._draw_progress(100,cc); self.pct_lbl.config(text="100%",fg=cc)
            labels={"mp3":"⚙ CONVERTING→MP3","flac":"⚙ CONVERTING→FLAC",
                    "wav":"⚙ CONVERTING→WAV","mp4":"⚙ MERGING VIDEO"}
            self.status_track.config(text=labels.get(mode,"⚙ PROCESSING"),fg=cc)
        elif status=="playlist":
            cur=data.get("current",0); total=data.get("total",0)
            pct=(cur-1)/total*100 if total>0 else 0
            self._draw_progress(pct,BLUE)
            self.pl_lbl.config(text=f"[{cur}/{total}]",fg=MAGENTA)
            t=data.get("title",""); self.status_track.config(text=f"⬇ {t[:48]}",fg=BLUE)

    def _on_dl_log(self,msg): self.root.after(0,lambda:self._log(msg))

    def _on_complete(self,count,title=""):
        def update():
            self._draw_progress(100,SUCCESS)
            self.pct_lbl.config(text="100%",fg=SUCCESS)
            self.status_track.config(text="// COMPLETE //",fg=SUCCESS)
            ext=self._dl_mode.upper()
            self._log(f"🎉 COMPLETE — {count} {ext} file(s) saved!","success")
            self._log("─"*46,"dim")
            self._reset_ui()
            self._update_status("COMPLETE")
            hist.add_entry(title or self._dl_url[:80],self._dl_url,
                           self._dl_mode,self._dl_folder,count,"success")
            if self.cfg.get("notify_on_complete",True):
                send_notification("Softcurse — Complete",
                    f"{count} {ext} file(s) saved!\n{title[:50] if title else ''}")
            if self._tray: self._tray.update_tooltip("Download Complete!")
            # Auto-load into player if audio
            if self._dl_mode in ("mp3","flac","wav") and check_pygame():
                self.player_panel.load_folder(self._dl_folder)
        self.root.after(0,update)

    def _on_error(self,error):
        def update():
            self._draw_progress(0)
            self.status_track.config(text="// ERROR //",fg=ERROR)
            self._log(f"❌ ERROR: {error}","error")
            self._reset_ui(); self._update_status("ERROR")
            hist.add_failed_entry(self._dl_url,self._dl_mode,self._dl_folder,error)
            if self.cfg.get("notify_on_complete",True):
                send_notification("Softcurse — Error",f"Download failed: {error[:80]}")
        self.root.after(0,update)

    def _reset_ui(self):
        self._downloading=False
        self.dl_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")

    def _update_status(self,msg):
        ts=time.strftime("%H:%M:%S")
        self.status_bar.config(text=f"// {msg} // [{ts}] // SOFTCURSE v4 //")

    # ── Logging ───────────────────────────────────────────────────────────────
    def _log(self,msg,tag="info"):
        def _do():
            self.log_text.config(state="normal")
            ts=time.strftime("%H:%M:%S")
            if tag=="info":
                if any(x in msg for x in ["✅","🎉","COMPLETE"]): t="success"
                elif any(x in msg for x in ["❌","ERROR"]):       t="error"
                elif any(x in msg for x in ["⚠️","warn"]):        t="warn"
                else: t="info"
            else: t=tag
            self.log_text.insert("end",f"[{ts}] {msg}\n",t)
            self.log_text.see("end"); self.log_text.config(state="disabled")
            lines=int(self.log_text.index("end-1c").split(".")[0])
            if lines>300:
                self.log_text.config(state="normal")
                self.log_text.delete("1.0","60.0")
                self.log_text.config(state="disabled")
        self.root.after(0,_do)

    # ── Config ────────────────────────────────────────────────────────────────
    def _save_cfg_quick(self):
        mode=self._mode.get()
        key = "mp4_output_folder" if mode=="mp4" else "output_folder"
        self.cfg[key]             = self.folder_var.get()
        self.cfg["quality"]       = self.quality_var.get()
        self.cfg["video_quality"] = self.video_quality_var.get()
        self.cfg["last_url"]      = self.url_var.get()
        self.cfg["sponsorblock"]  = self.sb_var.get()
        self.cfg["sb_categories"] = [k for k,v in self.sb_cat_vars.items() if v.get()]
        save_config(self.cfg)