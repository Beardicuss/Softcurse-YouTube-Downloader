"""
tray.py - Softcurse // System Tray Integration
Uses pystray for tray icon, plyer for toast notifications.
Both are optional — app works without them.
"""
import threading
import os
import sys

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

try:
    from plyer import notification as plyer_notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


def check_tray_deps() -> dict:
    return {
        "pystray": TRAY_AVAILABLE,
        "plyer": PLYER_AVAILABLE,
    }


def install_tray_deps(log_callback=None):
    """Install pystray and plyer via pip."""
    import subprocess
    def log(msg):
        if log_callback:
            log_callback(msg)
    pkgs = []
    if not TRAY_AVAILABLE:
        pkgs += ["pystray", "Pillow"]
    if not PLYER_AVAILABLE:
        pkgs.append("plyer")
    if not pkgs:
        return True
    log(f"Installing tray deps: {', '.join(pkgs)}...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + pkgs,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        log("Tray dependencies installed. Restart the app to enable tray.")
        return True
    except Exception as e:
        log(f"Failed to install tray deps: {e}")
        return False


def send_notification(title: str, message: str, app_name: str = "Softcurse"):
    """Send a desktop toast notification (non-blocking)."""
    if not PLYER_AVAILABLE:
        return
    def _notify():
        try:
            plyer_notification.notify(
                title=title,
                message=message,
                app_name=app_name,
                timeout=5,
            )
        except Exception:
            pass
    threading.Thread(target=_notify, daemon=True).start()


def _make_icon_image(size=64):
    """Generate a simple cyan 'SC' icon image for the tray."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGBA", (size, size), (2, 2, 2, 255))
        draw = ImageDraw.Draw(img)
        # Cyan border
        draw.rectangle([0, 0, size-1, size-1], outline=(0, 255, 255, 255), width=2)
        # SC text
        draw.text((size//2 - 12, size//2 - 10), "SC",
                  fill=(0, 255, 255, 255))
        return img
    except Exception:
        return None


class TrayManager:
    def __init__(self, on_show: callable, on_quit: callable):
        self._icon = None
        self._on_show = on_show
        self._on_quit = on_quit
        self._running = False

    def start(self):
        if not TRAY_AVAILABLE:
            return False
        try:
            img = _make_icon_image()
            if img is None:
                return False

            menu = pystray.Menu(
                pystray.MenuItem("Show Softcurse", self._show, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._quit),
            )
            self._icon = pystray.Icon(
                "softcurse",
                img,
                "Softcurse // YouTube Downloader",
                menu
            )
            self._running = True
            thread = threading.Thread(target=self._icon.run, daemon=True)
            thread.start()
            return True
        except Exception as e:
            print(f"[Tray] Failed to start: {e}")
            return False

    def stop(self):
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
        self._running = False

    def update_tooltip(self, text: str):
        if self._icon:
            try:
                self._icon.title = f"Softcurse — {text}"
            except Exception:
                pass

    def _show(self, icon=None, item=None):
        if self._on_show:
            self._on_show()

    def _quit(self, icon=None, item=None):
        self.stop()
        if self._on_quit:
            self._on_quit()
