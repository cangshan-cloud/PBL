from __future__ import annotations

from contextlib import asynccontextmanager
import json

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.factors import FACTOR_REGISTRY, get_factor
from app.db import Base, engine, get_db
from app.auth import authenticate, create_access_token, get_current_user, require_roles
from app.models import Run, RunStatus, User, UserRole
from app.schemas import ComparisonRequest, CompositeResearchRequest, DatasetPreviewResponse, DatasetVersionResponse, LoginRequest, ReportSummaryResponse, ResearchRequest, RunLogResponse, RunResponse, TokenResponse, UserCreateRequest, UserResponse, UserUpdateRequest
from app.services.catalog import ensure_composite_factor, ensure_demo_catalog, ensure_factor_catalog
from app.services.cn_csv_adapter import adapt_cn_stock_csv
from app.services.datasets import (
    DatasetValidationError,
    get_dataset_version,
    import_csv,
    list_dataset_versions,
    preview_dataset,
    publish_dataset_version,
)
from app.services.dashboard import build_dashboard
from app.services.comparisons import compare_runs, comparison_csv, comparison_html
from app.services.conclusions import build_run_conclusion
from app.services.runs import create_composite_run, create_research_run, execute_research_run, get_run, list_run_logs, list_runs, request_cancellation, serialize_run
from app.services.reports import get_report, list_reports, read_verified_report
from app.services.reproducibility import build_reproducibility_bundle
from app.tasks import celery_app, execute_research_run_task
from app.services.users import create_user as create_user_record, ensure_bootstrap_users, list_users, update_user as update_user_record


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with Session(bind=engine) as session:
        ensure_demo_catalog(session)
        ensure_factor_catalog(session)
        ensure_composite_factor(session)
        ensure_bootstrap_users(session)
    yield


app = FastAPI(title="FactorLab API", version="0.22.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "factorlab-api", "version": "0.22.0"}


@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, session: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate(session, request.username, request.password)
    if user is None:
        raise HTTPException(401, "用户名或密码错误")
    return TokenResponse(access_token=create_access_token(user))


@app.get("/api/v1/auth/me", response_model=UserResponse)
def current_user(user: User = Depends(get_current_user)) -> User:
    return user


@app.get("/api/v1/dashboard")
def dashboard(user: User = Depends(get_current_user), session: Session = Depends(get_db)) -> dict:
    return build_dashboard(session, user)


@app.get("/api/v1/users", response_model=list[UserResponse])
def users(_: User = Depends(require_roles(UserRole.ADMIN)), session: Session = Depends(get_db)) -> list[User]:
    return list_users(session)


@app.post("/api/v1/users", response_model=UserResponse, status_code=201)
def create_user(request: UserCreateRequest, _: User = Depends(require_roles(UserRole.ADMIN)), session: Session = Depends(get_db)) -> User:
    try:
        return create_user_record(session, **request.model_dump())
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.patch("/api/v1/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, request: UserUpdateRequest, admin: User = Depends(require_roles(UserRole.ADMIN)), session: Session = Depends(get_db)) -> User:
    target = session.get(User, user_id)
    if target is None:
        raise HTTPException(404, "用户不存在")
    if not request.model_fields_set:
        raise HTTPException(400, "至少提供一个需要修改的字段")
    try:
        return update_user_record(session, target, actor_id=admin.id, **request.model_dump())
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/v1/factors")
def factors(_: User = Depends(get_current_user)) -> list[dict]:
    return [definition.public_dict() for definition in FACTOR_REGISTRY.values()]


@app.post("/api/v1/datasets/import", response_model=DatasetVersionResponse, status_code=201)
async def import_dataset(
    dataset_key: str = Form(...),
    name: str = Form(...),
    normalize_cn_csv: bool = Form(False),
    file: UploadFile = File(...),
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: Session = Depends(get_db),
) -> DatasetVersionResponse:
    settings = get_settings()
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(413, f"上传文件不能超过{settings.max_upload_bytes // 1024 // 1024}MB")
    try:
        adapter_report = None
        if normalize_cn_csv:
            adapted = adapt_cn_stock_csv(content)
            content = adapted.content
            adapter_report = {"adapter_report": adapted.report}
        dataset = import_csv(
            session,
            content=content,
            source_filename=file.filename or "upload.csv",
            dataset_key=dataset_key,
            name=name,
            data_root=settings.data_root,
            quality_metadata=adapter_report,
        )
    except DatasetValidationError as exc:
        raise HTTPException(422, detail={"message": str(exc), "quality_report": exc.report}) from exc
    return DatasetVersionResponse.model_validate(dataset)


@app.post("/api/v1/datasets/adapt/preview")
async def preview_adapted_dataset(
    file: UploadFile = File(...),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> dict:
    settings = get_settings()
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(413, f"上传文件不能超过{settings.max_upload_bytes // 1024 // 1024}MB")
    try:
        adapted = adapt_cn_stock_csv(content)
    except DatasetValidationError as exc:
        raise HTTPException(422, detail={"message": str(exc), "quality_report": exc.report}) from exc
    return {"report": adapted.report, "preview": adapted.preview}


@app.get("/api/v1/datasets", response_model=list[DatasetVersionResponse])
def datasets(_: User = Depends(get_current_user), session: Session = Depends(get_db)) -> list[DatasetVersionResponse]:
    return [DatasetVersionResponse.model_validate(item) for item in list_dataset_versions(session)]


@app.get("/api/v1/datasets/{dataset_id}", response_model=DatasetVersionResponse)
def dataset_detail(dataset_id: str, _: User = Depends(get_current_user), session: Session = Depends(get_db)) -> DatasetVersionResponse:
    dataset = get_dataset_version(session, dataset_id)
    if dataset is None:
        raise HTTPException(404, "数据版本不存在")
    return DatasetVersionResponse.model_validate(dataset)


@app.get("/api/v1/datasets/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def dataset_preview(dataset_id: str, limit: int = 20, _: User = Depends(get_current_user), session: Session = Depends(get_db)) -> dict:
    dataset = get_dataset_version(session, dataset_id)
    if dataset is None:
        raise HTTPException(404, "数据版本不存在")
    try:
        return preview_dataset(dataset, limit)
    except FileNotFoundError as exc:
        raise HTTPException(410, "数据文件已丢失") from exc
    except ValueError as exc:
        raise HTTPException(409, "数据文件校验失败") from exc


@app.post("/api/v1/datasets/{dataset_id}/publish", response_model=DatasetVersionResponse)
def publish_dataset(dataset_id: str, _: User = Depends(require_roles(UserRole.ADMIN)), session: Session = Depends(get_db)) -> DatasetVersionResponse:
    dataset = get_dataset_version(session, dataset_id)
    if dataset is None:
        raise HTTPException(404, "数据版本不存在")
    try:
        dataset = publish_dataset_version(session, dataset)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return DatasetVersionResponse.model_validate(dataset)


@app.post("/api/v1/research/tasks", response_model=RunResponse, status_code=201)
def create_task(request: ResearchRequest, user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RESEARCHER)), session: Session = Depends(get_db)) -> dict:
    try:
        get_factor(request.factor)
        run = create_research_run(session, request.model_dump(mode="json"), created_by_id=user.id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if get_settings().task_execution_mode == "inline":
        try:
            run = execute_research_run(session, run.id)
        except Exception:
            run = get_run(session, run.id)
            if run is None:
                raise HTTPException(500, "研究任务执行失败且状态不可读取")
    else:
        execute_research_run_task.apply_async(args=[run.id], task_id=run.id)
    return serialize_run(run)


@app.post("/api/v1/research/composite-tasks", response_model=RunResponse, status_code=201)
def create_composite_task(request: CompositeResearchRequest, user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RESEARCHER)), session: Session = Depends(get_db)) -> dict:
    try:
        run = create_composite_run(session, request.model_dump(mode="json"), created_by_id=user.id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if get_settings().task_execution_mode == "inline":
        try:
            run = execute_research_run(session, run.id)
        except Exception:
            run = get_run(session, run.id)
    else:
        execute_research_run_task.apply_async(args=[run.id], task_id=run.id)
    if run is None:
        raise HTTPException(500, "多因子任务状态不可读取")
    return serialize_run(run)


@app.get("/api/v1/research/tasks", response_model=list[RunResponse])
def research_tasks(user: User = Depends(get_current_user), session: Session = Depends(get_db)) -> list[dict]:
    runs = list_runs(session)
    if user.role == UserRole.RESEARCHER:
        runs = [run for run in runs if run.experiment.created_by_id == user.id]
    return [serialize_run(run) for run in runs]


@app.get("/api/v1/research/tasks/{task_id}", response_model=RunResponse)
def get_task(task_id: str, user: User = Depends(get_current_user), session: Session = Depends(get_db)) -> dict:
    run = get_run(session, task_id)
    if run is None:
        raise HTTPException(404, "研究任务不存在")
    if user.role == UserRole.RESEARCHER and run.experiment.created_by_id != user.id:
        raise HTTPException(403, "无权查看其他研究员的任务")
    return serialize_run(run)


@app.get("/api/v1/research/tasks/{task_id}/reproducibility.json")
def download_reproducibility_bundle(task_id: str, user: User = Depends(get_current_user), session: Session = Depends(get_db)) -> Response:
    run = _task_for_user(task_id, user, session)
    content = json.dumps(jsonable_encoder(build_reproducibility_bundle(run)), ensure_ascii=False, sort_keys=True, allow_nan=False)
    return Response(
        content=content,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="factor-run-{task_id[:8]}.json"'},
    )


@app.get("/api/v1/research/tasks/{task_id}/conclusion")
def get_task_conclusion(task_id: str, user: User = Depends(get_current_user), session: Session = Depends(get_db)) -> dict:
    run = _task_for_user(task_id, user, session)
    try:
        return build_run_conclusion(run)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post("/api/v1/research/comparisons")
def compare_research_tasks(request: ComparisonRequest, user: User = Depends(get_current_user), session: Session = Depends(get_db)) -> dict:
    runs = _comparison_runs_for_user(request.run_ids, user, session)
    try:
        return compare_runs(runs)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


def _comparison_runs_for_user(run_ids: list[str], user: User, session: Session) -> list[Run]:
    runs = []
    for run_id in run_ids:
        run = get_run(session, run_id)
        if run is None:
            raise HTTPException(404, f"研究任务不存在: {run_id}")
        if user.role == UserRole.RESEARCHER and run.experiment.created_by_id != user.id:
            raise HTTPException(403, "无权对比其他研究员的任务")
        runs.append(run)
    return runs


def _comparison_result(request: ComparisonRequest, user: User, session: Session) -> dict:
    try:
        return compare_runs(_comparison_runs_for_user(request.run_ids, user, session))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/v1/research/comparisons/export.csv")
def export_research_comparison_csv(request: ComparisonRequest, user: User = Depends(get_current_user), session: Session = Depends(get_db)) -> Response:
    content = comparison_csv(_comparison_result(request, user, session))
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="factorlab-comparison.csv"'},
    )


@app.post("/api/v1/research/comparisons/export.html")
def export_research_comparison_html(request: ComparisonRequest, user: User = Depends(get_current_user), session: Session = Depends(get_db)) -> Response:
    content = comparison_html(_comparison_result(request, user, session))
    return Response(
        content=content,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="factorlab-comparison.html"'},
    )


def _task_for_user(task_id: str, user: User, session: Session) -> Run:
    run = get_run(session, task_id)
    if run is None:
        raise HTTPException(404, "研究任务不存在")
    if user.role == UserRole.RESEARCHER and run.experiment.created_by_id != user.id:
        raise HTTPException(403, "无权操作其他研究员的任务")
    return run


@app.get("/api/v1/research/tasks/{task_id}/logs", response_model=list[RunLogResponse])
def task_logs(task_id: str, user: User = Depends(get_current_user), session: Session = Depends(get_db)):
    _task_for_user(task_id, user, session)
    return list_run_logs(session, task_id)


@app.post("/api/v1/research/tasks/{task_id}/cancel", response_model=RunResponse)
def cancel_task(task_id: str, user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RESEARCHER)), session: Session = Depends(get_db)) -> dict:
    run = _task_for_user(task_id, user, session)
    try:
        run = request_cancellation(session, run, user.display_name)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    if run.status == RunStatus.CANCELLED and get_settings().task_execution_mode != "inline":
        celery_app.control.revoke(run.id, terminate=False)
    return serialize_run(run)


@app.post("/api/v1/research/tasks/{task_id}/retry", response_model=RunResponse, status_code=201)
def retry_task(task_id: str, user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RESEARCHER)), session: Session = Depends(get_db)) -> dict:
    source = _task_for_user(task_id, user, session)
    if source.status not in {RunStatus.FAILED, RunStatus.CANCELLED}:
        raise HTTPException(409, "只有失败或已取消的任务可以重试")
    if source.experiment.parameters.get("mode") == "composite":
        run = create_composite_run(session, dict(source.experiment.parameters), created_by_id=user.id)
    else:
        run = create_research_run(session, dict(source.experiment.parameters), created_by_id=user.id)
    if get_settings().task_execution_mode == "inline":
        try:
            run = execute_research_run(session, run.id)
        except Exception:
            run = get_run(session, run.id)
    else:
        execute_research_run_task.apply_async(args=[run.id], task_id=run.id)
    if run is None:
        raise HTTPException(500, "重试任务状态不可读取")
    return serialize_run(run)


@app.get("/api/v1/reports", response_model=list[ReportSummaryResponse])
def reports(user: User = Depends(get_current_user), session: Session = Depends(get_db)) -> list[dict]:
    return list_reports(session, user.id if user.role == UserRole.RESEARCHER else None)


def _report_content(run_id: str, session: Session, user: User) -> bytes:
    item = get_report(session, run_id)
    if item is None:
        raise HTTPException(404, "研究报告不存在")
    run, artifact = item
    if user.role == UserRole.RESEARCHER and run.experiment.created_by_id != user.id:
        raise HTTPException(403, "无权查看其他研究员的报告")
    try:
        return read_verified_report(artifact)
    except FileNotFoundError as exc:
        raise HTTPException(410, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/v1/reports/{run_id}/html", response_class=HTMLResponse)
def preview_report(run_id: str, user: User = Depends(get_current_user), session: Session = Depends(get_db)) -> HTMLResponse:
    return HTMLResponse(_report_content(run_id, session, user))


@app.get("/api/v1/reports/{run_id}/download")
def download_report(run_id: str, user: User = Depends(get_current_user), session: Session = Depends(get_db)) -> Response:
    content = _report_content(run_id, session, user)
    return Response(
        content=content,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="factor-report-{run_id[:8]}.html"'},
    )
