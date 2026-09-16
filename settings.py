from __future__ import annotations

import json
import os
from pathlib import Path

APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "YaMusicTG"
APP_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = APP_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "api_id": None,
    "api_hash": "",
    "proxy_host": "127.0.0.1",
    "proxy_port": 1080,
    "proxy_secret": "",
    "check_interval": 5,
}


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

        else:

            self.first_setup()

        return self.data

    def first_setup(self):

        import webbrowser

        print()
        print("=" * 42)
        print("          YaMusicTG First Setup")
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

        api_id = int(
            input("Telegram API ID: ").strip()
        )

        api_hash = input(
            "Telegram API HASH: "
        ).strip()

        print()
        print("=" * 42)
        print("MTProto Proxy")
        print("=" * 42)
        print()
        print("Введите Secret вашего MTProto Proxy.")
        print("Если вы используете локальный прокси,")
        print("обычно он начинается с dd...")
        print()

        secret = input(
            "MTProto Secret: "
        ).strip()

        self.data = DEFAULT_SETTINGS.copy()

        self.data["api_id"] = api_id
        self.data["api_hash"] = api_hash
        self.data["proxy_secret"] = secret

        self.save()

        print()
        print("=" * 42)
        print("Настройка завершена!")
        print()
        print(f"Файл настроек сохранён:")
        print(SETTINGS_FILE)
        print()
        print("При следующем запуске")
        print("вводить данные больше не потребуется.")
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