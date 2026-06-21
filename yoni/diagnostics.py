"""Shared diagnostic types for the Yoni compiler pipeline."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Diagnostic(BaseModel):
    code: str
    severity: Literal["error", "warning"] = "error"
    message: str
    file: str = ""
    block_id: str | None = None
    suggestion: str | None = None
    line: int | None = None
    column: int | None = None
