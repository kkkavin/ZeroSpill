#!/usr/bin/env python3
"""ZeroSpill CLI: Pre-Commit Defense Gate & Agent Interceptor.

Scans git staged files for optical pixel leaks, honey-token scavenging, and airlock violations.
"""

import os
from pathlib import Path
import subprocess
import sys

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure backend package is in python search path
REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from PIL import Image
    from app.database import Base, SessionLocal, engine
    from app.services.agent_integration import install_git_hook_and_rule
    from app.services.airlock import scan_airlock_content
    from app.services.honey_trap import inspect_agent_command
    from app.services.pixel_shield import run_neural_ocr_scan
except ImportError as e:
    print(f"[ZeroSpill CLI Error] Failed to load ZeroSpill backend engine: {e}")
    sys.exit(1)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
DOC_OR_SELF_FILES = {
    "zerospill-guard.md",
    "README.md",
    "zerospill_cli.py",
    "test_zerospill.py",
    "agent_integration.py",
    "airlock.py",
    "honey_trap.py",
    "pixel_shield.py",
}


def get_staged_files():
    """Returns a list of relative paths for all git staged files."""
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(REPO_ROOT),
        )
        files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
        return files
    except Exception as e:
        print(f"[ZeroSpill CLI Warning] Unable to query git staged files: {e}")
        return []


def scan_staged_command():
    staged = get_staged_files()
    if not staged:
        print("🛡️  [ZeroSpill] No git staged files detected. Commit gate cleared.")
        sys.exit(0)

    print(f"🛡️  [ZeroSpill] Scanning {len(staged)} staged file(s) for pixel-DLP leaks & honey-tokens...")

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    violations = []

    try:
        for file_rel in staged:
            file_name = Path(file_rel).name
            if file_name in DOC_OR_SELF_FILES:
                continue

            file_path = REPO_ROOT / file_rel
            if not file_path.is_file():
                continue

            ext = file_path.suffix.lower()

            # 1. Optical Pixel-DLP check for image assets
            if ext in IMAGE_EXTENSIONS:
                try:
                    with Image.open(file_path) as img:
                        boxes, ocr_lines = run_neural_ocr_scan(img)
                        if boxes:
                            for b in boxes:
                                violations.append({
                                    "file": file_rel,
                                    "type": "OPTICAL_PIXEL_LEAK",
                                    "severity": b.severity,
                                    "detail": f"OCR detected {b.label} ({b.masked_text or 'secret'}) at ({b.x1},{b.y1})",
                                })
                except Exception as ex:
                    print(f"  [Warning] Could not inspect image {file_rel}: {ex}")

            # 2. Text, Code, SKILL.md, or .jsonl files check
            else:
                try:
                    # Ignore binary or very large files
                    if file_path.stat().st_size > 5 * 1024 * 1024:
                        continue
                    text_content = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                source_type = "SKILL_MD" if "SKILL" in file_rel.upper() else ("JSONL_TRACE" if ext == ".jsonl" else "CODE_FILE")

                # Airlock audit for embedded base64 screenshots and live API credentials
                audit = scan_airlock_content(db, text_content, source_type=source_type)
                if audit.blocked:
                    for f in audit.findings:
                        violations.append({
                            "file": file_rel,
                            "type": f"AIRLOCK_{f.rule}",
                            "severity": f.severity,
                            "detail": f"{f.description} - Snippet: '{f.snippet}'",
                        })

                # Honey-trap check for scripts and agent trace files
                if ext in (".sh", ".bash", ".zsh", ".jsonl") or "hook" in file_rel.lower():
                    honey_res = inspect_agent_command(db, text_content[:2000])
                    if honey_res.blocked:
                        violations.append({
                            "file": file_rel,
                            "type": "HONEY_TOKEN_SCAVENGE",
                            "severity": honey_res.severity,
                            "detail": honey_res.explanation,
                        })

    finally:
        db.close()

    # Verdict
    if violations:
        print("\n" + "=" * 80)
        print("❌ [ZeroSpill Gate] COMMIT REJECTED: Sensitive Security Violations Detected!")
        print("=" * 80)
        for v in violations:
            print(f"  • [{v['severity']}] {v['file']} ➜ {v['type']}: {v['detail']}")
        print("=" * 80)
        print("Remediation: Sanitize credentials with ZeroSpill PixelShield or remove tripwires.")
        sys.exit(1)

    print("✅ [ZeroSpill Gate] All staged files verified clean. Zero credentials or pixel leaks detected.")
    sys.exit(0)


def install_hook_command():
    res = install_git_hook_and_rule()
    print("=" * 80)
    print("🛡️  [ZeroSpill] Git Pre-Commit Hook & Agent Guardrail Installed Successfully!")
    print("=" * 80)
    print(f"  • Hook Script:  {res['hook_path']}")
    print(f"  • Agent Rules:  {res['rule_path']}")
    print("=" * 80)
    print("Now all future 'git commit' commands will be autonomously gated by ZeroSpill.")
    sys.exit(0)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print("ZeroSpill CLI v2.0 - Autonomous AI Agent Security Gate\n")
        print("Usage:")
        print("  python zerospill_cli.py scan-staged    Audit all git staged files for secrets & pixel leaks")
        print("  python zerospill_cli.py install-hook   Install .git/hooks/pre-commit and .agents/rules")
        print("  python zerospill_cli.py status         Check security hook status")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "scan-staged":
        scan_staged_command()
    elif cmd == "install-hook":
        install_hook_command()
    elif cmd == "status":
        from app.services.agent_integration import check_agent_hook_status
        st = check_agent_hook_status()
        print(f"Hook installed: {st['hook_installed']} ({st['hook_path']})")
        print(f"Rule installed: {st['rule_installed']} ({st['rule_path']})")
        sys.exit(0)
    else:
        print(f"Unknown command: {cmd}. Run with --help for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
