"""Scenario-level prechecks used before constructing the CP-SAT model."""

from __future__ import annotations

from typing import List

from .types import Scenario


def validate_basic_constraints(scenario: Scenario) -> List[str]:
    violations: List[str] = []
    station_ids = {s.id for s in scenario.stations}
    section_ids = {s.id for s in scenario.sections}

    for section in scenario.sections:
        if section.source not in station_ids or section.destination not in station_ids:
            violations.append(f"section {section.id} references unknown station")
        if section.capacity < 1:
            violations.append(f"section {section.id} has invalid capacity")
        if section.travel_time <= 0:
            violations.append(f"section {section.id} has non-positive travel time")

    for route in scenario.routes:
        if not route.sections:
            violations.append(f"route {route.id} has no sections")
        for section_id in route.sections:
            if section_id not in section_ids:
                violations.append(f"route {route.id} references unknown section {section_id}")

    for demand in scenario.demands:
        if demand.origin not in station_ids or demand.destination not in station_ids:
            violations.append(f"demand {demand.id} references unknown station")
        if demand.quantity <= 0:
            violations.append(f"demand {demand.id} has non-positive quantity")
        if demand.deadline <= 0:
            violations.append(f"demand {demand.id} has invalid deadline")

    for rake in scenario.rakes:
        if rake.current_location not in station_ids:
            violations.append(f"rake {rake.id} has unknown current location")
        if rake.capacity <= 0:
            violations.append(f"rake {rake.id} has non-positive capacity")

    for yard in scenario.yards:
        if yard.station_id not in station_ids:
            violations.append(f"yard {yard.id} references unknown station")
        if yard.track_capacity < 1:
            violations.append(f"yard {yard.id} has invalid track capacity")
        if not 0 <= yard.occupied_tracks <= yard.track_capacity:
            violations.append(f"yard {yard.id} has invalid occupancy")

    return violations
