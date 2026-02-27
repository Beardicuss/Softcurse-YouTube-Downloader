"""
main.py - Softcurse // YouTube Downloader v3
Entry point
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import SoftcurseApp
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app = SoftcurseApp(root)
    root.mainloop()
