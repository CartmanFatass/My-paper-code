#!/usr/bin/env python3
"""One fixed-only six-panel E01 evaluation; no fit or learner construction."""
import time
PROCESS_START = time.monotonic()
import os
for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[name] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import argparse
import json
from pathlib import Path
import signal
import sys
import traceback
import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.set_default_dtype(torch.float32)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.candidates.acvc.native_link_loss_b01.model import load_base
from experiments.candidates.acvc.native_link_loss_b01.learner import collect
from experiments.candidates.acvc.native_link_loss_b01.report import fixed_panel, write_json
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real


def run(output, checkpoints, launch_sha, process_start, execution_seconds,
        make_env=make_real, episodes=64, horizon=256):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    counts = dict(base_loads=0, environment_constructors=0, unscored_constructor_resets=0,
                  explicit_resets=0, step_calls=0, team_steps=0, eval_episodes=0,
                  base_agent_forwards=0, learned_gate_agent_forwards=0,
                  retained_base_fits=2, new_fits=0, training_episodes=0, training_team_steps=0, optimizer_updates=0,
                  gate_constructions=0, critic_constructions=0)
    summary = dict(object="ACVC_FIXED_RETRACE_REUSE_E01", launch_sha=launch_sha,
                   counts=counts, status="incomplete", panels=[], device="cpu", dtype="float32",
                   intraop_threads=torch.get_num_threads(), interop_threads=torch.get_num_interop_threads())
    rows = []
    def timeout(*_):
        raise TimeoutError("E01 remaining scientific-process allowance reached")
    def check():
        if time.monotonic() - process_start >= execution_seconds:
            timeout()
    old_handler = None
    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, timeout)
        signal.setitimer(signal.ITIMER_REAL, max(.001, execution_seconds - (time.monotonic() - process_start)))
    with (output / "episodes.jsonl").open("w", encoding="utf-8") as stream:
        try:
            for base_id, namespace in ((8201, 8911), (8202, 8912)):
                for arm, index in (("C", 2), ("F", 3), ("dwell", 4)):
                    check()
                    start = time.monotonic()
                    base = load_base(checkpoints[base_id], namespace)
                    counts["base_loads"] += 1
                    initial = {k: v.clone() for k, v in base.state_dict().items()}
                    env = make_env(namespace * 100000 + 60 + index)
                    counts["environment_constructors"] += 1
                    counts["unscored_constructor_resets"] += 1
                    def emit(row):
                        row.update(base=base_id, evaluation_namespace=namespace)
                        rows.append(row)
                        stream.write(json.dumps(row, allow_nan=False) + "\n")
                        stream.flush()
                    for e in range(episodes):
                        collect(env, base, None, None, namespace, arm, "eval", e, horizon, check, counts, emit)
                    movement = sum(float((v - initial[k]).double().square().sum()) for k, v in base.state_dict().items()) ** .5
                    summary["panels"].append(dict(base=base_id, arm=arm, episodes=episodes,
                        parameter_displacement_after_loading=movement, wall_s=time.monotonic() - start))
                    print(json.dumps(summary["panels"][-1]), flush=True)
            summary["primary_by_base"] = fixed_panel(rows)
            summary["status"] = "complete"
        except Exception as error:
            summary["error"] = f"{type(error).__name__}: {error}"
            summary["traceback"] = traceback.format_exc()
            print(summary["traceback"], flush=True)
        finally:
            if old_handler is not None:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, old_handler)
            summary["process_wall_s_to_summary"] = time.monotonic() - process_start
            summary["exposure_by_base_rule"] = [dict(base=b, arm=a, **{
                key: sum(r.get(key, 0) for r in rows if r["base"] == b and r["arm"] == a)
                for key in ("opportunities", "retrace", "dwell", "apply", "distinguishable")})
                for b in (8201, 8202) for a in ("C", "F", "dwell")]
            summary["intervention_count_scope"] = "Completed published episodes only; partial-episode transitions remain in team_steps."
            summary["parameter_displacement_during_evaluation"] = (
                max(p["parameter_displacement_after_loading"] for p in summary["panels"])
                if len(summary["panels"]) == 6 else None)
            summary["timing_boundary"] = "External process timing includes publication and actual exit; support billed separately."
            write_json(output / "summary.json", summary)
    return 0 if summary["status"] == "complete" else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, choices=[8911], default=8911,
                        help="First frozen namespace; second is8912")
    parser.add_argument("--checkpoint-8201", type=Path, required=True)
    parser.add_argument("--checkpoint-8202", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--execution-seconds", type=float, required=True)
    args = parser.parse_args()
    return run(args.output, {8201: args.checkpoint_8201, 8202: args.checkpoint_8202},
               args.launch_sha, PROCESS_START, args.execution_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
