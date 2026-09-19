from __future__ import annotations

import json
import os
import webbrowser
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

            with SETTINGS_FILE.open(
                "r",
                encoding="utf-8",
            ) as f:
                self.data = json.load(f)

            changed = False

            for key, value in DEFAULT_SETTINGS.items():
                if key not in self.data:
                    self.data[key] = value
                    changed = True

            if changed:
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
            f"Secret: {self.data['proxy_secret']}"
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

        with SETTINGS_FILE.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                self.data,
                f,
                indent=4,
                ensure_ascii=False,
            )


def load_settings():
    return Settings().load()