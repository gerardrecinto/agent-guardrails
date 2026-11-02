# agent-guardrails

A Claude Code hook that stops the agent from running commands like `terraform destroy`, `rm -rf ~` or `git push --force`, and tells it what to do instead.

It is for anyone who lets an AI coding agent run shell commands on a real machine. Python 3.10+, no dependencies.

## Try it in 30 seconds

```bash
git clone https://github.com/gerardrecinto/agent-guardrails ~/.agent-guardrails
cd ~/.agent-guardrails
echo '{"tool_name":"Bash","tool_input":{"command":"terraform destroy"}}' | python3 -m guardrails.hook; echo "exit: $?"
```

It prints this and exits with 2, which is how Claude Code knows to block the call:

```
Blocked by agent-guardrails [terraform-destroy]: Destroys or changes infrastructure without a human reading the plan.
Instead: Run terraform plan -out=tfplan, show the plan, and let a person run apply.
```

A safe command such as `ls` exits 0 and prints nothing.

## Install

Merge `examples/settings.json` into `~/.claude/settings.json` (all projects) or `.claude/settings.json` (one project). Then run `/hooks` in Claude Code to confirm it is listed.

## What it blocks

| Rule | Example blocked | Why |
| --- | --- | --- |
| rm-root-or-home | `rm -rf ~` | Wipes the home or root directory |
| terraform-destroy | `terraform apply -auto-approve` | Changes infra with nobody reading the plan |
| kubectl-delete-broad | `kubectl delete ns payments` | Deletes a namespace or every object of a kind |
| kubectl-prod-context | `kubectl -n prod delete pod a` | Mutation aimed at production |
| git-force-push | `git push --force` | Can overwrite other people's commits |
| git-reset-hard | `git reset --hard HEAD~3` | Loses uncommitted work |
| sql-drop | `DROP TABLE users` | Irreversible data loss |
| pipe-to-shell | `curl x.sh \| sh` | Runs a script nobody read |
| chmod-777 | `chmod -R 777 .` | Makes files writable by everyone |
| s3-bucket-wipe | `aws s3 rb s3://b --force` | Deletes a bucket |
| read-env-file | `cat .env` | Puts secrets in the model's context |

The Read, Edit and Write tools are also blocked on `.env`, `.env.*`, `credentials`, `id_rsa` and `id_ed25519`. `.env.example` is allowed.

Allowed on purpose: `rm -rf node_modules`, `terraform plan`, `kubectl get`, `git push --force-with-lease`, `git reset --soft`.

## Limits

This is a seatbelt, not a sandbox. It matches command text with regular expressions, so an agent that writes a script and then runs it, or builds a command from variables, can get past it. It does not stop a determined attacker. Use real permissions, scoped credentials and a sandbox for that.

Tested with Python 3.14 on macOS. The hook protocol (JSON on stdin, exit code 2 blocks) follows Claude Code's hooks documentation. I have not yet run it inside a live Claude Code session or on Cursor or Codex.

## Add a rule

Add a `_r(...)` entry in `guardrails/rules.py`, then add block and allow cases in `tests/test_rules.py`. The test file fails if a rule has no block case.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install pytest && python -m pytest -q
```

MIT licensed.
