import os
import sys

RUNTIME_MINUTES = 16.0
RUNTIME_SECONDS = int(RUNTIME_MINUTES * 60)
GAMES_URL = "https://cdn.discordapp.com/detectables/games.json"
CACHE_MAX_AGE = 60 * 60 * 24
MARKER_FILE = ".dispoof_marker"


def get_app_dir() -> str:
    """Directory of the running script (dev) or executable (frozen)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(sys.argv[0]))


CACHE_FILE = os.path.join(get_app_dir(), "games_cache.json")

# Discord Theme Colors
BLURPLE = "#5865F2"
BLURPLE_HOVER = "#4752C4"
DARK_BG = "#313338"
DARKER_BG = "#2B2D31"
DARKEST_BG = "#1E1F22"
INPUT_BG = "#383A40"
HOVER_BG = "#404249"
TEXT_PRIMARY = "#F2F3F5"
TEXT_SECONDARY = "#B5BAC1"
TEXT_MUTED = "#949BA4"
GREEN = "#57F287"
YELLOW = "#FEE75C"