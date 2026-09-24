from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import SessionLocal
from app.models.railway import Rake, Station, Section, Yard, FreightDemand
from app.schemas.railway import (
    RakeCreate, RakeResponse,
    StationCreate, StationResponse,
    SectionCreate, SectionResponse,
    YardCreate, YardResponse,
    FreightDemandCreate, FreightDemandResponse
)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# RAKE ENDPOINTS
@router.get("/rakes", response_model=List[RakeResponse])
def get_rakes(db: Session = Depends(get_db)):
    return db.query(Rake).all()

@router.post("/rakes", response_model=RakeResponse)
def create_rake(rake: RakeCreate, db: Session = Depends(get_db)):
    db_rake = Rake(**rake.model_dump())
    db.add(db_rake)
    db.commit()
    db.refresh(db_rake)
    return db_rake

@router.get("/rakes/{rake_id}", response_model=RakeResponse)
def get_rake(rake_id: int, db: Session = Depends(get_db)):
    rake = db.query(Rake).filter(Rake.id == rake_id).first()
    if not rake:
        raise HTTPException(status_code=404, detail="Rake not found")
    return rake

# STATION ENDPOINTS
@router.get("/stations", response_model=List[StationResponse])
def get_stations(db: Session = Depends(get_db)):
    return db.query(Station).all()

@router.post("/stations", response_model=StationResponse)
def create_station(station: StationCreate, db: Session = Depends(get_db)):
    db_station = Station(**station.model_dump())
    db.add(db_station)
    db.commit()
    db.refresh(db_station)
    return db_station

# SECTION ENDPOINTS
@router.get("/sections", response_model=List[SectionResponse])
def get_sections(db: Session = Depends(get_db)):
    return db.query(Section).all()

@router.post("/sections", response_model=SectionResponse)
def create_section(section: SectionCreate, db: Session = Depends(get_db)):
    db_section = Section(**section.model_dump())
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section

# YARD ENDPOINTS
@router.get("/yards", response_model=List[YardResponse])
def get_yards(db: Session = Depends(get_db)):
    return db.query(Yard).all()

@router.post("/yards", response_model=YardResponse)
def create_yard(yard: YardCreate, db: Session = Depends(get_db)):
    db_yard = Yard(**yard.model_dump())
    db.add(db_yard)
    db.commit()
    db.refresh(db_yard)
    return db_yard

# FREIGHT DEMAND ENDPOINTS
@router.get("/freight-demands", response_model=List[FreightDemandResponse])
def get_freight_demands(db: Session = Depends(get_db)):
    return db.query(FreightDemand).all()

@router.post("/freight-demands", response_model=FreightDemandResponse)
def create_freight_demand(demand: FreightDemandCreate, db: Session = Depends(get_db)):
    db_demand = FreightDemand(**demand.model_dump())
    db.add(db_demand)
    db.commit()
    db.refresh(db_demand)
    return db_demand