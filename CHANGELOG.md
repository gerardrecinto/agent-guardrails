# Changelog

## Unreleased

- Optional step order: set `AGENT_GUARDRAILS_ORDER` to a JSON file and a command that matches one of its steps is checked with Joltrin's `sop-mcp-server gate`, which remembers the steps already allowed in the session. Off unless the variable is set. A matching command that cannot be checked is blocked.

## 0.2.0
- `python3 -m guardrails install` adds the hook to your Claude Code settings and keeps a backup.
- `python3 -m guardrails check "cmd"` tests a command without running it.
- Web demo on GitHub Pages that runs the same patterns in the browser, with a test that keeps it in sync.
- Shared test cases in `tests/cases.json`.

## 0.1.0
- First release: 11 command rules, a secret-file check for the Read, Edit and Write tools, and the Claude Code hook.
