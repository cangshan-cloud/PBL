from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.factors import calculate_factor, get_factor
from app.domain.prices import apply_price_basis
from app.domain.composite import combine_factor_observations
from app.domain.research import evaluate
from app.domain.research import Observation, PriceRow
from app.models import Artifact, DatasetVersion, Experiment, FactorVersion, Run, RunLog, RunStatus
from app.services.catalog import ensure_composite_factor, ensure_demo_catalog, ensure_factor_catalog
from app.services.sample_data import load_price_file
from app.config import get_settings
from app.versioning import source_fingerprint


TERMINAL_STATUSES = {RunStatus.SUCCESS, RunStatus.FAILED, RunStatus.CANCELLED}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def add_run_log(session: Session, run: Run, event: str, message: str, level: str = "info") -> None:
    run.logs.append(RunLog(level=level, event=event, message=message))
    session.commit()


def _normalize_sample_parameters(parameters: dict) -> dict:
    output = dict(parameters)
    basis = output.setdefault("price_basis", "source_close")
    if basis not in {"source_close", "factor_adjusted"}:
        raise ValueError("unsupported price_basis")
    start_date = output.get("start_date")
    end_date = output.get("end_date")
    if isinstance(start_date, date):
        start_date = start_date.isoformat()
    if isinstance(end_date, date):
        end_date = end_date.isoformat()
    if start_date and end_date and date.fromisoformat(start_date) > date.fromisoformat(end_date):
        raise ValueError("start_date must not be later than end_date")
    symbols = output.get("symbols")
    if symbols is not None:
        cleaned = list(dict.fromkeys(str(symbol).strip() for symbol in symbols if str(symbol).strip()))
        if not cleaned:
            raise ValueError("symbols must contain at least one non-empty symbol")
        output["symbols"] = cleaned
    output["start_date"] = start_date
    output["end_date"] = end_date
    return output


def _filter_rows(rows: list[PriceRow], symbols: list[str] | None) -> list[PriceRow]:
    if not symbols:
        return rows
    selected = set(symbols)
    filtered = [row for row in rows if row.symbol in selected]
    if not filtered:
        raise ValueError("selected symbols do not exist in the dataset")
    return filtered


def _filter_observations(observations: list[Observation], start_date: str | None, end_date: str | None) -> list[Observation]:
    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None
    filtered = [
        item for item in observations
        if (start is None or item.trade_date >= start) and (end is None or item.trade_date <= end)
    ]
    if not filtered:
        raise ValueError("no factor observations remain in the selected date range")
    return filtered


def create_research_run(session: Session, parameters: dict, created_by_id: str | None = None) -> Run:
    parameters = _normalize_sample_parameters(parameters)
    transaction_cost_bps = float(parameters.get("transaction_cost_bps", 10))
    if not 0 <= transaction_cost_bps <= 100:
        raise ValueError("transaction_cost_bps must be between 0 and 100")
    parameters["transaction_cost_bps"] = transaction_cost_bps
    demo_dataset, _ = ensure_demo_catalog(session)
    definition = get_factor(parameters.get("factor", "momentum_20d"))
    ensure_factor_catalog(session)
    factor = session.scalar(
        select(FactorVersion).where(
            FactorVersion.factor_key == definition.key,
            FactorVersion.version == definition.version,
        )
    )
    if factor is None:
        raise LookupError("factor version not found")
    dataset_id = parameters.get("dataset_version_id")
    dataset = session.get(DatasetVersion, dataset_id) if dataset_id else demo_dataset
    if dataset is None:
        raise LookupError("dataset version not found")
    if dataset.status != "published":
        raise ValueError("dataset version must be published before research")
    available_columns = set(dataset.quality_report.get("columns", ("trade_date", "symbol", "close")))
    missing_columns = sorted(set(definition.required_columns) - available_columns)
    if missing_columns:
        raise ValueError(f"dataset is missing factor columns: {', '.join(missing_columns)}")
    parameters = {**parameters, "factor": definition.key, "dataset_version_id": dataset.id}
    if definition.default_lookback is None:
        parameters.pop("lookback", None)
    elif parameters.get("lookback") is None:
        parameters["lookback"] = definition.default_lookback
    experiment = Experiment(
        name=f"{factor.name}示例研究",
        dataset_version_id=dataset.id,
        factor_version_id=factor.id,
        parameters=parameters,
        created_by_id=created_by_id,
        code_version=source_fingerprint(),
    )
    run = Run(experiment=experiment)
    session.add(run)
    session.commit()
    add_run_log(session, run, "queued", "研究任务已创建并进入等待队列")
    return get_run(session, run.id)


def create_composite_run(session: Session, parameters: dict, created_by_id: str | None = None) -> Run:
    parameters = _normalize_sample_parameters(parameters)
    transaction_cost_bps = float(parameters.get("transaction_cost_bps", 10))
    if not 0 <= transaction_cost_bps <= 100:
        raise ValueError("transaction_cost_bps must be between 0 and 100")
    parameters["transaction_cost_bps"] = transaction_cost_bps
    demo_dataset, _ = ensure_demo_catalog(session)
    factor_keys = parameters.get("factors", [])
    if len(factor_keys) < 2 or len(factor_keys) > 6 or len(set(factor_keys)) != len(factor_keys):
        raise ValueError("select between two and six distinct factors")
    definitions = [get_factor(key) for key in factor_keys]
    factor_versions = {item.factor_key: item for item in ensure_factor_catalog(session)}
    composite_factor = ensure_composite_factor(session)
    dataset_id = parameters.get("dataset_version_id")
    dataset = session.get(DatasetVersion, dataset_id) if dataset_id else demo_dataset
    if dataset is None:
        raise LookupError("dataset version not found")
    if dataset.status != "published":
        raise ValueError("dataset version must be published before research")
    available_columns = set(dataset.quality_report.get("columns", ("trade_date", "symbol", "close")))
    missing_columns = sorted(set().union(*(set(item.required_columns) for item in definitions)) - available_columns)
    if missing_columns:
        raise ValueError(f"dataset is missing factor columns: {', '.join(missing_columns)}")

    requested_lookbacks = parameters.get("lookbacks", {})
    components = []
    for definition in definitions:
        lookback = requested_lookbacks.get(definition.key, definition.default_lookback)
        if lookback is not None and not 2 <= int(lookback) <= 120:
            raise ValueError("lookback must be between 2 and 120")
        version = factor_versions[definition.key]
        components.append({"key": definition.key, "version": version.version, "lookback": lookback, "weight": 1 / len(definitions)})
    stored_parameters = {
        **parameters,
        "mode": "composite",
        "factor": composite_factor.factor_key,
        "dataset_version_id": dataset.id,
        "weighting": "equal",
        "components": components,
    }
    experiment = Experiment(
        name=f"{len(components)}因子等权组合研究",
        dataset_version_id=dataset.id,
        factor_version_id=composite_factor.id,
        parameters=stored_parameters,
        created_by_id=created_by_id,
        code_version=source_fingerprint(),
    )
    run = Run(experiment=experiment)
    session.add(run)
    session.commit()
    add_run_log(session, run, "queued", "多因子研究任务已创建并进入等待队列")
    return get_run(session, run.id)


def get_run(session: Session, run_id: str) -> Run | None:
    return session.scalar(
        select(Run)
        .where(Run.id == run_id)
        .options(
            selectinload(Run.experiment).selectinload(Experiment.dataset_version),
            selectinload(Run.experiment).selectinload(Experiment.factor_version),
            selectinload(Run.artifacts),
            selectinload(Run.logs),
        )
    )


def list_runs(session: Session) -> list[Run]:
    return list(
        session.scalars(
            select(Run)
            .order_by(Run.queued_at.desc())
            .options(
                selectinload(Run.experiment).selectinload(Experiment.dataset_version),
                selectinload(Run.experiment).selectinload(Experiment.factor_version),
                selectinload(Run.artifacts),
                selectinload(Run.logs),
            )
        )
    )


def transition(session: Session, run: Run, target: RunStatus, *, error: str | None = None) -> None:
    allowed = {
        RunStatus.PENDING: {RunStatus.RUNNING, RunStatus.CANCELLED},
        RunStatus.RUNNING: {RunStatus.SUCCESS, RunStatus.FAILED, RunStatus.CANCELLED},
    }
    if target not in allowed.get(run.status, set()):
        raise ValueError(f"invalid run transition: {run.status.value} -> {target.value}")
    run.status = target
    if target == RunStatus.RUNNING:
        run.started_at = utc_now()
        run.progress = 5
    if target in TERMINAL_STATUSES:
        run.finished_at = utc_now()
        run.progress = 100 if target == RunStatus.SUCCESS else run.progress
    run.error_summary = error
    event_messages = {
        RunStatus.RUNNING: ("started", "Worker开始执行研究任务", "info"),
        RunStatus.SUCCESS: ("completed", "研究指标与报告生成完成", "info"),
        RunStatus.FAILED: ("failed", error or "研究任务执行失败", "error"),
        RunStatus.CANCELLED: ("cancelled", error or "研究任务已取消", "warning"),
    }
    event, message, level = event_messages[target]
    run.logs.append(RunLog(level=level, event=event, message=message))
    session.commit()


def request_cancellation(session: Session, run: Run, actor_name: str) -> Run:
    if run.status in TERMINAL_STATUSES:
        raise ValueError("terminal run cannot be cancelled")
    if run.status == RunStatus.PENDING:
        transition(session, run, RunStatus.CANCELLED, error=f"由{actor_name}在执行前取消")
    else:
        if run.cancellation_requested_at is None:
            run.cancellation_requested_at = utc_now()
            run.logs.append(RunLog(level="warning", event="cancellation_requested", message=f"{actor_name}请求取消运行中任务"))
            session.commit()
    return get_run(session, run.id)


def _stop_if_cancelled(session: Session, run_id: str) -> Run:
    session.expire_all()
    run = get_run(session, run_id)
    if run is None:
        raise LookupError(f"run not found: {run_id}")
    if run.cancellation_requested_at is not None:
        transition(session, run, RunStatus.CANCELLED, error="Worker已响应取消请求")
    return run


def list_run_logs(session: Session, run_id: str) -> list[RunLog]:
    return list(session.scalars(select(RunLog).where(RunLog.run_id == run_id).order_by(RunLog.created_at)))


def execute_research_run(session: Session, run_id: str) -> Run:
    run = get_run(session, run_id)
    if run is None:
        raise LookupError(f"run not found: {run_id}")
    transition(session, run, RunStatus.RUNNING)
    try:
        run = _stop_if_cancelled(session, run_id)
        if run.status == RunStatus.CANCELLED:
            return run
        if run.experiment.code_version != source_fingerprint():
            raise ValueError("研究任务的代码指纹与当前 Worker 不一致；请使用相同源码版本重试")
        parameters = run.experiment.parameters
        dataset = run.experiment.dataset_version
        rows = load_price_file(Path(dataset.storage_uri), expected_checksum=dataset.checksum)
        add_run_log(session, run, "dataset_loaded", f"数据校验通过，读取{len(rows)}行记录")
        rows = _filter_rows(rows, parameters.get("symbols"))
        price_basis = parameters.get("price_basis", "source_close")
        if price_basis == "factor_adjusted":
            flags = dataset.quality_report.get("adapter_report", {}).get("source_adjustment_flags", [])
            if any(flag != "3" for flag in flags):
                raise ValueError("source prices are already adjusted; refusing double adjustment")
        rows = apply_price_basis(rows, price_basis)
        add_run_log(session, run, "price_basis_applied", f"研究价格口径：{price_basis}")
        resolved_symbols = sorted({row.symbol for row in rows})
        if len(resolved_symbols) < int(parameters["groups"]):
            raise ValueError("selected sample contains fewer symbols than the requested groups")
        add_run_log(session, run, "sample_selected", f"样本筛选完成，共{len(resolved_symbols)}只证券")
        composite_diagnostics = None
        if parameters.get("mode") == "composite":
            component_observations = {
                item["key"]: _filter_observations(
                    calculate_factor(item["key"], rows, item.get("lookback")),
                    parameters.get("start_date"),
                    parameters.get("end_date"),
                )
                for item in parameters["components"]
            }
            observations, composite_diagnostics = combine_factor_observations(
                component_observations,
                {item["key"]: float(item["weight"]) for item in parameters["components"]},
                winsorize=bool(parameters.get("winsorize", True)),
                standardize=bool(parameters.get("standardize", True)),
                mad_scale=float(parameters.get("mad_scale", 3.0)),
            )
            add_run_log(session, run, "factor_calculated", f"{len(component_observations)}个因子完成对齐，得到{len(observations)}个共同观测")
        else:
            observations = _filter_observations(
                calculate_factor(parameters["factor"], rows, parameters.get("lookback")),
                parameters.get("start_date"),
                parameters.get("end_date"),
            )
            add_run_log(session, run, "factor_calculated", f"因子计算完成，得到{len(observations)}个观测")
        run = _stop_if_cancelled(session, run_id)
        if run.status == RunStatus.CANCELLED:
            return run
        result = evaluate(
            observations,
            int(parameters["groups"]),
            winsorize=False if composite_diagnostics else bool(parameters.get("winsorize", True)),
            standardize=False if composite_diagnostics else bool(parameters.get("standardize", True)),
            mad_scale=float(parameters.get("mad_scale", 3.0)),
            transaction_cost_bps=float(parameters.get("transaction_cost_bps", 0)),
        )
        if composite_diagnostics:
            result["composite"] = composite_diagnostics
            result["preprocessing"] = composite_diagnostics["component_preprocessing"]
        result["sample"] = {
            "price_basis": price_basis,
            "start_date": parameters.get("start_date"),
            "end_date": parameters.get("end_date"),
            "requested_symbols": parameters.get("symbols"),
            "resolved_symbol_count": len(resolved_symbols),
        }
        add_run_log(session, run, "metrics_calculated", "IC、分组收益、多空净值和换手率计算完成")
        run = _stop_if_cancelled(session, run_id)
        if run.status == RunStatus.CANCELLED:
            return run
        run.progress = 90
        run.artifacts.append(
            Artifact(artifact_type="metrics", name="single_factor_result.json", content=result)
        )
        from app.services.reports import create_report_artifact

        run.artifacts.append(create_report_artifact(run, result, get_settings().data_root))
        session.commit()
        transition(session, run, RunStatus.SUCCESS)
    except Exception as exc:
        session.rollback()
        run = get_run(session, run_id)
        if run is not None and run.status == RunStatus.RUNNING:
            transition(session, run, RunStatus.FAILED, error=str(exc)[:1000])
        raise
    return get_run(session, run_id)


def serialize_run(run: Run) -> dict:
    result_artifact = next((item for item in run.artifacts if item.artifact_type == "metrics"), None)
    return {
        "id": run.id,
        "experiment_id": run.experiment_id,
        "experiment_name": run.experiment.name,
        "status": run.status,
        "progress": run.progress,
        "error_summary": run.error_summary,
        "queued_at": run.queued_at,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "cancellation_requested_at": run.cancellation_requested_at,
        "parameters": run.experiment.parameters,
        "dataset_version_id": run.experiment.dataset_version_id,
        "dataset_version": run.experiment.dataset_version.version,
        "factor_version_id": run.experiment.factor_version_id,
        "factor_version": run.experiment.factor_version.version,
        "code_version": run.experiment.code_version,
        "result": result_artifact.content if result_artifact else None,
    }
