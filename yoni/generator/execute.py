"""Execute generation jobs — render, write, manifest, session."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from yoni.generator.errors import GenerateError
from yoni.generator.manifest import load_manifest, record_entry, save_manifest
from yoni.generator.models import GenerationJob, GenerationManifest, GenerationSession, JobStatus
from yoni.generator.plans import load_plan
from yoni.generator.session import load_session, mark_job_done, mark_job_failed, next_pending, save_session
from yoni.generator.templates import render_for_job
from yoni.generator.verify import verify_content
from yoni.normalizer.models import NormalizedRef, NormalizedWorkspace
from yoni.pipeline import compile_workspace
from yoni.planner.models import ExecutionPlan, JobType


class JobRunResult(BaseModel):
    job_id: str
    block: str
    job_type: JobType
    artifact: str
    status: JobStatus
    errors: list[str] = Field(default_factory=list)


def deps_satisfied(job: GenerationJob, manifest: GenerationManifest) -> bool:
    if not job.depends:
        return True
    generated_blocks: set[str] = set()
    for entry in manifest.entries.values():
        generated_blocks.update(entry.block_ids)
    return all(dep in generated_blocks for dep in job.depends)


def execute_job(
    root: Path | str,
    session: GenerationSession,
    job: GenerationJob,
    workspace: NormalizedWorkspace,
    manifest: GenerationManifest,
    *,
    plan: ExecutionPlan | None = None,
) -> JobRunResult:
    block = workspace.blocks.get(job.block)
    if block is None:
        mark_job_failed(session, job.id)
        save_session(root, session)
        raise GenerateError(
            "YONI5012",
            f"Block {job.block!r} not found in normalized workspace",
            block_id=job.block,
        )

    if not deps_satisfied(job, manifest):
        mark_job_failed(session, job.id)
        save_session(root, session)
        missing = [dep for dep in job.depends if dep not in {
            bid for entry in manifest.entries.values() for bid in entry.block_ids
        }]
        raise GenerateError(
            "YONI5013",
            f"Job {job.id} dependencies not generated: {missing}",
            block_id=job.block,
            suggestion="Run earlier queue jobs first.",
        )

    intent_plan = plan
    if job.type == JobType.INTENT_HANDLER:
        if intent_plan is None and job.intent:
            intent_plan = load_plan(root, job.intent)
        if intent_plan is None:
            mark_job_failed(session, job.id)
            save_session(root, session)
            raise GenerateError(
                "YONI5014",
                f"Execution plan required for intent handler {job.block}",
                block_id=job.block,
            )

    try:
        content = render_for_job(
            job.type,
            block,
            workspace,
            plan=intent_plan,
            manifest=manifest,
        )
    except ValueError as error:
        mark_job_failed(session, job.id)
        save_session(root, session)
        raise GenerateError(
            "YONI5015",
            str(error),
            block_id=job.block,
        ) from error

    required_markers = [job.block]
    if job.type == JobType.CONSTRAINT_IMPL:
        entity_ref = block.body.get("entity") or {}
        entity_id = (
            workspace.resolve(
                NormalizedRef.model_validate(entity_ref),
                domain=block.file.domain,
            )
            if entity_ref
            else None
        )
        if entity_id:
            required_markers.append(entity_id)

    verify_errors = verify_content(content, required_markers)
    if verify_errors:
        mark_job_failed(session, job.id)
        save_session(root, session)
        return JobRunResult(
            job_id=job.id,
            block=job.block,
            job_type=job.type,
            artifact=job.artifact or "",
            status=JobStatus.FAILED,
            errors=verify_errors,
        )

    artifact_rel = job.artifact
    if not artifact_rel:
        mark_job_failed(session, job.id)
        save_session(root, session)
        raise GenerateError(
            "YONI5016",
            f"Job {job.id} has no artifact path",
            block_id=job.block,
        )

    artifact_path = Path(root) / artifact_rel
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(content, encoding="utf-8")

    record_entry(
        manifest,
        path=artifact_rel,
        block_ids=required_markers,
        job_id=job.id,
        content=content,
    )
    save_manifest(root, manifest)

    updated = mark_job_done(session, job.id, artifact=artifact_rel)
    save_session(root, session)

    return JobRunResult(
        job_id=updated.id,
        block=updated.block,
        job_type=updated.type,
        artifact=artifact_rel,
        status=JobStatus.DONE,
    )


def run_next_job(
    root: Path | str,
    session_id: str,
    *,
    require_valid: bool = True,
) -> JobRunResult | None:
    project_root = Path(root).resolve()
    session = load_session(project_root)
    if session is None:
        raise GenerateError(
            "YONI5010",
            "No generation session found",
            suggestion="Run `yoni generate --intent <ID>` first.",
        )
    if session.session_id != session_id:
        raise GenerateError(
            "YONI5011",
            f"Session id mismatch: expected {session_id!r}, found {session.session_id!r}",
            suggestion="Use the session id from the last generate run.",
        )

    pending = next_pending(session)
    if pending is None:
        return None

    result = compile_workspace(project_root, write_cache=True)
    if result.normalized is None:
        raise GenerateError(
            "YONI5007",
            "Compile failed — workspace could not be normalized",
            suggestion="Fix parse errors before generating.",
        )
    if require_valid and not result.ok:
        err_count = len(
            error for error in result.validation_errors if error.severity == "error"
        )
        raise GenerateError(
            "YONI5008",
            f"Validation failed with {err_count} error(s)",
            suggestion="Fix validation errors before generating.",
        )

    manifest = load_manifest(project_root)
    plan: ExecutionPlan | None = None
    if pending.type == JobType.INTENT_HANDLER and pending.intent:
        plan = load_plan(project_root, pending.intent)

    return execute_job(
        project_root,
        session,
        pending,
        result.normalized,
        manifest,
        plan=plan,
    )


def run_all_pending(
    root: Path | str,
    session_id: str,
    *,
    require_valid: bool = True,
) -> list[JobRunResult]:
    results: list[JobRunResult] = []
    while True:
        result = run_next_job(root, session_id, require_valid=require_valid)
        if result is None:
            break
        results.append(result)
        if result.status == JobStatus.FAILED:
            break
    return results
