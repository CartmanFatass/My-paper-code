"""Run the bounded nonformal G17 continuous-roster access screen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys
import time
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.continuous_roster_policy import ContinuousRosterPolicy
from ha_ctse_process.continuous_service_roster_proxy_g17 import (
    ACTION_DIM,
    CAPACITY,
    CRITIC_STATE_DIM,
    HELDOUT_PROFILES,
    HORIZON,
    OBSERVATION_DIM,
    TRAIN_PROFILES,
    ContinuousServiceRosterEnv,
    RosterProfile,
    collect_trajectory,
    constructive_actions,
    evaluate_policy,
    make_ledger,
    optimize_update,
)


SCHEMA = "continuous_service_roster_proxy_g17_screen_v1"
ALGORITHM = "CONTINUOUS_SERVICE_ROSTER_PROXY_G17"
MODEL_SEED = 171_000
TRAIN_LEDGER_SEED = 172_000
ACTION_SEED = 173_000
EVALUATION_LEDGER_SEED = 174_000
EVALUATION_ACTION_SEED = 175_000
HIDDEN_DIM = 32
LEARNING_RATE = 3e-4


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def configure_runtime(seed: int) -> None:
    random.seed(int(seed))
    np.random.seed(int(seed))
    torch.manual_seed(int(seed))
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


def _model(*, initial_log_std: float) -> ContinuousRosterPolicy:
    model = ContinuousRosterPolicy(
        OBSERVATION_DIM,
        CRITIC_STATE_DIM,
        member_capacity=CAPACITY,
        action_dim=ACTION_DIM,
        hidden_dim=HIDDEN_DIM,
    )
    with torch.no_grad():
        model.log_std.fill_(float(initial_log_std))
    return model


def _source_control() -> dict[str, Any]:
    values: list[float] = []
    profiles: Sequence[RosterProfile] = TRAIN_PROFILES + HELDOUT_PROFILES
    for episode_id in range(10):
        ledger = make_ledger(
            episode_id,
            master_seed=EVALUATION_LEDGER_SEED,
            profiles=profiles,
        )
        environment = ContinuousServiceRosterEnv(ledger)
        for _ in range(48):
            view = environment.observe()
            environment.step(constructive_actions(view))
        values.append(environment.outcome().utility)
    return {
        "episodes": len(values),
        "mean_utility": float(np.mean(values)),
        "minimum_utility": float(np.min(values)),
    }


def _evaluate(
    model: ContinuousRosterPolicy,
    *,
    profiles: Sequence[RosterProfile],
    eval_episodes: int,
) -> list[float]:
    outcomes = evaluate_policy(
        model,
        episode_ids=range(int(eval_episodes)),
        ledger_seed=EVALUATION_LEDGER_SEED,
        action_seed=EVALUATION_ACTION_SEED,
        device=torch.device("cpu"),
        profiles=profiles,
        deterministic=True,
    )
    return [float(outcome.utility) for outcome in outcomes]


def _mapping_diagnostic(
    model: ContinuousRosterPolicy,
    *,
    profiles: Sequence[RosterProfile],
    eval_episodes: int,
) -> dict[str, float]:
    environments = tuple(
        ContinuousServiceRosterEnv(
            make_ledger(
                episode_id,
                master_seed=EVALUATION_LEDGER_SEED,
                profiles=profiles,
            )
        )
        for episode_id in range(int(eval_episodes))
    )
    hidden = torch.zeros(
        (len(environments), CAPACITY, model.hidden_dim), dtype=torch.float32
    )
    target_effort: list[float] = []
    predicted_effort: list[float] = []
    target_mix: list[float] = []
    predicted_mix: list[float] = []
    model.eval()
    with torch.no_grad():
        for _ in range(HORIZON):
            views = tuple(environment.observe() for environment in environments)
            output = model.forward_step(
                observations=torch.as_tensor(
                    np.stack([view.observations for view in views])
                ),
                active_mask=torch.as_tensor(
                    np.stack([view.active_mask for view in views])
                ),
                critic_state=torch.as_tensor(
                    np.stack([view.critic_state for view in views])
                ),
                hidden=hidden,
                deterministic=True,
            )
            actions = output.actions.cpu().numpy()
            for env_index, (environment, view) in enumerate(
                zip(environments, views)
            ):
                active_actions = actions[env_index, view.active_mask]
                target_effort.append(view.load)
                target_mix.append(view.target_mix)
                predicted_effort.append(float(((active_actions[:, 0] + 1.0) / 2.0).mean()))
                predicted_mix.append(float(((active_actions[:, 1] + 1.0) / 2.0).mean()))
                environment.step(actions[env_index])
            hidden = output.next_hidden
    effort_target = np.asarray(target_effort)
    effort_prediction = np.asarray(predicted_effort)
    mix_target = np.asarray(target_mix)
    mix_prediction = np.asarray(predicted_mix)

    def correlation(left: np.ndarray, right: np.ndarray) -> float:
        if float(left.std()) == 0.0 or float(right.std()) == 0.0:
            return 0.0
        return float(np.corrcoef(left, right)[0, 1])

    return {
        "effort_mae": float(np.abs(effort_target - effort_prediction).mean()),
        "mix_mae": float(np.abs(mix_target - mix_prediction).mean()),
        "effort_correlation": correlation(effort_target, effort_prediction),
        "mix_correlation": correlation(mix_target, mix_prediction),
        "predicted_effort_std": float(effort_prediction.std()),
        "predicted_mix_std": float(mix_prediction.std()),
    }


def screen(
    *,
    run_root: Path,
    updates: int,
    num_envs: int,
    eval_episodes: int,
    ppo_passes: int,
    learning_rate: float = LEARNING_RATE,
    initial_log_std: float = 0.0,
) -> dict[str, Any]:
    if min(updates, num_envs, eval_episodes, ppo_passes) <= 0:
        raise ValueError("G17 screen counts must be positive")
    run_root.mkdir(parents=True, exist_ok=False)
    configure_runtime(MODEL_SEED)
    started = time.perf_counter()
    model = _model(initial_log_std=initial_log_std)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(learning_rate))
    zero_iid = _evaluate(model, profiles=TRAIN_PROFILES, eval_episodes=eval_episodes)
    zero_heldout = _evaluate(
        model, profiles=HELDOUT_PROFILES, eval_episodes=eval_episodes
    )
    maximum_errors = {
        name: 0.0
        for name in (
            "logp_max_error",
            "joint_logp_max_error",
            "value_max_error",
            "hidden_max_error",
            "prefix_max_error",
            "inactive_logp_max_abs",
        )
    }
    finite = True
    for update in range(int(updates)):
        first = update * int(num_envs)
        trajectory = collect_trajectory(
            model,
            episode_ids=range(first, first + int(num_envs)),
            ledger_seed=TRAIN_LEDGER_SEED,
            action_seed=ACTION_SEED,
            device=torch.device("cpu"),
        )
        metrics = optimize_update(
            model,
            optimizer,
            trajectory,
            device=torch.device("cpu"),
            ppo_passes=int(ppo_passes),
        )
        finite = finite and bool(metrics["finite_update"])
        for name in maximum_errors:
            maximum_errors[name] = max(maximum_errors[name], float(metrics[name]))
    final_iid = _evaluate(model, profiles=TRAIN_PROFILES, eval_episodes=eval_episodes)
    final_heldout = _evaluate(
        model, profiles=HELDOUT_PROFILES, eval_episodes=eval_episodes
    )
    zero_joint = np.asarray(zero_iid + zero_heldout, dtype=np.float64)
    final_joint = np.asarray(final_iid + final_heldout, dtype=np.float64)
    iid_mean = float(np.mean(final_iid))
    heldout_mean = float(np.mean(final_heldout))
    gain = float(final_joint.mean() - zero_joint.mean())
    source_control = _source_control()
    mapping = _mapping_diagnostic(
        model,
        profiles=TRAIN_PROFILES + HELDOUT_PROFILES,
        eval_episodes=min(int(eval_episodes), 16),
    )
    promising = bool(
        finite
        and max(maximum_errors.values()) <= 1e-6
        and source_control["minimum_utility"] >= 1.0 - 2e-7
        and iid_mean >= 0.80
        and heldout_mean >= 0.75
        and gain >= 0.08
    )
    result = {
        "schema": SCHEMA,
        "algorithm": ALGORITHM,
        "formal": False,
        "status": (
            "NONFORMAL_G17_PROMISING"
            if promising
            else "NONFORMAL_G17_NOT_PROMISING"
        ),
        "counts": {
            "updates": int(updates),
            "num_envs": int(num_envs),
            "eval_episodes_per_domain": int(eval_episodes),
            "ppo_passes": int(ppo_passes),
        },
        "runtime": {
            "backend": "cpu",
            "torch": str(torch.__version__),
            "torch_threads": int(torch.get_num_threads()),
            "python": str(Path(sys.executable).resolve()),
            "elapsed_seconds": float(time.perf_counter() - started),
        },
        "parameter_count": model.parameter_count,
        "optimizer": {
            "learning_rate": float(learning_rate),
            "initial_log_std": float(initial_log_std),
            "final_log_std": [float(value) for value in model.log_std.detach().cpu()],
        },
        "source_control": source_control,
        "maximum_replay_errors": maximum_errors,
        "finite_updates": bool(finite),
        "zero": {
            "iid_mean": float(np.mean(zero_iid)),
            "heldout_mean": float(np.mean(zero_heldout)),
            "joint_mean": float(zero_joint.mean()),
        },
        "final": {
            "iid_mean": iid_mean,
            "heldout_mean": heldout_mean,
            "joint_mean": float(final_joint.mean()),
            "minimum_episode": float(final_joint.min()),
        },
        "final_minus_zero_joint": gain,
        "mapping_diagnostic": mapping,
        "interpretation": (
            "bounded access signal only; not formal evidence and not UAV evidence"
        ),
    }
    torch.save(
        {
            "schema": SCHEMA,
            "algorithm": ALGORITHM,
            "formal": False,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "completed_updates": int(updates),
        },
        run_root / "final_checkpoint.pt",
    )
    _write_json(run_root / "screen_result.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--updates", type=int, default=60)
    parser.add_argument("--num-envs", type=int, default=8)
    parser.add_argument("--eval-episodes", type=int, default=48)
    parser.add_argument("--ppo-passes", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=LEARNING_RATE)
    parser.add_argument("--initial-log-std", type=float, default=0.0)
    arguments = parser.parse_args()
    result = screen(
        run_root=arguments.run_root,
        updates=arguments.updates,
        num_envs=arguments.num_envs,
        eval_episodes=arguments.eval_episodes,
        ppo_passes=arguments.ppo_passes,
        learning_rate=arguments.learning_rate,
        initial_log_std=arguments.initial_log_std,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
