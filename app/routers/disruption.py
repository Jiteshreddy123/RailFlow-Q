# app/routers/disruption.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.disruption import simulate_disruption

router = APIRouter(prefix="/api/v1/disruption", tags=["Disruption Engine"])


@router.post("/simulate")
def run_disruption_simulation(section_id: int, db: Session = Depends(get_db)):
    """
    Simulate a disruption by blocking one section.
    Returns all affected rakes with rerouting analysis.

    - section_id: the DB ID of the section that is blocked
    """
    try:
        result = simulate_disruption(db, section_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

    return result