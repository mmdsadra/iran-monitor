from iran_monitor.intelligence.claims import EventClaim


class EventMatcher:
    def match(
        self,
        candidate: EventClaim,
        existing: list[EventClaim],
    ) -> EventClaim | None:
        for event in existing:
            if self._same_event(candidate, event):
                return event

        return None

    def _same_event(
        self,
        a: EventClaim,
        b: EventClaim,
    ) -> bool:
        if a.event_type != b.event_type:
            return False

        if a.city and b.city:
            if a.city.casefold() != b.city.casefold():
                return False

        return True