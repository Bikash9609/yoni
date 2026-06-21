"""CLI for generation scope, queue, and session."""

from __future__ import annotations

import argparse
from pathlib import Path

from yoni.generator.errors import GenerateError
from yoni.generator.models import GenerationLayer
from yoni.generator.run import (
    continue_session,
    next_pending,
    prepare_generation,
    prepare_impact_regen,
    scope_from_domain,
    scope_from_intent,
)
from yoni.generator.session import save_session


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="yoni generate")
    parser.add_argument(
        "--root",
        default="samples/invoicing",
        help="Project root containing .yoni files",
    )
    parser.add_argument(
        "--intent",
        help="Intent block id to generate (e.g. INT_REGISTER_USER_001)",
    )
    parser.add_argument(
        "--domain",
        help="Domain folder name — all intents in domain (e.g. customer)",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        help="Explicit target block ids or domain names",
    )
    parser.add_argument(
        "--layer",
        action="append",
        choices=[layer.value for layer in GenerationLayer],
        help="Generation layer filter (repeatable, default: backend)",
    )
    parser.add_argument(
        "--stack",
        default="python",
        help="Target stack/language (default: python)",
    )
    parser.add_argument(
        "--continue",
        dest="continue_id",
        metavar="SESSION_ID",
        help="Load session and show next pending job",
    )
    parser.add_argument(
        "--impact",
        metavar="BLOCK_ID",
        help="Requeue jobs affected by a spec change (uses impact analysis)",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Prepare queue even when validation errors exist",
    )
    parser.add_argument(
        "--list-queue",
        action="store_true",
        help="With --continue, list full queue instead of next job only",
    )
    args = parser.parse_args(argv)

    project_root = Path(args.root).resolve()

    if args.continue_id:
        return _continue(project_root, args.continue_id, list_queue=args.list_queue)

    if args.impact:
        return _impact(
            project_root,
            args.impact,
            require_valid=not args.skip_validation,
        )

    scope = _build_scope(args)
    if scope is None:
        parser.error("one of --intent, --domain, or --targets is required")

    try:
        session, session_path, manifest_path = prepare_generation(
            project_root,
            scope,
            require_valid=not args.skip_validation,
        )
    except GenerateError as error:
        print(f"{error.code}: {error.message}")
        if error.suggestion:
            print(f"suggestion: {error.suggestion}")
        return 1

    print(f"session {session.session_id} ({len(session.queue)} jobs)")
    print(f"intents: {', '.join(session.intent_ids)}")
    print(f"-> {session_path}")
    print(f"-> {manifest_path}")
    for job in session.queue:
        print(f"  {job.id} [{job.status.value}] {job.type.value} {job.block} -> {job.artifact}")
    return 0


def _build_scope(args: argparse.Namespace):
    layers = args.layer or [GenerationLayer.BACKEND.value]
    layer_enums = [GenerationLayer(value) for value in layers]

    if args.intent:
        scope = scope_from_intent(args.intent, stack=args.stack)
        scope.layers = layer_enums
        return scope
    if args.domain:
        scope = scope_from_domain(args.domain, stack=args.stack)
        scope.layers = layer_enums
        return scope
    if args.targets:
        from yoni.generator.models import ScopeRequest

        return ScopeRequest(
            targets=list(args.targets),
            layers=layer_enums,
            stack=args.stack,
        )
    return None


def _continue(project_root: Path, session_id: str, *, list_queue: bool) -> int:
    try:
        session = continue_session(project_root, session_id)
    except GenerateError as error:
        print(f"{error.code}: {error.message}")
        if error.suggestion:
            print(f"suggestion: {error.suggestion}")
        return 1

    if list_queue:
        print(f"session {session.session_id}")
        for job in session.queue:
            print(
                f"  {job.id} [{job.status.value}] {job.type.value} "
                f"{job.block} -> {job.artifact}"
            )
        return 0

    pending = next_pending(session)
    if pending is None:
        print(f"session {session.session_id}: queue complete")
        return 0

    print(f"session {session.session_id}: next {pending.id}")
    print(f"  type: {pending.type.value}")
    print(f"  block: {pending.block}")
    print(f"  artifact: {pending.artifact}")
    print(f"  depends: {', '.join(pending.depends) if pending.depends else '-'}")
    return 0


def _impact(project_root: Path, block_id: str, *, require_valid: bool) -> int:
    try:
        session, _manifest, impact, requeued, stale_paths = prepare_impact_regen(
            project_root,
            block_id,
            require_valid=require_valid,
        )
    except GenerateError as error:
        print(f"{error.code}: {error.message}")
        if error.suggestion:
            print(f"suggestion: {error.suggestion}")
        return 1

    save_session(project_root, session)
    print(f"impact {impact.block_id}: {len(impact.affected)} affected blocks")
    print(f"requeued jobs: {', '.join(requeued) if requeued else '-'}")
    print(f"removed manifest paths: {', '.join(stale_paths) if stale_paths else '-'}")
    return 0
