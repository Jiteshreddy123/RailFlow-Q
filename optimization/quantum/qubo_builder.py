"""QUBO builder placeholder for the IBM/Qiskit track."""

from __future__ import annotations

from typing import Any, Sequence

from .problem_encoder import QuantumVariable


def build_quadratic_program(variables: Sequence[QuantumVariable]) -> Any:
    """Construct the future Qiskit Optimization QuadraticProgram.

    The actual objective and penalty terms are added only after the railway
    constraints are frozen in the classical model.
    """

    raise NotImplementedError(
        "Qiskit QuadraticProgram construction begins after the CP-SAT model and "
        "constraint semantics are locked."
    )
