import pytest
from django.test import Client


pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> Client:
    return Client()


def make_case(suffix: str = ""):
    from europilot.models import CaseRecord, InvestigationRecord, InvoiceRecord, PaymentRecord

    invoice = InvoiceRecord.objects.create(invoice_id=f"case-invoice{suffix}", amount="10.00")
    payment = PaymentRecord.objects.create(payment_id=f"case-payment{suffix}", invoice=invoice)
    investigation = InvestigationRecord.objects.create(investigation_id=f"case-investigation{suffix}", payment=payment)
    return CaseRecord.objects.create(case_id=f"case-{investigation.investigation_id}", investigation=investigation)


def test_health(client: Client) -> None:
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "europilot", "data_mode": "sqlite_synthetic"}


def test_investigation_list_has_bounded_pagination(client: Client) -> None:
    response = client.get("/api/v1/investigations/?page=1&page_size=1")
    body = response.json()
    assert response.status_code == 200
    assert body["count"] == 1
    assert body["page_size"] == 1
    assert len(body["results"]) == 1
    assert client.get("/api/v1/investigations/?page_size=101").status_code == 400


def test_investigation_detail_contains_unknown_finding_and_provenance(client: Client) -> None:
    response = client.get("/api/v1/investigations/investigation-1/")
    body = response.json()
    assert response.status_code == 200
    assert body["outcome"] == "unknown"
    assert body["finding"]["outcome"] == "unknown"
    assert body["finding"]["missing_evidence"] == ["authoritative success or failure evidence is missing"]
    assert body["finding"]["rule_version"] == "phase1-v1"
    assert body["attempts"][1]["retry_of"] == "attempt-1"
    assert body["evidence"][0]["authoritative"] is False
    assert "event_time" in body["evidence"][0]
    assert "received_time" in body["evidence"][0]
    assert body["events"][0]["received_time"] == "2026-01-04T00:00:00+00:00"
    assert [item["received_time"] for item in body["deliveries"]] == ["2026-01-04T00:00:00+00:00", "2026-01-05T00:00:00+00:00"]
    assert body["supporting_evidence"] == []


def test_unknown_provider_event_receipt_time_serializes_as_null_without_changing_event_time(client: Client) -> None:
    from europilot.models import ProviderEventRecord

    ProviderEventRecord.objects.filter(provider="synthetic", event_id="event-1").update(received_at=None)

    body = client.get("/api/v1/investigations/investigation-1/").json()

    assert body["events"][0]["event_time"] == "2026-01-03T00:00:00+00:00"
    assert body["events"][0]["received_time"] is None


def test_unknown_identifier_is_not_fabricated(client: Client) -> None:
    assert client.get("/api/v1/investigations/missing/").status_code == 404


def test_fixture_seed_is_reproducible_without_request_duplicates(client: Client) -> None:
    first = client.get("/api/v1/investigations/").json()
    second = client.get("/api/v1/investigations/").json()
    assert first == second
    assert len(second["results"][0]["deliveries"]) == 2


def test_sqlite_seed_is_idempotent_and_persists_across_reinitialization(client: Client) -> None:
    from django.core.management import call_command
    from europilot.models import InvestigationRecord

    call_command("seed_demo", verbosity=0)
    first = client.get("/api/v1/investigations/").json()
    call_command("seed_demo", verbosity=0)
    second = client.get("/api/v1/investigations/").json()
    assert first == second
    assert InvestigationRecord.objects.count() == 1
    assert len(second["results"][0]["deliveries"]) == 2


def test_invalid_pagination_is_safe(client: Client) -> None:
    response = client.get("/api/v1/investigations/?page=not-a-number")
    assert response.status_code == 400


def test_case_list_is_empty_without_cases_and_is_read_only(client: Client) -> None:
    from europilot.models import AuditEventRecord, CaseNoteRecord, CaseRecord

    before = (CaseRecord.objects.count(), CaseNoteRecord.objects.count(), AuditEventRecord.objects.count())
    response = client.get("/api/v1/cases/")
    after = (CaseRecord.objects.count(), CaseNoteRecord.objects.count(), AuditEventRecord.objects.count())

    assert response.status_code == 200
    assert response.json() == {"count": 0, "page": 1, "page_size": 20, "results": []}
    assert after == before


def test_case_list_is_bounded_and_deterministically_ordered(client: Client) -> None:
    make_case("-z")
    make_case("-a")

    response = client.get("/api/v1/cases/?page=1&page_size=1")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert body["page_size"] == 1
    assert [item["id"] for item in body["results"]] == ["case-case-investigation-a"]
    assert client.get("/api/v1/cases/?page_size=101").status_code == 400


def test_case_detail_contains_context_notes_and_scoped_audit_history(client: Client) -> None:
    from europilot.models import ACTION_NOTE_CREATED, AuditEventRecord, CaseNoteRecord, IdempotencyRecord

    case = make_case("-detail")
    note = CaseNoteRecord.objects.create(note_id="case-note-detail", case=case, text="Untrusted <text>")
    idempotency = IdempotencyRecord.objects.create(
        case=case,
        action=ACTION_NOTE_CREATED,
        request_id="request-note-detail",
        fingerprint="a" * 64,
        original_status=201,
        original_response={"id": note.note_id},
    )
    AuditEventRecord.objects.create(
        audit_id="audit-note-detail",
        case=case,
        action=ACTION_NOTE_CREATED,
        note=note,
        request_id=idempotency.request_id,
        idempotency=idempotency,
    )

    response = client.get(f"/api/v1/cases/{case.case_id}/")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == case.case_id
    assert body["investigation_id"] == case.investigation.investigation_id
    assert body["payment_id"] == case.investigation.payment.payment_id
    assert body["state"] == "open"
    assert body["payment_outcome"] == "unknown"
    assert body["resolution_reason"] is None
    assert body["notes"] == [{"id": note.note_id, "text": "Untrusted <text>", "actor": "synthetic_local_operator", "created_at": note.created_at.isoformat()}]
    assert body["audit_events"] == [{
        "id": "audit-note-detail",
        "action": ACTION_NOTE_CREATED,
        "actor": "synthetic_local_operator",
        "created_at": body["audit_events"][0]["created_at"],
        "previous_state": None,
        "new_state": None,
        "reason": None,
        "note_id": note.note_id,
        "request_id": idempotency.request_id,
    }]


def test_case_detail_missing_case_is_not_found(client: Client) -> None:
    response = client.get("/api/v1/cases/missing-case/")

    assert response.status_code == 404
    assert response.json() == {"detail": "case not found"}


def test_case_gets_do_not_create_or_mutate_case_related_records(client: Client) -> None:
    from europilot.models import AuditEventRecord, CaseNoteRecord, CaseRecord

    case = make_case("-readonly")
    before = (CaseRecord.objects.count(), CaseNoteRecord.objects.count(), AuditEventRecord.objects.count())
    assert client.get("/api/v1/cases/").status_code == 200
    assert client.get(f"/api/v1/cases/{case.case_id}/").status_code == 200
    after = (CaseRecord.objects.count(), CaseNoteRecord.objects.count(), AuditEventRecord.objects.count())

    assert after == before


def test_case_transition_endpoint_commits_and_replays_exact_response(client: Client) -> None:
    from europilot.models import AuditEventRecord, CaseRecord, IdempotencyRecord

    case = make_case("-transition")
    payload = {"request_id": " request-transition ", "target_state": "deferred", "reason": " waiting "}
    first = client.post(f"/api/v1/cases/{case.case_id}/transitions/", payload, content_type="application/json")
    replay = client.post(f"/api/v1/cases/{case.case_id}/transitions/", payload, content_type="application/json")

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert CaseRecord.objects.get(pk=case.pk).state == "deferred"
    assert IdempotencyRecord.objects.filter(case=case).count() == 1
    assert AuditEventRecord.objects.filter(case=case).count() == 1


def test_case_note_endpoint_commits_and_rejects_different_reuse_payload(client: Client) -> None:
    from europilot.models import AuditEventRecord, CaseNoteRecord, IdempotencyRecord

    case = make_case("-note")
    first = client.post(f"/api/v1/cases/{case.case_id}/notes/", {"request_id": "request-note", "text": " analyst note "}, content_type="application/json")
    replay = client.post(f"/api/v1/cases/{case.case_id}/notes/", {"request_id": " request-note ", "text": "analyst note"}, content_type="application/json")
    conflict = client.post(f"/api/v1/cases/{case.case_id}/notes/", {"request_id": "request-note", "text": "different"}, content_type="application/json")

    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json() == first.json()
    assert first.json()["note"]["created_at"]
    assert first.json()["audit_event"]["created_at"]
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "idempotency_key_reused"
    assert CaseNoteRecord.objects.filter(case=case).count() == 1
    assert CaseNoteRecord.objects.get(case=case).actor == "synthetic_local_operator"
    assert IdempotencyRecord.objects.filter(case=case).count() == 1
    assert AuditEventRecord.objects.filter(case=case).count() == 1


def test_case_transition_response_contains_complete_schema_and_replays_exactly(client: Client) -> None:
    case = make_case("-transition-schema")
    first = client.post(f"/api/v1/cases/{case.case_id}/transitions/", {"request_id": "request-transition", "target_state": "under_review", "reason": None}, content_type="application/json")
    replay = client.post(f"/api/v1/cases/{case.case_id}/transitions/", {"request_id": " request-transition ", "target_state": "under_review", "reason": ""}, content_type="application/json")

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert first.json()["case"]["payment_outcome"] == "unknown"
    assert first.json()["audit_event"]["created_at"]


def test_case_mutation_validation_errors_are_safe_and_leave_no_records(client: Client) -> None:
    from europilot.models import AuditEventRecord, CaseNoteRecord, CaseRecord, IdempotencyRecord

    case = make_case("-invalid")
    malformed = client.post(f"/api/v1/cases/{case.case_id}/notes/", b"{", content_type="application/json")
    missing = client.post(f"/api/v1/cases/{case.case_id}/notes/", {"text": "note"}, content_type="application/json")
    blank = client.post(f"/api/v1/cases/{case.case_id}/notes/", {"request_id": "request", "text": "   "}, content_type="application/json")
    wrong_type = client.post(f"/api/v1/cases/{case.case_id}/notes/", {"request_id": 1, "text": "note"}, content_type="application/json")
    reason = client.post(f"/api/v1/cases/{case.case_id}/transitions/", {"request_id": "transition", "target_state": "deferred"}, content_type="application/json")

    assert malformed.status_code == 400
    assert missing.json()["error"]["code"] == "request_id_required"
    assert blank.json()["error"]["code"] == "note_required"
    assert wrong_type.json()["error"]["code"] == "invalid_request"
    assert reason.status_code == 422
    assert reason.json()["error"]["code"] == "reason_required"
    assert CaseRecord.objects.get(pk=case.pk).state == "open"
    assert CaseNoteRecord.objects.filter(case=case).count() == 0
    assert IdempotencyRecord.objects.filter(case=case).count() == 0
    assert AuditEventRecord.objects.filter(case=case).count() == 0


def test_case_mutation_limits_and_actor_field_are_enforced(client: Client) -> None:
    case = make_case("-limits")
    too_long_note = client.post(f"/api/v1/cases/{case.case_id}/notes/", {"request_id": "request", "text": "n" * 2001}, content_type="application/json")
    actor = client.post(f"/api/v1/cases/{case.case_id}/notes/", {"request_id": "request", "text": "note", "actor": "client"}, content_type="application/json")
    too_long_request = client.post(f"/api/v1/cases/{case.case_id}/notes/", {"request_id": "r" * 129, "text": "note"}, content_type="application/json")

    assert too_long_note.status_code == 422
    assert too_long_note.json()["error"]["code"] == "note_too_long"
    assert actor.status_code == 400
    assert actor.json()["error"]["code"] == "actor_not_allowed"
    assert too_long_request.status_code == 400
    assert too_long_request.json()["error"]["code"] == "request_id_too_long"


def test_case_mutation_unknown_case_and_retryable_failure(client: Client) -> None:
    from unittest.mock import patch

    from europilot.services import WorkflowConcurrencyError

    missing = client.post("/api/v1/cases/missing/notes/", {"request_id": "request", "text": "note"}, content_type="application/json")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "case_not_found"

    case = make_case("-retryable")
    with patch("europilot.api.create_case_note", side_effect=WorkflowConcurrencyError()):
        response = client.post(f"/api/v1/cases/{case.case_id}/notes/", {"request_id": "request", "text": "note"}, content_type="application/json")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "concurrency_retryable"
