"""CLI for impact analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

from yoni.impact.engine import compute_impact
from yoni.pipeline import compile_workspace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="yoni impact")
    parser.add_argument("block_id", help="Block id to analyze (e.g. ENT_CUSTOMER_001)")
    parser.add_argument(
        "--root",
        default="samples/invoicing",
        help="Project root containing .yoni files",
    )
    args = parser.parse_args(argv)

    result = compile_workspace(Path(args.root))
    if result.graph is None:
        print("graph build failed")
        return 1

    impact = compute_impact(result.graph, args.block_id.upper())
    if not impact.affected:
        print(f"No downstream impact for {impact.block_id}")
        return 0

    print(f"Impact for {impact.block_id}:")
    print("Affected:")
    for item in impact.affected:
        print(f"- {item.id} ({item.kind.value}) {item.name} [{item.file}]")
    return 0
