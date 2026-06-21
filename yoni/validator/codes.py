"""YONI2xxx validation diagnostic factories."""

from __future__ import annotations

from yoni.validator.models import ValidationError


def unresolved_reference(
    ref: str,
    *,
    file: str = "",
    block_id: str | None = None,
) -> ValidationError:
    return ValidationError(
        code="YONI2001",
        message=f"Unresolved reference: {ref}",
        file=file,
        block_id=block_id,
        suggestion=f"Define a block for {ref} or fix the reference.",
    )


def duplicate_block_id(
    block_id: str,
    *,
    file: str = "",
    other_file: str = "",
) -> ValidationError:
    return ValidationError(
        code="YONI2002",
        message=f"Duplicate block id: {block_id} (also in {other_file})",
        file=file,
        block_id=block_id,
        suggestion="Use a unique id: value per block.",
    )


def circular_dependency(
    cycle: list[str],
    *,
    file: str = "",
    block_id: str | None = None,
) -> ValidationError:
    path = " -> ".join(cycle)
    return ValidationError(
        code="YONI2003",
        message=f"Circular dependency detected: {path}",
        file=file,
        block_id=block_id or (cycle[0] if cycle else None),
        suggestion="Break the cycle by restructuring dependencies.",
    )


def wrong_id_prefix(
    block_id: str,
    expected_prefix: str,
    *,
    file: str = "",
) -> ValidationError:
    return ValidationError(
        code="YONI2004",
        message=f"Block id {block_id!r} must start with {expected_prefix!r}",
        file=file,
        block_id=block_id,
        suggestion=f"Rename id to use prefix {expected_prefix}.",
    )


def wrong_folder(
    kind: str,
    rel_path: str,
    expected: str,
    *,
    block_id: str | None = None,
) -> ValidationError:
    return ValidationError(
        code="YONI2005",
        message=f"{kind} block in {rel_path!r} should be under {expected}",
        file=rel_path,
        block_id=block_id,
        suggestion=f"Move file to {expected}.",
    )


def non_kebab_filename(
    filename: str,
    *,
    file: str = "",
    block_id: str | None = None,
) -> ValidationError:
    return ValidationError(
        code="YONI2006",
        message=f"Filename must be kebab-case: {filename!r}",
        file=file,
        block_id=block_id,
        suggestion="Rename file using lowercase letters, digits, and hyphens.",
    )


def duplicate_symbol(
    symbol: str,
    block_id: str,
    other_id: str,
    *,
    file: str = "",
) -> ValidationError:
    return ValidationError(
        code="YONI2007",
        message=f"Duplicate symbol {symbol}: {block_id} and {other_id}",
        file=file,
        block_id=block_id,
        suggestion="Ensure each Kind.Name maps to one block id.",
    )


def orphan_domain_block(
    rel_path: str,
    domain: str,
    *,
    block_id: str | None = None,
) -> ValidationError:
    return ValidationError(
        code="YONI2008",
        message=f"Block under domain {domain!r} has no domain block",
        file=rel_path,
        block_id=block_id,
        suggestion=f"Add domains/{domain}/domain.yoni",
    )


def breaking_migration_incomplete(
    block_id: str,
    *,
    file: str = "",
) -> ValidationError:
    return ValidationError(
        code="YONI2009",
        message="Breaking migration must declare changes and affects",
        file=file,
        block_id=block_id,
        suggestion="Add non-empty changes: and affects: sections.",
    )


def string_ref_forbidden(
    value: str,
    *,
    file: str = "",
    block_id: str | None = None,
) -> ValidationError:
    return ValidationError(
        code="YONI2010",
        message=f"String reference forbidden: {value!r}; use @Type.Name",
        file=file,
        block_id=block_id,
        suggestion="Replace the string with a typed reference such as @Entity.Customer.",
    )


def breaking_change_without_migration(
    block_id: str,
    *,
    file: str = "",
) -> ValidationError:
    return ValidationError(
        code="YONI2011",
        message=f"Version bump on {block_id} requires a migration block",
        file=file,
        block_id=block_id,
        suggestion="Add a migration with breaking: true, changes:, and affects: listing this block.",
    )
