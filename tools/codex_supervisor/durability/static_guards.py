"""Source scan for direct state writes and mutating client calls."""

from __future__ import annotations

import ast
import re
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_STATE_WRITERS = frozenset(
    {
        "durability/transitions.py",
        "db.py",
    }
)
ALLOWED_MUTATING_CALLERS = frozenset(
    {
        "durability/session_owner.py",
        "client.py",
    }
)
PROTECTED_TABLE_COLUMNS = {
    "managed_actor_bindings": frozenset({"binding_state"}),
    "managed_turn_intents": frozenset({"submission_state"}),
    "wake_batches": frozenset({"state"}),
    "mailbox_messages": frozenset({"delivery_state", "intake_state"}),
    "managed_actor_commands": frozenset({"validation_state"}),
    "app_server_effects": frozenset({"state"}),
}
MUTATING_METHODS = (
    "thread/start",
    "thread/resume",
    "thread/fork",
    "turn/start",
    "turn/steer",
    "turn/interrupt",
    "thread/compact/start",
    "review/start",
    "thread/memoryMode/set",
)
MUTATING_CALL = re.compile(
    r"""(?:client|self)\.request\(\s*['"](""" + "|".join(re.escape(item) for item in MUTATING_METHODS) + r""")['"]""",
)
MUTATING_BOUNDARY_CALL = re.compile(
    r"\.(?:prepare_request|send_prepared|_issue_committed_claim)\s*\("
)
LEGACY_INSERT = re.compile(r"INSERT\s+INTO\s+mutation_intents\b", re.IGNORECASE)
LEGACY_STATE_UPDATE = re.compile(r"UPDATE\s+mutation_intents\s+SET\s+state\b", re.IGNORECASE)
UPDATE_TABLE = re.compile(
    r"UPDATE\s+(managed_actor_bindings|managed_turn_intents|wake_batches|mailbox_messages|managed_actor_commands|app_server_effects)\b",
    re.IGNORECASE,
)


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _sql_literals(tree: ast.AST) -> list[str]:
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "UPDATE" in node.value.upper() or "INSERT" in node.value.upper():
                found.append(node.value)
        elif isinstance(node, ast.JoinedStr):
            parts: list[str] = []
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    parts.append(value.value)
                else:
                    parts.append(" ")
            text = "".join(parts)
            if "UPDATE" in text.upper() or "INSERT" in text.upper():
                found.append(text)
    return found


def _protected_update(sql: str) -> bool:
    match = UPDATE_TABLE.search(sql)
    if match is None:
        return False
    table = match.group(1).lower()
    columns = PROTECTED_TABLE_COLUMNS.get(table, frozenset())
    set_blob = sql[match.end() :]
    where = re.search(r"\bWHERE\b", set_blob, re.IGNORECASE)
    if where is not None:
        set_blob = set_blob[: where.start()]
    return any(re.search(rf"\b{re.escape(column)}\b", set_blob, re.IGNORECASE) for column in columns)


def scan_package(root: Path | None = None) -> list[str]:
    base = root or PACKAGE_ROOT
    violations: list[str] = []
    for path in base.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        rel = _rel(path, base)
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = None
        if tree is not None:
            for sql in _sql_literals(tree):
                if _protected_update(sql) and rel not in ALLOWED_STATE_WRITERS and not rel.endswith(tuple(ALLOWED_STATE_WRITERS)):
                    violations.append(f"{rel}: direct protected state UPDATE")
                if LEGACY_INSERT.search(sql) and rel != "db.py" and not rel.endswith("/db.py") and "test_" not in path.name:
                    violations.append(f"{rel}: new mutation_intents insert")
                if LEGACY_STATE_UPDATE.search(sql) and rel != "db.py" and not rel.endswith("/db.py") and "test_" not in path.name:
                    violations.append(f"{rel}: mutation_intents state update")
        if MUTATING_CALL.search(text) and rel not in ALLOWED_MUTATING_CALLERS and not any(
            rel.endswith(item) for item in ALLOWED_MUTATING_CALLERS
        ):
            violations.append(f"{rel}: direct mutating client.request")
        if MUTATING_BOUNDARY_CALL.search(text) and rel not in ALLOWED_MUTATING_CALLERS and not any(
            rel.endswith(item) for item in ALLOWED_MUTATING_CALLERS
        ):
            violations.append(f"{rel}: direct prepared mutation boundary call")
    return sorted(set(violations))


def summarize_guard_violations(violations: list[str], *, unsuperseded_legacy: int = 0) -> dict[str, int]:
    return {
        "direct_state_write_violations": sum(1 for item in violations if "protected state" in item),
        "direct_mutation_call_violations": sum(1 for item in violations if "mutating" in item),
        "new_legacy_mutation_writes": sum(1 for item in violations if "mutation_intents" in item) + unsuperseded_legacy,
    }


def scan_source_text(text: str, *, name: str = "synthetic.py") -> list[str]:
    violations: list[str] = []
    allow_state = name.replace("\\", "/") in ALLOWED_STATE_WRITERS or name.replace("\\", "/").endswith(
        tuple(ALLOWED_STATE_WRITERS)
    )
    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None
    if tree is not None:
        for sql in _sql_literals(tree):
            if _protected_update(sql) and not allow_state:
                violations.append(f"{name}: direct protected state UPDATE")
            if LEGACY_INSERT.search(sql):
                violations.append(f"{name}: new mutation_intents insert")
    if re.search(r'client\.request\(\s*"turn/start"', text):
        violations.append(f"{name}: direct mutating client.request")
    normalized = name.replace("\\", "/")
    if (
        MUTATING_BOUNDARY_CALL.search(text)
        and normalized not in ALLOWED_MUTATING_CALLERS
        and not normalized.endswith(tuple(ALLOWED_MUTATING_CALLERS))
    ):
        violations.append(f"{name}: direct prepared mutation boundary call")
    return sorted(set(violations))
