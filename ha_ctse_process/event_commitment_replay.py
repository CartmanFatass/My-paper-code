"""Direct owner of event-held commitment teacher replay and validation."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

from ha_ctse_process.dynamic_roster_testbed import MAX_LIFECYCLES
from ha_ctse_process.event_commitment_collector import (
    CREATE,
    KEEP,
    RENEW,
    _normal_parameters,
    _row_stable_event_heads,
    transformed_mark_component_logp,
)
from ha_ctse_process.event_commitment_types import CommitmentArm, EventTrajectory
from ha_ctse_process.noncalendar_commitment_testbed import (
    EVENT_JOINT_FACTOR_COUNT,
    REPLAY_COMPONENT_FIELDS,
    REPLAY_EVENT_JOINT_RATIO_FIELDS,
    REPLAY_EXACT_FIELDS,
    REPLAY_JOINT_FIELDS,
    REPLAY_JOINT_RECORD_FIELDS,
    REPLAY_LOG_COMPONENT_ATOL,
    REPLAY_LOG_COMPONENT_FIELDS,
    REPLAY_LOG_COMPONENT_RTOL,
    REPLAY_LOG_RATIO_DRIFT_CAP,
    REPLAY_RECORD_SCHEMA_VERSION,
    REPLAY_STATE_ATOL,
    REPLAY_STATE_FIELDS,
    REPLAY_WORST_RECORD_FIELDS,
    float32_reduction_gamma,
)

@dataclass
class ReplayOutput:
    log_probs: torch.Tensor
    entropies: torch.Tensor
    values: torch.Tensor
    hidden_after: torch.Tensor
    prefix_counts: torch.Tensor
    contexts: torch.Tensor
    event_inputs: torch.Tensor
    event_cat_mask: torch.Tensor
    event_mark_mask: torch.Tensor
    event_actions: torch.Tensor
    event_new_z: torch.Tensor
    event_cat_logp: torch.Tensor
    event_mark_component_logp: torch.Tensor
    event_joint_logp: torch.Tensor
    event_cat_entropy: torch.Tensor


def _replay_primitive(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    hidden = trajectory.hidden_before[0].to(device)
    logps: list[torch.Tensor] = []
    entropies: list[torch.Tensor] = []
    values: list[torch.Tensor] = []
    hidden_rows: list[torch.Tensor] = []
    prefixes: list[torch.Tensor] = []
    contexts: list[torch.Tensor] = []
    for time in range(trajectory.time_steps):
        reset_mask = trajectory.hidden_before[time].to(device).abs().sum(-1).eq(0.0)
        hidden = torch.where(reset_mask.unsqueeze(-1), torch.zeros_like(hidden), hidden)
        observations = trajectory.observations[time].to(device)
        active = trajectory.active_mask[time].to(device)
        prepared = arm.base.prepare_step(
            observations=observations, active_mask=active, validated=True
        )
        output = arm.base.forward_step(
            observations=observations,
            active_mask=active,
            order=trajectory.orders[time].to(device),
            hidden=hidden,
            teacher_actions=trajectory.actions[time].to(device),
            primitive_logit_bias=arm.primitive_bias(trajectory.primitive_z[time].to(device)),
            prepared=prepared,
            validated=True,
        )
        logps.append(output.token_log_probs)
        entropies.append(output.token_entropies)
        values.append(output.value)
        hidden_rows.append(output.next_hidden)
        prefixes.append(output.prefix_counts)
        contexts.append(prepared.context)
        hidden = output.next_hidden
    return (
        torch.stack(logps), torch.stack(entropies), torch.stack(values),
        torch.stack(hidden_rows), torch.stack(prefixes), torch.stack(contexts),
    )


def _replay_event_heads(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
    contexts: torch.Tensor | None,
) -> tuple[
    torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor,
    torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor,
]:
    kind = trajectory.event_kind.to(device)
    cat_mask = kind.eq(KEEP) | kind.eq(RENEW)
    mark_mask = kind.eq(CREATE) | kind.eq(RENEW)
    event_mask = cat_mask | mark_mask
    actions = torch.where(cat_mask, kind - KEEP, torch.full_like(kind, -1))
    if contexts is None:
        reconstructed_inputs = trajectory.event_inputs.to(device)
    else:
        expanded_context = contexts.unsqueeze(2).expand(
            -1, -1, MAX_LIFECYCLES, -1
        )
        reconstructed_inputs = torch.cat(
            (
                trajectory.observations.to(device),
                trajectory.hidden_before.to(device),
                expanded_context,
                trajectory.event_z_pre.to(device),
            ),
            dim=-1,
        ).detach()
    cat_logp = torch.zeros_like(trajectory.event_old_cat_logp, device=device)
    mark_component = torch.zeros_like(
        trajectory.event_old_mark_component_logp, device=device
    )
    cat_entropy = torch.zeros_like(cat_logp)
    if arm.arm != "OR":
        assert arm.event_head is not None and arm.mark_head is not None
        inputs = reconstructed_inputs[event_mask]
        logits, mark_output = _row_stable_event_heads(
            inputs, arm.event_head, arm.mark_head
        )
        log_probability = F.log_softmax(logits, dim=-1)
        probability = torch.exp(log_probability)
        cat_entropy[event_mask] = -(probability * log_probability).sum(-1)
        safe_actions = actions[event_mask].clamp(min=0)
        cat_values = torch.gather(
            log_probability, 1, safe_actions.unsqueeze(-1)
        ).squeeze(-1)
        cat_logp[event_mask] = cat_values
        mu, sigma = _normal_parameters(mark_output)
        u = trajectory.event_u.to(device)[event_mask]
        mark_component[event_mask] = transformed_mark_component_logp(u, mu, sigma)
    cat_logp = torch.where(cat_mask, cat_logp, 0.0)
    mark_component = torch.where(mark_mask.unsqueeze(-1), mark_component, 0.0)
    joint = cat_logp + mark_component.sum(-1)
    u = trajectory.event_u.to(device)
    z_pre = trajectory.event_z_pre.to(device)
    reconstructed_new_z = torch.where(
        mark_mask.unsqueeze(-1),
        torch.tanh(u),
        torch.where(cat_mask.unsqueeze(-1), z_pre, torch.zeros_like(z_pre)),
    ).detach()
    return (
        reconstructed_inputs, cat_mask, mark_mask, actions,
        reconstructed_new_z, cat_logp, mark_component, joint, cat_entropy,
    )


def replay_trajectory(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
) -> ReplayOutput:
    primitive = _replay_primitive(arm, trajectory, device=device)
    events = _replay_event_heads(
        arm, trajectory, device=device, contexts=primitive[5]
    )
    return ReplayOutput(
        log_probs=primitive[0],
        entropies=primitive[1],
        values=primitive[2],
        hidden_after=primitive[3],
        prefix_counts=primitive[4],
        contexts=primitive[5],
        event_inputs=events[0],
        event_cat_mask=events[1],
        event_mark_mask=events[2],
        event_actions=events[3],
        event_new_z=events[4],
        event_cat_logp=events[5],
        event_mark_component_logp=events[6],
        event_joint_logp=events[7],
        event_cat_entropy=events[8],
    )


def _ordered_float32_encoding(value: np.float32) -> int:
    bits = int(value.view(np.uint32))
    return bits ^ (0xFFFFFFFF if bits & 0x80000000 else 0x80000000)


def _float32_ulp_evidence(stored: float, replayed: float) -> tuple[float, int]:
    stored32 = np.float32(stored)
    replayed32 = np.float32(replayed)
    if not np.isfinite(stored32) or not np.isfinite(replayed32):
        return float("nan"), 0
    reference = stored32 if abs(float(stored32)) >= abs(float(replayed32)) else replayed32
    direction = np.float32(np.inf if not np.signbit(reference) else -np.inf)
    neighbor = np.nextafter(reference, direction, dtype=np.float32)
    spacing = abs(float(np.float64(neighbor) - np.float64(reference)))
    distance = abs(
        _ordered_float32_encoding(stored32)
        - _ordered_float32_encoding(replayed32)
    )
    return spacing, int(distance)


def _worst_likelihood_record(
    stored: torch.Tensor,
    replayed: torch.Tensor,
    mask: torch.Tensor,
    *,
    mixed_bound_override: torch.Tensor | None = None,
    ratio_only: bool = False,
) -> dict[str, Any]:
    """Serialize the coordinate that is closest to violating either gate."""

    if not bool(mask.any()):
        return {
            "stored_value": 0.0,
            "replayed_value": 0.0,
            "absolute_error": 0.0,
            "mixed_bound": 0.0,
            "ratio_drift": 0.0,
            "ratio_cap": REPLAY_LOG_RATIO_DRIFT_CAP,
            "float32_ulp_at_max_magnitude": 0.0,
            "ulp_distance": 0,
            "coordinate": None,
        }
    difference = replayed - stored
    absolute_error = difference.double().abs()
    mixed_bound = (
        REPLAY_LOG_COMPONENT_ATOL
        + REPLAY_LOG_COMPONENT_RTOL
        * torch.maximum(replayed.double().abs(), stored.double().abs())
        if mixed_bound_override is None
        else mixed_bound_override.double()
    )
    ratio_drift = torch.expm1(difference.double()).abs()
    severity = (
        ratio_drift / REPLAY_LOG_RATIO_DRIFT_CAP
        if ratio_only
        else torch.maximum(
            absolute_error / mixed_bound,
            ratio_drift / REPLAY_LOG_RATIO_DRIFT_CAP,
        )
    )
    finite = (
        torch.isfinite(stored)
        & torch.isfinite(replayed)
        & torch.isfinite(absolute_error)
        & torch.isfinite(mixed_bound)
        & torch.isfinite(ratio_drift)
    )
    severity = torch.where(
        mask & finite,
        severity,
        torch.where(mask, torch.full_like(severity, float("inf")), torch.full_like(severity, -float("inf"))),
    )
    flat_index = int(torch.argmax(severity.reshape(-1)).detach().cpu())
    coordinate = [int(value) for value in np.unravel_index(flat_index, stored.shape)]
    selected = torch.stack(
        (
            stored.reshape(-1)[flat_index].double(),
            replayed.reshape(-1)[flat_index].double(),
            absolute_error.reshape(-1)[flat_index],
            mixed_bound.reshape(-1)[flat_index],
            ratio_drift.reshape(-1)[flat_index],
        )
    ).detach().cpu().numpy()
    spacing, distance = _float32_ulp_evidence(float(selected[0]), float(selected[1]))
    return {
        "stored_value": float(selected[0]),
        "replayed_value": float(selected[1]),
        "absolute_error": float(selected[2]),
        "mixed_bound": float(selected[3]),
        "ratio_drift": float(selected[4]),
        "ratio_cap": REPLAY_LOG_RATIO_DRIFT_CAP,
        "float32_ulp_at_max_magnitude": spacing,
        "ulp_distance": distance,
        "coordinate": coordinate,
    }


def replay_errors(replay: ReplayOutput, trajectory: EventTrajectory) -> dict[str, float]:
    device = replay.log_probs.device
    active = trajectory.active_mask.to(device)
    stored_cat = trajectory.event_cat_mask.to(device)
    stored_mark = trajectory.event_mark_mask.to(device)
    derived_event = replay.event_cat_mask | replay.event_mark_mask

    def maximum(value: torch.Tensor, mask: torch.Tensor | None = None) -> float:
        selected = value if mask is None else value[mask]
        return float(selected.abs().max().detach().cpu()) if selected.numel() else 0.0

    event_input_mask = derived_event.unsqueeze(-1).expand_as(replay.event_inputs)
    mark_component_mask = replay.event_mark_mask.unsqueeze(-1).expand_as(
        replay.event_mark_component_logp
    )
    # The two component checks above read the stored factors only *inside*
    # their own support, so a factor recorded non-zero outside it is invisible
    # to them; and if the stored joint is reassembled to include that value the
    # assembly check sees a self-consistent sum while the joint bound widens by
    # exactly the corruption. These two quantities look where nothing else
    # does. The collector zeroes both factors outside their support before
    # storing, so on clean data they are exactly zero by construction.
    stored_cat_logp = trajectory.event_old_cat_logp.to(device)
    stored_mark_logp = trajectory.event_old_mark_component_logp.to(device)
    categorical_support_leak = torch.where(
        replay.event_cat_mask, torch.zeros_like(stored_cat_logp), stored_cat_logp
    )
    mark_support_leak = torch.where(
        replay.event_mark_mask.unsqueeze(-1),
        torch.zeros_like(stored_mark_logp),
        stored_mark_logp,
    )
    kind = trajectory.event_kind.to(device)
    kind_support = kind.eq(0) | kind.eq(CREATE) | kind.eq(KEEP) | kind.eq(RENEW)
    action_exact = torch.equal(
        trajectory.event_categorical_actions.to(device)[replay.event_cat_mask],
        replay.event_actions[replay.event_cat_mask],
    )
    detached_exact = (
        not trajectory.event_inputs.requires_grad
        and not trajectory.event_z_pre.requires_grad
        and not trajectory.event_new_z.requires_grad
    )
    return {
        "primitive_component": maximum(
            replay.log_probs - trajectory.old_log_probs.to(device), active
        ),
        "primitive_joint": maximum(
            torch.where(
                active, replay.log_probs - trajectory.old_log_probs.to(device), 0.0
            ).sum(-1)
        ),
        "value": maximum(replay.values - trajectory.old_values.to(device)),
        "hidden": maximum(
            replay.hidden_after - trajectory.hidden_after.to(device)
        ),
        "prefix": maximum(
            replay.prefix_counts - trajectory.prefix_counts.to(device)
        ),
        "event_input": maximum(
            replay.event_inputs - trajectory.event_inputs.to(device), event_input_mask
        ),
        "categorical_component": maximum(
            replay.event_cat_logp - stored_cat_logp, replay.event_cat_mask
        ),
        "mark_component": maximum(
            replay.event_mark_component_logp - stored_mark_logp,
            mark_component_mask,
        ),
        "event_joint": maximum(
            replay.event_joint_logp - trajectory.event_old_joint_logp.to(device),
            derived_event,
        ),
        "event_new_z": maximum(
            replay.event_new_z - trajectory.event_new_z.to(device),
            derived_event.unsqueeze(-1).expand_as(replay.event_new_z),
        ),
        "primitive_event_z": maximum(
            replay.event_new_z - trajectory.primitive_z.to(device),
            derived_event.unsqueeze(-1).expand_as(replay.event_new_z),
        ),
        "mask_mismatch": float(
            not torch.equal(stored_cat, replay.event_cat_mask)
            or not torch.equal(stored_mark, replay.event_mark_mask)
        ),
        "kind_support_mismatch": float(not bool(kind_support.all())),
        "event_action_mismatch": float(not action_exact),
        "detach_mismatch": float(not detached_exact),
        "categorical_support_leak": maximum(categorical_support_leak),
        "mark_support_leak": maximum(mark_support_leak),
    }


def replay_likelihood_records(
    replay: ReplayOutput, trajectory: EventTrajectory
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Worst-coordinate mixed/ratio evidence for every likelihood factor."""

    device = replay.log_probs.device
    active = trajectory.active_mask.to(device)
    categorical_mask = replay.event_cat_mask
    mark_mask = replay.event_mark_mask.unsqueeze(-1).expand_as(
        replay.event_mark_component_logp
    )
    records = {
        "primitive_component": _worst_likelihood_record(
            trajectory.old_log_probs.to(device), replay.log_probs, active
        ),
        "categorical_component": _worst_likelihood_record(
            trajectory.event_old_cat_logp.to(device),
            replay.event_cat_logp,
            categorical_mask,
        ),
        "mark_component": _worst_likelihood_record(
            trajectory.event_old_mark_component_logp.to(device),
            replay.event_mark_component_logp,
            mark_mask,
        ),
    }
    event = _worst_likelihood_record(
        trajectory.event_old_joint_logp.to(device),
        replay.event_joint_logp,
        replay.event_cat_mask | replay.event_mark_mask,
        mixed_bound_override=torch.ones_like(replay.event_joint_logp),
        ratio_only=True,
    )
    event_ratio = {name: event[name] for name in REPLAY_EVENT_JOINT_RATIO_FIELDS}
    return records, event_ratio


def _joint_row_summary(
    *,
    error: torch.Tensor,
    component_sum: torch.Tensor,
    allowance: torch.Tensor,
    factor_count: torch.Tensor,
    assembly_residual: torch.Tensor,
    assembly_allowance: torch.Tensor,
    assembly_excess: torch.Tensor,
    exact_error: torch.Tensor,
    mask: torch.Tensor,
) -> dict[str, float]:
    """Reduce one derived joint's per-row bound check to a reportable record.

    Every argument is a per-row tensor over the same rows; `mask` selects the
    rows on which the joint is defined. The comparison that decides
    acceptance is elementwise per row -- a joint error may only be compared
    against *its own* row's bound, never against the largest bound anywhere
    in the batch -- so `excess` is the per-row maximum of `error - bound` and
    must not exceed zero. The reported `error`/`component_sum`/`allowance`/
    `bound` are all read at the row that produced the largest error, so the
    reported bound is the bound the reported error was actually tested
    against. `excess` is therefore not `error - bound` in general: it is read
    at the row that comes closest to failing, which need not be the
    largest-error row, and it always dominates `error - bound`.

    The three assembly numbers are instead all read at the row *and* side
    that decide `assembly_excess`, so in the record `assembly_excess` is
    exactly `assembly_residual - assembly_allowance`. Reporting a residual
    against an allowance that did not gate it -- for instance the smaller of
    the two sides' magnitudes -- lets a passing record show a residual larger
    than its own allowance, which reads as a contradiction.

    Every reported number is selected on device and transferred once. The
    worst-row index stays a device tensor so that locating it costs no
    synchronization of its own.
    """

    bound = component_sum + allowance
    names = REPLAY_JOINT_RECORD_FIELDS
    if not bool(mask.any()):
        return {name: 0.0 for name in names}
    selected_error = error[mask]
    selected_bound = bound[mask]
    selected_assembly_excess = assembly_excess[mask]
    worst = torch.argmax(selected_error)
    assembly_worst = torch.argmax(selected_assembly_excess)
    values = torch.stack(
        (
            selected_error[worst],
            component_sum[mask][worst],
            allowance[mask][worst],
            selected_bound[worst],
            (selected_error - selected_bound).max(),
            factor_count[mask][worst],
            exact_error[mask].max(),
            assembly_residual[mask][assembly_worst],
            assembly_allowance[mask][assembly_worst],
            selected_assembly_excess[assembly_worst],
            mask.sum().to(selected_error.dtype),
        )
    )
    return dict(zip(names, (float(value) for value in values.detach().cpu())))


def replay_joint_bounds(
    replay: ReplayOutput, trajectory: EventTrajectory
) -> dict[str, dict[str, float]]:
    """Compositional bounds for the two derived joint log probabilities.

    A joint is a sum of float32 factors, so it accumulates its factors'
    replay differences; bounding it by one factor's tolerance is a category
    error. Each joint is instead validated against a float64 recomputation
    from its own recorded factors:

    * `assembly_residual = |joint_f32 - joint_f64|` must not exceed
      `gamma_n * sum|f|` on either side. This is the check that the stored
      and replayed joints really are the sum of their recorded factors --
      an omitted or duplicated factor fails here regardless of tolerance.
    * The stored/replay joint difference then satisfies, by the triangle
      inequality over the float64 assemblies,
      `|J32_replay - J32_stored| <= sum_i|f_replay_i - f_stored_i|
       + gamma_n*(sum|f_stored| + sum|f_replay|)`,
      which is the compositional bound the contract registers. It is
      derived from the per-factor tolerance and conservative float32
      summation, never fitted to an observed number.

    `gamma_n = n*u/(1 - n*u)` with the float32 unit roundoff `u = 2**-24`.
    `n` is 9 for the event joint (categorical plus eight transformed-mark
    components) and the row's active-lifecycle count for the primitive
    joint. Per-factor differences are widened to float64 before summing, so
    the bound itself carries no float32 error of its own.

    What these two records do *not* prove, stated so that nothing here reads
    as coverage it does not provide:

    * `primitive_joint` is unfalsifiable by construction. No primitive joint
      is stored independently, so its error is `|sum(replay - stored)|`
      compared against `sum|replay - stored|` plus slack -- the triangle
      inequality, an identity. `primitive_joint_assembly` compares the
      float32 and float64 reductions of the *same* difference terms against
      a bound orders of magnitude larger, and is likewise invariant to any
      injected corruption. Real primitive coverage is
      the primitive component gates, which are adequate; these two are
      reported for continuity of the record shape, not as gates.
    * `event_joint` gates only joint *assembly* drift. Once the stored and
      replayed assembly checks hold, its rule reduces to the same triangle
      inequality, so a factor-level defect is caught by the component class
      and by `categorical_support_leak`/`mark_support_leak`, never here.
    """

    device = replay.log_probs.device
    active = trajectory.active_mask.to(device)
    stored_logp = trajectory.old_log_probs.to(device)

    # Primitive joint: the reported quantity is the float32 masked sum of
    # per-lifecycle differences, exactly as `replay_errors` computes it.
    primitive_difference = torch.where(
        active, replay.log_probs - stored_logp, 0.0
    ).sum(-1)
    primitive_terms = torch.where(
        active, (replay.log_probs - stored_logp).double(), 0.0
    )
    primitive_exact = primitive_terms.sum(-1)
    primitive_count = active.sum(-1).double()
    primitive_gamma = float32_reduction_gamma(primitive_count)
    primitive_magnitude = (
        torch.where(active, stored_logp.double().abs(), 0.0).sum(-1)
        + torch.where(active, replay.log_probs.double().abs(), 0.0).sum(-1)
    )
    primitive_rows = active.any(-1)

    # Event joint: nine recorded factors per row, each already zeroed
    # outside the row's likelihood support by both the collector and the
    # replay, so masked-out factors contribute nothing to either sum.
    stored_cat = trajectory.event_old_cat_logp.to(device)
    stored_mark = trajectory.event_old_mark_component_logp.to(device)
    stored_joint = trajectory.event_old_joint_logp.to(device)
    stored_factors = torch.cat((stored_cat.unsqueeze(-1), stored_mark), dim=-1)
    replay_factors = torch.cat(
        (replay.event_cat_logp.unsqueeze(-1), replay.event_mark_component_logp),
        dim=-1,
    )
    event_rows = replay.event_cat_mask | replay.event_mark_mask
    event_difference = replay.event_joint_logp - stored_joint
    event_component_sum = (
        (replay_factors.double() - stored_factors.double()).abs().sum(-1)
    )
    event_gamma = float32_reduction_gamma(float(EVENT_JOINT_FACTOR_COUNT))
    stored_magnitude = stored_factors.double().abs().sum(-1)
    replay_magnitude = replay_factors.double().abs().sum(-1)
    stored_exact_joint = stored_factors.double().sum(-1)
    replay_exact_joint = replay_factors.double().sum(-1)
    # Each side is checked against its own factor magnitudes: the stored
    # joint must be the float32 sum of the stored factors, and the replayed
    # joint the float32 sum of the replayed factors. Combining the two sides
    # before comparing would let a large-magnitude side cover a small one.
    stored_assembly = (stored_joint.double() - stored_exact_joint).abs()
    replay_assembly = (replay.event_joint_logp.double() - replay_exact_joint).abs()
    stored_assembly_allowance = event_gamma * stored_magnitude
    replay_assembly_allowance = event_gamma * replay_magnitude
    # The deciding side is the one furthest past its own allowance, and the
    # reported residual/allowance pair is read from that same side. Reporting
    # `max(stored, replay)` residual against `gamma * min(magnitude)` mixes
    # sides and can show a residual above its allowance on a passing record.
    stored_side = stored_assembly - stored_assembly_allowance
    replay_side = replay_assembly - replay_assembly_allowance
    stored_decides = stored_side >= replay_side
    event_assembly = torch.where(stored_decides, stored_assembly, replay_assembly)
    event_assembly_allowance = torch.where(
        stored_decides, stored_assembly_allowance, replay_assembly_allowance
    )
    event_assembly_excess = torch.where(stored_decides, stored_side, replay_side)

    return {
        "primitive_joint": _joint_row_summary(
            error=primitive_difference.double().abs(),
            component_sum=primitive_terms.abs().sum(-1),
            allowance=primitive_gamma * primitive_magnitude,
            factor_count=primitive_count,
            assembly_residual=(primitive_difference.double() - primitive_exact).abs(),
            assembly_allowance=primitive_gamma * primitive_magnitude,
            assembly_excess=(
                (primitive_difference.double() - primitive_exact).abs()
                - primitive_gamma * primitive_magnitude
            ),
            exact_error=primitive_exact.abs(),
            mask=primitive_rows,
        ),
        "event_joint": _joint_row_summary(
            error=event_difference.double().abs(),
            component_sum=event_component_sum,
            allowance=event_gamma * (stored_magnitude + replay_magnitude),
            factor_count=torch.full_like(
                stored_magnitude, float(EVENT_JOINT_FACTOR_COUNT)
            ),
            assembly_residual=event_assembly,
            assembly_allowance=event_assembly_allowance,
            assembly_excess=event_assembly_excess,
            exact_error=(replay_exact_joint - stored_exact_joint).abs(),
            mask=event_rows,
        ),
    }


def replay_report(
    replay: ReplayOutput,
    trajectory: EventTrajectory,
) -> dict[str, Any]:
    """Named per-factor errors, applied joint bounds and a pass result.

    Nothing here is collapsed into a single scalar: an omitted mark
    component and a benign reduction-order difference are different facts
    and must stay separable in the evidence.

    Every acceptance test is written in the `not (x <= limit)` form rather
    than `x > limit`. Both IEEE comparisons against NaN are false, so the
    `>` form would let a replay that produced NaN anywhere report
    `passed: True` -- the exact opposite of the fail-closed contract. Every
    numeric leaf is additionally required to be finite.
    """

    errors = replay_errors(replay, trajectory)
    joints = replay_joint_bounds(replay, trajectory)
    likelihood_components, event_joint_ratio = replay_likelihood_records(
        replay, trajectory
    )
    # The partition is the contract. A factor silently dropped from the
    # error dictionary would otherwise be reported as covered, so an
    # unclassified or missing name is a failure of the check itself.
    if set(errors) != set(
        REPLAY_EXACT_FIELDS + REPLAY_COMPONENT_FIELDS + REPLAY_JOINT_FIELDS
    ):
        raise RuntimeError(f"replay error fields do not match the contract {set(errors)}")
    if any(set(joints[name]) != set(REPLAY_JOINT_RECORD_FIELDS) for name in joints):
        raise RuntimeError(f"replay joint record fields do not match the contract {joints}")
    if (
        set(likelihood_components) != set(REPLAY_LOG_COMPONENT_FIELDS)
        or any(
            set(record) != set(REPLAY_WORST_RECORD_FIELDS)
            for record in likelihood_components.values()
        )
        or set(event_joint_ratio) != set(REPLAY_EVENT_JOINT_RATIO_FIELDS)
    ):
        raise RuntimeError("replay likelihood evidence fields do not match contract")
    failures: list[str] = sorted(
        f"non_finite:{name}"
        for name, value in (
            *errors.items(),
            *(
                (f"{joint}.{key}", number)
                for joint, record in joints.items()
                for key, number in record.items()
            ),
            *(
                (f"{component}.{key}", number)
                for component, record in likelihood_components.items()
                for key, number in record.items()
                if key != "coordinate"
            ),
            *(
                (f"event_joint_ratio.{key}", number)
                for key, number in event_joint_ratio.items()
                if key != "coordinate"
            ),
        )
        if not math.isfinite(float(value))
    )
    failures.extend(name for name in REPLAY_EXACT_FIELDS if errors[name] != 0.0)
    failures.extend(
        name for name in REPLAY_STATE_FIELDS
        if not errors[name] <= REPLAY_STATE_ATOL
    )
    failures.extend(
        name
        for name, record in likelihood_components.items()
        if not (
            float(record["absolute_error"]) <= float(record["mixed_bound"])
            and float(record["ratio_drift"]) <= REPLAY_LOG_RATIO_DRIFT_CAP
        )
    )
    has_event_rows = bool(
        (trajectory.event_kind.eq(CREATE)
         | trajectory.event_kind.eq(KEEP)
         | trajectory.event_kind.eq(RENEW)).any()
    )
    failures.extend(
        f"empty_support:{name}"
        for name, record in likelihood_components.items()
        if record["coordinate"] is None
        and (name == "primitive_component" or has_event_rows)
    )
    failures.extend(
        name for name in REPLAY_JOINT_FIELDS if not joints[name]["excess"] <= 0.0
    )
    failures.extend(
        f"{name}_assembly"
        for name in REPLAY_JOINT_FIELDS
        if not joints[name]["assembly_excess"] <= 0.0
    )
    if not float(event_joint_ratio["ratio_drift"]) <= REPLAY_LOG_RATIO_DRIFT_CAP:
        failures.append("event_joint_ratio")
    return {
        "schema_version": REPLAY_RECORD_SCHEMA_VERSION,
        "errors": errors,
        "likelihood_components": likelihood_components,
        "joints": joints,
        "event_joint_ratio": event_joint_ratio,
        "log_component_atol": REPLAY_LOG_COMPONENT_ATOL,
        "log_component_rtol": REPLAY_LOG_COMPONENT_RTOL,
        "ratio_drift_cap": REPLAY_LOG_RATIO_DRIFT_CAP,
        "state_atol": REPLAY_STATE_ATOL,
        "failures": failures,
        "passed": not failures,
    }


def validate_replay(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
) -> tuple[ReplayOutput, dict[str, Any]]:
    replay = replay_trajectory(arm, trajectory, device=device)
    report = replay_report(replay, trajectory)
    if not report["passed"]:
        errors = report["errors"]
        if any(name in REPLAY_EXACT_FIELDS for name in report["failures"]):
            raise RuntimeError(
                f"semantic replay exact-support mismatch {report['failures']} {errors}"
            )
        raise RuntimeError(
            f"semantic replay tolerance mismatch {report['failures']} "
            f"{errors} {report['joints']}"
        )
    return replay, report
