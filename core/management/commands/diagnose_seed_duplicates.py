from django.core.management.base import BaseCommand

from contacts.merge import suggested_merge_command
from core.seed_demo import collect_seed_duplicate_report


class Command(BaseCommand):
    help = "Read-only diagnosis of duplicate seed/demo-related records."

    def handle(self, *args, **options):
        sections, total_groups = collect_seed_duplicate_report()

        self.stdout.write("Seed / demo duplicate diagnosis")
        self.stdout.write("=" * 40)

        contact_merge_suggestions = []

        for section in sections:
            self.stdout.write("")
            self.stdout.write(section["title"])
            if not section["groups"]:
                self.stdout.write("  (none)")
                continue
            for group in section["groups"]:
                filters = group["filters"]
                self.stdout.write(
                    self.style.WARNING(
                        f"  DUPLICATE count={group['count']} filters={filters} pks={group['pks']}"
                    )
                )
                if group.get("detail"):
                    self.stdout.write(f"    {group['detail']}")

                if section["title"] == "Contacts by contact_type + rnc_or_id":
                    keep_pk = group["pks"][0]
                    suggestion = suggested_merge_command(
                        filters["contact_type"],
                        filters["rnc_or_id"],
                        keep_pk,
                    )
                    contact_merge_suggestions.append(suggestion)
                    self.stdout.write(f"    Suggested merge (dry-run only):")
                    self.stdout.write(f"      {suggestion}")

        self.stdout.write("")
        if total_groups == 0:
            self.stdout.write(self.style.SUCCESS("No duplicate seed records detected"))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Found {total_groups} duplicate group(s). "
                    "This command is read-only; no changes were made."
                )
            )
            if contact_merge_suggestions:
                self.stdout.write("")
                self.stdout.write("Suggested merge commands (explicit opt-in; not applied):")
                for suggestion in contact_merge_suggestions:
                    self.stdout.write(f"  {suggestion}")
