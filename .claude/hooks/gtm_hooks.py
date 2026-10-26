"""Claude Code hooks for the Moment GTM Dashboard.

Staged per docs/plans/Moment_GTM_Dashboard_IMPLEMENTATION_ORDER.md "Hooks enablement order" and
docs/claude/Moment_GTM_Dashboard_Recommended_Hooks.md section A. One script, one subcommand per event:

  session-start  SessionStart  conventions reminder (context only)
  pre-edit       PreToolUse    block hand-edits to generated data; skill / metric-ID warnings
  post-edit      PostToolUse   ruff + black (backend .py), prettier + eslint (frontend)
  stop           Stop          backend pytest -q when backend code changed since the last run
  ci-gate        Manual/CI     reconciliation + RLS + frontend vitest + build gate (Step 8)

Warnings are injected as context for Claude (never blocking) except the generated-data guard.
Every hook exits 0 on unexpected errors so a broken hook never blocks work.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV_BIN = BACKEND / ".venv" / ("Scripts" if os.name == "nt" else "bin")
NODE_BIN = FRONTEND / "node_modules" / ".bin"
STATE = ROOT / ".claude" / "hooks" / ".state"
DEFINITIONS = BACKEND / "app" / "semantic" / "definitions.py"
METRIC_ID = re.compile(r"\b(?:EXE|PIP|PUR|OFF|ACC|PAR|CAP|MKT)-\d{2}\b")

CONVENTIONS = """Moment GTM Dashboard conventions (from the plans + project skill):
- Build order: docs/plans/Moment_GTM_Dashboard_IMPLEMENTATION_ORDER.md. Steps 0-8 are built and verified in
  .
- Layers: mock connectors -> raw -> conformed -> marts (DuckDB) -> semantic/ -> api/ -> React. Metric
  logic lives only in backend/app/semantic; routes stay thin; widgets compose shared components.
- Load the `moment-gtm-reusable-components` skill before touching shared components, widgets or the
  semantic layer; load `dataviz` before any chart code.
- Every metric ID must be registered in backend/app/semantic/definitions.py (FR-GEN-07).
- RLS (semantic/rls.py) applies to every query, drill-down, export and alert; status = text+icon+colour
  with bands from ref_threshold; money via $M to 1 dp.
- UI is a bento leadership theme: module routes use BentoGrid/BentoItem with eyebrow + scorecard
  (highlights), one variant="hero" widget + sticky spotlight inside a BentoRow (no chart marks on spotlights),
  then 6/6 or 4/4/4 rows; chrome colours from tokens.bento / CSS vars, chart colours unchanged.
- Generated artifacts (*.duckdb, backend/var/) are rebuilt by the ELT - never hand-edit them.
- Backend: backend/.venv (pytest, ruff, black). Frontend: npm in
  frontend/ (build, lint, vitest). E2E: e2e/ (Playwright, needs both servers running). Load: load/k6/."""


def read_input() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def emit(event: str, context: str | None = None, **extra) -> None:
    out: dict = dict(extra)
    if context:
        out["hookSpecificOutput"] = {"hookEventName": event, "additionalContext": context}
    if out:
        print(json.dumps(out))


def rel(path: str) -> str:
    p = Path(path)
    try:
        p = p.resolve().relative_to(ROOT.resolve())
    except Exception:
        pass
    return p.as_posix()


# --- SessionStart ---------------------------------------------------------------------------
def session_start(_: dict) -> None:
    emit("SessionStart", CONVENTIONS)


# --- PreToolUse -----------------------------------------------------------------------------
def registered_metric_ids() -> set[str]:
    try:
        return set(re.findall(r'^\s*"([A-Z]{3}-\d{2})":\s*\{', DEFINITIONS.read_text("utf8"), re.M))
    except OSError:
        return set()


def pre_edit(data: dict) -> None:
    ti = data.get("tool_input") or {}
    path = rel(ti.get("file_path") or ti.get("notebook_path") or "")
    if not path:
        return
    low = path.lower()
    if low.endswith((".duckdb", ".duckdb.wal")) or "/backend/var/" in f"/{low}":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"{path} is a generated data-platform artifact. Change the generator/ELT "
                "(backend/app/data, backend/app/platform) and rebuild instead of hand-editing."),
        }}))
        return
    notes: list[str] = []
    in_front = "/frontend/src/" in f"/{low}"
    shared = in_front and any(f"/components/{d}/" in low
                              for d in ("layout", "common", "charts", "data", "widgets"))
    semantic = "/backend/app/semantic/" in f"/{low}"
    if shared or semantic:
        notes.append("Shared component / widget / semantic-layer file: follow the "
                     "`moment-gtm-reusable-components` skill (extend shared parts, don't fork; "
                     "definition of done).")
    if in_front and "/src/routes/" in low:
        notes.append("Module route: follow the bento module pattern (catalog §2a) - BentoGrid/"
                     "BentoItem, eyebrow + HeadlineScorecard, one variant=\"hero\" widget (span 8) + "
                     "sticky spotlight (span 4) together inside a BentoRow, ExportViewButton; call "
                     "headline hooks only inside "
                     "ModuleHeadlines components (after the access check).")
    if in_front and ("/components/charts/" in low or "/widgets/" in low or "chart" in Path(low).name):
        notes.append("Chart code: load the `dataviz` skill first if not already loaded; colours only "
                     "from theme/tokens.ts.")
    if re.search(r"/backend/app/semantic/metrics/[^/]+\.py$", f"/{low}"):
        text = (ti.get("content") or "") + (ti.get("new_string") or "")
        missing = sorted(set(METRIC_ID.findall(text)) - registered_metric_ids())
        if missing:
            notes.append(f"Metric IDs {', '.join(missing)} are not registered in "
                         "backend/app/semantic/definitions.py — add them (FR-GEN-07) before use.")
    if notes:
        emit("PreToolUse", " ".join(notes))


# --- PostToolUse ----------------------------------------------------------------------------
def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120,
                          shell=os.name == "nt" and cmd[0].endswith(".cmd"))


def post_edit(data: dict) -> None:
    ti = data.get("tool_input") or {}
    raw = ti.get("file_path") or ""
    if not raw:
        return
    f = Path(raw).resolve()
    s = f.as_posix().lower()
    problems: list[str] = []
    if f.suffix == ".py" and s.startswith(BACKEND.resolve().as_posix().lower()) and "/.venv/" not in s:
        ruff, black = VENV_BIN / "ruff", VENV_BIN / "black"
        if (VENV_BIN / "ruff.exe").exists() or ruff.exists():
            run([str(ruff), "check", "--fix", "--quiet", str(f)], BACKEND)
            run([str(black), "--quiet", str(f)], BACKEND)
            r = run([str(ruff), "check", "--quiet", str(f)], BACKEND)
            if r.returncode:
                problems.append("ruff:\n" + (r.stdout or r.stderr)[-1500:])
    elif f.suffix in (".ts", ".tsx", ".css") and s.startswith((FRONTEND / "src").resolve().as_posix().lower()):
        ext = ".cmd" if os.name == "nt" else ""
        prettier, eslint = NODE_BIN / f"prettier{ext}", NODE_BIN / f"eslint{ext}"
        if prettier.exists():
            run([str(prettier), "--write", "--log-level", "warn", str(f)], FRONTEND)
        if eslint.exists() and f.suffix != ".css":
            r = run([str(eslint), "--fix", str(f)], FRONTEND)
            if r.returncode:
                problems.append("eslint:\n" + (r.stdout or r.stderr)[-1500:])
    if problems:
        emit("PostToolUse", f"Lint issues remain in {rel(raw)} after auto-fix:\n" + "\n".join(problems))


# --- Stop -----------------------------------------------------------------------------------
def backend_fingerprint() -> str:
    newest = 0.0
    for sub in ("app", "tests"):
        for p in (BACKEND / sub).rglob("*"):
            if p.suffix in (".py", ".sql"):
                newest = max(newest, p.stat().st_mtime)
    return f"{newest:.3f}"


def stop(data: dict) -> None:
    if data.get("stop_hook_active") or not (VENV_BIN / ("python.exe" if os.name == "nt" else "python")).exists():
        return
    STATE.mkdir(parents=True, exist_ok=True)
    stamp = STATE / "pytest_fingerprint"
    fp = backend_fingerprint()
    if stamp.exists() and stamp.read_text() == fp:
        return  # backend unchanged since the last green run
    py = VENV_BIN / ("python.exe" if os.name == "nt" else "python")
    r = subprocess.run([str(py), "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=BACKEND,
                       capture_output=True, text=True, timeout=600)
    tail = [ln for ln in (r.stdout or "").strip().splitlines() if ln.strip()]
    summary = tail[-1] if tail else "pytest produced no output"
    if r.returncode == 0:
        stamp.write_text(fp)
        print(json.dumps({"systemMessage": f"Backend tests: {summary}"}))
    else:
        failed = [ln for ln in tail if ln.startswith("FAILED")][:10]
        print(json.dumps({"systemMessage": "Backend tests FAILED: " + summary + "\n" + "\n".join(failed)}))


def ci_gate(_: dict) -> None:
    """Step 8 CI gate: runs AC-01 reconciliation, AC-03 RLS, and AC-05 API/load tests."""
    py = VENV_BIN / ("python.exe" if os.name == "nt" else "python")
    r = subprocess.run(
        [
            str(py),
            "-m",
            "pytest",
            "tests/test_reconciliation.py",
            "tests/test_rls.py",
            "tests/test_api.py",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        timeout=600,
    )
    tail = [ln for ln in (r.stdout or "").strip().splitlines() if ln.strip()]
    summary = tail[-1] if tail else "pytest produced no output"
    status = "PASSED" if r.returncode == 0 else "FAILED"
    print(json.dumps({"systemMessage": f"CI gate ({status}): {summary}"}))


def main() -> None:
    handlers = {
        "session-start": session_start,
        "pre-edit": pre_edit,
        "post-edit": post_edit,
        "stop": stop,
        "ci-gate": ci_gate,
    }
    try:
        handlers[sys.argv[1]](read_input())
    except Exception as exc:  # never block work because a hook broke
        print(f"gtm hook error: {exc}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
