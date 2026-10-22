from __future__ import annotations

from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError, UnsupportedMediaType
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_503_SERVICE_UNAVAILABLE

from .domain import Attempt, Delivery, DomainValidationError, EventType, Evidence, Investigation, Outcome, Payment, ProviderEvent, evaluate_outcome, validate_note, validate_transition_input
from .models import CaseRecord, InvestigationRecord
from .services import CaseNotFoundError, IdempotencyConflictError, WorkflowConcurrencyError, create_case_note, transition_case


def _to_domain(record: InvestigationRecord) -> Investigation:
    payment = Payment(record.payment.payment_id, record.payment.invoice.invoice_id)
    investigation = Investigation(payment)
    for item in record.payment.attempts.order_by("attempt_id"):
        investigation.add_attempt(Attempt(item.attempt_id, payment.payment_id, item.request_id, item.requested_at, Outcome(item.outcome), item.retry_of.attempt_id if item.retry_of_id else None))
    for item in record.payment.provider_events.order_by("provider", "event_id"):
        investigation.add_event(ProviderEvent(item.provider, item.event_id, payment.payment_id, EventType(item.event_type), item.occurred_at, item.received_at, item.payload))
    for item in record.payment.provider_events.prefetch_related("deliveries").order_by("provider", "event_id"):
        for delivery in item.deliveries.order_by("delivery_id"):
            investigation.add_delivery(Delivery(delivery.delivery_id, item.provider, item.event_id, delivery.received_at))
    for item in record.payment.evidence.order_by("evidence_id"):
        investigation.add_evidence(Evidence(item.evidence_id, payment.payment_id, item.source, item.reference, item.observed_at, item.received_at, EventType(item.event_type), item.provider, item.authoritative))
    return investigation


def _evidence(item: Evidence) -> dict:
    return {"id": item.evidence_id, "payment_id": item.payment_id, "source": item.source, "reference": item.reference, "event_time": item.observed_at.isoformat(), "received_time": item.received_at.isoformat(), "event_type": item.event_type.value, "provider": item.provider, "authoritative": item.authoritative}


def _serialize(investigation: Investigation, investigation_id: str) -> dict:
    finding = evaluate_outcome(investigation.payment.payment_id, investigation.evidence)
    return {"id": investigation_id, "payment": {"id": investigation.payment.payment_id, "invoice_id": investigation.payment.invoice_id}, "outcome": finding.outcome.value, "finding": {"outcome": finding.outcome.value, "missing_evidence": list(finding.missing_evidence), "rule_version": finding.rule_version, "conflict_evidence": [_evidence(item) for item in finding.conflict_evidence]}, "missing_evidence": list(finding.missing_evidence), "attempts": [{"id": a.attempt_id, "request_id": a.request_id, "requested_time": a.requested_at.isoformat(), "outcome": a.outcome.value, "retry_of": a.retry_of} for a in investigation.attempts], "events": [{"provider": e.provider, "id": e.event_id, "event_type": e.event_type.value, "event_time": e.occurred_at.isoformat(), "received_time": e.received_at.isoformat() if e.received_at else None} for e in investigation.events], "deliveries": [{"id": d.delivery_id, "provider": d.provider, "event_id": d.event_id, "received_time": d.received_at.isoformat()} for d in investigation.deliveries], "evidence": [_evidence(item) for item in investigation.evidence], "supporting_evidence": [_evidence(item) for item in finding.evidence]}


def _case_context(case: CaseRecord) -> tuple[Investigation, str, str]:
    investigation = case.investigation
    return _to_domain(investigation), investigation.investigation_id, investigation.payment.payment_id


def _serialize_case_summary(case: CaseRecord) -> dict:
    investigation, investigation_id, payment_id = _case_context(case)
    finding = evaluate_outcome(payment_id, investigation.evidence)
    return {
        "id": case.case_id,
        "investigation_id": investigation_id,
        "payment_id": payment_id,
        "state": case.state,
        "payment_outcome": finding.outcome.value,
        "updated_at": case.updated_at.isoformat(),
    }


def _serialize_case_detail(case: CaseRecord) -> dict:
    summary = _serialize_case_summary(case)
    summary.update(
        {
            "resolution_reason": case.resolution_reason or None,
            "notes": [
                {
                    "id": note.note_id,
                    "text": note.text,
                    "actor": note.actor,
                    "created_at": note.created_at.isoformat(),
                }
                for note in case.notes.order_by("created_at", "note_id")
            ],
            "audit_events": [
                {
                    "id": event.audit_id,
                    "action": event.action,
                    "actor": event.actor,
                    "created_at": event.created_at.isoformat(),
                    "previous_state": event.previous_state or None,
                    "new_state": event.new_state or None,
                    "reason": event.reason or None,
                    "note_id": event.note_id,
                    "request_id": event.request_id,
                }
                for event in case.audit_events.order_by("created_at", "audit_id")
            ],
        }
    )
    return summary


@api_view(["GET"])
def health(request: Request) -> JsonResponse:
    return JsonResponse({"status": "ok", "service": "europilot", "data_mode": "sqlite_synthetic"}, status=HTTP_200_OK)


@api_view(["GET"])
def investigation_list(request: Request) -> Response:
    try:
        page = int(request.query_params.get("page", "1"))
        page_size = int(request.query_params.get("page_size", "20"))
    except ValueError:
        return Response({"detail": "page and page_size must be integers"}, status=HTTP_400_BAD_REQUEST)
    if page < 1 or page_size < 1 or page_size > 100:
        return Response({"detail": "page must be positive and page_size must be between 1 and 100"}, status=HTTP_400_BAD_REQUEST)
    records = list(InvestigationRecord.objects.select_related("payment__invoice").order_by("investigation_id"))
    start = (page - 1) * page_size
    return Response({"count": len(records), "page": page, "page_size": page_size, "results": [_serialize(_to_domain(item), item.investigation_id) for item in records[start : start + page_size]]})


@api_view(["GET"])
def investigation_detail(request: Request, investigation_id: str) -> Response:
    record = InvestigationRecord.objects.select_related("payment__invoice").filter(investigation_id=investigation_id).first()
    if record is None:
        return Response({"detail": "investigation not found"}, status=HTTP_404_NOT_FOUND)
    return Response(_serialize(_to_domain(record), record.investigation_id))


@api_view(["GET"])
def case_list(request: Request) -> Response:
    try:
        page = int(request.query_params.get("page", "1"))
        page_size = int(request.query_params.get("page_size", "20"))
    except ValueError:
        return Response({"detail": "page and page_size must be integers"}, status=HTTP_400_BAD_REQUEST)
    if page < 1 or page_size < 1 or page_size > 100:
        return Response({"detail": "page must be positive and page_size must be between 1 and 100"}, status=HTTP_400_BAD_REQUEST)
    records = CaseRecord.objects.select_related("investigation__payment__invoice").order_by("case_id")
    count = records.count()
    start = (page - 1) * page_size
    return Response({"count": count, "page": page, "page_size": page_size, "results": [_serialize_case_summary(item) for item in records[start : start + page_size]]})


@api_view(["GET"])
def case_detail(request: Request, case_id: str) -> Response:
    case = CaseRecord.objects.select_related("investigation__payment__invoice").prefetch_related("notes", "audit_events").filter(case_id=case_id).first()
    if case is None:
        return Response({"detail": "case not found"}, status=HTTP_404_NOT_FOUND)
    return Response(_serialize_case_detail(case))


def _api_error(code: str, message: str, status: int) -> Response:
    return Response({"error": {"code": code, "message": message}}, status=status)


def _request_object(request: Request) -> dict | Response:
    try:
        payload = request.data
    except (ParseError, UnsupportedMediaType):
        return _api_error("invalid_request", "request body must be valid JSON.", HTTP_400_BAD_REQUEST)
    if not isinstance(payload, dict):
        return _api_error("invalid_request", "request body must be a JSON object.", HTTP_400_BAD_REQUEST)
    return payload


def _string_field(payload: dict, name: str, *, required: bool = True) -> str | None | Response:
    if name not in payload:
        if required:
            code = "request_id_required" if name == "request_id" else "invalid_request"
            return _api_error(code, f"{name} is required.", HTTP_400_BAD_REQUEST)
        return None
    value = payload[name]
    if value is None and not required:
        return None
    if not isinstance(value, str):
        return _api_error("invalid_request", f"{name} must be a string.", HTTP_400_BAD_REQUEST)
    return value


def _workflow_error(error: Exception) -> Response:
    if isinstance(error, CaseNotFoundError):
        return _api_error(error.code, "The requested case was not found.", HTTP_404_NOT_FOUND)
    if isinstance(error, IdempotencyConflictError):
        return _api_error(error.code, "The request ID was already used with a different payload.", HTTP_409_CONFLICT)
    if isinstance(error, WorkflowConcurrencyError):
        return _api_error(error.code, "The operation could not be safely completed; retry the request.", HTTP_503_SERVICE_UNAVAILABLE)
    if isinstance(error, DomainValidationError):
        status = HTTP_409_CONFLICT if error.code == "invalid_transition" else HTTP_422_UNPROCESSABLE_ENTITY if error.code in {"reason_required", "reason_too_long", "note_required", "note_too_long"} else HTTP_400_BAD_REQUEST
        return _api_error(error.code, error.message, status)
    return _api_error("invalid_request", "The request could not be processed.", HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def case_transition(request: Request, case_id: str) -> Response:
    payload = _request_object(request)
    if isinstance(payload, Response):
        return payload
    if "actor" in payload:
        return _api_error("actor_not_allowed", "The actor is assigned by the server.", HTTP_400_BAD_REQUEST)
    request_id = _string_field(payload, "request_id")
    target_state = _string_field(payload, "target_state")
    reason = _string_field(payload, "reason", required=False)
    if any(isinstance(value, Response) for value in (request_id, target_state, reason)):
        return next(value for value in (request_id, target_state, reason) if isinstance(value, Response))
    case = CaseRecord.objects.filter(case_id=case_id).first()
    if case is None:
        return _workflow_error(CaseNotFoundError(case_id))
    try:
        command = validate_transition_input(target_state, reason, request_id)
        return Response(transition_case(case_id, command), status=HTTP_200_OK)
    except (DomainValidationError, CaseNotFoundError, IdempotencyConflictError, WorkflowConcurrencyError) as error:
        return _workflow_error(error)


@api_view(["POST"])
def case_note_create(request: Request, case_id: str) -> Response:
    payload = _request_object(request)
    if isinstance(payload, Response):
        return payload
    if "actor" in payload:
        return _api_error("actor_not_allowed", "The actor is assigned by the server.", HTTP_400_BAD_REQUEST)
    request_id = _string_field(payload, "request_id")
    text = _string_field(payload, "text")
    if any(isinstance(value, Response) for value in (request_id, text)):
        return next(value for value in (request_id, text) if isinstance(value, Response))
    try:
        return Response(create_case_note(case_id, validate_note(text, request_id)), status=HTTP_201_CREATED)
    except (DomainValidationError, CaseNotFoundError, IdempotencyConflictError, WorkflowConcurrencyError) as error:
        return _workflow_error(error)
