"""Full-reset, common-randomness pair collection for a frozen UCOPE actor.

No simulator snapshot machinery, native imports, fitting or launcher is owned
here. The caller supplies an adapter and a frozen policy. Repeating the entire
prefix costs real steps; all 2 * horizon steps are counted, even when the
scheduled decision is ineligible. A failed prefix match is a technical failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, MutableMapping

import numpy as np
import torch

from ..frozen_mean_gate_b08.engine import _require_frozen_foundation
from ..uav_motion_prefix_b01.environment import actor_features, critic_features, team_reward


@dataclass(frozen=True)
class FocalCase:
    tick: int
    agent: int

    def validate(self, horizon: int) -> None:
        if type(horizon) is not int or horizon < 2:
            raise ValueError("horizon must be an integer of at least two")
        if type(self.tick) is not int or not 1 <= self.tick < horizon:
            raise ValueError("focal tick must be a nonreset tick within the horizon")
        if type(self.agent) is not int or not 0 <= self.agent < 5:
            raise ValueError("focal agent must be an integer in [0, 5)")


def schedule(count: int, horizon: int, seed: int) -> tuple[FocalCase, ...]:
    """Draw agent and tick independently of all world/policy outcomes."""
    if type(count) is not int or count <= 0:
        raise ValueError("count must be a positive integer")
    FocalCase(1, 0).validate(horizon)
    rng = np.random.default_rng(seed)
    ticks = rng.integers(1, horizon, size=count)
    agents = rng.integers(0, 5, size=count)
    return tuple(FocalCase(int(t), int(i)) for t, i in zip(ticks, agents))


def _add(counts: MutableMapping[str, int], name: str, count: int = 1) -> None:
    counts[name] = counts.get(name, 0) + count


@torch.no_grad()
def collect_pair(
    env: Any,
    foundation: torch.nn.Module,
    gate: torch.nn.Module,
    critic: torch.nn.Module | None,
    *,
    horizon: int,
    case: FocalCase,
    mode: Literal["paired", "factual"],
    reset_seed: int,
    common_seed: int,
    focal_seed: int,
    check: Callable[[], None],
    counts: MutableMapping[str, int],
) -> dict[str, Any]:
    """Collect KEEP/END branches or two independently drawn factual choices.

    The policy stays unchanged for the pair. A training-only critic supplies
    a pre-outcome baseline and saved targets for an eventual caller. Returned
    episode arrays are data, never extra runtime actor features.
    """
    case.validate(horizon)
    if mode not in ("paired", "factual"):
        raise ValueError("mode must be paired or factual")
    if mode == "factual" and critic is None:
        raise ValueError("factual reference requires a pre-outcome critic")
    if not callable(check):
        raise TypeError("check must be callable")
    _require_frozen_foundation(foundation)
    common = torch.rand(
        (horizon, 5), generator=torch.Generator(device="cpu").manual_seed(common_seed)
    )
    focal = torch.rand((2,), generator=torch.Generator(device="cpu").manual_seed(focal_seed))
    _add(counts, "common_uniform_values", horizon * 5)
    _add(counts, "focal_uniform_values", 2)
    episodes = []
    for branch in range(2):
        check()
        obs, info = env.reset(seed=reset_seed)
        _add(counts, "reset_calls")
        state = info["state"]
        previous = np.zeros((5, 3), dtype=np.float32)
        eligible = torch.zeros(5, dtype=torch.bool)
        hidden = torch.zeros(1, 5, 64, dtype=torch.float32)
        data: dict[str, list[torch.Tensor]] = {key: [] for key in (
            "context", "critic", "logits", "value", "eligible", "keep",
            "commands", "reward",
        )}
        for tick in range(horizon):
            check()
            observation = np.asarray(obs, dtype=np.float32)
            if observation.shape != (5, 104):
                raise ValueError("expected five 104-dimensional private observations")
            features = actor_features(observation, previous, np.zeros(5, dtype=np.int64))
            raw, recurrent, hidden = foundation(torch.from_numpy(features)[None], hidden)
            _add(counts, "foundation_forward_calls")
            if raw.shape != (1, 5, 3) or recurrent.shape != (1, 5, 64):
                raise ValueError("foundation output shape is invalid")
            if hidden.shape != (1, 5, 64) or not bool(torch.isfinite(hidden).all()):
                raise ValueError("foundation recurrent state is invalid")
            fresh = raw[0].tanh()
            prior = torch.from_numpy(previous)
            distance = (fresh - prior).square().sum(-1, keepdim=True) / 12.0
            context = torch.cat((torch.from_numpy(observation), prior, fresh,
                                 recurrent[0], distance), dim=-1)
            central = torch.from_numpy(critic_features(state, previous, eligible.numpy()))
            logits = gate(context)
            value = critic(central) if critic is not None else torch.zeros((), dtype=torch.float32)
            _add(counts, "gate_forward_calls")
            if critic is not None:
                _add(counts, "critic_forward_calls")
            if logits.shape != (5,) or value.ndim != 0:
                raise ValueError("gate or critic output shape is invalid")
            for tensor in (context, central, logits, value, fresh):
                if tensor.dtype != torch.float32 or tensor.device.type != "cpu":
                    raise TypeError("all acting tensors must be CPU float32")
                if not bool(torch.isfinite(tensor).all()):
                    raise ValueError("acting tensors must be finite")
            probability = logits.sigmoid()
            if not bool(((probability > 0) & (probability < 1)).all()):
                raise ValueError("gate has numerically lost binary support")
            keep = eligible & (common[tick] < probability)
            if tick == case.tick and bool(eligible[case.agent]):
                keep[case.agent] = (branch == 0) if mode == "paired" else bool(
                    focal[branch] < probability[case.agent]
                )
            command = fresh.clone()
            command[keep] = prior[keep]
            for key, tensor in (("context", context), ("critic", central),
                                ("logits", logits), ("value", value),
                                ("eligible", eligible), ("keep", keep),
                                ("commands", command)):
                data[key].append(tensor.detach().clone())
            check()
            next_obs, _, terminated, truncated, info = env.step(command.numpy())
            _add(counts, "team_steps")
            if bool(terminated) and bool(truncated):
                raise RuntimeError("episode cannot terminate and truncate simultaneously")
            if bool(terminated or truncated) != (tick == horizon - 1):
                raise RuntimeError("episode boundary does not match declared horizon")
            reward = torch.tensor(team_reward(info), dtype=torch.float64)
            if not bool(torch.isfinite(reward)):
                raise ValueError("nonfinite team reward")
            data["reward"].append(reward)
            obs, state = next_obs, info["next_state"]
            previous = command.numpy().copy()
            eligible = ~keep
            check()
        episodes.append({key: torch.stack(rows) for key, rows in data.items()})
        _add(counts, "completed_episodes")

    left, right = episodes
    # This also checks every teammate's predecision context. It is NOT sufficient
    # to match only the focal action, reward prefix, or simulator reset seed.
    for key in left:
        length = case.tick + 1 if key in (
            "context", "critic", "logits", "value", "eligible"
        ) else case.tick
        if not torch.equal(left[key][:length], right[key][:length]):
            raise RuntimeError(f"pair prefix mismatch in {key}")
    active = bool(left["eligible"][case.tick, case.agent])
    if not active and any(not torch.equal(left[key], right[key]) for key in left):
        raise RuntimeError("inactive pair diverged despite the identical policy law")
    # Includes current reward, every downstream team reaction, and the final tick.
    suffix = torch.stack([episode["reward"][case.tick:].sum() / horizon for episode in episodes])
    _add(counts, "completed_pairs")
    _add(counts, "eligible_pairs", int(active))
    return {
        "case": case,
        "mode": mode,
        "eligible": active,
        "old_logits": left["logits"][case.tick].clone(),
        "context": left["context"][case.tick].clone(),
        # The inherited critic is trained on unnormalized returns-to-go; the
        # gate's native-J target divides both the return and baseline by H.
        "baseline": left["value"][case.tick].clone() / horizon,
        "suffix_returns": suffix,
        "sampled_keep": torch.stack([episode["keep"][case.tick, case.agent] for episode in episodes]),
        "common_uniforms": common,
        "focal_uniforms": focal,
        "episodes": episodes,
    }
