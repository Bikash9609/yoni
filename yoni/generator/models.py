"""Generation scope, queue, session, and manifest models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from yoni.planner.models import JobType


class GenerationLayer(str, Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    INFRA = "infra"
    TESTS = "tests"
    DOCS = "docs"


class JobStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class ScopeRequest(BaseModel):
    targets: list[str] = Field(default_factory=list)
    layers: list[GenerationLayer] = Field(
        default_factory=lambda: [GenerationLayer.BACKEND]
    )
    stack: str = "python"


class ResolvedScope(BaseModel):
    targets: list[str]
    intent_ids: list[str] = Field(default_factory=list)
    block_closure: set[str] = Field(default_factory=set)
    layers: list[GenerationLayer] = Field(default_factory=list)
    stack: str = "python"


class GenerationJob(BaseModel):
    id: str
    type: JobType
    block: str
    intent: str | None = None
    status: JobStatus = JobStatus.PENDING
    artifact: str | None = None
    depends: list[str] = Field(default_factory=list)


class ManifestEntry(BaseModel):
    path: str
    block_ids: list[str] = Field(default_factory=list)
    job_id: str
    checksum: str = ""
    generated_at: str = ""


class GenerationSession(BaseModel):
    session_id: str
    scope: ScopeRequest
    intent_ids: list[str] = Field(default_factory=list)
    queue: list[GenerationJob] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class GenerationManifest(BaseModel):
    entries: dict[str, ManifestEntry] = Field(default_factory=dict)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
