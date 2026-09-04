"""One-shot runner for the EC4G-A5 portable source-bound census."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.ec4g_r1 import portable_source_bound_two_phase_execution_census as census  # noqa: E402
from experiments.candidates.ec4g_r1 import two_phase_execution_materialization_census as pure_dependency  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Bind cwd, runner, runtime core and pure-code dependency to one frozen "
            "registered source worktree, then run one fresh EC4G-A5 two-phase census."
        )
    )
    parser.add_argument("--source-revision", required=True, help="actual lowercase 40-hex frozen checkout revision")
    parser.add_argument("--registered-worktree-root", type=Path, required=True)
    parser.add_argument("--main-checkout-root", type=Path, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="perform source-entry binding only; do not read C0/C1 or create treatment artifacts",
    )
    return parser


def _git(root: Path, *arguments: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=not binary,
        encoding=None if binary else "utf-8",
    )
    return completed.stdout


def _read_snapshot_blob(root: Path, commit: str, path: str) -> bytes:
    resolved = str(_git(root, "rev-parse", "--verify", f"{commit}^{{commit}}")).strip()
    if resolved != commit:
        raise ValueError(f"snapshot commit did not resolve exactly: {commit}")
    object_type = str(_git(root, "cat-file", "-t", f"{commit}:{path}")).strip()
    if object_type != "blob":
        raise ValueError(f"snapshot path is not a blob: {commit}:{path}")
    return bytes(_git(root, "cat-file", "blob", f"{commit}:{path}", binary=True))


def _write_new(path: Path, content: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(content)
    except FileExistsError as exc:
        raise FileExistsError(f"refusing to overwrite one-shot result: {path}") from exc


def _entry(args: argparse.Namespace) -> census.SourceEntryAdmission:
    return census.admit_source_entry(
        source_revision=args.source_revision,
        registered_worktree_root=args.registered_worktree_root,
        main_checkout_root=args.main_checkout_root,
        runner_file=Path(__file__),
        runtime_module_file=Path(census.__file__),
        pure_algorithm_dependency_file=Path(pure_dependency.__file__),
    )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    entry = _entry(args)
    if args.preflight_only:
        print(json.dumps(entry.payload(), ensure_ascii=True, separators=(",", ":"), sort_keys=True))
        return 0 if entry.accepted else 2

    if args.run_id is None or not args.run_id.strip():
        raise SystemExit("--run-id must be nonempty outside --preflight-only")
    if args.artifact_root is None or args.output is None:
        raise SystemExit("--artifact-root and --output are required outside --preflight-only")
    output = args.output.resolve(strict=False)
    artifact_root = args.artifact_root.resolve(strict=False)
    if not output.parent.is_dir():
        raise SystemExit(f"output parent does not exist: {output.parent}")
    if output.exists():
        raise SystemExit(f"refusing to overwrite one-shot result: {output}")
    if artifact_root.exists():
        raise SystemExit(f"refusing to overwrite one-shot artifact root: {artifact_root}")
    if not artifact_root.parent.is_dir():
        raise SystemExit(f"artifact-root parent does not exist: {artifact_root.parent}")

    c0_bytes: bytes | None = None
    c1_bytes: bytes | None = None
    if entry.accepted:
        root = Path(entry.registered_worktree_root)
        try:
            c0_bytes = _read_snapshot_blob(root, census.C0_COMMIT, census.CONTRACT_PATH)
            c1_bytes = _read_snapshot_blob(root, census.C1_COMMIT, census.BINDING_PATH)
        except (OSError, subprocess.CalledProcessError, ValueError) as exc:
            # C0/C1 failure is downstream of a valid source-entry gate and is
            # therefore represented by A5_INPUT_OR_DESIGN_FREEZE_INVALID.
            c0_bytes = None
            c1_bytes = None
            snapshot_read_failure = str(exc)
        else:
            snapshot_read_failure = None
    else:
        snapshot_read_failure = None

    result = census.run_portable_two_phase_census(
        c0_bytes,
        c1_bytes,
        entry_admission=entry,
        artifact_root=artifact_root,
        run_id=args.run_id,
        input_read_failure=snapshot_read_failure,
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
                "source_entry_accepted": entry.accepted,
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
