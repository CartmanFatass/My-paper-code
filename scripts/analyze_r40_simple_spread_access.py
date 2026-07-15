"""Decide the registered R40 simple_spread cooperative-access gate."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
import pettingzoo
from pettingzoo.mpe import simple_spread_v3


EXPERIMENT_ID = "EXP-20260715-r40-simple-spread-access"
CONFIG_MODULE = "ha_ctse_process.config_r40_simple_spread"
SCENARIO = "simple_spread"
TRAIN_SEED = 40_041
EVAL_BLOCKS = (40_042, 40_043, 40_044, 40_045)
EPISODES_PER_BLOCK = 64
TOTAL_EPISODES = len(EVAL_BLOCKS) * EPISODES_PER_BLOCK
TOTAL_TIMESTEPS = 200_000
EXPECTED_UPDATES = 500
ACTION_RNG_SEED = 50_041
BOOTSTRAP_REPETITIONS = 10_000
BOOTSTRAP_SEED = 60_041
RETURN_FLOOR = -35.0
PAIRED_EFFECT_FLOOR = 5.0


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return payload


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def number(row: dict[str, str], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"missing/non-numeric {field!r}") from exc
    if not math.isfinite(value):
        raise ValueError(f"non-finite {field!r}")
    return value


def paired_bootstrap(values: np.ndarray) -> dict[str, float]:
    if values.shape != (TOTAL_EPISODES,) or not np.all(np.isfinite(values)):
        raise ValueError("paired bootstrap requires 256 finite differences")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = rng.integers(
        0,
        values.size,
        size=(BOOTSTRAP_REPETITIONS, values.size),
    )
    means = values[draws].mean(axis=1)
    return {
        "mean": float(values.mean()),
        "lower_95": float(np.quantile(means, 0.025)),
        "upper_95": float(np.quantile(means, 0.975)),
    }


def expected_reset_seeds() -> list[int]:
    return [
        block * 1000 + episode
        for block in EVAL_BLOCKS
        for episode in range(EPISODES_PER_BLOCK)
    ]


def run_random_reference(result_root: Path) -> list[dict[str, float]]:
    rng = np.random.default_rng(ACTION_RNG_SEED)
    rows: list[dict[str, float]] = []
    for episode_index, reset_seed in enumerate(expected_reset_seeds()):
        env = simple_spread_v3.parallel_env(
            N=3,
            local_ratio=0.0,
            max_cycles=25,
            continuous_actions=False,
        )
        env.reset(seed=reset_seed)
        episode_return = 0.0
        episode_length = 0
        while env.agents:
            actions = {
                agent: int(rng.integers(5))
                for agent in env.agents
            }
            _, rewards, _, _, _ = env.step(actions)
            episode_return += float(np.mean(list(rewards.values())))
            episode_length += 1
        env.close()
        rows.append(
            {
                "episode": episode_index,
                "reset_seed": reset_seed,
                "reward": episode_return,
                "length": episode_length,
            }
        )
    path = result_root / "uniform_random_eval.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def validate_manifest(manifest: dict, reasons: list[str]) -> None:
    expected_args = {
        "config": CONFIG_MODULE,
        "scenario": SCENARIO,
        "seed": TRAIN_SEED,
        "total_timesteps": TOTAL_TIMESTEPS,
        "rollout_length": 25,
        "skill_interval": 25,
        "num_envs": 16,
        "n_agents": 3,
        "collector_backend": "subproc",
        "collector_start_method": "spawn",
        "device": "cuda",
        "eval_interval": TOTAL_TIMESTEPS,
        "eval_episodes": TOTAL_EPISODES,
        "eval_max_steps": 25,
        "eval_action_mode": "stochastic",
        "eval_seed_blocks": ",".join(str(value) for value in EVAL_BLOCKS),
        "eval_episodes_per_seed": EPISODES_PER_BLOCK,
    }
    args = manifest.get("args", {})
    for field, expected in expected_args.items():
        if args.get(field) != expected:
            reasons.append(
                f"manifest args.{field}={args.get(field)!r}, expected {expected!r}"
            )

    if manifest.get("mode") != "train":
        reasons.append("manifest mode is not train")
    if manifest.get("total_steps") != TOTAL_TIMESTEPS:
        reasons.append("manifest total_steps mismatch")
    if manifest.get("update_idx") != EXPECTED_UPDATES:
        reasons.append("manifest update_idx mismatch")

    expected_sections = {
        "algorithm_config": {
            "algorithm": "r40_simple_spread_constant_code_recurrent_mappo",
            "constant_skill_no_high": True,
            "low_ppo_epochs": 5,
            "low_sequence_length": 25,
            "low_sequence_batch_size": 64,
            "lr_discoverer_actor": 3e-4,
            "lr_discoverer_critic": 3e-4,
            "low_value_loss_coef": 0.5,
            "low_gae_lambda": 0.95,
        },
        "training_config": {
            "low_ppo_epochs": 5,
            "low_sequence_length": 25,
            "low_sequence_batch_size": 64,
            "low_value_loss_coef": 0.5,
            "low_entropy_coef": 0.01,
            "gamma": 0.99,
            "low_gae_lambda": 0.95,
        },
        "model_config": {
            "n_agents": 3,
            "state_dim": 54,
            "obs_dim": 18,
            "action_dim": 5,
        },
        "physical_env_config": {
            "scenario": SCENARIO,
            "n_agents": 3,
        },
        "env_runtime_spec": {
            "state_dim": 54,
            "obs_dim": 18,
            "action_dim": 5,
        },
        "agent_runtime_spec": {
            "n_agents": 3,
            "obs_dim": 18,
            "action_dim": 5,
            "action_space_type": "discrete",
            "constant_skill_no_high": True,
        },
    }
    for section, expected_values in expected_sections.items():
        actual = manifest.get(section, {})
        for field, expected in expected_values.items():
            actual_value = actual.get(field)
            if isinstance(expected, float):
                valid = math.isclose(
                    float(actual_value), expected, rel_tol=1e-12, abs_tol=1e-12
                ) if actual_value is not None else False
            else:
                valid = actual_value == expected
            if not valid:
                reasons.append(
                    f"manifest {section}.{field}={actual_value!r}, expected {expected!r}"
                )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    args = parser.parse_args()

    run_root = Path(args.run_root).resolve()
    train_root = run_root / "runs" / "mappo" / "seed40041"
    result_root = run_root / "result"
    result_root.mkdir(parents=True, exist_ok=True)
    result_path = result_root / "r40_simple_spread_access.json"
    manifest_path = train_root / "metadata" / "run_manifest.json"
    updates_path = train_root / "metrics" / "train_updates.csv"
    eval_path = train_root / "metrics" / "eval_episodes.csv"
    checkpoint_path = train_root / "standalone_process_core_final.pt"

    reasons: list[str] = []
    manifest = load_json(manifest_path)
    updates = load_csv(updates_path)
    eval_rows = load_csv(eval_path)
    validate_manifest(manifest, reasons)

    if str(pettingzoo.__version__) != "1.24.3":
        reasons.append(f"PettingZoo version={pettingzoo.__version__}, expected 1.24.3")
    if not checkpoint_path.is_file():
        reasons.append("exact final checkpoint is missing")

    if len(updates) != EXPECTED_UPDATES:
        reasons.append(f"train update rows={len(updates)}, expected 500")
    else:
        update_ids = [int(number(row, "update")) for row in updates]
        step_ids = [int(number(row, "total_steps")) for row in updates]
        if update_ids != list(range(1, EXPECTED_UPDATES + 1)):
            reasons.append("train update indices are not exactly 1..500")
        if step_ids[-1] != TOTAL_TIMESTEPS:
            reasons.append("final training step is not 200000")

    selected_finite_fields = (
        "low_loss",
        "low_policy_loss",
        "low_value_loss",
        "low_entropy",
        "low_actor_grad_norm",
        "low_critic_grad_norm",
        "low_optimizer_steps",
        "low_replay_logp_max_error",
        "high_optimizer_steps",
        "process_segments",
        "r31_effect_windows",
        "aem_active",
        "r28_g1_active",
        "r29_action_info_active",
        "team_disc_active",
        "proto_disc_active",
        "effect_windows",
    )
    numeric_updates: dict[str, list[float]] = {}
    for field in selected_finite_fields:
        try:
            numeric_updates[field] = [number(row, field) for row in updates]
        except ValueError as exc:
            reasons.append(str(exc))

    replay_values = numeric_updates.get("low_replay_logp_max_error")
    if replay_values is not None:
        replay_max = max(replay_values, default=math.inf)
        if replay_max > 1e-6:
            reasons.append(f"low replay max error={replay_max} exceeds 1e-6")

    optimizer_values = numeric_updates.get("low_optimizer_steps")
    if optimizer_values is not None:
        if sum(optimizer_values) != 2_500:
            reasons.append("low optimizer exposure is not exactly 2500 steps")

    actor_grad_values = numeric_updates.get("low_actor_grad_norm")
    if actor_grad_values is not None:
        if max(actor_grad_values, default=0.0) <= 0.0:
            reasons.append("low actor never received a positive finite gradient")

    critic_grad_values = numeric_updates.get("low_critic_grad_norm")
    if critic_grad_values is not None:
        if max(critic_grad_values, default=0.0) <= 0.0:
            reasons.append("low critic never received a positive finite gradient")

    zero_fields = (
        "high_optimizer_steps",
        "process_segments",
        "r31_effect_windows",
        "aem_active",
        "r28_g1_active",
        "r29_action_info_active",
        "team_disc_active",
        "proto_disc_active",
        "effect_windows",
    )
    for field in zero_fields:
        values = numeric_updates.get(field)
        if values is not None and any(abs(value) > 1e-12 for value in values):
            reasons.append(f"forbidden field {field} was nonzero")

    expected_seeds = expected_reset_seeds()
    if len(eval_rows) != TOTAL_EPISODES:
        reasons.append(f"MAPPO eval rows={len(eval_rows)}, expected 256")
    else:
        observed_seeds = [int(number(row, "reset_seed")) for row in eval_rows]
        if observed_seeds != expected_seeds:
            reasons.append("MAPPO evaluation reset seeds do not match the four fixed blocks")
        if any(int(number(row, "length")) != 25 for row in eval_rows):
            reasons.append("MAPPO evaluation contains a non-25-step episode")
        if any(number(row, "action_mode_code") != 1.0 for row in eval_rows):
            reasons.append("MAPPO evaluation was not stochastic")

    random_rows = run_random_reference(result_root)
    mappo_returns = np.asarray(
        [number(row, "reward") for row in eval_rows], dtype=np.float64
    ) if len(eval_rows) == TOTAL_EPISODES else np.full(TOTAL_EPISODES, np.nan)
    random_returns = np.asarray(
        [float(row["reward"]) for row in random_rows], dtype=np.float64
    )
    paired = paired_bootstrap(mappo_returns - random_returns)
    block_means = [
        float(mappo_returns[index * 64 : (index + 1) * 64].mean())
        for index in range(4)
    ]
    mappo_mean = float(mappo_returns.mean())
    random_mean = float(random_returns.mean())

    m0 = not reasons
    m1 = bool(
        m0
        and mappo_mean >= RETURN_FLOOR
        and paired["lower_95"] > PAIRED_EFFECT_FLOOR
    )
    m2 = bool(m0 and sum(value > RETURN_FLOOR for value in block_means) >= 3)
    if not m0:
        status = "INVALID_R40_IMPLEMENTATION"
        next_action = "repair only the concrete implementation defect and rerun the unchanged contract"
    elif m1 and m2:
        status = "PASS_R40_SIMPLE_SPREAD_ACCESS"
        next_action = "register only native fixed-k HMASD on the exact same substrate"
    else:
        status = "VALID_FAIL_R40_ACCESS"
        next_action = "retire simple_spread under this MAPPO contract without rescue"

    result = {
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "implementation_valid": m0,
        "contract": {
            "pettingzoo_version": str(pettingzoo.__version__),
            "scenario": "simple_spread_v3",
            "n_agents": 3,
            "horizon": 25,
            "local_ratio": 0.0,
            "continuous_actions": False,
            "action_space": "Discrete(5)",
            "train_seed": TRAIN_SEED,
            "num_envs": 16,
            "rollout_length": 25,
            "total_timesteps": TOTAL_TIMESTEPS,
            "outer_updates": EXPECTED_UPDATES,
            "ppo_epochs": 5,
            "eval_seed_blocks": list(EVAL_BLOCKS),
            "episodes_per_block": EPISODES_PER_BLOCK,
            "random_action_rng_seed": ACTION_RNG_SEED,
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "gates": {
            "M0": {"passed": m0, "reasons": reasons},
            "M1": {
                "passed": m1,
                "mappo_mean_return": mappo_mean,
                "return_floor": RETURN_FLOOR,
                "random_mean_return": random_mean,
                "paired_difference_ci": paired,
                "paired_lower_floor": PAIRED_EFFECT_FLOOR,
            },
            "M2": {
                "passed": m2,
                "block_means": block_means,
                "blocks_above_floor": int(sum(value > RETURN_FLOOR for value in block_means)),
                "required_blocks": 3,
            },
        },
        "training": {
            "update_rows": len(updates),
            "final_total_steps": manifest.get("total_steps"),
            "final_update_idx": manifest.get("update_idx"),
            "low_optimizer_steps_total": float(
                sum(numeric_updates.get("low_optimizer_steps", []))
            ),
            "low_replay_logp_max_error": float(
                max(numeric_updates.get("low_replay_logp_max_error", [math.inf]))
            ),
            "high_optimizer_steps_total": float(
                sum(numeric_updates.get("high_optimizer_steps", []))
            ),
        },
        "artifacts": {
            "manifest": str(manifest_path),
            "train_updates": str(updates_path),
            "mappo_eval": str(eval_path),
            "random_eval": str(result_root / "uniform_random_eval.csv"),
            "final_checkpoint": str(checkpoint_path),
        },
        "next_action": next_action,
    }
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
