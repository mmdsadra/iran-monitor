# Iran Monitor

Iran Monitor is a local-first intelligence pipeline for collecting Persian/English news from RSS feeds and Telegram channels, extracting factual claims with an LLM, matching and clustering related events, corroborating evidence, and producing a compact situation report for Telegram.

## What it does

```text
RSS + Telegram
      ↓
Collectors / deduplication
      ↓
Claim extraction (LLM)
      ↓
Claim validation + event matching
      ↓
Event clustering + corroboration
      ↓
Situation assessment
      ↓
JPG map + assessment + pie chart + text report
      ↓
Telegram channel
```

The project is designed to be deterministic and testable around the LLM boundary: the model extracts structured facts; the event pipeline decides how claims relate to stored events.

## Requirements

- Python 3.11+ (tested in this project with Python 3.14)
- A Telegram bot token for publishing
- A Telegram API ID/hash for reading Telegram channels with Telethon
- An LLM API key. The current provider adapter is OpenAI-compatible and has been tested with Groq's OpenAI-compatible endpoint.
- Internet access for RSS/Telegram/LLM/Telegram publishing
- `matplotlib` for JPG output

## Installation

```bash
git clone https://github.com/mmdsadra/iran-monitor.git
cd iran-monitor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install matplotlib
```

Run the test suite:

```bash
PYTHONPATH=src pytest -q
```

## Environment

Create `.env` in the project root. Never commit this file.

```env
# LLM / Groq (OpenAI-compatible)
IRAN_MONITOR_LLM_API_KEY=your_llm_api_key
IRAN_MONITOR_LLM_BASE_URL=https://api.groq.com/openai/v1
IRAN_MONITOR_LLM_MODEL=llama-3.3-70b-versatile

# Telegram Bot API: bot that publishes the final report
TELEGRAM_BOT_TOKEN=123456789:replace_me
TELEGRAM_CHAT_ID=-1001234567890

# Telegram user API: used by Telethon to READ channel history
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=replace_me
TELEGRAM_SESSION_NAME=iran_monitor
```

Keep bot credentials, API hashes, LLM keys, and Telethon session files private.

## Telegram setup

### Publishing

1. Create a bot with BotFather.
2. Add the bot to your target channel as an administrator with permission to post.
3. Set `TELEGRAM_BOT_TOKEN`.
4. Set `TELEGRAM_CHAT_ID` to the channel ID.

### Reading source channels

Telethon uses a Telegram user session, not the publishing bot. Configure `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`, then run the Telegram login runner when needed:

```bash
PYTHONPATH=src python -m iran_monitor.runners.telegram_login
```

The session file must remain private and should not be committed.

## Configure sources

Sources are configured in:

```text
config/local/sources.yaml
```

RSS sources and Telegram sources can be enabled/disabled independently. The intelligence runner reads both and combines their items before extraction.

## Run the intelligence pipeline

Normal run:

```bash
PYTHONPATH=src python -m iran_monitor.runners.run_intelligence
```

Publish the generated feed to Telegram:

```bash
PYTHONPATH=src python -m iran_monitor.runners.run_intelligence --publish
```

On an initial Telegram backfill, fetch more history per source:

```bash
PYTHONPATH=src python -m iran_monitor.runners.run_intelligence --telegram-history-limit 200
```

The runner writes generated files under `output/` and persists collected news/events locally in SQLite databases.

## Output

Each run produces:

- `output/iran_monitor_map.jpg` — geographic event map
- `output/iran_monitor_assessment.jpg` — situation indicators
- `output/iran_monitor_pie.jpg` — signal composition
- terminal text report — overall status and recent important events

The percentages are **information-pressure/severity indicators**, not probabilities of war and not forecasts.

## Project layout

```text
src/iran_monitor/
├── collectors/       RSS + Telegram ingestion
├── classification/   source/content classification
├── events/           event model, matching, clustering, verification
├── intelligence/     claims, LLM extraction, validation, intelligence pipeline
├── pipeline/         collection orchestration
├── output/           reports, JPG rendering, Telegram publisher
├── runners/          executable pipeline entry points
├── storage/          SQLite persistence
└── config/           environment and source configuration

tests/                automated test suite
config/local/         local source configuration
output/               generated intelligence artifacts
```

## Development

Run all tests before committing:

```bash
PYTHONPATH=src pytest -q
```

The repository currently has a comprehensive unit-test suite covering collectors, intelligence extraction/validation, event matching/clustering/verification, storage, and output components.

## Important limitations

- LLM extraction is probabilistic; generated claims must be treated as structured extraction, not independent ground truth.
- Location quality depends on the source text and the configured geolocation logic.
- Telegram history is incremental after the initial backfill; use `--telegram-history-limit` to control the first/explicit history window.
- The generated assessment is an analytical signal, not a prediction engine.

## Security

Do not commit `.env`, Telegram session files, API keys, bot tokens, or private credentials. If a credential is exposed, revoke/rotate it immediately.
