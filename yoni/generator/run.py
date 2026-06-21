"""Generation orchestration — scope, queue, session."""

from __future__ import annotations

from pathlib import Path

from yoni.generator.errors import GenerateError
from yoni.generator.manifest import load_manifest, save_manifest
from yoni.generator.models import (
    GenerationLayer,
    GenerationManifest,
    GenerationSession,
    ScopeRequest,
)
from yoni.generator.plans import load_plans
from yoni.generator.queue import build_queue
from yoni.generator.scope import resolve_scope
from yoni.generator.session import (
    create_session,
    invalidate_for_impact,
    load_session,
    next_pending,
    save_session,
)
from yoni.impact.engine import ImpactResult, compute_impact
from yoni.pipeline import compile_workspace


def prepare_generation(
    root: Path | str,
    scope: ScopeRequest,
    *,
    require_valid: bool = True,
    session_id: str | None = None,
) -> tuple[GenerationSession, Path, Path]:
    """Compile, resolve scope, build queue, persist session + manifest shell."""
    project_root = Path(root).resolve()
    result = compile_workspace(project_root, write_cache=True)
    if result.normalized is None or result.graph is None:
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

    resolved = resolve_scope(result.normalized, result.graph, scope)
    plans = load_plans(
        project_root,
        resolved.intent_ids,
        require_valid=require_valid,
    )
    queue = build_queue(plans, resolved, result.normalized)
    if not queue:
        raise GenerateError(
            "YONI5009",
            "Scope resolved to zero generation jobs",
            suggestion="Check targets and --layer filters.",
        )

    session = create_session(
        scope,
        resolved.intent_ids,
        queue,
        session_id=session_id,
    )
    session_path = save_session(project_root, session)
    manifest = load_manifest(project_root)
    manifest_path = save_manifest(project_root, manifest)
    return session, session_path, manifest_path


def continue_session(root: Path | str, session_id: str) -> GenerationSession:
    session = load_session(root)
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
    return session


def prepare_impact_regen(
    root: Path | str,
    block_id: str,
    *,
    require_valid: bool = True,
) -> tuple[GenerationSession, GenerationManifest, ImpactResult, list[str], list[str]]:
    project_root = Path(root).resolve()
    session = load_session(project_root)
    if session is None:
        raise GenerateError(
            "YONI5010",
            "No generation session found",
            suggestion="Run `yoni generate --intent <ID>` before impact regen.",
        )

    result = compile_workspace(project_root, write_cache=True)
    if result.graph is None:
        raise GenerateError(
            "YONI5007",
            "Compile failed — graph unavailable",
            suggestion="Fix parse errors before regenerating.",
        )
    if require_valid and not result.ok:
        err_count = len(
            error for error in result.validation_errors if error.severity == "error"
        )
        raise GenerateError(
            "YONI5008",
            f"Validation failed with {err_count} error(s)",
            suggestion="Fix validation errors before regenerating.",
        )

    impact = compute_impact(result.graph, block_id.upper())
    session, manifest, requeued, stale_paths = invalidate_for_impact(
        project_root,
        session,
        impact,
    )
    return session, manifest, impact, requeued, stale_paths


def scope_from_intent(intent_id: str, *, stack: str = "python") -> ScopeRequest:
    return ScopeRequest(
        targets=[intent_id.upper()],
        layers=[GenerationLayer.BACKEND],
        stack=stack,
    )


def scope_from_domain(domain: str, *, stack: str = "python") -> ScopeRequest:
    return ScopeRequest(
        targets=[domain.lower()],
        layers=[GenerationLayer.BACKEND],
        stack=stack,
    )
