# YaMusicTG

<div align="center">

**Небольшое Windows-приложение, которое автоматически отображает текущий трек из Яндекс Музыки в описании профиля Telegram.**

![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-Source--Available-orange?style=for-the-badge)

</div>

---

## О проекте

**YaMusicTG** работает в фоне и получает информацию о воспроизводимом треке через Windows Global System Media Transport Controls. Как только трек обнаружен — его название и исполнитель автоматически устанавливаются в bio профиля Telegram.

---

## Возможности

- Отображение текущего трека Яндекс Музыки в Telegram bio
- Автоматическое обновление при смене трека
- Очистка bio при паузе или остановке воспроизведения
- Авторизация через Telegram API ID и API Hash
- Работа через MTProto Proxy
- Фоновый режим через системный трей Windows
- Локальное хранение настроек и сессии
- Запуск из исходников или в виде `.exe`

---

## Требования

| Компонент | Описание |
|:---------:|:---------|
| **ОС** | Windows 10/11 |
| **Python** | 3.12 (для запуска из исходников) |
| **API** | Telegram API ID и API Hash |
| **Плеер** | Яндекс Музыка или другой с поддержкой Windows Media Session API |

---

## Установка из исходников

**1. Клонируйте репозиторий:**

```bash
git clone <REPOSITORY_URL>
cd YaMusicTG
```

**2. Установите зависимости:**

```bash
py -3.12 -m pip install telethon winsdk pyinstaller python-socks
```

**3. Запустите приложение:**

```bash
py -3.12 app.py
```

> При первом запуске программа запросит **Telegram API ID**, **API Hash** и **MTProto Proxy Secret**.

Все данные сохраняются в `%LOCALAPPDATA%\YaMusicTG\` — там же хранятся сессия Telegram и лог.

---

## Сборка `.exe`

Установите PyInstaller:

```bash
py -3.12 -m pip install pyinstaller
```

Соберите приложение:

```bash
py -3.12 -m PyInstaller --onefile --windowed --clean --noconfirm --name YaMusicTG --icon=icon.ico --add-data "icon.ico;." --hidden-import pystray --hidden-import PIL --hidden-import PIL.Image --hidden-import PIL.ImageDraw --collect-all pystray main.py
```

Готовый файл появится в:

```text
dist\YaMusicTG.exe
```

Если есть `.spec` файл:

```bash
py -3.12 -m PyInstaller YaMusicTG.spec
```

---

## Конфигурация

| Файл | Путь |
|:----:|:-----|
| Настройки | `%LOCALAPPDATA%\YaMusicTG\settings.json` |
| Сессия | `%LOCALAPPDATA%\YaMusicTG\musictg.session` |
| Лог | `%LOCALAPPDATA%\YaMusicTG\YaMusicTG.log` |

---

## MTProto Proxy

Приложению необходимо подключение к Telegram через MTProto Proxy. Параметры задаются при первом запуске. 

---

## Структура проекта

```text
YaMusicTG/
├── app.py
├── telegram_client.py
├── music_detector.py
├── tray.py
├── console_manager.py
├── settings.py
├── version.py
├── icon.ico
└── ...
```

### Основные модули

| Модуль | Назначение |
|:------:|:-----------|
| **`app.py`** | Основной цикл приложения и обновление Telegram bio |
| **`telegram_client.py`** | Взаимодействие с Telegram через Telethon |
| **`music_detector.py`** | Получение трека через Windows Media Session API |
| **`tray.py`** | Системный трей Windows |
| **`console_manager.py`** | Управление консольным окном |
| **`settings.py`** | Загрузка и сохранение настроек |
| **`version.py`** | Проверка и обновление версии |

---

## Лицензия

Проект распространяется по собственной **Source-Available Non-Commercial License**.

Исходный код можно просматривать, изменять, форкать и использовать в некоммерческих целях. **Коммерческое использование без разрешения правообладателя запрещено.**

- [LICENSE](https://github.com/Mindcors/YaMusicTg/blob/main/LICENSE.md)
- Contributions — согласно [CLA](https://github.com/Mindcors/YaMusicTg/blob/main/CLA.md)
