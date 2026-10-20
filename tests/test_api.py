import pytest
from django.test import Client


pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> Client:
    return Client()


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
    assert body["finding"] == {"outcome": "unknown", "missing_evidence": ["authoritative success or failure evidence is missing"]}
    assert body["attempts"][1]["retry_of"] == "attempt-1"
    assert body["evidence"][0]["authoritative"] is False
    assert "event_time" in body["evidence"][0]
    assert "received_time" in body["evidence"][0]
    assert body["supporting_evidence"] == []


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
