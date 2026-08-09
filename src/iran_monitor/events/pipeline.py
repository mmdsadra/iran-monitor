from dataclasses import dataclass

from iran_monitor.events.clusterer import ClusterResult, EventClusterer
from iran_monitor.events.model import Event
from iran_monitor.events.verification import (
    EventVerificationEngine,
    SourceAssessment,
)
from iran_monitor.intelligence.claims import EventClaim
from iran_monitor.storage.events import EventRepository


@dataclass(frozen=True)
class EventPipelineResult:
    event: Event
    created: bool
    match_score: float | None


class EventIntelligencePipeline:
    """Run Claim -> match/merge/create -> corroboration -> persistence."""

    def __init__(
        self,
        repository: EventRepository,
        *,
        clusterer: EventClusterer | None = None,
        verifier: EventVerificationEngine | None = None,
    ):
        self.repository = repository
        self.clusterer = clusterer or EventClusterer(repository)
        self.verifier = verifier or EventVerificationEngine()

    def process(
        self,
        claim: EventClaim,
        source_assessments: list[SourceAssessment] | None = None,
    ) -> EventPipelineResult:
        cluster = self.clusterer.process_claim(claim)
        verified = self.verifier.apply(cluster.event, source_assessments)
        self.repository.save(verified)

        return EventPipelineResult(
            event=verified,
            created=cluster.created,
            match_score=cluster.match_score,
        )
