"""Run from repository cwd with python -m, after external admit-memory && this command."""

import argparse
import json
from pathlib import Path
import subprocess
import time

from experiments.candidates.degraded_incumbent_shadow_handover.first_trigger_source_scout_b01 import path_a03
from scripts.run_dish_first_trigger_source_scout_b01 import _peak_rss_bytes

ROOT = Path(__file__).resolve().parents[1]


def project_cost():
    per_host = 1.5 * (20 + 4 * 1_200 * 0.006038872852291206 + 10)
    return {"law": "1.5 * (20 + 4 * 1200 * 0.006038872852291206 + 10)",
            "per_host_seconds": per_host, "pair_seconds": 2 * per_host,
            "per_host_cap_seconds": 300, "pair_cap_seconds": 600,
            "hosts": list(path_a03.HOSTS)}


def run(checkpoint, admission, output):
    started = time.perf_counter()
    retained = checkpoint.read_bytes()
    result = path_a03.run_pair(retained, output)
    launch_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                                capture_output=True, text=True).stdout.strip()
    try:
        rss = _peak_rss_bytes()
    except OSError:
        rss = None
    completed = result["new_exposure"]["completed_ticks"]
    wall = time.perf_counter() - started
    result.update(launch_sha=launch_sha, checkpoint=str(checkpoint.resolve()),
                  checkpoint_bytes=len(retained), admission_receipt=str(admission.resolve()),
                  peak_rss_bytes=rss, resources_unmeasured=rss is None,
                  measured_cost={"wall_seconds": wall, "completed_ticks": completed,
                                 "seconds_per_completed_tick": wall / completed if completed else None},
                  timing_scope="Pair wall includes input read, both builds/models/evaluations and trace writes/flush/close; summary serialization/write excluded, checked against cap after write.")
    if wall >= path_a03.PAIR_CAP:
        raise RuntimeError("incomplete A03: pair time cap reached before summary publication")
    result["wall_seconds"] = wall
    result["measured_cost"]["wall_seconds"] = wall
    result["measured_cost"]["seconds_per_completed_tick"] = wall / completed if completed else None
    (output / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if time.perf_counter() - started >= path_a03.PAIR_CAP:
        raise RuntimeError("incomplete A03: pair time cap exceeded during summary publication")
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
    result = project_cost() if args.mode == "project-cost" else run(args.checkpoint, args.admission, args.out)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
