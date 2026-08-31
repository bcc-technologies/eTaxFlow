# DGII Pre-Certification Readiness Checklist

## Current status

The local report is intentionally **BLOCKED** and **NOT_DGII_COMPLIANT**. It
is an operational gap report, not certification evidence. Run:

```text
.venv/bin/python manage.py dgii_readiness_report
.venv/bin/python manage.py dgii_readiness_report --json
```

Phase 024 added source-backed checklist items from newly collected DGII PDFs.
Phase 025 adds endpoint design metadata (`dgii_endpoint_plan`) — URLs remain BLOCKED until deployed.
Phase 026 adds staging DNS/SSL deployment checklist and hardened disabled route stubs — still no live DGII, no production signing.
Phase 027 adds internal receiver endpoint contract (ECF/ARECF/ACECF classification skeleton) — public routes remain disabled; no persistence or signature verification.
Phase 028 adds non-production inbound XML lab with synthetic fixtures — internal command only; not certification evidence.
Phase 029 adds local/offline inbound XSD validation (`dgii_inbound_schema_lab`) — LOCAL_OFFLINE_ONLY; local valid is not DGII acceptance.
Phase 030 adds local/offline XMLDSig inspection (`dgii_inbound_signature_lab`) — LOCAL_OFFLINE_TEST_ONLY; presence is not validity; cryptographic verification is NOT_IMPLEMENTED.
Phase 031 adds lab-only inbound persistence (`dgii_inbound_persistence_lab`) — NON_PRODUCTION_LAB_ONLY; dry-run default; not fiscal documents.
Phase 032 adds lab-only inbound workflow routing (`dgii_inbound_workflow_lab`) — NON_PRODUCTION_LAB_ONLY; dry-run default; not fiscal acceptance.
Phase 033 adds lab-only inbound audit/retention (`dgii_inbound_audit_retention_lab`) — NON_PRODUCTION_LAB_ONLY; dry-run default; no deletes; metadata export only.
Phase 034 adds inbound security controls policy review (`dgii_inbound_security_policy_lab`) — NON_PRODUCTION_LAB_ONLY; SECURITY_POLICY_BLOCKED; placeholders ≠ enforced.
Phase 035 adds inbound reporting export lab (`dgii_inbound_reporting_lab`) — NON_PRODUCTION_LAB_ONLY metadata-only JSON/CSV/Markdown/bundle; no raw XML; no production dashboard.
Phase 036 adds staging deployment evidence collector (`dgii_staging_evidence_lab`) — offline/manual evidence only; no network checks; STAGING_EVIDENCE_BLOCKED.
Phase 037 adds certification portal package draft (`dgii_certification_package_lab`) — DRAFT_ONLY; PACKAGE_BLOCKED; no portal submission.

See also:
- `docs/dgii/source_intake/PHASE_024_SOURCE_REVIEW_SUMMARY.md`
- `docs/dgii/governance/PHASE_024_DGII_AUTHORIZATION_GATE.md`
- `docs/dgii/endpoints/PRE_CERTIFICATION_ENDPOINT_DESIGN.md` (Phase 025 — design-only URLs)
- `docs/deployment/DGII_STAGING_DNS_SSL_CHECKLIST.md` (Phase 026 — staging DNS/SSL checklist)
- `docs/dgii/endpoints/PRE_CERTIFICATION_RECEIVER_ENDPOINT_CONTRACT.md` (Phase 027 — receiver contract)
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_XML_LAB.md` (Phase 028 — synthetic inbound XML lab)
- `docs/dgii/lab/LOCAL_INBOUND_SCHEMA_VALIDATION_LAB.md` (Phase 029 — local/offline XSD lab)
- `docs/dgii/lab/LOCAL_INBOUND_SIGNATURE_VERIFICATION_LAB.md` (Phase 030 — signature inspection lab)
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_PERSISTENCE_LAB.md` (Phase 031 — lab-only persistence)
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_WORKFLOW_ROUTING_LAB.md` (Phase 032 — lab-only workflow routing)
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_AUDIT_RETENTION_POLICY_LAB.md` (Phase 033 — lab-only audit/retention)
- `docs/dgii/security/INBOUND_SECURITY_CONTROLS_POLICY_REVIEW_LAB.md` (Phase 034 — security policy lab)
- `docs/dgii/lab/NON_PRODUCTION_INBOUND_REPORTING_EXPORT_LAB.md` (Phase 035 — reporting export lab)
- `docs/deployment/DGII_STAGING_DEPLOYMENT_EVIDENCE_COLLECTOR_LAB.md` (Phase 036 — staging evidence lab)
- `docs/dgii/certification/CERTIFICATION_PORTAL_SUBMISSION_PACKAGE_DRAFT.md` (Phase 037 — package draft)
- `.env.staging.example` (Phase 026 — staging env placeholders only)

## Checklist

| Area | Current status | Required human/engineering action |
|---|---|---|
| Official source inventory reviewed | MANUAL_REQUIRED | Human review of Phase 024 inventory matrix; mark gate in authorization doc. |
| Endpoint design (Phase 025) | DESIGN_ONLY | Run `dgii_endpoint_plan`; URLs blocked until DNS/HTTPS/deploy approved. |
| Software name/version/type | READY (local metadata) | Confirm final registration metadata for DGII solicitud (`PROPIO` / eTaxFlow / 0.1.0). |
| URL Recepción | BLOCKED | Planned path `/fe/recepcion/api/ecf`; not deployed or HTTPS-verified. |
| URL Aprobación Comercial | BLOCKED | Planned path `/fe/aprobacioncomercial/api/ecf`; not deployed. |
| URL Autenticación | BLOCKED | Planned template `/fe/autenticacion/api/[semilla]validacioncertificado`; not deployed. |
| Public base URL configured | BLOCKED | `ETAXFLOW_PUBLIC_BASE_URL` blank by default. |
| Public DGII endpoints enabled | BLOCKED | `ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=false`; stubs return 503 DISABLED. |
| Endpoint SSL verified | BLOCKED | HTTPS/TLS not verified for public host. |
| Endpoint internet access verified | BLOCKED | External reachability not verified. |
| RNC registered | PARTIAL | Verify issuer RNC and taxpayer records with tax owner (not demo synthetic). |
| OFV access | MANUAL_REQUIRED | Confirm OFV enrollment, access, and responsible operator. |
| Alta NCF / authorized eNCF | MANUAL_REQUIRED | Confirm authorized NCF/eNCF range workflow; local demo/XSD-facet ranges are not authorization. |
| Usuario Administrador e-CF | MANUAL_REQUIRED | Assign before authorization request; maintain RNC, OFV, certificado tributario. |
| Representative linked to RNC | MANUAL_REQUIRED | Confirm legal/tax representative and certificate linkage. |
| Certificate digital (procedimiento tributario) | BLOCKED | Select custody, certificate, rotation, and revocation process. |
| Internal software vs certified provider route | MANUAL_REQUIRED | Choose route A (own software) or B (certified provider) in authorization gate. |
| Signing readiness (SHA-256 XMLDSig) | BLOCKED | Approve production XMLDSig architecture; enveloping, `Reference URI=""`, X509 KeyInfo. |
| Acuse de Recibo (ARECF) support | NOT_IMPLEMENTED | Signed receipt-ack service; requires live endpoint + production signing. |
| Aprobación Comercial (ACECF) support | NOT_IMPLEMENTED | Signed commercial-approval service; requires live endpoint + production signing. |
| XML validation | PARTIAL | Resolve source/stub limitations; no empty tags; XML naming per emitter technical doc. |
| SSL + internet-accessible receiver services | BLOCKED | Required when live; design in Phase 025, staging checklist in Phase 026 (`docs/deployment/DGII_STAGING_DNS_SSL_CHECKLIST.md`). Deploy only with human approval. |
| Contingency policy | NOT_IMPLEMENTED | Approve and implement contingency per Instructivo Contingencia FE. |
| Printed representation policy | PARTIAL | Review official RI models; local PDF remains NON_PRODUCTION_DRAFT. |
| Logs/audit retention | PARTIAL | Define retention, export, monitoring, and review controls. |
| Backups | NOT_IMPLEMENTED | Implement encrypted backups, restore tests, and recovery ownership. |
| Secrets handling | PARTIAL | Integrate deployment secret manager; no private keys in repo. |
| Security blockers | BLOCKED | Close live transport, signing, certificate, authorization, and access-control gaps. |

## Remaining documentation

The command reads `docs/dgii/DGII_ECF_DOCUMENT_INVENTORY.md` through the local
inventory helper. Missing legal sources remain blocked until a human provides
authoritative copies:

- `Norma_General_01-2020.pdf`
- `Ley_32-23.pdf`
- `Decreto_587-24.pdf`

Official certification test cases must not be invented.

## Explicit non-claims

- No DGII endpoint is called.
- No TrackId is created.
- Local mock contracts and test-only signatures do not satisfy certification.
- A local XSD or PDF result does not establish DGII approval.
- Phase 024 source intake does not change `NOT_DGII_COMPLIANT`.
- Phase 031 `InboundXMLLabRecord` rows are not fiscal documents, DGII acceptance, or certification evidence.
- Phase 032 workflow routes are not fiscal acceptance, acuse, or aprobación generation.
- Phase 033 lab audit events are not a DGII audit trail; retention decisions are not legal retention policy.
- Phase 034 security policy lab is not production security approval; CONFIGURED_PLACEHOLDER ≠ ENFORCED.
