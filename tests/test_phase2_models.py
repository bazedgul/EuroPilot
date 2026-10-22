from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

import pytest

from europilot.models import (
    ACTION_CASE_TRANSITIONED,
    ACTION_NOTE_CREATED,
    AuditEventRecord,
    CaseNoteRecord,
    CaseRecord,
    IdempotencyRecord,
    InvestigationRecord,
    InvoiceRecord,
    PaymentRecord,
)
from europilot.domain import normalize_request_id, normalize_text, validate_fingerprint


pytestmark = pytest.mark.django_db


def make_case(suffix: str = "") -> CaseRecord:
    invoice = InvoiceRecord.objects.create(invoice_id=f"phase2-invoice{suffix}", amount="10.00")
    payment = PaymentRecord.objects.create(payment_id=f"phase2-payment{suffix}", invoice=invoice)
    investigation = InvestigationRecord.objects.create(investigation_id=f"phase2-investigation{suffix}", payment=payment)
    return CaseRecord.objects.create(case_id=f"case-1{suffix}", investigation=investigation)


def test_case_model_supports_approved_states_and_requires_terminal_reason() -> None:
    case = make_case()
    case.state = CaseRecord.State.RESOLVED
    with pytest.raises(ValidationError, match="require a reason"):
        case.save()
    case.resolution_reason = "Evidence reviewed"
    case.save()
    assert case.state == "resolved"


def test_note_actor_is_server_controlled_and_text_is_bounded() -> None:
    case = make_case()
    note = CaseNoteRecord(note_id="note-1", case=case, text=" analyst note ", actor="client-supplied")
    note.save()
    assert note.actor == "synthetic_local_operator"
    with pytest.raises(ValidationError, match="note text is required"):
        CaseNoteRecord(note_id="note-2", case=case, text="   ").save()


def test_idempotency_scope_is_database_unique() -> None:
    case = make_case()
    fields = dict(case=case, action=ACTION_CASE_TRANSITIONED, request_id="req-1", fingerprint="a" * 64, original_status=200, original_response={"ok": True})
    IdempotencyRecord.objects.create(**fields)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            IdempotencyRecord.objects.bulk_create([IdempotencyRecord(**fields)])


def test_normalization_helper_trims_and_rejects_blank_or_overlong_values() -> None:
    assert normalize_text("  note  ", "note", 10) == "note"
    assert normalize_request_id(" req-1 ") == "req-1"
    with pytest.raises(ValueError, match="required"):
        normalize_text("   ", "note", 10)
    with pytest.raises(ValueError, match="at most 128"):
        normalize_request_id("x" * 129)


def test_fingerprint_requires_lowercase_sha256_hex() -> None:
    assert validate_fingerprint("a" * 64) == "a" * 64
    with pytest.raises(ValueError, match="SHA-256"):
        validate_fingerprint("g" * 64)
    with pytest.raises(ValidationError, match="invalid fingerprint"):
        IdempotencyRecord(case=make_case(), action=ACTION_CASE_TRANSITIONED, request_id="req", fingerprint="not-a-digest", original_status=200, original_response={}).save()


def test_model_boundaries_are_validated() -> None:
    case = make_case()
    CaseNoteRecord(note_id="note-max", case=case, text="x" * 2000).save()
    with pytest.raises(ValidationError, match="at most 2000"):
        CaseNoteRecord(note_id="note-too-long", case=case, text="x" * 2001).save()
    with pytest.raises(ValidationError, match="at most 128"):
        IdempotencyRecord(case=case, action=ACTION_CASE_TRANSITIONED, request_id="x" * 129, fingerprint="a" * 64, original_status=200, original_response={}).save()
    case.state = CaseRecord.State.DEFERRED
    case.resolution_reason = "r" * 500
    case.save()
    case.resolution_reason = "r" * 501
    with pytest.raises(ValidationError, match="at most 500"):
        case.save()


def test_audit_references_must_match_case_action_and_request() -> None:
    case = make_case()
    other_case = make_case("-other")
    idem = IdempotencyRecord.objects.create(case=case, action=ACTION_CASE_TRANSITIONED, request_id="req-1", fingerprint="a" * 64, original_status=200, original_response={"ok": True})
    with pytest.raises(ValidationError, match="action must match"):
        AuditEventRecord(audit_id="audit-action", case=case, action=ACTION_NOTE_CREATED, actor="client", request_id="req-1", idempotency=idem, note=CaseNoteRecord(note_id="note-action", case=case, text="note")).save()
    with pytest.raises(ValidationError, match="request_id must match"):
        AuditEventRecord(audit_id="audit-request", case=case, action=ACTION_CASE_TRANSITIONED, request_id="req-2", idempotency=idem, previous_state="open", new_state="under_review").save()
    other_idem = IdempotencyRecord.objects.create(case=other_case, action=ACTION_CASE_TRANSITIONED, request_id="req-other", fingerprint="b" * 64, original_status=200, original_response={"ok": True})
    with pytest.raises(ValidationError, match="same case"):
        AuditEventRecord(audit_id="audit-case", case=case, action=ACTION_CASE_TRANSITIONED, request_id="req-other", idempotency=other_idem, previous_state="open", new_state="under_review").save()


def test_case_investigation_relationship_is_one_to_one() -> None:
    case = make_case()
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            CaseRecord.objects.bulk_create([CaseRecord(case_id="case-2", investigation=case.investigation)])


def test_direct_database_constraints_reject_unsupported_values() -> None:
    case = make_case()
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            CaseRecord.objects.bulk_create([CaseRecord(case_id="case-invalid", investigation=InvestigationRecord.objects.get(investigation_id="phase2-investigation"), state="unsupported")])
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            IdempotencyRecord.objects.bulk_create([IdempotencyRecord(case=case, action="unsupported", request_id="req", fingerprint="a" * 64, original_status=200, original_response={})])
