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
    DomainValidationError,
    SYNTHETIC_ACTOR,
    evaluate_outcome,
    validate_case_transition,
    validate_note,
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


def test_provider_event_can_preserve_unknown_receipt_time_and_delivery_times() -> None:
    event = ProviderEvent("synthetic", "evt-unknown-receipt", "pay-1", EventType.UNKNOWN, datetime(2026, 1, 3, tzinfo=UTC), None)
    investigation = Investigation(Payment("pay-1", "inv-1"))

    investigation.add_event(event)
    investigation.add_delivery(Delivery("delivery-early", "synthetic", "evt-unknown-receipt", datetime(2026, 1, 4, tzinfo=UTC)))
    investigation.add_delivery(Delivery("delivery-late", "synthetic", "evt-unknown-receipt", datetime(2026, 1, 5, tzinfo=UTC)))

    assert investigation.events[0].occurred_at == datetime(2026, 1, 3, tzinfo=UTC)
    assert investigation.events[0].received_at is None
    assert [delivery.received_at for delivery in investigation.deliveries] == [datetime(2026, 1, 4, tzinfo=UTC), datetime(2026, 1, 5, tzinfo=UTC)]
    assert evaluate_outcome("pay-1", ()).outcome is Outcome.UNKNOWN


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


@pytest.mark.parametrize(
    ("source", "target"),
    [("open", "under_review"), ("open", "deferred"), ("under_review", "resolved"), ("under_review", "deferred"), ("deferred", "open"), ("deferred", "under_review")],
)
def test_approved_case_transitions_are_validated(source: str, target: str) -> None:
    command = validate_case_transition(source, target, " Evidence reviewed " if target in {"resolved", "deferred"} else None, " request-1 ")

    assert command.target_state == target
    assert command.reason == ("Evidence reviewed" if target in {"resolved", "deferred"} else None)
    assert command.request_id == "request-1"


@pytest.mark.parametrize(
    ("source", "target"),
    [("open", "resolved"), ("under_review", "open"), ("deferred", "resolved"), ("resolved", "open"), ("resolved", "under_review"), ("resolved", "deferred")],
)
def test_forbidden_case_transitions_have_stable_error_code(source: str, target: str) -> None:
    with pytest.raises(DomainValidationError) as error:
        validate_case_transition(source, target, "reason", "request-1")

    assert error.value.code == "invalid_transition"


def test_case_transition_rejects_unsupported_states() -> None:
    with pytest.raises(DomainValidationError) as error:
        validate_case_transition("unknown", "open", None, "request-1")

    assert error.value.code == "unsupported_state"


@pytest.mark.parametrize("target", ["resolved", "deferred"])
def test_terminal_case_transitions_require_bounded_reason(target: str) -> None:
    with pytest.raises(DomainValidationError, match="reason") as missing:
        validate_case_transition("under_review", target, "   ", "request-1")
    assert missing.value.code == "reason_required"

    accepted = validate_case_transition("under_review", target, "r" * 500, "request-1")
    assert accepted.reason == "r" * 500
    with pytest.raises(DomainValidationError) as too_long:
        validate_case_transition("under_review", target, "r" * 501, "request-1")
    assert too_long.value.code == "reason_too_long"


def test_nonterminal_transition_reason_is_optional_and_normalized() -> None:
    assert validate_case_transition("open", "under_review", "  ", "request-1").reason is None
    assert validate_case_transition("open", "under_review", " reason ", "request-1").reason == "reason"


@pytest.mark.parametrize("request_id", ["", "   ", "r" * 129])
def test_request_id_boundaries_have_stable_errors(request_id: str) -> None:
    with pytest.raises(DomainValidationError) as error:
        validate_case_transition("open", "under_review", None, request_id)

    assert error.value.code in {"request_id_required", "request_id_too_long"}


def test_note_validation_normalizes_text_and_assigns_server_actor() -> None:
    note = validate_note("  analyst note  ", " request-1 ")

    assert note.text == "analyst note"
    assert note.request_id == "request-1"
    assert note.actor == SYNTHETIC_ACTOR


@pytest.mark.parametrize("text", ["", "   ", "n" * 2001])
def test_note_validation_rejects_blank_or_overlong_text(text: str) -> None:
    with pytest.raises(DomainValidationError) as error:
        validate_note(text, "request-1")

    assert error.value.code in {"note_required", "note_too_long"}


def test_note_exact_limit_and_caller_actor_override_are_handled() -> None:
    assert validate_note("n" * 2000, "request-1").text == "n" * 2000
    with pytest.raises(DomainValidationError) as error:
        validate_note("note", "request-1", actor="client-supplied")
    assert error.value.code == "actor_not_allowed"


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
