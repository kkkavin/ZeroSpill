from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models import HoneyToken, TrapAlert
from ..schemas import (
    DeployHoneyTokensResponse,
    HoneyTokenOut,
    InspectCommandResponse,
    PlantDecoyResponse,
)


DESTRUCTIVE_PATTERNS = [
    (r"\brm\s+(-[rfRF]{1,4}\s+|--recursive\s+|--force\s+)*(\/|\*|\~|\.)", "DESTRUCTIVE_FILESYSTEM_WIPE", "Attempted destructive recursive filesystem deletion"),
    (r"\bDROP\s+(DATABASE|SCHEMA|TABLE)\b", "DATABASE_DESTRUCTION", "Attempted SQL DROP DATABASE or DROP TABLE destruction"),
    (r"\bTRUNCATE\s+TABLE\b", "DATABASE_TRUNCATE", "Attempted destructive SQL TRUNCATE TABLE command"),
    (r"\bgh\s+repo\s+create\b.*--public", "PUBLIC_EXFILTRATION_REPO", "Attempted exfiltrating code into a public GitHub repository"),
    (r"\b(curl|wget)\b.*(-d\s+@|--data\s+@|--post-file).*\.env", "CREDENTIAL_EXFILTRATION_HTTP", "Attempted uploading sensitive .env files via HTTP POST"),
    (r"\bcat\s+(\.env|\.env\.production|\.env\.vault|\.aws\/credentials|\/etc\/shadow)\b", "CREDENTIAL_SCAVENGING_READ", "Attempted direct reads of sensitive credential files"),
    (r"\bgit\s+push\b.*(--force|-f)\b", "DESTRUCTIVE_GIT_FORCE_PUSH", "Attempted force-push overwrite of remote branch"),
    (r"\bchmod\s+777\s+(-R\s+)?(\/|\~|\.)", "INSECURE_PERMISSIONS_OVERWRITE", "Attempted blanket world-writable chmod 777 overwrite"),
]


def deploy_default_honey_tokens(db: Session) -> DeployHoneyTokensResponse:
    """Generates synthetic decoy credentials across cloud, db, and payment platforms."""
    active_tokens = db.query(HoneyToken).filter(HoneyToken.status == "ACTIVE").all()
    if active_tokens and len(active_tokens) >= 4:
        return DeployHoneyTokensResponse(
            status="EXISTING_ACTIVE_RETURNED",
            deployed_count=len(active_tokens),
            tokens=[HoneyTokenOut.model_validate(t) for t in active_tokens],
        )

    db.query(HoneyToken).update({HoneyToken.status: "DECOMMISSIONED"})

    tokens_data = [
        {
            "token_type": "AWS_ACCESS_KEY",
            "decoy_key": "AWS_SECRET_ACCESS_KEY",
            "decoy_value": f"AKIA_TRAP_{secrets.token_hex(8).upper()}",
            "filepath_hint": "~/.aws/credentials",
        },
        {
            "token_type": "RAILWAY_PROD_TOKEN",
            "decoy_key": "RAILWAY_API_TOKEN",
            "decoy_value": f"rwy_trap_{secrets.token_hex(12)}",
            "filepath_hint": ".env.production",
        },
        {
            "token_type": "POSTGRES_PROD_URI",
            "decoy_key": "DATABASE_URL",
            "decoy_value": f"postgresql://decoy_admin:trap_pass_{secrets.token_hex(4)}@db-prod.internal:5432/primary",
            "filepath_hint": "config/database.yml",
        },
        {
            "token_type": "RAZORPAY_LIVE_SECRET",
            "decoy_key": "RAZORPAY_KEY_SECRET",
            "decoy_value": f"rzp_live_trap_{secrets.token_hex(10)}",
            "filepath_hint": ".env.vault",
        },
    ]

    created = []
    for t in tokens_data:
        token = HoneyToken(
            token_type=t["token_type"],
            decoy_key=t["decoy_key"],
            decoy_value=t["decoy_value"],
            filepath_hint=t["filepath_hint"],
            status="ACTIVE",
        )
        db.add(token)
        created.append(token)

    db.commit()
    for token in created:
        db.refresh(token)

    return DeployHoneyTokensResponse(
        status="DEPLOYED_NEW_DECOYS",
        deployed_count=len(created),
        tokens=[HoneyTokenOut.model_validate(t) for t in created],
    )


def plant_file_decoy(db: Session, target_path: Optional[str] = None) -> PlantDecoyResponse:
    """Writes a real file-system decoy containing active honey-tokens and a live Canary URL."""
    deploy_default_honey_tokens(db)
    active_tokens = db.query(HoneyToken).filter(HoneyToken.status == "ACTIVE").all()
    primary_id = active_tokens[0].id if active_tokens else 1

    file_path_str = target_path or "./.zerospill_decoys/.env.production.decoy"
    file_path = Path(file_path_str).resolve()
    file_path.parent.mkdir(parents=True, exist_ok=True)

    canary_url = f"http://127.0.0.1:8000/api/v1/honeytrap/canary/{primary_id}"

    lines = [
        "# ==============================================================================",
        "# ZeroSpill Production Decoy Credential Vault (Tripwire Canary Protected)",
        "# ANY ACCESS TO THESE VARIABLES OR CANARY URL WILL TRIGGER AGENT QUARANTINE",
        "# ==============================================================================",
    ]
    for token in active_tokens:
        lines.append(f"{token.decoy_key}={token.decoy_value}")
    lines.append(f"ZEROSPILL_INTERNAL_API={canary_url}")
    lines.append("")

    file_path.write_text("\n".join(lines), encoding="utf-8")
    now = datetime.now(timezone.utc)

    return PlantDecoyResponse(
        status="DECOY_FILE_PLANTED",
        file_path=str(file_path),
        canary_url=canary_url,
        tokens_written=len(active_tokens),
        timestamp=now,
    )


def trigger_canary_trip(db: Session, token_id: int) -> InspectCommandResponse:
    """Handles an HTTP GET request to the Canary URL, logging a critical alert and tripping circuit breaker."""
    now = datetime.now(timezone.utc)
    token = db.query(HoneyToken).filter(HoneyToken.id == token_id).first()
    token_label = f"{token.token_type} (#{token.id})" if token else f"Decoy #{token_id}"

    alert = TrapAlert(
        token_id=token_id if token else None,
        command_snippet=f"HTTP GET /api/v1/honeytrap/canary/{token_id}",
        trigger_type="CANARY_URL_TRIPPED",
        severity="CRITICAL",
        blocked=True,
        incident_details=json.dumps({
            "trigger": "CANARY_URL_TRIPPED",
            "token_id": token_id,
            "token_type": token.token_type if token else "UNKNOWN",
            "explanation": "Live Canary Endpoint Triggered by Agent curl/fetch",
        }),
        timestamp=now,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return InspectCommandResponse(
        blocked=True,
        severity="CRITICAL",
        trigger_type="CANARY_URL_TRIPPED",
        action_taken="CIRCUIT_BREAKER_TRIGGERED",
        matched_tokens=[token_label],
        matched_patterns=["LIVE_CANARY_PROBE"],
        explanation=f"Live Canary Endpoint Triggered by Agent! Token {token_label} tripped.",
        incident_id=alert.id,
        timestamp=now,
    )


def inspect_agent_command(
    db: Session, command: str, context: Optional[str] = None
) -> InspectCommandResponse:
    """Inspects agent terminal commands against active honey tokens and destructive behavior patterns."""
    full_trace = f"{command}\n{context or ''}"

    matched_tokens: List[str] = []
    matched_token_id: Optional[int] = None
    matched_patterns: List[str] = []
    reasons: List[str] = []

    # 1. Check against active Honey Tokens in SQLite
    active_tokens = db.query(HoneyToken).filter(HoneyToken.status == "ACTIVE").all()
    for token in active_tokens:
        if token.decoy_value in full_trace:
            matched_tokens.append(f"{token.token_type} ({token.decoy_key})")
            matched_token_id = token.id
            reasons.append(
                f"Agent accessed synthetic decoy honey-token '{token.token_type}' configured at '{token.filepath_hint}'"
            )

    # 2. Check destructive regex patterns
    for pattern, rule_code, description in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            matched_patterns.append(rule_code)
            reasons.append(f"[{rule_code}] {description}")

    # Determine circuit-breaker outcome
    is_blocked = len(matched_tokens) > 0 or len(matched_patterns) > 0
    now = datetime.now(timezone.utc)

    if is_blocked:
        trigger = (
            "HONEY_TOKEN_SCAVENGE"
            if len(matched_tokens) > 0
            else "DESTRUCTIVE_PATTERN_MATCH"
        )
        details = {
            "matched_tokens": matched_tokens,
            "matched_patterns": matched_patterns,
            "reasons": reasons,
            "command": command,
        }

        alert = TrapAlert(
            token_id=matched_token_id,
            command_snippet=command[:1000],
            trigger_type=trigger,
            severity="CRITICAL",
            blocked=True,
            incident_details=json.dumps(details),
            timestamp=now,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        explanation = (
            f"ZeroSpill Circuit-Breaker tripped! Prohibited agent activity detected: "
            + "; ".join(reasons)
        )

        return InspectCommandResponse(
            blocked=True,
            severity="CRITICAL",
            trigger_type=trigger,
            action_taken="CIRCUIT_BREAKER_TRIGGERED",
            matched_tokens=matched_tokens,
            matched_patterns=matched_patterns,
            explanation=explanation,
            incident_id=alert.id,
            timestamp=now,
        )

    return InspectCommandResponse(
        blocked=False,
        severity="NONE",
        trigger_type=None,
        action_taken="ALLOW",
        matched_tokens=[],
        matched_patterns=[],
        explanation="Command passed honey-trap and behavioral safety checks.",
        incident_id=None,
        timestamp=now,
    )
