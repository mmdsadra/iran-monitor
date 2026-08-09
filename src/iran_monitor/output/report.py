from datetime import datetime, timezone

from iran_monitor.events.model import Event
from iran_monitor.output.assessment import SituationAssessment


def build_report(events: list[Event], assessment: SituationAssessment) -> str:
    """Build the human-readable Persian situation summary."""
    if assessment.overall >= 75:
        state = "بحرانی"
    elif assessment.overall >= 50:
        state = "پرخطر"
    elif assessment.overall >= 25:
        state = "متشنج"
    else:
        state = "نسبتاً آرام"

    recent = sorted(
        events,
        key=lambda e: e.occurred_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )[:5]
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
    for event in recent:
        location = event.city or event.location_text or "مکان نامشخص"
        lines.append(
            f"• {event.event_type.value} — {location} — شدت {event.severity:.0%} — اعتبار {event.confidence:.0%}"
        )

    lines.extend([
        "",
        "توجه: درصدها شاخص شدت/فشار اطلاعاتی هستند، نه احتمال قطعی وقوع جنگ یا پیش‌بینی آینده.",
    ])
    return "\n".join(lines)
