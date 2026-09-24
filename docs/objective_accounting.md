# RailFlow-Q Phase 2 — Objective Accounting

The CP-SAT solver now has a solver-independent objective accounting pass.

## Measures

- `delay`: final arrival minus the original planned arrival, clipped at zero.
- `waiting`: initial wait from rake availability plus gaps between consecutive route sections.
- `reallocation`: number of selected assignments whose rake differs from the original plan.
- `route_changes`: number of selected assignments whose route differs from the original plan.
- `yard_load`: total yard dwell minutes implied by returned route sections at yard stations.
- `idle_time`: reserved for a later milestone; currently zero-weighted and not modeled.

The current Phase 2 configuration uses `conflicts` as the configured weight for the `route_changes` recovery-cost proxy. Actual section/timing conflicts remain hard feasibility constraints and are handled by the CP-SAT resource constraints plus the validator.

## Audit fields

Every successful solver result exposes:

- `objective_value`: recomputed weighted objective from the returned domain solution.
- `solver_objective_value`: CP-SAT's scaled objective converted back to the configured units.
- `objective_match`: whether those values agree within `1e-6`.
- `objective_breakdown`: unweighted and weighted component values.

This same accounting function will later be reused for decoded Qiskit / IBM solutions so the classical and quantum paths are measured under the same definitions.
