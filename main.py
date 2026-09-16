import asyncio

from app import Application


async def main() -> None:
    app = Application()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
