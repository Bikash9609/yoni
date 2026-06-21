"""Build deduplicated generation job queue from execution plans."""

from __future__ import annotations

from yoni.generator.models import GenerationJob, JobStatus, ResolvedScope
from yoni.generator.order import sort_jobs
from yoni.generator.paths import artifact_path
from yoni.generator.scope import block_in_closure, job_allowed_for_layers
from yoni.normalizer.models import NormalizedWorkspace
from yoni.planner.models import ExecutionPlan, JobType, PlannedArtifact


def build_queue(
    plans: list[ExecutionPlan],
    resolved: ResolvedScope,
    workspace: NormalizedWorkspace,
) -> list[GenerationJob]:
    """Merge plan artifacts into a scoped, ordered job queue."""
    merged: dict[tuple[JobType, str], GenerationJob] = {}

    for plan in plans:
        for artifact in plan.artifacts:
            job = _artifact_to_job(artifact, plan.intent, resolved, workspace)
            if job is None:
                continue
            key = (job.type, job.block)
            existing = merged.get(key)
            if existing is None:
                merged[key] = job
                continue
            existing.depends = sorted(set(existing.depends) | set(job.depends))
            if existing.intent is None:
                existing.intent = job.intent

    ordered = sort_jobs(list(merged.values()))
    return _assign_job_ids(ordered)


def _artifact_to_job(
    artifact: PlannedArtifact,
    intent_id: str,
    resolved: ResolvedScope,
    workspace: NormalizedWorkspace,
) -> GenerationJob | None:
    if not block_in_closure(artifact.block, resolved):
        return None
    if not job_allowed_for_layers(artifact.job, resolved.layers):
        return None

    block = workspace.blocks.get(artifact.block)
    if block is None:
        return None

    depends = [dep for dep in artifact.depends if dep in resolved.block_closure]
    artifact_rel = artifact_path(artifact.job, block, stack=resolved.stack)

    return GenerationJob(
        id="",
        type=artifact.job,
        block=artifact.block,
        intent=intent_id if artifact.job == JobType.INTENT_HANDLER else None,
        status=JobStatus.PENDING,
        artifact=artifact_rel,
        depends=sorted(set(depends)),
    )


def _assign_job_ids(jobs: list[GenerationJob]) -> list[GenerationJob]:
    renumbered: list[GenerationJob] = []
    for index, job in enumerate(jobs, start=1):
        renumbered.append(job.model_copy(update={"id": f"job_{index:03d}"}))
    return renumbered
