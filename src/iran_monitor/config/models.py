from pydantic import BaseModel


class Source(BaseModel):
    name: str
    language: str
    enabled: bool = True


class TelegramSource(Source):
    username: str


class RSSSource(Source):
    url: str


class WebsiteSource(Source):
    url: str


class SourcesConfig(BaseModel):
    telegram: list[TelegramSource] = []
    rss: list[RSSSource] = []
    websites: list[WebsiteSource] = []
