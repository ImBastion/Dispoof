import ctypes
import os
import shutil
import sys
import threading

from .marker import create_marker_file
from .paths import get_desktop_path


def create_and_launch(exe_name: str, folder_path: str, game_name: str, log_callback, done_callback):
    """Clone the executable to a new folder and prepare for launch."""
    def run():
        if not getattr(sys, 'frozen', False):
            done_callback(False, "Creation only works in the compiled EXE version.\n\nPlease build with PyInstaller to test this feature.")
            return

        desktop = get_desktop_path()
        final_path = os.path.join(desktop, folder_path)

        if os.path.exists(final_path):
            done_callback(False, f"Folder already exists:\n{final_path}")
            return

        log_callback("Creating folder...")
        try:
            os.makedirs(final_path, exist_ok=True)
        except Exception as e:
            done_callback(False, f"Failed to create folder: {e}")
            return

        log_callback("Cloning executable...")
        exe_dest = os.path.join(final_path, f"{exe_name}.exe")
        try:
            shutil.copy2(sys.executable, exe_dest)
        except Exception as e:
            done_callback(False, f"Failed to copy EXE: {e}")
            return

        log_callback("Creating marker file...")
        create_marker_file(final_path, exe_name, game_name)

        log_callback("Hiding folder...")
        try:
            ctypes.windll.kernel32.SetFileAttributesW(final_path, 0x02)
        except Exception:
            pass

        done_callback(True, exe_dest)

    threading.Thread(target=run, daemon=True).start()