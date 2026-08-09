"""Lightweight helpers for mapping-report issue classification.

These are not DGII XSD validators and do not prove compliance.
"""

from __future__ import annotations

from ecf.dgii.types import DGIIIssueSeverity, DGIIMappingIssue


def issue(
    code: str,
    message: str,
    *,
    severity: DGIIIssueSeverity = DGIIIssueSeverity.WARNING,
    area: str = "",
) -> DGIIMappingIssue:
    return DGIIMappingIssue(code=code, severity=severity, message=message, area=area)


def is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False
