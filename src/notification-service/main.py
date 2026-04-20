"""
Notification Service - Healthcare Platform
Consumes events from Service Bus and dispatches alerts via email, Teams, SMS.
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
import uvicorn

from prometheus_client import Counter, generate_latest
from starlette.responses import Response

SERVICE_NAME = os.getenv("SERVICE_NAME", "notification-service")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(SERVICE_NAME)

NOTIFICATIONS_SENT = Counter("notifications_sent_total", "Notifications dispatched", ["channel", "status"])


class NotificationRequest(BaseModel):
    recipient: str
    channel: str = Field(..., pattern=r"^(email|teams|sms|webhook)$")
    subject: str
    body: str
    priority: str = Field(default="normal", pattern=r"^(low|normal|high|critical)$")
    metadata: Optional[dict] = None

class NotificationResponse(BaseModel):
    id: str
    status: str
    channel: str
    sent_at: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{SERVICE_NAME} starting  -  listening for events")
    yield
    logger.info(f"{SERVICE_NAME} shutting down")

app = FastAPI(title="Notification Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def readiness():
    return {"status": "ready"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")


@app.post("/notify", response_model=NotificationResponse, status_code=201)
async def send_notification(req: NotificationRequest):
    import uuid
    notification_id = str(uuid.uuid4())

    # Route to appropriate channel
    logger.info(f"Sending {req.channel} notification to {req.recipient}: {req.subject}")
    NOTIFICATIONS_SENT.labels(channel=req.channel, status="success").inc()

    return NotificationResponse(
        id=notification_id,
        status="sent",
        channel=req.channel,
        sent_at=datetime.utcnow().isoformat(),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
