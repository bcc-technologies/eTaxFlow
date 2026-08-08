# Audit report: eTaxFlow

## 1. Executive summary

The repository currently looks like a small, early-stage Python prototype for invoice generation rather than a complete invoice-management platform. It contains a basic demo flow that creates an invoice object, prints a summary, and writes example JSON and XML files. The code is lightweight and uses only the Python standard library.

What works:
- A basic invoice object can be instantiated in principle.
- The app can generate example JSON and XML artifacts locally.
- The repository includes sample output files and a minimal README.

What is broken or incomplete:
- The main entry point currently fails at runtime because the client model requires a telephone field but the demo call does not provide one.
- The runtime log path is hardcoded to a directory that may not exist, causing startup failure unless the folder is created manually.
- There is no real persistence layer, no database, no authentication, no workflow engine, and no DGII integration.
- The requirements file is empty, so the project is not clearly defined as an installable package.
- The XML export logic is ad-hoc and not tied to a real DGII schema or validation flow.

Current classification:
- Closer to an incomplete prototype than to an e-CF-ready invoicer.
- It has some traits of a generic invoicer, but not enough maturity to be considered a serious accounting or fiscal system.

## 2. Tech stack inventory

- Language: Python
- Version assumption: Python 3.12 is present in the local environment; the code uses standard-library features only.
- Framework: none. This is plain Python, not a web app framework project.
- Package manager: pip via virtual environment; the requirements file is empty.
- Database: none. No SQLite, PostgreSQL, ORM, migrations, or persistence layer.
- Frontend: none.
- Backend: none. No API server, no CLI framework, no web interface.
- Storage approach: local filesystem writes to JSON and XML files in the repository root.
- Authentication: none.
- Testing framework: none. No pytest or unittest-based test suite is configured.
- Deployment files: none. No Dockerfile, docker-compose, CI workflow, deployment manifest, or environment config template.
- Environment variables: none detected.
- External services: none. No DGII endpoint client, no certificate handling, no email/SMS integrations.

## 3. Repository map

- [README.md](README.md) — support. Minimal project description.
- [main.py](main.py) — core. Entry point that demonstrates the invoice flow.
- [modules/invoice.py](modules/invoice.py) — core. Contains the invoice model and XML/JSON export logic.
- [modules/client.py](modules/client.py) — core. Contains the customer/client model.
- [modules/utils.py](modules/utils.py) — unclear / dead code. Present but empty.
- [config/settings.yaml](config/settings.yaml) — unclear / support. Present but empty.
- [requirements.txt](requirements.txt) — support. Present but empty.
- [factura_0001.json](factura_0001.json) — support / obsolete. Sample generated artifact.
- [factura_0001.xml](factura_0001.xml) — support / obsolete. Sample generated artifact.
- [.gitignore](.gitignore) — support. Standard Python ignore rules.
- [.venv](.venv) — support. Local virtual environment, not part of source logic.
- [.conda](.conda) — support. Local environment artifacts.

## 4. Current data model

### Invoice
- Exists as the class Invoice.
- Fields: number, client, items, taxes, type, total, emission date.
- Status: simplistic and insufficient for the new target.
- Assessment: incomplete for the new project. It lacks internal document code, official NCF/e-NCF separation, status lifecycle, approval workflow, payment data, attachments, and audit tracking.

### Client/Customer
- Exists as the class Client.
- Fields: name, RNC, address, phone, email.
- Assessment: too simple for a proper fiscal master-data model. It lacks customer type, tax regime, contact history, legal entity details, and customer-level approval rules.

### Supplier
- Not implemented.
- Assessment: missing and required for receiving invoices and supplier-side workflows.

### Product/Service
- Not implemented as a first-class model.
- Items are stored as dictionaries inside the invoice.
- Assessment: insufficient. A proper system needs product/service master data, SKU codes, units, taxable flags, and tax applicability.

### Tax
- Represented as a simple dictionary passed into Invoice.
- Assessment: too weak. The new system needs explicit tax regimes, rate types, legal tax treatment, and traceability.

### Payment
- Not implemented.
- Assessment: missing. Required for invoice settlement and reconciliation.

### Document/File
- Not implemented as a modeled entity.
- Files are handled as flat artifacts on disk.
- Assessment: insufficient for a vault-oriented system; needs storage metadata, content hash, version history, access control, and origin tracking.

### User/Role
- Not implemented.
- Assessment: missing. Required for approvals, audit, and access control.

### Audit/Event
- Not implemented.
- Assessment: missing. Required for compliance, troubleshooting, and forensic review.

### NCF/e-NCF fields
- Not modeled properly.
- The current invoice number is treated as a generic string and not distinguished from an official fiscal number.
- Assessment: wrong for DGII-oriented requirements.

### XML fields
- The code writes XML, but the structure is ad-hoc and not tied to a formal e-CF schema or documented validation rules.
- Assessment: incomplete and risky for compliance work.

### DGII status fields
- None present.
- Assessment: missing.

## 5. Current workflows

### Uploading/storing an invoice
- Status: not implemented.
- The repository has sample files in the root, but there is no ingestion flow, no upload endpoint, no document vault, and no metadata extraction pipeline.

### Creating an invoice
- Status: partially implemented.
- The Invoice class exists and main.py demonstrates invoice creation.
- It is still a demo, not a production workflow.

### Editing an invoice
- Status: missing.
- No editing interface or update workflow exists.

### Approving an invoice
- Status: missing.
- No approval model, no roles, no commercial approval state, no rejection path.

### Exporting/reporting
- Status: partially implemented.
- JSON output is basic and XML output is basic, but there are no reports, summaries by supplier/customer, or fiscal reporting logic.

### Searching documents
- Status: missing.
- No index, no metadata store, no search capabilities.

### Generating PDF
- Status: missing.
- There is no PDF generation module.

### Generating XML
- Status: partially implemented.
- XML is generated as a sample artifact, but it is not DGII-compliant, schema-validated, or tied to certificate/signature workflows.

### Sending anything externally
- Status: missing.
- No DGII connector, no transmission API, no submission queue, no TrackId handling.

## 6. Fiscal and DGII gap analysis

| Feature | Current repo status | Required for DGII-oriented system | Risk | Recommended action |
|---|---|---|---|---|
| Internal document code generation | Missing | Yes | High | Introduce internal document codes separate from official fiscal numbers |
| NCF/e-NCF separation | Missing | Yes | High | Model internal code, NCF, e-NCF, environment, and validity separately |
| e-CF XML generation | Partial | Yes | High | Build a formal XML builder with schema-aware fields and versioning |
| XML schema validation | Missing | Yes | High | Add XSD/schema validation and test fixtures |
| Digital signature | Missing | Yes | High | Add signing module and certificate lifecycle management |
| Certificate handling | Missing | Yes | High | Introduce secure certificate storage and key rotation process |
| Authentication endpoint/client | Missing | Yes | High | Implement DGII client with auth flow and token handling |
| URL Recepción | Missing | Yes | High | Configure environment-specific endpoint registry |
| URL Aprobación Comercial | Missing | Yes | High | Add endpoint configuration for commercial approval |
| URL Autenticación | Missing | Yes | High | Add endpoint configuration for authentication |
| TrackId storage | Missing | Yes | High | Persist transmission IDs and status history |
| Status consultation | Missing | Yes | High | Add polling/status-consultation module |
| Accepted/rejected/conditional/in-process states | Missing | Yes | High | Define and persist explicit document states |
| Printed representation | Missing | Yes | Medium | Add PDF/printed rendering workflow |
| Supplier e-CF reception | Missing | Yes | High | Add inbound invoice and supplier document handling |
| Commercial approval/rejection | Missing | Yes | High | Add approval workflow and reviewer roles |
| Contingency queue | Missing | Yes | High | Create retry/resubmission queue for failed transmissions |
| Audit log | Missing | Yes | High | Implement immutable audit/event history |
| Immutable file hash | Missing | Yes | High | Store SHA-256 hash at ingestion time |
| Environment separation | Missing | Yes | High | Introduce pre-certification, certification, production config |
| Production secrets handling | Missing | Yes | High | Add secret management and environment-based config |

## 7. Security audit

Authentication:
- Not implemented.
- Any future application should enforce user authentication and role-based authorization.

Authorization:
- Not implemented.
- There is no concept of admin, reviewer, accountant, or fiscal operator.

Password handling:
- Not applicable yet, but no secure password hashing or credential storage strategy exists.

File permissions:
- Files are written directly to the repository root with no explicit permission model.
- This is risky for production and for multi-user use.

Secret leakage:
- No environment variable handling is implemented.
- The repo currently does not expose secrets, but it also has no safe secret-management pattern.

.env handling:
- There is no .env example or configuration loader.
- The .gitignore file does ignore .env, which is good, but the project lacks a documented approach.

Certificate/private-key risks:
- None currently implemented, but this will become a major risk area once signing is introduced.
- Private keys must never be stored in source control or plain filesystem locations without protection.

Upload risks:
- Not implemented. When added later, the system must validate file type, size, malware risk, and content encoding.

SQL injection risks:
- Not applicable yet because there is no database layer.
- This will become relevant once persistence is introduced.

Dependency risks:
- The project currently uses no declared dependencies, which lowers immediate risk but also means the environment is under-specified.
- Once libraries are added, dependency pinning and vulnerability review will be essential.

Audit logs:
- Not implemented.
- A future system needs tamper-evident event logging for all document actions and state transitions.

## 8. Storage audit

Current storage model:
- The app writes example JSON and XML files to the repository root.
- There is no structured repository of documents, no database, and no document vault layer.

What is preserved today:
- Original uploaded file: no.
- Generated PDF: no.
- Generated XML: partially, as sample artifacts.
- Signed XML: no.
- Hash: no.
- Metadata: no.
- Version history: no.
- Deletion policy: no.

This means the repository is currently closer to a file-demo than to a compliant document archive. A future system should store:
- original source files,
- derived files (PDF/XML/signature artifacts),
- hashes,
- metadata,
- event history,
- retention/deletion policy,
- and version lineage.

## 9. Code quality and maintainability

Strengths:
- The code is small and understandable.
- The logic is centralized in a few modules.
- The project is easy to inspect manually.

Issues:
- The client model signature and the main demo call are inconsistent.
- The log directory is hardcoded and not created automatically.
- The invoice logic mixes business data and export concerns.
- XML generation is not schema-driven.
- Some modules are empty, which increases ambiguity.
- There is no packaging structure for a scalable multi-module app.
- The repository lacks tests, migrations, and formal configuration.
- The naming is partly generic and not aligned with fiscal terminology.

Parts that should be deleted rather than patched:
- Empty placeholder modules such as utilities and settings if they are not going to be used immediately.
- The current sample-root artifact approach should be replaced by a proper storage layer rather than patched.
- The current invoice demo should be re-architected rather than extended in place.

## 10. Test status

Existing tests:
- None found in the repository.

How to run tests:
- There is no test runner configuration yet.
- The attempted command was:
  - `python -m pytest -q`
- Result: it failed because pytest is not installed in the environment.

Runtime verification performed:
- The app was executed using the local virtual environment.
- It failed with a runtime error caused by the missing telephone argument in the client initialization.
- The log path issue also surfaced during startup until the logs directory was created manually.

Critical tests missing:
- Invoice creation and totals calculation
- Export to JSON/XML
- Client initialization and validation
- Error handling for missing config/log directories
- DGII-state transition tests
- Signature and XML validation tests
- Audit event logging tests

## 11. Recommended target architecture

The next version should be split into clear bounded modules:

- Document vault
  - Stores original source documents, generated artifacts, hashes, metadata, and lifecycle state.
- Fiscal master data
  - Maintains customers, suppliers, products/services, taxes, and legal entity information.
- Invoice issuing
  - Handles internal invoice creation, numbering, tax calculations, approvals, and exports.
- Invoice receiving
  - Handles supplier invoices, inbound document ingestion, and validation.
- e-CF XML builder
  - Constructs DGII-oriented XML with schema-aware structure and version control.
- DGII connector
  - Implements authentication, submission, status consultation, retries, and TrackId management.
- Reports
  - Produces internal analytics, fiscal summaries, and operational dashboards.
- Audit log
  - Records every state transition and security-relevant action.
- Contingency queue
  - Manages failed submissions, retries, and manual recovery actions.
- Admin/dashboard
  - Provides user management, workflow monitoring, and operational visibility.

## 12. Refactor plan

### Phase 0: make the repo runnable
- Fix startup issues such as the missing log directory and broken client initialization.
- Create a minimal, documented entry point.
- Define a basic runtime configuration pattern.

### Phase 1: preserve/recover useful code
- Keep the invoice model concept, but separate it from export logic.
- Preserve the sample files as fixtures, not as production data.
- Create a basic domain model for invoice, client, and document.

### Phase 2: implement invoice vault and internal codes
- Introduce a document vault abstraction.
- Add internal document code generation separate from official fiscal numbers.
- Store metadata and hashes for every ingested or generated file.

### Phase 3: implement normal invoice issuing
- Add invoice lifecycle states: draft, reviewed, approved, issued, archived.
- Add customer and product/service master data.
- Build reporting and search over stored documents.

### Phase 4: implement e-CF-ready architecture without DGII production connection
- Build an XML builder with versioned templates.
- Add schema validation hooks.
- Introduce environment-specific configuration for pre-certification and certification.

### Phase 5: certification-prep modules
- Add signing, certificate handling, and DGII client modules.
- Implement submission, query, and TrackId persistence.
- Add contingency handling and state machines.

### Phase 6: production hardening
- Add authentication, role-based authorization, audit logs, secrets management, and security review.
- Introduce tests, migrations, and deployment automation.

## 13. Immediate next tasks

1. Fix the current runtime crash in the main demo path.
2. Create a real project configuration structure for logging, storage, and environment settings.
3. Define the target data model for invoice, customer, supplier, document, and workflow state.
4. Decide the persistence approach: file-based vault first, or database-backed MVP.
5. Create a formal internal numbering strategy separate from NCF/e-NCF.
6. Design the document storage layout for original files, generated XML, PDF, hashes, and metadata.
7. Define the approval workflow and the roles involved.
8. Create a schema-driven XML builder skeleton for e-CF output.
9. Define the pre-certification and certification environment configuration model.
10. Add the first automated tests around invoice creation and export.

## Questions for Enrique

- Should the first MVP be a local/internal document vault with no database yet, or do you want the first version to use a real database from the start?
- Do you want the initial milestone to focus only on internal invoice organization and approval, or should supplier-invoice ingestion be included immediately?
- What is the desired numbering policy for internal document codes versus official NCF/e-NCF values?
- Should the first implementation target a DGII-ready architecture but remain disconnected from production DGII endpoints until certification is near?
