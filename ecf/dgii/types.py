"""Typed structures for DGII concept mapping (report-only)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DGIIMappingStatus(str, Enum):
    """Overall readiness for a *future* e-CF draft — not compliance."""

    READY_FOR_FUTURE_DRAFT = "READY_FOR_FUTURE_DRAFT"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class DGIIIssueSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKING = "BLOCKING"


@dataclass(frozen=True)
class DGIIDocumentTypeMapping:
    """How an internal FiscalDocumentType relates to a DGII TipoeCF concept."""

    internal_code: str | None
    internal_name: str | None
    dgii_tipoe_cf_concept: str | None
    mapped: bool
    notes: str = ""


@dataclass(frozen=True)
class DGIIFieldMapping:
    """Availability of one internal field for a future DGII XML concept."""

    area: str
    internal_field: str
    dgii_concept: str
    present: bool
    value_preview: str | None = None
    notes: str = ""


@dataclass(frozen=True)
class DGIIMappingIssue:
    code: str
    severity: DGIIIssueSeverity
    message: str
    area: str = ""


@dataclass
class DGIIMappingReport:
    """Read-only mapping report for one Invoice."""

    invoice_id: int | None
    internal_code: str
    official_ncf: str | None
    official_encf: str | None
    official_ncf_present: bool
    official_encf_present: bool
    fiscal_document_type: DGIIDocumentTypeMapping
    issuer_fields: list[DGIIFieldMapping] = field(default_factory=list)
    customer_fields: list[DGIIFieldMapping] = field(default_factory=list)
    line_fields: list[DGIIFieldMapping] = field(default_factory=list)
    totals_fields: list[DGIIFieldMapping] = field(default_factory=list)
    identity_fields: list[DGIIFieldMapping] = field(default_factory=list)
    issues: list[DGIIMappingIssue] = field(default_factory=list)
    status: DGIIMappingStatus = DGIIMappingStatus.PARTIAL
    enough_internal_data_for_future_ecf_draft: bool = False
    future_catalog: str | None = None
    catalog_status: str | None = None
    source_inventory_status: dict[str, Any] | None = None
    compliance_claim: str = (
        "NOT_DGII_COMPLIANT — Phase 005 mapping report only; "
        "no official XML, signing, or DGII submission."
    )

    @property
    def blocking_issues(self) -> list[DGIIMappingIssue]:
        return [i for i in self.issues if i.severity == DGIIIssueSeverity.BLOCKING]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["issues"] = [
            {
                "code": i.code,
                "severity": i.severity.value if isinstance(i.severity, DGIIIssueSeverity) else i.severity,
                "message": i.message,
                "area": i.area,
            }
            for i in self.issues
        ]
        data["fiscal_document_type"] = asdict(self.fiscal_document_type)
        data["blocking_issue_count"] = len(self.blocking_issues)
        return data
