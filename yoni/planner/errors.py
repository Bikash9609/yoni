"""Planner errors."""

from __future__ import annotations


class PlanError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        block_id: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.block_id = block_id
        self.suggestion = suggestion
        super().__init__(message)
