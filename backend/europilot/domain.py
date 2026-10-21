"""Deterministic, provider-neutral payment investigation domain primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Iterable


class Outcome(StrEnum):
    CONFIRMED_SUCCESS = "confirmed_success"
    CONFIRMED_FAILURE = "confirmed_failure"
    UNKNOWN = "unknown"
    CONFLICT = "conflict"


class EventType(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    amount: Decimal

    def __post_init__(self) -> None:
        if not self.invoice_id:
            raise ValueError("invoice_id is required")
        if self.amount < 0:
            raise ValueError("amount cannot be negative")


@dataclass(frozen=True)
class Payment:
    payment_id: str
    invoice_id: str

    def __post_init__(self) -> None:
        if not self.payment_id or not self.invoice_id:
            raise ValueError("payment_id and invoice_id are required")


@dataclass(frozen=True)
class Attempt:
    attempt_id: str
    payment_id: str
    request_id: str
    requested_at: datetime
    outcome: Outcome = Outcome.UNKNOWN
    retry_of: str | None = None

    def __post_init__(self) -> None:
        if not self.attempt_id or not self.payment_id or not self.request_id:
            raise ValueError("attempt, payment, and request identifiers are required")


@dataclass(frozen=True)
class ProviderEvent:
    provider: str
    event_id: str
    payment_id: str
    event_type: EventType
    occurred_at: datetime
    received_at: datetime
    payload: str = ""

    def __post_init__(self) -> None:
        if not self.provider or not self.event_id or not self.payment_id:
            raise ValueError("provider, event, and payment identifiers are required")


@dataclass(frozen=True)
class Delivery:
    delivery_id: str
    provider: str
    event_id: str
    received_at: datetime

    def __post_init__(self) -> None:
        if not self.delivery_id or not self.provider or not self.event_id:
            raise ValueError("delivery, provider, and event identifiers are required")


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    payment_id: str
    source: str
    reference: str
    observed_at: datetime
    received_at: datetime
    event_type: EventType
    provider: str | None = None
    authoritative: bool = False

    def __post_init__(self) -> None:
        if not self.evidence_id or not self.payment_id or not self.source or not self.reference:
            raise ValueError("evidence, payment, source, and reference identifiers are required")
        if self.authoritative and not self.provider:
            raise ValueError("authoritative evidence requires a provider")


@dataclass(frozen=True)
class Finding:
    payment_id: str
    outcome: Outcome
    evidence: tuple[Evidence, ...]
    missing_evidence: tuple[str, ...] = ()
    rule_version: str = "phase1-v1"
    conflict_evidence: tuple[Evidence, ...] = ()


@dataclass
class Investigation:
    payment: Payment
    attempts: list[Attempt] = field(default_factory=list)
    events: list[ProviderEvent] = field(default_factory=list)
    deliveries: list[Delivery] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)

    def add_attempt(self, attempt: Attempt) -> None:
        if attempt.payment_id != self.payment.payment_id:
            raise ValueError("attempt belongs to another payment")
        if any(existing.attempt_id == attempt.attempt_id for existing in self.attempts):
            raise ValueError("duplicate attempt_id")
        if any(existing.request_id == attempt.request_id for existing in self.attempts):
            raise ValueError("duplicate request_id")
        if attempt.retry_of and not any(a.attempt_id == attempt.retry_of for a in self.attempts):
            raise ValueError("retry_of must reference an existing attempt")
        self.attempts.append(attempt)

    def add_event(self, event: ProviderEvent) -> None:
        if event.payment_id != self.payment.payment_id:
            raise ValueError("event belongs to another payment")
        if any(e.provider == event.provider and e.event_id == event.event_id for e in self.events):
            raise ValueError("duplicate provider event")
        self.events.append(event)

    def add_delivery(self, delivery: Delivery) -> None:
        if not any(e.provider == delivery.provider and e.event_id == delivery.event_id for e in self.events):
            raise ValueError("delivery references an unknown provider event")
        if any(d.delivery_id == delivery.delivery_id for d in self.deliveries):
            raise ValueError("duplicate delivery")
        self.deliveries.append(delivery)

    def add_evidence(self, evidence: Evidence) -> None:
        if evidence.payment_id != self.payment.payment_id:
            raise ValueError("evidence belongs to another payment")
        if any(item.evidence_id == evidence.evidence_id for item in self.evidence):
            raise ValueError("duplicate evidence_id")
        self.evidence.append(evidence)


def evaluate_outcome(
    payment_id: str,
    evidence: Iterable[Evidence],
) -> Finding:
    """Evaluate provider-scoped evidence without inferring authority from absence."""

    relevant = tuple(
        sorted(
            (e for e in evidence if e.payment_id == payment_id and e.authoritative),
            key=lambda e: (e.observed_at, e.received_at, e.evidence_id),
        )
    )
    types = {e.event_type for e in relevant}
    if EventType.SUCCESS in types and EventType.FAILURE in types:
        return Finding(payment_id, Outcome.CONFLICT, relevant, ("authoritative evidence contains incompatible success and failure outcomes",), conflict_evidence=relevant)
    if types == {EventType.SUCCESS}:
        return Finding(payment_id, Outcome.CONFIRMED_SUCCESS, relevant)
    if types == {EventType.FAILURE}:
        return Finding(payment_id, Outcome.CONFIRMED_FAILURE, relevant)
    return Finding(payment_id, Outcome.UNKNOWN, relevant, ("authoritative success or failure evidence is missing",))
