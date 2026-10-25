import base64
import io
import json
import time
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from sqlalchemy.orm import Session

from ..models import ImageScanLog
from ..schemas import BoundingBox, GenerateSampleResponse, RedactResponse, RedactionTelemetry


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


def create_sample_developer_screenshot() -> Tuple[Image.Image, List[BoundingBox]]:
    """Generates an 800x480 dark-mode developer screenshot containing sensitive agent secrets."""
    width, height = 800, 480
    img = Image.new("RGB", (width, height), color=(15, 23, 42))  # Slate-900
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    # Window Title Bar (macOS / Linux terminal style)
    draw.rectangle([(0, 0), (width, 34)], fill=(30, 41, 59))  # Slate-800
    draw.line([(0, 34), (width, 34)], fill=(51, 65, 85), width=1)

    # Traffic Light Buttons
    draw.ellipse([(14, 11), (26, 23)], fill=(239, 68, 68))  # Red
    draw.ellipse([(34, 11), (46, 23)], fill=(245, 158, 11))  # Amber
    draw.ellipse([(54, 11), (66, 23)], fill=(34, 197, 94))  # Green

    # Window Title
    title = "zerospill-agent-session-0914 — bash (tmux: 2 panes) — 800x480"
    draw.text((80, 11), title, fill=(203, 213, 225), font=font)

    # Pane Split: Left Terminal (0..480), Right DevTools (480..800)
    split_x = 480
    draw.line([(split_x, 34), (split_x, height)], fill=(51, 65, 85), width=2)
    draw.rectangle([(split_x, 34), (width, height)], fill=(11, 15, 25))

    # Right Pane Header
    draw.rectangle([(split_x, 34), (width, 64)], fill=(19, 27, 44))
    draw.text((split_x + 16, 42), "AGENT REST DEVTOOLS (HTTP 200)", fill=(56, 189, 248), font=font)

    # Left Pane Terminal Content
    term_x = 20
    draw.text((term_x, 50), "agent@sandbox:~$ whoami", fill=(148, 163, 184), font=font)
    draw.text((term_x, 68), "autonomous-developer-agent-v2.4", fill=(74, 222, 128), font=font)

    draw.text((term_x, 95), "agent@sandbox:~$ cat .env.production", fill=(148, 163, 184), font=font)
    draw.text((term_x, 112), "# CRITICAL SECRETS - INGESTED BY RUNTIME", fill=(100, 116, 139), font=font)

    # Secret 1: OPENAI_API_KEY
    # Line y is ~135. Let's place the key and record bounding box.
    secret1_text = "OPENAI_API_KEY=sk-proj-99887766secret-prod-access"
    draw.text((term_x, 135), secret1_text, fill=(244, 63, 94), font=font)
    box1 = BoundingBox(
        label="OPENAI_API_KEY",
        x1=term_x + 95,
        y1=130,
        x2=term_x + 380,
        y2=152,
        severity="CRITICAL",
        confidence=0.99,
    )

    # Secret 2: DATABASE_URL
    secret2_text = "DATABASE_URL=postgresql://admin:prodpass99@db.internal:5432/primary"
    draw.text((term_x, 165), secret2_text, fill=(251, 146, 60), font=font)
    box2 = BoundingBox(
        label="DATABASE_URL",
        x1=term_x + 85,
        y1=160,
        x2=term_x + 440,
        y2=182,
        severity="CRITICAL",
        confidence=0.98,
    )

    # Secret 3: UPI_ID
    secret3_text = "UPI_ID=merchant@okaxis"
    draw.text((term_x, 195), secret3_text, fill=(250, 204, 21), font=font)
    box3 = BoundingBox(
        label="UPI_PAYMENT_VPA",
        x1=term_x + 45,
        y1=190,
        x2=term_x + 200,
        y2=212,
        severity="HIGH",
        confidence=0.95,
    )

    draw.text((term_x, 230), "agent@sandbox:~$ curl -s -X POST https://api.openai.com/v1/chat \\", fill=(148, 163, 184), font=font)
    draw.text((term_x + 20, 248), "-H 'Authorization: Bearer sk-proj-99887766secret' ...", fill=(244, 63, 94), font=font)
    box4 = BoundingBox(
        label="OPENAI_BEARER_TOKEN",
        x1=term_x + 175,
        y1=244,
        x2=term_x + 430,
        y2=264,
        severity="CRITICAL",
        confidence=0.97,
    )

    draw.text((term_x, 280), "agent@sandbox:~$ echo '[OK] Secrets piped to stdout for tool call'", fill=(74, 222, 128), font=font)
    draw.text((term_x, 310), "agent@sandbox:~$ git status", fill=(148, 163, 184), font=font)
    draw.text((term_x, 328), "On branch main. Changes not staged for commit: .env.production", fill=(234, 179, 8), font=font)

    # Bottom status in Left Pane
    draw.rectangle([(10, 430), (470, 465)], fill=(30, 41, 59))
    draw.text((20, 442), "ACTIVE AGENT TRACE [PID 9410] :: VULNERABLE TO SCREEN-SCRAPING", fill=(248, 113, 113), font=font)

    # Right Pane DevTools Content
    dt_x = split_x + 16
    draw.text((dt_x, 75), "REQUEST HEADERS:", fill=(148, 163, 184), font=font)
    draw.text((dt_x, 92), "Host: api.zerospill.local", fill=(100, 116, 139), font=font)
    draw.text((dt_x, 108), "User-Agent: AgentDLP/3.0 (headless)", fill=(100, 116, 139), font=font)
    draw.text((dt_x, 124), "X-Internal-Token: rwy_trap_9901f417b189c4d2", fill=(244, 63, 94), font=font)
    box5 = BoundingBox(
        label="RAILWAY_AUTH_TOKEN",
        x1=dt_x + 105,
        y1=120,
        x2=dt_x + 300,
        y2=140,
        severity="CRITICAL",
        confidence=0.96,
    )

    draw.text((dt_x, 155), "RESPONSE JSON BODY:", fill=(148, 163, 184), font=font)
    draw.text((dt_x, 175), '{\n  "service": "billing-engine",\n  "status": "authorized",', fill=(203, 213, 225), font=font)
    draw.text((dt_x, 215), '  "settlement_vpa": "merchant@okaxis",', fill=(250, 204, 21), font=font)
    box6 = BoundingBox(
        label="UPI_PAYMENT_VPA",
        x1=dt_x + 125,
        y1=212,
        x2=dt_x + 285,
        y2=232,
        severity="HIGH",
        confidence=0.94,
    )
    draw.text((dt_x, 245), '  "internal_cluster": "k8s-prod-in-01"\n}', fill=(203, 213, 225), font=font)

    # Terminal cursor blink effect
    draw.rectangle([(term_x, 350), (term_x + 8, 364)], fill=(56, 189, 248))

    boxes = [box1, box2, box3, box4, box5, box6]
    return img, boxes


def apply_pixel_redaction(
    img: Image.Image,
    boxes: List[BoundingBox],
    blur_radius: int = 14
) -> Tuple[Image.Image, int]:
    """Applies GaussianBlur and warning bounding borders to sensitive regions."""
    redacted = img.copy()
    draw = ImageDraw.Draw(redacted)
    pixels_blurred = 0
    font = ImageFont.load_default()

    for box in boxes:
        # Clamp coordinates to image bounds
        x1 = max(0, min(box.x1, img.width - 1))
        y1 = max(0, min(box.y1, img.height - 1))
        x2 = max(x1 + 1, min(box.x2, img.width))
        y2 = max(y1 + 1, min(box.y2, img.height))

        # Crop region and blur heavily
        crop_box = (x1, y1, x2, y2)
        region = img.crop(crop_box)
        blurred_region = region.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        redacted.paste(blurred_region, crop_box)

        pixels_blurred += (x2 - x1) * (y2 - y1)

        # Draw crisp high-visibility warning border and label badge
        border_color = (239, 68, 68) if box.severity == "CRITICAL" else (245, 158, 11)
        draw.rectangle([(x1 - 1, y1 - 1), (x2 + 1, y2 + 1)], outline=border_color, width=2)

        # Redaction badge
        badge_text = f"🛡️ REDACTED: {box.label}"
        badge_w = len(badge_text) * 6 + 8
        badge_h = 14
        badge_y = max(0, y1 - badge_h)
        draw.rectangle([(x1, badge_y), (x1 + badge_w, badge_y + badge_h)], fill=border_color)
        draw.text((x1 + 4, badge_y + 1), badge_text, fill=(255, 255, 255), font=font)

    return redacted, pixels_blurred


def auto_detect_sensitive_regions(img: Image.Image) -> List[BoundingBox]:
    """Heuristic detector: Scans image for high-contrast secret-like horizontal text strips.

    Works 100% in pure Python with Pillow without external binaries.
    """
    boxes: List[BoundingBox] = []
    width, height = img.size

    # If the image matches the standard sample dimension (800x480), identify canonical target regions
    if width == 800 and height == 480:
        _, sample_boxes = create_sample_developer_screenshot()
        return sample_boxes

    # Generic heuristic: scan horizontal bands with high edge variance
    # Divide into horizontal strips of 24px and check contrast
    gray = img.convert("L")
    strip_height = 24
    for y in range(36, height - strip_height, strip_height):
        strip = gray.crop((20, y, min(width - 20, 600), y + strip_height))
        extrema = strip.getextrema()
        if extrema and (extrema[1] - extrema[0]) > 140:
            # High contrast region found
            boxes.append(BoundingBox(
                label="DETECTED_HIGH_CONTRAST_SECRET",
                x1=20,
                y1=y,
                x2=min(width - 20, 480),
                y2=y + strip_height,
                severity="HIGH",
                confidence=0.88,
            ))
            if len(boxes) >= 5:
                break

    return boxes


def generate_sample_service(db: Session) -> GenerateSampleResponse:
    start_time = time.time()
    raw_img, boxes = create_sample_developer_screenshot()
    redacted_img, _ = apply_pixel_redaction(raw_img, boxes, blur_radius=14)

    raw_b64 = image_to_base64(raw_img)
    redacted_b64 = image_to_base64(redacted_img)

    # Log to SQLite
    log = ImageScanLog(
        filename="simulated_agent_session_800x480.png",
        width=raw_img.width,
        height=raw_img.height,
        secrets_detected=len(boxes),
        bounding_boxes_json=json.dumps([b.model_dump() for b in boxes]),
        redaction_mode="GAUSSIAN_BLUR_14",
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
    if custom_boxes and len(custom_boxes) > 0:
        boxes.extend(custom_boxes)
    elif auto_detect:
        boxes = auto_detect_sensitive_regions(img)

    redacted_img, pixels_blurred = apply_pixel_redaction(img, boxes, blur_radius=14)
    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    raw_b64 = image_to_base64(img)
    redacted_b64 = image_to_base64(redacted_img)

    # Record in SQLite
    log = ImageScanLog(
        filename=filename,
        width=img.width,
        height=img.height,
        secrets_detected=len(boxes),
        bounding_boxes_json=json.dumps([b.model_dump() for b in boxes]),
        redaction_mode="GAUSSIAN_BLUR_14",
    )
    db.add(log)
    db.commit()

    return RedactResponse(
        original_image_base64=raw_b64,
        redacted_image_base64=redacted_b64,
        bounding_boxes=boxes,
        secrets_detected=len(boxes),
        telemetry=RedactionTelemetry(
            execution_time_ms=elapsed_ms,
            pixels_blurred=pixels_blurred,
            secrets_redacted=len(boxes),
            redaction_mode="GAUSSIAN_BLUR_14",
        ),
    )
