from __future__ import annotations

import asyncio
from telethon import functions
import getpass
import logging
import os
from pathlib import Path

from telethon import TelegramClient
from telethon.network.connection.tcpmtproxy import (
    ConnectionTcpMTProxyRandomizedIntermediate,
)
from telethon.errors import (
    FloodWaitError,
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
    async def set_about(self, text: str) -> bool:
        await self.connect()

        if not await self.client.is_user_authorized():
            return False

        try:
            await self.client(
                functions.account.UpdateProfileRequest(
                    about=text
                )
            )

            return True

        except FloodWaitError as e:
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

    def has_session(self) -> bool:
        return self.session_file.exists()

    async def connect(self) -> None:
        
        if self.config is None:

            from settings import load_settings

            self.config = load_settings()

            if self.api_id is None:
                self.api_id = int(self.config["api_id"])

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

        phone = await self._read_line("Telegram phone number: ")
        try:
            sent_code = await self.client.send_code_request(phone)
        except FloodWaitError:
            self.logger.exception("Telegram flood wait while requesting login code")
            raise
        except Exception:
            self.logger.exception("Could not request Telegram login code")
            raise

        for attempt in range(3):
            code = await self._read_line("Telegram login code: ")
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
                print("Invalid code. Please try again.")
            except PhoneCodeExpiredError:
                self.logger.exception("Telegram login code expired")
                raise
            except FloodWaitError:
                self.logger.exception("Telegram flood wait while signing in")
                raise
            except SessionPasswordNeededError:
                password = await self._read_password("Telegram 2FA password: ")
                try:
                    await self.client.sign_in(password=password)
                except FloodWaitError:
                    self.logger.exception("Telegram flood wait while submitting 2FA password")
                    raise
                except Exception:
                    self.logger.exception("Telegram 2FA sign-in failed")
                    raise
                break
            except Exception:
                self.logger.exception("Telegram sign-in failed")
                raise

        if not await self.client.is_user_authorized():
            raise RuntimeError("Telegram authorization did not complete")
        self.logger.info("Telegram authorization completed")

    async def start_authorized(self) -> None:
        await self.connect()
        if not await self.client.is_user_authorized():
            raise RuntimeError("Telegram client is not authorized")
        self.logger.info("Telegram client is ready")

    async def disconnect(self) -> None:
        async with self._disconnect_lock:
            if self.client.is_connected():
                await self.client.disconnect()
                self.logger.info("Telegram client disconnected")

    def raw_client(self) -> TelegramClient:
        return self.client

    @staticmethod
    async def _read_line(prompt: str) -> str:
        return (await asyncio.to_thread(input, prompt)).strip()

    @staticmethod
    async def _read_password(prompt: str) -> str:
        return await asyncio.to_thread(getpass.getpass, prompt)
