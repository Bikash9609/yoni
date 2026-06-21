"""CLI for execution planning."""

from __future__ import annotations

import argparse
from pathlib import Path

from yoni.planner.errors import PlanError
from yoni.planner.run import plan_and_write, plan_workspace, write_all_plans, write_plan
from yoni.pipeline import compile_workspace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="yoni plan")
    parser.add_argument(
        "block_id",
        nargs="?",
        help="Intent block id (e.g. INT_REGISTER_USER_001). Omit with --all.",
    )
    parser.add_argument(
        "--root",
        default="samples/invoicing",
        help="Project root containing .yoni files",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Plan every intent in the workspace",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Plan even when validation errors exist",
    )
    args = parser.parse_args(argv)

    project_root = Path(args.root).resolve()
    if args.all:
        return _plan_all(
            project_root,
            require_valid=not args.skip_validation,
        )

    if not args.block_id:
        parser.error("block_id is required unless --all is set")

    try:
        plan, path = plan_and_write(
            project_root,
            args.block_id,
            require_valid=not args.skip_validation,
        )
    except PlanError as error:
        print(f"{error.code}: {error.message}")
        if error.suggestion:
            print(f"suggestion: {error.suggestion}")
        return 1

    print(f"planned {plan.intent} ({len(plan.steps)} steps, {len(plan.artifacts)} artifacts)")
    print(f"-> {path}")
    return 0


def _plan_all(project_root: Path, *, require_valid: bool) -> int:
    result = compile_workspace(project_root, write_cache=True)
    if result.normalized is None or result.graph is None:
        print("YONI4004: compile failed")
        return 1
    if require_valid and not result.ok:
        err_count = len([e for e in result.validation_errors if e.severity == "error"])
        print(f"YONI4005: validation failed with {err_count} error(s)")
        return 1

    plans = plan_workspace(result.normalized, result.graph)
    assert isinstance(plans, dict)
    paths = write_all_plans(project_root, plans)
    print(f"planned {len(paths)} intents -> {project_root / '.ai' / 'generation' / 'plans'}")
    return 0
