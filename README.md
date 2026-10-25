# 🛡️ ZeroSpill v2.0

> **Production-Grade Neural OCR Pixel-DLP, Honey-Token Trap & Live Agent Interceptor.**  
> *Zero external OS binaries. RapidOCR (ONNX) + pure Python Pillow + FastAPI + SQLite with a reactive dark-mode command center, CLI, and Git pre-commit hook.*

[![CI Pipeline](https://github.com/kkkavin/ZeroSpill/actions/workflows/ci.yml/badge.svg)](https://github.com/kkkavin/ZeroSpill/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![RapidOCR ONNX](https://img.shields.io/badge/OCR-RapidOCR%20ONNX-orange.svg)](https://github.com/RapidAI/RapidOCR)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![Zero External Binaries](https://img.shields.io/badge/Binaries-Pure%20Python%20Only-emerald.svg)](#core-engineering-principle)

---

## 🚀 What's New in v2.0

- 🧠 **Real Neural OCR via RapidOCR (ONNX Runtime):** Replaced heuristic bands with production-grade text recognition. Extracts exact polygon boxes and evaluates tokens against strict credential & PII signatures.
- 🎯 **Zero False Positives Guaranteed:** Normal UI screenshots, documentation, student dashboards, and clean code are recognized as **100% SAFE** (`boxes: []`, `secrets_detected: 0`) and remain crisp and unblurred.
- 🪤 **Real File-System Honey-Tokens & Canary URL:** `POST /api/v1/honeytrap/plant-file` seeds decoy `.env` files on disk with a live canary URL (`http://127.0.0.1:8000/api/v1/honeytrap/canary/<token_id>`). If an agent curls or fetches this URL, the circuit breaker engages instantly.
- 🪝 **AI Agent Git Pre-Commit Hook & CLI (`zerospill_cli.py`):** Standalone CLI tool that scans staged git files (`scan-staged`) and installs `.git/hooks/pre-commit` and `.agents/rules/zerospill-guard.md` in 1 click.
- 🧹 **1-Click Database Reset:** `POST /api/v1/admin/reset-db` wipes all demo logs and test decoys so users can reset to a clean slate.
- 🎛️ **Production Mode vs Sandbox Demo Mode Switch:** Built-in UI toggle in the dashboard header.

---

## 🚨 The Threat Model

Autonomous AI coding agents (such as Claude Computer Use, Cline, SWE-agent, OpenHands, and Devin) operate with unrestricted tool calling, terminal access, and optical screen-capture capabilities. This creates three critical attack vectors:

1. **Pixel-Leak Screen Ingestion (CWE-200 / CWE-532):**  
   Autonomous agents capture desktop, IDE, or browser screenshots to inspect errors. These images regularly contain visible API keys (`OPENAI_API_KEY=sk-proj-...`), production database connection strings (`postgresql://admin:...`), or payment handles (`merchant@okaxis`), which get embedded into unencrypted agent traces and committed to repositories.
2. **Autonomous Tool Scavenging (CERT-In CIAD-2026-0049 Defense):**  
   Adversarial prompts or hallucinatory agent steps cause tools to scavenge credential files (`cat .env.production`, `cat ~/.aws/credentials`) or trigger destructive database wipeouts (`DROP DATABASE`, `rm -rf /`).
3. **Poisoned `SKILL.md` & Leaky JSONL Trace Airlock Violations:**  
   Agent skill definition files and raw `.jsonl` conversation trajectories often contain embedded unredacted base64 image strings (`data:image/png;base64,...`) and covert exfiltration scripts (`gh gist create --public`, `curl -F file=@.env`).

**ZeroSpill** serves as an autonomous, self-contained firewall and data-loss prevention airlock positioned between agent runtimes, tool executors, and version control.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Agent Runtime ["🤖 Autonomous AI Coding Agent Runtime"]
        T["Tool Invocation & Terminal Commands"]
        S["Desktop & Browser Screen Capture"]
        P["Agent Skill Definition (SKILL.md) & Traces (.jsonl)"]
        G["Git Pre-Commit Hook (zerospill_cli.py)"]
    end

    subgraph ZeroSpill Engine ["🛡️ ZeroSpill DLP Engine (FastAPI + SQLite)"]
        subgraph ModA ["Module A: RapidOCR Neural PixelShield"]
            A1["RapidOCR ONNX Text Line Extraction"]
            A2["Strict Secret & PII Pattern Classifier"]
            A3["GaussianBlur(r=14) Redactor & Label Badges"]
        end

        subgraph ModB ["Module B: Honey-Token Scavenge Trap"]
            B1["Synthetic Decoy Credential Generator (AWS, Railway, Postgres, Razorpay)"]
            B2["File-System Decoy Planter & Live Canary URL"]
            B3["Circuit Breaker: Instant Session Quarantine & Alert"]
        end

        subgraph ModC ["Module C: Skill & Trace Airlock"]
            C1["Base64 PNG/JPEG Regex Interceptor"]
            C2["Shannon Character Entropy Calculator (H >= 4.3 bits)"]
            C3["Exfiltration Neutralizer & Content Sanitizer"]
        end

        DB[("SQLite: zerospill.db\n(Audit Logs, Decoys, Incidents)")]
    end

    subgraph UI ["💻 Cybersecurity Command Center (React + Vite + Tailwind)"]
        D1["PixelLeak Redactor Viewer (Raw vs Safe Blur & OCR Log)"]
        D2["Honey-Token Scavenge & Canary Simulator"]
        D3["Skill & JSONL Airlock Quarantine & Sanitizer"]
        D4["Agent Hook & Integration Center"]
    end

    S --> ModA
    T --> ModB
    P --> ModC
    G --> ModA
    G --> ModC

    ModA --> DB
    ModB --> DB
    ModC --> DB

    DB --> UI
```

---

## ⚡ Core Engineering Principle: Zero External Binaries

ZeroSpill is built to run anywhere without requiring OS-level OCR or system packages:
- **No Tesseract-OCR binary required.**
- **No poppler-utils or ImageMagick installation.**
- **100% Pure Python + ONNX Runtime:** Uses `rapidocr-onnxruntime`, `Pillow`, `FastAPI`, `SQLAlchemy`, and `Pydantic v2`.
- Automated test suites pass with zero extra system dependencies across Windows, macOS, and Linux CI runners.

---

## 🚀 2-Minute Local Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+ (with npm)

### 1. Clone the Repository
```bash
git clone https://github.com/kkkavin/ZeroSpill.git
cd ZeroSpill
```

### 2. Start Backend Service
```bash
cd backend

# Create & activate virtual environment (optional)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI backend with Uvicorn
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Backend API will be live at `http://127.0.0.1:8000` (Interactive Swagger docs at `http://127.0.0.1:8000/docs`).

### 3. Start Frontend Dashboard
In a new terminal:
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Open `http://localhost:5173` in your browser to launch the ZeroSpill Command Center.

---

## 🪝 CLI & Git Pre-Commit Hook Integration

ZeroSpill includes a standalone root CLI (`zerospill_cli.py`) for live AI coding agent defense:

```bash
# 1. Install pre-commit hook & agent guardrail
python zerospill_cli.py install-hook

# 2. Audit all currently staged files before git commit
python zerospill_cli.py scan-staged

# 3. Check hook installation status
python zerospill_cli.py status
```

When an autonomous AI agent executes `git commit`, the pre-commit hook automatically scans all staged `.png`/`.jpg` images with RapidOCR and all text/skill files with Airlock. If leaks are detected, the commit is rejected with exit code `1`.

---

## 🛠️ The Defense Modules

### 1. Module A — RapidOCR PixelShield Redactor
- **`POST /api/v1/pixel/generate-sample`**: Synthesizes a high-contrast dark-mode developer screenshot containing terminal and devtools panes with exposed secrets. Runs it through RapidOCR and returns detected boxes and redacted base64.
- **`POST /api/v1/pixel/redact`**: Accepts raw image data, runs RapidOCR, applies `ImageFilter.GaussianBlur(radius=14)` strictly over recognized secret tokens, and logs telemetry in SQLite (`ImageScanLog`). Returns `is_safe: true` with zero blur for clean images.

### 2. Module B — Anti-Scavenging Honey-Token Trap & Canary
- **`POST /api/v1/honeytrap/deploy`**: Generates synthetic tripwires:
  - AWS: `AKIA_TRAP_...` (seeded at `~/.aws/credentials`)
  - Railway: `rwy_trap_...` (seeded at `.env.production`)
  - PostgreSQL: `postgresql://decoy_admin:trap_pass_...@db-prod.internal:5432` (seeded at `config/database.yml`)
  - Razorpay: `rzp_live_trap_...` (seeded at `.env.vault`)
- **`POST /api/v1/honeytrap/plant-file`**: Writes a real decoy `.env` file on disk with a live canary URL (`http://127.0.0.1:8000/api/v1/honeytrap/canary/<token_id>`).
- **`GET /api/v1/honeytrap/canary/{token_id}`**: If curled or fetched, immediately trips the circuit breaker and aborts the agent session.

### 3. Module C — Agent Skill & JSONL Trace Airlock
- **`POST /api/v1/airlock/scan`**: Ingests raw `SKILL.md` text or `.jsonl` session trajectories. Evaluates:
  - Embedded Base64 Image URIs (`data:image/png;base64,...`)
  - Public exfiltration pipelines (`gh gist create --public`, `curl -F`)
  - High Shannon Entropy Character Anomalies ($H \ge 4.30\text{ bits/char}$)
- Automatically strips dangerous payload regions and returns a sanitized copy safe for repository commits.

### 4. Admin & Clean Slate
- **`POST /api/v1/admin/reset-db`**: Instant 1-click purge of all SQLite rows across image logs, honey-tokens, alerts, and airlock audits.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Healthcheck and service heartbeat |
| `GET` | `/api/v1/dashboard/stats` | System telemetry counts and recent incident audit events |
| `POST` | `/api/v1/pixel/generate-sample` | Generates simulated dark-mode screenshot and runs OCR |
| `POST` | `/api/v1/pixel/redact` | Runs RapidOCR and redacts secret tokens with Gaussian blur |
| `POST` | `/api/v1/pixel/redact-file` | Multipart form upload for screenshot redaction |
| `POST` | `/api/v1/honeytrap/deploy` | Seeds decoy credentials in SQLite |
| `GET` | `/api/v1/honeytrap/tokens` | Lists active honey-token tripwires |
| `POST` | `/api/v1/honeytrap/plant-file` | Writes real decoy `.env` file on disk with Canary URL |
| `GET` | `/api/v1/honeytrap/canary/{id}` | Live canary trigger endpoint |
| `POST` | `/api/v1/honeytrap/inspect-command` | Inspects terminal command for scavenge attempts or destructive actions |
| `POST` | `/api/v1/airlock/scan` | Scans agent skill files or traces for data leaks and rogue rules |
| `POST` | `/api/v1/agent-integration/install-hook` | Programmatically installs Git pre-commit hook and agent guardrail |
| `GET` | `/api/v1/agent-integration/status` | Checks Git hook and agent rule installation status |
| `POST` | `/api/v1/admin/reset-db` | Wipes SQLite database to a 100% clean slate |

---

## 🧪 Automated Testing & Verification

Run the comprehensive `pytest` test suite:
```bash
cd backend
python -m pytest tests/test_zerospill.py -v
```

Output:
```text
tests/test_zerospill.py::test_health_check PASSED                        [ 11%]
tests/test_zerospill.py::test_pixel_shield_zero_false_positives PASSED   [ 22%]
tests/test_zerospill.py::test_pixel_shield_true_positive_ocr PASSED      [ 33%]
tests/test_zerospill.py::test_pixel_shield_generate_sample PASSED        [ 44%]
tests/test_zerospill.py::test_honeytrap_deploy_and_tokens PASSED         [ 55%]
tests/test_zerospill.py::test_honeytrap_plant_file_and_canary_trigger PASSED [ 66%]
tests/test_zerospill.py::test_honeytrap_inspect_command_scavenge_and_destructive PASSED [ 77%]
tests/test_zerospill.py::test_airlock_scan PASSED                        [ 88%]
tests/test_zerospill.py::test_admin_reset_db PASSED                      [100%]

======================== 9 passed in 14.61s ========================
```

Verify frontend production bundle:
```bash
cd frontend
npm run build
```

---

## 📜 License

ZeroSpill is distributed under the open-source **MIT License**. See [LICENSE](LICENSE) for details.
