import pytest

from iran_monitor.intelligence.evidence import (
    Evidence,
    EvidenceType,
)


def test_evidence_creation():
    evidence = Evidence(
        source_id="news-001",
        evidence_type=EvidenceType.DIRECT_REPORT,
        description="گزارش مستقیم از محل حادثه",
        confidence=0.8,
    )

    assert evidence.source_id == "news-001"
    assert evidence.evidence_type == EvidenceType.DIRECT_REPORT
    assert evidence.confidence == 0.8


def test_evidence_confidence_range():
    with pytest.raises(ValueError):
        Evidence(
            source_id="news-001",
            evidence_type=EvidenceType.DIRECT_REPORT,
            description="invalid",
            confidence=1.5,
        )
