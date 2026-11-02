# Contributing

The most useful contribution is a command that should have been blocked, or a safe command that was blocked by mistake. Open an issue with the exact command.

## Add a rule

1. Add a `_r(...)` entry in `guardrails/rules.py` with an id, a pattern, why it is dangerous, and a safe alternative.
2. Add block cases under that id and a few allow cases in `tests/cases.json`.
3. Run the checks.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install pytest
python -m pytest -q
PYTHONPATH=. python scripts/export_rules.py   # refreshes docs/rules.json for the web demo
node tests/parity.mjs                        # web demo must agree with the hook
```

Keep patterns readable and avoid nested quantifiers that can backtrack badly. One rule per PR is easiest to review.
