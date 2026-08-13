#!/usr/bin/env python3
"""Generate the deterministic software-project-v1 benchmark dataset."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets" / "software_project_v1"
START = datetime(2026, 1, 2, 10, 0, tzinfo=UTC)


def iso(day: int, hour: int = 10) -> str:
    return (START + timedelta(days=day - 1, hours=hour - 10)).isoformat()


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")


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
                "subject_id": "project-atlas",
                "event_type": event_type,
                "content": content,
                "entities": entities or [],
                "semantic_facts": semantic_facts or [],
                "tags": tags or [],
                "supersedes": supersedes or [],
                "related_events": related_events or [],
            }
        )

    add(
        "atlas-001",
        1,
        "architecture_decision",
        "Project Atlas will use FastAPI for all public HTTP endpoints.",
        entities=["fastapi"],
        semantic_facts=[
            {
                "subject": "api-framework",
                "predicate": "implementation",
                "object": "fastapi",
                "cardinality": "one",
            }
        ],
        tags=["api"],
    )
    add(
        "atlas-002",
        2,
        "architecture_decision",
        "Redis was selected for distributed job coordination.",
        entities=["redis", "job-coordination"],
        semantic_facts=[
            {
                "subject": "job-coordination",
                "predicate": "implementation",
                "object": "redis",
                "cardinality": "one",
            }
        ],
    )
    add(
        "atlas-003",
        4,
        "implementation",
        "Added health-check endpoint returning service version metadata.",
    )
    add(
        "atlas-004",
        6,
        "incident",
        "Release failed because the database migration ran after application startup.",
        tags=["incident", "deployment"],
    )
    add(
        "atlas-005",
        8,
        "user_feedback",
        "Redis introduced additional operational overhead for on-call rotations.",
        related_events=["atlas-002"],
    )
    add(
        "atlas-006",
        10,
        "implementation",
        "Redis deployment proved unnecessarily complex for the current team size.",
        related_events=["atlas-005"],
    )
    add(
        "atlas-007",
        12,
        "architecture_decision",
        "PostgreSQL advisory locks replace Redis for job coordination.",
        entities=["postgresql", "redis", "job-coordination"],
        semantic_facts=[
            {
                "subject": "job-coordination",
                "predicate": "implementation",
                "object": "postgresql-advisory-locks",
                "cardinality": "one",
            }
        ],
        supersedes=["atlas-002"],
        related_events=["atlas-005", "atlas-006"],
    )
    add(
        "atlas-008",
        14,
        "architecture_decision",
        "AuthCorp OAuth2 was selected for customer authentication.",
        entities=["authcorp", "oauth2"],
        semantic_facts=[
            {
                "subject": "authentication",
                "predicate": "provider",
                "object": "authcorp",
                "cardinality": "one",
            }
        ],
    )
    add(
        "atlas-009",
        16,
        "documentation",
        "Engineer A confirmed production currently uses PostgreSQL.",
        entities=["postgresql"],
    )
    add(
        "atlas-010",
        17,
        "documentation",
        "An outdated deployment note still claims production uses MySQL.",
        entities=["mysql"],
        tags=["stale"],
    )
    add(
        "atlas-011",
        18,
        "documentation",
        "Production configuration review confirmed PostgreSQL as the live database.",
        supersedes=["atlas-010"],
        related_events=["atlas-009"],
    )
    add(
        "atlas-012",
        20,
        "implementation",
        "Prototype used temporary in-memory queues before coordination migration.",
        tags=["obsolete"],
    )
    add(
        "atlas-013",
        22,
        "architecture_decision",
        "RabbitMQ was selected for asynchronous task delivery.",
        entities=["rabbitmq"],
    )
    add(
        "atlas-014",
        24,
        "rejected_approach",
        "The team rejected Kafka for task delivery due to operational cost.",
        related_events=["atlas-013"],
    )
    add(
        "atlas-015",
        26,
        "architecture_decision",
        "GitHub Actions will run all CI/CD pipelines for Project Atlas.",
        entities=["github-actions", "ci-cd"],
    )
    add(
        "atlas-016",
        28,
        "implementation",
        "Added OpenTelemetry tracing to all API handlers.",
        entities=["opentelemetry", "observability"],
    )
    add(
        "atlas-017",
        30,
        "bug",
        "Cache invalidation missed tenant-specific keys during rollout.",
        entities=["cache"],
    )
    add(
        "atlas-018",
        31,
        "fix",
        "Patched cache invalidation to include tenant namespace prefixes.",
        related_events=["atlas-017"],
    )
    add("atlas-019", 33, "requirement", "Customers requested audit logs retained for 90 days.")
    add(
        "atlas-020",
        35,
        "requirement_change",
        "Audit log retention increased from 90 to 180 days.",
        supersedes=["atlas-019"],
    )
    add(
        "atlas-021",
        38,
        "user_feedback",
        "Enterprise customer asked for SAML support in addition to OAuth2.",
    )
    add(
        "atlas-022",
        40,
        "rejected_approach",
        "The team rejected building a custom SAML stack in favor of AuthCorp.",
        related_events=["atlas-008", "atlas-021"],
    )
    add(
        "atlas-023",
        42,
        "dependency",
        "Pinned SQLAlchemy 2.0 for async database access.",
        entities=["sqlalchemy"],
    )
    add(
        "atlas-024",
        44,
        "implementation",
        "Added Redis caching layer for read-heavy dashboard endpoints.",
        entities=["redis", "cache"],
    )
    add(
        "atlas-025",
        46,
        "architecture_decision",
        "Moved dashboard caching from Redis to in-process LRU cache.",
        supersedes=["atlas-024"],
        semantic_facts=[
            {
                "subject": "dashboard-cache",
                "predicate": "implementation",
                "object": "in-process-lru",
                "cardinality": "one",
            }
        ],
    )
    add(
        "atlas-026",
        48,
        "incident",
        "Payment webhook retries flooded the task queue during provider outage.",
        tags=["incident"],
    )
    add(
        "atlas-027",
        50,
        "fix",
        "Added exponential backoff and dead-letter handling for payment webhooks.",
        related_events=["atlas-026"],
    )
    add(
        "atlas-028",
        52,
        "release",
        "Project Atlas 0.4.0 released with observability and queue hardening.",
    )
    add("atlas-029", 54, "noise", "Updated the team lunch calendar spreadsheet.", tags=["noise"])
    add(
        "atlas-030",
        56,
        "architecture_decision",
        "Grafana Cloud was adopted for production dashboards and alerting.",
        entities=["grafana"],
    )
    add(
        "atlas-031",
        58,
        "implementation",
        "Migrated staging deployments to use the same Grafana dashboards as production.",
        related_events=["atlas-030"],
    )
    add(
        "atlas-032",
        60,
        "architecture_decision",
        "ZeroTrust SSO was adopted in the final enterprise security review.",
        entities=["zerotrust-sso", "oauth2"],
        semantic_facts=[
            {
                "subject": "enterprise-sso",
                "predicate": "provider",
                "object": "zerotrust-sso",
                "cardinality": "one",
            }
        ],
    )

    filler_types = [
        "implementation",
        "documentation",
        "conversation",
        "dependency",
        "test_failure",
        "fix",
        "noise",
    ]
    filler_topics = [
        "refactored repository layer",
        "updated onboarding docs",
        "discussed pagination defaults",
        "bumped pytest dependency",
        "flaky integration test on staging",
        "fixed flaky test by stabilizing clock",
        "renamed internal service folder",
        "added request logging middleware",
        "reviewed error envelope format",
        "cleaned obsolete feature flags",
        "updated API examples in README",
        "discussed blue/green deploy timing",
        "added database connection pooling",
        "reviewed queue retry policy",
        "migrated config to environment variables",
        "added canary deployment checklist",
        "reviewed customer support escalations",
        "added typed response models",
        "discussed log sampling strategy",
        "updated local development compose file",
    ]
    event_num = 33
    for day in range(3, 61):
        if any(event["timestamp"].startswith(iso(day)[:10]) for event in events):
            continue
        topic = filler_topics[(day + event_num) % len(filler_topics)]
        event_type = filler_types[(day + event_num) % len(filler_types)]
        add(
            f"atlas-{event_num:03d}",
            day,
            event_type,
            f"Project Atlas team {topic}.",
            tags=["noise"] if event_type == "noise" else [],
        )
        event_num += 1
        if event_num > 250:
            break
    while len(events) < 250:
        day = 3 + (len(events) % 58)
        topic = filler_topics[len(events) % len(filler_topics)]
        event_type = filler_types[len(events) % len(filler_types)]
        add(
            f"atlas-{len(events) + 1:03d}",
            day,
            event_type,
            f"Project Atlas follow-up: {topic}.",
            tags=["noise"] if event_type == "noise" else [],
        )
    return events[:250]


def _query_timestamp(
    event_map: dict[str, dict[str, object]], evidence_ids: list[str], *, day_offset: int = 1
) -> str:
    latest = max(parse_iso(str(event_map[event_id]["timestamp"])) for event_id in evidence_ids)
    return (latest + timedelta(days=day_offset)).isoformat()


def build_queries(events: list[dict[str, object]]) -> list[dict[str, object]]:
    event_map = {str(event["id"]): event for event in events}
    queries: list[dict[str, object]] = []

    def add_query(**kwargs: object) -> None:
        evidence = [str(item) for item in kwargs.pop("expected_evidence_ids", [])]
        acceptable = [str(item) for item in kwargs.pop("acceptable_evidence_ids", [])]
        forbidden = [str(item) for item in kwargs.pop("forbidden_evidence_ids", [])]
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
                **kwargs,
            }
        )

    add_query(
        id="atlas-direct-001",
        capability="direct_recall",
        query="Which API framework was selected for Project Atlas?",
        expected_evidence_ids=["atlas-001"],
        timestamp=iso(3),
    )
    add_query(
        id="atlas-episodic-001",
        capability="episodic_recall",
        query="What caused the failed deployment in the first week?",
        expected_evidence_ids=["atlas-004"],
        timestamp=iso(7),
    )
    add_query(
        id="atlas-assoc-001",
        capability="associative_recall",
        query="What operational concern influenced the coordination architecture?",
        expected_evidence_ids=["atlas-005"],
        acceptable_evidence_ids=["atlas-006", "atlas-007"],
        timestamp=iso(13),
    )
    add_query(
        id="atlas-update-001",
        capability="knowledge_update",
        query="What mechanism does Project Atlas currently use for job coordination?",
        expected_evidence_ids=["atlas-007"],
        forbidden_evidence_ids=["atlas-002"],
        timestamp=iso(14),
    )
    add_query(
        id="atlas-temporal-hist-001",
        capability="temporal_recall",
        query="What mechanism was selected for job coordination on Day 5?",
        expected_evidence_ids=["atlas-002"],
        forbidden_evidence_ids=["atlas-007"],
        valid_at=iso(5),
        timestamp=iso(15),
    )
    add_query(
        id="atlas-temporal-curr-001",
        capability="temporal_recall",
        query="What database does production currently use?",
        expected_evidence_ids=["atlas-011"],
        acceptable_evidence_ids=["atlas-009"],
        forbidden_evidence_ids=["atlas-010"],
        timestamp=iso(19),
    )
    add_query(
        id="atlas-leak-001",
        capability="direct_recall",
        query="Which enterprise SSO provider was adopted in the final security review?",
        expected_evidence_ids=[],
        forbidden_evidence_ids=["atlas-032"],
        should_abstain=True,
        timestamp=iso(57),
    )
    add_query(
        id="atlas-meta-001",
        capability="metamemory",
        query="Which Kafka topic carries payment events?",
        should_abstain=True,
        timestamp=iso(20),
    )
    add_query(
        id="atlas-forget-001",
        capability="forgetting",
        query="What does Project Atlas currently use for job coordination?",
        expected_evidence_ids=["atlas-007"],
        forbidden_evidence_ids=["atlas-012", "atlas-002"],
        timestamp=iso(45),
    )
    add_query(
        id="atlas-learn-pre-001",
        capability="learning",
        query="How is background work scheduled across Atlas services?",
        expected_evidence_ids=["atlas-007"],
        acceptable_evidence_ids=["atlas-002"],
        timestamp=iso(16),
    )
    add_query(
        id="atlas-learn-post-001",
        capability="learning",
        query="What coordination approach is now used for scheduled jobs?",
        expected_evidence_ids=["atlas-007"],
        forbidden_evidence_ids=["atlas-002"],
        related_query_id="atlas-learn-pre-001",
        timestamp=iso(17),
    )
    add_query(
        id="atlas-wm-001",
        capability="working_memory",
        query="Summarize the production database situation.",
        expected_evidence_ids=["atlas-011"],
        acceptable_evidence_ids=["atlas-009"],
        forbidden_evidence_ids=["atlas-010"],
        retrieval_limit=3,
        prompt_budget_tokens=120,
        timestamp=iso(21),
    )

    capability_cycle = [
        "direct_recall",
        "episodic_recall",
        "associative_recall",
        "temporal_recall",
        "knowledge_update",
        "forgetting",
        "working_memory",
        "learning",
        "metamemory",
    ]
    anchor_events = [
        "atlas-001",
        "atlas-004",
        "atlas-005",
        "atlas-007",
        "atlas-008",
        "atlas-011",
        "atlas-012",
        "atlas-013",
        "atlas-015",
        "atlas-016",
        "atlas-017",
        "atlas-018",
        "atlas-020",
        "atlas-022",
        "atlas-023",
        "atlas-025",
        "atlas-026",
        "atlas-027",
        "atlas-028",
        "atlas-030",
    ]
    for index in range(1, 69):
        event_id = anchor_events[index % len(anchor_events)]
        capability = capability_cycle[index % len(capability_cycle)]
        add_query(
            id=f"atlas-fill-{index:03d}",
            capability=capability,
            query=f"Project Atlas question {index} about event {event_id}?",
            expected_evidence_ids=[event_id],
        )
    return queries[:80]


def build_feedback() -> list[dict[str, object]]:
    return [
        {
            "id": "atlas-fb-001",
            "timestamp": iso(16, 11),
            "query_id": "atlas-learn-pre-001",
            "outcome": "helpful",
            "target_event_ids": ["atlas-007"],
        },
        {
            "id": "atlas-fb-002",
            "timestamp": iso(16, 12),
            "query_id": "atlas-learn-pre-001",
            "outcome": "unhelpful",
            "target_event_ids": ["atlas-002"],
        },
        {
            "id": "atlas-fb-003",
            "timestamp": iso(30, 11),
            "query_id": "atlas-fill-001",
            "outcome": "helpful",
            "target_event_ids": ["atlas-001"],
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
        "name": "software-project-v1",
        "schema_version": 1,
        "events": len(events),
        "queries": len(queries),
        "feedback": len(feedback),
        "description": (
            "Longitudinal software engineering project memory benchmark for Project Atlas."
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
