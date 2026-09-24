# RailFlow-Q — Person 1 Update Log

This file is the chronological development log for Person 1's Optimization & Quantum work.

Each update is kept collapsible so the repository homepage stays readable while the technical history remains available.

---

<details>
<summary><strong>Update 1 — Classical Optimization Foundation + IBM/Qiskit Readiness</strong></summary>

## Scope

Established the first working optimization foundation and verified the IBM/Qiskit environment before beginning the real quantum formulation.

## Classical optimization

Implemented and validated:

```text
Domain model
    ↓
Assignment options
    ↓
CP-SAT scheduling model
    ↓
Recovery schedule
    ↓
Common validator
    ↓
Objective accounting
```

The hardened model supports assignment decisions, route selection, integer timing, section resource constraints, yard capacity, rake availability, disruption avoidance, and configurable recovery costs.

## Hardening changes

The model was reviewed and hardened in four areas:

### Route connectivity

Routes are checked as connected section sequences rather than relying only on route-level origin/destination metadata.

### Conflict semantics

`conflicts` is no longer treated as a synonym for `route_changes`.

The result now distinguishes:

```text
conflicts      = actual physical / timing conflict metric
route_changes  = recovery route changes
reallocations  = demand/rake assignment changes
```

### Yard accounting

Yard load is accounted for per selected recovery operation instead of using a route-level shortcut.

### Objective consistency

The returned objective is recomputed from the decoded domain result so solver accounting can be checked independently.

## Current test result

```text
10 passed in 3.61s
```

## Current CP-SAT result

```text
STATUS: OPTIMAL
VALID: True
OBJECTIVE: 150.0
VIOLATIONS: []
```

Metrics:

```text
delay           = 0
waiting         = 64
reallocations   = 2
route_changes   = 2
conflicts       = 0
yard_load       = 60
idle_time       = 0
```

## Objective accounting

```text
waiting             64
reallocation cost   16
route-change cost   10
yard load            60
delay                 0
                    ----
TOTAL               150
```

## IBM/Qiskit environment

Verified locally:

```text
Qiskit              2.5.2
Qiskit Aer          0.17.2
Qiskit Algorithms   0.4.0
IBM Runtime         0.49.0
```

## QAOA smoke test

A tiny binary optimization problem was successfully solved using QAOA and the local Qiskit sampler:

```text
fval=0.0
x=1.0
y=1.0
status=SUCCESS
```

This verified that the local Qiskit/QAOA toolchain is functional before introducing the railway problem.

## Result

The classical reference model and the local quantum development environment are ready for the next stage.

## Next

```text
Affected Rakes
      ↓
Recovery Options
      ↓
Binary Decision Model
      ↓
Qiskit QuadraticProgram
      ↓
QUBO
      ↓
QAOA
```

</details>

---

<details>
<summary><strong>Future Update 2 — Recovery Option Generator</strong></summary>

Status: **Not started**

Planned work:

```text
Disruption
   ↓
Affected rakes
   ↓
Generate feasible recovery options
   ↓
Score options
   ↓
Expose compact candidate set
```

</details>

<details>
<summary><strong>Future Update 3 — Qiskit QuadraticProgram + QUBO</strong></summary>

Status: **Not started**

Planned work:

```text
Recovery options
      ↓
Binary variables
      ↓
Qiskit QuadraticProgram
      ↓
QUBO
```

</details>

<details>
<summary><strong>Future Update 4 — RailFlow-Q QAOA + Aer</strong></summary>

Status: **Not started**

Planned work:

```text
QUBO
  ↓
QAOA
  ↓
Qiskit Aer
  ↓
Bitstrings
  ↓
Decoder
```

</details>

<details>
<summary><strong>Future Update 5 — IBM Quantum Runtime</strong></summary>

Status: **Not started**

Planned work:

```text
Validated QAOA workflow
       ↓
IBM Quantum Runtime
       ↓
IBM Quantum hardware
       ↓
Samples
       ↓
Decode
       ↓
Validate
```

</details>

<details>
<summary><strong>Future Update 6 — Comparator + End-to-End Integration</strong></summary>

Status: **Not started**

Planned work:

```text
CP-SAT solution
       +
Quantum solution
       ↓
Common validator
       ↓
Common metrics
       ↓
Comparator
       ↓
Backend
       ↓
Frontend
```

</details>
