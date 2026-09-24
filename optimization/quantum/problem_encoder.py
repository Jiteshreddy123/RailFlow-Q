"""Encode a compact recovery subproblem for Qiskit.

The quantum formulation deliberately stays separate from CP-SAT interval
variables. The goal is to choose a compact binary subproblem that can become a
QUBO and eventually a QAOA circuit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..model import OptimizationModel


@dataclass(frozen=True)
class QuantumVariable:
    name: str
    rake_id: str
    demand_id: str
    route_id: str


def build_quantum_variables(model: OptimizationModel) -> List[QuantumVariable]:
    """Create one binary variable per candidate assignment option."""

    return [
        QuantumVariable(
            name=f"x_{opt.rake_id}_{opt.demand_id}_{opt.route_id}",
            rake_id=opt.rake_id,
            demand_id=opt.demand_id,
            route_id=opt.route_id,
        )
        for opt in model.assignment_options
    ]
