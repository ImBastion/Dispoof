import ctypes
import json
import os
import shutil
import time
import tkinter as tk
from tkinter import messagebox

from .config import MARKER_FILE
from .paths import get_desktop_path
from .ui_helpers import show_messagebox


def create_marker_file(folder_path: str, exe_name: str, game_name: str):
    """Create a hidden marker file to track Dispoof folders."""
    marker_data = {
        "version": "1.0",
        "exe_name": exe_name,
        "game_name": game_name,
        "folder_name": os.path.basename(folder_path),
        "full_path": folder_path,
        "created": time.time()
    }
    marker_path = os.path.join(folder_path, MARKER_FILE)
    try:
        with open(marker_path, "w", encoding="utf-8") as f:
            json.dump(marker_data, f, indent=2)
        ctypes.windll.kernel32.SetFileAttributesW(marker_path, 0x02)
    except Exception:
        pass


def scan_and_cleanup_orphans():
    """Scan desktop for orphaned Dispoof folders and offer to clean them."""
    orphans = _find_orphaned_folders()
    if orphans:
        _prompt_cleanup_orphans(orphans)


def _find_orphaned_folders():
    """Find all folders with Dispoof markers on desktop."""
    desktop = get_desktop_path()
    orphans = []
    try:
        for item in os.listdir(desktop):
            item_path = os.path.join(desktop, item)
            if not os.path.isdir(item_path):
                continue
            marker_path = os.path.join(item_path, MARKER_FILE)
            if os.path.exists(marker_path):
                orphans.append(_parse_marker_file(marker_path, item_path))
    except Exception:
        pass
    return orphans


def _parse_marker_file(marker_path, item_path):
    """Parse marker file or return default data if corrupted."""
    try:
        with open(marker_path, "r", encoding="utf-8") as f:
            marker_data = json.load(f)
        return {
            "path": item_path,
            "exe_name": marker_data.get("exe_name", "Unknown"),
            "folder_name": marker_data.get("folder_name", "Unknown"),
            "created": marker_data.get("created", 0)
        }
    except Exception:
        return {
            "path": item_path,
            "exe_name": "Unknown (corrupted marker)",
            "folder_name": os.path.basename(item_path),
            "created": 0
        }


def _prompt_cleanup_orphans(orphans):
    """Prompt user to clean up orphaned folders."""
    orphan_list = [
        f"• {o['folder_name']} ({o['exe_name']}.exe) — {_format_time_ago(o['created'])}"
        for o in orphans
    ]

    response = show_messagebox(
        messagebox.askyesno,
        "Orphaned Folders Detected",
        f"Found {len(orphans)} leftover folder(s) from previous sessions:\n\n"
        + "\n".join(orphan_list)
        + "\n\nThese may be from crashed sessions or incomplete cleanups.\n"
          "Would you like to delete them now?",
        icon='warning'
    )

    if response:
        _cleanup_orphans(orphans)


def _cleanup_orphans(orphans):
    """Delete orphaned folders."""
    cleaned = sum(1 for orphan in orphans if remove_folder_recursive(orphan["path"]))

    if cleaned > 0:
        show_messagebox(
            messagebox.showinfo, "Cleanup Complete",
            f"Successfully removed {cleaned} orphaned folder(s)."
        )


def remove_folder_recursive(path):
    """Recursively remove folder and all contents."""
    try:
        ctypes.windll.kernel32.SetFileAttributesW(path, 0x80)
        for root_dir, dirs, files in os.walk(path):
            for name in files + dirs:
                try:
                    ctypes.windll.kernel32.SetFileAttributesW(os.path.join(root_dir, name), 0x80)
                except Exception:
                    pass
        shutil.rmtree(path, ignore_errors=True)
        return True
    except Exception:
        return False


def _format_time_ago(timestamp: float) -> str:
    """Format timestamp as human-readable time ago."""
    if timestamp == 0:
        return "unknown age"
    delta = time.time() - timestamp
    if delta < 60:
        return "less than 1 minute ago"
    elif delta < 3600:
        mins = int(delta // 60)
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    elif delta < 86400:
        hours = int(delta // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(delta // 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"