"""
Clinical Service - Healthcare Platform
Event-driven microservice for AI-powered clinical assessments.
Consumes patient events, runs AI agents, publishes assessment results.
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

SERVICE_NAME = os.getenv("SERVICE_NAME", "clinical-service")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(SERVICE_NAME)

REQUEST_COUNT = Counter("http_requests_total", "Total requests", ["method", "endpoint", "status", "service"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Latency", ["method", "endpoint", "service"])
ASSESSMENTS = Counter("clinical_assessments_total", "Assessments performed", ["type", "status"])
AI_LATENCY = Histogram("ai_inference_duration_seconds", "AI model inference latency", ["model"])


class AssessmentRequest(BaseModel):
    patient_id: str
    assessment_type: str = Field(..., pattern=r"^(primary_care|cardiology|pharmacy|emergency|nursing)$")
    chief_complaint: str = Field(..., min_length=5, max_length=2000)
    history: Optional[str] = None
    vitals: Optional[dict] = None

class AssessmentResult(BaseModel):
    id: str
    patient_id: str
    assessment_type: str
    status: str
    findings: List[str]
    recommendations: List[str]
    risk_level: str
    ai_model: str
    processing_time_ms: int
    created_at: str

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


assessments_db: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{SERVICE_NAME} starting  -  AI model: {AZURE_OPENAI_DEPLOYMENT}")
    yield
    logger.info(f"{SERVICE_NAME} shutting down")

app = FastAPI(
    title="Clinical Service",
    description="AI-powered clinical assessment microservice",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    import time
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code, service=SERVICE_NAME).inc()
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path, service=SERVICE_NAME).observe(duration)
    return response


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy", service=SERVICE_NAME, version="1.0.0", timestamp=datetime.utcnow().isoformat())

@app.get("/ready")
async def readiness():
    return {"status": "ready"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")


@app.post("/assess", response_model=AssessmentResult, status_code=201)
async def create_assessment(request: AssessmentRequest):
    """Run AI-powered clinical assessment."""
    import uuid, time

    start = time.time()
    assessment_id = str(uuid.uuid4())

    # AI agent selection based on assessment type
    agent_prompts = {
        "primary_care": "You are a Primary Care Physician AI agent. Assess the patient's chief complaint and provide findings and recommendations.",
        "cardiology": "You are a Cardiologist AI agent. Evaluate cardiovascular risk and provide cardiac-specific findings.",
        "pharmacy": "You are a Clinical Pharmacist AI agent. Review medications, check interactions, and optimize dosing.",
        "emergency": "You are an Emergency Medicine AI agent. Perform rapid triage and risk stratification.",
        "nursing": "You are a Nurse Care Coordinator AI agent. Plan care transitions and patient education.",
    }

    # Simulate AI inference (in production: call Azure OpenAI)
    findings = [
        f"Assessment type: {request.assessment_type}",
        f"Chief complaint analyzed: {request.chief_complaint[:100]}",
        "Vital signs reviewed" if request.vitals else "No vital signs provided",
        "Medical history reviewed" if request.history else "No history provided",
    ]
    recommendations = [
        "Follow up in 2 weeks",
        "Monitor symptoms",
        "Complete blood panel recommended",
    ]

    processing_time = int((time.time() - start) * 1000)
    AI_LATENCY.labels(model=AZURE_OPENAI_DEPLOYMENT).observe(processing_time / 1000)

    result = AssessmentResult(
        id=assessment_id,
        patient_id=request.patient_id,
        assessment_type=request.assessment_type,
        status="completed",
        findings=findings,
        recommendations=recommendations,
        risk_level="moderate",
        ai_model=AZURE_OPENAI_DEPLOYMENT,
        processing_time_ms=processing_time,
        created_at=datetime.utcnow().isoformat(),
    )

    assessments_db[assessment_id] = result
    ASSESSMENTS.labels(type=request.assessment_type, status="success").inc()
    logger.info(f"Assessment {assessment_id} completed in {processing_time}ms")
    return result


@app.get("/assessments/{assessment_id}", response_model=AssessmentResult)
async def get_assessment(assessment_id: str):
    if assessment_id not in assessments_db:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessments_db[assessment_id]


@app.get("/assessments")
async def list_assessments(patient_id: Optional[str] = None, limit: int = 20):
    results = list(assessments_db.values())
    if patient_id:
        results = [a for a in results if a.patient_id == patient_id]
    return {"total": len(results), "assessments": results[:limit]}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
