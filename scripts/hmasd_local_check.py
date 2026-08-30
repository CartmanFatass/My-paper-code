"""Read-only, focused validation for local HMASD changes."""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import shutil
import sys
from typing import Generator, NoReturn, Sequence

try:
    from scripts import hmasd_state
except ImportError:  # Direct ``python scripts/hmasd_local_check.py`` execution.
    import hmasd_state  # type: ignore[no-redef]


CORE_STATES = {
    "docs/research/portfolio/workflow/registry.json": "portfolio_registry",
    ".omp/runtime/agents.json": "runtime_agents",
    ".omp/runtime/worktrees.json": "runtime_worktrees",
}
KNOWN_STATE_PATHS = {
    **CORE_STATES,
    ".omp/runtime/browser_assignments.json": "runtime_browser_assignments",
}
FOCUSED_TESTS = {
    "scripts/hmasd_clerk.py": "tests/hmasd_clerk_test.py",
    "scripts/hmasd_dashboard.py": "tests/hmasd_dashboard_test.py",
    "scripts/hmasd_external_review.py": "tests/hmasd_external_review_test.py",
    "scripts/hmasd_file_fingerprint.py": "tests/hmasd_file_fingerprint_test.py",
    "scripts/hmasd_local_check.py": "tests/hmasd_local_check_test.py",
    "scripts/hmasd_operator_result.py": "tests/hmasd_operator_result_test.py",
    "scripts/hmasd_resource_preflight.py": "tests/hmasd_resource_preflight_test.py",
    "scripts/hmasd_run.py": "tests/hmasd_run_test.py",
    "scripts/hmasd_science_capabilities.py": "tests/hmasd_science_capabilities_test.py",
    "scripts/hmasd_state.py": "tests/hmasd_state_phase0_test.py",
    "scripts/hmasd_worktree.py": "tests/hmasd_worktree_test.py",
}


class InputError(ValueError):
    """A command-line value cannot identify a repository check target."""


def _run_command(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    process_env = None
    if env is not None:
        process_env = os.environ.copy()
        process_env.update(env)
    return subprocess.run(
        list(argv),
        cwd=cwd,
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=process_env,
    )


def _output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run_command(["git", "-C", os.fspath(repo), *args], cwd=repo)


def _repository(path: str) -> Path:
    candidate = Path(path).expanduser().resolve()
    if not candidate.is_dir():
        raise InputError(f"repo: not a directory: {path}")
    result = _git(candidate, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        raise InputError("repo: not a Git repository")
    return Path(result.stdout.strip()).resolve()


def _base(repo: Path, value: str) -> str:
    result = _git(repo, "rev-parse", "--verify", "--quiet", f"{value}^{{commit}}")
    if result.returncode != 0:
        raise InputError(f"base: unknown commit: {value}")
    return result.stdout.strip()


def _scope(repo: Path, value: str) -> str:
    candidate = (repo / value).resolve(strict=False) if not Path(value).is_absolute() else Path(value).resolve(strict=False)
    try:
        relative = candidate.relative_to(repo)
    except ValueError as exc:
        raise InputError(f"scope: outside repository: {value}") from exc
    return relative.as_posix() or "."


def _in_scopes(path: str, scopes: Sequence[str]) -> bool:
    if not scopes or "." in scopes:
        return True
    return any(path == scope or path.startswith(f"{scope}/") for scope in scopes)


def _nul_paths(result: subprocess.CompletedProcess[str], label: str) -> set[str]:
    if result.returncode != 0:
        raise InputError(f"{label}: Git command failed")
    return {path for path in result.stdout.split("\0") if path}


def changed_paths(repo: Path, base: str, scopes: Sequence[str]) -> list[str]:
    pathspec = ["--", *scopes] if scopes else ["--"]
    tracked = _nul_paths(_git(repo, "diff", "--no-ext-diff", "--name-only", "-z", base, *pathspec), "diff")
    untracked = _nul_paths(
        _git(repo, "ls-files", "--others", "--exclude-standard", "-z", *pathspec), "untracked"
    )
    return sorted(path for path in tracked | untracked if _in_scopes(path, scopes))


def state_kind(path: str) -> str | None:
    if path in KNOWN_STATE_PATHS:
        return KNOWN_STATE_PATHS[path]
    parts = PurePosixPath(path).parts
    if len(parts) == 7 and parts[:3] == ("docs", "research", "candidates"):
        if parts[4:] == ("workflow", "research", "state.json"):
            return "research_state"
        if parts[4:] == ("workflow", "engineering", "state.json"):
            return "engineering_state"
    if len(parts) == 7 and parts[:3] == ("docs", "research", "candidates"):
        if parts[4:] == ("workflow", "external-review", "index.json"):
            return "external_review_index"
    if len(parts) == 6 and parts[:3] == ("docs", "research", "candidates"):
        if parts[4] == "results" and path.endswith(".json"):
            return "accepted_result"
    if len(parts) == 6 and parts[:2] == ("temp", "directions") and parts[-1] == "manifest.json":
        return "run_manifest"
    return None


@contextlib.contextmanager
def _state_repository(repo: Path) -> Generator[None, None, None]:
    original_root = hmasd_state.ROOT
    hmasd_state.ROOT = repo
    try:
        yield
    finally:
        hmasd_state.ROOT = original_root


def _check(name: str, status: str, output: str = "") -> dict[str, str]:
    return {"name": name, "status": status, "output": output}


def _state_paths(paths: Sequence[str], scopes: Sequence[str]) -> list[tuple[str, str, bool]]:
    targets: set[tuple[str, str, bool]] = set()
    for path in paths:
        kind = state_kind(path)
        if kind is not None:
            targets.add((path, kind, path in CORE_STATES))
    for path, kind in CORE_STATES.items():
        if _in_scopes(path, scopes):
            targets.add((path, kind, True))
    return sorted(targets)


def _validate_states(
    repo: Path, paths: Sequence[str], scopes: Sequence[str], checks: list[dict[str, str]], failures: list[str]
) -> None:
    with _state_repository(repo):
        for path, kind, core in _state_paths(paths, scopes):
            target = repo / path
            name = f"state:{path}"
            if not target.is_file():
                if core and path not in paths:
                    checks.append(_check(name, "SKIPPED", "missing"))
                else:
                    checks.append(_check(name, "FAIL", "missing"))
                    failures.append(f"{path}: state file is missing")
                continue
            try:
                hmasd_state.read_state(kind, target)
            except (OSError, hmasd_state.StateError) as exc:
                message = str(exc).splitlines()[0]
                checks.append(_check(name, "FAIL", message))
                failures.append(f"{path}: {message}")
            else:
                checks.append(_check(name, "PASS"))


def _compile_python(repo: Path, paths: Sequence[str], checks: list[dict[str, str]], failures: list[str]) -> None:
    for path in paths:
        if not path.endswith(".py"):
            continue
        target = repo / path
        if not target.is_file():
            checks.append(_check(f"compile:{path}", "SKIPPED", "missing"))
            continue
        try:
            compile(target.read_bytes(), path, "exec", dont_inherit=True)
        except (OSError, SyntaxError, UnicodeError) as exc:
            message = str(exc).splitlines()[0]
            checks.append(_check(f"compile:{path}", "FAIL", message))
            failures.append(f"{path}: {message}")
        else:
            checks.append(_check(f"compile:{path}", "PASS"))


def selected_tests(repo: Path, paths: Sequence[str]) -> list[str]:
    return sorted(
        {test for path, test in FOCUSED_TESTS.items() if path in paths and (repo / test).is_file()}
    )


def _pytest_argv(tests: Sequence[str]) -> list[str]:
    if importlib.util.find_spec("pytest") is not None:
        return [sys.executable, "-m", "pytest", "-q", *tests]
    uv = shutil.which("uv")
    if uv is not None:
        return [
            uv,
            "run",
            "--with",
            "pytest",
            "--with",
            "jsonschema",
            "pytest",
            "-q",
            *tests,
        ]
    raise InputError("focused tests: neither pytest nor uv is available")


def _run_tests(
    repo: Path, tests: Sequence[str], no_tests: bool, checks: list[dict[str, str]], failures: list[str]
) -> None:
    if no_tests:
        checks.append(_check("focused_tests", "SKIPPED", "disabled"))
        return
    if not tests:
        checks.append(_check("focused_tests", "SKIPPED", "none selected"))
        return
    try:
        argv = _pytest_argv(tests)
    except InputError as exc:
        checks.append(_check("focused_tests", "FAIL", str(exc)))
        failures.append(str(exc))
        return
    python_path = os.fspath(repo)
    if os.environ.get("PYTHONPATH"):
        python_path += os.pathsep + os.environ["PYTHONPATH"]
    result = _run_command(argv, cwd=repo, env={"PYTHONPATH": python_path})
    output = _output(result)
    if result.returncode == 0:
        checks.append(_check("focused_tests", "PASS", output))
    else:
        checks.append(_check("focused_tests", "FAIL", output))
        failures.append(f"focused tests: pytest exited {result.returncode}")


def _diff_check(repo: Path, base: str, scopes: Sequence[str], checks: list[dict[str, str]], failures: list[str]) -> None:
    pathspec = ["--", *scopes] if scopes else ["--"]
    result = _git(repo, "diff", "--no-ext-diff", "--check", base, *pathspec)
    output = _output(result)
    if result.returncode == 0:
        checks.append(_check("git_diff_check", "PASS", output))
    else:
        checks.append(_check("git_diff_check", "FAIL", output))
        first_line = next((line for line in output.splitlines() if line), "git diff --check failed")
        failures.append(first_line)


def _emit(status: str, paths: Sequence[str], checks: Sequence[dict[str, str]], tests: Sequence[str], failures: Sequence[str]) -> None:
    print(
        json.dumps(
            {
                "changed_paths": list(paths),
                "checks": list(checks),
                "failures": list(failures),
                "selected_tests": list(tests),
                "status": status,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise InputError(f"arguments: {message}")


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(add_help=False)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--no-tests", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        repo = _repository(args.repo)
        base = _base(repo, args.base)
        scopes = sorted(set(_scope(repo, value) for value in args.scope))
        paths = changed_paths(repo, base, scopes)
    except InputError as exc:
        _emit("INVALID_INPUT", [], [], [], [str(exc)])
        return 2

    checks: list[dict[str, str]] = []
    failures: list[str] = []
    _diff_check(repo, base, scopes, checks, failures)
    _validate_states(repo, paths, scopes, checks, failures)
    _compile_python(repo, paths, checks, failures)
    tests = selected_tests(repo, paths)
    _run_tests(repo, tests, args.no_tests, checks, failures)
    _emit("PASS" if not failures else "FAIL", paths, checks, tests, failures)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
