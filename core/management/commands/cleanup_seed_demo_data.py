from django.core.management.base import BaseCommand
from django.db import transaction

from contacts.models import Contact
from core.seed_demo import (
    DEMO_CATALOG_CODES,
    DEMO_CONTACT_NATURAL_KEYS,
    RETIRED_SEED_INVOICE_MARKER,
    SEED_INVOICE_MARKER,
    is_clearly_demo_contact,
    iter_duplicate_groups,
)
from fiscal.models import FiscalDocumentType, TaxRate, UnitOfMeasure
from invoicing.models import Invoice, ProductService


class Command(BaseCommand):
    help = (
        "Opt-in cleanup for clearly seeded/demo duplicate data. "
        "Default is --dry-run; pass --apply to modify."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=True,
            help="Show planned changes without modifying data (default).",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually apply safe demo cleanup changes.",
        )

    def handle(self, *args, **options):
        apply = bool(options.get("apply"))
        dry_run = not apply

        mode = "DRY-RUN" if dry_run else "APPLY"
        self.stdout.write(f"cleanup_seed_demo_data [{mode}]")
        self.stdout.write("=" * 40)

        notes = []
        actions = []
        contact_notes, contact_actions = self._plan_contact_cleanup()
        notes.extend(contact_notes)
        actions.extend(contact_actions)

        invoice_notes, invoice_actions = self._plan_seed_invoice_cleanup()
        notes.extend(invoice_notes)
        actions.extend(invoice_actions)

        notes.extend(self._catalog_duplicate_notes())

        for note in notes:
            self.stdout.write(self.style.WARNING(f"NOTE: {note}"))

        if not actions:
            if not notes:
                self.stdout.write(self.style.SUCCESS("No demo cleanup actions needed."))
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        "No mutable demo cleanup actions; see notes above."
                    )
                )
            return

        for action in actions:
            prefix = "WOULD" if dry_run else "DID"
            style = self.style.WARNING if dry_run else self.style.SUCCESS
            self.stdout.write(style(f"{prefix}: {action['message']}"))

        if dry_run:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    f"{len(actions)} action(s) planned. Re-run with --apply to execute."
                )
            )
            return

        with transaction.atomic():
            for action in actions:
                action["apply"]()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Applied {len(actions)} cleanup action(s)."))

    def _plan_contact_cleanup(self):
        notes = []
        actions = []
        for contact_type, rnc_or_id in DEMO_CONTACT_NATURAL_KEYS:
            qs = Contact.objects.filter(
                contact_type=contact_type,
                rnc_or_id=rnc_or_id,
            ).order_by("pk")
            if qs.count() <= 1:
                continue

            keeper = qs.first()
            for dup in qs.exclude(pk=keeper.pk):
                if not is_clearly_demo_contact(dup):
                    notes.append(
                        f"SKIP Contact pk={dup.pk} ({dup.legal_name!r}) — "
                        f"ambiguous duplicate of demo key "
                        f"({contact_type}, {rnc_or_id}); keeper pk={keeper.pk}"
                    )
                    continue

                if not dup.is_active:
                    continue

                def _deactivate(contact_id=dup.pk):
                    Contact.objects.filter(pk=contact_id, is_active=True).update(
                        is_active=False
                    )

                actions.append(
                    {
                        "message": (
                            f"Soft-deactivate clearly-demo Contact pk={dup.pk} "
                            f"({dup.legal_name!r}, {contact_type}/{rnc_or_id}); "
                            f"keeper pk={keeper.pk}"
                        ),
                        "apply": _deactivate,
                    }
                )
        return notes, actions

    def _plan_seed_invoice_cleanup(self):
        notes = []
        actions = []
        seed_qs = Invoice.objects.filter(notes__icontains=SEED_INVOICE_MARKER).order_by("pk")
        if not seed_qs.exists():
            return notes, actions

        keeper = seed_qs.first()
        for inv in seed_qs.exclude(pk=keeper.pk):
            def _retire(invoice_id=inv.pk):
                invoice = Invoice.objects.filter(pk=invoice_id).first()
                if not invoice:
                    return
                notes_text = invoice.notes or ""
                if SEED_INVOICE_MARKER not in notes_text:
                    return
                invoice.notes = notes_text.replace(
                    SEED_INVOICE_MARKER, RETIRED_SEED_INVOICE_MARKER
                )
                invoice.save(update_fields=["notes"])

            actions.append(
                {
                    "message": (
                        f"Retire duplicate seed marker on Invoice pk={inv.pk} "
                        f"({inv.internal_code}); keeper pk={keeper.pk}"
                    ),
                    "apply": _retire,
                }
            )

        extra_lines = keeper.lines.exclude(line_order__in=[1, 2])
        if extra_lines.exists():
            line_pks = list(extra_lines.values_list("pk", flat=True))

            def _delete_extra_lines(invoice_id=keeper.pk, pks=line_pks):
                invoice = Invoice.objects.filter(pk=invoice_id).first()
                if not invoice:
                    return
                deleted, _ = (
                    invoice.lines.filter(pk__in=pks)
                    .exclude(line_order__in=[1, 2])
                    .delete()
                )
                if deleted:
                    invoice._recalculate_totals()

            actions.append(
                {
                    "message": (
                        f"Delete {len(line_pks)} extra line(s) on seed Invoice "
                        f"pk={keeper.pk} ({keeper.internal_code}); keep line_order 1-2"
                    ),
                    "apply": _delete_extra_lines,
                }
            )
        return notes, actions

    def _catalog_duplicate_notes(self):
        notes = []
        catalog_models = [
            (FiscalDocumentType, "FiscalDocumentType"),
            (TaxRate, "TaxRate"),
            (UnitOfMeasure, "UnitOfMeasure"),
            (ProductService, "ProductService"),
        ]
        for model, label in catalog_models:
            for filters, count, qs in iter_duplicate_groups(model, ["code"]):
                code = filters["code"]
                pks = list(qs.values_list("pk", flat=True))
                keeper_pk = pks[0]
                if code not in DEMO_CATALOG_CODES.get(label, set()):
                    notes.append(
                        f"SKIP {label} code={code!r} duplicates pks={pks} — "
                        "not a known seed catalog code"
                    )
                    continue
                notes.append(
                    f"REPORT {label} duplicate seed code={code!r} "
                    f"count={count} pks={pks}; keeper pk={keeper_pk} "
                    "(no auto-delete of catalog rows)"
                )
        return notes
