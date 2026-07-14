"""R32 interventional fixed-window effect policy-gradient primitives.

The score in this module is defined only by randomized, fixed-window effect
branches.  It is a signed actor auxiliary objective: it is not an intrinsic
reward, does not train a scorer, and must not enter low GAE or the R30 high
return.  Only the focal actor log-probabilities participate in the PPO
surrogate; callers own branch collection, recurrent replay, and FiLM-only
optimizer scoping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np
import torch


ArrayOrTensor = np.ndarray | torch.Tensor


@dataclass(frozen=True)
class InterventionalContext:
    """One natural R30 decision snapshot used to launch forced branches.

    Arrays are deliberately kept in their source backend.  The context owns
    the complete joint observation/state and recurrent snapshots even though
    the R32 surrogate later replays only the focal actor sequence.
    """

    context_id: int
    reset_group: int
    focal_agent: int
    observations: ArrayOrTensor = field(repr=False, compare=False)
    state: ArrayOrTensor = field(repr=False, compare=False)
    active_skills: ArrayOrTensor = field(repr=False, compare=False)
    actor_rnn_states: ArrayOrTensor = field(repr=False, compare=False)
    critic_rnn_states: ArrayOrTensor = field(repr=False, compare=False)
    env_snapshot: Any = field(repr=False, compare=False)
    metadata: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        if int(self.context_id) < 0:
            raise ValueError("context_id must be non-negative")
        if int(self.reset_group) < 0:
            raise ValueError("reset_group must be non-negative")
        skill_shape = tuple(self.active_skills.shape)
        if len(skill_shape) != 1 or skill_shape[0] <= 1:
            raise ValueError("active_skills must contain a joint multi-agent roster")
        if not 0 <= int(self.focal_agent) < skill_shape[0]:
            raise ValueError("focal_agent is outside the active skill roster")


@dataclass(frozen=True)
class ForcedEffectBranch:
    """One focal skill intervention and stochastic replica.

    ``observations``, ``actions``, and ``old_log_probs`` are the exact focal
    sequence needed for on-policy replay.  ``effect`` is the task-agnostic
    fixed-window effect computed after collection and is never differentiated.
    """

    context_id: int
    focal_agent: int
    skill: int
    replica: int
    effect: ArrayOrTensor = field(repr=False, compare=False)
    observations: ArrayOrTensor = field(repr=False, compare=False)
    actions: ArrayOrTensor = field(repr=False, compare=False)
    old_log_probs: ArrayOrTensor = field(repr=False, compare=False)
    initial_actor_rnn_state: ArrayOrTensor = field(repr=False, compare=False)
    masks: ArrayOrTensor | None = field(default=None, repr=False, compare=False)
    metadata: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        if int(self.context_id) < 0:
            raise ValueError("context_id must be non-negative")
        if int(self.focal_agent) < 0 or int(self.skill) < 0:
            raise ValueError("focal_agent and skill must be non-negative")
        if int(self.replica) not in (0, 1):
            raise ValueError("R32 requires exactly two replicas indexed 0 and 1")
        if self.effect.ndim != 1 or int(self.effect.shape[0]) <= 0:
            raise ValueError("effect must be a non-empty vector")
        if self.observations.ndim < 2:
            raise ValueError("observations must contain a time dimension")
        window = int(self.observations.shape[0])
        if int(self.actions.shape[0]) != window or int(self.old_log_probs.shape[0]) != window:
            raise ValueError("branch observations/actions/log-probabilities must share a window")
        if self.masks is not None and int(self.masks.shape[0]) != window:
            raise ValueError("branch masks must share the trajectory window")


def _check_pair_backend(left: ArrayOrTensor, right: ArrayOrTensor) -> None:
    if isinstance(left, torch.Tensor) != isinstance(right, torch.Tensor):
        raise TypeError("inputs must use the same torch or NumPy backend")


def _finite(value: ArrayOrTensor) -> bool:
    if isinstance(value, torch.Tensor):
        return bool(torch.isfinite(value).all().item())
    return bool(np.isfinite(np.asarray(value)).all())


def effect_u_statistic(
    left_skill_effects: ArrayOrTensor,
    right_skill_effects: ArrayOrTensor,
) -> ArrayOrTensor:
    """Return the noise-corrected two-replica effect separation.

    Inputs have shape ``[..., 2, d_E]``.  For each leading item this computes

    ``<E_left[0] - E_right[0], E_left[1] - E_right[1]>``.

    Independent replicas make its expectation the squared distance between
    the two interventional effect means; stochastic execution variance is not
    a positive term in that expectation.
    """

    _check_pair_backend(left_skill_effects, right_skill_effects)
    if tuple(left_skill_effects.shape) != tuple(right_skill_effects.shape):
        raise ValueError("paired skill effects must have identical shapes")
    if left_skill_effects.ndim < 2 or int(left_skill_effects.shape[-2]) != 2:
        raise ValueError("skill effects must have shape [..., 2, d_E]")
    if int(left_skill_effects.shape[-1]) <= 0:
        raise ValueError("effect dimension must be positive")
    if not _finite(left_skill_effects) or not _finite(right_skill_effects):
        raise ValueError("effect values must be finite")

    first_difference = left_skill_effects[..., 0, :] - right_skill_effects[..., 0, :]
    second_difference = left_skill_effects[..., 1, :] - right_skill_effects[..., 1, :]
    if isinstance(first_difference, torch.Tensor):
        return torch.sum(first_difference * second_difference, dim=-1)
    return np.sum(first_difference * second_difference, axis=-1)


def context_effect_score(
    forced_effects: ArrayOrTensor,
    *,
    return_pairwise: bool = False,
) -> ArrayOrTensor | tuple[ArrayOrTensor, ArrayOrTensor, np.ndarray]:
    """Compute the signed R32 score for each intervention context.

    ``forced_effects`` has shape ``[..., K, 2, d_E]``.  The returned score is
    the sum of all skill-pair U-statistics divided by
    ``d_E * combinations(K, 2)``.  No ReLU or other positive clipping is used.
    When requested, the pairwise statistics and their ``[z, z']`` indices are
    returned alongside the context score.
    """

    if forced_effects.ndim < 3 or int(forced_effects.shape[-2]) != 2:
        raise ValueError("forced_effects must have shape [..., K, 2, d_E]")
    n_skills = int(forced_effects.shape[-3])
    effect_dim = int(forced_effects.shape[-1])
    if n_skills <= 1 or effect_dim <= 0:
        raise ValueError("R32 requires at least two skills and a non-empty effect")
    if not _finite(forced_effects):
        raise ValueError("forced effects must be finite")

    skill_pairs = np.asarray(
        [(left, right) for left in range(n_skills) for right in range(left + 1, n_skills)],
        dtype=np.int64,
    )
    pairwise_values = [
        effect_u_statistic(
            forced_effects[..., left, :, :],
            forced_effects[..., right, :, :],
        )
        for left, right in skill_pairs
    ]
    if isinstance(forced_effects, torch.Tensor):
        pairwise = torch.stack(pairwise_values, dim=-1)
        score = pairwise.sum(dim=-1) / float(effect_dim * len(skill_pairs))
    else:
        pairwise = np.stack(pairwise_values, axis=-1)
        score = pairwise.sum(axis=-1) / float(effect_dim * len(skill_pairs))
    if return_pairwise:
        return score, pairwise, skill_pairs
    return score


def leave_one_context_advantage(
    context_scores: ArrayOrTensor,
    *,
    epsilon: float = 1e-8,
) -> ArrayOrTensor:
    """Standardize each signed score against all other batch contexts.

    The baseline and population standard deviation for context ``c`` exclude
    ``c`` itself.  Tensor inputs are detached because the intervention score is
    a policy-gradient weight, not a differentiable environment objective.
    """

    if context_scores.ndim != 1 or int(context_scores.shape[0]) < 3:
        raise ValueError("leave-one-context advantages require at least three scores")
    if not np.isfinite(float(epsilon)) or float(epsilon) <= 0.0:
        raise ValueError("epsilon must be finite and positive")
    if not _finite(context_scores):
        raise ValueError("context scores must be finite")

    batch = int(context_scores.shape[0])
    if isinstance(context_scores, torch.Tensor):
        scores = context_scores.detach()
        tiled = scores.unsqueeze(0).expand(batch, batch)
        keep = ~torch.eye(batch, dtype=torch.bool, device=scores.device)
        others = tiled[keep].reshape(batch, batch - 1)
        baseline = others.mean(dim=1)
        scale = others.std(dim=1, unbiased=False)
        return (scores - baseline) / (scale + float(epsilon))

    scores = np.asarray(context_scores)
    tiled = np.broadcast_to(scores[None, :], (batch, batch))
    keep = ~np.eye(batch, dtype=bool)
    others = tiled[keep].reshape(batch, batch - 1)
    baseline = others.mean(axis=1)
    scale = others.std(axis=1, ddof=0)
    return (scores - baseline) / (scale + float(epsilon))


def _broadcast_context_advantages(
    context_advantages: ArrayOrTensor,
    target: ArrayOrTensor,
) -> ArrayOrTensor:
    if context_advantages.ndim == 0:
        return context_advantages
    if context_advantages.ndim == 1 and target.ndim > 1:
        if int(context_advantages.shape[0]) != int(target.shape[0]):
            raise ValueError("one context advantage is required per leading log-probability row")
        shape = (int(context_advantages.shape[0]),) + (1,) * (target.ndim - 1)
        return context_advantages.reshape(shape)
    return context_advantages


def focal_ppo_clipped_surrogate(
    current_log_probs: ArrayOrTensor,
    old_log_probs: ArrayOrTensor,
    context_advantages: ArrayOrTensor,
    *,
    clip: float = 0.10,
    mask: ArrayOrTensor | None = None,
) -> ArrayOrTensor:
    """Return the negative focal-only PPO-clipped IFEPG surrogate.

    Typical shapes are ``[B, K, 2, W]`` for log-probabilities and ``[B]`` for
    advantages.  ``old_log_probs`` and advantages are detached for tensor
    inputs.  A mask may exclude padded sequence positions.  The reduction is a
    mean over valid context/skill/replica/time entries.
    """

    if isinstance(current_log_probs, torch.Tensor):
        old_log_probs = torch.as_tensor(
            old_log_probs,
            dtype=current_log_probs.dtype,
            device=current_log_probs.device,
        )
        context_advantages = torch.as_tensor(
            context_advantages,
            dtype=current_log_probs.dtype,
            device=current_log_probs.device,
        )
        if mask is not None:
            mask = torch.as_tensor(mask, device=current_log_probs.device)
    else:
        current_log_probs = np.asarray(current_log_probs)
        old_log_probs = _as_numpy(old_log_probs, dtype=current_log_probs.dtype)
        context_advantages = _as_numpy(
            context_advantages,
            dtype=current_log_probs.dtype,
        )
        if mask is not None:
            mask = _as_numpy(mask)
    if tuple(current_log_probs.shape) != tuple(old_log_probs.shape):
        raise ValueError("current and old focal log-probabilities must have identical shapes")
    element_count = (
        int(current_log_probs.numel())
        if isinstance(current_log_probs, torch.Tensor)
        else int(current_log_probs.size)
    )
    if current_log_probs.ndim < 1 or element_count <= 0:
        raise ValueError("focal log-probabilities must be non-empty")
    if not np.isfinite(float(clip)) or not 0.0 < float(clip) < 1.0:
        raise ValueError("PPO clip must lie strictly between zero and one")
    if not _finite(current_log_probs) or not _finite(old_log_probs):
        raise ValueError("focal log-probabilities must be finite")
    if not _finite(context_advantages):
        raise ValueError("context advantages must be finite")
    advantages = _broadcast_context_advantages(context_advantages, current_log_probs)
    if isinstance(current_log_probs, torch.Tensor):
        old = old_log_probs.detach()
        advantages = advantages.detach()
        ratio = torch.exp(current_log_probs - old)
        unclipped = ratio * advantages
        clipped = torch.clamp(ratio, 1.0 - float(clip), 1.0 + float(clip)) * advantages
        surrogate = torch.minimum(unclipped, clipped)
        if mask is None:
            return -surrogate.mean()
        weights = torch.broadcast_to(mask.detach().to(dtype=surrogate.dtype), surrogate.shape)
        valid_count = weights.sum()
        if float(valid_count.detach().item()) <= 0.0:
            raise ValueError("focal PPO mask contains no valid entries")
        return -(surrogate * weights).sum() / valid_count

    current = np.asarray(current_log_probs)
    old = np.asarray(old_log_probs)
    advantages = np.asarray(advantages)
    ratio = np.exp(current - old)
    unclipped = ratio * advantages
    clipped = np.clip(ratio, 1.0 - float(clip), 1.0 + float(clip)) * advantages
    surrogate = np.minimum(unclipped, clipped)
    if mask is None:
        return np.asarray(-surrogate.mean())
    weights = np.broadcast_to(np.asarray(mask, dtype=surrogate.dtype), surrogate.shape)
    valid_count = float(weights.sum())
    if valid_count <= 0.0:
        raise ValueError("focal PPO mask contains no valid entries")
    return np.asarray(-(surrogate * weights).sum() / valid_count)


def _as_numpy64(value: ArrayOrTensor) -> np.ndarray:
    if isinstance(value, torch.Tensor):
        return value.detach().to(dtype=torch.float64, device="cpu").numpy()
    return np.asarray(value, dtype=np.float64)


def _as_numpy(value: Any, *, dtype=None) -> np.ndarray:
    if isinstance(value, torch.Tensor):
        value = value.detach().to(device="cpu").numpy()
    return np.asarray(value, dtype=dtype)


def _is_film_parameter(name: str, film_parameter_prefix: str) -> bool:
    token = str(film_parameter_prefix).strip(".")
    if not token:
        raise ValueError("film_parameter_prefix must be non-empty")
    parts = str(name).split(".")
    token_parts = token.split(".")
    width = len(token_parts)
    return any(parts[index : index + width] == token_parts for index in range(len(parts) - width + 1))


def parameter_drift_metrics(
    before: Mapping[str, ArrayOrTensor],
    after: Mapping[str, ArrayOrTensor],
    *,
    film_parameter_prefix: str = "actor_film",
    epsilon: float = 1e-12,
) -> dict[str, Any]:
    """Measure exact FiLM and non-FiLM parameter movement.

    Relative L2 drift is aggregated as
    ``sqrt(sum ||after-before||^2) / (sqrt(sum ||before||^2) + epsilon)``.
    The maximum absolute drift is also reported for fail-closed checks of all
    parameters that R32 must freeze.
    """

    if not np.isfinite(float(epsilon)) or float(epsilon) <= 0.0:
        raise ValueError("epsilon must be finite and positive")
    before_names = set(before)
    after_names = set(after)
    if before_names != after_names:
        missing = sorted(before_names - after_names)
        added = sorted(after_names - before_names)
        raise ValueError(f"parameter sets differ: missing_after={missing}, added_after={added}")
    if not before_names:
        raise ValueError("parameter mappings must be non-empty")

    totals = {
        "all": {"base_sq": 0.0, "delta_sq": 0.0, "max_abs": 0.0, "count": 0},
        "film": {"base_sq": 0.0, "delta_sq": 0.0, "max_abs": 0.0, "count": 0},
        "non_film": {"base_sq": 0.0, "delta_sq": 0.0, "max_abs": 0.0, "count": 0},
    }
    per_parameter: dict[str, dict[str, float | bool | int]] = {}
    for name in sorted(before_names):
        before_value = _as_numpy64(before[name])
        after_value = _as_numpy64(after[name])
        if before_value.shape != after_value.shape:
            raise ValueError(
                f"parameter {name!r} changed shape from {before_value.shape} to {after_value.shape}"
            )
        if not np.isfinite(before_value).all() or not np.isfinite(after_value).all():
            raise ValueError(f"parameter {name!r} contains non-finite values")
        delta = after_value - before_value
        base_sq = float(np.sum(before_value * before_value, dtype=np.float64))
        delta_sq = float(np.sum(delta * delta, dtype=np.float64))
        max_abs = float(np.max(np.abs(delta))) if delta.size else 0.0
        film = _is_film_parameter(name, film_parameter_prefix)
        group = "film" if film else "non_film"
        for key in ("all", group):
            totals[key]["base_sq"] += base_sq
            totals[key]["delta_sq"] += delta_sq
            totals[key]["max_abs"] = max(float(totals[key]["max_abs"]), max_abs)
            totals[key]["count"] += int(delta.size)
        parameter_l2 = float(np.sqrt(delta_sq))
        per_parameter[name] = {
            "is_film": film,
            "count": int(delta.size),
            "max_abs": max_abs,
            "l2": parameter_l2,
            "relative_l2": parameter_l2 / (float(np.sqrt(base_sq)) + float(epsilon)),
        }

    result: dict[str, Any] = {"parameters": per_parameter}
    for group, values in totals.items():
        base_l2 = float(np.sqrt(float(values["base_sq"])))
        drift_l2 = float(np.sqrt(float(values["delta_sq"])))
        result[f"{group}_parameter_count"] = int(values["count"])
        result[f"{group}_max_abs"] = float(values["max_abs"])
        result[f"{group}_l2"] = drift_l2
        result[f"{group}_relative_l2"] = drift_l2 / (base_l2 + float(epsilon))
    return result
