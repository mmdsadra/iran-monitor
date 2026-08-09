import json
import os
from pathlib import Path
from urllib import request
from urllib.parse import urlencode


class TelegramPublisher:
    """Publish an intelligence feed to a Telegram channel via Bot API."""

    def __init__(self, token: str | None = None, chat_id: str | None = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not configured")
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID is not configured")

    @property
    def api_base(self) -> str:
        return f"https://api.telegram.org/bot{self.token}"

    def _post(self, method: str, data: dict[str, str]) -> dict:
        encoded = urlencode(data).encode("utf-8")
        req = request.Request(
            f"{self.api_base}/{method}",
            data=encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with request.urlopen(req, timeout=30) as response:
            result = json.load(response)
        if not result.get("ok"):
            raise RuntimeError(f"Telegram {method} failed: {result}")
        return result

    def _send_photo(self, path: Path, caption: str | None = None) -> None:
        import mimetypes
        import uuid

        if not path.exists():
            raise FileNotFoundError(f"Output image does not exist: {path}")

        boundary = uuid.uuid4().hex
        body = bytearray()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(b'Content-Disposition: form-data; name="chat_id"\r\n\r\n')
        body.extend(f"{self.chat_id}\r\n".encode())
        if caption:
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(b'Content-Disposition: form-data; name="caption"\r\n\r\n')
            body.extend(caption.encode("utf-8"))
            body.extend(b"\r\n")
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="photo"; filename="{path.name}"\r\n'.encode()
        )
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.extend(path.read_bytes())
        body.extend(f"\r\n--{boundary}--\r\n".encode())

        req = request.Request(
            f"{self.api_base}/sendPhoto",
            data=bytes(body),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        with request.urlopen(req, timeout=60) as response:
            result = json.load(response)
            if not result.get("ok"):
                raise RuntimeError(f"Telegram sendPhoto failed: {result}")

    def send_report(self, report: str) -> None:
        self._post("sendMessage", {"chat_id": self.chat_id, "text": report})

    def publish(self, report: str, *images: str | Path) -> None:
        for image in images:
            self._send_photo(Path(image))
        self.send_report(report)
