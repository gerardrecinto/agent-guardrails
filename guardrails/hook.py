"""Claude Code PreToolUse hook. Reads the tool call as JSON on stdin.
Exit 0 allows the call. Exit 2 blocks it and sends stderr back to the agent."""
import json
import sys

from guardrails.rules import check_command, check_file_path


def decide(event: dict):
    tool = event.get("tool_name", "")
    args = event.get("tool_input") or {}
    if tool == "Bash":
        return check_command(args.get("command", ""))
    if tool in ("Read", "Edit", "Write"):
        return check_file_path(args.get("file_path", ""))
    return None


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    rule = decide(event)
    if rule is None:
        return 0
    print(f"Blocked by agent-guardrails [{rule.id}]: {rule.why}\nInstead: {rule.instead}",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
