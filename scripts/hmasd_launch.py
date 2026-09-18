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
import platform
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
    from scripts import hmasd_source_snapshot
except ImportError:
    import hmasd_admission
    import hmasd_platform
    import hmasd_resource_preflight
    import hmasd_source_snapshot


SCHEMA_VERSION = 1
FULL_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
DIRECTION_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,63}\Z")
REMOTE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
RECOGNIZED_ACTIVE_STATES = {"exploring", "confirming"}
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


@dataclass(frozen=True)
class RequestProbe:
    source_root: Path
    git_common_dir: Path
    output_root: Path
    identity_command_tail: tuple[str, ...]


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

    active_matches = list(re.finditer(
        r"(?ms)^## Active\s*$\n(?P<body>.*?)(?=^##\s|\Z)", text
    ))
    if len(active_matches) != 1:
        raise LaunchRefusal("RESEARCH.md has no unambiguous Active section")
    active_match = active_matches[0]
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


def _control_source(control_root: Path) -> tuple[str, str]:
    config = _load_config(control_root / ".codex" / "hmasd-compute.toml")
    control = config.get("control_source", {})
    control_remote = control.get("remote")
    control_ref = control.get("ref")
    if (not isinstance(control_remote, str) or REMOTE_RE.fullmatch(control_remote) is None
            or not isinstance(control_ref, str) or not control_ref.startswith("refs/heads/")
            or _run_git(control_root, "check-ref-format", control_ref, check=False).returncode):
        raise LaunchRefusal("compute config must pin control_source.remote and refs/heads/ ref")
    return control_remote, control_ref


def _published_control_text(control_root: Path, remote: str, evidence: dict | None = None) -> str:
    control_remote, control_ref = _control_source(control_root)
    # Source publication remote is independent of the fixed control source.
    # Switching the canonical checkout's branch never selects another authority.
    advertised = _run_git(
        control_root,
        "ls-remote",
        "--heads",
        control_remote,
        control_ref,
        timeout=60.0,
    ).stdout.splitlines()
    if len(advertised) != 1:
        raise LaunchRefusal(
            f"cannot establish one published control head for {control_remote}/{control_ref}"
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
    if evidence is not None:
        evidence.update(remote=control_remote, ref=control_ref, sha=remote_sha,
                        observed_at=_utc_now())
    return published.stdout


def _policy_digest(state: DirectionState) -> str:
    return hashlib.sha256(json.dumps(
        {"pause": "lifted", "direction": state.direction, "state": state.state, "lead": state.lead},
        sort_keys=True,
    ).encode("utf-8")).hexdigest()


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
    control_root: Path, direction: str, lead: str, remote: str = "origin",
    evidence: dict | None = None,
) -> tuple[DirectionState, str]:
    state, text = _require_local_policy(control_root, direction, lead)
    published_text = _published_control_text(control_root, remote, evidence)
    published_pause, published_state = parse_research_state(published_text, direction)
    if published_pause != "lifted" or published_state != state:
        raise LaunchRefusal("fresh published control state does not authorize this direction and lead")
    return state, _policy_digest(state)


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
    _validate_publication(source_root, sha, remote)


def _validate_publication(source_root: Path, sha: str, remote: str) -> None:

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
    *, validate_runner: bool = True,
) -> tuple[Path, Path, list[str]]:
    if not runner_argv:
        raise LaunchRefusal("runner argv is required after --")
    runner_raw = runner_argv[0]
    runner = Path(runner_raw)
    if not runner.is_absolute():
        runner = source_root / runner
    runner = runner.resolve(strict=validate_runner)
    if runner.suffix.lower() != ".py" or (validate_runner and not runner.is_file()):
        raise LaunchRefusal("runner entry must be a Python script")
    try:
        runner.relative_to(source_root)
    except ValueError as exc:
        raise LaunchRefusal("runner entry is outside the source checkout") from exc
    if _has_alias_component(source_root, runner):
        raise LaunchRefusal("runner entry traverses a symlink or reparse point")
    if validate_runner:
        tracked = _run_git(
            source_root, "ls-files", "--error-unmatch",
            runner.relative_to(source_root).as_posix(), check=False,
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
            resolved = Path(os.path.abspath(candidate))
            if resolved == output:
                index += 1
                continue
            try:
                relative = resolved.relative_to(source_root)
            except ValueError:
                scrubbed.append(value)
            else:
                # Request recovery must not depend on whether an old input still
                # exists. Normalize declared/syntactic paths, never filesystem state.
                path_like = (
                    (index > 0 and arguments[index - 1] == "--generic-summary")
                    or option_prefix == "--generic-summary="
                    or Path(path_value).is_absolute()
                    or "/" in path_value or "\\" in path_value
                    or path_value.startswith(".")
                    or re.search(r"\.[A-Za-z][A-Za-z0-9_-]*$", path_value) is not None
                )
                scrubbed.append(
                    option_prefix + "<SOURCE>/" + relative.as_posix()
                    if path_like
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


def _read_json_object(path: Path, *, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LaunchRefusal(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, Mapping):
        raise LaunchRefusal(f"{label} is not a JSON object: {path}")
    return value


def _probe_launch_request(args: argparse.Namespace, sha: str) -> RequestProbe:
    """Resolve only the stable local request identity used for replay lookup.

    This deliberately does not read compute policy, inspect the runner body,
    fetch Git refs, or validate source cleanliness.  Those are new-effect
    gates and must not prevent recovery of an already recorded operation.
    """

    if DIRECTION_RE.fullmatch(args.direction) is None:
        raise LaunchRefusal("--direction is invalid")
    source_root = _git_root(Path(args.source_root).expanduser().resolve(strict=True))
    common_dir = _git_common_dir(source_root)
    output = Path(args.output)
    if not output.is_absolute():
        output = source_root / output
    output = output.resolve(strict=False)
    expected_parent = source_root / "runs" / args.direction
    try:
        relative = output.relative_to(expected_parent)
    except ValueError as exc:
        raise LaunchRefusal(
            f"output must be inside runs/{args.direction}/ in the source checkout"
        ) from exc
    if not relative.parts:
        raise LaunchRefusal("output must name a tag below the direction run root")
    if not args.runner_argv:
        raise LaunchRefusal("runner argv is required after --")
    runner = Path(args.runner_argv[0])
    if not runner.is_absolute():
        runner = source_root / runner
    runner = runner.resolve(strict=False)
    try:
        runner.relative_to(source_root)
    except ValueError as exc:
        raise LaunchRefusal("runner entry is outside the source checkout") from exc
    arguments = [str(value) for value in args.runner_argv[1:]]
    identity = _command_identity(
        Path(sys.executable).resolve(), runner, arguments, output, source_root
    )
    return RequestProbe(
        source_root=source_root,
        git_common_dir=common_dir,
        output_root=output,
        identity_command_tail=tuple(identity[1:]),
    )


def _claim_manifest(claim: Mapping[str, Any]) -> Mapping[str, Any] | None:
    raw = claim.get("manifest_ref")
    if isinstance(raw, str) and raw:
        path = Path(raw).expanduser().resolve(strict=False)
    else:
        output_raw = claim.get("output_root")
        if not isinstance(output_raw, str) or not output_raw:
            return None
        path = Path(output_raw).expanduser().resolve(strict=False) / "launch-manifest.json"
    if not path.is_file():
        return None
    return _read_json_object(path, label="launch manifest")


def _claim_request_mismatches(
    claim: Mapping[str, Any], args: argparse.Namespace, sha: str, probe: RequestProbe
) -> list[str]:
    manifest = _claim_manifest(claim)

    def recorded(key: str) -> Any:
        value = claim.get(key)
        if value is None and manifest is not None:
            value = manifest.get(key)
        return value

    mismatches: list[str] = []
    if recorded("direction") != args.direction:
        mismatches.append("direction")
    if recorded("sha") != sha:
        mismatches.append("sha")
    identity = recorded("identity_command")
    if (
        not isinstance(identity, Sequence)
        or isinstance(identity, (str, bytes))
        or tuple(str(value) for value in identity[1:]) != probe.identity_command_tail
    ):
        mismatches.append("runner_argv")
    for key, requested in (
        ("lead", args.lead),
        ("node", args.node),
        ("published_remote", args.remote),
    ):
        value = recorded(key)
        if value is not None and requested is not None and value != requested:
            mismatches.append(key)
    return mismatches


def _find_existing_operation(
    state_root: Path, args: argparse.Namespace, sha: str, probe: RequestProbe
) -> tuple[Path, Mapping[str, Any]] | None:
    exact: list[tuple[Path, Mapping[str, Any]]] = []
    output_conflict: tuple[Path, Mapping[str, Any], list[str]] | None = None
    if not state_root.is_dir():
        return None
    for claim_path in sorted(state_root.glob("*.json")):
        claim = _read_claim(claim_path)
        if claim is None:
            continue
        output_raw = claim.get("output_root")
        same_output = (
            isinstance(output_raw, str)
            and _normalized_path(output_raw) == _normalized_path(probe.output_root)
        )
        mismatches = _claim_request_mismatches(claim, args, sha, probe)
        if same_output and mismatches:
            output_conflict = (claim_path, claim, mismatches)
        if not mismatches:
            exact.append((claim_path, claim))
    if output_conflict is not None:
        claim_path, _claim, mismatches = output_conflict
        raise LaunchRefusal(
            "existing operation input mismatch for this output tag: "
            + ", ".join(mismatches)
            + f"; inspect {claim_path}",
            exit_code=5,
        )
    if len(exact) > 1:
        references = ", ".join(str(path) for path, _claim in exact)
        raise LaunchRefusal(
            f"multiple existing operations match this request: {references}", exit_code=5
        )
    return exact[0] if exact else None


def _write_status(output: Path, status: str, **extra: Any) -> None:
    payload = {"schema_version": SCHEMA_VERSION, "status": status, "updated_at": _utc_now()}
    existing_path = output / "launch-status.json"
    if existing_path.is_file():
        try:
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = None
        if isinstance(existing, Mapping):
            for key in ("claim_key", "operation_ref", "claim_ref", "manifest_ref"):
                if key in existing:
                    payload[key] = existing[key]
    payload.update(extra)
    _atomic_write_json(existing_path, payload)


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


def _observe_native_identity(recorded: Any) -> Mapping[str, Any]:
    """Observe a recorded process without turning disappearance into exit proof."""

    if not isinstance(recorded, Mapping):
        return {"state": "unrecorded"}
    pid = recorded.get("pid")
    kind = recorded.get("kind")
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return {"state": "unrecorded", "recorded_identity": dict(recorded)}

    if os.name == "nt":
        if kind != "windows_pid_creation_time":
            return {
                "state": "unavailable",
                "reason": "recorded identity belongs to another platform",
                "recorded_identity": dict(recorded),
            }
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        ]
        kernel32.GetProcessTimes.restype = wintypes.BOOL
        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            error = ctypes.get_last_error()
            if error == 87:  # ERROR_INVALID_PARAMETER: no such process.
                return {"state": "absent", "recorded_identity": dict(recorded)}
            return {
                "state": "unknown",
                "reason": f"OpenProcess failed with Windows error {error}",
                "recorded_identity": dict(recorded),
            }
        try:
            created = wintypes.FILETIME()
            exited = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            if not kernel32.GetProcessTimes(
                handle,
                ctypes.byref(created),
                ctypes.byref(exited),
                ctypes.byref(kernel),
                ctypes.byref(user),
            ):
                return {
                    "state": "unknown",
                    "reason": "GetProcessTimes failed",
                    "recorded_identity": dict(recorded),
                }
            observed = {
                "kind": "windows_pid_creation_time",
                "pid": pid,
                "creation_time_100ns": (
                    (int(created.dwHighDateTime) << 32) | int(created.dwLowDateTime)
                ),
            }
            if observed != dict(recorded):
                return {
                    "state": "identity_mismatch",
                    "recorded_identity": dict(recorded),
                    "observed_identity": observed,
                }
            exit_code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return {
                    "state": "unknown",
                    "reason": "GetExitCodeProcess failed",
                    "recorded_identity": dict(recorded),
                    "observed_identity": observed,
                }
            state = "running" if int(exit_code.value) == 259 else "not_running"
            return {
                "state": state,
                "recorded_identity": dict(recorded),
                "observed_identity": observed,
            }
        finally:
            kernel32.CloseHandle(handle)

    if kind != "linux_pid_start_ticks":
        return {
            "state": "unavailable",
            "reason": "recorded identity belongs to another platform",
            "recorded_identity": dict(recorded),
        }
    try:
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
        stat_line = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"state": "absent", "recorded_identity": dict(recorded)}
    except OSError as exc:
        return {
            "state": "unknown",
            "reason": str(exc),
            "recorded_identity": dict(recorded),
        }
    closing = stat_line.rfind(")")
    fields = stat_line[closing + 2 :].split() if closing >= 0 else []
    if len(fields) <= 19:
        return {
            "state": "unknown",
            "reason": "invalid /proc stat record",
            "recorded_identity": dict(recorded),
        }
    try:
        start_ticks = int(fields[19])
        session_id = os.getsid(pid)
    except (OSError, ValueError) as exc:
        return {
            "state": "unknown",
            "reason": str(exc),
            "recorded_identity": dict(recorded),
        }
    observed = {
        "kind": "linux_pid_start_ticks",
        "pid": pid,
        "boot_id": boot_id,
        "start_ticks": start_ticks,
        "session_id": session_id,
    }
    if observed != dict(recorded):
        return {
            "state": "identity_mismatch",
            "recorded_identity": dict(recorded),
            "observed_identity": observed,
        }
    state = "not_running" if fields[0] in {"Z", "X"} else "running"
    return {
        "state": state,
        "recorded_identity": dict(recorded),
        "observed_identity": observed,
    }


def _load_optional_json(path: Path, *, label: str) -> tuple[str, Mapping[str, Any] | None, str | None]:
    if not path.exists():
        return "absent", None, None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return "invalid", None, str(exc)
    if not isinstance(value, Mapping):
        return "invalid", None, "JSON value is not an object"
    return "present", value, None


def _resolve_status_records(
    reference: str | os.PathLike[str],
) -> tuple[Path | None, Mapping[str, Any] | None, Path | None, Mapping[str, Any] | None, Path]:
    path = Path(reference).expanduser().resolve(strict=False)
    output = path if path.is_dir() else path.parent
    manifest_path: Path | None = None
    claim_path: Path | None = None
    manifest: Mapping[str, Any] | None = None
    claim: Mapping[str, Any] | None = None

    if path.is_dir():
        candidate = path / "launch-manifest.json"
        if candidate.is_file():
            manifest_path = candidate
            manifest = _read_json_object(candidate, label="launch manifest")
        else:
            status_path = path / "launch-status.json"
            if not status_path.is_file():
                raise LaunchRefusal(
                    f"status reference has no launch manifest or launch status: {path}"
                )
            launch_status = _read_json_object(status_path, label="launch status")
            raw_claim = launch_status.get("operation_ref") or launch_status.get("claim_ref")
            if not isinstance(raw_claim, str) or not raw_claim:
                raise LaunchRefusal(
                    "launch status predates stable operation references; use its claim path"
                )
            claim_path = Path(raw_claim).expanduser().resolve(strict=False)
            claim = _read_json_object(claim_path, label="operation claim")
    else:
        if not path.is_file():
            raise LaunchRefusal(f"status reference does not exist: {path}")
        record = _read_json_object(path, label="status reference")
        if path.name == "launch-manifest.json" or "process" in record:
            manifest_path, manifest = path, record
            output_raw = record.get("output_root")
            if isinstance(output_raw, str) and output_raw:
                output = Path(output_raw).expanduser().resolve(strict=False)
        elif "claim_key" in record and "output_root" in record:
            claim_path, claim = path, record
            output_raw = record.get("output_root")
            assert isinstance(output_raw, str)
            output = Path(output_raw).expanduser().resolve(strict=False)
        else:
            raise LaunchRefusal(
                "status reference is neither a launch manifest nor an operation claim"
            )

    if manifest is not None:
        raw_claim = manifest.get("operation_ref") or manifest.get("claim_ref")
        if isinstance(raw_claim, str) and raw_claim:
            candidate = Path(raw_claim).expanduser().resolve(strict=False)
            if candidate.is_file():
                claim_path = candidate
                claim = _read_json_object(candidate, label="operation claim")
    if claim is not None and manifest is None:
        raw_manifest = claim.get("manifest_ref")
        candidate = (
            Path(raw_manifest).expanduser().resolve(strict=False)
            if isinstance(raw_manifest, str) and raw_manifest
            else output / "launch-manifest.json"
        )
        if candidate.is_file():
            manifest_path = candidate
            manifest = _read_json_object(candidate, label="launch manifest")
    return manifest_path, manifest, claim_path, claim, output


def status(reference: str | os.PathLike[str]) -> Mapping[str, Any]:
    """Return read-only operation facts without consulting launch authority."""

    manifest_path, manifest, claim_path, claim, output = _resolve_status_records(reference)
    record_conflicts: list[str] = []
    if manifest is not None and claim is not None:
        for key in (
            "claim_key",
            "direction",
            "sha",
            "node",
            "output_root",
            "identity_command",
            "command_sha256",
        ):
            manifest_value = manifest.get(key)
            claim_value = claim.get(key)
            if (
                manifest_value is not None
                and claim_value is not None
                and manifest_value != claim_value
            ):
                record_conflicts.append(key)

    process = manifest.get("process") if isinstance(manifest, Mapping) else None
    runner_process = manifest.get("runner_process") if isinstance(manifest, Mapping) else None
    supervisor_identity = process.get("identity") if isinstance(process, Mapping) else None
    runner_identity = (
        runner_process.get("identity") if isinstance(runner_process, Mapping) else None
    )
    recorded_host = manifest.get("host_identity") if isinstance(manifest, Mapping) else None
    current_host = platform.node()
    if not isinstance(recorded_host, str) or not recorded_host:
        supervisor = runner = {
            "state": "unavailable",
            "reason": "manifest has no native-observation host binding",
        }
    elif recorded_host != current_host:
        supervisor = runner = {
            "state": "unavailable",
            "reason": "operation belongs to a different host",
            "recorded_host_identity": recorded_host,
            "observer_host_identity": current_host,
        }
    else:
        supervisor = _observe_native_identity(supervisor_identity)
        runner = _observe_native_identity(runner_identity)

    exit_path_raw = manifest.get("process_exit") if isinstance(manifest, Mapping) else None
    exit_path = (
        Path(exit_path_raw).expanduser().resolve(strict=False)
        if isinstance(exit_path_raw, str) and exit_path_raw
        else output / "process-exit.json"
    )
    witness_state, witness, witness_error = _load_optional_json(
        exit_path, label="process exit witness"
    )
    exit_witness: dict[str, Any] = {"state": witness_state, "path": str(exit_path)}
    if witness_error is not None:
        exit_witness["reason"] = witness_error
    valid_exit = False
    if witness is not None:
        mismatches: list[str] = []
        if witness.get("status") != "exited":
            mismatches.append("status")
        if runner_identity is None or witness.get("process_identity") != runner_identity:
            mismatches.append("runner_identity")
        if supervisor_identity is None or witness.get("supervisor_identity") != supervisor_identity:
            mismatches.append("supervisor_identity")
        exit_code = witness.get("exit_code")
        if isinstance(exit_code, bool) or not isinstance(exit_code, int):
            mismatches.append("exit_code")
        if mismatches:
            exit_witness.update(state="invalid", mismatches=mismatches)
        else:
            valid_exit = True
            exit_witness.update(
                state="valid",
                exit_code=exit_code,
                termination=witness.get("termination"),
                finished_at_epoch=witness.get("finished_at_epoch"),
            )

    live_exit_conflict = valid_exit and runner.get("state") == "running"
    if record_conflicts or live_exit_conflict:
        execution_state = "unknown"
    elif valid_exit:
        execution_state = "exited"
    elif runner.get("state") == "running":
        execution_state = "running"
    elif runner_identity is not None:
        execution_state = "unknown"
    elif claim is not None and claim.get("status") == "spawn_failed":
        execution_state = "not_started"
    else:
        execution_state = "unknown"

    source = manifest if manifest is not None else claim if claim is not None else {}
    claim_state = claim.get("status") if isinstance(claim, Mapping) else None
    admission_state = (
        claim.get("acceptance") if isinstance(claim, Mapping) else source.get("acceptance")
    )
    if record_conflicts:
        admission_state = "unknown"
    artifacts: dict[str, Any] = {}
    for name, candidate in (
        ("summary", output / "summary.json"),
        ("stdout", output / "stdout.log"),
        ("stderr", output / "stderr.log"),
    ):
        artifacts[name] = {
            "state": "present" if candidate.is_file() else "absent",
            "path": str(candidate),
        }
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "kind": "hmasd_operation_status",
        "observed_at": _utc_now(),
        "operation_ref": str(claim_path) if claim_path is not None else str(manifest_path),
        "manifest_ref": str(manifest_path) if manifest_path is not None else None,
        "claim_ref": str(claim_path) if claim_path is not None else None,
        "node": source.get("node"),
        "direction": source.get("direction"),
        "sha": source.get("sha"),
        "source_root": source.get("source_root"),
        "output_root": str(output),
        "admission": {"state": admission_state, "claim_state": claim_state},
        "execution": {
            "state": execution_state,
            "supervisor": supervisor,
            "runner": runner,
            "exit_witness": exit_witness,
        },
        "artifacts": artifacts,
        "record_consistency": {
            "state": "conflict" if record_conflicts else "consistent",
            "mismatches": record_conflicts,
        },
        "explicit_retry_available": False,
    }
    if live_exit_conflict:
        result["execution"]["conflict"] = "matching runner identity is live with exit witness"
    if valid_exit and not record_conflicts and not live_exit_conflict:
        result["execution"]["exit_code"] = exit_witness["exit_code"]
    return result


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
        "host_identity": platform.node(),
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
    author_root = source_root
    argv = list(args.runner_argv)
    output_raw = args.output
    if getattr(args, "snapshot", False):
        # Validate live authority and publication before preparing any snapshot.
        _require_policy(control_root, args.direction, args.lead, args.remote)
        _validate_publication(source_root, args.sha, args.remote)
        probe = _probe_launch_request(args, args.sha)
        _resolve_runner_and_output(author_root, args.direction, args.output, args.runner_argv,
                                   validate_runner=False)
        original_runner = Path(argv[0])
        if not original_runner.is_absolute():
            original_runner = author_root / original_runner
        runner_relative = original_runner.resolve(strict=False).relative_to(author_root)
        source_root = hmasd_source_snapshot.prepare(author_root, common_dir, args.sha, _run_git)
        argv[0] = str(source_root / runner_relative)
        output_raw = str(source_root / probe.output_root.relative_to(author_root))
        # Output stays in the original run root, not hidden in the source worktree.
        # The one current consumer's external input remains caller-relative and
        # must carry its expected digest; all other relative inputs refer to SHA.
        for index in range(1, len(argv)):
            value = argv[index]
            if argv[index - 1] in OUTPUT_ARGUMENTS:
                argv[index] = output_raw
            elif any(value.startswith(flag + "=") for flag in OUTPUT_ARGUMENTS):
                argv[index] = value.split("=", 1)[0] + "=" + output_raw
            elif argv[index - 1] == "--generic-summary":
                argv[index] = str((author_root / value).resolve())
            elif value.startswith("--generic-summary="):
                argv[index] = "--generic-summary=" + str((author_root / value.split("=", 1)[1]).resolve())
            else:
                prefix, candidate = (value.split("=", 1) if value.startswith("--") and "=" in value
                                     else ("", value))
                candidate_path = Path(candidate)
                if candidate_path.is_absolute() and candidate_path.is_relative_to(author_root):
                    bound = source_root / candidate_path.relative_to(author_root)
                    if not bound.exists():
                        raise LaunchRefusal(f"absolute author input is absent from published snapshot: {candidate}")
                    argv[index] = (prefix + "=" if prefix else "") + str(bound)
    runner, output, runner_arguments = _resolve_runner_and_output(
        source_root, args.direction, output_raw, argv
    )
    if getattr(args, "snapshot", False):
        snapshot_output = str(output)
        output = probe.output_root
        if _has_alias_component(author_root, output):
            raise LaunchRefusal("output path traverses a symlink or reparse point")
        runner_arguments = [
            str(output) if value == snapshot_output else
            value.split("=", 1)[0] + "=" + str(output)
            if any(value == flag + "=" + snapshot_output for flag in OUTPUT_ARGUMENTS) else value
            for value in runner_arguments
        ]
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
    probe = _probe_launch_request(args, sha)
    with _claim_lock(probe.git_common_dir) as state_root:
        existing = _find_existing_operation(state_root, args, sha, probe)
        if existing is not None:
            claim_path, _claim = existing
            recovered = dict(status(claim_path))
            recovered["request_resolution"] = "existing_operation"
            return recovered

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
    identity_command = [_normalized_path(python), *probe.identity_command_tail]
    command_sha256 = hmasd_admission.command_digest(python, paths.runner, runner_arguments)
    claim_key = _claim_key(args.direction, sha, identity_command)

    with _claim_lock(paths.git_common_dir) as state_root:
        claim_path = state_root / f"{claim_key}.json"
        existing = _read_claim(claim_path)
        if existing is not None:
            mismatches = _claim_request_mismatches(existing, args, sha, probe)
            if mismatches:
                raise LaunchRefusal(
                    "existing operation input mismatch: " + ", ".join(mismatches),
                    exit_code=5,
                )
            recovered = dict(status(claim_path))
            recovered["request_resolution"] = "existing_operation"
            return recovered
        # Re-read mutable launch facts after acquiring the global admission lock.
        _validate_source(paths.source_root, sha, args.remote)
        control_evidence: dict[str, Any] = {}
        _state, authorized_control_digest = _require_policy(
            paths.control_root, args.direction, args.lead, args.remote, control_evidence
        )
        if paths.output_root.exists():
            raise LaunchRefusal("output root already exists without a matching operation; inspect and preserve its evidence")
        paths.output_root.mkdir(parents=True, exist_ok=False)
        manifest_path = paths.output_root / "launch-manifest.json"
        claim: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "claim_key": claim_key,
            "direction": args.direction,
            "lead": args.lead,
            "node": node,
            "host_identity": platform.node(),
            "sha": sha,
            "published_remote": args.remote,
            "source_root": str(paths.source_root),
            "identity_command": identity_command,
            "command_sha256": command_sha256,
            "status": "reserved",
            "acceptance": "not_released",
            "created_at": _utc_now(),
            "output_root": str(paths.output_root),
            "operation_ref": str(claim_path),
            "claim_ref": str(claim_path),
            "manifest_ref": str(manifest_path),
        }
        _atomic_write_json(claim_path, claim)
        _write_status(
            paths.output_root,
            "reserved",
            claim_key=claim_key,
            operation_ref=str(claim_path),
            claim_ref=str(claim_path),
            manifest_ref=str(manifest_path),
        )

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
            environment = hmasd_source_snapshot.environment() if getattr(args, "snapshot", False) else dict(os.environ)
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
            manifest["control_observation"] = control_evidence
            manifest["process_exit"] = str(paths.output_root / "process-exit.json")
            manifest["operation_ref"] = str(claim_path)
            manifest["claim_ref"] = str(claim_path)
            manifest["manifest_ref"] = str(manifest_path)
            _atomic_write_json(manifest_path, manifest)
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
                    _atomic_write_json(manifest_path, manifest)
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
                    final_control_digest = _policy_digest(_final_state)
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
                    _atomic_write_json(manifest_path, manifest)
                    _write_status(
                        paths.output_root,
                        "release_unknown",
                        pid=process.pid,
                        runner_pid=runner_pid,
                    )

                    # Re-read after source/memory checks and persistence, directly
                    # before grant. No remote instantaneous revocation is claimed.
                    latest_state, _ = _require_local_policy(paths.control_root, args.direction, args.lead)
                    if (_policy_digest(latest_state) != authorized_control_digest
                            or _control_source(paths.control_root) !=
                            (control_evidence["remote"], control_evidence["ref"])):
                        raise LaunchRefusal("control authority changed before final grant", exit_code=3)
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
            _atomic_write_json(manifest_path, manifest)
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
    launch_parser.add_argument("--snapshot", action="store_true",
                               help="execute published SHA in a retained linked worktree")
    launch_parser.add_argument("--node")
    launch_parser.add_argument("--remote", default="origin")
    launch_parser.add_argument(
        "--admission-timeout-seconds",
        type=float,
        default=30.0,
        help=argparse.SUPPRESS,
    )
    launch_parser.add_argument("runner_argv", nargs=argparse.REMAINDER)
    status_parser = modes.add_parser(
        "status", help="observe an existing manifest, operation claim, or output directory"
    )
    status_parser.add_argument("reference")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.mode == "status":
            result = status(args.reference)
        else:
            if args.runner_argv and args.runner_argv[0] == "--":
                args.runner_argv.pop(0)
            if args.admission_timeout_seconds <= 0 or args.admission_timeout_seconds > 300:
                raise LaunchRefusal(
                    "admission timeout must be in (0, 300] seconds"
                )
            result = launch(args)
    except LaunchRefusal as exc:
        print(f"hmasd launch refused: {exc}", file=sys.stderr)
        return exc.exit_code
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
