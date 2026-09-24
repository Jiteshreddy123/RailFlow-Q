# RailFlow-Q Phase 1

## Scope

Phase 1 freezes the solver-neutral railway data structures before interval variables or quantum-specific representations are introduced.

## Core entities

- Station
- RailSection
- Route
- Rake
- FreightDemand
- Yard
- ScheduleLeg
- Disruption
- Scenario

## Design boundary

The domain model is shared by all future solvers. OR-Tools and Qiskit should not invent independent definitions of the railway network.

The classical model can use interval/cumulative reasoning. The quantum path will use a separate compact binary encoding suitable for Qiskit Optimization and QAOA.
