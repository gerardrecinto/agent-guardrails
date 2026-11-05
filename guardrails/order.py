"""Optional step order, enforced by Joltrin.

Rules in rules.py say "never run this". This adds "only after these steps". When the
environment variable AGENT_GUARDRAILS_ORDER points at a JSON file, a command that
matches one of its steps is checked with `sop-mcp-server gate`, which remembers the
steps already allowed for the session. Nothing here runs unless that variable is set.
"""
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass

ENV = "AGENT_GUARDRAILS_ORDER"


@dataclass(frozen=True)
class OrderBlock:
    id: str
    why: str
    instead: str


def load_config(path: str) -> dict:
    with open(path) as f:
        cfg = json.load(f)
    for key in ("runbooks", "workflow", "steps"):
        if key not in cfg:
            raise ValueError(f"missing {key!r}")
    for s in cfg["steps"]:
        if "match" not in s or "step" not in s:
            raise ValueError("each step needs 'match' and 'step'")
        re.compile(s["match"])
    return cfg


def _config_error(msg: str) -> OrderBlock:
    return OrderBlock("order-config", f"The step order file could not be used: {msg}.",
                      f"Fix the file named in {ENV}, or unset {ENV} to turn step order off.")


def check_order(command: str, session_id: str, run=subprocess.run):
    """Return None when the command is allowed or does not match a step, else an OrderBlock.

    A command that matches a step but cannot be checked is blocked, not allowed: a safety
    check that quietly stops working is worse than one that says so."""
    path = os.environ.get(ENV)
    if not path:
        return None
    try:
        cfg = load_config(path)
    except (OSError, ValueError) as e:
        return _config_error(str(e))
    step = next((s["step"] for s in cfg["steps"] if re.search(s["match"], command, re.IGNORECASE)), None)
    if step is None:
        return None
    binary = cfg.get("joltrin") or "sop-mcp-server"
    if not shutil.which(binary):
        return _config_error(f"{binary} is not on PATH (it needs a Joltrin build with the gate command)")
    base = os.path.dirname(os.path.abspath(path))
    runbooks = cfg["runbooks"] if os.path.isabs(cfg["runbooks"]) else os.path.join(base, cfg["runbooks"])
    session = re.sub(r"[^A-Za-z0-9._-]", "_", session_id or "default")[:128].lstrip("._-") or "default"
    try:
        p = run([binary, "gate", "--json", runbooks, cfg["workflow"], session, step],
                capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as e:
        return _config_error(f"{binary} gate failed to run: {e}")
    if p.returncode == 0:
        return None
    try:
        res = json.loads(p.stdout)
    except json.JSONDecodeError:
        return _config_error(f"{binary} gate said: {(p.stderr or p.stdout).strip()[:200]}")
    if res.get("decision") != "blocked":
        return _config_error(f"{binary} gate said: {(p.stderr or p.stdout).strip()[:200]}")
    first = res.get("run_first") or []
    instead = f"Run {' or '.join(first)} first, then try this again." if first else "Stop and ask a person."
    return OrderBlock(f"order:{step}", res.get("reason", "An earlier step has not happened yet."), instead)
