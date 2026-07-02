import tkinter as tk


def show_messagebox(msg_func, *args, **kwargs):
    """Show a messagebox using a temporary hidden root window."""
    root = tk.Tk()
    root.withdraw()
    try:
        return msg_func(*args, **kwargs)
    finally:
        root.destroy()