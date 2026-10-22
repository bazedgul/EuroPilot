"""Transactional case workflow services."""

from __future__ import annotations

import hashlib
import json
from uuid import uuid4

from django.db import IntegrityError, transaction

from .domain import EventType, Evidence, NoteCommand, SYNTHETIC_ACTOR, TransitionCommand, evaluate_outcome, validate_case_transition
from .models import (
    ACTION_CASE_TRANSITIONED,
    ACTION_NOTE_CREATED,
    AuditEventRecord,
    CaseNoteRecord,
    CaseRecord,
    EvidenceRecord,
    IdempotencyRecord,
)


class WorkflowServiceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class CaseNotFoundError(WorkflowServiceError):
    def __init__(self, case_id: str) -> None:
        super().__init__("case_not_found", f"case '{case_id}' was not found")


class IdempotencyConflictError(WorkflowServiceError):
    def __init__(self) -> None:
        super().__init__("idempotency_key_reused", "the request ID was already used with a different payload")


class WorkflowConcurrencyError(WorkflowServiceError):
    def __init__(self) -> None:
        super().__init__("concurrency_retryable", "the operation could not be safely completed; retry the request")


def _fingerprint(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _existing_result(case_id: str, action: str, request_id: str, fingerprint: str) -> dict | None:
    record = IdempotencyRecord.objects.filter(case_id=case_id, action=action, request_id=request_id).first()
    if record is None:
        return None
    if record.fingerprint != fingerprint:
        raise IdempotencyConflictError()
    return record.original_response


def _audit_payload(event: AuditEventRecord) -> dict:
    return {
        "id": event.audit_id,
        "action": event.action,
        "actor": SYNTHETIC_ACTOR,
        "previous_state": event.previous_state or None,
        "new_state": event.new_state or None,
        "reason": event.reason or None,
        "note_id": event.note_id,
        "request_id": event.request_id,
        "created_at": event.created_at.isoformat(),
    }


def _payment_outcome(case: CaseRecord) -> str:
    payment = case.investigation.payment
    evidence = [
        Evidence(
            item.evidence_id,
            payment.payment_id,
            item.source,
            item.reference,
            item.observed_at,
            item.received_at,
            EventType(item.event_type),
            item.provider,
            item.authoritative,
        )
        for item in EvidenceRecord.objects.filter(payment=payment).order_by("evidence_id")
    ]
    return evaluate_outcome(payment.payment_id, evidence).outcome.value


def _replay_or_retry(case_id: str, action: str, request_id: str, fingerprint: str) -> dict:
    result = _existing_result(case_id, action, request_id, fingerprint)
    if result is not None:
        return result
    raise WorkflowConcurrencyError()


def transition_case(case_id: str, command: TransitionCommand) -> dict:
    fingerprint = _fingerprint({"target_state": command.target_state, "reason": command.reason})
    try:
        with transaction.atomic():
            case = CaseRecord.objects.select_for_update().filter(case_id=case_id).first()
            if case is None:
                raise CaseNotFoundError(case_id)
            replay = _existing_result(case_id, ACTION_CASE_TRANSITIONED, command.request_id, fingerprint)
            if replay is not None:
                return replay

            command = validate_case_transition(case.state, command.target_state, command.reason, command.request_id)

            previous_state = case.state
            case.state = command.target_state
            case.resolution_reason = command.reason or ""
            case.save()
            idempotency = IdempotencyRecord.objects.create(
                case=case,
                action=ACTION_CASE_TRANSITIONED,
                request_id=command.request_id,
                fingerprint=fingerprint,
                original_status=200,
                original_response={"pending": True},
            )
            audit = AuditEventRecord.objects.create(
                audit_id=f"audit-{uuid4()}",
                case=case,
                action=ACTION_CASE_TRANSITIONED,
                previous_state=previous_state,
                new_state=case.state,
                reason=command.reason or "",
                request_id=command.request_id,
                idempotency=idempotency,
            )
            response = {
                "case": {"id": case.case_id, "state": case.state, "resolution_reason": case.resolution_reason or None, "payment_outcome": _payment_outcome(case)},
                "audit_event": _audit_payload(audit),
            }
            idempotency.original_response = response
            idempotency.save(update_fields=["original_response"])
            return response
    except IntegrityError:
        return _replay_or_retry(case_id, ACTION_CASE_TRANSITIONED, command.request_id, fingerprint)


def create_case_note(case_id: str, command: NoteCommand) -> dict:
    fingerprint = _fingerprint({"text": command.text})
    try:
        with transaction.atomic():
            case = CaseRecord.objects.select_for_update().filter(case_id=case_id).first()
            if case is None:
                raise CaseNotFoundError(case_id)
            replay = _existing_result(case_id, ACTION_NOTE_CREATED, command.request_id, fingerprint)
            if replay is not None:
                return replay

            note = CaseNoteRecord.objects.create(note_id=f"note-{uuid4()}", case=case, text=command.text)
            idempotency = IdempotencyRecord.objects.create(
                case=case,
                action=ACTION_NOTE_CREATED,
                request_id=command.request_id,
                fingerprint=fingerprint,
                original_status=201,
                original_response={"pending": True},
            )
            audit = AuditEventRecord.objects.create(
                audit_id=f"audit-{uuid4()}",
                case=case,
                action=ACTION_NOTE_CREATED,
                note=note,
                request_id=command.request_id,
                idempotency=idempotency,
            )
            response = {
                "note": {"id": note.note_id, "case_id": case.case_id, "text": note.text, "actor": SYNTHETIC_ACTOR, "created_at": note.created_at.isoformat()},
                "audit_event": _audit_payload(audit),
            }
            idempotency.original_response = response
            idempotency.save(update_fields=["original_response"])
            return response
    except IntegrityError:
        return _replay_or_retry(case_id, ACTION_NOTE_CREATED, command.request_id, fingerprint)
