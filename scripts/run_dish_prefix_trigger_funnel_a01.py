"""Publish the frozen seed-11 retained-prefix diagnostic."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.degraded_incumbent_shadow_handover.first_trigger_source_scout_b01.funnel_a01 import (
    CAP_SECONDS, INPUT_SHA256, INPUT_SOURCE, run_funnel,
)
from scripts.run_dish_first_trigger_source_scout_b01 import _peak_rss_bytes


def project_cost():
    return {"mode": "project-cost", "law": "1.5 * (0 * 10.672341100056656 + 300)",
            "projected_seconds": 450.0, "cap_seconds": CAP_SECONDS,
            "path": "seed11_original_prefix", "within_cap": 450.0 <= CAP_SECONDS}


def run(checkpoint: Path, admission: Path, output: Path):
    receipt = json.loads(admission.read_text(encoding="utf-8"))
    if not (receipt.get("passed") is True and receipt.get("physical_floor_pass") is True
            and receipt.get("effective_floor_pass") is True
            and int(receipt.get("available_physical_bytes", 0)) >= 2**32
            and int(receipt.get("effective_available_bytes", 0)) >= 2**32):
        raise RuntimeError("fresh memory admission did not pass")
    launch_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    retained = checkpoint.read_bytes()
    summary = run_funnel(retained)
    try:
        rss = _peak_rss_bytes()
    except OSError:
        rss = None
    result = {**summary, "launch_sha": launch_sha, "admission_receipt": str(admission.resolve()),
              "input_reference": {"path": str(checkpoint.resolve()), "bytes": len(retained),
                                  "declared_source": INPUT_SOURCE, "declared_sha256": INPUT_SHA256},
              "peak_rss_bytes": rss, "resources_unmeasured": rss is None}
    output.mkdir(parents=True)
    (output / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    modes = parser.add_subparsers(dest="mode", required=True)
    modes.add_parser("project-cost")
    command = modes.add_parser("run")
    command.add_argument("--seed", type=int, choices=(11,), required=True)
    command.add_argument("--checkpoint", type=Path, required=True)
    command.add_argument("--admission", type=Path, required=True)
    command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    payload = project_cost() if args.mode == "project-cost" else run(args.checkpoint, args.admission, args.out)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
