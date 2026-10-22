from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.db import IntegrityError

from europilot.models import (
    AttemptRecord,
    CaseRecord,
    EvidenceRecord,
    FindingRecord,
    InvestigationRecord,
    InvoiceRecord,
    PaymentRecord,
    ProviderEventRecord,
)


pytestmark = pytest.mark.django_db


def make_investigation(suffix: str = "") -> InvestigationRecord:
    invoice = InvoiceRecord.objects.create(invoice_id=f"backfill-invoice{suffix}", amount="10.00")
    payment = PaymentRecord.objects.create(payment_id=f"backfill-payment{suffix}", invoice=invoice)
    return InvestigationRecord.objects.create(
        investigation_id=f"backfill-investigation{suffix}", payment=payment
    )


def run_backfill() -> str:
    output = StringIO()
    call_command("backfill_cases", stdout=output)
    return output.getvalue()


def test_backfill_creates_one_open_case_for_each_investigation() -> None:
    first = make_investigation("-1")
    second = make_investigation("-2")
    investigation_count = InvestigationRecord.objects.count()
    existing_case_count = CaseRecord.objects.count()

    output = run_backfill()

    assert f"Created {investigation_count - existing_case_count} case(s); {existing_case_count} case(s) already existed." in output
    assert CaseRecord.objects.count() == investigation_count
    assert CaseRecord.objects.get(investigation=first).case_id == "case-backfill-investigation-1"
    assert CaseRecord.objects.get(investigation=second).state == CaseRecord.State.OPEN


def test_backfill_preserves_existing_case() -> None:
    investigation = make_investigation()
    existing = CaseRecord.objects.create(
        case_id="existing-case",
        investigation=investigation,
        state=CaseRecord.State.DEFERRED,
        resolution_reason="Waiting for review",
    )
    investigation_count = InvestigationRecord.objects.count()

    output = run_backfill()

    assert f"Created {investigation_count - 1} case(s); 1 case(s) already existed." in output
    existing.refresh_from_db()
    assert existing.case_id == "existing-case"
    assert existing.state == CaseRecord.State.DEFERRED
    assert existing.resolution_reason == "Waiting for review"


def test_backfill_is_idempotent_when_run_twice() -> None:
    investigation = make_investigation()
    investigation_count = InvestigationRecord.objects.count()

    first_output = run_backfill()
    second_output = run_backfill()

    assert f"Created {investigation_count} case(s); 0 case(s) already existed." in first_output
    assert f"Created 0 case(s); {investigation_count} case(s) already existed." in second_output
    assert CaseRecord.objects.filter(investigation=investigation).count() == 1


def test_backfill_does_not_change_phase_one_records() -> None:
    investigation = make_investigation()
    payment = investigation.payment
    attempt = AttemptRecord.objects.create(
        attempt_id="backfill-attempt",
        payment=payment,
        request_id="backfill-request",
        requested_at="2026-01-01T00:00:00Z",
    )
    provider_event = ProviderEventRecord.objects.create(
        provider="synthetic",
        event_id="backfill-event",
        payment=payment,
        event_type="timeout",
        occurred_at="2026-01-01T00:00:00Z",
        received_at="2026-01-01T00:00:00Z",
    )
    evidence = EvidenceRecord.objects.create(
        evidence_id="backfill-evidence",
        payment=payment,
        source="synthetic",
        reference="backfill-event",
        observed_at="2026-01-01T00:00:00Z",
        received_at="2026-01-01T00:00:00Z",
        event_type="timeout",
        authoritative=False,
    )
    finding = FindingRecord.objects.create(
        investigation=investigation,
        outcome="unknown",
        missing_evidence=["authoritative outcome"],
    )
    before = {
        "investigation": InvestigationRecord.objects.count(),
        "attempt": AttemptRecord.objects.count(),
        "provider_event": ProviderEventRecord.objects.count(),
        "evidence": EvidenceRecord.objects.count(),
        "finding": FindingRecord.objects.count(),
    }

    run_backfill()

    assert {
        "investigation": InvestigationRecord.objects.count(),
        "attempt": AttemptRecord.objects.count(),
        "provider_event": ProviderEventRecord.objects.count(),
        "evidence": EvidenceRecord.objects.count(),
        "finding": FindingRecord.objects.count(),
    } == before
    assert attempt.payment_id == payment.payment_id
    assert provider_event.payment_id == payment.payment_id
    assert evidence.payment_id == payment.payment_id
    assert finding.investigation_id == investigation.investigation_id


def test_backfill_preserves_previous_cases_and_exposes_unrelated_integrity_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = make_investigation("-1")
    second = make_investigation("-2")
    original_get_or_create = CaseRecord.objects.get_or_create

    def fail_for_second(*args, **kwargs):
        if kwargs.get("investigation") == second:
            raise IntegrityError("synthetic failure")
        return original_get_or_create(*args, **kwargs)

    monkeypatch.setattr(CaseRecord.objects, "get_or_create", fail_for_second)

    with pytest.raises(IntegrityError, match="synthetic failure") as error:
        run_backfill()

    assert str(error.value) == "synthetic failure"
    assert "collision" not in str(error.value).lower()
    assert CaseRecord.objects.filter(investigation=first).count() == 1
    assert CaseRecord.objects.filter(investigation=second).count() == 0


def test_backfill_reports_generated_id_owned_by_another_investigation() -> None:
    owner = make_investigation("-owner")
    target = make_investigation("-target")
    conflicting = CaseRecord.objects.create(
        case_id=f"case-{target.investigation_id}",
        investigation=owner,
    )

    with pytest.raises(CommandError, match="Case ID collision") as error:
        run_backfill()

    assert conflicting.investigation_id == owner.investigation_id
    assert CaseRecord.objects.filter(investigation=target).exists() is False
    assert InvestigationRecord.objects.get(pk=owner.pk).payment_id == owner.payment_id
    assert InvestigationRecord.objects.get(pk=target.pk).payment_id == target.payment_id
    assert target.investigation_id in str(error.value)


def test_backfill_recovers_after_collision_is_resolved() -> None:
    owner = make_investigation("-owner")
    target = make_investigation("-target")
    conflicting = CaseRecord.objects.create(
        case_id=f"case-{target.investigation_id}",
        investigation=owner,
    )

    with pytest.raises(CommandError, match="Case ID collision"):
        run_backfill()

    conflicting.delete()
    run_backfill()

    created = CaseRecord.objects.get(investigation=target)
    assert created.case_id == f"case-{target.investigation_id}"
    assert created.state == CaseRecord.State.OPEN
