"""Scan a Yoni project tree and parse all .yoni files."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from yoni.ast.base import ParseResult, YoniBlock
from yoni.errors import ParseError
from yoni.parser.engine import parse_file

_SKIP_PARTS = frozenset({".ai", "generated"})


class ParsedFile(BaseModel):
    rel_path: str
    abs_path: str
    result: ParseResult[YoniBlock]


class Workspace(BaseModel):
    root: str
    files: list[ParsedFile] = Field(default_factory=list)

    @property
    def parse_errors(self) -> list[ParseError]:
        errors: list[ParseError] = []
        for item in self.files:
            errors.extend(item.result.errors)
        return errors

    @property
    def parse_ok(self) -> bool:
        return all(f.result.ok for f in self.files)


def _should_skip(path: Path) -> bool:
    return any(part in _SKIP_PARTS for part in path.parts)


def load_workspace(root: Path | str) -> Workspace:
    project_root = Path(root).resolve()
    files: list[ParsedFile] = []
    for source in sorted(project_root.rglob("*.yoni")):
        if _should_skip(source):
            continue
        rel = str(source.relative_to(project_root))
        result = parse_file(source)
        files.append(
            ParsedFile(
                rel_path=rel,
                abs_path=str(source),
                result=result,
            )
        )
    return Workspace(root=str(project_root), files=files)
