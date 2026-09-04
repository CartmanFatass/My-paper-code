"""One-shot runner for the zero-runtime EC4G-A3 two-snapshot audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.ec4g_r1.rer3_complete_prospective_binding_audit import (  # noqa: E402
    C0_COMMIT,
    audit_frozen_pair,
    freeze_repository_pair,
)


def _actual_c1_commit() -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPOSITORY_ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run exactly one zero-runtime EC4G-A3 audit of the C0 contract and "
            "an externally supplied actual C1 binding commit. The output path "
            "must not exist."
        )
    )
    parser.add_argument(
        "--c1-commit",
        required=True,
        help="actual lowercase 40-hex C1 checkout commit supplied after C1 exists",
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _require_actual_c1(declared: str, actual: str) -> None:
    if declared != actual:
        raise ValueError(f"C1 commit mismatch: declared={declared!r} actual={actual!r}")
    if declared == C0_COMMIT:
        raise ValueError("C1 must be distinct from C0")


def _write_new(output: Path, encoded: bytes) -> None:
    try:
        with output.open("xb") as handle:
            handle.write(encoded)
    except FileExistsError as exc:
        raise FileExistsError(f"refusing to overwrite one-shot result: {output}") from exc


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.run_id.strip():
        raise SystemExit("run-id must be nonempty")

    output = args.output.resolve(strict=False)
    if not output.parent.is_dir():
        raise SystemExit(f"output parent does not exist: {output.parent}")
    # This preflight precedes source resolution, snapshot freeze, and every role inspection.
    if output.exists():
        raise SystemExit(f"refusing to overwrite one-shot result: {output}")

    actual_c1 = _actual_c1_commit()
    try:
        _require_actual_c1(args.c1_commit, actual_c1)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    frozen = freeze_repository_pair(REPOSITORY_ROOT, actual_c1)
    result = audit_frozen_pair(
        frozen,
        run_id=args.run_id,
        registered_audit=True,
    )
    encoded = result.to_bytes() + b"\n"
    try:
        _write_new(output, encoded)
    except FileExistsError as exc:
        raise SystemExit(str(exc)) from exc

    summary = {
        "bytes": len(encoded),
        "c0_commit": C0_COMMIT,
        "c1_commit": actual_c1,
        "output": str(output),
        "result_id": result.payload()["result_id"],
        "terminal_branch": result.terminal_branch.value,
    }
    print(json.dumps(summary, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
