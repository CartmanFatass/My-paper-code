"""Run one fixed Generic64 or raw last-sighting A01 fit."""

import time

START_WALL = time.monotonic()
START_CPU = time.process_time()

import argparse
import hashlib
import json
import math
from numbers import Real
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.hmasd_admission import require_admission


def _resource_snapshot(summary):
    summary["runner_wall_seconds"] = time.monotonic() - START_WALL
    summary["aggregate_cpu_seconds"] = time.process_time() - START_CPU
    summary["aggregate_cpu_scope"] = "single research process, user plus system CPU"
    try:
        import resource

        summary["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        summary["peak_rss_scope"] = "single research process ru_maxrss"
    except ImportError:
        summary["peak_rss_kib"] = None
        summary["peak_rss_scope"] = "unavailable on this platform"
        summary["resources_unmeasured"] = ["peak_rss_kib"]


def _write_summary(out, summary):
    encoded = json.dumps(summary, indent=2, allow_nan=False) + "\n"
    path = out / "summary.json"
    path.write_text(encoded)
    if json.loads(path.read_text()) != summary:
        raise IOError("summary publication/readback mismatch")


def _publish(out, summary):
    _resource_snapshot(summary)
    _write_summary(out, summary)


def _sanitize_failure(value, path, invalid_paths):
    if isinstance(value, dict):
        return {
            key: _sanitize_failure(item, f"{path}.{key}", invalid_paths)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            _sanitize_failure(item, f"{path}[{index}]", invalid_paths)
            for index, item in enumerate(value)
        ]
    if isinstance(value, Real) and not isinstance(value, (bool, int)):
        numeric = float(value)
        if not math.isfinite(numeric):
            invalid_paths.append(path)
            return None
        return numeric
    return value


def _publish_failure(out, summary):
    _resource_snapshot(summary)
    invalid_paths = []
    safe = _sanitize_failure(summary, "$", invalid_paths)
    safe["invalid_nonfinite_paths"] = invalid_paths
    _write_summary(out, safe)


def _movement(module, initial):
    return sum(
        (value.detach().double() - initial[name].double()).square().sum().item()
        for name, value in module.named_parameters()
    ) ** 0.5


def _lifecycle_add(total, row):
    for key, value in row.items():
        total[key] = total.get(key, 0) + int(value)


def _episode_transitions(episode):
    count = len(episode["reward"])
    if count != 20:
        raise RuntimeError(f"fixed H20 episode produced {count} transitions")
    return count


def _file_artifact(path, rows=None):
    result = {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }
    if rows is not None:
        result["rows"] = rows
    return result


def _source_hashes():
    root = Path(__file__).resolve().parents[1]
    paths = (
        Path(__file__).resolve(),
        root / "experiments/candidates/vap_folr_core/last_sighting_a01/model.py",
        root / "experiments/candidates/vap_folr_core/last_sighting_a01/learner.py",
        root / "experiments/candidates/vap_folr_core/last_sighting_a01/artifacts.py",
        root / "experiments/candidates/vap_folr_core/last_sighting_a01/publication.py",
        root / "experiments/candidates/vap_folr_core/entity_history_b01/model.py",
        root / "experiments/candidates/vap_folr_core/entity_history_b01/environment.py",
        root / "experiments/candidates/vap_folr_core/public_lifecycle_b01/collection.py",
        root / "experiments/candidates/vap_folr_core/public_lifecycle_b01/learner.py",
        root / "experiments/candidates/vap_folr_core/public_lifecycle_b01/flex_qmix.py",
    )
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def main():
    from experiments.candidates.vap_folr_core.last_sighting_a01.publication import (
        ARMS,
        EVALUATION_SEED,
        HORIZON,
        OBJECT,
        OPTIMIZER_STEPS,
        PANEL_EPISODES,
        TRAIN_EPISODES,
        TRAINING_SEEDS,
        arm_result,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--evaluation-seed", type=int, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seed not in TRAINING_SEEDS or args.evaluation_seed != EVALUATION_SEED:
        parser.error("seeds must match the fixed last-sighting A01 binding")

    # The guard precedes output creation and every environment, model and RNG effect.
    admission = require_admission(__file__, direction="vap_folr_core")
    if args.launch_sha != admission["sha"]:
        parser.error("--launch-sha must equal the admitted source SHA")

    args.out.mkdir(parents=True, exist_ok=True)
    progress_path = args.out / "training-progress.jsonl"
    summary = {
        "object": OBJECT,
        "arm": args.arm,
        "training_seed": args.seed,
        "evaluation_seed": args.evaluation_seed,
        "launch_sha": args.launch_sha,
        "source_hashes": _source_hashes(),
        "status": "incomplete",
        "training_identity_kind": "fresh_unscreened_fit",
        "training_episodes": 0,
        "training_transitions": 0,
        "optimizer_steps": 0,
        "evaluation_episodes": 0,
        "evaluation_transitions": 0,
        "evaluation_optimizer_steps": 0,
        "training_returns": [],
        "evaluation_returns": [],
        "training_lifecycle_counts": {},
        "evaluation_lifecycle_counts": {},
        "config": {
            "arms": list(ARMS),
            "selected_training_seeds": list(TRAINING_SEEDS),
            "training_episodes": TRAIN_EPISODES,
            "horizon": HORIZON,
            "optimizer_steps": OPTIMIZER_STEPS,
            "evaluation_episodes": PANEL_EPISODES,
            "evaluation_seed": EVALUATION_SEED,
            "environment": "EntityHistoryEnv(difficulty='easy', vision=1)",
            "learner": "native complete-episode double-Q FlexQMixer",
            "optimizer": "RMSprop(lr=.0005, alpha=.99, eps=.00001), norm 10",
            "gamma": 0.99,
            "target_update_episodes": 200,
            "cache": "per-observer 5x9 raw last visible physical/previous-action values",
            "torch_threads": [1, 1],
        },
    }
    _publish(args.out, summary)

    final_episodes = []
    try:
        import numpy as np
        import torch

        from experiments.candidates.vap_folr_core.entity_history_b01.environment import (
            EntityHistoryEnv,
        )
        from experiments.candidates.vap_folr_core.last_sighting_a01.artifacts import (
            write_panel,
        )
        from experiments.candidates.vap_folr_core.last_sighting_a01.learner import (
            Learner,
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
        initial_actor = {
            name: value.detach().clone() for name, value in actor.named_parameters()
        }
        initial_mixer = {
            name: value.detach().clone()
            for name, value in learner.mixer.named_parameters()
        }
        env = EntityHistoryEnv(difficulty="easy", vision=1, seed=args.seed)
        replay = []
        progress_rows = 0
        with progress_path.open("w", encoding="utf-8", newline="\n") as progress:
            for episode_num in range(1, TRAIN_EPISODES + 1):
                epsilon = epsilon_at(summary["training_transitions"])
                episode, score, counts = collect(env, actor, epsilon)
                transitions = _episode_transitions(episode)
                replay.append(episode)
                summary["training_returns"].append(score)
                summary["training_episodes"] += 1
                summary["training_transitions"] += transitions
                _lifecycle_add(summary["training_lifecycle_counts"], counts)

                loss = None
                if len(replay) >= 32:
                    loss = learner.update(sample(replay), episode_num)
                    summary["optimizer_steps"] = int(learner.updates)
                row = {
                    "episode": episode_num,
                    "transitions": transitions,
                    "return": score,
                    "epsilon": epsilon,
                    "optimizer_steps": int(learner.updates),
                    "update_loss": loss,
                }
                try:
                    encoded = json.dumps(row, allow_nan=False)
                except (TypeError, ValueError):
                    summary["invalid_progress_row"] = row
                    raise
                progress.write(encoded + "\n")
                progress_rows += 1
                if episode_num % 200 == 0:
                    progress.flush()
                    summary["training_progress"] = _file_artifact(
                        progress_path, progress_rows
                    )
                    _publish(args.out, summary)
                    print(
                        json.dumps(
                            {
                                "arm": args.arm,
                                "seed": args.seed,
                                "episode": episode_num,
                                "updates": learner.updates,
                                "wall_seconds": time.monotonic() - START_WALL,
                            }
                        ),
                        flush=True,
                    )

        summary["training_progress"] = _file_artifact(progress_path, progress_rows)
        if learner.updates != OPTIMIZER_STEPS:
            raise RuntimeError(
                f"fixed training produced {learner.updates} optimizer steps"
            )

        checkpoint = args.out / "final.pt"
        learner.save(checkpoint)
        summary["final_checkpoint"] = _file_artifact(checkpoint)
        summary["parameter_movement"] = {
            "actor_parameters": sum(value.numel() for value in actor.parameters()),
            "actor_initial_l2": sum(
                value.double().square().sum().item()
                for value in initial_actor.values()
            )
            ** 0.5,
            "actor_change_l2": _movement(actor, initial_actor),
            "mixer_parameters": sum(
                value.numel() for value in learner.mixer.parameters()
            ),
            "mixer_initial_l2": sum(
                value.double().square().sum().item()
                for value in initial_mixer.values()
            )
            ** 0.5,
            "mixer_change_l2": _movement(learner.mixer, initial_mixer),
        }

        actor.eval()
        updates_before_evaluation = learner.updates
        random.seed(args.evaluation_seed)
        np.random.seed(args.evaluation_seed)
        torch.manual_seed(args.evaluation_seed)
        env = EntityHistoryEnv(
            difficulty="easy", vision=1, seed=args.evaluation_seed
        )
        for _ in range(PANEL_EPISODES):
            episode, score, counts = collect(env, actor, 0.0)
            transitions = _episode_transitions(episode)
            final_episodes.append(episode)
            summary["evaluation_returns"].append(score)
            summary["evaluation_episodes"] += 1
            summary["evaluation_transitions"] += transitions
            _lifecycle_add(summary["evaluation_lifecycle_counts"], counts)

        summary["final_panel"] = write_panel(
            args.out / "final-panel.npz", final_episodes
        )
        summary["evaluation_optimizer_steps"] = (
            learner.updates - updates_before_evaluation
        )
        if summary["evaluation_optimizer_steps"] != 0:
            raise RuntimeError("final evaluation changed learner update count")
        summary["native_panel"] = arm_result(summary["evaluation_returns"])
        summary["mean_native_return"] = summary["native_panel"]["mean"]
        summary["status"] = "complete"
        summary["exposure"] = (
            "5000 H20 training episodes; 4969 native RMSprop actor/mixer steps; "
            "one final checkpoint; 128 final greedy H20 episodes; zero evaluation updates"
        )
        summary["rng"] = (
            "Fresh Python/global NumPy/Torch before construction and before the common "
            "final panel; both arms construct identical trainable actor/mixer state and "
            "consume the same constructor stream; each fit owns environment, replay, "
            "learner and targets; selector retains greedy/terminal Torch draws."
        )
        summary["torch_version"] = torch.__version__
        summary["numpy_version"] = np.__version__
        summary["torch_threads"] = [
            torch.get_num_threads(),
            torch.get_num_interop_threads(),
        ]
        _publish(args.out, summary)
    except BaseException as exc:
        active_learner = locals().get("learner")
        if active_learner is not None:
            summary["optimizer_steps"] = int(active_learner.updates)
        if progress_path.exists():
            summary["training_progress"] = _file_artifact(
                progress_path, locals().get("progress_rows", 0)
            )
        if final_episodes and "final_panel" not in summary:
            try:
                from experiments.candidates.vap_folr_core.last_sighting_a01.artifacts import (
                    write_panel,
                )

                summary["partial_final_panel"] = write_panel(
                    args.out / "final-panel.partial.npz", final_episodes
                )
            except BaseException as panel_exc:
                summary["partial_final_panel_error"] = (
                    type(panel_exc).__name__ + ": " + str(panel_exc)
                )
        summary["status"] = "incomplete"
        summary["failure_count_scope"] = (
            "Completed episodes, transitions and optimizer updates only."
        )
        summary["error"] = type(exc).__name__ + ": " + str(exc)
        _publish_failure(args.out, summary)
        raise

    print(
        json.dumps(
            {
                "arm": args.arm,
                "seed": args.seed,
                "status": summary["status"],
                "panel": summary["native_panel"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()

