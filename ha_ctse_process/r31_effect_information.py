"""R31 fixed-window causal effect-information data primitives.

This module owns only task-agnostic effect-window data and reward-off causal
metrics.  It does not read actions, rewards, task state, skill age, or process
segment length.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class EffectWindowRow:
    """One focal-agent view of a natural R30 fixed-check block."""

    env_id: int
    episode_id: int
    policy_update: int
    focal_agent: int
    start_rollout_index: int
    endpoint_rollout_index: int
    start_effect_view: np.ndarray
    effect_view_sequence: np.ndarray
    active_skills: np.ndarray
    effect_view_count: int = 1
    complete: bool = False
    invalid: bool = False
    invalid_reason: str = ""
    terminal: bool = False
    policy_truncated: bool = False

    @property
    def transition_count(self) -> int:
        return max(int(self.effect_view_count) - 1, 0)

    @property
    def ready(self) -> bool:
        return bool(self.complete and not self.invalid)


class EffectWindowBuffer:
    """Collect one fixed-length natural effect window per agent and real check.

    A caller must explicitly identify a real R30 decision row when opening a
    block.  Continuation rows therefore cannot silently create R31 samples.
    Windows that terminate or cross a policy-update boundary before ``W``
    transitions are retained only as invalid rows.
    """

    def __init__(self, num_envs: int, n_agents: int, window: int) -> None:
        self.num_envs = int(num_envs)
        self.n_agents = int(n_agents)
        self.window = int(window)
        if self.num_envs <= 0:
            raise ValueError("num_envs must be positive")
        if self.n_agents <= 1:
            raise ValueError("R31 requires at least two agents")
        if self.window <= 0 or self.window % 2 != 0:
            raise ValueError("R31 effect window must be a positive even integer")
        self.pending: dict[tuple[int, int], EffectWindowRow] = {}
        self.rows: list[EffectWindowRow] = []
        self.invalid_rows: list[EffectWindowRow] = []
        self._opened: set[tuple[int, int, int, int, int]] = set()

    def _effect_view(self, effect_view) -> np.ndarray:
        view = np.asarray(effect_view, dtype=np.float32)
        if view.ndim != 2 or view.shape[0] != self.n_agents:
            raise ValueError(
                "effect view must have shape "
                f"[{self.n_agents}, d_x], got {tuple(view.shape)}"
            )
        if view.shape[1] <= 0 or not np.all(np.isfinite(view)):
            raise ValueError("effect view must be finite and non-empty")
        return view

    def open_after_check(
        self,
        *,
        env_id: int,
        episode_id: int,
        policy_update: int,
        start_rollout_index: int,
        effect_view,
        active_skills,
        decision_mask: bool,
    ) -> list[EffectWindowRow]:
        """Open all focal-agent windows after an applied real R30 decision.

        ``decision_mask=False`` is a continuation row and is intentionally a
        no-op.  The identity key prevents a repeated hook from opening a second
        opportunity for the same agent and check block.
        """

        if not bool(decision_mask):
            return []
        env_id = int(env_id)
        if not 0 <= env_id < self.num_envs:
            raise IndexError(f"env_id {env_id} is out of range")
        view = self._effect_view(effect_view)
        skills = np.asarray(active_skills, dtype=np.int64).reshape(-1)
        if skills.shape != (self.n_agents,):
            raise ValueError(
                f"active_skills must have shape [{self.n_agents}], got {skills.shape}"
            )
        if np.any(skills < 0):
            raise ValueError("all agents must have an active skill after an R30 check")

        opened: list[EffectWindowRow] = []
        for focal_agent in range(self.n_agents):
            pending_key = (env_id, focal_agent)
            if pending_key in self.pending:
                raise RuntimeError(
                    f"R31 env {env_id} agent {focal_agent} already has a pending window"
                )
            identity = (
                env_id,
                int(episode_id),
                int(policy_update),
                int(start_rollout_index),
                focal_agent,
            )
            if identity in self._opened:
                raise RuntimeError(
                    f"R31 duplicate opportunity for env {env_id}, agent {focal_agent}"
                )
            sequence = np.full(
                (self.window + 1, self.n_agents, view.shape[1]),
                np.nan,
                dtype=np.float32,
            )
            sequence[0] = view
            row = EffectWindowRow(
                env_id=env_id,
                episode_id=int(episode_id),
                policy_update=int(policy_update),
                focal_agent=focal_agent,
                start_rollout_index=int(start_rollout_index),
                endpoint_rollout_index=-1,
                start_effect_view=view.copy(),
                effect_view_sequence=sequence,
                active_skills=skills.copy(),
            )
            self.pending[pending_key] = row
            self._opened.add(identity)
            opened.append(row)
        return opened

    def append_effect_view(
        self,
        *,
        env_id: int,
        effect_view,
        rollout_index: int,
        episode_id: int | None = None,
        terminal: bool = False,
        policy_truncated: bool = False,
    ) -> list[EffectWindowRow]:
        """Append one post-transition view and close or invalidate as needed."""

        env_id = int(env_id)
        keys = [key for key in self.pending if key[0] == env_id]
        if not keys:
            return []
        view = self._effect_view(effect_view)
        closed: list[EffectWindowRow] = []
        for key in keys:
            row = self.pending[key]
            if episode_id is not None and int(episode_id) != row.episode_id:
                closed.append(
                    self.invalidate(
                        env_id,
                        focal_agent=row.focal_agent,
                        terminal=True,
                        reason="episode_changed_before_endpoint",
                    )[0]
                )
                continue
            if row.effect_view_count >= self.window + 1:
                raise RuntimeError("cannot append beyond a complete R31 window")
            row.effect_view_sequence[row.effect_view_count] = view
            row.effect_view_count += 1
            at_endpoint = row.effect_view_count == self.window + 1
            if at_endpoint:
                closed.append(
                    self.complete(
                        env_id,
                        row.focal_agent,
                        endpoint_rollout_index=int(rollout_index),
                        terminal=terminal,
                        policy_truncated=policy_truncated,
                    )
                )
            elif terminal or policy_truncated:
                reason = "terminal_before_endpoint" if terminal else "policy_truncated_before_endpoint"
                closed.append(
                    self.invalidate(
                        env_id,
                        focal_agent=row.focal_agent,
                        terminal=terminal,
                        policy_truncated=policy_truncated,
                        reason=reason,
                    )[0]
                )
        return closed

    def complete(
        self,
        env_id: int,
        focal_agent: int,
        *,
        endpoint_rollout_index: int,
        terminal: bool = False,
        policy_truncated: bool = False,
    ) -> EffectWindowRow:
        """Mark an exactly ``W``-transition window ready for scoring."""

        key = (int(env_id), int(focal_agent))
        row = self.pending.get(key)
        if row is None:
            raise RuntimeError(f"R31 env/agent {key} has no pending window")
        if row.effect_view_count != self.window + 1:
            raise RuntimeError(
                f"R31 window has {row.transition_count} transitions, expected {self.window}"
            )
        row.endpoint_rollout_index = int(endpoint_rollout_index)
        row.complete = True
        row.terminal = bool(terminal)
        row.policy_truncated = bool(policy_truncated)
        self.rows.append(row)
        del self.pending[key]
        return row

    def invalidate(
        self,
        env_id: int,
        *,
        focal_agent: int | None = None,
        terminal: bool = False,
        policy_truncated: bool = False,
        reason: str,
    ) -> list[EffectWindowRow]:
        """Invalidate pending windows without creating a scorer/reward sample."""

        env_id = int(env_id)
        keys = [
            key
            for key in self.pending
            if key[0] == env_id and (focal_agent is None or key[1] == int(focal_agent))
        ]
        invalidated: list[EffectWindowRow] = []
        for key in keys:
            row = self.pending.pop(key)
            row.invalid = True
            row.invalid_reason = str(reason)
            row.terminal = bool(terminal)
            row.policy_truncated = bool(policy_truncated)
            self.invalid_rows.append(row)
            invalidated.append(row)
        return invalidated

    def invalidate_all(self, *, reason: str = "policy_update") -> list[EffectWindowRow]:
        invalidated: list[EffectWindowRow] = []
        for env_id in range(self.num_envs):
            invalidated.extend(
                self.invalidate(
                    env_id,
                    policy_truncated=True,
                    reason=reason,
                )
            )
        return invalidated

    def pop_completed(self) -> list[EffectWindowRow]:
        rows = self.rows
        self.rows = []
        return rows

    def pop_invalidated(self) -> list[EffectWindowRow]:
        rows = self.invalid_rows
        self.invalid_rows = []
        return rows


def build_effect_and_context(
    effect_view_sequence,
    active_skills,
    focal_agent: int,
    n_skills: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Build the R31 effect ``E`` and context ``C`` from normalized positions.

    The sequence must have shape ``[W+1, N, 2]``.  Context contains only focal
    and mean-teammate start positions plus canonical teammate skill one-hots;
    the focal skill is deliberately absent.
    """

    positions = np.asarray(effect_view_sequence, dtype=np.float32)
    if positions.ndim != 3 or positions.shape[2] != 2:
        raise ValueError(
            "R31 Alice-Bob effect sequence must have shape [W+1, N, 2]"
        )
    window = int(positions.shape[0] - 1)
    n_agents = int(positions.shape[1])
    focal_agent = int(focal_agent)
    n_skills = int(n_skills)
    if window <= 0 or window % 2 != 0:
        raise ValueError("R31 effect sequence requires a positive even W")
    if n_agents <= 1 or not 0 <= focal_agent < n_agents:
        raise ValueError("invalid R31 focal agent or agent count")
    if n_skills <= 1 or not np.all(np.isfinite(positions)):
        raise ValueError("R31 positions must be finite and n_skills must exceed one")
    skills = np.asarray(active_skills, dtype=np.int64).reshape(-1)
    if skills.shape != (n_agents,) or np.any(skills < 0) or np.any(skills >= n_skills):
        raise ValueError("active_skills must contain one valid label per agent")

    teammate_ids = [agent_id for agent_id in range(n_agents) if agent_id != focal_agent]
    focal = positions[:, focal_agent]
    teammate = positions[:, teammate_ids].mean(axis=1)
    focal_start = focal[0]
    teammate_start = teammate[0]
    late = slice(window // 2 + 1, window + 1)
    effect = np.concatenate(
        [
            focal[-1] - focal_start,
            teammate[-1] - teammate_start,
            (focal[late] - focal_start).mean(axis=0),
            (teammate[late] - teammate_start).mean(axis=0),
        ]
    ).astype(np.float32, copy=False)
    teammate_onehot = np.eye(n_skills, dtype=np.float32)[skills[teammate_ids]].reshape(-1)
    context = np.concatenate(
        [focal_start, teammate_start, teammate_onehot]
    ).astype(np.float32, copy=False)
    return effect, context


def matched_context_shuffle(
    effects,
    start_positions,
    active_skills,
    focal_agents,
    *,
    position_bins: int = 5,
    rng: np.random.Generator | int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Permute effects across matched teammate rosters and adjacent start bins.

    Returns ``(shuffled_effects, donor_indices, valid_mask)``.  Unmatched rows
    retain their own effect and must be excluded from the shuffle gate.
    """

    effect_array = np.asarray(effects, dtype=np.float32)
    starts = np.asarray(start_positions, dtype=np.float32)
    skills = np.asarray(active_skills, dtype=np.int64)
    focals = np.asarray(focal_agents, dtype=np.int64).reshape(-1)
    if effect_array.ndim != 2:
        raise ValueError("effects must have shape [B, d_e]")
    batch = int(effect_array.shape[0])
    if starts.ndim != 3 or starts.shape[0] != batch or starts.shape[2] != 2:
        raise ValueError("start_positions must have shape [B, N, 2]")
    if skills.shape != starts.shape[:2] or focals.shape != (batch,):
        raise ValueError("active_skills/focal_agents do not match start_positions")
    n_agents = int(starts.shape[1])
    if n_agents <= 1 or np.any(focals < 0) or np.any(focals >= n_agents):
        raise ValueError("invalid focal agent labels")
    if position_bins <= 0 or not np.all(np.isfinite(starts)):
        raise ValueError("position_bins must be positive and positions finite")

    context_starts = np.zeros((batch, 4), dtype=np.float32)
    roster_keys: list[tuple[int, ...]] = []
    for sample in range(batch):
        focal = int(focals[sample])
        teammate_ids = [idx for idx in range(n_agents) if idx != focal]
        context_starts[sample, :2] = starts[sample, focal]
        context_starts[sample, 2:] = starts[sample, teammate_ids].mean(axis=0)
        roster_keys.append(tuple(int(skills[sample, idx]) for idx in teammate_ids))
    clipped = np.clip(context_starts, 0.0, np.nextafter(1.0, 0.0))
    start_bins = np.floor(clipped * int(position_bins)).astype(np.int64)

    generator = rng if isinstance(rng, np.random.Generator) else np.random.default_rng(rng)
    candidates: list[list[int]] = []
    for receiver in range(batch):
        matched = [
            donor
            for donor in range(batch)
            if donor != receiver
            and roster_keys[donor] == roster_keys[receiver]
            and np.max(np.abs(start_bins[donor] - start_bins[receiver])) <= 1
        ]
        generator.shuffle(matched)
        candidates.append(matched)

    donor_owner = np.full(batch, -1, dtype=np.int64)
    donor_indices = np.full(batch, -1, dtype=np.int64)

    def assign(receiver: int, seen: set[int]) -> bool:
        for donor in candidates[receiver]:
            if donor in seen:
                continue
            seen.add(donor)
            prior_receiver = int(donor_owner[donor])
            if prior_receiver < 0 or assign(prior_receiver, seen):
                donor_owner[donor] = receiver
                donor_indices[receiver] = donor
                return True
        return False

    for receiver in generator.permutation(batch):
        assign(int(receiver), set())

    valid = donor_indices >= 0
    shuffled = effect_array.copy()
    shuffled[valid] = effect_array[donor_indices[valid]]
    return shuffled, donor_indices, valid


def causal_between_within_metrics(
    forced_effects,
    *,
    epsilon: float = 1e-8,
) -> dict[str, np.ndarray]:
    """Compute R31 between/within stochastic-effect ratios for every skill pair.

    ``forced_effects`` is ``[K, 2, d_e]`` or batched
    ``[B, K, 2, d_e]``.  The two replica streams are compared at the same
    replica index between skills and across replica indices within each skill.
    """

    effects = np.asarray(forced_effects, dtype=np.float64)
    squeeze_batch = effects.ndim == 3
    if squeeze_batch:
        effects = effects[None, ...]
    if effects.ndim != 4 or effects.shape[2] != 2 or effects.shape[3] <= 0:
        raise ValueError("forced_effects must have shape [B, K, 2, d_e]")
    if effects.shape[1] <= 1 or not np.all(np.isfinite(effects)):
        raise ValueError("forced effects require at least two skills and finite values")
    if epsilon <= 0.0:
        raise ValueError("epsilon must be positive")

    pairs = np.asarray(
        [(left, right) for left in range(effects.shape[1]) for right in range(left + 1, effects.shape[1])],
        dtype=np.int64,
    )
    between_values: list[np.ndarray] = []
    within_values: list[np.ndarray] = []
    for left, right in pairs:
        left_effect = effects[:, left]
        right_effect = effects[:, right]
        between = 0.5 * (
            np.sum((left_effect[:, 0] - right_effect[:, 0]) ** 2, axis=-1)
            + np.sum((left_effect[:, 1] - right_effect[:, 1]) ** 2, axis=-1)
        )
        within = 0.5 * (
            np.sum((left_effect[:, 0] - left_effect[:, 1]) ** 2, axis=-1)
            + np.sum((right_effect[:, 0] - right_effect[:, 1]) ** 2, axis=-1)
        )
        between_values.append(between)
        within_values.append(within)
    between_array = np.stack(between_values, axis=-1)
    within_array = np.stack(within_values, axis=-1)
    ratio = between_array / (within_array + float(epsilon))
    if squeeze_batch:
        between_array = between_array[0]
        within_array = within_array[0]
        ratio = ratio[0]
    return {
        "skill_pairs": pairs,
        "between": between_array,
        "within": within_array,
        "ratio": ratio,
    }
