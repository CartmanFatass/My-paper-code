"""One-shot zero-runtime runner for the EC4G A1 project-binding census."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.ec4g_r1.execution_digest_census import (  # noqa: E402
    build_registered_project_binding,
    run_project_census,
)


def _source_revision() -> str:
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
            "Run exactly one deterministic EC4G A1 project-binding census. "
            "The output path must not already exist."
        )
    )
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _require_source_revision(declared: str, actual: str) -> None:
    if declared != actual:
        raise ValueError(
            f"source revision mismatch: declared={declared!r} actual={actual!r}"
        )


def _write_new(output: Path, encoded: bytes) -> None:
    try:
        with output.open("xb") as handle:
            handle.write(encoded)
    except FileExistsError as exc:
        raise FileExistsError(f"refusing to overwrite one-shot result: {output}") from exc


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    actual_revision = _source_revision()
    try:
        _require_source_revision(args.source_revision, actual_revision)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if not args.run_id.strip():
        raise SystemExit("run-id must be nonempty")
    output = args.output.resolve(strict=False)
    if not output.parent.is_dir():
        raise SystemExit(f"output parent does not exist: {output.parent}")
    if output.exists():
        raise SystemExit(f"refusing to overwrite one-shot result: {output}")

    binding = build_registered_project_binding(
        source_revision=actual_revision,
        run_id=args.run_id,
    )
    result = run_project_census(binding)
    encoded = result.to_bytes() + b"\n"
    try:
        _write_new(output, encoded)
    except FileExistsError as exc:
        raise SystemExit(str(exc)) from exc

    summary = {
        "bytes": len(encoded),
        "output": str(output),
        "source_revision": actual_revision,
        "terminal_branch": result.terminal_branch.value,
    }
    print(json.dumps(summary, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
