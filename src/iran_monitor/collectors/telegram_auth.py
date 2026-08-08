from telethon import TelegramClient
import os


def create_telegram_client() -> TelegramClient:
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    session_path = os.getenv(
        "TELEGRAM_SESSION_PATH",
        "telegram_sessions/iran_monitor",
    )

    if not api_id:
        raise RuntimeError(
            "TELEGRAM_API_ID is missing"
        )

    if not api_hash:
        raise RuntimeError(
            "TELEGRAM_API_HASH is missing"
        )

    return TelegramClient(
        session_path,
        int(api_id),
        api_hash,
    )
