"""python3 -m guardrails check "cmd" | install [--settings PATH]"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from guardrails.rules import check_command

HOOK_COMMAND = "PYTHONPATH={root} python3 -m guardrails.hook"
MATCHER = "Bash|Read|Edit|Write"


def install(settings_path: Path, root: Path) -> str:
    command = HOOK_COMMAND.format(root=root)
    data = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    entries = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    for entry in entries:
        for h in entry.get("hooks", []):
            if "guardrails.hook" in h.get("command", ""):
                return "already installed"
    if settings_path.exists():
        shutil.copy2(settings_path, settings_path.with_suffix(".json.bak"))
    entries.append({"matcher": MATCHER, "hooks": [{"type": "command", "command": command}]})
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(data, indent=2) + "\n")
    return f"installed in {settings_path}"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python3 -m guardrails")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="test one command without running it")
    c.add_argument("command")
    i = sub.add_parser("install", help="add the hook to a Claude Code settings file")
    i.add_argument("--settings", type=Path, default=Path.home() / ".claude" / "settings.json")
    a = p.parse_args(argv)
    if a.cmd == "check":
        rule = check_command(a.command)
        if rule is None:
            print("allowed")
            return 0
        print(f"BLOCKED [{rule.id}]: {rule.why}\nInstead: {rule.instead}")
        return 2
    print(install(a.settings, Path(__file__).resolve().parent.parent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
