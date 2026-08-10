from __future__ import annotations

import argparse
from copy import deepcopy
import inspect
import json
from pathlib import Path

import pytest
import torch

from experiments.candidates.ec4g_r1 import (
    leave_receipt_content_learning_discriminator as b1,
)
from scripts import run_ec4g_b1_leave_receipt_content_learning_discriminator as runner


@pytest.fixture(scope="module")
def manifest() -> dict[str, object]:
    return b1.build_manifest(
        source_revision="TECHNICAL-PROOF-ONLY",
        run_id="ec4g-b1-proof",
        technical_only=True,
    )


@pytest.fixture(scope="module")
def preflight(manifest: dict[str, object]) -> dict[str, object]:
    return b1.preflight_report(manifest)


@pytest.fixture(scope="module")
def bounded_fixture() -> dict[str, object]:
    return b1.bounded_technical_fixture()


@pytest.fixture(scope="module")
def bounded_training() -> dict[str, object]:
    return b1.bounded_training_fixture()


def test_manifest_and_static_preflight_freeze_every_literal(
    manifest: dict[str, object], preflight: dict[str, object]
) -> None:
    assert b1.validate_manifest(manifest) == ()
    assert b1.validate_preflight(manifest, preflight) == ()
    assert preflight["all_passed"] is True
    assert tuple(preflight["gates"]) == tuple(f"P{i}_{suffix}" for i, suffix in (
        (0, "FROZEN_LITERAL_BINDING"),
        (1, "RANDOM_ACCESS_TAG_DONOR"),
        (2, "RECEIPT_REWARD_INPUT_FIREWALL"),
        (3, "EXACT_32_UNIT_CLASS_REPRESENTABILITY"),
        (4, "MODEL_AND_A2C_CONTRACT"),
        (5, "ANALYTIC_GATE_WITNESS"),
        (6, "EXACT_COUNTS_AND_CAPS"),
        (7, "TOTAL_BRANCH_MAP"),
    ))
    assert preflight["activity"] == b1._zero_activity()
    assert manifest["registered_fulls"] == 0


@pytest.mark.parametrize(
    "mutator",
    [
        lambda value: value.__setitem__("outer_seeds", [41_001]),
        lambda value: value.__setitem__("arms", ["R0", "RV"]),
        lambda value: value["learning"].__setitem__("blocks", 127),
        lambda value: value["thresholds"].__setitem__("q1_firewall_abs_max", 0.04),
        lambda value: value["caps"].__setitem__("optimizer_updates", 1),
        lambda value: value.__setitem__("branch_precedence", list(reversed(value["branch_precedence"]))),
    ],
)
def test_manifest_mutation_fails_closed(
    manifest: dict[str, object], mutator: object
) -> None:
    changed = deepcopy(manifest)
    mutator(changed)  # type: ignore[operator]
    assert b1.validate_manifest(changed) == (
        "manifest differs from the frozen EC4G-B1 literals",
    )


def test_random_access_tuple_seed_is_exact_and_treatment_free() -> None:
    signature = tuple(inspect.signature(b1.tuple_seed).parameters)
    assert signature == (
        "outer_seed",
        "split",
        "phase",
        "q",
        "arm",
        "episode",
        "lane",
        "draw_index",
    )
    assert b1.tuple_seed(
        41_001, "TRAIN", "EPISODE", "q0", "RV", 0, "latent_z", 0
    ) == 17_363_173_831_906_434_294
    assert b1.tuple_seed(
        41_001, "TRAIN", "EPISODE", "q0", "RV", 0, "latent_z", 0
    ) == b1.tuple_seed(
        41_001, "TRAIN", "EPISODE", "q0", "RV", 0, "latent_z", 0
    )


def test_named_coordinate_initialization_is_rng_free_and_order_independent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forward = b1.parameter_initialization_payload(41_001)
    reverse = b1.parameter_initialization_payload(
        41_001, tuple(reversed(b1.PARAMETER_ORDER))
    )
    assert set(forward) == set(reverse) == set(b1.PARAMETER_ORDER)
    assert all(torch.equal(forward[name], reverse[name]) for name in b1.PARAMETER_ORDER)
    assert {
        name: tuple(tensor.shape) for name, tensor in forward.items()
    } == b1.PARAMETER_SHAPES

    state_before = torch.get_rng_state().clone()

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("model initialization touched Torch/global RNG")

    monkeypatch.setattr(torch, "manual_seed", forbidden)
    monkeypatch.setattr(torch.random, "manual_seed", forbidden)
    monkeypatch.setattr(torch.random, "fork_rng", forbidden)
    monkeypatch.setattr(torch.nn.init, "uniform_", forbidden)
    monkeypatch.setattr(torch.nn.init, "kaiming_uniform_", forbidden)
    model = b1._new_model(41_001)
    assert torch.equal(torch.get_rng_state(), state_before)
    assert all(
        torch.equal(dict(model.named_parameters())[name], forward[name])
        for name in b1.PARAMETER_ORDER
    )


@pytest.mark.parametrize("split", b1.SPLITS)
def test_tag_domains_are_disjoint_complete_and_q_arm_blind(split: str) -> None:
    tags = b1.split_tags(41_001, split)
    lo, hi = b1.TAG_DOMAINS[split]
    assert len(tags) == b1.SPLIT_EPISODES[split]
    assert set(tags) == set(range(lo, hi + 1))
    assert len(tags) == len(set(tags))
    assert b1.BLIND_TAG not in tags
    assert tuple(inspect.signature(b1.split_tags).parameters) == ("outer_seed", "split")


@pytest.mark.parametrize("split", ("TRAIN", "CALIBRATION", "FORCED_EVAL"))
@pytest.mark.parametrize("q", b1.Q_VALUES)
def test_donor_mapping_is_fixed_nonself_and_never_tag_matching(split: str, q: str) -> None:
    tags = b1.split_tags(41_001, split)
    records = b1.donor_records(41_001, split, q)
    n = len(tags)
    assert len(records) == n
    for episode in range(n):
        donor_index = (episode + n // 2) % n
        assert donor_index != episode
        assert records[donor_index].record_index == donor_index
        assert records[donor_index].tag != tags[episode]


def test_complete_unit_construction_audit_is_closed() -> None:
    audit = b1.construction_audit(41_001)
    assert audit["all_passed"] is True
    assert audit["matched_body_checks"] == 6_144
    assert audit["matched_body_failures"] == 0
    assert audit["tuple_serializer_has_treatment_field"] is False


@pytest.mark.parametrize(
    ("physical", "sham"), (("RV", "PV"), ("RB", "PB"), ("RS", "PS"))
)
def test_matched_receipt_bodies_are_byte_identical(physical: str, sham: str) -> None:
    common = dict(
        outer_seed=41_001,
        split="FORCED_EVAL",
        q="q0",
        episode=17,
        own_y=1,
    )
    left = b1.receipt_body(arm=physical, **common)
    right = b1.receipt_body(arm=sham, **common)
    assert b1.canonical_bytes(left) == b1.canonical_bytes(right)
    physical_host = b1.FourStepRelayHost(arm=physical, **{key: common[key] for key in ("outer_seed", "split", "q", "episode")})
    sham_host = b1.FourStepRelayHost(arm=sham, **{key: common[key] for key in ("outer_seed", "split", "q", "episode")})
    assert b1.canonical_bytes(physical_host.receipt) == b1.canonical_bytes(sham_host.receipt)


def test_none_and_blind_bodies_cannot_leak_semantic_match() -> None:
    common = dict(
        outer_seed=41_001,
        split="FORCED_EVAL",
        q="q0",
        episode=8,
        own_y=1,
    )
    none = b1.receipt_body(arm="R0", **common)
    blind = b1.receipt_body(arm="RB", **common)
    assert none == {"present": 0, "tag": 0, "payload": 0}
    assert blind["present"] == 1
    assert blind["tag"] == 0xFFFF
    assert set(blind) == {"present", "tag", "payload"}


def test_reward_and_observation_firewalls_are_structural() -> None:
    assert tuple(inspect.signature(b1.terminal_reward).parameters) == (
        "z",
        "executed_bits",
        "physical_probe",
    )
    assert b1.terminal_reward(1, [1, 1], False) == 1.0
    assert b1.terminal_reward(1, [1, 1], True) == 0.98
    assert b1.terminal_reward(1, [1, 0], True) == -0.02
    assert b1.observation_vector(0, q="q1", x=1, current_tag=0x1234).numel() == 43
    assert b1.observation_vector(1).tolist()[4:] == [0.0] * 39
    assert b1.observation_vector(3).tolist()[4:] == [0.0] * 39


def test_four_step_host_has_one_probe_opportunity_and_exact_calls() -> None:
    host = b1.FourStepRelayHost(
        outer_seed=41_001,
        split="FORCED_EVAL",
        q="q0",
        arm="RV",
        episode=0,
    )
    observations = [host.step() for _ in range(4)]
    assert all(vector.shape == (43,) for vector in observations)
    assert host.transitions == 4
    assert host.probe_opportunities == 1
    with pytest.raises(RuntimeError):
        host.step()
    executed, reward = host.finish([0, 1])
    assert len(executed) == 2
    assert reward in (-0.02, 0.98)


def test_bounded_real_host_fixture_is_deterministic_and_has_zero_fulls(
    bounded_fixture: dict[str, object]
) -> None:
    assert b1.validate_bounded_technical_fixture(bounded_fixture) == ()
    assert bounded_fixture["registered_paired_fulls"] == 0
    assert bounded_fixture["result_bearing_runs"] == 0
    assert bounded_fixture["episodes"] == 2
    assert bounded_fixture["optimizer_updates"] == 0
    assert bounded_fixture["matched_body_equal"] is True
    assert [row["environment_transitions"] for row in bounded_fixture["rows"]] == [4, 4]
    assert [row["batched_policy_calls"] for row in bounded_fixture["rows"]] == [4, 4]
    assert [row["active_agent_forward_rows"] for row in bounded_fixture["rows"]] == [9, 9]


def test_training_block_is_exactly_fourteen_treatment_blind_episodes() -> None:
    order = b1.training_order(41_001, 0)
    assert len(order) == 14
    assert set(order) == {(q, arm) for q in b1.Q_VALUES for arm in b1.ARMS}
    assert order == b1.training_order(41_001, 0)
    assert order != b1.training_order(41_001, 1)


def test_bounded_training_fixture_exercises_one_exact_a2c_adam_update(
    bounded_training: dict[str, object]
) -> None:
    assert b1.validate_bounded_training_fixture(bounded_training) == ()
    assert bounded_training["registered_paired_fulls"] == 0
    assert bounded_training["result_bearing_runs"] == 0
    assert bounded_training["model_before"] != bounded_training["model_after"]
    assert bounded_training["optimizer_before"] != bounded_training["optimizer_after"]
    assert bounded_training["activity"] == {
        **b1._zero_activity(),
        "episodes": 14,
        "training_episodes": 14,
        "environment_transitions": 56,
        "batched_policy_calls": 56,
        "active_agent_forward_rows": 126,
        "learner_calls": 1,
        "trainer_calls": 1,
        "optimizer_updates": 1,
    }


def test_analytic_counterexample_and_calibration_witness_are_exact() -> None:
    report = b1.analytic_counterexample()
    assert report["q0"] == dict(
        zip(b1.ARMS, (0.570, 0.774, 0.598, 0.598, 0.730, 0.570, 0.570))
    )
    assert report["q1_finite_witness_inputs"] == pytest.approx(
        {"T": 0.026875, "C": 0.0, "V": 0.0}
    )
    assert report["q1_finite_witness_gates"] == {
        "DIRECT_TAU": "P",
        "EC4G": "A",
    }
    assert "never EC4G value" in report["branch_9_interpretation"]


def test_constructive_p3_has_exact_class_margins_and_zero_transition_fails() -> None:
    coordinates = b1.constructive_parameter_coordinates()
    for hidden in range(24, 29):
        assert coordinates[f"actor.weight[1,{hidden}]"] != 0.0
        assert coordinates[f"gru.bias_hh[{2 * b1.HIDDEN_SIZE + hidden}]"] != 0.0
        assert coordinates[f"gru.weight_ih[{b1.HIDDEN_SIZE + hidden},3]"] < 0.0
    certificate = b1.constructive_representability_certificate()
    assert certificate["passed"] is True
    assert certificate["exact_class_and_layout"] is True
    assert certificate["finite_tag_probe_count"] == 632
    assert certificate["finite_tag_probe_failures"] == 0
    assert all(value > 0.0 for value in certificate["checked_margins"].values())
    incapable = b1.constructive_representability_certificate(
        recurrent_transition_override="zero_recurrent"
    )
    assert incapable["passed"] is False
    assert incapable["parameter_match"] is True
    assert incapable["recurrent_transition_override"] == "zero_recurrent"
    assert incapable["finite_tag_probe_failures"] > 0
    assert "constructive recurrent transition override active" in incapable["issues"]


def test_direct_gate_cannot_consume_content_or_validity_inputs() -> None:
    class DirectFirewall(dict[str, float]):
        def __getitem__(self, key: str) -> float:
            if key in ("C", "V"):
                raise AssertionError("Direct consumed a forbidden gate input")
            return super().__getitem__(key)

    assert b1.gate_label("DIRECT_TAU", DirectFirewall(T=0.03)) == "P"
    assert b1.gate_label("DIRECT_TAU", DirectFirewall(T=0.00)) == "A"
    assert b1.gate_label("DIRECT_TAU", DirectFirewall(T=-0.03)) == "N"


@pytest.mark.parametrize(
    ("preflight", "gates", "delta", "expected"),
    [
        (False, {}, 0.0, b1.BRANCH_PRECEDENCE[0]),
        (True, {}, 0.0, b1.BRANCH_PRECEDENCE[1]),
        (True, {"tag_donor_match_audit": True, "q1_null_firewall": True}, 0.0, b1.BRANCH_PRECEDENCE[2]),
        (True, {"tag_donor_match_audit": True, "q1_null_firewall": True, "activity_complete": True}, 0.0, b1.BRANCH_PRECEDENCE[3]),
        (True, {"tag_donor_match_audit": True, "q1_null_firewall": True, "activity_complete": True, "forced_pair_invariance": True}, 0.0, b1.BRANCH_PRECEDENCE[4]),
        (True, {"tag_donor_match_audit": True, "q1_null_firewall": True, "activity_complete": True, "forced_pair_invariance": True, "q0_content": True, "generic_physical": True, "q0_gate_sanity": True}, 0.0, b1.BRANCH_PRECEDENCE[5]),
        (True, {key: True for key in ("tag_donor_match_audit", "q1_null_firewall", "activity_complete", "forced_pair_invariance", "q0_content", "generic_physical", "q0_gate_sanity", "q1_gate_divergence", "probe_selectivity")}, -0.01, b1.BRANCH_PRECEDENCE[6]),
        (True, {key: True for key in ("tag_donor_match_audit", "q1_null_firewall", "activity_complete", "forced_pair_invariance", "q0_content", "generic_physical", "q0_gate_sanity", "q1_gate_divergence", "probe_selectivity")}, 0.0, b1.BRANCH_PRECEDENCE[7]),
        (True, {key: True for key in ("tag_donor_match_audit", "q1_null_firewall", "activity_complete", "forced_pair_invariance", "q0_content", "generic_physical", "q0_gate_sanity", "q1_gate_divergence", "probe_selectivity")}, 0.02, b1.BRANCH_PRECEDENCE[8]),
    ],
)
def test_branch_precedence_is_first_true_and_total(
    preflight: bool, gates: dict[str, bool], delta: float, expected: str
) -> None:
    assert b1.classify_result(
        preflight_valid=preflight, gates=gates, delta_j=delta
    ) == expected


def test_static_invalid_result_has_exact_zero_activity(
    manifest: dict[str, object], preflight: dict[str, object]
) -> None:
    failed = deepcopy(preflight)
    failed["gates"]["P0_FROZEN_LITERAL_BINDING"]["passed"] = False
    failed["all_passed"] = False
    result = {
        "artifact_kind": "ec4g_b1_result",
        "assignment_id": b1.ASSIGNMENT_ID,
        "candidate": b1.CANDIDATE,
        "manifest": manifest,
        "manifest_identity": b1.manifest_identity(manifest),
        "preflight": failed,
        "branch": b1.BRANCH_PRECEDENCE[0],
        "activity": b1._zero_activity(),
        "units": [],
        "aggregates": None,
        "metric_gates": None,
    }
    # Fabricated failed preflight is rejected before its branch is trusted.
    assert b1.validate_result(manifest, result) == (
        "retained preflight P0_FROZEN_LITERAL_BINDING pass/issues inconsistency",
        "P0 gate/manifest literal binding mismatch",
    )


def test_retained_validation_and_validate_cli_have_no_runtime_surface(
    monkeypatch: pytest.MonkeyPatch,
    manifest: dict[str, object],
    preflight: dict[str, object],
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("retained validation entered a forbidden runtime surface")

    failed_preflight = deepcopy(preflight)
    failed_preflight["gates"]["P1_RANDOM_ACCESS_TAG_DONOR"] = {
        "passed": False,
        "issues": ["retained construction certificate failed"],
    }
    failed_preflight["all_passed"] = False
    result = {
        "artifact_kind": "ec4g_b1_result",
        "assignment_id": b1.ASSIGNMENT_ID,
        "candidate": b1.CANDIDATE,
        "manifest": manifest,
        "manifest_identity": b1.manifest_identity(manifest),
        "preflight": failed_preflight,
        "branch": b1.BRANCH_PRECEDENCE[0],
        "activity": b1._zero_activity(),
        "units": [],
        "aggregates": None,
        "metric_gates": None,
    }
    monkeypatch.setattr(b1, "preflight_report", forbidden)
    monkeypatch.setattr(b1, "tuple_seed", forbidden)
    monkeypatch.setattr(b1, "_uniform", forbidden)
    monkeypatch.setattr(b1, "_bit", forbidden)
    monkeypatch.setattr(b1, "split_tags", forbidden)
    monkeypatch.setattr(b1, "donor_records", forbidden)
    monkeypatch.setattr(b1, "run_treatment", forbidden)
    monkeypatch.setattr(b1, "run_unit", forbidden)
    monkeypatch.setattr(b1, "run_episode", forbidden)
    monkeypatch.setattr(b1, "_new_model", forbidden)
    monkeypatch.setattr(b1, "SharedGRUA2C", forbidden)
    monkeypatch.setattr(b1, "FourStepRelayHost", forbidden)
    monkeypatch.setattr(b1, "train_replica", forbidden)
    monkeypatch.setattr(torch.optim, "Adam", forbidden)
    monkeypatch.setattr(runner, "run_treatment", forbidden)

    assert b1.validate_result(manifest, result) == ()
    assert "run_treatment(" not in inspect.getsource(b1.validate_result)
    assert "preflight_report(" not in inspect.getsource(b1.validate_result)
    assert "run_treatment(" not in inspect.getsource(runner._validate_command)

    root = Path(f"C:/{runner.ROOT_MARKER}/pure-validation")
    monkeypatch.setattr(runner, "_require_root", lambda path: root)
    monkeypatch.setattr(
        runner,
        "_read_json",
        lambda path: manifest if path.name == runner.MANIFEST_NAME else result,
    )
    assert runner._validate_command(argparse.Namespace(run_root=root)) == 0


def test_runner_registered_full_is_exclusive_before_runtime(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, manifest: dict[str, object]
) -> None:
    root = tmp_path / runner.ROOT_MARKER
    root.mkdir()
    full_manifest = b1.build_manifest(
        source_revision="BOUND", run_id="one-shot", technical_only=False
    )
    (root / runner.MANIFEST_NAME).write_text(
        json.dumps(full_manifest), encoding="utf-8"
    )
    (root / runner.CLAIM_NAME).write_text("{}", encoding="utf-8")
    monkeypatch.setattr(runner, "_require_root", lambda path: root)
    monkeypatch.setattr(runner, "PROJECT_ROOT", Path.cwd().resolve())
    monkeypatch.setattr(runner, "_require_bound_manifest", lambda value: value)
    monkeypatch.setattr(runner, "_require_clean_claim_sources", lambda: None)
    with pytest.raises(FileExistsError):
        runner._registered_full_command(
            argparse.Namespace(manifest=root / runner.MANIFEST_NAME, run_root=root)
        )
