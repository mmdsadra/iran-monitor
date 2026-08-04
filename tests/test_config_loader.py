from iran_monitor.config.loader import load_sources


def test_load_sources():
    config = load_sources("config/sources.yaml")

    assert len(config.telegram) == 2
    assert len(config.rss) == 1
    assert len(config.websites) == 1


def test_telegram_source():
    config = load_sources("config/sources.yaml")

    source = config.telegram[0]

    assert source.name == "example_farsi"
    assert source.language == "fa"
    assert source.enabled is False
    assert source.username == "@example_farsi"