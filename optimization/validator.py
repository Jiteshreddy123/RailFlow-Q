"""Shared feasibility gate for classical and quantum solutions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .types import Scenario, ScheduleLeg


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and b_start < a_end


def validate_schedule(scenario: Scenario, schedule: List[ScheduleLeg]) -> ValidationResult:
    violations: List[str] = []
    warnings: List[str] = []
    rake_ids = {r.id for r in scenario.rakes}
    section_map = {s.id: s for s in scenario.sections}
    route_map = {r.id: r for r in scenario.routes}
    demand_map = {d.id: d for d in scenario.demands}
    rake_map = {r.id: r for r in scenario.rakes}

    for leg in schedule:
        if leg.rake_id not in rake_ids:
            violations.append(f"unknown rake: {leg.rake_id}")
        if leg.section not in section_map:
            violations.append(f"unknown section: {leg.section}")
        if leg.route_id not in route_map:
            violations.append(f"unknown route: {leg.route_id}")
        if leg.demand_id not in demand_map:
            violations.append(f"unknown demand: {leg.demand_id}")
        if leg.end <= leg.start:
            violations.append(f"invalid timing for {leg.rake_id}/{leg.section}")

    # Every demand exactly once structurally: one route/rake pair in the supplied schedule.
    demand_pairs = {
        d: {(leg.rake_id, leg.route_id) for leg in schedule if leg.demand_id == d}
        for d in demand_map
    }
    for demand_id, pairs in demand_pairs.items():
        if not pairs:
            violations.append(f"demand not scheduled: {demand_id}")
        elif len(pairs) > 1:
            violations.append(f"demand assigned to multiple rake/route pairs: {demand_id}")

    # Route sequence and section membership.
    for (rake_id, demand_id, route_id), legs in _group(schedule).items():
        route = route_map.get(route_id)
        if route is None:
            continue
        section_ids = [leg.section for leg in sorted(legs, key=lambda x: x.start)]
        if section_ids != route.sections:
            violations.append(f"route sequence mismatch: {rake_id}/{demand_id}/{route_id}")
        for leg in legs:
            rake = rake_map.get(rake_id)
            if rake and leg.start < rake.availability_time:
                violations.append(f"rake {rake_id} used before availability")

    # Section resource capacity and 2-minute headway for capacity-1 sections.
    for section in scenario.sections:
        legs = [x for x in schedule if x.section == section.id]
        for i, a in enumerate(legs):
            for b in legs[i + 1 :]:
                if _overlap(a.start, a.end, b.start, b.end):
                    violations.append(f"section capacity conflict: {section.id} between {a.rake_id} and {b.rake_id}")
                elif section.capacity == 1:
                    if a.end <= b.start and b.start - a.end < 2:
                        violations.append(f"headway violation: {section.id} between {a.rake_id} and {b.rake_id}")
                    if b.end <= a.start and a.start - b.end < 2:
                        violations.append(f"headway violation: {section.id} between {a.rake_id} and {b.rake_id}")

        if section.capacity > 1:
            # Sweep-line capacity check.
            events = []
            for leg in legs:
                events.append((leg.start, 1))
                events.append((leg.end, -1))
            active = 0
            for _, delta in sorted(events, key=lambda x: (x[0], x[1])):
                active += delta
                if active > section.capacity:
                    violations.append(f"section capacity exceeded: {section.id}")

    # Disruption block.
    if scenario.disruption and scenario.disruption.type == "section_blocked":
        d = scenario.disruption
        for leg in schedule:
            if leg.section == d.target_entity_id and _overlap(leg.start, leg.end, d.start_time, d.end_time):
                violations.append(f"disrupted section used during closure: {leg.section}")

    return ValidationResult(valid=not violations, violations=violations, warnings=warnings)


def _group(schedule: List[ScheduleLeg]):
    grouped = {}
    for leg in schedule:
        grouped.setdefault((leg.rake_id, leg.demand_id, leg.route_id), []).append(leg)
    return grouped
