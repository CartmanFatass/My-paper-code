from __future__ import annotations

import json
import math

import pytest
import torch

from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.contracts import (
    ACTION_COUNT,
    AdamWState,
    ContractError,
    FOUNDATION_ACTOR_PARAMETER_COUNT,
    FOUNDATION_CRITIC_PARAMETER_COUNT,
    FOUNDATION_PARAMETER_COUNT,
    FREE_TRAINABLE_PARAMETER_COUNT,
    K_TARGET,
    K_TRAIN,
    SET_TRAINABLE_PARAMETER_COUNT,
    SharedParameterizationContract,
    TREAT_TRAINABLE_PARAMETER_COUNT,
    adamw_step,
    clip_combined_gradient,
    duration_correct_targets,
    four_minibatches,
    inverse_cdf_index,
    optimizer_index_contract,
    ppo_tie_mean_min,
    initialization_schema,
    row_major_xavier_uniform_from_test_uniforms,
    strict_clip,
    three_epoch_permutations,
    validate_foundation_schema,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.controller_conformance import (
    LEXICOGRAPHIC_ACTIONS,
    free_logits,
    graph_slack_scores,
    reversed_compositor,
    set_compositor,
    set_scores,
    strict_containment_witness,
    treat_logits,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.lifecycle import (
    ADAPTER_SLOTS,
    Applicability,
    GateOutcome,
    InferenceBranch,
    InferenceFixture,
    LifecycleError,
    OpportunityExecutionPermit,
    PredicateState,
    RouteState,
    TechnicalFinal,
    exhaustive_first_true_branch,
    issue_opportunity_execution_permit,
    snapshot,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.synthetic_resume import (
    SyntheticFrontier,
    SyntheticResumeError,
    cold_scan_exact_frontier,
    commit_frontier,
    create_only_commit,
    fake_digest,
    require_complete_synthetic_stage,
    write_interrupted_test_fragment,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.host_types import (
    HostOutput,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.native_backend import (
    NativeBatch,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.oracle import (
    test_only_output as _oracle_output,
    test_only_renewal as _oracle_renewal,
    test_only_reset as _oracle_reset,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.opportunity import (
    D_THRESHOLD,
    PAIR_ROLLOUT_COUNT,
    Q_THRESHOLD,
    S_THRESHOLD,
    DisturbanceTape,
    OpportunityContractError,
    OpportunityState,
    PairOpportunityMetrics,
    ReplicateOpportunityMetrics,
    RolloutAddress,
    TapeOutcome,
    aggregate_replicate,
    analyze_gate,
    compute_pair_metrics,
    load_test_only_replicate_inventory,
    load_test_only_complete_opportunity_stage,
    publish_test_only_complete_opportunity_stage,
    publish_test_only_replicate_inventory,
    require_opportunity_lifecycle,
    run_complete_pair,
    resume_test_only_complete_opportunity_stage,
)


def _observation(batch: int = 1) -> torch.Tensor:
    value = torch.zeros((batch, 18), dtype=torch.float32)
    value[:, 17] = 0.0
    return value


def _foundation_finals():
    return tuple(
        TechnicalFinal(index, "FOUNDATION", fake_digest(f"TEST_ONLY:foundation:{index}"))
        for index in range(24)
    )


def _opportunity_permit(*, alternate: bool = False):
    finals = _foundation_finals()
    if alternate:
        finals = (
            TechnicalFinal(0, "FOUNDATION", fake_digest("TEST_ONLY:foundation:alternate")),
            *finals[1:],
        )
    return issue_opportunity_execution_permit(
        snapshot(finals, foundation_gate=GateOutcome.PASS)
    )


def _adapter_finals():
    return tuple(
        TechnicalFinal(index, arm, fake_digest(f"TEST_ONLY:adapter:{index}:{arm}"))
        for index, arm in sorted(ADAPTER_SLOTS)
    )


def _tapes():
    signs = ((1, 1, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1))
    return tuple(
        DisturbanceTape(
            address=f"TEST_ONLY:tape:{index}",
            eta_v=(0.003 * sv,) * 364,
            eta_y=(0.002 * sy,) * 364,
            eta_omega=(0.004 * so,) * 364,
        )
        for index, (sv, sy, so) in enumerate(signs)
    )


def _host_output(*, active: bool, terminal: bool, tick: int, observation=None, safe=False, dock_tick=None, advanced=None):
    return HostOutput(
        advanced=tick > 0 if advanced is None else advanced,
        active=active,
        terminal=terminal,
        ticks_advanced=0 if tick == 0 else 7,
        tick=tick,
        hold_k=7,
        next_k=7,
        observation=tuple([0.0] * 18) if observation is None else observation,
        safe_dock=safe,
        timeout=terminal and not safe,
        cable_overload=False,
        gantry_contact=False,
        attitude_loss=False,
        formation_loss=False,
        cumulative_reward=0.0,
        cumulative_energy=0.0,
        energy_ticks=tick,
        dock_tick=dock_tick,
    )


class _TestOnlyOpportunitySession:
    created_resets = ()
    forced_rows = ()
    foundation_rows = ()

    def __init__(self, resets):
        resets = tuple(resets)
        type(self).created_resets = resets
        self.initial = tuple(_host_output(active=True, terminal=False, tick=0) for _ in resets)
        self.calls = 0

    def renew(self, rows):
        rows = tuple(rows)
        self.calls += 1
        if self.calls == 1:
            type(self).forced_rows = rows
            return tuple(_host_output(active=True, terminal=False, tick=7) for _ in rows)
        type(self).foundation_rows = rows
        return tuple(_host_output(active=False, terminal=True, tick=14) for _ in rows)

    def close(self):
        pass


class _TestOnlyMaskedOpportunitySession:
    masked_rows = ()

    def __init__(self, resets):
        resets = tuple(resets)
        self.initial = tuple(_host_output(active=True, terminal=False, tick=0) for _ in resets)
        self.calls = 0
        self.early_terminal = ()

    def renew(self, rows):
        rows = tuple(rows)
        self.calls += 1
        if self.calls == 1:
            self.early_terminal = tuple(
                _host_output(active=False, terminal=True, tick=7)
                for _ in rows[:72]
            )
            return self.early_terminal + tuple(
                _host_output(active=True, terminal=False, tick=7)
                for _ in rows[72:]
            )
        type(self).masked_rows = rows[:72]
        return self.early_terminal + tuple(
            _host_output(active=False, terminal=True, tick=14)
            for _ in rows[72:]
        )

    def close(self):
        pass


def _terminal_signature(outputs):
    return tuple(
        (
            value.active,
            value.terminal,
            value.tick,
            value.safe_dock,
            value.timeout,
            value.cable_overload,
            value.gantry_contact,
            value.attitude_loss,
            value.formation_loss,
        )
        for value in outputs
    )


class _TracingNativeBatch:
    """TEST trace wrapper around the real candidate NativeBatch."""

    last = None

    def __init__(self, resets):
        self._inner = NativeBatch(tuple(resets))
        self.initial = self._inner.initial
        self.history = [_terminal_signature(self.initial)]
        self.input_masks = []
        type(self).last = self

    def renew(self, rows):
        rows = tuple(rows)
        self.input_masks.append(tuple(row.active for row in rows))
        outputs = self._inner.renew(rows)
        self.history.append(_terminal_signature(outputs))
        return outputs

    def close(self):
        self._inner.close()


class _TestOnlyOracleOpportunitySession:
    """Independent TEST-only adapter; never a production fallback."""

    last = None

    def __init__(self, resets):
        self._states = tuple(_oracle_reset(value) for value in tuple(resets))
        self.initial = tuple(
            _oracle_output(state, advanced=0, hold_k=state.current_k)
            for state in self._states
        )
        self._last = self.initial
        self.history = [_terminal_signature(self.initial)]
        self.input_masks = []
        self.closed = False
        type(self).last = self

    def renew(self, rows):
        rows = tuple(rows)
        if len(rows) != len(self._states):
            raise AssertionError("TEST oracle adapter width changed")
        self.input_masks.append(tuple(row.active for row in rows))
        next_states = []
        outputs = []
        for state, row, prior in zip(self._states, rows, self._last):
            if not row.active:
                next_states.append(state)
                outputs.append(prior)
                continue
            hold_k = state.current_k
            next_state, advanced = _oracle_renewal(state, row)
            next_states.append(next_state)
            outputs.append(_oracle_output(next_state, advanced=advanced, hold_k=hold_k))
        self._states = tuple(next_states)
        result = tuple(outputs)
        self._last = result
        self.history.append(_terminal_signature(result))
        return result

    def close(self):
        self.closed = True


def test_foundation_static_shape_counts_and_one_parameterization_across_k():
    schema = validate_foundation_schema()
    assert schema["actor_parameters"] == FOUNDATION_ACTOR_PARAMETER_COUNT == 12_882
    assert schema["critic_parameters"] == FOUNDATION_CRITIC_PARAMETER_COUNT == 11_233
    assert schema["total_parameters"] == FOUNDATION_PARAMETER_COUNT == 24_115
    assert schema["chronology_input"] is schema["graph_mode_input"] is False
    assert TREAT_TRAINABLE_PARAMETER_COUNT == 6_146
    assert FREE_TRAINABLE_PARAMETER_COUNT == SET_TRAINABLE_PARAMETER_COUNT == 12_756

    contract = SharedParameterizationContract("TEST_ONLY:one-vector", K_TRAIN, K_TARGET)
    contract.validate()
    with pytest.raises(ContractError, match="per-k specialization"):
        SharedParameterizationContract("TEST_ONLY:bad", K_TRAIN, K_TARGET, per_k_heads=1).validate()


def test_exact_static_initialization_schema_and_row_major_xavier_witness():
    rows = initialization_schema()
    by_name = {row.name: row for row in rows}
    foundation = tuple(row for row in rows if row.name.startswith("foundation."))
    assert all(
        row.law == "row_major_xavier_uniform" and row.gain == 1.0
        for row in foundation
        if row.name.endswith(".weight")
    )
    assert all(
        row.law == "constant" and row.constant == 0.0
        for row in foundation
        if row.name.endswith(".bias")
    )
    assert by_name["order.scale.output.weight"].constant == 0.0
    assert by_name["order.scale.output.bias"].constant == 0.001
    for prefix in ("free.residual.output", "set.residual.output"):
        assert by_name[f"{prefix}.weight"].constant == 0.0
        assert by_name[f"{prefix}.bias"].constant == 0.0
    assert by_name["order.critic.input.weight"].shape == (64, 19)
    assert by_name["free.residual.output.weight"].shape == (18, 64)
    assert by_name["set.residual.output.weight"].shape == (18, 64)

    matrix = row_major_xavier_uniform_from_test_uniforms(
        (0.0, 0.25, 0.5, 0.75), input_width=2, output_width=2
    )
    bound = torch.tensor(math.sqrt(6.0 / 4.0), dtype=torch.float32)
    expected = ((torch.tensor((0.0, 0.25, 0.5, 0.75)) * 2.0 - 1.0) * bound).reshape(2, 2)
    assert matrix.is_contiguous()
    assert torch.equal(matrix, expected)


def test_j_treat_free_reversed_and_set_fixture_conformance():
    observation = _observation(2)
    k = torch.tensor([7, 13], dtype=torch.int64)
    q = torch.tensor([0.0, 1.0], dtype=torch.float32)
    scores = graph_slack_scores(observation, q, k)
    assert scores.shape == (2, ACTION_COUNT)
    assert torch.isfinite(scores).all()
    assert len(LEXICOGRAPHIC_ACTIONS) == 18

    foundation = torch.linspace(-0.4, 0.4, 18, dtype=torch.float32).repeat(2, 1)
    alpha = torch.tensor([0.0, 0.25], dtype=torch.float32)
    treat = treat_logits(foundation, alpha, scores)
    assert torch.equal(treat[0], foundation[0])
    coordinate = 5
    lifted = scores.clone()
    lifted[1, coordinate] += 0.125
    changed = treat_logits(foundation, alpha, lifted)
    assert changed[1, coordinate] - treat[1, coordinate] == pytest.approx(0.25 * 0.125)
    assert bool((scores < 0).any())  # signed alpha*J is not a nonnegative bonus.

    assert torch.equal(free_logits(treat, torch.zeros_like(treat)), treat)
    witness = strict_containment_witness(scores[1])
    ones = torch.ones(18)
    centered = scores[1] - scores[1].mean()
    assert abs(float(torch.dot(witness, ones))) < 2e-6
    assert abs(float(torch.dot(witness, centered))) < 2e-6
    assert torch.linalg.vector_norm(witness) > 0

    reversed_q = reversed_compositor(q)
    assert torch.equal(reversed_q.physical_q, q)
    assert torch.equal(reversed_q.compositor_q, torch.tensor([1.0, 0.0]))
    expected_set = 0.5 * (
        graph_slack_scores(observation, torch.zeros(2), k)
        + graph_slack_scores(observation, torch.ones(2), k)
    )
    assert torch.equal(set_scores(observation, k), expected_set)
    assert set_compositor(("HOOK-HANDOFF", "FORMATION-ROTATE")) == set_compositor(
        ("FORMATION-ROTATE", "HOOK-HANDOFF")
    ) == 0.5


def test_strict_inverse_cdf_boundary_and_duration_correct_targets():
    probabilities = torch.tensor(
        [[0.25, 0.25, 0.5] + [0.0] * 15, [1.0 / 18.0] * 18],
        dtype=torch.float32,
    )
    # Exact contact at 0.25 advances from action 0 to action 1.
    assert inverse_cdf_index(probabilities, torch.tensor([0.25, 0.0], dtype=torch.float32)).tolist() == [1, 0]

    old = torch.tensor([0.5, 0.25, 0.1], dtype=torch.float32)
    targets = duration_correct_targets(
        ((1.0, 2.0), (3.0,), (-1.0, 0.5)),
        old,
        torch.tensor([True, False, False]),
    )
    r0 = 1.0 + 0.995 * 2.0
    d1 = 3.0 - 0.25
    d0 = r0 + 0.995**2 * 0.25 - 0.5
    a0 = d0 + (0.995 * 0.93) ** 2 * d1
    assert targets.discounted_rewards[0] == pytest.approx(r0)
    assert targets.raw_advantages == pytest.approx(torch.tensor([a0, d1, -1.0 + 0.995 * 0.5 - 0.1]))
    assert torch.mean(targets.normalized_advantages) == pytest.approx(0.0, abs=1e-6)
    assert all(not tensor.requires_grad for tensor in targets.__dict__.values())


def test_three_keyed_fisher_yates_and_quotient_remainder_minibatches():
    permutations = three_epoch_permutations(11, replicate=4, arm="FREE", update=9)
    assert len(set(permutations)) == 3
    for permutation in permutations:
        assert sorted(permutation) == list(range(11))
        batches = four_minibatches(permutation)
        assert tuple(map(len, batches)) == (3, 3, 3, 2)
        assert tuple(item for batch in batches for item in batch) == permutation


def test_autograd_ties_global_clip_and_adamw_global_index_accounting():
    value = torch.tensor([-1.0, 0.0, 0.5, 1.0, 2.0], requires_grad=True)
    strict_clip(value, 0.0, 1.0).sum().backward()
    assert value.grad.tolist() == [0.0, 0.0, 1.0, 0.0, 0.0]

    relu_value = torch.tensor([0.0], requires_grad=True)
    torch.relu(relu_value).backward()
    assert relu_value.grad.item() == 0.0

    left = torch.tensor([1.0], requires_grad=True)
    right = torch.tensor([1.0], requires_grad=True)
    ppo_tie_mean_min(left, right).backward()
    assert left.grad.item() == right.grad.item() == 0.5

    exactly = clip_combined_gradient((torch.tensor([0.8]),))[0]
    assert exactly.item() == pytest.approx(0.8)
    clipped = clip_combined_gradient((torch.tensor([0.6, 0.8]),))[0]
    assert torch.linalg.vector_norm(clipped).item() == pytest.approx(0.8)

    parameter = torch.tensor([0.25, -0.5], dtype=torch.float32)
    state = AdamWState(torch.zeros_like(parameter), torch.zeros_like(parameter), 0)
    updated, state = adamw_step(parameter, torch.tensor([0.1, -0.2]), state)
    assert state.step == 1 and not torch.equal(updated, parameter)
    _, state = adamw_step(updated, torch.tensor([0.1, -0.2]), state)
    assert state.step == 2
    assert optimizer_index_contract("FOUNDATION") == (1, 1_920)
    assert optimizer_index_contract("TREAT") == optimizer_index_contract("FREE") == (1, 1_152)


def test_prerequisite_lifecycle_requires_24_then_gates_then_72_and_marks_nonpass_inapplicable():
    foundation = _foundation_finals()
    nonpass = snapshot(foundation, foundation_gate=GateOutcome.NONPASS)
    assert nonpass.opportunity_applicability is Applicability.INAPPLICABLE
    assert nonpass.adapter_applicability is Applicability.INAPPLICABLE
    assert nonpass.final_applicability is Applicability.INAPPLICABLE

    opportunity_nonpass = snapshot(
        foundation,
        foundation_gate=GateOutcome.PASS,
        opportunity_gate=GateOutcome.NONPASS,
    )
    assert opportunity_nonpass.adapter_applicability is Applicability.INAPPLICABLE
    with pytest.raises(LifecycleError, match="before both prerequisites"):
        snapshot(
            foundation,
            foundation_gate=GateOutcome.PASS,
            opportunity_gate=GateOutcome.NONPASS,
            adapter_finals=_adapter_finals()[:1],
        )

    complete = snapshot(
        foundation,
        foundation_gate=GateOutcome.PASS,
        opportunity_gate=GateOutcome.PASS,
        adapter_finals=_adapter_finals(),
    )
    complete.require_atomic_final_eligibility()
    assert complete.final_applicability is Applicability.ELIGIBLE
    with pytest.raises(LifecycleError, match="all 24"):
        snapshot(foundation[:-1], foundation_gate=GateOutcome.PASS)


def test_exhaustive_first_true_inference_precedence_and_inapplicable_prerequisites():
    # Invalid required foundation evidence is first, even if a nonpass is supplied.
    assert exhaustive_first_true_branch(
        InferenceFixture(False, False, GateOutcome.NONPASS)
    ) is InferenceBranch.INVALID_EVIDENCE

    # A valid foundation nonpass makes every downstream stage inapplicable, not incomplete.
    assert exhaustive_first_true_branch(
        InferenceFixture(True, True, GateOutcome.NONPASS)
    ) is InferenceBranch.FOUNDATION_NOT_ESTABLISHED
    assert exhaustive_first_true_branch(
        InferenceFixture(
            True,
            True,
            GateOutcome.PASS,
            opportunity_stage_complete=True,
            opportunity_gate=GateOutcome.NONPASS,
        )
    ) is InferenceBranch.OPPORTUNITY_NOT_ESTABLISHED

    required_final = dict(
        conformance_valid=True,
        foundation_stage_complete=True,
        foundation_gate=GateOutcome.PASS,
        opportunity_stage_complete=True,
        opportunity_gate=GateOutcome.PASS,
        final_stage_complete=True,
        free_competence=PredicateState.PASS,
        set_competence=PredicateState.PASS,
    )
    assert exhaustive_first_true_branch(
        InferenceFixture(**required_final, v_route=RouteState.PASS, w_route=RouteState.EXCLUDED)
    ) is InferenceBranch.RETAIN
    assert exhaustive_first_true_branch(
        InferenceFixture(**required_final, v_route=RouteState.EXCLUDED, w_route=RouteState.EXCLUDED)
    ) is InferenceBranch.DECLINE
    unresolved_control = dict(required_final)
    unresolved_control["set_competence"] = PredicateState.UNRESOLVED
    assert exhaustive_first_true_branch(
        InferenceFixture(**unresolved_control, v_route=RouteState.EXCLUDED, w_route=RouteState.EXCLUDED)
    ) is InferenceBranch.NONIDENTIFIED
    incomplete = dict(required_final)
    incomplete["final_stage_complete"] = False
    assert exhaustive_first_true_branch(
        InferenceFixture(**incomplete, v_route=RouteState.EXCLUDED, w_route=RouteState.EXCLUDED)
    ) is InferenceBranch.INVALID_EVIDENCE


def test_synthetic_create_only_interrupt_cold_scan_resume_and_partial_rejection(tmp_path):
    payload = {"test_only": True, "question_relevant": False, "complete": True, "value": "fixture"}
    target = tmp_path / "payload.json"
    create_only_commit(target, payload)
    with pytest.raises(SyntheticResumeError, match="create-only"):
        create_only_commit(target, payload)

    root = tmp_path / "frontier"
    first = SyntheticFrontier(
        stage="TEST_ONLY_FOUNDATION",
        slot="TEST_ONLY_SLOT_00",
        generation=0,
        previous_fake_digest=None,
        payload_fake_digest=fake_digest("TEST_ONLY:payload:0"),
    )
    _, first_digest = commit_frontier(root, first)
    second = SyntheticFrontier(
        stage=first.stage,
        slot=first.slot,
        generation=1,
        previous_fake_digest=first_digest,
        payload_fake_digest=fake_digest("TEST_ONLY:payload:1"),
    )
    commit_frontier(root, second)
    write_interrupted_test_fragment(root / "ignored.TEST_ONLY.tmp")
    scanned = cold_scan_exact_frontier(root, stage=first.stage, slot=first.slot)
    assert scanned == (first, second)

    with pytest.raises(SyntheticResumeError, match="partial synthetic stage"):
        require_complete_synthetic_stage(
            {"a": payload}, required_slots=frozenset(("a", "b"))
        )
    with pytest.raises(SyntheticResumeError, match="forbidden"):
        create_only_commit(
            tmp_path / "bad.json",
            {"test_only": True, "question_relevant": False, "complete": True, "identity": "x"},
        )


def _pair_outcomes(*, mismatch_tape: bool = False):
    tapes = _tapes()
    rows = []
    for q in (0, 1):
        for action in range(18):
            if q == 0:
                value = 0.8 if action in (0, 1) else 0.1
            else:
                value = 0.7 if action == 2 else 0.1
            for tape_index, tape in enumerate(tapes):
                digest = tape.digest
                if mismatch_tape and (q, action, tape_index) == (1, 17, 3):
                    digest = "f" * 64
                rows.append(
                    TapeOutcome(
                        RolloutAddress(q, action, tape_index), digest, value
                    )
                )
    return tuple(rows)


def test_exact_opportunity_pair_tape_mean_ties_q_d_s_and_rejections():
    state = OpportunityState(0, 7, 0, 0.01, 0.0, 0.0)
    metrics = compute_pair_metrics(state, _pair_outcomes())
    assert metrics.rollout_count == PAIR_ROLLOUT_COUNT == 144
    assert metrics.argmax_q0 == frozenset((0, 1))
    assert metrics.argmax_q1 == frozenset((2,))
    assert metrics.q_value == 1.0
    assert metrics.d_value == pytest.approx(0.30)
    assert metrics.s_value == pytest.approx(0.65)
    with pytest.raises(OpportunityContractError, match="exactly 144"):
        compute_pair_metrics(state, _pair_outcomes()[:-1])
    duplicated = list(_pair_outcomes())
    duplicated[-1] = duplicated[-2]
    with pytest.raises(OpportunityContractError, match="partial, duplicate"):
        compute_pair_metrics(state, duplicated)
    with pytest.raises(OpportunityContractError, match="tape binding differs"):
        compute_pair_metrics(state, _pair_outcomes(mismatch_tape=True))


def test_complete_native_service_enumerates_18_actions_four_common_tapes_and_frozen_foundation():
    _TestOnlyOpportunitySession.created_resets = ()
    _TestOnlyOpportunitySession.forced_rows = ()
    _TestOnlyOpportunitySession.foundation_rows = ()
    foundation_calls = []

    def foundation(observations):
        foundation_calls.append(observations)
        return tuple((0.0,) * 18 for _ in observations)

    metrics = run_complete_pair(
        OpportunityState(3, 7, 5, 0.01, 0.0, 0.0),
        _tapes(),
        permit=_opportunity_permit(),
        foundation=foundation,
        session_factory=_TestOnlyOpportunitySession,
    )
    assert len(_TestOnlyOpportunitySession.created_resets) == 144
    assert len(_TestOnlyOpportunitySession.forced_rows) == 144
    assert len(foundation_calls) == 1 and len(foundation_calls[0]) == 144
    assert {row.action for row in _TestOnlyOpportunitySession.forced_rows} == set(range(18))
    # q-major, action-major, tape-minor: every action has the same four tapes.
    for q_offset in (0, 72):
        for action in range(18):
            rows = _TestOnlyOpportunitySession.forced_rows[
                q_offset + action * 4 : q_offset + (action + 1) * 4
            ]
            assert [row.action for row in rows] == [action] * 4
            assert [(row.eta_v[0], row.eta_y[0], row.eta_omega[0]) for row in rows] == [
                (tape.eta_v[0], tape.eta_y[0], tape.eta_omega[0]) for tape in _tapes()
            ]
    # Exact ties in frozen foundation logits use lexicographic action zero.
    assert {row.action for row in _TestOnlyOpportunitySession.foundation_rows} == {0}
    assert metrics.q_value == 0.0 and metrics.d_value == 0.0 and metrics.s_value == 0.0

    masked_foundation_calls = []

    def masked_foundation(observations):
        masked_foundation_calls.append(observations)
        return tuple((0.0,) * 18 for _ in observations)

    run_complete_pair(
        OpportunityState(3, 13, 6, 0.01, 0.0, 0.0),
        _tapes(),
        permit=_opportunity_permit(),
        foundation=masked_foundation,
        session_factory=_TestOnlyMaskedOpportunitySession,
    )
    assert len(masked_foundation_calls) == 1 and len(masked_foundation_calls[0]) == 72
    assert len(_TestOnlyMaskedOpportunitySession.masked_rows) == 72
    assert all(row.active is False for row in _TestOnlyMaskedOpportunitySession.masked_rows)


def test_opportunity_execution_requires_validated_unopened_passing_foundation_before_session_creation():
    forged = OpportunityExecutionPermit(
        foundation_inventory_digest="0" * 64,
        foundation_final_count=24,
        foundation_gate="PASS",
        opportunity_unopened=True,
        downstream_unopened=True,
    )
    sessions_created = []

    def forbidden_factory(resets):
        sessions_created.append(tuple(resets))
        raise AssertionError("native session must not be created")

    with pytest.raises(OpportunityContractError, match="passing-foundation permit"):
        run_complete_pair(
            OpportunityState(0, 7, 0, 0.01, 0.0, 0.0),
            _tapes(),
            permit=forged,
            foundation=lambda observations: (),
            session_factory=forbidden_factory,
        )
    assert sessions_created == []

    with pytest.raises(LifecycleError, match="complete passing foundation"):
        issue_opportunity_execution_permit(snapshot(_foundation_finals()[:-1]))
    with pytest.raises(LifecycleError, match="complete passing foundation"):
        issue_opportunity_execution_permit(
            snapshot(_foundation_finals(), foundation_gate=GateOutcome.NONPASS)
        )
    with pytest.raises(LifecycleError, match="unopened downstream"):
        issue_opportunity_execution_permit(
            snapshot(
                _foundation_finals(),
                foundation_gate=GateOutcome.PASS,
                opportunity_gate=GateOutcome.PASS,
            )
        )


def test_real_native_complete_opportunity_matches_independent_test_only_oracle_exactly():
    state = OpportunityState(0, 7, 0, 0.0125, -0.0025, 0.003)
    tapes = _tapes()

    def frozen_lexicographic_foundation(observations):
        # Deterministic finite TEST logits with a deliberate 0/1 tie.  The
        # service must choose lexicographic action zero in both executions.
        return tuple((1.0, 1.0) + (0.0,) * 16 for _ in observations)

    native_metrics = run_complete_pair(
        state,
        tapes,
        permit=_opportunity_permit(),
        foundation=frozen_lexicographic_foundation,
        session_factory=_TracingNativeBatch,
    )
    oracle_metrics = run_complete_pair(
        state,
        tapes,
        permit=_opportunity_permit(),
        foundation=frozen_lexicographic_foundation,
        session_factory=_TestOnlyOracleOpportunitySession,
    )
    assert native_metrics == oracle_metrics
    assert native_metrics.tape_digests == tuple(tape.digest for tape in tapes)
    assert native_metrics.argmax_q0 == oracle_metrics.argmax_q0
    assert native_metrics.argmax_q1 == oracle_metrics.argmax_q1

    native = _TracingNativeBatch.last
    oracle = _TestOnlyOracleOpportunitySession.last
    assert native is not None and oracle is not None and oracle.closed is True
    assert native.history == oracle.history
    assert native.input_masks == oracle.input_masks
    assert all(row[1] is True for row in native.history[-1])
    assert all(row[0] is False for row in native.history[-1])
    # At least one lane absorbs before the last lane, so the exact native and
    # oracle traces both exercise original-position inactive masking.
    assert any(not all(mask) and any(mask) for mask in native.input_masks)


def _replicate_pairs(replicate: int, template: PairOpportunityMetrics):
    return tuple(
        PairOpportunityMetrics(
            replicate=replicate,
            k=k,
            state_index=state,
            q_value=template.q_value,
            d_value=template.d_value,
            s_value=template.s_value,
            argmax_q0=template.argmax_q0,
            argmax_q1=template.argmax_q1,
            tape_digests=template.tape_digests,
        )
        for k in (7, 13)
        for state in range(16)
    )


def test_exact_replicate_inventory_bonferroni_gate_atomic_resume_and_lifecycle(tmp_path):
    template = compute_pair_metrics(
        OpportunityState(0, 7, 0, 0.01, 0.0, 0.0), _pair_outcomes()
    )
    aggregates = tuple(
        aggregate_replicate(_replicate_pairs(replicate, template))
        for replicate in range(24)
    )
    assert all(value.pair_count == 32 for value in aggregates)
    analysis = analyze_gate(aggregates)
    assert analysis.q.lower == pytest.approx(1.0)
    assert analysis.d.lower == pytest.approx(0.30)
    assert analysis.s.lower == pytest.approx(0.65)
    assert analysis.passes is True

    boundary = tuple(
        ReplicateOpportunityMetrics(replicate, Q_THRESHOLD, D_THRESHOLD, S_THRESHOLD)
        for replicate in range(24)
    )
    assert analyze_gate(boundary).passes is False  # strict threshold contact never passes
    with pytest.raises(OpportunityContractError, match="exact replicates"):
        analyze_gate(aggregates[:-1])

    complete_pairs = _replicate_pairs(0, template)
    path = tmp_path / "TEST_ONLY_opportunity_inventory.json"
    publish_test_only_replicate_inventory(path, complete_pairs)
    assert load_test_only_replicate_inventory(path) == complete_pairs
    with pytest.raises(OpportunityContractError, match="exactly 32"):
        publish_test_only_replicate_inventory(
            tmp_path / "partial.json", complete_pairs[:-1]
        )

    foundation_passed = snapshot(
        _foundation_finals(), foundation_gate=GateOutcome.PASS
    )
    require_opportunity_lifecycle(foundation_passed)
    with pytest.raises(OpportunityContractError, match="passing foundation"):
        require_opportunity_lifecycle(
            snapshot(_foundation_finals(), foundation_gate=GateOutcome.NONPASS)
        )

    permit = _opportunity_permit()
    complete_stage_path = tmp_path / "TEST_ONLY_complete_opportunity_stage.json"
    publish_test_only_complete_opportunity_stage(
        complete_stage_path, aggregates, permit=permit
    )
    with pytest.raises(SyntheticResumeError, match="create-only"):
        publish_test_only_complete_opportunity_stage(
            complete_stage_path, aggregates, permit=permit
        )
    loaded = load_test_only_complete_opportunity_stage(
        complete_stage_path, permit=permit
    )
    resumed = resume_test_only_complete_opportunity_stage(
        complete_stage_path, permit=permit
    )
    assert loaded == resumed
    assert loaded.replicates == aggregates
    assert loaded.analysis == analysis

    with pytest.raises(OpportunityContractError, match="exact replicates"):
        publish_test_only_complete_opportunity_stage(
            tmp_path / "only_23.json", aggregates[:-1], permit=permit
        )
    duplicated = aggregates[:-1] + (aggregates[-2],)
    with pytest.raises(OpportunityContractError, match="exact replicates"):
        publish_test_only_complete_opportunity_stage(
            tmp_path / "duplicate.json", duplicated, permit=permit
        )
    with pytest.raises(OpportunityContractError, match="permit.*analysis differs"):
        load_test_only_complete_opportunity_stage(
            complete_stage_path, permit=_opportunity_permit(alternate=True)
        )
    forged = OpportunityExecutionPermit(
        foundation_inventory_digest="0" * 64,
        foundation_final_count=24,
        foundation_gate="NONPASS",
        opportunity_unopened=True,
        downstream_unopened=True,
    )
    with pytest.raises(OpportunityContractError, match="passing-foundation permit"):
        publish_test_only_complete_opportunity_stage(
            tmp_path / "nonpassing.json", aggregates, permit=forged
        )

    tampered = json.loads(complete_stage_path.read_text(encoding="ascii"))
    tampered["analysis"]["q"]["lower"] += 0.01
    tampered_path = tmp_path / "tampered_analysis.json"
    create_only_commit(tampered_path, tampered)
    with pytest.raises(OpportunityContractError, match="recomputed analysis differs"):
        load_test_only_complete_opportunity_stage(tampered_path, permit=permit)
