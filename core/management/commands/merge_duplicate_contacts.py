from django.core.management.base import BaseCommand, CommandError

from contacts.merge import ContactMergeError, apply_merge_plan, build_merge_plan


class Command(BaseCommand):
    help = (
        "Explicit opt-in merge for duplicate Contact natural keys. "
        "Never runs automatically. Default is dry-run; --apply is required to mutate."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--rnc-or-id",
            required=True,
            dest="rnc_or_id",
            help="Natural-key RNC/ID of the duplicate contact group.",
        )
        parser.add_argument(
            "--contact-type",
            required=True,
            dest="contact_type",
            help="Natural-key contact type (CLIENT, SUPPLIER, BOTH).",
        )
        parser.add_argument(
            "--keep-pk",
            required=True,
            type=int,
            dest="keep_pk",
            help="Primary key of the canonical contact to keep.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=True,
            help="Preview merge actions without modifying data (default).",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply the merge. Required for actual changes.",
        )
        parser.add_argument(
            "--reason",
            default="",
            help="Optional reason recorded in AuditEvent metadata.",
        )
        parser.add_argument(
            "--allow-non-demo",
            action="store_true",
            default=False,
            help="Allow merging non-demo natural keys (default: false).",
        )

    def handle(self, *args, **options):
        apply = bool(options.get("apply"))
        dry_run = not apply

        contact_type = options["contact_type"]
        rnc_or_id = options["rnc_or_id"]
        keep_pk = options["keep_pk"]
        reason = options.get("reason") or ""
        allow_non_demo = bool(options.get("allow_non_demo"))

        mode = "DRY-RUN" if dry_run else "APPLY"
        self.stdout.write(f"merge_duplicate_contacts [{mode}]")
        self.stdout.write("=" * 40)

        try:
            plan = build_merge_plan(
                contact_type=contact_type,
                rnc_or_id=rnc_or_id,
                keep_pk=keep_pk,
                allow_non_demo=allow_non_demo,
                reason=reason,
            )
        except ContactMergeError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            f"Group: contact_type={plan.contact_type} rnc_or_id={plan.rnc_or_id}"
        )
        self.stdout.write(
            f"Contacts found: {', '.join(f'pk={c.pk}:{c.legal_name!r}:active={c.is_active}' for c in [plan.keeper, *plan.duplicates])}"
        )
        self.stdout.write(
            f"Canonical contact: pk={plan.keeper.pk} ({plan.keeper.legal_name!r})"
        )
        self.stdout.write(
            "Duplicates to merge: "
            + ", ".join(f"pk={c.pk} ({c.legal_name!r})" for c in plan.duplicates)
        )

        self.stdout.write("Foreign keys that would be repointed:")
        any_fk = False
        for ref in plan.fk_repoints:
            if not ref.object_pks:
                continue
            any_fk = True
            self.stdout.write(
                f"  {ref.model_label}.{ref.field_name} -> keep-pk={plan.keeper.pk} "
                f"object_pks={ref.object_pks}"
            )
        if not any_fk:
            self.stdout.write("  (none)")

        if plan.deactivate_pks:
            self.stdout.write(
                f"Contacts that would be soft-deactivated: pks={plan.deactivate_pks}"
            )
        else:
            self.stdout.write("Contacts that would be soft-deactivated: (none)")
        if plan.already_inactive_pks:
            self.stdout.write(
                f"Duplicates already inactive: pks={plan.already_inactive_pks}"
            )
        self.stdout.write("Hard delete: disabled (never by default)")

        if dry_run:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "DRY-RUN only. Re-run with --apply to execute this merge."
                )
            )
            return

        result = apply_merge_plan(plan)
        self.stdout.write("")
        if not result["changed"]:
            self.stdout.write(self.style.SUCCESS("No changes needed (already merged)."))
            return

        self.stdout.write(self.style.SUCCESS("Merge applied."))
        if result["repointed"]:
            for key, count in result["repointed"].items():
                self.stdout.write(f"  Repointed {count} row(s) on {key}")
        else:
            self.stdout.write("  Repointed: (none)")
        self.stdout.write(f"  Soft-deactivated contact pks={result['deactivated']}")
        if result["audit_created"]:
            self.stdout.write("  AuditEvent: contact_duplicate_merged")
        if reason:
            self.stdout.write(f"  Reason: {reason}")
