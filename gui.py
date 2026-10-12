"""
gui.py - Softcurse // Media Downloader v1.0
Redesigned UI: cleaner card layout, glowing accents, friendly sci-fi aesthetic
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, time, random, os, math, sys, webbrowser

from config import load_config, save_config
from downloader import Downloader
from download_models import DownloadRequest, DownloadResult, DownloadStatus, ProgressUpdate
from download_queue import DownloadQueue, QueueStatus
from dependency_status import collect_dependency_status, required_ready
import history as hist
from app_info import APP_TITLE, APP_VERSION, icon_path
from tray import TrayManager, send_notification, check_tray_deps, install_tray_deps
from thumbnail import fetch_info_and_thumb, check_pil, install_pil
from metadata_editor import MetadataEditorDialog, check_mutagen, install_mutagen
from player import PlayerPanel, check_pygame, install_pygame
from preview_controller import PreviewRequestCoordinator
from sponsorblock import CATEGORY_LABELS, DEFAULT_CATEGORIES
from ui_theme import (
    ACCENT_LINE, BG, BLUE, BLUE_DIM, CARD, CARD_BORDER, CYAN, CYAN_DARK,
    CYAN_DIM, CYAN_GLOW, ERROR, FONT_MONO, FONT_UI, MAGENTA, MAGENTA_DIM,
    MAGENTA_GLOW, ORANGE, ORANGE_DIM, PANEL, SUCCESS, SUCCESS_DIM, TEXT_DIM,
    TEXT_MED, WARNING, WHITE,
)
from ux_state import present_error
from update_checker import check_for_update

#  Palette  SOFTCURSE/SYS Design System 

TAB_DL=0; TAB_PLAYER=1; TAB_HISTORY=2; TAB_SETTINGS=3


class SoftcurseApp:
    def __init__(self, root: tk.Tk, downloader=None, history_service=None,
                 config_loader=load_config, config_saver=save_config):
        self.root = root
        self._config_saver = config_saver
        self._history = history_service or hist
        self.cfg = config_loader()
        self.dl = downloader or Downloader()
        self._downloading   = False
        self._mode          = tk.StringVar(value="mp3")
        self._platform      = tk.StringVar(value="youtube")
        self._active_tab    = TAB_DL
        self._thumb_photo   = None
        self._pending_info  = None
        self._preview_requests = PreviewRequestCoordinator()
        self._crt_after     = None
        self._glitch_after  = None
        self._pulse_after   = None
        self._resize_after  = None
        self._scanline_ids  = []
        self._glitch_line_id= None
        self._color_cache   = {}
        self._tray          = None
        self._dl_metadata   = {}
        self._dl_url = self._dl_mode = self._dl_folder = ""
        self._download_queue = DownloadQueue()
        self._active_queue_id = None

        self._setup_window()
        self._build_ui()
        self._bind_shortcuts()
        self._start_effects()
        self._check_deps_async()
        self._maybe_start_tray()

    def _setup_window(self):
        self.root.title(APP_TITLE)
        self.root.geometry("860x840")
        self.root.minsize(760, 700)
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        def remove_maximize():
            try:
                import ctypes
                GWL_STYLE = -16
                WS_MAXIMIZEBOX = 0x00010000
                SWP_FLAGS = 0x0027  # FRAMECHANGED|NOMOVE|NOSIZE|NOZORDER
                # Use wm_frame() for reliable HWND on modern Windows
                hwnd = int(self.root.wm_frame(), 16)
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style & ~WS_MAXIMIZEBOX)
                ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_FLAGS)
            except Exception:
                pass
        self.root.after(100, remove_maximize)
        app_icon = icon_path()
        if app_icon:
            try:
                self.root.iconbitmap(app_icon)
            except tk.TclError:
                pass
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()  - 860) // 2
        y = (self.root.winfo_screenheight() - 840) // 2
        self.root.geometry(f"860x840+{x}+{y}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _bind_shortcuts(self):
        self.root.bind("<Control-l>", self._focus_url)
        self.root.bind("<Control-d>", lambda event: self._start_download())
        self.root.bind("<Escape>", self._handle_escape)
        for number, tab in enumerate((TAB_DL, TAB_PLAYER, TAB_HISTORY, TAB_SETTINGS), 1):
            self.root.bind(f"<Control-Key-{number}>", lambda event, idx=tab: self._show_tab(idx))

    def _focus_url(self, event=None):
        self._show_tab(TAB_DL)
        self.url_entry.focus_set()
        self.url_entry.selection_range(0, "end")
        return "break"

    def _handle_escape(self, event=None):
        if self._downloading:
            self._cancel_download()
        elif self._active_tab != TAB_DL:
            self._show_tab(TAB_DL)
        else:
            self.url_entry.focus_set()
        return "break"

    #  Layout 
    def _build_ui(self):
        # Background layer: subtle dot grid
        self.bg_canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._draw_bg()
        self.crt_canvas = self.bg_canvas
        # Bind Configure ONCE with debounce (Fix #1)
        self.root.bind("<Configure>", self._on_resize)

        # Main scrollable container
        outer = tk.Frame(self.root, bg=BG)
        outer.place(x=0, y=0, relwidth=1, relheight=1)

        self.main_canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        self.main_scroll = tk.Scrollbar(outer, orient="vertical",
                                        command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self.main_scroll.set)

        # Don't show scrollbar unless needed  always use the canvas
        self.main_canvas.pack(side="left", fill="both", expand=True)

        self.main_frame = tk.Frame(self.main_canvas, bg=BG)
        self._mf_id = self.main_canvas.create_window((0, 0), window=self.main_frame,
                                                      anchor="nw")
        self.main_frame.bind("<Configure>", self._on_frame_configure)
        self.main_canvas.bind("<Configure>", self._on_canvas_configure)
        self.main_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._build_header()
        self._build_nav_tabs()
        self._build_tab_download()
        self._build_tab_player()
        self._build_tab_history()
        self._build_tab_settings()
        self._build_status_bar()
        self._show_tab(TAB_DL)

    def _on_frame_configure(self, e):
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self.main_canvas.itemconfig(self._mf_id, width=e.width)

    def _on_mousewheel(self, e):
        self.main_canvas.yview_scroll(int(-1*(e.delta/120)), "units")

    def _on_resize(self, event=None):
        """Debounced resize handler — redraws bg + rebuilds CRT scanlines."""
        if self._resize_after:
            self.root.after_cancel(self._resize_after)
        self._resize_after = self.root.after(100, self._do_resize)

    def _do_resize(self):
        self._draw_bg()
        width = self.root.winfo_width() or 860
        compact = width < 820
        title_size = 16 if compact else 20
        self.title_canvas.itemconfig(self.title_id, font=(FONT_MONO, title_size, "bold"))
        self.title_canvas.itemconfig(self.title_shadow, font=(FONT_MONO, title_size, "bold"))
        if hasattr(self, "info_title"):
            self.info_title.config(wraplength=max(260, width - 390))
        if hasattr(self, "_tab_btns"):
            for button, _ in self._tab_btns.values():
                button.config(font=(FONT_MONO, 10 if compact else 13, "bold"),
                              padx=8 if compact else 18)
        if hasattr(self, "hist_tree"):
            content_width = max(650, width - 90)
            self.hist_tree.column("title", width=int(content_width * 0.34))
            self.hist_tree.column("folder", width=int(content_width * 0.25))
        if self.cfg.get("crt_effects", True) and not self.cfg.get("reduced_motion", False):
            self._build_crt_scanlines()

    def _draw_bg(self):
        self.bg_canvas.delete("bg")
        w = self.root.winfo_width()  or 860
        h = self.root.winfo_height() or 840
        # Cyan line grid  40px spacing, ghost opacity
        grid_color = "#0a171e"
        for x in range(0, w, 40):
            self.bg_canvas.create_line(x, 0, x, h,
                fill=grid_color, width=1, tags="bg")
        for y in range(0, h, 40):
            self.bg_canvas.create_line(0, y, w, y,
                fill=grid_color, width=1, tags="bg")
        # Ambient glow bloom  subtle radial at center
        cx, cy = w // 2, h // 3
        for r, alpha in [(200, 0.08), (350, 0.04), (500, 0.02)]:
            shade = self._blend_color(BG, CYAN_GLOW, alpha)
            self.bg_canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=shade, outline="", tags="bg")
        # Fix #1: No re-bind here — bound once in _build_ui

    def _blend_color(self, c1, c2, t):
        # Fix #6: Cache parsed colors
        key = (c1, c2, t)
        cached = self._color_cache.get(key)
        if cached:
            return cached
        r1,g1,b1 = int(c1[1:3],16),int(c1[3:5],16),int(c1[5:7],16)
        r2,g2,b2 = int(c2[1:3],16),int(c2[3:5],16),int(c2[5:7],16)
        result = "#{:02x}{:02x}{:02x}".format(
            int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))
        self._color_cache[key] = result
        return result

    #  Widget helpers 
    def _card(self, parent, color=CYAN, pad=12, title=None, title_color=None):
        """Returns (outer_frame, inner_frame). Draws a styled card with glow border."""
        tc = title_color or color
        outer = tk.Frame(parent, bg=color, padx=1, pady=1)
        # Header bar inside card
        inner_wrap = tk.Frame(outer, bg=CARD)
        inner_wrap.pack(fill="both", expand=True)
        if title:
            hdr = tk.Frame(inner_wrap, bg=CARD, height=32)
            hdr.pack(fill="x")
            hdr.pack_propagate(False)
            # Left accent line
            tk.Frame(hdr, bg=tc, width=3).pack(side="left", fill="y", padx=(0,10))
            tk.Label(hdr, text=title.upper(), fg=tc, bg=CARD,
                     font=(FONT_MONO, 10, "bold")).pack(side="left", pady=8)
            # Separator
            sep = tk.Frame(inner_wrap, bg=ACCENT_LINE, height=1)
            sep.pack(fill="x")
        inner = tk.Frame(inner_wrap, bg=CARD, padx=pad, pady=pad)
        inner.pack(fill="both", expand=True)
        return outer, inner

    def _lbl(self, p, text, size=8, color=CYAN, bold=False, bg=CARD):
        return tk.Label(p, text=text, fg=color, bg=bg,
                        font=(FONT_MONO, size, "bold" if bold else "normal"))

    def _btn(self, p, text, cmd, color=CYAN, w=16, h=1, bg=CARD, size=9):
        b = tk.Button(p, text=text, command=cmd, fg=color, bg=bg,
                      activeforeground=BG, activebackground=color,
                      font=(FONT_MONO, size, "bold"), relief="flat", bd=0,
                      width=w, height=h, cursor="hand2",
                      takefocus=True, highlightthickness=2,
                      highlightbackground=ACCENT_LINE, highlightcolor=WHITE)
        b.bind("<Enter>", lambda e: b.config(bg=color, fg=BG))
        b.bind("<Leave>", lambda e: b.config(bg=bg, fg=color))
        return b

    def _bigbtn(self, p, text, cmd, color=CYAN, w=22, h=2):
        """Large prominent CTA button with glow effect."""
        container = tk.Frame(p, bg=color, padx=2, pady=2)
        b = tk.Button(container, text=text, command=cmd,
                      fg=color, bg=PANEL,
                      activeforeground=BG, activebackground=color,
                      font=(FONT_MONO, 13, "bold"), relief="flat", bd=0,
                      width=w, height=h, cursor="hand2", takefocus=True,
                      highlightthickness=2, highlightbackground=ACCENT_LINE,
                      highlightcolor=WHITE)
        b.pack(fill="both", expand=True)
        b.bind("<Enter>", lambda e: b.config(bg=color, fg=BG))
        b.bind("<Leave>", lambda e: b.config(bg=PANEL, fg=color))
        return container, b

    def _entry(self, p, var, width=None):
        kw = dict(font=(FONT_MONO, 11), fg=WHITE, bg=PANEL,
                  insertbackground=CYAN, relief="flat", bd=6,
                  highlightthickness=1, highlightbackground=CYAN_DIM,
                  highlightcolor=CYAN)
        if width: kw["width"] = width
        e = tk.Entry(p, textvariable=var, **kw)
        e.bind("<FocusIn>",  lambda ev: e.config(highlightbackground=CYAN))
        e.bind("<FocusOut>", lambda ev: e.config(highlightbackground=CYAN_DIM))
        return e

    def _sep(self, parent, color=ACCENT_LINE):
        tk.Frame(parent, bg=color, height=1).pack(fill="x", pady=6)

    #  Header 
    def _build_header(self):
        f = tk.Frame(self.main_frame, bg=BG)
        f.pack(fill="x", padx=20, pady=(18, 8))

        self.title_canvas = tk.Canvas(f, bg=BG, height=80, highlightthickness=0)
        self.title_canvas.pack(fill="x")

        # Decorative corner brackets
        self._corner_tl = self.title_canvas.create_text(20, 12,
            text="<>", font=(FONT_MONO, 10, "bold"), fill=MAGENTA, anchor="w")
        self._corner_tr = self.title_canvas.create_text(820, 12,
            text="<>", font=(FONT_MONO, 10, "bold"), fill=MAGENTA, anchor="e")

        # Sub-label
        self.t_sub = self.title_canvas.create_text(420, 14,
            text="S  O  F  T  C  U  R  S  E",
            font=(FONT_MONO, 13, "bold"), fill=MAGENTA_DIM, anchor="center")

        # Shadow + main title
        self.title_shadow = self.title_canvas.create_text(422, 44,
            text="[ MEDIA DOWNLOADER // SOFTCURSE ]",
            font=(FONT_MONO, 20, "bold"), fill=MAGENTA_DIM, anchor="center")
        self.title_id = self.title_canvas.create_text(420, 42,
            text="[ MEDIA DOWNLOADER // SOFTCURSE ]",
            font=(FONT_MONO, 20, "bold"), fill=CYAN, anchor="center")

        # Feature tags row
        self.t4 = self.title_canvas.create_text(420, 66,
            text="YOUTUBE  |  INSTAGRAM  |  TIKTOK  |  X  //  MP3  |  FLAC  |  WAV  |  MP4",
            font=(FONT_MONO, 9), fill=TEXT_MED, anchor="center")

        self.title_canvas.bind("<Configure>", lambda e: self._center_header(e.width))

    def _center_header(self, w):
        cx = w // 2
        self.title_canvas.coords(self.t_sub, cx, 14)
        self.title_canvas.coords(self._corner_tr, w - 20, 12)
        self.title_canvas.coords(self.title_shadow, cx + 2, 44)
        self.title_canvas.coords(self.title_id, cx, 42)
        self.title_canvas.coords(self.t4, cx, 66)

    #  Nav tabs 
    def _build_nav_tabs(self):
        nav_outer = tk.Frame(self.main_frame, bg=CARD, padx=1, pady=1)
        nav_outer.pack(fill="x", padx=20, pady=(0, 14))
        nav_inner = tk.Frame(nav_outer, bg=CARD)
        nav_inner.pack(fill="x")

        # Centered button row
        btn_row = tk.Frame(nav_inner, bg=CARD)
        btn_row.pack(expand=True, anchor="center")

        self._tab_btns = {}
        for label, idx, color in [
            (">> DOWNLOAD", TAB_DL,       CYAN),
            ("*  PLAYER",   TAB_PLAYER,    MAGENTA),
            ("#  HISTORY",  TAB_HISTORY,   BLUE),
            ("@  SETTINGS", TAB_SETTINGS,  ORANGE),
        ]:
            b = tk.Button(btn_row, text=label,
                          command=lambda i=idx: self._show_tab(i),
                          font=(FONT_MONO, 13, "bold"), relief="flat", bd=0,
                          padx=18, pady=10, cursor="hand2", takefocus=True,
                          highlightthickness=2, highlightbackground=ACCENT_LINE,
                          highlightcolor=WHITE)
            b.pack(side="left")
            self._tab_btns[idx] = (b, color)

        self._tab_ind = tk.Label(nav_inner, text="", fg=TEXT_DIM, bg=CARD,
                                  font=(FONT_MONO, 11))
        self._tab_ind.pack(pady=(0, 4))

    def _show_tab(self, idx):
        self._active_tab = idx
        for i, (b, color) in self._tab_btns.items():
            if i == idx:
                b.config(fg=BG, bg=color, highlightthickness=0)
            else:
                b.config(fg=TEXT_MED, bg=CARD, highlightthickness=0)
        frames = {TAB_DL: self.tab_dl, TAB_PLAYER: self.tab_player,
                  TAB_HISTORY: self.tab_hist, TAB_SETTINGS: self.tab_settings}
        labels = {TAB_DL: "DOWNLOAD", TAB_PLAYER: "MINI PLAYER",
                  TAB_HISTORY: "HISTORY", TAB_SETTINGS: "SETTINGS"}
        for i, fr in frames.items():
            if i == idx:
                fr.pack(fill="both", expand=True, padx=20, pady=(0, 10))
            else:
                fr.pack_forget()
        self._tab_ind.config(text=f"// {labels.get(idx, '')} //")
        if idx == TAB_HISTORY:
            self._refresh_history()

    # 
    # DOWNLOAD TAB
    # 
    def _build_tab_download(self):
        self.tab_dl = tk.Frame(self.main_frame, bg=BG)
        self._build_format_tabs(self.tab_dl)
        self._build_url_section(self.tab_dl)
        self._build_queue_section(self.tab_dl)
        self._build_thumb_section(self.tab_dl)
        self._build_options_section(self.tab_dl)
        self._build_sb_section(self.tab_dl)
        self._build_clip_section(self.tab_dl)
        self._build_progress_section(self.tab_dl)
        self._build_log_section(self.tab_dl)

    #  Platform + Format selector (two-tier) 
    def _build_format_tabs(self, parent):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=(0, 8))

        #  Row 1: Platform selector 
        plat_lbl = tk.Label(f, text="> PLATFORM", fg=TEXT_DIM, bg=BG,
                            font=(FONT_MONO, 9))
        plat_lbl.pack(anchor="center", pady=(0, 4))
        plat_row = tk.Frame(f, bg=BG)
        plat_row.pack(anchor="center")
        self._plat_btns = {}
        platforms = [
            ("YOUTUBE",   "youtube",   CYAN),
            ("INSTAGRAM", "instagram", ORANGE),
            ("TIKTOK",    "tiktok",    MAGENTA),
            ("X",         "x",         WHITE),
        ]
        for label, plat, color in platforms:
            wrap = tk.Frame(plat_row, bg=color, padx=1, pady=1)
            wrap.pack(side="left", padx=4)
            b = tk.Button(wrap, text=f"  {label}  ",
                          command=lambda p=plat: self._set_platform(p),
                          font=(FONT_MONO, 13, "bold"), relief="flat", bd=0,
                          cursor="hand2", padx=10, pady=6, takefocus=True,
                          highlightthickness=2, highlightbackground=ACCENT_LINE,
                          highlightcolor=WHITE)
            b.pack()
            self._plat_btns[plat] = (wrap, b, color)

        #  Row 2: Format selector (hidden until platform chosen) 
        self._fmt_lbl = tk.Label(f, text="> FORMAT", fg=TEXT_DIM, bg=BG,
                           font=(FONT_MONO, 9))
        self._fmt_row = tk.Frame(f, bg=BG)
        self._fmt_btns = {}
        formats = [
            (">>  MP3",   "mp3",  CYAN),
            ("**  FLAC",  "flac", SUCCESS),
            ("<>  WAV",   "wav",  BLUE),
            ("|>  MP4",   "mp4",  ORANGE),
        ]
        for label, mode, color in formats:
            wrap = tk.Frame(self._fmt_row, bg=color, padx=1, pady=1)
            wrap.pack(side="left", padx=4)
            b = tk.Button(wrap, text=f"  {label}  ",
                          command=lambda m=mode: self._set_mode(m),
                          font=(FONT_MONO, 13, "bold"), relief="flat", bd=0,
                          cursor="hand2", padx=10, pady=6, takefocus=True,
                          highlightthickness=2, highlightbackground=ACCENT_LINE,
                          highlightcolor=WHITE)
            b.pack()
            self._fmt_btns[mode] = (wrap, b, color)

        self.mode_lbl = tk.Label(f, text="", fg=CYAN_DIM, bg=BG,
                                  font=(FONT_MONO, 11))
        # Keep format row hidden  revealed on first platform click
        self._fmt_visible = False

    def _set_platform(self, plat: str):
        self._platform.set(plat)
        plat_colors = {"youtube": CYAN, "instagram": ORANGE,
                       "tiktok": MAGENTA, "x": WHITE}
        for p, (wrap, b, c) in self._plat_btns.items():
            if p == plat:
                b.config(fg=BG, bg=c)
                wrap.config(bg=c)
            else:
                b.config(fg=TEXT_MED, bg=CARD)
                wrap.config(bg=ACCENT_LINE)
        # Reveal format row on first platform click
        if not self._fmt_visible:
            self._fmt_visible = True
            self._fmt_lbl.pack(anchor="center", pady=(10, 4))
            self._fmt_row.pack(anchor="center")
            self.mode_lbl.pack(pady=(6, 0))
            self._set_mode("mp3")
        # SponsorBlock is YouTube-only
        try:
            if hasattr(self, "sb_outer"):
                is_yt = (plat == "youtube")
                is_audio = self._mode.get() in ("mp3", "flac", "wav")
                if is_yt and is_audio:
                    self.sb_outer.pack(fill="x", pady=(0, 8), before=self.clip_outer)
                else:
                    self.sb_outer.pack_forget()
        except Exception:
            pass

    def _set_mode(self, mode: str):
        self._mode.set(mode)
        colors = {"mp3": CYAN, "flac": SUCCESS, "wav": BLUE, "mp4": ORANGE}
        labels = {
            "mp3":  "MODE: MP3 -- Lossy audio, universal compatibility",
            "flac": "MODE: FLAC -- Lossless audio, audiophile quality",
            "wav":  "MODE: WAV -- Uncompressed audio, studio / DAW ready",
            "mp4":  "MODE: MP4 -- Video with audio",
        }
        for m, (wrap, b, c) in self._fmt_btns.items():
            if m == mode:
                b.config(fg=BG, bg=c)
                wrap.config(bg=c)
            else:
                b.config(fg=TEXT_MED, bg=CARD)
                wrap.config(bg=ACCENT_LINE)
        self.mode_lbl.config(text=labels.get(mode, ""), fg=colors.get(mode, CYAN_DIM))

        try:
            is_audio = mode in ("mp3", "flac", "wav")
            is_mp3   = mode == "mp3"
            if is_audio:
                self.mp4_q_frame.pack_forget()
                self.audio_q_frame.pack(side="left")
                self.kbps_lbl.config(text=" kbps" if is_mp3 else " (lossless)")
            else:
                self.audio_q_frame.pack_forget()
                self.mp4_q_frame.pack(side="left")
            if hasattr(self, "sb_outer"):
                is_yt = self._platform.get() == "youtube"
                if is_audio and is_yt:
                    self.sb_outer.pack(fill="x", pady=(0, 8), before=self.clip_outer)
                else:
                    self.sb_outer.pack_forget()
            if mode == "mp4":
                self.folder_var.set(self.cfg.get("mp4_output_folder", ""))
            else:
                self.folder_var.set(self.cfg.get("output_folder", ""))
            icon  = {"mp3": ">>", "flac": "**", "wav": "<>", "mp4": "|>"}.get(mode, ">>")
            c     = colors.get(mode, CYAN)
            self.dl_btn_inner.config(
                text=f"  {icon}  DOWNLOAD {mode.upper()}  ",
                fg=c)
            self.dl_btn_outer.config(bg=c)
        except AttributeError:
            pass

    #  URL 
    def _build_url_section(self, parent):
        o, i = self._card(parent, CYAN, pad=12, title="> Target URL")
        o.pack(fill="x", pady=(0, 8))
        row = tk.Frame(i, bg=CARD); row.pack(fill="x", pady=(4, 0))
        self.url_var = tk.StringVar(value=self.cfg.get("last_url", ""))
        self.url_entry = self._entry(row, self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>",   lambda e: self._trigger_fetch())
        self.url_entry.bind("<FocusOut>", lambda e: self._trigger_fetch())
        self._btn(row, "PASTE",  self._paste_url, CYAN,    7).pack(side="left", padx=(8, 0))
        self._btn(row, "CLR",    lambda: (self.url_var.set(""), self._clear_preview()),
                  TEXT_DIM, 5).pack(side="left", padx=(4, 0))
        self._btn(row, "FETCH", self._trigger_fetch, BLUE, 8).pack(side="left", padx=(4, 0))

    def _build_queue_section(self, parent):
        outer, inner = self._card(parent, BLUE_DIM, pad=8, title="> Download Queue")
        outer.pack(fill="x", pady=(0, 8))
        controls = tk.Frame(inner, bg=CARD)
        controls.pack(fill="x", pady=(0, 6))
        self._btn(controls, "[ + URL ]", self._add_current_to_queue, BLUE, 9).pack(side="left")
        self._btn(controls, "[ START ]", self._start_queue, SUCCESS, 10).pack(
            side="left", padx=(6, 0))
        self._btn(controls, "[ REMOVE ]", self._remove_queued_item, WARNING, 11).pack(
            side="left", padx=(6, 0))
        self._btn(controls, "[ CLEAR DONE ]", self._clear_finished_queue, TEXT_DIM, 14).pack(
            side="right")
        self.queue_list = tk.Listbox(
            inner, height=4, font=(FONT_MONO, 9), fg=CYAN, bg=PANEL,
            selectforeground=WHITE, selectbackground=CYAN_DARK,
            relief="flat", bd=4, highlightthickness=1,
            highlightbackground=ACCENT_LINE, highlightcolor=WHITE,
            exportselection=False,
        )
        self.queue_list.pack(fill="x")
        self.queue_item_ids = []

    def _refresh_queue(self):
        self.queue_list.delete(0, "end")
        self.queue_item_ids = []
        labels = {
            QueueStatus.PENDING: "WAIT", QueueStatus.ACTIVE: "RUN",
            QueueStatus.COMPLETE: "OK", QueueStatus.FAILED: "ERR",
            QueueStatus.CANCELLED: "STOP",
        }
        for item in self._download_queue.items:
            detail = f" - {item.detail[:45]}" if item.detail else ""
            self.queue_list.insert("end", f"[{labels[item.status]:4}] {item.url[:85]}{detail}")
            self.queue_item_ids.append(item.id)

    def _add_current_to_queue(self):
        added = self._download_queue.add_urls([self.url_var.get()])
        if not added:
            self._log(" Queue: URL is invalid or already pending", "warn")
        self._refresh_queue()

    def _start_queue(self):
        if self._downloading:
            self._log(" A download is already running", "warn")
            return
        if not self._download_queue.items:
            self._add_current_to_queue()
        self._run_next_queue()

    def _run_next_queue(self):
        if self._downloading:
            return
        item = self._download_queue.next_pending()
        if not item:
            self._active_queue_id = None
            self._refresh_queue()
            self._log(" Queue finished", "success")
            return
        self._active_queue_id = item.id
        self._refresh_queue()
        self._start_download(item.url)

    def _remove_queued_item(self):
        selection = self.queue_list.curselection()
        if not selection:
            return
        index = selection[0]
        if index < len(self.queue_item_ids):
            if not self._download_queue.remove_pending(self.queue_item_ids[index]):
                self._log(" Only waiting queue items can be removed", "warn")
            self._refresh_queue()

    def _clear_finished_queue(self):
        self._download_queue.clear_terminal()
        self._refresh_queue()

    #  Thumbnail 
    def _build_thumb_section(self, parent):
        o, i = self._card(parent, CYAN_DIM, pad=10, title="> Preview")
        o.pack(fill="x", pady=(0, 8))
        row = tk.Frame(i, bg=CARD); row.pack(fill="x")

        # Thumbnail box with subtle border
        thumb_border = tk.Frame(row, bg=CYAN_DARK, padx=1, pady=1)
        thumb_border.pack(side="left", padx=(0, 14))
        self.thumb_canvas = tk.Canvas(thumb_border, width=168, height=96,
            bg=PANEL, highlightthickness=0)
        self.thumb_canvas.pack()
        self.thumb_canvas.create_text(84, 48, text="NO PREVIEW", fill=TEXT_DIM,
                                      font=(FONT_MONO, 10))

        col = tk.Frame(row, bg=CARD); col.pack(side="left", fill="both", expand=True)
        self.info_title = tk.Label(col, text="// PASTE A URL TO PREVIEW //",
            fg=TEXT_MED, bg=CARD, font=(FONT_MONO, 13, "bold"),
            wraplength=420, justify="left", anchor="w")
        self.info_title.pack(anchor="w")
        self.info_meta = tk.Label(col, text="", fg=BLUE, bg=CARD,
            font=(FONT_MONO, 10), justify="left", anchor="w")
        self.info_meta.pack(anchor="w", pady=(6, 0))
        self.info_status = tk.Label(col, text="", fg=CYAN_DIM, bg=CARD,
            font=(FONT_MONO, 11), justify="left", anchor="w")
        self.info_status.pack(anchor="w", pady=(2, 0))
        self.meta_btn = self._btn(col, "[ EDIT METADATA ]",
                                  self._open_metadata_editor,
                                  MAGENTA_DIM, 20, 1, CARD, 8)
        self.meta_btn.pack(anchor="w", pady=(8, 0))
        self.meta_btn.pack_forget()

    def _trigger_fetch(self):
        url = self.url_var.get().strip()
        if not url or not url.startswith("http"): return
        if not self._preview_requests.begin(url): return
        self._clear_preview(keep_url=True)
        self.info_status.config(text="~ Fetching...", fg=WARNING)
        fetch_info_and_thumb(url,
            on_info=lambda d, request_url=url: self.root.after(
                0, lambda: self._on_info_if_current(request_url, d)),
            on_thumb=lambda p, request_url=url: self.root.after(
                0, lambda: self._on_thumb_if_current(request_url, p)),
            on_error=lambda e, request_url=url: self.root.after(
                0, lambda: self._on_preview_error_if_current(request_url, e)),
            thumb_size=(164, 94))

    def _on_info_if_current(self, request_url, data):
        if self._preview_requests.is_current(request_url):
            self._on_info(data)

    def _on_thumb_if_current(self, request_url, photo):
        if self._preview_requests.is_current(request_url):
            self._on_thumb(photo)

    def _on_preview_error_if_current(self, request_url, error):
        if self._preview_requests.is_current(request_url):
            self.info_status.config(text=f" {error[:60]}", fg=WARNING)

    def _on_info(self, d):
        self._pending_info = d
        title = d.get("title", "")
        if d.get("type") == "playlist":
            count = d.get("count", 0)
            meta  = f"[PL] Playlist  |  {count} items"
            ch    = d.get("channel", "")
            if ch: meta += f"  |  {ch}"
            self.info_status.config(text="OK Playlist -- enable PLAYLIST MODE below", fg=SUCCESS)
        else:
            parts = []
            if d.get("duration"):   parts.append(f"T: {d['duration']}")
            if d.get("channel"):    parts.append(f"By: {d['channel']}")
            if d.get("view_count"): parts.append(f"V: {d['view_count']:,}")
            meta = "  |  ".join(parts)
            self.info_status.config(text="OK Ready to download", fg=SUCCESS)
        self.info_title.config(text=title[:72] + ("..." if len(title) > 72 else ""), fg=WHITE)
        self.info_meta.config(text=meta)
        self._dl_metadata = {"title": title, "artist": d.get("channel", ""),
                              "album": "", "genre": "", "year": "", "track": "", "comment": ""}
        self.meta_btn.pack(anchor="w", pady=(8, 0))

    def _on_thumb(self, photo):
        self._thumb_photo = photo
        self.thumb_canvas.delete("all")
        if photo:
            self.thumb_canvas.create_image(84, 48, image=photo, anchor="center")
        else:
            self.thumb_canvas.create_text(84, 48, text="NO THUMB", fill=TEXT_DIM,
                                          font=(FONT_MONO, 10))

    def _clear_preview(self, keep_url=False):
        if not keep_url:
            self._preview_requests.clear()
        self._pending_info = None
        self._thumb_photo  = None
        self.thumb_canvas.delete("all")
        self.thumb_canvas.create_text(84, 48, text="NO PREVIEW", fill=TEXT_DIM,
                                      font=(FONT_MONO, 10))
        self.info_title.config(text="// PASTE A URL TO PREVIEW //", fg=TEXT_MED)
        self.info_meta.config(text="")
        self.info_status.config(text="", fg=CYAN_DIM)
        self.meta_btn.pack_forget()

    def _open_metadata_editor(self):
        dialog = MetadataEditorDialog(self.root, prefill=self._dl_metadata)
        result = dialog.show()
        if result is not None:
            self._dl_metadata = result
            filled = [f"{k}: {v}" for k, v in result.items() if v]
            if filled:
                self._log(f"  Metadata staged: {', '.join(filled[:3])}"
                          + ("..." if len(filled) > 3 else ""), "magenta")
            self.meta_btn.config(text="[ METADATA SET OK ]",
                                 fg=SUCCESS, highlightbackground=SUCCESS)

    #  Options 
    def _build_options_section(self, parent):
        o, i = self._card(parent, BLUE, pad=12, title="> Output")
        o.pack(fill="x", pady=(0, 8))
        cols = tk.Frame(i, bg=CARD); cols.pack(fill="x")

        # Folder column
        left = tk.Frame(cols, bg=CARD); left.pack(side="left", fill="x", expand=True)
        self._lbl(left, "OUTPUT FOLDER", size=7, color=TEXT_MED).pack(anchor="w", pady=(0, 4))
        fr = tk.Frame(left, bg=CARD); fr.pack(fill="x")
        self.folder_var = tk.StringVar(value=self.cfg.get("output_folder", ""))
        self._entry(fr, self.folder_var).pack(side="left", fill="x", expand=True)
        self._btn(fr, "[ BRW ]", self._browse_folder, BLUE, 7).pack(side="left", padx=(6, 0))

        tk.Frame(cols, bg=ACCENT_LINE, width=1).pack(side="left", fill="y", padx=16)

        # Quality column
        right = tk.Frame(cols, bg=CARD); right.pack(side="left")
        self._lbl(right, "QUALITY", size=7, color=TEXT_MED).pack(anchor="w", pady=(0, 4))
        q_row = tk.Frame(right, bg=CARD); q_row.pack(fill="x")

        sty = ttk.Style(); sty.theme_use("clam")
        for name, accent, bg_c in [
            ("C.TCombobox", CYAN,    CYAN_DARK),
            ("O.TCombobox", ORANGE,  ORANGE_DIM),
            ("G.TCombobox", SUCCESS, SUCCESS_DIM),
        ]:
            sty.configure(name, fieldbackground=PANEL, background=CARD,
                foreground="#000000", bordercolor=CYAN_DIM, arrowcolor=accent,
                selectbackground=bg_c, selectforeground="#000000")

        self.quality_var = tk.StringVar(value=self.cfg.get("quality", "320"))
        self.audio_q_frame = tk.Frame(q_row, bg=CARD)
        ttk.Combobox(self.audio_q_frame, textvariable=self.quality_var,
            values=["128", "192", "256", "320"], state="readonly",
            width=7, style="C.TCombobox").pack(side="left")
        self.kbps_lbl = tk.Label(self.audio_q_frame, text=" kbps",
            fg=TEXT_DIM, bg=CARD, font=(FONT_MONO, 10))
        self.kbps_lbl.pack(side="left")
        self.audio_q_frame.pack(side="left")

        self.video_quality_var = tk.StringVar(value=self.cfg.get("video_quality", "best"))
        self.mp4_q_frame = tk.Frame(q_row, bg=CARD)
        ttk.Combobox(self.mp4_q_frame, textvariable=self.video_quality_var,
            values=["best", "2160", "1440", "1080", "720", "480", "360"], state="readonly",
            width=7, style="O.TCombobox").pack(side="left")
        tk.Label(self.mp4_q_frame, text=" res", fg=TEXT_DIM, bg=CARD,
                 font=(FONT_MONO, 10)).pack(side="left")

        self.playlist_var = tk.BooleanVar(value=False)
        pr = tk.Frame(right, bg=CARD); pr.pack(fill="x", pady=(10, 0))
        tk.Checkbutton(pr, text="  PLAYLIST MODE",
            variable=self.playlist_var, fg=CYAN, bg=CARD,
            activeforeground=MAGENTA, activebackground=CARD,
            selectcolor=PANEL, font=(FONT_MONO, 10, "bold"), cursor="hand2"
        ).pack(side="left")

    #  SponsorBlock 
    def _build_sb_section(self, parent):
        o, i = self._card(parent, SUCCESS, pad=10, title="> SponsorBlock")
        self.sb_outer = o
        o.pack(fill="x", pady=(0, 8))

        self._sb_collapsed = False

        hdr = tk.Frame(i, bg=CARD); hdr.pack(fill="x")
        self.sb_var = tk.BooleanVar(value=self.cfg.get("sponsorblock", False))
        tk.Checkbutton(hdr, text="  Skip sponsors & unwanted segments",
            variable=self.sb_var, onvalue=True, offvalue=False,
            fg=SUCCESS, bg=CARD,
            activeforeground=WHITE, activebackground=CARD,
            selectcolor=PANEL, font=(FONT_MONO, 13, "bold"), cursor="hand2",
            command=self._toggle_sb_cats
        ).pack(side="left")

        # Collapse toggle button
        self._sb_toggle_btn = tk.Button(hdr, text="v", command=self._toggle_sb_collapse,
            fg=SUCCESS, bg=CARD, activeforeground=BG, activebackground=SUCCESS,
            font=(FONT_MONO, 10, "bold"), relief="flat", bd=0,
            padx=6, pady=2, cursor="hand2")
        self._sb_toggle_btn.pack(side="right")

        self.sb_cats_frame = tk.Frame(i, bg=CARD)
        self.sb_cats_frame.pack(fill="x", pady=(8, 0))
        self.sb_cat_vars = {}
        saved_cats = set(self.cfg.get("sb_categories", DEFAULT_CATEGORIES))
        cats_display = [
            ("sponsor",        "$ Sponsor"),
            ("intro",          "> Intro"),
            ("outro",          "< Outro"),
            ("selfpromo",      "! Self-Promo"),
            ("interaction",    "+ Interaction"),
            ("music_offtopic", "~ Non-Music"),
            ("filler",         ". Filler"),
        ]
        row1 = tk.Frame(self.sb_cats_frame, bg=CARD); row1.pack(anchor="center", pady=(0, 2))
        row2 = tk.Frame(self.sb_cats_frame, bg=CARD); row2.pack(anchor="center", pady=(2, 0))
        for idx, (key, label) in enumerate(cats_display):
            var = tk.BooleanVar(value=(key in saved_cats))
            self.sb_cat_vars[key] = var
            target_row = row1 if idx < 4 else row2
            tk.Checkbutton(target_row, text=f"  {label}",
                variable=var, fg=SUCCESS, bg=CARD,
                activeforeground=WHITE, activebackground=CARD,
                selectcolor=PANEL, font=(FONT_MONO, 13, "bold"), cursor="hand2"
            ).pack(side="left", padx=8)
        self._toggle_sb_cats()

    def _toggle_sb_collapse(self):
        self._sb_collapsed = not self._sb_collapsed
        if self._sb_collapsed:
            self.sb_cats_frame.pack_forget()
            self._sb_toggle_btn.config(text=">")
        else:
            self.sb_cats_frame.pack(fill="x", pady=(8, 0))
            self._sb_toggle_btn.config(text="v")

    def _toggle_sb_cats(self):
        state = "normal" if self.sb_var.get() else "disabled"
        for w in self.sb_cats_frame.winfo_children():
            for ww in w.winfo_children():
                try: ww.config(state=state)
                except: pass

    #  Clip / Trim 
    def _build_clip_section(self, parent):
        o, i = self._card(parent, MAGENTA_DIM, pad=10, title="> Clip / Trim  (optional)")
        self.clip_outer = o
        o.pack(fill="x", pady=(0, 8))
        row = tk.Frame(i, bg=CARD); row.pack(fill="x")
        self._lbl(row, "START:", size=8, color=TEXT_MED).pack(side="left")
        self.clip_start_var = tk.StringVar()
        self._entry(row, self.clip_start_var, 10).pack(side="left", padx=(6, 16))
        self._lbl(row, "END:", size=8, color=TEXT_MED).pack(side="left")
        self.clip_end_var = tk.StringVar()
        self._entry(row, self.clip_end_var, 10).pack(side="left", padx=(6, 16))
        self._btn(row, "[ CLR ]",
            lambda: (self.clip_start_var.set(""), self.clip_end_var.set("")),
            MAGENTA_DIM, 7).pack(side="left")
        self._lbl(row, "MM:SS  or  HH:MM:SS", size=7, color=TEXT_DIM).pack(side="right")

    #  Progress 
    def _build_progress_section(self, parent):
        o, i = self._card(parent, CYAN, pad=12, title="> Status")
        o.pack(fill="x", pady=(0, 8))

        # Status line
        status_row = tk.Frame(i, bg=CARD); status_row.pack(fill="x", pady=(0, 8))
        self.status_track = tk.Label(status_row, text="STANDBY",
            fg=TEXT_MED, bg=CARD, font=(FONT_MONO, 10))
        self.status_track.pack(side="right")

        # Progress bar  segmented style
        self.prog_canvas = tk.Canvas(i, height=28, bg=PANEL,
            highlightthickness=1, highlightbackground=CYAN_DIM)
        self.prog_canvas.pack(fill="x", pady=(0, 8))
        self._draw_progress(0)

        # Stats row
        stats = tk.Frame(i, bg=CARD); stats.pack(fill="x", pady=(0, 12))
        self.pct_lbl   = tk.Label(stats, text="0%",      fg=CYAN,    bg=CARD, font=(FONT_MONO, 13, "bold"))
        self.speed_lbl = tk.Label(stats, text=" KB/s",  fg=BLUE,    bg=CARD, font=(FONT_MONO, 10))
        self.eta_lbl   = tk.Label(stats, text="ETA: ",  fg=TEXT_MED, bg=CARD, font=(FONT_MONO, 10))
        self.pl_lbl    = tk.Label(stats, text="",         fg=MAGENTA, bg=CARD, font=(FONT_MONO, 10))
        self.pct_lbl.pack(side="left")
        self.speed_lbl.pack(side="left", padx=(14, 0))
        self.eta_lbl.pack(side="left", padx=(14, 0))
        self.pl_lbl.pack(side="right")

        # Action buttons
        btn_row = tk.Frame(i, bg=CARD); btn_row.pack(fill="x")

        self.dl_btn_outer, self.dl_btn_inner = self._bigbtn(

            btn_row, "  >>  DOWNLOAD MP3  ", self._start_download, CYAN, 22, 2)
        self.dl_btn_outer.pack(side="left")
        # Aliases for compatibility with _set_mode / effects
        self.dl_btn = self.dl_btn_inner

        self.cancel_btn = self._btn(btn_row, "[ X CANCEL ]",
            self._cancel_download, ERROR, 12, 2, CARD)
        self.cancel_btn.pack(side="left", padx=(10, 0))
        self.cancel_btn.config(state="disabled")

        self._btn(btn_row, "[ OPEN FOLDER ]",
            self._open_folder, SUCCESS, 14, 2, CARD).pack(side="right")

    def _draw_progress(self, pct, color=CYAN):
        self.prog_canvas.delete("bar")
        w = self.prog_canvas.winfo_width() or 800
        filled = int(w * pct / 100)
        seg_w, gap = 10, 3
        for x in range(0, w, seg_w + gap):
            fill = CYAN_DARK if x >= filled else color
            self.prog_canvas.create_rectangle(
                x + 1, 4, min(x + seg_w, w) - 1, 24,
                fill=fill, outline="", tags="bar")
        if filled > 8:
            # Bright leading edge
            self.prog_canvas.create_rectangle(
                filled - 4, 2, filled + 2, 26,
                fill=WHITE, outline="", tags="bar")

    #  Log 
    def _build_log_section(self, parent):
        o, i = self._card(parent, CYAN_DIM, pad=10, title="> System Log")
        o.pack(fill="both", expand=True, pady=(0, 8))

        hdr = tk.Frame(i, bg=CARD); hdr.pack(fill="x", pady=(0, 6))
        self._btn(hdr, "[ CLR ]", self._clear_log, TEXT_DIM, 6).pack(side="right")

        lf = tk.Frame(i, bg=PANEL, highlightthickness=1,
                      highlightbackground=ACCENT_LINE)
        lf.pack(fill="both", expand=True)
        self.log_text = tk.Text(lf, font=(FONT_MONO, 10), fg=CYAN_GLOW, bg=PANEL,
            insertbackground=CYAN, relief="flat", bd=6, wrap="word",
            state="disabled", height=7)
        sb2 = tk.Scrollbar(lf, orient="vertical", command=self.log_text.yview)
        sb2.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=sb2.set)
        self.log_text.pack(fill="both", expand=True)
        for tag, fg in [("success", SUCCESS), ("error", ERROR), ("warn", WARNING),
                        ("info", CYAN_GLOW), ("dim", TEXT_DIM),
                        ("magenta", MAGENTA), ("orange", ORANGE)]:
            self.log_text.tag_configure(tag, foreground=fg)
        self._log(f"SYSTEM BOOT... SOFTCURSE v{APP_VERSION}", "magenta")
        self._log("Initialising...", "dim")

    # 
    # PLAYER TAB
    # 
    def _build_tab_player(self):
        self.tab_player = tk.Frame(self.main_frame, bg=BG)
        if not check_pygame():
            o, i = self._card(self.tab_player, MAGENTA_DIM, title="> Player")
            o.pack(fill="x", pady=(0, 8))
            self._lbl(i, "[!] pygame not installed", size=11, color=WARNING, bold=True).pack(pady=(4, 4))
            self._lbl(i, "pygame is required for audio playback.", color=TEXT_MED).pack()
            self._btn(i, "[ INSTALL PYGAME ]",
                lambda: threading.Thread(target=lambda: install_pygame(
                    log_cb=self._log), daemon=True).start(),
                ORANGE, 22, 2, CARD
            ).pack(pady=(10, 4))
            self._lbl(i, "After installing, restart the application.", size=7, color=TEXT_DIM).pack()

        self.player_panel = PlayerPanel(self.tab_player)
        self.player_panel.pack(fill="both", expand=True)

    # 
    # HISTORY TAB
    # 
    def _build_tab_history(self):
        self.tab_hist = tk.Frame(self.main_frame, bg=BG)
        o, i = self._card(self.tab_hist, BLUE, title="> Download History")
        o.pack(fill="both", expand=True)

        hdr = tk.Frame(i, bg=CARD); hdr.pack(fill="x", pady=(0, 8))
        self._btn(hdr, "[ CLEAR ALL ]", self._clear_history, ERROR, 12).pack(side="right")
        self._btn(hdr, "[~ REFRESH ]", self._refresh_history, CYAN_DIM, 12).pack(side="right", padx=(0, 6))
        self.history_filter_var = tk.StringVar()
        history_filter = self._entry(hdr, self.history_filter_var, width=26)
        history_filter.pack(side="left", fill="x", expand=True, padx=(0, 8))
        history_filter.insert(0, "")
        self._lbl(hdr, "Search:", size=8, color=TEXT_MED).pack(side="left", before=history_filter)
        self.history_filter_var.trace_add("write", lambda *_: self._refresh_history())

        sty = ttk.Style()
        sty.configure("H.Treeview", background=PANEL, foreground=CYAN,
            fieldbackground=PANEL, rowheight=24, font=(FONT_MONO, 10))
        sty.configure("H.Treeview.Heading", background=CARD,
            foreground=BLUE, font=(FONT_MONO, 10, "bold"))
        sty.map("H.Treeview", background=[("selected", CYAN_DARK)],
                foreground=[("selected", CYAN)])

        tf = tk.Frame(i, bg=PANEL); tf.pack(fill="both", expand=True)
        cols = ("date", "title", "mode", "status", "folder")
        self.hist_tree = ttk.Treeview(tf, columns=cols, show="headings",
            style="H.Treeview", selectmode="browse")
        for col, w, stretch in [("date", 120, False), ("title", 260, True),
                                 ("mode", 60, False), ("status", 70, False), ("folder", 180, True)]:
            self.hist_tree.heading(col, text=col.upper())
            self.hist_tree.column(col, width=w, stretch=stretch)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.hist_tree.yview)
        vsb.pack(side="right", fill="y")
        self.hist_tree.config(yscrollcommand=vsb.set)
        self.hist_tree.pack(fill="both", expand=True)
        self.hist_tree.tag_configure("success", foreground=SUCCESS)
        self.hist_tree.tag_configure("failed",  foreground=ERROR)

        act = tk.Frame(i, bg=CARD); act.pack(fill="x", pady=(10, 0))
        self._btn(act, "[  RE-DOWNLOAD ]", self._retry_selected,  CYAN,    18).pack(side="left")
        self._btn(act, "[  PLAY FOLDER ]", self._play_from_hist,  MAGENTA, 16).pack(side="left", padx=(8, 0))
        self._btn(act, "[ OPEN FOLDER ]",   self._open_hist_folder, SUCCESS, 15).pack(side="left", padx=(8, 0))
        self._btn(act, "[ DELETE ]",         self._delete_hist,     ERROR,   10).pack(side="left", padx=(8, 0))
        self.hist_entry_ids = []
        self._history_view_entries = []

    def _refresh_history(self):
        for r in self.hist_tree.get_children(): self.hist_tree.delete(r)
        self.hist_entry_ids = []
        query = self.history_filter_var.get().strip().lower()
        entries = self._history.load_history()
        entries = hist.filter_history(entries, query)
        self._history_view_entries = entries
        for e in entries:
            tag = "success" if e.get("status") == "success" else "failed"
            m   = {"mp3": "MP3", "flac": "FLAC", "wav": "WAV",
                   "mp4": "MP4"}.get(e.get("mode", ""), e.get("mode", ""))
            t   = e.get("title", "")
            if e.get("count", 1) > 1: t = f"[{e['count']}] {t}"
            self.hist_tree.insert("", "end", values=(
                e.get("timestamp", ""), t[:80], m,
                e.get("status", "").upper(), e.get("folder", "")
            ), tags=(tag,))
            self.hist_entry_ids.append(e.get("id"))

    def _get_hist_entry(self):
        sel = self.hist_tree.selection()
        if not sel:
            messagebox.showinfo("History", "Select an entry first.")
            return None, None
        idx     = self.hist_tree.index(sel[0])
        entries = self._history_view_entries
        if idx >= len(entries): return None, None
        return entries[idx], self.hist_entry_ids[idx] if idx < len(self.hist_entry_ids) else None

    def _retry_selected(self):
        entry, _ = self._get_hist_entry()
        if not entry: return
        self.url_var.set(entry.get("url", ""))
        mode = entry.get("mode", "mp3")
        self._set_mode(mode)
        self._show_tab(TAB_DL)
        self._trigger_fetch()
        self._log(f" Re-queued: {entry.get('title', '')[:50]}", "magenta")

    def _play_from_hist(self):
        entry, _ = self._get_hist_entry()
        if not entry: return
        folder = entry.get("folder", "")
        if os.path.exists(folder):
            self.player_panel.load_folder(folder)
            self._show_tab(TAB_PLAYER)
        else:
            messagebox.showwarning("Not Found", f"Folder not found:\n{folder}")

    def _open_hist_folder(self):
        entry, _ = self._get_hist_entry()
        if not entry: return
        folder = entry.get("folder", "")
        if os.path.exists(folder): os.startfile(folder)
        else: messagebox.showwarning("Not Found", f"Folder not found:\n{folder}")

    def _delete_hist(self):
        entry, eid = self._get_hist_entry()
        if not entry or eid is None: return
        self._history.delete_entry(eid); self._refresh_history()

    def _clear_history(self):
        if messagebox.askyesno("Clear History", "Delete all history?"):
            self._history.clear_history(); self._refresh_history()

    # 
    # SETTINGS TAB
    # 
    def _build_tab_settings(self):
        self.tab_settings = tk.Frame(self.main_frame, bg=BG)
        c  = tk.Canvas(self.tab_settings, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self.tab_settings, orient="vertical", command=c.yview)
        self._settings_frame = tk.Frame(c, bg=BG)
        self._settings_frame.bind("<Configure>",
            lambda e: c.configure(scrollregion=c.bbox("all")))
        c.create_window((0, 0), window=self._settings_frame, anchor="nw")
        c.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); c.pack(side="left", fill="both", expand=True)
        self._build_settings_content(self._settings_frame)

    def _build_settings_content(self, parent):
        # Runtime readiness
        od, id_ = self._card(parent, SUCCESS, 12, title="> System Readiness")
        od.pack(fill="x", pady=(0, 10))
        self.readiness_label = self._lbl(
            id_, "Run diagnostics to verify required and optional components.",
            size=8, color=TEXT_MED,
        )
        self.readiness_label.pack(anchor="w", pady=(0, 8))
        self._btn(id_, "[ RUN DIAGNOSTICS ]", self._run_dependency_diagnostics,
                  SUCCESS, 20).pack(anchor="w")

        # Folders
        o, i = self._card(parent, CYAN, 12, title="> Default Folders")
        o.pack(fill="x", pady=(0, 10))
        self._setting_folder_vars = {}
        for label, key, default in [
            ("MP3 / FLAC / WAV Output", "output_folder",
             os.path.join(os.path.expanduser("~"), "Music")),
            ("MP4 Output", "mp4_output_folder",
             os.path.join(os.path.expanduser("~"), "Videos")),
        ]:
            row = tk.Frame(i, bg=CARD); row.pack(fill="x", pady=5)
            lbl = self._lbl(row, label, size=8, color=TEXT_MED)
            lbl.config(width=24); lbl.pack(side="left", anchor="w")
            var = tk.StringVar(value=self.cfg.get(key, default))
            self._setting_folder_vars[key] = var
            self._entry(row, var).pack(side="left", fill="x", expand=True)
            self._btn(row, "[ BRW ]",
                lambda k=key, v=var: self._browse_setting_folder(k, v),
                BLUE, 6).pack(side="left", padx=(6, 0))

        # Filename template
        o2, i2 = self._card(parent, MAGENTA_DIM, 12, title="> Filename Template")
        o2.pack(fill="x", pady=(0, 10))
        self._lbl(i2, "%(title)s  %(uploader)s  %(upload_date)s  %(id)s  %(track)s",
            size=7, color=TEXT_DIM).pack(anchor="w", pady=(0, 8))
        self.tmpl_var = tk.StringVar(value=self.cfg.get("filename_template", "%(title)s"))
        self._entry(i2, self.tmpl_var).pack(fill="x")
        pr = tk.Frame(i2, bg=CARD); pr.pack(fill="x", pady=(8, 0))
        self._lbl(pr, "Presets:", size=7, color=TEXT_DIM).pack(side="left")
        for lbl2, tmpl in [
            ("Title only",   "%(title)s"),
            ("Artist-Title", "%(uploader)s - %(title)s"),
            ("Date-Title",   "%(upload_date)s - %(title)s"),
            ("ID-Title",     "%(id)s - %(title)s"),
        ]:
            self._btn(pr, lbl2, lambda t=tmpl: self.tmpl_var.set(t),
                CYAN_DIM, len(lbl2) + 2, 1, CARD, 7).pack(side="left", padx=(6, 0))

        # Visual effects
        o3, i3 = self._card(parent, ORANGE_DIM, 12, title="> Visual Effects")
        o3.pack(fill="x", pady=(0, 10))
        self.crt_var = tk.BooleanVar(value=self.cfg.get("crt_effects", True))
        tk.Checkbutton(i3, text="  CRT Scanline Effect", variable=self.crt_var,
            fg=ORANGE, bg=CARD, activeforeground=WHITE, activebackground=CARD,
            selectcolor=PANEL, font=(FONT_MONO, 13, "bold"), cursor="hand2").pack(anchor="w")
        self.reduced_motion_var = tk.BooleanVar(value=self.cfg.get("reduced_motion", False))
        tk.Checkbutton(i3, text="  Reduced motion (disable glitch, pulse, and animated scanlines)",
            variable=self.reduced_motion_var,
            fg=WHITE, bg=CARD, activeforeground=WHITE, activebackground=CARD,
            selectcolor=PANEL, font=(FONT_MONO, 10), cursor="hand2").pack(
                anchor="w", pady=(6, 0))

        # Tray & notifications
        o4, i4 = self._card(parent, BLUE, 12, title="> System Tray & Notifications")
        o4.pack(fill="x", pady=(0, 10))
        self.tray_var   = tk.BooleanVar(value=self.cfg.get("minimize_to_tray", False))
        self.notify_var = tk.BooleanVar(value=self.cfg.get("notify_on_complete", True))
        for text, var in [
            ("Minimize to tray on close",        self.tray_var),
            ("Desktop notification on complete", self.notify_var),
        ]:
            tk.Checkbutton(i4, text=f"  {text}", variable=var,
                fg=CYAN, bg=CARD, activeforeground=WHITE, activebackground=CARD,
                selectcolor=PANEL, font=(FONT_MONO, 11), cursor="hand2"
            ).pack(anchor="w", pady=3)
        deps = check_tray_deps()
        tk.Label(i4,
            text=f"  pystray: {'OK' if deps['pystray'] else 'X'}   "
                 f"plyer: {'OK' if deps['plyer'] else 'X'}",
            fg=TEXT_DIM, bg=CARD, font=(FONT_MONO, 11)).pack(anchor="w", pady=(4, 0))
        if (not deps["pystray"] or not deps["plyer"]) and not getattr(sys, "frozen", False):
            self._btn(i4, "[ INSTALL TRAY DEPS ]",
                lambda: threading.Thread(target=lambda: install_tray_deps(
                    log_callback=self._log), daemon=True).start(),
                BLUE, 22, 1, CARD, 8).pack(anchor="w", pady=(8, 0))

        # Optional deps
        o5, i5 = self._card(parent, CYAN_DIM, 12, title="> Optional Dependencies")
        o5.pack(fill="x", pady=(0, 10))
        for label, check_fn, install_fn, pkg in [
            ("Pillow (thumbnail preview)", check_pil,     install_pil,     "Pillow"),
            ("mutagen (metadata writing)", check_mutagen, install_mutagen, "mutagen"),
            ("pygame (mini player)",       check_pygame,  install_pygame,  "pygame"),
        ]:
            row2 = tk.Frame(i5, bg=CARD); row2.pack(fill="x", pady=4)
            ok = check_fn()
            tk.Label(row2, text=f"{'[OK]' if ok else '[X]'}  {label}",
                fg=SUCCESS if ok else WARNING, bg=CARD,
                font=(FONT_MONO, 10)).pack(side="left")
            if not ok and not getattr(sys, "frozen", False):
                self._btn(row2, "[ INSTALL ]",
                    lambda f=install_fn: threading.Thread(
                        target=lambda: f(self._log), daemon=True).start(),
                    CYAN_DIM, 12, 1, CARD, 7).pack(side="right")

        # yt-dlp updater
        o6, i6 = self._card(parent, SUCCESS, 12, title="> yt-dlp Updater")
        o6.pack(fill="x", pady=(0, 10))
        self._lbl(i6, "Keep yt-dlp current to fix YouTube download issues.",
            size=7, color=TEXT_DIM).pack(anchor="w", pady=(0, 8))
        if getattr(sys, "frozen", False):
            self._lbl(i6, "Packaged builds update with the complete application installer.",
                      size=8, color=WARNING).pack(anchor="w")
        else:
            self._btn(i6, "[ >> UPDATE yt-dlp NOW ]",
                lambda: threading.Thread(target=lambda: self._run_ytdlp_update(),
                    daemon=True).start(),
                SUCCESS, 24, 2, CARD).pack(anchor="w")
        self._btn(i6, "[ CHECK FOR APP UPDATE ]", self._check_for_app_update,
                  BLUE, 26, 1, CARD).pack(anchor="w", pady=(8, 0))

        # Save button
        sr = tk.Frame(parent, bg=BG); sr.pack(fill="x", pady=(4, 14))
        outer_s, inner_s = self._bigbtn(sr, "  >>  SAVE SETTINGS  ",
                                         self._save_settings, CYAN, 22, 2)
        outer_s.pack(anchor="center")

    def _run_ytdlp_update(self):
        from downloader import update_ytdlp
        update_ytdlp(log_callback=self._log)

    def _check_for_app_update(self):
        self._log(" Checking GitHub Releases for an application update...", "info")
        def worker():
            try:
                info = check_for_update(APP_VERSION)
                self.root.after(0, lambda: self._show_update_result(info))
            except Exception as error:
                message = str(error)
                self.root.after(0, lambda: messagebox.showwarning(
                    "Update Check", f"Could not check for updates:\n{message}"))
        threading.Thread(target=worker, daemon=True).start()

    def _show_update_result(self, info):
        if info.available:
            open_release = messagebox.askyesno(
                "Update Available",
                f"Softcurse {info.latest_version} is available.\n"
                f"You have {info.current_version}.\n\nOpen the release page?",
            )
            if open_release:
                webbrowser.open(info.release_url)
        else:
            messagebox.showinfo("Update Check", f"Softcurse {APP_VERSION} is up to date.")

    def _run_dependency_diagnostics(self):
        self.readiness_label.config(text="Checking components...", fg=WARNING)
        threading.Thread(target=self._collect_dependency_diagnostics, daemon=True).start()

    def _collect_dependency_diagnostics(self, first_run=False):
        statuses = collect_dependency_status()
        self.root.after(0, lambda: self._show_dependency_diagnostics(statuses, first_run))

    def _show_dependency_diagnostics(self, statuses, first_run=False):
        ready = required_ready(statuses)
        required_missing = [status.name for status in statuses
                            if status.required and not status.available]
        optional_missing = [status.name for status in statuses
                            if not status.required and not status.available]
        summary = "READY" if ready else f"MISSING: {', '.join(required_missing)}"
        self.readiness_label.config(text=summary, fg=SUCCESS if ready else ERROR)
        for status in statuses:
            marker = "OK" if status.available else "MISSING"
            level = "success" if status.available else ("error" if status.required else "warn")
            self._log(f" [{marker}] {status.name}: {status.purpose}", level)
        if first_run or not ready:
            message = "Required components are ready."
            if required_missing:
                message = "Required components missing: " + ", ".join(required_missing)
            if optional_missing:
                message += "\n\nOptional components missing: " + ", ".join(optional_missing)
            if getattr(sys, "frozen", False) and required_missing:
                message += "\n\nRepair or reinstall the packaged application."
            elif required_missing:
                message += "\n\nInstall development dependencies, then run diagnostics again."
            messagebox.showinfo("Softcurse System Readiness", message)
        if first_run:
            self.cfg["first_run_complete"] = True
            self._config_saver(self.cfg)

    def _browse_setting_folder(self, key, var):
        f = filedialog.askdirectory(title=f"Select {key}", initialdir=var.get())
        if f: var.set(f)

    def _save_settings(self):
        for key, var in self._setting_folder_vars.items():
            self.cfg[key] = var.get()
        self.cfg["filename_template"]  = self.tmpl_var.get() or "%(title)s"
        self.cfg["crt_effects"]        = self.crt_var.get()
        self.cfg["reduced_motion"]     = self.reduced_motion_var.get()
        self.cfg["minimize_to_tray"]   = self.tray_var.get()
        self.cfg["notify_on_complete"] = self.notify_var.get()
        self._config_saver(self.cfg)
        self._apply_effect_preferences()
        self._log(" Settings saved!", "success")
        messagebox.showinfo("Softcurse", "Settings saved!")

    #  Status bar 
    def _build_status_bar(self):
        bar = tk.Frame(self.main_frame, bg=CARD, height=26)
        bar.pack(fill="x", padx=20, pady=(4, 10))
        bar.pack_propagate(False)
        tk.Frame(bar, bg=CYAN, width=3).pack(side="left", fill="y")
        self.status_bar = tk.Label(bar,
            text="// SOFTCURSE SYSTEMS ONLINE //",
            fg=TEXT_MED, bg=CARD, font=(FONT_MONO, 11), anchor="w")
        self.status_bar.pack(side="left", padx=8, fill="both")
        # Version tag
        tk.Label(bar, text="SOFTCURSE SYSTEMS", fg=TEXT_DIM, bg=CARD,
                 font=(FONT_MONO, 11)).pack(side="right", padx=10)

    # 
    # EFFECTS
    # 
    def _start_effects(self):
        if self.cfg.get("reduced_motion", False):
            return
        self._glitch_loop(initial=True)
        self._pulse_loop()
        if self.cfg.get("crt_effects", True):
            self._crt_loop()

    def _apply_effect_preferences(self):
        reduced = self.cfg.get("reduced_motion", False)
        if reduced or not self.cfg.get("crt_effects", True):
            self.crt_canvas.delete("scanline")
            self._scanline_ids = []
        if reduced:
            for attr in ("_glitch_after", "_pulse_after", "_crt_after"):
                after_id = getattr(self, attr, None)
                if after_id:
                    try:
                        self.root.after_cancel(after_id)
                    except tk.TclError:
                        pass
                    setattr(self, attr, None)
            self.dl_btn_outer.config(bg={
                "mp3": CYAN, "flac": SUCCESS, "wav": BLUE, "mp4": ORANGE,
            }.get(self._mode.get(), CYAN))
        elif not any((self._glitch_after, self._pulse_after, self._crt_after)):
            self._start_effects()

    def _glitch_loop(self, initial=False):
        if self.cfg.get("reduced_motion", False):
            self._glitch_after = None
            return
        def glitch():
            chars = "█▓▒░╬╫╪┼┤├╥╨╞╡◈◊▲▼◆●○■□"
            orig  = "[ MEDIA DOWNLOADER // SOFTCURSE ]"
            def flicker(n=0):
                w = self.title_canvas.winfo_width()
                cx = (w // 2) if w > 10 else 420
                if n >= 4:
                    self.title_canvas.itemconfig(self.title_id, text=orig, fill=CYAN)
                    self.title_canvas.itemconfig(self.title_shadow, text=orig, fill=MAGENTA_DIM)
                    self.title_canvas.coords(self.title_shadow, cx + 2, 44)
                    self.title_canvas.coords(self.title_id, cx, 42)
                    return
                g = "".join(random.choice(chars) if random.random() < 0.18 else c for c in orig)
                self.title_canvas.itemconfig(self.title_id, text=g,
                    fill=MAGENTA if n % 2 == 0 else CYAN)
                self.title_canvas.coords(self.title_shadow, cx + random.randint(-4, 4), 44)
                self.title_canvas.coords(self.title_id,     cx + random.randint(-2, 2), 42)
                self.root.after(55, lambda: flicker(n + 1))
            flicker()
        # Start visibly, then keep the effect alive often enough to feel intentional.
        iv = 650 if initial else random.randint(2500, 6500)
        self._glitch_after = self.root.after(iv, lambda: (glitch(), self._glitch_loop()))

    def _build_crt_scanlines(self):
        """Fix #2: Create scanline canvas items ONCE, then reuse via coords()."""
        self.crt_canvas.delete("scanline")
        self._scanline_ids = []
        h = self.root.winfo_height() or 840
        w = self.root.winfo_width()  or 860
        scanline_color = "#091018"
        for y in range(0, h, 4):
            lid = self.crt_canvas.create_line(0, y, w, y,
                fill=scanline_color, width=1, tags="scanline", stipple="gray50")
            self._scanline_ids.append(lid)
        # Persistent glitch line (hidden by default)
        self._glitch_line_id = self.crt_canvas.create_line(
            0, 0, w, 0, fill=MAGENTA, width=1, tags="scanline", state="hidden")
        self.crt_canvas.lower("scanline")

    def _crt_loop(self):
        if self.cfg.get("reduced_motion", False) or not self.cfg.get("crt_effects", True):
            self._crt_after = None
            return
        # Build scanlines if not yet created
        if not self._scanline_ids:
            self._build_crt_scanlines()
            self._crt_after = self.root.after(80, self._crt_loop)
            return
        # Update positions only (no create/delete)
        off = int(time.time() * 30) % 6
        w   = self.root.winfo_width() or 860
        for i, lid in enumerate(self._scanline_ids):
            y = i * 4 + off
            self.crt_canvas.coords(lid, 0, y, w, y)
        # Rare magenta glitch line  reuse persistent item
        if random.random() < 0.04 and self._glitch_line_id:
            h = self.root.winfo_height() or 840
            gy = random.randint(0, h)
            self.crt_canvas.coords(self._glitch_line_id, 0, gy, w, gy)
            self.crt_canvas.itemconfig(self._glitch_line_id, state="normal")
            self.root.after(160, lambda: self.crt_canvas.itemconfig(
                self._glitch_line_id, state="hidden"))
        self._crt_after = self.root.after(80, self._crt_loop)

    def _pulse_loop(self):
        if self.cfg.get("reduced_motion", False):
            self._pulse_after = None
            return
        mode = self._mode.get()
        palettes = {
            "mp3":  [CYAN, CYAN_GLOW, CYAN_DIM, CYAN_DARK, CYAN_DIM, CYAN_GLOW],
            "flac": [SUCCESS, "#63ffc0", "#2bcf86", SUCCESS_DIM, "#2bcf86", "#63ffc0"],
            "wav":  [BLUE, "#66a8ff", BLUE_DIM, "#24416a", BLUE_DIM, "#66a8ff"],
            "mp4":  [ORANGE, "#ffaaaa", ORANGE_DIM, "#ffaaaa"],
        }
        palette = palettes.get(mode, palettes["mp3"])
        idx = [0]
        def pulse():
            # Fix #5: Skip pulse when download tab is not active
            if self._active_tab != TAB_DL:
                self._pulse_after = self.root.after(500, pulse)
                return
            try:
                c = palette[idx[0] % len(palette)]
                self.dl_btn_outer.config(bg=c)
            except: pass
            idx[0] += 1
            self._pulse_after = self.root.after(160, pulse)
        pulse()

    # 
    # DEPS
    # 
    def _check_deps_async(self):
        def check():
            statuses = collect_dependency_status()
            for status in statuses:
                marker = "ONLINE" if status.available else "MISSING"
                level = "success" if status.available else ("error" if status.required else "dim")
                self._log(f" {status.name}: {marker}", level)
            self._log("" * 46, "dim")
            ready = required_ready(statuses)
            self._log("READY  Softcurse // All systems nominal" if ready
                      else "ACTION REQUIRED // Open Settings > System Readiness",
                      "info" if ready else "error")
            self._update_status("READY" if ready else "DEPENDENCY ERROR")
            if not self.cfg.get("first_run_complete", False):
                self.root.after(0, lambda: self._show_dependency_diagnostics(statuses, True))
        threading.Thread(target=check, daemon=True).start()

    # 
    # TRAY
    # 
    def _maybe_start_tray(self):
        from tray import TRAY_AVAILABLE
        if TRAY_AVAILABLE:
            self._tray = TrayManager(
                on_show=lambda: self.root.after(0, self._restore_window),
                on_quit=lambda: self.root.after(0, self._force_quit))
            self._tray.start()

    def _restore_window(self):
        self.root.deiconify(); self.root.lift()

    def _force_quit(self):
        if self._tray: self._tray.stop()
        self.root.destroy()

    def _on_close(self):
        if self.cfg.get("minimize_to_tray", False) and self._tray:
            self.root.withdraw()
        else:
            self._force_quit()

    # 
    # ACTIONS
    # 
    def _paste_url(self):
        try:
            clipboard = self.root.clipboard_get().strip()
            urls = [line.strip() for line in clipboard.splitlines() if line.strip()]
            if len(urls) > 1:
                added = self._download_queue.add_urls(urls)
                self._refresh_queue()
                if added:
                    self.url_var.set(added[0].url)
                    self._log(f" Added {len(added)} URL(s) to the queue", "success")
            else:
                self.url_var.set(clipboard)
                self.root.after(200, self._trigger_fetch)
        except tk.TclError:
            pass

    def _browse_folder(self):
        f = filedialog.askdirectory(title="Select Output Folder",
                                    initialdir=self.folder_var.get())
        if f:
            self.folder_var.set(f)
            key = "mp4_output_folder" if self._mode.get() == "mp4" else "output_folder"
            self.cfg[key] = f; self._config_saver(self.cfg)

    def _open_folder(self):
        f = self.folder_var.get()
        if os.path.exists(f): os.startfile(f)
        else: messagebox.showwarning("Not Found", f"Folder not found:\n{f}")

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def _start_download(self, queued_url=None):
        url = (queued_url or self.url_var.get()).strip()
        if not url or not url.startswith("http"):
            self._log(" Invalid URL!", "error")
            self._fail_active_queue_before_start("Invalid URL")
            return
        folder = self.folder_var.get().strip()
        if not folder:
            self._log(" No output folder!", "error")
            self._fail_active_queue_before_start("No output folder")
            return

        mode    = self._mode.get()
        quality = self.quality_var.get()
        vq      = self.video_quality_var.get()
        pl      = self.playlist_var.get()
        tmpl    = self.cfg.get("filename_template", "%(title)s")
        cs      = self.clip_start_var.get().strip()
        ce      = self.clip_end_var.get().strip()
        # Preview metadata belongs only to the URL currently displayed. Queued
        # URLs fetch their own title through yt-dlp and must not inherit it.
        meta = {} if queued_url else (self._dl_metadata if self._dl_metadata else {})
        sb_cats = None
        if self.sb_var.get():
            sb_cats = [k for k, v in self.sb_cat_vars.items() if v.get()]
            if not sb_cats: sb_cats = DEFAULT_CATEGORIES
            self._log(f"  SponsorBlock: {', '.join(sb_cats)}", "orange")

        self._downloading = True
        self.dl_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self._draw_progress(0)
        self.pct_lbl.config(text="0%", fg=CYAN)
        self.speed_lbl.config(text=" KB/s")
        self.eta_lbl.config(text="ETA: ")
        self.pl_lbl.config(text="")
        self.status_track.config(text="CONNECTING...", fg=BLUE)

        self._dl_url = url; self._dl_mode = mode; self._dl_folder = folder
        ext = mode.upper()
        self._log("" * 46, "dim")
        self._log(f" {url[:65]}{'...' if len(url) > 65 else ''}", "info")
        self._log(f" Mode: {ext}  |  Folder: {folder}", "dim")
        if cs or ce: self._log(f"  Clip: {cs or 'start'}  {ce or 'end'}", "magenta")
        if meta and any(meta.values()):
            self._log(f"  Metadata: "
                      f"{', '.join(f'{k}={v}' for k,v in meta.items() if v)[:60]}", "magenta")
        self._log(f"INITIATING {ext} DOWNLOAD...", "magenta")
        self._save_cfg_quick()

        try:
            self.dl.download(
                DownloadRequest(
                    url=url,
                    output_folder=folder,
                    mode=mode,
                    quality=quality,
                    video_quality=vq,
                    is_playlist=pl,
                    filename_template=tmpl,
                    clip_start=cs,
                    clip_end=ce,
                    sponsorblock_cats=tuple(sb_cats) if sb_cats else None,
                    metadata=meta,
                ),
                on_progress=self._on_progress,
                on_log=self._on_dl_log,
                on_complete=self._on_complete,
                on_error=self._on_error,
                on_cancel=self._on_cancelled,
            )
        except RuntimeError as error:
            self._on_error(str(error))

    def _fail_active_queue_before_start(self, detail):
        if self._active_queue_id is None:
            return
        self._download_queue.finish(self._active_queue_id, QueueStatus.FAILED, detail)
        self._active_queue_id = None
        self._refresh_queue()
        self.root.after(0, self._run_next_queue)

    def _cancel_download(self):
        self.dl.cancel()
        self._log(" Cancelling...", "warn")
        self.cancel_btn.config(state="disabled")
        self.status_track.config(text="CANCELLING...", fg=WARNING)

    def _on_cancelled(self):
        def update():
            self._draw_progress(0)
            self.status_track.config(text="CANCELLED", fg=WARNING)
            self._reset_ui()
            self._update_status("CANCELLED")
            if self._active_queue_id is not None:
                self._download_queue.finish(
                    self._active_queue_id, QueueStatus.CANCELLED, "Cancelled by user"
                )
                self._active_queue_id = None
                self._refresh_queue()
            if self._tray:
                self._tray.update_tooltip("Download Cancelled")
        self.root.after(0, update)

    def _on_progress(self, update: ProgressUpdate):
        self.root.after(0, lambda: self._update_progress(update))

    def _update_progress(self, data: ProgressUpdate):
        status = data.status
        mode = data.mode or self._mode.get()
        colors = {"mp3": CYAN, "flac": SUCCESS, "wav": BLUE, "mp4": ORANGE}
        bc = colors.get(mode, CYAN)
        if status == DownloadStatus.DOWNLOADING:
            pct = data.percent
            self._draw_progress(pct, bc)
            self.pct_lbl.config(text=f"{pct:.1f}%", fg=bc)
            self.speed_lbl.config(text=data.speed)
            self.eta_lbl.config(text=f"ETA: {data.eta}")
            fn = data.filename
            self.status_track.config(
                text=f" {fn[:48]}{'...' if len(fn) > 48 else ''}", fg=BLUE)
            if self._tray: self._tray.update_tooltip(f"{pct:.0f}% {fn[:30]}")
        elif status == DownloadStatus.CONVERTING:
            cc = MAGENTA if mode == "mp3" else bc
            self._draw_progress(100, cc); self.pct_lbl.config(text="100%", fg=cc)
            labels = {"mp3": " CONVERTINGMP3", "flac": " CONVERTINGFLAC",
                      "wav": " CONVERTINGWAV", "mp4": " MERGING VIDEO"}
            self.status_track.config(text=labels.get(mode, " PROCESSING"), fg=cc)
        elif status == DownloadStatus.PLAYLIST:
            cur = data.current; total = data.total
            pct = (cur - 1) / total * 100 if total > 0 else 0
            self._draw_progress(pct, BLUE)
            self.pl_lbl.config(text=f"[{cur}/{total}]", fg=MAGENTA)
            t = data.title
            self.status_track.config(text=f" {t[:48]}", fg=BLUE)

    def _on_dl_log(self, msg):
        self.root.after(0, lambda: self._log(msg))

    def _on_complete(self, result: DownloadResult):
        def update():
            count = result.count
            title = result.title
            self._draw_progress(100, SUCCESS)
            self.pct_lbl.config(text="100%", fg=SUCCESS)
            state = "PARTIAL" if result.failed else "COMPLETE"
            self.status_track.config(text=state, fg=WARNING if result.failed else SUCCESS)
            ext = self._dl_mode.upper()
            detail = f"; {result.failed} failed" if result.failed else ""
            self._log(f" {state}  {count} {ext} file(s) saved{detail}!",
                      "warn" if result.failed else "success")
            self._log("" * 46, "dim")
            self._reset_ui()
            self._update_status(state)
            self._history.add_entry(title or self._dl_url[:80], self._dl_url,
                                    self._dl_mode, self._dl_folder, count, "success")
            if self.cfg.get("notify_on_complete", True):
                send_notification("Softcurse  Complete",
                    f"{count} {ext} file(s) saved!\n{title[:50] if title else ''}")
            if self._tray: self._tray.update_tooltip("Download Complete!")
            if self._dl_mode in ("mp3", "flac", "wav") and check_pygame():
                self.player_panel.load_folder(self._dl_folder)
            if self._active_queue_id is not None:
                self._download_queue.finish(
                    self._active_queue_id, QueueStatus.COMPLETE,
                    f"{result.count} file(s) saved",
                )
                self._active_queue_id = None
                self._refresh_queue()
                self.root.after(250, self._run_next_queue)
        self.root.after(0, update)

    def _on_error(self, error):
        def update():
            presentation = present_error(error)
            self._draw_progress(0)
            self.status_track.config(text=f"{presentation.category} ERROR", fg=ERROR)
            self._log(f" {presentation.summary}", "error")
            self._log(f" Next: {presentation.action}", "warn")
            self._reset_ui(); self._update_status(f"{presentation.category} ERROR")
            self._history.add_failed_entry(
                self._dl_url, self._dl_mode, self._dl_folder, error
            )
            if self.cfg.get("notify_on_complete", True):
                send_notification("Softcurse  Error", f"Download failed: {error[:80]}")
            if self._active_queue_id is not None:
                self._download_queue.finish(
                    self._active_queue_id, QueueStatus.FAILED, presentation.summary
                )
                self._active_queue_id = None
                self._refresh_queue()
                self.root.after(250, self._run_next_queue)
        self.root.after(0, update)

    def _reset_ui(self):
        self._downloading = False
        self.dl_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")

    def _update_status(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.status_bar.config(text=f"// {msg} // [{ts}]")

    #  Logging 
    def _log(self, msg, tag="info"):
        def _do():
            self.log_text.config(state="normal")
            ts = time.strftime("%H:%M:%S")
            if tag == "info":
                if any(x in msg for x in ["", "", "COMPLETE"]): t = "success"
                elif any(x in msg for x in ["", "ERROR"]):        t = "error"
                elif any(x in msg for x in ["", "warn"]):         t = "warn"
                else: t = "info"
            else:
                t = tag
            self.log_text.insert("end", f"[{ts}] {msg}\n", t)
            self.log_text.see("end"); self.log_text.config(state="disabled")
            lines = int(self.log_text.index("end-1c").split(".")[0])
            if lines > 300:
                self.log_text.config(state="normal")
                self.log_text.delete("1.0", "60.0")
                self.log_text.config(state="disabled")
        self.root.after(0, _do)

    #  Config 
    def _save_cfg_quick(self):
        mode = self._mode.get()
        key = "mp4_output_folder" if mode == "mp4" else "output_folder"
        self.cfg[key]             = self.folder_var.get()
        self.cfg["quality"]       = self.quality_var.get()
        self.cfg["video_quality"] = self.video_quality_var.get()
        self.cfg["last_url"]      = self.url_var.get()
        self.cfg["sponsorblock"]  = self.sb_var.get()
        self.cfg["sb_categories"] = [k for k, v in self.sb_cat_vars.items() if v.get()]
        self._config_saver(self.cfg)
