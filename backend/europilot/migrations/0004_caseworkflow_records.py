from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("europilot", "0003_providereventrecord_received_at")]

    operations = [
        migrations.CreateModel(
            name="CaseRecord",
            fields=[
                ("case_id", models.CharField(max_length=120, primary_key=True, serialize=False)),
                ("state", models.CharField(choices=[("open", "Open"), ("under_review", "Under review"), ("resolved", "Resolved"), ("deferred", "Deferred")], default="open", max_length=32)),
                ("resolution_reason", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("investigation", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="case", to="europilot.investigationrecord")),
            ],
            options={"db_table": "europilot_case"},
        ),
        migrations.CreateModel(
            name="CaseNoteRecord",
            fields=[
                ("note_id", models.CharField(max_length=120, primary_key=True, serialize=False)),
                ("text", models.TextField(max_length=2000)),
                ("actor", models.CharField(default="synthetic_local_operator", editable=False, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="notes", to="europilot.caserecord")),
            ],
            options={"db_table": "europilot_case_note"},
        ),
        migrations.CreateModel(
            name="IdempotencyRecord",
            fields=[
                ("idempotency_id", models.BigAutoField(primary_key=True, serialize=False)),
                ("action", models.CharField(choices=[("case_transitioned", "case_transitioned"), ("note_created", "note_created")], max_length=64)),
                ("request_id", models.CharField(max_length=128)),
                ("fingerprint", models.CharField(max_length=64)),
                ("original_status", models.PositiveSmallIntegerField()),
                ("original_response", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="idempotency_records", to="europilot.caserecord")),
            ],
            options={"db_table": "europilot_idempotency"},
        ),
        migrations.CreateModel(
            name="AuditEventRecord",
            fields=[
                ("audit_id", models.CharField(max_length=120, primary_key=True, serialize=False)),
                ("action", models.CharField(choices=[("case_transitioned", "case_transitioned"), ("note_created", "note_created")], max_length=64)),
                ("actor", models.CharField(default="synthetic_local_operator", editable=False, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("previous_state", models.CharField(blank=True, choices=[("open", "Open"), ("under_review", "Under review"), ("resolved", "Resolved"), ("deferred", "Deferred")], max_length=32)),
                ("new_state", models.CharField(blank=True, choices=[("open", "Open"), ("under_review", "Under review"), ("resolved", "Resolved"), ("deferred", "Deferred")], max_length=32)),
                ("reason", models.CharField(blank=True, max_length=500)),
                ("request_id", models.CharField(max_length=128)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="audit_events", to="europilot.caserecord")),
                ("idempotency", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="audit_event", to="europilot.idempotencyrecord")),
                ("note", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="audit_events", to="europilot.casenoterecord")),
            ],
            options={"db_table": "europilot_audit_event"},
        ),
        migrations.AddConstraint(
            model_name="idempotencyrecord",
            constraint=models.UniqueConstraint(fields=("case", "action", "request_id"), name="case_action_request_unique"),
        ),
        migrations.AddConstraint(
            model_name="caserecord",
            constraint=models.CheckConstraint(name="case_state_supported", condition=models.Q(state__in=["open", "under_review", "resolved", "deferred"])),
        ),
        migrations.AddConstraint(
            model_name="casenoterecord",
            constraint=models.CheckConstraint(name="case_note_text_nonempty", condition=~models.Q(text="")),
        ),
        migrations.AddConstraint(
            model_name="idempotencyrecord",
            constraint=models.CheckConstraint(name="idempotency_action_supported", condition=models.Q(action__in=["case_transitioned", "note_created"])),
        ),
        migrations.AddConstraint(
            model_name="idempotencyrecord",
            constraint=models.CheckConstraint(name="idempotency_request_id_nonempty", condition=~models.Q(request_id="")),
        ),
        migrations.AddConstraint(
            model_name="auditeventrecord",
            constraint=models.CheckConstraint(name="audit_action_supported", condition=models.Q(action__in=["case_transitioned", "note_created"])),
        ),
        migrations.AddConstraint(
            model_name="auditeventrecord",
            constraint=models.CheckConstraint(name="audit_request_id_nonempty", condition=~models.Q(request_id="")),
        ),
    ]
