"""RNG-neutral deterministic model/conformance surfaces for TBCFV r04."""

from __future__ import annotations

import math
from dataclasses import dataclass
from collections.abc import Mapping, Sequence

import torch
from torch import nn

from .config import (
    BASELINE_DECAY,
    EPISODES_PER_CELL,
    FLEX,
    GRADIENT_DIRECTION_SCALE,
    LEARNED_PACKAGES,
    LEARNING_RATE,
    NONZERO_UPDATE_NORM,
    REGISTERED,
    TRAIN_CELLS,
    TRAIN_EPISODES_PER_BLOCK,
)


class DeterministicZeroLinear(nn.Linear):
    """A Linear layer whose construction consumes no global Torch RNG state."""

    def reset_parameters(self) -> None:
        with torch.no_grad():
            self.weight.zero_()
            if self.bias is not None:
                self.bias.zero_()


class SetEncoder(nn.Module):
    """Shared-shape 3-32-32 tanh element encoder with masked mean pooling."""

    def __init__(self) -> None:
        super().__init__()
        self.first = DeterministicZeroLinear(3, 32, dtype=torch.float64)
        self.second = DeterministicZeroLinear(32, 32, dtype=torch.float64)

    def forward(self, elements: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        if elements.ndim < 2 or elements.shape[-1] != 3:
            raise ValueError("set elements must have shape [..., set_size, 3]")
        encoded = torch.tanh(self.second(torch.tanh(self.first(elements.to(torch.float64)))))
        if mask is None:
            if elements.shape[-2] == 0:
                raise ValueError("set must be nonempty")
            return encoded.mean(dim=-2)
        mask_t = mask.to(device=encoded.device, dtype=encoded.dtype)
        if tuple(mask_t.shape) != tuple(elements.shape[:-1]):
            raise ValueError("mask must match element leading/set dimensions")
        count = mask_t.sum(dim=-1, keepdim=True)
        if bool((count <= 0).any()):
            raise ValueError("every pooled set must contain at least one element")
        return (encoded * mask_t[..., None]).sum(dim=-2) / count


@dataclass(frozen=True)
class ManagerOutput:
    mean: torch.Tensor
    raw_log_scale: torch.Tensor
    log_scale: torch.Tensor
    scale: torch.Tensor
    pooled_summary: torch.Tensor
    public_summary: torch.Tensor


class TBCFVModel(nn.Module):
    """The exact common maximum 26,161-scalar arm inventory."""

    def __init__(self) -> None:
        super().__init__()
        self.agent_encoder = SetEncoder()
        self.beacon_encoder = SetEncoder()
        self.manager_first = DeterministicZeroLinear(68, 64, dtype=torch.float64)
        self.manager_second = DeterministicZeroLinear(64, 64, dtype=torch.float64)
        self.manager_mean = DeterministicZeroLinear(64, 4, dtype=torch.float64)
        self.manager_raw_log_scale = DeterministicZeroLinear(64, 4, dtype=torch.float64)

        self.pointer_first = DeterministicZeroLinear(81, 64, dtype=torch.float64)
        self.pointer_second = DeterministicZeroLinear(64, 64, dtype=torch.float64)
        self.pointer_score = DeterministicZeroLinear(64, 1, dtype=torch.float64)

        self.common_update_hidden = DeterministicZeroLinear(72, 32, dtype=torch.float64)
        self.common_update_final = DeterministicZeroLinear(32, 4, dtype=torch.float64)
        self.agent_update_hidden = DeterministicZeroLinear(81, 32, dtype=torch.float64)
        self.agent_update_final = DeterministicZeroLinear(32, 4, dtype=torch.float64)

        if self.parameter_count != REGISTERED.parameters_per_arm:
            raise RuntimeError(
                f"model inventory is {self.parameter_count}, expected {REGISTERED.parameters_per_arm}"
            )

    @property
    def parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())

    def manager(
        self,
        agent_elements: torch.Tensor,
        beacon_elements: torch.Tensor,
        public_context: torch.Tensor,
        agent_mask: torch.Tensor | None = None,
        beacon_mask: torch.Tensor | None = None,
    ) -> ManagerOutput:
        """Return the epoch-start Normal and both unchanged public set summaries.

        ``public_context`` is exactly ``(N/12, t/64, roster_event, new_epoch)``.
        """

        agent = self.agent_encoder(agent_elements, agent_mask)
        beacon = self.beacon_encoder(beacon_elements, beacon_mask)
        pooled = torch.cat((agent, beacon), dim=-1)
        context = public_context.to(device=pooled.device, dtype=torch.float64)
        if context.shape[:-1] != pooled.shape[:-1] or context.shape[-1] != 4:
            raise ValueError("public_context must align with sets and have final dimension 4")
        public = torch.cat((pooled, context), dim=-1)
        hidden = torch.tanh(self.manager_second(torch.tanh(self.manager_first(public))))
        mean = self.manager_mean(hidden)
        raw = self.manager_raw_log_scale(hidden)
        log_scale = -2.0 + 2.0 * torch.sigmoid(raw)
        return ManagerOutput(
            mean=mean,
            raw_log_scale=raw,
            log_scale=log_scale,
            scale=torch.exp(log_scale),
            pooled_summary=pooled,
            public_summary=public,
        )

    def pointer_logits(self, pointer_inputs: torch.Tensor) -> torch.Tensor:
        if pointer_inputs.shape[-1] != REGISTERED.pointer_input:
            raise ValueError("pointer inputs must have final dimension 81")
        values = pointer_inputs.to(torch.float64)
        return self.pointer_score(
            torch.tanh(self.pointer_second(torch.tanh(self.pointer_first(values))))
        ).squeeze(-1)

    def claim_probabilities(self, pointer_inputs: torch.Tensor) -> torch.Tensor:
        if pointer_inputs.shape[-2] != REGISTERED.beacons:
            raise ValueError("pointer candidate dimension must contain exactly six beacons")
        return torch.softmax(self.pointer_logits(pointer_inputs), dim=-1)

    def common_update(self, old_plan: torch.Tensor, public_event_summary: torch.Tensor) -> torch.Tensor:
        old = old_plan.detach().to(torch.float64)
        event = public_event_summary.to(device=old.device, dtype=torch.float64)
        values = torch.cat((old, event), dim=-1)
        if values.shape[-1] != REGISTERED.common_update_input:
            raise ValueError("common update requires old plan [4] plus public event summary [68]")
        return self.common_update_final(torch.tanh(self.common_update_hidden(values)))

    def agent_update(
        self,
        old_plan: torch.Tensor,
        public_event_summary: torch.Tensor,
        physical_features: torch.Tensor,
        event_noise: torch.Tensor,
    ) -> torch.Tensor:
        old = old_plan.detach().to(torch.float64)
        event = public_event_summary.to(device=old.device, dtype=torch.float64)
        physical = physical_features.to(device=old.device, dtype=torch.float64)
        noise = event_noise.detach().to(device=old.device, dtype=torch.float64)
        values = torch.cat((old, event, physical, noise), dim=-1)
        if values.shape[-1] != REGISTERED.agent_update_input:
            raise ValueError(
                "agent update requires old plan [4], public summary [68], "
                "physical features [5], and event noise [4]"
            )
        return self.agent_update_final(torch.tanh(self.agent_update_hidden(values)))

    def event_plan(
        self,
        arm: str,
        old_plan: torch.Tensor,
        public_event_summary: torch.Tensor,
        physical_features: torch.Tensor | None = None,
        event_noise: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor | None, torch.Tensor | None]:
        """Apply FLEX heads or hard-mask both unused paths for another package."""

        if arm not in LEARNED_PACKAGES:
            raise ValueError(f"unknown learned package: {arm}")
        base = old_plan.detach().to(torch.float64)
        if arm != FLEX:
            return base, None, None
        if physical_features is None or event_noise is None:
            raise ValueError("FLEX event plan requires physical features and event noise")
        common = self.common_update(base, public_event_summary)
        agent = self.agent_update(base, public_event_summary, physical_features, event_noise)
        return base + common + agent, common, agent


def stopped_normal_log_density(
    sample: torch.Tensor,
    mean: torch.Tensor,
    raw_log_scale: torch.Tensor,
) -> torch.Tensor:
    """Per-draw Normal log density with a stopped sample argument.

    The final dimension is the four plan coordinates and is summed. The sample
    has no pathwise gradient; mean and raw log scale retain the score path.
    """

    stopped = sample.detach().to(dtype=torch.float64, device=mean.device)
    mean64 = mean.to(torch.float64)
    raw64 = raw_log_scale.to(torch.float64)
    log_scale = -2.0 + 2.0 * torch.sigmoid(raw64)
    standardized = (stopped - mean64) * torch.exp(-log_scale)
    return (-0.5 * standardized.square() - log_scale - 0.5 * math.log(2.0 * math.pi)).sum(dim=-1)


def stopped_normal_inverse_cdf(
    fixture_uniforms: torch.Tensor,
    mean: torch.Tensor,
    raw_log_scale: torch.Tensor,
) -> torch.Tensor:
    """Frozen Normal inverse-CDF map over caller-supplied fixture uniforms.

    The returned plan is stopped. This is deterministic conformance algebra,
    not an RNG materializer or a pathwise sampling surface.
    """

    uniforms = fixture_uniforms.to(device=mean.device, dtype=torch.float64)
    if uniforms.shape != mean.shape or raw_log_scale.shape != mean.shape:
        raise ValueError("fixture uniforms, mean, and raw log scale must have identical shapes")
    if not bool(torch.isfinite(uniforms).all()) or bool(((uniforms <= 0.0) | (uniforms >= 1.0)).any()):
        raise ValueError("Normal inverse-CDF fixture uniforms must lie strictly inside (0,1)")
    with torch.no_grad():
        log_scale = -2.0 + 2.0 * torch.sigmoid(raw_log_scale.detach().to(torch.float64))
        standard_normal = math.sqrt(2.0) * torch.erfinv(2.0 * uniforms - 1.0)
        return mean.detach().to(torch.float64) + torch.exp(log_scale) * standard_normal


def stopped_actor_plan(plan: torch.Tensor) -> torch.Tensor:
    """The only admissible plan value at the pointer-actor boundary."""

    return plan.detach()


def selected_claim_log_probability(probabilities: torch.Tensor, claims: torch.Tensor) -> torch.Tensor:
    """Return log probabilities for caller-supplied six-way claims."""

    if probabilities.shape[-1] != REGISTERED.beacons:
        raise ValueError("claim probabilities must have a six-way final dimension")
    selected = probabilities.gather(-1, claims.to(torch.int64)[..., None]).squeeze(-1)
    return torch.log(selected)


def required_affine_fixture_uniforms(model: TBCFVModel) -> dict[str, tuple[int, ...]]:
    """Names/shapes required by the exact caller-supplied affine transform."""

    final_zero = {"common_update_final", "agent_update_final"}
    return {
        f"{name}.weight": tuple(module.weight.shape)
        for name, module in model.named_modules()
        if isinstance(module, DeterministicZeroLinear) and name not in final_zero
    }


def apply_affine_fixture_uniforms(
    model: TBCFVModel,
    fixture_uniforms: Mapping[str, torch.Tensor],
) -> TBCFVModel:
    """Apply the registered uniform-to-Xavier transform without drawing.

    Every non-final affine weight is ``-b + 2*b*u`` with
    ``b=sqrt(6/(fan_in+fan_out))``. All biases and both FLEX final layers are
    exactly zero. Inputs are hand-written conformance tensors only.
    """

    required = required_affine_fixture_uniforms(model)
    if set(fixture_uniforms) != set(required):
        missing = sorted(set(required) - set(fixture_uniforms))
        extra = sorted(set(fixture_uniforms) - set(required))
        raise ValueError(f"affine fixture uniform keys mismatch; missing={missing}, extra={extra}")
    final_zero = {"common_update_final", "agent_update_final"}
    with torch.no_grad():
        for name, module in model.named_modules():
            if not isinstance(module, DeterministicZeroLinear):
                continue
            module.bias.zero_()
            if name in final_zero:
                module.weight.zero_()
                continue
            key = f"{name}.weight"
            uniforms = fixture_uniforms[key].to(device=module.weight.device, dtype=torch.float64)
            if tuple(uniforms.shape) != required[key]:
                raise ValueError(f"{key} has shape {tuple(uniforms.shape)}, expected {required[key]}")
            if not bool(torch.isfinite(uniforms).all()) or bool(((uniforms < 0.0) | (uniforms > 1.0)).any()):
                raise ValueError(f"{key} fixture uniforms must lie in [0,1]")
            bound = math.sqrt(6.0 / float(module.in_features + module.out_features))
            module.weight.copy_(-bound + 2.0 * bound * uniforms)
    return model


def make_paired_conformance_models(
    fixture_uniforms: Mapping[str, torch.Tensor],
) -> dict[str, TBCFVModel]:
    """Copy one complete deterministic fixture tensor across all five arms."""

    reference = apply_affine_fixture_uniforms(TBCFVModel(), fixture_uniforms)
    models: dict[str, TBCFVModel] = {}
    for arm in LEARNED_PACKAGES:
        model = TBCFVModel()
        model.load_state_dict(reference.state_dict())
        models[arm] = model
    return models


def averaged_episode_score(
    used_plan_log_densities: torch.Tensor,
    used_claim_log_probabilities: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Compute exact per-episode K_z and K_a averages from used paths only."""

    plan = used_plan_log_densities.reshape(-1)
    claims = used_claim_log_probabilities.reshape(-1)
    if plan.numel() < 1 or claims.numel() < 1:
        raise ValueError("every episode requires at least one used plan draw and claim decision")
    plan_average = plan.mean()
    claim_average = claims.mean()
    return plan_average, claim_average, plan_average + claim_average


def _validated_block_cells(cell_indices: torch.Tensor) -> torch.Tensor:
    cells = cell_indices.detach().to(torch.int64).reshape(-1)
    if cells.numel() != TRAIN_EPISODES_PER_BLOCK:
        raise ValueError("one update block must contain exactly 64 episodes")
    if bool(((cells < 0) | (cells >= TRAIN_CELLS)).any()):
        raise ValueError("cell indices must be in [0,7]")
    counts = torch.bincount(cells, minlength=TRAIN_CELLS)
    if not torch.equal(counts.cpu(), torch.full((TRAIN_CELLS,), EPISODES_PER_CELL, dtype=torch.int64)):
        raise ValueError("one update block must contain exactly eight episodes from every cell")
    return cells


def exact_advantage_loss(
    returns: torch.Tensor,
    cell_indices: torch.Tensor,
    baselines: torch.Tensor,
    used_plan_log_densities: Sequence[torch.Tensor],
    used_claim_log_probabilities: Sequence[torch.Tensor],
) -> torch.Tensor:
    """Exact stopped-advantage loss for one balanced 64-episode block."""

    cells = _validated_block_cells(cell_indices)
    returns64 = returns.reshape(-1)
    baseline8 = baselines.reshape(-1)
    if returns64.numel() != TRAIN_EPISODES_PER_BLOCK or baseline8.numel() != TRAIN_CELLS:
        raise ValueError("returns must have 64 entries and baselines must have eight")
    if len(used_plan_log_densities) != TRAIN_EPISODES_PER_BLOCK or len(used_claim_log_probabilities) != TRAIN_EPISODES_PER_BLOCK:
        raise ValueError("score-term sequences must contain exactly 64 episodes")
    scores = torch.stack(
        [
            averaged_episode_score(plan, claims)[2]
            for plan, claims in zip(used_plan_log_densities, used_claim_log_probabilities)
        ]
    )
    advantage = returns64.detach().to(scores) - baseline8.detach().to(scores)[cells.to(scores.device)]
    return -(advantage * scores).mean()


@dataclass(frozen=True)
class ParameterUpdateAudit:
    raw_gradient_norm: float
    direction_norm: float
    parameter_delta_norm: float
    nonzero: bool


def registered_plain_sgd_step(model: TBCFVModel) -> ParameterUpdateAudit:
    """Apply the exact whole-registered-tensor direction-normalized SGD step."""

    parameters = tuple(model.parameters())
    if sum(parameter.numel() for parameter in parameters) != REGISTERED.parameters_per_arm:
        raise ValueError("SGD surface requires the complete registered 26,161-scalar tensor")
    squared_norm = torch.zeros((), dtype=torch.float64)
    for parameter in parameters:
        if parameter.grad is not None:
            squared_norm = squared_norm + parameter.grad.detach().to(torch.float64).square().sum()
    raw_norm_tensor = torch.sqrt(squared_norm)
    raw_norm = float(raw_norm_tensor.item())
    if raw_norm == 0.0:
        return ParameterUpdateAudit(0.0, 0.0, 0.0, False)
    multiplier = -LEARNING_RATE * GRADIENT_DIRECTION_SCALE / raw_norm
    with torch.no_grad():
        for parameter in parameters:
            if parameter.grad is not None:
                parameter.add_(parameter.grad.to(parameter), alpha=multiplier)
    return ParameterUpdateAudit(
        raw_gradient_norm=raw_norm,
        direction_norm=GRADIENT_DIRECTION_SCALE,
        parameter_delta_norm=NONZERO_UPDATE_NORM,
        nonzero=True,
    )


@dataclass(frozen=True)
class BlockUpdateAudit:
    parameter_update: ParameterUpdateAudit
    updated_baselines: torch.Tensor
    event_order: tuple[str, str] = ("parameter_update", "baseline_update")


def apply_registered_block_update(
    model: TBCFVModel,
    baselines: torch.Tensor,
    returns: torch.Tensor,
    cell_indices: torch.Tensor,
) -> BlockUpdateAudit:
    """Update parameters first and only then update all eight stopped baselines."""

    cells = _validated_block_cells(cell_indices)
    returns64 = returns.detach().to(torch.float64).reshape(-1)
    baseline8 = baselines.detach().to(torch.float64).reshape(-1)
    if returns64.numel() != TRAIN_EPISODES_PER_BLOCK or baseline8.numel() != TRAIN_CELLS:
        raise ValueError("returns must have 64 entries and baselines must have eight")
    parameter_audit = registered_plain_sgd_step(model)
    # This operation is intentionally below the joint parameter step.
    cell_means = torch.stack([returns64[cells == cell].mean() for cell in range(TRAIN_CELLS)])
    updated = BASELINE_DECAY * baseline8 + (1.0 - BASELINE_DECAY) * cell_means
    return BlockUpdateAudit(parameter_update=parameter_audit, updated_baselines=updated.detach())


def make_pointer_inputs(
    pooled_public_summary: torch.Tensor,
    own_features: torch.Tensor,
    public_context: torch.Tensor,
    candidate_features: torch.Tensor,
    plan: torch.Tensor,
) -> torch.Tensor:
    """Assemble the exact 81-field pointer input without any actor-visible ID.

    Shapes end in 64 pooled public features, 5 own physical features, 4 public
    context fields, 4 per-candidate fields, and a 4-vector plan. Epoch samples
    must be passed through :func:`stopped_actor_plan` by the caller; a FLEX
    event plan must retain its deterministic update-head graph.
    Inputs may already contain arbitrary leading batch/agent/candidate axes;
    all leading shapes must be broadcastable to ``candidate_features``.
    """

    if pooled_public_summary.shape[-1] != 64:
        raise ValueError("pooled public summary must have dimension 64")
    if own_features.shape[-1] != 5:
        raise ValueError("own features must be (sin, cos, rank, displacement, newcomer)")
    if public_context.shape[-1] != 4:
        raise ValueError("public context must be (N/12, t/64, roster_event, new_epoch)")
    if candidate_features.shape[-1] != 4:
        raise ValueError("candidate features must be (sin, cos, demand/2, signed distance/60)")
    if plan.shape[-1] != 4:
        raise ValueError("plan must have dimension 4")
    target_shape = candidate_features.shape[:-1]

    def expanded(value: torch.Tensor) -> torch.Tensor:
        tensor = value.to(device=candidate_features.device, dtype=torch.float64)
        while tensor.ndim < candidate_features.ndim:
            tensor = tensor.unsqueeze(-2)
        return tensor.expand(*target_shape, tensor.shape[-1])

    result = torch.cat(
        (
            expanded(pooled_public_summary),
            expanded(own_features),
            expanded(public_context),
            candidate_features.to(torch.float64),
            expanded(plan),
        ),
        dim=-1,
    )
    if result.shape[-1] != REGISTERED.pointer_input:
        raise RuntimeError("assembled pointer input does not have 81 fields")
    return result


def make_conformance_fixture_model() -> TBCFVModel:
    """Return an explicit, hand-written, non-scientific conformance tensor.

    It consumes no RNG. Non-final FLEX features and one output-connected actor
    route are live, while both FLEX final affine layers remain exactly zero.
    """

    model = TBCFVModel()
    with torch.no_grad():
        # Public set encoders have a visible, permutation-equivariant mean path.
        model.agent_encoder.first.weight[0, 0] = 0.50
        model.agent_encoder.first.weight[1, 1] = -0.25
        model.agent_encoder.second.weight[0, 0] = 0.75
        model.agent_encoder.second.weight[1, 1] = 0.50
        model.beacon_encoder.first.weight[0, 0] = -0.40
        model.beacon_encoder.first.weight[1, 2] = 0.30
        model.beacon_encoder.second.weight[0, 0] = 0.60
        model.beacon_encoder.second.weight[1, 1] = -0.50

        # The pointer route nonlinearly couples candidate sine and plan[0].
        model.pointer_first.weight[0, 73] = 1.00
        model.pointer_first.weight[0, 77] = 0.75
        model.pointer_first.weight[1, 76] = 0.50
        model.pointer_second.weight[0, 0] = 1.00
        model.pointer_second.weight[0, 1] = 0.25
        model.pointer_score.weight[0, 0] = 1.00

        # Preceding FLEX layers are live. The final layers intentionally stay zero.
        model.common_update_hidden.weight[0, 0] = 0.50
        model.common_update_hidden.weight[0, 4] = 0.25
        model.agent_update_hidden.weight[0, 72] = 0.75
        model.agent_update_hidden.weight[1, 73] = -0.50
    return model
