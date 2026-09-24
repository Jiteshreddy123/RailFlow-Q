from pathlib import Path
import json

from optimization.constraints import validate_basic_constraints
from optimization.model import build_optimization_model
from optimization.types import Scenario
from mock.backend.scenario import affected_rakes

ROOT = Path(__file__).resolve().parents[1]


def load_scenario() -> Scenario:
    payload = json.loads(
        (ROOT / "data" / "scenarios" / "demo_scenario.json").read_text(encoding="utf-8")
    )
    return Scenario.from_dict(payload)


def test_demo_scenario_is_modelable():
    scenario = load_scenario()
    assert validate_basic_constraints(scenario) == []
    model = build_optimization_model(scenario)
    assert model.assignment_options
    assert {x.demand_id for x in model.assignment_options} == {"D1", "D2", "D3"}


def test_disruption_identifies_affected_rakes():
    scenario = load_scenario()
    assert affected_rakes(scenario) == ["R1", "R2"]
