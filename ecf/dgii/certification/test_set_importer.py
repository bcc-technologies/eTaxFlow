"""Import synthetic or explicitly sanitized local harness cases."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction

from contacts.models import Contact
from contacts.natural_keys import resolve_contact_by_natural_key
from fiscal.models import BillingIndicator, FiscalDocumentType, FiscalIncomeType, PaymentType
from invoicing.models import Invoice, InvoiceLine, ProductService
from organizations.models import Organization


@dataclass(frozen=True)
class ImportedCertificationCase:
    case_id: str
    invoice: Invoice
    source_kind: str


def load_test_set(path: Path | str) -> dict[str, Any]:
    """Load a local JSON fixture and reject unmarked/official invented data."""
    fixture_path = Path(path)
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not load local certification fixture: {fixture_path}") from exc
    fixture_kind = payload.get("fixture_kind")
    if fixture_kind not in {"synthetic", "sanitized"}:
        raise ValueError("Fixture must be explicitly marked synthetic or sanitized.")
    if payload.get("official") is True and fixture_kind != "sanitized":
        raise ValueError("Official certification rows require a supplied sanitized fixture.")
    if not payload.get("disclaimer"):
        raise ValueError("Fixture must include a disclaimer describing its provenance.")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Fixture must contain a non-empty cases list.")
    return payload


def _decimal(value: Any, default: str = "0.00") -> Decimal:
    return Decimal(str(value if value is not None else default))


@transaction.atomic
def import_case_rows(payload: dict[str, Any]) -> list[ImportedCertificationCase]:
    """Map fixture rows to local Invoice/InvoiceLine records, idempotently."""
    source_kind = str(payload["fixture_kind"])
    User = get_user_model()
    actor, _ = User.objects.get_or_create(
        username="certification-harness",
        defaults={"email": "certification-harness@example.invalid"},
    )
    actor.set_unusable_password()
    actor.save(update_fields=["password"])

    imported: list[ImportedCertificationCase] = []
    for case in payload["cases"]:
        case_id = str(case.get("case_id") or "")
        row = case.get("invoice") or {}
        if not case_id or not row.get("internal_code"):
            raise ValueError("Each certification case requires case_id and invoice.internal_code.")
        issuer_row = row.get("issuer") or {}
        customer_row = row.get("customer") or {}
        issuer, _ = Organization.objects.get_or_create(
            rnc=str(issuer_row["rnc"]),
            defaults={
                "legal_name": str(issuer_row.get("legal_name") or "Synthetic Issuer"),
                "address": str(issuer_row.get("address") or "Synthetic local address"),
                "is_default_issuer": False,
            },
        )
        customer, _, _warnings = resolve_contact_by_natural_key(
            "CLIENT",
            str(customer_row["rnc_or_id"]),
            defaults={
                "legal_name": str(customer_row.get("legal_name") or "Synthetic Customer"),
                "id_type": "RNC",
                "address": str(customer_row.get("address") or "Synthetic local address"),
                "is_active": True,
            },
            update_existing=False,
        )
        fiscal_type, _ = FiscalDocumentType.objects.get_or_create(
            code=str(row.get("fiscal_document_type_code") or "31"),
            defaults={
                "name": "Synthetic Tipo e-CF",
                "document_group": "INVOICE",
                "direction": "OUTBOUND",
            },
        )
        income_type, _ = FiscalIncomeType.objects.get_or_create(
            code=str(row.get("income_type_code") or "01"),
            defaults={"name": "Synthetic income type"},
        )
        payment_type, _ = PaymentType.objects.get_or_create(
            code=str(row.get("payment_type_code") or "1"),
            defaults={"name": "Synthetic payment type"},
        )
        invoice, _ = Invoice.objects.update_or_create(
            internal_code=str(row["internal_code"]),
            defaults={
                "issuer": issuer,
                "customer": customer,
                "invoice_direction": "OUTBOUND",
                "lifecycle_status": "DRAFT",
                "currency": str(row.get("currency") or "DOP"),
                "issue_date": date.fromisoformat(str(row.get("issue_date") or "2026-01-15")),
                "due_date": None,
                "official_encf": str(row.get("official_encf") or ""),
                "sequence_expiration_date": date(2030, 12, 31),
                "fiscal_document_type": fiscal_type.code,
                "fiscal_document_type_ref": fiscal_type,
                "income_type": income_type,
                "payment_type": payment_type,
                "notes": f"CERTIFICATION_HARNESS_{source_kind.upper()}_{case_id}",
                "created_by": actor,
            },
        )
        billing_indicator, _ = BillingIndicator.objects.get_or_create(
            code="1", defaults={"name": "Synthetic taxable"}
        )
        for line_row in row.get("lines") or []:
            line_order = int(line_row.get("line_order") or 1)
            product, _ = ProductService.objects.get_or_create(
                code=f"HARNESS-{case_id}-{line_order}",
                defaults={
                    "name": str(line_row.get("description") or "Synthetic item"),
                    "item_type": "SERVICE",
                    "default_unit_price": _decimal(line_row.get("unit_price")),
                },
            )
            quantity = _decimal(line_row.get("quantity"), "1.00")
            unit_price = _decimal(line_row.get("unit_price"))
            tax_rate = _decimal(line_row.get("tax_rate"))
            tax_amount = quantity * unit_price * tax_rate / Decimal("100")
            InvoiceLine.objects.update_or_create(
                invoice=invoice,
                line_order=line_order,
                defaults={
                    "product_service": product,
                    "description": str(line_row.get("description") or product.name),
                    "item_name_snapshot": product.name,
                    "item_code_snapshot": product.code,
                    "unit_snapshot": "UND",
                    "tax_rate_snapshot": str(line_row.get("tax_rate") or "0.00"),
                    "currency_snapshot": invoice.currency,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "tax_rate": tax_rate,
                    "tax_amount": tax_amount,
                    "line_total": quantity * unit_price + tax_amount,
                    "billing_indicator": billing_indicator,
                },
            )
        invoice.refresh_from_db()
        imported.append(
            ImportedCertificationCase(case_id=case_id, invoice=invoice, source_kind=source_kind)
        )
    return imported
