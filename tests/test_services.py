from unittest.mock import patch

import pytest
from django.db import IntegrityError

from europilot.domain import DomainValidationError, validate_case_transition, validate_note
from europilot.models import ACTION_CASE_TRANSITIONED, ACTION_NOTE_CREATED, AuditEventRecord, CaseRecord, CaseNoteRecord, IdempotencyRecord, InvestigationRecord, InvoiceRecord, PaymentRecord
from europilot.services import CaseNotFoundError, IdempotencyConflictError, WorkflowConcurrencyError, create_case_note, transition_case


pytestmark = pytest.mark.django_db


def make_case(suffix: str = "") -> CaseRecord:
    invoice = InvoiceRecord.objects.create(invoice_id=f"service-invoice{suffix}", amount="10.00")
    payment = PaymentRecord.objects.create(payment_id=f"service-payment{suffix}", invoice=invoice)
    investigation = InvestigationRecord.objects.create(investigation_id=f"service-investigation{suffix}", payment=payment)
    return CaseRecord.objects.create(case_id=f"service-case{suffix}", investigation=investigation)


def test_transition_commits_case_idempotency_and_one_audit_event() -> None:
    case = make_case()
    result = transition_case(case.case_id, validate_case_transition("open", "under_review", None, " request-1 "))

    case.refresh_from_db()
    assert case.state == "under_review"
    assert case.resolution_reason == ""
    assert result["case"]["state"] == "under_review"
    assert result["case"]["payment_outcome"] == "unknown"
    assert result["audit_event"]["created_at"] == AuditEventRecord.objects.get(case=case).created_at.isoformat()
    assert IdempotencyRecord.objects.filter(case=case, action=ACTION_CASE_TRANSITIONED, request_id="request-1").count() == 1
    assert AuditEventRecord.objects.filter(case=case, action=ACTION_CASE_TRANSITIONED).count() == 1
    audit = AuditEventRecord.objects.get(case=case)
    assert audit.previous_state == "open"
    assert audit.new_state == "under_review"
    assert audit.request_id == "request-1"


def test_note_commits_note_idempotency_audit_and_server_actor() -> None:
    case = make_case()
    result = create_case_note(case.case_id, validate_note(" note ", " request-note "))

    note = CaseNoteRecord.objects.get(case=case)
    assert result["note"]["text"] == "note"
    assert result["note"]["created_at"] == note.created_at.isoformat()
    assert result["audit_event"]["created_at"] == AuditEventRecord.objects.get(case=case, action=ACTION_NOTE_CREATED).created_at.isoformat()
    assert note.actor == "synthetic_local_operator"
    assert IdempotencyRecord.objects.filter(case=case, action=ACTION_NOTE_CREATED, request_id="request-note").count() == 1
    assert AuditEventRecord.objects.filter(case=case, action=ACTION_NOTE_CREATED, note=note).count() == 1


def test_same_normalized_request_replays_exact_response_without_side_effects() -> None:
    case = make_case()
    command = validate_note(" note ", " request-note ")
    first = create_case_note(case.case_id, command)
    counts = (CaseNoteRecord.objects.count(), AuditEventRecord.objects.count(), IdempotencyRecord.objects.count())

    replay = create_case_note(case.case_id, validate_note("note", "request-note"))

    assert replay == first
    assert (CaseNoteRecord.objects.count(), AuditEventRecord.objects.count(), IdempotencyRecord.objects.count()) == counts
    assert replay["note"]["created_at"] == first["note"]["created_at"]
    assert replay["audit_event"]["created_at"] == first["audit_event"]["created_at"]


def test_same_request_with_different_payload_raises_stable_conflict() -> None:
    case = make_case()
    create_case_note(case.case_id, validate_note("first", "request-note"))

    with pytest.raises(IdempotencyConflictError) as error:
        create_case_note(case.case_id, validate_note("second", "request-note"))

    assert error.value.code == "idempotency_key_reused"


def test_transition_replay_does_not_repeat_state_change_or_audit() -> None:
    case = make_case()
    command = validate_case_transition("open", "deferred", " waiting ", "request-transition")
    first = transition_case(case.case_id, command)
    counts = (AuditEventRecord.objects.count(), IdempotencyRecord.objects.count())

    replay = transition_case(case.case_id, validate_case_transition("open", "deferred", "waiting", "request-transition"))

    assert replay == first
    assert (AuditEventRecord.objects.count(), IdempotencyRecord.objects.count()) == counts
    assert CaseRecord.objects.get(pk=case.pk).state == "deferred"
    assert replay["case"]["payment_outcome"] == first["case"]["payment_outcome"]
    assert replay["audit_event"]["created_at"] == first["audit_event"]["created_at"]


def test_invalid_transition_creates_no_records() -> None:
    case = make_case()
    with pytest.raises(DomainValidationError) as error:
        validate_case_transition("open", "resolved", None, "request-invalid")

    assert error.value.code == "invalid_transition"
    assert not IdempotencyRecord.objects.exists()
    assert not AuditEventRecord.objects.exists()
    assert CaseRecord.objects.get(pk=case.pk).state == "open"


def test_service_rolls_back_intermediate_note_writes() -> None:
    case = make_case()
    command = validate_note("note", "request-note")
    with patch("europilot.services.AuditEventRecord.objects.create", side_effect=IntegrityError("forced failure")):
        with pytest.raises(WorkflowConcurrencyError):
            create_case_note(case.case_id, command)

    assert not CaseNoteRecord.objects.exists()
    assert not IdempotencyRecord.objects.exists()
    assert not AuditEventRecord.objects.exists()


def test_service_rolls_back_intermediate_transition_writes() -> None:
    case = make_case()
    command = validate_case_transition("open", "under_review", None, "request-transition")
    with patch("europilot.services.AuditEventRecord.objects.create", side_effect=IntegrityError("forced failure")):
        with pytest.raises(WorkflowConcurrencyError):
            transition_case(case.case_id, command)

    case.refresh_from_db()
    assert case.state == "open"
    assert not IdempotencyRecord.objects.exists()
    assert not AuditEventRecord.objects.exists()


def test_request_id_scope_allows_same_id_for_different_actions() -> None:
    case = make_case()
    transition_case(case.case_id, validate_case_transition("open", "under_review", None, "shared-request"))
    result = create_case_note(case.case_id, validate_note("note", "shared-request"))

    assert result["note"]["text"] == "note"
    assert IdempotencyRecord.objects.filter(case=case, request_id="shared-request").count() == 2


def test_case_isolation_and_missing_case_errors() -> None:
    first = make_case("-first")
    second = make_case("-second")
    create_case_note(second.case_id, validate_note("second", "request-second"))

    with pytest.raises(CaseNotFoundError) as error:
        create_case_note("missing", validate_note("note", "request-missing"))
    assert error.value.code == "case_not_found"
    assert CaseNoteRecord.objects.filter(case=first).count() == 0
    assert CaseNoteRecord.objects.filter(case=second).count() == 1


def test_integrity_failure_without_winning_idempotency_record_is_retryable() -> None:
    case = make_case()
    command = validate_note("note", "request-note")
    with patch("europilot.services.CaseNoteRecord.objects.create", side_effect=IntegrityError("unrelated")):
        with pytest.raises(WorkflowConcurrencyError) as error:
            create_case_note(case.case_id, command)
    assert error.value.code == "concurrency_retryable"
