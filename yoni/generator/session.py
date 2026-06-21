"""Generation session persistence and queue control."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from yoni.generator.manifest import (
    load_manifest,
    paths_for_blocks,
    remove_entries,
    save_manifest,
)
from yoni.generator.models import (
    GenerationJob,
    GenerationManifest,
    GenerationSession,
    JobStatus,
    ScopeRequest,
    utc_now_iso,
)
from yoni.impact.engine import ImpactResult


def session_path(root: Path) -> Path:
    return root / ".ai" / "generation" / "session.json"


def load_session(root: Path | str) -> GenerationSession | None:
    path = session_path(Path(root))
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return GenerationSession.model_validate(payload)


def save_session(root: Path | str, session: GenerationSession) -> Path:
    project_root = Path(root)
    session.updated_at = utc_now_iso()
    path = session_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(session.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def create_session(
    scope: ScopeRequest,
    intent_ids: list[str],
    queue: list[GenerationJob],
    *,
    session_id: str | None = None,
) -> GenerationSession:
    now = utc_now_iso()
    return GenerationSession(
        session_id=session_id or f"gen_{uuid.uuid4().hex[:8]}",
        scope=scope,
        intent_ids=intent_ids,
        queue=queue,
        created_at=now,
        updated_at=now,
    )


def next_pending(session: GenerationSession) -> GenerationJob | None:
    for job in session.queue:
        if job.status == JobStatus.PENDING:
            return job
    return None


def mark_job_done(
    session: GenerationSession,
    job_id: str,
    *,
    artifact: str | None = None,
) -> GenerationJob:
    for index, job in enumerate(session.queue):
        if job.id != job_id:
            continue
        updated = job.model_copy(
            update={
                "status": JobStatus.DONE,
                "artifact": artifact or job.artifact,
            }
        )
        session.queue[index] = updated
        return updated
    msg = f"Job {job_id!r} not found in session"
    raise KeyError(msg)


def mark_job_failed(session: GenerationSession, job_id: str) -> GenerationJob:
    for index, job in enumerate(session.queue):
        if job.id != job_id:
            continue
        updated = job.model_copy(update={"status": JobStatus.FAILED})
        session.queue[index] = updated
        return updated
    msg = f"Job {job_id!r} not found in session"
    raise KeyError(msg)


def requeue_jobs_for_blocks(
    session: GenerationSession,
    block_ids: set[str],
) -> list[str]:
    """Reset queue jobs touching affected blocks back to pending."""
    requeued: list[str] = []
    for index, job in enumerate(session.queue):
        touches = job.block in block_ids or bool(set(job.depends) & block_ids)
        if not touches:
            continue
        session.queue[index] = job.model_copy(
            update={"status": JobStatus.PENDING, "artifact": job.artifact}
        )
        requeued.append(job.id)
    return requeued


def invalidate_for_impact(
    root: Path | str,
    session: GenerationSession,
    impact: ImpactResult,
) -> tuple[GenerationSession, GenerationManifest, list[str], list[str]]:
    """Requeue jobs and drop manifest entries affected by an impact result."""
    affected_ids = {impact.block_id} | {item.id for item in impact.affected}
    manifest = load_manifest(root)
    stale_paths = paths_for_blocks(manifest, affected_ids)
    remove_entries(manifest, stale_paths)
    requeued = requeue_jobs_for_blocks(session, affected_ids)
    save_session(root, session)
    save_manifest(root, manifest)
    return session, manifest, requeued, stale_paths
