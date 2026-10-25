import base64
from collections import Counter
from datetime import datetime, timezone
import io
import json
import math
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from rapidocr_onnxruntime import RapidOCR
from sqlalchemy.orm import Session

from ..models import ImageScanLog
from ..schemas import BoundingBox, GenerateSampleResponse, OCRLine, RedactResponse, RedactionTelemetry

# Lazy-loaded singleton OCR instance
_OCR_ENGINE: Optional[RapidOCR] = None


def get_ocr_engine() -> RapidOCR:
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        _OCR_ENGINE = RapidOCR()
    return _OCR_ENGINE


def image_to_base64(img: Image.Image, format: str = "PNG") -> str:
    buffered = io.BytesIO()
    img.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/{format.lower()};base64,{img_str}"


def base64_to_image(b64_string: str) -> Image.Image:
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]
    image_bytes = base64.b64decode(b64_string)
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def shannon_entropy(text: str) -> float:
    """Calculates the Shannon entropy of a string in bits per symbol."""
    if not text:
        return 0.0
    length = len(text)
    counts = Counter(text)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return round(entropy, 3)


# Strict Regex Rules for Secrets & Sensitive PII
SECRET_PATTERNS = [
    # a) Secret assignments & specific prefixes
    (r"(?i)\b(?:OPENAI_API_KEY|API_KEY|SECRET_KEY|SECRET|TOKEN|PASSWORD|PASSWD|AUTH_TOKEN)\b\s*[:=]\s*['\"]?([^\s'\"]{6,})", "CREDENTIAL_ASSIGNMENT", "CRITICAL"),
    (r"\bsk-proj-[a-zA-Z0-9_\-]{16,}\b", "OPENAI_PROJECT_KEY", "CRITICAL"),
    (r"\bsk-[a-zA-Z0-9]{20,}\b", "OPENAI_LEGACY_KEY", "CRITICAL"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS_ACCESS_KEY_ID", "CRITICAL"),
    (r"\bghp_[a-zA-Z0-9]{30,}\b", "GITHUB_PAT", "CRITICAL"),
    (r"\bgho_[a-zA-Z0-9]{30,}\b", "GITHUB_OAUTH_TOKEN", "CRITICAL"),
    (r"\brwy_trap_[a-zA-Z0-9]{8,}\b", "RAILWAY_TRAP_TOKEN", "CRITICAL"),
    (r"\brwy_[a-zA-Z0-9]{16,}\b", "RAILWAY_PROD_TOKEN", "CRITICAL"),
    (r"\brzp_live_[a-zA-Z0-9]{10,}\b", "RAZORPAY_LIVE_SECRET", "CRITICAL"),
    (r"\brzp_test_[a-zA-Z0-9]{10,}\b", "RAZORPAY_TEST_SECRET", "HIGH"),

    # b) Connection URIs with credentials
    (r"(?i)\b(?:postgresql|postgres|mongodb(?:\+srv)?|mysql|redis):\/\/[a-zA-Z0-9_\-\.]+:[^@\s]+@[^\s]+\b", "DATABASE_URI_WITH_CREDS", "CRITICAL"),
    (r"(?i)\bDATABASE_URL\s*[:=]\s*[^\s]+", "DATABASE_URL_CONFIG", "CRITICAL"),

    # c) PII patterns
    (r"\b[a-zA-Z0-9.\-_]{2,}@(okaxis|okhdfcbank|okicici|oksbi|paytm|ybl|upi|apl)\b", "UPI_PAYMENT_VPA", "HIGH"),
    (r"\bUPI_ID\s*[:=]\s*[a-zA-Z0-9.\-_@]+\b", "UPI_PAYMENT_VPA", "HIGH"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "PII_EMAIL_ADDRESS", "HIGH"),
    (r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "PII_PHONE_NUMBER", "HIGH"),
    (r"\b(?:\d{4}[-\s]){3}\d{4}\b", "PII_CREDIT_CARD_BLOCK", "CRITICAL"),
    (r"\b\d{4}\s\d{4}\s\d{4}\b", "PII_AADHAAR_BLOCK", "HIGH"),
]


def mask_secret(text: str) -> str:
    """Produces a safe masked representation of recognized secret text."""
    if len(text) <= 8:
        return text[:2] + "***"
    return text[:6] + "..." + text[-4:] + " [MASKED]"


def classify_ocr_text(text: str) -> Optional[Tuple[str, str, str]]:
    """Evaluates recognized text against strict secret and PII rules.

    Returns (label, severity, masked_text) if a secret is found, else None.
    NEVER flags normal English prose, UI labels, or standard safe code.
    """
    clean_text = text.strip()
    if not clean_text or len(clean_text) < 4:
        return None

    # Ignore common benign code/terminal prompts that might look like keywords
    lower = clean_text.lower()
    if lower in ("git status", "npm run test", "pytest", "ls -la", "cd ..", "python main.py"):
        return None

    # Check against known secret / PII patterns
    for pattern, rule_label, severity in SECRET_PATTERNS:
        match = re.search(pattern, clean_text)
        if match:
            matched_str = match.group(0)
            return (rule_label, severity, mask_secret(matched_str))

    # d) Check for high-entropy secret tokens:
    # Must be a continuous token (len >= 16, no spaces), high Shannon entropy (>= 4.30 bits),
    # and contain mixed character classes (lowercase + uppercase + digits/symbols)
    words = clean_text.split()
    for w in words:
        # Strip common punctuation quotes
        w_clean = w.strip("'\",;()[]{}")
        if len(w_clean) >= 16 and not w_clean.startswith("http") and not "/" in w_clean:
            has_upper = any(c.isupper() for c in w_clean)
            has_lower = any(c.islower() for c in w_clean)
            has_digit = any(c.isdigit() for c in w_clean)
            classes = sum([has_upper, has_lower, has_digit])
            if classes >= 2:
                entropy = shannon_entropy(w_clean)
                if entropy >= 4.30:
                    return ("HIGH_SHANNON_ENTROPY_SECRET", "HIGH", mask_secret(w_clean))

    return None


def run_neural_ocr_scan(img: Image.Image) -> Tuple[List[BoundingBox], List[OCRLine]]:
    """Runs RapidOCR on the image and returns genuine secret bounding boxes and all OCR text lines."""
    ocr = get_ocr_engine()
    np_img = np.array(img)

    result, _ = ocr(np_img)
    if not result:
        return [], []

    boxes: List[BoundingBox] = []
    ocr_lines: List[OCRLine] = []

    for item in result:
        # RapidOCR format: [polygon_box, text, confidence]
        poly, text, score = item[0], str(item[1]), float(item[2])
        ocr_lines.append(OCRLine(text=text, confidence=round(score, 3)))

        classification = classify_ocr_text(text)
        if classification:
            label, severity, masked = classification
            # Convert 4-point polygon to [x1, y1, x2, y2]
            xs = [pt[0] for pt in poly]
            ys = [pt[1] for pt in poly]
            min_x = max(0, int(min(xs)) - 3)
            min_y = max(0, int(min(ys)) - 3)
            max_x = min(img.width, int(max(xs)) + 3)
            max_y = min(img.height, int(max(ys)) + 3)

            boxes.append(BoundingBox(
                label=label,
                x1=min_x,
                y1=min_y,
                x2=max_x,
                y2=max_y,
                severity=severity,
                confidence=round(score, 3),
                masked_text=masked,
            ))

    return boxes, ocr_lines


def apply_pixel_redaction(
    img: Image.Image,
    boxes: List[BoundingBox],
    blur_radius: int = 14
) -> Tuple[Image.Image, int]:
    """Applies GaussianBlur(radius=14) and warning bounding borders strictly over sensitive regions."""
    if not boxes:
        return img.copy(), 0

    redacted = img.copy()
    draw = ImageDraw.Draw(redacted)
    pixels_blurred = 0
    font = ImageFont.load_default()

    for box in boxes:
        x1 = max(0, min(box.x1, img.width - 1))
        y1 = max(0, min(box.y1, img.height - 1))
        x2 = max(x1 + 1, min(box.x2, img.width))
        y2 = max(y1 + 1, min(box.y2, img.height))

        crop_box = (x1, y1, x2, y2)
        region = img.crop(crop_box)
        blurred_region = region.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        redacted.paste(blurred_region, crop_box)

        pixels_blurred += (x2 - x1) * (y2 - y1)

        border_color = (239, 68, 68) if box.severity == "CRITICAL" else (245, 158, 11)
        draw.rectangle([(x1 - 1, y1 - 1), (x2 + 1, y2 + 1)], outline=border_color, width=2)

        badge_text = f"REDACTED: {box.label}"
        badge_w = len(badge_text) * 6 + 8
        badge_h = 14
        badge_y = max(0, y1 - badge_h)
        draw.rectangle([(x1, badge_y), (x1 + badge_w, badge_y + badge_h)], fill=border_color)
        draw.text((x1 + 4, badge_y + 1), badge_text, fill=(255, 255, 255), font=font)

    return redacted, pixels_blurred


def create_sample_developer_screenshot() -> Image.Image:
    """Generates an 800x480 dark-mode developer screenshot with high-contrast text for OCR."""
    width, height = 800, 480
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    # Title bar
    draw.rectangle([(0, 0), (width, 34)], fill=(30, 41, 59))
    draw.ellipse([(14, 11), (26, 23)], fill=(239, 68, 68))
    draw.ellipse([(34, 11), (46, 23)], fill=(245, 158, 11))
    draw.ellipse([(54, 11), (66, 23)], fill=(34, 197, 94))
    draw.text((80, 11), "agent-session-0914 — bash (tmux: 2 panes) — 800x480", fill=(203, 213, 225), font=font)

    # Split panes
    split_x = 440
    draw.line([(split_x, 34), (split_x, height)], fill=(51, 65, 85), width=2)
    draw.rectangle([(split_x, 34), (width, height)], fill=(11, 15, 25))

    # Left pane text
    tx = 20
    draw.text((tx, 50), "agent@sandbox:~$ cat .env.production", fill=(148, 163, 184), font=font)
    draw.text((tx, 75), "# PRODUCTION SECRETS", fill=(100, 116, 139), font=font)
    draw.text((tx, 105), "OPENAI_API_KEY=sk-proj-99887766secretKey12345", fill=(244, 63, 94), font=font)
    draw.text((tx, 140), "DATABASE_URL=postgresql://admin:prodpass99@db.internal:5432/main", fill=(251, 146, 60), font=font)
    draw.text((tx, 175), "UPI_ID=merchant@okaxis", fill=(250, 204, 21), font=font)
    draw.text((tx, 210), "AWS_ACCESS_KEY_ID=AKIA9988776655443322", fill=(244, 63, 94), font=font)
    draw.text((tx, 250), "agent@sandbox:~$ git commit -m 'feat: add runtime'", fill=(148, 163, 184), font=font)

    # Right pane devtools
    dx = split_x + 16
    draw.text((dx, 50), "REST API DEVTOOLS [POST /v1/auth]", fill=(56, 189, 248), font=font)
    draw.text((dx, 85), "X-Railway-Token: rwy_trap_9901f417b189c4d2", fill=(244, 63, 94), font=font)
    draw.text((dx, 120), "Settlement: merchant@okaxis", fill=(250, 204, 21), font=font)
    draw.text((dx, 155), "Razorpay: rzp_live_99887766aabbcc", fill=(244, 63, 94), font=font)

    return img


def generate_sample_service(db: Session) -> GenerateSampleResponse:
    raw_img = create_sample_developer_screenshot()
    boxes, ocr_lines = run_neural_ocr_scan(raw_img)
    redacted_img, _ = apply_pixel_redaction(raw_img, boxes, blur_radius=14)

    raw_b64 = image_to_base64(raw_img)
    redacted_b64 = image_to_base64(redacted_img)

    log = ImageScanLog(
        filename="simulated_agent_session_800x480.png",
        width=raw_img.width,
        height=raw_img.height,
        secrets_detected=len(boxes),
        bounding_boxes_json=json.dumps([b.model_dump() for b in boxes]),
        redaction_mode="NEURAL_RAPIDOCR_GAUSSIAN_BLUR_14",
    )
    db.add(log)
    db.commit()

    return GenerateSampleResponse(
        original_image_base64=raw_b64,
        redacted_image_base64=redacted_b64,
        bounding_boxes=boxes,
        secrets_detected=len(boxes),
        width=raw_img.width,
        height=raw_img.height,
        is_safe=len(boxes) == 0,
        ocr_lines=ocr_lines,
    )


def redact_image_service(
    db: Session,
    img: Image.Image,
    filename: str = "uploaded_screenshot.png",
    custom_boxes: Optional[List[BoundingBox]] = None,
    auto_detect: bool = True
) -> RedactResponse:
    start_time = time.time()

    boxes: List[BoundingBox] = []
    ocr_lines: List[OCRLine] = []

    if custom_boxes and len(custom_boxes) > 0:
        boxes.extend(custom_boxes)
    elif auto_detect:
        # Run real Neural OCR
        detected_boxes, ocr_lines = run_neural_ocr_scan(img)
        boxes.extend(detected_boxes)

    redacted_img, pixels_blurred = apply_pixel_redaction(img, boxes, blur_radius=14)
    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    raw_b64 = image_to_base64(img)
    redacted_b64 = image_to_base64(redacted_img)

    log = ImageScanLog(
        filename=filename,
        width=img.width,
        height=img.height,
        secrets_detected=len(boxes),
        bounding_boxes_json=json.dumps([b.model_dump() for b in boxes]),
        redaction_mode="NEURAL_RAPIDOCR_GAUSSIAN_BLUR_14",
    )
    db.add(log)
    db.commit()

    return RedactResponse(
        original_image_base64=raw_b64,
        redacted_image_base64=redacted_b64,
        bounding_boxes=boxes,
        secrets_detected=len(boxes),
        is_safe=len(boxes) == 0,
        ocr_lines=ocr_lines,
        telemetry=RedactionTelemetry(
            execution_time_ms=elapsed_ms,
            pixels_blurred=pixels_blurred,
            secrets_redacted=len(boxes),
            redaction_mode="NEURAL_RAPIDOCR_GAUSSIAN_BLUR_14",
            ocr_lines_processed=len(ocr_lines),
        ),
    )
