"""Build docs/assets/demo.cast from real runs of the hook. Typing is simulated,
the output of every command is captured from the actual process."""
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
steps = [
    ("terraform destroy", "Agent runs:"),
    ("git push --force origin main", "Agent runs:"),
    ("cat .env", "Agent runs:"),
    ("terraform plan -out=tfplan", "Agent runs:"),
]
events, t = [], 0.3


def out(text, dt=0.0):
    global t
    t += dt
    events.append([round(t, 3), "o", text.replace("\n", "\r\n")])


out("\x1b[1magent-guardrails\x1b[0m: the agent tries four commands\n\n", 0.2)
for cmd, label in steps:
    out(f"\x1b[2m{label}\x1b[0m ", 0.7)
    for ch in cmd:
        out(ch, 0.04)
    out("\n", 0.35)
    p = subprocess.run([sys.executable, "-m", "guardrails", "check", cmd],
                       capture_output=True, text=True, cwd=root)
    color = "31" if p.returncode == 2 else "32"
    for line in p.stdout.splitlines():
        out(f"\x1b[{color}m{line}\x1b[0m\n", 0.12)
    out("\n", 0.6)
out("The first three never ran. The plan did.\n", 0.4)
out("", 2.5)
header = {"version": 2, "width": 100, "height": 24, "title": "agent-guardrails demo"}
with open(root / "docs" / "assets" / "demo.cast", "w") as f:
    f.write(json.dumps(header) + "\n")
    for e in events:
        f.write(json.dumps(e) + "\n")
