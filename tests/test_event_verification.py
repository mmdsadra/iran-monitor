from iran_monitor.events.model import Event, EventType, VerificationStatus
from iran_monitor.events.verification import EventVerificationEngine, SourceAssessment


def make_event(*source_ids, confidence=0.2):
    return Event(
        id="event-1",
        event_type=EventType.EXPLOSION,
        description="Explosion in Isfahan",
        confidence=confidence,
        source_ids=list(source_ids),
    )


def test_single_source_is_unverified():
    engine = EventVerificationEngine()

    result = engine.assess(make_event("a"))

    assert result.verification == VerificationStatus.UNVERIFIED
    assert result.independent_sources == 1
    assert result.total_sources == 1


def test_two_independent_sources_are_corroborated():
    engine = EventVerificationEngine()

    result = engine.assess(
        make_event("a", "b"),
        [SourceAssessment("a", reliability=0.8), SourceAssessment("b", reliability=0.7)],
    )

    assert result.verification == VerificationStatus.CORROBORATED
    assert result.independent_sources == 2
    assert result.confidence > 0.8


def test_three_high_reliability_sources_are_verified():
    engine = EventVerificationEngine()

    result = engine.assess(
        make_event("a", "b", "c"),
        [
            SourceAssessment("a", reliability=0.9),
            SourceAssessment("b", reliability=0.85),
            SourceAssessment("c", reliability=0.8),
        ],
    )

    assert result.verification == VerificationStatus.VERIFIED
    assert result.independent_sources == 3


def test_duplicate_source_does_not_increase_corroboration():
    engine = EventVerificationEngine()

    result = engine.assess(
        make_event("a", "a"),
        [SourceAssessment("a", reliability=0.95)],
    )

    assert result.total_sources == 1
    assert result.independent_sources == 1
    assert result.verification == VerificationStatus.UNVERIFIED


def test_dependent_source_does_not_count_as_independent():
    engine = EventVerificationEngine()

    result = engine.assess(
        make_event("a", "b"),
        [
            SourceAssessment("a", reliability=0.9, independent=True),
            SourceAssessment("b", reliability=0.9, independent=False),
        ],
    )

    assert result.independent_sources == 1
    assert result.verification == VerificationStatus.UNVERIFIED


def test_apply_updates_event_assessment():
    engine = EventVerificationEngine()
    event = make_event("a", "b", confidence=0.1)

    updated = engine.apply(
        event,
        [SourceAssessment("a", reliability=0.8), SourceAssessment("b", reliability=0.8)],
    )

    assert updated.confidence > event.confidence
    assert updated.verification == VerificationStatus.CORROBORATED
    assert event.confidence == 0.1
