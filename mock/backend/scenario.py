"""Tiny backend-like scenario service used until FastAPI/PostgreSQL exists."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from optimization.types import Disruption, Scenario

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_PATH = ROOT / "data" / "scenarios" / "demo_scenario.json"


def load_demo_scenario() -> Scenario:
    payload = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    return Scenario.from_dict(payload)


def affected_rakes(scenario: Scenario) -> list[str]:
    disruption = scenario.disruption
    if disruption is None or disruption.type != "section_blocked":
        return []
    blocked = disruption.target_entity_id
    return sorted({leg.rake_id for leg in scenario.schedule if leg.section == blocked and leg.present})


def simulate_disruption(
    scenario: Scenario, disruption: Disruption
) -> dict[str, Any]:
    updated = Scenario(
        scenario_id=scenario.scenario_id,
        stations=scenario.stations,
        sections=scenario.sections,
        routes=scenario.routes,
        rakes=scenario.rakes,
        demands=scenario.demands,
        yards=scenario.yards,
        schedule=scenario.schedule,
        disruption=disruption,
    )
    return {
        "scenario_id": updated.scenario_id,
        "disruption": {
            "type": disruption.type,
            "target_entity_id": disruption.target_entity_id,
            "start_time": disruption.start_time,
            "duration": disruption.duration,
            "severity": disruption.severity,
        },
        "affected_rakes": affected_rakes(updated),
    }
