import sys
import traceback
from tkinter import messagebox

from dispoof.app import App
from dispoof.config import RUNTIME_SECONDS
from dispoof.game_window import GameWindow
from dispoof.instance_lock import SingleInstanceLock
from dispoof.marker import scan_and_cleanup_orphans
from dispoof.ui_helpers import show_messagebox


def run_game_mode():
    """Game mode - run timer window."""
    try:
        exe_name = (
            __import__("os").path.splitext(__import__("os").path.basename(sys.executable))[0]
            if getattr(sys, 'frozen', False) else "Game"
        )

        game_name = exe_name
        if "-gamename" in sys.argv:
            try:
                idx = sys.argv.index("-gamename")
                if idx + 1 < len(sys.argv):
                    game_name = sys.argv[idx + 1]
            except Exception:
                pass

        is_windowed = "-w" in sys.argv or "-windowed" in sys.argv
        start_minimized = not is_windowed

        GameWindow(exe_name, game_name, RUNTIME_SECONDS, start_minimized)
    except Exception as e:
        show_messagebox(messagebox.showerror, "Payload Error", str(e))
        sys.exit(1)


def run_main_app():
    """Main app mode."""
    lock = None
    try:
        lock = SingleInstanceLock()
        if not lock.acquire():
            show_messagebox(
                messagebox.showwarning,
                "Already Running",
                "Dispoof! is already running.\n\n"
                "Only one instance can be open at a time to prevent file conflicts."
            )
            sys.exit(0)

        scan_and_cleanup_orphans()
        app = App()
        app.mainloop()

    except Exception:
        traceback.print_exc()
        input("Press ENTER to close...")
    finally:
        if lock:
            lock.release()


if __name__ == "__main__":
    if "-game" in sys.argv or "-g" in sys.argv:
        run_game_mode()
    else:
        run_main_app()