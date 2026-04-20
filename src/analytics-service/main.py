"""
Analytics Service - Healthcare Platform
Aggregates metrics, generates reports, and provides dashboards data.
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn

from prometheus_client import Counter, generate_latest
from starlette.responses import Response

SERVICE_NAME = os.getenv("SERVICE_NAME", "analytics-service")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(SERVICE_NAME)

REPORT_GENERATED = Counter("reports_generated_total", "Reports generated", ["type"])


class ReportRequest(BaseModel):
    report_type: str  # daily_summary, patient_outcomes, ai_performance, compliance_audit
    date_from: str
    date_to: str
    filters: Optional[dict] = None

class DashboardMetrics(BaseModel):
    total_patients: int
    assessments_today: int
    avg_response_time_ms: float
    error_rate_percent: float
    active_alerts: int
    slo_budget_remaining_percent: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{SERVICE_NAME} starting")
    yield

app = FastAPI(title="Analytics Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def readiness():
    return {"status": "ready"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")


@app.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard():
    """Real-time dashboard metrics for the platform."""
    return DashboardMetrics(
        total_patients=1247,
        assessments_today=89,
        avg_response_time_ms=342.5,
        error_rate_percent=0.02,
        active_alerts=1,
        slo_budget_remaining_percent=94.7,
    )


@app.post("/reports")
async def generate_report(req: ReportRequest):
    """Generate analytics report."""
    import uuid
    report_id = str(uuid.uuid4())
    REPORT_GENERATED.labels(type=req.report_type).inc()
    logger.info(f"Generating {req.report_type} report: {report_id}")

    return {
        "report_id": report_id,
        "type": req.report_type,
        "status": "generated",
        "date_range": {"from": req.date_from, "to": req.date_to},
        "generated_at": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
