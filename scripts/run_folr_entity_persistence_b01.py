"""Fresh current-only or persistent fit for FOLR entity persistence B01."""

import time

START_WALL = time.monotonic()
START_CPU = time.process_time()

import argparse
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def publish(out, summary):
    summary["runner_wall_seconds"] = time.monotonic() - START_WALL
    summary["aggregate_cpu_seconds"] = time.process_time() - START_CPU
    summary["aggregate_cpu_scope"] = "single research process, user plus system CPU"
    try:
        import resource

        summary["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except ImportError:
        summary["peak_rss_kib"] = None
        summary["resources_unmeasured"] = ["peak_rss_kib on local Windows check"]
    encoded = json.dumps(summary, indent=2, allow_nan=False) + "\n"
    path = out / "summary.json"
    path.write_text(encoded)
    if json.loads(path.read_text()) != summary:
        raise IOError("summary publication/readback mismatch")


def main():
    from experiments.candidates.vap_folr_core.entity_persistence_b01.publication import (
        EVALUATION_SEED,
        OBJECT,
        TRAINING_SEED,
        arm_result,
        attach_primary,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--arm", choices=["AUGMENTED_CURRENT_ONLY", "AUGMENTED_PERSISTENT"], required=True
    )
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--evaluation-seed", type=int, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--current-only-summary", type=Path)
    args = parser.parse_args()
    if (args.seed, args.evaluation_seed) != (TRAINING_SEED, EVALUATION_SEED):
        parser.error("seeds must match the selected entity persistence B01 card")
    if args.arm == "AUGMENTED_CURRENT_ONLY" and args.current_only_summary is not None:
        parser.error("only the augmented arm consumes the collected current-only summary")

    args.out.mkdir(parents=True, exist_ok=True)
    summary = {
        "object": OBJECT,
        "arm": args.arm,
        "training_seed": args.seed,
        "evaluation_seed": args.evaluation_seed,
        "launch_sha": args.launch_sha,
        "status": "incomplete",
        "training_identity_kind": "fresh_unscreened_fit",
        "training_episodes": 0,
        "training_ticks": 0,
        "optimizer_steps": 0,
        "evaluation_episodes": 0,
        "evaluation_ticks": 0,
        "training_returns": [],
        "evaluation_returns": [],
    }
    try:
        import numpy as np
        import torch

        from experiments.candidates.vap_folr_core.entity_persistence_b01.learner import (
            Learner,
        )
        from experiments.candidates.vap_folr_core.entity_history_b01.environment import (
            EntityHistoryEnv,
        )
        from experiments.candidates.vap_folr_core.public_lifecycle_b01.collection import (
            collect,
            epsilon_at,
            sample,
        )

        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        random.seed(args.seed)
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
        learner = Learner(args.arm)
        actor = learner.actor
        initial = {name: value.detach().clone() for name, value in actor.named_parameters()}
        env = EntityHistoryEnv(difficulty="easy", vision=1, seed=args.seed)
        replay = []
        for episode_num in range(1, 5001):
            episode, score, _ = collect(
                env, actor, epsilon_at(summary["training_ticks"])
            )
            replay.append(episode)
            summary["training_returns"].append(score)
            summary["training_episodes"] += 1
            summary["training_ticks"] += 20
            if len(replay) >= 32:
                learner.update(sample(replay), episode_num)
                summary["optimizer_steps"] += 1
            if episode_num % 200 == 0:
                print(
                    json.dumps(
                        {
                            "episode": episode_num,
                            "updates": summary["optimizer_steps"],
                            "wall_seconds": time.monotonic() - START_WALL,
                        }
                    ),
                    flush=True,
                )

        checkpoint = args.out / "final.pt"
        learner.save(checkpoint)
        summary["final_checkpoint"] = str(checkpoint)
        summary["actor_initial_l2"] = sum(
            value.double().square().sum().item() for value in initial.values()
        ) ** 0.5
        summary["actor_change_l2"] = sum(
            (value.detach().double() - initial[name].double()).square().sum().item()
            for name, value in actor.named_parameters()
        ) ** 0.5
        summary["actor_parameters"] = sum(value.numel() for value in actor.parameters())

        actor.eval()
        random.seed(args.evaluation_seed)
        np.random.seed(args.evaluation_seed)
        torch.manual_seed(args.evaluation_seed)
        env = EntityHistoryEnv(
            difficulty="easy", vision=1, seed=args.evaluation_seed
        )
        for _ in range(128):
            _, score, _ = collect(env, actor, 0.0)
            summary["evaluation_returns"].append(score)
            summary["evaluation_episodes"] += 1
            summary["evaluation_ticks"] += 20

        summary["native_panel"] = arm_result(summary["evaluation_returns"])
        summary["mean_native_return"] = summary["native_panel"]["mean"]
        summary["status"] = "complete"
        summary["exposure"] = (
            "100000 native train ticks; 4969 RMSprop actor/mixer steps at "
            "lr=.0005; one final checkpoint; 128 final greedy episodes/2560 "
            "native ticks; no checkpoint selection"
        )
        summary["rng"] = (
            "Fresh Python/global NumPy/Torch before construction; complete "
            "actor and mixer initialization aligned across arms; each "
            "arm owns learner, targets and replay; native environment and replay "
            "share NumPy; selector retains greedy/terminal Torch draws; fresh "
            "evaluation reset; no claimed episode coupling."
        )
        summary["torch_version"] = torch.__version__
        summary["numpy_version"] = np.__version__
        summary["torch_threads"] = [
            torch.get_num_threads(),
            torch.get_num_interop_threads(),
        ]

        if args.arm == "AUGMENTED_PERSISTENT":
            current_only = None
            if args.current_only_summary is not None:
                try:
                    current_only = json.loads(args.current_only_summary.read_text())
                    summary["current_only_input"] = str(args.current_only_summary)
                except (OSError, json.JSONDecodeError) as exc:
                    summary["current_only_input"] = str(args.current_only_summary)
                    summary["pair_primary"] = None
                    summary["pair_primary_unavailable"] = (
                        f"Selected current-only endpoint is unreadable ({exc}); no A-minus-Z polarity."
                    )
            if "pair_primary" not in summary:
                attach_primary(summary, current_only)
        publish(args.out, summary)
    except BaseException as exc:
        summary["status"] = "incomplete"
        summary.pop("pair_primary", None)
        summary["failure_count_scope"] = (
            "Completed episodes/updates only; interrupted prefix unmeasured."
        )
        summary["error"] = type(exc).__name__ + ": " + str(exc)
        publish(args.out, summary)
        raise
    print(
        json.dumps(
            {
                "arm": args.arm,
                "status": summary["status"],
                "panel": summary["native_panel"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
