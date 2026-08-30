"""Fail closed for recognized writes outside the active HMASD workspace.

This PreToolUse syntactic guard preserves its existing denials and complements
the tool/OS sandbox and Git-visible checks. It does not replace those
authoritative controls or claim to parse arbitrary shell semantics.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

SHELL_TOOLS = {"bash", "exec_command", "shell_command", "unified_exec"}
PATCH_TOOLS = {"apply_patch", "applypatch"}
GLOBAL_MUTATION = re.compile(
    r"(?i)(?:\bmount(?:\.?fuse)?\b|\bumount\b|\bln\b[^\r\n]*"
    r"(?:-\s*s\b|--symbolic\b)|\bgit\b[^\r\n]*\bworktree\s+"
    r"(?:add|move|remove|prune|lock|unlock|repair)\b)"
)
MUTATION = re.compile(
    r"(?i)(?:\bmkdir\b|\binstall\b|\btee\b|\btruncate\b|\bnew-item\b|"
    r"\bset-content\b|\badd-content\b|\bout-file\b|\bremove-item\b|"
    r"\bmove-item\b|\bcopy-item\b|\brename-item\b|\bclear-content\b|"
    r"\bdel\b|\berase\b|\brmdir\b|\brm\b|\bmv\b|\bcp\b|\bset-acl\b|"
    r"\bicacls\b|\btakeown\b|(?:^|[\s;&|])(?:md|ni)\s)"
)
REDIRECTION = re.compile(r"(?m)(?<![<>=])-?>{1,2}(?![=])")
DYNAMIC_TARGET = re.compile(r"(?:\$\{|\$[A-Za-z_]|`|\$\()")
PATCH_PATH = re.compile(
    r"(?m)^\*\*\* (?:(?:Add|Update|Delete) File:|Move to:) (.+?)\s*$"
)
PATH_ARGUMENT = re.compile(
    r'''(?ix)(?:-\s*(?:literalpath|path|destination|target|filepath)\s+|(?<![<>=])>{1,2}\s*)(?:"([^"]*)"|'([^']*)'|([^\s;|]+))'''
)
PATH_ALIAS = re.compile(r"(?:^|/)(?:\.{1,2})(?=$|/)")
RECURSIVE_DELETE = re.compile(
    r"(?is)\b(?:rmdir|rm)\b[^\r\n;&|]*(?:--recursive\b|-\s*r\b)"
)
class GuardError(RuntimeError):
    """A fail-closed decision for a recognized workspace-boundary case."""


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
    return left == right


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _has_path_alias(path: Path) -> bool:
    """Reject lexical aliases and existing symlink components."""

    if PATH_ALIAS.search(str(path)):
        return True
    candidate = path if path.is_absolute() else Path.cwd() / path
    while True:
        if candidate.is_symlink():
            return True
        parent = candidate.parent
        if parent == candidate:
            return False
        candidate = parent




def _target_path(raw: str, cwd: Path) -> Path:
    """Validate one syntactic target and return its canonical path."""

    value = raw.strip()
    if value.startswith("//"):
        raise GuardError("network mutation targets are outside the HMASD workspace")
    candidate = Path(value)
    if _has_path_alias(candidate):
        raise GuardError("symlink or path alias mutation target is forbidden")
    if not candidate.is_absolute():
        candidate = cwd / candidate
    if _has_path_alias(candidate):
        raise GuardError("symlink or path alias mutation target is forbidden")
    return _canonical(candidate)


def _marker_root(start: Path) -> Path:
    """Resolve the project from the active OMP control-plane markers."""

    candidate = _canonical(start)
    if not candidate.exists():
        candidate = candidate.parent
    if candidate.is_file():
        candidate = candidate.parent
    for ancestor in (candidate, *candidate.parents):
        control = ancestor / ".omp"
        if _has_path_alias(control):
            continue
        if (control / "AGENTS.md").is_file() or (control / "config.yml").is_file():
            return ancestor
    raise GuardError(
        "cannot resolve HMASD workspace from .omp/AGENTS.md or .omp/config.yml "
        f"(start={start!s}; process_cwd={Path.cwd()!s})"
    )


def _workspace_scope(cwd: Path) -> tuple[Path, list[Path], bool]:
    """Return marker root, writable project scope and optional Git status.

    Git is useful for diagnostics but is not an identity or admission gate.  A
    copied project with the two stable markers is therefore still guarded.
    """
    root = _marker_root(cwd)
    git_verified = False
    git_dir = root / ".git"
    if git_dir.exists() or git_dir.is_symlink():
        if _has_path_alias(git_dir):
            raise GuardError("symlink or path alias Git root is forbidden")
        try:
            git_top = _canonical(Path(_git(root, "rev-parse", "--show-toplevel")))
        except (GuardError, OSError):
            git_top = root
        else:
            if not _same(git_top, root):
                raise GuardError(
                    f"resolved Git workspace top does not match marker root: {git_top}"
                )
        git_verified = _same(git_top, root)
    return root, [root], git_verified


def _extract_absolute_paths(command: str, cwd: Path) -> list[Path]:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        raise GuardError(f"shell command has invalid quoting: {exc}") from exc
    unique: list[Path] = []
    for token in tokens:
        value = token.lstrip("<>")
        if not value.startswith("/") or value == "/":
            continue
        candidate = _target_path(value, cwd)
        if not any(_same(candidate, prior) for prior in unique):
            unique.append(candidate)
    return unique


def _extract_target_paths(command: str, cwd: Path) -> list[Path]:
    """Return canonical paths named by recognized path options/redirections."""

    targets: list[Path] = []
    for match in PATH_ARGUMENT.finditer(command):
        value = match.group(1) or match.group(2) or match.group(3)
        if value is None:
            continue
        target = _target_path(value, cwd)
        if not any(_same(target, prior) for prior in targets):
            targets.append(target)
    return targets


def _recursive_delete_is_broad(command: str, cwd: Path, repo: Path) -> bool:
    """Identify recursive deletion of cwd/root or an unresolved broad target."""

    if not RECURSIVE_DELETE.search(command):
        return False
    try:
        targets = _extract_target_paths(command, cwd)
        targets.extend(_extract_absolute_paths(command, cwd))
    except GuardError:
        # Aliased and unresolved recursive targets are broad by definition.
        return True
    command_match = re.search(
        r"(?is)\b(?:rmdir|rm)\b([^\r\n;&|]*)",
        command,
    )
    if command_match:
        args = command_match.group(1)
        for token in re.findall(r'''"[^"]*"|'[^']*'|[^\s]+''', args):
            value = token.strip('"\'')
            if not value or value.startswith("/"):
                continue
            if value.startswith("-"):
                continue
            try:
                target = _target_path(value, cwd)
            except GuardError:
                return True
            if not any(_same(target, prior) for prior in targets):
                targets.append(target)
            break
    for target in targets:
        if _same(target, cwd) or _same(target, repo):
            return True
    # A wildcard or no recognizable target leaves the deletion scope unresolved.
    if re.search(r"(?i)(?:-\s*(?:literalpath|path)\s+)[^\r\n;&|]*\*", command):
        return True
    if command_match:
        args = command_match.group(1)
        # A recursive delete without a recognized path is cwd-wide by default.
        if not targets and not re.search(r"(?<![\w-])/[^\s-]+", args):
            return True
    return not targets


def _patch_text(tool_input: Any) -> str:
    if isinstance(tool_input, str):
        return tool_input
    if isinstance(tool_input, dict):
        # Current apply_patch sends the patch in `command`; older clients used
        # `patch` or `input`.  Accept all three without accepting arbitrary
        # nested transcript fields.
        for key in ("command", "patch", "input"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    raise GuardError("apply_patch payload has no patch text")


def _guard_patch(
    cwd: Path,
    allowed_roots: list[Path],
    tool_input: Any,
    forbidden_roots: tuple[Path, ...] = (),
) -> None:
    paths = PATCH_PATH.findall(_patch_text(tool_input))
    if not paths:
        raise GuardError("apply_patch payload has no recognized file paths")
    for raw in paths:
        resolved = _target_path(raw, cwd)
        if any(_inside(resolved, root) for root in forbidden_roots):
            raise GuardError(f"apply_patch target is reserved for another role: {resolved}")
        if not any(_inside(resolved, root) for root in allowed_roots):
            raise GuardError(f"apply_patch target is outside the writable scope: {resolved}")


def _guard_shell(
    repo: Path,
    cwd: Path,
    allowed_roots: list[Path],
    tool_input: Any,
) -> None:
    if isinstance(tool_input, str):
        command = tool_input
    elif isinstance(tool_input, dict):
        command = tool_input.get("command")
        if not isinstance(command, str):
            command = tool_input.get("cmd")
        if not isinstance(command, str):
            command = tool_input.get("script")
    else:
        command = None
    if not isinstance(command, str) or not command.strip():
        raise GuardError("shell payload has no command")
    if GLOBAL_MUTATION.search(command):
        raise GuardError("mount, path alias, or raw Git worktree mutation is forbidden")

    mutating = bool(MUTATION.search(command) or REDIRECTION.search(command))
    if not mutating:
        return
    if DYNAMIC_TARGET.search(command):
        raise GuardError("dynamic mutation target cannot be proven inside the writable scope")
    if _recursive_delete_is_broad(command, cwd, repo):
        raise GuardError("recursive deletion target is broad or unresolved")
    target_paths = _extract_target_paths(command, cwd)
    absolute_paths = _extract_absolute_paths(command, cwd)
    candidates = target_paths + [path for path in absolute_paths if not any(_same(path, prior) for prior in target_paths)]
    if not candidates:
        if not any(_inside(cwd, root) for root in allowed_roots):
            raise GuardError(f"working directory is outside the writable scope: {cwd}")
        return
    for candidate in candidates:
        if not any(_inside(candidate, root) for root in allowed_roots):
            raise GuardError(f"mutation target is outside the writable scope: {candidate}")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as exc:
        return _emit_deny(f"invalid hook payload: {exc}")
    event_name = payload.get("hook_event_name") or payload.get("event_name") or payload.get("event")
    if str(event_name).replace("_", "").lower() != "pretooluse":
        return 0
    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "").lower()
    if tool_name not in SHELL_TOOLS | PATCH_TOOLS:
        return 0
    try:
        cwd_raw = payload.get("cwd") or payload.get("working_directory")
        # The CLI normally supplies cwd. If an older hook payload omits it,
        # the launcher itself is already running from the project root.
        cwd_input = Path(cwd_raw) if isinstance(cwd_raw, str) and cwd_raw else Path.cwd()
        if _has_path_alias(cwd_input):
            raise GuardError("symlink or path alias working directory is forbidden")
        cwd = _canonical(cwd_input)
        repo, allowed_roots, _git_verified = _workspace_scope(cwd)
        if tool_name in PATCH_TOOLS:
            _guard_patch(
                cwd,
                allowed_roots,
                payload.get("tool_input"),
            )
        else:
            _guard_shell(
                repo,
                cwd,
                allowed_roots,
                payload.get("tool_input"),
            )
    except (GuardError, OSError) as exc:
        return _emit_deny(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
