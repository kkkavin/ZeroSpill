# 🛡️ ZeroSpill

> **Open-Source Pixel-DLP, Honey-Token Trap & Skill Airlock for Autonomous AI Coding Agents.**  
> *Zero external OS binaries. 100% pure Python Pillow + FastAPI + SQLite with a reactive dark-mode command center.*

[![CI Pipeline](https://github.com/kkkavin/ZeroSpill/actions/workflows/ci.yml/badge.svg)](https://github.com/kkkavin/ZeroSpill/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![Zero External Binaries](https://img.shields.io/badge/Binaries-Pure%20Python%20Only-emerald.svg)](#core-engineering-principle)

---

## 🚨 The Threat Model

Autonomous AI coding agents (such as Claude Computer Use, Cline, SWE-agent, OpenHands, and autonomous GitHub bots) operate with unrestricted tool calling, terminal access, and optical screen-capture capabilities. This creates three critical attack vectors:

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
    end

    subgraph ZeroSpill Engine ["🛡️ ZeroSpill DLP Engine (FastAPI + SQLite)"]
        subgraph ModA ["Module A: PixelShield Optical DLP"]
            A1["Pillow Synthetic Image Synthesizer"]
            A2["High-Contrast Band Secret Detector"]
            A3["GaussianBlur(r=14) Redactor & Label Badge"]
        end

        subgraph ModB ["Module B: Honey-Token Scavenge Trap"]
            B1["Synthetic Decoy Credential Generator (AWS, Railway, Postgres, Razorpay)"]
            B2["Command & Trace Pattern Inspection Engine"]
            B3["Circuit Breaker: Instant Session Quarantine & Alert"]
        end

        subgraph ModC ["Module C: Skill & Trace Airlock"]
            C1["Base64 PNG/JPEG Regex Interceptor"]
            C2["Shannon Character Entropy Calculator (H >= 4.2 bits)"]
            C3["Exfiltration Neutralizer & Content Sanitizer"]
        end

        DB[("SQLite: zerospill.db\n(Audit Logs, Decoys, Incidents)")]
    end

    subgraph UI ["💻 Cybersecurity Command Center (React + Vite + Tailwind)"]
        D1["PixelLeak Redactor Viewer (Raw vs Safe Blur)"]
        D2["Honey-Token Scavenge Attack Simulator"]
        D3["Skill & JSONL Airlock Quarantine & Sanitizer"]
        D4["Global Telemetry & Real-Time Security Stream"]
    end

    S --> ModA
    T --> ModB
    P --> ModC

    ModA --> DB
    ModB --> DB
    ModC --> DB

    DB --> UI
```

---

## ⚡ Core Engineering Principle: Zero External Binaries

ZeroSpill is built from the ground up to run anywhere without requiring OS-level OCR or system packages:
- **No Tesseract-OCR binary required.**
- **No poppler-utils or ImageMagick installation.**
- **100% Pure Python:** Uses `Pillow`, `FastAPI`, `SQLAlchemy`, `Pydantic v2`, and `httpx`.
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

## 🛠️ The 3 Defense Modules

### 1. Module A — PixelShield Image Redactor
- **`POST /api/v1/pixel/generate-sample`**: Synthesizes a pixel-perfect 800x480 dark-mode developer screenshot containing terminal and devtools panes with exposed `OPENAI_API_KEY`, `DATABASE_URL`, `UPI_ID`, and `RAILWAY_AUTH_TOKEN`.
- **`POST /api/v1/pixel/redact`**: Accepts raw image data, applies `ImageFilter.GaussianBlur(radius=14)` over sensitive bounding boxes, renders prominent border tags, and logs redaction telemetry in SQLite (`ImageScanLog`).

### 2. Module B — Anti-Scavenging Honey-Token Trap
- **`POST /api/v1/honeytrap/deploy`**: Generates synthetic tripwires:
  - AWS: `AKIA_TRAP_...` (seeded at `~/.aws/credentials`)
  - Railway: `rwy_trap_...` (seeded at `.env.production`)
  - PostgreSQL: `postgresql://decoy_admin:trap_pass_...@db-prod.internal:5432` (seeded at `config/database.yml`)
  - Razorpay: `rzp_live_trap_...` (seeded at `.env.vault`)
- **`POST /api/v1/honeytrap/inspect-command`**: Evaluates agent tool calls in real time. Tripping a decoy credential or executing destructive commands (`DROP DATABASE`, `rm -rf /`, `gh repo create --public`) engages the **ZeroSpill Circuit-Breaker**, aborting the agent process and recording an incident alert in SQLite (`TrapAlert`).

### 3. Module C — Agent Skill & JSONL Trace Airlock
- **`POST /api/v1/airlock/scan`**: Ingests raw `SKILL.md` text or `.jsonl` session trajectories. Evaluates:
  - Embedded Base64 Image URIs (`data:image/png;base64,...`)
  - Public exfiltration pipelines (`gh gist create --public`, `curl -F`)
  - High Shannon Entropy Character Anomalies ($H \ge 4.25\text{ bits/char}$)
- Automatically strips dangerous payload regions and returns a sanitized copy safe for repository commits.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Healthcheck and service heartbeat |
| `GET` | `/api/v1/dashboard/stats` | System telemetry counts and recent incident audit events |
| `POST` | `/api/v1/pixel/generate-sample` | Generates synthetic dark-mode agent screenshot with detected secrets |
| `POST` | `/api/v1/pixel/redact` | Redacts base64 images with Gaussian blur & border overlays |
| `POST` | `/api/v1/pixel/redact-file` | Multipart form upload for screenshot redaction |
| `POST` | `/api/v1/honeytrap/deploy` | Seeds decoy credentials across cloud, database, and payment formats |
| `GET` | `/api/v1/honeytrap/tokens` | Lists active honey-token tripwires |
| `POST` | `/api/v1/honeytrap/inspect-command` | Inspects terminal command for scavenge attempts or destructive actions |
| `POST` | `/api/v1/airlock/scan` | Scans agent skill files or traces for data leaks and rogue rules |
| `GET` | `/api/v1/airlock/audits` | Retrieves chronological history of airlock audits |

---

## 🧪 Automated Testing & Verification

Run the comprehensive `pytest` test suite:
```bash
cd backend
python -m pytest tests/test_zerospill.py -v
```

Output:
```text
tests/test_zerospill.py::test_health_check PASSED                        [ 10%]
tests/test_zerospill.py::test_pixel_shield_generate_sample PASSED        [ 20%]
tests/test_zerospill.py::test_pixel_shield_redact PASSED                 [ 30%]
tests/test_zerospill.py::test_honeytrap_deploy_and_tokens PASSED         [ 40%]
tests/test_zerospill.py::test_honeytrap_inspect_command_safe PASSED      [ 50%]
tests/test_zerospill.py::test_honeytrap_inspect_command_honeytoken_scavenge PASSED [ 60%]
tests/test_zerospill.py::test_honeytrap_inspect_command_destructive_patterns PASSED [ 70%]
tests/test_zerospill.py::test_airlock_scan_safe_content PASSED           [ 80%]
tests/test_zerospill.py::test_airlock_scan_embedded_base64_and_exfil PASSED [ 90%]
tests/test_zerospill.py::test_dashboard_stats PASSED                     [100%]

======================== 10 passed in 3.01s ========================
```

Verify frontend production bundle:
```bash
cd frontend
npm run build
```

---

## 📜 License

ZeroSpill is distributed under the open-source **MIT License**. See [LICENSE](LICENSE) for details.
