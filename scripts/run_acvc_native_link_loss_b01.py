#!/usr/bin/env python3
"""The single P78 T/G/C/F native comparison; synthetic injection is test-only."""
import time
PROCESS_START = time.monotonic()

import os
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[_name] = "1"
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.acvc.native_link_loss_b01.model import load_base, build_learned, snapshot, displacement
from experiments.candidates.acvc.native_link_loss_b01.learner import collect, update, optimizer_for
from experiments.candidates.acvc.native_link_loss_b01.report import panel, write_json


def run(output, checkpoint, seed, check_wall, process_start, launch_sha,
        make_env=make_real, train_episodes=512, horizon=256, eval_episodes=32):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    counts = dict(environment_constructors=0, unscored_constructor_resets=0, explicit_resets=0,
                  step_calls=0, team_steps=0, train_episodes=0, eval_episodes=0,
                  optimizer_steps=0, rollouts=0, base_agent_forwards=0, learned_gate_agent_forwards=0)
    summary = dict(object="ACVC-NATIVE-LINK-LOSS-B01", seed=seed, launch_sha=launch_sha,
                   status="incomplete", counts=counts, focused_check_wall_s=check_wall,
                   device="cpu", dtype="float32", torch_threads=torch.get_num_threads(),
                   torch_interop_threads=torch.get_num_interop_threads(), exposure={}, arm_own_wall_s={})
    rows = []
    learned_times = summary["arm_own_wall_s"]
    shared_start = time.monotonic()
    shared_wall = check_wall + shared_start - process_start
    current_arm = None
    arm_start = None

    def deadline_seconds():
        now = time.monotonic()
        elapsed = now - process_start
        shared = shared_wall if current_arm in ("T", "G") else shared_wall + now - shared_start
        arm_bills = [shared + v for v in learned_times.values()]
        if current_arm in ("T", "G"):
            arm_bills.append(shared + now - arm_start)
        return min(3600 - check_wall - elapsed, 1800 - max(arm_bills, default=shared))

    def check():
        remaining = deadline_seconds()
        if remaining <= 0:
            raise TimeoutError("P78 complete arm or logical study cap reached")
        if hasattr(signal, "setitimer"):
            signal.setitimer(signal.ITIMER_REAL, remaining)

    def timeout(_signum, _frame):
        raise TimeoutError("P78 wall deadline reached")

    previous_handler = signal.signal(signal.SIGALRM, timeout) if hasattr(signal, "SIGALRM") else None
    with (output / "episodes.jsonl").open("w", encoding="utf-8") as episode_file, (output / "updates.jsonl").open("w", encoding="utf-8") as update_file:
        def emit(row):
            rows.append(row)
            episode_file.write(json.dumps(row, allow_nan=False) + "\n")
            episode_file.flush()

        try:
            check()
            for arm in ("T", "G", "C", "F"):
                if arm in ("T", "G"):
                    shared_wall += time.monotonic() - shared_start
                    arm_start = time.monotonic()
                current_arm = arm
                check()
                base = load_base(checkpoint, seed)
                env = make_env(seed * 100000 + 900)
                counts["environment_constructors"] += 1
                counts["unscored_constructor_resets"] += 1
                gate, critic = build_learned(seed, arm) if arm in ("T", "G") else (None, None)
                if gate is not None:
                    initial = snapshot(gate, critic)
                    optimizer = optimizer_for(gate, critic)
                    for rollout in range(train_episodes // 2):
                        episodes = [collect(env, base, gate, critic, seed, arm, "train", rollout * 2 + e,
                                            horizon, check, counts, emit) for e in range(2)]
                        records = update(gate, critic, optimizer, episodes, check, counts)
                        counts["rollouts"] += 1
                        update_file.write(json.dumps(dict(arm=arm, rollout=rollout, updates=records), allow_nan=False) + "\n")
                        update_file.flush()
                        if (rollout + 1) % 16 == 0:
                            print(json.dumps(dict(arm=arm, rollouts=rollout + 1, team_steps=counts["team_steps"], process_wall_s=time.monotonic() - process_start)), flush=True)
                for episode in range(eval_episodes):
                    collect(env, base, gate, critic, seed, arm, "eval", episode,
                            horizon, check, counts, emit)
                if gate is not None:
                    summary["exposure"][arm] = displacement(initial, gate, critic)
                    torch.save(dict(gate=gate.state_dict(), critic=critic.state_dict(), arm=arm, seed=seed), output / f"final_{arm}.pt")
                    learned_times[arm] = time.monotonic() - arm_start
                    shared_start = time.monotonic()
                print(json.dumps(dict(completed_arm=arm, team_steps=counts["team_steps"], process_wall_s=time.monotonic() - process_start)), flush=True)
            current_arm = None
            summary["primary"] = panel(rows)
            summary["gate_decisions"] = {
                arm: {phase: {key: sum(r[key] for r in rows if r["arm"] == arm and r["phase"] == phase)
                              for key in ("opportunities", "apply", "retrace", "distinguishable")}
                      for phase in ("train", "eval")} for arm in ("T", "G", "C", "F")}
            check()
            summary["status"] = "complete"
        except Exception as error:
            summary["error"] = f"{type(error).__name__}: {error}"
            summary["traceback"] = traceback.format_exc()
            print(summary["traceback"], flush=True)
        finally:
            if hasattr(signal, "setitimer"):
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous_handler)
            if current_arm in ("T", "G") and current_arm not in learned_times:
                learned_times[current_arm] = time.monotonic() - arm_start
            shared_total = check_wall + time.monotonic() - process_start - sum(learned_times.values())
            summary["shared_wall_s_to_summary"] = shared_total
            summary["complete_arm_bill_s_to_summary"] = {a: shared_total + t for a, t in learned_times.items()}
            summary["process_wall_s_to_summary"] = time.monotonic() - process_start
            summary["logical_study_wall_s_to_summary"] = check_wall + summary["process_wall_s_to_summary"]
            summary["timing_boundary"] = "Through summary construction; supervisor/process timing supplies publication and actual exit tail. Shared work conservatively charged to both learned arms."
            write_json(output / "summary.json", summary)
    return 0 if summary["status"] == "complete" else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, choices=[8901], default=8901)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--focused-check-wall-s", type=float, required=True)
    args = parser.parse_args()
    return run(args.output, args.checkpoint, args.seed, args.focused_check_wall_s, PROCESS_START, args.launch_sha)


if __name__ == "__main__":
    raise SystemExit(main())
