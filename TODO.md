# Iran Monitor — Engineering TODO

> Working checklist for the next development cycle. The project currently has the end-to-end collection → intelligence → event → scoring → JPG/Telegram flow; the priority is to make the intelligence layer observable, accurate, and robust before adding more surface features.

## P0 — Diagnose the current intelligence-quality problem

- [ ] Add a per-run diagnostics summary with counts for:
  - collected items
  - deduplicated items
  - gate accepted
  - gate rejected by reason
  - LLM requests
  - LLM `no_event`
  - LLM errors/timeouts
  - parsed claims
  - validation failures
  - events created
  - events merged
  - events clustered
  - corroborated events
  - events contributing to scoring
- [ ] Add a `--debug-intelligence` mode that prints one compact line per item through the pipeline.
- [ ] Give every item a stable trace ID and carry it through collection → claim → event → evidence.
- [ ] Persist enough processing metadata to answer: **where did this news item disappear?**
- [ ] Add a small deterministic fixture set representing real-world Iran-focused stories:
  - [ ] Trump / US statement about Iran
  - [ ] Iran-US diplomacy / negotiations
  - [ ] Iranian military activity
  - [ ] Strait of Hormuz incident
  - [ ] Iranian protest
  - [ ] Iranian infrastructure incident
  - [ ] unrelated Colombia earthquake
  - [ ] unrelated foreign political story
  - [ ] advertisement / spam

## P0 — Intelligence gate / Iran relevance

- [ ] Measure gate precision and recall against the fixture set instead of tuning keywords blindly.
- [ ] Separate **Iran relevance** from **event severity**. A diplomatic statement can be highly relevant without being a high-severity physical event.
- [ ] Support explicit Iran relevance through:
  - [ ] direct Iran references
  - [ ] Iranian cities/regions
  - [ ] Iranian institutions and political actors
  - [ ] Iran-US / Iran-Israel context
  - [ ] Gulf / Hormuz context
  - [ ] Persian Telegram channel context
- [ ] Avoid accepting unrelated foreign events merely because they contain generic words such as `attack`, `damage`, `military`, or `earthquake`.
- [ ] Avoid rejecting Iran-related political/diplomatic stories simply because they lack a physical location.
- [ ] Add tests for false positives and false negatives.

## P0 — LLM extraction observability

- [ ] Log provider/model/request status without logging API keys.
- [ ] Record request/response timing and token usage when the provider exposes it.
- [ ] Record whether the provider returned:
  - [ ] valid structured claim
  - [ ] empty/no-event result
  - [ ] invalid JSON
  - [ ] schema validation failure
  - [ ] HTTP/API error
  - [ ] timeout/rate-limit failure
- [ ] Add a safe local debug mode that can inspect the raw model response for a single selected item.
- [ ] Add provider-independent tests for the OpenAI-compatible adapter.
- [ ] Keep the core `IntelligencePipeline` contract deterministic: if the provider returns no claim, the core pipeline must report `no_event` unless an explicitly tested higher-level recovery strategy is invoked.

## P0 — Claim quality

- [ ] Review the extraction prompt against real Persian and English examples.
- [ ] Require factual extraction rather than article summarization.
- [ ] Require explicit uncertainty when a report is ambiguous.
- [ ] Prevent invented location, timestamp, casualty count, actors, or actions.
- [ ] Improve event-type selection for:
  - [ ] attack
  - [ ] airstrike
  - [ ] missile launch
  - [ ] explosion
  - [ ] military movement
  - [ ] protest
  - [ ] diplomacy
  - [ ] infrastructure damage
  - [ ] casualty
  - [ ] other
- [ ] Add regression tests for Trump statements, negotiations, and other diplomacy-heavy articles.

## P1 — Event matching / clustering

- [ ] Verify that repeated reports about the same incident converge on one event.
- [ ] Verify that geographically distant events do not merge.
- [ ] Verify that temporally distant events do not merge.
- [ ] Improve text similarity so stronger descriptions beat weak generic descriptions.
- [ ] Inspect event identity when location is missing.
- [ ] Preserve all source/evidence references when events are merged.
- [ ] Add regression fixtures for multi-source corroboration of one incident.

## P1 — Corroboration / verification

- [ ] Distinguish independent sources from duplicated syndication.
- [ ] Weight source reliability separately from source count.
- [ ] Do not treat an LLM's confidence as independent evidence.
- [ ] Make verification state explainable:
  - [ ] unverified
  - [ ] single-source
  - [ ] corroborated
  - [ ] strongly corroborated
- [ ] Surface the evidence count and source diversity in the report/debug output.

## P1 — Geospatial intelligence

- [ ] Verify normalization for Iranian cities, provinces, military sites, ports, and maritime locations.
- [ ] Verify Strait of Hormuz / Gulf of Oman locations.
- [ ] Distinguish geographic names that exist in multiple countries.
- [ ] Reject or flag low-confidence geocoding rather than silently plotting a wrong point.
- [ ] Add tests for Tehran, Isfahan, Sirik, Bandar Abbas, Hormuz, Strait of Hormuz, Gulf of Oman, and ambiguous names.
- [ ] Keep the real geographic map as the primary visual output.

## P1 — Scoring model

- [ ] Document the exact formula for every category score.
- [ ] Separate:
  - [ ] event severity
  - [ ] event confidence
  - [ ] source reliability
  - [ ] corroboration
  - [ ] Iran relevance
  - [ ] recency
- [ ] Ensure unrelated events cannot affect Iran's situation score.
- [ ] Ensure diplomacy is represented even when there is no physical incident.
- [ ] Add time decay so stale events do not dominate current reports.
- [ ] Cap duplicate evidence so ten copies of one report do not look like ten independent incidents.
- [ ] Add synthetic scoring tests with known expected outputs.

## P1 — Output quality

- [ ] Make the text report show the most important events by score, not merely the latest records.
- [ ] Include event title/description when available instead of mostly `other — location unknown`.
- [ ] Show confidence / verification in a useful way.
- [ ] Include source diversity or evidence count for important events.
- [ ] Ensure all JPGs contain useful content when events exist.
- [ ] Keep map, assessment, and pie chart numerically consistent with the text report.

## P2 — Source expansion

Add and validate RSS sources one at a time. Priority candidates:

- [ ] Reuters
- [ ] CNN
- [ ] Fox News
- [ ] Mexico News / relevant English-language feed
- [ ] Al Jazeera
- [ ] Other high-quality regional sources

For each source:

- [ ] Verify the RSS URL actually works.
- [ ] Verify language and encoding.
- [ ] Verify publication timestamps.
- [ ] Verify deduplication behavior.
- [ ] Verify Iran relevance filtering.
- [ ] Add a source-specific fixture/test where necessary.

## P2 — Larger collection windows

- [ ] Make per-source history limits configurable instead of one global assumption.
- [ ] Support 100–200+ items per source for backfills where practical.
- [ ] Avoid processing the same old messages repeatedly unless explicitly requested.
- [ ] Add source-level collection statistics to the run report.

## P2 — Telegram publishing

- [ ] Publish the text report first so failures in image publishing do not hide the assessment.
- [ ] Publish map / assessment / pie independently with clear error reporting.
- [ ] Add retry/backoff for Telegram API failures.
- [ ] Make publishing idempotent where possible.
- [ ] Add a `--dry-run` mode that generates everything but does not send to Telegram.

## P2 — Reliability / operations

- [ ] Add structured logging.
- [ ] Add explicit configuration validation before a run starts.
- [ ] Handle LLM rate limits and transient network failures gracefully.
- [ ] Handle malformed RSS feeds without aborting the complete run.
- [ ] Handle one broken Telegram source without aborting other sources.
- [ ] Add database migration/versioning strategy before schema changes become frequent.
- [ ] Add a reproducible local fixture mode that runs without network access or an LLM.

## P2 — Documentation

- [x] README installation and environment setup.
- [x] README architecture overview.
- [x] README intelligence subsystem overview.
- [x] README operational/debugging flow.
- [ ] Add `docs/ARCHITECTURE.md` with module-level architecture and data flow.
- [ ] Add `docs/INTELLIGENCE.md` with detailed gate → claim → event → corroboration → scoring semantics.
- [ ] Add `docs/CONFIGURATION.md` with every environment variable and source configuration field.
- [ ] Add `docs/TROUBLESHOOTING.md` with common failure modes and diagnostic commands.
- [ ] Add a contributor guide explaining how to add a collector, event type, provider, or output.

## Definition of done for the next intelligence milestone

The next milestone should not be considered complete until a single run can explain every major transition:

```text
N collected
→ N deduplicated
→ N accepted by Iran gate
→ N rejected (with reasons)
→ N sent to LLM
→ N valid claims
→ N no-event
→ N validation failures
→ N new events
→ N merged events
→ N corroborated events
→ N scored events
→ final category scores
```

And the fixture suite must demonstrate that:

1. Iran-related military events are detected.
2. Iran-related diplomacy is detected.
3. Iran-related protests/domestic events are detected.
4. Unrelated foreign incidents do not affect the score.
5. Multiple reports of one event are corroborated rather than counted as independent events.
6. Geographic output points to the correct location.
7. The Telegram report and JPG outputs reflect the same underlying event set.
