import ctypes


class SingleInstanceLock:
    def __init__(self, mutex_name="Global\\DisproofMainAppMutex"):
        self.mutex_name = mutex_name
        self.mutex = None
        self._locked = False

    def acquire(self) -> bool:
        """Acquire the mutex lock."""
        try:
            self.mutex = ctypes.windll.kernel32.CreateMutexW(None, True, self.mutex_name)
            last_error = ctypes.windll.kernel32.GetLastError()
            self._locked = (last_error != 183)
            return self._locked
        except Exception:
            return False

    def release(self):
        """Release the mutex lock."""
        if self._locked and self.mutex:
            try:
                ctypes.windll.kernel32.ReleaseMutex(self.mutex)
                ctypes.windll.kernel32.CloseHandle(self.mutex)
            except Exception:
                pass
            self._locked = False