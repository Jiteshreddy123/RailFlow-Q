from pathlib import Path
import json

from optimization.classical_solver import solve_with_cp_sat
from optimization.model import build_optimization_model
from optimization.objective import ObjectiveWeights, calculate_objective_breakdown
from optimization.types import Route, Scenario, ScheduleLeg
from optimization.validator import validate_schedule

ROOT = Path(__file__).resolve().parents[1]


def load_scenario() -> Scenario:
    payload = json.loads((ROOT / "data" / "scenarios" / "demo_scenario.json").read_text(encoding="utf-8"))
    return Scenario.from_dict(payload)


def test_cpsat_finds_recovery_solution():
    scenario = load_scenario()
    model = build_optimization_model(scenario)
    result = solve_with_cp_sat(scenario, model, time_limit_s=10)

    assert result.status in {"OPTIMAL", "FEASIBLE"}
    assert result.valid is True
    assert len(result.assignments) == len(scenario.demands)
    assert result.schedule
    assert result.objective_match is True


def test_cpsat_does_not_use_blocked_section_during_closure():
    scenario = load_scenario()
    model = build_optimization_model(scenario)
    result = solve_with_cp_sat(scenario, model, time_limit_s=10)
    assert result.valid

    disruption = scenario.disruption
    assert disruption is not None
    for leg in result.schedule:
        if leg["section"] == disruption.target_entity_id:
            assert not (leg["start"] < disruption.end_time and disruption.start_time < leg["end"])


def test_validator_accepts_solver_schedule():
    scenario = load_scenario()
    model = build_optimization_model(scenario)
    result = solve_with_cp_sat(scenario, model, time_limit_s=10)
    schedule = [ScheduleLeg(**x) for x in result.schedule]
    validation = validate_schedule(scenario, schedule)
    assert validation.valid, validation.violations


def test_disconnected_route_is_excluded_from_assignment_options():
    scenario = load_scenario()
    scenario.routes.append(
        Route(
            id="R_BAD",
            origin="ST1",
            destination="ST5",
            sections=["S1", "S4"],  # ST2 -> ST4 jump: disconnected
            travel_time=40,
        )
    )
    model = build_optimization_model(scenario)
    assert not any(option.route_id == "R_BAD" for option in model.assignment_options)


def test_valid_routes_remain_available_after_connectivity_check():
    scenario = load_scenario()
    model = build_optimization_model(scenario)
    assert {option.route_id for option in model.assignment_options} == {"R_A", "R_B", "R_C"}


def test_conflicts_are_not_route_changes():
    scenario = load_scenario()
    model = build_optimization_model(scenario)
    result = solve_with_cp_sat(scenario, model, time_limit_s=10)

    assert result.valid
    assert result.metrics["conflicts"] == 0.0
    assert result.metrics["route_changes"] >= 0.0


def test_yard_load_is_counted_per_selected_rake_not_unique_route():
    scenario = load_scenario()
    model = build_optimization_model(scenario)
    result = solve_with_cp_sat(scenario, model, time_limit_s=10)

    assert result.valid
    # Current deterministic demo selects R2 and R3 on R_B and R1 on R_C.
    # R_B contributes Y1 dwell twice; R_C contributes Y1 + Y2 dwell once.
    # With 15 minutes per dwell this is 60 minutes of total yard load.
    assert result.metrics["yard_load"] == 60.0


def test_objective_breakdown_reports_zero_hard_conflicts_for_valid_solution():
    scenario = load_scenario()
    model = build_optimization_model(scenario)
    result = solve_with_cp_sat(scenario, model, time_limit_s=10)
    breakdown = calculate_objective_breakdown(
        scenario, result.assignments, result.schedule, ObjectiveWeights(route_change=5.0)
    )
    assert breakdown.conflicts == 0.0
    assert breakdown.route_changes == result.metrics["route_changes"]

