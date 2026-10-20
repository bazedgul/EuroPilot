import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction

from europilot.models import (
    AttemptRecord,
    DeliveryRecord,
    EvidenceRecord,
    FindingEvidenceRecord,
    FindingRecord,
    InvestigationRecord,
    InvoiceRecord,
    PaymentRecord,
    ProviderEventRecord,
)


pytestmark = pytest.mark.django_db


def test_database_constraints_reject_duplicate_provider_event_and_delivery() -> None:
    payment = PaymentRecord.objects.get(payment_id="payment-1")
    event = ProviderEventRecord.objects.get(provider="synthetic", event_id="event-1")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ProviderEventRecord.objects.create(provider="synthetic", event_id="event-1", payment=payment, event_type="unknown", occurred_at=event.occurred_at)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            DeliveryRecord.objects.create(delivery_id="delivery-1", provider_event=event, received_at=event.occurred_at)


def test_retry_and_supporting_evidence_cannot_cross_payment_boundaries() -> None:
    invoice = InvoiceRecord.objects.create(invoice_id="invoice-2", amount="20.00")
    other_payment = PaymentRecord.objects.create(payment_id="payment-2", invoice=invoice)
    first = AttemptRecord.objects.get(attempt_id="attempt-1")
    with pytest.raises(ValidationError, match="same logical payment"):
        AttemptRecord(attempt_id="attempt-other", payment=other_payment, request_id="request-other", requested_at=first.requested_at, retry_of=first).save()

    evidence = EvidenceRecord.objects.get(evidence_id="evidence-1")
    investigation = InvestigationRecord.objects.get(investigation_id="investigation-1")
    finding = FindingRecord.objects.get(investigation=investigation)
    other_evidence = EvidenceRecord.objects.create(evidence_id="evidence-2", payment=other_payment, source="synthetic", reference="other", observed_at=evidence.observed_at, received_at=evidence.received_at, event_type="success", provider="synthetic", authoritative=True)
    with pytest.raises(ValidationError, match="investigation payment"):
        FindingEvidenceRecord(finding=finding, evidence=other_evidence).save()


def test_get_endpoints_do_not_seed_or_mutate_database(client) -> None:
    before = {model: model.objects.count() for model in (InvoiceRecord, PaymentRecord, AttemptRecord, ProviderEventRecord, DeliveryRecord, EvidenceRecord, InvestigationRecord, FindingRecord)}
    assert client.get("/api/v1/investigations/").status_code == 200
    assert client.get("/api/v1/investigations/investigation-1/").status_code == 200
    after = {model: model.objects.count() for model in before}
    assert after == before
