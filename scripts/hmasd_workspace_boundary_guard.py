"""Fail closed for recognized writes outside the active HMASD workspace.

This PreToolUse syntactic guard preserves its existing denials and complements
the tool/OS sandbox, registered ticket identity and Git-visible checks. It does
not replace those authoritative controls or claim to parse arbitrary shell
semantics.
"""

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
GIT_MUTATION = re.compile(
    r"(?i)\bgit(?:\.exe)?\b[^\r\n;&|]*\b(?:add|am|apply|branch|checkout|"
    r"cherry-pick|clean|clone|commit|fetch|init|merge|mv|pull|push|rebase|"
    r"reset|restore|revert|rm|stash|switch|tag|worktree)\b"
)
RESEARCH_READ_ONLY_COMMAND = re.compile(
    r"(?i)^\s*(?:get-content|get-childitem|get-item|get-filehash|select-string|"
    r"test-path|resolve-path|measure-object|compare-object|rg(?:\.exe)?|"
    r"git(?:\.exe)?\s+(?:status|diff|log|show|rev-parse|ls-files|check-ignore))\b"
)
RESEARCH_UNSAFE_READ_OPTION = re.compile(
    r"(?i)(?:^|\s)(?:--pre(?:-glob)?(?:=|\s)|--output(?:=|\s)|"
    r"--exec-path(?:=|\s)|--hostname-bin(?:=|\s)|"
    r"--ext-diff(?:\s|$)|--textconv(?:\s|$))"
)
RESEARCH_UNSAFE_EXPRESSION = re.compile(
    r"(?i)(?:[\(\)\{\}\[\]]|::|\b(?:start-process|invoke-expression|iex)\b)"
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
PATCH_PATH = re.compile(
    r"(?m)^\*\*\* (?:(?:Add|Update|Delete) File:|Move to:) (.+?)\s*$"
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


def _registered_research_sessions(repo: Path) -> dict[str, str]:
    role_path = repo / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md"
    if not role_path.is_file():
        return {}
    text = role_path.read_text(encoding="utf-8")
    fields = {"explorer": "session_id"}
    sessions: dict[str, str] = {}
    for role, field in fields.items():
        matches = re.findall(rf"(?m)^{field}=([^\s]+)\s*$", text)
        if len(matches) > 1:
            raise GuardError(f"role charter has multiple {role} sessions")
        if matches:
            sessions[role] = matches[0]
    if len(set(sessions.values())) != len(sessions):
        raise GuardError("independent research roles share one session identity")
    return sessions


def _registered_python(repo: Path) -> str | None:
    router = repo / "AGENTS.md"
    if not router.is_file():
        return None
    matches = re.findall(
        r"(?m)^hmasd_python_interpreter=([^\r\n]+?)\s*$",
        router.read_text(encoding="utf-8"),
    )
    return matches[0] if len(matches) == 1 else None


def _registered_script_prefix(command: str, interpreter: str, script: Path) -> bool:
    normalized = command.strip().replace("\\", "/")
    normalized_interpreter = interpreter.replace("\\", "/")
    registered = str(script).replace("\\", "/")
    prefix = re.compile(
        rf'^"?{re.escape(normalized_interpreter)}"?\s+'
        rf'"?{re.escape(registered)}"?(?:\s|$)',
        re.IGNORECASE,
    )
    return bool(prefix.match(normalized))


def _trusted_research_script(
    command: str,
    repo: Path,
    role: str,
) -> bool:
    if re.search(r"(?:;|&&|\|\||\||&|\r|\n|>|<|`|\$\()", command):
        return False
    interpreter = _registered_python(repo)
    if interpreter is None:
        return False
    if role == "explorer":
        forbidden = str(repo / "local_research" / "pro_reviews").replace("\\", "/")
        normalized = command.replace("\\", "/")
        if (
            forbidden.lower() in normalized.lower()
            or "local_research/pro_reviews" in normalized.lower()
        ):
            return False
        for basename in ("mylib_research_probe.py", "research_portfolio_gate.py"):
            script = (
                repo
                / ".agents"
                / "skills"
                / "hmasd-independent-research-exploration"
                / "scripts"
                / basename
            )
            if _registered_script_prefix(command, interpreter, script):
                return True
        return False

    return False


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
        candidate = Path(raw.strip())
        resolved = _canonical(candidate if candidate.is_absolute() else cwd / candidate)
        if any(_inside(resolved, root) for root in forbidden_roots):
            raise GuardError(f"apply_patch target is reserved for another role: {resolved}")
        if not any(_inside(resolved, root) for root in allowed_roots):
            raise GuardError(f"apply_patch target is outside the writable scope: {resolved}")


def _guard_shell(
    repo: Path,
    cwd: Path,
    allowed_roots: list[Path],
    linked: bool,
    tool_input: Any,
    research_role: str | None = None,
) -> None:
    if not isinstance(tool_input, dict) or not isinstance(tool_input.get("command"), str):
        raise GuardError("shell payload has no command")
    command = tool_input["command"]
    if research_role is not None:
        if GIT_MUTATION.search(command) or re.search(
            r"(?i)(?:^|\s)git(?:\.exe)?(?:\s|$)", command
        ):
            raise GuardError("Git mutation is forbidden for the independent research session")
        if RESEARCH_UNSAFE_EXPRESSION.search(command):
            raise GuardError("nested or executable shell expression is forbidden")
        if re.search(r"(?:;|&&|\|\||\||&|\r|\n|>|<|`|\$\()", command):
            raise GuardError("compound shell commands are forbidden for the research session")
        if _trusted_research_script(command, repo, research_role):
            return
        if RESEARCH_UNSAFE_READ_OPTION.search(command):
            raise GuardError("shell option can execute or write and is forbidden")
        known_mutation = bool(
            MUTATION.search(command)
            or re.search(r"(?m)(?<![<>=])-?>{1,2}(?![=])", command)
        )
        if known_mutation:
            raise GuardError(
                "research shell mutation is forbidden; use apply_patch under local_research"
            )
        if not RESEARCH_READ_ONLY_COMMAND.search(command):
            raise GuardError(
                "research shell command is not an approved read-only form; "
                "use a registered research script or apply_patch under local_research"
            )
        return
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
        registered = _registered_research_sessions(repo)
        session_id = payload.get("session_id")
        research_role = next(
            (
                role
                for role, registered_session in registered.items()
                if isinstance(session_id, str) and session_id == registered_session
            ),
            None,
        )
        review_root = _canonical(repo / "local_research" / "pro_reviews")
        if research_role is None:
            if _inside(cwd, review_root):
                raise GuardError(
                    "local_research/pro_reviews requires the registered persistent session"
                )
        forbidden_roots: tuple[Path, ...] = ()
        if research_role is not None:
            if linked:
                raise GuardError("independent research is confined to the main checkout")
            allowed_roots = [_canonical(repo / "local_research")]
        if tool_name in PATCH_TOOLS:
            _guard_patch(
                cwd,
                allowed_roots,
                payload.get("tool_input"),
                forbidden_roots,
            )
        else:
            _guard_shell(
                repo,
                cwd,
                allowed_roots,
                linked,
                payload.get("tool_input"),
                research_role,
            )
    except (GuardError, OSError, ticketing.TicketError) as exc:
        return _emit_deny(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
