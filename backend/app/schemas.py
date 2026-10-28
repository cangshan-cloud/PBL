from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import RunStatus, UserRole


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    display_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z][a-zA-Z0-9_]+$")
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=10, max_length=128)
    role: UserRole


class UserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: UserRole | None = None
    is_active: bool | None = None


class ResearchRequest(BaseModel):
    price_basis: Literal["source_close", "factor_adjusted"] = "source_close"
    factor: str = "momentum_20d"
    dataset_version_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    validation_start_date: date | None = None
    symbols: list[str] | None = Field(default=None, max_length=1000)
    lookback: int | None = Field(default=None, ge=2, le=120)
    groups: int = Field(default=5, ge=2, le=10)
    winsorize: bool = True
    standardize: bool = True
    mad_scale: float = Field(default=3.0, gt=0, le=10)
    transaction_cost_bps: float = Field(default=10.0, ge=0, le=100)


class CompositeResearchRequest(BaseModel):
    price_basis: Literal["source_close", "factor_adjusted"] = "source_close"
    dataset_version_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    validation_start_date: date | None = None
    symbols: list[str] | None = Field(default=None, max_length=1000)
    factors: list[str] = Field(min_length=2, max_length=6)
    lookbacks: dict[str, int] = Field(default_factory=dict)
    groups: int = Field(default=5, ge=2, le=10)
    winsorize: bool = True
    standardize: bool = True
    mad_scale: float = Field(default=3.0, gt=0, le=10)
    transaction_cost_bps: float = Field(default=10.0, ge=0, le=100)


class HistoricalResearchRequest(BaseModel):
    dataset_version_id: str
    groups: int = Field(default=5, ge=2, le=10)
    validation_start_date: Literal["2024-07-01"] | None = None


class ComparisonRequest(BaseModel):
    run_ids: list[str] = Field(min_length=2, max_length=6)


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    artifact_type: str
    name: str
    content: dict | None
    storage_uri: str | None


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    experiment_id: str
    experiment_name: str
    status: RunStatus
    progress: int
    error_summary: str | None
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    cancellation_requested_at: datetime | None
    parameters: dict
    dataset_version_id: str
    dataset_version: str
    factor_version_id: str
    factor_version: str
    code_version: str
    result: dict | None = None


class RunLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    level: str
    event: str
    message: str
    created_at: datetime


class DatasetVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dataset_key: str
    name: str
    version: str
    market: str
    frequency: str
    start_date: date | None
    end_date: date | None
    row_count: int
    symbol_count: int
    checksum: str
    source_filename: str
    quality_report: dict
    status: str
    created_at: datetime
    published_at: datetime | None


class HistoricalBundleRegistrationRequest(BaseModel):
    bundle_id: str


class DatasetPreviewResponse(BaseModel):
    dataset_id: str
    columns: list[str]
    rows: list[dict[str, str]]
    preview_count: int
    total_rows: int
    truncated: bool


class ReportSummaryResponse(BaseModel):
    run_id: str
    experiment_name: str
    dataset_version: str
    dataset_version_id: str
    dataset_checksum_sha256: str
    factor_version: str
    created_at: datetime
    checksum: str
