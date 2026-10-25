from collections import Counter
from datetime import datetime, timezone
import json
import math
import re
from typing import List, Tuple
from sqlalchemy.orm import Session

from ..models import AirlockAudit
from ..schemas import AirlockFinding, AirlockScanResponse


def shannon_entropy(data: str) -> float:
    """Calculates the Shannon entropy of a string in bits per symbol."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    counts = Counter(data)
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return round(entropy, 3)


# Known credential patterns
CREDENTIAL_REGEXES = [
    (r"\bsk-proj-[a-zA-Z0-9_\-]{32,}\b", "OPENAI_PROJECT_API_KEY", "CRITICAL", "Live OpenAI Project API Key detected"),
    (r"\bsk-[a-zA-Z0-9]{32,}\b", "OPENAI_LEGACY_API_KEY", "CRITICAL", "Live OpenAI API Key detected"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS_ACCESS_KEY_ID", "CRITICAL", "AWS Access Key ID detected"),
    (r"\bghp_[a-zA-Z0-9]{36}\b", "GITHUB_PERSONAL_ACCESS_TOKEN", "CRITICAL", "GitHub Personal Access Token detected"),
    (r"\bgho_[a-zA-Z0-9]{36}\b", "GITHUB_OAUTH_TOKEN", "CRITICAL", "GitHub OAuth Access Token detected"),
    (r"\bxox[baprs]-[0-9a-zA-Z]{10,48}\b", "SLACK_API_TOKEN", "HIGH", "Slack Bot/User Token detected"),
    (r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b", "JWT_AUTH_TOKEN", "HIGH", "JSON Web Token (JWT) detected"),
    (r"\bpostgres(ql)?:\/\/[a-zA-Z0-9_]+:[^@\s]+@[a-zA-Z0-9_\-\.]+:[0-9]+\/[a-zA-Z0-9_\-\.]+\b", "DATABASE_CONNECTION_URI", "CRITICAL", "PostgreSQL database URI with credentials detected"),
]

# Exfiltration & public upload patterns
EXFIL_PATTERNS = [
    (r"\bgh\s+gist\s+create\b.*--public", "PUBLIC_GIST_EXFIL", "CRITICAL", "Command publishes code or logs to a public GitHub Gist"),
    (r"\bgh\s+repo\s+create\b.*--public", "PUBLIC_REPO_EXFIL", "CRITICAL", "Command creates public repository that may leak workspace code"),
    (r"\bcurl\s+(-[a-zA-Z]*F|--form)\s+", "CURL_FORM_FILE_UPLOAD", "HIGH", "curl multipart form upload detected (potential file exfiltration)"),
    (r"\b(pastebin\.com|transfer\.sh|webhook\.site|requestbin\.net)\b", "EXTERNAL_DUMP_SERVICE", "HIGH", "Reference to external data drop / public exfiltration endpoint"),
    (r"\bgitshot\b", "GITSHOT_SCREENSHOT_TOOL", "MEDIUM", "Automated git screenshot tool detected"),
    (r"\b(curl|wget)\b[^\n\r\|]+?\|\s*(bash|sh)\b", "REMOTE_CODE_EXECUTION_PIPE", "CRITICAL", "Dangerous piped remote shell execution (curl | bash)"),
]

# Base64 image patterns: data URIs or raw PNG / JPEG base64 strings
BASE64_IMAGE_DATA_URI_REGEX = re.compile(r"data:image\/(?:png|jpeg|jpg|webp);base64,[A-Za-z0-9+/=]{100,}")
# Standalone raw base64 PNG header (starts with iVBORw0KGgo) or JPEG header (/9j/)
RAW_PNG_BASE64_REGEX = re.compile(r"\biVBORw0KGgo[A-Za-z0-9+/=]{120,}\b")
RAW_JPEG_BASE64_REGEX = re.compile(r"\b/9j/[A-Za-z0-9+/=]{120,}\b")


def scan_airlock_content(
    db: Session,
    content: str,
    source_type: str = "SKILL_MD"
) -> AirlockScanResponse:
    """Audits agent SKILL.md, jsonl trace, or git hook for secrets, unredacted base64 screenshots, and public uploads."""
    findings: List[AirlockFinding] = []
    lines = content.splitlines()

    # 1. Check for Embedded Base64 Images (Pixel-Leak DLP)
    # Check data URIs
    for i, line in enumerate(lines, start=1):
        for match in BASE64_IMAGE_DATA_URI_REGEX.finditer(line):
            snippet = match.group(0)[:60] + "..."
            findings.append(AirlockFinding(
                rule="EMBEDDED_BASE64_IMAGE_DATA_URI",
                severity="CRITICAL",
                snippet=snippet,
                description="Unredacted embedded base64 image data URI detected inside agent trace or skill.",
                line_number=i
            ))

        for match in RAW_PNG_BASE64_REGEX.finditer(line):
            snippet = match.group(0)[:60] + "..."
            findings.append(AirlockFinding(
                rule="RAW_PNG_BASE64_LEAK",
                severity="CRITICAL",
                snippet=snippet,
                description="Raw base64-encoded PNG image detected (violates screenshot redaction policy).",
                line_number=i
            ))

        for match in RAW_JPEG_BASE64_REGEX.finditer(line):
            snippet = match.group(0)[:60] + "..."
            findings.append(AirlockFinding(
                rule="RAW_JPEG_BASE64_LEAK",
                severity="CRITICAL",
                snippet=snippet,
                description="Raw base64-encoded JPEG image detected.",
                line_number=i
            ))

    # 2. Check for Exfiltration / Public Upload Commands
    for i, line in enumerate(lines, start=1):
        for pattern, rule, severity, desc in EXFIL_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append(AirlockFinding(
                    rule=rule,
                    severity=severity,
                    snippet=line.strip()[:100],
                    description=desc,
                    line_number=i
                ))

    # 3. Check for Known Credential Regexes
    for i, line in enumerate(lines, start=1):
        for pattern, rule, severity, desc in CREDENTIAL_REGEXES:
            matches = re.finditer(pattern, line)
            for m in matches:
                findings.append(AirlockFinding(
                    rule=rule,
                    severity=severity,
                    snippet=m.group(0)[:30] + "...",
                    description=desc,
                    line_number=i
                ))

    # 4. Check for High-Entropy Token Anomalies (Shannon Entropy)
    # Tokenize words containing alphanumeric/symbols of length >= 24
    for i, line in enumerate(lines, start=1):
        words = re.findall(r"[A-Za-z0-9_\-\.]{24,}", line)
        for w in words:
            # Skip if already flagged as base64 image
            if w.startswith("iVBORw0KGgo") or w.startswith("/9j/"):
                continue
            entropy = shannon_entropy(w)
            if entropy >= 4.25 and len(w) >= 28:
                # Potential raw API secret with high entropy
                findings.append(AirlockFinding(
                    rule="HIGH_SHANNON_ENTROPY_TOKEN",
                    severity="HIGH",
                    snippet=w[:24] + "...",
                    description=f"High Shannon entropy secret anomaly detected (H={entropy:.2f} bits/symbol, len={len(w)}).",
                    line_number=i
                ))

    # Compute Risk Score (0-100)
    risk_score = 0
    for f in findings:
        if f.severity == "CRITICAL":
            risk_score += 35
        elif f.severity == "HIGH":
            risk_score += 20
        elif f.severity == "MEDIUM":
            risk_score += 10
        else:
            risk_score += 5
    risk_score = min(100, risk_score)

    blocked = risk_score >= 50 or any(f.severity == "CRITICAL" for f in findings)

    # Sanitize content
    sanitized = content
    # Redact base64 image data URIs
    sanitized = BASE64_IMAGE_DATA_URI_REGEX.sub("[ZEROSPILL_REDACTED_BASE64_IMAGE_URI]", sanitized)
    sanitized = RAW_PNG_BASE64_REGEX.sub("[ZEROSPILL_REDACTED_RAW_PNG_BASE64]", sanitized)
    sanitized = RAW_JPEG_BASE64_REGEX.sub("[ZEROSPILL_REDACTED_RAW_JPEG_BASE64]", sanitized)

    # Redact known credential patterns
    for pattern, rule, _, _ in CREDENTIAL_REGEXES:
        sanitized = re.sub(pattern, f"[ZEROSPILL_REDACTED_{rule}]", sanitized)

    now = datetime.now(timezone.utc)

    # Save to SQLite
    audit = AirlockAudit(
        source_type=source_type,
        risk_score=risk_score,
        findings_json=json.dumps([f.model_dump() for f in findings]),
        raw_content_preview=content[:500],
        sanitized_content=sanitized[:10000],
        blocked=blocked,
        timestamp=now,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    return AirlockScanResponse(
        risk_score=risk_score,
        blocked=blocked,
        findings=findings,
        sanitized_content=sanitized,
        audit_id=audit.id,
        timestamp=now,
    )
