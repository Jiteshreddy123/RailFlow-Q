# RailFlow-Q 🚂

**Quantum-Assisted Freight Disruption Recovery System**

A backend system that simulates railway freight disruptions and computes recovery schedules using both classical (OR-Tools) and quantum-assisted (D-Wave Ocean) optimization.

---

## Tech Stack

- **FastAPI** — REST API framework
- **PostgreSQL** — relational database
- **SQLAlchemy** — ORM
- **Alembic** — database migrations
- **NetworkX** — railway graph modeling
- **OR-Tools** — classical constraint solver (Day 6–7)
- **D-Wave Ocean SDK** — QUBO quantum solver (Day 8–10)

---

## Project Structure
railflow-backend/
├── app/
│ ├── models/ # SQLAlchemy models
│ ├── schemas/ # Pydantic schemas
│ ├── routers/ # API route handlers
│ ├── services/ # Business logic
│ └── db.py # Database connection
├── alembic/ # Migration files
├── seed.py # Seed data (10 rakes, 15 stations, 20 sections)
├── main.py # App entry point
└── .env # Environment variables (not committed)


---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-username/railflow-backend.git
cd railflow-backend

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/railflow

# 5. Run migrations
alembic upgrade head

# 6. Seed the database
python seed.py

# 7. Start the server
uvicorn app.main:app --reload
```

---

## API Endpoints

### Railway Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rakes` | List all rakes |
| POST | `/rakes` | Create a rake |
| GET | `/rakes/{id}` | Get rake by ID |
| GET | `/stations` | List all stations |
| POST | `/stations` | Create a station |
| GET | `/sections` | List all sections |
| POST | `/sections` | Create a section |
| GET | `/yards` | List all yards |
| POST | `/yards` | Create a yard |
| GET | `/freight-demands` | List all freight demands |
| POST | `/freight-demands` | Create a freight demand |

### Disruption Engine
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/disruption/simulate?section_id={id}` | Run disruption simulation |

---

## Disruption Simulation Response

```json
{
  "blocked_section_id": 1,
  "blocked_section_name": "MA-S1",
  "from_station": "Mine A",
  "to_station": "Station S1",
  "total_affected_rakes": 4,
  "rerouted_rakes": 4,
  "stranded_rakes": 0,
  "total_extra_distance_km": 0,
  "affected_rakes": [...],
  "secondary_affected_rakes": [...],
  "congested_yards": [...]
}
```

---

## Development Progress
 Focus | Status |
 -------|--------|
FastAPI + PostgreSQL + Alembic setup | ✅ Done |
Railway models + CRUD endpoints | ✅ Done |
Freight demands + seed data | ✅ Done |
Disruption engine + graph + affected rake detection | ✅ Done |
Delay propagation + yard congestion | ✅ Done |

---

## Team

Built for the RailFlow Quantum Hackathon.