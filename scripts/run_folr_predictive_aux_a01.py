"""Run one fixed DETACHED or COUPLED predictive-auxiliary A01 fit."""

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
    except ImportError:
        summary["peak_rss_kib"] = None
        summary["resources_unmeasured"] = ["peak_rss_kib on local Windows check"]


def _write_summary(out, summary):
    encoded = json.dumps(summary, indent=2, allow_nan=False) + "\n"
    path = out / "summary.json"
    path.write_text(encoded)
    if json.loads(path.read_text()) != summary:
        raise IOError("summary publication/readback mismatch")


def _publish(out, summary):
    """Publish only a fully JSON-finite live or complete summary."""
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
    """Retain incomplete evidence even when a scientific field is nonfinite."""
    _resource_snapshot(summary)
    invalid_paths = []
    safe_summary = _sanitize_failure(summary, "$", invalid_paths)
    safe_summary["invalid_nonfinite_paths"] = invalid_paths
    _write_summary(out, safe_summary)


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


def _sync_optimizer_counts(summary, learner):
    summary["native_optimizer_steps"] = int(learner.updates)
    summary["predictor_optimizer_steps"] = int(learner.predictor_updates)


def _source_hashes():
    root = Path(__file__).resolve().parents[1]
    paths = (
        Path(__file__).resolve(),
        root / "experiments/candidates/vap_folr_core/predictive_aux_a01/learner.py",
        root / "experiments/candidates/vap_folr_core/predictive_aux_a01/artifacts.py",
        root / "experiments/candidates/vap_folr_core/predictive_aux_a01/publication.py",
    )
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def main():
    from experiments.candidates.vap_folr_core.predictive_aux_a01.publication import (
        EVALUATION_SEED,
        OBJECT,
        PANEL_EPISODES,
        PROBE_SEED,
        TRAIN_EPISODES,
        TRAINING_SEED,
        arm_result,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("DETACHED", "COUPLED"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--evaluation-seed", type=int, required=True)
    parser.add_argument("--probe-seed", type=int, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if (args.seed, args.evaluation_seed, args.probe_seed) != (
        TRAINING_SEED, EVALUATION_SEED, PROBE_SEED
    ):
        parser.error("seeds must match the selected predictive auxiliary A01 binding")

    admission = require_admission(__file__, direction="vap_folr_core")
    if args.launch_sha != admission["sha"]:
        parser.error("--launch-sha must equal the admitted source SHA")

    args.out.mkdir(parents=True, exist_ok=True)
    summary = {
        "object": OBJECT,
        "arm": args.arm,
        "training_seed": args.seed,
        "evaluation_seed": args.evaluation_seed,
        "probe_seed": args.probe_seed,
        "launch_sha": args.launch_sha,
        "source_hashes": _source_hashes(),
        "status": "incomplete",
        "training_identity_kind": "fresh_unscreened_fit",
        "training_episodes": 0,
        "training_transitions": 0,
        "native_optimizer_steps": 0,
        "predictor_optimizer_steps": 0,
        "final_episodes": 0,
        "final_transitions": 0,
        "probe_episodes": 0,
        "probe_transitions": 0,
        "evaluation_optimizer_steps": 0,
        "training_returns": [],
        "final_returns": [],
        "probe_returns": [],
        "training_lifecycle_counts": {},
        "final_lifecycle_counts": {},
        "probe_lifecycle_counts": {},
        "config": {
            "training_episodes": TRAIN_EPISODES,
            "final_episodes": PANEL_EPISODES,
            "probe_episodes": PANEL_EPISODES,
            "horizon": 20,
            "prediction_window": 3,
            "prediction_steps": 18,
            "auxiliary_weight": 0.1 if args.arm == "COUPLED" else 0.0,
            "native_optimizer": "RMSprop(lr=.0005, alpha=.99, eps=.00001), norm 10",
            "predictor_optimizer": "RMSprop(lr=.0005, alpha=.99, eps=.00001), norm 10",
            "probe_epsilon": 1.0,
            "torch_threads": [1, 1],
        },
    }
    _publish(args.out, summary)
    try:
        import numpy as np
        import torch

        from experiments.candidates.vap_folr_core.entity_history_b01.environment import EntityHistoryEnv
        from experiments.candidates.vap_folr_core.predictive_aux_a01.artifacts import (
            aggregate_update_moments,
            write_panel,
        )
        from experiments.candidates.vap_folr_core.predictive_aux_a01.learner import Learner
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
        initial = {
            "actor": {name: value.detach().clone() for name, value in actor.named_parameters()},
            "mixer": {name: value.detach().clone() for name, value in learner.mixer.named_parameters()},
            "predictor": {
                name: value.detach().clone() for name, value in learner.predictor.named_parameters()
            },
        }
        env = EntityHistoryEnv(difficulty="easy", vision=1, seed=args.seed)
        replay, update_rows = [], []
        update_path = args.out / "training-updates.jsonl"
        with update_path.open("w", encoding="utf-8", newline="\n") as update_stream:
            for episode_num in range(1, TRAIN_EPISODES + 1):
                episode, score, counts = collect(
                    env, actor, epsilon_at(summary["training_transitions"])
                )
                replay.append(episode)
                summary["training_returns"].append(score)
                summary["training_episodes"] += 1
                summary["training_transitions"] += _episode_transitions(episode)
                _lifecycle_add(summary["training_lifecycle_counts"], counts)
                if len(replay) >= 32:
                    update_row = learner.update(sample(replay), episode_num)
                    _sync_optimizer_counts(summary, learner)
                    update_rows.append(update_row)
                    try:
                        encoded_update = json.dumps(update_row, allow_nan=False)
                    except (TypeError, ValueError):
                        summary["invalid_update_diagnostic"] = update_row
                        raise
                    update_stream.write(encoded_update + "\n")
                if episode_num % 200 == 0:
                    update_stream.flush()
                    _publish(args.out, summary)
                    print(
                        json.dumps(
                            {
                                "episode": episode_num,
                                "native_updates": summary["native_optimizer_steps"],
                                "predictor_updates": summary["predictor_optimizer_steps"],
                                "wall_seconds": time.monotonic() - START_WALL,
                            }
                        ),
                        flush=True,
                    )
        summary["training_update_artifact"] = {
            "path": str(update_path),
            "sha256": hashlib.sha256(update_path.read_bytes()).hexdigest(),
            "rows": len(update_rows),
        }

        checkpoint = args.out / "final.pt"
        learner.save(checkpoint)
        summary["final_checkpoint"] = str(checkpoint)
        summary["final_checkpoint_sha256"] = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        summary["parameter_movement"] = {
            "actor_initial_l2": sum(v.double().square().sum().item() for v in initial["actor"].values()) ** 0.5,
            "actor_change_l2": _movement(actor, initial["actor"]),
            "mixer_initial_l2": sum(v.double().square().sum().item() for v in initial["mixer"].values()) ** 0.5,
            "mixer_change_l2": _movement(learner.mixer, initial["mixer"]),
            "predictor_initial_l2": sum(v.double().square().sum().item() for v in initial["predictor"].values()) ** 0.5,
            "predictor_change_l2": _movement(learner.predictor, initial["predictor"]),
        }
        summary["training_prediction"] = aggregate_update_moments(update_rows)

        actor.eval()
        learner.predictor.eval()
        updates_before_evaluation = (learner.updates, learner.predictor_updates)

        random.seed(args.evaluation_seed)
        np.random.seed(args.evaluation_seed)
        torch.manual_seed(args.evaluation_seed)
        env = EntityHistoryEnv(difficulty="easy", vision=1, seed=args.evaluation_seed)
        final_episodes = []
        for _ in range(PANEL_EPISODES):
            episode, score, counts = collect(env, actor, 0.0)
            final_episodes.append(episode)
            summary["final_returns"].append(score)
            summary["final_episodes"] += 1
            summary["final_transitions"] += _episode_transitions(episode)
            _lifecycle_add(summary["final_lifecycle_counts"], counts)
        summary["final_panel"] = write_panel(
            args.out / "final-panel.npz", final_episodes, actor, learner.predictor
        )

        random.seed(args.probe_seed)
        np.random.seed(args.probe_seed)
        torch.manual_seed(args.probe_seed)
        env = EntityHistoryEnv(difficulty="easy", vision=1, seed=args.probe_seed)
        probe_episodes = []
        for _ in range(PANEL_EPISODES):
            episode, score, counts = collect(env, actor, 1.0)
            probe_episodes.append(episode)
            summary["probe_returns"].append(score)
            summary["probe_episodes"] += 1
            summary["probe_transitions"] += _episode_transitions(episode)
            _lifecycle_add(summary["probe_lifecycle_counts"], counts)
        summary["probe_panel"] = write_panel(
            args.out / "probe-panel.npz", probe_episodes, actor, learner.predictor
        )

        if (learner.updates, learner.predictor_updates) != updates_before_evaluation:
            raise RuntimeError("evaluation changed learner optimizer counts")
        summary["native_panel"] = arm_result(summary["final_returns"])
        summary["mean_native_return"] = summary["native_panel"]["mean"]
        summary["status"] = "complete"
        summary["exposure"] = (
            "5000 H20 training episodes; 4969 native and predictor RMSprop steps; "
            "one final checkpoint; 128 greedy and 128 epsilon-one H20 panels; "
            "zero evaluation updates"
        )
        summary["rng"] = (
            "Fresh Python/global NumPy/Torch at each bound phase; predictor construction uses "
            "fork_rng and does not move native construction RNG; each arm owns environment, replay, "
            "learner and optimizers; uniform probe retains fixed-width selector and terminal draws."
        )
        summary["torch_version"] = torch.__version__
        summary["numpy_version"] = np.__version__
        summary["torch_threads"] = [torch.get_num_threads(), torch.get_num_interop_threads()]
        _publish(args.out, summary)
    except BaseException as exc:
        active_learner = locals().get("learner")
        if active_learner is not None:
            _sync_optimizer_counts(summary, active_learner)
        summary["status"] = "incomplete"
        summary["failure_count_scope"] = "Completed episodes, transitions and updates only."
        summary["error"] = type(exc).__name__ + ": " + str(exc)
        _publish_failure(args.out, summary)
        raise
    print(
        json.dumps({"arm": args.arm, "status": summary["status"], "panel": summary["native_panel"]}),
        flush=True,
    )


if __name__ == "__main__":
    main()
