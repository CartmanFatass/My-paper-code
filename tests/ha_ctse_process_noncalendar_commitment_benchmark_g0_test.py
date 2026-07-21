from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Any
import hashlib
import json
import math
import random

import numpy as np
import pytest
import torch
import torch.nn.functional as F

from ha_ctse_process import event_held_commitment_link
from ha_ctse_process.event_held_commitment_link import (
    CREATE,
    FORK_STREAM_NAMES,
    KEEP,
    MARK_DIM,
    OPPORTUNITY_SUPPORT,
    RENEW,
    RNG_NAMES,
    _ForkGenerator,
    _ForkStream,
    _ForkStreamView,
    _nested_equal,
    _normal_parameters,
    _rng_states,
    action_distribution_tv,
    authoritative_seed_map,
    base_primitive_logits,
    collect_trajectory,
    compare_continuations,
    factor_counts,
    fork_single_opportunity,
    initialize_arms,
    load_checkpoint,
    make_training_state,
    natural_and_permuted_action_tv,
    nested_state_maximum_difference,
    optimize_update,
    parameter_and_optimizer_counts,
    replay_joint_bounds,
    replay_report,
    replay_trajectory,
    runtime_rng_equal,
    runtime_rng_snapshot,
    save_checkpoint,
    transformed_mark_component_logp,
    validate_replay,
)
from ha_ctse_process.dynamic_roster_testbed import HORIZON, MAX_LIFECYCLES
from ha_ctse_process.noncalendar_commitment_testbed import (
    ACCESS_FLOOR,
    EVENT_JOINT_FACTOR_COUNT,
    EVENT_SEED,
    FLOAT32_UNIT_ROUNDOFF,
    GAIN_THRESHOLD,
    HELD_OUT_EVAL_TASK_SEED,
    IID_EVAL_TASK_SEED,
    INTERVENTION_THRESHOLD,
    LIFETIME_BIN_THRESHOLD,
    MARK_SEED,
    OPPORTUNITY_SEED,
    REPLAY_COMPONENT_FIELDS,
    REPLAY_COMPONENT_TOLERANCE,
    REPLAY_EXACT_FIELDS,
    REPLAY_JOINT_FIELDS,
    REPLAY_JOINT_RECORD_FIELDS,
    SUPPORT_FLOOR,
    TRAIN_ACTION_SEED,
    TRAIN_ORDER_SEED,
    TRAIN_TASK_SEED,
    NoncalendarTrackingEnv,
    float32_reduction_gamma,
    make_noncalendar_ledger,
    make_rng,
    paired_ledgers_equal_except_targets,
    registered_contract,
    select_result_branch,
)
from scripts.run_noncalendar_commitment_benchmark_g0 import (
    ARMS,
    EVALUATION_CELLS,
    EVALUATION_CELL_SCHEMA,
    FORMAL_AUTHORIZATION,
    TRAIN_MANIFEST_SCHEMA,
    _evaluation_state,
    _json_ready,
    _replay_record_valid,
    _trajectory_episode_rows,
    merge_replay_records,
    run_smoke,
    validate_operational_records,
)


@pytest.fixture(scope="module")
def cuda_device() -> torch.device:
    if not torch.cuda.is_available():
        pytest.fail(
            "EVENT_HELD_COMMITMENT_LINK_G0 focused evidence requires CUDA; "
            "no CPU fallback"
        )
    return torch.device("cuda")


def test_initialization_rng_isolation_and_capacity(
    cuda_device: torch.device,
) -> None:
    random.seed(144)
    np.random.seed(145)
    torch.manual_seed(146)
    torch.cuda.manual_seed_all(147)
    before = runtime_rng_snapshot()
    arms, base_optimizers, event_optimizers = initialize_arms(cuda_device)
    after = runtime_rng_snapshot()
    assert runtime_rng_equal(before, after)
    for name in ("base", "W_z", "event_head", "mark_head"):
        if name == "base":
            left = arms["DUM"].base.state_dict()
            right = arms["EHC"].base.state_dict()
        else:
            left = getattr(arms["DUM"], name).state_dict()
            right = getattr(arms["EHC"], name).state_dict()
        assert nested_state_maximum_difference(left, right) == 0.0
    changed, _, _ = initialize_arms(
        cuda_device, mark_seed=MARK_SEED + 1
    )
    assert nested_state_maximum_difference(
        arms["DUM"].W_z.state_dict(), changed["DUM"].W_z.state_dict()
    ) == 0.0
    assert nested_state_maximum_difference(
        arms["DUM"].event_head.state_dict(),
        changed["DUM"].event_head.state_dict(),
    ) == 0.0
    assert nested_state_maximum_difference(
        arms["DUM"].mark_head.state_dict(),
        changed["DUM"].mark_head.state_dict(),
    ) > 0.0
    dum_counts = parameter_and_optimizer_counts(
        arms["DUM"], base_optimizers["DUM"], event_optimizers["DUM"]
    )
    ehc_counts = parameter_and_optimizer_counts(
        arms["EHC"], base_optimizers["EHC"], event_optimizers["EHC"]
    )
    assert dum_counts == ehc_counts == {
        "base_model": 14980,
        "added_model": 1608,
        "base_optimizer": 15004,
        "event_optimizer": 1584,
    }


def test_ledger_rejoin_epoch_due_event_and_partial_continuity(
    cuda_device: torch.device,
) -> None:
    left = make_noncalendar_ledger(
        0, profile="held_out", task_seed=HELD_OUT_EVAL_TASK_SEED,
        order_seed=TRAIN_ORDER_SEED,
    )
    right = make_noncalendar_ledger(
        1, profile="held_out", task_seed=HELD_OUT_EVAL_TASK_SEED,
        order_seed=TRAIN_ORDER_SEED,
    )
    assert paired_ledgers_equal_except_targets(left, right)
    assert NoncalendarTrackingEnv(left).observe().observations.shape[1] == 15

    arms, _, _ = initialize_arms(cuda_device)
    full_state = make_training_state("EHC", 0)
    partial_state = make_training_state("EHC", 0)
    full = collect_trajectory(
        arms["EHC"], full_state, device=cuda_device, episode_ids=(0,)
    )
    first = collect_trajectory(
        arms["EHC"], partial_state, device=cuda_device,
        episode_ids=(0,), max_steps=17,
    )
    second = collect_trajectory(
        arms["EHC"], partial_state, device=cuda_device, cursor=first.cursor
    )
    for name in (
        "actions", "old_log_probs", "old_values", "hidden_after",
        "event_kind", "primitive_z", "event_z_pre",
    ):
        assert torch.equal(
            getattr(full, name),
            torch.cat((getattr(first, name), getattr(second, name))),
        )
    assert first.cutoff
    assert any(
        record.close_reason == "RENEW" and not record.censored
        for record in full.segments[0]
    )
    assert any(
        record.close_reason in ("TERMINAL_LEAVE", "EPISODE_END")
        and record.censored
        for record in full.segments[0]
    )

    forced_state = make_training_state("EHC", 0)
    pre_rejoin = collect_trajectory(
        arms["EHC"], forced_state, device=cuda_device,
        episode_ids=(0,), max_steps=40,
    )
    key = pre_rejoin.cursor.ledgers[0].temporary_key
    life = pre_rejoin.cursor.lifecycles[0][key]
    frozen_z = life.z.clone()
    frozen_hidden = pre_rejoin.cursor.hidden[0, key].clone()
    frozen_segment = life.segment_id
    frozen_start = life.segment_start_active_step
    old_epoch = life.membership_epoch
    life.q = 0
    rejoin = collect_trajectory(
        arms["EHC"], forced_state, device=cuda_device,
        cursor=pre_rejoin.cursor, max_steps=1,
    )
    event_kind = int(rejoin.event_kind[0, 0, key].detach().cpu())
    assert event_kind in (KEEP, RENEW)
    assert event_kind != CREATE
    assert torch.equal(rejoin.hidden_before[0, 0, key], frozen_hidden)
    assert torch.equal(rejoin.event_z_pre[0, 0, key], frozen_z)
    assert int(rejoin.membership_epoch[0, 0, key]) == old_epoch + 1
    restored = rejoin.cursor.lifecycles[0][key]
    assert restored.membership_epoch == old_epoch + 1
    if event_kind == KEEP:
        assert restored.segment_id == frozen_segment
        assert restored.segment_start_active_step == frozen_start
        assert torch.equal(rejoin.primitive_z[0, 0, key], frozen_z)
    else:
        assert restored.segment_id == frozen_segment + 1
        assert restored.segment_start_active_step == restored.active_steps - 1
        assert torch.equal(
            rejoin.primitive_z[0, 0, key],
            rejoin.event_new_z[0, 0, key],
        )


def _reconstruct_key_spells(event_kind_row: list[int]) -> list[tuple[int, bool]]:
    """Independently recompute (K, closed_by_renew) per spell from a raw
    event-kind timeline for one lifecycle key, ignoring all physical-time
    gaps (a temporary-absence gap is simply a run of zero entries and so
    contributes zero opportunities to K by construction of this walk)."""

    running: int | None = None
    results: list[tuple[int, bool]] = []
    for value in event_kind_row:
        if value == CREATE:
            assert running is None, "unexpected repeated CREATE for one key"
            running = 0
        elif value == KEEP:
            assert running is not None, "KEEP without an open spell"
            running += 1
        elif value == RENEW:
            assert running is not None, "RENEW without an open spell"
            running += 1
            results.append((running, True))
            running = 0
    if running is not None:
        results.append((running, False))
    return results


def test_k_accounting_complete_censored_and_temporary_absence(
    cuda_device: torch.device,
) -> None:
    arms, _, _ = initialize_arms(cuda_device)
    state = make_training_state("EHC", 0)
    episode_count = 8
    trajectory = collect_trajectory(
        arms["EHC"], state, device=cuda_device,
        episode_ids=tuple(range(episode_count)),
    )

    found_two_keep_then_renew = False
    for env_index in range(episode_count):
        ledger = make_noncalendar_ledger(
            trajectory.ledger_ids[env_index], profile=state.profile,
            task_seed=state.seed_map["ledger"], order_seed=state.seed_map["order"],
        )
        temporary_key = ledger.temporary_key
        leave_time = ledger.temporary_leave_time
        rejoin_time = ledger.rejoin_time
        # Temporary absence must contribute no opportunity: no event at all
        # (CREATE/KEEP/RENEW) is recorded for the absent key while it is away.
        absence_events = trajectory.event_kind[leave_time:rejoin_time, env_index, temporary_key]
        assert bool((absence_events == 0).all())

        for key in range(trajectory.event_kind.shape[-1]):
            row = trajectory.event_kind[:, env_index, key].detach().cpu().tolist()
            if all(value == 0 for value in row):
                continue
            reconstructed = _reconstruct_key_spells(row)
            recorded = [
                (record.opportunity_count, record.close_reason == "RENEW")
                for record in trajectory.segments[env_index] if record.key == key
            ]
            assert reconstructed == recorded, (env_index, key)
            # Exactly one spell per key is open at episode end, and it is
            # always closed by a forced (censored) reason, never RENEW.
            assert recorded[-1][1] is False
            complete = [k for k, closed_by_renew in recorded if closed_by_renew]
            censored = [k for k, closed_by_renew in recorded if not closed_by_renew]
            assert len(complete) + len(censored) == len(recorded)
            assert len(censored) >= 1
            if any(k == 3 and closed for k, closed in reconstructed):
                found_two_keep_then_renew = True

    # A CREATE-opened spell closed by RENEW after exactly two KEEP decisions
    # (KEEP, KEEP, RENEW) records K=3; confirm this exact scenario actually
    # occurred and was recorded correctly above (not merely inferred).
    assert found_two_keep_then_renew


def test_trajectory_episode_rows_k_accounting_and_complete_spell_bins(
    cuda_device: torch.device,
) -> None:
    """`_trajectory_episode_rows` and `aggregate_analysis` previously had no
    test at all -- the same unreachability that let a `torch.flatnonzero`
    call and an `env_index` indexing bug survive a freeze. This builds rows
    on a real collected trajectory, JSON round-trips them (as the real
    evaluate/analyze split does through disk), and checks the row/segment
    accounting `aggregate_analysis` relies on."""

    arms, _, _ = initialize_arms(cuda_device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(
        arm, state, device=cuda_device, episode_ids=tuple(range(16))
    )
    rows = _trajectory_episode_rows(trajectory, arm, compute_intervention=True)
    round_tripped = json.loads(json.dumps(_json_ready(rows)))

    all_segments = [segment for row in round_tripped for segment in row["segments"]]
    complete_segments = [segment for segment in all_segments if not segment["censored"]]
    censored_segments = [segment for segment in all_segments if segment["censored"]]
    assert complete_segments and censored_segments

    # sum(K over ALL segments, censored included) == sum(non_create events).
    assert sum(segment["opportunity_count"] for segment in all_segments) == sum(
        row["non_create"] for row in round_tripped
    )
    # sum(row["renew"]) == number of complete (uncensored) segments. Each
    # RENEW event closes exactly one uncensored segment.
    assert sum(row["renew"] for row in round_tripped) == len(complete_segments)

    # The three K-bin proportions over COMPLETE spells sum to exactly 1.0.
    k_values = [segment["opportunity_count"] for segment in complete_segments]
    assert k_values
    predicates = (lambda k: k == 1, lambda k: k == 2, lambda k: k >= 3)
    proportions = [
        sum(predicate(value) for value in k_values) / len(k_values)
        for predicate in predicates
    ]
    assert sum(proportions) == pytest.approx(1.0, abs=1e-12)

    # K-bin proportions are computed over complete spells only, so a
    # censored K=0 spell does not enter any bin. This trajectory is known
    # (deterministically, given the fixed seeds) to contain at least one
    # such spell; demonstrate that including it (the swapped-in-all-segments
    # bug) breaks the sum-to-1 invariant just checked.
    censored_zero_k = [
        segment for segment in censored_segments if segment["opportunity_count"] == 0
    ]
    assert censored_zero_k
    all_k_values = [segment["opportunity_count"] for segment in all_segments]
    wrongly_included_sum = sum(
        sum(predicate(value) for value in all_k_values) / len(all_k_values)
        for predicate in predicates
    )
    assert wrongly_included_sum < 1.0 - 1e-9


def test_action_distribution_tv_zero_under_constant_logit_shift(
    cuda_device: torch.device,
) -> None:
    # This is the specific defect being fixed: the superseded
    # ||W_z(z - z_perm)|| / sqrt(3) metric is positive for a residual
    # proportional to (c, c, c), even though a softmax-common shift leaves
    # the three-action distribution exactly unchanged. Assert the fixed
    # I_TV metric is exactly (within float tolerance) zero in that case.
    natural = torch.tensor([0.7, -1.3, 2.1], device=cuda_device)
    for constant in (4.25, -9.0, 0.0):
        perturbed = natural + constant
        tv = action_distribution_tv(natural, perturbed)
        assert float(tv.detach().cpu()) == pytest.approx(0.0, abs=1e-6)

    # Batched form: a per-row constant shift must still cancel exactly.
    batch_natural = torch.tensor(
        [[0.1, 0.2, 0.3], [-2.0, 0.5, 1.5], [3.0, -3.0, 0.0]], device=cuda_device
    )
    shifts = torch.tensor([[1.0], [-3.5], [0.0]], device=cuda_device)
    tv_batch = action_distribution_tv(batch_natural, batch_natural + shifts)
    assert torch.allclose(tv_batch, torch.zeros_like(tv_batch), atol=1e-6)


def test_action_distribution_tv_bounded_and_realized_from_trajectory(
    cuda_device: torch.device,
) -> None:
    generator = torch.Generator(device=cuda_device).manual_seed(4471)
    random_natural = 6.0 * torch.randn((256, 3), generator=generator, device=cuda_device)
    random_perm = 6.0 * torch.randn((256, 3), generator=generator, device=cuda_device)
    tv = action_distribution_tv(random_natural, random_perm)
    assert bool((tv >= -1e-6).all())
    assert bool((tv <= 1.0 + 1e-6).all())

    arms, _, _ = initialize_arms(cuda_device)
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(
        arms["EHC"], state, device=cuda_device, episode_ids=(0,)
    )
    values: list[float] = []
    for time in range(trajectory.time_steps):
        values.extend(
            natural_and_permuted_action_tv(
                arms["EHC"], trajectory, env_index=0, time=time, device=cuda_device
            )
        )
    assert values, "expected at least one step with >=2 active lifecycles"
    assert all(-1e-6 <= value <= 1.0 + 1e-6 for value in values)

    # OR carries no W_z treatment at all: the intervention is vacuous.
    or_state = make_training_state("OR", 0)
    or_trajectory = collect_trajectory(
        arms["OR"], or_state, device=cuda_device, episode_ids=(0,)
    )
    assert natural_and_permuted_action_tv(
        arms["OR"], or_trajectory, env_index=0, time=0, device=cuda_device
    ) == []


def test_base_primitive_logits_reconstruction_matches_recorded_natural_log_probs(
    cuda_device: torch.device,
) -> None:
    """Guards acceptance item 7b: I_TV must be computed from the same
    held-fixed state as the natural action actually executed during
    collection. `base_primitive_logits` hand-reimplements the autoregressive
    loop of `DirectPrimitiveARPolicy.forward_step` from a different module;
    nothing else asserts the two stay in lockstep. If a future edit to
    `forward_step` silently repoints `base_primitive_logits` at a policy that
    was never executed, this test catches it: for every active key-step,
    `log_softmax(base_primitive_logits(...)[key] + arm.primitive_bias(z))`
    at the recorded natural action must reproduce the recorded
    `old_log_probs` exactly (up to float tolerance)."""

    arms, _, _ = initialize_arms(cuda_device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(
        arm, state, device=cuda_device, episode_ids=tuple(range(16))
    )
    maximum_error = 0.0
    checked_key_steps = 0
    for env_index in range(len(trajectory.ledger_ids)):
        for time in range(trajectory.time_steps):
            active_row = trajectory.active_mask[time, env_index]
            active_keys = torch.nonzero(active_row, as_tuple=True)[0].tolist()
            if not active_keys:
                continue
            base_logits = base_primitive_logits(
                arm, trajectory, env_index=env_index, time=time, device=cuda_device
            )
            for key in active_keys:
                z = trajectory.primitive_z[time, env_index, key].to(cuda_device)
                bias = arm.primitive_bias(z)
                logits = base_logits[key] + bias
                log_probability = F.log_softmax(logits, dim=-1)
                action = int(trajectory.actions[time, env_index, key].item())
                reconstructed = float(log_probability[action].detach().cpu())
                stored = float(
                    trajectory.old_log_probs[time, env_index, key].detach().cpu()
                )
                maximum_error = max(maximum_error, abs(reconstructed - stored))
                checked_key_steps += 1
    assert checked_key_steps > 0
    assert maximum_error <= 1e-6


def _corrupt_tensor(tensor: torch.Tensor, index: tuple[int, ...]) -> torch.Tensor:
    value = tensor.clone()
    value[index] += 0.25
    return value


def test_semantic_replay_corruption_negatives(
    cuda_device: torch.device,
) -> None:
    arms, _, _ = initialize_arms(cuda_device)
    state = make_training_state("DUM", 0)
    trajectory = collect_trajectory(
        arms["DUM"], state, device=cuda_device, episode_ids=(0,)
    )
    _replay, report = validate_replay(
        arms["DUM"], trajectory, device=cuda_device
    )
    errors = report["errors"]
    assert report["passed"] and not report["failures"]
    assert all(errors[name] == 0.0 for name in REPLAY_EXACT_FIELDS)
    assert all(
        errors[name] <= REPLAY_COMPONENT_TOLERANCE
        for name in REPLAY_COMPONENT_FIELDS
    )
    assert all(
        report["joints"][name]["excess"] <= 0.0
        and report["joints"][name]["assembly_excess"] <= 0.0
        for name in REPLAY_JOINT_FIELDS
    )
    event_index = tuple(
        int(value) for value in torch.nonzero(
            trajectory.event_kind.ne(0), as_tuple=False
        )[0].detach().cpu()
    )
    mark_index = tuple(
        int(value) for value in torch.nonzero(
            trajectory.event_mark_mask, as_tuple=False
        )[0].detach().cpu()
    )
    prefix_index = (0, 0, 0, 0)

    corrupted = [
        replace(
            trajectory,
            event_inputs=_corrupt_tensor(
                trajectory.event_inputs, (*event_index, 0)
            ),
        ),
        replace(
            trajectory,
            event_cat_mask=trajectory.event_cat_mask.clone(),
        ),
        replace(
            trajectory,
            event_u=_corrupt_tensor(trajectory.event_u, (*mark_index, 0)),
        ),
        replace(
            trajectory,
            event_new_z=_corrupt_tensor(
                trajectory.event_new_z, (*mark_index, 0)
            ),
        ),
        replace(
            trajectory,
            prefix_counts=_corrupt_tensor(
                trajectory.prefix_counts, prefix_index
            ),
        ),
    ]
    corrupted[1].event_cat_mask[event_index] = ~corrupted[1].event_cat_mask[event_index]
    for value in corrupted:
        with pytest.raises(RuntimeError, match="semantic replay"):
            validate_replay(arms["DUM"], value, device=cuda_device)

    changed_kind = trajectory.event_kind.clone()
    changed_kind[event_index] = 0
    with pytest.raises(RuntimeError, match="semantic replay"):
        validate_replay(
            arms["DUM"], replace(trajectory, event_kind=changed_kind),
            device=cuda_device,
        )


def test_candidate_retention_faithful_and_recovers_discarded_keep(
    cuda_device: torch.device,
) -> None:
    """Stage-1 retention (audit-only `candidate_u`/`candidate_z`): on
    CREATE/RENEW rows (`event_mark_mask` true) the retained candidate must
    be bit-identical to what was actually used to produce `event_u` /
    `event_new_z` -- proving no extra draw and no value drift. On natural
    KEEP rows the existing masking rule must be untouched (`event_u` still
    zero) while the retained candidate recovers the discarded pre-mask
    value. Uses a real 16-environment collection, not a hand-built stub.

    Audit-only isolation used to be "checked" by asserting
    `candidate_u.requires_grad is False` and `.grad_fn is None`. That is
    VACUOUS: the whole collection body runs under `torch.no_grad()`, so
    `torch.tanh(u)` WITHOUT `.detach()` also yields
    `requires_grad=False, grad_fn=None` -- an implementation that dropped
    both `.detach()` calls would pass every one of those asserts. The real
    invariant is a corruption-negative: `candidate_u`/`candidate_z` must be
    read by nothing in the optimization path. Collect and `optimize_update`
    from a fresh, identically-seeded start twice -- once faithful, once
    with `candidate_u`/`candidate_z` overwritten with NaN before
    `optimize_update` -- and require the resulting model parameters, both
    optimizer states and the full returned metrics (including the replay
    error dict) to be bit-identical between the two runs. Any read of the
    corrupted fields would poison the result with NaN or otherwise diverge;
    since neither field is referenced anywhere in `optimize_update`,
    `replay_trajectory` or `compute_gae`, faithfully audit-only code is
    unaffected by construction, and this test proves that empirically
    rather than via the vacuous no-grad check."""

    def collect_and_optimize(*, corrupt: bool):
        arms, base_optimizers, event_optimizers = initialize_arms(cuda_device)
        arm = arms["EHC"]
        state = make_training_state("EHC", 0)
        trajectory = collect_trajectory(
            arm, state, device=cuda_device, episode_ids=tuple(range(16))
        )
        if corrupt:
            trajectory = replace(
                trajectory,
                candidate_u=torch.full_like(trajectory.candidate_u, float("nan")),
                candidate_z=torch.full_like(trajectory.candidate_z, float("nan")),
            )
        update = optimize_update(
            arm, base_optimizers["EHC"], event_optimizers["EHC"], state,
            trajectory, device=cuda_device,
        )
        return trajectory, arm, base_optimizers["EHC"], event_optimizers["EHC"], update

    trajectory, faithful_arm, faithful_base, faithful_event, faithful_update = (
        collect_and_optimize(corrupt=False)
    )
    _corrupted_trajectory, corrupted_arm, corrupted_base, corrupted_event, corrupted_update = (
        collect_and_optimize(corrupt=True)
    )

    assert nested_state_maximum_difference(
        faithful_arm.state_dict(), corrupted_arm.state_dict()
    ) == 0.0
    assert nested_state_maximum_difference(
        faithful_base.state_dict(), corrupted_base.state_dict()
    ) == 0.0
    assert nested_state_maximum_difference(
        faithful_event.state_dict(), corrupted_event.state_dict()
    ) == 0.0
    assert faithful_update == corrupted_update

    mark_mask = trajectory.event_mark_mask
    assert bool(mark_mask.any())
    assert torch.equal(
        trajectory.candidate_u[mark_mask], trajectory.event_u[mark_mask]
    )
    assert torch.equal(
        trajectory.candidate_z[mark_mask], trajectory.event_new_z[mark_mask]
    )

    keep_rows = trajectory.event_kind.eq(KEEP)
    assert bool(keep_rows.any())
    assert torch.equal(
        trajectory.event_u[keep_rows],
        torch.zeros_like(trajectory.event_u[keep_rows]),
    )
    candidate_u_on_keep = trajectory.candidate_u[keep_rows]
    assert bool(torch.isfinite(candidate_u_on_keep).all())
    assert bool((candidate_u_on_keep != 0.0).any())
    assert torch.equal(
        trajectory.candidate_z[keep_rows], torch.tanh(candidate_u_on_keep)
    )

    # Padded (no-request) positions keep zeros, consistent with event_u.
    no_request_rows = trajectory.event_kind.eq(0)
    assert bool(no_request_rows.any())
    assert torch.equal(
        trajectory.candidate_u[no_request_rows],
        torch.zeros_like(trajectory.candidate_u[no_request_rows]),
    )
    assert torch.equal(
        trajectory.candidate_z[no_request_rows],
        torch.zeros_like(trajectory.candidate_z[no_request_rows]),
    )


def test_candidate_retention_deterministic_matches_mu(
    cuda_device: torch.device,
) -> None:
    """With `deterministic=True` the registered mark rule sets `u = mu`
    for every request. `candidate_u`/`candidate_z` must retain exactly
    that value; recomputed here independently from the stored
    `event_inputs` and the arm's own `mark_head`, for every request row
    (CREATE/KEEP/RENEW alike, not only the categorical-masked ones)."""

    arms, _, _ = initialize_arms(cuda_device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(
        arm, state, device=cuda_device, episode_ids=tuple(range(16)),
        deterministic=True,
    )
    event_mask = trajectory.event_kind.ne(0)
    assert bool(event_mask.any())
    inputs = trajectory.event_inputs[event_mask]
    with torch.no_grad():
        mu, _sigma = _normal_parameters(arm.mark_head(inputs))
    candidate_u = trajectory.candidate_u[event_mask]
    candidate_z = trajectory.candidate_z[event_mask]
    assert torch.allclose(candidate_u, mu, atol=1e-6, rtol=1e-5)
    assert torch.allclose(candidate_z, torch.tanh(mu), atol=1e-6, rtol=1e-5)


def _fork_boundary_differences(
    left: dict, right: dict
) -> tuple[list[str], dict[int, list[str]]]:
    """Field names that differ between the two branch states at the fork."""

    assert set(left) == set(right)
    assert set(left["lifecycles"]) == set(right["lifecycles"])
    fields = sorted(
        name for name in left
        if name != "lifecycles" and not _nested_equal(left[name], right[name])
    )
    lifecycle_fields = {
        key: sorted(
            name for name in left["lifecycles"][key]
            if not _nested_equal(
                left["lifecycles"][key][name], right["lifecycles"][key][name]
            )
        )
        for key in left["lifecycles"]
    }
    return fields, {key: value for key, value in lifecycle_fields.items() if value}


def test_fork_single_opportunity_reproduces_the_natural_branch(
    cuda_device: torch.device,
) -> None:
    """Counterfactual KEEP/RENEW fork of one held-out opportunity.

    The headline property is state-reconstruction correctness: the branch
    matching the naturally taken action must reproduce the *original*
    continuation exactly -- not merely a close terminal utility, but the
    identical `TrackingOutcome` (utility, tracking/completion numerators
    and denominators, roster sizes and the full reward trace), i.e. the
    same environment terminal state the collected trajectory recorded for
    that episode. Nothing weaker distinguishes a correct reconstruction
    from one that merely lands nearby.

    The same fork is used to check the four supporting properties: the
    pair consumes identical randomness (the same realized variates, not
    merely the same generator objects), the two branch states differ only
    by the commitment mark `z`, neither branch is truncated (this
    environment pays zero reward until the terminal step, so a truncated
    branch would report zero utility), and the caller's owned and global
    RNG state is untouched.

    The exactness claim is enforced inside the engine on every fork, over
    the whole reconstructed window at the registered collection width; this
    test additionally reads back those engine-side error diagnostics.
    """

    arms, _, _ = initialize_arms(cuda_device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0, profile="held_out")
    trajectory = collect_trajectory(
        arm, state, device=cuda_device, episode_ids=tuple(range(16)),
        deterministic=True, profile="held_out",
    )
    kinds = trajectory.event_kind.detach().cpu()
    eligible = [
        tuple(int(v) for v in row)
        for row in torch.nonzero(
            kinds.eq(KEEP) | kinds.eq(RENEW), as_tuple=False
        ).tolist()
        if int(row[0]) >= 1
    ]
    natural_keep = [row for row in eligible if int(kinds[row]) == KEEP]
    natural_renew = [row for row in eligible if int(kinds[row]) == RENEW]
    assert natural_keep and natural_renew

    owned_before = deepcopy(_rng_states(state))
    global_before = runtime_rng_snapshot()

    checked: list[tuple[int, int, int]] = []
    discriminating = 0
    # One naturally-KEEP and one naturally-RENEW coordinate, so the
    # reproduction claim is not carried by a single branch label. At least
    # one of them must be *discriminating* (the two branches reach
    # different terminal utilities); otherwise a fork that silently ignored
    # `candidate_z` would reproduce the natural branch for free.
    for coordinates in (natural_keep[:1], natural_renew[:4]):
        for step, env_index, key in coordinates:
            diagnostics: dict = {}
            result = fork_single_opportunity(
                arm, trajectory, env_index=env_index, time=step, key=key,
                device=cuda_device, state=state, diagnostics=diagnostics,
            )
            checked.append((step, env_index, key))

            expected = "KEEP" if int(kinds[step, env_index, key]) == KEEP else "RENEW"
            assert result["natural_action"] == expected
            assert set(result) == {"keep_utility", "renew_utility", "natural_action"}

            # Natural-branch reproduction: exact, on the whole outcome.
            natural_outcome = trajectory.outcomes[env_index]
            branch_outcome = diagnostics["outcomes"][result["natural_action"]]
            assert branch_outcome == natural_outcome, (step, env_index, key)
            assert result[f"{result['natural_action'].lower()}_utility"] == float(
                natural_outcome.utility
            )

            # No truncation: both branches run to the terminal step.
            assert diagnostics["branch_cutoff"] == {"KEEP": False, "RENEW": False}
            assert diagnostics["branch_terminal"] == {"KEEP": True, "RENEW": True}
            assert diagnostics["branch_steps"] == {
                "KEEP": HORIZON - step, "RENEW": HORIZON - step,
            }

            # Pair randomness identity: same draw counts on every stream and
            # -- the falsifiable part -- the same realized variates actually
            # consumed by the two branches. Comparing the two views' shared
            # generator objects instead would assert nothing.
            positions = diagnostics["stream_positions"]
            assert set(positions["KEEP"]) == set(FORK_STREAM_NAMES)
            assert positions["KEEP"] == positions["RENEW"]
            assert diagnostics["stream_calls"]["KEEP"] == diagnostics["stream_calls"]["RENEW"]
            assert _nested_equal(
                diagnostics["stream_values"]["KEEP"],
                diagnostics["stream_values"]["RENEW"],
            )
            assert positions["KEEP"]["opportunity"] > 0
            assert len(diagnostics["stream_values"]["KEEP"]["opportunity"]) > 0

            # Engine-side natural-branch guard: the reconstruction is exact
            # on every recorded discrete field of the whole continuation,
            # not only on the terminal outcome.
            natural_errors = diagnostics["natural_branch_errors"]
            assert natural_errors["outcome_mismatch"] == 0.0
            assert natural_errors["discrete_mismatch"] == 0.0, natural_errors
            assert diagnostics["prefix_errors"]["discrete_mismatch"] == 0.0

            # Bitwise, not within tolerance. Reconstructing at the collected
            # width instead of at width 1 is justified *only* by removing the
            # float32 reduction-order drift class rather than bounding it, so
            # the claim is pinned as exact equality on both windows. A
            # width-1-grade residual is order 1e-6 and would satisfy any
            # tolerance-shaped assertion while silently reintroducing the
            # drift that can flip a primitive argmax.
            assert natural_errors["continuous"] == 0.0, natural_errors
            assert diagnostics["prefix_errors"]["continuous"] == 0.0, (
                diagnostics["prefix_errors"]
            )

            # `segments` is part of the collected continuation and
            # `compare_continuations` compares it order sensitively, so the
            # natural branch must reproduce the whole per-environment
            # sequence -- compared here directly against the record rather
            # than by reading back the engine's own verdict. It is also the
            # only place a `SegmentRecord`'s own fields are checked: the
            # focal cell of the per-step `membership_epoch` tensor is the
            # excluded coordinate, so a RENEW record written with a wrong
            # epoch reaches no tensor comparison at all.
            branch_segments = diagnostics["natural_branch_segments"]
            assert branch_segments == trajectory.segments, (step, env_index, key)
            assert branch_segments[env_index] == trajectory.segments[env_index]
            focal_renewals = [
                record for record in branch_segments[env_index]
                if record.key == key and record.close_reason == "RENEW"
            ]
            if result["natural_action"] == "RENEW":
                assert focal_renewals, (step, env_index, key)
            assert natural_errors["segment_mismatch"] == 0.0, natural_errors
            assert diagnostics["prefix_errors"]["segment_mismatch"] == 0.0

            # Treatment isolation: only the focal key's `z` differs.
            fields, lifecycle_fields = _fork_boundary_differences(
                diagnostics["boundaries"]["KEEP"], diagnostics["boundaries"]["RENEW"]
            )
            assert fields == [], (step, env_index, key, fields)
            assert lifecycle_fields == {key: ["z"]}, (step, env_index, key)

            if result["keep_utility"] != result["renew_utility"]:
                discriminating += 1
                break

    assert len(checked) >= 2
    assert discriminating >= 1

    # Caller RNG untouched: neither the collector state's owned streams nor
    # the global Python/NumPy/CPU/CUDA snapshot moved.
    assert _nested_equal(owned_before, _rng_states(state))
    assert runtime_rng_equal(global_before, runtime_rng_snapshot())


def _held_out_fork_setup(
    device: torch.device,
) -> tuple[Any, Any, Any, tuple, list[tuple[int, int, int]]]:
    """One deterministic held-out collection plus its eligible fork rows."""

    arms, _, _ = initialize_arms(device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0, profile="held_out")
    trajectory = collect_trajectory(
        arm, state, device=device, episode_ids=tuple(range(16)),
        deterministic=True, profile="held_out",
    )
    ledgers = tuple(
        make_noncalendar_ledger(
            value, profile="held_out",
            task_seed=state.seed_map["ledger"], order_seed=state.seed_map["order"],
        )
        for value in trajectory.ledger_ids
    )
    kinds = trajectory.event_kind.detach().cpu()
    eligible = [
        tuple(int(v) for v in row)
        for row in torch.nonzero(
            kinds.eq(KEEP) | kinds.eq(RENEW), as_tuple=False
        ).tolist()
        if int(row[0]) >= 1
    ]
    return arm, state, trajectory, ledgers, eligible


def test_fork_reproduces_hazardous_lifecycle_coordinates(
    cuda_device: torch.device,
) -> None:
    """Fork where reconstruction is structurally hardest, not only at `t=1`.

    The headline fork test takes the earliest eligible coordinates, so its
    branch tails start at the very beginning of the episode and never cross
    a membership transition in a way the *branch* has to carry. Four
    structurally different coordinates are pinned here:

    * a late step, where almost the whole episode is prefix reconstruction
      rather than branch tail, and where the branch is only a few steps
      long -- the regime in which a per-step drift residual is smallest and
      an exactness claim is easiest to lose unnoticed;
    * the REJOIN step itself, where a lifecycle's membership epoch advances
      and a second lifecycle genuinely JOINs in the same physical step the
      forced event is recorded against;
    * a coordinate whose focal lifecycle temporarily LEAVEs and REJOINs
      *inside* the branch tail, so the branch must carry an absent
      lifecycle across the gap and resume its spell accounting after it;
    * a coordinate whose focal lifecycle terminally LEAVEs inside the
      branch tail, so the branch must emit the censored TERMINAL_LEAVE
      close at the same sequence position the collector did.

    All four are expected to reconstruct exactly; this is regression
    protection for the reconstruction and segment-ordering contracts, not a
    discovery test.
    """

    arm, state, trajectory, ledgers, eligible = _held_out_fork_setup(cuda_device)
    temporary_leave_time = int(ledgers[0].temporary_leave_time)
    rejoin_time = int(ledgers[0].rejoin_time)
    terminal_leave_time = int(ledgers[0].terminal_leave_time)
    assert 0 < temporary_leave_time < rejoin_time < terminal_leave_time < HORIZON

    def first(predicate) -> tuple[int, int, int]:
        return next(row for row in eligible if predicate(row))

    coordinates = {
        "late_step": first(lambda row: row[0] >= HORIZON - 5),
        "rejoin_step": first(lambda row: row[0] == rejoin_time),
        "tail_spans_rejoin": first(
            lambda row: row[0] < temporary_leave_time
            and row[2] == int(ledgers[row[1]].temporary_key)
        ),
        "tail_spans_terminal_leave": first(
            lambda row: row[0] < terminal_leave_time
            and row[2] == int(ledgers[row[1]].terminal_key)
        ),
    }
    assert len(set(coordinates.values())) == 4

    # The membership claims above are properties of the record, not of the
    # selection comment: assert them so the coverage cannot go vacuous if
    # the ledger contract moves.
    active = trajectory.active_mask.detach().cpu()
    step, env_index, key = coordinates["tail_spans_rejoin"]
    assert bool(active[step, env_index, key])
    assert not bool(active[rejoin_time - 1, env_index, key])
    assert bool(active[rejoin_time, env_index, key])
    step, env_index, key = coordinates["tail_spans_terminal_leave"]
    assert bool(active[terminal_leave_time - 1, env_index, key])
    assert not bool(active[terminal_leave_time, env_index, key])

    for label, (step, env_index, key) in coordinates.items():
        diagnostics: dict = {}
        result = fork_single_opportunity(
            arm, trajectory, env_index=env_index, time=step, key=key,
            device=cuda_device, state=state, diagnostics=diagnostics,
        )
        context = (label, step, env_index, key)
        natural_errors = diagnostics["natural_branch_errors"]
        prefix_errors = diagnostics["prefix_errors"]
        assert natural_errors["outcome_mismatch"] == 0.0, (context, natural_errors)
        assert natural_errors["discrete_mismatch"] == 0.0, (context, natural_errors)
        assert natural_errors["continuous"] == 0.0, (context, natural_errors)
        assert natural_errors["segment_mismatch"] == 0.0, (context, natural_errors)
        assert prefix_errors["discrete_mismatch"] == 0.0, (context, prefix_errors)
        assert prefix_errors["continuous"] == 0.0, (context, prefix_errors)
        assert prefix_errors["segment_mismatch"] == 0.0, (context, prefix_errors)
        assert diagnostics["natural_branch_segments"] == trajectory.segments, context
        assert (
            diagnostics["outcomes"][result["natural_action"]]
            == trajectory.outcomes[env_index]
        ), context
        assert diagnostics["branch_steps"] == {
            "KEEP": HORIZON - step, "RENEW": HORIZON - step,
        }, context
        assert diagnostics["coordinate"] == {
            "time": step, "env_index": env_index, "key": key,
        }


def test_fork_rejects_a_corrupted_branch(cuda_device: torch.device, monkeypatch) -> None:
    """The natural-branch reproduction guard must actually be able to fail.

    Every other fork test asserts that a correct branch is accepted, which
    a guard that never fires would satisfy for free. Three corruptions of
    the forced event are injected here, each on the same coordinate that
    forks cleanly as the control:

    * the assigned opportunity clock, which desynchronizes the focal
      lifecycle's next request;
    * the installed commitment mark, which changes the primitive logit bias
      from the forked step onward;
    * the recorded membership epoch of the forced RENEW's `SegmentRecord`,
      which reaches *no* per-step tensor -- the focal cell of the per-step
      `membership_epoch` grid is the excluded coordinate -- and is
      therefore visible only to the order-sensitive `segments` comparison.

    The third case is asserted to be caught by `segments` alone, with the
    continuous error still exactly zero, because that is the guard the
    other two do not exercise.
    """

    arm, state, trajectory, _ledgers, eligible = _held_out_fork_setup(cuda_device)
    kinds = trajectory.event_kind.detach().cpu()
    step, env_index, key = next(
        row for row in eligible
        if row[0] >= HORIZON - 5 and int(kinds[row]) == RENEW
    )

    # Control: uncorrupted, the same coordinate is accepted.
    control: dict = {}
    fork_single_opportunity(
        arm, trajectory, env_index=env_index, time=step, key=key,
        device=cuda_device, state=state, diagnostics=control,
    )
    assert control["natural_action"] == "RENEW"
    assert control["natural_branch_errors"]["segment_mismatch"] == 0.0

    pristine = event_held_commitment_link._apply_fork_event

    def corrupted(offsets):
        def wrapper(cursor, **kwargs):
            kwargs["assigned_q"] += offsets.get("assigned_q", 0)
            kwargs["record_epoch"] += offsets.get("record_epoch", 0)
            if "new_z" in offsets:
                kwargs["new_z"] = kwargs["new_z"] + offsets["new_z"]
            return pristine(cursor, **kwargs)

        return wrapper

    for offsets in ({"assigned_q": 4}, {"new_z": 0.5}):
        monkeypatch.setattr(
            event_held_commitment_link, "_apply_fork_event", corrupted(offsets)
        )
        stale: dict = {"stale_key": "from a previous fork"}
        with pytest.raises(RuntimeError, match="fork natural branch continuation"):
            fork_single_opportunity(
                arm, trajectory, env_index=env_index, time=step, key=key,
                device=cuda_device, state=state, diagnostics=stale,
            )
        # A raise must not leave the caller reading a previous fork's values.
        assert "stale_key" not in stale
        assert stale["coordinate"] == {
            "time": step, "env_index": env_index, "key": key,
        }
        monkeypatch.undo()

    monkeypatch.setattr(
        event_held_commitment_link, "_apply_fork_event",
        corrupted({"record_epoch": 7}),
    )
    with pytest.raises(RuntimeError) as excinfo:
        fork_single_opportunity(
            arm, trajectory, env_index=env_index, time=step, key=key,
            device=cuda_device, state=state,
        )
    message = str(excinfo.value)
    assert "fork natural branch continuation mismatch" in message
    # Caught by `segments` and by nothing else: every per-step tensor still
    # reconstructs bitwise exactly under this corruption.
    assert "'mismatched_fields': ('segments',)" in message, message
    assert "'continuous': 0.0" in message, message
    assert f"(time={step}, env_index={env_index}, key={key})" in message, message


def test_fork_rejects_a_collector_state_from_another_profile(
    cuda_device: torch.device,
) -> None:
    """The fork must not silently rebuild a different task ledger.

    An `EventTrajectory` does not record the profile it was collected
    under, and the fork rebuilds every ledger from the caller's
    `state.profile`/`state.seed_map`. Handing it the wrong profile yields a
    different membership schedule and frontier priority order, i.e. a
    reconstruction of a different episode. That must be named at the fork
    boundary, not discovered as an opaque reconstruction mismatch after a
    full rollout, and not left to chance.
    """

    arms, _, _ = initialize_arms(cuda_device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0, profile="held_out")
    trajectory = collect_trajectory(
        arm, state, device=cuda_device, episode_ids=tuple(range(16)),
        deterministic=True, profile="held_out",
    )
    kinds = trajectory.event_kind.detach().cpu()
    step, env_index, key = next(
        tuple(int(v) for v in row)
        for row in torch.nonzero(
            kinds.eq(KEEP) | kinds.eq(RENEW), as_tuple=False
        ).tolist()
        if int(row[0]) >= 1
    )

    wrong_profile = make_training_state("EHC", 0, profile="train")
    with pytest.raises(ValueError, match="disagrees with the collected trajectory"):
        fork_single_opportunity(
            arm, trajectory, env_index=env_index, time=step, key=key,
            device=cuda_device, state=wrong_profile,
        )

    tampered = make_training_state("EHC", 0, profile="held_out")
    tampered.seed_map = dict(tampered.seed_map)
    tampered.seed_map["mark"] += 1
    with pytest.raises(ValueError, match="seed map is not the authoritative map"):
        fork_single_opportunity(
            arm, trajectory, env_index=env_index, time=step, key=key,
            device=cuda_device, state=tampered,
        )

    wrong_arm = make_training_state("DUM", 0, profile="held_out")
    with pytest.raises(ValueError, match="fork state owns arm"):
        fork_single_opportunity(
            arm, trajectory, env_index=env_index, time=step, key=key,
            device=cuda_device, state=wrong_arm,
        )


def test_fork_generator_honors_the_requested_float_dtype() -> None:
    """The fork RNG facade must draw in the precision it is asked for.

    NumPy's float32 path consumes a different number of bits per variate
    than its float64 path, so drawing in float64 and casting produces
    *different values*, not a rounded copy of the same ones. The collector
    draws its primitive uniform table as float32, so a facade that silently
    drew float64 would not reproduce that stream once stochastic forking
    exists. One fork stream is materialized exactly once and replayed, so a
    second consumer asking for a different precision is a contradiction and
    must raise rather than hand back the other precision's variates.
    """

    seed, count = 12345, 24

    for dtype in (np.float32, np.float64):
        view = _ForkStreamView(
            {"primitive": _ForkStream("primitive", make_rng(seed, 7))}
        )
        drawn = _ForkGenerator(view, "primitive").random((3, 8), dtype=dtype)
        reference = make_rng(seed, 7).random(count, dtype=dtype).reshape(3, 8)
        assert drawn.dtype == np.dtype(dtype)
        assert np.array_equal(drawn, reference)

    # The two precisions really are different variates, so the equality
    # above is not something a float64-and-cast implementation could pass.
    narrow = _ForkGenerator(
        _ForkStreamView({"primitive": _ForkStream("primitive", make_rng(seed, 7))}),
        "primitive",
    ).random(count, dtype=np.float32)
    wide = make_rng(seed, 7).random(count)
    assert float(np.max(np.abs(narrow.astype(np.float64) - wide))) > 1e-3

    normal = _ForkGenerator(
        _ForkStreamView({"mark": _ForkStream("mark", make_rng(seed, 9))}), "mark"
    ).standard_normal((2, 4), dtype=np.float32)
    assert np.array_equal(
        normal, make_rng(seed, 9).standard_normal(8, dtype=np.float32).reshape(2, 4)
    )

    shared = _ForkStream("primitive", make_rng(seed, 7))
    _ForkGenerator(_ForkStreamView({"primitive": shared}), "primitive").random(
        4, dtype=np.float32
    )
    with pytest.raises(RuntimeError, match="dtype changed"):
        _ForkGenerator(_ForkStreamView({"primitive": shared}), "primitive").random(
            4, dtype=np.float64
        )


def test_candidate_retention_preserves_mark_rng_stream_position(
    cuda_device: torch.device,
) -> None:
    """No new RNG draw anywhere: retaining the discarded candidate must not
    perturb any owned RNG stream. Two identically seeded collections stay
    byte-identical on primitive actions, event categorical actions,
    `old_log_probs` and `event_old_joint_logp`, and their owned RNG states
    agree afterward -- but that alone only proves the *modified* code is
    self-consistent across two runs, not that its draw count matches the
    pre-change behavior (an added-but-deterministic draw would still pass
    it). The stronger, independent checks below reconstruct the expected
    stream consumption directly from counts recorded in the collected
    trajectory against freshly seeded reference generators, and confirm
    each owned RNG lands in exactly that position: proof the stream
    position is unchanged, not merely reproducible.

    Independently reconstructed:
    - `mark`: one `standard_normal((*, MARK_DIM))` draw per request,
      regardless of derived masking -- unchanged by the Stage-1 edit.
    - `opportunity`: one `choice(OPPORTUNITY_SUPPORT, size=*)` draw per
      request, from the same per-step call site as `mark`.
    - `primitive`: one `random((env_count, MAX_LIFECYCLES), dtype=float32)`
      table per physical collection step, unconditional on requests.

    `Generator.choice`'s internal implementation differs from
    `standard_normal`'s (it is not simply "consume K raw draws"), so its
    chunk-invariance -- drawing N in one call leaves the same state, and
    the same element values, as several calls whose sizes sum to N -- was
    verified independently for this exact call shape (`choice` over a
    fixed 3-element support, `size=N`, default `replace=True`, no `p`)
    before relying on it here; it holds. The same was verified for
    `Generator.random(shape, dtype=np.float32)` chunked along its leading
    axis, matching how `primitive` is drawn once per step.

    Not independently reconstructed here: `event` (categorical mark-kind
    selection consumes one `random(len(requests))` draw per step -- the
    same shape as `opportunity`/`primitive` and reconstructable the same
    way, but extending to it was outside this bounded hardening pass),
    `order` (derived from `frontier_order`, a function of ledger content
    and the active mask rather than a simple per-step draw count) and
    `ledger` (task/ledger generation, not a per-step draw at all). Those
    three streams are covered only by the cross-run agreement check above,
    not by an independent reconstruction.
    """

    arms, _, _ = initialize_arms(cuda_device)
    arm = arms["EHC"]
    state_left = make_training_state("EHC", 0)
    state_right = make_training_state("EHC", 0)
    left = collect_trajectory(
        arm, state_left, device=cuda_device, episode_ids=tuple(range(16))
    )
    right = collect_trajectory(
        arm, state_right, device=cuda_device, episode_ids=tuple(range(16))
    )
    for name in (
        "actions", "event_categorical_actions", "old_log_probs",
        "event_old_joint_logp",
    ):
        assert torch.equal(getattr(left, name), getattr(right, name))
    for name in RNG_NAMES:
        assert (
            state_left.rngs[name].bit_generator.state
            == state_right.rngs[name].bit_generator.state
        )

    total_requests = int(left.event_kind.ne(0).sum())
    assert total_requests > 0

    mark_reference = np.random.default_rng(state_left.seed_map["mark"])
    mark_reference.standard_normal((total_requests, MARK_DIM))
    assert (
        mark_reference.bit_generator.state
        == state_left.rngs["mark"].bit_generator.state
    )

    opportunity_reference = np.random.default_rng(
        state_left.seed_map["opportunity"]
    )
    opportunity_reference.choice(OPPORTUNITY_SUPPORT, size=total_requests)
    assert (
        opportunity_reference.bit_generator.state
        == state_left.rngs["opportunity"].bit_generator.state
    )

    env_count = len(left.ledger_ids)
    primitive_reference = np.random.default_rng(state_left.seed_map["primitive"])
    primitive_reference.random(
        (left.time_steps, env_count, MAX_LIFECYCLES), dtype=np.float32
    )
    assert (
        primitive_reference.bit_generator.state
        == state_left.rngs["primitive"].bit_generator.state
    )


def _tensor_sha256(tensor: torch.Tensor) -> str:
    return hashlib.sha256(
        tensor.detach().cpu().contiguous().numpy().tobytes()
    ).hexdigest()


def test_collector_protected_outputs_pinned_digest(
    cuda_device: torch.device,
) -> None:
    """Regression pin against silent drift in the protected collector
    outputs `event_new_z` / `primitive_z`. `validate_replay` recomputes
    both from the same forward pass that collection used, so if a future
    change silently altered `packed_new_z` on some rows, replay would stay
    self-consistent with the (equally altered) collected value and the
    `<=1e-7` continuation gate would still pass -- both sides would drift
    together. This test compares against a reference fixed independently
    of any code path in this module, for a fixed EHC collection at the
    registered 16-environment width, replicate 0, `train` profile.

    Reproducibility was verified before pinning, not assumed: the SHA256
    digest of both tensors was observed bit-for-bit identical across 3
    collections within one process AND across 2 separate process
    invocations of the same script (6 observations total on this machine,
    zero variation -- see the probe run at task time). Because
    bitwise-exact reproduction held in every observation, this pins an
    exact digest rather than falling back to a numeric summary at
    tolerance.
    """

    arms, _, _ = initialize_arms(cuda_device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(
        arm, state, device=cuda_device, episode_ids=tuple(range(16))
    )
    assert _tensor_sha256(trajectory.event_new_z) == (
        "93456fbf72531b9deb203d86bcb1c012db4d072160450c9e26e333ebd0eb5fd3"
    )
    assert _tensor_sha256(trajectory.primitive_z) == (
        "2c0a71be5a455a3f1260149f5dac4527f6deabaa1ad9de6cfe3267fa8158a57f"
    )


def test_checkpoint_strict_continuation_and_cuda_smoke(
    cuda_device: torch.device, tmp_path,
) -> None:
    arms, base_optimizers, event_optimizers = initialize_arms(cuda_device)
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(
        arms["EHC"], state, device=cuda_device, episode_ids=(0,)
    )
    update = optimize_update(
        arms["EHC"], base_optimizers["EHC"], event_optimizers["EHC"],
        state, trajectory, device=cuda_device,
    )
    assert update["primitive_replays"] == 4
    assert update["event_head_replays"] == 4
    assert update["packed_trajectory_count"] == 1
    checkpoint = tmp_path / "origin.pt"
    save_checkpoint(
        checkpoint, arm=arms["EHC"], base_optimizer=base_optimizers["EHC"],
        event_optimizer=event_optimizers["EHC"], state=state,
    )
    with pytest.raises(ValueError, match="arm/replicate"):
        load_checkpoint(
            checkpoint, device=cuda_device,
            expected_arm="DUM", expected_replicate=0,
        )
    with pytest.raises(ValueError, match="arm/replicate"):
        load_checkpoint(
            checkpoint, device=cuda_device,
            expected_arm="EHC", expected_replicate=1,
        )
    with pytest.raises(ValueError, match="update-250"):
        load_checkpoint(
            checkpoint, device=cuda_device,
            expected_arm="EHC", expected_replicate=0,
            formal_evaluation=True,
        )
    corrupt_payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    corrupt_payload["owned_rngs"].pop("mark")
    corrupt_path = tmp_path / "corrupt_rng.pt"
    torch.save(corrupt_payload, corrupt_path)
    with pytest.raises(ValueError, match="owned-RNG"):
        load_checkpoint(
            corrupt_path, device=cuda_device,
            expected_arm="EHC", expected_replicate=0,
        )

    left_arm, left_base, left_event, left_state = load_checkpoint(
        checkpoint, device=cuda_device,
        expected_arm="EHC", expected_replicate=0,
    )
    left_trajectory = collect_trajectory(
        left_arm, left_state, device=cuda_device, episode_ids=(1,)
    )
    optimize_update(
        left_arm, left_base, left_event, left_state,
        left_trajectory, device=cuda_device,
    )
    left_global = runtime_rng_snapshot()
    right_arm, right_base, right_event, right_state = load_checkpoint(
        checkpoint, device=cuda_device,
        expected_arm="EHC", expected_replicate=0,
    )
    right_trajectory = collect_trajectory(
        right_arm, right_state, device=cuda_device, episode_ids=(1,)
    )
    optimize_update(
        right_arm, right_base, right_event, right_state,
        right_trajectory, device=cuda_device,
    )
    right_global = runtime_rng_snapshot()
    continuation = compare_continuations(
        left_arm, right_arm, left_trajectory, right_trajectory,
        left_base, right_base, left_event, right_event,
        left_state, right_state, left_global, right_global,
    )
    assert continuation["discrete_equal"]
    assert continuation["lifecycle_equal"]
    assert continuation["owned_rng_equal"]
    assert continuation["global_rng_equal"]
    assert max(
        continuation[name] for name in (
            "continuous_error", "model_error", "base_optimizer_error",
            "event_optimizer_error",
        )
    ) <= 1e-7

    smoke = run_smoke(tmp_path / "smoke", device_name="cuda")
    assert smoke["device"] == "cuda" and smoke["formal"] is False
    assert smoke["or_dum_no_op"]
    assert all(value["update"]["primitive_replays"] == 4 for value in smoke["arms"].values())
    assert smoke["arms"]["DUM"]["update"]["base_zero_gradients"] == [1, 1, 1, 1]
    assert all(smoke["continuation"][name] for name in (
        "discrete_equal", "lifecycle_equal", "owned_rng_equal", "global_rng_equal"
    ))
    assert (tmp_path / "smoke" / "smoke_result.json").is_file()
    # The serialized replay evidence must survive the JSON round trip and
    # still satisfy the same fail-closed validation the formal evaluation
    # artifacts are held to -- named per-factor errors plus the derived
    # joint bounds actually applied, never a single collapsed scalar.
    serialized = json.loads(
        (tmp_path / "smoke" / "smoke_result.json").read_text(encoding="utf-8")
    )
    for arm_name in ARMS:
        record = serialized["arms"][arm_name]["replay"]
        assert "maximum_error" not in record
        event_rows = arm_name != "OR"
        assert _replay_record_valid(record, event_rows_required=event_rows), arm_name
        assert _replay_record_valid(
            serialized["arms"][arm_name]["update"]["replay"],
            event_rows_required=event_rows,
        ), arm_name
        assert record["joints"]["event_joint"]["factor_count"] == (
            0.0 if arm_name == "OR" else 9.0
        )
        # An arm that carries an event head must have examined event rows;
        # the ordinary source legitimately has none, and its event joint is
        # then all-zero rather than merely row-less.
        assert (record["joints"]["event_joint"]["rows"] > 0.0) is event_rows
        assert record["joints"]["primitive_joint"]["rows"] > 0.0
        assert _replay_record_valid(record) is event_rows, arm_name
        # Clean trajectories leak nothing outside either factor's support.
        assert record["errors"]["categorical_support_leak"] == 0.0, arm_name
        assert record["errors"]["mark_support_leak"] == 0.0, arm_name


def test_authoritative_seed_maps_and_independent_cells() -> None:
    training = authoritative_seed_map("train", 2)
    iid = authoritative_seed_map("iid", 2)
    held = authoritative_seed_map("held_out", 2)
    assert training == {
        "ledger": TRAIN_TASK_SEED + 2000,
        "order": TRAIN_ORDER_SEED + 2000,
        "primitive": TRAIN_ACTION_SEED + 2000,
        "opportunity": OPPORTUNITY_SEED + 2000,
        "event": EVENT_SEED + 2000,
        "mark": MARK_SEED + 2000,
    }
    assert iid == training | {"ledger": IID_EVAL_TASK_SEED + 2000}
    assert held == training | {"ledger": HELD_OUT_EVAL_TASK_SEED + 2000}
    all_seed_values = set(training.values()) | set(iid.values()) | set(held.values())
    assert 79_058 not in all_seed_values
    assert 89_058 not in all_seed_values
    states = [
        _evaluation_state("EHC", 2, profile=profile)
        for profile, _deterministic, _cell in EVALUATION_CELLS
    ]
    assert states[0] is not states[1] and states[2] is not states[3]
    assert states[0].seed_map == states[1].seed_map == iid
    assert states[2].seed_map == states[3].seed_map == held
    assert all(set(state.rngs) == set(RNG_NAMES) for state in states)


def _synthetic_replay_record() -> dict[str, object]:
    """A clean structured replay record in the registered artifact shape.

    Deliberately not a single scalar: every named factor is present, and
    each derived joint carries the compositional bound it was tested
    against. `_replay_record_valid` re-derives acceptance from these
    numbers, so an incomplete record cannot pass by carrying `passed`.
    """

    def joint(factor_count: float, magnitude: float) -> dict[str, float]:
        allowance = float(float32_reduction_gamma(factor_count) * magnitude)
        return {
            "error": 0.0,
            "component_sum": 0.0,
            "allowance": allowance,
            "bound": allowance,
            "excess": -allowance,
            "factor_count": factor_count,
            "float64_error": 0.0,
            "assembly_residual": 0.0,
            "assembly_allowance": allowance,
            "assembly_excess": -allowance,
            "rows": 1280.0,
        }

    return {
        "errors": {
            name: 0.0
            for name in (
                REPLAY_EXACT_FIELDS + REPLAY_COMPONENT_FIELDS + REPLAY_JOINT_FIELDS
            )
        },
        "joints": {
            "primitive_joint": joint(3.0, 12.0),
            "event_joint": joint(float(EVENT_JOINT_FACTOR_COUNT), 16.0),
        },
        "component_tolerance": REPLAY_COMPONENT_TOLERANCE,
        "failures": [],
        "passed": True,
    }


def _synthetic_operational_records() -> tuple[
    dict[str, object], dict[tuple[int, str, str], dict[str, object]]
]:
    contract = registered_contract()
    arms = {}
    for arm in ARMS:
        checkpoint = f"replicate_0/{arm}/update_250.pt"
        arms[arm] = {
            "arm": arm,
            "replicate": 0,
            "checkpoint": checkpoint,
            "checkpoint_origin": "update_250.pt",
            "completed_update": 250,
            "next_episode_id": 4000,
            "base_steps": 1000,
            "event_steps": 0 if arm == "OR" else 1000,
            "seed_map": authoritative_seed_map("train", 0),
            "checkpoint_resume": True,
        }
    training = {
        "schema_version": TRAIN_MANIFEST_SCHEMA,
        "contract": contract,
        "mode": "formal_train",
        "replicates": {
            "0": {
                "operational": {
                    "no_op": True,
                    "probability_replay": True,
                    "lifecycle": True,
                    "finiteness": True,
                    "rng_pairing": True,
                    "checkpoint_resume": True,
                    "exposure": True,
                },
                "updates": [{} for _ in range(250)],
                "arms": arms,
            }
        },
    }
    cells = {}
    episodes = [{"episode_id": value} for value in range(256)]
    for arm in ARMS:
        for profile, deterministic, cell in EVALUATION_CELLS:
            cells[(0, arm, cell)] = {
                "schema_version": EVALUATION_CELL_SCHEMA,
                "contract": contract,
                "arm": arm,
                "replicate": 0,
                "cell": cell,
                "profile": profile,
                "mode": "deterministic" if deterministic else "stochastic",
                "checkpoint": arms[arm]["checkpoint"],
                "checkpoint_origin": "update_250.pt",
                "counts": {"episodes": 256, "horizon": 80},
                "seed_map": authoritative_seed_map(profile, 0),
                "replay": _synthetic_replay_record(),
                "operational": {
                    "probability_replay": True,
                    "lifecycle": True,
                    "rng": True,
                    "checkpoint": True,
                    "finite": True,
                },
                "episodes": deepcopy(episodes),
            }
    return training, cells


def test_fail_closed_operational_manifest_negatives() -> None:
    training, cells = _synthetic_operational_records()
    valid, errors = validate_operational_records(
        training, cells, expected_replicates=(0,)
    )
    assert valid and not errors
    corrupted_cell = deepcopy(cells)
    corrupted_cell[(0, "EHC", "iid_deterministic")]["profile"] = "held_out"
    assert not validate_operational_records(
        training, corrupted_cell, expected_replicates=(0,)
    )[0]
    # The replay record is conclusion-bearing evidence, so every way of
    # degrading it must fail closed: the retired single-scalar shape, a
    # dropped factor, a component over its own tolerance, a joint over its
    # compositional bound, a joint that is not the sum of its factors, and
    # a `passed` flag not supported by the numbers beneath it.
    for label, mutation in (
        ("legacy_scalar", lambda record: {"maximum_error": 0.0}),
        ("dropped_factor", lambda record: record | {
            "errors": {
                name: value for name, value in record["errors"].items()
                if name != "mark_component"
            }
        }),
        ("component_over_tolerance", lambda record: record | {
            "errors": record["errors"] | {"mark_component": 2e-6}
        }),
        ("joint_over_bound", lambda record: record | {
            "joints": record["joints"] | {
                "event_joint": record["joints"]["event_joint"] | {"excess": 1e-9}
            }
        }),
        ("joint_assembly", lambda record: record | {
            "joints": record["joints"] | {
                "event_joint": record["joints"]["event_joint"]
                | {"assembly_excess": 1e-9}
            }
        }),
        ("unsupported_pass", lambda record: record | {
            "errors": record["errors"] | {"mask_mismatch": 1.0}
        }),
        ("wrong_tolerance", lambda record: record | {"component_tolerance": 1e-5}),
    ):
        degraded = deepcopy(cells)
        target = degraded[(0, "EHC", "iid_stochastic")]
        target["replay"] = mutation(deepcopy(target["replay"]))
        assert not _replay_record_valid(target["replay"]), label
        assert not validate_operational_records(
            training, degraded, expected_replicates=(0,)
        )[0], label
    for family, mutation in (
        ("no_op", lambda value: value["replicates"]["0"]["operational"].__setitem__("no_op", False)),
        ("exposure", lambda value: value["replicates"]["0"]["arms"]["EHC"].__setitem__("base_steps", 999)),
        ("resume", lambda value: value["replicates"]["0"]["arms"]["EHC"].__setitem__("checkpoint_resume", False)),
    ):
        corrupted = deepcopy(training)
        mutation(corrupted)
        operational_valid = validate_operational_records(
            corrupted, cells, expected_replicates=(0,)
        )[0]
        assert not operational_valid, family
        assert select_result_branch(
            **(_branch_inputs() | {"operational_valid": operational_valid})
        ) == "INVALID_OPERATIONAL"


def _branch_inputs() -> dict[str, object]:
    return {
        "operational_valid": True,
        "non_create_opportunities": 1000,
        "multi_opportunity_lifecycles": 250,
        "eligible_keep_rows": SUPPORT_FLOOR,
        "eligible_renew_rows": SUPPORT_FLOOR,
        "utility_ci": {
            "OR": (0.79, 0.81), "DUM": (0.79, 0.81), "EHC": (0.80, 0.84)
        },
        "g_ci": (0.11, 0.15),
        "k_bin_cis": ((0.11, 0.20), (0.11, 0.20), (0.05, 0.09)),
        "intervention_ci": (0.11, 0.20),
    }


def test_result_branch_first_match_and_boundaries() -> None:
    base = _branch_inputs()
    assert select_result_branch(**base) == "COMMITMENT_SUPPORTED"
    assert select_result_branch(
        **(base | {"operational_valid": False, "non_create_opportunities": 0})
    ) == "INVALID_OPERATIONAL"
    assert select_result_branch(
        **(base | {"non_create_opportunities": 999})
    ) == "BENCHMARK_NON_IDENTIFIABLE"
    assert select_result_branch(
        **(base | {"multi_opportunity_lifecycles": 249})
    ) == "BENCHMARK_NON_IDENTIFIABLE"
    # Support-floor boundary: exactly 127 fails, exactly 128 (the base case
    # above) proceeds past BENCHMARK_NON_IDENTIFIABLE.
    assert select_result_branch(
        **(base | {"eligible_keep_rows": SUPPORT_FLOOR - 1})
    ) == "BENCHMARK_NON_IDENTIFIABLE"
    assert select_result_branch(
        **(base | {"eligible_renew_rows": SUPPORT_FLOOR - 1})
    ) == "BENCHMARK_NON_IDENTIFIABLE"
    low = {
        "OR": (0.1, ACCESS_FLOOR - 1e-6),
        "DUM": (0.1, 0.7),
        "EHC": (0.1, 0.7),
    }
    assert select_result_branch(
        **(base | {"utility_ci": low})
    ) == "NO_ACCESS_THIS_BENCHMARK"
    crossing = {
        "OR": (0.7, ACCESS_FLOOR),
        "DUM": (0.7, 0.8),
        "EHC": (0.7, 0.8),
    }
    assert select_result_branch(
        **(base | {"utility_ci": crossing})
    ) == "UNDERPOWERED_ACCESS"
    # Fewer than two K-bins keep UCB above threshold: confident failure.
    assert select_result_branch(
        **(base | {"k_bin_cis": ((0.01, 0.05), (0.01, 0.05), (0.11, 0.20))})
    ) == "REPRESENTATION_ONLY"
    # Equality boundary: UCB exactly at threshold still counts as failed
    # (`UCB <=` threshold), same as the source's strict-dual definition.
    assert select_result_branch(
        **(base | {
            "k_bin_cis": (
                (0.01, LIFETIME_BIN_THRESHOLD),
                (0.01, LIFETIME_BIN_THRESHOLD),
                (0.11, 0.20),
            )
        })
    ) == "REPRESENTATION_ONLY"
    # Intervention confident failure alone, K-bins still passing.
    assert select_result_branch(
        **(base | {"intervention_ci": (0.05, INTERVENTION_THRESHOLD)})
    ) == "REPRESENTATION_ONLY"
    # Interval-crossing boundary: neither passes (strict LCB `>`) nor
    # confidently fails (UCB `<=`) -> falls through to MIXED_UNDERPOWERED.
    assert select_result_branch(
        **(base | {
            "k_bin_cis": (
                (LIFETIME_BIN_THRESHOLD, 0.20), (0.11, 0.20), (0.05, 0.09),
            )
        })
    ) == "MIXED_UNDERPOWERED"
    assert select_result_branch(
        **(base | {"g_ci": (0.0, GAIN_THRESHOLD)})
    ) == "ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED"
    assert select_result_branch(
        **(base | {"g_ci": (0.05, 0.11)})
    ) == "MIXED_UNDERPOWERED"
    contract = registered_contract()
    assert contract["arms"] == ["OR", "DUM", "EHC"]
    assert contract["duration_support"]["held_out"] == [5, 7, 9]
    assert contract["optimization"]["opportunity_support"] == [4, 8, 12]
    assert contract["thresholds"]["support_floor"] == SUPPORT_FLOOR
    assert "keep" not in contract["thresholds"]
    assert "renew" not in contract["thresholds"]
    assert "cv" not in contract["thresholds"]
    # The K-bin battery (policy-determined K==1/K==2/K>=3 over complete
    # spells) must be identifiable from the contract alone, distinct from
    # the physical-time bins the retired "lifetime_bin" name evoked.
    assert "lifetime_bin" not in contract["thresholds"]
    assert contract["thresholds"]["k_bin"] == LIFETIME_BIN_THRESHOLD
    assert contract["k_bins"] == ["K==1", "K==2", "K>=3"]
    assert contract["intervention_metric"] == "primitive_action_total_variation"


def test_select_result_branch_rejects_non_three_k_bins() -> None:
    base = _branch_inputs()
    for wrong in (
        (),
        ((0.1, 0.2),),
        ((0.1, 0.2), (0.1, 0.2)),
        ((0.1, 0.2), (0.1, 0.2), (0.1, 0.2), (0.1, 0.2)),
    ):
        with pytest.raises(ValueError, match="k_bin_cis"):
            select_result_branch(**(base | {"k_bin_cis": wrong}))


def _event_factor_tensors(
    replay: Any, trajectory: Any, device: torch.device
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """The nine recorded event factors, stored and replayed, plus the rows."""

    stored = torch.cat(
        (
            trajectory.event_old_cat_logp.to(device).unsqueeze(-1),
            trajectory.event_old_mark_component_logp.to(device),
        ),
        dim=-1,
    ).double()
    replayed = torch.cat(
        (
            replay.event_cat_logp.unsqueeze(-1),
            replay.event_mark_component_logp,
        ),
        dim=-1,
    ).double()
    return stored, replayed, replay.event_cat_mask | replay.event_mark_mask


def test_derived_joint_bounds_are_recomputed_not_fitted(
    cuda_device: torch.device,
) -> None:
    """The joint allowance follows from the factor algebra, not observation.

    A derived joint accumulates its summands' replay differences, so it
    cannot share a single summand's tolerance. The bound applied is
    `sum_i|f_replay_i - f_stored_i| + gamma_n*(sum|f_stored| + sum|f_replay|)`
    with `gamma_n = n*u/(1 - n*u)` and float32 unit roundoff `u = 2**-24`.
    Every term is recomputed here from the recorded factors and the two
    published contract constants alone -- the observed joint error appears
    nowhere in the allowance -- so a bound quietly widened to whatever a
    particular device happened to produce would fail this test.
    """

    arms, _, _ = initialize_arms(cuda_device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(arm, state, device=cuda_device)
    assert trajectory.active_mask.shape[1] == 16
    replay = replay_trajectory(arm, trajectory, device=cuda_device)
    joints = replay_joint_bounds(replay, trajectory)

    unit_roundoff = 2.0**-24
    assert FLOAT32_UNIT_ROUNDOFF == unit_roundoff
    contract_block = registered_contract()["replay_tolerances"]
    assert contract_block["float32_unit_roundoff"] == unit_roundoff
    assert contract_block["event_joint_factor_count"] == EVENT_JOINT_FACTOR_COUNT == 9
    gamma_nine = 9.0 * unit_roundoff / (1.0 - 9.0 * unit_roundoff)
    assert float32_reduction_gamma(9.0) == gamma_nine
    assert gamma_nine == pytest.approx(5.36442090748478e-07, rel=1e-12)

    stored, replayed, rows = _event_factor_tensors(replay, trajectory, cuda_device)
    assert bool(rows.any())
    error = (
        replay.event_joint_logp - trajectory.event_old_joint_logp.to(cuda_device)
    ).double().abs()
    component_sum = (replayed - stored).abs().sum(-1)
    allowance = gamma_nine * (stored.abs().sum(-1) + replayed.abs().sum(-1))
    worst = int(torch.argmax(error[rows]).detach().cpu())
    record = joints["event_joint"]
    assert record["factor_count"] == 9.0
    assert record["error"] == pytest.approx(float(error[rows][worst]), rel=1e-12)
    assert record["component_sum"] == pytest.approx(
        float(component_sum[rows][worst]), rel=1e-12
    )
    assert record["allowance"] == pytest.approx(
        float(allowance[rows][worst]), rel=1e-12
    )
    assert record["bound"] == pytest.approx(
        float((component_sum + allowance)[rows][worst]), rel=1e-12
    )
    assert record["excess"] == pytest.approx(
        float((error - component_sum - allowance)[rows].max()), rel=1e-12
    )
    assert record["excess"] <= 0.0
    assert record["rows"] == float(int(rows.sum()))

    active = trajectory.active_mask.to(cuda_device)
    stored_logp = trajectory.old_log_probs.to(cuda_device)
    terms = torch.where(active, (replay.log_probs - stored_logp).double(), 0.0)
    primitive_error = (
        torch.where(active, replay.log_probs - stored_logp, 0.0).sum(-1).double().abs()
    )
    counts = active.sum(-1).double()
    primitive_gamma = counts * unit_roundoff / (1.0 - counts * unit_roundoff)
    magnitude = torch.where(
        active, stored_logp.double().abs(), 0.0
    ).sum(-1) + torch.where(active, replay.log_probs.double().abs(), 0.0).sum(-1)
    primitive_rows = active.any(-1)
    assert bool(primitive_rows.any())
    primitive_worst = int(torch.argmax(primitive_error[primitive_rows]).detach().cpu())
    primitive = joints["primitive_joint"]
    # The primitive factor count is the row's own active-lifecycle count,
    # not a constant: a two-lifecycle row must not borrow a six-lifecycle
    # row's allowance.
    assert 1.0 <= primitive["factor_count"] <= float(MAX_LIFECYCLES)
    assert primitive["factor_count"] == float(
        counts[primitive_rows][primitive_worst]
    )
    assert primitive["component_sum"] == pytest.approx(
        float(terms.abs().sum(-1)[primitive_rows][primitive_worst]), rel=1e-12
    )
    assert primitive["allowance"] == pytest.approx(
        float((primitive_gamma * magnitude)[primitive_rows][primitive_worst]),
        rel=1e-12,
    )
    assert primitive["excess"] <= 0.0
    assert len(set(counts[primitive_rows].tolist())) > 1


def _first_renew_index(trajectory: Any) -> tuple[int, ...]:
    """A row whose support carries all nine event factors."""

    rows = torch.nonzero(trajectory.event_kind.eq(RENEW), as_tuple=False)
    assert rows.numel() > 0
    return tuple(int(value) for value in rows[0].detach().cpu())


def _restated_event_factors(
    trajectory: Any,
    *,
    index: tuple[int, ...],
    categorical: torch.Tensor | None = None,
    marks: torch.Tensor | None = None,
) -> Any:
    """Rewrite one row's stored event factors and its stored joint together.

    The joint is reassembled by the collector's own rule
    (`categorical + marks.sum(-1)`, float32), so the recorded joint stays a
    faithful sum of the recorded factors. That isolates the per-component
    guard from the float64 assembly guard: whatever fails afterwards fails
    because a *factor* is wrong, not because the joint stopped matching its
    own factors.
    """

    stored_cat = trajectory.event_old_cat_logp.clone()
    stored_mark = trajectory.event_old_mark_component_logp.clone()
    if categorical is not None:
        stored_cat[index] = categorical
    if marks is not None:
        stored_mark[index] = marks
    stored_joint = trajectory.event_old_joint_logp.clone()
    stored_joint[index] = stored_cat[index] + stored_mark[index].sum(-1)
    return replace(
        trajectory,
        event_old_cat_logp=stored_cat,
        event_old_mark_component_logp=stored_mark,
        event_old_joint_logp=stored_joint,
    )


def test_defective_component_still_fails_under_the_relaxed_joint_rule(
    cuda_device: torch.device,
) -> None:
    """The relaxed joint rule must never rescue a defective factor.

    Each defect below is placed on a RENEW row (all nine factors in
    support) and sized at `2e-6` -- above the unchanged `1e-6` per-component
    bound but far below the derived joint bound, which is roughly `1e-5` on
    these magnitudes. The decisive assertion is therefore not merely that
    `validate_replay` raises, but that it raises *naming the component*
    while the joint it belongs to is still comfortably inside its own
    compositional bound. If the correction had widened the per-component
    class, every case here would pass silently.
    """

    arms, _, _ = initialize_arms(cuda_device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(arm, state, device=cuda_device)
    replay = replay_trajectory(arm, trajectory, device=cuda_device)
    assert replay_report(replay, trajectory)["passed"]
    index = _first_renew_index(trajectory)
    defect = 2e-6

    inputs = trajectory.event_inputs[index].unsqueeze(0).to(cuda_device)
    u_row = trajectory.event_u[index].unsqueeze(0).to(cuda_device)
    with torch.no_grad():
        mu, sigma = _normal_parameters(arm.mark_head(inputs))
        correct_marks = transformed_mark_component_logp(u_row, mu, sigma)[0]
        # The registered Jacobian, recomputed here from the contract's own
        # stable form rather than read back from the module under test.
        log_jacobian = (
            2.0 * (math.log(2.0) - u_row - F.softplus(-2.0 * u_row))
        )[0]
    assert torch.allclose(
        correct_marks,
        trajectory.event_old_mark_component_logp[index],
        atol=REPLAY_COMPONENT_TOLERANCE,
    )
    assert float(log_jacobian.abs().max()) > 0.0

    omitted_jacobian = correct_marks + log_jacobian
    # A Jacobian error of size `d` reaches the likelihood as a mark-component
    # error of size `d`, because the component is `normal - log_jacobian`.
    # `2e-6` is the smallest such error the per-component class must still
    # reject; the whole-row omission is the coarse version of the same fault.
    shifted_jacobian = correct_marks.clone()
    shifted_jacobian[0] = correct_marks[0] - defect

    displaced_marks = trajectory.event_old_mark_component_logp[index].clone()
    displaced_marks[0] = displaced_marks[0] - defect
    cases = {
        "mark_component": _restated_event_factors(
            trajectory, index=index, marks=displaced_marks
        ),
        "categorical_component": _restated_event_factors(
            trajectory,
            index=index,
            categorical=trajectory.event_old_cat_logp[index] - defect,
        ),
        "jacobian_shift": _restated_event_factors(
            trajectory, index=index, marks=shifted_jacobian
        ),
        "jacobian_omitted": _restated_event_factors(
            trajectory, index=index, marks=omitted_jacobian
        ),
    }
    expected_field = {
        "mark_component": "mark_component",
        "categorical_component": "categorical_component",
        "jacobian_shift": "mark_component",
        "jacobian_omitted": "mark_component",
    }
    for label, corrupted in cases.items():
        corrupted_replay = replay_trajectory(arm, corrupted, device=cuda_device)
        report = replay_report(corrupted_replay, corrupted)
        assert not report["passed"], label
        assert expected_field[label] in report["failures"], label
        assert (
            report["errors"][expected_field[label]] > REPLAY_COMPONENT_TOLERANCE
        ), label
        if label != "jacobian_omitted":
            # The joint moved by the same amount and is still well inside
            # its own bound: only the per-component class caught this.
            assert "event_joint" not in report["failures"], label
            assert report["joints"]["event_joint"]["excess"] < 0.0, label
            assert (
                report["errors"]["event_joint"]
                <= report["joints"]["event_joint"]["bound"]
            ), label
        assert "event_joint_assembly" not in report["failures"], label
        with pytest.raises(RuntimeError, match="semantic replay tolerance mismatch"):
            validate_replay(arm, corrupted, device=cuda_device)


def test_joint_rule_admits_accumulation_and_rejects_a_joint_defect(
    cuda_device: torch.device,
) -> None:
    """Accumulation across nine factors passes; a joint defect does not.

    First case: every one of the nine factors on a RENEW row is displaced
    by `2e-7`, which stacks on that row's own reduction-order difference and
    still leaves every component inside the unchanged `1e-6` bound, and the
    recorded joint is reassembled from them. Their sum then exceeds `1e-6`
    -- exactly the situation the old single scalar declared a failure. It
    must pass, and the measured numbers here prove the joint really did
    exceed `1e-6` rather than the test asserting a vacuous inequality.

    Second case: the recorded joint alone is displaced past its
    compositional bound while every factor stays clean. It must raise, and
    it must raise on the joint rather than on any component.
    """

    arms, _, _ = initialize_arms(cuda_device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(arm, state, device=cuda_device)
    index = _first_renew_index(trajectory)
    displacement = 2e-7

    accumulated = _restated_event_factors(
        trajectory,
        index=index,
        categorical=trajectory.event_old_cat_logp[index] - displacement,
        marks=trajectory.event_old_mark_component_logp[index] - displacement,
    )
    accumulated_replay = replay_trajectory(arm, accumulated, device=cuda_device)
    report = replay_report(accumulated_replay, accumulated)
    assert report["passed"], report["failures"]
    assert all(
        report["errors"][name] <= REPLAY_COMPONENT_TOLERANCE
        for name in REPLAY_COMPONENT_FIELDS
    )
    assert report["errors"]["event_joint"] > REPLAY_COMPONENT_TOLERANCE
    assert report["errors"]["event_joint"] <= report["joints"]["event_joint"]["bound"]
    assert report["joints"]["event_joint"]["excess"] < 0.0
    assert report["joints"]["event_joint"]["assembly_excess"] < 0.0
    # It is the nine-way accumulation, not one large factor, that carries
    # the joint past `1e-6`: no single component is even at half the bound.
    assert (
        report["errors"]["event_joint"]
        > 2.0 * max(report["errors"][name] for name in REPLAY_COMPONENT_FIELDS)
    )

    over_bound = trajectory.event_old_joint_logp.clone()
    over_bound[index] = over_bound[index] - 5e-5
    defective = replace(trajectory, event_old_joint_logp=over_bound)
    defective_replay = replay_trajectory(arm, defective, device=cuda_device)
    defective_report = replay_report(defective_replay, defective)
    assert not defective_report["passed"]
    assert "event_joint" in defective_report["failures"]
    assert defective_report["joints"]["event_joint"]["excess"] > 0.0
    assert all(
        defective_report["errors"][name] <= REPLAY_COMPONENT_TOLERANCE
        for name in REPLAY_COMPONENT_FIELDS
    )
    # A joint that is no longer the sum of its own recorded factors is
    # caught by the float64 assembly check as well, independently of the
    # size of the displacement.
    assert "event_joint_assembly" in defective_report["failures"]
    with pytest.raises(RuntimeError, match="event_joint"):
        validate_replay(arm, defective, device=cuda_device)


def test_registered_contract_replay_block_and_checkpoint_strictness(
    cuda_device: torch.device, tmp_path: Any
) -> None:
    """The contract carries the four classes, not one scalar.

    `load_checkpoint` rejects on contract inequality, so a checkpoint
    written under the retired scalar must fail strict load. That is the
    intended consequence of the correction and there is no migration path.
    """

    contract = registered_contract()
    block = contract["replay_tolerances"]
    assert "replay_tolerance" not in contract["optimization"]
    assert "replay_tolerance" not in contract
    assert json.dumps(contract, sort_keys=True).count('"replay_tolerance"') == 0
    assert block["exact_fields"] == list(REPLAY_EXACT_FIELDS)
    assert block["continuous_component_fields"] == list(REPLAY_COMPONENT_FIELDS)
    assert block["joint_fields"] == list(REPLAY_JOINT_FIELDS)
    assert block["continuous_component_atol"] == REPLAY_COMPONENT_TOLERANCE == 1e-6
    assert block["categorical_component_atol"] == REPLAY_COMPONENT_TOLERANCE
    assert block["mark_component_atol"] == REPLAY_COMPONENT_TOLERANCE
    assert block["primitive_joint_rule"] == "component_sum_plus_float32_reduction"
    assert (
        block["event_joint_rule"]
        == "categorical_plus_8_marks_plus_float32_reduction"
    )
    assert block["float32_unit_roundoff"] == 2.0**-24
    # Every field the validator checks is named in the contract, including
    # the two support-leak fields and the full per-joint record shape.
    assert block["support_leak_fields"] == [
        "categorical_support_leak", "mark_support_leak"
    ]
    assert set(block["support_leak_fields"]) <= set(block["exact_fields"])
    assert block["joint_record_fields"] == list(REPLAY_JOINT_RECORD_FIELDS)
    # The two primitive joint gates are declared non-gating rather than
    # advertised as coverage they cannot provide.
    assert block["primitive_joint_gating"].startswith("non_gating")
    assert block["primitive_joint_assembly_gating"].startswith("non_gating")
    assert "primitive_component" in block["primitive_joint_gating"]
    assert "triangle inequality" in block["event_joint_gating"]
    # The intended relaxation is declared, not left to be discovered.
    assert "9e-6" in block["correlated_bias_sensitivity"]
    assert "rows > 0" in block["joint_record_internal_consistency"]
    assert block["non_finite_rule"] == "any_non_finite_leaf_fails_closed"
    # The same-checkpoint continuation invariant is a different quantity and
    # is untouched by the replay correction.
    assert contract["optimization"]["resume_tolerance"] == 1e-7

    arms, base_optimizers, event_optimizers = initialize_arms(cuda_device)
    state = make_training_state("EHC", 0)
    path = tmp_path / "contract_strictness.pt"
    save_checkpoint(
        path, arm=arms["EHC"], base_optimizer=base_optimizers["EHC"],
        event_optimizer=event_optimizers["EHC"], state=state,
    )
    loaded_arm, _, _, _ = load_checkpoint(
        path, device=cuda_device, expected_arm="EHC", expected_replicate=0
    )
    assert nested_state_maximum_difference(
        arms["EHC"].state_dict(), loaded_arm.state_dict()
    ) == 0.0

    payload = torch.load(path, map_location="cpu", weights_only=False)
    legacy = deepcopy(contract)
    legacy.pop("replay_tolerances")
    legacy["optimization"] = dict(legacy["optimization"]) | {
        "replay_tolerance": 1e-6
    }
    payload["contract"] = legacy
    legacy_path = tmp_path / "legacy_contract.pt"
    torch.save(payload, legacy_path)
    with pytest.raises(ValueError, match="registered contract mismatch"):
        load_checkpoint(
            legacy_path, device=cuda_device, expected_arm="EHC",
            expected_replicate=0,
        )


def test_merged_replay_records_keep_every_factor_named() -> None:
    """Merging batches must not collapse the evidence back to one scalar."""

    left = _synthetic_replay_record()
    right = deepcopy(left)
    right["errors"]["mark_component"] = 7e-7
    right["errors"]["event_joint"] = 3e-6
    allowance = float(right["joints"]["event_joint"]["allowance"])
    bound = 2e-6 + allowance
    right["joints"]["event_joint"] = dict(right["joints"]["event_joint"]) | {
        "error": 3e-6, "component_sum": 2e-6, "bound": bound,
        "excess": 3e-6 - bound, "rows": 600.0,
    }
    merged = merge_replay_records([left, right])
    assert set(merged["errors"]) == set(
        REPLAY_EXACT_FIELDS + REPLAY_COMPONENT_FIELDS + REPLAY_JOINT_FIELDS
    )
    assert merged["errors"]["mark_component"] == 7e-7
    assert merged["errors"]["event_joint"] == 3e-6
    # The retained bound is the one the retained error was tested against.
    assert merged["joints"]["event_joint"]["error"] == 3e-6
    assert merged["joints"]["event_joint"]["bound"] == bound
    assert merged["joints"]["event_joint"]["rows"] == 1880.0
    assert merged["joints"]["event_joint"]["excess"] == max(
        left["joints"]["event_joint"]["excess"], 3e-6 - bound
    )
    # The three assembly numbers move together, so the merged record still
    # satisfies `assembly_excess == assembly_residual - assembly_allowance`.
    assert merged["joints"]["event_joint"]["assembly_excess"] == pytest.approx(
        merged["joints"]["event_joint"]["assembly_residual"]
        - merged["joints"]["event_joint"]["assembly_allowance"],
        rel=1e-12,
    )
    assert _replay_record_valid(merged)
    failing = deepcopy(left)
    failing["passed"] = False
    failing["failures"] = ["mark_component"]
    assert not merge_replay_records([left, failing])["passed"]


def _leaked_support_trajectory(
    arm: Any, trajectory: Any, *, field: str, device: torch.device
) -> tuple[Any, torch.Tensor, torch.Tensor]:
    """Record one factor *outside* its own support and reassemble the joint.

    This is the one-line collector regression made explicit. Dropping the
    collector's `torch.where(derived_cat_mask, categorical_logp, 0.0)` records
    a categorical factor on `CREATE` rows, where the factorization says there
    is none, and folds it into the stored joint; the mark twin records a mark
    component on `KEEP` rows from the candidate `u` that was drawn but not
    committed. Both corruptions are built *outside* the factor's mask, which
    is exactly where the masked component checks do not look, and the joint is
    reassembled from the corrupted factors by the collector's own float32 rule
    so the assembly check stays clean and the joint bound widens by precisely
    the corruption.
    """

    kind = trajectory.event_kind.to(device)
    rows = kind.eq(CREATE) if field == "categorical" else kind.eq(KEEP)
    assert bool(rows.any())
    stored_cat = trajectory.event_old_cat_logp.to(device).clone()
    stored_mark = trajectory.event_old_mark_component_logp.to(device).clone()
    inputs = trajectory.event_inputs.to(device)[rows]
    with torch.no_grad():
        if field == "categorical":
            leaked = F.log_softmax(arm.event_head(inputs), dim=-1)[:, 0]
            stored_cat[rows] = leaked
        else:
            mu, sigma = _normal_parameters(arm.mark_head(inputs))
            leaked = transformed_mark_component_logp(
                trajectory.candidate_u.to(device)[rows], mu, sigma
            )
            stored_mark[rows] = leaked
    # Only the corrupted rows are reassembled, so no clean row picks up a
    # reduction-order difference from this test's own summation.
    reassembled = stored_cat + stored_mark.sum(-1)
    stored_joint = torch.where(
        rows, reassembled, trajectory.event_old_joint_logp.to(device)
    )
    corrupted = replace(
        trajectory,
        event_old_cat_logp=stored_cat,
        event_old_mark_component_logp=stored_mark,
        event_old_joint_logp=stored_joint,
    )
    return corrupted, leaked, rows


def test_factor_recorded_outside_its_own_support_is_rejected(
    cuda_device: torch.device,
) -> None:
    """A factor outside its mask is a defect no joint bound can catch.

    Given the two assembly checks hold, the joint rule reduces to
    `|sum d_i| <= sum|d_i| + gamma(...)`, the triangle inequality -- an
    identity. So a factor recorded non-zero outside its own support, with the
    stored joint reassembled to include it, is invisible three ways at once:
    `categorical_component` is read only inside `event_cat_mask` and
    `mark_component` only inside `event_mark_mask`, the assembly check sees a
    self-consistent sum, and the joint bound widens by exactly the
    corruption. Every other corruption test in this file builds its defect
    *inside* the support, so this is the invariant a wrong implementation
    could previously violate while passing all of them.

    The stored joint is consumed unmasked at `event_ratio = torch.exp(...)`,
    so what reaches PPO here is a first-pass importance ratio far from one.
    Both assertions below are therefore load-bearing: the joint class must be
    shown *not* to fire, and the exact class must.
    """

    arms, _, _ = initialize_arms(cuda_device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(arm, state, device=cuda_device)
    clean = replay_report(
        replay_trajectory(arm, trajectory, device=cuda_device), trajectory
    )
    assert clean["passed"]
    assert clean["errors"]["categorical_support_leak"] == 0.0
    assert clean["errors"]["mark_support_leak"] == 0.0

    for field, leak_name in (
        ("categorical", "categorical_support_leak"),
        ("mark", "mark_support_leak"),
    ):
        corrupted, leaked, rows = _leaked_support_trajectory(
            arm, trajectory, field=field, device=cuda_device
        )
        assert float(leaked.abs().max()) > 1e-3, field
        report = replay_report(
            replay_trajectory(arm, corrupted, device=cuda_device), corrupted
        )
        assert not report["passed"], field
        assert leak_name in report["failures"], field
        assert report["errors"][leak_name] == pytest.approx(
            float(leaked.abs().max()), rel=1e-12
        ), field
        # The corruption really does reach the ratio PPO would start from.
        assert report["errors"]["event_joint"] > 0.1, field
        # ... and none of the classes that already existed can see it.
        assert "event_joint" not in report["failures"], field
        assert "event_joint_assembly" not in report["failures"], field
        assert report["joints"]["event_joint"]["excess"] <= 0.0, field
        assert report["joints"]["event_joint"]["assembly_excess"] <= 0.0, field
        assert "categorical_component" not in report["failures"], field
        assert "mark_component" not in report["failures"], field
        assert "mask_mismatch" not in report["failures"], field
        with pytest.raises(RuntimeError, match=leak_name):
            validate_replay(arm, corrupted, device=cuda_device)
        # The other support-leak field is untouched: the two look in
        # different places and neither stands in for the other.
        other = (
            "mark_support_leak" if field == "categorical"
            else "categorical_support_leak"
        )
        assert report["errors"][other] == 0.0, field


def test_replay_reports_and_records_fail_closed_on_non_finite_values(
    cuda_device: torch.device,
) -> None:
    """NaN must fail, not pass. `nan > tol` and `nan > 0.0` are both false.

    Written as `not (x <= limit)` throughout, a NaN fails every gate; written
    as `x > limit` it satisfies every one of them, so a live replay producing
    NaN would report `passed: True`. The record validator and the merge are
    held to the same rule -- `max(0.0, nan)` is `0.0` in Python while
    `max(nan, 0.0)` is `nan`, so a plain maximum launders NaN out of the
    evidence depending on batch order.
    """

    arms, _, _ = initialize_arms(cuda_device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(arm, state, device=cuda_device)
    index = _first_renew_index(trajectory)
    for label, mutation in (
        ("joint", "event_old_joint_logp"),
        ("mark", "event_old_mark_component_logp"),
    ):
        tensor = getattr(trajectory, mutation).clone()
        tensor[index] = float("nan")
        corrupted = replace(trajectory, **{mutation: tensor})
        report = replay_report(
            replay_trajectory(arm, corrupted, device=cuda_device), corrupted
        )
        assert not report["passed"], label
        assert any(
            name.startswith("non_finite:") for name in report["failures"]
        ), label
        with pytest.raises(RuntimeError):
            validate_replay(arm, corrupted, device=cuda_device)

    clean = _synthetic_replay_record()
    assert _replay_record_valid(clean)
    for label, path in (
        ("error_leaf", ("errors", "mark_component")),
        ("exact_leaf", ("errors", "mark_support_leak")),
        ("joint_excess", ("joints", "event_joint", "excess")),
        ("joint_assembly", ("joints", "primitive_joint", "assembly_excess")),
    ):
        degraded = deepcopy(clean)
        target = degraded
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = float("nan")
        assert not _replay_record_valid(degraded), label
        with pytest.raises(ValueError, match="non-finite"):
            merge_replay_records([clean, degraded])
        # Order must not decide: the laundering form of the bug is
        # order-dependent, the fail-closed form is not.
        with pytest.raises(ValueError, match="non-finite"):
            merge_replay_records([degraded, clean])


def test_replay_record_validator_rejects_degraded_joint_records() -> None:
    """The validator is advertised as fail-closed re-derivation; hold it to that.

    A record that carries only the three keys a reader happens to look at, a
    record that examined no rows, and a record whose declared bound is not the
    sum of its own parts all prove nothing, and all previously validated.
    """

    clean = _synthetic_replay_record()
    assert _replay_record_valid(clean)

    # Truncated joint: only the keys the old validator read.
    truncated = deepcopy(clean)
    truncated["joints"]["event_joint"] = {
        key: clean["joints"]["event_joint"][key]
        for key in ("excess", "assembly_excess", "bound")
    }
    assert not _replay_record_valid(truncated)
    assert set(clean["joints"]["event_joint"]) == set(REPLAY_JOINT_RECORD_FIELDS)

    # `rows: 0` on an arm that carries an event head proves nothing was
    # examined; the ordinary source's all-zero event joint is the one lawful
    # form of it, and only when every other number is zero too.
    no_rows = deepcopy(clean)
    no_rows["joints"]["event_joint"]["rows"] = 0.0
    assert not _replay_record_valid(no_rows)
    assert not _replay_record_valid(no_rows, event_rows_required=False)
    ordinary = deepcopy(clean)
    ordinary["joints"]["event_joint"] = {
        key: 0.0 for key in REPLAY_JOINT_RECORD_FIELDS
    }
    assert not _replay_record_valid(ordinary)
    assert _replay_record_valid(ordinary, event_rows_required=False)
    no_primitive_rows = deepcopy(clean)
    no_primitive_rows["joints"]["primitive_joint"]["rows"] = 0.0
    assert not _replay_record_valid(no_primitive_rows, event_rows_required=False)

    # A self-declared bound must be the sum of its own parts, and the parts
    # must be supported by the recorded per-factor errors. Without both, a
    # record can validate `error = 1e9` beneath `bound = 1e10`.
    inconsistent = deepcopy(clean)
    inconsistent["errors"]["event_joint"] = 1e9
    inconsistent["joints"]["event_joint"] |= {
        "error": 1e9, "bound": 1e10, "excess": -9e9
    }
    assert not _replay_record_valid(inconsistent)
    self_consistent = deepcopy(inconsistent)
    allowance = float(clean["joints"]["event_joint"]["allowance"])
    self_consistent["joints"]["event_joint"] |= {
        "component_sum": 1e10 - allowance
    }
    # Now `bound == component_sum + allowance`, so only the link to the
    # recorded per-factor errors still rejects it.
    assert self_consistent["joints"]["event_joint"]["bound"] == pytest.approx(
        self_consistent["joints"]["event_joint"]["component_sum"] + allowance,
        rel=1e-12,
    )
    assert not _replay_record_valid(self_consistent)

    # `excess` must dominate `error - bound`; it is the row maximum and the
    # reported error/bound come from the largest-error row.
    understated = deepcopy(clean)
    understated["joints"]["event_joint"] |= {
        "error": 2e-6, "excess": -1e9
    }
    assert not _replay_record_valid(understated)

    # The assembly triple is read at one row and one side, so it must be
    # exactly self-consistent.
    assembly = deepcopy(clean)
    assembly["joints"]["event_joint"]["assembly_residual"] = 1e-7
    assert not _replay_record_valid(assembly)
