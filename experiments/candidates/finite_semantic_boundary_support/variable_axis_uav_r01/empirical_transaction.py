from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from .empirical_contract import OUTPUT_ROOT
from .empirical_manifest import (
    build_runtime_contract,
    observe_candidate_blob_hashes,
    validate_candidate_source_binding,
    validate_operator_runtime_files,
    validate_release_manifest,
)
from .empirical_validation import assert_no_terminal_rerun
from .engine import run_registered_transaction
from .result import build_registered_complete_result, write_registered_complete_result


def _git_identity(repo: Path) -> tuple[str, str]:
    branch = subprocess.run(
        ["git", "-C", str(repo), "symbolic-ref", "--quiet", "--short", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if branch.returncode or head.returncode:
        raise PermissionError("registered release Git identity cannot be observed")
    return branch.stdout.strip(), head.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Exact FSBS R01 registered empirical transaction"
    )
    parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[4]
    output_root = repo / OUTPUT_ROOT
    manifest_path = output_root / "manifest.json"
    if not output_root.is_dir() or not manifest_path.is_file():
        print("registered empirical transaction not released", file=sys.stderr)
        return 7
    try:
        assert_no_terminal_rerun(output_root)
        branch, head = _git_identity(repo)
        contract = build_runtime_contract(repo, candidate_branch=branch)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        operator_runtime_files = validate_operator_runtime_files(
            manifest, manifest_path, observed_branch=branch
        )
        release = validate_release_manifest(
            manifest,
            contract,
            manifest_path=manifest_path,
            observed_cwd=repo,
            observed_branch=branch,
            observed_candidate_head=head,
            observed_payload_pid=os.getpid(),
            operator_runtime_files=operator_runtime_files,
        )
        validate_candidate_source_binding(
            contract, observe_candidate_blob_hashes(repo, head, contract)
        )
        receipt = run_registered_transaction(output_root, release=release)
        result = build_registered_complete_result(receipt, release=release)
        write_registered_complete_result(output_root / "result.json", result, release=release)
    except (OSError, ValueError, PermissionError, KeyError, TypeError) as exc:
        print(f"registered empirical transaction failed: {exc}", file=sys.stderr)
        return 7
    print("FSBS_R01_REGISTERED_COMPLETE", file=sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
