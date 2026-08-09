"""Soft natural-key helpers for Contact.

Contact uniqueness on (contact_type, rnc_or_id) is business-level only.
It is intentionally not enforced with a database UniqueConstraint until
existing duplicates can be cleaned safely.
"""

from __future__ import annotations

from contacts.models import Contact


def find_contacts_by_natural_key(contact_type: str, rnc_or_id: str, *, active_only: bool = False):
    """Return contacts matching the natural key, oldest first."""
    qs = Contact.objects.filter(
        contact_type=contact_type,
        rnc_or_id=rnc_or_id,
    )
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by("pk")


def natural_key_duplicate_warnings(contact_type: str, rnc_or_id: str) -> list[str]:
    """Return warnings when multiple *active* contacts share a natural key."""
    qs = find_contacts_by_natural_key(contact_type, rnc_or_id, active_only=True)
    count = qs.count()
    if count <= 1:
        return []
    pks = list(qs.values_list("pk", flat=True))
    return [
        (
            f"WARNING: Found {count} Contact records for natural key "
            f"(contact_type={contact_type!r}, rnc_or_id={rnc_or_id!r}); "
            f"pks={pks}. Soft uniqueness only — not enforced at DB level."
        )
    ]


def resolve_contact_by_natural_key(
    contact_type: str,
    rnc_or_id: str,
    defaults: dict | None = None,
    *,
    update_existing: bool = True,
):
    """Resolve a Contact by natural key without raising MultipleObjectsReturned.

    Prefers the first active match (lowest pk). Falls back to any match.
    Warnings are emitted only for multiple active duplicates.
    Returns ``(contact, created, warnings)``.
    """
    defaults = defaults or {}
    warnings = natural_key_duplicate_warnings(contact_type, rnc_or_id)

    active = find_contacts_by_natural_key(contact_type, rnc_or_id, active_only=True)
    if active.exists():
        contact = active.first()
    else:
        queryset = find_contacts_by_natural_key(contact_type, rnc_or_id)
        if not queryset.exists():
            contact = Contact.objects.create(
                contact_type=contact_type,
                rnc_or_id=rnc_or_id,
                **defaults,
            )
            return contact, True, warnings
        contact = queryset.first()

    if update_existing and defaults:
        for key, value in defaults.items():
            setattr(contact, key, value)
        contact.save()
    return contact, False, warnings
