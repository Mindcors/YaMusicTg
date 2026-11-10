from __future__ import annotations

import asyncio
from telethon import functions
import logging
import msvcrt
import os
import re
import threading
import time
from pathlib import Path

from telethon import TelegramClient

from console_manager import ensure_console_width
from telethon.network.connection.tcpmtproxy import (
    ConnectionTcpMTProxyRandomizedIntermediate,
)
from telethon.errors import (
    FloodWaitError,
    PasswordHashInvalidError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
)

class TelegramProfile:
    def __init__(
        self,
        *,
        api_id: int | None = None,
        api_hash: str | None = None,
        session_name: str = "yamusictg",
        session_dir: Path | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.config = None
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_dir = session_dir or self._default_session_dir()
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_path = self.session_dir / session_name
        self.session_file = self.session_path.with_suffix(".session")
        self.client = None
        self._disconnect_lock = asyncio.Lock()
        self._flood_wait_until = 0.0
        self._deauthorized = False

    def flood_wait_remaining(self) -> float:
        return max(0.0, self._flood_wait_until - time.monotonic())

    def is_deauthorized(self) -> bool:
        return self._deauthorized

    async def set_about(self, text: str) -> bool:
        await self.connect()

        if not await self.client.is_user_authorized():
            self._deauthorized = True
            return False

        self._deauthorized = False

        try:
            await self.client(
                functions.account.UpdateProfileRequest(
                    about=text
                )
            )

            return True

        except FloodWaitError as e:
            self._flood_wait_until = time.monotonic() + e.seconds
            self.logger.warning(
                "FloodWait %s seconds while updating bio",
                e.seconds,
            )
            return False

        except Exception:
            self.logger.exception("Failed to update Telegram bio")
            return False

    @staticmethod
    def _default_session_dir() -> Path:
        path = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "YaMusicTG"
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def connect(self) -> None:
        if self.config is None:

            from settings import load_settings

            self.config = load_settings()

            if self.api_id is None:
                api_id = self.config.get("api_id")
                if api_id in (None, ""):
                    raise RuntimeError(
                        "Telegram API ID не настроен. "
                        "Удалите файл настроек и запустите "
                        "программу заново."
                    )
                self.api_id = int(api_id)

            if self.api_hash is None:
                self.api_hash = self.config["api_hash"]

            self.client = TelegramClient(
                str(self.session_path),
                self.api_id,
                self.api_hash,
                connection=ConnectionTcpMTProxyRandomizedIntermediate,
                proxy=(
                    self.config["proxy_host"],
                    self.config["proxy_port"],
                    self.config["proxy_secret"],
                ),
            )

        if not self.client.is_connected():

            try:
                await self.client.connect()

            except Exception:
                self.logger.exception("Telegram connection failed")
                raise

    async def is_authorized(self) -> bool:
        await self.connect()
        return await self.client.is_user_authorized()

    async def authorize_interactively(self) -> None:
        await self.connect()
        if await self.client.is_user_authorized():
            self.logger.info("Telegram session is already authorized")
            return

        if not await self._login_with_qr():
            await self._login_with_code()

        if not await self.client.is_user_authorized():
            raise RuntimeError("Авторизация в Telegram не завершена")
        self._deauthorized = False
        self.logger.info("Telegram authorization completed")

    async def _login_with_qr(self) -> bool:
        print()
        print("Авторизация через QR-код")
        print()

        try:
            import qrcode
        except ImportError:
            self.logger.error(
                "qrcode module is not installed; falling back to code login"
            )
            return False

        try:
            qr = await self.client.qr_login()
        except FloodWaitError:
            self.logger.exception(
                "Telegram flood wait while requesting QR token"
            )
            raise
        except Exception:
            self.logger.exception("QR login is unavailable")
            return False

        while True:
            self._render_qr(qr.url, qrcode)

            wait_task = asyncio.ensure_future(qr.wait())
            stop_watcher = threading.Event()
            cancel_task = asyncio.ensure_future(
                asyncio.to_thread(
                    self._watch_cancel_key, stop_watcher
                )
            )

            done, pending = await asyncio.wait(
                {wait_task, cancel_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            stop_watcher.set()

            for task in pending:
                task.cancel()

            if cancel_task in done and wait_task.cancelled():
                print("\033[2J\033[H", end="")
                print()
                print("Вход по QR-коду отменён.")
                print()
                return False

            try:
                await wait_task
            except asyncio.TimeoutError:
                try:
                    await qr.recreate()
                except FloodWaitError:
                    self.logger.exception(
                        "Telegram flood wait while refreshing QR"
                    )
                    raise
                except Exception:
                    self.logger.exception("QR refresh failed")
                    return False
                continue
            except SessionPasswordNeededError:
                print("\033[2J\033[H", end="")
                await self._prompt_2fa_password()
                return True
            except asyncio.CancelledError:
                return False
            except Exception:
                self.logger.exception("QR login failed")
                return False

            return True

    async def _prompt_2fa_password(self) -> None:
        print()
        print("Включена двухфакторная защита аккаунта.")
        print()

        for attempt in range(3):
            password = await self._read_password("Пароль 2FA Telegram: ")
            try:
                await self.client.sign_in(password=password)
                return
            except PasswordHashInvalidError:
                if attempt == 2:
                    self.logger.exception("Telegram 2FA password was invalid")
                    raise
                print("  \033[91m✗\033[0m Неверный пароль. Попробуйте ещё раз.")
            except FloodWaitError:
                self.logger.exception(
                    "Telegram flood wait while submitting 2FA password"
                )
                raise

    async def _login_with_code(self) -> None:
        print()
        print("Вход по номеру телефона")
        print()

        phone = await self._read_line("Номер телефона Telegram: ")
        phone = self._normalize_phone(phone)
        try:
            sent_code = await self.client.send_code_request(phone)
        except FloodWaitError:
            self.logger.exception("Telegram flood wait while requesting login code")
            raise
        except Exception:
            self.logger.exception("Could not request Telegram login code")
            raise

        for attempt in range(3):
            code = await self._read_password("Код входа Telegram: ")
            try:
                await self.client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=sent_code.phone_code_hash,
                )
                break
            except PhoneCodeInvalidError:
                if attempt == 2:
                    self.logger.exception("Telegram login code was invalid")
                    raise
                print("  \033[91m✗\033[0m Неверный код. Попробуйте ещё раз.")
            except PhoneCodeExpiredError:
                self.logger.exception("Telegram login code expired")
                raise
            except FloodWaitError:
                self.logger.exception("Telegram flood wait while signing in")
                raise
            except SessionPasswordNeededError:
                await self._prompt_2fa_password()
                break
            except Exception:
                self.logger.exception("Telegram sign-in failed")
                raise

    async def start_authorized(self) -> None:
        await self.connect()
        if not await self.client.is_user_authorized():
            raise RuntimeError("Клиент Telegram не авторизован")
        self._deauthorized = False
        self.logger.info("Telegram client is ready")

    async def disconnect(self) -> None:
        async with self._disconnect_lock:
            if self.client is not None and self.client.is_connected():
                await self.client.disconnect()
                self.logger.info("Telegram client disconnected")

    @staticmethod
    def _normalize_phone(raw: str) -> str:
        digits = re.sub(r"\D", "", raw)

        if len(digits) == 11 and digits[0] in ("7", "8"):
            digits = "7" + digits[1:]

        return "+" + digits

    @staticmethod
    def _render_qr(url: str, qrcode_module) -> None:
        code = qrcode_module.QRCode(
            border=1,
            error_correction=qrcode_module.constants.ERROR_CORRECT_L,
        )
        code.add_data(url)
        code.make(fit=True)

        ensure_console_width((code.modules_count + 2) * 2 + 4)

        print("\033[2J\033[H", end="")
        print("Отсканируйте этот QR-код в приложении Telegram:")
        print("Настройки → Устройства → Подключить устройство.")
        print()
        code.print_ascii(invert=True)
        print()
        print("Нажмите Esc для входа по номеру телефона и коду.")
        print()

    @staticmethod
    def _watch_cancel_key(stop: threading.Event) -> None:
        time.sleep(0.3)

        while not stop.is_set():
            if msvcrt.kbhit():
                ch = msvcrt.getwch()

                if ch == "\x1b":
                    return

                if ch in ("\x00", "\xe0"):
                    msvcrt.getwch()

            time.sleep(0.05)

    @staticmethod
    async def _read_line(prompt: str) -> str:
        return (await asyncio.to_thread(input, prompt)).strip()

    @staticmethod
    async def _read_password(prompt: str) -> str:
        return (
            await asyncio.to_thread(TelegramProfile._read_password_sync, prompt)
        ).strip()

    @staticmethod
    def _read_password_sync(prompt: str) -> str:
        print(prompt, end="", flush=True)

        chars = []

        while True:
            ch = msvcrt.getwch()

            if ch in ("\r", "\n"):
                print()
                break

            if ch == "\x03":
                raise KeyboardInterrupt

            if ch in ("\x00", "\xe0"):
                msvcrt.getwch()
                continue

            if ch in ("\x08", "\x7f"):
                if chars:
                    chars.pop()
                    print("\b \b", end="", flush=True)
                continue

            chars.append(ch)

        return "".join(chars)
