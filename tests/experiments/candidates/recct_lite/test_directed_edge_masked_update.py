from __future__ import annotations

from dataclasses import fields
import hashlib
import inspect

import pytest
import torch
from torch.nn import functional as F

import ha_ctse_process.continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process.anchored_residual_g19 import AnchoredRosterTrajectory
from experiments.candidates.recct_lite import directed_edge_masked_update as a1


SEED = 20_260_819


def _technical_batch(model: g40.G40NativeSixPolicy) -> AnchoredRosterTrajectory:
    observations = torch.tensor(
        [[
            [[-0.8, 0.1, 0.3, -0.2, 0.4, 0.6],
             [0.25, -0.65, 0.45, 0.15, -0.35, 0.75],
             [0.7, 0.35, -0.55, 0.5, 0.05, -0.45]],
            [[-0.45, 0.55, 0.2, 0.65, -0.1, 0.3],
             [0.6, -0.15, -0.7, 0.25, 0.8, -0.05],
             [0.05, 0.85, -0.25, -0.6, 0.35, 0.4]],
        ]],
        dtype=torch.float32,
    )
    pre_tanh = torch.tensor(
        [[
            [[-0.35, 0.10], [0.20, -0.45], [0.55, 0.30]],
            [[0.15, 0.50], [-0.60, 0.25], [0.40, -0.20]],
        ]],
        dtype=torch.float32,
    )
    active = torch.ones((1, 2, 3), dtype=torch.bool)
    hidden = torch.zeros((1, 2, 3, model.hidden_dim), dtype=torch.float32)
    return AnchoredRosterTrajectory(
        observations=observations,
        active_mask=active,
        critic_states=torch.tensor(
            [[[0.1, -0.2, 0.3, -0.4, 0.5, -0.6],
              [-0.15, 0.25, -0.35, 0.45, -0.55, 0.65]]],
            dtype=torch.float32,
        ),
        actions=torch.tanh(pre_tanh),
        pre_tanh_actions=pre_tanh,
        old_log_probs=torch.zeros((1, 2, 3), dtype=torch.float32),
        old_values=torch.zeros((1, 2), dtype=torch.float32),
        old_immediate_baselines=torch.zeros((1, 2), dtype=torch.float32),
        old_successor_baselines=torch.zeros((1, 2), dtype=torch.float32),
        rewards=torch.tensor([[1.0, -0.5]], dtype=torch.float32),
        hidden_before=hidden,
        hidden_after=hidden.clone(),
        prefix_action_sums=torch.zeros((1, 2, 3, 2), dtype=torch.float32),
        outcomes=(),
        ledgers=(),
        terminal_hidden_reset_mask=torch.zeros((1, 2, 3), dtype=torch.bool),
    )


def _config(optimizer: torch.optim.Adam) -> a1.LearnerConfig:
    group = optimizer.param_groups[0]
    return a1.LearnerConfig(
        learning_rate=float(group["lr"]),
        betas=tuple(float(row) for row in group["betas"]),
        eps=float(group["eps"]),
        weight_decay=float(group["weight_decay"]),
        amsgrad=bool(group["amsgrad"]),
        maximize=bool(group.get("maximize", False)),
    )


def _capsule(
    names: tuple[str, str, str] = ("a", "b", "c"),
) -> tuple[
    a1.DirectedEdgeMaskedLearner,
    a1.SealedLearnerCapsule,
    tuple[a1.OpaqueDirectedHandle, a1.OpaqueDirectedHandle],
    g40.G40NativeSixPolicy,
    torch.optim.Adam,
    AnchoredRosterTrajectory,
]:
    model = g40.make_model(3, initialization_seed=SEED)
    optimizer = torch.optim.Adam(
        model.actor_credit_parameters(), lr=g40.LEARNING_RATE
    )
    trajectory = _technical_batch(model)
    learner = a1.DirectedEdgeMaskedLearner("technical-learner")
    ancestry = a1.RosterEpochAncestry(
        roster_epoch=7,
        policy_generation="technical-generation",
        learner_checkpoint_digest=a1.model_digest(model),
        optimizer_checkpoint_digest=a1.optimizer_digest(model, optimizer),
        pretreatment_batch_digest=a1.trajectory_digest(trajectory),
        parent_epoch_digest=hashlib.sha256(b"technical-parent").hexdigest(),
    )
    capsule = learner.seal_capsule(
        model=model,
        optimizer=optimizer,
        trajectory=trajectory,
        roster=tuple(a1.AgentInstance(name, slot) for slot, name in enumerate(names)),
        ancestry=ancestry,
        frozen_selection=a1.FrozenSelectionState(
            (True, True),
            (0.6, 0.6),
            hashlib.sha256(b"technical-predictor").hexdigest(),
            "10",
        ),
        rng_plan=a1.SiteKeyedRNGPlan(
            (("learner/replay", 0), ("optimizer/adam", 0))
        ),
        learner_config=_config(optimizer),
        scheduler_state=a1.DisabledUpdateState("scheduler"),
        scaler_state=a1.DisabledUpdateState("scaler"),
        clipping_state=a1.DisabledUpdateState("gradient_clipping"),
        accumulation_state=a1.DisabledUpdateState("gradient_accumulation"),
    )
    handles = (
        learner.handle(capsule, names[0], names[1]),
        learner.handle(capsule, names[1], names[0]),
    )
    return learner, capsule, handles, model, optimizer, trajectory


def _ordinary_update(
    model: g40.G40NativeSixPolicy,
    optimizer: torch.optim.Adam,
    trajectory: AnchoredRosterTrajectory,
) -> tuple[torch.Tensor, ...]:
    replay = g40.replay_trajectory(model, trajectory, device=torch.device("cpu"))
    credit = g40.compute_credit_targets(
        rewards=trajectory.rewards,
        slow_values=trajectory.old_values,
        immediate_baselines=trajectory.old_immediate_baselines,
        successor_baselines=trajectory.old_successor_baselines,
        terminals=g40.terminal_mask(trajectory),
    )
    normalized = g40.normalize_advantage(credit.immediate_advantage)
    loss = (
        g40._policy_loss_from_normalized_advantage(replay, trajectory, normalized)
        + g40.VALUE_COEFFICIENT
        * F.mse_loss(replay.immediate_baselines, trajectory.rewards.detach())
        - g40.ENTROPY_COEFFICIENT * g40._entropy(replay)
    )
    parameters = model.actor_credit_parameters()
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    gradients = tuple(
        torch.zeros_like(parameter)
        if parameter.grad is None
        else parameter.grad.detach().clone()
        for parameter in parameters
    )
    g40._optimizer_step(optimizer, parameters)
    return gradients


def _receipt_model_equal(
    receipt: a1.UpdateReceipt, model: g40.G40NativeSixPolicy
) -> bool:
    expected = tuple(model.state_dict().items())
    return all(
        name == value.name and torch.equal(tensor.detach().cpu(), value.tensor())
        for (name, tensor), value in zip(expected, receipt.after.learner_state)
    )


def test_capsule_is_complete_handles_are_opaque_and_forged_objects_fail_closed():
    learner, capsule, handles, *_ = _capsule()
    manifest_fields = {field.name for field in fields(a1.CapsuleManifest)}
    assert {
        "learner_instance",
        "roster",
        "ancestry",
        "frozen_selection",
        "rng_plan",
        "learner_config",
        "scheduler_state",
        "scaler_state",
        "clipping_state",
        "accumulation_state",
        "edge_registry_digest",
    } <= manifest_fields
    assert not a1.FORBIDDEN_INPUT_NAMES & manifest_fields
    assert set(vars(handles[0])) == set() if hasattr(handles[0], "__dict__") else True
    with pytest.raises(TypeError, match="only by the learner"):
        a1.OpaqueDirectedHandle(object(), "forged")
    forged = object.__new__(a1.OpaqueDirectedHandle)
    with pytest.raises(ValueError, match="provenance"):
        learner._record_for(capsule, forged)


@pytest.mark.parametrize(
    "reserved_site",
    (
        "global",
        "global/seed",
        "audit",
        "audit/seed",
        "future",
        "future/outcome",
        "semantic_label",
        "semantic/label",
        "learner/replay/audit",
    ),
)
def test_rng_plan_rejects_every_nonallowlisted_reserved_namespace(reserved_site):
    with pytest.raises(ValueError, match="allowlist"):
        a1.SiteKeyedRNGPlan(
            (
                ("learner/replay", 0),
                ("optimizer/adam", 0),
                (reserved_site, 0),
            )
        )


def test_mask_11_is_bit_exact_to_the_ordinary_g40_update():
    learner, capsule, handles, model, optimizer, trajectory = _capsule()
    ordinary_gradients = _ordinary_update(model, optimizer, trajectory)
    receipt = a1.DirectedEdgeMaskedUpdate(
        capsule, handles, "11", learner.clone_counterfactual_rng(capsule)
    )

    assert receipt.ordinary_update_path
    assert all(
        torch.equal(row.tensor(), expected)
        for row, expected in zip(receipt.gradient, ordinary_gradients)
    )
    assert _receipt_model_equal(receipt, model)
    assert receipt.after.optimizer_state.digest == a1.optimizer_digest(model, optimizer)


def test_four_pure_masks_conserve_full_gradient_and_bind_only_named_ports():
    learner, capsule, handles, *_ = _capsule()
    receipts = {
        mask: a1.DirectedEdgeMaskedUpdate(
            capsule, handles, mask, learner.clone_counterfactual_rng(capsule)
        )
        for mask in a1.MASKS
    }

    assert a1._factorial_conservation(receipts) <= 2e-6
    assert not receipts["00"].intervention.enabled_ports
    assert receipts["10"].intervention.enabled_ports == (handles[0].opaque_id,)
    assert receipts["01"].intervention.enabled_ports == (handles[1].opaque_id,)
    assert receipts["11"].intervention.enabled_ports == tuple(
        handle.opaque_id for handle in handles
    )
    assert len({row.call_lineage for row in receipts.values()}) == 4
    assert len({row.before.digest for row in receipts.values()}) == 1
    assert len({row.ancestry.rng_plan_digest for row in receipts.values()}) == 1
    assert all(row.optimizer_transitions == 1 for row in receipts.values())
    assert all(
        row.intervention.structural_preaggregation_gate
        and row.intervention.post_aggregate_cancellation_path_count == 0
        and row.intervention.undeclared_duplicate_path_count == 0
        for row in receipts.values()
    )
    first, second = a1._port_contrast_norms(receipts)
    assert min(first, second) > 1e-12
    assert a1._port_contrast_separation(receipts) > 1e-12


def test_structural_gate_precedes_sum_and_has_no_aggregate_then_cancel_route():
    source = inspect.getsource(g40._directed_learning_forward_step)
    assert "ordinary_sum" not in source
    assert "corrections" not in source
    assert source.index("source_terms.append(term)") < source.index(
        "torch.stack(source_terms, dim=1).sum(dim=1)"
    )
    inventory = g40.directed_learning_port_path_inventory(
        3,
        (
            g40.G40DirectedLearningPort(0, 1, False),
            g40.G40DirectedLearningPort(1, 0, True),
        ),
    )
    assert inventory == {
        "declared_pairs": ((0, 1), (1, 0)),
        "declared_path_count": 2,
        "undeclared_duplicate_path_count": 0,
        "post_aggregate_cancellation_path_count": 0,
        "structural_preaggregation_gate": True,
    }
    with pytest.raises(ValueError, match="unique"):
        g40.directed_learning_port_path_inventory(
            3,
            (
                g40.G40DirectedLearningPort(0, 1, False),
                g40.G40DirectedLearningPort(0, 1, True),
            ),
        )


def _port_gradients(enabled: bool, perturbation: float) -> dict[str, torch.Tensor]:
    model = g40.make_model(3, initialization_seed=SEED)
    trajectory = _technical_batch(model)
    replay = g40.replay_trajectory_with_directed_learning_ports(
        model,
        trajectory,
        device=torch.device("cpu"),
        ports=(g40.G40DirectedLearningPort(0, 1, enabled, perturbation),),
    )
    credit = g40.compute_credit_targets(
        rewards=trajectory.rewards,
        slow_values=trajectory.old_values,
        immediate_baselines=trajectory.old_immediate_baselines,
        successor_baselines=trajectory.old_successor_baselines,
        terminals=g40.terminal_mask(trajectory),
    )
    loss = g40._policy_loss_from_normalized_advantage(
        replay, trajectory, g40.normalize_advantage(credit.immediate_advantage)
    )
    loss.backward()
    return {
        name: torch.zeros_like(parameter)
        if parameter.grad is None
        else parameter.grad.detach().clone()
        for name, parameter in zip(
            g40.actor_credit_parameter_names(model), model.actor_credit_parameters()
        )
    }


def test_disabled_port_perturbation_is_invariant_and_enabled_propagation_is_path_local():
    disabled_left = _port_gradients(False, 0.5)
    disabled_right = _port_gradients(False, 7.0)
    enabled_left = _port_gradients(True, 0.5)
    enabled_right = _port_gradients(True, 2.0)

    assert disabled_left.keys() == disabled_right.keys()
    assert all(
        torch.equal(disabled_left[name], disabled_right[name])
        for name in disabled_left
    )
    changed = {
        name
        for name in enabled_left
        if not torch.equal(enabled_left[name], enabled_right[name])
    }
    assert changed
    assert all(name.startswith("policy.member_encoder.") for name in changed)


def test_agent_name_permutation_is_equivariant_and_coordinates_never_mint_identity():
    left_learner, left_capsule, left_handles, *_ = _capsule(("a", "b", "c"))
    right_learner, right_capsule, right_handles, *_ = _capsule(("z", "x", "y"))
    left = a1.DirectedEdgeMaskedUpdate(
        left_capsule,
        left_handles,
        "10",
        left_learner.clone_counterfactual_rng(left_capsule),
    )
    right = a1.DirectedEdgeMaskedUpdate(
        right_capsule,
        right_handles,
        "10",
        right_learner.clone_counterfactual_rng(right_capsule),
    )

    assert left.gradient == right.gradient
    assert left.parameter_delta == right.parameter_delta
    assert left.after.learner_state == right.after.learner_state
    assert left.after.optimizer_state == right.after.optimizer_state


def test_fresh_commit_api_accepts_no_shadow_objects_and_matches_frozen_mask():
    signature = inspect.signature(a1.commit_selected_update)
    assert tuple(signature.parameters) == (
        "capsule",
        "ordered_edge_pair",
        "selected_mask",
        "cloned_counterfactual_rng",
    )
    learner, capsule, handles, *_ = _capsule()
    commit = a1.commit_selected_update(
        capsule,
        handles,
        "10",
        learner.clone_counterfactual_rng(capsule),
    )
    assert commit.call_kind == "commit"
    with pytest.raises(ValueError, match="frozen"):
        a1.commit_selected_update(
            capsule,
            handles,
            "01",
            learner.clone_counterfactual_rng(capsule),
        )


def test_eight_branch_precedence_is_exact():
    names = tuple(field.name for field in fields(a1.A1Checks))
    expected = (
        a1.A1_MISSING_REAL_CALLABLE_OR_NO_UNIQUE_PREAGGREGATION_PORT,
        a1.A1_HANDLE_FORGEABLE_OR_PROVENANCE_LOST,
        a1.A1_COMPOUND_INTERVENTION_OR_UNDECLARED_PATH,
        a1.A1_MASK_SEMANTICS_FAILURE,
        a1.A1_RECOMPUTATION_OR_ANCESTRY_FAILURE,
        a1.A1_IDENTITY_STICKY_NONIDENTIFIABILITY,
        a1.A1_CALLABLE_BUT_HOST_NONIDENTIFYING,
    )
    for index, branch in enumerate(expected):
        values = {name: True for name in names}
        values[names[index]] = False
        for later in names[index + 1 :]:
            values[later] = False
        assert a1.classify_a1(a1.A1Checks(**values)) == branch
    assert a1.classify_a1(a1.A1Checks(*(True,) * 7)) == a1.A1_DIRECTED_EDGE_BINDING_PASS
