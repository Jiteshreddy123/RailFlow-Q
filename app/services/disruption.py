# app/services/disruption.py

import networkx as nx
from sqlalchemy.orm import Session
from app.models.railway import Section, Rake, Station, Yard, FreightDemand


def build_railway_graph(db: Session) -> nx.DiGraph:
    """
    Build a directed graph from all sections.
    Nodes = station IDs, Edges = sections weighted by distance_km.
    """
    G = nx.DiGraph()

    stations = db.query(Station).all()
    for s in stations:
        G.add_node(s.id, name=s.name, code=s.code)

    sections = db.query(Section).filter(Section.is_blocked == False).all()
    for sec in sections:
        G.add_edge(
            sec.from_station_id,
            sec.to_station_id,
            section_id=sec.id,
            section_name=sec.name,
            weight=sec.distance_km,
        )
        G.add_edge(
            sec.to_station_id,
            sec.from_station_id,
            section_id=sec.id,
            section_name=sec.name,
            weight=sec.distance_km,
        )

    return G


def build_graph_with_blockage(db: Session, blocked_section_id: int) -> tuple[nx.DiGraph, dict]:
    """
    Build graph with one section removed. Returns graph + blocked section metadata.
    """
    blocked = db.query(Section).filter(Section.id == blocked_section_id).first()
    if not blocked:
        raise ValueError(f"Section ID {blocked_section_id} not found.")

    blocked_info = {
        "id": blocked.id,
        "section_name": blocked.name,
        "from_station_id": blocked.from_station_id,
        "to_station_id": blocked.to_station_id,
    }

    G = build_railway_graph(db)

    if G.has_edge(blocked.from_station_id, blocked.to_station_id):
        G.remove_edge(blocked.from_station_id, blocked.to_station_id)
    if G.has_edge(blocked.to_station_id, blocked.from_station_id):
        G.remove_edge(blocked.to_station_id, blocked.from_station_id)

    return G, blocked_info


def get_station_name(db: Session, station_id: int) -> str:
    st = db.query(Station).filter(Station.id == station_id).first()
    return st.name if st else str(station_id)


def find_affected_rakes(db: Session, blocked_section_id: int) -> list[dict]:
    """
    Find all rakes whose path from current_station to their freight demand destination
    passes through the blocked section.

    Since Rake has no destination_station_id, we derive destination from FreightDemand:
    - Match rakes to freight demands where the demand's origin_station_id == rake's current_station_id
    - If no demand matches, skip the rake (no assigned trip)
    """
    blocked = db.query(Section).filter(Section.id == blocked_section_id).first()
    if not blocked:
        raise ValueError(f"Section ID {blocked_section_id} not found.")

    G_full, _ = build_graph_with_blockage.__wrapped__(db) if hasattr(build_graph_with_blockage, '__wrapped__') else (build_railway_graph(db), None)
    G_full = build_railway_graph(db)
    G_blocked, blocked_info = build_graph_with_blockage(db, blocked_section_id)

    rakes = db.query(Rake).all()
    demands = db.query(FreightDemand).filter(FreightDemand.is_fulfilled == False).all()

    # Map origin_station_id -> list of destination_station_ids from active demands
    demand_destinations: dict[int, list[int]] = {}
    for d in demands:
        demand_destinations.setdefault(d.origin_station_id, [])
        if d.destination_station_id not in demand_destinations[d.origin_station_id]:
            demand_destinations[d.origin_station_id].append(d.destination_station_id)

    affected = []

    for rake in rakes:
        origin = rake.current_station_id
        if origin is None:
            continue

        # Get destinations this rake might be headed to
        destinations = demand_destinations.get(origin, [])
        if not destinations:
            continue

        for dest in destinations:
            if origin == dest:
                continue

            # Original shortest path
            try:
                original_path = nx.shortest_path(G_full, source=origin, target=dest, weight="weight")
                original_dist = nx.shortest_path_length(G_full, source=origin, target=dest, weight="weight")
            except nx.NetworkXNoPath:
                continue

            # Check if blocked section is used in this path
            uses_blocked = False
            for i in range(len(original_path) - 1):
                a, b = original_path[i], original_path[i + 1]
                if (a == blocked.from_station_id and b == blocked.to_station_id) or \
                   (a == blocked.to_station_id and b == blocked.from_station_id):
                    uses_blocked = True
                    break

            if not uses_blocked:
                continue

            # Try alternate route
            try:
                alt_path = nx.shortest_path(G_blocked, source=origin, target=dest, weight="weight")
                alt_dist = nx.shortest_path_length(G_blocked, source=origin, target=dest, weight="weight")
                rerouted = True
                delay_km = round(alt_dist - original_dist, 2)
            except nx.NetworkXNoPath:
                alt_path = []
                alt_dist = None
                rerouted = False
                delay_km = None

            affected.append({
                "rake_id": rake.id,
                "rake_name": rake.name,
                "rake_status": rake.status.value if hasattr(rake.status, 'value') else rake.status,
                "current_station": get_station_name(db, origin),
                "destination_station": get_station_name(db, dest),
                "original_path": [get_station_name(db, n) for n in original_path],
                "original_distance_km": original_dist,
                "alternate_path": [get_station_name(db, n) for n in alt_path],
                "alternate_distance_km": alt_dist,
                "rerouted": rerouted,
                "extra_distance_km": delay_km,
                "stranded": not rerouted,
            })

    return affected


def propagate_delays(db: Session, affected_rakes: list[dict]) -> list[dict]:
    """
    Find rakes waiting at stations where affected rakes are headed.
    Those rakes inherit a downstream delay because their connecting freight is late.
    """
    # Collect all destination station names from affected rakes
    affected_destinations = set()
    for r in affected_rakes:
        if r["rerouted"] and r["destination_station"]:
            affected_destinations.add(r["destination_station"])

    if not affected_destinations:
        return []

    # Map station name -> station id
    stations = db.query(Station).all()
    station_id_by_name = {s.name: s.id for s in stations}

    secondary = []
    seen_rake_ids = {r["rake_id"] for r in affected_rakes}

    for dest_name in affected_destinations:
        dest_id = station_id_by_name.get(dest_name)
        if dest_id is None:
            continue

        # Rakes currently waiting at this station that aren't already affected
        waiting_rakes = db.query(Rake).filter(
            Rake.current_station_id == dest_id,
            Rake.id.notin_(seen_rake_ids),
        ).all()

        # Find which upstream rake is causing the delay
        causing_rakes = [r for r in affected_rakes if r["destination_station"] == dest_name and r["rerouted"]]

        for waiting_rake in waiting_rakes:
            for causer in causing_rakes:
                secondary.append({
                    "rake_id": waiting_rake.id,
                    "rake_name": waiting_rake.name,
                    "waiting_at_station": dest_name,
                    "caused_by_rake_id": causer["rake_id"],
                    "caused_by_rake_name": causer["rake_name"],
                    "extra_distance_on_upstream_km": causer["extra_distance_km"],
                    "impact": "Upstream rake delayed — connecting freight arrival uncertain",
                })

    return secondary


def detect_yard_congestion(db: Session, affected_rakes: list[dict]) -> list[dict]:
    """
    Count rerouted rakes passing through each yard station.
    Flag yards where rerouted traffic exceeds capacity.
    """
    yards = db.query(Yard).all()
    yard_by_station_id = {y.station_id: y for y in yards}

    stations = db.query(Station).all()
    station_id_by_name = {s.name: s.id for s in stations}

    yard_traffic: dict[int, list[str]] = {}

    for rake in affected_rakes:
        if not rake["rerouted"] or not rake["alternate_path"]:
            continue
        for station_name in rake["alternate_path"]:
            sid = station_id_by_name.get(station_name)
            if sid is None:
                continue
            yard = yard_by_station_id.get(sid)
            if yard is None:
                continue
            yard_traffic.setdefault(yard.id, [])
            yard_traffic[yard.id].append(rake["rake_name"])

    congested = []
    for yard_id, rake_names in yard_traffic.items():
        yard = yard_by_station_id[
            next(sid for sid, y in yard_by_station_id.items() if y.id == yard_id)
        ]
        count = len(rake_names)
        effective_load = yard.current_load + count
        if effective_load > yard.capacity:
            congested.append({
                "yard_id": yard.id,
                "yard_name": yard.name,
                "station_id": yard.station_id,
                "yard_capacity": yard.capacity,
                "current_load": yard.current_load,
                "rerouted_rakes_through": count,
                "effective_load": effective_load,
                "overload_by": effective_load - yard.capacity,
                "rake_names": rake_names,
                "severity": "critical" if effective_load > yard.capacity * 1.5 else "moderate",
            })

    return congested


def simulate_disruption(db: Session, blocked_section_id: int) -> dict:
    """
    Full disruption report:
    - Which section is blocked
    - Which rakes are affected and whether they can be rerouted
    - Secondary rakes impacted by upstream delays
    - Yards that will become congested on alternate routes
    """
    blocked = db.query(Section).filter(Section.id == blocked_section_id).first()
    if not blocked:
        raise ValueError(f"Section ID {blocked_section_id} not found.")

    affected_rakes = find_affected_rakes(db, blocked_section_id)
    secondary_affected = propagate_delays(db, affected_rakes)
    congested_yards = detect_yard_congestion(db, affected_rakes)

    stranded_count = sum(1 for r in affected_rakes if r["stranded"])
    rerouted_count = sum(1 for r in affected_rakes if r["rerouted"])
    total_extra_km = sum(
        r["extra_distance_km"] for r in affected_rakes if r["extra_distance_km"] is not None
    )

    return {
        "blocked_section_id": blocked_section_id,
        "blocked_section_name": blocked.name,
        "from_station": get_station_name(db, blocked.from_station_id),
        "to_station": get_station_name(db, blocked.to_station_id),
        "total_affected_rakes": len(affected_rakes),
        "rerouted_rakes": rerouted_count,
        "stranded_rakes": stranded_count,
        "total_extra_distance_km": round(total_extra_km, 2),
        "affected_rakes": affected_rakes,
        "secondary_affected_rakes": secondary_affected,
        "congested_yards": congested_yards,
    }