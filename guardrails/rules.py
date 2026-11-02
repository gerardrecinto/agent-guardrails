"""Each rule: id, regex over the shell command, why it is blocked, what to do instead."""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    id: str
    pattern: re.Pattern
    why: str
    instead: str


def _r(id, pattern, why, instead):
    return Rule(id, re.compile(pattern, re.IGNORECASE), why, instead)


RULES = [
    _r("rm-root-or-home",
       r"\brm\s+(-\w*[rf]\w*\s+)+(--no-preserve-root\s+)?(/|~|\$HOME|\"\$HOME\"|/\*|~/\*)(\s|$)",
       "Recursive delete of the root or home directory.",
       "Delete a specific, named subdirectory and list it first with ls."),
    _r("terraform-destroy",
       r"\bterraform\s+(destroy|apply\b.*-auto-approve)|\btofu\s+(destroy|apply\b.*-auto-approve)",
       "Destroys or changes infrastructure without a human reading the plan.",
       "Run terraform plan -out=tfplan, show the plan, and let a person run apply."),
    _r("kubectl-delete-broad",
       r"\bkubectl\s+delete\s+(ns|namespace|--all\b|.*\s--all\b|.*-A\b|.*--all-namespaces)",
       "Deletes a namespace or every object of a kind.",
       "Name one resource, run with --dry-run=server first, and check the current context."),
    _r("kubectl-prod-context",
       r"\bkubectl\b.*--context[= ]\S*prod|\bkubectl\b.*-n\s+\S*prod",
       "Mutating command aimed at a production context or namespace.",
       "Use get/describe for read-only checks. Ask a person to run changes in prod."),
    _r("git-force-push",
       r"\bgit\s+push\b(?!.*--force-with-lease).*(\s--force\b|\s-f\b|\s\+\S)",
       "Force push can overwrite other people's commits.",
       "Use git push --force-with-lease on your own branch, never on main."),
    _r("git-reset-hard",
       r"\bgit\s+(reset\s+--hard|clean\s+-\w*f)",
       "Throws away uncommitted work that cannot be recovered.",
       "Run git status, then git stash or commit first."),
    _r("sql-drop",
       r"\bdrop\s+(database|schema|table)\b|\btruncate\s+table\b",
       "Irreversible data loss.",
       "Take and verify a backup, then ask a person to run it."),
    _r("pipe-to-shell",
       r"\b(curl|wget)\b[^|;]*\|\s*(sudo\s+)?(ba|z)?sh\b",
       "Runs a remote script you have not read.",
       "Download it, read it, then run it."),
    _r("chmod-777",
       r"\bchmod\s+(-\w+\s+)*0?777\b",
       "Makes files writable by everyone.",
       "Grant the narrowest mode that works, such as 644 or 755."),
    _r("s3-bucket-wipe",
       r"\baws\s+s3\s+(rb\b|rm\b.*--recursive)|\baws\s+s3api\s+delete-bucket",
       "Deletes a bucket or all of its objects.",
       "List the contents, check versioning and replication, and ask a person to run it."),
    _r("read-env-file",
       r"\b(cat|less|more|head|tail|grep|printenv|env)\b.*(\.env(?!\.(example|sample|template))\b|\.aws/credentials|id_rsa|id_ed25519)",
       "Prints secrets into the model's context.",
       "Check that the variable is set with [ -n \"$NAME\" ] instead of printing it."),
]

SECRET_FILE = re.compile(r"(^|/)(\.env(\.\w+)?|credentials|id_rsa|id_ed25519)$")


def check_command(command: str):
    """Return the first matching Rule, or None."""
    for rule in RULES:
        if rule.pattern.search(command):
            return rule
    return None


def check_file_path(path: str):
    """Block the Read tool on obvious secret files."""
    if SECRET_FILE.search(path) and not path.endswith(".env.example"):
        return Rule("read-secret-file", SECRET_FILE,
                    "Reads a secrets file into the model's context.",
                    "Read .env.example, or ask which variable names are needed.")
    return None
