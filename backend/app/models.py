from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


def utc_now():
    return datetime.now(timezone.utc)


class HoneyToken(Base):
    __tablename__ = "honey_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_type = Column(String(64), nullable=False, index=True)
    decoy_key = Column(String(128), nullable=False)
    decoy_value = Column(String(256), nullable=False, index=True)
    filepath_hint = Column(String(256), nullable=False)
    status = Column(String(32), default="ACTIVE", index=True)
    created_at = Column(DateTime, default=utc_now)

    alerts = relationship("TrapAlert", back_populates="token")


class TrapAlert(Base):
    __tablename__ = "trap_alerts"

    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, ForeignKey("honey_tokens.id"), nullable=True)
    command_snippet = Column(Text, nullable=False)
    trigger_type = Column(String(64), nullable=False)
    severity = Column(String(32), default="CRITICAL")
    blocked = Column(Boolean, default=True)
    incident_details = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utc_now)

    token = relationship("HoneyToken", back_populates="alerts")


class ImageScanLog(Base):
    __tablename__ = "image_scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(256), default="screenshot.png")
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    secrets_detected = Column(Integer, default=0)
    bounding_boxes_json = Column(Text, default="[]")
    redaction_mode = Column(String(64), default="GAUSSIAN_BLUR_14")
    timestamp = Column(DateTime, default=utc_now)


class AirlockAudit(Base):
    __tablename__ = "airlock_audits"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(String(64), default="SKILL_MD")
    risk_score = Column(Integer, default=0)
    findings_json = Column(Text, default="[]")
    raw_content_preview = Column(Text, default="")
    sanitized_content = Column(Text, default="")
    blocked = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=utc_now)
