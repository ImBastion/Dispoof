import os
import sys


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        return os.path.join(sys._MEIPASS, relative_path)
    except Exception:
        return os.path.join(os.path.abspath("."), relative_path)


def get_desktop_path() -> str:
    """Get path to user's desktop."""
    return os.path.join(os.path.expanduser("~"), "Desktop")


def sanitize_path_segment(segment: str):
    """Sanitize a single path segment."""
    segment = segment.strip()
    invalid_chars = r'<>:"|?*'
    if any(char in segment for char in invalid_chars) or ".." in segment:
        return None
    return segment


def sanitize_folder_path(folder_path: str) -> str:
    """Sanitize a full folder path."""
    if not folder_path:
        return folder_path
    segments = folder_path.replace('/', '\\').split('\\')
    sanitized = [sanitize_path_segment(seg) for seg in segments if seg]
    return '\\'.join(filter(None, sanitized))


def sanitize_exe_name(name: str) -> str:
    """Sanitize an executable name."""
    name = name.strip()
    if name.lower().endswith(".exe"):
        name = name[:-4]
    invalid_chars = r'<>:"|?*\/'
    name = ''.join(c for c in name if c not in invalid_chars)
    return name.strip()