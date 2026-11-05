import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from guardrails.hook import decide
from guardrails.order import ENV, check_order

ROOT = Path(__file__).resolve().parent.parent
BLOCKED = json.dumps({"decision": "blocked", "reason": 'step "apply" requires state "planned"',
                      "run_first": ["plan"]})


def write_config(tmp_path, joltrin=sys.executable, **extra):
    cfg = {"runbooks": "runbooks.json", "workflow": "infra", "joltrin": joltrin,
           "steps": [{"match": r"\bterraform\s+plan\b", "step": "plan"},
                     {"match": r"\bterraform\s+apply\b", "step": "apply"}], **extra}
    p = tmp_path / "order.json"
    p.write_text(json.dumps(cfg))
    return p


def fake(code, out=""):
    calls = []

    def run(argv, **kw):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, code, stdout=out, stderr="")
    run.calls = calls
    return run


def test_off_when_env_is_unset(monkeypatch):
    monkeypatch.delenv(ENV, raising=False)
    run = fake(1, BLOCKED)
    assert check_order("terraform apply", "s", run=run) is None
    assert run.calls == []


def test_command_that_matches_no_step_is_not_checked(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV, str(write_config(tmp_path)))
    run = fake(1, BLOCKED)
    assert check_order("ls -la", "s", run=run) is None
    assert run.calls == []


def test_allowed_step_passes(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV, str(write_config(tmp_path)))
    assert check_order("terraform plan -out=tfplan", "s", run=fake(0)) is None


def test_blocked_step_says_what_to_run_first(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV, str(write_config(tmp_path)))
    run = fake(1, BLOCKED)
    block = check_order("terraform apply tfplan", "sess-1", run=run)
    assert block.id == "order:apply"
    assert "Run plan first" in block.instead
    argv = run.calls[0]
    assert argv[1:3] == ["gate", "--json"] and argv[-2:] == ["sess-1", "apply"]
    assert argv[3].endswith("runbooks.json") and os.path.isabs(argv[3])


def test_session_name_cannot_carry_a_path(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV, str(write_config(tmp_path)))
    run = fake(0)
    check_order("terraform apply", "../../etc/passwd", run=run)
    assert "/" not in run.calls[0][-2] and not run.calls[0][-2].startswith(".")


def test_missing_binary_blocks_instead_of_allowing(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV, str(write_config(tmp_path, joltrin="no-such-joltrin-binary")))
    block = check_order("terraform apply", "s", run=fake(0))
    assert block.id == "order-config" and "not on PATH" in block.why


def test_unreadable_config_blocks_a_matching_command_only(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV, str(tmp_path / "missing.json"))
    assert check_order("terraform apply", "s").id == "order-config"


def test_gate_failure_that_is_not_a_decision_blocks(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV, str(write_config(tmp_path)))
    block = check_order("terraform apply", "s", run=fake(2, "not json"))
    assert block.id == "order-config"


def test_stateless_rule_wins_and_gate_is_not_called(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV, str(write_config(tmp_path, joltrin="no-such-joltrin-binary")))
    rule = decide({"tool_name": "Bash", "tool_input": {"command": "terraform apply -auto-approve"}})
    assert rule.id == "terraform-destroy"


@pytest.mark.skipif(not os.environ.get("JOLTRIN_BIN"), reason="set JOLTRIN_BIN to a sop-mcp-server with the gate command")
def test_real_gate_orders_plan_before_apply(monkeypatch, tmp_path):
    (tmp_path / "runbooks.json").write_text((ROOT / "examples" / "runbooks.json").read_text())
    monkeypatch.setenv(ENV, str(write_config(tmp_path, joltrin=os.environ["JOLTRIN_BIN"])))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("HOME", str(tmp_path))
    event = lambda c: {"tool_name": "Bash", "session_id": "it-1", "tool_input": {"command": c}}
    assert decide(event("terraform apply tfplan")).id == "order:apply"
    assert decide(event("terraform plan -out=tfplan")) is None
    assert decide(event("terraform apply tfplan")) is None
