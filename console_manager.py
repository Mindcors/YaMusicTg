from __future__ import annotations

import ctypes
import io
import os
import sys
import threading
from ctypes import wintypes

import msvcrt


def ensure_console_width(min_width: int) -> None:

    class COORD(ctypes.Structure):
        _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

    class SMALL_RECT(ctypes.Structure):
        _fields_ = [
            ("Left", ctypes.c_short),
            ("Top", ctypes.c_short),
            ("Right", ctypes.c_short),
            ("Bottom", ctypes.c_short),
        ]

    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [
            ("dwSize", COORD),
            ("dwCursorPosition", COORD),
            ("wAttributes", ctypes.c_ushort),
            ("srWindow", SMALL_RECT),
            ("dwMaximumWindowSize", COORD),
        ]

    kernel32 = ctypes.windll.kernel32
    kernel32.GetStdHandle.restype = wintypes.HANDLE
    kernel32.GetStdHandle.argtypes = [wintypes.DWORD]

    handle = kernel32.GetStdHandle(-11)
    info = CONSOLE_SCREEN_BUFFER_INFO()

    if not kernel32.GetConsoleScreenBufferInfo(
        handle, ctypes.byref(info)
    ):
        return

    window_width = info.srWindow.Right - info.srWindow.Left + 1
    if window_width >= min_width:
        return

    target = min(min_width, info.dwMaximumWindowSize.X)
    if target <= window_width:
        return

    if info.dwSize.X < target:
        kernel32.SetConsoleScreenBufferSize(
            handle, COORD(target, info.dwSize.Y)
        )

    rect = SMALL_RECT(
        info.srWindow.Left,
        info.srWindow.Top,
        info.srWindow.Left + target - 1,
        info.srWindow.Bottom,
    )
    kernel32.SetConsoleWindowInfo(handle, True, ctypes.byref(rect))


class ConsoleManager:
    SW_HIDE = 0
    SW_SHOW = 5
    SW_RESTORE = 9

    STD_INPUT_HANDLE = -10
    STD_OUTPUT_HANDLE = -11
    STD_ERROR_HANDLE = -12

    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000

    FILE_SHARE_READ = 1
    FILE_SHARE_WRITE = 2

    OPEN_EXISTING = 3

    FILE_ATTRIBUTE_NORMAL = 0x80

    def __init__(self, title="YaMusicTG"):

        self.title = title

        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)

        self._created = False
        self._visible = False

        self._lock = threading.RLock()

        self._stdin = None
        self._stdout = None
        self._stderr = None

        self._orig_stdin = sys.stdin
        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr

        self.kernel32.GetConsoleWindow.restype = wintypes.HWND

        self.kernel32.AllocConsole.argtypes = []
        self.kernel32.AllocConsole.restype = wintypes.BOOL
        self.kernel32.FreeConsole.argtypes = []
        self.kernel32.FreeConsole.restype = wintypes.BOOL
        self.kernel32.SetConsoleCP.argtypes = [wintypes.UINT]
        self.kernel32.SetConsoleCP.restype = wintypes.BOOL
        self.kernel32.SetConsoleOutputCP.argtypes = [wintypes.UINT]
        self.kernel32.SetConsoleOutputCP.restype = wintypes.BOOL
        self.kernel32.GetStdHandle.argtypes = [wintypes.DWORD]
        self.kernel32.GetStdHandle.restype = wintypes.HANDLE
        self.kernel32.GetConsoleMode.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.kernel32.GetConsoleMode.restype = wintypes.BOOL
        self.kernel32.SetConsoleMode.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
        ]
        self.kernel32.SetConsoleMode.restype = wintypes.BOOL
        self.kernel32.SetConsoleTitleW.argtypes = [wintypes.LPCWSTR]
        self.kernel32.SetConsoleTitleW.restype = wintypes.BOOL
        self.kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        self.kernel32.CreateFileW.restype = wintypes.HANDLE

    def show(self):

        with self._lock:

            if not self._created:

                self.kernel32.AllocConsole()
                self.kernel32.SetConsoleCP(65001)
                self.kernel32.SetConsoleOutputCP(65001)
                STD_OUTPUT_HANDLE = -11
                ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

                handle = self.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

                mode = wintypes.DWORD()

                if self.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                    self.kernel32.SetConsoleMode(
                        handle,
                        mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING,
                    )

                try:
                    import locale
                    locale.setlocale(locale.LC_ALL, "")
                except Exception:
                    pass

                self.kernel32.SetConsoleTitleW(self.title)
                self._redirect_streams()

                try:
                    sys.stdout.reconfigure(
                        encoding="utf-8",
                        errors="replace",
                    )
                    sys.stderr.reconfigure(
                        encoding="utf-8",
                        errors="replace",
                    )
                    sys.stdin.reconfigure(
                        encoding="utf-8",
                        errors="replace",
                    )
                except Exception:
                    pass

                self.rebind_logging()

                hwnd = self.kernel32.GetConsoleWindow()

                menu = self.user32.GetSystemMenu(hwnd, False)

                if menu:
                    self.user32.DeleteMenu(
                    menu,
                    0xF060,
                    0x00000000, 
                    )

                    self.user32.DrawMenuBar(hwnd)

                self._created = True

            hwnd = self.kernel32.GetConsoleWindow()

            if hwnd:
                self.user32.ShowWindow(hwnd, self.SW_RESTORE)
                self.user32.ShowWindow(hwnd, self.SW_SHOW)
                self.user32.SetForegroundWindow(hwnd)

            self._visible = True

    def hide(self):

        with self._lock:

            if not self._created:
                return

            hwnd = self.kernel32.GetConsoleWindow()

            if hwnd:
                try:
                    sys.stdout.flush()
                    sys.stderr.flush()
                except Exception:
                    pass    

                self.user32.ShowWindow(hwnd, self.SW_HIDE)

            self._visible = False

    def destroy(self):

        with self._lock:

            if not self._created:
                return

            try:

                if self._stdout:
                    self._stdout.flush()

            except Exception:
                pass

            sys.stdin = self._orig_stdin
            sys.stdout = self._orig_stdout
            sys.stderr = self._orig_stderr

            try:
                self.kernel32.FreeConsole()
            except Exception:
                pass

            self._stdin = None
            self._stdout = None
            self._stderr = None

            self._created = False
            self._visible = False

    def is_visible(self):

        return self._visible

    def _redirect_streams(self):

        stdin = self._open_console(
            "CONIN$",
            self.GENERIC_READ,
            "r",
        )

        stdout = self._open_console(
            "CONOUT$",
            self.GENERIC_WRITE,
            "w",
        )

        stderr = self._open_console(
            "CONOUT$",
            self.GENERIC_WRITE,
            "w",
        )

        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr

        sys.stdin = stdin
        sys.stdout = stdout
        sys.stderr = stderr

    def _open_console(
        self,
        name,
        access,
        mode,
    ):

        handle = self.kernel32.CreateFileW(
            name,
            access,
            self.FILE_SHARE_READ | self.FILE_SHARE_WRITE,
            None,
            self.OPEN_EXISTING,
            self.FILE_ATTRIBUTE_NORMAL,
            None,
        )

        fd = msvcrt.open_osfhandle(handle, 0)

        if "r" in mode:

            return io.TextIOWrapper(
                os.fdopen(fd, "rb", buffering=0),
                encoding="utf-8",
                line_buffering=True,
            )

        return io.TextIOWrapper(
            os.fdopen(fd, "wb", buffering=0),
            encoding="utf-8",
            line_buffering=True,
            write_through=True,
        )
    def rebind_logging(self):

        import logging

        root = logging.getLogger()

        for handler in root.handlers:
            if (
                isinstance(handler, logging.StreamHandler)
                and not isinstance(handler, logging.FileHandler)
            ):
                handler.stream = sys.stdout