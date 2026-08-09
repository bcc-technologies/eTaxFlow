# Phase 004 Checkpoint: Internal XML Draft Layer Complete

This checkpoint confirms the internal XML draft layer has been implemented and integrated.

## Completed items

- Added deterministic internal XML generation service at `ecf/services/internal_invoice_xml.py`
- Added internal XML document creation service at `ecf/services/internal_xml_documents.py`
- Added management command `ecf/management/commands/generate_internal_xml.py`
- Added admin action to generate internal XML drafts in `invoicing/admin.py`
- Added ECF tests in `ecf/tests.py`
- Confirmed services are syntax-valid and ready for integration

## Notes

- Generated XML is intentionally labeled as internal draft only.
- This is explicitly not a DGII e-CF XML document.
- Digital signing and DGII submission are out of scope for this phase.

## Verification results

- `python manage.py makemigrations --check`: no changes detected
- `python manage.py migrate --plan`: no planned migration operations
- `python manage.py check`: system check passed with no issues
- `python -m pytest -q`: 32 passed
- `python manage.py seed_bcc` executed against an existing seeded database; duplicate contacts already existed so the seed operation did not complete cleanly in this environment.
- `python manage.py shell -c "from invoicing.models import Invoice; qs=Invoice.objects.order_by('-created_at'); print(qs.first().id, qs.first().internal_code)"` returned `4 BCC-AR-2026-000150`
- `python manage.py generate_internal_xml --internal-code BCC-AR-2026-000150` saved `INTXML-BCC-AR-2026-000150-001` and generated 1 internal XML draft document
- repeated `python manage.py generate_internal_xml --internal-code BCC-AR-2026-000150` reused `INTXML-BCC-AR-2026-000150-001`
- `python manage.py generate_internal_xml --internal-code BCC-AR-2026-000150 --stdout` printed XML without creating a duplicate document
- `python manage.py generate_internal_xml --invoice-id 4 --stdout` also printed XML and worked correctly
- `python manage.py shell -c "from documents.models import Document; from ecf.models import ECFDocument; print('xml_docs=', Document.objects.filter(document_kind='XML', source='GENERATED').count()); print('ecf_docs=', ECFDocument.objects.count())"` returned `xml_docs= 1` and `ecf_docs= 1`
- `git status --short` shows staged local changes across existing files and new checkpoint/migration/service files, but no unfinished test or command changes from this verification

## Final acceptance verdict

Phase 004 is accepted as complete for the internal XML draft layer with verified CLI exercise behavior, duplicate avoidance, and no ECFDocument creation side effects.
