from __future__ import annotations

import asyncio
import ctypes
import logging
import threading
import webbrowser
import os
import sys
from ctypes import wintypes
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app import Application
def resource_path(path: str) -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, path)

    return os.path.join(os.path.dirname(__file__), path)

HANDLE = ctypes.c_void_p
HWND = HANDLE
HMENU = HANDLE
HICON = HANDLE
HCURSOR = HANDLE
HBRUSH = HANDLE
HINSTANCE = HANDLE
HMODULE = HANDLE
ATOM = ctypes.c_ushort
LRESULT = ctypes.c_ssize_t
WPARAM = ctypes.c_size_t
LPARAM = ctypes.c_ssize_t
LONG_PTR = ctypes.c_ssize_t
ULONG_PTR = ctypes.c_size_t
UINT_PTR = ctypes.c_size_t


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", ctypes.c_byte * 16),
        ("hBalloonIcon", HICON),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


WNDPROC = ctypes.WINFUNCTYPE(LRESULT, HWND, wintypes.UINT, WPARAM, LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", HINSTANCE),
        ("hIcon", HICON),
        ("hCursor", HCURSOR),
        ("hbrBackground", HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", HWND),
        ("message", wintypes.UINT),
        ("wParam", WPARAM),
        ("lParam", LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    ]


user32 = ctypes.WinDLL("user32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype = ATOM
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    HWND,
    HMENU,
    HINSTANCE,
    wintypes.LPVOID,
]
user32.CreateWindowExW.restype = HWND
user32.DefWindowProcW.argtypes = [HWND, wintypes.UINT, WPARAM, LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.DestroyWindow.argtypes = [HWND]
user32.DestroyWindow.restype = wintypes.BOOL
user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.PostQuitMessage.restype = None
user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.TranslateMessage.restype = wintypes.BOOL
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.restype = LRESULT
user32.PostMessageW.argtypes = [HWND, wintypes.UINT, WPARAM, LPARAM]
user32.PostMessageW.restype = wintypes.BOOL
user32.CreatePopupMenu.argtypes = []
user32.CreatePopupMenu.restype = HMENU
user32.AppendMenuW.argtypes = [HMENU, wintypes.UINT, UINT_PTR, wintypes.LPCWSTR]
user32.AppendMenuW.restype = wintypes.BOOL
user32.TrackPopupMenu.argtypes = [HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, HWND, wintypes.LPVOID]
user32.TrackPopupMenu.restype = wintypes.BOOL
user32.DestroyMenu.argtypes = [HMENU]
user32.DestroyMenu.restype = wintypes.BOOL
user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.LoadIconW.argtypes = [HINSTANCE, wintypes.LPCWSTR]
user32.LoadIconW.restype = HICON
user32.LoadImageW.argtypes = [
    wintypes.HINSTANCE,
    wintypes.LPCWSTR,
    wintypes.UINT,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]

user32.LoadImageW.restype = HICON

shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
shell32.Shell_NotifyIconW.restype = wintypes.BOOL
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = HMODULE


class TrayIcon:
    WM_TRAYICON = 0x0400 + 1
    WM_COMMAND = 0x0111
    WM_CLOSE = 0x0010
    WM_DESTROY = 0x0002
    WM_CONTEXTMENU = 0x007B
    WM_RBUTTONUP = 0x0205
    WM_LBUTTONUP = 0x0202

    NIM_ADD = 0x00000000
    NIM_DELETE = 0x00000002
    NIF_MESSAGE = 0x00000001
    NIF_ICON = 0x00000002
    NIF_TIP = 0x00000004

    MF_STRING = 0x00000000
    MF_SEPARATOR = 0x00000800
    MF_CHECKED = 0x00000008
    MF_UNCHECKED = 0x00000000
    TPM_RIGHTBUTTON = 0x0002

    WS_OVERLAPPED = 0x00000000
    CW_USEDEFAULT = 0x80000000 - 0x100000000
    IDI_APPLICATION = 32512

    ID_CONSOLE = 1001
    ID_GITHUB = 1002
    ID_EXIT = 1003

    ICON_ID = 1
    CLASS_NAME = "MusicTGNativeTrayWindow"

    def __init__(self, app: "Application", logger: logging.Logger | None = None) -> None:
        self.app = app
        self.logger = logger or logging.getLogger(__name__)
        self._thread: threading.Thread | None = None
        self._hwnd: int | None = None
        self._hicon: int | None = None
        self._hinstance: int | None = None
        self._wndproc = WNDPROC(self._window_proc)
        self._lock = threading.RLock()
        self._icon_added = False
        self._stopping = False

    async def start(self) -> None:
        with self._lock:
            if self._thread is not None:
                return
            self._stopping = False
            self._thread = threading.Thread(target=self._message_loop, name="MusicTGTray", daemon=False)
            self._thread.start()

    async def stop(self) -> None:
        thread: threading.Thread | None
        with self._lock:
            self._stopping = True
            hwnd = self._hwnd
            thread = self._thread

        self._delete_icon()
        if hwnd:
            user32.PostMessageW(hwnd, self.WM_CLOSE, 0, 0)
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            await asyncio.to_thread(thread.join)

    def refresh(self) -> None:
        hwnd = self._hwnd
        if hwnd:
            user32.PostMessageW(hwnd, self.WM_TRAYICON, 0, self.WM_CONTEXTMENU)

    def _message_loop(self) -> None:
        try:
            self._hinstance = kernel32.GetModuleHandleW(None)
            self._register_class()
            hwnd = user32.CreateWindowExW(
                0,
                self.CLASS_NAME,
                "MusicTG",
                self.WS_OVERLAPPED,
                self.CW_USEDEFAULT,
                self.CW_USEDEFAULT,
                self.CW_USEDEFAULT,
                self.CW_USEDEFAULT,
                None,
                None,
                self._hinstance,
                None,
            )
            if not hwnd:
                raise ctypes.WinError(ctypes.get_last_error())
            with self._lock:
                self._hwnd = hwnd
            self._add_icon(hwnd)
            self._pump_messages()
        except Exception:
            self.logger.exception("Native tray message loop failed")
            self._schedule_shutdown()
        finally:
            self._delete_icon()
            with self._lock:
                self._hwnd = None
                self._thread = None
                self._stopping = False

    def _register_class(self) -> None:
        wc = WNDCLASSW()
        wc.lpfnWndProc = self._wndproc
        wc.hInstance = self._hinstance
        wc.lpszClassName = self.CLASS_NAME
        atom = user32.RegisterClassW(ctypes.byref(wc))
        if not atom and ctypes.get_last_error() != 1410:
            raise ctypes.WinError(ctypes.get_last_error())

    def _pump_messages(self) -> None:
        msg = MSG()
        while True:
            result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if result == 0:
                break
            if result == -1:
                raise ctypes.WinError(ctypes.get_last_error())
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def _window_proc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        try:
            if msg == self.WM_TRAYICON:
                if lparam in (self.WM_RBUTTONUP, self.WM_LBUTTONUP, self.WM_CONTEXTMENU):
                    self._show_menu(hwnd)
                return 0
            if msg == self.WM_COMMAND:
                self._handle_command(wparam & 0xFFFF)
                return 0
            if msg == self.WM_CLOSE:
                self._delete_icon()
                user32.DestroyWindow(hwnd)
                return 0
            if msg == self.WM_DESTROY:
                self._delete_icon()
                user32.PostQuitMessage(0)
                return 0
        except Exception:
            self.logger.exception("Native tray window procedure failed")
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _add_icon(self, hwnd: int) -> None:
        icon = resource_path("icon.ico")


        self._hicon = user32.LoadImageW(
            None,
            icon,
            1,        
            0,
            0,
            0x10,     
        )
        if not self._hicon:
            raise ctypes.WinError(ctypes.get_last_error())

        data = self._notify_data(hwnd)
        data.uFlags = self.NIF_MESSAGE | self.NIF_ICON | self.NIF_TIP
        data.uCallbackMessage = self.WM_TRAYICON
        data.hIcon = self._hicon
        data.szTip = "MusicTG"
        if not shell32.Shell_NotifyIconW(self.NIM_ADD, ctypes.byref(data)):
            raise ctypes.WinError(ctypes.get_last_error())
        with self._lock:
            self._icon_added = True

    def _delete_icon(self) -> None:
        with self._lock:
            if not self._icon_added or not self._hwnd:
                return
            hwnd = self._hwnd
            self._icon_added = False
        data = self._notify_data(hwnd)
        if not shell32.Shell_NotifyIconW(self.NIM_DELETE, ctypes.byref(data)):
            self.logger.warning("Shell_NotifyIconW(NIM_DELETE) failed: %s", ctypes.get_last_error())

    def _notify_data(self, hwnd: int) -> NOTIFYICONDATAW:
        data = NOTIFYICONDATAW()
        data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        data.hWnd = hwnd
        data.uID = self.ICON_ID
        return data

    def _show_menu(self, hwnd: int) -> None:
        menu = user32.CreatePopupMenu()
        if not menu:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            console_text = "Close Console" if self.app.console_visible else "Open Console"
            user32.AppendMenuW(menu, self.MF_STRING, self.ID_CONSOLE, console_text)
            user32.AppendMenuW(menu, self.MF_STRING, self.ID_GITHUB, "GitHub")
            user32.AppendMenuW(menu, self.MF_SEPARATOR, 0, None)
            user32.AppendMenuW(menu, self.MF_STRING, self.ID_EXIT, "Exit")
            point = POINT()
            if not user32.GetCursorPos(ctypes.byref(point)):
                raise ctypes.WinError(ctypes.get_last_error())
            user32.SetForegroundWindow(hwnd)
            user32.TrackPopupMenu(menu, self.TPM_RIGHTBUTTON, point.x, point.y, 0, hwnd, None)
        finally:
            user32.DestroyMenu(menu)

    def _handle_command(self, command_id: int) -> None:
        if command_id == self.ID_CONSOLE:
            self._schedule(self._toggle_console())
        elif command_id == self.ID_GITHUB:
            self._open_github()
        elif command_id == self.ID_EXIT:
            self._schedule(self.app.shutdown())

    async def _toggle_console(self) -> None:
        if self.app.console_visible:
            self.app.hide_console()
        else:
            self.app.show_console()

    def _open_github(self) -> None:
        try:
            webbrowser.open("https://github.com/Mindcors/YaMusicTg")
        except Exception:
            self.logger.exception("Could not open GitHub URL")

    def _schedule(self, coroutine: object) -> None:
        loop = self.app.loop
        if loop is None or loop.is_closed():
            close = getattr(coroutine, "close", None)
            if callable(close):
                close()
            return
        future = asyncio.run_coroutine_threadsafe(coroutine, loop)
        future.add_done_callback(self._log_future_error)

    def _schedule_shutdown(self) -> None:
        with self._lock:
            if self._stopping:
                return
        self._schedule(self.app.shutdown())

    def _log_future_error(self, future: object) -> None:
        try:
            future.result()
        except Exception:
            self.logger.exception("Native tray callback failed")
