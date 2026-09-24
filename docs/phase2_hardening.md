# Phase 2 hardening notes

Before freezing the classical baseline, RailFlow-Q separates physical feasibility from recovery cost.

- **Physical conflicts:** section overlap or sub-headway separation on capacity-1 sections. These are feasibility violations and therefore should be zero on any accepted CP-SAT solution.
- **Route changes:** a soft recovery cost that captures how much the recovery plan deviates from the planned route.
- **Reallocations:** a soft recovery cost for changing which rake serves a demand.

The quantum decoder will be evaluated with the same metric definitions. This keeps the classical and Qiskit paths comparable at the domain level.
