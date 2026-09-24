"""Objective weights and shared objective accounting for RailFlow-Q.

The classical solver and the later quantum solver use the same business-level
metric definitions when evaluating decoded schedules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .types import Scenario, ScheduleLeg


@dataclass(frozen=True)
class ObjectiveWeights:
    delay: float = 1.0
    waiting: float = 1.0
    conflicts: float = 5.0
    yard_congestion: float = 1.0
    idle_time: float = 0.0  # Reserved for a later milestone; not modeled yet.
    reallocation: float = 8.0
    route_change: float = 5.0

    def as_dict(self) -> dict[str, float]:
        return {
            "delay": self.delay,
            "waiting": self.waiting,
            "conflicts": self.conflicts,
            "yard_congestion": self.yard_congestion,
            "idle_time": self.idle_time,
            "reallocation": self.reallocation,
            "route_change": self.route_change,
        }


@dataclass(frozen=True)
class ObjectiveBreakdown:
    """Unweighted measures plus their weighted contributions."""

    delay: float
    waiting: float
    conflicts: float
    reallocation: float
    route_changes: float
    yard_load: float
    idle_time: float
    weighted_delay: float
    weighted_waiting: float
    weighted_conflicts: float
    weighted_reallocation: float
    weighted_route_changes: float
    weighted_yard_load: float
    weighted_idle_time: float
    weighted_total: float

    def as_dict(self) -> dict[str, float]:
        return {
            "delay": self.delay,
            "waiting": self.waiting,
            "conflicts": self.conflicts,
            "reallocation": self.reallocation,
            "route_changes": self.route_changes,
            "yard_load": self.yard_load,
            "idle_time": self.idle_time,
            "weighted_delay": self.weighted_delay,
            "weighted_waiting": self.weighted_waiting,
            "weighted_conflicts": self.weighted_conflicts,
            "weighted_reallocation": self.weighted_reallocation,
            "weighted_route_changes": self.weighted_route_changes,
            "weighted_yard_load": self.weighted_yard_load,
            "weighted_idle_time": self.weighted_idle_time,
            "weighted_total": self.weighted_total,
        }


def _planned_details(scenario: Scenario):
    planned_rake: Dict[str, str] = {}
    planned_route: Dict[str, str] = {}
    planned_arrival: Dict[str, int] = {}
    for leg in scenario.schedule:
        planned_rake.setdefault(leg.demand_id, leg.rake_id)
        planned_route.setdefault(leg.demand_id, leg.route_id)
        planned_arrival[leg.demand_id] = max(planned_arrival.get(leg.demand_id, 0), leg.end)
    return planned_rake, planned_route, planned_arrival


def _overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and b_start < a_end


def _count_section_conflicts(scenario: Scenario, schedule: List[ScheduleLeg]) -> int:
    """Count actual section timing/headway conflicts in the decoded schedule.

    Capacity > 1 resources are governed by the validator's cumulative check and
    are not counted pairwise here. For capacity-1 sections, overlapping trains
    and sub-headway separation are each one conflict per affected pair.
    """
    section_map = {section.id: section for section in scenario.sections}
    conflicts = 0

    for section in scenario.sections:
        if section.capacity != 1:
            continue

        legs = [leg for leg in schedule if leg.section == section.id]
        for i, first in enumerate(legs):
            for second in legs[i + 1 :]:
                if _overlap(first.start, first.end, second.start, second.end):
                    conflicts += 1
                    continue

                if first.end <= second.start:
                    separation = second.start - first.end
                elif second.end <= first.start:
                    separation = first.start - second.end
                else:
                    separation = 0

                if separation < 2:
                    conflicts += 1

    # Keep the local mapping referenced so future conflict categories can use it
    # without changing this function's public contract.
    _ = section_map
    return conflicts


def calculate_objective_breakdown(
    scenario: Scenario,
    assignments: Iterable[dict],
    schedule: Iterable[dict | ScheduleLeg],
    weights: ObjectiveWeights,
) -> ObjectiveBreakdown:
    """Recompute objective components from the returned domain solution.

    This is solver-independent and is reused for decoded Qiskit/IBM solutions.
    """

    schedule_legs: List[ScheduleLeg] = [
        leg if isinstance(leg, ScheduleLeg) else ScheduleLeg(**leg)
        for leg in schedule
    ]
    assignments_list = list(assignments)

    rake_map = {r.id: r for r in scenario.rakes}
    section_map = {s.id: s for s in scenario.sections}
    demand_map = {d.id: d for d in scenario.demands}
    yard_by_station: Dict[str, list] = {}
    for yard in scenario.yards:
        yard_by_station.setdefault(yard.station_id, []).append(yard)

    planned_rake, planned_route, planned_arrival = _planned_details(scenario)

    grouped: Dict[tuple[str, str], list[ScheduleLeg]] = {}
    for leg in schedule_legs:
        grouped.setdefault((leg.rake_id, leg.demand_id), []).append(leg)

    total_delay = 0.0
    total_waiting = 0.0
    total_yard_load = 0.0

    for (rake_id, demand_id), legs in grouped.items():
        legs = sorted(legs, key=lambda x: (x.start, x.end, x.section))
        if not legs:
            continue

        rake = rake_map[rake_id]
        final_end = max(leg.end for leg in legs)
        planned_end = planned_arrival.get(demand_id, demand_map[demand_id].deadline)
        total_delay += max(0, final_end - planned_end)

        total_waiting += max(0, legs[0].start - rake.availability_time)
        for previous, current in zip(legs, legs[1:]):
            total_waiting += max(0, current.start - previous.end)

        # Count yard dwell per selected rake/demand traversal, not once per
        # unique route id. This keeps the decoded objective identical to the
        # CP-SAT resource terms when multiple rakes share the same route.
        for leg in legs:
            section = section_map[leg.section]
            for yard in yard_by_station.get(section.destination, []):
                total_yard_load += yard.dwell_time

    total_reallocation = float(
        sum(1 for assignment in assignments_list if assignment.get("reallocated", False))
    )
    total_route_changes = float(
        sum(
            1
            for assignment in assignments_list
            if planned_route.get(assignment["demand_id"]) != assignment["route_id"]
        )
    )
    total_conflicts = float(_count_section_conflicts(scenario, schedule_legs))

    # CP-SAT hard resource constraints guarantee zero actual conflicts for a
    # feasible schedule. The metric is still computed here because the quantum
    # decoder may produce an invalid candidate that should be visibly rejected.
    idle_time = 0.0

    weighted_delay = weights.delay * total_delay
    weighted_waiting = weights.waiting * total_waiting
    weighted_conflicts = weights.conflicts * total_conflicts
    weighted_reallocation = weights.reallocation * total_reallocation
    weighted_route_changes = weights.route_change * total_route_changes
    weighted_yard = weights.yard_congestion * total_yard_load
    weighted_idle = weights.idle_time * idle_time
    weighted_total = (
        weighted_delay
        + weighted_waiting
        + weighted_conflicts
        + weighted_reallocation
        + weighted_route_changes
        + weighted_yard
        + weighted_idle
    )

    return ObjectiveBreakdown(
        delay=float(total_delay),
        waiting=float(total_waiting),
        conflicts=total_conflicts,
        reallocation=total_reallocation,
        route_changes=total_route_changes,
        yard_load=float(total_yard_load),
        idle_time=idle_time,
        weighted_delay=float(weighted_delay),
        weighted_waiting=float(weighted_waiting),
        weighted_conflicts=float(weighted_conflicts),
        weighted_reallocation=float(weighted_reallocation),
        weighted_route_changes=float(weighted_route_changes),
        weighted_yard_load=float(weighted_yard),
        weighted_idle_time=float(weighted_idle),
        weighted_total=float(weighted_total),
    )


def objective_summary(weights: ObjectiveWeights) -> str:
    return (
        "minimize(weighted_delay + weighted_waiting + weighted_conflicts + "
        "weighted_reallocation + weighted_route_changes + weighted_yard_load), "
        f"with weights={weights.as_dict()}; idle_time is reserved until modeled."
    )
