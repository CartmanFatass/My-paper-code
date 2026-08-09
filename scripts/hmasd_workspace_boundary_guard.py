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
import stat
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
IDENTITY_OBSERVATION_DIRECTORY = (
    Path("temp") / "sessions" / "research_scheduler" / "identity_observations"
)
IDENTITY_OBSERVATION_KEYS = frozenset(
    {"assignment_id", "thread_id", "host_id", "session_id"}
)
IDENTITY_OBSERVATION_INTERPRETER = (
    "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
)
IDENTITY_OBSERVATION_SCRIPT = "scripts/hmasd_workspace_boundary_guard.py"
IDENTITY_THREAD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")


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


def _registered_python(repo: Path) -> str | None:
    router = repo / "AGENTS.md"
    if not router.is_file():
        return None
    matches = re.findall(
        r"(?m)^hmasd_python_interpreter=([^\r\n]+?)\s*$",
        router.read_text(encoding="utf-8"),
    )
    return matches[0] if len(matches) == 1 else None


def _valid_identity_session(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and not any(character.isspace() for character in value)
    )


def _valid_identity_thread(value: Any) -> bool:
    return isinstance(value, str) and bool(IDENTITY_THREAD_ID.fullmatch(value))


def _parse_identity_observation_command(command: Any) -> tuple[str, str]:
    if not isinstance(command, str):
        raise GuardError("owner identity observation command is not a string")
    pattern = re.compile(
        rf"^{re.escape(IDENTITY_OBSERVATION_INTERPRETER)} "
        rf"{re.escape(IDENTITY_OBSERVATION_SCRIPT)} observe-owner-session "
        r"--assignment-id (?P<assignment>[A-Za-z0-9][A-Za-z0-9_-]{0,95}) "
        r"--thread-id (?P<thread>[A-Za-z0-9][A-Za-z0-9._:-]{0,255}) "
        r"--host-id local$"
    )
    match = pattern.fullmatch(command)
    if match is None:
        raise GuardError("owner identity observation command is malformed or unsafe")
    assignment_id = match.group("assignment")
    thread_id = match.group("thread")
    if not ticketing.ASSIGNMENT_ID.fullmatch(assignment_id):
        raise GuardError("owner identity observation assignment_id is unsafe")
    if not _valid_identity_thread(thread_id):
        raise GuardError("owner identity observation thread_id is unsafe")
    return assignment_id, thread_id


def _identity_observation_root(repo: Path, *, create: bool) -> Path:
    repository = _canonical(repo)
    expected_parent = repository / "temp" / "sessions" / "research_scheduler"
    parent = expected_parent.resolve(strict=False)
    if not _same(parent, expected_parent):
        raise GuardError("identity observation directory is redirected")
    requested = repository / IDENTITY_OBSERVATION_DIRECTORY
    if requested.exists() and (
        requested.is_symlink()
        or bool(
            getattr(requested.stat(), "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        )
    ):
        raise GuardError("identity observation directory is redirected")
    if create:
        requested.mkdir(parents=True, exist_ok=True)
    if not requested.is_dir():
        raise GuardError("identity observation directory is not a directory")
    return requested


def _identity_observation_path(
    repo: Path, assignment_id: str, *, create_root: bool
) -> Path:
    if not ticketing.ASSIGNMENT_ID.fullmatch(assignment_id):
        raise GuardError("owner identity observation assignment_id is unsafe")
    root = _identity_observation_root(repo, create=create_root)
    path = root / f"{assignment_id}.json"
    if path.exists() and path.is_symlink():
        raise GuardError("identity observation file is redirected")
    resolved = path.resolve(strict=False)
    if not _inside(resolved, root) or not _same(resolved, path):
        raise GuardError("identity observation file is redirected")
    return path


def _validate_identity_observation(
    value: Any,
    *,
    assignment_id: str,
    thread_id: str,
) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != IDENTITY_OBSERVATION_KEYS:
        raise GuardError("identity observation is malformed")
    if value.get("assignment_id") != assignment_id:
        raise GuardError("identity observation assignment_id does not match")
    if value.get("thread_id") != thread_id:
        raise GuardError("identity observation thread_id does not match")
    if value.get("host_id") != "local":
        raise GuardError("identity observation host_id is not local")
    if not _valid_identity_session(value.get("session_id")):
        raise GuardError("identity observation session_id is malformed")
    return {
        "assignment_id": assignment_id,
        "thread_id": thread_id,
        "host_id": "local",
        "session_id": value["session_id"],
    }


def _read_identity_observation(
    repo: Path, assignment_id: str, thread_id: str
) -> dict[str, str]:
    path = _identity_observation_path(repo, assignment_id, create_root=False)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GuardError(f"identity observation cannot be read: {exc}") from exc
    return _validate_identity_observation(
        value, assignment_id=assignment_id, thread_id=thread_id
    )


def _persist_identity_observation(
    repo: Path,
    *,
    assignment_id: str,
    thread_id: str,
    session_id: str,
) -> None:
    observation = {
        "assignment_id": assignment_id,
        "thread_id": thread_id,
        "host_id": "local",
        "session_id": session_id,
    }
    path = _identity_observation_path(repo, assignment_id, create_root=True)
    if path.exists():
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GuardError(f"identity observation is malformed: {exc}") from exc
        validated = _validate_identity_observation(
            current, assignment_id=assignment_id, thread_id=thread_id
        )
        if validated == observation:
            return
        raise GuardError("conflicting identity observation will not be overwritten")
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(observation, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
    except FileExistsError:
        # A concurrent identical write may have won the create race. Re-read
        # and apply the same conflict/malformed checks without overwriting.
        current = _read_identity_observation(repo, assignment_id, thread_id)
        if current != observation:
            raise GuardError("conflicting identity observation will not be overwritten")


def _observe_owner_session(
    repo: Path,
    cwd: Path,
    linked: bool,
    payload: dict[str, Any],
    command: str,
) -> None:
    assignment_id, thread_id = _parse_identity_observation_command(command)
    session_id = payload.get("session_id")
    if not _valid_identity_session(session_id):
        raise GuardError("owner identity observation requires a valid payload session_id")
    inherited_thread_id = os.environ.get("CODEX_THREAD_ID")
    if not _valid_identity_thread(inherited_thread_id):
        raise GuardError("owner identity observation requires CODEX_THREAD_ID")
    if inherited_thread_id != thread_id:
        raise GuardError("owner identity observation thread_id does not match CODEX_THREAD_ID")
    observation_repo = ticketing.main_checkout(repo) if linked else repo
    _persist_identity_observation(
        observation_repo,
        assignment_id=assignment_id,
        thread_id=thread_id,
        session_id=session_id,
    )


def _run_observe_owner_session_cli(argv: list[str]) -> int:
    if len(argv) != 7 or argv[0] != "observe-owner-session":
        print("malformed observe-owner-session arguments", file=sys.stderr)
        return 2
    if argv[1] != "--assignment-id" or argv[3] != "--thread-id" or argv[5] != "--host-id":
        print("malformed observe-owner-session arguments", file=sys.stderr)
        return 2
    assignment_id, thread_id = argv[2], argv[4]
    if not ticketing.ASSIGNMENT_ID.fullmatch(assignment_id):
        print("unsafe observe-owner-session assignment_id", file=sys.stderr)
        return 2
    if not _valid_identity_thread(thread_id):
        print("unsafe observe-owner-session thread_id", file=sys.stderr)
        return 2
    if argv[6] != "local":
        print("observe-owner-session host_id must be local", file=sys.stderr)
        return 2
    inherited_thread_id = os.environ.get("CODEX_THREAD_ID")
    if not _valid_identity_thread(inherited_thread_id):
        print("observe-owner-session requires CODEX_THREAD_ID", file=sys.stderr)
        return 2
    if inherited_thread_id != thread_id:
        print("observe-owner-session thread_id does not match CODEX_THREAD_ID", file=sys.stderr)
        return 2
    try:
        cwd = _canonical(Path.cwd())
        repo, _, linked = _workspace_scope(cwd)
        observation_repo = ticketing.main_checkout(repo) if linked else repo
        observation = _read_identity_observation(
            observation_repo, assignment_id, thread_id
        )
    except (GuardError, OSError, ticketing.TicketError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(observation, sort_keys=True, separators=(",", ":")))
    return 0


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


def _binding_owned_roots(repo: Path) -> tuple[Path, ...]:
    return tuple(
        _canonical(repo / relative)
        for relative in (
            Path("local_research"),
            Path("temp") / "handoffs" / "explorer_to_code_manager",
            ticketing.TREATMENT_TRANSPORT_DIRECTORY,
        )
    )


def _binding_scope_requires_exact_session(
    repo: Path,
    cwd: Path,
    linked: bool,
    tool_name: str,
    tool_input: Any,
) -> bool:
    """Identify mutations that cannot be authorized without an exact owner binding."""

    if tool_name in PATCH_TOOLS:
        try:
            raw_paths = PATCH_PATH.findall(_patch_text(tool_input))
        except GuardError:
            return False
        candidates = [
            _canonical(
                Path(raw.strip())
                if Path(raw.strip()).is_absolute()
                else cwd / Path(raw.strip())
            )
            for raw in raw_paths
        ]
        return any(
            _inside(candidate, root)
            for candidate in candidates
            for root in _binding_owned_roots(repo)
        ) or linked
    if tool_name not in SHELL_TOOLS:
        return False
    if not isinstance(tool_input, dict) or not isinstance(tool_input.get("command"), str):
        return False
    command = tool_input["command"]
    mutating = bool(
        MUTATION.search(command)
        or re.search(r"(?m)(?<![<>=])-?>{1,2}(?![=])", command)
    )
    if not mutating:
        return False
    if linked:
        return True
    normalized_command = command.replace("\\", "/").lower()
    if any(
        marker in normalized_command
        for marker in (
            "local_research",
            "temp/handoffs/explorer_to_code_manager",
            "temp/handoffs/code_manager_to_explorer",
        )
    ):
        return True
    absolute_paths = _extract_absolute_paths(command)
    candidates = absolute_paths or [cwd]
    return any(
        _inside(candidate, root)
        for candidate in candidates
        for root in _binding_owned_roots(repo)
    )


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
            raise GuardError("Git mutation is forbidden for the independent research owner task")
        if RESEARCH_UNSAFE_EXPRESSION.search(command):
            raise GuardError("nested or executable shell expression is forbidden")
        if re.search(r"(?:;|&&|\|\||\||&|\r|\n|>|<|`|\$\()", command):
            raise GuardError("compound shell commands are forbidden for the research owner task")
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
        if tool_name in SHELL_TOOLS:
            tool_input = payload.get("tool_input")
            command = (
                tool_input.get("command")
                if isinstance(tool_input, dict)
                else None
            )
            if isinstance(command, str) and "observe-owner-session" in command:
                _observe_owner_session(repo, cwd, linked, payload, command)
                return 0
        shell_allowed_roots = allowed_roots
        binding_repo = ticketing.main_checkout(repo) if linked else repo
        session_id = payload.get("session_id")
        valid_session = (
            isinstance(session_id, str)
            and bool(session_id)
            and not any(character.isspace() for character in session_id)
        )
        binding = (
            ticketing.resolve_scheduler_binding(binding_repo, session_id=session_id)
            if valid_session
            else None
        )
        if binding is None and _binding_scope_requires_exact_session(
            binding_repo,
            cwd,
            linked,
            tool_name,
            payload.get("tool_input"),
        ):
            raise GuardError("binding-scoped mutation requires an exact active session binding")
        research_role = (
            "explorer"
            if binding is not None
            and binding["owner_role"] == "independent_research_explorer"
            else None
        )
        review_root = _canonical(repo / "local_research" / "pro_reviews")
        if research_role is None:
            if _inside(cwd, review_root) and binding is None:
                raise GuardError(
                    "local_research/pro_reviews requires an active Scheduler Explorer binding"
                )
        forbidden_roots: tuple[Path, ...] = ()
        if research_role is not None:
            if linked:
                raise GuardError("independent research is confined to the main checkout")
            allowed_roots = [
                _canonical(repo / Path(relative))
                for relative in binding["allowed_write_paths"]
            ]
            shell_allowed_roots = allowed_roots
        elif binding is not None and binding["owner_role"] == "code_project_manager":
            if binding["owner_mode"] == "treatment":
                if not linked:
                    raise GuardError("treatment binding requires its registered linked worktree")
                _, binding_worktree, binding_allowed = ticketing.resolve_binding_ticket(binding_repo, binding)
                if not _same(binding_worktree, cwd):
                    raise GuardError("treatment binding does not match the active worktree")
                allowed_roots = []
                shell_allowed_roots = []
                for relative in binding_allowed:
                    if ticketing.is_treatment_transport_path(binding_repo, relative):
                        allowed_roots.append(_canonical(binding_repo / Path(relative)))
                    else:
                        root = _canonical(cwd / Path(relative))
                        allowed_roots.append(root)
                        shell_allowed_roots.append(root)
            else:
                if linked:
                    raise GuardError("integration binding is confined to the main checkout")
                allowed_roots = [
                    _canonical(repo / Path(relative))
                    for relative in binding["allowed_write_paths"]
                ]
                shell_allowed_roots = allowed_roots
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
                shell_allowed_roots,
                linked,
                payload.get("tool_input"),
                research_role,
            )
    except (GuardError, OSError, ticketing.TicketError) as exc:
        return _emit_deny(str(exc))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raise SystemExit(_run_observe_owner_session_cli(sys.argv[1:]))
    raise SystemExit(main())
