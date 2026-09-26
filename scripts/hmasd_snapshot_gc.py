#!/usr/bin/env python3
"""Inspect or explicitly reclaim completed HMASD launch source snapshots.

Preview is the default. Apply requires one or more exact snapshot IDs. Claims,
manifests, and result directories are retained for operation recovery.
Explicit --unclaimed-source also permits an unused, clean source-only copy;
it never infers a process exit or a scientific result from a missing claim.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any

try:
    from scripts import hmasd_launch
except ImportError:
    import hmasd_launch


SNAPSHOT_ID = re.compile(r"[0-9a-f]{32}\Z")
TERMINAL_PROCESS_STATES = {"absent", "identity_mismatch", "not_running"}


class Refusal(RuntimeError):
    pass


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], text=True, capture_output=True,
            timeout=120, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Refusal(f"git {args[0]} failed: {exc}") from exc
    if check and result.returncode:
        raise Refusal(f"git {args[0]} refused: {result.stderr.strip() or result.stdout.strip()}")
    return result


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Refusal(f"unreadable record {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise Refusal(f"record is not an object: {path}")
    return value


def _registered(repo: Path, snapshot: Path) -> bool:
    lines = _git(repo, "worktree", "list", "--porcelain").stdout.splitlines()
    return f"worktree {snapshot}" in lines


def _durable_ref(repo: Path, sha: str) -> str | None:
    refs = _git(repo, "for-each-ref", f"--contains={sha}", "--format=%(refname)",
                "refs/heads", "refs/tags", "refs/remotes").stdout.splitlines()
    return refs[0] if refs else None


def _process_references(snapshot: Path, *, uid: int | None = None,
                        pids: list[int] | None = None) -> list[str]:
    """Inspect all observable processes owned by this uid; uncertainty refuses GC."""
    if sys.platform != "linux":
        raise Refusal("process reference inspection is supported only on Linux")
    prefix = os.fsencode(str(snapshot))
    references: list[str] = []
    target_uid = os.geteuid() if uid is None else uid
    entries = ([Path("/proc") / str(pid) for pid in pids] if pids is not None
               else Path("/proc").iterdir())
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            # /proc/<pid> ownership changes to root for a non-dumpable process.
            # Its status Uid remains the real process owner.
            status = (entry / "status").read_text(encoding="utf-8")
            uid_line = next((line for line in status.splitlines() if line.startswith("Uid:")), None)
            if uid_line is None:
                raise Refusal(f"process {entry.name} has no Uid status")
            process_uids = [int(part) for part in uid_line.split()[1:]]
            if target_uid not in process_uids:
                continue
            # A process may disappear during the scan. Other inspection errors
            # for a live own-user process are uncertainty, not clearance.
            for name in ("cwd", "exe"):
                target = os.fsencode(os.readlink(entry / name))
                if target == prefix or target.startswith(prefix + b"/"):
                    references.append(f"pid {entry.name} {name}")
            if prefix in (entry / "cmdline").read_bytes():
                references.append(f"pid {entry.name} cmdline")
            fd_root = entry / "fd"
            for fd in fd_root.iterdir():
                try:
                    target = os.fsencode(os.readlink(fd))
                except FileNotFoundError:
                    # A descriptor closed while enumerating cannot retain a
                    # snapshot reference; the process itself is still checked.
                    continue
                if target == prefix or target.startswith(prefix + b"/"):
                    references.append(f"pid {entry.name} fd/{fd.name}")
            if prefix in (entry / "maps").read_bytes():
                references.append(f"pid {entry.name} maps")
        except FileNotFoundError:
            if entry.exists():
                raise Refusal(f"process {entry.name} changed during reference inspection")
        except OSError as exc:
            raise Refusal(f"cannot inspect own process {entry.name}: {exc}; "
                          "retry with --sudo-process-scan") from exc
    return references


def _sudo_process_references(snapshot: Path) -> list[str]:
    request = json.dumps({"snapshot": str(snapshot), "uid": os.geteuid()})
    try:
        result = subprocess.run(
            ["sudo", "-n", "/usr/bin/python3", "-B", str(Path(__file__).resolve()),
             "--_scan-processes"], input=request, text=True, capture_output=True,
            timeout=120, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise Refusal(f"elevated read-only process scan failed: {exc}") from exc
    if result.returncode:
        raise Refusal("elevated read-only process scan refused: " + result.stderr.strip())
    try:
        references = json.loads(result.stdout)
    except ValueError as exc:
        raise Refusal("elevated process scan returned invalid JSON") from exc
    if not isinstance(references, list) or not all(isinstance(item, str) for item in references):
        raise Refusal("elevated process scan returned invalid references")
    return references


def _check_source(repo: Path, snapshot: Path, sha: str, *, sudo_process_scan: bool) -> str:
    dirty = _git(snapshot, "status", "--porcelain=v1", "--untracked-files=all",
                 "--ignored=matching", "--ignore-submodules=none").stdout
    if dirty:
        raise Refusal("snapshot has changed, untracked, or ignored files")
    durable = _durable_ref(repo, sha)
    if durable is None:
        raise Refusal("source commit is not reachable from a branch, tag, or remote ref")
    references = (_sudo_process_references(snapshot) if sudo_process_scan
                  else _process_references(snapshot))
    if references:
        raise Refusal("snapshot is referenced by " + ", ".join(references[:8]))
    return durable


def _check(repo: Path, common: Path, snapshot_id: str, *, sudo_process_scan: bool,
           unclaimed_source: bool = False) -> dict[str, Any]:
    parent = common / "hmasd-launch-sources"
    snapshot = parent / snapshot_id
    result: dict[str, Any] = {"snapshot": snapshot_id, "path": str(snapshot), "eligible": False}
    if not snapshot.exists():
        result["reason"] = "absent"
        return result
    if snapshot.is_symlink() or snapshot.resolve(strict=True) != snapshot:
        raise Refusal("snapshot path is redirected")
    if not snapshot.is_dir() or not _registered(repo, snapshot):
        raise Refusal("snapshot is not a registered Git worktree")
    if hmasd_launch._git_common_dir(snapshot) != common:
        raise Refusal("snapshot belongs to another Git repository")
    claims_root = common / "hmasd-admission"
    claims = []
    for path in claims_root.glob("*.json"):
        record = _read_object(path)
        source = record.get("source_root")
        if not isinstance(source, str) or not source:
            raise Refusal(f"claim has no source root: {path}")
        if Path(source).resolve(strict=False) == snapshot:
            claims.append((path, record))
    if not claims and unclaimed_source:
        # Only the redundant source checkout is reclaimed. No output, claim,
        # witness or branch is edited, and no operation state is manufactured.
        if _git(snapshot, "symbolic-ref", "-q", "HEAD", check=False).returncode == 0:
            raise Refusal("unclaimed source must be a detached snapshot")
        sha = _git(snapshot, "rev-parse", "HEAD").stdout.strip()
        durable = _check_source(repo, snapshot, sha, sudo_process_scan=sudo_process_scan)
        result.update(eligible=True, kind="unclaimed_source_only", sha=sha,
                      durable_ref=durable)
        return result
    if len(claims) != 1:
        raise Refusal(f"expected one associated claim, found {len(claims)}")
    claim_path, claim = claims[0]
    output_raw = claim.get("output_root")
    manifest_raw = claim.get("manifest_ref")
    if not isinstance(output_raw, str) or not isinstance(manifest_raw, str):
        raise Refusal("claim lacks result paths")
    output = Path(output_raw).resolve(strict=True)
    manifest_path = Path(manifest_raw).resolve(strict=True)
    if _inside(output, snapshot) or _inside(manifest_path, snapshot):
        raise Refusal("operation evidence is inside snapshot")
    if manifest_path != output / "launch-manifest.json":
        raise Refusal("manifest path differs from result root")
    manifest = _read_object(manifest_path)
    if claim_path.name != f"{claim.get('claim_key')}.json":
        raise Refusal("claim key differs from claim filename")
    reference = manifest.get("operation_ref") or manifest.get("claim_ref")
    if not isinstance(reference, str) or Path(reference).resolve(strict=False) != claim_path:
        raise Refusal("manifest refers to another claim")
    for key in ("claim_key", "direction", "sha", "node", "host_identity", "source_root",
                "output_root", "identity_command", "command_sha256"):
        if claim.get(key) != manifest.get(key):
            raise Refusal(f"claim and manifest disagree on {key}")
    if manifest.get("source_root") != str(snapshot) or manifest.get("cwd") != str(snapshot):
        raise Refusal("manifest source/cwd differs from snapshot")
    if manifest.get("host_identity") != platform.node():
        raise Refusal("operation belongs to another host")
    sha = manifest.get("sha")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise Refusal("invalid source SHA")
    if _git(snapshot, "rev-parse", "HEAD").stdout.strip() != sha:
        raise Refusal("snapshot HEAD differs from operation SHA")
    operation = hmasd_launch.status(claim_path)
    execution = operation["execution"]
    if operation["record_consistency"]["state"] != "consistent":
        raise Refusal("operation records conflict")
    if execution["state"] != "exited" or execution["exit_witness"]["state"] != "valid":
        raise Refusal("operation has no valid terminal exit witness")
    for role in ("supervisor", "runner"):
        if execution[role]["state"] not in TERMINAL_PROCESS_STATES:
            raise Refusal(f"{role} is not positively terminal: {execution[role]['state']}")
    witness_path = Path(execution["exit_witness"]["path"]).resolve(strict=True)
    if witness_path != output / "process-exit.json":
        raise Refusal("exit witness path differs from result root")
    durable = _check_source(repo, snapshot, sha, sudo_process_scan=sudo_process_scan)
    result.update(eligible=True, claim=str(claim_path), output=str(output), sha=sha,
                  durable_ref=durable)
    return result


def inspect(repo: Path, snapshot_id: str, *, apply: bool = False,
            sudo_process_scan: bool = False, unclaimed_source: bool = False) -> dict[str, Any]:
    if SNAPSHOT_ID.fullmatch(snapshot_id) is None:
        return {"snapshot": snapshot_id, "eligible": False, "reason": "invalid snapshot ID"}
    repo = hmasd_launch._git_root(repo.resolve(strict=True))
    common = hmasd_launch._git_common_dir(repo)
    try:
        with hmasd_launch._claim_lock(common):
            result = _check(repo, common, snapshot_id, sudo_process_scan=sudo_process_scan,
                            unclaimed_source=unclaimed_source)
            if not apply or not result["eligible"]:
                return result
            snapshot = Path(result["path"])
            _git(repo, "worktree", "unlock", str(snapshot))
            try:
                _git(repo, "worktree", "remove", str(snapshot))
            except Refusal:
                if snapshot.exists() and _registered(repo, snapshot):
                    _git(repo, "worktree", "lock", str(snapshot))
                raise
            result["removed"] = True
            return result
    except (Refusal, hmasd_launch.LaunchRefusal, OSError, ValueError) as exc:
        return {"snapshot": snapshot_id, "path": str(common / "hmasd-launch-sources" / snapshot_id),
                "eligible": False, "reason": str(exc)}


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv == ["--_scan-processes"]:
        try:
            request = json.load(sys.stdin)
            caller_uid = int(os.environ["SUDO_UID"])
            if (not isinstance(request, dict) or request.get("uid") != caller_uid
                    or not isinstance(request.get("snapshot"), str)
                    or not Path(request["snapshot"]).is_absolute()):
                raise Refusal("invalid elevated scan request")
            print(json.dumps(_process_references(Path(request["snapshot"]), uid=caller_uid)))
            return 0
        except (OSError, ValueError, TypeError, Refusal) as exc:
            print(f"process scan refused: {exc}", file=sys.stderr)
            return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--snapshot", action="append", default=[], metavar="ID")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--unclaimed-source", action="store_true",
                        help="allow an explicitly selected clean source-only snapshot with no claim")
    parser.add_argument("--sudo-process-scan", action="store_true",
                        help="run only the read-only Linux process scan with sudo -n")
    args = parser.parse_args(argv)
    if args.apply and not args.snapshot:
        parser.error("--apply requires at least one --snapshot ID")
    if args.unclaimed_source and not args.snapshot:
        parser.error("--unclaimed-source requires at least one --snapshot ID")
    try:
        repo = hmasd_launch._git_root(args.repo.resolve(strict=True))
        common = hmasd_launch._git_common_dir(repo)
        parent = common / "hmasd-launch-sources"
        ids = args.snapshot or sorted(path.name for path in parent.iterdir()) if parent.exists() else args.snapshot
        results = [inspect(repo, snapshot_id, apply=args.apply,
                           sudo_process_scan=args.sudo_process_scan,
                           unclaimed_source=args.unclaimed_source) for snapshot_id in ids]
    except (OSError, hmasd_launch.LaunchRefusal) as exc:
        print(f"snapshot GC refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"mode": "apply" if args.apply else "preview", "snapshots": results},
                     ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if args.apply and any(not item.get("removed") for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
