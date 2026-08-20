"""Source scan for direct state writes and mutating client calls."""

from __future__ import annotations

import ast
import re
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_STATE_WRITERS = {
    "durability/transitions.py",
    "durability/operator_resolution.py",
    "db.py",
}
ALLOWED_MUTATING_CALLERS = {
    "durability/session_owner.py",
    "client.py",
}
PROTECTED_UPDATE = re.compile(
    r"UPDATE\s+(managed_actor_bindings|managed_turn_intents|wake_batches|mailbox_messages|managed_actor_commands|app_server_effects)\s+SET[\s\S]{0,240}?\b(binding_state|submission_state|delivery_state|intake_state|validation_state)\b",
    re.IGNORECASE,
)
MUTATING_CALL = re.compile(
    r"""(?:client|self)\.request\(\s*['"](thread/start|thread/resume|thread/fork|turn/start|turn/steer|turn/interrupt|thread/compact/start|review/start|thread/memoryMode/set)['"]""",
)
LEGACY_INSERT = re.compile(r"INSERT\s+INTO\s+mutation_intents\b", re.IGNORECASE)
LEGACY_STATE_UPDATE = re.compile(r"UPDATE\s+mutation_intents\s+SET\s+state\b", re.IGNORECASE)
STATE_COLUMNS = (
    "binding_state",
    "submission_state",
    "delivery_state",
    "intake_state",
    "validation_state",
)


def _rel(path: Path) -> str:
    return path.relative_to(PACKAGE_ROOT).as_posix()


def scan_package(root: Path | None = None) -> list[str]:
    base = root or PACKAGE_ROOT
    violations: list[str] = []
    for path in base.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        rel = _rel(path) if root is None else path.as_posix()
        text = path.read_text(encoding="utf-8")
        if PROTECTED_UPDATE.search(text):
            if not any(rel.endswith(allowed) or rel.replace("\\", "/").endswith(allowed) for allowed in ALLOWED_STATE_WRITERS):
                if "durability/" not in rel and rel not in {"db.py"} and "TransitionKernel" not in text:
                    violations.append(f"{rel}: direct protected state UPDATE")
        if MUTATING_CALL.search(text) and not any(rel.endswith(item) for item in ALLOWED_MUTATING_CALLERS):
            violations.append(f"{rel}: direct mutating client.request")
        if LEGACY_INSERT.search(text) and "db.py" not in rel and "test_" not in path.name:
            violations.append(f"{rel}: new mutation_intents insert")
        if LEGACY_STATE_UPDATE.search(text) and "db.py" not in rel and "durability/" not in rel and "test_" not in path.name:
            if "legacy" not in text.lower() and "MutationIntentStore" not in text:
                violations.append(f"{rel}: mutation_intents state update")
    return sorted(set(violations))


def summarize_guard_violations(violations: list[str], *, unsuperseded_legacy: int = 0) -> dict[str, int]:
    return {
        "direct_state_write_violations": sum(1 for item in violations if "protected state" in item),
        "direct_mutation_call_violations": sum(1 for item in violations if "mutating" in item),
        "new_legacy_mutation_writes": sum(1 for item in violations if "mutation_intents" in item) + unsuperseded_legacy,
    }


def scan_source_text(text: str, *, name: str = "synthetic.py") -> list[str]:
    violations: list[str] = []
    if re.search(r'client\.request\(\s*"turn/start"', text):
        violations.append(f"{name}: direct mutating client.request")
    if re.search(r"UPDATE\s+wake_batches\s+SET\s+state", text, re.IGNORECASE) and "TransitionKernel" not in text:
        violations.append(f"{name}: direct protected state UPDATE")
    if re.search(r"INSERT\s+INTO\s+mutation_intents", text, re.IGNORECASE):
        violations.append(f"{name}: new mutation_intents insert")
    return violations
