# Non-Production Inbound Workflow Routing Lab

**Phase:** 032  
**Status:** LAB_ONLY — routes synthetic lab records, not fiscal workflows  
**Compliance boundary:** `NOT_DGII_COMPLIANT` · `dgii_submission_allowed=false`  
**Workflow scope:** `NON_PRODUCTION_LAB_ONLY`

## 1. Purpose

Lab-only workflow routing for synthetic inbound XML lab records.

- No public endpoint workflow
- No production fiscal workflow
- No DGII calls, no TrackId
- No certification claim
- Default command mode is **DRY_RUN** (no workflow event write)

## 2. Scope

Route lab records by `document_type`, `classification_status`, schema result, signature result, duplicate/idempotency state, and safety flags:

- ECF review route
- ARECF review route
- ACECF review route
- Invalid XML route
- Unsupported root route
- Signature issue route
- Schema issue route
- Duplicate route
- Manual review route

## 3. Boundary warning

- Workflow route ≠ fiscal acceptance
- Workflow route ≠ DGII approval
- Workflow route does not create Invoice, Document, ECFDocument, TrackId, acuse, or aprobación
- Public routes cannot invoke this workflow in Phase 032
- All outputs are `NON_PRODUCTION_LAB_ONLY`

## 4. Workflow route vocabulary

| Route | Meaning |
|---|---|
| `LAB_ROUTE_ECF_REVIEW` | ECF lab record with no higher-priority issue |
| `LAB_ROUTE_ARECF_REVIEW` | ARECF lab record with no higher-priority issue |
| `LAB_ROUTE_ACECF_REVIEW` | ACECF lab record with no higher-priority issue |
| `LAB_ROUTE_INVALID_XML_REVIEW` | Parse/classification invalid XML |
| `LAB_ROUTE_UNSUPPORTED_ROOT_REVIEW` | Unknown/unsupported root |
| `LAB_ROUTE_SCHEMA_ISSUE_REVIEW` | Local XSD compile/validation issue |
| `LAB_ROUTE_SIGNATURE_ISSUE_REVIEW` | Missing/placeholder/unverified signature |
| `LAB_ROUTE_DUPLICATE_REVIEW` | Duplicate/idempotent re-ingest of same SHA-256 |
| `LAB_ROUTE_MANUAL_REVIEW` | Fallback manual lab review |

## 5. Workflow status vocabulary

| Status | Meaning |
|---|---|
| `LAB_ROUTED` | Workflow event persisted |
| `LAB_ROUTING_DRY_RUN` | Decision computed; no DB write |
| `LAB_ROUTING_SKIPPED` | Record skipped (e.g. limit) |
| `LAB_ROUTING_ERROR` | Routing failed |

## 6. Routing rules (priority order)

1. `INVALID_XML` / parse error → `LAB_ROUTE_INVALID_XML_REVIEW`
2. `UNSUPPORTED_ROOT` / unknown root → `LAB_ROUTE_UNSUPPORTED_ROOT_REVIEW`
3. Duplicate `raw_sha256` re-ingest → `LAB_ROUTE_DUPLICATE_REVIEW`
4. `local_xsd_valid` false or `xsd_compiled` false → `LAB_ROUTE_SCHEMA_ISSUE_REVIEW`
5. `signature_present` false or status in `MISSING` / `PLACEHOLDER_ONLY` / `VERIFICATION_NOT_IMPLEMENTED` → `LAB_ROUTE_SIGNATURE_ISSUE_REVIEW`
6. `document_type=ECF` → `LAB_ROUTE_ECF_REVIEW`
7. `document_type=ARECF` → `LAB_ROUTE_ARECF_REVIEW`
8. `document_type=ACECF` → `LAB_ROUTE_ACECF_REVIEW`
9. Otherwise → `LAB_ROUTE_MANUAL_REVIEW`

Schema and signature issues route **before** document-specific review routes.

## 7. Lab pipeline

1. Load lab records or analyze fixture path
2. Compute routing decision
3. Dry-run by default
4. Optionally persist `InboundXMLLabWorkflowEvent` with `--apply-lab-workflow`
5. No production mutation, no public endpoint, no DGII, no TrackId

```bash
python manage.py dgii_inbound_workflow_lab --path tests/fixtures/dgii/inbound_lab/
python manage.py dgii_inbound_workflow_lab --path tests/fixtures/dgii/inbound_lab/ --json
python manage.py dgii_inbound_workflow_lab --path tests/fixtures/dgii/inbound_lab/ --apply-lab-workflow --json
python manage.py dgii_inbound_workflow_lab --from-lab-records --json
python manage.py dgii_inbound_workflow_lab --record-id 1 --json
```

## 8. Exit criteria

- [x] Routing command works (dry-run default)
- [x] JSON output parseable
- [x] Dry-run writes no workflow events
- [x] Explicit apply writes lab-only workflow events
- [x] Public `/fe/...` routes remain 503 DISABLED
- [x] Readiness remains `BLOCKED` / `NOT_DGII_COMPLIANT`

## Related artifacts

- `ecf/models.py` — `InboundXMLLabWorkflowEvent`
- `ecf/dgii/inbound_workflow_lab.py`
- `ecf/management/commands/dgii_inbound_workflow_lab.py`

## Next phase

**Phase 035** — security-owner sign-off / staging rehearsal checklist — still no public endpoints, no DGII live, no TrackId.
