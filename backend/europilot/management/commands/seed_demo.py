from datetime import datetime, timezone
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from europilot.models import (
    AttemptRecord,
    DeliveryRecord,
    EvidenceRecord,
    FindingRecord,
    InvestigationRecord,
    InvoiceRecord,
    PaymentRecord,
    ProviderEventRecord,
)


class Command(BaseCommand):
    help = "Create the idempotent synthetic EuroPilot investigation fixture."

    @transaction.atomic
    def handle(self, *args, **options):
        invoice, _ = InvoiceRecord.objects.get_or_create(invoice_id="invoice-1", defaults={"amount": Decimal("10.00")})
        payment, _ = PaymentRecord.objects.get_or_create(payment_id="payment-1", defaults={"invoice": invoice})
        attempt_one, _ = AttemptRecord.objects.get_or_create(
            attempt_id="attempt-1", defaults={"payment": payment, "request_id": "request-1", "requested_at": datetime(2026, 1, 1, tzinfo=timezone.utc), "outcome": "unknown"}
        )
        attempt_two, _ = AttemptRecord.objects.get_or_create(
            attempt_id="attempt-2", defaults={"payment": payment, "request_id": "request-2", "requested_at": datetime(2026, 1, 2, tzinfo=timezone.utc), "outcome": "unknown", "retry_of": attempt_one}
        )
        event, _ = ProviderEventRecord.objects.get_or_create(
            provider="synthetic", event_id="event-1", defaults={"payment": payment, "event_type": "unknown", "occurred_at": datetime(2026, 1, 3, tzinfo=timezone.utc), "payload": ""}
        )
        DeliveryRecord.objects.get_or_create(delivery_id="delivery-1", defaults={"provider_event": event, "received_at": datetime(2026, 1, 4, tzinfo=timezone.utc)})
        DeliveryRecord.objects.get_or_create(delivery_id="delivery-2", defaults={"provider_event": event, "received_at": datetime(2026, 1, 5, tzinfo=timezone.utc)})
        evidence, _ = EvidenceRecord.objects.get_or_create(
            evidence_id="evidence-1", defaults={"payment": payment, "source": "synthetic", "reference": "event-1", "observed_at": event.occurred_at, "received_at": datetime(2026, 1, 4, tzinfo=timezone.utc), "event_type": "unknown", "provider": "synthetic", "authoritative": False}
        )
        investigation, _ = InvestigationRecord.objects.get_or_create(investigation_id="investigation-1", defaults={"payment": payment})
        finding, _ = FindingRecord.objects.get_or_create(investigation=investigation, defaults={"outcome": "unknown", "missing_evidence": ["authoritative success or failure evidence is missing"]})
        finding.supporting_evidence.add(*[])
        self.stdout.write(self.style.SUCCESS("Synthetic demo data is present (idempotent)."))
