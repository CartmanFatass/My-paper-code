"""Validate an Agentify assignment result locator without reading its payload."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path


class GuardError(Exception):
    """A deterministic, machine-readable path guard failure."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


_REQUESTER_PARTITIONS = frozenset(
    {"code_project_manager", "independent_research_explorer"}
)


class _GuardParser(argparse.ArgumentParser):
    """Keep argument failures on the same machine-readable output channel."""

    def error(self, message: str) -> None:  # pragma: no cover - exercised by CLI callers
        raise GuardError("RESULT_PATH_INVALID")


def _norm(path: Path) -> str:
    """Normalize only path spelling; no file contents are inspected."""
    return os.path.normcase(os.path.normpath(os.path.abspath(os.fspath(path))))


def _has_redirect_component(path: Path) -> bool:
    """Reject symlinks and Windows reparse points in an existing path."""
    current = Path(path.anchor) if path.anchor else Path()
    for part in path.parts:
        if part == path.anchor:
            continue
        current = current / part
        try:
            if os.path.islink(os.fspath(current)):
                return True
            attributes = getattr(os.stat(os.fspath(current), follow_symlinks=False), "st_file_attributes", 0)
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            # A missing final file is handled by the regular-file check. Existing
            # ancestors are the only components that can redirect this locator.
            continue
        if attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x0400):
            return True
    return False


def _canonical_path(raw: str) -> Path:
    if not raw:
        raise GuardError("RESULT_PATH_INVALID")
    lexical = Path(raw)
    if not lexical.is_absolute():
        raise GuardError("RESULT_PATH_SCOPE_INVALID")
    lexical = Path(os.path.abspath(os.fspath(lexical)))
    if _has_redirect_component(lexical):
        raise GuardError("RESULT_PATH_REDIRECT")
    resolved = Path(os.path.realpath(os.fspath(lexical)))
    if _norm(lexical) != _norm(resolved):
        raise GuardError("RESULT_PATH_REDIRECT")
    return resolved


def _strict_assignment_descendant(path: Path, root: Path) -> str | None:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise GuardError("RESULT_PATH_SCOPE_INVALID") from exc
    # Legacy shared assignments used <transport-root>/<assignment>/<file> and
    # remain readable until their later retirement slice. Production callers
    # use <transport-root>/<requester-role>/<assignment>/<file>; returning a
    # path in another requester partition must never be accepted.
    if len(relative.parts) < 2:
        raise GuardError("RESULT_PATH_SCOPE_INVALID")
    if relative.parts[0] in _REQUESTER_PARTITIONS:
        if len(relative.parts) < 3 or not relative.parts[1]:
            raise GuardError("RESULT_PATH_SCOPE_INVALID")
        return relative.parts[0]
    return None


def validate(repo: str, expected_results_path: str, returned_results_path: str) -> None:
    """Validate locator identity and existence without opening the result file."""
    repo_path = _canonical_path(repo)
    root = repo_path / "temp" / "sessions" / "agentify_transport_operator"
    if not root.is_dir() or _has_redirect_component(root):
        raise GuardError("RESULT_PATH_SCOPE_INVALID")
    root = Path(os.path.realpath(os.fspath(root)))

    expected = _canonical_path(expected_results_path)
    returned = _canonical_path(returned_results_path)
    if _norm(expected) != _norm(returned):
        raise GuardError("RESULT_PATH_MISMATCH")

    expected_partition = _strict_assignment_descendant(expected, root)
    returned_partition = _strict_assignment_descendant(returned, root)
    if expected_partition != returned_partition:
        raise GuardError("RESULT_PATH_PARTITION_MISMATCH")

    try:
        result_stat = os.stat(os.fspath(expected), follow_symlinks=False)
    except FileNotFoundError as exc:
        raise GuardError("RESULT_FILE_MISSING") from exc
    except (NotADirectoryError, PermissionError) as exc:
        raise GuardError("RESULT_FILE_UNREADABLE") from exc
    if not stat.S_ISREG(result_stat.st_mode):
        raise GuardError("RESULT_FILE_NOT_REGULAR")


def _parser() -> argparse.ArgumentParser:
    parser = _GuardParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--expected-results-path", required=True)
    parser.add_argument("--returned-results-path", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        validate(args.repo, args.expected_results_path, args.returned_results_path)
    except GuardError as exc:
        print(json.dumps({"status": "ERROR", "code": exc.code}, separators=(",", ":")))
        return 1
    except (OSError, ValueError):
        print(json.dumps({"status": "ERROR", "code": "RESULT_PATH_INVALID"}, separators=(",", ":")))
        return 1
    print(json.dumps({"status": "VALID"}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
