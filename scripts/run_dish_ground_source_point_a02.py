"""One ordinary native prepared point, with separately derived clearance samples."""

import argparse
import json
import math
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

from experiments.candidates.degraded_incumbent_shadow_handover.first_trigger_source_scout_b01 import study
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_backend as backend
from scripts.run_dish_first_trigger_source_scout_b01 import _peak_rss_bytes

CAP_SECONDS = 60.0


def terrain(x, y):
    return (135.0 * math.exp(-(x / 75.0)**2 - (y / 220.0)**4)
            + 55.0 * math.exp(-((x - 90.0) / 35.0)**2 - ((y + 40.0) / 85.0)**2))


def clearance_sample(start, end, j, clearance, reflection):
    q = j / 128.0
    x, y, z = (a + q * (b - a) for a, b in zip(start, end))
    height = terrain(x, reflection * y)
    return {"j": j, "xyz": [x, y, z], "terrain_y": reflection * y,
            "terrain_height": height, "clearance": clearance,
            "terrain_plus_clearance": height + clearance,
            "strict_clearance_pass": z > height + clearance}


def read_point(point, coordinate):
    state, physics, observation = point.state, point.physics, point.observation
    source = [physics.gx, physics.gy, 0.0]
    receivers = []
    for receiver in range(2):
        uav = [state.p[2 * receiver], state.p[2 * receiver + 1], 90.0]
        distance = math.sqrt(sum((a - b)**2 for a, b in zip(source, uav)))
        radio = clearance_sample(source, uav, 1, 8.0, state.reflection)
        camera = clearance_sample(uav, source, 127, 5.0, state.reflection)
        margin = float(physics.radio[receiver])
        if not all(math.isfinite(v) for v in (
            *source, *uav, distance, margin, radio["terrain_height"], camera["terrain_height"],
        )):
            raise RuntimeError("incomplete A02: nonfinite point measurement")
        receivers.append({
            "receiver": receiver, "hop": f"G_TO_U{receiver}",
            "role": "owner" if receiver == state.owner else "standby",
            "native": {"uav_xy": uav[:2], "camera_present": int(physics.camera_present[receiver]),
                       "source_hop_margin_db": margin, "send_margin_eligible": margin >= 6.0},
            "derived": {"declared_uav_height": 90.0, "source_hop_distance": distance,
                        "radio_j1": radio, "reverse_camera_j127": camera},
        })
    boundary = {name: int(getattr(state, name)) for name in (
        "initialized", "tick", "test_mode", "block", "package", "schedule", "route_speed",
        "evaluation_slot", "initial_owner", "owner", "reflection", "mask_enabled", "terminal",
    )}
    expected = {"initialized": 1, "tick": 0, "test_mode": 0, "block": 0, "package": 0,
                "schedule": 1, "route_speed": 4, "evaluation_slot": 0, "initial_owner": 0,
                "owner": 0, "reflection": 1, "mask_enabled": 1, "terminal": 0}
    boundary_matches = (boundary == expected and observation.tick == 0
                        and observation.owner == 0 and coordinate == study.panel()[0])
    witness = all(not r["derived"]["radio_j1"]["strict_clearance_pass"]
                  and not r["derived"]["reverse_camera_j127"]["strict_clearance_pass"]
                  and r["native"]["camera_present"] == 0 for r in receivers)
    return {
        "object": "DISH-GROUND-SOURCE-POINT-A02", "seed": 11,
        "coordinate": coordinate.canonical_key(), "action_tick": int(observation.tick),
        "native_boundary": boundary, "expected_boundary": expected,
        "boundary_matches": boundary_matches,
        "result": "A02-ENDPOINT-CLEARANCE-WITNESS" if boundary_matches and witness else "A02-POINT-DISCREPANCY",
        "native_source_xy": source[:2], "declared_source_height": 0.0, "receivers": receivers,
        "derived_definition": {"ray_samples": "j=1..127, q=j/128",
                               "terrain": "135*exp(-(x/75)^2-(y/220)^4)+55*exp(-((x-90)/35)^2-((y+40)/85)^2)",
                               "terrain_y": "reflection * sample_y", "strict_clearance": "sample_z > terrain + clearance"},
        "margin_interpretation": "Native send-margin eligibility only; no packet reception observed.",
        "sample_interpretation": "Derived samples of the declared equation; not native exported ray flags.",
        "input_law": "seed_master(11), panel()[0], _reset_row; original normal-mode masks and addressed RNG",
        "new_exposure": {"models_initialized": 0, "policies_initialized": 0, "optimizers_initialized": 0,
                         "training_transitions": 0, "learner_updates": 0, "optimizer_steps": 0,
                         "prepared_native_points": 1, "completed_native_ticks": 0,
                         "parameter_displacement": None},
    }


def native_point():
    coordinate = study.panel()[0]
    native = backend.native_batch_from_rows((study._reset_row(study.seed_master(11), coordinate),))
    prepared = native.prepare_b01_tick()
    return backend._B01PreparedTick.from_buffer_copy(prepared.snapshot_bytes()), coordinate


def project_cost():
    return {"mode": "project-cost", "law": "1.5 * (5 + 5)", "projected_seconds": 15.0,
            "cap_seconds": CAP_SECONDS, "prepared_points": 1, "within_cap": 15.0 <= CAP_SECONDS}


def run(admission, output):
    started = time.perf_counter()
    point, coordinate = native_point()
    summary = read_point(point, coordinate)
    launch_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                                capture_output=True, text=True).stdout.strip()
    try:
        rss = _peak_rss_bytes()
    except OSError:
        rss = None
    wall = time.perf_counter() - started
    if wall >= CAP_SECONDS:
        raise RuntimeError("incomplete A02: 60-second cap exceeded")
    summary.update(launch_sha=launch_sha, admission_receipt=str(admission.resolve()),
                   wall_seconds=wall, peak_rss_bytes=rss, resources_unmeasured=rss is None,
                   measured_cost={"prepared_points": 1, "wall_seconds": wall, "seconds_per_point": wall})
    output.mkdir(parents=True)
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser()
    modes = parser.add_subparsers(dest="mode", required=True)
    modes.add_parser("project-cost")
    command = modes.add_parser("run")
    command.add_argument("--seed", type=int, choices=(11,), required=True)
    command.add_argument("--admission", type=Path, required=True)
    command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(project_cost() if args.mode == "project-cost" else run(args.admission, args.out), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
