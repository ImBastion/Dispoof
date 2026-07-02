<p align="center">
  <img src="https://github.com/ImBastion/Dispoof/blob/master/Dispoof_Logo.png" />
</p>

A lightweight Windows utility that clones itself as a game's executable, runs a countdown timer, and cleans up automatically when finished — useful for spoofing "Currently Playing" status without keeping the actual game installed or running.

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## How it works

1. Pick a game from the searchable list.
2. Dispoof copies itself to a hidden folder on your Desktop, renamed to match that game's real executable name and folder structure.
3. The cloned copy launches in "game mode" — a minimal countdown timer window — which Discord detects the same way it would the real game.
4. When the timer ends (or the window is closed), the cloned folder is automatically deleted. No leftover files.

<p align="center">
  <img width="610" height="633" alt="image" src="https://github.com/user-attachments/assets/fba88441-7c04-4b59-913b-9b43d475c7b6" />
</p>

---

## Features

- 🔍 **Searchable game list** — pulled live from Discord's CDN, with local caching (24h) to avoid unnecessary network calls
- 🛠️ **Custom mode** — manually specify any exe name / folder path if the game isn't in Discord's list
- ⏱️ **Countdown timer** — countdown window with live taskbar progress (Windows `ITaskbarList3`)
- 🔔 **Toast notifications** — Discord-themed popup when a session ends
- 🧹 **Self-cleaning** — automatically deletes the cloned folder once the process ends
- 🩹 **Orphan recovery** — detects and offers to remove leftover folders from crashed sessions

---

## Download

Grab the latest `Dispoof.exe` from the [Releases](../../releases) page. No installation required — just run it.

> **Note:** Dispoof only works when run as a compiled `.exe`. Running `main.py` directly in a Python environment lets you browse the UI, but the actual clone-and-launch feature requires a frozen build (since it copies its own executable).

---

## Usage

1. Launch `Dispoof.exe`.
2. Search for a game, or use **Custom...** to enter a specific exe name/path manually.
3. (Optional) Check **Start Minimized** if you don't want the timer window visible.
4. Click **Launch**.

---

## Building from source

### Requirements

- Python 3.10+
- Windows (uses Windows-only APIs: `ctypes.windll`, COM taskbar interface, etc.)
- [PyInstaller](https://pyinstaller.org/) for building the standalone `.exe`

### Build

```bat
pyinstaller --onefile --windowed --name "Dispoof" --icon="icon.ico" --add-data "Dispoof_Logo.png;." --add-data "icon.ico;." main.py
```

The compiled executable will be in `dist/Dispoof.exe`.

> All runtime dependencies are Python standard library — no third-party packages are needed to *run* the app, only to *build* it.

---

## Disclaimer

This project is intended for personal use and experimentation with Discord's game executable detection system. Use responsibly. The author is not responsible for any misuse.

---

## License

[MIT](LICENSE)
