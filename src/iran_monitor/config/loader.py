from pathlib import Path

import yaml

from iran_monitor.config.models import SourcesConfig


def load_sources(path: str | Path) -> SourcesConfig:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Source configuration not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    return SourcesConfig.model_validate(data)