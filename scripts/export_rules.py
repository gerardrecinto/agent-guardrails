"""Write docs/rules.json so the web demo runs the same patterns as the hook."""
import json
from pathlib import Path

from guardrails.rules import RULES, SECRET_FILE

root = Path(__file__).resolve().parent.parent
out = {
    "rules": [{"id": r.id, "pattern": r.pattern.pattern, "why": r.why, "instead": r.instead} for r in RULES],
    "secret_file": SECRET_FILE.pattern,
}
(root / "docs" / "rules.json").write_text(json.dumps(out, indent=1) + "\n")
