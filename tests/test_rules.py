import json
import subprocess
import sys
from pathlib import Path

import pytest

from guardrails.hook import decide
from guardrails.rules import RULES

ROOT = Path(__file__).resolve().parent.parent

CASES = json.loads((ROOT / "tests" / "cases.json").read_text())
BLOCK = CASES["block"]
ALLOW = CASES["allow"]


def bash(cmd):
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


def test_every_rule_has_block_cases():
    assert {r.id for r in RULES} == set(BLOCK)


@pytest.mark.parametrize("rule_id,cmd", [(k, c) for k, v in BLOCK.items() for c in v])
def test_blocks(rule_id, cmd):
    rule = decide(bash(cmd))
    assert rule is not None, f"not blocked: {cmd}"
    assert rule.id == rule_id


@pytest.mark.parametrize("cmd", ALLOW)
def test_allows(cmd):
    assert decide(bash(cmd)) is None


@pytest.mark.parametrize("path,blocked", [
    ("/repo/.env", True), ("/repo/.env.local", True), ("/home/u/.aws/credentials", True),
    ("/repo/.env.example", False), ("/repo/README.md", False),
])
def test_read_tool(path, blocked):
    got = decide({"tool_name": "Read", "tool_input": {"file_path": path}})
    assert (got is not None) == blocked


def run_hook(event):
    return subprocess.run([sys.executable, "-m", "guardrails.hook"], input=json.dumps(event),
                          capture_output=True, text=True, cwd=ROOT)


def test_end_to_end_block_exit_code_and_message():
    p = run_hook(bash("terraform destroy"))
    assert p.returncode == 2
    assert "terraform-destroy" in p.stderr and "Instead:" in p.stderr


def test_end_to_end_allow():
    assert run_hook(bash("ls")).returncode == 0


def test_bad_json_does_not_crash():
    p = subprocess.run([sys.executable, "-m", "guardrails.hook"], input="not json",
                       capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0


def test_install_is_idempotent_and_keeps_existing_settings(tmp_path):
    from guardrails.__main__ import install
    s = tmp_path / "settings.json"
    s.write_text(json.dumps({"model": "x", "hooks": {"PreToolUse": [{"matcher": "Task", "hooks": []}]}}))
    assert install(s, ROOT).startswith("installed")
    assert install(s, ROOT) == "already installed"
    data = json.loads(s.read_text())
    assert data["model"] == "x"
    assert len(data["hooks"]["PreToolUse"]) == 2
    assert (tmp_path / "settings.json.bak").exists()


def test_cli_check_exit_codes():
    def run(cmd):
        return subprocess.run([sys.executable, "-m", "guardrails", "check", cmd],
                              capture_output=True, text=True, cwd=ROOT)
    assert run("git push --force").returncode == 2
    assert run("git status").returncode == 0
