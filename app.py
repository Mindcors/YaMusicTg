from __future__ import annotations

import asyncio
import concurrent.futures
import inspect
import logging
import os
import sys
import time
from settings import load_settings
from version import check_for_updates
from collections.abc import Awaitable, Callable, Coroutine
from pathlib import Path
from typing import TypeVar

from console_manager import ConsoleManager
from music_detector import MusicDetector
from telegram_client import TelegramProfile
from tray import TrayIcon


T = TypeVar("T")


class Application:

    def __init__(self) -> None:
        self.loop: asyncio.AbstractEventLoop | None = None

        self.logger = self._create_logger()

        self.console = ConsoleManager("YaMusicTG")

        self.telegram = TelegramProfile(
            logger=self.logger.getChild("telegram")
        )

        self.detector = MusicDetector()

        self.tray = TrayIcon(
            self,
            logger=self.logger.getChild("tray"),
        )

        self._shutdown_event: asyncio.Event | None = None
        self._shutdown_lock: asyncio.Lock | None = None

        self._tasks: set[asyncio.Task] = set()

        self._console_visible = False

        self._last_status: str = ""
        self._last_update = 0.0
        self._status_sent = True
        self.settings = None

    @property
    def console_visible(self) ->bool:
        return self._console_visible

    async def run(self):
        self.logger.info("Application started")

        self.show_console()
        self._print_header()

        self.settings = load_settings()
        check_for_updates()
        self._print_separator()

        self.loop = asyncio.get_running_loop()
        self._shutdown_event = asyncio.Event()
        self._shutdown_lock = asyncio.Lock()

        try:
            try:
                await self._start_telegram()

                self.logger.info("Telegram ready")
                self._print_separator()

                await self.detector.connect()
                self.logger.info("Music detector connected")
                self._print_section_ok("Музыкальный монитор", "Подключение к Media Session установлено")

                await self.tray.start()
                self.logger.info("Tray started")

                self.create_task(
                    self._status_loop(),
                    name="StatusLoop",
                )

                await self._shutdown_event.wait()

            except Exception as e:
                self.logger.exception("Application startup failed")

                print()
                print("\033[91m✗ Не удалось запустить программу\033[0m")
                print(f"Ошибка: {e}")
                print()
                print("Консоль останется открытой для просмотра ошибки.")
                print()

                await asyncio.to_thread(
                    input,
                    "Нажмите Enter для выхода... "
                )

        finally:
            await self._cancel_tasks()

    async def _start_telegram(self):
        self.show_console()

        self._print_section("Подключение к Telegram")
        print("Подключение...", end=" ", flush=True)
        await self.telegram.connect()
        print("\033[92m✓\033[0m")

        print("Проверка авторизации...", end=" ", flush=True)
        authorized = await self.telegram.is_authorized()
        print("\033[92m✓\033[0m")

        if not authorized:
            self.show_console()
            print()
            print("Требуется авторизация.")
            print()

            try:
                await self.telegram.authorize_interactively()
            finally:
                self.hide_console()

        await self.telegram.start_authorized()

        print("Telegram готов к работе \033[92m✓\033[0m")
        await asyncio.sleep(3)
        self.hide_console()

    def _print_header(self):
        width = 46
        title = "YaMusicTG"
        version = f"v{self._version()}"

        print()
        print(f"\033[96m╭{'─' * width}╮\033[0m")
        print(f"\033[96m│\033[0m{title:^{width}}\033[96m│\033[0m")
        print(f"\033[96m│\033[0m{version:^{width}}\033[96m│\033[0m")
        print(f"\033[96m╰{'─' * width}╯\033[0m")
        print()

    @staticmethod
    def _version():
        try:
            from version import VERSION
            return VERSION
        except Exception:
            return "?"

    @staticmethod
    def _print_separator():
        print()
        print("\033[90m──────────────────────────────────────────────────\033[0m")
        print()

    @staticmethod
    def _print_section(title):
        print(f"\033[96m{title}\033[0m")

    @staticmethod
    def _print_section_ok(title, message):
        print(f"\033[96m{title}\033[0m")
        print(f"\033[92m✓\033[0m {message}")

    async def _status_loop(self):

        self.logger.info("Status loop started")
        print("Waiting for music...")

        while True:

            try:

                track = await self.detector.get_track()

                status = self.build_status(track)

                now = time.monotonic()

                if status != self._last_status:

                    self._last_status = status
                    self._last_update = now
                    self._status_sent = False

                if (
                    not self._status_sent
                    and now - self._last_update >= self.settings["check_interval"]
                ):

                    ok = await self.telegram.set_about(status)

                    if ok:

                        if status:
                            print(f"\033[91m[YaMusicTG]\033[0m Telegram bio updated: {status}")
                        else:
                            print("\033[91m[YaMusicTG]\033[0m Telegram bio cleared")

                        self._status_sent = True

                await asyncio.sleep(0.5)

            except asyncio.CancelledError:

                raise

            except Exception:

                self.logger.exception(
                    "Status loop failed"
                )

                await asyncio.sleep(5)

    async def shutdown(self):

        if self._shutdown_lock is None:
            return

        async with self._shutdown_lock:

            if self._shutdown_event is None:
                return

            if self._shutdown_event.is_set():
                return

            try:
                await self.telegram.disconnect()
            except Exception:
                self.logger.exception("Telegram disconnect")

            try:
                await self.tray.stop()
            except Exception:
                self.logger.exception("Tray stop")

            try:
                self.console.destroy()
            except Exception:
                self.logger.exception("Console destroy")

            await self._cancel_tasks()

            self._shutdown_event.set()

    def create_task(
        self,
        coroutine: Coroutine,
        name: str,
    ):

        task = asyncio.create_task(
            coroutine,
            name=name,
        )

        self._tasks.add(task)

        task.add_done_callback(
            self._task_done
        )

        return task

    def _task_done(self, task):

        self._tasks.discard(task)

        try:

            task.result()

        except asyncio.CancelledError:

            pass

        except Exception:

            self.logger.exception(
                "Background task crashed"
            )

            self.request_shutdown()

    async def _cancel_tasks(self):

        current = asyncio.current_task()

        tasks = [
            t
            for t in self._tasks
            if t is not current
        ]

        self._tasks.clear()

        for task in tasks:
            task.cancel()

        if tasks:
            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

    def request_shutdown(self):

        if self.loop is None:
            return

        asyncio.run_coroutine_threadsafe(
            self.shutdown(),
            self.loop,
        )

    def show_console(self):

        self.console.show()

        self._console_visible = True

    def hide_console(self):

        self.console.hide()

        self._console_visible = False

    @staticmethod
    def build_status(track):

        if track is None:
            return ""

        if not track["playing"]:
            return ""

        artist = track["artist"].strip()

        title = track["title"].strip()

        if artist:
            text = f"🎵 {artist} — {title}"
        else:
            text = f"🎵 {title}"

        return text[:70]

    @staticmethod
    def _create_logger():

        path = (
            Path(
                os.environ.get("LOCALAPPDATA", Path.home())
            )
            / "YaMusicTG"
        )

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        logging.basicConfig(
            filename=path / "YaMusicTG.log",
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            encoding="utf-8",
        )

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        logger = logging.getLogger("MusicTG")
        logger.setLevel(logging.INFO)
        return logger