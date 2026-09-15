#!/usr/bin/env python3
"""One granted C or M original, or the offline comparison of its saved final panels."""
import time

PROCESS_START = time.monotonic()
import os

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
              "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[_name] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import argparse
import json
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.candidates.acvc.cluster_mappo_comparison_b01 import protocol as p


def execute_m(output, summary, emit, emit_update, progress):
    from experiments.candidates.acvc.cluster_mappo_comparison_b01 import mappo as m

    args, settings = m.configuration()
    summary["configuration"].update(settings)
    summary["upstream_sha"] = p.UPSTREAM_SHA
    policy, spaces = m.make_policy(args)
    summary["fit_started"] = True
    initial = m.parameter_snapshot(policy)
    trainer = m.R_MAPPO(args, policy, device=m.torch.device("cpu"))
    buffer = m.make_buffer(args, spaces)
    counts = summary["counts"]
    m.count_steps(policy.actor_optimizer, counts, "actor_optimizer_steps")
    m.count_steps(policy.critic_optimizer, counts, "critic_optimizer_steps")
    m.torch.manual_seed(100000 * p.MASTER + 141)
    envs = [p.make_cluster(100000 * p.MASTER + 1000 + lane) for lane in range(2)]
    counts["environment_constructors"] += 2
    counts["unscored_constructor_resets"] += 2
    for rollout in range(p.TRAIN_EPISODES // 2):
        m.fill_rollout(policy, buffer, envs, (2 * rollout, 2 * rollout + 1), counts, emit)
        # Both lanes are actual terminal episodes; no next-reset value is bootstrapped.
        buffer.compute_returns(m.np.zeros((2, 5, 1), dtype=m.np.float32), trainer.value_normalizer)
        trainer.prep_training()
        before = counts["optimizer_steps"]
        try:
            info = trainer.train(buffer)
        except Exception:
            summary["interrupted_update"] = dict(rollout=rollout,
                completed_adam_steps=counts["optimizer_steps"] - before,
                limitation="Pinned trainer returns averaged diagnostics only after all epochs.")
            raise
        counts["backward_calls"] += counts["optimizer_steps"] - before
        counts["replayed_actor_agent_steps"] += 4 * 2 * p.HORIZON * 5
        counts["critic_update_rows"] += 4 * 2 * p.HORIZON * 5
        emit_update(dict(rollout=rollout, episodes=[2 * rollout, 2 * rollout + 1],
                         record_unit="mean of four PPO minibatches",
                         **{key: float(value.detach().cpu()) if m.torch.is_tensor(value) else float(value)
                            for key, value in info.items()}))
        counts["rollouts"] += 1
        if (rollout + 1) % 16 == 0:
            progress()
    summary["fit_complete"] = True
    counts["new_fits"] += 1
    summary["exposure"] = m.parameter_exposure(initial, policy)
    path = output / "final.pt"
    m.torch.save(dict(actor=policy.actor.state_dict(), critic=policy.critic.state_dict(),
                      value_normalizer=trainer.value_normalizer.state_dict(), object=p.OBJECT,
                      master=p.MASTER, checkpoint_episode=p.TRAIN_EPISODES,
                      actor_optimizer_steps=counts["actor_optimizer_steps"],
                      critic_optimizer_steps=counts["critic_optimizer_steps"]), path)
    counts["final_checkpoints"] += 1
    summary["checkpoint"] = path.name
    checkpoint = m.torch.load(path, map_location="cpu", weights_only=True)
    policy.actor.load_state_dict(checkpoint["actor"])
    policy.critic.load_state_dict(checkpoint["critic"])
    trainer.value_normalizer.load_state_dict(checkpoint["value_normalizer"])
    counts["post_fit_loads"] += 1
    env = p.make_cluster(100000 * p.EVALUATION_NAMESPACE + 65)
    counts["environment_constructors"] += 1
    counts["unscored_constructor_resets"] += 1
    for episode in range(p.EVAL_EPISODES):
        m.evaluate(policy, env, episode, counts, emit)
    progress()


def run(output, arm, launch_sha, upstream_root=None):
    from scripts import run_acvc_fresh_dense_reuse_b01 as shared

    if upstream_root is not None:
        sys.path.insert(0, str(upstream_root))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    counts = shared._counts()
    summary = dict(object=p.OBJECT, card=p.CARD, arm=arm, master=p.MASTER,
                   evaluation_namespace=p.EVALUATION_NAMESPACE, launch_sha=launch_sha,
                   status="incomplete", fit_started=False, fit_complete=False, counts=counts, limits=[],
                   configuration=dict(horizon=p.HORIZON, training_episodes=p.TRAIN_EPISODES,
                     episodes_per_rollout=2, ppo_epochs_per_rollout=4, chunk=32,
                     checkpoint_episode=p.TRAIN_EPISODES, evaluation_panels=list(p.ARMS[arm]),
                     evaluation_episodes_per_panel=p.EVAL_EPISODES, device="cpu", dtype="float32",
                     intraop_threads=shared.torch.get_num_threads(), interop_threads=shared.torch.get_num_interop_threads()),
                   ordinary_plan_seconds=p.PLANS[arm], plan_is_cap=False,
                   cost_law=dict(training_team_ticks=p.TRAIN_EPISODES * p.HORIZON,
                     evaluation_team_ticks=len(p.ARMS[arm]) * p.EVAL_EPISODES * p.HORIZON,
                     rollouts=2048, PPO_minibatches=8192, optimizer_step_calls=8192 if arm == "C" else 16384,
                     actor_replayed_rows=20971520, critic_replayed_rows=4194304 if arm == "C" else 20971520,
                     snapshots=1, final_loads=len(p.ARMS[arm])))
    rows = []
    with (output / "episodes.jsonl").open("w", encoding="utf-8", newline="\n") as epfile, \
         (output / "updates.jsonl").open("w", encoding="utf-8", newline="\n") as upfile:
        def emit(row):
            row = dict(row, master=p.MASTER, evaluation_namespace=p.EVALUATION_NAMESPACE)
            if row["phase"] == "eval":
                row["checkpoint_episode"] = p.TRAIN_EPISODES
            rows.append(row)
            epfile.write(json.dumps(row, allow_nan=False) + "\n")
            epfile.flush()

        def emit_update(row):
            upfile.write(json.dumps(dict(row, master=p.MASTER, arm=arm), allow_nan=False) + "\n")
            upfile.flush()
            counts["update_records"] += 1

        def progress():
            print(json.dumps(dict(arm=arm, rollouts=counts["rollouts"], train_episodes=counts["train_episodes"],
                eval_episodes=counts["eval_episodes"], optimizer_steps=counts["optimizer_steps"],
                process_wall_s=time.monotonic() - PROCESS_START)), flush=True)

        try:
            if arm == "C":
                from experiments.candidates.acvc.cluster_mappo_comparison_b01.c_fit import execute
                execute(output, summary, emit, emit_update, progress)
            else:
                execute_m(output, summary, emit, emit_update, progress)
        except Exception as error:
            summary.update(error=f"{type(error).__name__}: {error}", traceback=traceback.format_exc())
            print(summary["traceback"], flush=True)
        finally:
            if "interrupted_update" in summary:
                counts["backward_calls"] = None
                counts["replayed_actor_agent_steps"] = None
                counts["critic_update_rows"] = None
            counts["backward_calls_lower_bound"] = counts["optimizer_steps"]
            actor_steps = counts["optimizer_steps"] if arm == "C" else counts.get("actor_optimizer_steps", 0)
            critic_steps = counts["optimizer_steps"] if arm == "C" else counts.get("critic_optimizer_steps", 0)
            counts["replayed_actor_agent_steps_lower_bound"] = actor_steps * 2 * p.HORIZON * 5
            counts["critic_update_rows_lower_bound"] = critic_steps * 2 * p.HORIZON * (1 if arm == "C" else 5)
            summary["panels"] = {a: p.panel(rows, a) for a in p.ARMS[arm]}
            summary["training_rows"] = sum(r["phase"] == "train" for r in rows)
            summary["evaluation_rows"] = sum(r["phase"] == "eval" for r in rows)
            summary["interventions"] = {a: {k: sum(r.get(k, 0) for r in rows if r["phase"] == "eval" and r["arm"] == a)
                for k in ("opportunities", "retrace", "dwell", "apply", "distinguishable")} for a in p.ARMS[arm]}
            if p.fit_eligible(summary, arm) and all(v["complete"] for v in summary["panels"].values()):
                summary["status"] = "complete"
            summary["process_wall_s_to_summary"] = time.monotonic() - PROCESS_START
            summary["timing_boundary"] = "Before imports through pre-serialization; external GNU time encloses actual exit."
            shared.write_json(output / "summary.json", shared.clean_json(summary, summary["limits"]))
    return 0 if summary["status"] == "complete" else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["run", "reduce"], default="run")
    parser.add_argument("--seed", type=int, choices=[p.MASTER], default=p.MASTER)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--arm", choices=["C", "M"])
    parser.add_argument("--launch-sha")
    parser.add_argument("--on-policy-root", type=Path)
    parser.add_argument("--c-summary", type=Path)
    parser.add_argument("--m-summary", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "reduce":
        summaries = {arm: json.loads(path.read_text(encoding="utf-8")) if path else None
                     for arm, path in (("C", args.c_summary), ("M", args.m_summary))}
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "summary.json").write_text(json.dumps(p.reduce_pair(summaries), indent=2,
                                                            allow_nan=False) + "\n", encoding="utf-8")
        return 0
    if not args.arm or not args.launch_sha or (args.arm == "M" and not args.on_policy_root):
        parser.error("run needs --arm and --launch-sha; M additionally needs --on-policy-root")
    return run(args.output, args.arm, args.launch_sha, args.on_policy_root)


if __name__ == "__main__":
    raise SystemExit(main())
