#!/usr/bin/env python3
"""Admit and detach one result-bearing HMASD Python runner.

The launcher is a cooperative safety kernel.  It verifies the current owner
pause and direction lead in the canonical control checkout, exact published
source, a clean tracked tree, the configured interpreter, a fresh actual-node
memory preflight, and a persistent idempotency claim.  It never invokes a
shell.  The runner must call ``hmasd_admission.require_admission`` before doing
result-bearing work.

Remote sparse checkouts must include ``.codex/hmasd-compute.toml`` and
``docs/research/RESEARCH.md`` in the configured canonical ``repo_root``.  A
frozen source snapshot alone is deliberately insufficient authority to launch.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
from dataclasses import dataclass
import datetime as _datetime
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterator, Mapping, Sequence

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 on the configured compute nodes.
    import tomli as tomllib  # type: ignore[no-redef]

try:
    from scripts import hmasd_admission
    from scripts import hmasd_platform
    from scripts import hmasd_resource_preflight
except ImportError:
    import hmasd_admission
    import hmasd_platform
    import hmasd_resource_preflight


SCHEMA_VERSION = 1
FULL_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
DIRECTION_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
REMOTE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
RECOGNIZED_ACTIVE_STATES = {"exploring", "confirming"}
RETRYABLE_CLAIM_STATES = {"preflight_refused", "spawn_failed"}
OUTPUT_ARGUMENTS = {"--output", "--output-root", "--out"}
MAX_MESSAGE_BYTES = 64 * 1024


class LaunchRefusal(RuntimeError):
    """A launch condition failed before safe acceptance was established."""

    def __init__(self, message: str, *, exit_code: int = 4) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class DirectionState:
    direction: str
    state: str
    lead: str


@dataclass(frozen=True)
class LaunchPaths:
    source_root: Path
    control_root: Path
    config_path: Path
    output_root: Path
    runner: Path
    bootstrap: Path
    git_common_dir: Path


def _utc_now() -> str:
    return (
        _datetime.datetime.now(_datetime.timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _normalized_path(path: str | os.PathLike[str]) -> str:
    return os.path.normcase(str(Path(path).resolve(strict=False))).replace("\\", "/")


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=".hmasd-launch-",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = stream.name
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        hmasd_platform.fsync_directory(path.parent)
    finally:
        if temporary is not None:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary)


def _run_git(
    root: Path,
    *arguments: str,
    check: bool = True,
    timeout: float = 30.0,
) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            env=environment,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise LaunchRefusal(f"git {' '.join(arguments)} failed: {exc}") from exc
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise LaunchRefusal(f"git {' '.join(arguments)} refused: {detail}")
    return result


def _git_root(path: Path) -> Path:
    result = _run_git(path, "rev-parse", "--show-toplevel")
    return Path(result.stdout.strip()).resolve(strict=True)


def _git_common_dir(root: Path) -> Path:
    result = _run_git(root, "rev-parse", "--git-common-dir")
    path = Path(result.stdout.strip())
    if not path.is_absolute():
        path = root / path
    return path.resolve(strict=True)


def _common_worktree_root(common_dir: Path) -> Path | None:
    if common_dir.name.lower() == ".git" and common_dir.parent.is_dir():
        return common_dir.parent.resolve(strict=True)
    return None


def _load_config(path: Path) -> Mapping[str, Any]:
    try:
        with path.open("rb") as stream:
            value = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise LaunchRefusal(f"cannot read compute configuration {path}: {exc}") from exc
    if not isinstance(value, Mapping) or value.get("status") != "active":
        raise LaunchRefusal("compute configuration is missing or inactive")
    return value


def _node_config(config: Mapping[str, Any], requested: str | None) -> tuple[str, Mapping[str, Any]]:
    node = requested or config.get("control_plane_node")
    if not isinstance(node, str) or not node:
        raise LaunchRefusal("no execution node was selected")
    nodes = config.get("nodes")
    entry = nodes.get(node) if isinstance(nodes, Mapping) else None
    if not isinstance(entry, Mapping):
        raise LaunchRefusal(f"execution node {node!r} is not configured")
    if entry.get("enabled") is False:
        raise LaunchRefusal(f"execution node {node!r} is disabled")
    return node, entry


def _configured_root(entry: Mapping[str, Any]) -> Path:
    raw = entry.get("project_root", entry.get("repo_root"))
    if not isinstance(raw, str) or not raw:
        raise LaunchRefusal("selected node has no canonical project_root or repo_root")
    return Path(raw).expanduser().resolve(strict=False)


def _locate_config(source_root: Path, common_root: Path | None) -> Path:
    # In a linked worktree the common worktree is the live control checkout.
    # Never let an exact-SHA source snapshot redirect control by supplying a
    # different compute file of its own.
    candidates: list[Path] = []
    if common_root is not None:
        candidates.append(common_root / ".codex" / "hmasd-compute.toml")
    if common_root is None or common_root == source_root:
        candidates.append(source_root / ".codex" / "hmasd-compute.toml")
    existing = [candidate for candidate in candidates if candidate.is_file()]
    if not existing:
        raise LaunchRefusal(
            "canonical .codex/hmasd-compute.toml is unavailable; remote sparse policy "
            "must include .codex/hmasd-compute.toml and docs/research/RESEARCH.md"
        )
    return existing[0].resolve(strict=True)


def _resolve_control_root(
    source_root: Path,
    common_root: Path | None,
    configured_root: Path,
) -> Path:
    if common_root is not None and common_root.is_dir():
        common_control = _git_root(common_root)
        if common_control != common_root.resolve(strict=True):
            raise LaunchRefusal("Git common worktree is not a canonical worktree root")
        if configured_root.is_dir():
            configured_control = _git_root(configured_root)
            if configured_control != configured_root.resolve(strict=True):
                raise LaunchRefusal("configured canonical control path is not a Git worktree root")
            if configured_control != common_control:
                raise LaunchRefusal(
                    "compute configuration conflicts with the Git common control checkout"
                )
        elif common_control == source_root:
            raise LaunchRefusal(
                f"configured canonical control checkout is unavailable: {configured_root}; "
                "a standalone source snapshot cannot authorize itself"
            )
        return common_control
    if configured_root.is_dir():
        control = _git_root(configured_root)
        if control != configured_root.resolve(strict=True):
            raise LaunchRefusal("configured canonical control path is not a Git worktree root")
        return control
    raise LaunchRefusal(
        f"configured canonical control checkout is unavailable: {configured_root}; "
        "a source snapshot alone cannot authorize a launch"
    )


def parse_research_state(text: str, direction: str) -> tuple[str, DirectionState]:
    pause_values = [value.strip().lower() for value in re.findall(
        r"\*\*Owner pause:\s*([^*]+?)\*\*", text, flags=re.IGNORECASE
    )]
    if len(pause_values) != 1:
        raise LaunchRefusal("RESEARCH.md must contain exactly one recognized owner pause state")
    pause = pause_values[0]
    if pause not in {"in force", "lifted"}:
        raise LaunchRefusal(f"RESEARCH.md owner pause state is unrecognized: {pause!r}")

    active_match = re.search(
        r"(?ms)^## Active\s*$\n(?P<body>.*?)(?=^##\s|\Z)", text
    )
    if active_match is None:
        raise LaunchRefusal("RESEARCH.md has no unambiguous Active section")
    rows: list[DirectionState] = []
    for raw_line in active_match.group("body").splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in line[1:-1].split("|")]
        if len(cells) < 5 or cells[0].lower() == "direction" or set(cells[0]) <= {"-", ":"}:
            continue
        observed_direction = cells[0].strip("`")
        if observed_direction == direction:
            rows.append(
                DirectionState(
                    direction=observed_direction,
                    state=cells[2].strip("`").lower(),
                    lead=cells[3],
                )
            )
    if len(rows) != 1:
        raise LaunchRefusal(
            f"direction {direction!r} must appear exactly once in the Active table"
        )
    if rows[0].state not in RECOGNIZED_ACTIVE_STATES:
        raise LaunchRefusal(
            f"direction {direction!r} has unrecognized active state {rows[0].state!r}"
        )
    return pause, rows[0]


def _published_control_text(control_root: Path, remote: str) -> str:
    branch_result = _run_git(
        control_root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False
    )
    branch = branch_result.stdout.strip()
    if branch_result.returncode != 0 or not branch:
        raise LaunchRefusal("canonical control checkout must be on a named branch")
    upstream_result = _run_git(
        control_root,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
        check=False,
    )
    upstream = upstream_result.stdout.strip()
    if upstream_result.returncode == 0 and "/" in upstream:
        upstream_remote, remote_branch = upstream.split("/", 1)
        if upstream_remote != remote:
            raise LaunchRefusal(
                f"canonical control upstream uses {upstream_remote!r}, not requested {remote!r}"
            )
    else:
        remote_branch = branch
    advertised = _run_git(
        control_root,
        "ls-remote",
        "--heads",
        remote,
        f"refs/heads/{remote_branch}",
        timeout=60.0,
    ).stdout.splitlines()
    if len(advertised) != 1:
        raise LaunchRefusal(
            f"cannot establish one published control head for {remote}/{remote_branch}"
        )
    remote_sha = advertised[0].split()[0].lower()
    if FULL_SHA_RE.fullmatch(remote_sha) is None:
        raise LaunchRefusal("published control branch returned an invalid SHA")
    available = _run_git(
        control_root, "cat-file", "-e", f"{remote_sha}^{{commit}}", check=False
    )
    if available.returncode != 0:
        raise LaunchRefusal(
            "canonical control checkout has not fetched the published control head; sync it "
            "before launch"
        )
    published = _run_git(
        control_root,
        "show",
        f"{remote_sha}:docs/research/RESEARCH.md",
        check=False,
    )
    if published.returncode != 0:
        raise LaunchRefusal("published control head has no docs/research/RESEARCH.md")
    return published.stdout


def _require_local_policy(
    control_root: Path, direction: str, lead: str
) -> tuple[DirectionState, str]:
    research = control_root / "docs" / "research" / "RESEARCH.md"
    if not research.is_file():
        raise LaunchRefusal(
            f"canonical control checkout lacks {research}; remote sparse policy must "
            "include docs/research/RESEARCH.md"
        )
    try:
        text = research.read_text(encoding="utf-8")
    except OSError as exc:
        raise LaunchRefusal(f"cannot read canonical RESEARCH.md: {exc}") from exc
    pause, state = parse_research_state(text, direction)
    if pause != "lifted":
        raise LaunchRefusal("owner pause is in force", exit_code=3)
    if state.lead != lead:
        raise LaunchRefusal(
            f"direction lead mismatch: RESEARCH.md records {state.lead!r}, not {lead!r}"
        )
    return state, text


def _require_policy(
    control_root: Path, direction: str, lead: str, remote: str = "origin"
) -> tuple[DirectionState, str]:
    state, text = _require_local_policy(control_root, direction, lead)
    published_text = _published_control_text(control_root, remote)
    if published_text != text:
        raise LaunchRefusal(
            "canonical RESEARCH.md differs from the fresh published control branch; sync or "
            "publish the control state before launch"
        )
    published_pause, published_state = parse_research_state(published_text, direction)
    if published_pause != "lifted" or published_state != state:
        raise LaunchRefusal("published control state does not authorize this direction and lead")
    return state, hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require_full_sha(value: str) -> str:
    normalized = value.lower()
    if FULL_SHA_RE.fullmatch(normalized) is None:
        raise LaunchRefusal("--sha must be a full 40-character hexadecimal commit SHA")
    return normalized


def _validate_source_local(source_root: Path, sha: str) -> None:
    observed = _run_git(source_root, "rev-parse", "HEAD").stdout.strip().lower()
    if observed != sha:
        raise LaunchRefusal(f"source HEAD is {observed}, not requested SHA {sha}")
    status_lines = _run_git(
        source_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    ).stdout.splitlines()
    dirty: list[str] = []
    for line in status_lines:
        if not line:
            continue
        if line.startswith("?? "):
            relative = line[3:].replace("\\", "/")
            if relative == "runs" or relative.startswith("runs/"):
                continue
            if relative == "temp" or relative.startswith("temp/"):
                continue
        dirty.append(line)
    if dirty:
        raise LaunchRefusal("source checkout has modified, staged, or untracked source inputs")


def _validate_source(source_root: Path, sha: str, remote: str) -> None:
    _validate_source_local(source_root, sha)

    _run_git(
        source_root,
        "fetch",
        "--quiet",
        "--prune",
        "--no-tags",
        remote,
        timeout=120.0,
    )
    remote_refs = _run_git(
        source_root,
        "for-each-ref",
        "--format=%(refname)",
        f"refs/remotes/{remote}/",
    ).stdout.splitlines()
    published = False
    for reference in remote_refs:
        reference = reference.strip()
        if not reference or reference.endswith("/HEAD"):
            continue
        contains = _run_git(
            source_root,
            "merge-base",
            "--is-ancestor",
            sha,
            reference,
            check=False,
        )
        if contains.returncode == 0:
            published = True
            break
        if contains.returncode not in {0, 1}:
            detail = contains.stderr.strip() or f"exit {contains.returncode}"
            raise LaunchRefusal(f"cannot verify published SHA against {reference}: {detail}")
    if not published:
        raise LaunchRefusal(f"SHA {sha} is not contained in any freshly fetched {remote} ref")


def _has_alias_component(root: Path, target: Path) -> bool:
    current = root
    if hmasd_platform.is_reparse_or_symlink(current):
        return True
    for part in target.relative_to(root).parts:
        current = current / part
        if not current.exists():
            continue
        try:
            info = os.lstat(current)
        except OSError:
            return True
        if stat.S_ISLNK(info.st_mode) or hmasd_platform.is_reparse_or_symlink(current, info):
            return True
    return False


def _resolve_runner_and_output(
    source_root: Path,
    direction: str,
    output_raw: str,
    runner_argv: Sequence[str],
) -> tuple[Path, Path, list[str]]:
    if not runner_argv:
        raise LaunchRefusal("runner argv is required after --")
    runner_raw = runner_argv[0]
    runner = Path(runner_raw)
    if not runner.is_absolute():
        runner = source_root / runner
    runner = runner.resolve(strict=True)
    if runner.suffix.lower() != ".py" or not runner.is_file():
        raise LaunchRefusal("runner entry must be a Python script")
    try:
        runner.relative_to(source_root)
    except ValueError as exc:
        raise LaunchRefusal("runner entry is outside the source checkout") from exc
    if _has_alias_component(source_root, runner):
        raise LaunchRefusal("runner entry traverses a symlink or reparse point")
    tracked = _run_git(
        source_root,
        "ls-files",
        "--error-unmatch",
        runner.relative_to(source_root).as_posix(),
        check=False,
    )
    if tracked.returncode != 0:
        raise LaunchRefusal("runner entry is not a tracked input at the requested SHA")

    output = Path(output_raw)
    if not output.is_absolute():
        output = source_root / output
    output = output.resolve(strict=False)
    expected_parent = source_root / "runs" / direction
    try:
        relative = output.relative_to(expected_parent)
    except ValueError as exc:
        raise LaunchRefusal(
            f"output must be inside runs/{direction}/ in the source checkout"
        ) from exc
    if not relative.parts:
        raise LaunchRefusal("output must name a fresh tag below the direction run root")
    if _has_alias_component(source_root, output):
        raise LaunchRefusal("output path traverses a symlink or reparse point")

    arguments = [str(value) for value in runner_argv[1:]]
    bindings: list[Path] = []
    index = 0
    while index < len(arguments):
        value = arguments[index]
        if value in OUTPUT_ARGUMENTS:
            if index + 1 >= len(arguments):
                raise LaunchRefusal(f"{value} has no path value")
            candidate = Path(arguments[index + 1])
            if not candidate.is_absolute():
                candidate = source_root / candidate
            bindings.append(candidate.resolve(strict=False))
            index += 2
            continue
        matched = next((flag for flag in OUTPUT_ARGUMENTS if value.startswith(flag + "=")), None)
        if matched is not None:
            candidate = Path(value.split("=", 1)[1])
            if not candidate.is_absolute():
                candidate = source_root / candidate
            bindings.append(candidate.resolve(strict=False))
        index += 1
    if bindings != [output]:
        raise LaunchRefusal(
            "runner argv must bind the declared output exactly once with --output, "
            "--output-root, or --out"
        )
    return runner, output, arguments


def _validate_guard_contract(runner: Path, direction: str) -> None:
    try:
        tree = ast.parse(runner.read_text(encoding="utf-8"), filename=str(runner))
    except (OSError, SyntaxError, UnicodeError) as exc:
        raise LaunchRefusal(f"cannot inspect runner admission contract: {exc}") from exc
    matching_calls = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        name = function.id if isinstance(function, ast.Name) else (
            function.attr if isinstance(function, ast.Attribute) else None
        )
        if name != "require_admission" or not node.args:
            continue
        first = node.args[0]
        if not isinstance(first, ast.Name) or first.id != "__file__":
            continue
        direction_values = [
            keyword.value
            for keyword in node.keywords
            if keyword.arg == "direction"
        ]
        if len(direction_values) != 1:
            continue
        value = direction_values[0]
        if isinstance(value, ast.Constant) and value.value == direction:
            matching_calls += 1
    if matching_calls != 1:
        raise LaunchRefusal(
            "runner must contain exactly one require_admission(__file__, "
            f"direction={direction!r}) call before it can be spawned"
        )


def _command_identity(
    python: Path,
    runner: Path,
    arguments: Sequence[str],
    output: Path,
    source_root: Path,
) -> list[str]:
    scrubbed: list[str] = []
    index = 0
    while index < len(arguments):
        value = arguments[index]
        if value in OUTPUT_ARGUMENTS:
            index += 2
            continue
        matched = next((flag for flag in OUTPUT_ARGUMENTS if value.startswith(flag + "=")), None)
        if matched is not None:
            index += 1
            continue
        else:
            option_prefix = ""
            path_value = value
            if value.startswith("--") and "=" in value:
                option, path_value = value.split("=", 1)
                option_prefix = option + "="
            candidate = Path(path_value)
            if not candidate.is_absolute():
                candidate = source_root / candidate
            resolved = candidate.resolve(strict=False)
            if resolved == output:
                index += 1
                continue
            try:
                relative = resolved.relative_to(source_root)
            except ValueError:
                scrubbed.append(value)
            else:
                # Canonicalize paths inside equivalent linked worktrees.  Only
                # existing source inputs are rewritten, so ordinary scalar
                # argv values keep their exact spelling.
                scrubbed.append(
                    option_prefix + "<SOURCE>/" + relative.as_posix()
                    if resolved.exists()
                    else value
                )
        index += 1
    runner_relative = runner.relative_to(source_root).as_posix()
    return [_normalized_path(python), runner_relative, *scrubbed]


def _claim_key(direction: str, sha: str, identity_command: Sequence[str]) -> str:
    payload = {
        "direction": direction,
        "sha": sha,
        "command": list(identity_command),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@contextlib.contextmanager
def _claim_lock(common_dir: Path) -> Iterator[Path]:
    state_root = common_dir / "hmasd-admission"
    state_root.mkdir(parents=True, exist_ok=True)
    lock_path = state_root / "launch.lock"
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        hmasd_platform.apply_fd_mode(descriptor, 0o600)
        with hmasd_platform.exclusive_file_lock(descriptor):
            yield state_root
    finally:
        os.close(descriptor)


def _read_claim(path: Path) -> Mapping[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LaunchRefusal(f"existing idempotency claim is unreadable: {path}: {exc}") from exc
    if not isinstance(value, Mapping):
        raise LaunchRefusal(f"existing idempotency claim is invalid: {path}")
    return value


def _write_status(output: Path, status: str, **extra: Any) -> None:
    payload = {"schema_version": SCHEMA_VERSION, "status": status, "updated_at": _utc_now()}
    payload.update(extra)
    _atomic_write_json(output / "launch-status.json", payload)


def _read_message(stream: Any) -> Mapping[str, Any]:
    raw = stream.readline(MAX_MESSAGE_BYTES + 1)
    if not raw or len(raw) > MAX_MESSAGE_BYTES or not raw.endswith(b"\n"):
        raise LaunchRefusal("runner admission message is invalid", exit_code=7)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LaunchRefusal("runner admission message is invalid JSON", exit_code=7) from exc
    if not isinstance(value, Mapping):
        raise LaunchRefusal("runner admission message is not an object", exit_code=7)
    return value


def _write_message(stream: Any, value: Mapping[str, Any]) -> None:
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    stream.write(rendered)
    stream.flush()


def _spawn(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    stdout: Any,
    stderr: Any,
) -> subprocess.Popen[bytes]:
    options: dict[str, Any] = {
        "cwd": str(cwd),
        "env": dict(environment),
        "stdin": subprocess.DEVNULL,
        "stdout": stdout,
        "stderr": stderr,
        "shell": False,
    }
    if os.name == "nt":
        options["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, "DETACHED_PROCESS", 0x8)
        )
    else:
        options["start_new_session"] = True
    return subprocess.Popen(list(command), **options)


def _process_identity(process: subprocess.Popen[bytes]) -> Mapping[str, Any]:
    """Capture a reconnectable PID-birth identity for later supervision."""

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        created = wintypes.FILETIME()
        exited = wintypes.FILETIME()
        kernel = wintypes.FILETIME()
        user = wintypes.FILETIME()
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        ]
        kernel32.GetProcessTimes.restype = wintypes.BOOL
        handle = wintypes.HANDLE(int(getattr(process, "_handle")))
        if not kernel32.GetProcessTimes(
            handle,
            ctypes.byref(created),
            ctypes.byref(exited),
            ctypes.byref(kernel),
            ctypes.byref(user),
        ):
            raise LaunchRefusal("cannot capture Windows child creation identity", exit_code=7)
        created_100ns = (int(created.dwHighDateTime) << 32) | int(created.dwLowDateTime)
        return {
            "kind": "windows_pid_creation_time",
            "pid": process.pid,
            "creation_time_100ns": created_100ns,
        }

    try:
        stat_line = Path(f"/proc/{process.pid}/stat").read_text(encoding="utf-8")
        fields_after_name = stat_line[stat_line.rfind(")") + 2 :].split()
        start_ticks = int(fields_after_name[19])
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
    except (OSError, ValueError, IndexError) as exc:
        raise LaunchRefusal("cannot capture POSIX child birth identity", exit_code=7) from exc
    return {
        "kind": "linux_pid_start_ticks",
        "pid": process.pid,
        "boot_id": boot_id,
        "start_ticks": start_ticks,
        "session_id": process.pid,
    }


def _manifest(
    *,
    paths: LaunchPaths,
    node: str,
    direction: str,
    lead: str,
    sha: str,
    remote: str,
    command: Sequence[str],
    identity_command: Sequence[str],
    command_sha256: str,
    claim_key: str,
    process: subprocess.Popen[bytes],
    acceptance: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": _utc_now(),
        "direction": direction,
        "lead": lead,
        "node": node,
        "sha": sha,
        "published_remote": remote,
        "source_root": str(paths.source_root),
        "control_root": str(paths.control_root),
        "cwd": str(paths.source_root),
        "output_root": str(paths.output_root),
        "command": list(command),
        "identity_command": list(identity_command),
        "command_sha256": command_sha256,
        "claim_key": claim_key,
        "acceptance": acceptance,
        "process": {
            "pid": process.pid,
            "process_group_id": process.pid,
            "detached": True,
            "native_handle_kind": "windows_process_group" if os.name == "nt" else "posix_session",
            "identity": _process_identity(process),
        },
        "stdout": str(paths.output_root / "stdout.log"),
        "stderr": str(paths.output_root / "stderr.log"),
        "preflight": str(paths.output_root / "admission-preflight.json"),
    }


def _validate_hello(
    hello: Mapping[str, Any],
    *,
    nonce: str,
    expected_pid: int,
    parent_pid: int,
    direction: str,
    runner: Path,
    source_root: Path,
    sha: str,
    command_sha256: str,
) -> None:
    expected = {
        "schema_version": SCHEMA_VERSION,
        "kind": "hello",
        "nonce": nonce,
        "pid": expected_pid,
        "parent_pid": parent_pid,
        "direction": direction,
        "runner": _normalized_path(runner),
        "source_root": _normalized_path(source_root),
        "sha": sha,
        "command_sha256": command_sha256,
    }
    mismatches = [key for key, value in expected.items() if hello.get(key) != value]
    if mismatches:
        raise LaunchRefusal(
            "runner admission binding mismatch: " + ", ".join(mismatches), exit_code=7
        )


def _prepare_paths_and_config(args: argparse.Namespace) -> tuple[LaunchPaths, str, Mapping[str, Any], Path, list[str]]:
    if DIRECTION_RE.fullmatch(args.direction) is None:
        raise LaunchRefusal("--direction is invalid")
    source_root = _git_root(Path(args.source_root).expanduser().resolve(strict=True))
    common_dir = _git_common_dir(source_root)
    common_root = _common_worktree_root(common_dir)
    config_path = _locate_config(source_root, common_root)
    config = _load_config(config_path)
    node, entry = _node_config(config, args.node)
    configured_root = _configured_root(entry)
    control_root = _resolve_control_root(source_root, common_root, configured_root)
    runner, output, runner_arguments = _resolve_runner_and_output(
        source_root, args.direction, args.output, args.runner_argv
    )
    _validate_guard_contract(runner, args.direction)
    bootstrap = (source_root / "scripts" / "hmasd_admission.py").resolve(strict=True)
    bootstrap_tracked = _run_git(
        source_root,
        "ls-files",
        "--error-unmatch",
        bootstrap.relative_to(source_root).as_posix(),
        check=False,
    )
    if bootstrap_tracked.returncode != 0:
        raise LaunchRefusal("admission bootstrap is not tracked at the requested source")
    python_raw = entry.get("python")
    if not isinstance(python_raw, str) or not python_raw:
        raise LaunchRefusal(f"execution node {node!r} has no configured interpreter")
    python = Path(python_raw).expanduser().resolve(strict=True)
    if not python.is_file():
        raise LaunchRefusal(f"configured interpreter is not a file: {python}")
    return (
        LaunchPaths(
            source_root=source_root,
            control_root=control_root,
            config_path=config_path,
            output_root=output,
            runner=runner,
            bootstrap=bootstrap,
            git_common_dir=common_dir,
        ),
        node,
        entry,
        python,
        runner_arguments,
    )


def launch(args: argparse.Namespace) -> Mapping[str, Any]:
    sha = _require_full_sha(args.sha)
    if REMOTE_RE.fullmatch(args.remote) is None:
        raise LaunchRefusal("--remote must be a configured simple Git remote name")
    paths, node, _node_entry, python, runner_arguments = _prepare_paths_and_config(args)
    _require_policy(paths.control_root, args.direction, args.lead, args.remote)
    _validate_source(paths.source_root, sha, args.remote)

    command = [str(python), str(paths.runner), *runner_arguments]
    bootstrap_command = [
        str(python),
        str(paths.bootstrap),
        "_run-admitted",
        "--runner",
        str(paths.runner),
        "--output",
        str(paths.output_root),
        "--",
        *runner_arguments,
    ]
    identity_command = _command_identity(
        python, paths.runner, runner_arguments, paths.output_root, paths.source_root
    )
    command_sha256 = hmasd_admission.command_digest(python, paths.runner, runner_arguments)
    claim_key = _claim_key(args.direction, sha, identity_command)

    with _claim_lock(paths.git_common_dir) as state_root:
        # Re-read mutable launch facts after acquiring the global admission lock.
        _validate_source(paths.source_root, sha, args.remote)
        _state, authorized_control_digest = _require_policy(
            paths.control_root, args.direction, args.lead, args.remote
        )
        claim_path = state_root / f"{claim_key}.json"
        existing = _read_claim(claim_path)
        if existing is not None and existing.get("status") not in RETRYABLE_CLAIM_STATES:
            raise LaunchRefusal(
                f"duplicate or uncertain launch claim {claim_key}: {existing.get('status')}",
                exit_code=5,
            )
        if paths.output_root.exists():
            raise LaunchRefusal("output root already exists; choose a fresh run tag")
        paths.output_root.mkdir(parents=True, exist_ok=False)
        claim: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "claim_key": claim_key,
            "direction": args.direction,
            "sha": sha,
            "identity_command": identity_command,
            "command_sha256": command_sha256,
            "status": "reserved",
            "acceptance": "not_released",
            "created_at": _utc_now(),
            "output_root": str(paths.output_root),
        }
        _atomic_write_json(claim_path, claim)
        _write_status(paths.output_root, "reserved", claim_key=claim_key)

        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        process: subprocess.Popen[bytes] | None = None
        stdout_stream = None
        stderr_stream = None
        try:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
            listener.bind(("127.0.0.1", 0))
            listener.listen(2)
            listener.settimeout(args.admission_timeout_seconds)
            endpoint = listener.getsockname()
            nonce = secrets.token_hex(32)
            expires_at = time.time() + args.admission_timeout_seconds
            admission_spec = {
                "schema_version": SCHEMA_VERSION,
                "endpoint": ["127.0.0.1", endpoint[1]],
                "nonce": nonce,
                "expires_at": expires_at,
                "direction": args.direction,
                "python": str(python),
                "runner": str(paths.runner),
                "output_root": str(paths.output_root),
                "source_root": str(paths.source_root),
                "sha": sha,
                "command_sha256": command_sha256,
                "parent_pid": os.getpid(),
            }
            environment = dict(os.environ)
            environment[hmasd_admission.ENVIRONMENT_KEY] = json.dumps(
                admission_spec, sort_keys=True, separators=(",", ":")
            )
            stdout_stream = (paths.output_root / "stdout.log").open("ab", buffering=0)
            stderr_stream = (paths.output_root / "stderr.log").open("ab", buffering=0)
            try:
                process = _spawn(
                    bootstrap_command,
                    cwd=paths.source_root,
                    environment=environment,
                    stdout=stdout_stream,
                    stderr=stderr_stream,
                )
            except OSError as exc:
                claim.update(status="spawn_failed", acceptance="not_released", error=str(exc))
                _atomic_write_json(claim_path, claim)
                _write_status(paths.output_root, "spawn_failed", error=str(exc))
                raise LaunchRefusal(f"cannot start admitted runner: {exc}", exit_code=7) from exc

            manifest = _manifest(
                paths=paths,
                node=node,
                direction=args.direction,
                lead=args.lead,
                sha=sha,
                remote=args.remote,
                command=command,
                identity_command=identity_command,
                command_sha256=command_sha256,
                claim_key=claim_key,
                process=process,
                acceptance="waiting_for_runner",
            )
            manifest["bootstrap_command"] = bootstrap_command
            manifest["process_exit"] = str(paths.output_root / "process-exit.json")
            _atomic_write_json(paths.output_root / "launch-manifest.json", manifest)
            claim.update(
                pid=process.pid,
                process_identity=manifest["process"]["identity"],
                status="waiting_for_runner",
            )
            _atomic_write_json(claim_path, claim)
            _write_status(paths.output_root, "waiting_for_runner", pid=process.pid)

            try:
                supervisor_peer, _address = listener.accept()
            except socket.timeout as exc:
                claim.update(
                    status="child_acceptance_unknown",
                    acceptance="not_released",
                    child_returncode=process.poll(),
                )
                _atomic_write_json(claim_path, claim)
                _write_status(
                    paths.output_root,
                    "child_acceptance_unknown",
                    pid=process.pid,
                    child_returncode=process.poll(),
                )
                raise LaunchRefusal(
                    "supervisor did not identify itself before the deadline; claim is blocked",
                    exit_code=7,
                ) from exc

            with supervisor_peer:
                supervisor_peer.settimeout(args.admission_timeout_seconds)
                with supervisor_peer.makefile("rwb", buffering=0) as supervisor_stream:
                    supervisor_hello = _read_message(supervisor_stream)
                    supervisor_expected = {
                        "schema_version": SCHEMA_VERSION,
                        "kind": "supervisor",
                        "nonce": nonce,
                        "pid": process.pid,
                        "parent_pid": os.getpid(),
                    }
                    mismatches = [
                        key
                        for key, value in supervisor_expected.items()
                        if supervisor_hello.get(key) != value
                    ]
                    if mismatches:
                        raise LaunchRefusal(
                            "supervisor binding mismatch: " + ", ".join(mismatches),
                            exit_code=7,
                        )
                    if supervisor_hello.get("process_identity") != manifest["process"]["identity"]:
                        raise LaunchRefusal("supervisor native identity mismatch", exit_code=7)
                    _write_message(
                        supervisor_stream,
                        {"schema_version": SCHEMA_VERSION, "kind": "prepare_child", "nonce": nonce},
                    )
                    child_started = _read_message(supervisor_stream)
                    runner_pid = child_started.get("pid")
                    runner_identity = child_started.get("process_identity")
                    if (
                        child_started.get("schema_version") != SCHEMA_VERSION
                        or child_started.get("kind") != "child_started"
                        or child_started.get("nonce") != nonce
                        or child_started.get("supervisor_pid") != process.pid
                        or isinstance(runner_pid, bool)
                        or not isinstance(runner_pid, int)
                        or runner_pid <= 0
                        or not isinstance(runner_identity, Mapping)
                        or runner_identity.get("pid") != runner_pid
                    ):
                        raise LaunchRefusal("supervisor returned an invalid runner identity", exit_code=7)
                    manifest["runner_process"] = {
                        "pid": runner_pid,
                        "process_group_id": process.pid,
                        "identity": dict(runner_identity),
                        "supervisor_pid": process.pid,
                    }
                    claim.update(
                        runner_pid=runner_pid,
                        runner_process_identity=dict(runner_identity),
                    )
                    _atomic_write_json(paths.output_root / "launch-manifest.json", manifest)
                    _atomic_write_json(claim_path, claim)
                    _write_message(
                        supervisor_stream,
                        {"schema_version": SCHEMA_VERSION, "kind": "child_recorded", "nonce": nonce},
                    )

            try:
                runner_peer, _address = listener.accept()
            except socket.timeout as exc:
                claim.update(status="child_acceptance_unknown", acceptance="not_released")
                _atomic_write_json(claim_path, claim)
                _write_status(
                    paths.output_root,
                    "child_acceptance_unknown",
                    pid=process.pid,
                    runner_pid=runner_pid,
                )
                raise LaunchRefusal(
                    "runner did not request admission before the deadline; claim is blocked",
                    exit_code=7,
                ) from exc

            with runner_peer:
                runner_peer.settimeout(args.admission_timeout_seconds)
                with runner_peer.makefile("rwb", buffering=0) as stream:
                    hello = _read_message(stream)
                    _validate_hello(
                        hello,
                        nonce=nonce,
                        expected_pid=runner_pid,
                        parent_pid=process.pid,
                        direction=args.direction,
                        runner=paths.runner,
                        source_root=paths.source_root,
                        sha=sha,
                        command_sha256=command_sha256,
                    )

                    # No network operation follows this final local authority/input
                    # check.  The runner remains blocked until the fresh memory check.
                    _final_state, final_control_text = _require_local_policy(
                        paths.control_root, args.direction, args.lead
                    )
                    final_control_digest = hashlib.sha256(
                        final_control_text.encode("utf-8")
                    ).hexdigest()
                    if final_control_digest != authorized_control_digest:
                        claim.update(status="policy_changed", acceptance="not_released")
                        _atomic_write_json(claim_path, claim)
                        _write_message(
                            stream,
                            {
                                "schema_version": SCHEMA_VERSION,
                                "kind": "deny",
                                "nonce": nonce,
                                "reason": "canonical control state changed before release",
                            },
                        )
                        raise LaunchRefusal(
                            "canonical control state changed before release", exit_code=3
                        )
                    _validate_source_local(paths.source_root, sha)

                    # The runner is blocked in require_admission at this point.  Capture and
                    # assess the actual node immediately before its one release.
                    snapshot = hmasd_resource_preflight.capture_snapshot()
                    preflight = hmasd_resource_preflight.assess_memory_floor(snapshot)
                    receipt = {
                        **preflight,
                        "preflight_id": snapshot.get("preflight_id"),
                        "node": node,
                        "direction": args.direction,
                        "sha": sha,
                        "claim_key": claim_key,
                    }
                    _atomic_write_json(paths.output_root / "admission-preflight.json", receipt)
                    if not preflight.get("passed"):
                        _write_message(
                            stream,
                            {
                                "schema_version": SCHEMA_VERSION,
                                "kind": "deny",
                                "nonce": nonce,
                                "reason": "fresh actual-node memory preflight failed",
                            },
                        )
                        claim.update(status="preflight_refused", acceptance="not_released")
                        _atomic_write_json(claim_path, claim)
                        _write_status(
                            paths.output_root,
                            "preflight_refused",
                            pid=process.pid,
                            runner_pid=runner_pid,
                        )
                        raise LaunchRefusal("fresh actual-node memory preflight failed", exit_code=6)

                    # Persist uncertainty before the external effect.  A crash after this
                    # write cannot turn into an automatic or output-renamed retry.
                    claim.update(
                        status="release_unknown",
                        acceptance="unknown",
                        preflight_id=receipt.get("preflight_id"),
                    )
                    _atomic_write_json(claim_path, claim)
                    manifest["acceptance"] = "release_unknown"
                    _atomic_write_json(paths.output_root / "launch-manifest.json", manifest)
                    _write_status(
                        paths.output_root,
                        "release_unknown",
                        pid=process.pid,
                        runner_pid=runner_pid,
                    )

                    _write_message(
                        stream,
                        {
                            "schema_version": SCHEMA_VERSION,
                            "kind": "grant",
                            "nonce": nonce,
                            "pid": runner_pid,
                        },
                    )
                    accepted = _read_message(stream)
                    if (
                        accepted.get("kind") != "accepted"
                        or accepted.get("nonce") != nonce
                        or accepted.get("pid") != runner_pid
                    ):
                        raise LaunchRefusal(
                            "runner release occurred but acceptance acknowledgement is invalid; "
                            "claim remains unknown",
                            exit_code=7,
                        )

            claim.update(status="accepted", acceptance="accepted", accepted_at=_utc_now())
            _atomic_write_json(claim_path, claim)
            manifest["acceptance"] = "accepted"
            manifest["accepted_at"] = claim["accepted_at"]
            _atomic_write_json(paths.output_root / "launch-manifest.json", manifest)
            _write_status(
                paths.output_root, "accepted", pid=process.pid, runner_pid=runner_pid
            )
            return manifest
        except LaunchRefusal:
            raise
        except Exception as exc:
            if process is not None:
                claim.update(
                    status="child_acceptance_unknown",
                    acceptance="unknown",
                    pid=process.pid,
                    error=str(exc),
                )
                _atomic_write_json(claim_path, claim)
                _write_status(
                    paths.output_root,
                    "child_acceptance_unknown",
                    pid=process.pid,
                    error=str(exc),
                )
            raise LaunchRefusal(f"admission handshake failed: {exc}", exit_code=7) from exc
        finally:
            listener.close()
            if stdout_stream is not None:
                stdout_stream.close()
            if stderr_stream is not None:
                stderr_stream.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    launch_parser = modes.add_parser("launch", help="admit and detach one Python runner")
    launch_parser.add_argument("--direction", required=True)
    launch_parser.add_argument("--lead", required=True)
    launch_parser.add_argument("--sha", required=True)
    launch_parser.add_argument("--output", required=True)
    launch_parser.add_argument("--source-root", default=".")
    launch_parser.add_argument("--node")
    launch_parser.add_argument("--remote", default="origin")
    launch_parser.add_argument(
        "--admission-timeout-seconds",
        type=float,
        default=30.0,
        help=argparse.SUPPRESS,
    )
    launch_parser.add_argument("runner_argv", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.runner_argv and args.runner_argv[0] == "--":
        args.runner_argv.pop(0)
    if args.admission_timeout_seconds <= 0 or args.admission_timeout_seconds > 300:
        print("hmasd launch refused: admission timeout must be in (0, 300] seconds", file=sys.stderr)
        return 4
    try:
        manifest = launch(args)
    except LaunchRefusal as exc:
        print(f"hmasd launch refused: {exc}", file=sys.stderr)
        return exc.exit_code
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
