from django.core.exceptions import ValidationError
from django.db import models


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
