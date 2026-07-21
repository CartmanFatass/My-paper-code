from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import random

import numpy as np
import pytest
import torch
import torch.nn.functional as F

from ha_ctse_process.event_held_commitment_link import (
    CREATE,
    KEEP,
    MARK_DIM,
    OPPORTUNITY_SUPPORT,
    RENEW,
    RNG_NAMES,
    _normal_parameters,
    action_distribution_tv,
    authoritative_seed_map,
    base_primitive_logits,
    collect_trajectory,
    compare_continuations,
    factor_counts,
    initialize_arms,
    load_checkpoint,
    make_training_state,
    natural_and_permuted_action_tv,
    nested_state_maximum_difference,
    optimize_update,
    parameter_and_optimizer_counts,
    runtime_rng_equal,
    runtime_rng_snapshot,
    save_checkpoint,
    validate_replay,
)
from ha_ctse_process.dynamic_roster_testbed import MAX_LIFECYCLES
from ha_ctse_process.noncalendar_commitment_testbed import (
    ACCESS_FLOOR,
    EVENT_SEED,
    GAIN_THRESHOLD,
    HELD_OUT_EVAL_TASK_SEED,
    IID_EVAL_TASK_SEED,
    INTERVENTION_THRESHOLD,
    LIFETIME_BIN_THRESHOLD,
    MARK_SEED,
    OPPORTUNITY_SEED,
    SUPPORT_FLOOR,
    TRAIN_ACTION_SEED,
    TRAIN_ORDER_SEED,
    TRAIN_TASK_SEED,
    NoncalendarTrackingEnv,
    make_noncalendar_ledger,
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
    _trajectory_episode_rows,
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
    _replay, errors = validate_replay(
        arms["DUM"], trajectory, device=cuda_device
    )
    assert max(errors.values()) <= 1e-6
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
                "replay": {"maximum_error": 0.0},
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
