"""Preview or remove one exact empty directory tree in a temp assignment."""

from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn


class Refusal(RuntimeError):
    """A bounded, non-mutating refusal."""


@dataclass(frozen=True)
class Inspection:
    status: str
    target: Path
    directories: tuple[Path, ...] = ()


def _refuse(message: str) -> NoReturn:
    raise Refusal(message)


def _same_path(left: Path, right: Path) -> bool:
    return left == right


def _under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _safe_input(raw: str, label: str) -> Path:
    if not isinstance(raw, str) or not raw or raw != raw.strip():
        _refuse(f"{label} is not an exact absolute path")
    if "\x00" in raw:
        _refuse(f"{label} contains an invalid path character")
    if any(token in raw for token in ("*", "?", "[", "]", "{", "}")):
        _refuse(f"{label} contains unsupported pattern syntax")
    if "\\" in raw:
        _refuse(f"{label} contains an unsupported path separator")
    if "//" in raw:
        _refuse(f"{label} contains a separator alias")
    pieces = raw.split("/")
    if any(piece in (".", "..") for piece in pieces):
        _refuse(f"{label} contains a lexical path alias")
    candidate = Path(raw)
    if not candidate.is_absolute():
        _refuse(f"{label} must be absolute")
    if raw.endswith("/") and raw != candidate.anchor:
        _refuse(f"{label} contains a trailing alias")
    try:
        resolved = candidate.resolve(strict=False)
    except OSError as exc:
        _refuse(f"{label} cannot be resolved: {exc}")
    if not _same_path(candidate, resolved):
        _refuse(f"{label} does not match its canonical path")
    return candidate


def _is_symlink(path: Path) -> bool:
    try:
        info = os.lstat(path)
    except OSError as exc:
        _refuse(f"cannot inspect path component {path}: {exc}")
    return stat.S_ISLNK(info.st_mode)


def _require_directory(path: Path, label: str) -> None:
    if not os.path.lexists(path):
        _refuse(f"{label} does not exist")
    if _is_symlink(path):
        _refuse(f"{label} contains a symlink")
    try:
        mode = os.lstat(path).st_mode
    except OSError as exc:
        _refuse(f"cannot inspect {label}: {exc}")
    if not stat.S_ISDIR(mode):
        _refuse(f"{label} is not a directory")


def _walk_existing_chain(anchor: Path, candidate: Path, label: str) -> bool:
    """Check every existing component from an admitted root to a candidate."""

    try:
        relative = candidate.relative_to(anchor)
    except ValueError:
        _refuse(f"{label} escapes its admitted root")
    current = anchor
    for part in relative.parts:
        current /= part
        if not os.path.lexists(current):
            return False
        if _is_symlink(current):
            _refuse(f"{label} contains a symlink")
        try:
            mode = os.lstat(current).st_mode
        except OSError as exc:
            _refuse(f"cannot inspect {label}: {exc}")
        if not stat.S_ISDIR(mode):
            _refuse(f"{label} has a non-directory path component")
    return True


def _git_top(repo: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "not a Git repository"
        _refuse(f"repository top is not an exact Git root: {detail}")
    try:
        return Path(result.stdout.strip()).resolve(strict=True)
    except (OSError, ValueError) as exc:
        _refuse(f"cannot resolve repository top: {exc}")


def _assignment_layout(repo: Path, assignment: Path) -> None:
    try:
        parts = assignment.relative_to(repo).parts
    except ValueError:
        _refuse("assignment root is unrelated to repository top")
    direction = len(parts) == 3 and parts[:2] == ("temp", "directions")
    if not direction:
        _refuse("assignment root is not an exact temp/directions/<direction-id> root")
    if any(not part or part in (".", "..") for part in parts):
        _refuse("assignment root contains an invalid component")


def _status(repo: Path, target: Path) -> None:
    relative = target.relative_to(repo).as_posix()
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignored=matching",
            "--",
            relative,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "status inspection failed"
        _refuse(f"repository status could not be inspected: {detail}")
    for line in result.stdout.splitlines():
        if line and line[:2] != "!!":
            _refuse("target contains tracked or non-ignored content")


def _empty_tree(target: Path) -> tuple[Path, ...]:
    directories: list[Path] = []
    pending = [target]
    while pending:
        current = pending.pop()
        if _is_symlink(current):
            _refuse("target contains a symlink")
        try:
            with os.scandir(current) as entries:
                children = list(entries)
        except OSError as exc:
            _refuse(f"target cannot be inspected safely: {exc}")
        directories.append(current)
        for entry in children:
            child = Path(entry.path)
            if _is_symlink(child):
                _refuse("target contains a symlink")
            try:
                mode = entry.stat(follow_symlinks=False).st_mode
            except OSError as exc:
                _refuse(f"target entry cannot be inspected safely: {exc}")
            if not stat.S_ISDIR(mode):
                _refuse("target is not an empty-directory tree")
            pending.append(child)
    directories.sort(key=lambda path: len(path.parts), reverse=True)
    return tuple(directories)


def inspect(repo: Path, assignment: Path, target: Path) -> Inspection:
    _require_directory(repo, "repository top")
    control = repo / ".omp"
    if not ((control / "AGENTS.md").is_file() or (control / "config.yml").is_file()):
        _refuse("repository top lacks .omp/AGENTS.md or .omp/config.yml")
    if not _same_path(repo, _git_top(repo)):
        _refuse("repository top does not match Git's exact top")
    _assignment_layout(repo, assignment)
    _require_directory(assignment, "assignment root")
    if not _under(assignment, repo) or _same_path(assignment, repo):
        _refuse("assignment root is outside repository scope")
    _walk_existing_chain(repo, assignment, "assignment root")
    if not _under(target, assignment):
        _refuse("target is outside assignment scope")
    if not _walk_existing_chain(assignment, target, "target"):
        _status(repo, target)
        return Inspection("ALREADY_ABSENT", target)
    if _is_symlink(target):
        _refuse("target is a symlink")
    try:
        if not stat.S_ISDIR(os.lstat(target).st_mode):
            _refuse("target is not a directory")
    except OSError as exc:
        _refuse(f"cannot inspect target: {exc}")
    _status(repo, target)
    return Inspection("PRESENT", target, _empty_tree(target))


def _remove(inspected: Inspection) -> None:
    for directory in inspected.directories:
        try:
            os.rmdir(directory)
        except OSError as exc:
            _refuse(f"target changed before removal; retry safely: {exc}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--repo-top", required=True)
    parser.add_argument("--assignment-root", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--apply", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if args.actor != "root":
            _refuse("only the root actor is admitted")
        repo = _safe_input(args.repo_top, "repository top")
        assignment = _safe_input(args.assignment_root, "assignment root")
        target = _safe_input(args.target, "target")
        first = inspect(repo, assignment, target)
        if not args.apply:
            print("ALREADY_ABSENT" if first.status == "ALREADY_ABSENT" else "PREVIEW_SAFE")
            return 0
        second = inspect(repo, assignment, target)
        if second.status == "ALREADY_ABSENT":
            print("ALREADY_ABSENT")
            return 0
        _remove(second)
        print("REMOVED")
        return 0
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
