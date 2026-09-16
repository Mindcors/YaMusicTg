
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)


class MusicDetector:

    YANDEX_SOURCES = (
        "ru.yandex.desktop.music",
        "YandexMusic",
        "Яндекс Музыка",
    )

    def __init__(self):
        self.manager = None

    async def connect(self):
        self.manager = await MediaManager.request_async()

    async def reconnect(self):
        await self.connect()

    async def _session(self):

        if self.manager is None:
            await self.connect()

        for session in self.manager.get_sessions():

            try:

                app = (
                    session.source_app_user_model_id or ""
                ).lower()

                if any(
                    source.lower() in app
                    for source in self.YANDEX_SOURCES
                ):
                    return session

            except Exception:
                pass

        return None

    async def get_track(self):
        session = await self._session()

        if session is None:
            return None

        try:
            props = await session.try_get_media_properties_async()
            playback = session.get_playback_info()

            playing = (
                playback.playback_status ==
                PlaybackStatus.PLAYING
            )
            title = (props.title or "").strip()
            artist = (props.artist or "").strip()

            bad_words = (
                "сегодня",
                "вчера",
                "голосовое",
                "voice",
                "index.html",
                "program files",
                "nvfile",
            )

            text = f"{artist} {title}".lower()

            if any(word in text for word in bad_words):
                return None

            return {
                "playing": playing,
                "title": (props.title or "").strip(),
                "artist": (props.artist or "").strip(),
                "album": (props.album_title or "").strip(),
                "source": session.source_app_user_model_id,
            }

        except Exception:
            return None
