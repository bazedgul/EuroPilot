from datetime import datetime, timezone
from decimal import Decimal

import pytest

from europilot.domain import (
    Attempt,
    Delivery,
    EventType,
    Evidence,
    Invoice,
    Investigation,
    Outcome,
    Payment,
    ProviderEvent,
    evaluate_outcome,
)


UTC = timezone.utc


def evidence(evidence_id: str, event_type: EventType, observed: int, received: int, provider: str = "synthetic", payment_id: str = "pay-1") -> Evidence:
    return Evidence(evidence_id, payment_id, provider, evidence_id, datetime.fromtimestamp(observed, UTC), datetime.fromtimestamp(received, UTC), event_type, provider, True)


@pytest.fixture
def investigation() -> Investigation:
    invoice = Invoice("inv-1", Decimal("10.00"))
    return Investigation(Payment("pay-1", invoice.invoice_id))


def test_timeout_retry_and_duplicate_delivery_preserve_identity(investigation: Investigation) -> None:
    first = Attempt("att-1", "pay-1", "req-1", datetime(2026, 1, 1, tzinfo=UTC))
    retry = Attempt("att-2", "pay-1", "req-2", datetime(2026, 1, 2, tzinfo=UTC), retry_of="att-1")
    investigation.add_attempt(first)
    investigation.add_attempt(retry)
    event = ProviderEvent("synthetic", "evt-1", "pay-1", EventType.UNKNOWN, datetime(2026, 1, 3, tzinfo=UTC), datetime(2026, 1, 4, tzinfo=UTC))
    investigation.add_event(event)
    investigation.add_delivery(Delivery("delivery-1", "synthetic", "evt-1", datetime(2026, 1, 4, tzinfo=UTC)))
    investigation.add_delivery(Delivery("delivery-2", "synthetic", "evt-1", datetime(2026, 1, 5, tzinfo=UTC)))
    finding = evaluate_outcome("pay-1", ())
    assert [a.attempt_id for a in investigation.attempts] == ["att-1", "att-2"]
    assert len(investigation.deliveries) == 2
    assert finding.outcome is Outcome.UNKNOWN


def test_confirmed_success_and_failure() -> None:
    assert evaluate_outcome("pay-1", [evidence("success", EventType.SUCCESS, 1, 2)]).outcome is Outcome.CONFIRMED_SUCCESS
    assert evaluate_outcome("pay-1", [evidence("failure", EventType.FAILURE, 1, 2)]).outcome is Outcome.CONFIRMED_FAILURE


def test_conflicting_authoritative_evidence_remains_conflict() -> None:
    finding = evaluate_outcome("pay-1", [evidence("success", EventType.SUCCESS, 1, 2), evidence("failure", EventType.FAILURE, 3, 4)])
    assert finding.outcome is Outcome.CONFLICT
    assert {item.evidence_id for item in finding.evidence} == {"success", "failure"}


def test_event_time_and_received_time_are_preserved_and_order_is_repeatable() -> None:
    items = [evidence("late", EventType.SUCCESS, 10, 30), evidence("early", EventType.SUCCESS, 20, 25)]
    first = evaluate_outcome("pay-1", items)
    second = evaluate_outcome("pay-1", list(reversed(items)))
    assert [(e.observed_at, e.received_at) for e in first.evidence] == [(e.observed_at, e.received_at) for e in second.evidence]
    assert first.outcome is Outcome.CONFIRMED_SUCCESS


def test_invalid_relationships_and_unsupported_correlation_are_rejected(investigation: Investigation) -> None:
    with pytest.raises(ValueError, match="another payment"):
        investigation.add_attempt(Attempt("att-x", "other", "req-x", datetime.now(UTC)))
    with pytest.raises(ValueError, match="unknown provider event"):
        investigation.add_delivery(Delivery("delivery-x", "synthetic", "missing", datetime.now(UTC)))


def test_missing_or_non_authoritative_evidence_is_unknown() -> None:
    finding = evaluate_outcome("pay-1", [Evidence("local", "pay-1", "local", "note", datetime.now(UTC), datetime.now(UTC), EventType.UNKNOWN)])
    assert finding.outcome is Outcome.UNKNOWN
    assert finding.missing_evidence


def test_evidence_is_scoped_to_payment_and_authority() -> None:
    other_payment = evidence("other-success", EventType.SUCCESS, 1, 2, payment_id="pay-2")
    non_authoritative = Evidence("untrusted", "pay-1", "synthetic", "untrusted", datetime.now(UTC), datetime.now(UTC), EventType.SUCCESS, "synthetic")
    assert evaluate_outcome("pay-1", [other_payment, non_authoritative]).outcome is Outcome.UNKNOWN


def test_investigation_rejects_cross_payment_and_duplicate_evidence(investigation: Investigation) -> None:
    item = evidence("evidence-1", EventType.SUCCESS, 1, 2)
    investigation.add_evidence(item)
    with pytest.raises(ValueError, match="another payment"):
        investigation.add_evidence(evidence("other", EventType.SUCCESS, 1, 2, payment_id="pay-2"))
    with pytest.raises(ValueError, match="duplicate evidence_id"):
        investigation.add_evidence(item)


def test_conflict_explains_why_authoritative_evidence_is_insufficient() -> None:
    finding = evaluate_outcome("pay-1", [evidence("success", EventType.SUCCESS, 1, 2), evidence("failure", EventType.FAILURE, 3, 4)])
    assert finding.conflict_evidence == finding.evidence
    assert finding.missing_evidence
    assert finding.rule_version == "phase1-v1"


def test_authoritative_evidence_requires_provider() -> None:
    with pytest.raises(ValueError, match="provider"):
        Evidence("evidence-1", "pay-1", "fixture", "ref", datetime.now(UTC), datetime.now(UTC), EventType.SUCCESS, authoritative=True)
