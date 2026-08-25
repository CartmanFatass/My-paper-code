from __future__ import annotations

import copy
from dataclasses import fields, replace
import inspect
from pathlib import Path
import tempfile

import numpy as np
import pytest
import torch

from experiments.candidates.recct_lite import orientation_paired_relay_cancellation as recct
from experiments.candidates.recct_lite import orientation_paired_relay_host as host
from scripts import run_recct_b1_orientation_paired_relay_cancellation as runner


def _batch(model: recct.RelayPolicy, orientation: int = 1) -> recct.EpisodeBatch:
    plan = host.make_episode_plan(2_701_001, orientation, host.TRAINING_POOL)
    return runner._rollout_episode(
        model,
        plan,
        runner.SiteKeyedRNG(2_001_701),
        deterministic=False,
        pool_kind="training",
    )


def _sealed() -> tuple[
    recct.OrientationPairedRelayLearner,
    recct.RelayPolicy,
    torch.optim.Adam,
    recct.SealedCapsule,
    tuple[recct.OpaqueDirectedHandle, recct.OpaqueDirectedHandle],
]:
    model = recct.make_model(1701)
    optimizer = recct.make_optimizer(model)
    learner = recct.OrientationPairedRelayLearner("focused-test-learner")
    capsule = learner.seal_capsule(
        model=model,
        optimizer=optimizer,
        batch=_batch(model),
        policy_generation="test-generation-0",
        parent_digest="parent-ancestry",
        rng_counters=(
            ("learner/replay", 0),
            ("optimizer/adam", 0),
            ("selector/balanced_coin", 0),
        ),
    )
    handles = (
        learner.handle(capsule, "L", "R"),
        learner.handle(capsule, "R", "L"),
    )
    return learner, model, optimizer, capsule, handles


def _gradient_difference(
    left: recct.TransitionReceipt, right: recct.TransitionReceipt
) -> dict[str, torch.Tensor]:
    return {
        name: left_tensor - right_tensor
        for (name, left_tensor), (right_name, right_tensor) in zip(
            left.gradient, right.gradient
        )
        if name == right_name
    }


def test_real_host_has_exact_churn_observation_action_and_reward_contract() -> None:
    plan = host.make_episode_plan(2_701_001, 1, host.TRAINING_POOL)
    environment = host.OrientationPairedRelayHost()
    current = environment.reset(plan)
    terminal = []
    observed_slot_orders = []
    reset_by_epoch = []
    while not current.done:
        assert current.observations.shape == (
            host.ACTIVE_COUNT_BY_EPOCH[current.epoch],
            15,
        )
        assert all(name not in host.observation_schema()["fields"] for name in host.FORBIDDEN_OBSERVATION_FIELDS)
        assert np.allclose(current.observations[:, :4].sum(axis=1), 1.0)
        assert np.allclose(current.observations[:, 4:7].sum(axis=1), 1.0)
        assert np.allclose(current.observations[:, 7:9].sum(axis=1), 1.0)
        if current.phase == 0:
            observed_slot_orders.append(current.active_roles)
            reset_by_epoch.append(current.state_reset)
        actions = np.zeros((len(current.active_roles), 2), dtype=np.int64)
        source, receiver = ("L", "R")
        if current.phase == 0:
            actions[current.active_roles.index(source), 0] = (current.cue + 1) // 2
        if current.phase == 3:
            actions[current.active_roles.index(receiver), 1] = (current.cue + 1) // 2
        following = environment.step(actions)
        if current.phase == 3:
            terminal.append(following.terminal_reward)
            assert np.all(following.rewards == following.terminal_reward)
        current = following
    assert terminal == [1.0] * 8
    assert [len(row) for row in observed_slot_orders] == list(host.ACTIVE_COUNT_BY_EPOCH)
    assert any(row != tuple(role for role in host.ROLES if role in row) for row in observed_slot_orders)
    assert all(any(row) for row in reset_by_epoch)


def test_orientation_complement_changes_only_hidden_source_receiver_assignment() -> None:
    plus = host.make_episode_plan(2_701_002, 1, host.TRAINING_POOL)
    minus = plus.complemented()
    host.validate_orientation_pair(plus, minus)
    plus_step = host.OrientationPairedRelayHost().reset(plus)
    minus_step = host.OrientationPairedRelayHost().reset(minus)
    assert plus.exogenous_digest == minus.exogenous_digest
    assert plus.epochs == minus.epochs
    assert np.flatnonzero(plus_step.observations[:, 9]).tolist() == [
        plus_step.active_roles.index("L")
    ]
    assert np.flatnonzero(minus_step.observations[:, 9]).tolist() == [
        minus_step.active_roles.index("R")
    ]
    schema_text = repr(host.observation_schema())
    assert "omega" not in repr(host.observation_schema()["fields"])
    assert all(name not in schema_text.split("'fields':", 1)[1].split("'forbidden':", 1)[0] for name in host.FORBIDDEN_OBSERVATION_FIELDS)

    model = recct.make_model(1701)
    observations = torch.from_numpy(plus_step.observations.copy())
    hidden = torch.zeros((3, 32))
    ports = (recct.DirectedPort("L", "R", False), recct.DirectedPort("R", "L", True))
    ordinary = model.forward_roster(observations, plus_step.active_roles, hidden, ports)
    permutation = torch.tensor((2, 0, 1))
    permuted_roles = tuple(plus_step.active_roles[index] for index in permutation.tolist())
    permuted = model.forward_roster(
        observations[permutation], permuted_roles, hidden[permutation], ports
    )
    inverse = torch.argsort(permutation)
    assert all(torch.allclose(left, right[inverse], atol=1e-7, rtol=0) for left, right in zip(ordinary, permuted))


def test_capsule_handles_are_opaque_authenticated_and_tamper_evident() -> None:
    learner, _, _, capsule, handles = _sealed()
    assert set(vars(capsule.manifest)).isdisjoint(
        {"orientation", "omega", "seed", "useful_edge_label", "instance_id"}
    )
    assert not hasattr(handles[0], "source_role")
    assert not hasattr(handles[0], "receiver_role")
    with pytest.raises(TypeError):
        recct.OpaqueDirectedHandle(object(), handles[0].opaque_id)
    other = recct.OrientationPairedRelayLearner("wrong-owner")
    with pytest.raises(ValueError):
        other.handle(capsule, "L", "R")
    original = capsule.digest
    object.__setattr__(capsule, "_SealedCapsule__digest", "0" * 64)
    with pytest.raises(ValueError, match="digest|provenance"):
        learner.shadow(capsule, handles, "00", learner.clone_rng(capsule))
    object.__setattr__(capsule, "_SealedCapsule__digest", original)


def test_four_shadows_are_pure_conserved_and_port_local() -> None:
    learner, model, optimizer, capsule, handles = _sealed()
    model_before = {name: row.detach().clone() for name, row in model.state_dict().items()}
    optimizer_before = runner._digest_bytes(recct._pack(optimizer.state_dict()))
    shadows = {
        mask: learner.shadow(capsule, handles, mask, learner.clone_rng(capsule))
        for mask in recct.MASKS
    }
    assert all(torch.equal(model.state_dict()[name], row) for name, row in model_before.items())
    assert runner._digest_bytes(recct._pack(optimizer.state_dict())) == optimizer_before
    assert recct.factorial_gradient_residual(shadows) <= 1e-5
    assert max(row.loss for row in shadows.values()) - min(
        row.loss for row in shadows.values()
    ) <= 1e-7
    lr = _gradient_difference(shadows["10"], shadows["00"])
    rl = _gradient_difference(shadows["01"], shadows["00"])
    allowed = {"encoder.weight", "encoder.bias", "message_head.weight"}
    assert {name for name, row in lr.items() if bool((row != 0).any())}.issubset(allowed)
    assert {name for name, row in rl.items() if bool((row != 0).any())}.issubset(allowed)
    lr_head = lr["message_head.weight"]
    rl_head = rl["message_head.weight"]
    head_mask = torch.zeros_like(lr_head, dtype=torch.bool)
    head_mask[0, 0] = True
    assert not bool(lr_head[~head_mask].any())
    assert not bool(rl_head[~head_mask].any())
    assert torch.allclose(lr_head, -rl_head, atol=1e-6, rtol=0)
    assert all(row.declared_path_count == 2 for row in shadows.values())
    assert all(row.duplicate_path_count == 0 for row in shadows.values())
    assert all(row.postaggregate_cancellation_path_count == 0 for row in shadows.values())
    assert all(row.structural_preaggregation_gate for row in shadows.values())


def test_geometry_support_rho_and_sign_destroyed_transform_reject_wrong_semantics() -> None:
    geometry = recct.geometry_receipt(recct.make_model(1701))
    assert geometry == {
        "shared_parameter": "message_head.weight",
        "shared_coordinate": (0, 0),
        "isolated_gradient_norm_ratio": 1.0,
        "shared_coordinate_cosine": -1.0,
        "support_per_port_per_update": 4,
        "identifying": True,
    }
    learner, _, _, capsule, handles = _sealed()
    base = learner.shadow(capsule, handles, "00", learner.clone_rng(capsule))
    scores = {
        "00": (("A", -0.8), ("B", -0.7)),
        "10": (("A", -0.6), ("B", -0.5)),
        "01": (("A", -0.9), ("B", -0.8)),
        "11": (("A", -0.7), ("B", -0.6)),
    }
    shadows = {
        mask: replace(base, mask=mask, confirmation_scores=score)
        for mask, score in scores.items()
    }
    signed = recct.credit_from_shadows(shadows, absolute=False)
    destroyed = recct.credit_from_shadows(shadows, absolute=True)
    assert signed.support_lr == signed.support_rl == 4
    assert signed.rho_lr == signed.rho_rl == 1.0
    assert signed.credit_lr > 0 and signed.credit_rl < 0
    assert destroyed.credit_lr > 0 and destroyed.credit_rl > 0
    wrong_support = replace(signed, support_lr=3)
    assert recct.select_credit_mask(wrong_support, "00") != "10"
    wrong_rho = replace(signed, rho_lr=0.5)
    assert recct.select_credit_mask(wrong_rho, "00") != "10"
    aggregate_left = learner.select(
        capsule, "G_AGG_SYM", "00", shadows, balanced_coin=0
    )
    aggregate_right = learner.select(
        capsule, "G_AGG_SYM", "00", shadows, balanced_coin=1
    )
    assert aggregate_left.credit.credit_lr == aggregate_left.credit.credit_rl
    assert aggregate_right.credit.credit_lr == aggregate_right.credit.credit_rl
    assert (aggregate_left.selected_mask, aggregate_right.selected_mask) == ("10", "01")


def test_fresh_commit_recomputes_selected_shadow_and_advances_only_live_state() -> None:
    learner, model, optimizer, capsule, handles = _sealed()
    shadows = {
        mask: learner.shadow(capsule, handles, mask, learner.clone_rng(capsule))
        for mask in recct.MASKS
    }
    selection = learner.select(capsule, "ALL_11", "00", shadows, balanced_coin=0)
    before = recct._state_digest(model.state_dict())
    commit = learner.commit(
        capsule,
        handles,
        selection,
        learner.clone_rng(capsule),
        live_model=model,
        live_optimizer=optimizer,
    )
    assert runner._tuple_equal(
        shadows["11"].transition_predicate(), commit.transition_predicate()
    )
    assert recct._state_digest(model.state_dict()) != before
    assert tuple(inspect.signature(learner.commit).parameters) == (
        "capsule",
        "handles",
        "selection",
        "rng",
        "live_model",
        "live_optimizer",
    )
    with pytest.raises(ValueError, match="selection"):
        learner.commit(
            capsule,
            handles,
            selection,
            learner.clone_rng(capsule),
            live_model=model,
            live_optimizer=optimizer,
        )


def test_public_shadow_receipt_contains_no_decodable_post_transition_state() -> None:
    learner, model, optimizer, capsule, handles = _sealed()
    shadow = learner.shadow(capsule, handles, "11", learner.clone_rng(capsule))
    assert "_state_payload" not in {field.name for field in fields(shadow)}
    assert not any(isinstance(value, (bytes, bytearray, memoryview)) for value in vars(shadow).values())
    with pytest.raises(AttributeError):
        getattr(shadow, "_state_payload")

    shadows = {
        mask: learner.shadow(capsule, handles, mask, learner.clone_rng(capsule))
        for mask in recct.MASKS
    }
    selection = learner.select(capsule, "ALL_11", "00", shadows, balanced_coin=0)
    public_selected_shadow = replace(
        shadows["11"], after_model_digest="public-receipt-cannot-carry-commit-state"
    )
    assert public_selected_shadow.after_model_digest != shadows["11"].after_model_digest
    commit = learner.commit(
        capsule,
        handles,
        selection,
        learner.clone_rng(capsule),
        live_model=model,
        live_optimizer=optimizer,
    )
    assert commit.after_model_digest == shadows["11"].after_model_digest


def test_retained_artifact_validator_reconstructs_rows_and_rejects_tampering() -> None:
    cache_root = Path.cwd() / ".pytest_cache"
    cache_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="recct-b1-retained-", dir=cache_root) as temporary:
        run_root = Path(temporary) / "retained"
        runner.train(
            run_root=run_root,
            source_commit="focused-source",
            full=False,
            authorization_token=None,
        )
        runner.evaluate(run_root=run_root)
        configuration = runner._read_json(run_root / "configuration_manifest.json")
        training = runner._read_json(run_root / "train_manifest.json")
        evaluation = runner._read_json(run_root / "evaluation_manifest.json")
        analysis = runner.analyze(run_root=run_root)

    validated = runner.validate_retained_artifacts(configuration, training, evaluation)
    assert analysis["branch"] == runner.TECHNICAL_ONLY_BRANCH
    assert analysis["activity_counts"] == dict(validated.activity_counts)
    assert validated.activity_counts == runner._counts(runner.RunConfiguration.technical())
    assert [
        (fit.arm, fit.master_seed, fit.orientation_replica)
        for fit in validated.fits
    ] == [
        (arm, 1701, replica)
        for arm in recct.ARMS
        for replica in (0, 1)
    ]
    assert all(
        left.exogenous_digest == right.exogenous_digest
        and left.omega == -right.omega
        for fit_index in range(0, len(validated.fits), 2)
        for left, right in zip(
            validated.fits[fit_index].updates,
            validated.fits[fit_index + 1].updates,
        )
    )

    wrong_label = copy.deepcopy(training)
    wrong_label["fits"][0]["arm"] = "G_SD"
    with pytest.raises(ValueError, match="fit|label"):
        runner.validate_retained_artifacts(configuration, wrong_label, evaluation)

    incomplete = copy.deepcopy(training)
    incomplete["fits"].pop()
    with pytest.raises(ValueError, match="incomplete|duplicated"):
        runner.validate_retained_artifacts(configuration, incomplete, evaluation)

    duplicate = copy.deepcopy(training)
    duplicate["fits"][-1] = copy.deepcopy(duplicate["fits"][0])
    with pytest.raises(ValueError, match="fit|label|duplicated"):
        runner.validate_retained_artifacts(configuration, duplicate, evaluation)

    tampered = copy.deepcopy(training)
    tampered_update = tampered["fits"][0]["updates"][0]
    tampered_update["exogenous_digest"] = "0" * 64
    with pytest.raises(ValueError, match="schedule|digest"):
        runner.validate_retained_artifacts(configuration, tampered, evaluation)

    selector_tamper = copy.deepcopy(training)
    selector_update = selector_tamper["fits"][0]["updates"][0]
    selector_update["credit"].update(
        {
            "credit_lr": 0.0,
            "credit_rl": 0.0,
            "rho_lr": 1.0,
            "rho_rl": 1.0,
            "conditional_lr": [0.0, 0.0, 0.0, 0.0],
            "conditional_rl": [0.0, 0.0, 0.0, 0.0],
        }
    )
    selector_update["selected_mask"] = "11"
    selector_update["direction_code"] = 0
    selector_update["active_port_count"] = 2
    with pytest.raises(ValueError, match="reconstructed selector"):
        runner.validate_retained_artifacts(configuration, selector_tamper, evaluation)

    wrong_direction = copy.deepcopy(training)
    direction_update = wrong_direction["fits"][0]["updates"][0]
    direction_update["direction_code"] = 1 - int(direction_update["direction_code"])
    with pytest.raises(ValueError, match="direction code"):
        runner.validate_retained_artifacts(configuration, wrong_direction, evaluation)

    producer_counts_only = copy.deepcopy(training)
    producer_counts_only["fits"] = []
    with pytest.raises(ValueError, match="incomplete|producer-count-only"):
        runner.validate_retained_artifacts(configuration, producer_counts_only, evaluation)

    wrong_evaluation = copy.deepcopy(evaluation)
    wrong_evaluation["cells"][0]["episodes"][0]["evaluation_seed"] = 9999
    with pytest.raises(ValueError, match="evaluation schedule"):
        runner.validate_retained_artifacts(configuration, training, wrong_evaluation)

    wrong_pool = copy.deepcopy(configuration)
    wrong_pool["training_pool"] = list(host.EVALUATION_POOL)
    with pytest.raises(ValueError, match="frozen schedule"):
        runner.validate_retained_artifacts(wrong_pool, training, evaluation)


def test_rng_split_checkpoint_tamper_branch_and_exact_activity_contract() -> None:
    left = runner.SiteKeyedRNG(3_001_701)
    right = runner.SiteKeyedRNG(3_001_701)
    assert [left.uniform("selector/coin") for _ in range(4)] == [
        right.uniform("selector/coin") for _ in range(4)
    ]
    with pytest.raises(ValueError):
        left.uniform("orientation-seed")
    assert set(host.TRAINING_POOL).isdisjoint(host.EVALUATION_POOL)
    full = runner.RunConfiguration.full()
    full.validate()
    assert runner._counts(full) == runner.FULL_ACTIVITY_CAPS
    with pytest.raises(ValueError, match="frozen schedule"):
        replace(full, train_episodes_per_replica=31).validate()
    assert runner._counts(runner.RunConfiguration.technical())["named_full_runs"] == 0
    assert runner._counts(runner.RunConfiguration.technical())["learner_update_calls"] == 40

    sidecar = {
        "checkpoint_digest": "checkpoint",
        "configuration_digest": "configuration",
        "checkpoint_selection": "none",
        "checkpoint_kind": "final",
    }
    runner.validate_checkpoint_sidecar(
        sidecar,
        checkpoint_digest="checkpoint",
        configuration_digest="configuration",
    )
    with pytest.raises(ValueError, match="sidecar"):
        runner.validate_checkpoint_sidecar(
            sidecar,
            checkpoint_digest="tampered-checkpoint",
            configuration_digest="configuration",
        )

    valid = {
        "readiness": True,
        "contract_activity": True,
        "information_split": True,
        "host_geometry": True,
        "matching": True,
    }
    metrics = {
        "alignment": {"RECCT_SIGNED": 0.75, "G_SD": 0.0, "G_AGG_SYM": 0.0},
        "crossing_rate": {"RECCT_SIGNED": 1.0},
        "heldout_return": {"RECCT_SIGNED": 0.8},
        "primary_return_contrasts": {"G_SD": 0.2, "G_AGG_SYM": 0.2, "ALL_11": 0.2},
        "positive_seed_pairs": {"G_SD": 4, "G_AGG_SYM": 4},
        "negative_orientation_halves": 0,
    }
    for key, expected in zip(valid, runner.BRANCH_PRECEDENCE[:5]):
        wrong = dict(valid)
        wrong[key] = False
        assert runner.select_branch(wrong, metrics) == expected
    assert runner.select_branch(valid, metrics) == "B_DIRECTED_CREDIT_EXPLORATORY_SIGNAL"
    directionless = {**metrics, "alignment": {**metrics["alignment"], "RECCT_SIGNED": 0.49}}
    assert runner.select_branch(valid, directionless) == "B_DIRECTION_INSENSITIVE_MASKING"
    generic = {**metrics, "alignment": {**metrics["alignment"], "G_SD": 0.60}}
    assert runner.select_branch(valid, generic) == "B_GENERIC_SPARSIFICATION_EQUIVALENCE"
    nontransfer = {**metrics, "negative_orientation_halves": 1}
    assert runner.select_branch(valid, nontransfer) == "B_FINITE_LOOKUP_OR_ROSTER_NONTRANSFER"
    no_utility = {
        **metrics,
        "heldout_return": {"RECCT_SIGNED": 0.64},
    }
    assert runner.select_branch(valid, no_utility) == "B_DIRECTED_SELECTION_WITHOUT_UTILITY"
    assert runner.TECHNICAL_ONLY_BRANCH not in runner.BRANCH_PRECEDENCE
