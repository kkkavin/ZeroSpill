from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# Pixel Shield Schemas
class BoundingBox(BaseModel):
    label: str
    x1: int
    y1: int
    x2: int
    y2: int
    severity: str = "CRITICAL"
    confidence: float = 0.99


class GenerateSampleResponse(BaseModel):
    original_image_base64: str
    redacted_image_base64: str
    bounding_boxes: List[BoundingBox]
    secrets_detected: int
    width: int
    height: int


class RedactRequest(BaseModel):
    image_base64: Optional[str] = None
    filename: Optional[str] = "uploaded_screenshot.png"
    custom_boxes: Optional[List[BoundingBox]] = None
    auto_detect: bool = True


class RedactionTelemetry(BaseModel):
    execution_time_ms: float
    pixels_blurred: int
    secrets_redacted: int
    redaction_mode: str


class RedactResponse(BaseModel):
    original_image_base64: str
    redacted_image_base64: str
    bounding_boxes: List[BoundingBox]
    secrets_detected: int
    telemetry: RedactionTelemetry


# Honey-Token Schemas
class HoneyTokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    token_type: str
    decoy_key: str
    decoy_value: str
    filepath_hint: str
    status: str
    created_at: datetime


class DeployHoneyTokensResponse(BaseModel):
    status: str
    deployed_count: int
    tokens: List[HoneyTokenOut]


class InspectCommandRequest(BaseModel):
    command: str
    context: Optional[str] = None


class InspectCommandResponse(BaseModel):
    blocked: bool
    severity: str
    trigger_type: Optional[str] = None
    action_taken: str
    matched_tokens: List[str] = Field(default_factory=list)
    matched_patterns: List[str] = Field(default_factory=list)
    explanation: str
    incident_id: Optional[int] = None
    timestamp: datetime


# Airlock Schemas
class AirlockFinding(BaseModel):
    rule: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    snippet: str
    description: str
    line_number: Optional[int] = None


class AirlockScanRequest(BaseModel):
    content: str
    source_type: Optional[str] = "SKILL_MD"


class AirlockScanResponse(BaseModel):
    risk_score: int
    blocked: bool
    findings: List[AirlockFinding]
    sanitized_content: str
    audit_id: int
    timestamp: datetime


# Dashboard Telemetry Schemas
class DashboardStats(BaseModel):
    total_screenshots_redacted: int
    active_honey_tokens: int
    blocked_scavenge_attempts: int
    airlock_audits: int
    recent_events: List[Dict[str, Any]]

