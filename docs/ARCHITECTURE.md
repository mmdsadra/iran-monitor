# Iran Monitor — Architecture

## 1. System purpose

Iran Monitor is an OSINT processing pipeline for Iran-focused situational awareness. It turns heterogeneous raw reporting into a normalized event store and a compact intelligence feed.

The central architectural principle is:

> **LLM extracts facts; deterministic software decides what those facts mean operationally.**

The LLM is useful for language understanding, especially across Persian and English. It is not treated as a database, event deduplicator, geocoder, corroboration engine, or forecasting oracle.

## 2. End-to-end flow

```text
RSS / Telegram
      │
      ▼
NewsItem
      │
      ▼
Deduplication
      │
      ▼
IntelligenceGate
      │
      ├── rejected → diagnostics
      │
      ▼
LLM Provider
      │
      ▼
Structured EventClaim
      │
      ├── no_event → diagnostics
      ├── provider error → diagnostics
      │
      ▼
Parser / Validator
      │
      ▼
Geography normalization
      │
      ▼
EventMatcher
      │
      ├── existing event → merge evidence
      └── no match → create event
      │
      ▼
EventClusterer
      │
      ▼
Verification / Corroboration
      │
      ▼
Scoring / Assessment
      │
      ├── map
      ├── assessment chart
      ├── pie chart
      └── text report
      │
      ▼
Telegram Publisher
```

## 3. Data layers

### Raw news layer

`NewsItem` represents one collected source item. It contains source identity, source type, language, title/text, publication time, and raw source metadata.

This layer should remain close to the original source. Do not overwrite raw text with LLM-generated summaries.

### Claim layer

An `EventClaim` is a structured interpretation of one news item. It describes what the source claims happened.

A claim is **not automatically true**. It is a machine-readable representation of a report.

### Event layer

An `Event` represents the system's current hypothesis that multiple claims refer to one underlying real-world occurrence.

One event can therefore have:

```text
1 Event
 ├── Claim A / source A
 ├── Claim B / source B
 ├── Claim C / source C
 └── evidence / verification metadata
```

This distinction prevents repeated reporting from inflating the apparent number of incidents.

## 4. Collection

Collectors live under `src/iran_monitor/collectors/`.

- `rss.py` handles RSS ingestion.
- `telegram.py` handles Telegram source history.
- `telegram_auth.py` and the login runner manage the Telethon user session.
- `deduplicator.py` prevents identical content from entering the intelligence pipeline repeatedly.

Collection is intentionally separated from intelligence. A source failure should not require changes to event logic.

## 5. Intelligence gate

The gate is the first intelligence boundary and lives under `src/iran_monitor/intelligence/`.

The gate should answer:

> **Is this source item relevant enough to Iran Monitor to spend LLM/API/database resources on it?**

It should not answer:

> Is this event dangerous?

Those are different questions.

The gate currently uses deterministic patterns for Iran, regional context, Persian Iran-focused vocabulary, advertising, and gambling/noise. The gate returns a `GateDecision` with acceptance, score, relevance score, and rejection reason.

When tuning this subsystem, measure both:

- **false negatives** — Iran stories incorrectly rejected;
- **false positives** — unrelated world stories incorrectly accepted.

## 6. LLM boundary

The provider adapter sits under `intelligence/providers/`.

The provider's job is narrow:

```text
NewsItem → structured claim or no-event
```

It should not persist events or perform matching.

Provider failures must be observable separately from legitimate `no_event` responses. A `no_event` result means the model did not identify a supported event; an HTTP 403, timeout, invalid JSON response, or schema error means the processing path failed.

## 7. Parsing and validation

LLM output passes through parser and validator layers before entering event intelligence.

The parser converts provider output into application models. The validator checks structural and semantic constraints.

Examples of facts that must not be silently invented:

- location;
- occurrence time;
- casualty count;
- actor identity;
- weapon type;
- damage level.

If the source does not support a fact, it should remain unknown.

## 8. Geography

Location processing is separate from extraction so that natural-language place references can be normalized consistently.

A location can have:

- raw location text from the source/claim;
- normalized name;
- latitude/longitude;
- confidence.

The map renderer should prefer verified/high-confidence coordinates. Ambiguous locations should be flagged or omitted rather than plotted at a misleading coordinate.

## 9. Claim → Event matching

The matcher determines whether a new claim describes an existing event.

Relevant dimensions include:

- event type;
- geographic proximity;
- temporal proximity;
- textual/contextual similarity.

A match must be strong enough to avoid merging distinct incidents. In particular, distance and time are important negative signals.

The matcher should select the best candidate rather than simply returning the first acceptable candidate.

## 10. Clustering

Matching operates at insertion time; clustering provides a broader event consolidation layer.

The clusterer should ensure that multiple claims referring to the same incident form one coherent event while distinct incidents remain separate.

When merging, evidence and source references must be preserved.

## 11. Corroboration and verification

Corroboration answers:

> How much independent evidence supports this event?

It should consider both the number and diversity of sources.

Ten copies of one syndicated report should not be equivalent to ten independent sources.

Verification/confidence should be explainable from stored evidence. The LLM's confidence field is not independent corroboration.

## 12. Scoring

Scoring converts the event store into category-level situation indicators.

Current report categories include:

- war/conflict;
- diplomacy;
- protests;
- military activity;
- infrastructure damage;
- casualties.

A robust score should conceptually separate:

```text
Iran relevance
× event severity
× confidence / verification
× source reliability
× recency
```

The exact implementation must be documented in the scoring module and covered by deterministic tests.

Scores are information-pressure/severity indicators. They are not probability estimates or forecasts.

## 13. Output layer

`src/iran_monitor/output/` transforms the event store into user-facing artifacts.

The text report should be generated from the same assessment object as the JPGs so the numbers cannot drift between outputs.

The map visualizes geospatial events. Assessment and pie charts summarize the same event set used by the report.

Telegram publishing is a delivery layer and must not alter the underlying intelligence state.

## 14. Storage

SQLite is the local persistence layer.

Storage is intentionally local-first to reduce external dependencies and make the pipeline reproducible. Event persistence should preserve enough source/evidence references to trace an assessment back to its inputs.

## 15. Debugging methodology

When a report looks wrong, debug from left to right. Never start by changing the final score without proving the upstream event set is correct.

```text
1. Collection
   Did the source actually return the expected articles/messages?

2. Deduplication
   Were valid items removed as duplicates?

3. Gate
   Were Iran-related items accepted?
   Were unrelated items rejected?

4. LLM
   Did the request happen?
   Did the provider return valid structured output?

5. Parsing/validation
   Did the claim survive schema/semantic validation?

6. Geography
   Was location normalized correctly?

7. Matching
   Was the claim attached to the correct event?

8. Clustering
   Were events incorrectly merged or split?

9. Corroboration
   Was evidence/source diversity preserved?

10. Scoring
    Did the correct events contribute to the right category?

11. Output
    Does the rendered report reflect the assessment?

12. Telegram
    Was the correct generated artifact published?
```

The `TODO.md` checklist defines the diagnostics needed to make these transitions observable in one run.
