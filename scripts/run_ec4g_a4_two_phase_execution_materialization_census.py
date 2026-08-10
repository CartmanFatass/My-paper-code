"""One-shot runner for the EC4G-A4 two-phase materialization census."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.ec4g_r1.two_phase_execution_materialization_census import (  # noqa: E402
    BINDING_PATH,
    C0_COMMIT,
    C1_COMMIT,
    CONTRACT_PATH,
    RUNNER_PATH,
    SOURCE_PATH,
    run_two_phase_census,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run one EC4G-A4 treatment: materialize and seal six C0/C1-bound "
            "execution objects, then compare the three sealed pairs. The "
            "artifact root and output must not already exist."
        )
    )
    parser.add_argument("--source-revision", required=True, help="actual lowercase 40-hex checkout revision")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _git(*arguments: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", "-C", str(REPOSITORY_ROOT), *arguments],
        check=True,
        capture_output=True,
        text=not binary,
        encoding=None if binary else "utf-8",
    )
    return completed.stdout


def _read_snapshot_blob(commit: str, path: str) -> bytes:
    resolved = str(_git("rev-parse", "--verify", f"{commit}^{{commit}}" )).strip()
    if resolved != commit:
        raise ValueError(f"snapshot commit did not resolve exactly: {commit}")
    object_type = str(_git("cat-file", "-t", f"{commit}:{path}")).strip()
    if object_type != "blob":
        raise ValueError(f"snapshot path is not a blob: {commit}:{path}")
    return bytes(_git("cat-file", "blob", f"{commit}:{path}", binary=True))


def _require_frozen_source_revision(declared: str) -> None:
    actual = str(_git("rev-parse", "HEAD")).strip()
    if declared != actual:
        raise ValueError(f"source revision mismatch: declared={declared!r} actual={actual!r}")
    for relative in (SOURCE_PATH, RUNNER_PATH):
        committed = _read_snapshot_blob(declared, relative)
        working = (REPOSITORY_ROOT / relative).read_bytes()
        if committed != working:
            raise ValueError(f"working entry point differs from frozen source revision: {relative}")


def _write_new(path: Path, content: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(content)
    except FileExistsError as exc:
        raise FileExistsError(f"refusing to overwrite one-shot result: {path}") from exc


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.run_id.strip():
        raise SystemExit("run-id must be nonempty")
    output = args.output.resolve(strict=False)
    artifact_root = args.artifact_root.resolve(strict=False)
    if not output.parent.is_dir():
        raise SystemExit(f"output parent does not exist: {output.parent}")
    # The one-shot guards precede source resolution, C0/C1 reads and all calls.
    if output.exists():
        raise SystemExit(f"refusing to overwrite one-shot result: {output}")
    if artifact_root.exists():
        raise SystemExit(f"refusing to overwrite one-shot artifact root: {artifact_root}")
    if not artifact_root.parent.is_dir():
        raise SystemExit(f"artifact-root parent does not exist: {artifact_root.parent}")
    try:
        _require_frozen_source_revision(args.source_revision)
        c0_bytes = _read_snapshot_blob(C0_COMMIT, CONTRACT_PATH)
        c1_bytes = _read_snapshot_blob(C1_COMMIT, BINDING_PATH)
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    result = run_two_phase_census(
        c0_bytes,
        c1_bytes,
        artifact_root=artifact_root,
        source_revision=args.source_revision,
        run_id=args.run_id,
    )
    encoded = result.to_bytes() + b"\n"
    try:
        _write_new(output, encoded)
    except (FileExistsError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    print(
        json.dumps(
            {
                "artifact_root": str(artifact_root),
                "bytes": len(encoded),
                "output": str(output),
                "result_id": result.payload()["result_id"],
                "terminal_branch": result.terminal_branch.value,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
