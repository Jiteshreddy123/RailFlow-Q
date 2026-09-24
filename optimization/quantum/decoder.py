"""Translate quantum bitstrings back into railway decisions."""

from __future__ import annotations

from typing import Mapping, Sequence

from .problem_encoder import QuantumVariable


def decode_assignment(bitstring: Mapping[str, int], variables: Sequence[QuantumVariable]):
    """Return selected assignment variables from a quantum sample."""

    return [var for var in variables if int(bitstring.get(var.name, 0)) == 1]
