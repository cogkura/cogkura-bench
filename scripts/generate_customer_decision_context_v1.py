#!/usr/bin/env python3
"""Generate the customer-decision-context-v1 benchmark dataset."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets" / "customer_decision_context_v1"
START = datetime(2025, 1, 15, 10, 0, tzinfo=UTC)
SUBJECT = "customer-alex"


def iso(months: int, day: int = 15, hour: int = 10) -> str:
    base = START + timedelta(days=months * 30 + day - 15)
    return base.replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def build_events() -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    seq = 0

    def add(
        event_id: str,
        months: int,
        event_type: str,
        content: str,
        *,
        day: int = 15,
        hour: int = 10,
        tags: list[str] | None = None,
        entities: list[str] | None = None,
        semantic_facts: list[dict[str, object]] | None = None,
        session_id: str | None = None,
        related_events: list[str] | None = None,
    ) -> None:
        nonlocal seq
        seq += 1
        if session_id is None:
            session_id = f"timeline-{months:02d}"
        record: dict[str, object] = {
            "id": event_id,
            "timestamp": iso(months, day, hour),
            "sequence": seq,
            "subject_id": SUBJECT,
            "event_type": event_type,
            "content": content,
            "entities": entities or [],
            "semantic_facts": semantic_facts or [],
            "tags": tags or [],
            "supersedes": [],
            "related_events": related_events or [],
        }
        if session_id is not None:
            record["session_id"] = session_id
        events.append(record)

    add(
        "ski-browse-001",
        0,
        "browse",
        "Browsed ski jackets and alpine goggles in the winter sale.",
        session_id="ski-session-001",
        tags=["skiing", "stale"],
    )
    add(
        "ski-browse-002",
        0,
        day=16,
        event_type="browse",
        content="Compared ski pants and thermal base layers online.",
        session_id="ski-session-001",
        tags=["skiing", "stale"],
    )
    add(
        "ski-interest-001",
        1,
        "preference_statement",
        "Customer mentioned interest in skiing trips to the Alps.",
        semantic_facts=[
            {
                "subject": SUBJECT,
                "predicate": "activity_interest",
                "object": "skiing",
                "cardinality": "many",
            }
        ],
        tags=["skiing", "stale"],
    )

    # --- Early hiking interest (months 2-4) ---
    add(
        "hiking-browse-001",
        2,
        "browse",
        "Browsed waterproof hiking jackets and trail maps for Snowdonia.",
        session_id="hiking-session-001",
        tags=["hiking"],
    )
    add(
        "hiking-browse-002",
        2,
        day=20,
        event_type="browse",
        content="Looked at hiking boots and gaiters for weekend walks.",
        session_id="hiking-session-001",
        tags=["hiking"],
    )
    add(
        "hiking-interest-001",
        3,
        "preference_statement",
        "Customer said weekend hiking in the Lake District is their main outdoor activity.",
        semantic_facts=[
            {
                "subject": SUBJECT,
                "predicate": "activity_interest",
                "object": "hiking",
                "cardinality": "many",
            }
        ],
        tags=["hiking"],
    )
    add(
        "hiking-browse-003",
        3,
        day=22,
        event_type="browse",
        content="Compared mid-layer fleeces and softshell jackets for hiking.",
        session_id="hiking-session-002",
        tags=["hiking"],
    )
    add(
        "hiking-purchase-001",
        4,
        "purchase",
        "Purchased TrailMaster hiking boots size 10 and merino base layers.",
        entities=["trailmaster-boots"],
        tags=["hiking"],
    )
    add(
        "hiking-browse-004",
        4,
        day=18,
        event_type="browse",
        content="Browsed trekking poles and hydration packs for long day hikes.",
        session_id="hiking-session-002",
        tags=["hiking"],
    )
    add(
        "hiking-positive-001",
        5,
        "positive_outcome",
        "Customer reported the TrailMaster boots were excellent on a 14-mile Peak District hike.",
        entities=["trailmaster-boots"],
        tags=["hiking"],
        related_events=["hiking-purchase-001"],
    )

    # --- Size L (historical, month 5) ---
    add(
        "size-old-l-001",
        5,
        day=25,
        event_type="preference_statement",
        content="Customer profile updated: jacket size recorded as L after in-store fitting.",
        semantic_facts=[
            {
                "subject": SUBJECT,
                "predicate": "jacket_size",
                "object": "L",
                "cardinality": "one",
            }
        ],
        tags=["size"],
    )

    # --- Colour preference (month 6) ---
    add(
        "colour-preference-001",
        6,
        "preference_statement",
        "Customer prefers black, navy, or grey jackets and avoids bright colours.",
        semantic_facts=[
            {
                "subject": SUBJECT,
                "predicate": "colour_preference",
                "object": "neutral",
                "cardinality": "one",
            }
        ],
        tags=["preference"],
    )

    # --- Lightweight outerwear (months 7-9) ---
    add(
        "lightweight-browse-001",
        7,
        "browse",
        "Browsed ultralight packable jackets under 300g for summer hiking.",
        session_id="lightweight-session-001",
        tags=["lightweight"],
    )
    add(
        "lightweight-browse-002",
        7,
        day=20,
        event_type="browse",
        content="Compared featherweight windshells and minimalist rain shells.",
        session_id="lightweight-session-001",
        tags=["lightweight"],
    )
    add(
        "lightweight-purchase-001",
        8,
        "purchase",
        "Purchased FeatherLite Packable Shell jacket in navy, size L.",
        entities=["featherlite-packable-shell"],
        tags=["lightweight"],
    )
    add(
        "lightweight-positive-001",
        9,
        "positive_outcome",
        "Customer praised the FeatherLite shell for being barely noticeable in a day pack.",
        entities=["featherlite-packable-shell"],
        tags=["lightweight"],
        related_events=["lightweight-purchase-001"],
    )

    # --- NorthPeak Alpine Shell fit issue (months 9-11) ---
    add(
        "northpeak-compare-001",
        9,
        day=12,
        event_type="browse",
        content=(
            "Compared NorthPeak Alpine Shell against other technical shells for Scottish winter."
        ),
        entities=["northpeak-alpine-shell"],
        tags=["northpeak"],
    )
    add(
        "northpeak-purchase-001",
        9,
        day=18,
        event_type="purchase",
        content="Purchased NorthPeak Alpine Shell jacket in black, size L.",
        entities=["northpeak-alpine-shell"],
        tags=["northpeak"],
    )
    add(
        "northpeak-return-001",
        10,
        "product_return",
        "Returned NorthPeak Alpine Shell because sleeves were too short when reaching overhead.",
        entities=["northpeak-alpine-shell"],
        tags=["northpeak", "fit"],
        related_events=["northpeak-purchase-001"],
        semantic_facts=[
            {
                "subject": SUBJECT,
                "predicate": "product_fit_issue",
                "object": "northpeak-alpine-shell:sleeves_too_short",
                "cardinality": "many",
            }
        ],
    )
    add(
        "northpeak-support-001",
        10,
        day=20,
        event_type="support_interaction",
        content=(
            "Support agent noted sleeve length issue and suggested trying regular-fit alternatives."
        ),
        entities=["northpeak-alpine-shell"],
        tags=["northpeak", "fit"],
        related_events=["northpeak-return-001"],
    )

    # --- More hiking evidence for competition (months 10-12) ---
    add(
        "hiking-browse-005",
        10,
        day=5,
        event_type="browse",
        content="Browsed Gore-Tex hiking jackets for Scottish Highlands trips.",
        session_id="scotland-waterproof-session-001",
        tags=["hiking"],
    )
    add(
        "hiking-browse-006",
        10,
        day=6,
        event_type="browse",
        content="Compared 3-layer waterproof shells rated for sustained rain on ridges.",
        session_id="scotland-waterproof-session-001",
        tags=["hiking"],
    )
    add(
        "hiking-browse-007",
        11,
        "browse",
        content="Looked at breathable hardshells for fast-and-light hiking.",
        session_id="hiking-session-003",
        tags=["hiking"],
    )
    add(
        "hiking-browse-008",
        11,
        day=22,
        event_type="browse",
        content="Browsed hiking rain pants and pack covers for wet-weather kit.",
        session_id="hiking-session-003",
        tags=["hiking"],
    )
    add(
        "hiking-positive-002",
        12,
        "positive_outcome",
        "Customer completed a wet Ben Nevis ascent and wants better waterproof kit next time.",
        tags=["hiking"],
    )

    # --- Current size M (month 13) ---
    add(
        "size-current-m-001",
        13,
        "preference_statement",
        "Customer profile updated: jacket size now M after recent fitting and weight change.",
        semantic_facts=[
            {
                "subject": SUBJECT,
                "predicate": "jacket_size",
                "object": "M",
                "cardinality": "one",
            }
        ],
        tags=["size"],
    )

    # --- Noise events (spread across timeline with unique timestamps) ---
    noise_templates = [
        ("browse", "Browsed 30L daypacks for commuting."),
        ("purchase", "Purchased casual chino trousers size 32."),
        ("browse", "Looked at wool beanie hats and gloves."),
        ("support_interaction", "Asked about delivery status for order #48291."),
        ("browse", "Browsed camping stoves and fuel canisters."),
        ("purchase", "Purchased a 20L commuter backpack in grey."),
        ("browse", "Compared hiking trousers with zip-off legs."),
        ("purchase", "Bought merino socks multipack."),
        ("support_interaction", "Requested invoice copy for expense claim."),
        ("browse", "Browsed head torches and spare batteries."),
        ("browse", "Compared 40L trekking backpacks for multi-day trips."),
        ("purchase", "Purchased softshell hiking trousers size M."),
        ("browse", "Looked at gaiters and crampon-compatible boots."),
        ("support_interaction", "Asked about loyalty points balance."),
        ("browse", "Browsed camping mats and inflatable pillows."),
        ("purchase", "Purchased dry bags for kayaking gear."),
        ("browse", "Compared insulated trousers for winter camping."),
        ("purchase", "Bought a neck gaiter and liner gloves."),
        ("support_interaction", "Reported missing item from split shipment."),
        ("browse", "Browsed carabiners and climbing chalk bags."),
        ("browse", "Compared ultralight frameless packs."),
        ("purchase", "Purchased rain trousers for cycling commute."),
        ("browse", "Looked at sunglasses and retainer straps."),
        ("browse", "Browsed water filters and purification tablets."),
        ("support_interaction", "Updated delivery address for pending order."),
        ("browse", "Compared insulated flasks and mug sets."),
        ("purchase", "Bought a packable down vest."),
        ("browse", "Browsed map cases and compass sets."),
        ("browse", "Compared convertible travel trousers."),
        ("browse", "Looked at hydration bladder replacements."),
        ("purchase", "Purchased trekking sock liners."),
        ("browse", "Browsed emergency bivvy bags and whistles."),
        ("support_interaction", "Asked about extended returns window."),
        ("browse", "Compared LED lanterns for campsite use."),
        ("browse", "Looked at trekking pole baskets and tips."),
        ("browse", "Browsed bike panniers and rack adapters."),
        ("purchase", "Purchased thermal leggings for winter runs."),
        ("browse", "Compared portable power banks for trail use."),
        ("browse", "Browsed hat liners and balaclavas."),
        ("support_interaction", "Confirmed gift receipt for returned item."),
        ("browse", "Looked at camp cutlery and mess tins."),
        ("browse", "Compared roll-top dry sacks by capacity."),
        ("purchase", "Bought replacement boot laces."),
        ("browse", "Browsed insect repellent and sun cream."),
        ("browse", "Compared fleece-lined joggers for camp evenings."),
        ("support_interaction", "Asked about price match on competitor listing."),
        ("browse", "Browsed car roof boxes and straps."),
        ("browse", "Looked at watch compasses and altimeters."),
        ("purchase", "Purchased a hip belt pouch for trail snacks."),
        ("browse", "Compared folding camp chairs and tables."),
        ("browse", "Browsed waterproof overtrousers for dog walking."),
        ("browse", "Compared hand warmer packets and toe warmers."),
        ("support_interaction", "Requested size exchange for gloves."),
        ("browse", "Browsed trail running vests and flasks."),
        ("browse", "Compared camera chest harnesses for hiking."),
        ("purchase", "Bought a pack rain cover."),
        ("browse", "Looked at trekking towel microfibre sets."),
        ("purchase", "Purchased windproof running tights."),
        ("support_interaction", "Asked about repair service for zip failure."),
        ("browse", "Browsed hammock straps and carabiners."),
        ("browse", "Compared blister prevention tape and balms."),
        ("browse", "Browsed ski boot bags and helmet cases."),
        ("browse", "Looked at portable camp showers."),
        ("browse", "Compared cargo shorts for summer travel."),
        ("purchase", "Bought a lightweight shemagh scarf."),
        ("support_interaction", "Confirmed subscription pause for gear box."),
        ("browse", "Browsed bear canisters and food storage."),
        ("browse", "Compared travel cubes and organisers."),
        ("browse", "Looked at carabiner key rings and badges."),
        ("browse", "Browsed camp soap and biodegradable wipes."),
        ("browse", "Compared ski touring pants with vents."),
        ("support_interaction", "Asked about student discount eligibility."),
        ("browse", "Browsed avalanche transceivers and probes."),
        ("purchase", "Purchased reflective armbands for night runs."),
        ("browse", "Compared wheeled travel bags for flights."),
        ("browse", "Looked at camp axe and saw multitools."),
        ("browse", "Browsed bib ski pants for resort days."),
        ("browse", "Compared lip balm SPF and face tape."),
        ("support_interaction", "Reported duplicate charge on recent order."),
        ("browse", "Browsed snow shovels and probe kits."),
        ("purchase", "Purchased a lightweight stuff sack set."),
        ("browse", "Compared GPS handhelds and mapping software."),
        ("browse", "Looked at trekking pole tip protectors."),
        ("browse", "Browsed insulated bib overalls for ice climbing."),
        ("support_interaction", "Asked about trade-in program for old boots."),
        ("browse", "Browsed camp coffee makers and grinders."),
        ("purchase", "Bought a packable sun hat."),
        ("browse", "Compared courier-style messenger bags."),
        ("browse", "Looked at rope bags and chalk buckets."),
        ("purchase", "Purchased lined jeans for autumn walks."),
        ("support_interaction", "Updated payment card on file."),
        ("browse", "Browsed avalanche airbag packs."),
        ("browse", "Compared glove liners and touchscreen tips."),
        ("browse", "Browsed ski helmet audio adapters."),
        ("browse", "Looked at camp pie irons and grills."),
        ("browse", "Compared softshell ski pants."),
        ("purchase", "Bought replacement insoles for hiking boots."),
        ("support_interaction", "Asked about corporate bulk order discount."),
        ("browse", "Browsed trail mix and energy bar bundles."),
        ("browse", "Compared camera clip systems for straps."),
        ("browse", "Looked at folding trowels and toilet paper."),
        ("browse", "Browsed ski goggle lenses and cases."),
        ("browse", "Compared rain skirts for pack protection."),
        ("support_interaction", "Requested carbon offset for shipping."),
        ("browse", "Browsed camp pillows and neck supports."),
        ("purchase", "Purchased a lightweight duffel for gym kit."),
        ("browse", "Compared boot dryers and deodoriser sprays."),
        ("browse", "Looked at tent footprint groundsheets."),
        ("browse", "Browsed ski base layer sets."),
        ("support_interaction", "Asked about warranty on trekking poles."),
        ("browse", "Browsed car window shades for road trips."),
        ("purchase", "Bought a packable poncho as emergency cover."),
        ("browse", "Compared hydration vest sizing charts."),
        ("browse", "Looked at camp spice kits and condiment sets."),
        ("browse", "Browsed padded ski pants for park sessions."),
        ("browse", "Compared watch bands for GPS devices."),
        ("support_interaction", "Confirmed pickup from local store."),
        ("browse", "Browsed folding solar panels for base camp."),
        ("browse", "Compared ski boot backpacks with wheels."),
        ("purchase", "Purchased a lightweight wallet for travel."),
        ("browse", "Looked at camp dish racks and sponges."),
        ("browse", "Browsed mountaineering salopettes."),
        ("support_interaction", "Asked about recycling program for old gear."),
    ]
    for index, (event_type, content) in enumerate(noise_templates, start=1):
        month = 1 + (index % 15)
        day = 3 + (index % 24)
        hour = 9 + (index % 7)
        add(
            f"noise-{index:03d}",
            month,
            event_type,
            content,
            day=day,
            hour=hour,
            tags=["noise"],
        )

    return events


def build_queries(events: list[dict[str, object]]) -> list[dict[str, object]]:
    last_ts = max(datetime.fromisoformat(str(event["timestamp"])) for event in events)
    query_ts = (last_ts + timedelta(hours=2)).isoformat()

    primary_query = {
        "id": "customer-waterproof-jacket",
        "timestamp": query_ts,
        "capability": "working_memory",
        "query": (
            "I'm looking for a waterproof jacket for a hiking trip next month. "
            "What would you recommend?"
        ),
        "goal": "Help the customer choose an appropriate waterproof hiking jacket.",
        "expected_evidence_ids": [
            "size-current-m-001",
            "hiking-interest-001",
            "colour-preference-001",
            "lightweight-purchase-001",
            "northpeak-return-001",
        ],
        "acceptable_evidence_ids": [
            "hiking-purchase-001",
            "hiking-positive-001",
            "hiking-positive-002",
            "lightweight-positive-001",
            "northpeak-support-001",
        ],
        "forbidden_evidence_ids": [
            "size-old-l-001",
            "ski-browse-001",
            "ski-browse-002",
            "ski-interest-001",
        ],
        "expected_evidence_groups": [
            {
                "id": "current_jacket_size",
                "label": "Current jacket size",
                "event_ids": ["size-current-m-001"],
            },
            {
                "id": "hiking_interest",
                "label": "Established hiking interest",
                "event_ids": [
                    "hiking-interest-001",
                    "hiking-purchase-001",
                    "hiking-positive-001",
                    "hiking-positive-002",
                ],
            },
            {
                "id": "colour_preference",
                "label": "Neutral colour preference",
                "event_ids": ["colour-preference-001"],
            },
            {
                "id": "lightweight_preference",
                "label": "Prefers lightweight outerwear",
                "event_ids": [
                    "lightweight-purchase-001",
                    "lightweight-positive-001",
                ],
            },
            {
                "id": "northpeak_fit_issue",
                "label": "Previous NorthPeak sleeve-fit issue",
                "event_ids": [
                    "northpeak-return-001",
                    "northpeak-support-001",
                ],
            },
        ],
        "forbidden_evidence_groups": [
            {
                "id": "stale_jacket_size",
                "label": "Historical jacket size",
                "event_ids": ["size-old-l-001"],
            },
            {
                "id": "old_skiing_interest",
                "label": "Old skiing interest",
                "event_ids": [
                    "ski-browse-001",
                    "ski-browse-002",
                    "ski-interest-001",
                ],
            },
        ],
        "should_abstain": False,
        "retrieval_limit": 50,
        "prompt_budget_tokens": 750,
        "tags": [
            "core",
            "customer_memory",
            "working_memory",
            "decision_context",
            "redundancy",
        ],
    }
    return [primary_query]


def main() -> None:
    events = build_events()
    queries = build_queries(events)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(DATASET_DIR / "events.jsonl", events)
    write_jsonl(DATASET_DIR / "queries.jsonl", queries)
    write_jsonl(DATASET_DIR / "feedback.jsonl", [])
    manifest = {
        "name": "customer-decision-context-v1",
        "schema_version": 1,
        "events": len(events),
        "queries": len(queries),
        "feedback": 0,
        "description": (
            "Customer decision context scenario for bounded working-memory diagnostics."
        ),
        "required_capabilities": ["working_memory"],
    }
    (DATASET_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(events)} events and {len(queries)} queries to {DATASET_DIR}")


if __name__ == "__main__":
    main()
