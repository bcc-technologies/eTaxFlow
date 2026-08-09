"""Explicit opt-in merge helpers for duplicate Contact natural keys."""

from __future__ import annotations

from dataclasses import dataclass, field

from django.apps import apps
from django.db import transaction

from audit.models import AuditEvent
from contacts.models import Contact
from core.seed_demo import is_demo_contact_natural_key


class ContactMergeError(ValueError):
    """Raised when a merge request is invalid or unsafe."""


@dataclass
class ContactFKRef:
    model_label: str
    field_name: str
    object_pks: list[int] = field(default_factory=list)


@dataclass
class ContactMergePlan:
    contact_type: str
    rnc_or_id: str
    keeper: Contact
    duplicates: list[Contact]
    fk_repoints: list[ContactFKRef]
    deactivate_pks: list[int]
    already_inactive_pks: list[int]
    reason: str = ""

    @property
    def has_work(self) -> bool:
        if self.deactivate_pks:
            return True
        return any(ref.object_pks for ref in self.fk_repoints)


def discover_contact_fk_fields():
    """Return concrete (model, field_name) FKs pointing at Contact."""
    contact_model = Contact
    results = []
    for model in apps.get_models():
        if model is contact_model:
            continue
        for field in model._meta.fields:
            if not getattr(field, "is_relation", False):
                continue
            if not getattr(field, "many_to_one", False):
                continue
            if field.related_model is not contact_model:
                continue
            results.append((model, field.name))
    return results


def suggested_merge_command(contact_type: str, rnc_or_id: str, keep_pk: int) -> str:
    return (
        "python manage.py merge_duplicate_contacts "
        f"--contact-type {contact_type} "
        f"--rnc-or-id {rnc_or_id} "
        f"--keep-pk {keep_pk} "
        "--dry-run"
    )


def build_merge_plan(
    *,
    contact_type: str,
    rnc_or_id: str,
    keep_pk: int,
    allow_non_demo: bool = False,
    reason: str = "",
) -> ContactMergePlan:
    if not allow_non_demo and not is_demo_contact_natural_key(contact_type, rnc_or_id):
        raise ContactMergeError(
            "Refusing merge for non-demo natural key. "
            "Pass --allow-non-demo only if you intentionally accept that risk."
        )

    matches = list(
        Contact.objects.filter(contact_type=contact_type, rnc_or_id=rnc_or_id).order_by("pk")
    )
    if len(matches) <= 1:
        raise ContactMergeError(
            f"No duplicate contacts for contact_type={contact_type!r} rnc_or_id={rnc_or_id!r}."
        )

    match_pks = {c.pk for c in matches}
    if keep_pk not in match_pks:
        raise ContactMergeError(
            f"keep-pk={keep_pk} is not in the matching contact group {sorted(match_pks)}."
        )

    for contact in matches:
        if contact.contact_type != contact_type:
            raise ContactMergeError("Refusing merge across different contact_type values.")
        if contact.rnc_or_id != rnc_or_id:
            raise ContactMergeError("Refusing merge across different rnc_or_id values.")

    keeper = next(c for c in matches if c.pk == keep_pk)
    duplicates = [c for c in matches if c.pk != keep_pk]
    duplicate_pks = [c.pk for c in duplicates]

    fk_repoints = []
    for model, field_name in discover_contact_fk_fields():
        object_pks = list(
            model.objects.filter(**{f"{field_name}__in": duplicate_pks})
            .order_by("pk")
            .values_list("pk", flat=True)
        )
        fk_repoints.append(
            ContactFKRef(
                model_label=model._meta.label,
                field_name=field_name,
                object_pks=object_pks,
            )
        )

    deactivate_pks = [c.pk for c in duplicates if c.is_active]
    already_inactive_pks = [c.pk for c in duplicates if not c.is_active]

    return ContactMergePlan(
        contact_type=contact_type,
        rnc_or_id=rnc_or_id,
        keeper=keeper,
        duplicates=duplicates,
        fk_repoints=fk_repoints,
        deactivate_pks=deactivate_pks,
        already_inactive_pks=already_inactive_pks,
        reason=reason or "",
    )


def apply_merge_plan(plan: ContactMergePlan) -> dict:
    """Apply a validated merge plan. Idempotent when no remaining work exists."""
    if not plan.has_work:
        return {
            "repointed": {},
            "deactivated": [],
            "audit_created": False,
            "changed": False,
        }

    repointed = {}
    deactivated = []
    with transaction.atomic():
        for ref in plan.fk_repoints:
            if not ref.object_pks:
                continue
            model = apps.get_model(ref.model_label)
            updated = model.objects.filter(
                pk__in=ref.object_pks,
                **{f"{ref.field_name}__in": [d.pk for d in plan.duplicates]},
            ).update(**{ref.field_name: plan.keeper})
            if updated:
                repointed[f"{ref.model_label}.{ref.field_name}"] = updated

        deactivated = list(
            Contact.objects.filter(pk__in=plan.deactivate_pks, is_active=True).values_list(
                "pk", flat=True
            )
        )
        if deactivated:
            Contact.objects.filter(pk__in=deactivated).update(is_active=False)

        changed = bool(repointed or deactivated)
        if changed:
            AuditEvent.objects.create(
                event_type="contact_duplicate_merged",
                entity_type="Contact",
                entity_id=plan.keeper.pk,
                message=(
                    f"Merged duplicate contacts for "
                    f"({plan.contact_type}, {plan.rnc_or_id}) into pk={plan.keeper.pk}."
                ),
                metadata={
                    "contact_type": plan.contact_type,
                    "rnc_or_id": plan.rnc_or_id,
                    "keep_pk": plan.keeper.pk,
                    "duplicate_pks": [c.pk for c in plan.duplicates],
                    "repointed": repointed,
                    "deactivated": deactivated,
                    "reason": plan.reason,
                },
            )

    return {
        "repointed": repointed,
        "deactivated": deactivated,
        "audit_created": bool(repointed or deactivated),
        "changed": bool(repointed or deactivated),
    }
