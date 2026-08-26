# Non-Production Inbound Audit and Retention Policy Lab

**Phase:** 033  
**Status:** LAB_ONLY — audit/retention review for synthetic inbound lab rows  
**Compliance boundary:** `NOT_DGII_COMPLIANT` · `dgii_submission_allowed=false`  
**Scope:** `NON_PRODUCTION_LAB_ONLY`

## 1. Purpose

Lab-only audit and retention policy for synthetic inbound XML lab records.

- No public endpoint audit ingestion
- No production fiscal audit workflow
- No DGII calls, no TrackId
- No certification claim
- Default command mode is **DRY_RUN** (no audit event write)
- **No destructive deletion** in Phase 033

## 2. Scope

- Audit lab record creation / updates (as retention review context)
- Audit lab workflow routing presence
- Audit raw XML storage choice
- Audit duplicate / idempotent ingestion signals
- Review retention age
- Review raw XML retention risk
- Generate lab-only metadata export manifests
- Produce deletion **candidates** only as dry-run decisions (no delete)

## 3. Boundary warning

- Audit event ≠ DGII audit trail
- Retention review ≠ legal retention policy
- Export manifest ≠ certification evidence
- Cleanup candidate ≠ approved deletion
- Public routes cannot invoke this policy in Phase 033
- All outputs are `NON_PRODUCTION_LAB_ONLY`

## 4. Lab audit event vocabulary

| Event type | Meaning |
|---|---|
| `LAB_AUDIT_RECORD_CREATED` | Lab record create context |
| `LAB_AUDIT_RECORD_UPDATED` | Lab record update context |
| `LAB_AUDIT_WORKFLOW_ROUTED` | Workflow events present |
| `LAB_AUDIT_DUPLICATE_DETECTED` | Duplicate/idempotent signal |
| `LAB_AUDIT_RAW_XML_STORED` | Raw XML stored on lab row |
| `LAB_AUDIT_RETENTION_REVIEWED` | Retention decision computed |
| `LAB_AUDIT_EXPORT_MANIFEST_CREATED` | Metadata export written |
| `LAB_AUDIT_PURGE_CANDIDATE_IDENTIFIED` | Age/policy purge candidate |
| `LAB_AUDIT_MANUAL_REVIEW_REQUIRED` | Policy violation / unsafe flags |

## 5. Retention policy vocabulary

| Decision | Meaning |
|---|---|
| `LAB_RETENTION_KEEP` | Recent safe lab row |
| `LAB_RETENTION_REVIEW` | Needs human/lab review |
| `LAB_RETENTION_PURGE_CANDIDATE` | Older than retention days (candidate only) |
| `LAB_RETENTION_RAW_XML_REVIEW` | Raw XML stored — review retention risk |
| `LAB_RETENTION_EXPORT_READY` | Suitable for metadata export |
| `LAB_RETENTION_ERROR` | Policy evaluation error |

## 6. Suggested policy rules (priority)

1. `certification_evidence=true` → `LAB_AUDIT_MANUAL_REVIEW_REQUIRED` / policy violation
2. `dgii_submission_allowed=true` → policy violation
3. `track_id` not null/blank → policy violation
4. `dgii_call_made=true` → policy violation
5. `persisted_raw_xml=true` → `LAB_RETENTION_RAW_XML_REVIEW`
6. Age > retention_days → `LAB_RETENTION_PURGE_CANDIDATE` (+ purge-candidate audit type)
7. Otherwise recent safe → `LAB_RETENTION_KEEP` (`LAB_AUDIT_RETENTION_REVIEWED`)

No delete action by default. Phase 033 never purges rows.

## 7. Lab pipeline

1. Load lab records and related workflow events
2. Compute audit/retention decision
3. Dry-run by default
4. Optionally persist `InboundXMLLabAuditEvent` with `--apply-lab-audit`
5. Optionally write metadata-only JSON under `runtime/dgii_lab_exports/`
6. No production mutation, no public endpoint, no DGII, no TrackId

```bash
python manage.py dgii_inbound_audit_retention_lab --from-lab-records
python manage.py dgii_inbound_audit_retention_lab --from-lab-records --json
python manage.py dgii_inbound_audit_retention_lab --from-lab-records --apply-lab-audit --json
python manage.py dgii_inbound_audit_retention_lab --from-lab-records --export-manifest --json
```

## 8. Exit criteria

- [x] Audit/retention command works (dry-run default)
- [x] JSON output parseable
- [x] Dry-run writes no audit events
- [x] Explicit apply writes lab-only audit events
- [x] Export manifest only under explicit flag; metadata only
- [x] No destructive delete in Phase 033
- [x] Public `/fe/...` routes remain 503 DISABLED
- [x] Readiness remains `BLOCKED` / `NOT_DGII_COMPLIANT`

## Related artifacts

- `ecf/models.py` — `InboundXMLLabAuditEvent`
- `ecf/dgii/inbound_audit_retention_lab.py`
- `ecf/management/commands/dgii_inbound_audit_retention_lab.py`

## Next phase

**Phase 035** — security-owner sign-off / staging rehearsal checklist — still no public endpoints, no DGII live, no TrackId.
