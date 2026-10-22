from django.core.exceptions import ValidationError
from django.db import models

from .domain import SYNTHETIC_ACTOR, normalize_request_id, normalize_text, validate_fingerprint


CASE_STATE_OPEN = "open"
CASE_STATE_UNDER_REVIEW = "under_review"
CASE_STATE_RESOLVED = "resolved"
CASE_STATE_DEFERRED = "deferred"
ACTION_CASE_TRANSITIONED = "case_transitioned"
ACTION_NOTE_CREATED = "note_created"


class InvoiceRecord(models.Model):
    invoice_id = models.CharField(max_length=120, primary_key=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        db_table = "europilot_invoice"


class PaymentRecord(models.Model):
    payment_id = models.CharField(max_length=120, primary_key=True)
    invoice = models.ForeignKey(InvoiceRecord, on_delete=models.PROTECT, related_name="payments")

    class Meta:
        db_table = "europilot_payment"


class AttemptRecord(models.Model):
    attempt_id = models.CharField(max_length=120, primary_key=True)
    payment = models.ForeignKey(PaymentRecord, on_delete=models.PROTECT, related_name="attempts")
    request_id = models.CharField(max_length=120, unique=True)
    requested_at = models.DateTimeField()
    outcome = models.CharField(max_length=32, default="unknown")
    retry_of = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="retries")

    class Meta:
        db_table = "europilot_attempt"
        constraints = [models.UniqueConstraint(fields=("payment", "attempt_id"), name="attempt_payment_identity")]

    def clean(self):
        if self.retry_of_id and self.retry_of and self.retry_of.payment_id != self.payment_id:
            raise ValidationError({"retry_of": "retry attempt must belong to the same logical payment"})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ProviderEventRecord(models.Model):
    provider = models.CharField(max_length=120)
    event_id = models.CharField(max_length=120)
    payment = models.ForeignKey(PaymentRecord, on_delete=models.PROTECT, related_name="provider_events")
    event_type = models.CharField(max_length=32)
    occurred_at = models.DateTimeField()
    received_at = models.DateTimeField(null=True, blank=True)
    payload = models.TextField(blank=True)

    class Meta:
        db_table = "europilot_provider_event"
        constraints = [models.UniqueConstraint(fields=("provider", "event_id"), name="provider_event_identity")]


class DeliveryRecord(models.Model):
    delivery_id = models.CharField(max_length=120, primary_key=True)
    provider_event = models.ForeignKey(ProviderEventRecord, on_delete=models.PROTECT, related_name="deliveries")
    received_at = models.DateTimeField()

    class Meta:
        db_table = "europilot_delivery"


class EvidenceRecord(models.Model):
    evidence_id = models.CharField(max_length=120, primary_key=True)
    payment = models.ForeignKey(PaymentRecord, on_delete=models.PROTECT, related_name="evidence")
    source = models.CharField(max_length=120)
    reference = models.CharField(max_length=240)
    observed_at = models.DateTimeField()
    received_at = models.DateTimeField()
    event_type = models.CharField(max_length=32)
    provider = models.CharField(max_length=120, null=True, blank=True)
    authoritative = models.BooleanField(default=False)

    class Meta:
        db_table = "europilot_evidence"


class InvestigationRecord(models.Model):
    investigation_id = models.CharField(max_length=120, primary_key=True)
    payment = models.OneToOneField(PaymentRecord, on_delete=models.PROTECT, related_name="investigation")

    class Meta:
        db_table = "europilot_investigation"


class FindingRecord(models.Model):
    investigation = models.OneToOneField(InvestigationRecord, on_delete=models.PROTECT, related_name="finding")
    outcome = models.CharField(max_length=32)
    missing_evidence = models.JSONField(default=list)
    supporting_evidence = models.ManyToManyField(EvidenceRecord, through="FindingEvidenceRecord", blank=True, related_name="findings")

    class Meta:
        db_table = "europilot_finding"


class FindingEvidenceRecord(models.Model):
    finding = models.ForeignKey(FindingRecord, on_delete=models.PROTECT)
    evidence = models.ForeignKey(EvidenceRecord, on_delete=models.PROTECT)

    class Meta:
        db_table = "europilot_finding_evidence"
        constraints = [models.UniqueConstraint(fields=("finding", "evidence"), name="finding_evidence_unique")]

    def clean(self):
        if self.finding_id and self.evidence_id and self.finding.investigation.payment_id != self.evidence.payment_id:
            raise ValidationError("supporting evidence must belong to the investigation payment")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class CaseRecord(models.Model):
    class State(models.TextChoices):
        OPEN = CASE_STATE_OPEN, "Open"
        UNDER_REVIEW = CASE_STATE_UNDER_REVIEW, "Under review"
        RESOLVED = CASE_STATE_RESOLVED, "Resolved"
        DEFERRED = CASE_STATE_DEFERRED, "Deferred"

    case_id = models.CharField(max_length=120, primary_key=True)
    investigation = models.OneToOneField(InvestigationRecord, on_delete=models.PROTECT, related_name="case")
    state = models.CharField(max_length=32, choices=State.choices, default=State.OPEN)
    resolution_reason = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "europilot_case"
        constraints = [
            models.CheckConstraint(name="case_state_supported", condition=models.Q(state__in=[CASE_STATE_OPEN, CASE_STATE_UNDER_REVIEW, CASE_STATE_RESOLVED, CASE_STATE_DEFERRED])),
        ]

    def clean(self):
        if self.state in {self.State.RESOLVED, self.State.DEFERRED} and not self.resolution_reason.strip():
            raise ValidationError({"resolution_reason": "resolved and deferred cases require a reason"})
        if self.resolution_reason and len(self.resolution_reason.strip()) > 500:
            raise ValidationError({"resolution_reason": "resolution reason must be at most 500 characters"})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class CaseNoteRecord(models.Model):
    note_id = models.CharField(max_length=120, primary_key=True)
    case = models.ForeignKey(CaseRecord, on_delete=models.PROTECT, related_name="notes")
    text = models.TextField(max_length=2000)
    actor = models.CharField(max_length=64, default=SYNTHETIC_ACTOR, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "europilot_case_note"
        constraints = [
            models.CheckConstraint(name="case_note_text_nonempty", condition=~models.Q(text="")),
        ]

    def clean(self):
        if not self.text.strip():
            raise ValidationError({"text": "note text is required"})
        if len(self.text.strip()) > 2000:
            raise ValidationError({"text": "note text must be at most 2000 characters"})

    def save(self, *args, **kwargs):
        self.actor = SYNTHETIC_ACTOR
        self.full_clean()
        return super().save(*args, **kwargs)


class IdempotencyRecord(models.Model):
    idempotency_id = models.BigAutoField(primary_key=True)
    case = models.ForeignKey(CaseRecord, on_delete=models.PROTECT, related_name="idempotency_records")
    action = models.CharField(max_length=64, choices=((ACTION_CASE_TRANSITIONED, ACTION_CASE_TRANSITIONED), (ACTION_NOTE_CREATED, ACTION_NOTE_CREATED)))
    request_id = models.CharField(max_length=128)
    fingerprint = models.CharField(max_length=64)
    original_status = models.PositiveSmallIntegerField()
    original_response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "europilot_idempotency"
        constraints = [
            models.UniqueConstraint(fields=("case", "action", "request_id"), name="case_action_request_unique"),
            models.CheckConstraint(name="idempotency_action_supported", condition=models.Q(action__in=[ACTION_CASE_TRANSITIONED, ACTION_NOTE_CREATED])),
            models.CheckConstraint(name="idempotency_request_id_nonempty", condition=~models.Q(request_id="")),
        ]

    def clean(self):
        try:
            normalize_request_id(self.request_id)
            validate_fingerprint(self.fingerprint)
        except ValueError as error:
            raise ValidationError({"request_id": str(error) if "request_id" in str(error) else "invalid fingerprint"}) from error

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class AuditEventRecord(models.Model):
    audit_id = models.CharField(max_length=120, primary_key=True)
    case = models.ForeignKey(CaseRecord, on_delete=models.PROTECT, related_name="audit_events")
    action = models.CharField(max_length=64, choices=((ACTION_CASE_TRANSITIONED, ACTION_CASE_TRANSITIONED), (ACTION_NOTE_CREATED, ACTION_NOTE_CREATED)))
    actor = models.CharField(max_length=64, default=SYNTHETIC_ACTOR, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    previous_state = models.CharField(max_length=32, choices=CaseRecord.State.choices, blank=True)
    new_state = models.CharField(max_length=32, choices=CaseRecord.State.choices, blank=True)
    reason = models.CharField(max_length=500, blank=True)
    note = models.ForeignKey(CaseNoteRecord, null=True, blank=True, on_delete=models.PROTECT, related_name="audit_events")
    request_id = models.CharField(max_length=128)
    idempotency = models.OneToOneField(IdempotencyRecord, on_delete=models.PROTECT, related_name="audit_event")

    class Meta:
        db_table = "europilot_audit_event"
        constraints = [
            models.CheckConstraint(name="audit_action_supported", condition=models.Q(action__in=[ACTION_CASE_TRANSITIONED, ACTION_NOTE_CREATED])),
            models.CheckConstraint(name="audit_request_id_nonempty", condition=~models.Q(request_id="")),
        ]

    def clean(self):
        if self.idempotency_id and self.idempotency.case_id != self.case_id:
            raise ValidationError("audit event and idempotency record must belong to the same case")
        if self.idempotency_id and self.idempotency.action != self.action:
            raise ValidationError("audit event and idempotency action must match")
        if self.idempotency_id and self.idempotency.request_id != self.request_id:
            raise ValidationError("audit event and idempotency request_id must match")
        if self.note_id and self.note.case_id != self.case_id:
            raise ValidationError("audit event and note must belong to the same case")
        if self.action == ACTION_CASE_TRANSITIONED and (not self.previous_state or not self.new_state):
            raise ValidationError("case transition audit events require previous and new states")
        if self.action == ACTION_CASE_TRANSITIONED and self.note_id:
            raise ValidationError("case transition audit events cannot reference a note")
        if self.action == ACTION_NOTE_CREATED and not self.note_id:
            raise ValidationError("note audit events require a note")
        if self.action == ACTION_NOTE_CREATED and (self.previous_state or self.new_state or self.reason):
            raise ValidationError("note audit events cannot contain transition metadata")

    def save(self, *args, **kwargs):
        self.actor = SYNTHETIC_ACTOR
        self.full_clean()
        return super().save(*args, **kwargs)
