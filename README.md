````markdown
# YaMusicTG

YaMusicTG — небольшое Windows-приложение, которое автоматически отображает текущий трек из Яндекс Музыки в описании (bio) профиля Telegram.

Программа работает в фоне и получает информацию о воспроизводимом треке через Windows Global System Media Transport Controls. После обнаружения трека его название и исполнитель устанавливаются в описание профиля Telegram.

## Возможности

- Отображение текущего трека Яндекс Музыки в Telegram bio.
- Автоматическое обновление информации при смене трека.
- Очистка bio при остановке или паузе воспроизведения.
- Работа через MTProto Proxy.
- Авторизация Telegram через API ID и API Hash.
- Работа в фоне через системный трей Windows.
- Хранение настроек и сессии локально.
- Поддержка запуска из исходного кода и в виде `.exe`.

## Требования

- Windows 10/11
- Python 3.12 — для запуска из исходного кода
- Аккаунт Telegram
- Telegram API ID и API Hash
- Яндекс Музыка или другой медиаплеер, поддерживающий Windows Media Session API

## Установка из исходников

Клонируйте репозиторий:

```bash
git clone <REPOSITORY_URL>
cd YaMusicTG
````

Установите зависимости:

```bash
py -3.12 -m pip install telethon winsdk pyinstaller
```

После этого программу можно запустить:

```bash
py -3.12 app.py
```

При первом запуске программа запросит:

* Telegram API ID
* Telegram API Hash
* MTProto Proxy Secret

Настройки сохраняются в:

```text
%LOCALAPPDATA%\YaMusicTG\
```

В этой директории также хранится Telegram-сессия и файл журнала.

## Сборка

Для создания самостоятельного `.exe` используется PyInstaller.

Установка PyInstaller:

```bash
py -3.12 -m pip install pyinstaller
```

Сборка:

```bash
py -3.12 -m PyInstaller --onefile --windowed --name YaMusicTG --icon icon.ico app.py
```

После успешной сборки исполняемый файл будет находиться в:

```text
dist\YaMusicTG.exe
```

Если в проекте используется `.spec` файл, сборку можно выполнить командой:

```bash
py -3.12 -m PyInstaller YaMusicTG.spec
```

## Конфигурация

Основные настройки хранятся в:

```text
%LOCALAPPDATA%\YaMusicTG\settings.json
```

Telegram-сессия:

```text
%LOCALAPPDATA%\YaMusicTG\musictg.session
```

Лог программы:

```text
%LOCALAPPDATA%\YaMusicTG\YaMusicTG.log
```

## MTProto Proxy

YaMusicTG поддерживает подключение к Telegram через MTProto Proxy.

Параметры прокси задаются в настройках приложения. По умолчанию используется:

```text
Host: 127.0.0.1
Port: 1080
```

Secret указывается пользователем при первоначальной настройке.

## Структура проекта

```text
YaMusicTG/
├── app.py
├── telegram_client.py
├── music_detector.py
├── tray.py
├── console_manager.py
├── settings.py
├── icon.ico
└── ...
```

### Основные модули

**`app.py`** — основной цикл приложения и обновление Telegram bio.

**`telegram_client.py`** — подключение и взаимодействие с Telegram через Telethon.

**`music_detector.py`** — получение информации о текущем воспроизводимом треке через Windows Media Session API.

**`tray.py`** — системный трей Windows.

**`console_manager.py`** — управление консольным окном приложения.

**`settings.py`** — загрузка и сохранение настроек.

## Лицензия

Проект распространяется по собственной Source-Available Non-Commercial License.

Исходный код можно просматривать, изменять, форкать и использовать в некоммерческих целях. Коммерческое использование без отдельного разрешения правообладателя запрещено.

См. [LICENSE](https://github.com/Mindcors/YaMusicTg/blob/main/LICENSE.md) файл с полными условиями лицензии.

Contributions предоставляются в соответствии с [CLA](https://github.com/Mindcors/YaMusicTg/blob/main/CLA.md).
