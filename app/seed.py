from app.db import SessionLocal
from app.models.railway import Rake, Station, Section, Yard, FreightDemand, RakeStatus

def seed():
    db = SessionLocal()
    try:
        if db.query(Station).count() > 0:
            print("Database already seeded.")
            return

        stations = [
            Station(name="Mine A", code="MA", has_yard=False),
            Station(name="Mine B", code="MB", has_yard=False),
            Station(name="Station S1", code="S1", has_yard=False),
            Station(name="Station S2", code="S2", has_yard=True),
            Station(name="Station S3", code="S3", has_yard=False),
            Station(name="Station S4", code="S4", has_yard=False),
            Station(name="Station S5", code="S5", has_yard=True),
            Station(name="Port", code="PT", has_yard=False),
            Station(name="Factory", code="FC", has_yard=True),
            Station(name="Junction J1", code="J1", has_yard=False),
            Station(name="Junction J2", code="J2", has_yard=False),
            Station(name="Junction J3", code="J3", has_yard=False),
            Station(name="Depot D1", code="D1", has_yard=True),
            Station(name="Depot D2", code="D2", has_yard=False),
            Station(name="Yard Central", code="YC", has_yard=True),
        ]
        db.add_all(stations)
        db.commit()

        rakes = [
            Rake(name="R1", capacity=500, current_station_id=1),
            Rake(name="R2", capacity=600, current_station_id=2),
            Rake(name="R3", capacity=450, current_station_id=3),
            Rake(name="R4", capacity=700, current_station_id=4),
            Rake(name="R5", capacity=500, current_station_id=5),
            Rake(name="R6", capacity=600, current_station_id=1),
            Rake(name="R7", capacity=550, current_station_id=6),
            Rake(name="R8", capacity=650, current_station_id=7),
            Rake(name="R9", capacity=500, current_station_id=8),
            Rake(name="R10", capacity=600, current_station_id=9),
        ]
        db.add_all(rakes)
        db.commit()

        sections = [
            Section(name="MA-S1", from_station_id=1, to_station_id=3, distance_km=50),
            Section(name="MB-S4", from_station_id=2, to_station_id=6, distance_km=40),
            Section(name="S1-S2", from_station_id=3, to_station_id=4, distance_km=30),
            Section(name="S2-S3", from_station_id=4, to_station_id=5, distance_km=35),
            Section(name="S3-PT", from_station_id=5, to_station_id=8, distance_km=60),
            Section(name="S4-S2", from_station_id=6, to_station_id=4, distance_km=25),
            Section(name="S2-S5", from_station_id=4, to_station_id=7, distance_km=20),
            Section(name="S5-FC", from_station_id=7, to_station_id=9, distance_km=45),
            Section(name="S1-J1", from_station_id=3, to_station_id=10, distance_km=15),
            Section(name="J1-J2", from_station_id=10, to_station_id=11, distance_km=20),
            Section(name="J2-S3", from_station_id=11, to_station_id=5, distance_km=25),
            Section(name="J2-PT", from_station_id=11, to_station_id=8, distance_km=30),
            Section(name="S4-J3", from_station_id=6, to_station_id=12, distance_km=10),
            Section(name="J3-S5", from_station_id=12, to_station_id=7, distance_km=15),
            Section(name="S5-D1", from_station_id=7, to_station_id=13, distance_km=20),
            Section(name="D1-YC", from_station_id=13, to_station_id=15, distance_km=10),
            Section(name="YC-FC", from_station_id=15, to_station_id=9, distance_km=15),
            Section(name="D2-J1", from_station_id=14, to_station_id=10, distance_km=12),
            Section(name="MA-J1", from_station_id=1, to_station_id=10, distance_km=35),
            Section(name="MB-J3", from_station_id=2, to_station_id=12, distance_km=28),
        ]
        db.add_all(sections)
        db.commit()

        yards = [
            Yard(name="Yard S2", station_id=4, capacity=20, current_load=8),
            Yard(name="Yard S5", station_id=7, capacity=15, current_load=5),
            Yard(name="Yard Central", station_id=15, capacity=30, current_load=12),
        ]
        db.add_all(yards)
        db.commit()

        freight_demands = [
            FreightDemand(origin_station_id=1, destination_station_id=8, weight_tons=200, priority=1),
            FreightDemand(origin_station_id=2, destination_station_id=9, weight_tons=150, priority=2),
            FreightDemand(origin_station_id=1, destination_station_id=9, weight_tons=300, priority=1),
            FreightDemand(origin_station_id=2, destination_station_id=8, weight_tons=250, priority=3),
            FreightDemand(origin_station_id=3, destination_station_id=8, weight_tons=180, priority=2),
            FreightDemand(origin_station_id=1, destination_station_id=7, weight_tons=220, priority=1),
            FreightDemand(origin_station_id=2, destination_station_id=7, weight_tons=190, priority=2),
            FreightDemand(origin_station_id=4, destination_station_id=8, weight_tons=160, priority=3),
            FreightDemand(origin_station_id=1, destination_station_id=9, weight_tons=280, priority=1),
            FreightDemand(origin_station_id=2, destination_station_id=8, weight_tons=210, priority=2),
            FreightDemand(origin_station_id=3, destination_station_id=9, weight_tons=175, priority=1),
            FreightDemand(origin_station_id=5, destination_station_id=8, weight_tons=195, priority=3),
            FreightDemand(origin_station_id=1, destination_station_id=7, weight_tons=240, priority=2),
            FreightDemand(origin_station_id=2, destination_station_id=9, weight_tons=165, priority=1),
            FreightDemand(origin_station_id=4, destination_station_id=7, weight_tons=230, priority=2),
            FreightDemand(origin_station_id=1, destination_station_id=8, weight_tons=185, priority=3),
            FreightDemand(origin_station_id=3, destination_station_id=7, weight_tons=205, priority=1),
            FreightDemand(origin_station_id=2, destination_station_id=8, weight_tons=170, priority=2),
            FreightDemand(origin_station_id=5, destination_station_id=9, weight_tons=215, priority=1),
            FreightDemand(origin_station_id=1, destination_station_id=7, weight_tons=260, priority=3),
            FreightDemand(origin_station_id=2, destination_station_id=9, weight_tons=145, priority=2),
            FreightDemand(origin_station_id=3, destination_station_id=8, weight_tons=225, priority=1),
            FreightDemand(origin_station_id=4, destination_station_id=9, weight_tons=190, priority=2),
            FreightDemand(origin_station_id=1, destination_station_id=8, weight_tons=275, priority=1),
            FreightDemand(origin_station_id=2, destination_station_id=7, weight_tons=155, priority=3),
            FreightDemand(origin_station_id=5, destination_station_id=8, weight_tons=235, priority=2),
            FreightDemand(origin_station_id=3, destination_station_id=9, weight_tons=200, priority=1),
            FreightDemand(origin_station_id=4, destination_station_id=8, weight_tons=180, priority=2),
            FreightDemand(origin_station_id=1, destination_station_id=9, weight_tons=245, priority=1),
            FreightDemand(origin_station_id=2, destination_station_id=8, weight_tons=165, priority=3),
        ]
        db.add_all(freight_demands)
        db.commit()
        print("Database seeded successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    seed()