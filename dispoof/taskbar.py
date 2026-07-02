import ctypes


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


_CLSID_TaskbarList = _GUID(
    0x56FDF344, 0xFD6D, 0x11D0,
    (ctypes.c_ubyte * 8)(0x95, 0x8A, 0x00, 0x60, 0x97, 0xC9, 0xA0, 0x90)
)
_IID_ITaskbarList3 = _GUID(
    0xEA1AFB91, 0x9E28, 0x4B86,
    (ctypes.c_ubyte * 8)(0x90, 0xE9, 0x9E, 0x9F, 0x8A, 0x5E, 0xEF, 0xAF)
)


class TaskbarProgress:
    """Windows taskbar progress bar via ITaskbarList3."""

    TBPF_NOPROGRESS = 0
    TBPF_NORMAL = 0x2
    TBPF_PAUSED = 0x8

    def __init__(self, tk_root):
        self._ok = False
        self._obj = ctypes.c_void_p(None)
        self._hwnd = self._get_window_handle(tk_root)
        self._setup()

    def _get_window_handle(self, tk_root):
        """Get the window handle for the given Tk root."""
        title = tk_root.title()
        hwnd = ctypes.windll.user32.FindWindowW(None, title)
        if not hwnd:
            hwnd = tk_root.winfo_id()
            hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2)
        return hwnd

    def _vtbl(self, index: int):
        """Get virtual table function pointer."""
        vptr = ctypes.cast(self._obj, ctypes.POINTER(ctypes.c_void_p))
        ftbl = ctypes.cast(vptr[0], ctypes.POINTER(ctypes.c_void_p))
        return ftbl[index]

    def _setup(self):
        """Initialize COM interface."""
        try:
            ole32 = ctypes.windll.ole32
            ole32.CoInitialize(None)
            hr = ole32.CoCreateInstance(
                ctypes.byref(_CLSID_TaskbarList), None, 0x17,
                ctypes.byref(_IID_ITaskbarList3), ctypes.byref(self._obj),
            )
            if hr != 0:
                return
            HrInit = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p)(self._vtbl(3))
            if HrInit(self._obj) != 0:
                return
            self._ok = True
        except Exception:
            self._ok = False

    def set_value(self, completed: int, total: int):
        """Set progress bar value."""
        if not self._ok:
            return
        try:
            fn = ctypes.WINFUNCTYPE(
                ctypes.HRESULT, ctypes.c_void_p,
                ctypes.c_size_t, ctypes.c_ulonglong, ctypes.c_ulonglong,
            )(self._vtbl(9))
            fn(self._obj, self._hwnd, completed, total)
        except Exception:
            pass

    def set_state(self, state: int):
        """Set progress bar state."""
        if not self._ok:
            return
        try:
            fn = ctypes.WINFUNCTYPE(
                ctypes.HRESULT, ctypes.c_void_p,
                ctypes.c_size_t, ctypes.c_int,
            )(self._vtbl(10))
            fn(self._obj, self._hwnd, state)
        except Exception:
            pass

    def release(self):
        """Release COM interface."""
        if not self._ok:
            return
        try:
            self.set_state(self.TBPF_NOPROGRESS)
            Release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(self._vtbl(2))
            Release(self._obj)
        except Exception:
            pass
        self._ok = False