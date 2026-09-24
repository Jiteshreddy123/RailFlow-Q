"""OR-Tools CP-SAT solver for the first working RailFlow-Q recovery model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple
import json

from ortools.sat.python import cp_model

from .model import AssignmentOption, OptimizationModel
from .types import Scenario
from .validator import validate_schedule
from .objective import ObjectiveWeights, calculate_objective_breakdown
import math


@dataclass(frozen=True)
class SolverResult:
    solver: str
    status: str
    valid: bool
    objective_value: float | None = None
    metrics: Dict[str, float] = field(default_factory=dict)
    assignments: List[dict] = field(default_factory=list)
    routes: List[dict] = field(default_factory=list)
    schedule: List[dict] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    message: str | None = None
    solve_time_s: float | None = None
    solver_objective_value: float | None = None
    objective_match: bool | None = None
    objective_breakdown: Dict[str, float] = field(default_factory=dict)


def _planned_details(scenario: Scenario) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, int]]:
    """Recover the current plan as demand -> rake/route/planned-arrival maps."""
    demand_rake: Dict[str, str] = {}
    demand_route: Dict[str, str] = {}
    demand_arrival: Dict[str, int] = {}

    for leg in scenario.schedule:
        demand_rake.setdefault(leg.demand_id, leg.rake_id)
        demand_route.setdefault(leg.demand_id, leg.route_id)
        demand_arrival[leg.demand_id] = max(demand_arrival.get(leg.demand_id, 0), leg.end)

    return demand_rake, demand_route, demand_arrival


def _load_config() -> dict:
    path = Path(__file__).resolve().parents[1] / "config" / "optimization.json"
    return json.loads(path.read_text(encoding="utf-8"))


def solve_with_cp_sat(scenario: Scenario, model: OptimizationModel, time_limit_s: float | None = None) -> SolverResult:
    """Solve the compact full-scenario recovery model with CP-SAT.

    The model uses assignment booleans plus optional section/yard intervals.
    Section capacity is handled with NoOverlap/Cumulative, while a blocked
    section is handled with a before/after disjunction.
    """
    cfg = _load_config()
    horizon = int(cfg.get("time_horizon_minutes", 360))
    weights = cfg.get("objective_weights", {})
    time_limit = float(time_limit_s if time_limit_s is not None else cfg.get("demo_time_limit_seconds", 15))
    headway = int(cfg.get("headway_minutes", 2))

    cp = cp_model.CpModel()
    section_index = {s.id: s for s in scenario.sections}
    demand_index = {d.id: d for d in scenario.demands}
    rake_index = {r.id: r for r in scenario.rakes}
    route_index = {r.id: r for r in scenario.routes}

    planned_rake, planned_route, planned_arrival = _planned_details(scenario)

    # Assignment decision: one option = one rake/demand/route combination.
    x: Dict[Tuple[str, str, str], cp_model.IntVar] = {}
    for option in model.assignment_options:
        name = f"assign_{option.rake_id}_{option.demand_id}_{option.route_id}"
        x[(option.rake_id, option.demand_id, option.route_id)] = cp.NewBoolVar(name)

    for demand_id in model.demand_ids:
        vars_for_demand = [v for (r, d, route), v in x.items() if d == demand_id]
        if not vars_for_demand:
            return SolverResult(
                solver="classical_cp_sat",
                status="INFEASIBLE",
                valid=False,
                message=f"No assignment option exists for demand {demand_id}.",
            )
        cp.AddExactlyOne(vars_for_demand)

    for rake_id in model.rake_ids:
        vars_for_rake = [v for (r, d, route), v in x.items() if r == rake_id]
        if vars_for_rake:
            cp.AddAtMostOne(vars_for_rake)

    # Section and yard resource intervals.
    section_travel_intervals: Dict[str, List[cp_model.IntervalVar]] = {s.id: [] for s in scenario.sections}
    section_resource_intervals: Dict[str, List[cp_model.IntervalVar]] = {s.id: [] for s in scenario.sections}
    yard_intervals: Dict[str, List[cp_model.IntervalVar]] = {y.id: [] for y in scenario.yards}

    option_legs: Dict[Tuple[str, str, str], List[Tuple[str, cp_model.IntVar, cp_model.IntVar, cp_model.IntervalVar, cp_model.IntervalVar]]] = {}
    wait_terms: List[cp_model.IntVar] = []
    delay_vars: List[cp_model.IntVar] = []
    reallocation_vars: List[cp_model.IntVar] = []
    route_change_vars: List[cp_model.IntVar] = []
    yard_load_terms: List[cp_model.IntVar] = []

    for option in model.assignment_options:
        key = (option.rake_id, option.demand_id, option.route_id)
        present = x[key]
        rake = rake_index[option.rake_id]
        demand = demand_index[option.demand_id]
        route = route_index[option.route_id]
        legs: List[Tuple[str, cp_model.IntVar, cp_model.IntVar, cp_model.IntervalVar, cp_model.IntervalVar]] = []

        previous_end = None
        for idx, section_id in enumerate(route.sections):
            section = section_index[section_id]
            start = cp.NewIntVar(0, horizon, f"start_{option.rake_id}_{option.demand_id}_{option.route_id}_{idx}")
            actual_end = cp.NewIntVar(0, horizon, f"end_{option.rake_id}_{option.demand_id}_{option.route_id}_{idx}")
            resource_end = cp.NewIntVar(0, horizon + headway, f"resource_end_{option.rake_id}_{option.demand_id}_{option.route_id}_{idx}")

            cp.Add(start == 0).OnlyEnforceIf(present.Not())
            cp.Add(actual_end == 0).OnlyEnforceIf(present.Not())
            cp.Add(start <= horizon * present)
            cp.Add(actual_end <= horizon * present)

            duration = int(section.travel_time)
            travel_interval = cp.NewOptionalIntervalVar(
                start, duration, actual_end, present,
                f"travel_{option.rake_id}_{option.demand_id}_{option.route_id}_{section_id}",
            )
            resource_interval = cp.NewOptionalIntervalVar(
                start, duration + headway, resource_end, present,
                f"resource_{option.rake_id}_{option.demand_id}_{option.route_id}_{section_id}",
            )
            section_travel_intervals[section_id].append(travel_interval)
            section_resource_intervals[section_id].append(resource_interval)
            legs.append((section_id, start, actual_end, travel_interval, resource_interval))

            if previous_end is not None:
                cp.Add(start >= previous_end).OnlyEnforceIf(present)
                gap = cp.NewIntVar(0, horizon, f"wait_{option.rake_id}_{option.demand_id}_{option.route_id}_{idx}")
                cp.Add(gap == start - previous_end).OnlyEnforceIf(present)
                cp.Add(gap == 0).OnlyEnforceIf(present.Not())
                wait_terms.append(gap)
            previous_end = actual_end

            # A blocked section requires the train to be completely before or after the closure.
            disruption = scenario.disruption
            if disruption and disruption.type == "section_blocked" and disruption.target_entity_id == section_id:
                before = cp.NewBoolVar(f"before_block_{option.rake_id}_{option.demand_id}_{option.route_id}_{section_id}")
                after = cp.NewBoolVar(f"after_block_{option.rake_id}_{option.demand_id}_{option.route_id}_{section_id}")
                cp.Add(before + after == present)
                cp.Add(actual_end <= disruption.start_time).OnlyEnforceIf(before)
                cp.Add(start >= disruption.end_time).OnlyEnforceIf(after)

        option_legs[key] = legs

        # First section cannot start before the rake is available.
        if legs:
            cp.Add(legs[0][1] >= rake.availability_time).OnlyEnforceIf(present)

            planned = planned_arrival.get(demand.id, demand.deadline)
            delay = cp.NewIntVar(0, horizon, f"delay_{option.rake_id}_{option.demand_id}_{option.route_id}")
            final_end = legs[-1][2]
            cp.AddMaxEquality(delay, [final_end - planned, 0])
            cp.Add(delay <= horizon * present)
            delay_vars.append(delay)

            initial_wait = cp.NewIntVar(0, horizon, f"initial_wait_{option.rake_id}_{option.demand_id}_{option.route_id}")
            cp.Add(initial_wait == legs[0][1] - rake.availability_time).OnlyEnforceIf(present)
            cp.Add(initial_wait == 0).OnlyEnforceIf(present.Not())
            wait_terms.append(initial_wait)

        reallocation = cp.NewBoolVar(f"reallocation_{option.rake_id}_{option.demand_id}_{option.route_id}")
        if planned_rake.get(demand.id) == option.rake_id:
            cp.Add(reallocation == 0)
        else:
            cp.Add(reallocation == present)
        reallocation_vars.append(reallocation)

        route_change = cp.NewBoolVar(f"route_change_{option.rake_id}_{option.demand_id}_{option.route_id}")
        if planned_route.get(demand.id) == option.route_id:
            cp.Add(route_change == 0)
        else:
            cp.Add(route_change == present)
        route_change_vars.append(route_change)

        # Yard dwell intervals occur when a route reaches a yard station.
        for section_id, start, end, _, _ in legs:
            destination = section_index[section_id].destination
            for yard in scenario.yards:
                if yard.station_id != destination:
                    continue
                ystart = end
                yend = cp.NewIntVar(0, horizon + yard.dwell_time, f"yard_end_{option.rake_id}_{option.demand_id}_{option.route_id}_{yard.id}_{section_id}")
                yard_interval = cp.NewOptionalIntervalVar(
                    ystart, int(yard.dwell_time), yend, present,
                    f"yard_{option.rake_id}_{option.demand_id}_{option.route_id}_{yard.id}_{section_id}",
                )
                yard_intervals[yard.id].append(yard_interval)
                yard_load_terms.append(int(yard.dwell_time) * present)

    # Resource capacity.
    for section in scenario.sections:
        if section.capacity <= 1:
            cp.AddNoOverlap(section_resource_intervals[section.id])
        else:
            cp.AddCumulative(section_resource_intervals[section.id], [1] * len(section_resource_intervals[section.id]), section.capacity)

    for yard in scenario.yards:
        cp.AddCumulative(yard_intervals[yard.id], [1] * len(yard_intervals[yard.id]), yard.track_capacity)

    # Deadline is a soft objective term via delay, but make severe misses visible through metrics.
    objective_scale = 100
    objective_terms = []
    objective_terms += [int(round(weights.get("delay", 1.0) * objective_scale)) * v for v in delay_vars]
    objective_terms += [int(round(weights.get("waiting", 1.0) * objective_scale)) * v for v in wait_terms]
    objective_terms += [int(round(weights.get("reallocation", 8.0) * objective_scale)) * v for v in reallocation_vars]
    route_change_weight = weights.get("route_change", weights.get("conflicts", 5.0))
    objective_terms += [int(round(route_change_weight * objective_scale)) * v for v in route_change_vars]
    objective_terms += [int(round(weights.get("yard_congestion", 1.0) * objective_scale)) * v for v in yard_load_terms]
    cp.Minimize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit

    # Demo mode is deterministic by default so judges see the same result
    # every time the supplied scenario is executed. Development can restore
    # multi-worker search through config.
    deterministic_demo = bool(cfg.get("deterministic_demo", True))
    if deterministic_demo:
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = int(cfg.get("random_seed", 42))
        solver.parameters.randomize_search = False
    else:
        solver.parameters.num_search_workers = int(cfg.get("num_search_workers", 8))
    status = solver.Solve(cp)
    status_name = solver.StatusName(status)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return SolverResult(
            solver="classical_cp_sat",
            status=status_name,
            valid=False,
            message="No feasible recovery plan found within the configured time limit.",
            solve_time_s=solver.WallTime(),
        )

    assignments: List[dict] = []
    routes: List[dict] = []
    schedule: List[dict] = []
    total_delay = 0
    total_wait = 0
    reallocations = 0
    route_changes = 0
    yard_load = 0

    for option in model.assignment_options:
        key = (option.rake_id, option.demand_id, option.route_id)
        if solver.Value(x[key]) != 1:
            continue
        reallocated = planned_rake.get(option.demand_id) != option.rake_id
        changed_route = planned_route.get(option.demand_id) != option.route_id
        assignments.append({
            "rake_id": option.rake_id,
            "demand_id": option.demand_id,
            "route_id": option.route_id,
            "reallocated": reallocated,
        })
        routes.append({
            "route_id": option.route_id,
            "rake_id": option.rake_id,
            "sections": list(route_index[option.route_id].sections),
        })
        reallocations += int(reallocated)
        route_changes += int(changed_route)
        for section_id, start, end, _, _ in option_legs[key]:
            s = solver.Value(start)
            e = solver.Value(end)
            schedule.append({
                "rake_id": option.rake_id,
                "demand_id": option.demand_id,
                "route_id": option.route_id,
                "section": section_id,
                "start": s,
                "end": e,
                "present": True,
            })
        final_end = max(item["end"] for item in schedule if item["rake_id"] == option.rake_id and item["demand_id"] == option.demand_id)
        total_delay += max(0, final_end - planned_arrival.get(option.demand_id, demand_index[option.demand_id].deadline))

    total_wait = sum(
        max(0, schedule[i + 1]["start"] - schedule[i]["end"])
        for i in range(len(schedule) - 1)
        if schedule[i]["rake_id"] == schedule[i + 1]["rake_id"] and schedule[i]["demand_id"] == schedule[i + 1]["demand_id"]
    )


    validation = validate_schedule(scenario, [
        __import__("optimization.types", fromlist=["ScheduleLeg"]).ScheduleLeg(**leg)
        for leg in schedule
    ])

    solver_objective_value = solver.ObjectiveValue() / objective_scale

    objective_weights = ObjectiveWeights(
        delay=float(weights.get("delay", 1.0)),
        waiting=float(weights.get("waiting", 1.0)),
        conflicts=float(weights.get("conflicts", 5.0)),
        yard_congestion=float(weights.get("yard_congestion", 1.0)),
        idle_time=float(weights.get("idle_time", 0.0)),
        reallocation=float(weights.get("reallocation", 8.0)),
        route_change=float(weights.get("route_change", weights.get("conflicts", 5.0))),
    )
    objective_breakdown = calculate_objective_breakdown(
        scenario, assignments, schedule, objective_weights
    )
    objective_match = math.isclose(
        float(solver_objective_value),
        objective_breakdown.weighted_total,
        rel_tol=0.0,
        abs_tol=1e-6,
    )

    metrics = {
        "delay": objective_breakdown.delay,
        "waiting": objective_breakdown.waiting,
        "reallocations": objective_breakdown.reallocation,
        "route_changes": objective_breakdown.route_changes,
        "conflicts": objective_breakdown.conflicts,
        "yard_load": objective_breakdown.yard_load,
        "idle_time": objective_breakdown.idle_time,
        "solve_time_s": float(solver.WallTime()),
    }

    return SolverResult(
        solver="classical_cp_sat",
        status=status_name,
        valid=validation.valid,
        objective_value=objective_breakdown.weighted_total,
        metrics=metrics,
        assignments=assignments,
        routes=routes,
        schedule=schedule,
        violations=validation.violations,
        message=(
            None
            if validation.valid and objective_match
            else (
                "Solver returned a schedule that failed validation."
                if not validation.valid
                else "Objective accounting mismatch between solver and decoded result."
            )
        ),
        solve_time_s=solver.WallTime(),
        solver_objective_value=float(solver_objective_value),
        objective_match=objective_match,
        objective_breakdown=objective_breakdown.as_dict(),
    )
