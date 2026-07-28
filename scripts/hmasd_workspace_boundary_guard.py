"""Fail closed on agent-initiated writes outside the active HMASD workspace."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import hmasd_workspace_ticket as ticketing


SHELL_TOOLS = {"bash", "exec_command", "shell_command", "unified_exec"}
PATCH_TOOLS = {"apply_patch", "applypatch"}
GLOBAL_MUTATION = re.compile(
    r"(?i)(?:\bsubst(?:\.exe)?\b|\bnew-psdrive\b|\bnet(?:\.exe)?\s+use\b|"
    r"\bmklink\b|\bmountvol\b|\bgit(?:\.exe)?\b[^\r\n]*\bworktree\s+"
    r"(?:add|move|remove|prune|lock|unlock|repair)\b|"
    r"-itemtype\s+(?:junction|symboliclink)|\bnew-item\b[^\r\n]*"
    r"-itemtype\s+(?:junction|symboliclink))"
)
MUTATION = re.compile(
    r"(?i)(?:\bnew-item\b|\bmkdir\b|\bset-content\b|\badd-content\b|"
    r"\bout-file\b|\bremove-item\b|\bmove-item\b|\bcopy-item\b|"
    r"\brename-item\b|\bclear-content\b|\bdel\b|\berase\b|\brmdir\b|"
    r"\bset-acl\b|\bicacls\b|\btakeown\b|(?:^|[\s;&|])(?:md|ni|rm|mv|cp)\s)"
)
DYNAMIC_TARGET = re.compile(r"(?:\$\{|\$[A-Za-z_]|%[A-Za-z_][A-Za-z0-9_]*%|`|\$\(|\[IO\.)")
QUOTED_WINDOWS_PATH = re.compile(r"(?i)(?:\"([^\"]*[A-Z]:[\\/][^\"]*)\"|'([^']*[A-Z]:[\\/][^']*)')")
BARE_WINDOWS_PATH = re.compile(r"(?i)(?<![A-Za-z0-9_])([A-Z]:[\\/][^\s;|>'\"\)\]]+)")
UNC_PATH = re.compile(r"(?<![\\])((?:\\\\|//)[^\s;|>'\"\)\]]+)")
PATCH_PATH = re.compile(r"(?m)^\*\*\* (?:Add|Update|Delete) File: (.+?)\s*$")


class GuardError(RuntimeError):
    """A fail-closed workspace-boundary decision."""


def _decision(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"HMASD_WORKSPACE_BOUNDARY_DENY {reason}",
        }
    }


def _emit_deny(reason: str) -> int:
    print(json.dumps(_decision(reason), sort_keys=True))
    return 0


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise GuardError(f"cannot resolve active Git workspace: {detail}")
    return completed.stdout.strip()


def _canonical(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _same(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left)) == os.path.normcase(str(right))


def _inside(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((os.path.normcase(str(path)), os.path.normcase(str(root)))) == os.path.normcase(str(root))
    except ValueError:
        return False


def _workspace_scope(cwd: Path) -> tuple[Path, list[Path], bool]:
    if not cwd.exists():
        raise GuardError(f"working directory does not exist: {cwd}")
    top = _canonical(Path(_git(cwd, "rev-parse", "--show-toplevel")))
    marker = top / ".git"
    if marker.is_dir():
        return top, [top], False
    if not marker.is_file():
        raise GuardError("active workspace is neither the main checkout nor a linked worktree")

    common_raw = Path(_git(top, "rev-parse", "--git-common-dir"))
    common = _canonical(common_raw if common_raw.is_absolute() else top / common_raw)
    registry = common / ticketing.TICKET_DIRECTORY
    matches: list[tuple[Path, list[str]]] = []
    if registry.is_dir():
        for candidate in registry.glob("*.json"):
            try:
                _, worktree, allowed = ticketing._resolve_payload(candidate, None)
            except ticketing.TicketError:
                continue
            if _same(worktree, top):
                matches.append((candidate, allowed))
    if len(matches) != 1:
        raise GuardError("linked worktree has no unique valid workspace ticket")
    allowed_roots = [_canonical(top / Path(relative)) for relative in matches[0][1]]
    return top, allowed_roots, True


def _extract_absolute_paths(command: str) -> list[Path]:
    raw: list[str] = []
    for match in QUOTED_WINDOWS_PATH.finditer(command):
        raw.append(match.group(1) or match.group(2))
    raw.extend(match.group(1).rstrip(",") for match in BARE_WINDOWS_PATH.finditer(command))
    if UNC_PATH.search(command):
        raise GuardError("UNC mutation targets are outside the HMASD workspace")
    unique: list[Path] = []
    for value in raw:
        candidate = _canonical(Path(value))
        if not any(_same(candidate, prior) for prior in unique):
            unique.append(candidate)
    return unique


def _trusted_provision(command: str, repo: Path, linked: bool) -> bool:
    lowered = command.lower().replace("/", "\\")
    if linked or "hmasd_workspace_ticket.py" not in lowered or " provision " not in f" {lowered} ":
        return False
    if re.search(r"(?:;|&&|\|\||\r|\n|>|<)", command):
        return False
    registered = _canonical(repo / "scripts" / "hmasd_workspace_ticket.py")
    return str(registered).lower() in lowered or "scripts\\hmasd_workspace_ticket.py" in lowered


def _patch_text(tool_input: Any) -> str:
    if isinstance(tool_input, str):
        return tool_input
    if isinstance(tool_input, dict):
        for key in ("patch", "input"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    raise GuardError("apply_patch payload has no patch text")


def _guard_patch(cwd: Path, allowed_roots: list[Path], tool_input: Any) -> None:
    paths = PATCH_PATH.findall(_patch_text(tool_input))
    if not paths:
        raise GuardError("apply_patch payload has no recognized file paths")
    for raw in paths:
        candidate = Path(raw.strip())
        resolved = _canonical(candidate if candidate.is_absolute() else cwd / candidate)
        if not any(_inside(resolved, root) for root in allowed_roots):
            raise GuardError(f"apply_patch target is outside the writable scope: {resolved}")


def _guard_shell(
    repo: Path, cwd: Path, allowed_roots: list[Path], linked: bool, tool_input: Any
) -> None:
    if not isinstance(tool_input, dict) or not isinstance(tool_input.get("command"), str):
        raise GuardError("shell payload has no command")
    command = tool_input["command"]
    if _trusted_provision(command, repo, linked):
        return
    if GLOBAL_MUTATION.search(command):
        raise GuardError("drive mapping, path alias, or raw Git worktree mutation is forbidden")

    mutating = bool(MUTATION.search(command) or re.search(r"(?m)(?<![<>=])-?>{1,2}(?![=])", command))
    if not mutating:
        return
    if DYNAMIC_TARGET.search(command):
        raise GuardError("dynamic mutation target cannot be proven inside the writable scope")
    absolute_paths = _extract_absolute_paths(command)
    if not absolute_paths:
        if linked:
            raise GuardError("linked-worktree shell mutation must name an allowed absolute target")
        if not any(_inside(cwd, root) for root in allowed_roots):
            raise GuardError(f"working directory is outside the writable scope: {cwd}")
        return
    for candidate in absolute_paths:
        if not any(_inside(candidate, root) for root in allowed_roots):
            raise GuardError(f"mutation target is outside the writable scope: {candidate}")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as exc:
        return _emit_deny(f"invalid hook payload: {exc}")
    if payload.get("hook_event_name") != "PreToolUse":
        return 0
    tool_name = str(payload.get("tool_name", "")).lower()
    if tool_name not in SHELL_TOOLS | PATCH_TOOLS:
        return 0
    try:
        cwd_raw = payload.get("cwd")
        if not isinstance(cwd_raw, str) or not cwd_raw:
            raise GuardError("hook payload has no working directory")
        cwd = _canonical(Path(cwd_raw))
        repo, allowed_roots, linked = _workspace_scope(cwd)
        if tool_name in PATCH_TOOLS:
            _guard_patch(cwd, allowed_roots, payload.get("tool_input"))
        else:
            _guard_shell(repo, cwd, allowed_roots, linked, payload.get("tool_input"))
    except (GuardError, OSError, ticketing.TicketError) as exc:
        return _emit_deny(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
