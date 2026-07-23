from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping
import base64
import functools
import hashlib
import json
import math
import random
import shutil
import zlib
from collections import Counter, defaultdict

import numpy as np
import pytest
import torch
import torch.nn.functional as F

from ha_ctse_process import event_held_commitment_link
from scripts import run_noncalendar_commitment_benchmark_g0 as benchmark_runner
from ha_ctse_process.event_held_commitment_link import (
    CREATE,
    EVENT_INPUT_DIM,
    AUDIT_BRANCHES,
    AUDIT_STREAM_NAMES,
    KEEP,
    MARK_DIM,
    OPPORTUNITY_SUPPORT,
    RENEW,
    RNG_NAMES,
    TYPED_CAUSAL_AUDIT_SCHEMA,
    _nested_equal,
    _normal_parameters,
    _rng_states,
    action_distribution_tv,
    authoritative_seed_map,
    batched_natural_and_permuted_action_tv,
    collect_trajectory,
    compare_continuations,
    factor_counts,
    audit_opportunities_batched,
    native_bitwise_finite_comparison,
    audit_single_opportunity,
    initialize_arms,
    load_checkpoint,
    make_training_state,
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
    validate_typed_natural_audit,
)
from ha_ctse_process.dynamic_roster_testbed import HORIZON, MAX_LIFECYCLES
from ha_ctse_process.noncalendar_commitment_testbed import (
    ACCESS_FLOOR,
    ADDED_PARAMETER_COUNT,
    C_TOTAL_KEEP_LCB_FLOOR,
    C_TOTAL_KEEP_MEAN_FLOOR,
    C_TOTAL_RENEW_LCB_FLOOR,
    C_TOTAL_RENEW_MEAN_FLOOR,
    BOOTSTRAP_SEED,
    EVENT_JOINT_FACTOR_COUNT,
    EVENT_SEED,
    FLOAT32_UNIT_ROUNDOFF,
    FORMAL_EXECUTION_BACKEND,
    GAIN_THRESHOLD,
    HELD_OUT_EVAL_TASK_SEED,
    IID_EVAL_TASK_SEED,
    INTERVENTION_THRESHOLD,
    LIFETIME_BIN_THRESHOLD,
    MARK_SEED,
    CAUSAL_AUDIT_BRANCHES,
    CAUSAL_AUDIT_BRANCH_ROWS,
    CAUSAL_AUDIT_NATURAL_ACTIONS,
    CAUSAL_AUDIT_QUOTA_PER_ACTION,
    CAUSAL_AUDIT_REPLICATES,
    CAUSAL_AUDIT_SELECTED_ROWS,
    CAUSAL_AUDIT_SELECTION_COORDINATE,
    CAUSAL_AUDIT_SELECTION_NAMESPACE,
    OPPORTUNITY_SEED,
    PARAMETER_COUNT,
    REGISTERED_EXECUTION_BACKENDS,
    REGISTERED_TORCH_THREADS,
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
    SUPPORT_FLOOR,
    TRAIN_ACTION_SEED,
    TRAIN_ORDER_SEED,
    TRAIN_TASK_SEED,
    NoncalendarTrackingEnv,
    active_execution_backend,
    float32_reduction_gamma,
    make_noncalendar_ledger,
    make_rng,
    paired_ledgers_equal_except_targets,
    registered_contract,
    require_registered_backend,
    select_result_branch,
)
from scripts.run_noncalendar_commitment_benchmark_g0 import (
    ARMS,
    EVALUATION_CELLS,
    EVALUATION_CELL_SCHEMA,
    FORMAL_EVALUATION_ARTIFACT_SCHEMA,
    FORMAL_AUTHORIZATION,
    FORMAL_TRAIN_ARTIFACT_SCHEMA,
    TRAIN_MANIFEST_SCHEMA,
    _aggregate_analysis_core,
    _digest_json,
    _evaluation_state,
    _json_default,
    _replay_record_valid,
    _training_update_valid,
    _trajectory_episode_rows,
    _write_json,
    formal_path_exercise,
    merge_replay_records,
    run_smoke,
)


@pytest.fixture(scope="session", autouse=True)
def registered_backend() -> str:
    """Activate the registered execution backend once per session.

    The rule is "never silently fall back", not "always CUDA": both `cuda`
    and `cpu` are registered backends and the focused suite exercises the one
    the formal run is registered on. It still fails closed -- an unavailable
    registered backend fails the session rather than being substituted.

    Autouse and session-scoped because `registered_contract()` refuses to
    build a contract before a backend is active, and the contract is compared
    for equality by every checkpoint and artifact assertion in this file.
    """

    try:
        require_registered_backend(FORMAL_EXECUTION_BACKEND)
    except (ValueError, RuntimeError) as error:
        pytest.fail(
            f"EVENT_HELD_COMMITMENT_LINK_G0 focused evidence requires the "
            f"registered {FORMAL_EXECUTION_BACKEND!r} backend; no fallback "
            f"({error})"
        )
    return FORMAL_EXECUTION_BACKEND


@pytest.fixture(scope="module")
def device(registered_backend: str) -> torch.device:
    return torch.device(registered_backend)


@pytest.fixture(scope="module")
def streamed_exercise_root(
    device: torch.device, tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    # Exercises the registered backend, whichever it is. Pinning this to
    # "cuda" made 21 tests error on a CUDA-less host while the code under
    # test was backend-agnostic.
    root = tmp_path_factory.mktemp("streamed_formal_path")
    formal_path_exercise(root, device_name=device.type)
    return root / "formal_path_exercise"


def _assert_likelihood_within_frozen_contract(
    report: dict[str, Any], name: str,
) -> None:
    """Hold a likelihood component to the registered rule, not to zero.

    Fails on a real defect rather than on device noise: an omitted mark
    component, a dropped Jacobian or a wrong mask moves `absolute_error` by
    orders of magnitude past `mixed_bound`, and the component's name then
    appears in `failures`. What it stops doing is failing on a legal one-ULP
    difference the frozen contract admits.
    """

    assert report["passed"], report["failures"]
    assert name not in report["failures"], report["failures"]
    record = report["likelihood_components"][name]
    assert float(record["absolute_error"]) <= float(record["mixed_bound"]), record
    assert float(record["ratio_drift"]) <= report["ratio_drift_cap"], record


def _assert_joint_within_frozen_contract(
    report: dict[str, Any], name: str,
) -> None:
    """Hold a joint to its compositional rule, not to a scalar threshold."""

    assert report["passed"], report["failures"]
    assert name not in report["failures"], report["failures"]
    joint = report["joints"][name]
    assert float(joint["excess"]) <= 0.0, joint
    assert float(joint["assembly_excess"]) <= 0.0, joint


def test_shared_event_heads_are_row_stable_and_used_by_collection_and_replay(
    device: torch.device, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both heads have one packing-independent binary32 implementation."""

    arms, _, _ = initialize_arms(device)
    arm = arms["EHC"]
    assert arm.event_head is not None and arm.mark_head is not None
    generator = torch.Generator(device="cpu").manual_seed(202_607_22)
    inputs = torch.randn(
        (23, EVENT_INPUT_DIM), generator=generator, dtype=torch.float32,
    ).to(device)
    helper = event_held_commitment_link._row_stable_event_heads
    together = helper(inputs, arm.event_head, arm.mark_head)

    permutation = torch.tensor(
        [7, 2, 19, 0, 13, 22, 5, 11, 1, 17, 8, 21, 3, 15, 6, 20, 9,
         4, 18, 10, 14, 12, 16],
        device=device,
    )
    inverse = torch.argsort(permutation)
    permuted = helper(inputs[permutation], arm.event_head, arm.mark_head)
    partitioned_pairs = [
        helper(part, arm.event_head, arm.mark_head)
        for part in inputs.split((1, 4, 7, 11))
    ]
    partitioned = tuple(
        torch.cat([pair[head] for pair in partitioned_pairs], dim=0)
        for head in range(2)
    )
    singled = helper(inputs[9:10], arm.event_head, arm.mark_head)
    for head in range(2):
        assert torch.equal(together[head], permuted[head][inverse])
        assert torch.equal(together[head], partitioned[head])
        assert torch.equal(together[head][9:10], singled[head])

    calls: list[int] = []

    def observed(
        packed: torch.Tensor, event_head: Any, mark_head: Any,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        calls.append(int(packed.shape[0]))
        return helper(packed, event_head, mark_head)

    monkeypatch.setattr(
        event_held_commitment_link, "_row_stable_event_heads", observed,
    )
    stochastic = collect_trajectory(
        arm, make_training_state("EHC", 0), device=device,
    )
    collection_calls = len(calls)
    assert collection_calls > 0
    deterministic = collect_trajectory(
        arm, make_training_state("EHC", 0), device=device, deterministic=True,
    )
    assert len(calls) > collection_calls
    before_replay = len(calls)
    replay = replay_trajectory(arm, stochastic, device=device)
    assert len(calls) == before_replay + 1
    report = replay_report(replay, stochastic)
    # The exact-equality assertions above this line are the deliberate ones:
    # they feed *identical* rows to the *identical* evaluator, so bitwise
    # agreement is the property the helper actually promises.
    #
    # The assertions below used to demand `errors[...] == 0.0` for the
    # likelihood classes too. That was stricter than the registered contract
    # they exist to protect: the frozen replay rules govern likelihood
    # components with the mixed absolute-relative bound plus the ratio cap,
    # and joints with the compositional excess -- not exact zero. On CPU
    # `mark_component` measures 2.384e-07 with `passed` True, so the oracle
    # contradicted the contract rather than the code failing it. Aligned to
    # the frozen contract on external ruling; the exact classes are unchanged.
    _assert_likelihood_within_frozen_contract(report, "categorical_component")
    _assert_likelihood_within_frozen_contract(report, "mark_component")
    _assert_joint_within_frozen_contract(report, "event_joint")
    # Deterministic selection changes samples only; it reaches the same head
    # evaluator and remains exactly replayable.
    deterministic_report = replay_report(
        replay_trajectory(arm, deterministic, device=device), deterministic,
    )
    _assert_likelihood_within_frozen_contract(
        deterministic_report, "mark_component",
    )


def test_initialization_rng_isolation_and_capacity(
    device: torch.device,
) -> None:
    random.seed(144)
    np.random.seed(145)
    torch.manual_seed(146)
    torch.cuda.manual_seed_all(147)
    before = runtime_rng_snapshot()
    arms, base_optimizers, event_optimizers = initialize_arms(device)
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
        device, mark_seed=MARK_SEED + 1
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
    device: torch.device,
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

    arms, _, _ = initialize_arms(device)
    full_state = make_training_state("EHC", 0)
    partial_state = make_training_state("EHC", 0)
    full = collect_trajectory(
        arms["EHC"], full_state, device=device, episode_ids=(0,)
    )
    first = collect_trajectory(
        arms["EHC"], partial_state, device=device,
        episode_ids=(0,), max_steps=17,
    )
    second = collect_trajectory(
        arms["EHC"], partial_state, device=device, cursor=first.cursor
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
        arms["EHC"], forced_state, device=device,
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
        arms["EHC"], forced_state, device=device,
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
    device: torch.device,
) -> None:
    arms, _, _ = initialize_arms(device)
    state = make_training_state("EHC", 0)
    episode_count = 8
    trajectory = collect_trajectory(
        arms["EHC"], state, device=device,
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
    device: torch.device,
) -> None:
    """`_trajectory_episode_rows` and `aggregate_analysis` previously had no
    test at all -- the same unreachability that let a `torch.flatnonzero`
    call and an `env_index` indexing bug survive a freeze. This builds rows
    on a real collected trajectory, JSON round-trips them (as the real
    evaluate/analyze split does through disk), and checks the row/segment
    accounting `aggregate_analysis` relies on."""

    arms, _, _ = initialize_arms(device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(
        arm, state, device=device, episode_ids=tuple(range(16))
    )
    rows, reduction_counts = _trajectory_episode_rows(
        trajectory, arm, compute_intervention=True
    )
    assert reduction_counts["keep"] == sum(row["keep"] for row in rows)
    assert reduction_counts["renew"] == sum(row["renew"] for row in rows)
    assert reduction_counts["intervention_values"] == sum(
        len(row["intervention"]) for row in rows
    )
    round_tripped = json.loads(json.dumps(rows, default=_json_default))

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
    device: torch.device,
) -> None:
    # This is the specific defect being fixed: the superseded
    # ||W_z(z - z_perm)|| / sqrt(3) metric is positive for a residual
    # proportional to (c, c, c), even though a softmax-common shift leaves
    # the three-action distribution exactly unchanged. Assert the fixed
    # I_TV metric is exactly (within float tolerance) zero in that case.
    natural = torch.tensor([0.7, -1.3, 2.1], device=device)
    for constant in (4.25, -9.0, 0.0):
        perturbed = natural + constant
        tv = action_distribution_tv(natural, perturbed)
        assert float(tv.detach().cpu()) == pytest.approx(0.0, abs=1e-6)

    # Batched form: a per-row constant shift must still cancel exactly.
    batch_natural = torch.tensor(
        [[0.1, 0.2, 0.3], [-2.0, 0.5, 1.5], [3.0, -3.0, 0.0]], device=device
    )
    shifts = torch.tensor([[1.0], [-3.5], [0.0]], device=device)
    tv_batch = action_distribution_tv(batch_natural, batch_natural + shifts)
    assert torch.allclose(tv_batch, torch.zeros_like(tv_batch), atol=1e-6)


def _sequential_intervention_oracle(
    arm: Any, trajectory: Any, *, device: torch.device
) -> tuple[torch.Tensor, torch.Tensor, float]:
    """Independent sequential oracle for the registered TV estimand."""

    values = torch.zeros_like(trajectory.active_mask, dtype=torch.float32, device=device)
    eligible = torch.zeros_like(trajectory.active_mask, dtype=torch.bool, device=device)
    natural_logp_error = 0.0
    for env_index in range(len(trajectory.ledger_ids)):
        for time in range(trajectory.time_steps):
            active = trajectory.active_mask[time, env_index:env_index + 1].to(device)
            keys = torch.nonzero(active[0], as_tuple=True)[0]
            observations = trajectory.observations[time, env_index:env_index + 1].to(device)
            order = trajectory.orders[time, env_index:env_index + 1].to(device)
            hidden = trajectory.hidden_before[time, env_index:env_index + 1].to(device)
            actions = trajectory.actions[time, env_index:env_index + 1].to(device)
            prepared = arm.base.prepare_step(
                observations=observations, active_mask=active, validated=True
            )
            prefix = torch.zeros((1, 3), dtype=observations.dtype, device=device)
            logits_by_key: dict[int, torch.Tensor] = {}
            for position in range(int(active.sum())):
                key = int(order[0, position])
                candidate = arm.base.actor_rnn(
                    torch.cat((
                        prepared.member_embeddings[:, key], prepared.context, prefix
                    ), dim=-1),
                    hidden[:, key],
                )
                logits = arm.base.action_head(torch.cat((candidate, prefix), dim=-1))[0]
                logits_by_key[key] = logits
                action = int(actions[0, key])
                prefix[0, action] += 1.0
                z = trajectory.primitive_z[time, env_index, key].to(device)
                reconstructed = F.log_softmax(logits + arm.primitive_bias(z), dim=-1)[action]
                stored = trajectory.old_log_probs[time, env_index, key].to(device)
                natural_logp_error = max(
                    natural_logp_error, float((reconstructed - stored).abs())
                )
            if keys.numel() < 2:
                continue
            z = trajectory.primitive_z[time, env_index, keys].to(device)
            permuted = torch.roll(z, 1, 0)
            for index, key_tensor in enumerate(keys):
                key = int(key_tensor)
                natural_logits = logits_by_key[key] + arm.primitive_bias(z[index])
                permuted_logits = logits_by_key[key] + arm.primitive_bias(permuted[index])
                values[time, env_index, key] = action_distribution_tv(
                    natural_logits, permuted_logits
                )
                eligible[time, env_index, key] = True
    return values, eligible, natural_logp_error


def test_batched_intervention_matches_sequential_oracle_registered_shape(
    device: torch.device,
) -> None:
    generator = torch.Generator(device=device).manual_seed(4471)
    random_natural = 6.0 * torch.randn((256, 3), generator=generator, device=device)
    random_perm = 6.0 * torch.randn((256, 3), generator=generator, device=device)
    tv = action_distribution_tv(random_natural, random_perm)
    assert bool((tv >= -1e-6).all())
    assert bool((tv <= 1.0 + 1e-6).all())

    arms, _, _ = initialize_arms(device)
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(
        arms["EHC"], state, device=device, episode_ids=tuple(range(16))
    )
    batched_values, batched_eligible = batched_natural_and_permuted_action_tv(
        arms["EHC"], trajectory, device=device
    )
    oracle_values, oracle_eligible, natural_logp_error = _sequential_intervention_oracle(
        arms["EHC"], trajectory, device=device
    )
    assert torch.equal(batched_eligible, oracle_eligible)
    assert torch.equal(
        torch.nonzero(batched_eligible), torch.nonzero(oracle_eligible)
    )
    assert int(batched_eligible.sum()) > 0
    assert torch.allclose(
        batched_values[batched_eligible], oracle_values[oracle_eligible],
        atol=2.0 * FLOAT32_UNIT_ROUNDOFF, rtol=0.0,
    )
    assert natural_logp_error <= 1e-6
    assert bool((batched_values[batched_eligible] >= -1e-7).all())
    assert bool((batched_values[batched_eligible] <= 1.0 + 1e-7).all())
    rows, reductions = _trajectory_episode_rows(
        trajectory, arms["EHC"], compute_intervention=True
    )
    kind_cpu = trajectory.event_kind.detach().cpu()
    oracle_cpu = oracle_values.detach().cpu()
    eligible_cpu = oracle_eligible.detach().cpu()
    for env_index, row in enumerate(rows):
        keep = renew = 0
        lifecycle_opportunities = [0] * MAX_LIFECYCLES
        intervention_values: list[float] = []
        for time_index in range(trajectory.time_steps):
            for key in range(MAX_LIFECYCLES):
                kind = int(kind_cpu[time_index, env_index, key])
                keep += int(kind == KEEP)
                renew += int(kind == RENEW)
                lifecycle_opportunities[key] += int(kind in (KEEP, RENEW))
                if bool(eligible_cpu[time_index, env_index, key]):
                    intervention_values.append(
                        float(oracle_cpu[time_index, env_index, key])
                    )
        assert row["keep"] == keep
        assert row["renew"] == renew
        assert row["non_create"] == keep + renew
        assert row["multi_opportunity_lifecycles"] == sum(
            value >= 2 for value in lifecycle_opportunities
        )
        assert row["intervention"] == pytest.approx(
            intervention_values, abs=2.0 * FLOAT32_UNIT_ROUNDOFF
        )
    assert reductions == {
        "keep": sum(row["keep"] for row in rows),
        "renew": sum(row["renew"] for row in rows),
        "non_create": sum(row["non_create"] for row in rows),
        "multi_opportunity_lifecycles": sum(
            row["multi_opportunity_lifecycles"] for row in rows
        ),
        "intervention_values": sum(len(row["intervention"]) for row in rows),
    }

    # OR carries no W_z treatment at all: the intervention is vacuous.
    or_state = make_training_state("OR", 0)
    or_trajectory = collect_trajectory(
        arms["OR"], or_state, device=device, episode_ids=(0,)
    )
    or_values, or_eligible = batched_natural_and_permuted_action_tv(
        arms["OR"], or_trajectory, device=device
    )
    assert not bool(or_eligible.any())
    assert bool(or_values.eq(0).all())


def _corrupt_tensor(tensor: torch.Tensor, index: tuple[int, ...]) -> torch.Tensor:
    value = tensor.clone()
    value[index] += 0.25
    return value


def test_semantic_replay_corruption_negatives(
    device: torch.device,
) -> None:
    arms, _, _ = initialize_arms(device)
    state = make_training_state("DUM", 0)
    trajectory = collect_trajectory(
        arms["DUM"], state, device=device, episode_ids=(0,)
    )
    _replay, report = validate_replay(
        arms["DUM"], trajectory, device=device
    )
    errors = report["errors"]
    assert report["passed"] and not report["failures"]
    assert all(errors[name] == 0.0 for name in REPLAY_EXACT_FIELDS)
    assert all(errors[name] <= REPLAY_STATE_ATOL for name in REPLAY_STATE_FIELDS)
    assert all(
        report["likelihood_components"][name]["absolute_error"]
        <= report["likelihood_components"][name]["mixed_bound"]
        and report["likelihood_components"][name]["ratio_drift"]
        <= REPLAY_LOG_RATIO_DRIFT_CAP
        for name in REPLAY_LOG_COMPONENT_FIELDS
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
            validate_replay(arms["DUM"], value, device=device)

    changed_kind = trajectory.event_kind.clone()
    changed_kind[event_index] = 0
    with pytest.raises(RuntimeError, match="semantic replay"):
        validate_replay(
            arms["DUM"], replace(trajectory, event_kind=changed_kind),
            device=device,
        )


def test_candidate_retention_faithful_and_recovers_discarded_keep(
    device: torch.device,
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
        arms, base_optimizers, event_optimizers = initialize_arms(device)
        arm = arms["EHC"]
        state = make_training_state("EHC", 0)
        trajectory = collect_trajectory(
            arm, state, device=device, episode_ids=tuple(range(16))
        )
        if corrupt:
            trajectory = replace(
                trajectory,
                candidate_u=torch.full_like(trajectory.candidate_u, float("nan")),
                candidate_z=torch.full_like(trajectory.candidate_z, float("nan")),
            )
        update = optimize_update(
            arm, base_optimizers["EHC"], event_optimizers["EHC"], state,
            trajectory, device=device,
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
    device: torch.device,
) -> None:
    """With `deterministic=True` the registered mark rule sets `u = mu`
    for every request. `candidate_u`/`candidate_z` must retain exactly
    that value; recomputed here independently from the stored
    `event_inputs` and the arm's own `mark_head`, for every request row
    (CREATE/KEEP/RENEW alike, not only the categorical-masked ones)."""

    arms, _, _ = initialize_arms(device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(
        arm, state, device=device, episode_ids=tuple(range(16)),
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


# CAUSAL_AUDIT_CORE_TESTS

def _trace_key(batch_index: int, trace: dict[str, Any]) -> tuple[int, ...]:
    coordinate = trace["coordinate"]
    return (
        batch_index, int(coordinate["time"]), int(coordinate["env_index"]),
        int(coordinate["key"]), int(coordinate["membership_epoch"]),
        int(coordinate["segment_id"]),
    )


def _audit_action(trace: dict[str, Any]) -> str:
    return "KEEP" if int(trace["natural_kind"]) == KEEP else "RENEW"


@pytest.fixture(scope="module")
def causal_audit_oracle_bundle(device: torch.device) -> dict[str, Any]:
    arms, _, _ = initialize_arms(device)
    arm = arms["EHC"]
    origins, trajectories, end_states = [], [], []
    for batch_index in range(2):
        state = make_training_state("EHC", 0, profile="held_out")
        origins.append(deepcopy(state))
        trajectories.append(collect_trajectory(
            arm, state, device=device,
            episode_ids=tuple(range(batch_index * 16, (batch_index + 1) * 16)),
            deterministic=False, profile="held_out",
            causal_audit_evidence=True,
        ))
        end_states.append(event_held_commitment_link.owned_rng_states(state))
    inventory: dict[tuple[int, ...], dict[str, Any]] = {}
    cells: dict[tuple[int, int], list[tuple[int, ...]]] = defaultdict(list)
    for batch_index, trajectory in enumerate(trajectories):
        assert trajectory.raw_event_trace and trajectory.outcomes
        for trace in trajectory.raw_event_trace:
            key = _trace_key(batch_index, trace)
            inventory[key] = trace
            cells[(batch_index, key[1])].append(key)
    anchor, keys = next(
        (cell, rows) for cell, rows in sorted(cells.items())
        if cell[0] == 0 and cell[1] > 0 and len(rows) >= 5
    )
    chosen = sorted(keys)[:5]
    chosen += [next(
        row for cell, rows in sorted(cells.items())
        if cell[0] == 0 and cell != anchor for row in sorted(rows)
    )]
    chosen += [next(
        row for cell, rows in sorted(cells.items())
        if cell[0] == 1 for row in sorted(rows)
    )]
    for action in CAUSAL_AUDIT_NATURAL_ACTIONS:
        while sum(_audit_action(inventory[row]) == action for row in chosen) < 2:
            chosen.append(next(
                row for row, trace in sorted(inventory.items())
                if row not in chosen and _audit_action(trace) == action
            ))
    strata: dict[str, list[tuple[int, ...]]] = defaultdict(list)
    for row in sorted(chosen):
        strata[_audit_action(inventory[row])].append(row)
    donor_for = {
        recipient: rows[(index + 1) % len(rows)]
        for rows in strata.values() for index, recipient in enumerate(rows)
    }
    selected = []
    for index, recipient in enumerate(sorted(chosen)):
        batch_index, time, env_index, key, _epoch, _segment = recipient
        donor = donor_for[recipient]
        binding = {"recipient_key": list(recipient), "donor_key": list(donor)}
        selected.append({
            "audit_id": f"audit-{index}", "replicate": 0,
            "batch_index": batch_index, "time": time,
            "env_index": env_index, "key": key,
            "natural_action": _audit_action(inventory[recipient]),
            "trajectory": trajectories[batch_index],
            "origin_state": origins[batch_index],
            "recipient_key": list(recipient), "donor_key": list(donor),
            "mapping_position": strata[_audit_action(inventory[recipient])].index(recipient),
            "donor_candidate_u": inventory[donor]["candidate_u"],
            "donor_candidate_z": inventory[donor]["candidate_z"],
            "donor_binding": binding,
            "selected_state": {"batch_index": batch_index, "time": time,
                               "env_index": env_index, "key": key},
        })
    return {
        "arm": arm, "origins": origins, "trajectories": trajectories,
        "end_states": end_states,
        "inventory": inventory, "selected": selected,
        "batched": audit_opportunities_batched(arm, selected, device=device, debug=True),
    }


def test_three_branch_width16_batched_audit_matches_sequential_oracle(
    device: torch.device, causal_audit_oracle_bundle: dict[str, Any],
) -> None:
    bundle = causal_audit_oracle_bundle
    selected, batched = bundle["selected"], bundle["batched"]
    assert tuple(AUDIT_BRANCHES) == tuple(CAUSAL_AUDIT_BRANCHES)
    assert {row["batch_index"] for row in selected} == {0, 1}
    assert len({(row["batch_index"], row["time"]) for row in selected}) >= 3
    cell_counts = Counter((row["batch_index"], row["time"]) for row in selected)
    expected_calls = len(cell_counts) + sum(math.ceil(value / 5) for value in cell_counts.values())
    assert 5 in cell_counts.values()
    for row, packed in zip(selected, batched, strict=True):
        diagnostics: dict[str, Any] = {}
        sequential = audit_single_opportunity(
            bundle["arm"], bundle["trajectories"][row["batch_index"]],
            env_index=row["env_index"], time=row["time"], key=row["key"],
            device=device, state=bundle["origins"][row["batch_index"]],
            donor_candidate_u=row["donor_candidate_u"],
            donor_candidate_z=row["donor_candidate_z"],
            donor_binding=row["donor_binding"], deterministic=False,
            diagnostics=diagnostics,
        )
        assert set(packed["branches"]) == set(CAUSAL_AUDIT_BRANCHES)
        assert packed["rng_contract_equal"] is True
        assert validate_typed_natural_audit(packed["natural_audit"])
        assert packed["natural_audit"]["schema"] == TYPED_CAUSAL_AUDIT_SCHEMA
        assert packed["natural_audit"]["status"] in {"complete", "unavailable"}
        for branch in CAUSAL_AUDIT_BRANCHES:
            assert packed["branch_outcomes"][branch] == sequential["branch_outcomes"][branch]
            assert packed["branches"][branch]["trajectory"].rewards.shape[1] == 16
        telemetry = packed["telemetry"]
        assert telemetry["selected_state_count"] == len(selected)
        assert telemetry["collector_call_count"] == expected_calls
        assert telemetry["serialized_size_bytes"] > 0
        assert 0.0 <= telemetry["prefix_seconds"] <= telemetry["total_seconds"]
        assert 0.0 <= telemetry["branch_seconds"] <= telemetry["total_seconds"]
        assert packed["selected_state"] == row["selected_state"]

def _first_complete_natural_audit(bundle: dict[str, Any]) -> dict[str, Any]:
    for result in bundle["batched"]:
        audit = result["natural_audit"]
        if audit["status"] == "complete":
            assert validate_typed_natural_audit(audit)
            return deepcopy(audit)
    pytest.fail("typed discriminator requires one complete natural recurrence")



def _flip_first_payload_bit(payload: dict[str, Any]) -> None:
    encoded = bytearray(base64.b64decode(payload["bytes_b64"], validate=True))
    encoded[0] ^= 1
    raw = bytes(encoded)
    payload["bytes_b64"] = base64.b64encode(raw).decode("ascii")
    payload["sha256"] = hashlib.sha256(raw).hexdigest()


def _resign_typed_pair(audit: dict[str, Any], pair: dict[str, Any]) -> None:
    binding = audit["binding_evidence"]
    pair["pair_digest"] = event_held_commitment_link._canonical_json_digest({
        "schema": TYPED_CAUSAL_AUDIT_SCHEMA,
        "audit_id": binding["audit_id"],
        "replicate": int(binding["replicate"]),
        "batch_index": int(binding["batch_index"]),
        "source_episode": int(binding["source_episode"]),
        "source_environment": int(binding["source_environment"]),
        "focal_time": int(binding["focal_time"]),
        "focal_key": int(binding["focal_key"]),
        "natural_action": binding["natural_action"],
        "natural_branch": binding["natural_branch"],
        "continuation_offset": int(pair["continuation_offset"]),
        "coordinate": pair["coordinate"],
        "source_call": pair["source_call"],
        "natural_call": pair["natural_call"],
    })


def _patch_lightweight_typed_validator_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_held_commitment_link,
        "_typed_rng_evidence_valid",
        lambda _evidence: True,
    )
    monkeypatch.setattr(
        event_held_commitment_link,
        "_validate_replay_report_evidence",
        lambda _report, **_kwargs: (True, True, True),
    )


def _lightweight_typed_natural_audit(
    natural_action: str,
    *,
    audit_id: str,
    source_episode: int,
    source_environment: int = 0,
    batch_index: int = 0,
    focal_time: int = 0,
    focal_key: int = 0,
    membership_epoch: int = 0,
    segment_id: int = 0,
) -> dict[str, Any]:
    assert natural_action in {"KEEP", "RENEW"}
    natural_branch = (
        "KEEP_HELD_MARK"
        if natural_action == "KEEP"
        else "RENEW_CANDIDATE_MARK"
    )
    native_payload = event_held_commitment_link._native_payload
    empty_parameter_digest = (
        event_held_commitment_link._parameter_payload_digest(())
    )
    parameter_evidence = {
        family: {"parameters": [], "digest": empty_parameter_digest}
        for family in ("event", "mark", "primitive")
    }
    final_action = KEEP if natural_action == "KEEP" else RENEW
    base_coordinate = {
        "time": focal_time,
        "episode_id": source_episode,
        "environment_row": source_environment,
        "lifecycle_key": focal_key,
        "membership_epoch": membership_epoch,
        "segment_id": segment_id,
    }

    def canonical_call(
        family: str,
        call_id: int,
        call_input: Mapping[str, Any],
        payload: Mapping[str, Any],
        *,
        coordinate: Mapping[str, Any],
        packed_width: int,
        row: int,
        physical_rows: list[Any],
    ) -> dict[str, Any]:
        identity = {
            "sampler_family": family,
            "call_site": event_held_commitment_link._CALL_SITES[family],
            "call_id": call_id,
            "packed_width": packed_width,
            "row": row,
            "scientific_coordinate": dict(coordinate),
            "input_digest": (
                event_held_commitment_link._canonical_json_digest(call_input)
            ),
            "parameter_digest": parameter_evidence[family]["digest"],
            "payload_digest": (
                event_held_commitment_link._canonical_json_digest(payload)
            ),
        }
        return {
            "identity": identity,
            "physical_rows": physical_rows,
            "input": dict(call_input),
            "payload": dict(payload),
            "identity_digest": (
                event_held_commitment_link._canonical_json_digest(identity)
            ),
        }

    scalar_input = native_payload(np.asarray([0.0], dtype=np.float32))
    event_payload = {
        "logits": native_payload(
            np.asarray([0.0, 0.0], dtype=np.float32)
        ),
        "probabilities": native_payload(
            np.asarray([0.5, 0.5], dtype=np.float32)
        ),
        "cdf": native_payload(np.asarray([0.5, 1.0], dtype=np.float32)),
        "converted_uniform": native_payload(
            np.asarray([0.25], dtype=np.float32)
        ),
        "pre_force_action": final_action,
        "final_action": final_action,
    }
    mark_payload = {
        name: native_payload(np.asarray([0.0], dtype=np.float32))
        for name in (
            "mu", "sigma", "noise", "u", "tanh_u", "candidate_mark",
            "installed_z_pre",
        )
    }
    primitive_input = {
        "action_input": native_payload(
            np.asarray([0.0], dtype=np.float32)
        ),
        "primitive_bias": native_payload(
            np.asarray([0.0], dtype=np.float32)
        ),
    }
    primitive_payload = {
        "logits": native_payload(
            np.asarray([0.0, 0.0, 0.0], dtype=np.float32)
        ),
        "probabilities": native_payload(
            np.asarray([0.25, 0.25, 0.5], dtype=np.float32)
        ),
        "cdf": native_payload(
            np.asarray([0.25, 0.5, 1.0], dtype=np.float32)
        ),
        "converted_uniform": native_payload(
            np.asarray([0.125], dtype=np.float32)
        ),
        "selected_action": 0,
    }
    event_coordinate = base_coordinate | {"request_kind": KEEP}
    primitive_coordinate = base_coordinate | {"autoregressive_position": 0}
    source_calls = [
        canonical_call(
            "event", 0, scalar_input, event_payload,
            coordinate=event_coordinate,
            packed_width=1,
            row=0,
            physical_rows=[[source_environment, focal_key, KEEP]],
        ),
        canonical_call(
            "mark", 1, scalar_input, mark_payload,
            coordinate=event_coordinate,
            packed_width=1,
            row=0,
            physical_rows=[[source_environment, focal_key, KEEP]],
        ),
        canonical_call(
            "primitive", 2, primitive_input, primitive_payload,
            coordinate=primitive_coordinate,
            packed_width=16,
            row=source_environment,
            physical_rows=list(range(16)),
        ),
    ]
    pairs = []
    for source_call in source_calls:
        natural_call = deepcopy(source_call)
        pair_coordinate = list(
            event_held_commitment_link._call_coordinate_key(source_call)
        )
        pairs.append({
            "coordinate": pair_coordinate,
            "continuation_offset": 0,
            "source_call": source_call,
            "natural_call": natural_call,
            "pair_digest": None,
            "passed": True,
        })
    expected_family_counts = {"event": 1, "mark": 1, "primitive": 1}
    binding = {
        "audit_id": audit_id,
        "replicate": 0,
        "batch_index": batch_index,
        "source_episode": source_episode,
        "focal_time": focal_time,
        "source_environment": source_environment,
        "focal_key": focal_key,
        "membership_epoch": membership_epoch,
        "segment_id": segment_id,
        "natural_action": natural_action,
        "natural_branch": natural_branch,
        "parameter_evidence": parameter_evidence,
        "expected_family_counts": expected_family_counts,
        "expected_pairs": len(pairs),
        "source_call_count": len(pairs),
        "natural_call_count": len(pairs),
        "duplicate_source": False,
        "duplicate_natural": False,
        "pairs": pairs,
        "passed": True,
    }
    boolean_fields = {
        "active_mask", "terminal", "event_cat_mask", "event_mark_mask",
    }
    true_boolean_fields = {
        "active_mask", "event_cat_mask", "event_mark_mask",
    }
    structural_fields = []
    for field in event_held_commitment_link.CAUSAL_STRUCTURAL_FIELDS:
        if field in boolean_fields:
            array = np.asarray(
                [field in true_boolean_fields], dtype=np.bool_,
            )
        else:
            array = np.asarray(
                [KEEP if field == "event_kind" else 0], dtype=np.int64,
            )
        payload = native_payload(array)
        structural_fields.append(
            native_bitwise_finite_comparison(payload, payload, field=field)
        )
    causal_fields = []
    for field in event_held_commitment_link.CAUSAL_FLOAT_FIELDS:
        payload = native_payload(np.asarray([0.0], dtype=np.float32))
        causal_fields.append(
            native_bitwise_finite_comparison(payload, payload, field=field)
        )
    for pair in pairs:
        family = pair["source_call"]["identity"]["sampler_family"]
        causal_fields.extend(
            event_held_commitment_link._call_input_comparisons(
                pair["source_call"]["input"],
                pair["natural_call"]["input"],
                family=family,
                pair_coordinate=pair["coordinate"],
            )
        )
    comparison_names = {
        "event": ("cdf", "converted_uniform"),
        "mark": (
            "mu", "sigma", "noise", "u", "tanh_u", "candidate_mark",
        ),
        "primitive": ("cdf", "converted_uniform"),
    }
    kernel_comparisons = {}
    for pair in pairs:
        family = pair["source_call"]["identity"]["sampler_family"]
        kernel_comparisons[family] = [
            event_held_commitment_link._paired_comparison(
                pair["source_call"]["payload"][field],
                pair["natural_call"]["payload"][field],
                field=f"{family}.{field}",
                pair_coordinate=pair["coordinate"],
            )
            for field in comparison_names[family]
        ]
    reward_payload = native_payload(np.asarray([0.0], dtype=np.float32))
    reward_comparison = native_bitwise_finite_comparison(
        reward_payload, reward_payload, field="rewards",
    )
    record = {
        "schema": TYPED_CAUSAL_AUDIT_SCHEMA,
        "status": "complete",
        "reason_code": None,
        "causal_identity_passed": True,
        "derived_record_fidelity_passed": True,
        "runtime_provenance": event_held_commitment_link._runtime_provenance(),
        "binding_evidence": binding,
        "structural_evidence": {
            "fields": structural_fields,
            "passed": True,
        },
        "causal_field_evidence": {
            "fields": causal_fields,
            "passed": True,
        },
        "segment_evidence": {"source": [], "natural": [], "passed": True},
        "outcome_evidence": {
            "source": {},
            "natural": {},
            "reward_comparison": reward_comparison,
            "passed": True,
        },
        "rng_evidence": {
            "realized_variates_exact": True,
            "passed": True,
        },
        "kernel_evidence": {
            "event": {
                "expected_call_count": 1,
                "comparisons": kernel_comparisons["event"],
                "selected_actions_exact": True,
                "parameter_exact": True,
                "passed": True,
            },
            "mark": {
                "expected_call_count": 1,
                "comparisons": kernel_comparisons["mark"],
                "passed": True,
            },
            "primitive": {
                "expected_call_count": 1,
                "comparisons": kernel_comparisons["primitive"],
                "selected_actions_exact": True,
                "parameter_exact": True,
                "passed": True,
            },
        },
        "derived_evidence": {
            "replay_report": {},
            "critic_record_valid": True,
            "likelihood_components_valid": True,
            "joint_record_valid": True,
            "passed": True,
        },
        "first_failure": None,
        "attempted_rows": 1,
        "completed_rows": 1,
    }
    for pair in pairs:
        _resign_typed_pair(record, pair)
    return record


def _typed_outer_row(audit: Mapping[str, Any]) -> dict[str, Any]:
    binding = audit["binding_evidence"]
    return {
        "audit_id": binding["audit_id"],
        "replicate": binding["replicate"],
        "batch_index": binding["batch_index"],
        "episode_id": binding["source_episode"],
        "time": binding["focal_time"],
        "env_index": binding["source_environment"],
        "key": binding["focal_key"],
        "membership_epoch": binding["membership_epoch"],
        "segment_id": binding["segment_id"],
        "natural_action": binding["natural_action"],
    }


def test_typed_validator_requires_natural_action_branch_bijection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_lightweight_typed_validator_dependencies(monkeypatch)
    clean_keep = _lightweight_typed_natural_audit(
        "KEEP", audit_id="keep-audit", source_episode=0,
    )
    clean_renew = _lightweight_typed_natural_audit(
        "RENEW", audit_id="renew-audit", source_episode=2,
    )
    assert validate_typed_natural_audit(clean_keep)
    assert validate_typed_natural_audit(clean_renew)

    wrong_legal_label = deepcopy(clean_renew)
    wrong_legal_label["binding_evidence"][
        "natural_branch"
    ] = "RENEW_DERANGED_MARK"
    for pair in wrong_legal_label["binding_evidence"]["pairs"]:
        _resign_typed_pair(wrong_legal_label, pair)
    assert not validate_typed_natural_audit(wrong_legal_label)


def test_runner_outer_binding_requires_row_derived_natural_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_lightweight_typed_validator_dependencies(monkeypatch)
    clean = _lightweight_typed_natural_audit(
        "RENEW", audit_id="renew-audit", source_episode=2,
    )
    outer_row = _typed_outer_row(clean)
    assert benchmark_runner._typed_binding_matches_causal_row(
        clean, outer_row, replicate=0,
    )

    wrong_legal_label = deepcopy(clean)
    wrong_legal_label["binding_evidence"][
        "natural_branch"
    ] = "RENEW_DERANGED_MARK"
    for pair in wrong_legal_label["binding_evidence"]["pairs"]:
        _resign_typed_pair(wrong_legal_label, pair)
    assert not benchmark_runner._typed_binding_matches_causal_row(
        wrong_legal_label, outer_row, replicate=0,
    )


@pytest.mark.parametrize(
    ("result_action", "result_branch"),
    (
        ("RENEW", "KEEP_HELD_MARK"),
        ("KEEP", "RENEW_CANDIDATE_MARK"),
    ),
)
def test_live_collection_rejects_engine_natural_action_branch_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    result_action: str,
    result_branch: str,
) -> None:
    _patch_lightweight_typed_validator_dependencies(monkeypatch)
    monkeypatch.setattr(
        benchmark_runner, "CAUSAL_AUDIT_QUOTA_PER_ACTION", 1,
    )
    mark_payload = benchmark_runner._float32_payload(
        np.zeros(MARK_DIM, dtype=np.float32)
    )
    raw_event_trace = [
        {
            "coordinate": {
                "time": 0,
                "env_index": env_index,
                "key": 0,
                "membership_epoch": 0,
                "segment_id": 0,
            },
            "natural_kind": natural_kind,
            "origin_binding": {"episode_id": episode_id},
            "installed_z": deepcopy(mark_payload),
            "candidate_u": deepcopy(mark_payload),
            "candidate_z": deepcopy(mark_payload),
        }
        for env_index, natural_kind, episode_id in (
            (0, KEEP, 0),
            (1, RENEW, 2),
        )
    ]
    trajectory = SimpleNamespace(
        raw_event_trace=raw_event_trace,
        event_z_pre=torch.zeros((1, 2, 1, MARK_DIM), dtype=torch.float32),
        candidate_u=torch.zeros((1, 2, 1, MARK_DIM), dtype=torch.float32),
        candidate_z=torch.zeros((1, 2, 1, MARK_DIM), dtype=torch.float32),
    )
    first_key = (0, 0, 0, 0, 0, 0, 0, "KEEP")
    audit_id = benchmark_runner._digest_json(list(first_key))
    natural_audit = _lightweight_typed_natural_audit(
        "KEEP", audit_id=audit_id, source_episode=0,
    )

    def mismatched_engine(
        _arm: Any,
        selected: list[dict[str, Any]],
        *,
        device: torch.device,
    ) -> list[dict[str, Any]]:
        assert len(selected) == 2
        assert device.type == "cpu"
        return [{
            "audit_id": audit_id,
            "natural_action": result_action,
            "natural_branch": result_branch,
            "natural_audit": natural_audit,
        }]

    monkeypatch.setattr(
        benchmark_runner, "audit_opportunities_batched", mismatched_engine,
    )
    with pytest.raises(
        RuntimeError,
        match="INVALID_OPERATIONAL engine natural action/branch mismatch",
    ):
        benchmark_runner._collect_causal_audit_evidence(
            object(),
            replicate=0,
            batches=[(trajectory, object(), {})],
            episode_rows=[
                {"episode_id": 0, "outcome": {}},
                {"episode_id": 2, "outcome": {}},
            ],
            device=torch.device("cpu"),
            formal=False,
            mode="formal_path_exercise_evaluate",
        )


def _structured_unavailable_audit(clean: dict[str, Any]) -> dict[str, Any]:
    unavailable = deepcopy(clean)
    comparison = unavailable["causal_field_evidence"]["fields"][0]
    _flip_first_payload_bit(comparison["source_payload"])
    replacement = native_bitwise_finite_comparison(
        comparison["source_payload"],
        comparison["natural_payload"],
        field=comparison["field"],
    )
    unavailable["causal_field_evidence"]["fields"][0] = replacement
    unavailable["causal_field_evidence"]["passed"] = False
    unavailable["causal_identity_passed"] = False
    unavailable["status"] = "unavailable"
    unavailable["reason_code"] = "natural_branch_causal_identity_failed"
    unavailable["first_failure"] = {
        "class": "causal_field",
        "field": replacement["field"],
        "coordinate": replacement["first_coordinate"],
        "magnitude": replacement["magnitude"],
        "ulp_distance": replacement["ulp_distance"],
        "detail": replacement["detail"],
    }
    unavailable["completed_rows"] = 0
    assert validate_typed_natural_audit(unavailable)
    return unavailable


class TestTypedDerivedOnlyUlpDiscriminator:
    def test_one_to_four_ulp_mark_drift_is_derived_only(
        self, causal_audit_oracle_bundle: dict[str, Any],
    ) -> None:
        clean = _first_complete_natural_audit(causal_audit_oracle_bundle)
        causal_evidence = {
            name: deepcopy(clean[name])
            for name in (
                "binding_evidence", "structural_evidence",
                "causal_field_evidence", "segment_evidence",
                "outcome_evidence", "rng_evidence", "kernel_evidence",
            )
        }
        for ulps in range(1, 5):
            mutated = deepcopy(clean)
            mark = mutated["derived_evidence"]["replay_report"][
                "likelihood_components"
            ]["mark_component"]
            replayed = np.float32(mark["replayed_value"])
            for _ in range(ulps):
                replayed = np.nextafter(
                    replayed, np.float32(np.inf), dtype=np.float32,
                )
            mark["replayed_value"] = float(replayed)
            stale = deepcopy(mutated)
            assert not validate_typed_natural_audit(stale), ulps
            stored = float(mark["stored_value"])
            replayed_value = float(mark["replayed_value"])
            mark["absolute_error"] = abs(replayed_value - stored)
            mark["mixed_bound"] = (
                REPLAY_LOG_COMPONENT_ATOL
                + REPLAY_LOG_COMPONENT_RTOL
                * max(abs(stored), abs(replayed_value))
            )
            mark["ratio_drift"] = abs(math.expm1(replayed_value - stored))
            spacing, distance = (
                event_held_commitment_link._float32_ulp_evidence(
                    stored, replayed_value,
                )
            )
            mark["float32_ulp_at_max_magnitude"] = spacing
            mark["ulp_distance"] = distance
            assert mutated["causal_identity_passed"] is True
            assert {
                name: mutated[name] for name in causal_evidence
            } == causal_evidence
            assert validate_typed_natural_audit(mutated), ulps

    def test_derived_stale_arithmetic_fails_closed(
        self, causal_audit_oracle_bundle: dict[str, Any],
    ) -> None:
        mutated = _first_complete_natural_audit(causal_audit_oracle_bundle)
        mark = mutated["derived_evidence"]["replay_report"][
            "likelihood_components"
        ]["mark_component"]
        mark["replayed_value"] = float(
            np.nextafter(
                np.float32(mark["replayed_value"]),
                np.float32(np.inf),
                dtype=np.float32,
            )
        )
        assert not validate_typed_natural_audit(mutated)


class TestTypedOneBitKeyInvariants:
    @pytest.mark.parametrize(
        "evidence_class",
        (
            "causal_leaf", "event_cdf", "primitive_cdf",
            "compared_uniform", "pair_binding",
        ),
    )
    def test_one_bit_mutation_fails_named_evidence_class(
        self, causal_audit_oracle_bundle: dict[str, Any],
        evidence_class: str,
    ) -> None:
        mutated = _first_complete_natural_audit(causal_audit_oracle_bundle)
        if evidence_class == "pair_binding":
            identity = mutated["binding_evidence"]["pairs"][0][
                "source_call"
            ]["identity"]
            digest = identity["parameter_digest"]
            identity["parameter_digest"] = (
                ("0" if digest[0] != "0" else "1") + digest[1:]
            )
        else:
            if evidence_class == "causal_leaf":
                target = mutated["causal_field_evidence"]["fields"][0]
            else:
                family = (
                    "primitive"
                    if evidence_class == "primitive_cdf" else "event"
                )
                field = (
                    "primitive.cdf"
                    if evidence_class == "primitive_cdf"
                    else "event.converted_uniform"
                    if evidence_class == "compared_uniform"
                    else "event.cdf"
                )
                target = next(
                    row
                    for row in mutated["kernel_evidence"][family]["comparisons"]
                    if row["field"] == field
                )
            _flip_first_payload_bit(target["source_payload"])
        assert not validate_typed_natural_audit(mutated), evidence_class

    def test_coherent_payload_and_identity_staleness_fail_closed(
        self, causal_audit_oracle_bundle: dict[str, Any],
    ) -> None:
        clean = _first_complete_natural_audit(causal_audit_oracle_bundle)
        payload_stale = deepcopy(clean)
        pair = next(
            row for row in payload_stale["binding_evidence"]["pairs"]
            if row["source_call"]["identity"]["sampler_family"] == "event"
        )
        for side in ("source_call", "natural_call"):
            _flip_first_payload_bit(pair[side]["payload"]["cdf"])
        replacement = native_bitwise_finite_comparison(
            pair["source_call"]["payload"]["cdf"],
            pair["natural_call"]["payload"]["cdf"],
            field="event.cdf",
        ) | {"pair_coordinate": deepcopy(pair["coordinate"])}
        comparisons = payload_stale["kernel_evidence"]["event"]["comparisons"]
        comparisons[comparisons.index(next(
            row for row in comparisons
            if row["field"] == "event.cdf"
            and row["pair_coordinate"] == pair["coordinate"]
        ))] = replacement
        assert not validate_typed_natural_audit(payload_stale)

        identity_stale = deepcopy(clean)
        pair = next(
            row for row in identity_stale["binding_evidence"]["pairs"]
            if row["source_call"]["identity"]["sampler_family"] == "event"
        )
        for side in ("source_call", "natural_call"):
            call = pair[side]
            digest = call["identity"]["payload_digest"]
            call["identity"]["payload_digest"] = (
                ("0" if digest[0] != "0" else "1") + digest[1:]
            )
            call["identity_digest"] = (
                event_held_commitment_link._canonical_json_digest(
                    call["identity"]
                )
            )
        _resign_typed_pair(identity_stale, pair)
        assert not validate_typed_natural_audit(identity_stale)

    def test_outer_row_swap_fails_binding(
        self, causal_audit_oracle_bundle: dict[str, Any],
    ) -> None:
        first = _first_complete_natural_audit(causal_audit_oracle_bundle)
        second = next(
            deepcopy(result["natural_audit"])
            for result in causal_audit_oracle_bundle["batched"]
            if result["natural_audit"]["binding_evidence"]["source_episode"]
            != first["binding_evidence"]["source_episode"]
        )
        binding = first["binding_evidence"]
        row = {
            "audit_id": binding["audit_id"],
            "replicate": binding["replicate"],
            "batch_index": binding["batch_index"],
            "episode_id": binding["source_episode"],
            "time": binding["focal_time"],
            "env_index": binding["source_environment"],
            "key": binding["focal_key"],
            "membership_epoch": binding["membership_epoch"],
            "segment_id": binding["segment_id"],
            "natural_action": binding["natural_action"],
        }
        assert benchmark_runner._typed_binding_matches_causal_row(
            first, row, replicate=0,
        )
        swapped = deepcopy(row)
        swapped["episode_id"] = second["binding_evidence"]["source_episode"]
        assert not benchmark_runner._typed_binding_matches_causal_row(
            first, swapped, replicate=0,
        )

    def test_actual_width_row_and_family_inventory(
        self, causal_audit_oracle_bundle: dict[str, Any],
    ) -> None:
        audit = _first_complete_natural_audit(causal_audit_oracle_bundle)
        binding = audit["binding_evidence"]
        families = Counter(
            pair["source_call"]["identity"]["sampler_family"]
            for pair in binding["pairs"]
        )
        assert dict(families) == binding["expected_family_counts"]
        assert families["event"] > 0
        assert families["mark"] >= families["event"]
        for pair in binding["pairs"]:
            for side in ("source_call", "natural_call"):
                call = pair[side]
                identity = call["identity"]
                assert identity["packed_width"] == len(call["physical_rows"])
                assert 0 <= identity["row"] < identity["packed_width"]
                if identity["sampler_family"] == "primitive":
                    assert identity["packed_width"] == 16
                else:
                    physical = call["physical_rows"][identity["row"]]
                    scientific = identity["scientific_coordinate"]
                    assert physical == [
                        scientific["environment_row"],
                        scientific["lifecycle_key"],
                        scientific["request_kind"],
                    ]
                    if identity["sampler_family"] == "event":
                        assert scientific["request_kind"] != CREATE


class TestTypedRealPathRecurrence:
    def test_registered_width_is_complete_or_structured_unavailable(
        self, causal_audit_oracle_bundle: dict[str, Any],
    ) -> None:
        results = causal_audit_oracle_bundle["batched"]
        assert results
        for result in results:
            audit = result["natural_audit"]
            serialized_audit = json.loads(json.dumps(audit))
            assert validate_typed_natural_audit(audit)
            assert validate_typed_natural_audit(serialized_audit)
            assert audit["schema"] == TYPED_CAUSAL_AUDIT_SCHEMA
            if audit["status"] == "complete":
                assert audit["reason_code"] is None
                assert audit["causal_identity_passed"] is True
                assert audit["derived_record_fidelity_passed"] is True
                assert audit["completed_rows"] == 1
            else:
                assert audit["status"] == "unavailable"
                assert audit["reason_code"] == (
                    "natural_branch_causal_identity_failed"
                )
                assert audit["causal_identity_passed"] is False
                assert audit["derived_record_fidelity_passed"] is True
                assert audit["first_failure"] is not None
                assert audit["completed_rows"] == 0
            assert audit["attempted_rows"] == 1

    def test_categorical_only_replay_accepts_empty_mark_support(self) -> None:
        report = _synthetic_replay_record()
        report["likelihood_components"]["mark_component"] = {
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
        support = {
            "event_rows_required": True,
            "categorical_rows_required": True,
            "mark_rows_required": False,
        }

        assert report["passed"] is True and report["failures"] == []
        assert event_held_commitment_link.validate_serialized_replay_report(
            report, **support,
        )
        assert event_held_commitment_link._validate_replay_report_evidence(
            report, **support,
        ) == (True, True, True)

        assert not event_held_commitment_link.validate_serialized_replay_report(
            report,
            event_rows_required=True,
            categorical_rows_required=True,
            mark_rows_required=True,
        )

        unsupported_payload = deepcopy(report)
        unsupported_payload["likelihood_components"]["mark_component"][
            "stored_value"
        ] = 1.0
        assert not event_held_commitment_link.validate_serialized_replay_report(
            unsupported_payload, **support,
        )

    def test_first_unavailable_stops_later_chunks(
        self, causal_audit_oracle_bundle: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch, device: torch.device,
    ) -> None:
        original = event_held_commitment_link._typed_natural_audit
        calls = 0

        def first_unavailable(*args: Any, **kwargs: Any) -> dict[str, Any]:
            nonlocal calls
            calls += 1
            audit = original(*args, **kwargs)
            return _structured_unavailable_audit(audit) if calls == 1 else audit

        monkeypatch.setattr(
            event_held_commitment_link,
            "_typed_natural_audit",
            first_unavailable,
        )
        results = audit_opportunities_batched(
            causal_audit_oracle_bundle["arm"],
            causal_audit_oracle_bundle["selected"],
            device=device,
        )
        assert len(results) == 1
        assert calls >= 1
        assert results[0]["natural_audit"]["status"] == "unavailable"
        telemetry = results[0]["telemetry"]
        assert telemetry["selected_state_count"] == 1
        assert (
            telemetry["physical_selected_state_count"]
            < len(causal_audit_oracle_bundle["selected"])
        )

    def test_quota_shortfall_is_invalid_before_artifact(
        self, causal_audit_oracle_bundle: dict[str, Any],
        device: torch.device,
    ) -> None:
        with pytest.raises(RuntimeError, match="INVALID_OPERATIONAL.*quota"):
            benchmark_runner._collect_causal_audit_evidence(
                causal_audit_oracle_bundle["arm"],
                replicate=0,
                batches=[],
                episode_rows=[],
                device=device,
                formal=False,
                mode="formal_path_exercise_evaluate",
            )

    def test_unavailable_analysis_bypasses_c_rows_and_selector(
        self, causal_audit_oracle_bundle: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        unavailable = _structured_unavailable_audit(
            _first_complete_natural_audit(causal_audit_oracle_bundle)
        )
        natural_evidence = {
            "schema": TYPED_CAUSAL_AUDIT_SCHEMA,
            "status": "unavailable",
            "reason_code": "natural_branch_causal_identity_failed",
            "replicate": 0,
            "attempted_rows": 1,
            "completed_rows": 0,
            "failed_selected_coordinate": [0, 0, 0, 0, 0, 0, 0, "KEEP"],
            "natural_rows": [{
                "natural_outcome": {"utility": 1.0},
                "natural_audit": unavailable,
            }],
        }
        compact = {
            "episodes": {},
            "audit_rows": {},
            "causal_audits": {0: natural_evidence},
            "evidence_status": "unavailable",
        }
        published: list[tuple[Path, dict[str, Any]]] = []
        monkeypatch.setattr(
            benchmark_runner, "_load_json_file",
            lambda _path: {"formal": True},
        )
        monkeypatch.setattr(
            benchmark_runner, "_write_json",
            lambda path, value: published.append((path, deepcopy(value))),
        )
        monkeypatch.setattr(
            benchmark_runner, "_validate_streamed_operational_records",
            lambda _root: (True, [], compact),
        )

        def forbidden_selector(**_kwargs: Any) -> str:
            raise AssertionError("unavailable evidence must bypass result selection")

        monkeypatch.setattr(
            benchmark_runner, "select_result_branch", forbidden_selector,
        )
        result = _aggregate_analysis_core(
            Path("unused"), authorization=FORMAL_AUTHORIZATION,
        )
        assert published == [(Path("unused/analysis_result.json"), result)]
        assert result["status"] == "COMPLETE_PARTIAL_EVIDENCE"
        assert result["branch"] == "FORK_EVIDENCE_UNAVAILABLE"
        assert result["artifact_schema"].endswith(".formal_analysis.v6")
        assert result["natural_evidence"] == [natural_evidence]
        encoded = json.dumps(result)
        assert '"predicate_inputs"' not in encoded
        assert '"diagnostics"' not in encoded
        assert '"c_total_' not in encoded
        assert '"causal_keep_rows_by_replicate"' not in encoded
        assert '"causal_renew_rows_by_replicate"' not in encoded



def test_cyclic_donors_preserve_float32_multisets_and_frozen_additivity(
    causal_audit_oracle_bundle: dict[str, Any],
) -> None:
    bundle = causal_audit_oracle_bundle
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in bundle["selected"]:
        grouped[row["natural_action"]].append(row)
        assert row["recipient_key"] != row["donor_key"]
    for action, rows in grouped.items():
        recipients = [bundle["inventory"][tuple(row["recipient_key"])] for row in rows]
        donors = [bundle["inventory"][tuple(row["donor_key"])] for row in rows]
        for field in ("candidate_u", "candidate_z"):
            assert sorted(value[field]["bytes_b64"] for value in recipients) == sorted(
                value[field]["bytes_b64"] for value in donors
            ), (action, field)
    for row, result in zip(bundle["selected"], bundle["batched"], strict=True):
        outcomes = {
            name: benchmark_runner._tracking_outcome_record(result["branch_outcomes"][name])
            for name in CAUSAL_AUDIT_BRANCHES
        }
        contrasts = benchmark_runner._causal_contrasts(row["natural_action"], outcomes)
        additivity = benchmark_runner._contrast_additivity_evidence(contrasts, outcomes)
        held, deranged, candidate = (
            outcomes[name]["utility"] for name in CAUSAL_AUDIT_BRANCHES
        )
        if row["natural_action"] == "KEEP":
            expected = (held - candidate, held - deranged, deranged - candidate)
        else:
            expected = (candidate - held, deranged - held, candidate - deranged)
        assert tuple(contrasts[name] for name in ("total", "timing", "mark")) == expected
        assert additivity == benchmark_runner._contrast_additivity_evidence(
            contrasts, outcomes
        )
        assert additivity["residual"] <= additivity["bound"]


def test_raw_pre_outcome_trace_is_minimal_and_origin_bound(
    causal_audit_oracle_bundle: dict[str, Any],
) -> None:
    allowed = {"coordinate", "natural_kind", "installed_z", "candidate_u",
               "candidate_z", "origin_binding"}
    all_keys = set()
    for batch_index, trajectory in enumerate(causal_audit_oracle_bundle["trajectories"]):
        for trace in trajectory.raw_event_trace:
            assert set(trace) == allowed
            assert not {"reward", "outcome", "utility", "terminal", "future"} & set(trace)
            for field in ("installed_z", "candidate_u", "candidate_z"):
                payload = trace[field]
                raw = base64.b64decode(payload["bytes_b64"], validate=True)
                assert payload["shape"] == [MARK_DIM] and payload["dtype"] == "float32"
                assert hashlib.sha256(raw).hexdigest() == payload["sha256"]
            origin = trace["origin_binding"]
            unsigned_row = deepcopy(trace)
            unsigned_row["origin_binding"] = {
                key: value for key, value in origin.items() if key != "binding_digest"
            }
            encoded = json.dumps(
                unsigned_row, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            ).encode("utf-8")
            assert origin["binding_digest"] == hashlib.sha256(
                b"HMASD_RAW_EVENT_TRACE_V1\0" + encoded
            ).hexdigest()
            all_keys.add(_trace_key(batch_index, trace))
    assert {tuple(row["recipient_key"]) for row in causal_audit_oracle_bundle["selected"]} <= all_keys


def test_no_active_legacy_or_scalar_audit_cuda_path() -> None:
    legacy_prefix, legacy_schema = "fork" + "_", "natural" + "_fork"
    production = [Path(event_held_commitment_link.__file__), Path(benchmark_runner.__file__),
                  Path(__file__).parents[1] / "ha_ctse_process" / "noncalendar_commitment_testbed.py"]
    for path in production:
        source = path.read_text(encoding="utf-8")
        # The frozen selection-stream namespace is preserved verbatim; it is
        # RNG identity, not a callable API or evidence schema.
        swept = source.replace('"' + legacy_schema + '_selection"', "")
        assert legacy_prefix not in swept, path
        assert legacy_schema not in swept, path
        assert "natural_errors" not in source, path
    assert "audit_single_opportunity(" not in Path(benchmark_runner.__file__).read_text(encoding="utf-8")
    import ast
    tree = ast.parse(Path(event_held_commitment_link.__file__).read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "audit_opportunities_batched")
    assert all(
        not (
            isinstance(node, ast.Constant)
            and node.value in {"natural_errors", "continuous_error"}
        )
        for node in ast.walk(function)
    )
    for loop in (node for node in ast.walk(function) if isinstance(node, (ast.For, ast.While))):
        for call in (node for node in ast.walk(loop) if isinstance(node, ast.Call)):
            if isinstance(call.func, ast.Attribute):
                assert call.func.attr not in {"item", "numpy"}, ast.unparse(call)

def test_candidate_retention_preserves_mark_rng_stream_position(
    device: torch.device,
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

    arms, _, _ = initialize_arms(device)
    arm = arms["EHC"]
    state_left = make_training_state("EHC", 0)
    state_right = make_training_state("EHC", 0)
    left = collect_trajectory(
        arm, state_left, device=device, episode_ids=tuple(range(16))
    )
    right = collect_trajectory(
        arm, state_right, device=device, episode_ids=tuple(range(16))
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


# float32 reduction order is device-dependent, so the protected collector
# outputs have one digest per registered backend rather than one digest. Both
# were measured at `torch.set_num_threads(1)`; the CUDA pair is bit-for-bit the
# pair pinned before CPU was admitted, which is direct evidence that the thread
# pin does not perturb a CUDA collection.
PINNED_COLLECTOR_DIGESTS = {
    "cuda": (
        "891f0914729c09633a57c3557a36b9066b66c4cbffdbee299783a25bc551d047",
        "3376441c78954199d112ab9b591e0b29464c2842dcb706ccfd8d88c718eae639",
    ),
    "cpu": (
        "59752b3f61f2a80a5e1def2c586832d295b471947c64bdfd63ff8e7544146268",
        "185453bc48be61a775332bb1a29e6d3d5692945db19c47d46fee405ae03faaf9",
    ),
}


def test_collector_protected_outputs_pinned_digest(
    device: torch.device,
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

    Reproducibility was verified before pinning, not assumed. For each
    registered backend the SHA256 digest of both tensors was observed
    bit-for-bit identical across 3 collections within one process AND
    across 2 separate process invocations of the same probe script (6
    observations per backend on this machine, zero variation). Because
    bitwise-exact reproduction held in every observation, this pins an
    exact digest rather than falling back to a numeric summary at
    tolerance.

    Both backends are pinned so the guard survives a change of registered
    backend, but only the entry for the backend this session activated is
    exercised: one process activates exactly one backend by construction,
    so the other entry is carried, not checked, here.
    """

    backend = active_execution_backend()
    assert set(PINNED_COLLECTOR_DIGESTS) == set(REGISTERED_EXECUTION_BACKENDS)
    expected_event_z, expected_primitive_z = PINNED_COLLECTOR_DIGESTS[backend]
    arms, _, _ = initialize_arms(device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(
        arm, state, device=device, episode_ids=tuple(range(16))
    )
    assert _tensor_sha256(trajectory.event_new_z) == expected_event_z
    assert _tensor_sha256(trajectory.primitive_z) == expected_primitive_z
    # The two backends genuinely disagree, which is why one digest could not
    # serve both: this asserts the pin is backend-specific rather than an
    # accidental duplicate.
    assert len({tuple(value) for value in PINNED_COLLECTOR_DIGESTS.values()}) == 2


def test_checkpoint_strict_continuation_and_registered_backend_smoke(
    device: torch.device, tmp_path,
) -> None:
    arms, base_optimizers, event_optimizers = initialize_arms(device)
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(
        arms["EHC"], state, device=device, episode_ids=(0,)
    )
    update = optimize_update(
        arms["EHC"], base_optimizers["EHC"], event_optimizers["EHC"],
        state, trajectory, device=device,
    )
    assert update["primitive_replays"] == 4
    assert update["event_head_replays"] == 4
    assert update["packed_trajectory_count"] == 1
    expected_manifest = benchmark_runner._expected_optimizer_manifest("EHC")
    assert update["ownership_manifest"] == expected_manifest
    for group in ("base", "event"):
        for index, record in enumerate(update[f"{group}_passes"]):
            valid, summary = benchmark_runner._optimizer_pass_valid(
                record, group=group, pass_index=index + 1,
                step_before=index,
                manifest=expected_manifest["groups"][group],
            )
            assert valid, (group, index, record)
            assert summary["nonfinite_values"] == 0
    checkpoint = tmp_path / "origin.pt"
    save_checkpoint(
        checkpoint, arm=arms["EHC"], base_optimizer=base_optimizers["EHC"],
        event_optimizer=event_optimizers["EHC"], state=state,
    )
    with pytest.raises(ValueError, match="arm/replicate"):
        load_checkpoint(
            checkpoint, device=device,
            expected_arm="DUM", expected_replicate=0,
        )
    with pytest.raises(ValueError, match="arm/replicate"):
        load_checkpoint(
            checkpoint, device=device,
            expected_arm="EHC", expected_replicate=1,
        )
    with pytest.raises(ValueError, match="update-250"):
        load_checkpoint(
            checkpoint, device=device,
            expected_arm="EHC", expected_replicate=0,
            formal_evaluation=True,
        )
    corrupt_payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    corrupt_payload["owned_rngs"].pop("mark")
    corrupt_path = tmp_path / "corrupt_rng.pt"
    torch.save(corrupt_payload, corrupt_path)
    with pytest.raises(ValueError, match="owned-RNG"):
        load_checkpoint(
            corrupt_path, device=device,
            expected_arm="EHC", expected_replicate=0,
        )

    left_arm, left_base, left_event, left_state = load_checkpoint(
        checkpoint, device=device,
        expected_arm="EHC", expected_replicate=0,
    )
    left_trajectory = collect_trajectory(
        left_arm, left_state, device=device, episode_ids=(1,)
    )
    optimize_update(
        left_arm, left_base, left_event, left_state,
        left_trajectory, device=device,
    )
    left_global = runtime_rng_snapshot()
    right_arm, right_base, right_event, right_state = load_checkpoint(
        checkpoint, device=device,
        expected_arm="EHC", expected_replicate=0,
    )
    right_trajectory = collect_trajectory(
        right_arm, right_state, device=device, episode_ids=(1,)
    )
    optimize_update(
        right_arm, right_base, right_event, right_state,
        right_trajectory, device=device,
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

    smoke = run_smoke(tmp_path / "smoke", device_name=device.type)
    assert smoke["device"] == device.type and smoke["formal"] is False
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

    def worst(dimensions: int) -> dict[str, object]:
        stored = np.float32(0.0)
        neighbor = np.nextafter(stored, np.float32(np.inf), dtype=np.float32)
        return {
            "stored_value": 0.0,
            "replayed_value": 0.0,
            "absolute_error": 0.0,
            "mixed_bound": REPLAY_LOG_COMPONENT_ATOL,
            "ratio_drift": 0.0,
            "ratio_cap": REPLAY_LOG_RATIO_DRIFT_CAP,
            "float32_ulp_at_max_magnitude": float(neighbor),
            "ulp_distance": 0,
            "coordinate": [0] * dimensions,
        }

    return {
        "schema_version": REPLAY_RECORD_SCHEMA_VERSION,
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
        "likelihood_components": {
            "primitive_component": worst(3),
            "categorical_component": worst(3),
            "mark_component": worst(4),
        },
        "event_joint_ratio": {
            "stored_value": 0.0,
            "replayed_value": 0.0,
            "ratio_drift": 0.0,
            "ratio_cap": REPLAY_LOG_RATIO_DRIFT_CAP,
            "coordinate": [0, 0, 0],
        },
        "log_component_atol": REPLAY_LOG_COMPONENT_ATOL,
        "log_component_rtol": REPLAY_LOG_COMPONENT_RTOL,
        "ratio_drift_cap": REPLAY_LOG_RATIO_DRIFT_CAP,
        "state_atol": REPLAY_STATE_ATOL,
        "failures": [],
        "passed": True,
    }


@functools.lru_cache(maxsize=1)
def _synthetic_operational_records(
    training_updates: int = benchmark_runner.FORMAL_UPDATES,
) -> tuple[
    dict[str, object], dict[tuple[int, str, str], dict[str, object]]
]:
    contract = registered_contract()
    arms: dict[str, dict[str, object]] = {}
    for arm in ARMS:
        checkpoint = f"replicate_0/{arm}/update_250.pt"
        arms[arm] = {
            "arm": arm,
            "replicate": 0,
            "checkpoint": checkpoint,
            "checkpoint_origin": "update_250.pt",
            "completed_update": 250,
            "next_episode_id": 4000,
            "exposure": {"base": 1000, "event": 0 if arm == "OR" else 1000},
            "seed_map": authoritative_seed_map("train", 0),
            "parameter_counts": benchmark_runner._expected_parameter_counts(arm),
            "restore_metrics": _zero_restore_metrics(),
            "checkpoint_sha256": "0" * 64,
        }
    replay = _synthetic_replay_record()
    lifecycle = {
        "create": 1, "keep": 1, "renew": 1,
        "categorical": 2, "mark": 2,
        "invalid_segment_lifetimes": 0, "segment_count": 2,
    }
    finite = {
        name: 0 for name in (
            "old_log_probs", "old_values", "hidden_after", "prefix_counts",
            "event_inputs", "event_old_cat_logp",
            "event_old_mark_component_logp", "event_old_joint_logp",
        )
    }
    ledger_audit_cache: dict[
        tuple[str, int, int, tuple[int, ...]],
        tuple[list[Any], dict[str, list[dict[str, Any]]]],
    ] = {}
    schedule_evidence_cache: dict[
        tuple[Any, ...],
        tuple[dict[str, list[dict[str, Any]]], dict[str, Any]],
    ] = {}
    def schedules_for(
        counts: dict[str, int], *, arm: str, profile: str,
        seed_map: dict[str, int], deterministic: bool,
        episode_ids: list[int], start_time: int = 0,
    ) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
        schedule_key = (
            arm == "OR", profile, bool(deterministic), tuple(episode_ids),
            int(start_time), tuple(sorted(counts.items())),
        )
        if schedule_key in schedule_evidence_cache:
            return schedule_evidence_cache[schedule_key]
        cache_key = (
            profile, int(seed_map["ledger"]), int(seed_map["order"]),
            tuple(episode_ids),
        )
        if cache_key not in ledger_audit_cache:
            ledger_trace = {name: [] for name in RNG_NAMES}
            ledgers = [
                make_noncalendar_ledger(
                    episode_id, profile=profile, task_seed=seed_map["ledger"],
                    order_seed=seed_map["order"], audit_trace=ledger_trace,
                )
                for episode_id in episode_ids
            ]
            ledger_audit_cache[cache_key] = (ledgers, ledger_trace)
        ledgers, ledger_trace = ledger_audit_cache[cache_key]
        schedules = deepcopy(ledger_trace)
        request_count = sum(counts[name] for name in ("create", "keep", "renew"))
        request_rows: list[list[int]] = []
        request_evidence = []
        for time in range(HORIZON):
            environments = []
            for env_index, (episode_id, ledger) in enumerate(
                zip(episode_ids, ledgers, strict=True)
            ):
                frontier = []
                if arm != "OR" and time == start_time and env_index == 0:
                    keys = sorted(
                        range(MAX_LIFECYCLES),
                        key=lambda key: float(
                            ledger.direct_frontier_priorities[time, key]
                        ),
                    )[:request_count]
                    for request_index, key in enumerate(keys):
                        q_before = -1 if request_index == 0 else 0
                        request_kind = CREATE if q_before < 0 else KEEP
                        frontier.append({
                            "key": key,
                            "priority": float(
                                ledger.direct_frontier_priorities[time, key]
                            ),
                            "q_before": q_before,
                        })
                        request_rows.append([env_index, key, request_kind])
                environments.append({
                    "env_index": env_index, "episode_id": episode_id,
                    "frontier": frontier,
                })
            request_evidence.append({"time": time, "environments": environments})
        coordinates = {
            "time": start_time,
            "requests": request_rows,
        }
        if request_count:
            schedules["opportunity"] = [{
                "stream": "opportunity",
                "operation": "choice_opportunity", "dtype": "int64",
                "shape": [request_count], "coordinates": coordinates,
            }]
            if not deterministic:
                schedules["event"] = [{
                    "stream": "event",
                    "operation": "random", "dtype": "float64",
                    "shape": [request_count], "coordinates": coordinates,
                }]
                schedules["mark"] = [{
                    "stream": "mark",
                    "operation": "standard_normal", "dtype": "float64",
                    "shape": [request_count, MARK_DIM], "coordinates": coordinates,
                }]
        if not deterministic:
            schedules["primitive"] = [
                {
                    "stream": "primitive",
                    "operation": "random", "dtype": "float32",
                    "shape": [16, MAX_LIFECYCLES],
                    "coordinates": {
                        "time": time, "episode_ids": episode_ids,
                        "frontier_orders": [
                            [value["key"] for value in environment["frontier"]]
                            for environment in request_evidence[time]["environments"]
                        ],
                    },
                }
                for time in range(HORIZON)
            ]
        result = schedules, {
            "streams": schedules,
            "request_evidence": request_evidence,
            "ledgers": [benchmark_runner._ledger_record(ledger) for ledger in ledgers],
        }
        schedule_evidence_cache[schedule_key] = result
        return result

    def binding_family(
        context: dict[str, Any], seed_map: dict[str, int],
        starts: dict[str, Any], schedules: dict[str, list[dict[str, Any]]],
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
        ends = {
            name: event_held_commitment_link.replay_rng_schedule_end_state(
                starts[name], schedules[name], seed=seed_map[name]
            )
            for name in RNG_NAMES
        }
        bindings = {}
        for name in RNG_NAMES:
            binding = event_held_commitment_link.make_rng_binding(
                context=context, stream=name, seed=seed_map[name],
                start_state=starts[name], draw_schedule=schedules[name],
                expected_end_state=ends[name],
            )
            binding["draw_schedule"] = schedules[name]
            binding["binding_digest"] = _digest_json({
                key: value for key, value in binding.items()
                if key != "binding_digest"
            })
            bindings[name] = binding
        return bindings, ends, {
            name: _digest_json(ends[name]) for name in RNG_NAMES
        }

    optimizer_parameters_cache: dict[
        tuple[str, str], list[dict[str, Any]]
    ] = {}
    def optimizer_pass(
        arm: str, group: str, pass_index: int, step_before: int,
    ) -> dict[str, Any]:
        manifest = benchmark_runner._expected_optimizer_manifest(arm)["groups"][group]
        cache_key = (arm, group)
        if cache_key not in optimizer_parameters_cache:
            parameters = []
            for owner in manifest:
                all_zero = arm == "DUM" and owner["name"] == "W_z.weight"
                array = np.zeros(tuple(owner["shape"]), dtype="<f4")
                if not all_zero:
                    array.reshape(-1)[0] = 1.0
                raw = array.tobytes(order="C")
                encoded = base64.b64encode(
                    zlib.compress(raw, level=9)
                ).decode("ascii")
                parameters.append({
                    **owner,
                    "dtype": "<f4",
                    "gradient_present": True,
                    "nonfinite_count": 0,
                    "zero_count": (
                        owner["numel"] if all_zero else owner["numel"] - 1
                    ),
                    "squared_l2": 0.0 if all_zero else 1.0,
                    "maxabs": 0.0 if all_zero else 1.0,
                    "preclip_gradient_digest": hashlib.sha256(raw).hexdigest(),
                    "gradient_payload": {
                        "encoding": "zlib9_base64", "dtype": "<f4",
                        "shape": list(owner["shape"]),
                        "uncompressed_nbytes": len(raw), "data": encoded,
                    },
                })
            optimizer_parameters_cache[cache_key] = parameters
        parameters = optimizer_parameters_cache[cache_key]
        norm = math.sqrt(sum(float(value["squared_l2"]) for value in parameters))
        components = (
            {"policy_loss": 0.0, "value_loss": 0.0, "primitive_entropy": 0.0}
            if group == "base" else
            {"event_policy_loss": 0.0, "categorical_entropy": 0.0}
        )
        unsigned = {
            "schema_version": benchmark_runner.OPTIMIZER_EVIDENCE_SCHEMA_VERSION,
            "group": group, "pass_index": pass_index,
            "step_before": step_before, "step_after": step_before + 1,
            "raw_loss": 0.0, "loss_components": components,
            "unclipped_norm": norm,
            "clip_coefficient": min(1.0, 0.5 / (norm + 1e-6)),
            "parameters": parameters,
            "payload_raw_bytes": sum(
                value["gradient_payload"]["uncompressed_nbytes"]
                for value in parameters
            ),
            "payload_encoded_bytes": sum(
                len(value["gradient_payload"]["data"].encode("ascii"))
                for value in parameters
            ),
        }
        return unsigned | {"record_digest": _digest_json(unsigned)}
    pair_tensor = {
        "left_digest": "a", "right_digest": "a",
        "mismatch_count": 0, "maximum_absolute_error": 0.0,
    }
    updates = []
    train_rng_states = {
        arm: benchmark_runner._initial_rng_states(
            authoritative_seed_map("train", 0)
        )
        for arm in ARMS
    }
    for update in range(1, int(training_updates) + 1):
        arm_evidence = {}
        for arm in ARMS:
            event_steps = 0 if arm == "OR" else 4
            arm_lifecycle = ({name: 0 for name in lifecycle} if arm == "OR" else dict(lifecycle))
            train_seed_map = authoritative_seed_map("train", 0)
            schedules, rng_evidence = schedules_for(
                arm_lifecycle, arm=arm, profile="train",
                seed_map=train_seed_map, deterministic=False,
                episode_ids=list(range(
                    (update - 1) * 16, update * 16
                )),
            )
            bindings, train_rng_states[arm], owned_digests = binding_family(
                {
                    "domain": "training", "mode": "formal_train",
                    "formal": True, "replicate": 0, "arm": arm,
                    "update": update,
                },
                train_seed_map, train_rng_states[arm], schedules,
            )
            manifest = benchmark_runner._expected_optimizer_manifest(arm)
            base_passes = [
                optimizer_pass(arm, "base", index + 1, 4 * (update - 1) + index)
                for index in range(4)
            ]
            event_passes = [
                optimizer_pass(arm, "event", index + 1, 4 * (update - 1) + index)
                for index in range(event_steps)
            ]
            arm_evidence[arm] = {
                "arm": arm,
                "seed_map": authoritative_seed_map("train", 0),
                "owned_stream_digests": owned_digests,
                "rng_bindings": bindings,
                "rng_evidence": rng_evidence,
                "replay": deepcopy(replay),
                "lifecycle_counts": arm_lifecycle,
                "finite_checks": dict(finite),
                "exposure": {
                    "before": {"base": 4 * (update - 1), "event": event_steps * (update - 1)},
                    "delta": {"base": 4, "event": event_steps},
                    "after": {"base": 4 * update, "event": event_steps * update},
                },
                "optimizer": {
                    "base_steps": 4, "event_steps": event_steps,
                    "primitive_replays": 4, "event_head_replays": event_steps,
                    "packed_trajectory_count": 1,
                    "base_non_none_gradients": [18 if arm == "OR" else 19] * 4,
                    "base_zero_gradients": [1 if arm == "DUM" else 0] * 4,
                    "base_nonfinite_gradient_values": [0] * 4,
                    "base_nonfinite_loss_values": [0] * 4,
                    "base_nonfinite_norm_values": [0] * 4,
                    "event_non_none_gradients": [4] * event_steps,
                    "event_zero_gradients": [0] * event_steps,
                    "event_nonfinite_gradient_values": [0] * event_steps,
                    "event_nonfinite_loss_values": [0] * event_steps,
                    "event_nonfinite_norm_values": [0] * event_steps,
                    "ownership_manifest": manifest,
                    "base_passes": base_passes,
                    "event_passes": event_passes,
                    "evidence_storage": {
                        "raw_bytes": sum(
                            value["payload_raw_bytes"]
                            for value in base_passes + event_passes
                        ),
                        "encoded_bytes": sum(
                            value["payload_encoded_bytes"]
                            for value in base_passes + event_passes
                        ),
                        "formal_scale_projected_encoded_bytes": sum(
                            value["payload_encoded_bytes"]
                            for value in base_passes + event_passes
                        ) * benchmark_runner.FORMAL_UPDATES,
                    },
                },
                "parameter_counts": benchmark_runner._expected_parameter_counts(arm),
            }
        updates.append({
            "update": update,
            "arms": arm_evidence,
            "paired": {
                "or_dum_tensors": {
                    name: dict(pair_tensor) for name in (
                        "observations", "active_mask", "orders", "actions",
                        "old_log_probs", "old_values", "hidden_before",
                        "hidden_after", "prefix_counts", "rewards", "terminal",
                    )
                },
                "or_dum_rng": {
                    name: {
                        "left": arm_evidence["OR"]["owned_stream_digests"][name],
                        "right": arm_evidence["DUM"]["owned_stream_digests"][name],
                    }
                    for name in ("ledger", "order", "primitive")
                },
                "dum_ehc_rng": {
                    name: {
                        "left": arm_evidence["DUM"]["owned_stream_digests"][name],
                        "right": arm_evidence["EHC"]["owned_stream_digests"][name],
                    }
                    for name in RNG_NAMES
                },
                "base_noop_error": 0.0,
            },
        })
    training = {
        "artifact_schema": FORMAL_TRAIN_ARTIFACT_SCHEMA,
        "schema_version": TRAIN_MANIFEST_SCHEMA,
        "formal": True,
        "contract": contract,
        "mode": "formal_train",
        "status": "COMPLETE",
        "branch": "FORMAL_TRAIN_COMPLETE",
        "replicates": {
            "0": {
                "operational": True,
                "updates": updates,
                "arms": arms,
            }
        },
    }
    cells = {}
    episodes = [
        {
            "episode_id": value, "utility": 0.0, "keep": 0, "renew": 0,
            "non_create": 0, "multi_opportunity_lifecycles": 0,
            "segments": [], "intervention": [],
            "outcome": {
                "tracking": 0.0, "completion": 0.0, "utility": 0.0,
                "terminal_reward": 0.0, "tracking_quarter_units": 0,
                "active_rows": 1, "completed_segments": 0,
                "eligible_segments": 1,
                "roster_sizes": [1] + [0] * (HORIZON - 1),
                "reward_trace": [0.0] * HORIZON,
            },
        }
        for value in range(256)
    ]
    for arm in ARMS:
        for profile, deterministic, cell in EVALUATION_CELLS:
            arm_lifecycle = ({name: 0 for name in lifecycle} if arm == "OR" else dict(lifecycle))
            eval_rng_states = benchmark_runner._initial_rng_states(
                authoritative_seed_map(profile, 0)
            )
            batch_records = []
            for batch in range(16):
                eval_seed_map = authoritative_seed_map(profile, 0)
                schedules, rng_evidence = schedules_for(
                    arm_lifecycle, arm=arm, profile=profile,
                    seed_map=eval_seed_map, deterministic=deterministic,
                    episode_ids=list(range(batch * 16, (batch + 1) * 16)),
                )
                bindings, eval_rng_states, owned_digests = binding_family(
                    {
                        "domain": "evaluation", "mode": "formal_evaluate",
                        "formal": True, "replicate": 0, "arm": arm,
                        "cell": cell, "batch": batch,
                    },
                    eval_seed_map, eval_rng_states, schedules,
                )
                batch_records.append({
                    "batch_index": batch,
                    "episode_ids": list(range(batch * 16, (batch + 1) * 16)),
                    "replay": deepcopy(replay),
                    "lifecycle_counts": dict(arm_lifecycle),
                    "finite_checks": dict(finite),
                    "seed_map": authoritative_seed_map(profile, 0),
                    "owned_stream_digests": owned_digests,
                    "rng_bindings": bindings,
                    "rng_evidence": rng_evidence,
                    "reduction_counts": {
                        "keep": 0, "renew": 0, "non_create": 0,
                        "multi_opportunity_lifecycles": 0,
                        "intervention_values": 0,
                    },
                    "checkpoint_origin": "update_250.pt",
                    "episodes_digest": _digest_json(
                        episodes[batch * 16:(batch + 1) * 16]
                    ),
                    "raw_event_trace_binding": {
                        "row_count": 0, "trace_sha256": _digest_json([]),
                    },
                })
            cells[(0, arm, cell)] = {
                "artifact_schema": FORMAL_EVALUATION_ARTIFACT_SCHEMA,
                "schema_version": EVALUATION_CELL_SCHEMA,
                "formal": True,
                "contract": contract,
                "arm": arm,
                "replicate": 0,
                "cell": cell,
                "profile": profile,
                "mode": "deterministic" if deterministic else "stochastic",
                "checkpoint": arms[arm]["checkpoint"],
                "checkpoint_origin": "update_250.pt",
                "counts": {"episodes": 256, "horizon": 80, "batch_size": 16, "batches": 16},
                "batches": batch_records,
                "causal_audit": None,
                "operational": True,
                "episodes": deepcopy(episodes),
                "status": "COMPLETE",
            }
    return training, cells


def test_fail_closed_operational_manifest_negatives() -> None:
    training, cells = _synthetic_operational_records()
    clean_cell = cells[(0, "EHC", "iid_deterministic")]
    valid, _episode_ids, _rng_digests = benchmark_runner._evaluation_cell_valid(
        clean_cell, replicate=0, arm="EHC", profile="iid",
        deterministic=True, cell="iid_deterministic", formal=True,
        mode="formal_evaluate", episodes_per_cell=256,
        checkpoint_origin="update_250.pt",
        checkpoint_path=training["replicates"]["0"]["arms"]["EHC"]["checkpoint"],
        ledger_cache={},
    )
    assert valid
    for key in ("schema_version", "replicate"):
        original = clean_cell[key]
        for replacement in (True, float(original), str(original)):
            mutated = deepcopy(clean_cell)
            mutated[key] = replacement
            assert not benchmark_runner._evaluation_cell_valid(
                mutated, replicate=0, arm="EHC", profile="iid",
                deterministic=True, cell="iid_deterministic", formal=True,
                mode="formal_evaluate", episodes_per_cell=256,
                checkpoint_origin="update_250.pt",
                checkpoint_path=training["replicates"]["0"]["arms"]["EHC"]["checkpoint"],
                ledger_cache={},
            )[0], (key, replacement)
    for key in ("episodes", "horizon", "batch_size", "batches"):
        original = clean_cell["counts"][key]
        for replacement in (True, float(original), str(original)):
            mutated = deepcopy(clean_cell)
            mutated["counts"][key] = replacement
            assert not benchmark_runner._evaluation_cell_valid(
                mutated, replicate=0, arm="EHC", profile="iid",
                deterministic=True, cell="iid_deterministic", formal=True,
                mode="formal_evaluate", episodes_per_cell=256,
                checkpoint_origin="update_250.pt",
                checkpoint_path=training["replicates"]["0"]["arms"]["EHC"]["checkpoint"],
                ledger_cache={},
            )[0], (key, replacement)
    for replacement in (True, 0.0, "0"):
        mutated = deepcopy(clean_cell)
        mutated["batches"][0]["batch_index"] = replacement
        assert not benchmark_runner._evaluation_cell_valid(
            mutated, replicate=0, arm="EHC", profile="iid",
            deterministic=True, cell="iid_deterministic", formal=True,
            mode="formal_evaluate", episodes_per_cell=256,
            checkpoint_origin="update_250.pt",
            checkpoint_path=training["replicates"]["0"]["arms"]["EHC"]["checkpoint"],
            ledger_cache={},
        )[0], ("batch_index", replacement)
    for replacement in (True, 0.0, "0"):
        mutated = deepcopy(clean_cell)
        mutated["episodes"][0]["episode_id"] = replacement
        mutated["batches"][0]["episode_ids"][0] = replacement
        mutated["batches"][0]["episodes_digest"] = _digest_json(
            mutated["episodes"][:16]
        )
        assert not benchmark_runner._evaluation_cell_valid(
            mutated, replicate=0, arm="EHC", profile="iid",
            deterministic=True, cell="iid_deterministic", formal=True,
            mode="formal_evaluate", episodes_per_cell=256,
            checkpoint_origin="update_250.pt",
            checkpoint_path=training["replicates"]["0"]["arms"]["EHC"]["checkpoint"],
            ledger_cache={},
        )[0], ("episode_id_rehashed", replacement)
    update_record = deepcopy(training["replicates"]["0"]["updates"][0])
    for replacement in (True, 1.0, "1"):
        mutated = deepcopy(update_record)
        mutated["update"] = replacement
        assert not _training_update_valid(mutated, update=1, replicate=0)
    corrupted_cell = clean_cell | {"profile": "held_out"}
    assert not benchmark_runner._evaluation_cell_valid(
        corrupted_cell, replicate=0, arm="EHC", profile="iid",
        deterministic=True, cell="iid_deterministic", formal=True,
        mode="formal_evaluate", episodes_per_cell=256,
        checkpoint_origin="update_250.pt",
        checkpoint_path=training["replicates"]["0"]["arms"]["EHC"]["checkpoint"],
        ledger_cache={},
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
            "likelihood_components": record["likelihood_components"] | {
                "mark_component": record["likelihood_components"]["mark_component"]
                | {"replayed_value": 2e-6, "absolute_error": 2e-6,
                   "ratio_drift": math.expm1(2e-6)}
            }
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
        ("wrong_tolerance", lambda record: record | {"log_component_rtol": 1e-5}),
    ):
        degraded = mutation(deepcopy(
            cells[(0, "EHC", "iid_stochastic")]["batches"][0]["replay"]
        ))
        assert not _replay_record_valid(degraded), label
    for family, mutation in (
        ("no_op", lambda value: value["replicates"]["0"]["updates"][0]["paired"].__setitem__("base_noop_error", 1.0)),
        ("exposure", lambda value: value["replicates"]["0"]["arms"]["EHC"]["exposure"].__setitem__("base", 999)),
        ("resume", lambda value: value["replicates"]["0"]["arms"]["EHC"]["restore_metrics"]["continuous"].__setitem__("model", 1.0)),
    ):
        if family == "no_op":
            update = deepcopy(training["replicates"]["0"]["updates"][0])
            wrapper = {"replicates": {"0": {"updates": [update]}}}
            mutation(wrapper)
            operational_valid = _training_update_valid(
                update, update=1, replicate=0
            )
        else:
            arm_entry = deepcopy(training["replicates"]["0"]["arms"]["EHC"])
            wrapper = {"replicates": {"0": {"arms": {"EHC": arm_entry}}}}
            mutation(wrapper)
            operational_valid = (
                arm_entry["exposure"] == {"base": 1000, "event": 1000}
                and benchmark_runner._restore_metrics_valid(
                    arm_entry["restore_metrics"]
                )
            )
        assert not operational_valid, family
        assert select_result_branch(
            **(_branch_inputs() | {"operational_valid": operational_valid})
        ) == "INVALID_OPERATIONAL"


def test_atomic_publication_and_operational_failure_cleanup(
    device: torch.device, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    json_path = tmp_path / "atomic.json"
    pristine_replace = benchmark_runner.os.replace
    monkeypatch.setattr(
        benchmark_runner.os,
        "replace",
        lambda _source, _target: (_ for _ in ()).throw(OSError("json publish")),
    )
    with pytest.raises(OSError, match="json publish"):
        _write_json(json_path, {"complete": True})
    assert not json_path.exists()
    assert not list(tmp_path.glob(".atomic.json.*.tmp"))
    monkeypatch.setattr(benchmark_runner.os, "replace", pristine_replace)

    arms, base_optimizers, event_optimizers = initialize_arms(device)
    checkpoint = tmp_path / "atomic.pt"
    pristine_checkpoint_replace = event_held_commitment_link.os.replace
    monkeypatch.setattr(
        event_held_commitment_link.os,
        "replace",
        lambda _source, _target: (_ for _ in ()).throw(OSError("checkpoint publish")),
    )
    with pytest.raises(OSError, match="checkpoint publish"):
        save_checkpoint(
            checkpoint,
            arm=arms["EHC"],
            base_optimizer=base_optimizers["EHC"],
            event_optimizer=event_optimizers["EHC"],
            state=make_training_state("EHC", 0),
        )
    assert not checkpoint.exists()
    assert not list(tmp_path.glob(".atomic.pt.*.tmp"))
    monkeypatch.setattr(
        event_held_commitment_link.os, "replace", pristine_checkpoint_replace
    )

    monkeypatch.setattr(
        benchmark_runner,
        "_training_core",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("injected")),
    )
    with pytest.raises(RuntimeError, match="injected"):
        formal_path_exercise(tmp_path / "exercise", device_name=device.type)
    exercise_root = tmp_path / "exercise" / "formal_path_exercise"
    terminal = json.loads((exercise_root / "manifest.json").read_text())
    assert terminal["formal"] is False
    assert terminal["status"] == terminal["branch"] == "INVALID_OPERATIONAL"
    failure_path, failure = benchmark_runner._verified_json_reference(
        exercise_root, terminal["failure_artifact"],
        identity_keys=frozenset({"artifact"}),
    )
    assert failure_path.is_file()
    assert failure["exception_type"] == "RuntimeError"
    assert failure["last_complete_evidence"] == {}


def test_direct_atomic_json_streaming_and_incremental_reference_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = {
        "nested": [{"array": np.arange(8, dtype=np.int64)}],
        "tensor": torch.arange(4, dtype=torch.float32),
    }
    observed: list[bool] = []
    pristine_dump = benchmark_runner.json.dump

    def observing_dump(value: Any, *args: Any, **kwargs: Any) -> Any:
        observed.append(value is source)
        return pristine_dump(value, *args, **kwargs)

    monkeypatch.setattr(benchmark_runner.json, "dump", observing_dump)
    direct_path = tmp_path / "direct.json"
    _write_json(direct_path, source)
    assert observed == [True]
    with direct_path.open("r", encoding="utf-8") as handle:
        assert json.load(handle) == {
            "nested": [{"array": list(range(8))}],
            "tensor": [0.0, 1.0, 2.0, 3.0],
        }
    assert "_json_ready" not in benchmark_runner.__dict__

    train_root = {
        "identity": "synthetic_streaming", "status": "IN_PROGRESS",
        "progress": {"completed_updates": 0, "total_updates": 2},
        "replicate_indexes": [],
    }
    train_root_path = tmp_path / "train_manifest.json"
    indexes_path = tmp_path / "train" / "replicate_0" / "indexes"
    evidence_path = tmp_path / "train" / "replicate_0" / "evidence"
    index = {
        "replicate": 0, "generation": 0, "updates": [],
        "progress": {"completed_updates": 0, "total_updates": 2},
    }
    snapshots = []
    generation_bytes: list[bytes] = []
    for update in (1, 2):
        shard_path = evidence_path / f"update_{update}.json"
        _write_json(shard_path, {"update": update, "verbose": [update] * 32})
        index["updates"].append(
            benchmark_runner._artifact_reference(
                tmp_path, shard_path, update=update,
            )
        )
        index["progress"]["completed_updates"] = update
        index["generation"] = update
        index_path = indexes_path / f"index_{update}.json"
        _write_json(index_path, index)
        generation_bytes.append(index_path.read_bytes())
        train_root["replicate_indexes"] = [
            benchmark_runner._artifact_reference(
                tmp_path, index_path, replicate=0, generation=update,
            )
        ]
        train_root["progress"]["completed_updates"] = update
        _write_json(train_root_path, train_root)
        with train_root_path.open("r", encoding="utf-8") as handle:
            snapshots.append(json.load(handle))
    assert [value["progress"]["completed_updates"] for value in snapshots] == [1, 2]
    assert all("updates" not in value and "evidence" not in value for value in snapshots)
    assert [value["update"] for value in index["updates"]] == [1, 2]
    assert (indexes_path / "index_1.json").read_bytes() == generation_bytes[0]
    assert not (indexes_path.parent / "index.json").exists()

    # Publishing the next immutable generation without the root swap leaves
    # the prior root/index authoritative and byte-identical.
    orphan = deepcopy(index)
    orphan["generation"] = 3
    orphan_path = indexes_path / "index_3.json"
    before_interrupted_swap = train_root_path.read_bytes()
    proposed_root = deepcopy(train_root)
    pristine_write = benchmark_runner._write_json

    def interrupt_root_swap(path: Path, value: Any) -> None:
        if path == train_root_path:
            raise RuntimeError("injected after generation before root swap")
        pristine_write(path, value)

    monkeypatch.setattr(
        benchmark_runner, "_write_json", interrupt_root_swap,
    )
    with pytest.raises(RuntimeError, match="before root swap"):
        benchmark_runner._write_json(orphan_path, orphan)
        proposed_root["replicate_indexes"] = [
            benchmark_runner._artifact_reference(
                tmp_path, orphan_path, replicate=0, generation=3,
            )
        ]
        benchmark_runner._write_json(train_root_path, proposed_root)
    monkeypatch.setattr(benchmark_runner, "_write_json", pristine_write)
    assert train_root_path.read_bytes() == before_interrupted_swap
    authoritative = json.loads(train_root_path.read_text(encoding="utf-8"))
    assert authoritative["replicate_indexes"][0]["generation"] == 2
    assert authoritative["replicate_indexes"][0]["path"].endswith(
        "indexes/index_2.json"
    )
    assert orphan_path.as_posix() not in json.dumps(authoritative)

    evaluation_root = {"progress": {"completed_cells": 0, "total_cells": 2}, "cells": []}
    evaluation_root_path = tmp_path / "evaluation_manifest.json"
    for number, cell in enumerate(("iid_deterministic", "iid_stochastic"), start=1):
        cell_path = tmp_path / "evaluation" / "replicate_0" / "OR" / f"{cell}.json"
        _write_json(cell_path, {"cell": cell, "verbose": [number] * 32})
        evaluation_root["cells"].append(
            benchmark_runner._artifact_reference(
                tmp_path, cell_path, replicate=0, arm="OR", cell=cell,
            )
        )
        evaluation_root["progress"]["completed_cells"] = number
        _write_json(evaluation_root_path, evaluation_root)
    assert "verbose" not in json.dumps(evaluation_root)
    assert not list(tmp_path.rglob("*.tmp"))


def test_streaming_reference_fail_closed_variants_and_order_contract(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "evidence" / "update_1.json"
    _write_json(artifact, {"payload": list(range(64))})
    reference = benchmark_runner._artifact_reference(tmp_path, artifact, update=1)
    path, payload = benchmark_runner._verified_json_reference(
        tmp_path, reference, identity_keys=frozenset({"update"}),
    )
    assert path == artifact.resolve() and payload["payload"][-1] == 63
    assert benchmark_runner._ordered_reference_values(
        [{"update": 1}, {"update": 2}], "update", [1, 2]
    )
    for values in (
        [], [{"update": 1}], [{"update": 1}, {"update": 1}],
        [{"update": 2}, {"update": 1}],
        [{"update": 1}, {"update": 2}, {"update": 3}],
    ):
        assert not benchmark_runner._ordered_reference_values(
            values, "update", [1, 2]
        )

    for label, mutation in (
        ("size", lambda value: value.__setitem__("byte_count", value["byte_count"] + 1)),
        ("hash", lambda value: value.__setitem__("sha256", "f" * 64)),
        ("escape", lambda value: value.__setitem__("path", "../escape.json")),
        ("absolute", lambda value: value.__setitem__("path", str(artifact.resolve()))),
    ):
        corrupted = deepcopy(reference)
        mutation(corrupted)
        with pytest.raises(ValueError):
            benchmark_runner._verified_json_reference(
                tmp_path, corrupted, identity_keys=frozenset({"update"}),
            )

    for key, replacements in (
        ("byte_count", (True, float(reference["byte_count"]), str(reference["byte_count"]))),
        ("update", (True, 1.0, "1")),
        ("sha256", (reference["sha256"].upper(),)),
    ):
        for replacement in replacements:
            corrupted = deepcopy(reference)
            corrupted[key] = replacement
            with pytest.raises(ValueError, match="type mismatch"):
                benchmark_runner._verified_json_reference(
                    tmp_path, corrupted, identity_keys=frozenset({"update"}),
                )
    generated_reference = benchmark_runner._artifact_reference(
        tmp_path, artifact, replicate=0, generation=1,
    )
    for key in ("replicate", "generation"):
        original = generated_reference[key]
        for replacement in (True, float(original), str(original)):
            corrupted = deepcopy(generated_reference)
            corrupted[key] = replacement
            with pytest.raises(ValueError, match="type mismatch"):
                benchmark_runner._verified_json_reference(
                    tmp_path, corrupted,
                    identity_keys=frozenset({"replicate", "generation"}),
                )

    pristine_bytes = artifact.read_bytes()
    artifact.write_bytes(pristine_bytes[:-5])
    with pytest.raises(ValueError, match="byte count"):
        benchmark_runner._verified_json_reference(
            tmp_path, reference, identity_keys=frozenset({"update"}),
        )
    artifact.write_bytes(b"{corrupt")
    corrupt_reference = benchmark_runner._artifact_reference(
        tmp_path, artifact, update=1,
    )
    with pytest.raises(json.JSONDecodeError):
        benchmark_runner._verified_json_reference(
            tmp_path, corrupt_reference, identity_keys=frozenset({"update"}),
        )
    artifact.unlink()
    with pytest.raises(ValueError, match="missing"):
        benchmark_runner._verified_json_reference(
            tmp_path, reference, identity_keys=frozenset({"update"}),
        )


def test_streaming_failure_preserves_indexed_refs_and_ignores_orphan(
    tmp_path: Path,
) -> None:
    indexed_path = tmp_path / "train" / "replicate_0" / "evidence" / "update_1.json"
    _write_json(indexed_path, {"update": 1, "accepted": True})
    indexed = benchmark_runner._artifact_reference(
        tmp_path, indexed_path, update=1,
    )
    index_path = indexed_path.parent.parent / "indexes" / "index_1.json"
    _write_json(index_path, {
        "replicate": 0, "generation": 1, "updates": [indexed],
    })
    index_reference = benchmark_runner._artifact_reference(
        tmp_path, index_path, replicate=0, generation=1,
    )
    manifest_path = tmp_path / "train_manifest.json"
    root = {
        "artifact_schema": FORMAL_TRAIN_ARTIFACT_SCHEMA,
        "formal": True, "mode": "formal_train", "status": "IN_PROGRESS",
        "branch": "IN_PROGRESS", "replicate_indexes": [index_reference],
    }
    _write_json(manifest_path, root)

    orphan_path = indexed_path.parent / "update_2.json"
    _write_json(orphan_path, {"update": 2, "accepted": False})
    terminal = benchmark_runner._publish_operational_failure(
        tmp_path, mode="formal_train", formal=True, stage="training",
        replicate=0, arm=None, cell=None, batch=None,
        exception=RuntimeError("injected after shard before index"),
        completed_paths=[indexed["path"]], last_evidence=indexed,
        manifest_path=manifest_path,
    )
    assert terminal["replicate_indexes"] == [index_reference]
    assert terminal["status"] == terminal["branch"] == "INVALID_OPERATIONAL"
    valid, errors = benchmark_runner._operational_failure_manifest_valid(
        tmp_path, manifest_path,
    )
    assert valid and not errors
    with index_path.open("r", encoding="utf-8") as handle:
        assert json.load(handle)["updates"] == [indexed]
    assert orphan_path.as_posix() not in json.dumps(terminal)
    failure_path = benchmark_runner._resolve_artifact_path(
        tmp_path, terminal["failure_artifact"]["path"],
    )
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    failure["last_complete_evidence"] = benchmark_runner._artifact_reference(
        tmp_path, orphan_path, update=2,
    )
    _write_json(failure_path, failure)
    terminal["failure_artifact"] = benchmark_runner._artifact_reference(
        tmp_path, failure_path, artifact="operational_failure",
    )
    _write_json(manifest_path, terminal)
    valid, errors = benchmark_runner._operational_failure_manifest_valid(
        tmp_path, manifest_path,
    )
    assert not valid and "failure_last_reference_not_indexed" in errors
    assert not list(tmp_path.rglob("*.tmp"))


@pytest.mark.parametrize(
    ("interruption", "expected_batch"),
    (("mid_cell", 0), ("before_cell_publication", None)),
)
def test_evaluation_failure_keeps_only_prior_indexed_cell_reference(
    streamed_exercise_root: Path, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, interruption: str,
    expected_batch: int | None,
) -> None:
    output_root = tmp_path / interruption
    shutil.copytree(streamed_exercise_root / "train", output_root / "train")
    completed_paths: list[str] = []
    last_evidence: dict[str, Any] = {}
    context: dict[str, Any] = {
        "replicate": None, "arm": None, "cell": None, "batch": None,
    }
    if interruption == "mid_cell":
        pristine_rows = benchmark_runner._trajectory_episode_rows
        calls = 0

        def interrupted_rows(*args: Any, **kwargs: Any) -> Any:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("injected mid-cell")
            return pristine_rows(*args, **kwargs)

        monkeypatch.setattr(
            benchmark_runner, "_trajectory_episode_rows", interrupted_rows,
        )
    else:
        pristine_write = benchmark_runner._write_json

        def interrupted_write(path: Path, value: Any) -> None:
            if path.name == "iid_stochastic.json":
                raise RuntimeError("injected before cell publication")
            pristine_write(path, value)

        monkeypatch.setattr(benchmark_runner, "_write_json", interrupted_write)
    manifest_path = output_root / "evaluation_manifest.json"
    with pytest.raises(RuntimeError, match="injected") as raised:
        benchmark_runner._evaluation_core(
            output_root, device=torch.device("cuda"), replicates=(0,),
            episodes_per_cell=16, formal=False,
            artifact_schema=benchmark_runner.EXERCISE_EVALUATION_ARTIFACT_SCHEMA,
            checkpoint_name="update_1.pt", completed_paths=completed_paths,
            last_evidence=last_evidence, failure_context=context,
        )
    terminal = benchmark_runner._publish_operational_failure(
        output_root, mode="formal_path_exercise_evaluate", formal=False,
        stage="evaluation", replicate=context["replicate"], arm=context["arm"],
        cell=context["cell"], batch=context["batch"],
        exception=raised.value, completed_paths=completed_paths,
        last_evidence=last_evidence, manifest_path=manifest_path,
    )
    assert terminal["status"] == terminal["branch"] == "INVALID_OPERATIONAL"
    assert len(terminal["cells"]) == 1
    prior = terminal["cells"][0]
    _failure_path, failure = benchmark_runner._verified_json_reference(
        output_root, terminal["failure_artifact"],
        identity_keys=frozenset({"artifact"}),
    )
    assert failure["last_complete_evidence"] == prior
    assert not {"batch_index", "episode_ids", "replay"} & set(
        failure["last_complete_evidence"]
    )
    assert failure["replicate"] == 0
    assert failure["arm"] == "OR"
    assert failure["cell"] == "iid_stochastic"
    assert failure["batch"] == expected_batch
    valid, errors = benchmark_runner._operational_failure_manifest_valid(
        output_root, manifest_path,
    )
    assert valid and not errors
    assert not list(output_root.rglob("*.tmp"))


def test_streamed_exercise_validates_one_verbose_artifact_at_a_time(
    streamed_exercise_root: Path,
) -> None:
    live: set[Path] = set()
    maximum_live = 0

    def observer(event: str, path: Path) -> None:
        nonlocal maximum_live
        if event == "loaded":
            live.add(path)
            maximum_live = max(maximum_live, len(live))
        else:
            live.remove(path)

    valid, errors, compact = benchmark_runner._validate_streamed_operational_records(
        streamed_exercise_root, expected_replicates=(0,), expected_updates=1,
        episodes_per_cell=16, formal=False, artifact_observer=observer,
    )
    assert valid and not errors
    assert maximum_live == 1 and not live
    assert set(compact["episodes"]) == {(0, arm) for arm in ARMS}
    assert set(compact["audit_rows"]) == {0}
    with (streamed_exercise_root / "train_manifest.json").open(
        "r", encoding="utf-8"
    ) as handle:
        train_root = json.load(handle)
    with (streamed_exercise_root / "evaluation_manifest.json").open(
        "r", encoding="utf-8"
    ) as handle:
        evaluation_root = json.load(handle)
    assert "updates" not in train_root and "replicates" not in train_root
    assert "artifacts" not in evaluation_root
    assert all("batches" not in reference and "episodes" not in reference for reference in evaluation_root["cells"])
    assert not list(streamed_exercise_root.rglob("*.tmp"))
    with pytest.raises(ValueError, match="rejects non-formal training"):
        _aggregate_analysis_core(
            streamed_exercise_root, authorization=FORMAL_AUTHORIZATION,
        )


def test_four_update_formal_trajectory_replays_and_streams_exactly(
    device: torch.device, tmp_path: Path,
) -> None:
    """Reproduce the failed fourth update through the non-formal shared core."""

    assert device.type == "cuda"
    assert benchmark_runner.FORMAL_NUM_ENVS == 16
    assert HORIZON == 80
    assert benchmark_runner.PPO_PASSES == 4
    output_root = tmp_path / "four_update_replay_gate"
    completed_paths: list[str] = []
    last_evidence: dict[str, Any] = {}
    manifest = benchmark_runner._training_core(
        output_root,
        device=device,
        replicates=(0,),
        updates=4,
        formal=False,
        artifact_schema=benchmark_runner.EXERCISE_TRAIN_ARTIFACT_SCHEMA,
        completed_paths=completed_paths,
        last_evidence=last_evidence,
    )
    assert manifest["status"] == "COMPLETE"
    assert manifest["progress"] == {
        "completed_updates": 4,
        "total_updates": 4,
        "completed_replicates": 1,
        "total_replicates": 1,
    }
    index_path, index = benchmark_runner._verified_json_reference(
        output_root,
        manifest["replicate_indexes"][0],
        identity_keys=frozenset({"replicate", "generation"}),
    )
    assert index["status"] == "COMPLETE"
    assert [reference["update"] for reference in index["updates"]] == [1, 2, 3, 4]
    assert index_path.name == f"index_{index['generation']}.json"

    rng_chain = {
        arm: benchmark_runner._initial_rng_states(
            authoritative_seed_map("train", 0)
        )
        for arm in ARMS
    }
    ledger_cache: dict[Any, Any] = {}
    for update, reference in enumerate(index["updates"], start=1):
        shard_path, shard = benchmark_runner._verified_json_reference(
            output_root, reference, identity_keys=frozenset({"update"}),
        )
        assert shard_path.name == f"update_{update}.json"
        ends: dict[str, dict[str, Any]] = {}
        assert _training_update_valid(
            shard["evidence"],
            update=update,
            replicate=0,
            formal=False,
            mode="formal_path_exercise_train",
            rng_starts=rng_chain,
            validated_rng_ends=ends,
            ledger_cache=ledger_cache,
        )
        for arm_name in ARMS:
            replay = shard["evidence"]["arms"][arm_name]["replay"]
            assert replay["passed"] and not replay["failures"]
            for component in REPLAY_LOG_COMPONENT_FIELDS:
                record = replay["likelihood_components"][component]
                assert record["absolute_error"] <= record["mixed_bound"]
                assert record["ratio_drift"] <= record["ratio_cap"]
            for joint_name in REPLAY_JOINT_FIELDS:
                joint = replay["joints"][joint_name]
                assert joint["error"] <= joint["bound"]
                assert joint["excess"] <= 0.0
                assert joint["assembly_excess"] <= 0.0
            assert (
                replay["event_joint_ratio"]["ratio_drift"]
                <= replay["event_joint_ratio"]["ratio_cap"]
            )
        rng_chain = ends
        del shard

    assert {
        path.name
        for path in (output_root / "train" / "replicate_0" / "evidence").glob(
            "update_*.json"
        )
    } == {"update_1.json", "update_2.json", "update_3.json", "update_4.json"}
    assert all(
        benchmark_runner._restore_metrics_valid(
            index["arms"][arm]["restore_metrics"]
        )
        for arm in ARMS
    )
    assert not list(output_root.rglob("*.tmp"))


def test_causal_audit_telemetry_is_descriptive(
    causal_audit_oracle_bundle: dict[str, Any],
) -> None:
    record = causal_audit_oracle_bundle["batched"][0]
    outcomes = deepcopy(record["branch_outcomes"])
    telemetry = record["telemetry"]
    assert telemetry["selected_state_count"] == len(causal_audit_oracle_bundle["selected"])
    assert telemetry["collector_call_count"] > 0 and telemetry["serialized_size_bytes"] > 0
    mutated = deepcopy(record)
    mutated["telemetry"] = {key: 0 for key in telemetry}
    assert mutated["branch_outcomes"] == outcomes


def test_formal_validator_rejects_exercise_identity(tmp_path: Any) -> None:
    training, cells = _synthetic_operational_records()
    with pytest.raises(ValueError, match="monolithic"):
        benchmark_runner._reject_monolithic_operational_records(
            training, cells, expected_replicates=(0,),
        )
    exercise_training = dict(training)
    exercise_training["artifact_schema"] = benchmark_runner.EXERCISE_TRAIN_ARTIFACT_SCHEMA
    exercise_training["formal"] = False
    exercise_training["mode"] = "formal_path_exercise_train"
    exercise_training["branch"] = "FORMAL_PATH_EXERCISE_TRAIN_COMPLETE"
    assert exercise_training["artifact_schema"] != FORMAL_TRAIN_ARTIFACT_SCHEMA
    assert exercise_training["formal"] is False
    _write_json(tmp_path / "train_manifest.json", exercise_training)
    with pytest.raises(ValueError, match="rejects non-formal training"):
        _aggregate_analysis_core(tmp_path, authorization=FORMAL_AUTHORIZATION)

    copied = cells[(0, "EHC", "held_out_stochastic")] | {
        "artifact_schema": benchmark_runner.EXERCISE_EVALUATION_ARTIFACT_SCHEMA,
        "formal": False,
    }
    assert not benchmark_runner._evaluation_cell_valid(
        copied, replicate=0, arm="EHC", profile="held_out",
        deterministic=False, cell="held_out_stochastic", formal=True,
        mode="formal_evaluate", episodes_per_cell=256,
        checkpoint_origin="update_250.pt",
        checkpoint_path=training["replicates"]["0"]["arms"]["EHC"]["checkpoint"],
        ledger_cache={},
    )[0]


def _branch_inputs() -> dict[str, object]:
    return {
        "operational_valid": True,
        "non_create_opportunities": 1000,
        "multi_opportunity_lifecycles": 250,
        "eligible_keep_rows": SUPPORT_FLOOR,
        "eligible_renew_rows": SUPPORT_FLOOR,
        "causal_keep_rows_by_replicate": (
            CAUSAL_AUDIT_QUOTA_PER_ACTION,
        ) * CAUSAL_AUDIT_REPLICATES,
        "causal_renew_rows_by_replicate": (
            CAUSAL_AUDIT_QUOTA_PER_ACTION,
        ) * CAUSAL_AUDIT_REPLICATES,
        "utility_ci": {
            "OR": (0.79, 0.81), "DUM": (0.79, 0.81), "EHC": (0.80, 0.84)
        },
        "g_ci": (0.11, 0.15),
        "k_bin_cis": ((0.11, 0.20), (0.11, 0.20), (0.05, 0.09)),
        "intervention_ci": (0.11, 0.20),
        "c_total_keep_ci": (0.03, 0.09),
        "c_total_renew_ci": (0.03, 0.09),
        "c_total_keep_mean": 0.06,
        "c_total_renew_mean": 0.06,
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


def test_registered_contract_carries_execution_and_replacement_c() -> None:
    """The contract is about to be frozen into every checkpoint, so both the
    execution environment and the whole of Replacement C must be readable
    from it alone."""

    contract = registered_contract()
    execution = contract["execution"]
    assert execution["backend"] == active_execution_backend()
    assert execution["backend"] in REGISTERED_EXECUTION_BACKENDS
    assert execution["registered_backends"] == list(REGISTERED_EXECUTION_BACKENDS)
    assert execution["torch_threads"] == REGISTERED_TORCH_THREADS
    assert execution["torch_threads"] == torch.get_num_threads()
    streaming = contract["evidence_streaming"]
    assert streaming["train_manifest_schema"] == 6
    assert streaming["train_index_schema"] == 3
    assert streaming["train_update_schema"] == 2
    assert streaming["evaluation_manifest_schema"] == 6
    assert streaming["evaluation_cell_schema"] == EVALUATION_CELL_SCHEMA == 9
    assert benchmark_runner.FORMAL_EVALUATION_MANIFEST_SCHEMA.endswith(
        ".formal_evaluation_manifest.v6"
    )
    assert FORMAL_EVALUATION_ARTIFACT_SCHEMA.endswith(".formal_evaluation.v9")
    assert benchmark_runner.FORMAL_ANALYSIS_ARTIFACT_SCHEMA.endswith(
        ".formal_analysis.v6"
    )
    assert benchmark_runner.EXERCISE_EVALUATION_MANIFEST_SCHEMA.endswith(
        ".formal_path_exercise.evaluation_manifest.v5"
    )
    assert benchmark_runner.EXERCISE_EVALUATION_ARTIFACT_SCHEMA.endswith(
        ".formal_path_exercise.evaluation.v7"
    )
    assert benchmark_runner.EXERCISE_MANIFEST_SCHEMA.endswith(
        ".formal_path_exercise.manifest.v4"
    )

    thresholds = contract["thresholds"]
    assert thresholds["c_total_keep_lcb"] == C_TOTAL_KEEP_LCB_FLOOR == 0.0
    assert thresholds["c_total_renew_lcb"] == C_TOTAL_RENEW_LCB_FLOOR == 0.0
    assert thresholds["c_total_keep_mean_floor"] == C_TOTAL_KEEP_MEAN_FLOOR == 0.02
    assert thresholds["c_total_renew_mean_floor"] == C_TOTAL_RENEW_MEAN_FLOOR == 0.02

    audit = contract["causal_audit"]
    assert audit["natural_actions"] == ["KEEP", "RENEW"] == list(
        CAUSAL_AUDIT_NATURAL_ACTIONS
    )
    assert audit["branches"] == list(CAUSAL_AUDIT_BRANCHES)
    assert audit["quota_per_action_per_replicate"] == 32 == CAUSAL_AUDIT_QUOTA_PER_ACTION
    assert audit["replicates"] == 5 == CAUSAL_AUDIT_REPLICATES
    assert audit["selected_rows"] == 320 == CAUSAL_AUDIT_SELECTED_ROWS
    assert audit["branch_rows"] == 960 == CAUSAL_AUDIT_BRANCH_ROWS
    selection = audit["selection_stream"]
    assert selection["namespace"] == CAUSAL_AUDIT_SELECTION_NAMESPACE
    assert selection["base_seed"] == BOOTSTRAP_SEED
    assert selection["coordinate"] == CAUSAL_AUDIT_SELECTION_COORDINATE
    # A dedicated stream, not a re-use of an existing one: it must differ
    # from the bootstrap resample stream that shares its base seed, and from
    # every owned collector stream.
    assert set(RNG_NAMES) <= set(selection["distinct_from"])
    assert "bootstrap_resample" in selection["distinct_from"]
    selection_state = make_rng(
        BOOTSTRAP_SEED, CAUSAL_AUDIT_SELECTION_COORDINATE
    ).bit_generator.state
    assert selection_state != np.random.default_rng(
        BOOTSTRAP_SEED
    ).bit_generator.state
    seed_map = authoritative_seed_map("held_out", 0)
    for name in RNG_NAMES:
        assert selection_state != np.random.default_rng(
            seed_map[name]
        ).bit_generator.state


def test_checkpoint_rejects_a_foreign_execution_backend(
    device: torch.device, tmp_path,
) -> None:
    """The same-backend constraint is structural, not documented.

    The execution block rides inside the contract that `load_checkpoint`
    compares for equality, so a checkpoint produced under another backend --
    or under another thread configuration -- is unloadable here. This test
    edits only that block of an otherwise valid checkpoint, so a failure can
    only come from the execution record.
    """

    arms, base_optimizers, event_optimizers = initialize_arms(device)
    state = make_training_state("EHC", 0)
    checkpoint = tmp_path / "origin.pt"
    save_checkpoint(
        checkpoint, arm=arms["EHC"], base_optimizer=base_optimizers["EHC"],
        event_optimizer=event_optimizers["EHC"], state=state,
    )
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    assert payload["contract"]["execution"]["backend"] == device.type
    # Control: the unedited checkpoint loads, so the rejections below are
    # caused by the edit and not by an unrelated defect.
    load_checkpoint(
        checkpoint, device=device, expected_arm="EHC", expected_replicate=0
    )
    foreign_backend = next(
        name for name in REGISTERED_EXECUTION_BACKENDS if name != device.type
    )
    for label, mutation in (
        ("backend", {"backend": foreign_backend}),
        ("threads", {"torch_threads": REGISTERED_TORCH_THREADS + 13}),
    ):
        foreign = deepcopy(payload)
        foreign["contract"]["execution"] |= mutation
        foreign_path = tmp_path / f"foreign_{label}.pt"
        torch.save(foreign, foreign_path)
        with pytest.raises(ValueError, match="registered contract mismatch"):
            load_checkpoint(
                foreign_path, device=device,
                expected_arm="EHC", expected_replicate=0,
            )


def test_registered_backend_activation_never_falls_back(
    device: torch.device,
) -> None:
    """`cuda` and `cpu` are both registered; anything else raises, an
    unavailable backend raises rather than being substituted, and a second
    backend cannot be activated in a process that already has one."""

    active = active_execution_backend()
    assert require_registered_backend(active) == torch.device(active)
    for unregistered in ("mps", "xpu", "CUDA", "cuda:0", ""):
        with pytest.raises(ValueError, match="registered execution backend"):
            require_registered_backend(unregistered)
    other = next(
        name for name in REGISTERED_EXECUTION_BACKENDS if name != active
    )
    # Two refusals are both correct and both fail closed: "already active"
    # when the other backend exists on this host, "unavailable" when it does
    # not. Which one fires is a property of the machine, so asserting only
    # the first would encode this host's hardware into the contract. What
    # matters is that no substitution occurs.
    with pytest.raises(RuntimeError, match="already active|unavailable"):
        require_registered_backend(other)
    # A device from the other backend is refused everywhere arms are built,
    # so a stray device object cannot smuggle work onto it.
    with pytest.raises(RuntimeError, match="active execution backend"):
        initialize_arms(torch.device(other))


def test_replacement_c_requires_both_natural_action_strata() -> None:
    """Both natural-action total-consequence strata are required.

    Covers the equality boundaries on both the interval gate (`LCB > 0`, so
    `LCB == 0` does not pass; `UCB <= 0`, so `UCB == 0` confidently fails)
    and the frozen point floors (`mean >= 0.02`, so exactly `0.02` passes).
    """

    base = _branch_inputs()
    assert select_result_branch(**base) == "COMMITMENT_SUPPORTED"
    passing = (0.03, 0.09)
    crossing = (C_TOTAL_KEEP_LCB_FLOOR, 0.09)
    failing = (-0.05, C_TOTAL_KEEP_LCB_FLOOR)
    # One-sided pass: whichever direction is not established, the result is
    # never COMMITMENT_SUPPORTED.
    for one_sided in (
        {"c_total_keep_ci": crossing, "c_total_renew_ci": passing},
        {"c_total_keep_ci": passing, "c_total_renew_ci": crossing},
        {"c_total_keep_ci": failing, "c_total_renew_ci": passing},
        {"c_total_keep_ci": passing, "c_total_renew_ci": failing},
        {"c_total_keep_mean": C_TOTAL_KEEP_MEAN_FLOOR - 0.001},
        {"c_total_renew_mean": C_TOTAL_RENEW_MEAN_FLOOR - 0.001},
    ):
        assert select_result_branch(
            **(base | one_sided)
        ) != "COMMITMENT_SUPPORTED", one_sided
    # `LCB == 0` does not clear a strict `> 0` gate, and `UCB > 0` is not the
    # dual either, so the crossing case is underpowered, not a failure.
    assert select_result_branch(
        **(base | {"c_total_keep_ci": crossing})
    ) == "MIXED_UNDERPOWERED"
    assert select_result_branch(
        **(base | {"c_total_renew_ci": crossing})
    ) == "MIXED_UNDERPOWERED"
    # `UCB == 0` is the exact statistical dual and confidently fails.
    assert select_result_branch(
        **(base | {"c_total_keep_ci": failing})
    ) == "REPRESENTATION_ONLY"
    assert select_result_branch(
        **(base | {"c_total_renew_ci": failing})
    ) == "REPRESENTATION_ONLY"
    # The point floors are point estimates: exactly at the floor passes, and
    # missing the floor is underpowered rather than a confident failure,
    # because a point estimate carries no interval dual.
    assert select_result_branch(
        **(base | {
            "c_total_keep_mean": C_TOTAL_KEEP_MEAN_FLOOR,
            "c_total_renew_mean": C_TOTAL_RENEW_MEAN_FLOOR,
        })
    ) == "COMMITMENT_SUPPORTED"
    assert select_result_branch(
        **(base | {"c_total_keep_mean": C_TOTAL_KEEP_MEAN_FLOOR - 0.001})
    ) == "MIXED_UNDERPOWERED"
    assert select_result_branch(
        **(base | {"c_total_renew_mean": C_TOTAL_RENEW_MEAN_FLOOR - 0.001})
    ) == "MIXED_UNDERPOWERED"
    for name in ("c_total_keep_ci", "c_total_renew_ci"):
        with pytest.raises(ValueError, match="inverted"):
            select_result_branch(**(base | {name: (0.09, 0.03)}))
        with pytest.raises(ValueError, match="lcb, ucb"):
            select_result_branch(**(base | {name: (0.03,)}))


def test_causal_audit_quota_shortfall_is_non_identifiable_and_unpoolable() -> None:
    """A replicate short of the registered quota for either natural action
    makes the run non-identifiable, and no pooled total can rescue it.

    Pooling is not merely rejected, it is inexpressible: the branch selector
    takes exactly `CAUSAL_AUDIT_REPLICATES` per-replicate counts and no
    total, so there is no input through which a surplus in one replicate can
    cover a shortfall in another.
    """

    base = _branch_inputs()
    quota = CAUSAL_AUDIT_QUOTA_PER_ACTION
    assert select_result_branch(**base) == "COMMITMENT_SUPPORTED"
    for name in (
        "causal_keep_rows_by_replicate", "causal_renew_rows_by_replicate"
    ):
        for short_index in range(CAUSAL_AUDIT_REPLICATES):
            counts = [quota] * CAUSAL_AUDIT_REPLICATES
            counts[short_index] = quota - 1
            assert select_result_branch(
                **(base | {name: tuple(counts)})
            ) == "BENCHMARK_NON_IDENTIFIABLE", (name, short_index)
            # A large surplus everywhere else -- a pooled total far above
            # 5*32 -- still does not rescue the short replicate.
            surplus = [10 * quota] * CAUSAL_AUDIT_REPLICATES
            surplus[short_index] = quota - 1
            assert sum(surplus) > quota * CAUSAL_AUDIT_REPLICATES
            assert select_result_branch(
                **(base | {name: tuple(surplus)})
            ) == "BENCHMARK_NON_IDENTIFIABLE", (name, short_index)
        # Exactly the quota everywhere is sufficient; the quota is a floor,
        # not a target, so a surplus is also fine.
        assert select_result_branch(
            **(base | {name: (quota,) * CAUSAL_AUDIT_REPLICATES})
        ) == "COMMITMENT_SUPPORTED"
        # A pooled scalar, or any count vector that is not one entry per
        # replicate, is rejected outright rather than interpreted.
        for wrong in ((), (quota,), (quota,) * 4, (quota,) * 6):
            with pytest.raises(ValueError, match=name):
                select_result_branch(**(base | {name: wrong}))
    # The shortfall resolves at position 2, ahead of every evidence branch,
    # so it cannot be masked by otherwise passing statistics.
    assert select_result_branch(
        **(base | {
            "causal_keep_rows_by_replicate": (quota - 1,) * CAUSAL_AUDIT_REPLICATES,
            "g_ci": (0.0, 0.01),
        })
    ) == "BENCHMARK_NON_IDENTIFIABLE"


# CAUSAL_AUDIT_EVIDENCE_TESTS

def _zero_restore_metrics() -> dict[str, Any]:
    return {
        "continuous": {"model": 0.0, "base_optimizer": 0.0, "event_optimizer": 0.0},
        "discrete": {"training_state": 0},
        "runtime_rng": {
            "python": 0, "numpy_global": 0, "torch_cpu": 0,
            "torch_cuda": {str(index): 0 for index in range(torch.cuda.device_count())},
        },
        "owned_rng": {name: 0 for name in RNG_NAMES},
    }


def test_strict_restore_metrics_cover_every_rng_owner_and_reject_bad_leaves() -> None:
    clean = _zero_restore_metrics()
    assert benchmark_runner._restore_metrics_valid(clean)
    leaf_paths = [
        ("continuous", name) for name in clean["continuous"]
    ] + [("discrete", "training_state")] + [
        ("runtime_rng", name) for name in ("python", "numpy_global", "torch_cpu")
    ] + [
        ("runtime_rng", "torch_cuda", name) for name in clean["runtime_rng"]["torch_cuda"]
    ] + [("owned_rng", name) for name in RNG_NAMES]
    assert {path[-1] for path in leaf_paths if path[0] == "owned_rng"} == set(RNG_NAMES)
    for path in leaf_paths:
        for bad in (True, float("nan"), float("inf"), -1e-12, 1.0000001e-7):
            mutated = deepcopy(clean)
            target = mutated
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = bad
            assert not benchmark_runner._restore_metrics_valid(mutated), (path, bad)
        missing = deepcopy(clean)
        target = missing
        for key in path[:-1]:
            target = target[key]
        target.pop(path[-1])
        assert not benchmark_runner._restore_metrics_valid(missing), path


def _trace_inventory_inputs(bundle: dict[str, Any]) -> tuple[list[Any], list[Any]]:
    raw, batches = [], []
    for batch_index, trajectory in enumerate(bundle["trajectories"]):
        rows = list(trajectory.raw_event_trace)
        raw.extend({"batch_index": batch_index, "row": deepcopy(row)} for row in rows)
        batches.append({
            "episode_ids": list(trajectory.ledger_ids),
            "rng_evidence": {"ledgers": deepcopy(trajectory.rng_audit["ledgers"])},
            "raw_event_trace_binding": {
                "row_count": len(rows), "trace_sha256": _digest_json(rows),
            },
        })
    return raw, batches


def _refresh_lightweight_causal_provenance_size(
    artifact: dict[str, Any],
) -> None:
    artifact["telemetry"]["serialized_size_bytes"] = len(json.dumps(
        {
            "raw_event_trace": artifact["raw_event_trace"],
            "audit_rows": artifact["audit_rows"],
        },
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8"))


def _lightweight_causal_provenance_bundle(
    monkeypatch: pytest.MonkeyPatch, *, status: str,
) -> dict[str, Any]:
    assert status in {"complete", "unavailable"}
    monkeypatch.setattr(
        benchmark_runner, "CAUSAL_AUDIT_QUOTA_PER_ACTION", 2,
    )
    inventory: dict[str, list[dict[str, Any]]] = {
        action: [] for action in CAUSAL_AUDIT_NATURAL_ACTIONS
    }
    for action_index, action in enumerate(CAUSAL_AUDIT_NATURAL_ACTIONS):
        for offset in range(2):
            episode_id = action_index * 2 + offset
            payload_offset = float(1 + episode_id)
            inventory[action].append({
                "replicate": 0,
                "base_episode_id": episode_id // 2,
                "episode_id": episode_id,
                "sign_parity": episode_id & 1,
                "time": 0,
                "key": 0,
                "membership_epoch": 0,
                "segment_id": 0,
                "natural_action": action,
                "batch_index": 0,
                "env_index": episode_id,
                "installed_z": benchmark_runner._float32_payload(
                    np.full(MARK_DIM, payload_offset, dtype=np.float32),
                ),
                "candidate_u": benchmark_runner._float32_payload(
                    np.full(MARK_DIM, payload_offset + 0.25, dtype=np.float32),
                ),
                "candidate_z": benchmark_runner._float32_payload(
                    np.full(MARK_DIM, payload_offset + 0.5, dtype=np.float32),
                ),
            })
        inventory[action].sort(key=benchmark_runner._causal_audit_key)
    monkeypatch.setattr(
        benchmark_runner,
        "_causal_audit_trace_inventory",
        lambda *_args, **_kwargs: deepcopy(inventory),
    )
    monkeypatch.setattr(
        benchmark_runner,
        "_tracking_outcome_valid",
        lambda outcome: (
            isinstance(outcome, dict)
            and set(outcome) == {"utility"}
            and type(outcome["utility"]) in (int, float)
            and math.isfinite(float(outcome["utility"]))
        ),
    )
    monkeypatch.setattr(
        benchmark_runner,
        "validate_typed_natural_audit",
        lambda audit: (
            isinstance(audit, dict)
            and set(audit) == {"status", "binding_evidence"}
            and audit["status"] in {"complete", "unavailable"}
        ),
    )

    selected_keys = {
        action: [
            list(benchmark_runner._causal_audit_key(row))
            for row in inventory[action]
        ]
        for action in CAUSAL_AUDIT_NATURAL_ACTIONS
    }
    selected_order = sorted(
        tuple(key) for keys in selected_keys.values() for key in keys
    )
    records = {
        benchmark_runner._causal_audit_key(row): row
        for rows in inventory.values() for row in rows
    }
    donors: dict[tuple[Any, ...], tuple[int, dict[str, Any]]] = {}
    for action in CAUSAL_AUDIT_NATURAL_ACTIONS:
        rows = inventory[action]
        for position, recipient in enumerate(rows):
            donors[benchmark_runner._causal_audit_key(recipient)] = (
                position, rows[(position + 1) % len(rows)],
            )

    seed_map = authoritative_seed_map("held_out", 0)
    start_states = {
        name: deepcopy(
            np.random.default_rng(int(seed_map[name])).bit_generator.state
        )
        for name in RNG_NAMES
    }
    cell_batches = [{
        "rng_bindings": {
            name: {
                "start_state": deepcopy(start_states[name]),
                "draw_schedule": [],
            }
            for name in RNG_NAMES
        },
    }]
    episode_outcomes = {
        row["episode_id"]: {"utility": float(10 + row["episode_id"])}
        for row in records.values()
    }
    attempted_keys = (
        selected_order if status == "complete" else selected_order[:1]
    )
    audit_rows = []
    for key_index, key in enumerate(attempted_keys):
        record = records[key]
        mapping_position, donor = donors[key]
        audit_id = _digest_json(list(key))
        expected_branch_evidence = (
            benchmark_runner._causal_audit_branch_evidence(
                record, donor, mapping_position,
            )
        )
        natural_status = (
            "unavailable"
            if status == "unavailable" and key_index == len(attempted_keys) - 1
            else "complete"
        )
        natural_branch = (
            "KEEP_HELD_MARK"
            if record["natural_action"] == "KEEP"
            else "RENEW_CANDIDATE_MARK"
        )
        natural_audit = {
            "status": natural_status,
            "binding_evidence": {
                "audit_id": audit_id,
                "replicate": 0,
                "batch_index": 0,
                "source_episode": record["episode_id"],
                "focal_time": record["time"],
                "source_environment": record["env_index"],
                "focal_key": record["key"],
                "membership_epoch": record["membership_epoch"],
                "segment_id": record["segment_id"],
                "natural_action": record["natural_action"],
                "natural_branch": natural_branch,
            },
        }
        rng_bindings: dict[str, dict[str, Any]] = {}
        for branch in CAUSAL_AUDIT_BRANCHES:
            context = benchmark_runner._causal_audit_bound_context(
                {
                    "domain": "stage2",
                    "mode": "formal_path_exercise_evaluate",
                    "formal": False,
                    "replicate": 0,
                    "arm": "EHC",
                    "cell": "held_out_stochastic",
                    "batch": 0,
                    "audit_id": audit_id,
                    "episode_id": record["episode_id"],
                    "time": record["time"],
                    "key": record["key"],
                    "membership_epoch": record["membership_epoch"],
                    "segment_id": record["segment_id"],
                    "natural_action": record["natural_action"],
                    "branch": branch,
                },
                key=key,
                donor_key=benchmark_runner._causal_audit_key(donor),
                branch_evidence=expected_branch_evidence,
            )
            rng_bindings[branch] = {
                name: benchmark_runner.make_rng_binding(
                    context=context,
                    stream=name,
                    seed=int(seed_map[name]),
                    start_state=start_states[name],
                    draw_schedule=[],
                    expected_end_state=start_states[name],
                )
                for name in RNG_NAMES
            }
        donor_material = benchmark_runner._causal_audit_donor_material(
            record, donor, mapping_position,
        )
        row = {
            **{name: record[name] for name in (
                "replicate", "base_episode_id", "episode_id", "sign_parity",
                "time", "key", "membership_epoch", "segment_id",
                "natural_action", "batch_index", "env_index",
            )},
            "audit_id": audit_id,
            "natural_outcome": deepcopy(
                episode_outcomes[record["episode_id"]]
            ),
            "natural_audit": natural_audit,
            "donor": {
                "mapping_position": mapping_position,
                "donor_key": donor_material["donor_key"],
                "candidate_u": donor_material["candidate_u"],
                "candidate_z": donor_material["candidate_z"],
                "candidate_digest": donor_material["candidate_digest"],
            },
            "executed_branch_evidence": expected_branch_evidence,
            "rng_bindings": rng_bindings,
            "stream_consumption": {
                branch: {
                    name: benchmark_runner._expected_audit_stream_consumption(
                        stream=name,
                        start_state=start_states[name],
                        schedule=[],
                        seed=int(seed_map[name]),
                        env_index=record["env_index"],
                    )
                    for name in benchmark_runner.CAUSAL_AUDIT_STREAM_NAMES
                }
                for branch in CAUSAL_AUDIT_BRANCHES
            },
            "end_rng_digests": {
                name: _digest_json(start_states[name]) for name in RNG_NAMES
            },
        }
        if status == "complete":
            outcomes = {
                branch: {"utility": float(20 + branch_index)}
                for branch_index, branch in enumerate(CAUSAL_AUDIT_BRANCHES)
            }
            outcomes[natural_branch] = deepcopy(row["natural_outcome"])
            contrasts = benchmark_runner._causal_contrasts(
                record["natural_action"], outcomes,
            )
            row |= {
                "outcomes": outcomes,
                "contrasts": contrasts,
                "contrast_additivity": (
                    benchmark_runner._contrast_additivity_evidence(
                        contrasts, outcomes,
                    )
                ),
            }
        audit_rows.append(row)

    attempted = len(attempted_keys)
    schedule_position = 0
    physical_rows = 0
    branch_calls = 0
    prefix_cells: set[tuple[int, int]] = set()
    while schedule_position < attempted:
        selected_record = records[selected_order[schedule_position]]
        cell = (
            int(selected_record["batch_index"]),
            int(selected_record["time"]),
        )
        chunk_stop = schedule_position
        while (
            chunk_stop < len(selected_order)
            and chunk_stop - schedule_position < 5
            and (
                int(records[selected_order[chunk_stop]]["batch_index"]),
                int(records[selected_order[chunk_stop]]["time"]),
            ) == cell
        ):
            chunk_stop += 1
        physical_rows += chunk_stop - schedule_position
        branch_calls += 1
        prefix_cells.add(cell)
        schedule_position = chunk_stop
    branch_rows = physical_rows * len(CAUSAL_AUDIT_BRANCHES)
    collector_calls = len(prefix_cells) + branch_calls
    artifact = {
        "schema": TYPED_CAUSAL_AUDIT_SCHEMA,
        "status": status,
        "reason_code": (
            "natural_branch_causal_identity_failed"
            if status == "unavailable" else None
        ),
        "replicate": 0,
        "quota_per_action": 2,
        "attempted_rows": attempted,
        "completed_rows": attempted if status == "complete" else attempted - 1,
        "failed_selected_coordinate": (
            None if status == "complete" else list(attempted_keys[-1])
        ),
        "raw_event_trace": [],
        "selected_keys": selected_keys,
        "execution": {
            "engine": "registered_width_batched_causal_audit_v1",
            "registered_width": benchmark_runner.FORMAL_NUM_ENVS,
            "selected_state_count": physical_rows,
            "branch_row_count": branch_rows,
            "padding_row_count": (
                branch_calls * benchmark_runner.FORMAL_NUM_ENVS - branch_rows
            ),
            "collector_call_count": collector_calls,
        },
        "telemetry": {
            "prefix_seconds": 0.0,
            "branch_seconds": 0.0,
            "total_seconds": 0.0,
            "selected_state_count": attempted,
            "collector_call_count": collector_calls,
            "serialized_size_bytes": 0,
        },
        "audit_rows": audit_rows,
    }
    _refresh_lightweight_causal_provenance_size(artifact)
    return {
        "artifact": artifact,
        "episodes": [
            {"episode_id": episode_id, "outcome": deepcopy(outcome)}
            for episode_id, outcome in episode_outcomes.items()
        ],
        "cell_batches": cell_batches,
    }


def _lightweight_causal_provenance_valid(bundle: dict[str, Any]) -> bool:
    return benchmark_runner._causal_audit_valid(
        bundle["artifact"],
        replicate=0,
        episodes=bundle["episodes"],
        cell_batches=bundle["cell_batches"],
        formal=False,
        mode="formal_path_exercise_evaluate",
    )


def test_fixture_light_causal_provenance_complete_path_stays_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _lightweight_causal_provenance_bundle(
        monkeypatch, status="complete",
    )
    assert _lightweight_causal_provenance_valid(bundle)


@pytest.mark.parametrize(
    "mutation",
    (
        "missing_donor",
        "mutated_donor",
        "selected_state_binding",
        "executed_branch_binding",
        "rng_branch_binding",
        "rng_schedule",
        "stream_consumption",
        "end_rng_digest",
        "end_rng_schema",
    ),
)
def test_fixture_light_causal_provenance_unavailable_common_mutations_fail(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    bundle = _lightweight_causal_provenance_bundle(
        monkeypatch, status="unavailable",
    )
    assert _lightweight_causal_provenance_valid(bundle)
    row = bundle["artifact"]["audit_rows"][0]
    if mutation == "missing_donor":
        row.pop("donor")
    elif mutation == "mutated_donor":
        row["donor"]["mapping_position"] += 1
    elif mutation == "selected_state_binding":
        row["executed_branch_evidence"]["selected_state"]["key"] += 1
    elif mutation == "executed_branch_binding":
        row["executed_branch_evidence"]["branch_payload_sha256"][
            "KEEP_HELD_MARK"
        ] = row["executed_branch_evidence"]["branch_payload_sha256"][
            "RENEW_CANDIDATE_MARK"
        ]
    elif mutation == "rng_branch_binding":
        row["rng_bindings"].pop(CAUSAL_AUDIT_BRANCHES[-1])
    elif mutation == "rng_schedule":
        row["rng_bindings"][CAUSAL_AUDIT_BRANCHES[0]][
            RNG_NAMES[0]
        ]["draw_schedule"] = [{"stream": RNG_NAMES[0]}]
    elif mutation == "stream_consumption":
        row["stream_consumption"][CAUSAL_AUDIT_BRANCHES[0]][
            benchmark_runner.CAUSAL_AUDIT_STREAM_NAMES[0]
        ]["position"] += 1
    elif mutation == "end_rng_digest":
        row["end_rng_digests"][RNG_NAMES[0]] = "0" * 64
    else:
        assert mutation == "end_rng_schema"
        row["end_rng_digests"] = []
    _refresh_lightweight_causal_provenance_size(bundle["artifact"])
    assert not _lightweight_causal_provenance_valid(bundle), mutation


@pytest.mark.parametrize(
    "forbidden_key",
    (
        "outcomes",
        "contrasts",
        "contrast_additivity",
        "c_total",
        "c_total_ci",
        "causal_row_count",
        "selector_inputs",
    ),
)
def test_fixture_light_causal_provenance_unavailable_rejects_leakage(
    monkeypatch: pytest.MonkeyPatch, forbidden_key: str,
) -> None:
    bundle = _lightweight_causal_provenance_bundle(
        monkeypatch, status="unavailable",
    )
    assert _lightweight_causal_provenance_valid(bundle)
    bundle["artifact"]["audit_rows"][0][forbidden_key] = {}
    _refresh_lightweight_causal_provenance_size(bundle["artifact"])
    assert not _lightweight_causal_provenance_valid(bundle), forbidden_key


def test_fixture_light_live_unavailable_persists_common_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        benchmark_runner, "CAUSAL_AUDIT_QUOTA_PER_ACTION", 2,
    )
    installed = np.zeros(
        (1, benchmark_runner.FORMAL_NUM_ENVS, 1, MARK_DIM),
        dtype=np.float32,
    )
    candidate_u = np.zeros_like(installed)
    candidate_z = np.zeros_like(installed)
    raw_event_trace = []
    for episode_id in range(4):
        installed[0, episode_id, 0] = float(1 + episode_id)
        candidate_u[0, episode_id, 0] = float(5 + episode_id)
        candidate_z[0, episode_id, 0] = float(9 + episode_id)
        raw_event_trace.append({
            "coordinate": {
                "time": 0,
                "env_index": episode_id,
                "key": 0,
                "membership_epoch": 0,
                "segment_id": 0,
            },
            "natural_kind": KEEP if episode_id < 2 else RENEW,
            "origin_binding": {"episode_id": episode_id},
            "installed_z": benchmark_runner._float32_payload(
                installed[0, episode_id, 0],
            ),
            "candidate_u": benchmark_runner._float32_payload(
                candidate_u[0, episode_id, 0],
            ),
            "candidate_z": benchmark_runner._float32_payload(
                candidate_z[0, episode_id, 0],
            ),
        })
    trajectory = SimpleNamespace(
        raw_event_trace=raw_event_trace,
        event_z_pre=torch.from_numpy(installed),
        candidate_u=torch.from_numpy(candidate_u),
        candidate_z=torch.from_numpy(candidate_z),
        rng_audit={"streams": {name: [] for name in RNG_NAMES}},
    )
    seed_map = authoritative_seed_map("held_out", 0)
    origin = SimpleNamespace(
        rngs={
            name: np.random.default_rng(int(seed_map[name]))
            for name in RNG_NAMES
        },
    )
    end_states = benchmark_runner.owned_rng_states(origin)
    episode_rows = [
        {"episode_id": episode_id, "outcome": {"utility": float(10 + episode_id)}}
        for episode_id in range(4)
    ]
    captured_selected: list[dict[str, Any]] = []

    def unavailable_engine(
        _arm: Any,
        selected: list[dict[str, Any]],
        *,
        device: torch.device,
    ) -> list[dict[str, Any]]:
        assert device.type == "cpu"
        assert len(selected) == 4
        captured_selected.extend(deepcopy(selected))
        first = selected[0]
        audit_id = str(first["audit_id"])
        natural_outcome = deepcopy(episode_rows[first["episode_id"]]["outcome"])
        natural_audit = {
            "status": "unavailable",
            "binding_evidence": {
                "audit_id": audit_id,
                "replicate": 0,
                "batch_index": first["batch_index"],
                "source_episode": first["episode_id"],
                "focal_time": first["time"],
                "source_environment": first["env_index"],
                "focal_key": first["key"],
                "membership_epoch": first["membership_epoch"],
                "segment_id": first["segment_id"],
                "natural_action": first["natural_action"],
                "natural_branch": "KEEP_HELD_MARK",
            },
        }
        rng_material = {
            name: {
                "start_state": deepcopy(end_states[name]),
                "draw_schedule": [],
                "end_state": deepcopy(end_states[name]),
            }
            for name in RNG_NAMES
        }
        stream_consumption = {
            name: benchmark_runner._expected_audit_stream_consumption(
                stream=name,
                start_state=end_states[name],
                schedule=[],
                seed=int(seed_map[name]),
                env_index=first["env_index"],
            )
            for name in benchmark_runner.CAUSAL_AUDIT_STREAM_NAMES
        }
        donor_binding_material = {
            "recipient_key": deepcopy(first["recipient_key"]),
            "donor_key": deepcopy(first["donor_key"]),
            "mapping_position": first["mapping_position"],
            "candidate_u": deepcopy(first["donor_candidate_u"]),
            "candidate_z": deepcopy(first["donor_candidate_z"]),
            "candidate_digest": _digest_json({
                "candidate_u": first["donor_candidate_u"],
                "candidate_z": first["donor_candidate_z"],
            }),
            "binding": deepcopy(first["donor_binding"]),
        }
        return [{
            "audit_id": audit_id,
            "natural_action": first["natural_action"],
            "natural_branch": "KEEP_HELD_MARK",
            "natural_audit": natural_audit,
            "branch_outcomes": {
                branch: deepcopy(natural_outcome)
                for branch in CAUSAL_AUDIT_BRANCHES
            },
            "donor_binding_material": donor_binding_material,
            "selected_state": deepcopy(first["selected_state"]),
            "rng_binding_material": rng_material,
            "end_rng_states": deepcopy(end_states),
            "branches": {
                branch: {
                    "stream_consumption": deepcopy(stream_consumption),
                }
                for branch in CAUSAL_AUDIT_BRANCHES
            },
            "telemetry": {
                "prefix_seconds": 0.0,
                "branch_seconds": 0.0,
                "total_seconds": 0.0,
                "selected_state_count": 1,
                "physical_selected_state_count": len(selected),
                "padding_row_count": (
                    benchmark_runner.FORMAL_NUM_ENVS
                    - len(selected) * len(CAUSAL_AUDIT_BRANCHES)
                ),
                "collector_call_count": 2,
            },
        }]

    monkeypatch.setattr(
        benchmark_runner, "audit_opportunities_batched", unavailable_engine,
    )
    monkeypatch.setattr(
        benchmark_runner,
        "validate_typed_natural_audit",
        lambda audit: audit.get("status") == "unavailable",
    )
    monkeypatch.setattr(
        benchmark_runner,
        "_tracking_outcome_record",
        lambda outcome: deepcopy(outcome),
    )
    artifact = benchmark_runner._collect_causal_audit_evidence(
        object(),
        replicate=0,
        batches=[(trajectory, origin, end_states)],
        episode_rows=episode_rows,
        device=torch.device("cpu"),
        formal=False,
        mode="formal_path_exercise_evaluate",
    )

    assert artifact["status"] == "unavailable"
    assert artifact["attempted_rows"] == 1
    assert artifact["completed_rows"] == 0
    assert len(captured_selected) == 4
    assert len(artifact["audit_rows"]) == 1
    row = artifact["audit_rows"][0]
    assert set(row) == set(benchmark_runner._CAUSAL_AUDIT_COMMON_ROW_KEYS)
    assert benchmark_runner._CAUSAL_AUDIT_COMPLETE_ONLY_ROW_KEYS.isdisjoint(row)
    assert {
        "c_total", "c_total_ci", "causal_row_count", "selector_inputs",
    }.isdisjoint(row)
    assert row["natural_outcome"] == episode_rows[0]["outcome"]
    assert row["natural_audit"]["status"] == "unavailable"
    assert row["donor"]["donor_key"] == captured_selected[0]["donor_key"]
    assert (
        row["executed_branch_evidence"]["selected_state"]
        == captured_selected[0]["selected_state"]
    )
    assert tuple(row["rng_bindings"]) == CAUSAL_AUDIT_BRANCHES
    assert tuple(row["stream_consumption"]) == CAUSAL_AUDIT_BRANCHES
    assert set(row["end_rng_digests"]) == set(RNG_NAMES)


@pytest.fixture(scope="module")
def causal_audit_artifact_bundle(
    causal_audit_oracle_bundle: dict[str, Any],
) -> dict[str, Any]:
    source = causal_audit_oracle_bundle
    episode_rows: list[dict[str, Any]] = []
    cell_batches: list[dict[str, Any]] = []
    audit_batches: list[tuple[Any, Any, Any]] = []
    for batch_index, (trajectory, origin, end_state) in enumerate(zip(
        source["trajectories"], source["origins"], source["end_states"], strict=True,
    )):
        rows, _counts = benchmark_runner._trajectory_episode_rows(
            trajectory, source["arm"], compute_intervention=False,
        )
        episode_rows.extend(rows)
        cell_batches.append({
            "episode_ids": list(trajectory.ledger_ids),
            "rng_evidence": deepcopy(trajectory.rng_audit),
            "rng_bindings": benchmark_runner._collection_rng_bindings(
                context={
                    "domain": "evaluation",
                    "mode": "formal_path_exercise_evaluate",
                    "formal": False,
                    "replicate": 0,
                    "arm": "EHC",
                    "cell": "held_out_stochastic",
                    "batch": batch_index,
                },
                seed_map=origin.seed_map,
                start_states=event_held_commitment_link.owned_rng_states(origin),
                end_states=end_state,
                trajectory=trajectory,
                deterministic=False,
            ),
            "raw_event_trace_binding": {
                "row_count": len(trajectory.raw_event_trace),
                "trace_sha256": _digest_json(list(trajectory.raw_event_trace)),
            },
        })
        audit_batches.append((trajectory, origin, end_state))

    captured: list[list[dict[str, Any]]] = []
    original = benchmark_runner.audit_opportunities_batched

    def capture_engine(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        result = original(*args, **kwargs)
        captured.append(deepcopy(result))
        return result

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(benchmark_runner, "audit_opportunities_batched", capture_engine)
        artifact = benchmark_runner._collect_causal_audit_evidence(
            source["arm"], replicate=0, batches=audit_batches,
            episode_rows=episode_rows, device=next(source["arm"].parameters()).device,
            formal=False, mode="formal_path_exercise_evaluate",
        )
    assert len(captured) == 1
    assert benchmark_runner._causal_audit_valid(
        artifact, replicate=0, episodes=episode_rows, cell_batches=cell_batches,
        formal=False, mode="formal_path_exercise_evaluate",
    )
    return {
        "artifact": artifact,
        "cell_batches": cell_batches,
        "audit_batches": audit_batches,
        "episode_rows": episode_rows,
        "engine_results": captured[0],
        "arm": source["arm"],
    }


def _replace_trace_payload_and_resign(
    artifact: dict[str, Any], cell_batches: list[dict[str, Any]],
    *, key: tuple[Any, ...], field: str,
) -> None:
    target_entry = next(
        entry for entry in artifact["raw_event_trace"]
        if (
            0,
            cell_batches[entry["batch_index"]]["episode_ids"][
                entry["row"]["coordinate"]["env_index"]
            ] // 2,
            cell_batches[entry["batch_index"]]["episode_ids"][
                entry["row"]["coordinate"]["env_index"]
            ] & 1,
            entry["row"]["coordinate"]["time"],
            entry["row"]["coordinate"]["key"],
            entry["row"]["coordinate"]["membership_epoch"],
            entry["row"]["coordinate"]["segment_id"],
            "KEEP" if entry["row"]["natural_kind"] == KEEP else "RENEW",
        ) == key
    )
    payload = target_entry["row"][field]
    values = np.frombuffer(
        base64.b64decode(payload["bytes_b64"], validate=True), dtype=np.float32,
    ).copy()
    values[0] = np.nextafter(values[0], np.float32(np.inf), dtype=np.float32)
    target_entry["row"][field] = benchmark_runner._float32_payload(values)
    origin = target_entry["row"]["origin_binding"]
    unsigned = deepcopy(target_entry["row"])
    unsigned["origin_binding"] = {
        name: value for name, value in origin.items() if name != "binding_digest"
    }
    encoded = json.dumps(
        unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")
    origin["binding_digest"] = hashlib.sha256(
        b"HMASD_RAW_EVENT_TRACE_V1\0" + encoded
    ).hexdigest()
    batch_index = target_entry["batch_index"]
    batch_rows = [
        entry["row"] for entry in artifact["raw_event_trace"]
        if entry["batch_index"] == batch_index
    ]
    cell_batches[batch_index]["raw_event_trace_binding"] = {
        "row_count": len(batch_rows), "trace_sha256": _digest_json(batch_rows),
    }


def _rederive_causal_payload_records(
    artifact: dict[str, Any], cell_batches: list[dict[str, Any]],
) -> None:
    inventory = benchmark_runner._causal_audit_trace_inventory(
        artifact["raw_event_trace"], replicate=0, cell_batches=cell_batches,
    )
    assert inventory is not None
    donor_by_key: dict[tuple[Any, ...], tuple[int, dict[str, Any]]] = {}
    records: dict[tuple[Any, ...], dict[str, Any]] = {}
    for action in CAUSAL_AUDIT_NATURAL_ACTIONS:
        lookup = {
            benchmark_runner._causal_audit_key(row): row for row in inventory[action]
        }
        chosen = [lookup[tuple(key)] for key in artifact["selected_keys"][action]]
        chosen.sort(key=benchmark_runner._causal_audit_key)
        for position, recipient in enumerate(chosen):
            recipient_key = benchmark_runner._causal_audit_key(recipient)
            records[recipient_key] = recipient
            donor_by_key[recipient_key] = (position, chosen[(position + 1) % len(chosen)])
    for row in artifact["audit_rows"]:
        key = benchmark_runner._causal_audit_key(row)
        position, donor = donor_by_key[key]
        material = benchmark_runner._causal_audit_donor_material(
            records[key], donor, position,
        )
        row["donor"] = {
            "mapping_position": position,
            "donor_key": material["donor_key"],
            "candidate_u": material["candidate_u"],
            "candidate_z": material["candidate_z"],
            "candidate_digest": material["candidate_digest"],
        }
        row["executed_branch_evidence"] = benchmark_runner._causal_audit_branch_evidence(
            records[key], donor, position,
        )
    artifact["telemetry"]["serialized_size_bytes"] = len(json.dumps(
        {"raw_event_trace": artifact["raw_event_trace"],
         "audit_rows": artifact["audit_rows"]},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8"))


def test_trace_inventory_and_coherently_resigned_tampering_fail_closed(
    causal_audit_oracle_bundle: dict[str, Any],
) -> None:
    raw, batches = _trace_inventory_inputs(causal_audit_oracle_bundle)
    inventory = benchmark_runner._causal_audit_trace_inventory(
        raw, replicate=0, cell_batches=batches
    )
    assert inventory is not None
    assert all(inventory[action] for action in CAUSAL_AUDIT_NATURAL_ACTIONS)

    duplicated = deepcopy(raw)
    duplicated.append(deepcopy(duplicated[0]))
    batch_index = duplicated[0]["batch_index"]
    rows = [entry["row"] for entry in duplicated if entry["batch_index"] == batch_index]
    duplicated_batches = deepcopy(batches)
    duplicated_batches[batch_index]["raw_event_trace_binding"] = {
        "row_count": len(rows), "trace_sha256": _digest_json(rows),
    }
    assert benchmark_runner._causal_audit_trace_inventory(
        duplicated, replicate=0, cell_batches=duplicated_batches
    ) is None

    rebound = deepcopy(raw)
    target = rebound[0]["row"]
    target["origin_binding"]["episode_id"] += 1
    unsigned = deepcopy(target)
    unsigned["origin_binding"].pop("binding_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    target["origin_binding"]["binding_digest"] = hashlib.sha256(
        b"HMASD_RAW_EVENT_TRACE_V1\0" + encoded
    ).hexdigest()
    rebound_batches = deepcopy(batches)
    rows = [entry["row"] for entry in rebound if entry["batch_index"] == batch_index]
    rebound_batches[batch_index]["raw_event_trace_binding"] = {
        "row_count": len(rows), "trace_sha256": _digest_json(rows),
    }
    assert benchmark_runner._causal_audit_trace_inventory(
        rebound, replicate=0, cell_batches=rebound_batches
    ) is None


def test_tracking_outcome_recomputation_rejects_utility_outcome_cotampering(
    causal_audit_oracle_bundle: dict[str, Any],
) -> None:
    outcome = causal_audit_oracle_bundle["batched"][0]["branch_outcomes"][
        CAUSAL_AUDIT_BRANCHES[0]
    ]
    clean = benchmark_runner._tracking_outcome_record(outcome)
    assert benchmark_runner._tracking_outcome_valid(clean)
    for field in (
        "tracking", "completion", "utility", "terminal_reward",
        "tracking_quarter_units", "active_rows", "completed_segments",
        "eligible_segments", "roster_sizes", "reward_trace",
    ):
        mutated = deepcopy(clean)
        if field == "roster_sizes":
            mutated[field][0] = -1
        elif isinstance(mutated[field], list):
            mutated[field][-1] = mutated[field][-1] + 1
        else:
            mutated[field] = mutated[field] + 1
        assert not benchmark_runner._tracking_outcome_valid(mutated), field
    cotampered = deepcopy(clean)
    cotampered["utility"] += 0.125
    cotampered["terminal_reward"] = cotampered["utility"]
    cotampered["reward_trace"][-1] = cotampered["utility"]
    assert not benchmark_runner._tracking_outcome_valid(cotampered)

    coordinated = deepcopy(clean)
    coordinated["tracking_quarter_units"] *= 2
    coordinated["active_rows"] *= 2
    assert (
        coordinated["tracking_quarter_units"]
        / (4.0 * coordinated["active_rows"])
        == clean["tracking"]
    )
    assert not benchmark_runner._tracking_outcome_valid(coordinated)


@pytest.mark.parametrize("field", ["installed_z", "candidate_u"])
def test_coherent_selected_and_donor_payload_redigests_retain_old_rng_and_fail(
    causal_audit_artifact_bundle: dict[str, Any], field: str,
) -> None:
    artifact = deepcopy(causal_audit_artifact_bundle["artifact"])
    cell_batches = deepcopy(causal_audit_artifact_bundle["cell_batches"])
    if field == "installed_z":
        target_key = tuple(artifact["selected_keys"]["KEEP"][0])
        affected_row = next(
            row for row in artifact["audit_rows"]
            if benchmark_runner._causal_audit_key(row) == target_key
        )
    else:
        target_key = tuple(artifact["audit_rows"][0]["donor"]["donor_key"])
        affected_row = artifact["audit_rows"][0]
    old_context_digest = affected_row["rng_bindings"][
        CAUSAL_AUDIT_BRANCHES[0]
    ][RNG_NAMES[0]]["context"]["executed_branch_evidence_digest"]
    _replace_trace_payload_and_resign(
        artifact, cell_batches, key=target_key, field=field,
    )
    _rederive_causal_payload_records(artifact, cell_batches)
    changed_row = next(
        row for row in artifact["audit_rows"]
        if benchmark_runner._causal_audit_key(row)
        == benchmark_runner._causal_audit_key(affected_row)
    )
    assert old_context_digest != _digest_json(changed_row["executed_branch_evidence"])
    assert not benchmark_runner._causal_audit_valid(
        artifact, replicate=0,
        episodes=causal_audit_artifact_bundle["episode_rows"],
        cell_batches=cell_batches, formal=False,
        mode="formal_path_exercise_evaluate",
    )


def test_runner_collector_call_telemetry_is_rederived_for_lazy_recurrence() -> None:
    selected_cells = (
        [(0, 4)] * 6
        + [(1, 2)] * 3
        + [(0, 4)] * 2
        + [(2, 1)]
    )
    selected_rows = [
        {"batch_index": batch_index, "time": time}
        for batch_index, time in selected_cells
    ]
    expected_collector_calls = 6
    clean = [
        {"telemetry": {"collector_call_count": expected_collector_calls}}
        for _ in range(10)
    ]
    assert benchmark_runner._validated_causal_audit_collector_call_count(
        selected_rows, clean,
    ) == expected_collector_calls

    forged = deepcopy(clean)
    for result in forged:
        result["telemetry"]["collector_call_count"] += 1
    disagreeing = deepcopy(clean)
    disagreeing[-1]["telemetry"]["collector_call_count"] += 1
    for mutated in (forged, disagreeing):
        with pytest.raises(
            RuntimeError, match="collector-call telemetry mismatch",
        ):
            benchmark_runner._validated_causal_audit_collector_call_count(
                selected_rows, mutated,
            )


def test_engine_reported_collector_count_mismatch_fails_before_publication(
    causal_audit_artifact_bundle: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
) -> None:
    stale = deepcopy(causal_audit_artifact_bundle["engine_results"])
    for result in stale:
        result["telemetry"]["collector_call_count"] += 1
    monkeypatch.setattr(
        benchmark_runner, "audit_opportunities_batched",
        lambda *_args, **_kwargs: deepcopy(stale),
    )
    with pytest.raises(RuntimeError, match="collector-call telemetry mismatch"):
        benchmark_runner._collect_causal_audit_evidence(
            causal_audit_artifact_bundle["arm"], replicate=0,
            batches=causal_audit_artifact_bundle["audit_batches"],
            episode_rows=causal_audit_artifact_bundle["episode_rows"],
            device=next(causal_audit_artifact_bundle["arm"].parameters()).device,
            formal=False, mode="formal_path_exercise_evaluate",
        )


_BRANCH_ORDER = (
    "INVALID_OPERATIONAL",
    "BENCHMARK_NON_IDENTIFIABLE",
    "NO_ACCESS_THIS_BENCHMARK",
    "UNDERPOWERED_ACCESS",
    "COMMITMENT_SUPPORTED",
    "REPRESENTATION_ONLY",
    "ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED",
    "MIXED_UNDERPOWERED",
)


def _independent_branch_predicates(inputs: dict[str, Any]) -> dict[str, bool]:
    """The eight branch conditions, written out from the registered
    precedence list rather than read back from the implementation."""

    utility = inputs["utility_ci"]
    k_bins = inputs["k_bin_cis"]
    intervention = inputs["intervention_ci"]
    gain = inputs["g_ci"]
    keep_lcb, keep_ucb = inputs["c_total_keep_ci"]
    renew_lcb, renew_ucb = inputs["c_total_renew_ci"]
    access_established = (
        max(interval[1] for interval in utility.values()) >= ACCESS_FLOOR
        and max(interval[0] for interval in utility.values()) >= ACCESS_FLOOR
    )
    passes = (
        sum(ci[0] > LIFETIME_BIN_THRESHOLD for ci in k_bins) >= 2
        and intervention[0] > INTERVENTION_THRESHOLD
        and keep_lcb > C_TOTAL_KEEP_LCB_FLOOR
        and renew_lcb > C_TOTAL_RENEW_LCB_FLOOR
        and inputs["c_total_keep_mean"] >= C_TOTAL_KEEP_MEAN_FLOOR
        and inputs["c_total_renew_mean"] >= C_TOTAL_RENEW_MEAN_FLOOR
    )
    confidently_fails = (
        sum(ci[1] > LIFETIME_BIN_THRESHOLD for ci in k_bins) < 2
        or intervention[1] <= INTERVENTION_THRESHOLD
        or keep_ucb <= C_TOTAL_KEEP_LCB_FLOOR
        or renew_ucb <= C_TOTAL_RENEW_LCB_FLOOR
    )
    return {
        "INVALID_OPERATIONAL": not inputs["operational_valid"],
        "BENCHMARK_NON_IDENTIFIABLE": (
            inputs["non_create_opportunities"] < 1000
            or inputs["multi_opportunity_lifecycles"] < 250
            or inputs["eligible_keep_rows"] < SUPPORT_FLOOR
            or inputs["eligible_renew_rows"] < SUPPORT_FLOOR
            or min(inputs["causal_keep_rows_by_replicate"])
            < CAUSAL_AUDIT_QUOTA_PER_ACTION
            or min(inputs["causal_renew_rows_by_replicate"])
            < CAUSAL_AUDIT_QUOTA_PER_ACTION
        ),
        "NO_ACCESS_THIS_BENCHMARK": (
            max(interval[1] for interval in utility.values()) < ACCESS_FLOOR
        ),
        "UNDERPOWERED_ACCESS": (
            max(interval[0] for interval in utility.values()) < ACCESS_FLOOR
        ),
        "COMMITMENT_SUPPORTED": (
            access_established and gain[0] > GAIN_THRESHOLD and passes
        ),
        "REPRESENTATION_ONLY": (
            access_established and gain[0] > GAIN_THRESHOLD and confidently_fails
        ),
        "ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED": gain[1] <= GAIN_THRESHOLD,
        "MIXED_UNDERPOWERED": True,
    }


def test_eight_branches_mutually_exclusive_under_first_match() -> None:
    """Over a grid that includes every registered equality boundary, the
    selector returns exactly the first satisfied branch of the eight.

    Two things are checked together: the returned branch's own condition
    holds, and no earlier branch's condition holds. That is what "mutually
    exclusive under first-match precedence" means operationally -- a later
    branch is only reachable when every earlier one is false.
    """

    import itertools

    base = _branch_inputs()
    quota = CAUSAL_AUDIT_QUOTA_PER_ACTION
    late_axes = {
        "g_ci": ((0.11, 0.15), (GAIN_THRESHOLD, 0.15), (0.0, GAIN_THRESHOLD), (0.05, 0.11)),
        "k_bin_cis": (
            ((0.11, 0.20), (0.11, 0.20), (0.05, 0.09)),
            ((0.01, 0.05), (0.01, LIFETIME_BIN_THRESHOLD), (0.11, 0.20)),
            ((LIFETIME_BIN_THRESHOLD, 0.20), (0.11, 0.20), (0.05, 0.09)),
        ),
        "intervention_ci": (
            (0.11, 0.20),
            (0.05, INTERVENTION_THRESHOLD),
            (INTERVENTION_THRESHOLD, 0.20),
        ),
        "c_total_keep_ci": ((0.03, 0.09), (C_TOTAL_KEEP_LCB_FLOOR, 0.09), (-0.05, C_TOTAL_KEEP_LCB_FLOOR)),
        "c_total_renew_ci": ((0.03, 0.09), (C_TOTAL_RENEW_LCB_FLOOR, 0.09), (-0.05, C_TOTAL_RENEW_LCB_FLOOR)),
        "c_total_keep_mean": (0.06, C_TOTAL_KEEP_MEAN_FLOOR, C_TOTAL_KEEP_MEAN_FLOOR - 0.001),
    }
    early_axes = {
        "operational_valid": (True, False),
        "non_create_opportunities": (1000, 999),
        "multi_opportunity_lifecycles": (250, 249),
        "eligible_keep_rows": (SUPPORT_FLOOR, SUPPORT_FLOOR - 1),
        "eligible_renew_rows": (SUPPORT_FLOOR, SUPPORT_FLOOR - 1),
        "causal_keep_rows_by_replicate": (
            (quota,) * CAUSAL_AUDIT_REPLICATES,
            (quota, quota, quota - 1, quota, quota),
        ),
        "causal_renew_rows_by_replicate": (
            (quota,) * CAUSAL_AUDIT_REPLICATES,
            (quota - 1,) + (quota,) * (CAUSAL_AUDIT_REPLICATES - 1),
        ),
        "utility_ci": (
            {"OR": (0.79, 0.81), "DUM": (0.79, 0.81), "EHC": (0.80, 0.84)},
            {"OR": (0.1, ACCESS_FLOOR - 1e-6), "DUM": (0.1, 0.7), "EHC": (0.1, 0.7)},
            {"OR": (0.7, ACCESS_FLOOR), "DUM": (0.7, 0.8), "EHC": (0.7, 0.8)},
        ),
    }

    def grid(axes: dict[str, Any]) -> list[dict[str, Any]]:
        names = tuple(axes)
        return [
            base | dict(zip(names, combination))
            for combination in itertools.product(*(axes[name] for name in names))
        ]

    cases = grid(late_axes) + grid(early_axes)
    assert len(cases) > 1000
    seen: set[str] = set()
    for inputs in cases:
        predicates = _independent_branch_predicates(inputs)
        assert set(predicates) == set(_BRANCH_ORDER)
        expected = next(name for name in _BRANCH_ORDER if predicates[name])
        branch = select_result_branch(**inputs)
        assert branch == expected, inputs
        # Nothing earlier in the precedence may also be satisfied.
        assert not any(
            predicates[name]
            for name in _BRANCH_ORDER[: _BRANCH_ORDER.index(branch)]
        ), inputs
        seen.add(branch)
    # A grid that never reaches a branch would prove nothing about it.
    assert seen == set(_BRANCH_ORDER)


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
    device: torch.device,
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

    arms, _, _ = initialize_arms(device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(arm, state, device=device)
    assert trajectory.active_mask.shape[1] == 16
    replay = replay_trajectory(arm, trajectory, device=device)
    joints = replay_joint_bounds(replay, trajectory)

    unit_roundoff = 2.0**-24
    assert FLOAT32_UNIT_ROUNDOFF == unit_roundoff
    contract_block = registered_contract()["replay_tolerances"]
    assert contract_block["float32_unit_roundoff"] == unit_roundoff
    assert contract_block["event_joint_factor_count"] == EVENT_JOINT_FACTOR_COUNT == 9
    gamma_nine = 9.0 * unit_roundoff / (1.0 - 9.0 * unit_roundoff)
    assert float32_reduction_gamma(9.0) == gamma_nine
    assert gamma_nine == pytest.approx(5.36442090748478e-07, rel=1e-12)

    stored, replayed, rows = _event_factor_tensors(replay, trajectory, device)
    assert bool(rows.any())
    error = (
        replay.event_joint_logp - trajectory.event_old_joint_logp.to(device)
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

    active = trajectory.active_mask.to(device)
    stored_logp = trajectory.old_log_probs.to(device)
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
    device: torch.device,
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

    arms, _, _ = initialize_arms(device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(arm, state, device=device)
    replay = replay_trajectory(arm, trajectory, device=device)
    assert replay_report(replay, trajectory)["passed"]
    index = _first_renew_index(trajectory)
    defect = 2e-6

    inputs = trajectory.event_inputs[index].unsqueeze(0).to(device)
    u_row = trajectory.event_u[index].unsqueeze(0).to(device)
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
        atol=REPLAY_LOG_COMPONENT_ATOL,
        rtol=REPLAY_LOG_COMPONENT_RTOL,
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
        corrupted_replay = replay_trajectory(arm, corrupted, device=device)
        report = replay_report(corrupted_replay, corrupted)
        assert not report["passed"], label
        assert expected_field[label] in report["failures"], label
        likelihood = report["likelihood_components"][expected_field[label]]
        assert (
            likelihood["absolute_error"] > likelihood["mixed_bound"]
            or likelihood["ratio_drift"] > REPLAY_LOG_RATIO_DRIFT_CAP
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
            validate_replay(arm, corrupted, device=device)


def test_independent_float64_transformed_density_and_mutations(
    device: torch.device,
) -> None:
    # Deterministic saturated tails, independent of model weights and sampled
    # trajectories. Both signs are present in every coordinate pair and the
    # reference uses logaddexp rather than the production softplus identity.
    u_tail = torch.tensor(
        [[-20.0, 20.0, -24.0, 24.0, -28.0, 28.0, -32.0, 32.0]],
        dtype=torch.float64, device=device,
    )
    mu_tail = torch.tensor(
        [[-0.4, 0.3, -0.2, 0.1, 0.0, -0.1, 0.2, -0.3]],
        dtype=torch.float64, device=device,
    )
    sigma_tail = torch.tensor(
        [[0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 0.25]],
        dtype=torch.float64, device=device,
    )
    independent_normal = (
        -0.5 * ((u_tail - mu_tail) / sigma_tail).square()
        - sigma_tail.log()
        - 0.5 * math.log(2.0 * math.pi)
    )
    independent_jacobian = 2.0 * (
        math.log(2.0) - u_tail
        - torch.logaddexp(torch.zeros_like(u_tail), -2.0 * u_tail)
    )
    independent_density = independent_normal - independent_jacobian
    production_density = transformed_mark_component_logp(
        u_tail, mu_tail, sigma_tail
    )
    tail_error = (production_density - independent_density).abs()
    tail_bound = REPLAY_LOG_COMPONENT_ATOL + REPLAY_LOG_COMPONENT_RTOL * torch.maximum(
        production_density.abs(), independent_density.abs()
    )
    tail_ratio = torch.expm1(tail_error)
    assert bool((tail_error <= tail_bound).all())
    assert bool((tail_ratio <= REPLAY_LOG_RATIO_DRIFT_CAP).all())
    assert torch.equal(torch.tanh(u_tail), torch.sign(u_tail))
    missing_tail = independent_density.clone()
    missing_tail[0, 0] = 0.0
    for label, mutation in (
        ("tail_omitted_jacobian", independent_normal),
        ("tail_reversed_jacobian", independent_normal + independent_jacobian),
        ("tail_missing_component", missing_tail),
    ):
        mutation_error = (mutation - production_density).abs()
        mutation_bound = REPLAY_LOG_COMPONENT_ATOL + REPLAY_LOG_COMPONENT_RTOL * torch.maximum(
            mutation.abs(), production_density.abs()
        )
        mutation_ratio = torch.expm1(torch.clamp(mutation_error, max=80.0))
        assert bool(
            ((mutation_error > mutation_bound)
             | (mutation_ratio > REPLAY_LOG_RATIO_DRIFT_CAP)).any()
        ), label

    arms, _, _ = initialize_arms(device)
    arm = arms["EHC"]
    trajectory = collect_trajectory(
        arm, make_training_state("EHC", 0), device=device
    )
    rows = torch.nonzero(
        trajectory.event_kind.eq(RENEW), as_tuple=False
    )
    assert len(rows) >= 2
    magnitudes = torch.stack([
        trajectory.event_u[tuple(index)].abs().max() for index in rows
    ])
    chosen = (rows[int(torch.argmin(magnitudes))], rows[int(torch.argmax(magnitudes))])
    references: list[tuple[tuple[int, ...], torch.Tensor, torch.Tensor, torch.Tensor]] = []
    with torch.no_grad():
        for index_tensor in chosen:
            index = tuple(int(value) for value in index_tensor)
            inputs = trajectory.event_inputs[index].unsqueeze(0).to(device)
            u64 = trajectory.event_u[index].unsqueeze(0).to(device).double()
            mu32, sigma32 = _normal_parameters(arm.mark_head(inputs))
            mu64, sigma64 = mu32.double(), sigma32.double()
            normal64 = (
                -0.5 * torch.square((u64 - mu64) / sigma64)
                - torch.log(sigma64)
                - 0.5 * math.log(2.0 * math.pi)
            )
            log_jacobian64 = 2.0 * (
                math.log(2.0) - u64 - torch.log1p(torch.exp(-2.0 * u64))
            )
            density64 = normal64 - log_jacobian64
            stored64 = trajectory.event_old_mark_component_logp[index].double()
            assert torch.allclose(stored64, density64[0], atol=2e-6, rtol=1e-6)
            references.append((index, density64[0], normal64[0], log_jacobian64[0]))

    index, density64, normal64, log_jacobian64 = references[1]
    assert float(log_jacobian64.abs().max()) > 1e-3
    missing = density64.clone()
    missing[0] = 0.0
    for label, mutated64 in (
        ("omitted_jacobian", normal64),
        ("reversed_jacobian", normal64 + log_jacobian64),
        ("missing_component", missing),
    ):
        corrupted = _restated_event_factors(
            trajectory, index=index, marks=mutated64.float()
        )
        report = replay_report(
            replay_trajectory(arm, corrupted, device=device), corrupted
        )
        assert not report["passed"], label
        assert "mark_component" in report["failures"], label

    wrong_mask = trajectory.event_mark_mask.clone()
    wrong_mask[index] = False
    corrupted_mask = replace(trajectory, event_mark_mask=wrong_mask)
    report = replay_report(
        replay_trajectory(arm, corrupted_mask, device=device), corrupted_mask
    )
    assert not report["passed"]
    assert "mask_mismatch" in report["failures"]


def test_joint_rule_admits_accumulation_and_rejects_a_joint_defect(
    device: torch.device,
) -> None:
    """Accumulation across nine factors passes; a joint defect does not.

    First case: every one of the nine factors on a RENEW row is displaced
    by `4e-7`, which stacks across the row while still leaving every component
    inside the unchanged `1e-6` bound, and the
    recorded joint is reassembled from them. Their sum then exceeds `1e-6`
    -- exactly the situation the old single scalar declared a failure. It
    must pass, and the measured numbers here prove the joint really did
    exceed `1e-6` rather than the test asserting a vacuous inequality.

    Second case: the recorded joint alone is displaced past its
    compositional bound while every factor stays clean. It must raise, and
    it must raise on the joint rather than on any component.
    """

    arms, _, _ = initialize_arms(device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(arm, state, device=device)
    index = _first_renew_index(trajectory)
    displacement = 4e-7

    accumulated = _restated_event_factors(
        trajectory,
        index=index,
        categorical=trajectory.event_old_cat_logp[index] - displacement,
        marks=trajectory.event_old_mark_component_logp[index] - displacement,
    )
    accumulated_replay = replay_trajectory(arm, accumulated, device=device)
    report = replay_report(accumulated_replay, accumulated)
    assert report["passed"], report["failures"]
    assert all(report["errors"][name] <= REPLAY_STATE_ATOL for name in REPLAY_STATE_FIELDS)
    assert all(
        report["likelihood_components"][name]["absolute_error"]
        <= report["likelihood_components"][name]["mixed_bound"]
        for name in REPLAY_LOG_COMPONENT_FIELDS
    )
    assert report["errors"]["event_joint"] > 1e-6
    assert report["errors"]["event_joint"] <= report["joints"]["event_joint"]["bound"]
    assert report["joints"]["event_joint"]["excess"] < 0.0
    assert report["joints"]["event_joint"]["assembly_excess"] < 0.0
    # It is the nine-way accumulation, not one large factor, that carries
        # the joint past `1e-6`: no single component exceeds half the joint error.
    assert (
        report["errors"]["event_joint"]
        >= 2.0 * max(report["errors"][name] for name in REPLAY_LOG_COMPONENT_FIELDS)
    )

    over_bound = trajectory.event_old_joint_logp.clone()
    over_bound[index] = over_bound[index] - 5e-5
    defective = replace(trajectory, event_old_joint_logp=over_bound)
    defective_replay = replay_trajectory(arm, defective, device=device)
    defective_report = replay_report(defective_replay, defective)
    assert not defective_report["passed"]
    assert "event_joint" in defective_report["failures"]
    assert defective_report["joints"]["event_joint"]["excess"] > 0.0
    assert all(
        defective_report["errors"][name] <= REPLAY_STATE_ATOL
        for name in REPLAY_STATE_FIELDS
    )
    assert all(
        defective_report["likelihood_components"][name]["absolute_error"]
        <= defective_report["likelihood_components"][name]["mixed_bound"]
        for name in REPLAY_LOG_COMPONENT_FIELDS
    )
    # A joint that is no longer the sum of its own recorded factors is
    # caught by the float64 assembly check as well, independently of the
    # size of the displacement.
    assert "event_joint_assembly" in defective_report["failures"]
    with pytest.raises(RuntimeError, match="event_joint"):
        validate_replay(arm, defective, device=device)


def test_registered_contract_replay_block_and_checkpoint_strictness(
    device: torch.device, tmp_path: Any
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
    assert block["log_component_fields"] == list(REPLAY_LOG_COMPONENT_FIELDS)
    assert block["state_fields"] == list(REPLAY_STATE_FIELDS)
    assert block["joint_fields"] == list(REPLAY_JOINT_FIELDS)
    assert block["log_component_atol"] == REPLAY_LOG_COMPONENT_ATOL == 1e-6
    assert block["log_component_rtol"] == REPLAY_LOG_COMPONENT_RTOL
    assert block["log_ratio_drift_cap"] == REPLAY_LOG_RATIO_DRIFT_CAP
    assert block["state_atol"] == REPLAY_STATE_ATOL == 1e-6
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
    assert "ratio drift 1e-4" in block["correlated_bias_sensitivity"]
    assert "rows > 0" in block["joint_record_internal_consistency"]
    assert block["non_finite_rule"] == "any_non_finite_leaf_fails_closed"
    # The same-checkpoint continuation invariant is a different quantity and
    # is untouched by the replay correction.
    assert contract["optimization"]["resume_tolerance"] == 1e-7

    arms, base_optimizers, event_optimizers = initialize_arms(device)
    state = make_training_state("EHC", 0)
    path = tmp_path / "contract_strictness.pt"
    save_checkpoint(
        path, arm=arms["EHC"], base_optimizer=base_optimizers["EHC"],
        event_optimizer=event_optimizers["EHC"], state=state,
    )
    loaded_arm, _, _, _ = load_checkpoint(
        path, device=device, expected_arm="EHC", expected_replicate=0
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
            legacy_path, device=device, expected_arm="EHC",
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
    device: torch.device,
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

    arms, _, _ = initialize_arms(device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(arm, state, device=device)
    clean = replay_report(
        replay_trajectory(arm, trajectory, device=device), trajectory
    )
    assert clean["passed"]
    assert clean["errors"]["categorical_support_leak"] == 0.0
    assert clean["errors"]["mark_support_leak"] == 0.0

    for field, leak_name in (
        ("categorical", "categorical_support_leak"),
        ("mark", "mark_support_leak"),
    ):
        corrupted, leaked, rows = _leaked_support_trajectory(
            arm, trajectory, field=field, device=device
        )
        assert float(leaked.abs().max()) > 1e-3, field
        report = replay_report(
            replay_trajectory(arm, corrupted, device=device), corrupted
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
            validate_replay(arm, corrupted, device=device)
        # The other support-leak field is untouched: the two look in
        # different places and neither stands in for the other.
        other = (
            "mark_support_leak" if field == "categorical"
            else "categorical_support_leak"
        )
        assert report["errors"][other] == 0.0, field


def test_replay_reports_and_records_fail_closed_on_non_finite_values(
    device: torch.device,
) -> None:
    """NaN must fail, not pass. `nan > tol` and `nan > 0.0` are both false.

    Written as `not (x <= limit)` throughout, a NaN fails every gate; written
    as `x > limit` it satisfies every one of them, so a live replay producing
    NaN would report `passed: True`. The record validator and the merge are
    held to the same rule -- `max(0.0, nan)` is `0.0` in Python while
    `max(nan, 0.0)` is `nan`, so a plain maximum launders NaN out of the
    evidence depending on batch order.
    """

    arms, _, _ = initialize_arms(device)
    arm = arms["EHC"]
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(arm, state, device=device)
    index = _first_renew_index(trajectory)
    for label, mutation in (
        ("joint", "event_old_joint_logp"),
        ("mark", "event_old_mark_component_logp"),
    ):
        tensor = getattr(trajectory, mutation).clone()
        tensor[index] = float("nan")
        corrupted = replace(trajectory, **{mutation: tensor})
        report = replay_report(
            replay_trajectory(arm, corrupted, device=device), corrupted
        )
        assert not report["passed"], label
        assert any(
            name.startswith("non_finite:") for name in report["failures"]
        ), label
        with pytest.raises(RuntimeError):
            validate_replay(arm, corrupted, device=device)

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


def test_worst_coordinate_and_ulp_evidence_is_strict() -> None:
    clean = _synthetic_replay_record()
    assert _replay_record_valid(clean)
    for mutation in ("ulp", "coordinate", "bound", "ratio"):
        degraded = deepcopy(clean)
        record = degraded["likelihood_components"]["mark_component"]
        if mutation == "ulp":
            record["ulp_distance"] += 1
        elif mutation == "coordinate":
            record["coordinate"] = [0, 0, 0]
        elif mutation == "bound":
            record["mixed_bound"] *= 2.0
        else:
            record["ratio_drift"] = 1e-8
        assert not _replay_record_valid(degraded), mutation

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

    # A serialized component beyond its own mixed bound is rejected even
    # when the separately recorded event joint remains wholly passing.
    component_failure = deepcopy(clean)
    stored = np.float32(1.0)
    replayed = stored
    for _ in range(13):
        replayed = np.nextafter(
            replayed, np.float32(np.inf), dtype=np.float32,
        )
    absolute_error = abs(float(replayed) - float(stored))
    mixed_bound = REPLAY_LOG_COMPONENT_ATOL + REPLAY_LOG_COMPONENT_RTOL * max(
        abs(float(stored)), abs(float(replayed))
    )
    spacing, distance = event_held_commitment_link._float32_ulp_evidence(
        float(stored), float(replayed)
    )
    component_failure["errors"]["mark_component"] = absolute_error
    component_failure["likelihood_components"]["mark_component"] |= {
        "stored_value": float(stored),
        "replayed_value": float(replayed),
        "absolute_error": absolute_error,
        "mixed_bound": mixed_bound,
        "ratio_drift": abs(math.expm1(float(replayed) - float(stored))),
        "float32_ulp_at_max_magnitude": spacing,
        "ulp_distance": distance,
    }
    assert absolute_error > mixed_bound
    assert component_failure["joints"]["event_joint"]["error"] == 0.0
    assert component_failure["joints"]["event_joint"]["excess"] < 0.0
    assert component_failure["joints"]["event_joint"]["assembly_excess"] < 0.0
    assert not _replay_record_valid(component_failure)
