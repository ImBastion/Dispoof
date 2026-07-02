import os
import sys
import threading
import time
import tkinter as tk

from .config import DARK_BG, YELLOW, GREEN
from .paths import resource_path
from .taskbar import TaskbarProgress
from .toast import show_custom_toast


class GameWindow:
    WINDOW_WIDTH = 320
    WINDOW_HEIGHT = 240

    def __init__(self, exe_name: str, game_name: str, total_seconds: int, start_minimized: bool = False):
        self.TOTAL = total_seconds
        self.exe_name = exe_name
        self.game_name = game_name
        self.running = True
        self.start_time = time.time()

        self.root = tk.Tk()
        self._setup_window()
        self._create_widgets()
        self._setup_taskbar()

        threading.Thread(target=self.countdown, daemon=True).start()
        self.update_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        if start_minimized:
            self.root.iconify()

        self.root.mainloop()

    def _setup_window(self):
        """Configure window properties."""
        self.root.title(self.exe_name)
        self.root.configure(bg=DARK_BG)
        self.root.resizable(False, False)

        x = (self.root.winfo_screenwidth() // 2) - (self.WINDOW_WIDTH // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.WINDOW_HEIGHT // 2)
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x}+{y}")

        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

    def _create_widgets(self):
        """Create UI widgets."""
        self.timer_label = tk.Label(
            self.root, text="00:00",
            font=("Consolas", 48, "bold"),
            bg=DARK_BG, fg=YELLOW
        )
        self.timer_label.pack(expand=True)

    def _setup_taskbar(self):
        """Setup taskbar progress."""
        self.root.update()
        self._taskbar = TaskbarProgress(self.root)
        self._taskbar.set_state(TaskbarProgress.TBPF_NORMAL)

    def on_close(self):
        """Handle window close event."""
        self.running = False
        self._taskbar.release()
        self.root.destroy()
        sys.exit(0)

    def countdown(self):
        """Background countdown thread."""
        while self.running:
            elapsed = int(time.time() - self.start_time)
            if elapsed >= self.TOTAL:
                self.running = False
                self.root.after(0, self.finish)
                break
            time.sleep(0.1)

    def update_ui(self):
        """Update timer display and taskbar."""
        if self.running:
            elapsed = int(time.time() - self.start_time)
            remaining = max(0, self.TOTAL - elapsed)
            mins, secs = divmod(remaining, 60)
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
            self._taskbar.set_value(elapsed, self.TOTAL)
            self.root.after(100, self.update_ui)

    def finish(self):
        """Handle timer completion."""
        self.timer_label.config(text="00:00", fg=GREEN)
        self._taskbar.set_state(TaskbarProgress.TBPF_PAUSED)
        self._taskbar.set_value(self.TOTAL, self.TOTAL)

        show_custom_toast(
            title="Time's up!",
            message=f"{self.game_name} session has ended.",
            duration_ms=10000,
            sound=True
        )