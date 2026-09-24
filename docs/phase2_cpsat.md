# RailFlow-Q Phase 2 — CP-SAT Baseline

This milestone turns the Phase 1 solver-neutral domain model into a working classical recovery optimizer.

## Model

- Binary assignment variable for each `(rake, demand, route)` option.
- Exactly one option per demand.
- At most one demand per rake.
- Optional section intervals linked directly to the assignment literal.
- `NoOverlap` for capacity-1 sections and `Cumulative` for higher-capacity resources.
- Optional yard dwell intervals with yard-track capacity.
- Section-block disruption handled by a before/after disjunction.
- Configurable time horizon and solve-time limit.

## Objective

The prototype minimizes weighted delay, waiting, route-change conflict cost, and reallocation cost. Yard dwell is represented in the returned metrics. The weights remain configurable so the demo can later expose sensitivity experiments.

## Important scope boundary

The classical model is intentionally the trustworthy baseline. The later Qiskit formulation should consume the same scenario but use a compact binary representation suited to QUBO/QAOA rather than attempting a literal translation of CP-SAT interval variables.
