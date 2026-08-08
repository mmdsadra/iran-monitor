import asyncio

from iran_monitor.collectors.telegram_auth import (
    create_telegram_client,
)
from iran_monitor.config.environment import load_environment


async def main() -> None:
    load_environment()

    client = create_telegram_client()

    print("Starting Telegram authentication...")
    print("Telegram will ask for your phone number and code.")

    async with client:
        me = await client.get_me()

        if me is None:
            print("Authentication failed.")
            return

        print()
        print("Authentication successful.")
        print(f"Logged in as: {me.first_name}")
        print(f"User ID: {me.id}")


if __name__ == "__main__":
    asyncio.run(main())
