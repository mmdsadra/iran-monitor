import os

from dotenv import load_dotenv


def load_environment() -> None:
    """Load environment variables from the local .env file."""

    load_dotenv()

    if os.getenv("TELEGRAM_API_ID"):
        return

    if os.getenv("TELEGRAM_API_HASH"):
        return
