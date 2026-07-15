"""Read-only counterfactual context diagnostic for the R39 toy high policy."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch  # noqa: E402

from ha_ctse_process import train as train_mod  # noqa: E402
from ha_ctse_process.r33_interventional_roster_complementarity import (  # noqa: E402
    enumerate_final_rosters,
    exact_roster_probabilities,
)
from ha_ctse_process.r30_fixed_clock import SET_TOKEN  # noqa: E402


ROSTERS = enumerate_final_rosters(4, 2)
PREV_SKILLS = np.asarray([0, 2], dtype=np.int64)
PREV_AGES = np.asarray([5, 5], dtype=np.int64)
PREV_ACTIVE = np.asarray([True, True], dtype=np.bool_)


def _load_agent(config_name: str, checkpoint: Path, device: str):
    module = importlib.import_module(config_name)
    config = module.Config()
    env = train_mod.create_env(
        config,
        scenario=str(config.scenario),
        seed=39041,
        rank=0,
        scale_mode="eval",
    )
    agent = train_mod.create_agent(
        config,
        argparse.Namespace(device=device),
        env,
        num_envs=1,
        state_dim=int(env.state_dim),
    )
    total_steps, update_idx = train_mod.load_checkpoint(
        checkpoint.resolve(), agent, load_optimizers=False
    )
    for value in vars(agent).values():
        if isinstance(value, torch.nn.Module):
            value.eval()
    return env, agent, int(total_steps), int(update_idx)


def _distribution(agent, slow_sign: int, fast_sign: int) -> np.ndarray:
    state = np.asarray(
        [float(slow_sign), 0.0, 0.0, float(fast_sign), 0.0, 0.0],
        dtype=np.float32,
    )
    joint_obs = np.zeros((2, 4), dtype=np.float32)
    with torch.no_grad():
        values = agent._r30_context_tensors(state, joint_obs)
        kwargs = {
            "joint_obs": values[1].squeeze(0),
            "compact": values[2],
            "team_vector": values[4],
            "prev_skills": torch.as_tensor(
                PREV_SKILLS, dtype=torch.long, device=agent.device
            ),
            "prev_ages": torch.as_tensor(
                PREV_AGES, dtype=torch.long, device=agent.device
            ),
            "prev_active": torch.as_tensor(
                PREV_ACTIVE, dtype=torch.bool, device=agent.device
            ),
            "agent_order": torch.arange(2, dtype=torch.long, device=agent.device),
        }
        if not agent.high.force_refresh_every_check:
            probabilities = exact_roster_probabilities(
                agent.high, **kwargs, final_rosters=ROSTERS
            )
        else:
            log_probabilities = []
            for roster in ROSTERS:
                token_logp, _ = agent.high.evaluate_sequence(
                    **kwargs,
                    token_kind=torch.full(
                        (2,), SET_TOKEN, dtype=torch.long, device=agent.device
                    ),
                    set_skill=torch.as_tensor(
                        roster, dtype=torch.long, device=agent.device
                    ),
                )
                log_probabilities.append(token_logp.sum())
            probabilities = torch.exp(torch.stack(log_probabilities))
    return probabilities.detach().cpu().numpy().astype(np.float64)


def _tv(left: np.ndarray, right: np.ndarray) -> float:
    return float(0.5 * np.abs(left - right).sum())


def _summarize_arm(config_name: str, checkpoint: Path, device: str) -> dict:
    env, agent, total_steps, update_idx = _load_agent(
        config_name, checkpoint, device
    )
    try:
        distributions: dict[tuple[int, int], np.ndarray] = {}
        contexts: dict[str, dict] = {}
        for slow_sign in (-1, 1):
            for fast_sign in (-1, 1):
                key = (slow_sign, fast_sign)
                probabilities = _distribution(agent, *key)
                if not np.isclose(probabilities.sum(), 1.0, atol=1e-6):
                    raise RuntimeError(
                        f"roster probabilities sum to {probabilities.sum()} for {key}"
                    )
                distributions[key] = probabilities
                slow_skill = 0 if slow_sign > 0 else 1
                fast_skill = 2 if fast_sign > 0 else 3
                correct = np.all(ROSTERS == (slow_skill, fast_skill), axis=1) | np.all(
                    ROSTERS == (fast_skill, slow_skill), axis=1
                )
                best = int(np.argmax(probabilities))
                contexts[f"slow_{slow_sign:+d}_fast_{fast_sign:+d}"] = {
                    "correct_unordered_pair_mass": float(probabilities[correct].sum()),
                    "argmax_roster": ROSTERS[best].tolist(),
                    "argmax_probability": float(probabilities[best]),
                    "entropy": float(
                        -(probabilities * np.log(np.clip(probabilities, 1e-12, 1.0))).sum()
                    ),
                }

        slow_flip = [
            _tv(distributions[(-1, fast)], distributions[(1, fast)])
            for fast in (-1, 1)
        ]
        fast_flip = [
            _tv(distributions[(slow, -1)], distributions[(slow, 1)])
            for slow in (-1, 1)
        ]
        all_pairs = []
        keys = sorted(distributions)
        for index, left in enumerate(keys):
            for right in keys[index + 1 :]:
                all_pairs.append(_tv(distributions[left], distributions[right]))
        return {
            "checkpoint": str(checkpoint.resolve()),
            "total_steps": total_steps,
            "update_idx": update_idx,
            "fixed_prev_roster": PREV_SKILLS.tolist(),
            "fixed_prev_ages": PREV_AGES.tolist(),
            "contexts": contexts,
            "target_flip_tv": {
                "slow": slow_flip,
                "fast": fast_flip,
                "all_pair_min": float(min(all_pairs)),
                "all_pair_max": float(max(all_pairs)),
                "all_pair_mean": float(np.mean(all_pairs)),
            },
        }
    finally:
        env.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adaptive-checkpoint", type=Path, required=True)
    parser.add_argument("--control-checkpoint", type=Path, required=True)
    parser.add_argument(
        "--adaptive-config",
        default="ha_ctse_process.config_r39_toy_fixed_primitives",
    )
    parser.add_argument(
        "--control-config",
        default="ha_ctse_process.config_r39_toy_fixed_primitives_shared_refresh",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")

    result = {
        "scope": "read-only R39 toy checkpoint context diagnostic",
        "training_or_environment_steps": 0,
        "arms": {
            "adaptive_retention": _summarize_arm(
                args.adaptive_config,
                args.adaptive_checkpoint,
                args.device,
            ),
            "force_refresh": _summarize_arm(
                args.control_config,
                args.control_checkpoint,
                args.device,
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    print(args.output.resolve())


if __name__ == "__main__":
    main()
