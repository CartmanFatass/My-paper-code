"""Single fail-closed entry point for the later complete R03 transaction.

S3 constructs and validates this interface but does not release it.  A future
Operator invocation must arrive inside the exact code-SHA-bound ``hmasd_run``
manifest and a separately released prelaunch dossier.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .production_contract import (
    DEFAULT_RUN_BINDING,
    RunBinding,
    canonical_run_binding,
    require_canonical_run_binding,
)
from .production_engine import execute_registered_transaction
from .production_validation import (
    PrelaunchRefusal,
    read_json,
    reject_forbidden_options,
    validate_live_hmasd_manifest,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(prog="ucope-r03-empirical-transaction")
    value.add_argument("--run-id", required=True)
    value.add_argument("--output-root", required=True)
    value.add_argument("--hmasd-manifest", required=True)
    return value


def resolve_run_binding(argv: Sequence[str]) -> RunBinding:
    reject_forbidden_options(argv)
    args = parser().parse_args(list(argv))
    try:
        return canonical_run_binding(args.run_id, args.output_root)
    except ValueError as exc:
        raise PrelaunchRefusal("run/output override is forbidden") from exc


def validate_launch(
    argv: Sequence[str],
    *,
    repository_root: Path,
    binding: RunBinding | None = None,
) -> dict[str, object]:
    reject_forbidden_options(argv)
    args = parser().parse_args(list(argv))
    if binding is None:
        try:
            binding = canonical_run_binding(args.run_id, args.output_root)
        except ValueError as exc:
            raise PrelaunchRefusal("run/output override is forbidden") from exc
    else:
        try:
            binding = require_canonical_run_binding(binding)
        except ValueError as exc:
            raise PrelaunchRefusal("run binding is not canonical") from exc
    if args.run_id != binding.run_id or args.output_root != binding.output_root:
        raise PrelaunchRefusal("run/output override is forbidden")
    root = Path(repository_root).resolve()
    expected_manifest = (
        root / Path(*binding.output_root.split("/")) / "manifest.json"
    ).resolve(strict=False)
    observed_manifest = Path(args.hmasd_manifest).resolve(strict=False)
    if observed_manifest != expected_manifest:
        raise PrelaunchRefusal("hmasd manifest path override is forbidden")
    hmasd = read_json(observed_manifest)
    if Path(str(hmasd.get("cwd", ""))).resolve(strict=False) != root:
        raise PrelaunchRefusal("hmasd manifest cwd differs")
    code_sha = hmasd.get("code_sha")
    validate_live_hmasd_manifest(hmasd, code_sha=str(code_sha), binding=binding)
    return {
        "run_id": binding.run_id,
        "output_root": binding.output_root,
        "code_sha": code_sha,
        "validated": True,
        "complete_only": True,
        "rerun_permitted": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    # Resolving the repository is read-only.  hmasd_run itself owns output-root
    # creation, process identity, and terminal observation.
    repository_root = Path(__file__).resolve().parents[4]
    arguments = tuple(argv) if argv is not None else None
    if arguments is None:
        import sys

        arguments = tuple(sys.argv[1:])
    launch = validate_launch(arguments, repository_root=repository_root)
    execute_registered_transaction(launch, repository_root=repository_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
