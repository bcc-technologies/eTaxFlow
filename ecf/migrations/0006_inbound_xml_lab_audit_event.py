# Generated manually for Phase 033

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ecf", "0005_inbound_xml_lab_workflow_event"),
    ]

    operations = [
        migrations.CreateModel(
            name="InboundXMLLabAuditEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("event_type", models.CharField(db_index=True, max_length=64)),
                (
                    "retention_decision",
                    models.CharField(blank=True, db_index=True, max_length=64),
                ),
                (
                    "severity",
                    models.CharField(db_index=True, default="INFO", max_length=16),
                ),
                ("reason", models.CharField(blank=True, max_length=128)),
                (
                    "policy_version",
                    models.CharField(default="phase-033-v1", max_length=32),
                ),
                ("input_summary_json", models.JSONField(default=dict)),
                ("output_summary_json", models.JSONField(default=dict)),
                (
                    "compliance_status",
                    models.CharField(default="NOT_DGII_COMPLIANT", max_length=32),
                ),
                ("dgii_submission_allowed", models.BooleanField(default=False)),
                ("certification_evidence", models.BooleanField(default=False)),
                (
                    "track_id",
                    models.CharField(
                        blank=True, default=None, max_length=255, null=True
                    ),
                ),
                ("dgii_call_made", models.BooleanField(default=False)),
                (
                    "lab_mode",
                    models.CharField(default="NON_PRODUCTION_LAB_ONLY", max_length=40),
                ),
                (
                    "lab_record",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lab_audit_events",
                        to="ecf.inboundxmllabrecord",
                    ),
                ),
                (
                    "workflow_event",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lab_audit_events",
                        to="ecf.inboundxmllabworkflowevent",
                    ),
                ),
            ],
            options={
                "verbose_name": "Inbound XML lab audit event (NON_PRODUCTION_LAB_ONLY)",
                "verbose_name_plural": "Inbound XML lab audit events (NON_PRODUCTION_LAB_ONLY)",
                "indexes": [
                    models.Index(
                        fields=["created_at"], name="ecf_inbound_audit_created_idx"
                    ),
                    models.Index(
                        fields=["event_type", "retention_decision"],
                        name="ecf_inbound_audit_type_decision_idx",
                    ),
                    models.Index(
                        fields=["lab_record", "created_at"],
                        name="ecf_inbound_audit_record_created_idx",
                    ),
                ],
            },
        ),
    ]
