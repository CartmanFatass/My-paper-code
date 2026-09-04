"""Exact role-sampled full-suffix (RSCF) FRRIE update semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Mapping, Sequence

from .contracts.core import ContractError, FP32_PROBABILITY_TOLERANCE
from .policy import FRRIEActorCritic, TORCH_AVAILABLE, require_torch

if TORCH_AVAILABLE:
    import torch


TRAIN_EPISODES_PER_UPDATE: Final[int] = 64
TRAIN_ROSTER_COUNTS: Final[dict[int, int]] = {9: 32, 15: 32}
TRAIN_ROSTER_ORDER: Final[tuple[int, ...]] = (9, 15) * 32
SLOTS_PER_EPISODE: Final[int] = 12
ENTROPY_COEFFICIENT: Final[float] = 0.01
CRITIC_COEFFICIENT: Final[float] = 0.5
GRADIENT_CLIP_NORM: Final[float] = 0.5
ROLE_ORDER: Final[tuple[str, str, str]] = (
    "WEST-SURVEYOR", "EAST-SURVEYOR", "RIDGE-RELAY",
)


@dataclass(frozen=True)
class RSCFEpisode:
    """Complete differentiable factual episode plus stopped RSCF targets.

    ``selected_probabilities`` contains the three factual policy rows at the
    one preselected W/E/R origins. ``q_targets`` contains all legal full-suffix
    action targets; illegal columns are ignored. ``all_probabilities`` is the
    factual [12,N,6] graph used only for the inherited entropy term.
    """

    roster_size: int
    selected_probabilities: Any
    q_targets: Any
    legal_masks: Any
    factual_actions: Any
    all_probabilities: Any
    critic_values: Any
    terminal_return: Any


@dataclass(frozen=True)
class LossTerms:
    loss: Any
    score: Any
    entropy: Any
    critic: Any
    baselines: Any
    advantages: Any


@dataclass(frozen=True)
class LossReductionReceipt:
    """Detached bit provenance for the unchanged 64-episode FP32 reduction."""

    schema: str
    component_order: tuple[str, ...]
    roster_order: tuple[int, ...]
    per_episode_u32_bits: tuple[tuple[int, ...], ...]
    reduction_law: str
    divisor: int
    dtype: str
    aggregate_u32_bits: tuple[int, ...]


def exact_loss_reduction_contract() -> dict[str, Any]:
    return {
        "schema": "FRRIE_RSCF_LOSS_REDUCTION_CONTRACT_V1",
        "component_order": ["loss", "score", "entropy", "critic"],
        "roster_order": list(TRAIN_ROSTER_ORDER),
        "reduction_law": "PYTHON_SUM_INT0_LEFT_FOLD_THEN_DIVIDE_FLOAT64_LITERAL_64",
        "divisor": TRAIN_EPISODES_PER_UPDATE,
        "dtype": "CPU_FP32",
        "episode_axis": TRAIN_EPISODES_PER_UPDATE,
    }


@dataclass(frozen=True)
class UpdateReceipt:
    loss: float
    preclip_global_norm: float
    backward_calls: int
    optimizer_steps: int
    episodes: int
    roster_counts: dict[int, int]
    projection_after_step: bool


def _require_tensor(name: str, value: Any) -> None:
    if not isinstance(value, torch.Tensor):
        raise ContractError(f"{name} must be a Torch tensor")
    if value.device.type != "cpu":
        raise ContractError(f"{name} must remain on CPU")


def _validate_episode(episode: RSCFEpisode) -> None:
    if not isinstance(episode, RSCFEpisode):
        raise ContractError("RSCF loss requires a complete RSCFEpisode")
    if type(episode.roster_size) is not int or episode.roster_size not in TRAIN_ROSTER_COUNTS:
        raise ContractError("training roster must be exactly 9 or 15")
    for name in (
        "selected_probabilities", "q_targets", "legal_masks", "factual_actions",
        "all_probabilities", "critic_values", "terminal_return",
    ):
        _require_tensor(name, getattr(episode, name))

    probabilities = episode.selected_probabilities
    targets = episode.q_targets
    legal = episode.legal_masks
    factual = episode.factual_actions
    all_probabilities = episode.all_probabilities
    values = episode.critic_values
    terminal = episode.terminal_return

    if probabilities.shape != (3, 6) or probabilities.dtype != torch.float32:
        raise ContractError("selected origin probabilities must be FP32 [3,6] in W/E/R order")
    if targets.shape != (3, 6) or targets.dtype != torch.float32:
        raise ContractError("selected all-action Q targets must be FP32 [3,6]")
    if legal.shape != (3, 6) or legal.dtype != torch.bool:
        raise ContractError("selected origin legal masks must be bool [3,6]")
    if factual.shape != (3,) or factual.dtype != torch.int64:
        raise ContractError("factual actions must be int64 [3]")
    expected_legal = torch.tensor(
        ((1, 1, 0, 0, 0, 1), (1, 1, 0, 0, 0, 1), (0, 0, 1, 1, 1, 1)),
        dtype=torch.bool,
    )
    if not bool(torch.equal(legal, expected_legal)):
        raise ContractError("one W/E/R origin must use the exact frozen role masks")
    factual_legal = legal.gather(1, factual[:, None]).squeeze(1)
    if bool(((factual < 0) | (factual >= 6)).any().item()) or not bool(factual_legal.all().item()):
        raise ContractError("each factual focal action must be legal")
    if not bool(torch.isfinite(targets[legal]).all().item()):
        raise ContractError("every legal focal action requires a finite full-suffix target")
    if targets.requires_grad or terminal.requires_grad:
        raise ContractError("counterfactual targets and terminal return must be graph-detached")
    if not bool(torch.isfinite(probabilities).all().item()):
        raise ContractError("selected factual probabilities must be finite")
    if bool((probabilities < 0.0).any().item()) or not bool(
        torch.allclose(
            probabilities.sum(dim=1), torch.ones(3),
            atol=FP32_PROBABILITY_TOLERANCE, rtol=0.0,
        )
    ):
        raise ContractError("selected policy rows must be nonnegative and sum to one")
    if not bool((probabilities.masked_select(~legal) == 0.0).all().item()):
        raise ContractError("illegal selected-action probabilities must be exactly zero")
    floors = 0.04 / legal.sum(dim=1).to(torch.float32)
    if bool((probabilities.masked_select(legal).reshape(-1) <= 0.0).any().item()):
        raise ContractError("legal selected actions require positive probability")
    for role in range(3):
        if bool((probabilities[role, legal[role]] < floors[role]).any().item()):
            raise ContractError("selected policy violates the exact legal-uniform floor")

    if all_probabilities.shape != (SLOTS_PER_EPISODE, episode.roster_size, 6):
        raise ContractError("factual entropy probabilities must have shape [12,N,6]")
    if all_probabilities.dtype != torch.float32 or not bool(
        torch.isfinite(all_probabilities).all().item()
    ):
        raise ContractError("factual entropy probabilities must be finite FP32")
    if bool((all_probabilities < 0.0).any().item()) or not bool(
        torch.allclose(
            all_probabilities.sum(dim=2),
            torch.ones((SLOTS_PER_EPISODE, episode.roster_size)),
            atol=FP32_PROBABILITY_TOLERANCE,
            rtol=0.0,
        )
    ):
        raise ContractError("each factual agent-slot policy row must sum to one")
    if values.shape != (SLOTS_PER_EPISODE,) or values.dtype != torch.float32:
        raise ContractError("critic values must be FP32 [12]")
    if terminal.ndim != 0 or terminal.dtype != torch.float32 or not bool(
        torch.isfinite(terminal).item()
    ):
        raise ContractError("terminal return must be one finite FP32 scalar")


def rscf_episode_loss(episode: RSCFEpisode) -> LossTerms:
    """Compute one equally weighted episode loss with fully stopped targets."""

    require_torch()
    _validate_episode(episode)
    probabilities = episode.selected_probabilities
    legal = episode.legal_masks
    targets = episode.q_targets

    stopped_policy = probabilities.detach()
    stopped_targets = targets.detach()
    baselines = (stopped_policy * torch.where(legal, stopped_targets, 0.0)).sum(dim=1)
    advantages = (episode.terminal_return.detach() - baselines).detach()
    factual_probabilities = probabilities.gather(
        1, episode.factual_actions[:, None]
    ).squeeze(1)
    score = -(torch.log(factual_probabilities) * advantages).sum() / 3.0

    # Illegal columns are structural zeros.  Clamp only the logarithm operand
    # so their value stays 0 and their zero policy Jacobian cannot encounter
    # xlogy's undefined 0/0 derivative.  Every legal probability is >=.01.
    entropy_rows = -(
        episode.all_probabilities
        * torch.log(episode.all_probabilities.clamp_min(torch.finfo(torch.float32).tiny))
    ).sum(dim=2)
    entropy = entropy_rows.mean()
    critic = torch.mean(
        (episode.critic_values - episode.terminal_return.detach()) ** 2
    )
    loss = score - ENTROPY_COEFFICIENT * entropy + CRITIC_COEFFICIENT * critic
    return LossTerms(loss, score, entropy, critic, baselines, advantages)


def validate_update_batch(episodes: Sequence[RSCFEpisode]) -> dict[int, int]:
    require_torch()
    if len(episodes) != TRAIN_EPISODES_PER_UPDATE:
        raise ContractError("each FRRIE update requires exactly 64 complete episodes")
    counts = {9: 0, 15: 0}
    identities: set[int] = set()
    for episode in episodes:
        if id(episode) in identities:
            raise ContractError("an episode object cannot receive duplicate batch weight")
        identities.add(id(episode))
        _validate_episode(episode)
        counts[episode.roster_size] += 1
    if counts != TRAIN_ROSTER_COUNTS:
        raise ContractError("each update requires exactly 32 N=9 and 32 N=15 episodes")
    actual_order = tuple(episode.roster_size for episode in episodes)
    if actual_order != TRAIN_ROSTER_ORDER:
        raise ContractError("the 64-position training roster order must alternate N=9,N=15")
    return counts


def _rscf_batch_loss_with_receipt(
    episodes: Sequence[RSCFEpisode],
) -> tuple[LossTerms, LossReductionReceipt]:
    """One unchanged graph pass plus detached exact reduction provenance."""

    validate_update_batch(episodes)
    terms = [rscf_episode_loss(episode) for episode in episodes]
    divisor = float(TRAIN_EPISODES_PER_UPDATE)
    aggregate = LossTerms(
        loss=sum(term.loss for term in terms) / divisor,
        score=sum(term.score for term in terms) / divisor,
        entropy=sum(term.entropy for term in terms) / divisor,
        critic=sum(term.critic for term in terms) / divisor,
        baselines=torch.stack([term.baselines for term in terms]),
        advantages=torch.stack([term.advantages for term in terms]),
    )
    component_order = ("loss", "score", "entropy", "critic")

    def bits(value: Any) -> int:
        return int(value.detach().contiguous().view(torch.int32).item()) & 0xFFFFFFFF

    receipt = LossReductionReceipt(
        schema="FRRIE_RSCF_LOSS_REDUCTION_RECEIPT_V1",
        component_order=component_order,
        roster_order=tuple(episode.roster_size for episode in episodes),
        per_episode_u32_bits=tuple(
            tuple(bits(getattr(term, name)) for name in component_order)
            for term in terms
        ),
        reduction_law="PYTHON_SUM_INT0_LEFT_FOLD_THEN_DIVIDE_FLOAT64_LITERAL_64",
        divisor=TRAIN_EPISODES_PER_UPDATE,
        dtype="CPU_FP32",
        aggregate_u32_bits=tuple(bits(getattr(aggregate, name)) for name in component_order),
    )
    return aggregate, receipt


def rscf_batch_loss(episodes: Sequence[RSCFEpisode]) -> LossTerms:
    """Average 64 losses with the original graph/order; discard provenance."""

    return _rscf_batch_loss_with_receipt(episodes)[0]


def validate_loss_reduction_receipt(
    value: Any, *, aggregate_scalars: Mapping[str, Any],
) -> dict[str, Any]:
    """Replay composite and left-fold arithmetic exactly on CPU FP32 bits."""

    import numpy as np

    expected_fields = {
        "schema", "component_order", "roster_order", "per_episode_u32_bits",
        "reduction_law", "divisor", "dtype", "aggregate_u32_bits",
    }
    if not isinstance(value, Mapping) or set(value) != expected_fields:
        raise ContractError("loss reduction receipt fields differ")
    receipt = dict(value)
    component_order = ("loss", "score", "entropy", "critic")
    if (
        receipt["schema"] != "FRRIE_RSCF_LOSS_REDUCTION_RECEIPT_V1"
        or tuple(receipt["component_order"]) != component_order
        or tuple(receipt["roster_order"]) != TRAIN_ROSTER_ORDER
        or receipt["reduction_law"]
        != "PYTHON_SUM_INT0_LEFT_FOLD_THEN_DIVIDE_FLOAT64_LITERAL_64"
        or receipt["divisor"] != TRAIN_EPISODES_PER_UPDATE
        or receipt["dtype"] != "CPU_FP32"
        or not isinstance(receipt["per_episode_u32_bits"], (list, tuple))
        or len(receipt["per_episode_u32_bits"]) != TRAIN_EPISODES_PER_UPDATE
        or not isinstance(receipt["aggregate_u32_bits"], (list, tuple))
        or len(receipt["aggregate_u32_bits"]) != len(component_order)
        or any(
            type(item) is not int or not 0 <= item <= 0xFFFFFFFF
            for item in receipt["aggregate_u32_bits"]
        )
        or not isinstance(aggregate_scalars, Mapping)
        or set(aggregate_scalars) != set(component_order)
        or any(
            type(aggregate_scalars[name]) not in (int, float)
            or not np.isfinite(aggregate_scalars[name])
            for name in component_order
        )
    ):
        raise ContractError("loss reduction receipt identity/order differs")

    rows = []
    for row in receipt["per_episode_u32_bits"]:
        if (
            not isinstance(row, (list, tuple)) or len(row) != len(component_order)
            or any(type(item) is not int or not 0 <= item <= 0xFFFFFFFF for item in row)
        ):
            raise ContractError("loss reduction episode bit row differs")
        tensor = torch.from_numpy(
            np.asarray(row, dtype="<u4").view("<f4").copy(),
        )
        if not bool(torch.isfinite(tensor).all().item()):
            raise ContractError("loss reduction episode components are nonfinite")
        composite = (
            tensor[1] - ENTROPY_COEFFICIENT * tensor[2]
            + CRITIC_COEFFICIENT * tensor[3]
        )
        composite_bits = int(composite.view(torch.int32).item()) & 0xFFFFFFFF
        if composite_bits != row[0]:
            raise ContractError("loss reduction episode composite bits differ")
        rows.append(tensor)

    aggregates = tuple(
        sum(row[column] for row in rows) / float(TRAIN_EPISODES_PER_UPDATE)
        for column in range(len(component_order))
    )
    aggregate_bits = tuple(
        int(item.contiguous().view(torch.int32).item()) & 0xFFFFFFFF
        for item in aggregates
    )
    if tuple(receipt["aggregate_u32_bits"]) != aggregate_bits:
        raise ContractError("loss reduction aggregate bits differ")
    scalar_bits = tuple(
        int(np.asarray([aggregate_scalars[name]], dtype="<f4").view("<u4")[0])
        for name in component_order
    )
    if scalar_bits != aggregate_bits:
        raise ContractError("loss reduction receipt scalar bits differ")
    return {
        **receipt,
        "component_order": list(component_order),
        "roster_order": list(TRAIN_ROSTER_ORDER),
        "per_episode_u32_bits": [list(row) for row in receipt["per_episode_u32_bits"]],
        "aggregate_u32_bits": list(aggregate_bits),
        "exact_replay_validated": True,
    }


def make_optimizer(model: FRRIEActorCritic) -> Any:
    """Create the sole authorized projected-Adam optimizer."""

    require_torch()
    if not isinstance(model, FRRIEActorCritic):
        raise ContractError("optimizer requires the fresh FRRIE actor/critic")
    return torch.optim.Adam(
        model.ordered_parameters(),
        lr=3.0e-4,
        betas=(0.9, 0.999),
        eps=1.0e-8,
        weight_decay=0.0,
        amsgrad=False,
        maximize=False,
        foreach=False,
        capturable=False,
        differentiable=False,
        fused=None,
    )


class RSCFTrainer:
    """One-call transaction for one full-batch backward/Adam/project update."""

    def __init__(self, model: FRRIEActorCritic, optimizer: Any | None = None) -> None:
        require_torch()
        if not isinstance(model, FRRIEActorCritic):
            raise ContractError("trainer requires the fresh FRRIE actor/critic")
        self.model = model
        self.optimizer = make_optimizer(model) if optimizer is None else optimizer
        self._validate_optimizer()

    def _validate_optimizer(self) -> None:
        if not isinstance(self.optimizer, torch.optim.Adam):
            raise ContractError("FRRIE optimizer must be Torch Adam")
        if len(self.optimizer.param_groups) != 1:
            raise ContractError("FRRIE Adam requires one common parameter group")
        group = self.optimizer.param_groups[0]
        expected = self.model.ordered_parameters()
        actual = tuple(group["params"])
        if len(actual) != len(expected) or any(a is not b for a, b in zip(actual, expected)):
            raise ContractError("Adam parameter order differs from LAYER_SHAPES")
        exact = (
            group["lr"] == 3.0e-4 and group["betas"] == (0.9, 0.999)
            and group["eps"] == 1.0e-8 and group["weight_decay"] == 0.0
            and group["amsgrad"] is False and group.get("maximize") is False
            and group.get("capturable") is False
            and group.get("differentiable") is False
            and group.get("foreach") is False
            and group.get("fused") in (None, False)
            and group.get("decoupled_weight_decay", False) is False
        )
        if not exact:
            raise ContractError("Adam hyperparameters differ from the frozen FRRIE update")

    def update(self, episodes: Sequence[RSCFEpisode]) -> UpdateReceipt:
        roster_counts = validate_update_batch(episodes)
        self._validate_optimizer()
        self.optimizer.zero_grad(set_to_none=True)
        terms = rscf_batch_loss(episodes)
        if not bool(torch.isfinite(terms.loss).item()) or not terms.loss.requires_grad:
            raise ContractError("full-batch loss must be finite and differentiable")

        backward_calls = 0
        terms.loss.backward()
        backward_calls += 1
        parameters = self.model.ordered_parameters()
        missing = [name for (name, _), parameter in zip(self.model.named_parameters(), parameters)
                   if parameter.grad is None]
        if missing:
            raise ContractError(f"parameters missing gradients after full backward: {missing}")
        if any(not bool(torch.isfinite(parameter.grad).all().item()) for parameter in parameters):
            raise ContractError("nonfinite gradient in the full FRRIE inventory")
        preclip = torch.nn.utils.clip_grad_norm_(
            parameters, GRADIENT_CLIP_NORM, norm_type=2.0,
            error_if_nonfinite=True, foreach=False,
        )
        optimizer_steps = 0
        self.optimizer.step()
        optimizer_steps += 1
        # Projection is deliberately after Adam; optimizer moments are untouched.
        self.model.project_beta()
        return UpdateReceipt(
            loss=float(terms.loss.detach().item()),
            preclip_global_norm=float(preclip.detach().item()),
            backward_calls=backward_calls,
            optimizer_steps=optimizer_steps,
            episodes=TRAIN_EPISODES_PER_UPDATE,
            roster_counts=roster_counts,
            projection_after_step=True,
        )
