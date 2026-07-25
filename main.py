"""
main.py - Softcurse // Media Downloader v1.0
Entry point
"""
import sys
import os
import multiprocessing

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _already_running():
    """Use a named Windows mutex to enforce single-instance."""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, True, "SoftcurseMediaDownloader_SingleInstance")
        # ERROR_ALREADY_EXISTS = 183
        if kernel32.GetLastError() == 183:
            return True
        # Keep mutex alive for the lifetime of the process (prevent GC)
        _already_running._mutex = mutex
    except Exception:
        pass
    return False


if __name__ == "__main__":
    multiprocessing.freeze_support()

    if _already_running():
        sys.exit(0)

    from gui import SoftcurseApp
    import tkinter as tk

    root = tk.Tk()
    app = SoftcurseApp(root)
    root.mainloop()
