"""Solver-neutral optimization model construction and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .types import FreightDemand, Rake, Route, Scenario


@dataclass(frozen=True)
class AssignmentOption:
    """One structurally feasible rake -> demand -> route option."""

    rake_id: str
    demand_id: str
    route_id: str


@dataclass(frozen=True)
class OptimizationModel:
    scenario_id: str
    assignment_options: List[AssignmentOption]
    demand_ids: List[str]
    rake_ids: List[str]
    route_ids: List[str]

    def options_for_demand(self, demand_id: str) -> List[AssignmentOption]:
        return [x for x in self.assignment_options if x.demand_id == demand_id]

    def options_for_rake(self, rake_id: str) -> List[AssignmentOption]:
        return [x for x in self.assignment_options if x.rake_id == rake_id]


def _route_index(routes: Iterable[Route]) -> Dict[str, Route]:
    return {route.id: route for route in routes}


def _route_is_connected(route: Route, section_index: Dict[str, object]) -> bool:
    """Return True when route.sections form a continuous path.

    Sections are interpreted in the order supplied by the route. Bidirectional
    sections may be traversed in either direction. The final reachable station
    must match route.destination.
    """
    if not route.sections:
        return False

    current_station = route.origin
    for section_id in route.sections:
        section = section_index.get(section_id)
        if section is None:
            return False

        if section.source == current_station:
            current_station = section.destination
        elif section.bidirectional and section.destination == current_station:
            current_station = section.source
        else:
            return False

    return current_station == route.destination


def _compatible(rake: Rake, demand: FreightDemand, route: Route) -> bool:
    # Phase 2 assumes a rake starts at the route origin. A later milestone can
    # add deadhead/repositioning decisions when that becomes necessary.
    return (
        rake.capacity >= demand.quantity
        and rake.availability_time >= 0
        and rake.current_location == route.origin
        and route.origin == demand.origin
        and route.destination == demand.destination
    )


def build_optimization_model(scenario: Scenario) -> OptimizationModel:
    """Build the solver-neutral assignment layer.

    Route connectivity is checked here. Temporal/resource constraints will be
    encoded by the classical solver in the next milestone.
    """

    route_index = _route_index(scenario.routes)
    section_index = {section.id: section for section in scenario.sections}
    options: List[AssignmentOption] = []

    for demand in scenario.demands:
        for rake in scenario.rakes:
            for route in scenario.routes:
                if not route.sections:
                    continue
                if route.id not in route_index:
                    continue
                if not _route_is_connected(route, section_index):
                    continue
                if not _compatible(rake, demand, route):
                    continue
                options.append(
                    AssignmentOption(
                        rake_id=rake.id,
                        demand_id=demand.id,
                        route_id=route.id,
                    )
                )

    return OptimizationModel(
        scenario_id=scenario.scenario_id,
        assignment_options=options,
        demand_ids=[d.id for d in scenario.demands],
        rake_ids=[r.id for r in scenario.rakes],
        route_ids=[r.id for r in scenario.routes],
    )
