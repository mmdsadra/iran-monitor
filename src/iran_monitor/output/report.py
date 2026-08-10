from datetime import datetime, timezone

from iran_monitor.events.model import Event, EventType
from iran_monitor.output.assessment import SituationAssessment


def _utc(value: datetime | None) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def build_report(events: list[Event], assessment: SituationAssessment) -> str:
    if assessment.overall >= 75:
        state = "بحرانی"
    elif assessment.overall >= 50:
        state = "پرخطر"
    elif assessment.overall >= 25:
        state = "متشنج"
    else:
        state = "نسبتاً آرام"

    # Prefer concrete security, protest, casualty and diplomatic events over
    # generic `other` records. Show up to 8 so a busy feed is actually useful.
    concrete = [e for e in events if e.event_type != EventType.OTHER]
    candidates = concrete or events
    recent = sorted(candidates, key=lambda e: (_utc(e.occurred_at), e.severity, e.confidence), reverse=True)[:8]

    lines = [
        "🇮🇷 گزارش وضعیت ایران — Iran Monitor",
        f"وضعیت کلی: {state} ({assessment.overall:.0f}/100)",
        "",
        f"جنگ/درگیری: {assessment.war:.0f}%",
        f"دیپلماسی: {assessment.diplomacy:.0f}%",
        f"اعتراضات: {assessment.protests:.0f}%",
        f"فعالیت نظامی: {assessment.military:.0f}%",
        f"آسیب زیرساختی: {assessment.infrastructure:.0f}%",
        f"تلفات: {assessment.casualties:.0f}%",
        "",
        f"تعداد رویدادهای تحلیل‌شده: {len(events)}",
        "",
        "رویدادهای مهم اخیر:",
    ]

    if not recent:
        lines.append("• مورد مهمی در داده‌های فعلی ثبت نشده است.")
    else:
        for event in recent:
            location = event.city or event.location_text or event.country or "مکان نامشخص"
            lines.append(
                f"• {event.event_type.value} — {location} — شدت {event.severity:.0%} — اعتبار {event.confidence:.0%}"
            )

    lines.extend([
        "",
        "توجه: درصدها شاخص شدت/فشار اطلاعاتی هستند، نه احتمال قطعی وقوع جنگ یا پیش‌بینی آینده.",
    ])
    return "\n".join(lines)
