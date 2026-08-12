# Iran Monitor

Iran Monitor is a **local-first open-source intelligence (OSINT) pipeline focused on Iran and its surrounding security environment**. It collects Persian/English reporting from RSS feeds and Telegram channels, filters for Iran relevance, extracts structured factual claims with an LLM, validates and geolocates those claims, matches and clusters related events, corroborates evidence, scores the resulting situation, and publishes a compact intelligence feed to Telegram.

> **Analytical boundary:** Iran Monitor is an information-processing and situational-awareness system. Its percentages represent information pressure / event severity signals. They are **not probabilities of war, forecasts, or independently verified ground truth**.

## Pipeline at a glance

```text
                 ┌────────────── RSS ──────────────┐
                 │                                  │
Telegram user ──┤                                  ├──> NewsItem
session          │                                  │
                 └──────── Telegram channels ──────┘
                                  │
                                  ▼
                         Collection + dedup
                                  │
                                  ▼
                     Iran relevance / noise gate
                                  │
                                  ▼
                    LLM factual claim extraction
                                  │
                                  ▼
                    Claim parsing + validation
                                  │
                                  ▼
                 Location normalization / geocoding
                                  │
                                  ▼
                     Claim → Event matching
                                  │
                                  ▼
                     Event clustering / merging
                                  │
                                  ▼
                  Evidence corroboration + confidence
                                  │
                                  ▼
                       Intelligence scoring
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
          JPG map / charts                  Text report
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
                           Telegram publisher
```

The system deliberately keeps the LLM at the **fact-extraction boundary**. Deterministic application code owns filtering, validation, event identity, clustering, corroboration, scoring, rendering, persistence, and publishing.

## Capabilities

### Collection

- RSS ingestion with configurable feeds.
- Telegram history ingestion through a **Telegram user session / Telethon**, not the publishing bot.
- Source-level configuration and enable/disable controls.
- Deduplication before intelligence processing.
- Configurable history limits so an initial backfill can inspect substantially more than the default recent window.

### Intelligence gate

Every collected `NewsItem` goes through a deterministic relevance/noise gate before the expensive LLM step.

The gate rejects obvious spam/advertising/gambling and unrelated foreign stories. Iran relevance can come from:

- explicit Iran/Iranian references;
- Iranian cities, infrastructure, military sites, Persian Gulf / Strait of Hormuz references;
- regional context such as Israel, the United States, Pentagon, Houthi activity, Red Sea, carriers, Gulf of Oman, or Arabian Sea;
- curated Persian Telegram vocabulary covering diplomacy, protests, domestic politics, economy, military activity, energy, and other Iran-specific topics.

This is intentionally **not** a generic keyword-only classifier: the goal is to retain relevant Iranian reporting even when a post does not literally say `Iran`.

### LLM claim extraction

The LLM receives an accepted news item and is asked to extract a structured factual claim. The model is not the event database and is not trusted to decide event identity.

A claim can contain fields such as:

- event type;
- description;
- location / location text;
- occurrence time;
- entities;
- source reference;
- confidence / verification metadata.

The provider layer is OpenAI-compatible. The project has been tested with Groq's OpenAI-compatible endpoint and can be configured through environment variables.

### Event intelligence

Claims are converted into persistent events and then processed through:

1. **Validation** — reject malformed or unsupported claims.
2. **Geospatial normalization** — normalize place names and attach coordinates when possible.
3. **Matching** — compare new claims against existing events using event type, location, time, and textual/contextual similarity.
4. **Clustering** — merge claims describing the same underlying occurrence.
5. **Corroboration** — use multiple independent pieces of evidence to increase confidence and verification state.
6. **Scoring** — derive category-level information-pressure/severity indicators for the final situation report.

The resulting event store is intended to be more stable than the raw news stream: many reports can become one event with multiple evidence items.

## Output

Each intelligence run can generate:

- `output/iran_monitor_map.jpg` — real geographic event map with event markers.
- `output/iran_monitor_assessment.jpg` — situation/severity indicators.
- `output/iran_monitor_pie.jpg` — category composition.
- terminal/Telegram text report — overall status, category scores, event count, and important recent events.

The report currently tracks categories including:

- war / conflict;
- diplomacy;
- protests;
- military activity;
- infrastructure damage;
- casualties.

## Repository structure

```text
src/iran_monitor/
├── collectors/       RSS + Telegram ingestion and deduplication
├── classification/   source/content classification helpers
├── config/           environment and source configuration
├── events/           event model, extraction, matching, clustering, verification
├── intelligence/     gate, claims, LLM extraction, validation, geography, pipeline
├── models/           shared news models
├── output/           report generation, JPG rendering, Telegram publishing
├── pipeline/         collection orchestration
├── runners/          executable entry points
└── storage/          SQLite persistence

tests/                automated unit/integration tests
config/local/         local source configuration (do not commit sensitive values)
output/               generated local intelligence artifacts
```

For a deeper architecture and data-flow description see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). For the intelligence subsystem specifically see [`docs/INTELLIGENCE.md`](docs/INTELLIGENCE.md). Active engineering work is tracked in [`TODO.md`](TODO.md).

## Requirements

- Python 3.11+ (the project is currently tested with Python 3.14).
- Internet access for configured RSS feeds, Telegram, LLM requests, and Telegram publishing.
- Telegram Bot API token for publishing.
- Telegram API ID/hash and a Telethon user session for reading Telegram channels.
- LLM API key for the configured OpenAI-compatible provider.
- `matplotlib`, GeoPandas, Shapely and related geospatial dependencies for geographic JPG output.

All Python dependencies are pinned in `requirements.txt`.

## Installation

```bash
git clone https://github.com/mmdsadra/iran-monitor.git
cd iran-monitor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the test suite:

```bash
PYTHONPATH=src pytest -q
```

## Environment

Create `.env` in the project root. **Never commit it.**

```env
# LLM / Groq (OpenAI-compatible)
IRAN_MONITOR_LLM_API_KEY=your_llm_api_key
IRAN_MONITOR_LLM_BASE_URL=https://api.groq.com/openai/v1
IRAN_MONITOR_LLM_MODEL=llama-3.3-70b-versatile

# Telegram Bot API: bot that publishes the final report
TELEGRAM_BOT_TOKEN=123456789:replace_me
TELEGRAM_CHAT_ID=-1001234567890

# Telegram user API: Telethon reads source channel history
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=replace_me
TELEGRAM_SESSION_NAME=iran_monitor
```

Keep API keys, bot tokens, API hashes, and Telethon session files private.

## Telegram setup

### Publishing

1. Create a bot with BotFather.
2. Add the bot to the target channel as an administrator with permission to post.
3. Set `TELEGRAM_BOT_TOKEN`.
4. Set `TELEGRAM_CHAT_ID`.

### Reading source channels

Telethon uses a **user session**, not the publishing bot. Configure `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`, then authenticate when required:

```bash
PYTHONPATH=src python -m iran_monitor.runners.telegram_login
```

The generated session file is a credential and must remain private.

## Configure sources

Local sources are configured in:

```text
config/local/sources.yaml
```

RSS and Telegram sources can be enabled/disabled independently. The intelligence runner combines the collected items before relevance filtering and extraction.

For high-volume or initial-backfill runs, increase the Telegram history limit so the intelligence layer has enough context:

```bash
PYTHONPATH=src python -m iran_monitor.runners.run_intelligence --telegram-history-limit 200
```

## Run the system

### Collect only

Telegram:

```bash
PYTHONPATH=src python -m iran_monitor.runners.collect_telegram
```

RSS:

```bash
PYTHONPATH=src python -m iran_monitor.runners.collect_rss
```

### Run intelligence and generate output

```bash
PYTHONPATH=src python -m iran_monitor.runners.run_intelligence
```

### Run and publish to Telegram

```bash
PYTHONPATH=src python -m iran_monitor.runners.run_intelligence --publish
```

The runner persists local data in SQLite and writes generated artifacts under `output/`.

## Development workflow

Before committing:

```bash
PYTHONPATH=src pytest -q
```

The test suite covers collection, classification, intelligence gating, claim extraction/parsing/validation, event modeling, matching, clustering, verification, storage, rendering, and output behavior.

When debugging a low or empty intelligence report, do not immediately change the scoring formula. Trace the pipeline in order:

```text
collected items
→ gate accepted/rejected
→ LLM requests/responses
→ parsed claims
→ validation
→ normalized locations
→ matched/created events
→ clustered events
→ corroboration/verification
→ scoring
→ rendered output
→ Telegram publishing
```

This order makes it possible to identify whether information was lost during ingestion, filtering, extraction, event formation, or scoring.

## Operational limitations

- LLM extraction is probabilistic and can return no claim, malformed output, or an incorrect interpretation. Treat extracted claims as structured reports, not ground truth.
- Relevance filtering is deliberately conservative but cannot perfectly classify every geopolitical article.
- Location normalization depends on the source wording and geospatial knowledge available to the project.
- Multiple reports about one incident may be merged; this is desirable for event identity but can hide the raw-message count unless evidence is inspected.
- The assessment is a signal aggregation layer, not a forecasting model.
- RSS/Telegram source coverage determines what the system can know. Missing a source can produce a misleadingly quiet report.

## Security

Never commit:

- `.env` files;
- Telegram user session files;
- Telegram bot tokens;
- Telegram API hashes/IDs when treated as sensitive deployment configuration;
- LLM API keys;
- private credentials or raw private source data.

If a credential is exposed, revoke/rotate it immediately.
