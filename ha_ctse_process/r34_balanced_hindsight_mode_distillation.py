"""R34 balanced hindsight mode-distillation primitives.

R34 discovers balanced, task-agnostic modes from natural focal-position
trajectories and distils the resulting labels into the strict recurrent low
actor.  This module owns only deterministic offline transformations, the
actor-only sequence objective, and reward-free evaluation metrics.  Collection,
optimizer scoping, and the registered Alice--Bob gate remain caller concerns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment


ArrayOrTensor = np.ndarray | torch.Tensor
DEFAULT_ALLOWED_PREFIXES = (
    "actor_film",
    "actor_rnn",
    "actor_act.action_out.fc_mean",
)


def _as_numpy64(value: ArrayOrTensor) -> np.ndarray:
    if isinstance(value, torch.Tensor):
        return value.detach().to(dtype=torch.float64, device="cpu").numpy()
    return np.asarray(value, dtype=np.float64)


def _require_finite(name: str, value: np.ndarray) -> None:
    if not np.isfinite(value).all():
        raise ValueError(f"{name} must contain only finite values")


@dataclass(frozen=True)
class InteractionModeDescriptor:
    """Frozen train-only standardizer for the focal displacement sequence.

    A raw descriptor is the flattened sequence
    ``x[t + 1:t + W + 1] - x[t]`` from normalized two-dimensional focal
    positions.  With the registered ``W=10`` this has exactly 20 values.  No
    teammate, action, reward, old-skill, age, identity, or task field enters.
    """

    mean: np.ndarray
    std: np.ndarray
    zero_std: np.ndarray
    n_fit_rows: int
    window: int = 10

    def __post_init__(self) -> None:
        expected = 2 * int(self.window)
        mean = np.asarray(self.mean, dtype=np.float64)
        std = np.asarray(self.std, dtype=np.float64)
        zero_std = np.asarray(self.zero_std, dtype=bool)
        if int(self.window) != 10:
            raise ValueError("R34 uses the fixed W=10 descriptor")
        if mean.shape != (expected,) or std.shape != (expected,):
            raise ValueError("descriptor mean/std must have shape [20]")
        if zero_std.shape != (expected,):
            raise ValueError("descriptor zero_std mask must have shape [20]")
        if int(self.n_fit_rows) <= 0:
            raise ValueError("descriptor standardizer needs at least one train row")
        _require_finite("descriptor mean", mean)
        _require_finite("descriptor std", std)
        if np.any(std <= 0.0):
            raise ValueError("stored descriptor std must be strictly positive")
        object.__setattr__(self, "mean", mean.copy())
        object.__setattr__(self, "std", std.copy())
        object.__setattr__(self, "zero_std", zero_std.copy())

    @property
    def dimension(self) -> int:
        return 2 * int(self.window)

    @property
    def feature_names(self) -> tuple[str, ...]:
        return tuple(
            f"focal_d{axis}_t{step}"
            for step in range(1, int(self.window) + 1)
            for axis in ("x", "y")
        )

    @staticmethod
    def build_raw(
        normalized_focal_positions: ArrayOrTensor,
        *,
        window: int = 10,
    ) -> np.ndarray:
        """Build one or more focal-only raw descriptors.

        Input shape is ``[..., W+1, 2]`` and output shape is ``[..., 2W]``.
        Positions must already be normalized by the environment's world size.
        """

        if int(window) != 10:
            raise ValueError("R34 uses the fixed W=10 descriptor")
        positions = _as_numpy64(normalized_focal_positions)
        if positions.ndim < 2 or positions.shape[-2:] != (int(window) + 1, 2):
            raise ValueError("normalized focal positions must have shape [..., 11, 2]")
        _require_finite("normalized focal positions", positions)
        displacement = positions[..., 1:, :] - positions[..., :1, :]
        return displacement.reshape(positions.shape[:-2] + (2 * int(window),))

    @classmethod
    def fit(
        cls,
        train_raw_descriptors: ArrayOrTensor,
        *,
        window: int = 10,
        zero_std_epsilon: float = 1e-12,
    ) -> "InteractionModeDescriptor":
        """Fit the sole standardizer from train rows and freeze its statistics."""

        if int(window) != 10:
            raise ValueError("R34 uses the fixed W=10 descriptor")
        if not np.isfinite(float(zero_std_epsilon)) or float(zero_std_epsilon) < 0.0:
            raise ValueError("zero_std_epsilon must be finite and non-negative")
        matrix = _as_numpy64(train_raw_descriptors)
        if matrix.ndim != 2 or matrix.shape[0] <= 0 or matrix.shape[1] != 2 * int(window):
            raise ValueError("train descriptors must have shape [N, 20]")
        _require_finite("train descriptors", matrix)
        mean = np.mean(matrix, axis=0, dtype=np.float64)
        raw_std = np.std(matrix, axis=0, ddof=0, dtype=np.float64)
        zero_std = raw_std <= float(zero_std_epsilon)
        safe_std = np.where(zero_std, 1.0, raw_std)
        return cls(
            mean=mean,
            std=safe_std,
            zero_std=zero_std,
            n_fit_rows=int(matrix.shape[0]),
            window=int(window),
        )

    def transform(self, raw_descriptors: ArrayOrTensor) -> np.ndarray:
        matrix = _as_numpy64(raw_descriptors)
        if matrix.ndim < 1 or matrix.shape[-1] != self.dimension:
            raise ValueError("raw descriptors must have trailing shape [20]")
        _require_finite("raw descriptors", matrix)
        standardized = (matrix - self.mean) / self.std
        # Constant train columns are exactly zero on train data; the explicit
        # finite fallback also keeps all-identical mode banks valid.
        standardized = np.where(np.isfinite(standardized), standardized, 0.0)
        return standardized.astype(np.float64, copy=False)

    def build_and_transform(self, normalized_focal_positions: ArrayOrTensor) -> np.ndarray:
        return self.transform(self.build_raw(normalized_focal_positions, window=self.window))


@dataclass(frozen=True)
class BalancedPrototypeResult:
    prototypes: np.ndarray
    assignments: np.ndarray
    counts: np.ndarray
    initial_indices: np.ndarray
    iterations: int
    converged: bool
    objective: float
    seed: int


def _deterministic_kmeanspp_indices(
    matrix: np.ndarray,
    *,
    n_modes: int,
    seed: int,
) -> np.ndarray:
    """Deterministic k-means++ with an explicit duplicate-data fallback."""

    n_rows = int(matrix.shape[0])
    rng = np.random.default_rng(int(seed))
    selected = [int(rng.integers(0, n_rows))]
    chosen = np.zeros(n_rows, dtype=bool)
    chosen[selected[0]] = True
    while len(selected) < int(n_modes):
        centers = matrix[np.asarray(selected, dtype=np.int64)]
        squared = np.sum(
            (matrix[:, None, :] - centers[None, :, :]) ** 2,
            axis=-1,
            dtype=np.float64,
        )
        nearest = np.min(squared, axis=1)
        nearest[chosen] = 0.0
        total = float(np.sum(nearest, dtype=np.float64))
        if not np.isfinite(total) or total <= 0.0:
            next_index = int(np.flatnonzero(~chosen)[0])
        else:
            threshold = float(rng.random()) * total
            cumulative = np.cumsum(nearest, dtype=np.float64)
            next_index = int(np.searchsorted(cumulative, threshold, side="right"))
            if next_index >= n_rows or chosen[next_index] or nearest[next_index] <= 0.0:
                candidates = np.flatnonzero((~chosen) & (nearest > 0.0))
                next_index = int(candidates[0])
        selected.append(next_index)
        chosen[next_index] = True
    return np.asarray(selected, dtype=np.int64)


def _balanced_assignment(matrix: np.ndarray, centers: np.ndarray) -> np.ndarray:
    n_rows = int(matrix.shape[0])
    n_modes = int(centers.shape[0])
    if n_rows % n_modes != 0:
        raise ValueError("exact balanced assignment requires N divisible by K")
    capacity = n_rows // n_modes
    slots = np.repeat(centers, capacity, axis=0)
    cost = np.sum(
        (matrix[:, None, :] - slots[None, :, :]) ** 2,
        axis=-1,
        dtype=np.float64,
    )
    _require_finite("balanced assignment costs", cost)

    # scipy's solver is deterministic for a fixed matrix.  This tiny stable
    # row/slot perturbation additionally defines exact-cost ties; identity is
    # preferred for all-identical data and cannot alter a resolved float gap.
    scale = max(1.0, float(np.max(np.abs(cost))))
    tie_unit = np.finfo(np.float64).eps * scale * 8.0
    row_ids = np.arange(n_rows, dtype=np.float64)[:, None]
    slot_ids = np.arange(n_rows, dtype=np.float64)[None, :]
    tie = np.abs(row_ids - slot_ids) / float(max(n_rows - 1, 1))
    row_index, slot_index = linear_sum_assignment(cost + tie_unit * tie)
    if not np.array_equal(row_index, np.arange(n_rows, dtype=np.int64)):
        raise RuntimeError("balanced assignment did not cover every row")
    labels = (slot_index // capacity).astype(np.int64)
    counts = np.bincount(labels, minlength=n_modes)
    if not np.array_equal(counts, np.full(n_modes, capacity, dtype=np.int64)):
        raise RuntimeError("balanced assignment violated exact mode capacity")
    return labels


def fit_exact_balanced_prototypes(
    standardized_descriptors: ArrayOrTensor,
    *,
    n_modes: int = 4,
    seed: int = 34031,
    max_iter: int = 50,
    expected_rows: int | None = 384,
) -> BalancedPrototypeResult:
    """Fit deterministic exact-capacity prototypes in standardized space."""

    matrix = _as_numpy64(standardized_descriptors)
    if matrix.ndim != 2 or matrix.shape[0] <= 0 or matrix.shape[1] <= 0:
        raise ValueError("standardized descriptors must be a non-empty 2-D matrix")
    _require_finite("standardized descriptors", matrix)
    n_rows = int(matrix.shape[0])
    n_modes = int(n_modes)
    if n_modes != 4:
        raise ValueError("R34 fixes K=4")
    if expected_rows is not None and n_rows != int(expected_rows):
        raise ValueError(f"R34 expected {int(expected_rows)} train rows, got {n_rows}")
    if n_rows < n_modes or n_rows % n_modes != 0:
        raise ValueError("R34 rows must divide exactly across four modes")
    if int(max_iter) <= 0:
        raise ValueError("max_iter must be positive")

    initial_indices = _deterministic_kmeanspp_indices(
        matrix,
        n_modes=n_modes,
        seed=int(seed),
    )
    centers = matrix[initial_indices].copy()
    previous: np.ndarray | None = None
    converged = False
    labels = np.zeros(n_rows, dtype=np.int64)
    iterations = 0
    for iterations in range(1, int(max_iter) + 1):
        labels = _balanced_assignment(matrix, centers)
        updated = np.stack(
            [np.mean(matrix[labels == mode], axis=0, dtype=np.float64) for mode in range(n_modes)],
            axis=0,
        )
        _require_finite("balanced prototypes", updated)
        if previous is not None and np.array_equal(labels, previous):
            centers = updated
            converged = True
            break
        previous = labels.copy()
        centers = updated

    counts = np.bincount(labels, minlength=n_modes).astype(np.int64)
    expected_count = n_rows // n_modes
    if not np.array_equal(counts, np.full(n_modes, expected_count, dtype=np.int64)):
        raise RuntimeError("balanced clustering produced unequal mode counts")
    objective = float(np.sum((matrix - centers[labels]) ** 2, dtype=np.float64))
    return BalancedPrototypeResult(
        prototypes=centers.copy(),
        assignments=labels.copy(),
        counts=counts,
        initial_indices=initial_indices,
        iterations=int(iterations),
        converged=bool(converged),
        objective=objective,
        seed=int(seed),
    )


@dataclass(frozen=True)
class PrototypeAlignmentResult:
    prototypes_by_skill: np.ndarray
    aligned_assignments: np.ndarray
    prototype_to_skill: np.ndarray
    skill_to_prototype: np.ndarray
    overlap: np.ndarray
    agreement: float


def hungarian_align_to_existing_skills(
    prototypes: ArrayOrTensor,
    assignments: ArrayOrTensor,
    old_skills: ArrayOrTensor,
    *,
    n_skills: int = 4,
) -> PrototypeAlignmentResult:
    """Rename train-only prototypes to maximize agreement with old numeric z."""

    centers = _as_numpy64(prototypes)
    cluster = np.asarray(assignments, dtype=np.int64).reshape(-1)
    old = np.asarray(old_skills, dtype=np.int64).reshape(-1)
    n_skills = int(n_skills)
    if n_skills != 4 or centers.ndim != 2 or centers.shape[0] != n_skills:
        raise ValueError("R34 alignment requires four prototypes")
    if cluster.shape != old.shape or cluster.size <= 0:
        raise ValueError("train assignments and old skills must have equal non-zero length")
    if np.any(cluster < 0) or np.any(cluster >= n_skills):
        raise ValueError("prototype assignments lie outside [0, K)")
    if np.any(old < 0) or np.any(old >= n_skills):
        raise ValueError("old train skills lie outside [0, K)")
    _require_finite("prototypes", centers)

    overlap = np.zeros((n_skills, n_skills), dtype=np.int64)
    np.add.at(overlap, (cluster, old), 1)
    # One unit of overlap dominates the complete lexicographic tie code.
    base = n_skills + 1
    tie = np.asarray(
        [
            [skill * (base ** (n_skills - 1 - prototype)) for skill in range(n_skills)]
            for prototype in range(n_skills)
        ],
        dtype=np.int64,
    )
    dominance = int(np.sum(np.max(tie, axis=1))) + 1
    rows, cols = linear_sum_assignment(-overlap * dominance + tie)
    if not np.array_equal(rows, np.arange(n_skills, dtype=np.int64)):
        raise RuntimeError("Hungarian alignment omitted a prototype")
    prototype_to_skill = cols.astype(np.int64)
    if np.unique(prototype_to_skill).size != n_skills:
        raise RuntimeError("prototype-to-skill alignment is not bijective")
    skill_to_prototype = np.empty(n_skills, dtype=np.int64)
    skill_to_prototype[prototype_to_skill] = np.arange(n_skills, dtype=np.int64)
    prototypes_by_skill = centers[skill_to_prototype].copy()
    aligned = prototype_to_skill[cluster]
    agreement = float(np.mean(aligned == old))
    return PrototypeAlignmentResult(
        prototypes_by_skill=prototypes_by_skill,
        aligned_assignments=aligned.astype(np.int64, copy=False),
        prototype_to_skill=prototype_to_skill,
        skill_to_prototype=skill_to_prototype,
        overlap=overlap,
        agreement=agreement,
    )


def _best_assignment_total(
    scores: np.ndarray,
    rows: np.ndarray,
    columns: np.ndarray,
    forbidden: np.ndarray,
) -> int | None:
    if rows.size == 0:
        return 0
    sub_scores = scores[np.ix_(rows, columns)]
    sub_forbidden = forbidden[np.ix_(rows, columns)]
    bound = int(np.max(scores)) * int(scores.shape[0]) + 1
    cost = -sub_scores.astype(np.int64, copy=True)
    cost[sub_forbidden] = bound
    local_rows, local_cols = linear_sum_assignment(cost)
    if np.any(sub_forbidden[local_rows, local_cols]):
        return None
    return int(np.sum(sub_scores[local_rows, local_cols], dtype=np.int64))


def _lexicographic_max_assignment(scores: np.ndarray, forbidden: np.ndarray) -> np.ndarray:
    """Maximum-score assignment with a deterministic donor-vector tie break."""

    size = int(scores.shape[0])
    remaining_columns = list(range(size))
    donor = np.full(size, -1, dtype=np.int64)
    all_rows = np.arange(size, dtype=np.int64)
    all_columns = np.arange(size, dtype=np.int64)
    target = _best_assignment_total(scores, all_rows, all_columns, forbidden)
    if target is None:
        raise ValueError("no feasible deranged episode assignment exists")
    for row in range(size):
        remaining_rows = np.arange(row + 1, size, dtype=np.int64)
        selected = None
        for column in remaining_columns:
            if forbidden[row, column]:
                continue
            next_columns = np.asarray(
                [candidate for candidate in remaining_columns if candidate != column],
                dtype=np.int64,
            )
            remainder = _best_assignment_total(
                scores,
                remaining_rows,
                next_columns,
                forbidden,
            )
            if remainder is not None and int(scores[row, column]) + remainder == target:
                selected = int(column)
                target -= int(scores[row, column])
                break
        if selected is None:
            raise RuntimeError("failed to resolve a deterministic optimal donor")
        donor[row] = selected
        remaining_columns.remove(selected)
    return donor


@dataclass(frozen=True)
class EpisodeSequenceShamResult:
    sequences: np.ndarray
    donor_map: np.ndarray
    per_agent_hamming: np.ndarray
    total_hamming: int


def build_max_hamming_episode_sham(mode_sequences: ArrayOrTensor) -> EpisodeSequenceShamResult:
    """Derange complete episode label sequences independently per agent.

    Input and output have shape ``[episodes, agents, blocks]``.  For each agent,
    linear assignment maximizes total sequence Hamming distance subject to a
    bijective no-self donor map.  Consequently the exact sequence multiset,
    label counts, and run-length multiset are preserved.
    """

    sequences = np.asarray(mode_sequences, dtype=np.int64)
    if sequences.ndim != 3 or sequences.shape[0] < 2 or sequences.shape[1] <= 0:
        raise ValueError("mode sequences must have shape [E>=2, A, B]")
    episodes, agents, _blocks = sequences.shape
    donor_map = np.empty((episodes, agents), dtype=np.int64)
    sham = np.empty_like(sequences)
    per_agent_hamming = np.zeros(agents, dtype=np.int64)
    forbidden = np.eye(episodes, dtype=bool)
    for agent in range(agents):
        channel = sequences[:, agent, :]
        hamming = np.sum(channel[:, None, :] != channel[None, :, :], axis=-1, dtype=np.int64)
        donors = _lexicographic_max_assignment(hamming, forbidden)
        if np.any(donors == np.arange(episodes)) or np.unique(donors).size != episodes:
            raise RuntimeError("episode sham is not a derangement")
        donor_map[:, agent] = donors
        sham[:, agent, :] = channel[donors]
        per_agent_hamming[agent] = int(np.sum(hamming[np.arange(episodes), donors]))
    return EpisodeSequenceShamResult(
        sequences=sham,
        donor_map=donor_map,
        per_agent_hamming=per_agent_hamming,
        total_hamming=int(np.sum(per_agent_hamming)),
    )


def _as_actor_tensor(value: Any, *, dtype: torch.dtype, device: torch.device) -> torch.Tensor:
    if isinstance(value, torch.Tensor):
        return value.to(dtype=dtype, device=device)
    return torch.as_tensor(value, dtype=dtype, device=device)


def full_episode_distillation_loss(
    low_actor: Any,
    observations: ArrayOrTensor,
    actions: ArrayOrTensor,
    skill_labels: ArrayOrTensor,
    initial_actor_hxs: ArrayOrTensor,
    *,
    team_codes: ArrayOrTensor | None = None,
    masks: ArrayOrTensor | None = None,
    valid_steps: ArrayOrTensor | None = None,
    return_log_probs: bool = False,
) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
    """Negative full-episode recurrent action log likelihood.

    Every episode is replayed through the existing strict actor-only helper;
    no critic, reward, GAE, posterior, or environment objective is consulted.
    """

    evaluator = getattr(low_actor, "evaluate_focal_sequence_log_probs", None)
    if not callable(evaluator):
        raise TypeError("low actor lacks strict focal sequence replay")
    device = torch.device(low_actor.device)
    obs = _as_actor_tensor(observations, dtype=torch.float32, device=device)
    action = _as_actor_tensor(actions, dtype=torch.float32, device=device)
    skills = _as_actor_tensor(skill_labels, dtype=torch.long, device=device)
    hidden = _as_actor_tensor(initial_actor_hxs, dtype=torch.float32, device=device)
    if obs.ndim != 3:
        raise ValueError("full-episode observations must have shape [B, T, obs_dim]")
    batch, time_steps = int(obs.shape[0]), int(obs.shape[1])
    if action.ndim != 3 or action.shape[:2] != (batch, time_steps):
        raise ValueError("full-episode actions must have shape [B, T, action_dim]")
    if skills.shape != (batch, time_steps):
        raise ValueError("full-episode skill labels must have shape [B, T]")
    if hidden.ndim == 3 and hidden.shape[1] == 1:
        hidden = hidden[:, 0, :]
    if hidden.shape != (batch, int(low_actor.hidden_dim)):
        raise ValueError("initial actor hidden states must have shape [B, hidden_dim]")

    if team_codes is None:
        teams = torch.zeros((batch, time_steps), dtype=torch.long, device=device)
    else:
        teams = _as_actor_tensor(team_codes, dtype=torch.long, device=device)
        if teams.shape != (batch, time_steps):
            raise ValueError("team codes must have shape [B, T]")
    if masks is None:
        rnn_masks = torch.ones((batch, time_steps), dtype=torch.float32, device=device)
    else:
        rnn_masks = _as_actor_tensor(masks, dtype=torch.float32, device=device)
        if rnn_masks.shape != (batch, time_steps):
            raise ValueError("RNN masks must have shape [B, T]")
    if valid_steps is None:
        valid = torch.ones((batch, time_steps), dtype=torch.float32, device=device)
    else:
        valid = _as_actor_tensor(valid_steps, dtype=torch.float32, device=device)
        if valid.shape != (batch, time_steps):
            raise ValueError("valid-step mask must have shape [B, T]")
        if torch.any(valid < 0.0):
            raise ValueError("valid-step weights must be non-negative")

    rows = [
        evaluator(
            obs[index],
            skills[index],
            action[index],
            hidden[index],
            team_codes_seq=teams[index],
            masks_seq=rnn_masks[index],
        )
        for index in range(batch)
    ]
    log_probs = torch.stack(rows, dim=0)
    if log_probs.shape != (batch, time_steps) or not torch.isfinite(log_probs).all():
        raise RuntimeError("strict actor replay returned invalid full-episode log probabilities")
    denominator = valid.sum()
    if float(denominator.detach().item()) <= 0.0:
        raise ValueError("full-episode distillation has no valid steps")
    loss = -(log_probs * valid).sum() / denominator
    if return_log_probs:
        return loss, log_probs
    return loss


def replay_actor_prefix_hidden(
    low_actor: Any,
    observations: ArrayOrTensor,
    skill_labels: ArrayOrTensor,
    *,
    initial_actor_hxs: ArrayOrTensor | None = None,
    team_codes: ArrayOrTensor | None = None,
    masks: ArrayOrTensor | None = None,
    detach: bool = True,
) -> torch.Tensor:
    """Replay a source prefix under the current actor and return its hidden state."""

    if not callable(getattr(low_actor, "_actor_features", None)):
        raise TypeError("low actor lacks the strict actor feature path")
    device = torch.device(low_actor.device)
    obs = _as_actor_tensor(observations, dtype=torch.float32, device=device)
    skills = _as_actor_tensor(skill_labels, dtype=torch.long, device=device).reshape(-1)
    if obs.ndim != 2:
        raise ValueError("prefix observations must have shape [T, obs_dim]")
    time_steps = int(obs.shape[0])
    if skills.shape != (time_steps,):
        raise ValueError("prefix skills must have shape [T]")
    if initial_actor_hxs is None:
        state = torch.zeros((1, int(low_actor.hidden_dim)), dtype=torch.float32, device=device)
    else:
        state = _as_actor_tensor(initial_actor_hxs, dtype=torch.float32, device=device)
        if state.ndim == 1:
            state = state.unsqueeze(0)
        if state.shape != (1, int(low_actor.hidden_dim)):
            raise ValueError("prefix initial hidden state must have shape [hidden_dim]")
    if team_codes is None:
        teams = torch.zeros(time_steps, dtype=torch.long, device=device)
    else:
        teams = _as_actor_tensor(team_codes, dtype=torch.long, device=device).reshape(-1)
        if teams.shape != (time_steps,):
            raise ValueError("prefix team codes must have shape [T]")
    if masks is None:
        rnn_masks = torch.ones(time_steps, dtype=torch.float32, device=device)
    else:
        rnn_masks = _as_actor_tensor(masks, dtype=torch.float32, device=device).reshape(-1)
        if rnn_masks.shape != (time_steps,):
            raise ValueError("prefix masks must have shape [T]")

    context = torch.no_grad() if detach else torch.enable_grad()
    with context:
        recurrent_state = state
        for step in range(time_steps):
            features = low_actor._actor_features(
                obs[step : step + 1],
                skills[step : step + 1],
                teams[step : step + 1],
            )
            _output, recurrent_state = low_actor.actor_rnn(
                features,
                recurrent_state,
                rnn_masks[step].reshape(1, 1),
            )
    return recurrent_state.detach() if detach else recurrent_state


def nearest_prototype(
    standardized_descriptors: ArrayOrTensor,
    prototypes_by_skill: ArrayOrTensor,
    *,
    return_distances: bool = False,
) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
    """Assign frozen standardized descriptors to the nearest numeric skill."""

    values = _as_numpy64(standardized_descriptors)
    prototypes = _as_numpy64(prototypes_by_skill)
    if values.ndim < 1 or prototypes.ndim != 2 or values.shape[-1] != prototypes.shape[1]:
        raise ValueError("descriptor/prototype dimensions do not match")
    if prototypes.shape[0] != 4:
        raise ValueError("R34 requires four numeric-skill prototypes")
    _require_finite("standardized descriptors", values)
    _require_finite("prototypes", prototypes)
    distances = np.sum(
        (values[..., None, :] - prototypes) ** 2,
        axis=-1,
        dtype=np.float64,
    )
    labels = np.argmin(distances, axis=-1).astype(np.int64)
    if return_distances:
        return labels, distances
    return labels


@dataclass(frozen=True)
class ModeFidelityResult:
    fidelity: float
    per_skill: np.ndarray
    counts: np.ndarray
    correct: np.ndarray
    assignments: np.ndarray


def causal_mode_fidelity(
    standardized_descriptors: ArrayOrTensor,
    forced_skills: ArrayOrTensor,
    prototypes_by_skill: ArrayOrTensor,
) -> ModeFidelityResult:
    """Measure whether do(z) trajectories return to numeric prototype z."""

    assignments = np.asarray(
        nearest_prototype(standardized_descriptors, prototypes_by_skill),
        dtype=np.int64,
    )
    targets = np.asarray(forced_skills, dtype=np.int64)
    if assignments.shape != targets.shape or assignments.size <= 0:
        raise ValueError("forced skill labels must match descriptor leading shape")
    if np.any(targets < 0) or np.any(targets >= 4):
        raise ValueError("forced skills lie outside [0, 4)")
    flat_target = targets.reshape(-1)
    flat_assignment = assignments.reshape(-1)
    counts = np.bincount(flat_target, minlength=4).astype(np.int64)
    correct = np.bincount(
        flat_target,
        weights=(flat_assignment == flat_target).astype(np.int64),
        minlength=4,
    ).astype(np.int64)
    per_skill = np.divide(
        correct,
        counts,
        out=np.full(4, np.nan, dtype=np.float64),
        where=counts > 0,
    )
    return ModeFidelityResult(
        fidelity=float(np.mean(flat_assignment == flat_target)),
        per_skill=per_skill,
        counts=counts,
        correct=correct,
        assignments=assignments,
    )


@dataclass(frozen=True)
class ModeSeparationResult:
    between: np.ndarray
    within: np.ndarray
    ratio: np.ndarray
    median_ratio: float


def between_within_mode_ratio(
    forced_standardized_descriptors: ArrayOrTensor,
    *,
    epsilon: float = 1e-8,
) -> ModeSeparationResult:
    """Persistent between/within mode SNR in frozen standardized space.

    Input shape is ``[..., K=4, replicas=2, descriptor_dim]``.  Leading axes
    are preserved in all returned arrays.
    """

    if not np.isfinite(float(epsilon)) or float(epsilon) <= 0.0:
        raise ValueError("epsilon must be finite and positive")
    values = _as_numpy64(forced_standardized_descriptors)
    if values.ndim < 3 or values.shape[-3] != 4 or values.shape[-2] != 2:
        raise ValueError("forced descriptors must have shape [..., 4, 2, D]")
    if values.shape[-1] <= 0:
        raise ValueError("forced descriptor dimension must be positive")
    _require_finite("forced standardized descriptors", values)
    replica_mean = np.mean(values, axis=-2, dtype=np.float64)
    pair_values = []
    for left in range(4):
        for right in range(left + 1, 4):
            difference = replica_mean[..., left, :] - replica_mean[..., right, :]
            pair_values.append(np.sum(difference * difference, axis=-1, dtype=np.float64))
    between = np.mean(np.stack(pair_values, axis=-1), axis=-1, dtype=np.float64)
    replica_difference = values[..., :, 0, :] - values[..., :, 1, :]
    within_by_skill = 0.5 * np.sum(
        replica_difference * replica_difference,
        axis=-1,
        dtype=np.float64,
    )
    within = np.mean(within_by_skill, axis=-1, dtype=np.float64)
    ratio = between / (within + float(epsilon))
    return ModeSeparationResult(
        between=np.asarray(between, dtype=np.float64),
        within=np.asarray(within, dtype=np.float64),
        ratio=np.asarray(ratio, dtype=np.float64),
        median_ratio=float(np.median(ratio)),
    )


def _contains_parameter_path(name: str, prefix: str) -> bool:
    path = str(prefix).strip(".")
    if not path:
        raise ValueError("allowed parameter prefixes must be non-empty")
    name_parts = str(name).split(".")
    path_parts = path.split(".")
    width = len(path_parts)
    return any(
        name_parts[index : index + width] == path_parts
        for index in range(len(name_parts) - width + 1)
    )


def parameter_drift_metrics(
    before: Mapping[str, ArrayOrTensor],
    after: Mapping[str, ArrayOrTensor],
    *,
    allowed_prefixes: Sequence[str] = DEFAULT_ALLOWED_PREFIXES,
    epsilon: float = 1e-12,
) -> dict[str, Any]:
    """Measure drift in R34's allowed actor subset and every frozen parameter."""

    if not np.isfinite(float(epsilon)) or float(epsilon) <= 0.0:
        raise ValueError("epsilon must be finite and positive")
    prefixes = tuple(str(prefix).strip(".") for prefix in allowed_prefixes)
    if not prefixes or any(not prefix for prefix in prefixes):
        raise ValueError("allowed_prefixes must be non-empty")
    before_names = set(before)
    after_names = set(after)
    if before_names != after_names:
        raise ValueError(
            f"parameter sets differ: missing_after={sorted(before_names-after_names)}, "
            f"added_after={sorted(after_names-before_names)}"
        )
    if not before_names:
        raise ValueError("parameter mappings must be non-empty")

    group_names = ("all", "allowed", "other") + tuple(f"prefix:{prefix}" for prefix in prefixes)
    totals = {
        group: {"base_sq": 0.0, "delta_sq": 0.0, "max_abs": 0.0, "count": 0}
        for group in group_names
    }
    per_parameter: dict[str, dict[str, Any]] = {}
    matched_prefixes: set[str] = set()
    for name in sorted(before_names):
        before_value = _as_numpy64(before[name])
        after_value = _as_numpy64(after[name])
        if before_value.shape != after_value.shape:
            raise ValueError(f"parameter {name!r} changed shape")
        _require_finite(f"parameter {name!r} before", before_value)
        _require_finite(f"parameter {name!r} after", after_value)
        delta = after_value - before_value
        base_sq = float(np.sum(before_value * before_value, dtype=np.float64))
        delta_sq = float(np.sum(delta * delta, dtype=np.float64))
        max_abs = float(np.max(np.abs(delta))) if delta.size else 0.0
        matches = tuple(prefix for prefix in prefixes if _contains_parameter_path(name, prefix))
        if len(matches) > 1:
            raise ValueError(f"parameter {name!r} matches multiple allowed prefixes {matches}")
        allowed = bool(matches)
        if matches:
            matched_prefixes.add(matches[0])
        groups = ["all", "allowed" if allowed else "other"]
        if matches:
            groups.append(f"prefix:{matches[0]}")
        for group in groups:
            totals[group]["base_sq"] += base_sq
            totals[group]["delta_sq"] += delta_sq
            totals[group]["max_abs"] = max(float(totals[group]["max_abs"]), max_abs)
            totals[group]["count"] += int(delta.size)
        l2 = float(np.sqrt(delta_sq))
        per_parameter[name] = {
            "allowed": allowed,
            "allowed_prefix": matches[0] if matches else None,
            "count": int(delta.size),
            "max_abs": max_abs,
            "l2": l2,
            "relative_l2": l2 / (float(np.sqrt(base_sq)) + float(epsilon)),
        }
    missing_prefixes = sorted(set(prefixes) - matched_prefixes)
    if missing_prefixes:
        raise ValueError(f"allowed parameter prefixes not found: {missing_prefixes}")

    result: dict[str, Any] = {
        "allowed_prefixes": list(prefixes),
        "parameters": per_parameter,
        "allowed_parameter_names": [name for name in sorted(before_names) if per_parameter[name]["allowed"]],
        "other_parameter_names": [name for name in sorted(before_names) if not per_parameter[name]["allowed"]],
    }
    for group, values in totals.items():
        base_l2 = float(np.sqrt(float(values["base_sq"])))
        drift_l2 = float(np.sqrt(float(values["delta_sq"])))
        key = group.replace("prefix:", "prefix_").replace(".", "_")
        result[f"{key}_parameter_count"] = int(values["count"])
        result[f"{key}_max_abs"] = float(values["max_abs"])
        result[f"{key}_l2"] = drift_l2
        result[f"{key}_relative_l2"] = drift_l2 / (base_l2 + float(epsilon))
    return result


__all__ = [
    "BalancedPrototypeResult",
    "DEFAULT_ALLOWED_PREFIXES",
    "EpisodeSequenceShamResult",
    "InteractionModeDescriptor",
    "ModeFidelityResult",
    "ModeSeparationResult",
    "PrototypeAlignmentResult",
    "between_within_mode_ratio",
    "build_max_hamming_episode_sham",
    "causal_mode_fidelity",
    "fit_exact_balanced_prototypes",
    "full_episode_distillation_loss",
    "hungarian_align_to_existing_skills",
    "nearest_prototype",
    "parameter_drift_metrics",
    "replay_actor_prefix_hidden",
]
