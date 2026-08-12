# Iran Monitor — Intelligence Subsystem

## Purpose

The intelligence subsystem transforms raw multilingual news into a traceable set of Iran-relevant events.

```text
NewsItem
  ↓
Relevance Gate
  ↓
LLM Claim Extraction
  ↓
Parsing + Validation
  ↓
Geography
  ↓
Claim → Event Matching
  ↓
Clustering
  ↓
Corroboration / Verification
  ↓
Scoring
```

The subsystem is intentionally layered. Each layer has one responsibility and should expose enough information to diagnose losses or false positives.

## 1. Relevance Gate

**Input:** `NewsItem`

**Output:** `GateDecision`

Question answered:

> Is this item relevant to Iran Monitor?

It should reject obvious noise and unrelated foreign stories before expensive LLM processing.

### Relevance signals

Strong signals include direct references to Iran, Iranian institutions, Iranian locations, the Persian Gulf, Strait of Hormuz, or Iranian military/nuclear infrastructure.

Regional context can also be relevant when the relationship to Iran is explicit or sufficiently strong, for example Iran-US, Iran-Israel, Gulf security, Houthi/Red Sea activity, or major US military deployments connected to the Iran theater.

Persian Telegram sources need broader topical handling because many posts omit explicit `Iran`. Relevant topics include diplomacy, negotiations, protests, domestic politics, economy, military activity, energy, and security.

### Gate anti-patterns

Do not make generic words such as `attack`, `damage`, `military`, or `earthquake` sufficient by themselves. They produce large numbers of foreign false positives.

Do not require the literal word `Iran` for every Persian story. That produces false negatives for contextual reporting.

## 2. Claim extraction

**Input:** accepted `NewsItem`

**Output:** structured `EventClaim` or `no_event`

The provider is responsible for language understanding and factual extraction.

The model should identify what the source says happened, not invent an intelligence assessment.

### Extraction rules

- Extract only facts supported by the source.
- Keep unsupported fields unknown.
- Do not invent coordinates.
- Do not infer casualty numbers without textual support.
- Do not convert speculation into fact.
- Preserve source wording where uncertainty matters.
- Prefer a specific event type when the evidence supports it.
- Use `other` only when the event does not fit the supported taxonomy.

### Event taxonomy

Current event types include:

```text
attack
airstrike
missile_launch
explosion
protest
military_movement
diplomacy
infrastructure_damage
casualty
fire
strike
other
```

The taxonomy should remain small enough to be useful for aggregation. Add a new type only when existing categories cannot express the event reliably.

## 3. Parser and validator

The parser converts provider output into domain models. The validator checks whether the claim is structurally and semantically acceptable.

A provider response can fail in several different ways:

```text
HTTP/API failure
→ provider error

valid response with no supported event
→ no_event

invalid JSON / schema
→ parse or validation failure

valid claim
→ accepted claim
```

These cases must remain distinguishable in diagnostics.

## 4. Geography

Location extraction and location normalization are separate concerns.

A claim can contain a raw string such as:

```text
"near Sirik"
"Strait of Hormuz"
"Tehran"
```

The geography layer should normalize it into a canonical place and, where possible, coordinates.

Never silently assign a low-confidence ambiguous place to an unrelated country simply because the name exists there too.

For maritime events, locations such as the Strait of Hormuz and Gulf of Oman should be represented as geographic areas/points appropriate for visualization rather than forced into a city model.

## 5. Claim → Event matching

A claim is compared against existing events.

The matcher should use multiple independent dimensions:

### Event type

An explosion and a diplomatic meeting should not match merely because they occurred near the same city.

### Time

Events far apart in time should not merge simply because the text is similar.

### Location

Events far apart geographically should not merge merely because they share a generic description.

### Semantic/text similarity

Text helps identify related reports, but should not override strong time/location contradictions.

### Candidate selection

When multiple candidates exist, select the best-scoring candidate, not the first candidate returned from storage.

## 6. Event clustering

Clustering consolidates related claims/events into coherent incident groups.

Example:

```text
Source A: "Explosion reported near Sirik"
Source B: "Blast heard around Sirik"
Source C: "Officials report an incident near Sirik"

             ↓

        ONE EVENT
        ├── evidence A
        ├── evidence B
        └── evidence C
```

Clustering should not erase evidence provenance.

## 7. Corroboration

Corroboration increases confidence when independent evidence supports the same event.

Important distinction:

```text
3 independent sources → strong corroboration

3 reposts of one article → weak corroboration
```

Source diversity should therefore be measured separately from raw evidence count.

## 8. Verification / confidence

Confidence should represent how strongly the available evidence supports the event representation.

It should not mean:

> "The model is 95% sure this happened."

A better interpretation is:

> "Given the available source evidence and consistency checks, this event representation has high support."

Verification state should be explainable from evidence.

## 9. Scoring

Scoring occurs after the event set has been formed and corroborated.

The score should distinguish:

### Relevance

How strongly the event concerns Iran/the monitored theater.

### Severity

How significant the event is in the relevant category.

### Confidence

How strongly evidence supports the event.

### Source reliability

How trustworthy the source is for the particular claim type.

### Recency

How relevant the event is to the current situation.

Conceptually:

```text
contribution =
    relevance
  × severity
  × confidence
  × source_support
  × recency_weight
```

The actual implementation may differ, but the components should remain inspectable.

### Important scoring rule

**An unrelated event must contribute zero to Iran's score.**

This is why the relevance gate and event-level Iran relevance are critical. A Colombia earthquake must never increase Iran's infrastructure-damage score.

Likewise, a diplomatic event can be highly relevant without producing a military/severity spike.

## 10. Debugging a bad report

If the report says:

```text
Collected: 200
Events: 2
```

do not immediately change scoring.

First ask:

```text
Collected 200
  ↓
How many survived dedup?
  ↓
How many passed the Iran gate?
  ↓
How many reached the LLM?
  ↓
How many returned valid claims?
  ↓
How many became events?
  ↓
How many were merged?
  ↓
How many were corroborated?
  ↓
How many contributed to scoring?
```

The first unexpected drop is normally where the bug lives.

## 11. Testing strategy

Tests should exist at every boundary.

### Gate tests

Test both:

- Iran-related items accepted;
- unrelated world events rejected;
- advertisements rejected;
- Persian contextual stories accepted;
- generic foreign stories rejected.

### Provider tests

Test:

- successful structured response;
- `no_event` response;
- malformed response;
- provider HTTP error;
- timeout/rate-limit behavior.

### Extraction tests

Use realistic Persian and English examples. Include diplomatic and political statements, not only physical incidents.

### Matcher tests

Cover:

- same event → match;
- distant location → no match;
- distant time → no match;
- best candidate selection.

### Clusterer tests

Cover repeated multi-source reports and distinct nearby incidents.

### Corroboration tests

Cover source count versus source diversity and duplicate/syndicated reporting.

### Scoring tests

Use synthetic events with known expected category contributions. Include irrelevant foreign events and verify that they contribute zero.

## 12. Operational principle

When the system behaves incorrectly, preserve the data path and instrument it before modifying the algorithm.

The most valuable diagnostic question is:

> **For this specific source item, what was the last stage that saw it?**

The engineering TODO tracks the observability work required to answer that question automatically.
