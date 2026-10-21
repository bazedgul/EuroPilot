from __future__ import annotations

from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST

from .domain import Attempt, Delivery, EventType, Evidence, Investigation, Outcome, Payment, ProviderEvent, evaluate_outcome
from .models import InvestigationRecord


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
    return {"id": investigation_id, "payment": {"id": investigation.payment.payment_id, "invoice_id": investigation.payment.invoice_id}, "outcome": finding.outcome.value, "finding": {"outcome": finding.outcome.value, "missing_evidence": list(finding.missing_evidence), "rule_version": finding.rule_version, "conflict_evidence": [_evidence(item) for item in finding.conflict_evidence]}, "missing_evidence": list(finding.missing_evidence), "attempts": [{"id": a.attempt_id, "request_id": a.request_id, "requested_time": a.requested_at.isoformat(), "outcome": a.outcome.value, "retry_of": a.retry_of} for a in investigation.attempts], "events": [{"provider": e.provider, "id": e.event_id, "event_type": e.event_type.value, "event_time": e.occurred_at.isoformat(), "received_time": e.received_at.isoformat()} for e in investigation.events], "deliveries": [{"id": d.delivery_id, "provider": d.provider, "event_id": d.event_id, "received_time": d.received_at.isoformat()} for d in investigation.deliveries], "evidence": [_evidence(item) for item in investigation.evidence], "supporting_evidence": [_evidence(item) for item in finding.evidence]}


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
