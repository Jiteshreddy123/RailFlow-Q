"""Common comparison data structures for solver outputs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SolverMetrics:
    objective_value: float | None
    delay: float | None
    waiting: float | None
    conflicts: float | None
    yard_congestion: float | None
    solve_time_s: float | None
    valid: bool


@dataclass(frozen=True)
class SolverComparison:
    classical: SolverMetrics | None
    quantum: SolverMetrics | None
