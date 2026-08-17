import asyncio

from backend.app.gemini import health_check


async def main():
    print("Testing Gemini backend...")

    result = await health_check()

    print(result)


if __name__ == "__main__":
    asyncio.run(main())