#!/usr/bin/env python3
"""Read-only adapters for codex_wait: producer result JSON or a published Git file.

Only adapters decide readiness. The generic controller never interprets research,
build, browser or publication semantics, and these probes never start that work.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import time


def result_json(path: Path, expected_id: str, identity_key: str = "operation_id") -> dict:
    if not path.exists():
        return {"state": "running", "reason": "producer result is not published"}
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict) or result.get(identity_key) != expected_id:
        return {"state": "blocked", "reason": "producer result identity does not match"}
    if result.get("state") not in ("running", "complete", "failed", "blocked", "unknown"):
        raise ValueError("producer must publish a generic state, not an inferred success")
    return {**result, "result_file": str(path.resolve())}


def git_publication(repo: Path, remote: str, ref: str, path: str,
                    baseline: str, timeout: float = 15) -> dict:
    relative = PurePosixPath(path)
    if (not path or relative.is_absolute() or ".." in relative.parts
            or str(relative) != path or "\x00" in path):
        raise ValueError("file must be an exact repository-relative POSIX path")
    if not remote or remote.startswith("-") or not ref.startswith("refs/"):
        raise ValueError("name a remote and an exact fully qualified Git ref")
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", baseline):
        raise ValueError("baseline must be a full immutable commit ID")
    deadline = time.monotonic() + timeout

    def git(*args):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("publication probe exhausted its query budget")
        value = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                               timeout=remaining, check=False)
        if value.returncode:
            raise RuntimeError(f"read-only Git query failed with exit {value.returncode}")
        return value.stdout

    def blob(sha):
        # Require a real commit even if its selected path is absent.
        git("cat-file", "-e", sha + "^{commit}")
        output = git("ls-tree", "-z", "--full-tree", sha, "--", path)
        matches = []
        for record in output.split(b"\0"):
            if not record:
                continue
            metadata, name = record.split(b"\t", 1)
            if name.decode("utf-8") == path:
                mode, kind, object_id = metadata.decode("ascii").split()
                if kind != "blob":
                    raise ValueError("publication predicate expects a file")
                matches.append(object_id)
        if len(matches) > 1:
            raise ValueError("publication path did not resolve uniquely")
        return matches[0] if matches else None

    published = git("ls-remote", "--refs", "--exit-code", remote, ref).decode("ascii").splitlines()
    matches = [line.split()[0] for line in published if line.split()[1] == ref]
    if len(matches) != 1:
        raise ValueError("published ref did not resolve uniquely")
    sha = matches[0]
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha):
        raise ValueError("published ref returned an invalid commit ID")
    old_blob, new_blob = blob(baseline), blob(sha)
    return {"state": "complete" if old_blob != new_blob else "running",
            "condition": "published_file_changed", "repository": str(repo.resolve()),
            "ref": ref, "path": path, "baseline_sha": baseline,
            "source_sha": sha, "baseline_blob": old_blob, "published_blob": new_blob,
            "meaning": "file publication changed; producer's full task may still be incomplete"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="kind", required=True)
    result = commands.add_parser("result-json")
    result.add_argument("--path", type=Path, required=True)
    result.add_argument("--expected-id", required=True)
    result.add_argument("--identity-key", default="operation_id")
    publication = commands.add_parser("git-publication")
    publication.add_argument("--repo", type=Path, required=True)
    publication.add_argument("--remote", default="origin")
    publication.add_argument("--ref", default="refs/heads/main")
    publication.add_argument("--path", required=True)
    publication.add_argument("--baseline", required=True)
    publication.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args(argv)
    try:
        if args.kind == "result-json":
            value = result_json(args.path, args.expected_id, args.identity_key)
        else:
            value = git_publication(args.repo, args.remote, args.ref, args.path,
                                    args.baseline, args.timeout)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        value = {"state": "unknown", "reason": "read-only probe could not establish current state",
                 "error_type": type(exc).__name__}
    print(json.dumps(value, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
