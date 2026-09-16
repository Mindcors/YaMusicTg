
from __future__ import annotations

from datetime import datetime
import threading
import logging
import os
from pathlib import Path

APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "YaMusicTG"
APP_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = APP_DIR / "YaMusicTG.log"

class Logger:

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = APP_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.console_callback = None

    def set_console_callback(self, callback):
        self.console_callback = callback

    @property
    def logfile(self) -> Path:
        return self.log_dir / f"{datetime.now():%Y-%m-%d}.log"

    def _write(self, level: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] [{level}] {message}"

        with self._lock:
            print(line)

            with self.logfile.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

            if self.console_callback:
                try:
                    self.console_callback(line)
                except Exception:
                    pass

    def info(self, message: str):
        self._write("INFO", message)

    def warning(self, message: str):
        self._write("WARNING", message)

    def error(self, message: str):
        self._write("ERROR", message)

    def exception(self, exc: Exception):
        self._write("EXCEPTION", f"{type(exc).__name__}: {exc}")

    def separator(self):
        self._write("INFO", "-" * 60)

    def clear_old_logs(self, keep_days: int = 30):
        now = datetime.now()

        for file in self.log_dir.glob("*.log"):
            try:
                age = (now - datetime.fromtimestamp(file.stat().st_mtime)).days
                if age > keep_days:
                    file.unlink()
            except Exception:
                pass


logger = Logger()
