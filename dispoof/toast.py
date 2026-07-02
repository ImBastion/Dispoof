import ctypes
import threading
import tkinter as tk

from .config import BLURPLE, DARKEST_BG, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, HOVER_BG, DARKER_BG

_active_toasts = []


def show_custom_toast(title: str, message: str, duration_ms: int = 8000, sound: bool = True):
    """Shows a Discord-themed toast notification as a borderless topmost window."""
    def _show():
        root = _get_or_create_root()
        toast = _create_toast_window(root, title, message)
        _position_toast(toast)
        _active_toasts.append(toast)

        if sound:
            _play_notification_sound()

        toast.after(duration_ms, lambda: _dismiss_toast(toast))

    _schedule_on_main_thread(_show)


def _get_or_create_root():
    """Get existing Tk root or create a new one."""
    try:
        root = tk._default_root
        if root is None:
            root = tk.Tk()
            root.withdraw()
    except Exception:
        root = tk.Tk()
        root.withdraw()
    return root


def _create_toast_window(root, title, message):
    """Create and configure the toast window."""
    toast = tk.Toplevel(root)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.configure(bg=DARKEST_BG)

    frame = tk.Frame(toast, bg=DARKEST_BG, bd=0, highlightthickness=2, highlightbackground=BLURPLE)
    frame.pack(fill="both", expand=True)

    title_label = tk.Label(
        frame, text=title, font=("Segoe UI", 12, "bold"),
        bg=DARKEST_BG, fg=TEXT_PRIMARY, anchor="w"
    )
    title_label.pack(fill="x", padx=16, pady=(12, 4))

    msg_label = tk.Label(
        frame, text=message, font=("Segoe UI", 10),
        bg=DARKEST_BG, fg=TEXT_SECONDARY, anchor="w",
        justify="left", wraplength=280
    )
    msg_label.pack(fill="x", padx=16, pady=(0, 4))

    dismiss_btn = tk.Button(
        frame, text="✕ Dismiss", font=("Segoe UI", 9),
        bg=DARKER_BG, fg=TEXT_MUTED, activebackground=HOVER_BG,
        activeforeground=TEXT_PRIMARY, relief="flat", cursor="hand2",
        command=lambda: _dismiss_toast(toast)
    )
    dismiss_btn.pack(fill="x", padx=16, pady=(0, 12))

    dismiss_btn.bind("<Enter>", lambda e: dismiss_btn.config(bg=HOVER_BG, fg=TEXT_PRIMARY))
    dismiss_btn.bind("<Leave>", lambda e: dismiss_btn.config(bg=DARKER_BG, fg=TEXT_MUTED))

    for widget in (toast, frame, title_label, msg_label):
        widget.bind("<Button-1>", lambda e: _dismiss_toast(toast))

    return toast


def _position_toast(toast):
    """Position toast in bottom-right corner, stacking if needed."""
    toast.update_idletasks()
    w = toast.winfo_reqwidth() or 320
    h = toast.winfo_reqheight() or 120

    screen_w = toast.winfo_screenwidth()
    screen_h = toast.winfo_screenheight()

    y_offset = sum(t.winfo_height() + 10 for t in _active_toasts if t.winfo_exists())
    x = screen_w - w - 20
    y = screen_h - h - 60 - y_offset

    toast.geometry(f"{w}x{h}+{x}+{y}")
    toast.lift()
    toast.focus_force()


def _play_notification_sound():
    """Play Windows notification sound."""
    try:
        ctypes.windll.user32.MessageBeep(0x40)
    except Exception:
        pass


def _schedule_on_main_thread(func):
    """Schedule function on main thread."""
    try:
        tk._default_root.after(0, func)
    except Exception:
        threading.Thread(target=func, daemon=True).start()


def _dismiss_toast(toast):
    """Dismiss and cleanup toast."""
    try:
        if toast.winfo_exists():
            toast.destroy()
        if toast in _active_toasts:
            _active_toasts.remove(toast)
    except Exception:
        pass