# Security

agent-guardrails is a seatbelt, not a sandbox. A command that gets past a rule is a bug worth reporting, but it is not a vulnerability by itself, because the hook only reads command text.

Report a bypass or a flaw in the installer through a private GitHub security advisory on this repository. Please do not post working exploits in a public issue. I will reply within a week.

Rules are plain regular expressions, so the usual risk is a pattern that is too slow on long input. If you find one, include the command that makes it slow.
