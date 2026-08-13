#!/usr/bin/env python3
"""Generate the deterministic helios-v1 benchmark dataset."""

from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets" / "helios_v1"
SCRIPT_DIR = Path(__file__).resolve().parent
START = datetime(2026, 2, 1, 10, 0, tzinfo=UTC)

_dist_spec = importlib.util.spec_from_file_location(
    "helios_distractor_content",
    SCRIPT_DIR / "helios_distractor_content.py",
)
_dist_module = importlib.util.module_from_spec(_dist_spec)
assert _dist_spec.loader is not None
_dist_spec.loader.exec_module(_dist_module)
DISTRACTOR_SPECS: list[tuple[int, str, str, list[str]]] = _dist_module.DISTRACTOR_SPECS

LEARN_QUERY_TEXT = "How do finalized billing events reach downstream consumers?"

STORY_EVENT_COUNT = 110
DISTRACTOR_COUNT = 440
TOTAL_EVENTS = STORY_EVENT_COUNT + DISTRACTOR_COUNT


def iso(day: int, hour: int = 10) -> str:
    return (START + timedelta(days=day - 1, hours=hour - 10)).isoformat()


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def _distractor_specs() -> list[tuple[int, str, str, list[str]]]:
    """Return (day, event_type, content, tags) for each authored distractor."""
    if len(DISTRACTOR_SPECS) != DISTRACTOR_COUNT:
        raise RuntimeError(
            f"expected {DISTRACTOR_COUNT} distractors, found {len(DISTRACTOR_SPECS)}"
        )
    return list(DISTRACTOR_SPECS)


def build_events() -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    seq = 0

    def add(
        event_id: str,
        day: int,
        event_type: str,
        content: str,
        *,
        tags: list[str] | None = None,
        entities: list[str] | None = None,
        semantic_facts: list[dict[str, str]] | None = None,
        supersedes: list[str] | None = None,
        related_events: list[str] | None = None,
    ) -> None:
        nonlocal seq
        seq += 1
        events.append(
            {
                "id": event_id,
                "timestamp": iso(day),
                "sequence": seq,
                "subject_id": "project-helios",
                "event_type": event_type,
                "content": content,
                "entities": entities or [],
                "semantic_facts": semantic_facts or [],
                "tags": tags or [],
                "supersedes": supersedes or [],
                "related_events": related_events or [],
            }
        )

    # Story thread (helios-001 .. helios-110)
    add(
        "helios-001",
        1,
        "architecture_decision",
        "Python with FastAPI was chosen as the billing platform application stack.",
        entities=["fastapi", "python", "billing-platform"],
        semantic_facts=[
            {
                "subject": "billing-platform",
                "predicate": "application-stack",
                "object": "fastapi-python",
                "cardinality": "one",
            }
        ],
        tags=["stack"],
    )
    add(
        "helios-002",
        2,
        "architecture_decision",
        "DynamoDB was selected to store immutable finalized charge ledger records.",
        entities=["dynamodb", "charge-ledger"],
        semantic_facts=[
            {
                "subject": "charge-ledger",
                "predicate": "backing-store",
                "object": "dynamodb",
                "cardinality": "one",
            }
        ],
    )
    add(
        "helios-003",
        3,
        "implementation",
        "Charge ingestion now writes finalized amounts into the DynamoDB ledger table.",
        entities=["dynamodb", "charge-ledger"],
        related_events=["helios-002"],
    )
    add(
        "helios-004",
        4,
        "architecture_decision",
        "Auth0 was adopted for merchant portal authentication.",
        entities=["auth0", "merchant-portal"],
        semantic_facts=[
            {
                "subject": "merchant-authentication",
                "predicate": "provider",
                "object": "auth0",
                "cardinality": "one",
            }
        ],
    )
    add(
        "helios-005",
        5,
        "user_feedback",
        "Finance reported month-end reconciliation jobs were painfully slow "
        "on current ledger access.",
        entities=["finance", "charge-ledger"],
        related_events=["helios-002", "helios-003"],
    )
    add(
        "helios-006",
        6,
        "implementation",
        "Reconciliation exporter timed out repeatedly on hot partition keys during close week.",
        related_events=["helios-005"],
    )
    add(
        "helios-007",
        7,
        "rejected_approach",
        "Engineering rejected a homegrown JWT issuer because key rotation burden was too high.",
        related_events=["helios-004"],
    )
    add(
        "helios-008",
        8,
        "conversation",
        "Analytics requested SQL-friendly access patterns over finalized charge history.",
        related_events=["helios-005"],
    )
    add(
        "helios-009",
        9,
        "implementation",
        "Downstream propagation initially used a polled outbox table scanned every five seconds.",
        entities=["outbox", "polling"],
        semantic_facts=[
            {
                "subject": "downstream-propagation",
                "predicate": "mechanism",
                "object": "polled-outbox",
                "cardinality": "one",
            }
        ],
    )
    add(
        "helios-010",
        10,
        "architecture_decision",
        "CircleCI was selected to run billing platform CI/CD pipelines.",
        entities=["circleci", "ci-cd"],
        semantic_facts=[
            {
                "subject": "billing-platform-ci",
                "predicate": "provider",
                "object": "circleci",
                "cardinality": "one",
            }
        ],
    )
    add(
        "helios-011",
        11,
        "rejected_approach",
        "Kafka was rejected as the internal billing event bus due to operational overhead.",
        related_events=["helios-009"],
        entities=["kafka"],
    )
    add(
        "helios-012",
        12,
        "architecture_decision",
        "PostgreSQL replaces DynamoDB as the authoritative charge ledger backing store.",
        entities=["postgresql", "dynamodb", "charge-ledger"],
        semantic_facts=[
            {
                "subject": "charge-ledger",
                "predicate": "backing-store",
                "object": "postgresql",
                "cardinality": "one",
            }
        ],
        supersedes=["helios-002"],
        related_events=["helios-005", "helios-006", "helios-008"],
    )
    add(
        "helios-013",
        13,
        "architecture_decision",
        "Datadog was adopted for billing platform metrics, traces, and SLO dashboards.",
        entities=["datadog", "observability"],
        semantic_facts=[
            {
                "subject": "billing-observability",
                "predicate": "provider",
                "object": "datadog",
                "cardinality": "one",
            }
        ],
    )
    add(
        "helios-014",
        14,
        "documentation",
        "An outdated internal wiki page still describes DynamoDB as the charge ledger store.",
        entities=["dynamodb"],
        tags=["stale"],
    )
    add(
        "helios-015",
        15,
        "documentation",
        "Production configuration review confirmed PostgreSQL hosts the live charge ledger.",
        entities=["postgresql", "charge-ledger"],
        related_events=["helios-012"],
    )
    add(
        "helios-016",
        16,
        "documentation",
        "Architecture review minutes confirmed PostgreSQL as the current ledger backing store.",
        supersedes=["helios-014"],
        related_events=["helios-015"],
        entities=["postgresql", "charge-ledger"],
        semantic_facts=[
            {
                "subject": "charge-ledger",
                "predicate": "backing-store",
                "object": "postgresql",
                "cardinality": "one",
            }
        ],
    )
    add(
        "helios-017",
        17,
        "requirement",
        "Compliance requested audit logs be retained for 90 days.",
        tags=["audit"],
    )
    add(
        "helios-018",
        18,
        "architecture_decision",
        "WorkOS replaces Auth0 for merchant portal authentication.",
        entities=["workos", "auth0", "merchant-portal"],
        semantic_facts=[
            {
                "subject": "merchant-authentication",
                "predicate": "provider",
                "object": "workos",
                "cardinality": "one",
            }
        ],
        supersedes=["helios-004"],
        related_events=["helios-007"],
    )
    add(
        "helios-019",
        19,
        "bug",
        "Invoice PDF generation dropped line items for multi-currency statements.",
        entities=["invoice-pdf"],
        tags=["invoice"],
    )
    add(
        "helios-020",
        20,
        "architecture_decision",
        "Debezium change-data capture replaces the polled outbox for downstream propagation.",
        entities=["debezium", "outbox"],
        semantic_facts=[
            {
                "subject": "downstream-propagation",
                "predicate": "mechanism",
                "object": "debezium-cdc",
                "cardinality": "one",
            }
        ],
        supersedes=["helios-009"],
        related_events=["helios-011"],
    )
    add(
        "helios-021",
        21,
        "fix",
        "Patched invoice PDF renderer to include all line items on multi-currency statements.",
        related_events=["helios-019"],
        entities=["invoice-pdf"],
    )
    add(
        "helios-022",
        22,
        "incident",
        "A 3am reconciliation mismatch alert woke billing on-call during month-end close.",
        tags=["incident", "on-call"],
        entities=["reconciliation"],
    )
    add(
        "helios-023",
        23,
        "implementation",
        "Ledger cutover migrated historical finalized charges from DynamoDB into PostgreSQL.",
        related_events=["helios-012"],
        entities=["postgresql", "dynamodb"],
    )
    add(
        "helios-024",
        24,
        "implementation",
        "PagerDuty routing was updated so billing reconciliation alerts "
        "reach the primary rotation.",
        related_events=["helios-022"],
        entities=["pagerduty", "on-call"],
    )
    add(
        "helios-025",
        25,
        "implementation",
        "Debezium connector deployed to stream ledger changes to downstream analytics consumers.",
        related_events=["helios-020"],
        entities=["debezium"],
    )
    add(
        "helios-026",
        26,
        "implementation",
        "WorkOS SSO rollout completed for merchant portal login flows.",
        related_events=["helios-018"],
        entities=["workos"],
    )
    add(
        "helios-027",
        27,
        "implementation",
        "CircleCI pipeline now runs contract tests against staging billing APIs.",
        related_events=["helios-010"],
        entities=["circleci"],
    )
    add(
        "helios-028",
        28,
        "requirement",
        "Leadership froze opening new AWS accounts until Q3 cost review finished.",
        entities=["aws", "cost"],
        tags=["cost"],
    )
    add(
        "helios-029",
        29,
        "dependency",
        "Pinned SQLAlchemy 2.x for async PostgreSQL ledger repository access.",
        entities=["sqlalchemy", "postgresql"],
    )
    add(
        "helios-030",
        30,
        "implementation",
        "Datadog monitors added for ledger write latency and reconciliation job duration.",
        related_events=["helios-013"],
        entities=["datadog"],
    )
    add(
        "helios-031",
        31,
        "bug",
        "Sandbox payout simulation returned stale FX rates after cache TTL misconfiguration.",
        entities=["sandbox", "payout"],
    )
    add(
        "helios-032",
        32,
        "requirement_change",
        "Finance approved a temporary exception allowing one sandbox AWS "
        "account during the freeze.",
        related_events=["helios-028"],
        entities=["aws", "sandbox"],
    )
    add(
        "helios-033",
        33,
        "fix",
        "Corrected FX cache TTL for sandbox payout simulation endpoints.",
        related_events=["helios-031"],
    )
    add(
        "helios-034",
        34,
        "conversation",
        "Platform guild reviewed structured logging fields for billing API handlers.",
    )
    add(
        "helios-035",
        35,
        "implementation",
        "Added OpenTelemetry spans around charge ingestion and ledger persistence.",
        entities=["opentelemetry"],
    )
    add(
        "helios-036",
        36,
        "requirement_change",
        "The sandbox AWS account exception was reversed after the cost review completed.",
        supersedes=["helios-032"],
        related_events=["helios-028"],
        entities=["aws", "sandbox"],
    )
    add(
        "helios-037",
        37,
        "test_failure",
        "Staging contract test failed when merchant portal auth redirect URL changed.",
        related_events=["helios-026"],
    )
    add(
        "helios-038",
        38,
        "fix",
        "Updated staging auth redirect fixtures after WorkOS rollout.",
        related_events=["helios-037", "helios-026"],
    )
    add(
        "helios-039",
        39,
        "documentation",
        "Runbook expanded for Debezium connector lag and replay procedures.",
        related_events=["helios-025"],
        entities=["debezium"],
    )
    add(
        "helios-040",
        40,
        "conversation",
        "Engineering discussed active-active failover in eu-west but made no region decision.",
        tags=["multi-region"],
        entities=["multi-region"],
    )
    add(
        "helios-041",
        41,
        "implementation",
        "Read replica added for finance reconciliation SQL queries against the ledger.",
        related_events=["helios-012", "helios-023"],
        entities=["postgresql"],
    )
    add(
        "helios-042",
        42,
        "requirement_change",
        "Audit log retention increased from 90 days to 180 days.",
        supersedes=["helios-017"],
        tags=["audit"],
    )
    add(
        "helios-043",
        43,
        "release",
        "Billing platform 0.6.0 released with ledger migration and WorkOS auth.",
        related_events=["helios-023", "helios-026"],
    )
    add(
        "helios-044",
        44,
        "implementation",
        "Deprecated DynamoDB ledger table marked read-only after PostgreSQL cutover.",
        related_events=["helios-023"],
        entities=["dynamodb"],
        tags=["obsolete"],
    )
    add(
        "helios-045",
        45,
        "documentation",
        "Merchant portal docs updated to describe WorkOS login instead of Auth0.",
        related_events=["helios-018"],
        entities=["workos"],
    )
    add(
        "helios-046",
        46,
        "conversation",
        "On-call reviewed PagerDuty escalation paths after the reconciliation incident.",
        related_events=["helios-024", "helios-022"],
    )
    add(
        "helios-047",
        47,
        "implementation",
        "Removed obsolete outbox polling cron after Debezium stabilization.",
        related_events=["helios-020", "helios-025"],
        tags=["obsolete"],
        entities=["outbox", "polling"],
    )
    add(
        "helios-048",
        48,
        "user_feedback",
        "Merchant success praised clearer invoice PDF layout after the line-item fix.",
        related_events=["helios-021"],
    )
    add(
        "helios-049",
        49,
        "dependency",
        "Upgraded httpx client used for payment provider webhook verification.",
    )
    add(
        "helios-050",
        50,
        "implementation",
        "CircleCI nightly job now publishes Datadog deployment markers.",
        related_events=["helios-010", "helios-013"],
    )
    add(
        "helios-051",
        51,
        "bug",
        "Audit export job omitted entries older than 90 days before policy update propagated.",
        related_events=["helios-042"],
        tags=["audit"],
    )
    add(
        "helios-052",
        52,
        "fix",
        "Audit export window aligned to the new 180-day retention policy.",
        related_events=["helios-051", "helios-042"],
    )
    add(
        "helios-053",
        53,
        "noise",
        "Updated the team lunch rotation spreadsheet.",
        tags=["noise"],
    )
    add(
        "helios-054",
        54,
        "implementation",
        "Added dead-letter handling for Debezium sink retries on analytics topics.",
        related_events=["helios-025"],
    )
    add(
        "helios-055",
        55,
        "documentation",
        "Internal wiki banner added warning the ledger page was stale pending rewrite.",
        related_events=["helios-014"],
        tags=["stale"],
    )
    add(
        "helios-056",
        56,
        "conversation",
        "Security reviewed Auth0 to WorkOS migration cutover checklist.",
        related_events=["helios-018"],
    )
    add(
        "helios-057",
        57,
        "test_failure",
        "Load test showed reconciliation SQL saturated the read replica connection pool.",
        related_events=["helios-041"],
    )
    add(
        "helios-058",
        58,
        "fix",
        "Tuned read replica pool limits after reconciliation load test failures.",
        related_events=["helios-057"],
    )
    add(
        "helios-059",
        59,
        "implementation",
        "Sandbox environments blocked from provisioning net-new AWS accounts per policy.",
        related_events=["helios-028", "helios-036"],
    )
    add(
        "helios-060",
        60,
        "release",
        "Billing platform 0.7.0 released with audit retention and Debezium hardening.",
        related_events=["helios-042", "helios-054"],
    )
    add(
        "helios-061",
        61,
        "documentation",
        "On-call runbook documents the 3am reconciliation mismatch response steps.",
        related_events=["helios-022", "helios-024"],
    )
    add(
        "helios-062",
        62,
        "conversation",
        "Finance asked whether eu-west would become the active billing region; no answer recorded.",
        related_events=["helios-040"],
        tags=["multi-region"],
    )
    add(
        "helios-063",
        63,
        "implementation",
        "Invoice PDF service now emits structured logs to Datadog for rendering failures.",
        related_events=["helios-021", "helios-013"],
    )
    add(
        "helios-064",
        64,
        "dependency",
        "Pinned Debezium connector version after staging replay test passed.",
        entities=["debezium"],
    )
    add(
        "helios-065",
        65,
        "bug",
        "Merchant portal displayed expired Auth0 session hints after WorkOS cutover.",
        related_events=["helios-026"],
        entities=["auth0", "workos"],
    )
    add(
        "helios-066",
        66,
        "fix",
        "Removed stale Auth0 session banners from merchant portal templates.",
        related_events=["helios-065"],
    )
    add(
        "helios-067",
        67,
        "implementation",
        "Added feature flag to disable legacy outbox polling code paths.",
        related_events=["helios-047"],
        tags=["obsolete"],
    )
    add(
        "helios-068",
        68,
        "documentation",
        "Developer portal examples now show FastAPI handlers for charge creation.",
        related_events=["helios-001"],
    )
    add(
        "helios-069",
        69,
        "conversation",
        "Discussed whether Kafka could revisit later; team kept Debezium approach.",
        related_events=["helios-011", "helios-020"],
    )
    add(
        "helios-070",
        70,
        "implementation",
        "PostgreSQL ledger table partitioned by billing period for reconciliation scans.",
        related_events=["helios-012"],
    )
    add(
        "helios-071",
        71,
        "test_failure",
        "PDF snapshot test failed after font embedding change in invoice service.",
        related_events=["helios-021"],
    )
    add(
        "helios-072",
        72,
        "fix",
        "Updated invoice PDF snapshot fixtures after font embedding change.",
        related_events=["helios-071"],
    )
    add(
        "helios-073",
        73,
        "user_feedback",
        "Enterprise merchant requested longer audit export windows for quarterly reviews.",
        related_events=["helios-042"],
    )
    add(
        "helios-074",
        74,
        "implementation",
        "CircleCI added migration lint step for PostgreSQL ledger schema changes.",
        related_events=["helios-010", "helios-070"],
    )
    add(
        "helios-075",
        75,
        "documentation",
        "Cost review memo documented why the sandbox AWS exception was reversed.",
        related_events=["helios-036"],
    )
    add(
        "helios-076",
        76,
        "conversation",
        "Platform team debated dual-write ledger strategy during migration; chose cutover instead.",
        related_events=["helios-023"],
    )
    add(
        "helios-077",
        77,
        "implementation",
        "Datadog SLO dashboard tracks month-end reconciliation job success rate.",
        related_events=["helios-030", "helios-022"],
    )
    add(
        "helios-078",
        78,
        "bug",
        "Debezium lag monitor false-positive during connector maintenance window.",
        related_events=["helios-025"],
    )
    add(
        "helios-079",
        79,
        "fix",
        "Suppressed Debezium lag alerts during scheduled connector maintenance.",
        related_events=["helios-078"],
    )
    add(
        "helios-080",
        80,
        "release",
        "Billing platform 0.8.0 released with invoice PDF and portal polish.",
        related_events=["helios-072", "helios-066"],
    )
    add(
        "helios-081",
        81,
        "documentation",
        "Architecture decision record filed for PostgreSQL ledger migration rationale.",
        related_events=["helios-012", "helios-005"],
    )
    add(
        "helios-082",
        82,
        "implementation",
        "Added reconciliation diff tool comparing provider totals to ledger aggregates.",
        related_events=["helios-022"],
    )
    add(
        "helios-083",
        83,
        "conversation",
        "Leadership asked for SOC2 timeline estimates without selecting a vendor yet.",
        tags=["compliance"],
    )
    add(
        "helios-084",
        84,
        "dependency",
        "Upgraded WorkOS SDK after organization mapping API change.",
        entities=["workos"],
    )
    add(
        "helios-085",
        85,
        "implementation",
        "Merchant portal enforces WorkOS organization mapping on login.",
        related_events=["helios-026", "helios-084"],
    )
    add(
        "helios-086",
        86,
        "test_failure",
        "Contract test caught missing charge idempotency header on refund endpoint.",
    )
    add(
        "helios-087",
        87,
        "fix",
        "Refund endpoint now requires idempotency headers in public API contract.",
        related_events=["helios-086"],
    )
    add(
        "helios-088",
        88,
        "noise",
        "Caterer menu options circulated for spring engineering offsite.",
        tags=["noise"],
    )
    add(
        "helios-089",
        89,
        "implementation",
        "Ledger read API exposes PostgreSQL-backed finalized charge queries to finance.",
        related_events=["helios-015", "helios-041"],
    )
    add(
        "helios-090",
        90,
        "documentation",
        "Stale DynamoDB ledger references removed from internal onboarding checklist.",
        supersedes=["helios-055"],
        related_events=["helios-016"],
    )
    add(
        "helios-091",
        91,
        "conversation",
        "Multi-region working group reconvened but adjourned without picking an active region.",
        related_events=["helios-040", "helios-062"],
        tags=["multi-region"],
    )
    add(
        "helios-092",
        92,
        "implementation",
        "PagerDuty service linked to Datadog SLO burn alerts for billing.",
        related_events=["helios-024", "helios-077"],
    )
    add(
        "helios-093",
        93,
        "user_feedback",
        "Finance praised faster reconciliation after PostgreSQL read replica rollout.",
        related_events=["helios-041", "helios-005"],
    )
    add(
        "helios-094",
        94,
        "bug",
        "CircleCI artifact upload failed when cache key exceeded length limit.",
        related_events=["helios-027"],
    )
    add(
        "helios-095",
        95,
        "fix",
        "Shortened CircleCI cache keys for billing platform artifact uploads.",
        related_events=["helios-094"],
    )
    add(
        "helios-096",
        96,
        "implementation",
        "Debezium schema registry entries versioned for ledger change events.",
        related_events=["helios-025"],
    )
    add(
        "helios-097",
        97,
        "documentation",
        "Public API changelog notes WorkOS authentication for merchant integrations.",
        related_events=["helios-045"],
    )
    add(
        "helios-098",
        98,
        "conversation",
        "Security asked whether Vanta or Drata would be evaluated for SOC2; no vendor chosen.",
        related_events=["helios-083"],
        tags=["compliance"],
    )
    add(
        "helios-099",
        99,
        "release",
        "Billing platform 0.9.0 released with reconciliation tooling and API hardening.",
        related_events=["helios-082", "helios-087"],
    )
    add(
        "helios-100",
        100,
        "implementation",
        "Legacy polled outbox table archived after Debezium lag stayed under threshold.",
        related_events=["helios-047", "helios-067"],
        tags=["obsolete"],
    )
    add(
        "helios-101",
        101,
        "documentation",
        "Finance playbook documents month-end reconciliation using PostgreSQL ledger exports.",
        related_events=["helios-089", "helios-061"],
    )
    add(
        "helios-102",
        102,
        "test_failure",
        "Staging load test revealed slow invoice PDF renders for large statements.",
        related_events=["helios-063"],
    )
    add(
        "helios-103",
        103,
        "fix",
        "Optimized invoice PDF rendering path for large multi-page statements.",
        related_events=["helios-102"],
    )
    add(
        "helios-104",
        104,
        "conversation",
        "Leadership reiterated AWS account freeze except approved production expansions.",
        related_events=["helios-028", "helios-059"],
    )
    add(
        "helios-105",
        105,
        "implementation",
        "Audit log exporter validates 180-day window against compliance policy.",
        related_events=["helios-052"],
    )
    add(
        "helios-106",
        106,
        "documentation",
        "Runbook cross-links PagerDuty and Datadog dashboards for billing on-call.",
        related_events=["helios-092"],
    )
    add(
        "helios-107",
        107,
        "dependency",
        "Pinned FastAPI after async dependency injection regression in patch release.",
        related_events=["helios-001"],
    )
    add(
        "helios-108",
        175,
        "architecture_decision",
        "Vanta was selected as the SOC2 compliance vendor for Project Helios.",
        entities=["vanta", "soc2"],
        semantic_facts=[
            {
                "subject": "soc2-compliance",
                "predicate": "vendor",
                "object": "vanta",
                "cardinality": "one",
            }
        ],
        tags=["leak", "compliance"],
        related_events=["helios-098"],
    )
    add(
        "helios-109",
        177,
        "implementation",
        "Vanta integration scaffold added for evidence collection workflows.",
        related_events=["helios-108"],
        entities=["vanta"],
        tags=["compliance"],
    )
    add(
        "helios-110",
        179,
        "release",
        "Billing platform 1.0.0 released ahead of SOC2 readiness milestone.",
        related_events=["helios-108", "helios-099"],
    )

    event_num = STORY_EVENT_COUNT + 1
    for day, event_type, content, tags in _distractor_specs():
        add(f"helios-{event_num:03d}", day, event_type, content, tags=tags)
        event_num += 1

    if len(events) != TOTAL_EVENTS:
        raise RuntimeError(f"expected {TOTAL_EVENTS} events, built {len(events)}")
    return events


def _query_timestamp(
    event_map: dict[str, dict[str, object]], evidence_ids: list[str], *, day_offset: int = 1
) -> str:
    latest = max(parse_iso(str(event_map[event_id]["timestamp"])) for event_id in evidence_ids)
    return (latest + timedelta(days=day_offset)).isoformat()


def build_queries(events: list[dict[str, object]]) -> list[dict[str, object]]:
    event_map = {str(event["id"]): event for event in events}
    queries: list[dict[str, object]] = []

    def add_query(*, core: bool = False, **kwargs: object) -> None:
        evidence = [str(item) for item in kwargs.pop("expected_evidence_ids", [])]  # type: ignore[arg-type]
        acceptable = [str(item) for item in kwargs.pop("acceptable_evidence_ids", [])]  # type: ignore[arg-type]
        forbidden = [str(item) for item in kwargs.pop("forbidden_evidence_ids", [])]  # type: ignore[arg-type]
        tags = list(kwargs.pop("tags", []))  # type: ignore[arg-type]
        if core:
            tags.append("core")
        if "timestamp" not in kwargs:
            reference_ids = evidence or acceptable or forbidden
            if reference_ids:
                kwargs["timestamp"] = _query_timestamp(event_map, reference_ids)
            else:
                kwargs["timestamp"] = iso(20)
        queries.append(
            {
                "expected_evidence_ids": evidence,
                "acceptable_evidence_ids": acceptable,
                "forbidden_evidence_ids": forbidden,
                "should_abstain": False,
                "retrieval_limit": 5,
                "tags": tags,
                **kwargs,
            }
        )

    # Core story queries
    add_query(
        id="helios-direct-001",
        capability="direct_recall",
        query="Which application stack was chosen for the billing platform?",
        expected_evidence_ids=["helios-001"],
        timestamp=iso(3),
        core=True,
    )
    add_query(
        id="helios-episodic-001",
        capability="episodic_recall",
        query="What overnight incident disrupted billing on-call during month-end close?",
        expected_evidence_ids=["helios-022"],
        timestamp=iso(24),
        core=True,
    )
    add_query(
        id="helios-assoc-001",
        capability="associative_recall",
        query="What operational pain from finance drove the charge ledger architecture change?",
        expected_evidence_ids=["helios-005"],
        acceptable_evidence_ids=["helios-006"],
        entity_ids=["finance", "charge-ledger"],
        timestamp=iso(13),
        core=True,
    )
    add_query(
        id="helios-update-001",
        capability="knowledge_update",
        query="Where do finalized charges persist in production now?",
        expected_evidence_ids=["helios-012"],
        acceptable_evidence_ids=["helios-015", "helios-016"],
        forbidden_evidence_ids=["helios-002"],
        entity_ids=["charge-ledger"],
        timestamp=iso(17),
        core=True,
    )
    add_query(
        id="helios-temporal-hist-001",
        capability="temporal_recall",
        query="What backing store held the charge ledger during the first week of the project?",
        expected_evidence_ids=["helios-002"],
        forbidden_evidence_ids=["helios-012"],
        valid_at=iso(7),
        timestamp=iso(10),
        core=True,
    )
    add_query(
        id="helios-temporal-curr-001",
        capability="temporal_recall",
        query="Which database backs the live charge ledger according to current documentation?",
        expected_evidence_ids=["helios-016"],
        acceptable_evidence_ids=["helios-015"],
        forbidden_evidence_ids=["helios-014"],
        entity_ids=["charge-ledger"],
        predicate="backing-store",
        timestamp=iso(20),
        core=True,
    )
    add_query(
        id="helios-leak-001",
        capability="direct_recall",
        query="Which vendor was selected to manage SOC2 compliance for Project Helios?",
        expected_evidence_ids=[],
        forbidden_evidence_ids=["helios-108"],
        should_abstain=True,
        timestamp=iso(160),
        core=True,
    )
    add_query(
        id="helios-meta-001",
        capability="metamemory",
        query="Which AWS region is the active primary for billing production traffic?",
        should_abstain=True,
        timestamp=iso(45),
        core=True,
    )
    add_query(
        id="helios-forget-001",
        capability="forgetting",
        query="What mechanism propagates ledger changes to downstream consumers today?",
        expected_evidence_ids=["helios-020"],
        acceptable_evidence_ids=["helios-025"],
        forbidden_evidence_ids=["helios-009", "helios-011"],
        entity_ids=["downstream-propagation"],
        timestamp=iso(55),
        core=True,
    )
    add_query(
        id="helios-learn-pre-001",
        capability="learning",
        query=LEARN_QUERY_TEXT,
        expected_evidence_ids=["helios-020"],
        acceptable_evidence_ids=["helios-009"],
        entity_ids=["downstream-propagation"],
        timestamp=iso(22),
        core=True,
    )
    add_query(
        id="helios-learn-post-001",
        capability="learning",
        query=LEARN_QUERY_TEXT,
        expected_evidence_ids=["helios-020"],
        forbidden_evidence_ids=["helios-009"],
        related_query_id="helios-learn-pre-001",
        entity_ids=["downstream-propagation"],
        timestamp=iso(28),
        core=True,
    )
    add_query(
        id="helios-wm-001",
        capability="working_memory",
        query="Summarize the charge ledger storage situation.",
        expected_evidence_ids=["helios-016"],
        acceptable_evidence_ids=["helios-015"],
        forbidden_evidence_ids=["helios-014"],
        entity_ids=["charge-ledger"],
        goal="Prefer the live ledger store; ignore stale wiki pages.",
        retrieval_limit=3,
        prompt_budget_tokens=120,
        timestamp=iso(21),
        core=True,
    )

    # Additional authored coverage queries
    add_query(
        id="helios-direct-002",
        capability="direct_recall",
        query="Which CI/CD platform runs billing platform pipelines?",
        expected_evidence_ids=["helios-010"],
        timestamp=iso(12),
    )
    add_query(
        id="helios-direct-003",
        capability="direct_recall",
        query="Which observability vendor monitors billing SLOs?",
        expected_evidence_ids=["helios-013"],
        timestamp=iso(15),
    )
    add_query(
        id="helios-episodic-002",
        capability="episodic_recall",
        query="Which incident led to changing PagerDuty routing for billing alerts?",
        expected_evidence_ids=["helios-022"],
        acceptable_evidence_ids=["helios-024"],
        timestamp=iso(26),
    )
    add_query(
        id="helios-episodic-003",
        capability="episodic_recall",
        query="What production bug caused invoice PDFs to omit statement line items?",
        expected_evidence_ids=["helios-019"],
        timestamp=iso(20),
    )
    add_query(
        id="helios-assoc-002",
        capability="associative_recall",
        query="Why was Kafka rejected for internal billing event delivery?",
        expected_evidence_ids=["helios-011"],
        acceptable_evidence_ids=["helios-020"],
        timestamp=iso(22),
    )
    add_query(
        id="helios-assoc-003",
        capability="associative_recall",
        query="What customer-facing issue was fixed after the invoice PDF renderer patch?",
        expected_evidence_ids=["helios-021"],
        acceptable_evidence_ids=["helios-019"],
        timestamp=iso(49),
    )
    add_query(
        id="helios-update-002",
        capability="knowledge_update",
        query="Which identity provider handles merchant portal login now?",
        expected_evidence_ids=["helios-018"],
        forbidden_evidence_ids=["helios-004"],
        timestamp=iso(20),
    )
    add_query(
        id="helios-update-003",
        capability="knowledge_update",
        query="Are new sandbox AWS accounts allowed under current cost policy?",
        expected_evidence_ids=["helios-036"],
        forbidden_evidence_ids=["helios-032"],
        timestamp=iso(38),
    )
    add_query(
        id="helios-temporal-hist-002",
        capability="temporal_recall",
        query="How were downstream ledger changes propagated before Debezium adoption?",
        expected_evidence_ids=["helios-009"],
        forbidden_evidence_ids=["helios-020"],
        valid_at=iso(15),
        timestamp=iso(19),
    )
    add_query(
        id="helios-temporal-curr-002",
        capability="temporal_recall",
        query="How long must billing audit logs be retained today?",
        expected_evidence_ids=["helios-042"],
        forbidden_evidence_ids=["helios-017"],
        timestamp=iso(44),
    )
    add_query(
        id="helios-temporal-hist-003",
        capability="temporal_recall",
        query=(
            "Which authentication provider served the merchant portal in the second project week?"
        ),
        expected_evidence_ids=["helios-004"],
        forbidden_evidence_ids=["helios-018"],
        valid_at=iso(10),
        timestamp=iso(12),
    )
    add_query(
        id="helios-forget-002",
        capability="forgetting",
        query="Which vendor provides merchant portal authentication today?",
        expected_evidence_ids=["helios-018"],
        forbidden_evidence_ids=["helios-004", "helios-007"],
        timestamp=iso(70),
    )
    add_query(
        id="helios-forget-003",
        capability="forgetting",
        query="What observability platform backs billing production dashboards?",
        expected_evidence_ids=["helios-013"],
        forbidden_evidence_ids=["helios-053"],
        timestamp=iso(55),
    )
    add_query(
        id="helios-wm-002",
        capability="working_memory",
        query="Briefly describe the invoice PDF defect and its remediation.",
        expected_evidence_ids=["helios-021"],
        acceptable_evidence_ids=["helios-019"],
        retrieval_limit=3,
        prompt_budget_tokens=120,
        timestamp=iso(23),
    )
    add_query(
        id="helios-wm-003",
        capability="working_memory",
        query="Summarize the AWS account freeze and sandbox exception outcome.",
        expected_evidence_ids=["helios-036"],
        acceptable_evidence_ids=["helios-028"],
        forbidden_evidence_ids=["helios-032"],
        retrieval_limit=3,
        prompt_budget_tokens=120,
        timestamp=iso(40),
    )
    add_query(
        id="helios-meta-002",
        capability="metamemory",
        query="What is the primary Kafka cluster hostname for billing event streaming?",
        should_abstain=True,
        timestamp=iso(30),
    )
    add_query(
        id="helios-meta-003",
        capability="metamemory",
        query="Was an active-active eu-west billing region ever selected?",
        should_abstain=True,
        timestamp=iso(65),
    )
    add_query(
        id="helios-direct-004",
        capability="direct_recall",
        query="Which mechanism was rejected in favor of Debezium for downstream propagation?",
        expected_evidence_ids=["helios-011"],
        acceptable_evidence_ids=["helios-009"],
        timestamp=iso(21),
    )
    add_query(
        id="helios-episodic-004",
        capability="episodic_recall",
        query="When did finance temporarily gain a sandbox AWS account exception?",
        expected_evidence_ids=["helios-032"],
        forbidden_evidence_ids=["helios-036"],
        valid_at=iso(33),
        timestamp=iso(35),
    )
    add_query(
        id="helios-assoc-004",
        capability="associative_recall",
        query="What feedback followed the reconciliation performance improvements on PostgreSQL?",
        expected_evidence_ids=["helios-093"],
        acceptable_evidence_ids=["helios-005", "helios-041"],
        timestamp=iso(95),
    )
    add_query(
        id="helios-update-004",
        capability="knowledge_update",
        query="What audit retention window does compliance require now?",
        expected_evidence_ids=["helios-042"],
        forbidden_evidence_ids=["helios-017"],
        timestamp=iso(44),
    )
    add_query(
        id="helios-temporal-curr-003",
        capability="temporal_recall",
        query="Which CI system executes billing platform deployments today?",
        expected_evidence_ids=["helios-010"],
        timestamp=iso(30),
    )
    add_query(
        id="helios-forget-004",
        capability="forgetting",
        query="What downstream propagation approach is obsolete after Debezium rollout?",
        expected_evidence_ids=["helios-047"],
        acceptable_evidence_ids=["helios-100"],
        forbidden_evidence_ids=["helios-009"],
        timestamp=iso(105),
    )
    add_query(
        id="helios-direct-005",
        capability="direct_recall",
        query="Which login approach was rejected before adopting Auth0?",
        expected_evidence_ids=["helios-007"],
        timestamp=iso(9),
    )
    add_query(
        id="helios-episodic-005",
        capability="episodic_recall",
        query="What load test problem affected reconciliation against the read replica?",
        expected_evidence_ids=["helios-057"],
        acceptable_evidence_ids=["helios-058"],
        timestamp=iso(59),
    )
    add_query(
        id="helios-assoc-005",
        capability="associative_recall",
        query="What documentation still misstated the ledger backing store before correction?",
        expected_evidence_ids=["helios-014"],
        acceptable_evidence_ids=["helios-055"],
        forbidden_evidence_ids=["helios-016"],
        timestamp=iso(56),
    )
    add_query(
        id="helios-update-005",
        capability="knowledge_update",
        query="Where should finance run SQL reconciliation queries against finalized charges?",
        expected_evidence_ids=["helios-089"],
        acceptable_evidence_ids=["helios-041"],
        forbidden_evidence_ids=["helios-003"],
        timestamp=iso(92),
    )
    add_query(
        id="helios-temporal-hist-004",
        capability="temporal_recall",
        query="What audit retention period was requested before the policy extension?",
        expected_evidence_ids=["helios-017"],
        forbidden_evidence_ids=["helios-042"],
        valid_at=iso(30),
        timestamp=iso(35),
    )
    add_query(
        id="helios-wm-004",
        capability="working_memory",
        query="Summarize the merchant authentication migration outcome.",
        expected_evidence_ids=["helios-018"],
        acceptable_evidence_ids=["helios-026", "helios-045"],
        forbidden_evidence_ids=["helios-004"],
        retrieval_limit=3,
        prompt_budget_tokens=120,
        timestamp=iso(50),
    )
    add_query(
        id="helios-meta-004",
        capability="metamemory",
        query="Which vendor manages Drata integrations for Project Helios?",
        should_abstain=True,
        timestamp=iso(100),
    )
    add_query(
        id="helios-direct-006",
        capability="direct_recall",
        query="Which compliance automation vendor was chosen after the 1.0 release planning?",
        expected_evidence_ids=["helios-108"],
        timestamp=iso(176),
    )
    add_query(
        id="helios-episodic-006",
        capability="episodic_recall",
        query="Which release bundled reconciliation tooling with API hardening?",
        expected_evidence_ids=["helios-099"],
        timestamp=iso(100),
    )
    add_query(
        id="helios-assoc-006",
        capability="associative_recall",
        query="What on-call change followed the month-end reconciliation mismatch?",
        expected_evidence_ids=["helios-024"],
        acceptable_evidence_ids=["helios-022", "helios-046"],
        timestamp=iso(47),
    )
    add_query(
        id="helios-update-006",
        capability="knowledge_update",
        query="Does the internal wiki still list DynamoDB as the charge ledger store?",
        expected_evidence_ids=["helios-016"],
        forbidden_evidence_ids=["helios-014"],
        timestamp=iso(18),
    )
    add_query(
        id="helios-temporal-curr-004",
        capability="temporal_recall",
        query="Which connector streams ledger mutations to analytics consumers now?",
        expected_evidence_ids=["helios-025"],
        acceptable_evidence_ids=["helios-020"],
        forbidden_evidence_ids=["helios-009"],
        timestamp=iso(50),
    )
    add_query(
        id="helios-forget-005",
        capability="forgetting",
        query="Which legacy ledger table was marked read-only after cutover?",
        expected_evidence_ids=["helios-044"],
        forbidden_evidence_ids=["helios-002"],
        timestamp=iso(46),
    )
    add_query(
        id="helios-wm-005",
        capability="working_memory",
        query="Summarize the Debezium rollout and retired outbox polling.",
        expected_evidence_ids=["helios-020"],
        acceptable_evidence_ids=["helios-047", "helios-100"],
        forbidden_evidence_ids=["helios-009"],
        retrieval_limit=3,
        prompt_budget_tokens=120,
        timestamp=iso(102),
    )

    return queries


def build_feedback() -> list[dict[str, object]]:
    return [
        {
            "id": "helios-fb-001",
            "timestamp": iso(22, 11),
            "query_id": "helios-learn-pre-001",
            "outcome": "helpful",
            "target_event_ids": ["helios-020"],
        },
        {
            "id": "helios-fb-002",
            "timestamp": iso(22, 12),
            "query_id": "helios-learn-pre-001",
            "outcome": "unhelpful",
            "target_event_ids": ["helios-009"],
        },
        {
            "id": "helios-fb-003",
            "timestamp": iso(27, 11),
            "query_id": "helios-episodic-002",
            "outcome": "helpful",
            "target_event_ids": ["helios-022"],
        },
    ]


def main() -> None:
    events = build_events()
    queries = build_queries(events)
    feedback = build_feedback()
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(DATASET_DIR / "events.jsonl", events)
    write_jsonl(DATASET_DIR / "queries.jsonl", queries)
    write_jsonl(DATASET_DIR / "feedback.jsonl", feedback)
    manifest = {
        "name": "helios-v1",
        "schema_version": 1,
        "events": len(events),
        "queries": len(queries),
        "feedback": len(feedback),
        "description": (
            "Longitudinal billing platform memory benchmark for Project Helios "
            "over ~180 simulated days."
        ),
        "required_capabilities": [
            "direct_recall",
            "episodic_recall",
            "associative_recall",
            "temporal_recall",
            "knowledge_update",
            "forgetting",
            "working_memory",
            "learning",
            "metamemory",
        ],
    }
    (DATASET_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(events)} events, {len(queries)} queries, {len(feedback)} feedback records")


if __name__ == "__main__":
    main()
