import json
import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from .config import (
    CACHE_MAX_AGE, BLURPLE, BLURPLE_HOVER, DARK_BG, DARKER_BG, DARKEST_BG,
    INPUT_BG, HOVER_BG, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)
from .games import load_cache, save_cache, cache_age_seconds, fetch_games_from_network
from .launcher import create_and_launch
from .marker import remove_folder_recursive
from .paths import resource_path, get_desktop_path, sanitize_exe_name, sanitize_folder_path


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._init_properties()
        self._setup_window()
        self._build_ui()
        self._initial_load()

    def _init_properties(self):
        """Initialize application properties."""
        self.all_games = []
        self.selected_exe = tk.StringVar()
        self.selected_path = tk.StringVar()
        self.selected_game_name = tk.StringVar()
        self.tracked_games = {}
        self._search_after_id = None
        self.start_minimized_var = tk.BooleanVar(value=False)

    def _setup_window(self):
        """Configure main window."""
        self.title("Dispoof!")
        self.geometry("600x600")
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close_main)

        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

    def _build_ui(self):
        """Build user interface."""
        self._build_header()
        self._build_search_bar()
        self._build_bottom_bar()
        self._build_action_frame()
        self._build_list_frame()

    def _build_header(self):
        """Build header with logo."""
        header_frame = tk.Frame(self, bg=DARK_BG)
        header_frame.pack(fill="x", padx=20, pady=(10, 0))

        logo_path = resource_path("Dispoof_Logo.png")
        if os.path.exists(logo_path):
            self.logo_img = tk.PhotoImage(file=logo_path)
            tk.Label(header_frame, image=self.logo_img, bg=DARK_BG).pack(side="left", pady=(5, 0))
        else:
            tk.Label(
                header_frame, text="Dispoof!",
                font=("Arial", 20, "bold"), bg=DARK_BG, fg=BLURPLE
            ).pack(side="left")

        tk.Label(
            header_frame, text="Search game -> select executable -> create",
            font=("Arial", 9), bg=DARK_BG, fg=TEXT_SECONDARY
        ).pack(side="left", padx=(15, 0), pady=(8, 0))

    def _build_search_bar(self):
        """Build search bar with refresh button."""
        search_frame = tk.Frame(self, bg=DARK_BG)
        search_frame.pack(fill="x", padx=20, pady=(8, 0))
        search_row = tk.Frame(search_frame, bg=DARK_BG)
        search_row.pack(fill="x")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)

        tk.Entry(
            search_row, textvariable=self.search_var, font=("Arial", 11),
            bg=INPUT_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
            relief="flat", bd=5
        ).pack(side="left", fill="x", expand=True)

        self.refresh_btn = tk.Button(
            search_row, text="Refresh", font=("Arial", 9, "bold"),
            bg=BLURPLE, fg=TEXT_PRIMARY, activebackground=BLURPLE_HOVER,
            activeforeground=TEXT_PRIMARY, relief="flat",
            padx=8, pady=4, cursor="hand2", command=self._force_refresh
        )
        self.refresh_btn.pack(side="left", padx=(6, 0))

    def _build_bottom_bar(self):
        """Build bottom status bar."""
        bottom_frame = tk.Frame(self, bg=DARKEST_BG)
        bottom_frame.pack(fill="x", side="bottom", padx=20, pady=(0, 0))

        tk.Label(
            bottom_frame, text="Select a game from the list above",
            font=("Arial", 8), bg=DARKEST_BG, fg=TEXT_MUTED, anchor="w"
        ).pack(side="left", fill="x", expand=True, padx=(10, 0), pady=8)

        self.log_var = tk.StringVar(value="")
        tk.Label(
            bottom_frame, textvariable=self.log_var, font=("Consolas", 8),
            bg=DARKEST_BG, fg=TEXT_SECONDARY, anchor="e"
        ).pack(side="right", padx=(0, 10), pady=8)

    def _build_action_frame(self):
        """Build action buttons frame."""
        action_frame = tk.Frame(self, bg=DARK_BG)
        action_frame.pack(fill="x", side="bottom", padx=20, pady=(5, 12))

        btn_container = tk.Frame(action_frame, bg=DARK_BG)
        btn_container.pack(pady=(0, 5))

        self.create_btn = tk.Button(
            btn_container, text="Launch", font=("Arial", 14, "bold"),
            bg=BLURPLE, fg=TEXT_PRIMARY, activebackground=BLURPLE_HOVER,
            activeforeground=TEXT_PRIMARY, relief="flat",
            padx=30, pady=10, cursor="hand2", command=self._on_create
        )
        self.create_btn.pack(side="left", padx=(0, 10))

        self.custom_btn = tk.Button(
            btn_container, text="Custom...", font=("Arial", 12),
            bg=DARKER_BG, fg=TEXT_PRIMARY, activebackground=HOVER_BG,
            activeforeground=TEXT_PRIMARY, relief="flat",
            padx=20, pady=10, cursor="hand2", command=self._on_custom
        )
        self.custom_btn.pack(side="left")

        self.minimized_check = tk.Checkbutton(
            action_frame, text="Start Minimized", variable=self.start_minimized_var,
            font=("Arial", 10), bg=DARK_BG, fg=TEXT_SECONDARY, selectcolor=INPUT_BG,
            activebackground=DARK_BG, activeforeground=TEXT_PRIMARY,
            relief="flat", cursor="hand2"
        )
        self.minimized_check.pack(pady=(0, 5))

    def _build_list_frame(self):
        """Build games list frame."""
        list_frame = tk.Frame(self, bg=DARK_BG)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(5, 5))

        self.status_var = tk.StringVar(value="Loading games...")
        tk.Label(
            list_frame, textvariable=self.status_var, font=("Arial", 9),
            bg=DARK_BG, fg=BLURPLE
        ).pack(anchor="w")

        self._build_treeview(list_frame)

    def _build_treeview(self, parent):
        """Build and configure treeview."""
        columns = ("name",)
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
        self.tree.heading("name", text="GAME NAME")
        self.tree.column("name", width=450, anchor="w")

        self._configure_treeview_style()

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _configure_treeview_style(self):
        """Configure treeview styling."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=DARKER_BG, foreground=TEXT_PRIMARY, rowheight=24,
            fieldbackground=DARKER_BG, font=("Arial", 10)
        )
        style.configure(
            "Treeview.Heading",
            background=DARKEST_BG, foreground=BLURPLE,
            font=("Arial", 8, "bold"), relief="flat"
        )
        style.map(
            "Treeview",
            background=[("selected", HOVER_BG)],
            foreground=[("selected", TEXT_PRIMARY)]
        )

    def _initial_load(self):
        """Initial loading of games data."""
        cached = load_cache()
        age = cache_age_seconds()

        if cached:
            self.all_games = cached
            self._populate_tree(cached)
            age_str = self._format_age(age)

            if age > CACHE_MAX_AGE:
                self.status_var.set(f"{len(cached)} games loaded from cache ({age_str} old) — refreshing...")
                self._fetch_in_background(silent=True)
            else:
                self.status_var.set(f"{len(cached)} games loaded from cache ({age_str} old)")
        else:
            self.status_var.set("No cache found — fetching from Discord CDN...")
            self._fetch_in_background(silent=False)

    def _format_age(self, seconds: float) -> str:
        """Format cache age for display."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m"
        elif seconds < 86400:
            return f"{int(seconds // 3600)}h"
        else:
            return f"{int(seconds // 86400)}d"

    def _fetch_in_background(self, silent: bool = False):
        """Fetch games data in background thread."""
        self.refresh_btn.config(state="disabled", text="...")

        def fetch():
            try:
                games = fetch_games_from_network()
                save_cache(games)
                self.all_games = games
                self.after(0, lambda: self._on_fetch_success(games))
            except Exception as e:
                self.after(0, lambda: self._on_fetch_failure(str(e), silent))

        threading.Thread(target=fetch, daemon=True).start()

    def _on_fetch_success(self, games):
        """Handle successful games fetch."""
        query = self.search_var.get().strip().lower()
        filtered = self._filter_games(games, query)
        self._populate_tree(filtered)
        self.status_var.set(f"{len(games)} games loaded — cache updated")
        self.refresh_btn.config(state="normal", text="Refresh")

    def _on_fetch_failure(self, error, silent):
        """Handle failed games fetch."""
        self.refresh_btn.config(state="normal", text="Refresh")
        if not silent:
            self.status_var.set(f"Fetch failed: {error}")
            if not self.all_games:
                messagebox.showerror(
                    "Network Error",
                    f"Could not load games:\n{error}\n\n"
                    "Make sure you are connected to the internet."
                )
        else:
            self.status_var.set("Background refresh failed — using cached data")

    def _force_refresh(self):
        """Force refresh of games data."""
        self.status_var.set("Fetching latest games from Discord CDN...")
        self._fetch_in_background(silent=False)

    def _populate_tree(self, games):
        """Populate treeview with games."""
        self.tree.delete(*self.tree.get_children())
        for game in games:
            self.tree.insert("", "end", values=(game["name"],), tags=(json.dumps(game),))

    def _filter_games(self, games, query):
        """Filter games by search query."""
        if not query:
            return games
        return [
            g for g in games
            if query in g["name"].lower() or any(query in a.lower() for a in g["aliases"])
        ]

    def _on_search(self, *_):
        """Handle search input."""
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(250, self._execute_search)

    def _execute_search(self):
        """Execute search filtering."""
        self._search_after_id = None
        query = self.search_var.get().strip().lower()
        filtered = self._filter_games(self.all_games, query)
        self._populate_tree(filtered)

    def _on_select(self, _):
        """Handle game selection."""
        selected = self.tree.selection()
        if not selected:
            return

        tags = self.tree.item(selected[0], "tags")
        if not tags:
            return

        game = json.loads(tags[0])
        best_exe = game["executables"][0]["name"]
        exe_name = sanitize_exe_name(os.path.basename(best_exe))
        raw_path = os.path.dirname(best_exe).strip("/\\")
        folder_path = sanitize_folder_path(raw_path) if raw_path else exe_name

        self.selected_exe.set(exe_name)
        self.selected_path.set(folder_path if folder_path else exe_name)
        self.selected_game_name.set(game["name"])

    def _on_custom(self):
        """Open custom exe dialog."""
        dialog = tk.Toplevel(self)
        dialog.title("Run Custom EXE")
        dialog.geometry("450x160")
        dialog.configure(bg=DARK_BG)
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(
            dialog, text="Paste a directory or exe name:",
            font=("Arial", 11), bg=DARK_BG, fg=TEXT_SECONDARY
        ).pack(pady=(20, 5))

        entry_var = tk.StringVar()
        entry = tk.Entry(
            dialog, textvariable=entry_var, font=("Arial", 11),
            bg=INPUT_BG, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
            relief="flat", bd=5, width=40
        )
        entry.pack(pady=5)
        entry.focus_set()

        def on_ok():
            text = entry_var.get().strip()
            if not text:
                messagebox.showwarning("Empty", "Please enter a path or name.", parent=dialog)
                return

            exe_name, folder_path = self._parse_custom(text)
            if not exe_name:
                messagebox.showerror("Error", "Could not parse exe name from input.", parent=dialog)
                return

            dialog.destroy()

            self.selected_exe.set(exe_name)
            self.selected_path.set(folder_path)
            self.selected_game_name.set(exe_name)

            self._on_create()

        def on_cancel():
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg=DARK_BG)
        btn_frame.pack(pady=15)
        tk.Button(
            btn_frame, text="Cancel", command=on_cancel,
            bg=DARKER_BG, fg=TEXT_PRIMARY, relief="flat",
            padx=15, pady=5, cursor="hand2", font=("Arial", 10)
        ).pack(side="left", padx=5)
        tk.Button(
            btn_frame, text="Launch", command=on_ok,
            bg=BLURPLE, fg=TEXT_PRIMARY, relief="flat",
            padx=15, pady=5, cursor="hand2", font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)

        dialog.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())

    def _parse_custom(self, text: str):
        """Parse custom input to extract exe name and folder path."""
        text = text.strip().strip('"').strip("'").strip()
        if not text:
            return None, None

        normalized = text.replace('/', '\\').rstrip('\\ ').rstrip('\\').strip()
        if not normalized:
            return None, None

        if '\\' in normalized:
            parts = [p.strip() for p in normalized.split('\\') if p.strip()]
            if not parts:
                return None, None
            last_part = parts[-1]
            dir_part = '\\'.join(parts[:-1])
        else:
            last_part = normalized
            dir_part = ""

        exe_name = last_part
        if exe_name.lower().endswith('.exe'):
            exe_name = exe_name[:-4]

        exe_name = sanitize_exe_name(exe_name)
        if not exe_name:
            return None, None

        folder_path = dir_part

        if len(folder_path) >= 2 and folder_path[1] == ':':
            folder_path = folder_path[2:].strip()

        folder_path = sanitize_folder_path(folder_path)
        if not folder_path:
            folder_path = exe_name

        return exe_name, folder_path

    def _on_create(self):
        """Handle create/launch button click."""
        exe_name = sanitize_exe_name(self.selected_exe.get())
        folder_path = sanitize_folder_path(self.selected_path.get().strip())
        game_name = self.selected_game_name.get()

        if not exe_name:
            messagebox.showerror("Error", "Please select a game from the list first.")
            return

        if not folder_path:
            folder_path = exe_name

        desktop = get_desktop_path()
        final_path = os.path.join(desktop, folder_path)

        if os.path.exists(final_path):
            messagebox.showerror("Error", f"Folder already exists:\n{final_path}\n\nPlease remove it or choose a different name.")
            return

        self.create_btn.config(state="disabled", text="Launching...")
        self.log_var.set("")

        def log(msg):
            self.after(0, lambda: self.log_var.set(f"> {msg}"))

        def done(success, result):
            self.after(0, lambda: self._handle_create_done(success, result, final_path))

        create_and_launch(exe_name, folder_path, game_name, log, done)

    def _handle_create_done(self, success, result, final_path):
        """Handle completion of create/launch process."""
        if success:
            self.log_var.set("Done! Launching...")
            self.create_btn.config(state="normal", text="Launch")

            launch_cmd = [result, "-game", "-gamename", self.selected_game_name.get()]
            if not self.start_minimized_var.get():
                launch_cmd.append("-w")

            try:
                proc = subprocess.Popen(launch_cmd)
                self.tracked_games[final_path] = proc
                self._monitor_process(final_path)
            except Exception as e:
                self.log_var.set("Launch failed.")
                messagebox.showerror("Launch Error", f"Failed to start the cloned executable:\n{e}")
                self._cleanup_folder(final_path)
        else:
            self.log_var.set("Failed.")
            self.create_btn.config(state="normal", text="Launch")
            messagebox.showerror("Error", result)

    def _monitor_process(self, folder_path: str):
        """Monitor child process and cleanup when done."""
        def monitor():
            proc = self.tracked_games.get(folder_path)
            if proc:
                proc.wait()
                self._cleanup_folder(folder_path)

        threading.Thread(target=monitor, daemon=True).start()

    def _cleanup_folder(self, folder_path: str):
        """Cleanup folder after process ends."""
        if os.path.exists(folder_path):
            remove_folder_recursive(folder_path)

        if folder_path in self.tracked_games:
            del self.tracked_games[folder_path]

        self.after(0, lambda: self.log_var.set(f"Cleaned up: {os.path.basename(folder_path)}"))

    def _on_close_main(self):
        """Handle main window close."""
        active = [
            os.path.basename(p)
            for p, proc in self.tracked_games.items()
            if proc.poll() is None
        ]

        if active:
            messagebox.showwarning(
                "Active Game",
                f"Cannot close Dispoof! while game EXE is running:\n{', '.join(active)}\n\n"
                "Please stop the game EXE first to ensure cleanup works."
            )
            return

        self.destroy()