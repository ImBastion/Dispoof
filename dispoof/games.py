import json
import os
import time
import urllib.request

from .config import CACHE_FILE, GAMES_URL


def parse_games(data: list) -> list:
    """Parse and filter games data for Windows executables."""
    win_games = []
    for game in data:
        exes = [e for e in game.get("executables", []) if e.get("os") == "win32"]
        if not exes:
            continue
        exes.sort(key=lambda e: (e.get("is_launcher", False), len(e["name"])))
        win_games.append({
            "name": game["name"],
            "aliases": game.get("aliases", []),
            "executables": exes
        })
    win_games.sort(key=lambda g: g["name"].lower())
    return win_games


def load_cache() -> list:
    """Load games from cache file."""
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cached = json.load(f)
        return cached.get("games", None)
    except Exception:
        return None


def save_cache(games: list):
    """Save games to cache file."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"timestamp": time.time(), "games": games}, f, ensure_ascii=False)
    except Exception:
        pass


def cache_age_seconds() -> float:
    """Get age of cache in seconds."""
    if not os.path.exists(CACHE_FILE):
        return float("inf")
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cached = json.load(f)
        return time.time() - cached.get("timestamp", 0)
    except Exception:
        return float("inf")


def fetch_games_from_network() -> list:
    """Fetch games data from Discord CDN."""
    req = urllib.request.Request(
        GAMES_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/125.0.0.0 Safari/537.36"
        },
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode())
    return parse_games(data)