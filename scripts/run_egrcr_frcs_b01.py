"""Run or statically project the EGRCR-FRCS-B01 experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.expressibility_gated_renewal_credit_relay.finite_resource_censored_substitution_b01 import config as C


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    subparsers.add_parser("project-cost", help="print the prospective static cost calculation")
    run = subparsers.add_parser("run", help="run one paired learned-arm invocation")
    run.add_argument("--seed", type=int, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--admission-receipt", type=Path, required=True)
    run.add_argument("--toy", action="store_true", help="small non-scientific profile for the smoke test")
    return parser


def _launch_sha() -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def _read_passing_admission(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    minimum = 4 * 1024**3
    if not (
        payload.get("passed") is True
        and int(payload.get("available_physical_bytes", 0)) >= minimum
        and int(payload.get("effective_available_bytes", 0)) >= minimum
    ):
        raise ValueError("external admission receipt does not show both memory floors passing")
    return {"path": str(path.resolve()), "payload": payload}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.mode == "project-cost":
        print(json.dumps(C.project_cost_payload(), sort_keys=True))
        return 0
    if not args.toy and args.seed != C.SCIENTIFIC_SEED:
        print(
            f"scientific run requires frozen seed {C.SCIENTIFIC_SEED}",
            file=sys.stderr,
        )
        return 2

    from experiments.candidates.expressibility_gated_renewal_credit_relay.finite_resource_censored_substitution_b01.experiment import run_experiment

    admission = _read_passing_admission(args.admission_receipt)
    options = {}
    profile = "scientific"
    if args.toy:
        options = {"train_episodes": 24, "updates": 4, "batch_size": 8, "evaluation_episodes": 32}
        profile = "toy_smoke_non_scientific"
    command_argv = list(sys.argv if argv is None else [str(Path(__file__)), *argv])
    summary = run_experiment(
        args.seed,
        argv=command_argv,
        launch_sha=_launch_sha(),
        profile=profile,
        admission_receipt=admission,
        **options,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"branch": summary["branch"], "summary": str(summary_path)}, sort_keys=True))
    if summary["technical_outcome"] == "NON_SCIENTIFIC_TOY_SMOKE_COMPLETE":
        return 0
    return 0 if summary["branch"] not in {None, "FRCS-INVALID-INCOMPLETE"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
