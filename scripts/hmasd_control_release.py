#!/usr/bin/env python3
"""Inspect or verify the published HMASD control-plane release."""
from __future__ import annotations

import argparse, datetime, hashlib, json, subprocess, sys
from pathlib import Path, PurePosixPath
from typing import Any

PROTOCOL_EPOCH = 2
EXACT_PATHS = {
    "AGENTS.md",
    ".codex/config.toml",
    "docs/project/WORKFLOW_GOALS_AND_ACCEPTANCE.md",
    "docs/project/WORKFLOW_PROTOCOL.md",
    "docs/project/git-path-policy-v1.json",
    *{f".codex/prompts/hmasd-{name}.md" for name in ("root", "workflow-clerk", "portfolio", "em", "cm")},
    *{f"scripts/{name}" for name in ("hmasd_session_envelope.py", "hmasd_control_release.py", "hmasd_state.py", "hmasd_dashboard.py")},
    *{f"scripts/{name}" for name in (
        "hmasd_direction_git.py", "hmasd_path_policy.py", "hmasd_operator_result.py",
        "hmasd_protocol_contracts.py", "hmasd_run.py",
    )},
    "tests/hmasd_session_envelope_test.py",
    "tests/hmasd_control_release_test.py",
    "tests/hmasd_dashboard_test.py",
    "tests/hmasd_portfolio_decision_v2_test.py",
    "tests/hmasd_code_review_scope_test.py",
    *{f"tests/{name}" for name in (
        "hmasd_direction_git_test.py", "hmasd_path_policy_test.py",
        "hmasd_operator_result_test.py", "hmasd_protocol_contracts_test.py",
        "hmasd_run_test.py",
    )},
}
SKILLS = {
    "hmasd-root-task", "hmasd-workflow-clerk-task", "hmasd-portfolio-task",
    "hmasd-em-task", "hmasd-cm-task", "hmasd-slice-interface",
    "hmasd-operations-manual", "code-review",
}

class ReleaseError(ValueError): pass

def _git(repo: Path, *args: str, allow_missing: bool = False) -> str | None:
    run = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    if run.returncode:
        if allow_missing: return None
        raise ReleaseError(f"git {' '.join(args)} failed: {run.stderr.strip()}")
    return run.stdout.strip()

def is_control_path(path: str) -> bool:
    path = path.replace("\\", "/")
    if path in EXACT_PATHS or path.startswith("scripts/dashboard/"): return True
    if path.startswith(".codex/agents/") and PurePosixPath(path).name.startswith("hmasd-") and path.endswith(".toml"): return True
    parts = PurePosixPath(path).parts
    if len(parts) >= 3 and parts[:2] == (".agents", "skills") and parts[2] in SKILLS: return True
    if path.startswith("scripts/schemas/"): return True
    return False

def _dirty_paths(repo: Path) -> list[str]:
    run = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        capture_output=True, text=True, check=False,
    )
    if run.returncode:
        raise ReleaseError(f"git status failed: {run.stderr.strip()}")
    raw = run.stdout
    entries = raw.split("\0"); result: list[str] = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        if not entry: break
        status, path = entry[:2], entry[3:].replace("\\", "/")
        result.append(path)
        if any(code in {"R", "C"} for code in status):
            index += 1
            if index < len(entries) and entries[index]:
                result.append(entries[index].replace("\\", "/"))
        index += 1
    return sorted(set(result))

def inspect_repo(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    top = _git(repo, "rev-parse", "--show-toplevel", allow_missing=True)
    exact_repo = bool(top and Path(top).resolve() == repo)
    branch = _git(repo, "branch", "--show-current", allow_missing=True) if exact_repo else None
    head = _git(repo, "rev-parse", "HEAD", allow_missing=True) if exact_repo else None
    origin = _git(repo, "rev-parse", "--verify", "origin/main", allow_missing=True) if exact_repo else None
    tracked = ((_git(repo, "ls-files", allow_missing=True) or "") if exact_repo else "").splitlines()
    control_paths = sorted(path.replace("\\", "/") for path in tracked if is_control_path(path))
    release_rows: list[str] = []
    for path in control_paths:
        blob = _git(repo, "rev-parse", f"HEAD:{path}", allow_missing=True)
        if blob: release_rows.append(f"{path}\0{blob}\n")
    release_id = hashlib.sha256("".join(release_rows).encode("utf-8")).hexdigest()
    dirty_control = sorted(path for path in (_dirty_paths(repo) if exact_repo else []) if is_control_path(path))
    return {
        "control_release_id": release_id,
        "protocol_epoch": PROTOCOL_EPOCH,
        "head": head,
        "origin_main": origin,
        "branch": branch,
        "control_paths": control_paths,
        "dirty_control_paths": dirty_control,
        "publishable": bool(branch == "main" and head and origin and head == origin and not dirty_control),
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect"); inspect.add_argument("--repo", required=True)
    verify = commands.add_parser("verify"); verify.add_argument("--repo", required=True); verify.add_argument("--expected-id", required=True)
    args = parser.parse_args(argv)
    try:
        record = inspect_repo(Path(args.repo))
        if args.command == "verify":
            if record["control_release_id"] != args.expected_id: raise ReleaseError("control_release_id does not match expected-id")
            if not record["publishable"]: raise ReleaseError("control release is not publishable")
    except ReleaseError as exc:
        print(str(exc), file=sys.stderr); return 2
    print(json.dumps(record, ensure_ascii=False, sort_keys=True)); return 0

if __name__ == "__main__": raise SystemExit(main())
