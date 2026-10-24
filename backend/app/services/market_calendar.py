"""Versioned SSE/SZSE scheduled holiday closures; not a full trading calendar."""

from __future__ import annotations

from datetime import date, timedelta


CALENDAR_VERSION = "sse-szse-announced-closures-2024-2026-v2"
CALENDAR_SOURCES = {
    2024: (
        "https://www.sse.com.cn/disclosure/dealinstruc/closed/c/c_20231226_5733941.shtml",
        "https://www.szse.cn/disclosure/notice/t20231226_605108.html",
    ),
    2025: (
        "https://www.sse.com.cn/disclosure/dealinstruc/closed/c/c_20241223_10767110.shtml",
        "https://www.szse.cn/disclosure/notice/t20241223_611283.html",
    ),
    2026: (
        "https://www.sse.com.cn/disclosure/announcement/general/c/c_20251222_10802507.shtml",
        "https://www.szse.cn/disclosure/notice/general/t20251222_618087.html",
    ),
}

# Inclusive intervals transcribed from both exchanges' published annual closure notices.
_CLOSURE_RANGES = {
    2024: (
        ("2024-01-01", "2024-01-01"),
        ("2024-02-09", "2024-02-17"),
        ("2024-04-04", "2024-04-06"),
        ("2024-05-01", "2024-05-05"),
        ("2024-06-10", "2024-06-10"),
        ("2024-09-15", "2024-09-17"),
        ("2024-10-01", "2024-10-07"),
    ),
    2025: (
        ("2025-01-01", "2025-01-01"),
        ("2025-01-28", "2025-02-04"),
        ("2025-04-04", "2025-04-06"),
        ("2025-05-01", "2025-05-05"),
        ("2025-05-31", "2025-06-02"),
        ("2025-10-01", "2025-10-08"),
    ),
    2026: (
        ("2026-01-01", "2026-01-03"),
        ("2026-02-15", "2026-02-23"),
        ("2026-04-04", "2026-04-06"),
        ("2026-05-01", "2026-05-05"),
        ("2026-06-19", "2026-06-21"),
        ("2026-09-25", "2026-09-27"),
        ("2026-10-01", "2026-10-07"),
    ),
}


def _closure_days() -> frozenset[date]:
    days: set[date] = set()
    for ranges in _CLOSURE_RANGES.values():
        for start_text, end_text in ranges:
            start, end = date.fromisoformat(start_text), date.fromisoformat(end_text)
            days.update(start + timedelta(days=offset) for offset in range((end - start).days + 1))
    return frozenset(days)


ANNOUNCED_CLOSURE_DAYS = _closure_days()


def is_announced_weekday_closure(day: date) -> bool:
    return day.weekday() < 5 and day in ANNOUNCED_CLOSURE_DAYS
