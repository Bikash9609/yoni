"""Yoni compiler CLI."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if args and args[0] == "impact":
        from yoni.impact.cli import main as impact_main

        return impact_main(args[1:])
    from yoni.compile import main as compile_main

    return compile_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
