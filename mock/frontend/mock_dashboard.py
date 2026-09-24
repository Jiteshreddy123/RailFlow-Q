"""Terminal UI that mimics the future React dashboard contract."""

from __future__ import annotations

from mock.backend.scenario import load_demo_scenario, affected_rakes


def run() -> None:
    scenario = load_demo_scenario()
    print("=" * 60)
    print("RAILFLOW-Q | MOCK DASHBOARD")
    print("=" * 60)
    print(f"Scenario: {scenario.scenario_id}")
    if scenario.disruption:
        d = scenario.disruption
        print(f"Disruption: {d.type} -> {d.target_entity_id} for {d.duration} min")
        print(f"Affected rakes: {', '.join(affected_rakes(scenario)) or 'None'}")
    else:
        print("Disruption: none")
    print(f"Stations: {len(scenario.stations)}")
    print(f"Sections: {len(scenario.sections)}")
    print(f"Rakes: {len(scenario.rakes)}")
    print(f"Demands: {len(scenario.demands)}")
    print("=" * 60)


if __name__ == "__main__":
    run()
