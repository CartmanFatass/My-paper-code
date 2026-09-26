#!/usr/bin/env python3
"""Preview, retain, and independently verify data from a retiring Git worktree.

This backs up working-tree data, not Git history. It never removes a source or
changes Git registration. The destination must be outside every registered
worktree; keep its manifest and files together after the source is removed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import uuid

try:
    from scripts import hmasd_snapshot_gc as gc
except ImportError:
    import hmasd_snapshot_gc as gc


MANIFEST = "manifest.json"
CACHE_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
              ".tox", ".nox", ".venv", "venv", "node_modules"}
CACHE_FILES = {".DS_Store"}
CACHE_SUFFIXES = {".pyc", ".pyo"}


class Refusal(RuntimeError):
    pass


def _git(root: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                                timeout=120, check=False,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    except (OSError, subprocess.SubprocessError) as exc:
        raise Refusal(f"git {args[0]} failed: {exc}") from exc
    if result.returncode:
        raise Refusal(f"git {args[0]} refused: {os.fsdecode(result.stderr).strip()}")
    return result.stdout


def _paths(raw: bytes) -> set[str]:
    return {os.fsdecode(item).replace(os.sep, "/") for item in raw.split(b"\0") if item}


def _plain_absolute(path: Path) -> Path:
    if ".." in path.parts:
        raise Refusal(f"parent traversal in path: {path}")
    path = path.absolute()
    for part in (path, *path.parents):
        if part.is_symlink():
            raise Refusal(f"symlink path component: {part}")
    return path


def _inside(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def _worktrees(root: Path) -> list[Path]:
    output = _git(root, "worktree", "list", "--porcelain", "-z")
    return [Path(os.fsdecode(field[9:])).absolute() for field in output.split(b"\0")
            if field.startswith(b"worktree ")]


def _source(root: Path) -> Path:
    root = _plain_absolute(root)
    if not root.is_dir() or root not in _worktrees(root):
        raise Refusal("source must be a registered Git worktree")
    if Path(os.fsdecode(_git(root, "rev-parse", "--show-toplevel").strip())).absolute() != root:
        raise Refusal("source must be the worktree root")
    return root


def _destination(root: Path, dest: Path) -> Path:
    dest = _plain_absolute(dest)
    for worktree in _worktrees(root):
        if _inside(dest, worktree) or _inside(worktree, dest):
            raise Refusal(f"destination overlaps registered worktree {worktree}")
    if dest.exists() and not dest.is_dir():
        raise Refusal("destination is not a directory")
    return dest


def _safe_rel(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\0" in value:
        raise Refusal("invalid manifest path")
    path = PurePosixPath(value)
    if (path.is_absolute() or ":" in value.split("/", 1)[0]
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise Refusal(f"unsafe manifest path: {value!r}")
    return value


def _output_path(rel: str) -> bool:
    return rel.split("/", 1)[0] in {"runs", "temp"}


def _cache_path(rel: str) -> bool:
    parts = rel.split("/")
    return (any(part in CACHE_DIRS for part in parts[:-1])
            or parts[-1] in CACHE_FILES or Path(parts[-1]).suffix in CACHE_SUFFIXES)


def _file_info(path: Path) -> dict[str, object]:
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise Refusal(f"source is symlink or special file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    digest = hashlib.sha256()
    size = 0
    try:
        with os.fdopen(os.open(path, flags), "rb") as stream:
            opened = os.fstat(stream.fileno())
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise Refusal(f"source changed during read: {path}")
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
            after = os.fstat(stream.fileno())
    except OSError as exc:
        raise Refusal(f"cannot read {path}: {exc}") from exc
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
        stat.S_IMODE(before.st_mode)) != (after.st_dev, after.st_ino, after.st_size,
                                        after.st_mtime_ns, stat.S_IMODE(after.st_mode)) or size != after.st_size:
        raise Refusal(f"source changed during read: {path}")
    return {"sha256": digest.hexdigest(), "bytes": size,
            "mode": stat.S_IMODE(after.st_mode)}


def _selected(root: Path) -> dict[str, object]:
    head = os.fsdecode(_git(root, "rev-parse", "HEAD")).strip()
    staged = _paths(_git(root, "diff", "--cached", "--no-renames", "--name-only", "-z", "HEAD"))
    if staged:
        raise Refusal("index differs from HEAD; preserve or commit staged changes before retention: "
                      + ", ".join(sorted(staged)[:4]))
    branch = os.fsdecode(_git(root, "branch", "--show-current")).strip()
    refs = os.fsdecode(_git(root, "for-each-ref", f"--contains={head}",
                            "--format=%(refname)", "refs/heads", "refs/tags",
                            "refs/remotes")).splitlines()
    if not refs:
        raise Refusal("HEAD is not contained in a durable branch, tag, or remote ref")
    status = os.fsdecode(_git(root, "status", "--porcelain=v1", "-z",
                              "--untracked-files=all", "--ignore-submodules=none"))
    # Disable rename detection so a moved tracked path records its deleted
    # original as well as retaining the new path's bytes.
    changed = _paths(_git(root, "diff", "--no-renames", "--name-only", "-z", "HEAD"))
    deleted = sorted(_paths(_git(root, "diff", "--no-renames", "--name-only",
                              "--diff-filter=D", "-z", "HEAD")))
    tracked = _paths(_git(root, "ls-files", "-z"))
    nonignored = _paths(_git(root, "ls-files", "--others", "--exclude-standard", "-z"))
    required_outside_cache = changed | nonignored
    entries: dict[str, dict[str, object]] = {}
    def walk_error(exc: OSError) -> None:
        raise Refusal(f"cannot scan source: {exc}") from exc

    for base, dirs, files in os.walk(root, topdown=True, followlinks=False,
                                     onerror=walk_error):
        current = Path(base)
        kept_dirs = []
        for name in dirs:
            if current == root and name == ".git":
                continue
            candidate = current / name
            rel = candidate.relative_to(root).as_posix()
            if name in CACHE_DIRS and (_output_path(rel) or not any(
                item.startswith(rel + "/") for item in required_outside_cache
            )):
                continue
            if candidate.is_symlink() and (rel in changed or rel not in tracked):
                raise Refusal(f"source is symlink or special file: {candidate}")
            kept_dirs.append(name)
        dirs[:] = kept_dirs
        for name in files:
            if current == root and name == ".git":
                continue
            path = current / name
            rel = path.relative_to(root).as_posix()
            if (_output_path(rel) and not _cache_path(rel)
                    or not _output_path(rel) and (rel in changed or
                        rel not in tracked and (rel in nonignored or not _cache_path(rel)))):
                entries[rel] = _file_info(path)
    missing = changed - set(entries) - set(deleted)
    if missing:
        raise Refusal(f"changed tracked paths missing from selection: {sorted(missing)[:4]}")
    return {"schema": 1, "source_root": str(root), "head": head, "branch": branch,
            "durable_refs": sorted(refs), "status_porcelain_z": status,
            "deleted_tracked": deleted, "files": entries}


def _process_check(root: Path, sudo: bool) -> None:
    try:
        refs = gc._sudo_process_references(root) if sudo else gc._process_references(root)
    except gc.Refusal as exc:
        raise Refusal(str(exc)) from exc
    # The inspecting process necessarily has this script/cwd in the source.
    refs = [ref for ref in refs if not ref.startswith(f"pid {os.getpid()} ")]
    if refs:
        raise Refusal("worktree has live or uncertain process references: " + ", ".join(refs[:8]))


def _verify(dest: Path) -> dict[str, object]:
    dest = _plain_absolute(dest)
    path = _plain_absolute(dest / MANIFEST)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Refusal(f"cannot read manifest: {exc}") from exc
    if (not isinstance(data, dict) or set(data) != {"schema", "source_root", "head", "branch",
                                               "durable_refs", "status_porcelain_z",
                                               "deleted_tracked", "files"}
            or data.get("schema") != 1 or not isinstance(data.get("files"), dict)):
        raise Refusal("malformed manifest")
    if (not isinstance(data.get("source_root"), str) or not Path(data["source_root"]).is_absolute()
            or not isinstance(data.get("head"), str)
            or re.fullmatch(r"[0-9a-f]{40,64}", data["head"]) is None
            or not isinstance(data.get("branch"), str)
            or not isinstance(data.get("status_porcelain_z"), str)
            or not isinstance(data.get("deleted_tracked"), list)
            or not all(isinstance(item, str) for item in data["deleted_tracked"])):
        raise Refusal("malformed manifest metadata")
    for rel in data["deleted_tracked"]:
        _safe_rel(rel)
    if (not isinstance(data.get("durable_refs"), list) or not data["durable_refs"]
            or not all(isinstance(item, str) and item.startswith("refs/")
                       for item in data["durable_refs"])):
        raise Refusal("manifest has no durable refs")
    total = 0
    for rel, expected in data["files"].items():
        _safe_rel(rel)
        if (not isinstance(expected, dict) or set(expected) != {"sha256", "bytes", "mode"}
                or not isinstance(expected["sha256"], str)
                or re.fullmatch(r"[0-9a-f]{64}", expected["sha256"]) is None
                or type(expected["bytes"]) is not int or expected["bytes"] < 0
                or type(expected["mode"]) is not int or not 0 <= expected["mode"] <= 0o7777):
            raise Refusal(f"malformed file record: {rel}")
        file = _plain_absolute(dest / "files" / rel)
        if _file_info(file) != expected:
            raise Refusal(f"retained file differs from manifest: {rel}")
        total += expected["bytes"]
    return {"verified": len(data["files"]), "bytes": total, "source_root": data["source_root"]}


def _copy_one(source: Path, dest: Path, expected: dict[str, object]) -> None:
    _plain_absolute(dest)
    if dest.exists():
        if _file_info(dest) != expected:
            raise Refusal(f"existing destination differs: {dest}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    _plain_absolute(dest)
    tmp = dest.with_name(dest.name + f".partial-{uuid.uuid4().hex}")
    try:
        with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as out:
            with os.fdopen(os.open(source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)), "rb") as inp:
                while chunk := inp.read(1024 * 1024):
                    out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(tmp, expected["mode"])
        if _file_info(tmp) != expected:
            raise Refusal(f"source changed while copying: {source}")
        # Hard-link publish is exclusive: a concurrent writer cannot be overwritten.
        os.link(tmp, dest)
        _sync_directory(dest.parent)
    except FileExistsError as exc:
        raise Refusal(f"destination appeared during copy: {dest}") from exc
    finally:
        tmp.unlink(missing_ok=True)


def _sync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _retain(root: Path, dest: Path, sudo: bool) -> dict[str, object]:
    _process_check(root, sudo)
    first = _selected(root)
    dest.mkdir(parents=True, exist_ok=True)
    if (dest / MANIFEST).exists():
        verified = _verify(dest)
        recorded = json.loads((dest / MANIFEST).read_text(encoding="utf-8"))
        if recorded != first:
            raise Refusal("completed destination records different source selection")
        return verified
    for rel, expected in first["files"].items():
        _copy_one(root / rel, dest / "files" / rel, expected)
    second = _selected(root)
    _process_check(root, sudo)
    if first != second:
        raise Refusal("source selection changed during retention; no complete manifest written")
    for rel, expected in first["files"].items():
        if _file_info(_plain_absolute(dest / "files" / rel)) != expected:
            raise Refusal(f"retained copy changed before manifest: {rel}")
    tmp = dest / f".{MANIFEST}.partial-{uuid.uuid4().hex}"
    try:
        with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w",
                       encoding="utf-8") as stream:
            json.dump(first, stream, sort_keys=True, ensure_ascii=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(tmp, dest / MANIFEST)
        _sync_directory(dest)
    except FileExistsError as exc:
        raise Refusal("manifest appeared during retention") from exc
    finally:
        tmp.unlink(missing_ok=True)
    return _verify(dest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("preview", "retain"):
        part = sub.add_parser(command)
        part.add_argument("--root", required=True, type=Path)
        part.add_argument("--dest", required=True, type=Path)
        part.add_argument("--sudo-process-scan", action="store_true")
    verify = sub.add_parser("verify")
    verify.add_argument("--dest", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            result = _verify(args.dest)
        else:
            root = _source(args.root)
            dest = _destination(root, args.dest)
            if args.command == "retain":
                result = _retain(root, dest, args.sudo_process_scan)
            else:
                selection = _selected(root)
                blockers = []
                try:
                    _process_check(root, args.sudo_process_scan)
                except Refusal as exc:
                    blockers.append(str(exc))
                result = {"files": len(selection["files"]),
                          "bytes": sum(entry["bytes"] for entry in selection["files"].values()),
                          "deleted_tracked": selection["deleted_tracked"],
                          "head": selection["head"], "durable_refs": selection["durable_refs"],
                          "destination": str(dest), "blockers": blockers}
                print(json.dumps(result, sort_keys=True))
                return 2 if blockers else 0
        print(json.dumps(result, sort_keys=True))
        return 0
    except (Refusal, OSError, ValueError) as exc:
        print(json.dumps({"refused": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
