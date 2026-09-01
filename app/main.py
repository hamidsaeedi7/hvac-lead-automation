from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import dashboard_stats, get_lead, init_db, list_leads
from app.models import DashboardStats, LeadCreate, LeadCreated
from app.services.automation import process_lead, seed_demo_data


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed_demo_data()
    yield


app = FastAPI(
    title="HVAC Lead Response Automation",
    version="1.0.0",
    description="Portfolio demo for lead classification, CRM routing and follow-up automation.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "portfolio-demo"}


@app.post("/api/leads", response_model=LeadCreated, status_code=201)
def create_lead(payload: LeadCreate) -> dict:
    if not payload.consent:
        raise HTTPException(status_code=422, detail="Consent is required for this demo workflow")
    return process_lead(payload)


@app.get("/api/leads")
def read_leads(limit: int = Query(default=50, ge=1, le=200)) -> list[dict]:
    return list_leads(limit)


@app.get("/api/leads/{lead_id}")
def read_lead(lead_id: str) -> dict:
    lead = get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@app.get("/api/dashboard", response_model=DashboardStats)
def read_dashboard() -> dict:
    return dashboard_stats()

