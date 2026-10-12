from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.factors import FACTOR_REGISTRY
from app.models import DatasetVersion, RunStatus, User, UserRole
from app.services.reports import list_reports
from app.services.runs import list_runs, serialize_run


def build_dashboard(session: Session, user: User) -> dict:
    datasets = list(session.scalars(select(DatasetVersion).order_by(DatasetVersion.created_at.desc())))
    runs = list_runs(session)
    if user.role == UserRole.RESEARCHER:
        runs = [run for run in runs if run.experiment.created_by_id == user.id]
    reports = list_reports(session, user.id if user.role == UserRole.RESEARCHER else None)
    status_counts = Counter(run.status.value for run in runs)
    completed = status_counts[RunStatus.SUCCESS.value] + status_counts[RunStatus.FAILED.value]
    published = [item for item in datasets if item.status == "published"]
    return {
        "scope": "personal" if user.role == UserRole.RESEARCHER else "global",
        "datasets": {
            "total": len(datasets),
            "published": len(published),
            "draft": len(datasets) - len(published),
            "latest_name": datasets[0].name if datasets else None,
        },
        "factors": {"builtin": len(FACTOR_REGISTRY), "composite_available": True},
        "tasks": {
            "total": len(runs),
            "by_status": {status.value: status_counts[status.value] for status in RunStatus},
            "success_rate": status_counts[RunStatus.SUCCESS.value] / completed if completed else None,
        },
        "reports": {"total": len(reports)},
        "recent_tasks": [serialize_run(run) for run in runs[:5]],
        "recent_reports": reports[:5],
    }
