# RailFlow-Q — Person 1: Optimization & Quantum Lead

RailFlow-Q is a quantum-assisted decision-support prototype for freight railway disruption recovery. This README describes **Person 1's territory**, the optimization architecture, the IBM/Qiskit quantum track, and the integration contract required from the other team members.

> **Project boundary:** RailFlow-Q is a prototype decision-support layer. It does not control trains, replace signalling or traffic-control systems, or claim access to confidential railway operational data.

## 1. Person 1 Scope

Person 1 owns the optimization intelligence of RailFlow-Q:

```text
Railway Scenario
      ↓
Optimization Formulation
      ↓
Classical CP-SAT Baseline
      ↓
Disruption Recovery
      ↓
IBM/Qiskit Quantum Formulation
      ↓
QUBO → QAOA
      ↓
Decode
      ↓
Validate
      ↓
Compare
      ↓
Return Decision-Support Result
```

### Core optimization decisions

- **Rake allocation:** which available rake serves which freight demand.
- **Route / path selection:** which feasible route the assigned rake should use.
- **Timing:** when the rake occupies each railway section.
- **Yard sequencing:** how rakes use limited yard capacity.
- **Disruption recovery:** reroute, reschedule, resequence, or reassign affected operations.

The project architecture defines these as the core railway decisions for the optimization engine. fileciteturn0file0L17-L26

## 2. Person 1 Repository Territory

```text
optimization/
├── model.py
├── constraints.py
├── objective.py
├── classical_solver.py
├── validator.py
├── comparator.py
│
└── quantum/
    ├── problem_encoder.py
    ├── qubo_builder.py
    ├── qaoa_solver.py
    ├── aer_solver.py
    ├── ibm_solver.py
    └── decoder.py
```

### Responsibilities

| File | Responsibility |
|---|---|
| `model.py` | Solver-neutral railway optimization model and assignment-option generation |
| `constraints.py` | Reusable feasibility / constraint logic |
| `objective.py` | Shared business-level objective and metric accounting |
| `classical_solver.py` | OR-Tools CP-SAT implementation |
| `validator.py` | Common validation of returned schedules |
| `comparator.py` | Classical vs quantum/hybrid result comparison |
| `quantum/problem_encoder.py` | Extract compact quantum-worthy recovery decisions |
| `quantum/qubo_builder.py` | Build the QUBO / binary formulation |
| `quantum/qaoa_solver.py` | QAOA execution logic |
| `quantum/aer_solver.py` | Qiskit Aer local/noisy simulation |
| `quantum/ibm_solver.py` | IBM Quantum Runtime execution boundary |
| `quantum/decoder.py` | Convert quantum bitstrings into railway decisions |

The supplied architecture identifies the optimization model, CP-SAT solver, quantum/hybrid formulation, validator, and comparator as Person 1 deliverables. fileciteturn0file0L73-L81

## 3. Classical Optimization

The classical baseline uses **OR-Tools CP-SAT** and currently supports:

- Boolean assignment decisions
- Optional interval variables
- Integer timing
- `NoOverlap` for capacity-1 resources
- `Cumulative` for multi-capacity resources
- Rake availability
- Route feasibility
- Disruption avoidance
- Configurable recovery costs
- Deterministic demo execution
- Solver-independent objective accounting

The classical solver is the reference implementation for the quantum work. The supplied project plan explicitly puts the classical working system before the quantum/hybrid phase. fileciteturn0file0L96-L104

## 4. Validation

Every solver result must use the common validation path:

```text
Solver Result
     ↓
Validator
     ↓
VALID    → continue
INVALID  → reject / repair / re-solve
```

Validation covers the railway feasibility layer, including:

- section capacity
- yard capacity
- rake availability
- route feasibility
- timing / headway
- demand completeness
- disruption avoidance
- objective consistency

Invalid solutions must not be forwarded as planner-ready recovery plans. fileciteturn0file0L58-L60

## 5. IBM / Qiskit Quantum Track

The quantum implementation is centered on the IBM ecosystem.

Target stack:

```text
Qiskit
Qiskit Optimization
Qiskit Algorithms
Qiskit Aer
qiskit-ibm-runtime
IBM Quantum hardware
```

The installed development environment has been verified as:

```text
Qiskit              2.5.2
Qiskit Aer          0.17.2
Qiskit Algorithms   0.4.0
IBM Runtime         0.49.0
```

### Quantum strategy

We do not try to translate the entire interval-based railway scheduling model directly into a quantum circuit.

Instead:

```text
Full Railway Recovery Problem
              ↓
Classical preprocessing / candidate generation
              ↓
Affected rakes
              ↓
Feasible recovery options
              ↓
Compact binary decision problem
              ↓
Qiskit QuadraticProgram
              ↓
QUBO
              ↓
QAOA
       ┌──────┴──────┐
       ↓             ↓
   Qiskit Aer    IBM Quantum
   simulation     Runtime / QPU
       └──────┬──────┘
              ↓
          Bitstrings
              ↓
            Decoder
              ↓
       Common Validator
              ↓
          Comparator
```

The first quantum target is expected to be the recovery-option selection problem: choose one feasible recovery option for each affected rake while minimizing recovery cost and avoiding incompatible combinations.

Conceptually:

\[
x_{r,o} \in \{0,1\}
\]

where `x[r,o] = 1` means rake `r` selects recovery option `o`.

The project must not assume quantum advantage. Any performance or solution-quality claim must come from measured experiments. fileciteturn0file0L54-L60 fileciteturn0file0L118-L124

## 6. Common Solver Contract

Classical and quantum paths should ultimately produce the same business-level result shape:

```text
SolverResult
    ├── solver
    ├── status
    ├── valid
    ├── objective_value
    ├── metrics
    ├── assignments
    ├── routes
    ├── schedule
    └── violations
```

The frontend and backend should consume this domain-level contract rather than solver-specific internals.

Quantum internals that stay inside the optimization layer:

```text
QUBO coefficients
qubit indices
Hamiltonians
raw circuits
transpiled circuits
backend topology
raw sampling distributions
QAOA parameters
```

## 7. What Person 1 Expects From Person 2 — Backend & Data

Person 2 owns the application backbone, including FastAPI, PostgreSQL, synthetic railway data, scenario management, disruption APIs, and the connection into the optimization engine. fileciteturn0file0L82-L88

### Person 1 needs

A canonical scenario object containing:

```text
stations
rail sections
routes
yards
rakes
freight demands
current schedule
yard occupancy
disruption state
```

Representative input:

```json
{
  "scenario_id": "DEMO-001",
  "network": {
    "stations": [],
    "sections": [],
    "routes": [],
    "yards": []
  },
  "rakes": [],
  "demands": [],
  "current_schedule": [],
  "yard_occupancy": [],
  "disruption": {
    "type": "section_blocked",
    "target_entity_id": "S3",
    "start_time": 0,
    "duration": 120,
    "severity": 1.0
  },
  "solver": "classical"
}
```

### Backend integration expectations

```text
✅ Stable scenario schema
✅ Stable disruption schema
✅ Network / rake / demand / yard data
✅ Current schedule
✅ Deterministic demo scenario
✅ Optimization API contract
✅ Backend calls optimization engine
✅ No duplicated optimization logic inside FastAPI
```

Person 1 does not expect Person 2 to implement QUBO or QAOA.

## 8. What Person 1 Expects From Person 3 — Frontend & Demo

Person 3 owns the React dashboard, network and schedule visualization, disruption controls, results display, screenshots/README, and the demo flow. fileciteturn0file0L89-L95

### Person 1 needs the UI to display

```text
Scenario state
Disruption state
Affected rakes
Assignments
Routes
Schedule
Validation status
Objective
Solver metrics
Classical vs quantum comparison
```

The frontend should visualize:

```text
Network
 ├── stations
 ├── sections
 ├── yards
 └── disruption

Rakes
 ├── current positions
 ├── affected status
 └── selected recovery action

Schedule
 ├── normal schedule
 └── recovery schedule

Comparison
 ├── objective
 ├── delay
 ├── waiting
 ├── reallocations
 ├── route changes
 ├── conflicts
 ├── yard load
 ├── solve time
 └── validity
```

### Frontend integration expectations

```text
✅ Display validated solver results
✅ Display before / after schedule
✅ Display recovery alternatives
✅ Display classical vs quantum/hybrid comparison
✅ Keep optimization logic out of React
✅ Treat assignments, routes and schedule as separate data
✅ Do not reverse-engineer solver decisions from raw interval order
```

## 9. Integration Boundary

```text
                 Person 2
            Backend / Data
                   │
                   │ Canonical Scenario JSON
                   ▼
        ┌──────────────────────────┐
        │        Person 1          │
        │   Optimization Engine   │
        │                          │
        │ CP-SAT / Qiskit / IBM   │
        │ Validator / Comparator  │
        └────────────┬─────────────┘
                     │
                     │ Validated Solver Result
                     ▼
                 Person 3
              Frontend / Demo
```

The intended architecture is:

```text
Backend
   ↓
Optimization Engine
   ↓
Solver
   ↓
Validator
   ↓
Comparator
   ↓
Backend
   ↓
Frontend
```

## 10. Development Roadmap

```text
Phase 1  Problem + Data
   ↓
Phase 2  Classical Working System
   ↓
Phase 3  Disruption Recovery
   ↓
Phase 4  IBM/Qiskit Quantum Track
   ↓
Phase 5  Validation + Integration + Demo Polish
```

Current Person 1 position:

```text
✅ Repository setup
✅ Python environment
✅ OR-Tools
✅ Qiskit environment
✅ Domain model
✅ Synthetic demo scenario
✅ Disruption model
✅ CP-SAT baseline
✅ Validator
✅ Objective accounting
✅ Classical hardening
✅ QAOA smoke test

⬜ Recovery-option generator
⬜ Qiskit QuadraticProgram formulation
⬜ QUBO
⬜ RailFlow-Q QAOA solver
⬜ Aer execution of the railway problem
⬜ IBM Quantum Runtime execution
⬜ Quantum decoder
⬜ Comparator integration
⬜ Backend integration
⬜ Frontend integration
```

## 11. Current Project Result

The current classical demonstration has reached:

```text
STATUS: OPTIMAL
VALID: True
OBJECTIVE: 150.0
VIOLATIONS: []
```

Current metrics:

```text
delay           = 0
waiting         = 64
reallocations   = 2
route_changes   = 2
conflicts       = 0
yard_load       = 60
idle_time       = 0
```

The local Qiskit smoke test has also completed successfully before applying QAOA to the railway problem.

---

# Updates

The detailed development history is maintained separately in [`UPDATES.md`](UPDATES.md).

<details>
<summary><strong>Latest Update — Classical Foundation + IBM/Qiskit Readiness</strong></summary>

The current classical optimization model has been hardened and validated.

```text
10 tests passed
CP-SAT status: OPTIMAL
Solution valid: True
Objective: 150.0
Violations: 0
```

The objective accounting now separates:

```text
route_changes
reallocations
conflicts
```

instead of treating route changes as physical conflicts.

The route validation and yard-load accounting were also hardened.

The local IBM/Qiskit environment is verified:

```text
Qiskit              2.5.2
Qiskit Aer          0.17.2
Qiskit Algorithms   0.4.0
IBM Runtime         0.49.0
```

A standalone QAOA smoke test completed successfully:

```text
fval=0.0
x=1.0
y=1.0
status=SUCCESS
```

**Next milestone:**

```text
Affected Rakes
      ↓
Recovery Options
      ↓
Binary Variables
      ↓
Qiskit QuadraticProgram
      ↓
QUBO
      ↓
QAOA
      ↓
Aer
      ↓
IBM Quantum Runtime
      ↓
Decoder
      ↓
Common Validator
      ↓
Comparator
```

[View the complete update history →](UPDATES.md)

</details>
