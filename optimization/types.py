"""Canonical domain objects shared by the mock backend and solvers.

The domain model is intentionally solver-agnostic. OR-Tools and Qiskit
should consume these objects rather than defining their own railway data model.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional

DisruptionType = Literal[
    "section_blocked",
    "rake_delayed",
    "yard_closed",
    "congestion",
]


@dataclass(frozen=True)
class Station:
    id: str
    name: str


@dataclass(frozen=True)
class RailSection:
    id: str
    source: str
    destination: str
    capacity: int
    travel_time: int
    bidirectional: bool = False


@dataclass(frozen=True)
class Route:
    id: str
    origin: str
    destination: str
    sections: List[str]
    travel_time: int


@dataclass(frozen=True)
class Rake:
    id: str
    current_location: str
    availability_time: int
    capacity: int
    type: str


@dataclass(frozen=True)
class FreightDemand:
    id: str
    origin: str
    destination: str
    quantity: int
    deadline: int
    priority: int = 1


@dataclass(frozen=True)
class Yard:
    id: str
    station_id: str
    track_capacity: int
    occupied_tracks: int = 0
    dwell_time: int = 15


@dataclass(frozen=True)
class ScheduleLeg:
    rake_id: str
    demand_id: str
    route_id: str
    section: str
    start: int
    end: int
    present: bool = True


@dataclass(frozen=True)
class Disruption:
    type: DisruptionType
    target_entity_id: str
    start_time: int
    duration: int
    severity: float = 1.0

    @property
    def end_time(self) -> int:
        return self.start_time + self.duration


@dataclass
class Scenario:
    scenario_id: str
    stations: List[Station] = field(default_factory=list)
    sections: List[RailSection] = field(default_factory=list)
    routes: List[Route] = field(default_factory=list)
    rakes: List[Rake] = field(default_factory=list)
    demands: List[FreightDemand] = field(default_factory=list)
    yards: List[Yard] = field(default_factory=list)
    schedule: List[ScheduleLeg] = field(default_factory=list)
    disruption: Optional[Disruption] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Scenario":
        return cls(
            scenario_id=payload["scenario_id"],
            stations=[Station(**x) for x in payload.get("stations", [])],
            sections=[RailSection(**x) for x in payload.get("sections", [])],
            routes=[Route(**x) for x in payload.get("routes", [])],
            rakes=[Rake(**x) for x in payload.get("rakes", [])],
            demands=[FreightDemand(**x) for x in payload.get("demands", [])],
            yards=[Yard(**x) for x in payload.get("yards", [])],
            schedule=[ScheduleLeg(**x) for x in payload.get("schedule", [])],
            disruption=(Disruption(**payload["disruption"]) if payload.get("disruption") else None),
        )
