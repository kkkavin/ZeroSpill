from contextlib import asynccontextmanager
import io
import json
from typing import List, Optional
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import AirlockAudit, HoneyToken, ImageScanLog, TrapAlert
from .schemas import (
    AgentHookInstallResponse,
    AgentHookStatusResponse,
    AirlockScanRequest,
    AirlockScanResponse,
    BoundingBox,
    DashboardStats,
    DeployHoneyTokensResponse,
    GenerateSampleResponse,
    HoneyTokenOut,
    InspectCommandRequest,
    InspectCommandResponse,
    PlantDecoyRequest,
    PlantDecoyResponse,
    RedactRequest,
    RedactResponse,
    ResetDbResponse,
)
from .services.agent_integration import check_agent_hook_status, install_git_hook_and_rule
from .services.airlock import scan_airlock_content
from .services.honey_trap import (
    deploy_default_honey_tokens,
    inspect_agent_command,
    plant_file_decoy,
    trigger_canary_trip,
)
from .services.pixel_shield import (
    base64_to_image,
    generate_sample_service,
    redact_image_service,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ZeroSpill API",
    description="Production-Grade Neural OCR Pixel-DLP, Honey-Token Trap & Skill Airlock for Autonomous AI Coding Agents",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", summary="Health check endpoint")
def health_check():
    return {"status": "ok", "service": "ZeroSpill", "version": "2.0.0"}


@app.get("/api/v1/dashboard/stats", response_model=DashboardStats, summary="System-wide telemetry stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_redacted = db.query(ImageScanLog).count()
    active_tokens = db.query(HoneyToken).filter(HoneyToken.status == "ACTIVE").count()
    blocked_attempts = db.query(TrapAlert).filter(TrapAlert.blocked == True).count()
    airlock_audits_count = db.query(AirlockAudit).count()

    recent_events = []

    recent_alerts = (
        db.query(TrapAlert)
        .order_by(TrapAlert.timestamp.desc())
        .limit(6)
        .all()
    )
    for alert in recent_alerts:
        recent_events.append({
            "id": f"alert-{alert.id}",
            "type": "HONEY_TRAP_CIRCUIT_BREAKER",
            "title": f"Circuit-Breaker Block: {alert.trigger_type}",
            "severity": alert.severity,
            "blocked": alert.blocked,
            "details": alert.command_snippet[:80],
            "timestamp": alert.timestamp.isoformat(),
        })

    recent_audits = (
        db.query(AirlockAudit)
        .order_by(AirlockAudit.timestamp.desc())
        .limit(6)
        .all()
    )
    for audit in recent_audits:
        recent_events.append({
            "id": f"audit-{audit.id}",
            "type": "AIRLOCK_SCAN",
            "title": f"Airlock Audit: {audit.source_type} (Score {audit.risk_score})",
            "severity": "CRITICAL" if audit.risk_score >= 50 else ("HIGH" if audit.risk_score >= 20 else "LOW"),
            "blocked": audit.blocked,
            "details": audit.raw_content_preview[:80],
            "timestamp": audit.timestamp.isoformat(),
        })

    recent_events.sort(key=lambda x: x["timestamp"], reverse=True)

    return DashboardStats(
        total_screenshots_redacted=total_redacted,
        active_honey_tokens=active_tokens,
        blocked_scavenge_attempts=blocked_attempts,
        airlock_audits=airlock_audits_count,
        recent_events=recent_events[:10],
    )


# Module A: PixelShield Endpoints
@app.post("/api/v1/pixel/generate-sample", response_model=GenerateSampleResponse, summary="Generate simulated agent screenshot with real OCR secrets")
def generate_sample_screenshot(db: Session = Depends(get_db)):
    return generate_sample_service(db)


@app.post("/api/v1/pixel/redact", response_model=RedactResponse, summary="Redact sensitive bounding boxes in base64 image via RapidOCR")
def redact_image_json(payload: RedactRequest, db: Session = Depends(get_db)):
    if not payload.image_base64:
        raise HTTPException(status_code=400, detail="Missing image_base64 string in request.")
    try:
        img = base64_to_image(payload.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {str(e)}")

    return redact_image_service(
        db=db,
        img=img,
        filename=payload.filename or "uploaded.png",
        custom_boxes=payload.custom_boxes,
        auto_detect=payload.auto_detect,
    )


@app.post("/api/v1/pixel/redact-file", response_model=RedactResponse, summary="Redact sensitive bounding boxes from uploaded image file")
async def redact_image_file(
    file: UploadFile = File(...),
    custom_boxes_json: Optional[str] = Form(None),
    auto_detect: bool = Form(True),
    db: Session = Depends(get_db),
):
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode uploaded image: {str(e)}")

    custom_boxes: Optional[List[BoundingBox]] = None
    if custom_boxes_json:
        try:
            raw_boxes = json.loads(custom_boxes_json)
            custom_boxes = [BoundingBox(**b) for b in raw_boxes]
        except Exception:
            pass

    return redact_image_service(
        db=db,
        img=img,
        filename=file.filename or "upload.png",
        custom_boxes=custom_boxes,
        auto_detect=auto_detect,
    )


# Module B: Honey-Token Trap Endpoints
@app.post("/api/v1/honeytrap/deploy", response_model=DeployHoneyTokensResponse, summary="Deploy synthetic decoy credentials to SQLite")
def deploy_honey_tokens(db: Session = Depends(get_db)):
    return deploy_default_honey_tokens(db)


@app.get("/api/v1/honeytrap/tokens", response_model=List[HoneyTokenOut], summary="List all active honey-tokens")
def get_active_honey_tokens(db: Session = Depends(get_db)):
    tokens = db.query(HoneyToken).filter(HoneyToken.status == "ACTIVE").all()
    return [HoneyTokenOut.model_validate(t) for t in tokens]


@app.post("/api/v1/honeytrap/plant-file", response_model=PlantDecoyResponse, summary="Plant real decoy file on disk with live Canary URL")
def plant_decoy_file(req: PlantDecoyRequest, db: Session = Depends(get_db)):
    return plant_file_decoy(db, req.target_path)


@app.get("/api/v1/honeytrap/canary/{token_id}", response_model=InspectCommandResponse, summary="Live Canary URL endpoint: trips circuit breaker when accessed")
def canary_endpoint(token_id: int, db: Session = Depends(get_db)):
    return trigger_canary_trip(db, token_id)


@app.post("/api/v1/honeytrap/inspect-command", response_model=InspectCommandResponse, summary="Inspect agent command for honey-tokens and destructive behaviors")
def inspect_command(req: InspectCommandRequest, db: Session = Depends(get_db)):
    return inspect_agent_command(db, req.command, req.context)


# Module C: Airlock Endpoints
@app.post("/api/v1/airlock/scan", response_model=AirlockScanResponse, summary="Scan agent skill or trace for data leaks and rogue commands")
def scan_airlock(req: AirlockScanRequest, db: Session = Depends(get_db)):
    return scan_airlock_content(db, req.content, req.source_type or "SKILL_MD")


@app.get("/api/v1/airlock/audits", summary="Get recent airlock audit logs")
def list_airlock_audits(db: Session = Depends(get_db)):
    audits = (
        db.query(AirlockAudit)
        .order_by(AirlockAudit.timestamp.desc())
        .limit(20)
        .all()
    )
    return audits


# Agent Hook & Integration Endpoints
@app.post("/api/v1/agent-integration/install-hook", response_model=AgentHookInstallResponse, summary="Install Git pre-commit hook and agent guardrail rule")
def install_hook():
    res = install_git_hook_and_rule()
    return AgentHookInstallResponse(**res)


@app.get("/api/v1/agent-integration/status", response_model=AgentHookStatusResponse, summary="Check Git hook and rule installation status")
def get_hook_status():
    res = check_agent_hook_status()
    return AgentHookStatusResponse(**res)


# Admin & Clean Slate
@app.post("/api/v1/admin/reset-db", response_model=ResetDbResponse, summary="Reset SQLite database to 100% clean slate")
def reset_database(db: Session = Depends(get_db)):
    deleted_images = db.query(ImageScanLog).delete()
    deleted_alerts = db.query(TrapAlert).delete()
    deleted_tokens = db.query(HoneyToken).delete()
    deleted_audits = db.query(AirlockAudit).delete()
    db.commit()

    return ResetDbResponse(
        status="DATABASE_RESET_CLEAN",
        message="All logs, tokens, alerts, and airlock audits deleted. Database is in pristine state.",
        rows_deleted={
            "images": deleted_images,
            "alerts": deleted_alerts,
            "tokens": deleted_tokens,
            "audits": deleted_audits,
        },
    )
