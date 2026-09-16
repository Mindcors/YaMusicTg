from __future__ import annotations

import json
import re
import urllib.request


VERSION = "1.0.0"

GITHUB_API_URL = (
    "https://api.github.com/repos/Mindcors/YaMusicTg/releases/latest"
)


def _parse_version(version: str) -> tuple[int, ...]:
    version = version.strip().lower().lstrip("v")

    match = re.match(r"^(\d+(?:\.\d+)*)", version)

    if not match:
        raise ValueError(f"Invalid version: {version}")

    return tuple(
        int(part)
        for part in match.group(1).split(".")
    )


def check_for_updates() -> None:

    print(f"YaMusicTG v{VERSION}")
    print("Checking for updates...")

    try:

        request = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "User-Agent": "YaMusicTG",
                "Accept": "application/vnd.github+json",
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=5,
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        latest_version = data.get("tag_name", "").strip()

        if not latest_version:
            raise RuntimeError(
                "GitHub release does not contain a version tag"
            )

        current = _parse_version(VERSION)
        latest = _parse_version(latest_version)

        if latest > current:

            print()
            print(
                "\033[93m"
                "[YaMusicTG] New version available!"
                "\033[0m"
            )

            print(
                f"Current version: v{VERSION}"
            )

            print(
                f"Latest version:  {latest_version}"
            )

            print(
                "Download: "
                "https://github.com/Mindcors/YaMusicTg/releases/latest"
            )

        else:

            print(
                f"YaMusicTG is up to date (v{VERSION})."
            )

    except Exception as e:

        print(
            f"\033[91m"
            f"[YaMusicTG] Update check failed: {e}"
            f"\033[0m"
        )