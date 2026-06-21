"""Normalized workspace models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from yoni.ast.base import BlockKind


class FileContext(BaseModel):
    rel_path: str
    domain: str | None = None
    folder_role: str | None = None


class NormalizedRef(BaseModel):
    kind: str
    name: str
    raw: str = ""
    path: list[str] = Field(default_factory=list)
    role: str | None = None


class NormalizedBlock(BaseModel):
    block_id: str
    kind: BlockKind
    name: str
    desc: str
    version: int
    file: FileContext
    body: dict = Field(default_factory=dict)
    refs: list[NormalizedRef] = Field(default_factory=list)


class NormalizedWorkspace(BaseModel):
    root: str
    blocks: dict[str, NormalizedBlock] = Field(default_factory=dict)
    symbols: dict[str, str] = Field(default_factory=dict)

    def resolve(self, ref: NormalizedRef | str, *, domain: str | None = None) -> str | None:
        if isinstance(ref, NormalizedRef):
            if domain:
                scoped = f"{domain}:{ref.kind}.{ref.name}"
                if scoped in self.symbols:
                    return self.symbols[scoped]
            return self.symbols.get(f"{ref.kind}.{ref.name}")
        if domain and ref in self.symbols:
            return self.symbols[ref]
        return self.symbols.get(ref)
