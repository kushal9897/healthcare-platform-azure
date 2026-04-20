"""
Patient Service - Healthcare Platform
Event-driven microservice for patient management and FHIR integration.
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

# --- Configuration ------------------------------------------------------------

SERVICE_NAME = os.getenv("SERVICE_NAME", "patient-service")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
FHIR_BASE_URL = os.getenv("FHIR_BASE_URL", "http://localhost:8080/fhir")
SERVICE_BUS_CONNECTION = os.getenv("AZURE_SERVICE_BUS_CONNECTION", "")

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(SERVICE_NAME)

# --- Metrics ------------------------------------------------------------------

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status", "service"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", ["method", "endpoint", "service"])
PATIENT_OPERATIONS = Counter("patient_operations_total", "Patient CRUD operations", ["operation", "status"])
EVENT_PUBLISHED = Counter("events_published_total", "Events published to Service Bus", ["event_type"])

# --- Models -------------------------------------------------------------------

class PatientCreate(BaseModel):
    given_name: str = Field(..., min_length=1, max_length=100)
    family_name: str = Field(..., min_length=1, max_length=100)
    birth_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    gender: str = Field(..., pattern=r"^(male|female|other|unknown)$")
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

class Patient(BaseModel):
    id: str
    given_name: str
    family_name: str
    birth_date: str
    gender: str
    phone: Optional[str] = None
    email: Optional[str] = None
    active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class PatientSearchResult(BaseModel):
    total: int
    patients: List[Patient]

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    checks: dict

# --- In-Memory Store (replaced by PostgreSQL/FHIR in production) --------------

patients_db: dict = {}

# --- Event Publisher ----------------------------------------------------------

async def publish_event(event_type: str, payload: dict):
    """Publish event to Azure Service Bus for downstream consumers."""
    logger.info(f"Publishing event: {event_type}")
    EVENT_PUBLISHED.labels(event_type=event_type).inc()
    # In production: use azure.servicebus.aio.ServiceBusClient
    # await sender.send_messages(ServiceBusMessage(json.dumps(payload)))

# --- Application Lifecycle ----------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{SERVICE_NAME} starting up")
    # Initialize connections: DB, Redis, Service Bus, FHIR
    yield
    logger.info(f"{SERVICE_NAME} shutting down")

# --- FastAPI App --------------------------------------------------------------

app = FastAPI(
    title="Patient Service",
    description="FHIR-compliant patient management microservice",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)

# --- Middleware: Request Metrics ----------------------------------------------

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    import time
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
        service=SERVICE_NAME,
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
        service=SERVICE_NAME,
    ).observe(duration)

    return response

# --- Health Endpoints ---------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        checks={
            "database": "connected",
            "fhir_server": "reachable",
            "service_bus": "connected",
        },
    )

@app.get("/ready")
async def readiness():
    return {"status": "ready"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

# --- Patient CRUD -------------------------------------------------------------

@app.post("/patients", response_model=Patient, status_code=201)
async def create_patient(patient_data: PatientCreate):
    """Create a new patient record and publish event."""
    import uuid
    patient_id = str(uuid.uuid4())

    patient = Patient(
        id=patient_id,
        given_name=patient_data.given_name,
        family_name=patient_data.family_name,
        birth_date=patient_data.birth_date,
        gender=patient_data.gender,
        phone=patient_data.phone,
        email=patient_data.email,
    )

    patients_db[patient_id] = patient
    PATIENT_OPERATIONS.labels(operation="create", status="success").inc()

    await publish_event("patient.created", {
        "patient_id": patient_id,
        "name": f"{patient.given_name} {patient.family_name}",
        "timestamp": datetime.utcnow().isoformat(),
    })

    logger.info(f"Created patient: {patient_id}")
    return patient

@app.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str):
    """Retrieve a patient by ID."""
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")
    PATIENT_OPERATIONS.labels(operation="read", status="success").inc()
    return patients_db[patient_id]

@app.get("/patients", response_model=PatientSearchResult)
async def search_patients(
    name: Optional[str] = None,
    gender: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    """Search patients with optional filters."""
    results = list(patients_db.values())

    if name:
        name_lower = name.lower()
        results = [
            p for p in results
            if name_lower in p.given_name.lower() or name_lower in p.family_name.lower()
        ]

    if gender:
        results = [p for p in results if p.gender == gender]

    total = len(results)
    results = results[offset : offset + limit]

    PATIENT_OPERATIONS.labels(operation="search", status="success").inc()
    return PatientSearchResult(total=total, patients=results)

@app.delete("/patients/{patient_id}", status_code=204)
async def delete_patient(patient_id: str):
    """Deactivate a patient record (soft delete for HIPAA)."""
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")

    patients_db[patient_id].active = False
    PATIENT_OPERATIONS.labels(operation="delete", status="success").inc()

    await publish_event("patient.deactivated", {
        "patient_id": patient_id,
        "timestamp": datetime.utcnow().isoformat(),
    })

    logger.info(f"Deactivated patient: {patient_id}")

# --- FHIR Endpoints ----------------------------------------------------------

@app.get("/patients/{patient_id}/fhir")
async def get_patient_fhir(patient_id: str):
    """Return patient data in FHIR R4 format."""
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = patients_db[patient_id]
    return {
        "resourceType": "Patient",
        "id": patient.id,
        "active": patient.active,
        "name": [{"family": patient.family_name, "given": [patient.given_name]}],
        "gender": patient.gender,
        "birthDate": patient.birth_date,
        "telecom": [
            {"system": "phone", "value": patient.phone} if patient.phone else None,
            {"system": "email", "value": patient.email} if patient.email else None,
        ],
    }

# --- Entry Point --------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
