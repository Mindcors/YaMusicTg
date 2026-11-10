from __future__ import annotations

import base64
import ctypes
import json
import os
import subprocess
import webbrowser
from ctypes import wintypes
from pathlib import Path
from urllib.parse import parse_qs, urlparse


APP_DIR = Path(
    os.environ.get("LOCALAPPDATA", Path.home())
) / "YaMusicTG"

APP_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

SETTINGS_FILE = APP_DIR / "settings.json"


DEFAULT_SETTINGS = {
    "api_id": None,
    "api_hash": "",
    "proxy_host": "127.0.0.1",
    "proxy_port": 1080,
    "proxy_secret": "",
    "check_interval": 5,
}


_ENCRYPTED_PREFIX = "dpapi:"

_SENSITIVE_KEYS = (
    "api_id",
    "api_hash",
    "proxy_host",
    "proxy_port",
    "proxy_secret",
)


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _dpapi_protect(data: bytes) -> bytes:
    buffer = ctypes.create_string_buffer(data, len(data))
    blob_in = _DATA_BLOB(
        len(data),
        ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)),
    )
    blob_out = _DATA_BLOB()

    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(blob_in),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(blob_out),
    )

    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def _dpapi_unprotect(data: bytes) -> bytes:
    buffer = ctypes.create_string_buffer(data, len(data))
    blob_in = _DATA_BLOB(
        len(data),
        ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)),
    )
    blob_out = _DATA_BLOB()

    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(blob_in),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(blob_out),
    )

    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def _encrypt_value(value) -> str:
    raw = str(value).encode("utf-8")
    encoded = base64.b64encode(_dpapi_protect(raw)).decode("ascii")
    return _ENCRYPTED_PREFIX + encoded


def _decrypt_value(value: str) -> str:
    raw = base64.b64decode(value[len(_ENCRYPTED_PREFIX):])
    return _dpapi_unprotect(raw).decode("utf-8")


def _restrict_acl(path: Path) -> None:
    user = os.environ.get("USERNAME", "")
    if not user:
        return

    try:
        subprocess.run(
            [
                "icacls",
                str(path),
                "/inheritance:r",
                "/grant:r",
                f"{user}:(OI)(CI)F",
                "SYSTEM:(OI)(CI)F",
                "/c",
            ],
            check=False,
            capture_output=True,
        )
    except Exception:
        pass


_restrict_acl(APP_DIR)


def parse_proxy_link(link: str) -> tuple[str, int, str]:

    link = link.strip()

    if not link:
        raise ValueError("Ссылка не может быть пустой")

    parsed = urlparse(link)

    if parsed.scheme.lower() != "tg" or parsed.netloc.lower() != "proxy":
        raise ValueError(
            "Неверная ссылка. Используйте ссылку вида:\n"
            "tg://proxy?server=...&port=...&secret=..."
        )

    params = parse_qs(parsed.query)

    server = params.get("server", [None])[0]
    port = params.get("port", [None])[0]
    secret = params.get("secret", [None])[0]

    if not server:
        raise ValueError(
            "В ссылке отсутствует параметр server"
        )

    if not port:
        raise ValueError(
            "В ссылке отсутствует параметр port"
        )

    if not secret:
        raise ValueError(
            "В ссылке отсутствует параметр secret"
        )

    try:
        port = int(port)
    except (TypeError, ValueError):
        raise ValueError(
            "Порт должен быть числом"
        )

    if not 1 <= port <= 65535:
        raise ValueError(
            "Некорректный порт. Допустимый диапазон: 1-65535"
        )

    return server, port, secret


class Settings:

    def __init__(self):
        self.data = {}

    def load(self):

        if SETTINGS_FILE.exists():

            try:
                with SETTINGS_FILE.open(
                    "r",
                    encoding="utf-8",
                ) as f:
                    self.data = json.load(f)
            except PermissionError:
                raise RuntimeError(
                    "Нет доступа к файлу настроек. Вероятно, папка "
                    f"{APP_DIR} скопирована с другого компьютера. "
                    "Удалите эту папку и настройте программу заново."
                )

            changed = False

            for key, value in DEFAULT_SETTINGS.items():
                if key not in self.data:
                    self.data[key] = value
                    changed = True

            migrated = False

            for key in _SENSITIVE_KEYS:
                if key not in self.data:
                    continue

                value = self.data[key]

                if (
                    isinstance(value, str)
                    and value.startswith(_ENCRYPTED_PREFIX)
                ):
                    try:
                        self.data[key] = _decrypt_value(value)
                    except Exception:
                        raise RuntimeError(
                            "Не удалось расшифровать файл настроек. "
                            "Удалите settings.json и настройте "
                            "программу заново."
                        )
                else:
                    migrated = True

            api_id = self.data.get("api_id")
            self.data["api_id"] = (
                int(api_id) if api_id not in (None, "") else None
            )

            proxy_port = self.data.get("proxy_port")
            self.data["proxy_port"] = (
                int(proxy_port)
                if proxy_port not in (None, "")
                else DEFAULT_SETTINGS["proxy_port"]
            )

            if migrated or changed:
                self.save()

        else:
            self.first_setup()

        return self.data

    def first_setup(self):

        print()
        print("=" * 42)
        print("          YaMusicTG Первая настройка")
        print("=" * 42)
        print()

        print("Для работы программы необходим Telegram API.")
        print()

        print("Если у вас его нет, сейчас откроется сайт")
        print("my.telegram.org")
        print()

        input("Нажмите Enter для продолжения...")

        webbrowser.open("https://my.telegram.org")

        print()
        print("=" * 42)
        print("Получение API")
        print("=" * 42)
        print()

        print("1. Войдите в свой Telegram аккаунт.")
        print("2. Нажмите 'API development tools'.")
        print("3. Создайте приложение.")
        print("4. Скопируйте API ID и API HASH.")
        print()

        while True:

            try:
                api_id = int(
                    input("Telegram API ID: ").strip()
                )

                if api_id <= 0:
                    raise ValueError

                break

            except ValueError:
                print()
                print("Ошибка: API ID должен быть числом.")
                print()

        api_hash = input(
            "Telegram API HASH: "
        ).strip()

        while True:

            print()
            print("=" * 42)
            print("MTProto Proxy")
            print("=" * 42)
            print()

            print(
                "Вставьте ссылку TG WS Proxy."
            )
            print()

            print("Пример:")
            print(
                "tg://proxy?"
                "server=127.0.0.1"
                "&port=1443"
                "&secret=ddd6fb406614df81c526cb6c1dfca5c3ae"
            )
            print()

            proxy_link = input(
                "Ссылка на прокси: "
            ).strip()

            try:

                proxy_host, proxy_port, proxy_secret = (
                    parse_proxy_link(proxy_link)
                )

                break

            except ValueError as e:

                print()
                print(
                    f"Ошибка: {e}"
                )
                print()
                print(
                    "Попробуйте вставить ссылку ещё раз."
                )
                print()

        self.data = DEFAULT_SETTINGS.copy()

        self.data["api_id"] = api_id
        self.data["api_hash"] = api_hash

        self.data["proxy_host"] = proxy_host
        self.data["proxy_port"] = proxy_port
        self.data["proxy_secret"] = proxy_secret

        self.save()

        print()
        print("=" * 42)
        print("Настройка завершена!")
        print("=" * 42)
        print()

        print("Параметры прокси:")

        print(
            f"Server: {self.data['proxy_host']}"
        )

        print(
            f"Port:   {self.data['proxy_port']}"
        )

        print(
            "Secret: "
            + "*" * len(str(self.data["proxy_secret"]))
        )

        print()

        print("Файл настроек сохранён:")

        print(
            SETTINGS_FILE
        )

        print()

        print(
            "При следующем запуске "
            "вводить данные больше не потребуется."
        )

        print()

        print("=" * 42)
        print()

    def save(self):

        payload = {}

        for key, value in self.data.items():
            if key in _SENSITIVE_KEYS and value is not None:
                payload[key] = _encrypt_value(value)
            else:
                payload[key] = value

        try:
            with SETTINGS_FILE.open(
                "w",
                encoding="utf-8",
            ) as f:

                json.dump(
                    payload,
                    f,
                    indent=4,
                    ensure_ascii=False,
                )
        except PermissionError:
            raise RuntimeError(
                "Нет доступа к файлу настроек. Вероятно, папка "
                f"{APP_DIR} скопирована с другого компьютера. "
                "Удалите эту папку и настройте программу заново."
            )


def load_settings():
    return Settings().load()
