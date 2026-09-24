from fastapi import FastAPI
from dotenv import load_dotenv
from app.db import engine, Base
from app.models import railway
from app.routers.railway import router as railway_router
from app.routers.disruption import router as disruption_router

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RailFlow-Q API",
    description="Quantum-Assisted Freight Disruption Recovery",
    version="1.0.0"
)

app.include_router(railway_router)
app.include_router(disruption_router)

@app.get("/")
def root():
    return {"message": "RailFlow-Q Backend is running"}