from __future__ import annotations

from dataclasses import asdict, replace
from collections import defaultdict
import copy
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner as b01
from experiments.candidates.complementary_skill_learning.b01.learning import (
    MIXTURE_POLICY_WEIGHT,
    MIXTURE_UNIFORM_WEIGHT,
    MixtureSkillDecoder,
)
from experiments.candidates.complementary_skill_learning.b02.runner import effective_config
from experiments.candidates.complementary_skill_learning.b07 import runner as r
from hmasd.networks import SkillDecoder


@pytest.fixture(scope="module")
def spec():
    return replace(
        r.DEFAULT_SPEC,
        n_users=8,
        horizon=20,
        lanes=2,
        rollouts=1,
        eval_lanes=2,
        threads=1,
        small_model=True,
    )


def _run_batch(root: Path, spec: r.Spec, device: str):
    root.mkdir()
    summaries = {}
    summaries["M"] = r.run_fit(
        "M", root / "M", "technical-check", spec=spec, device=device
    )
    reference = summaries["M"]["M_final_S_reference"]
    summaries["E"] = r.run_fit(
        "E",
        root / "E",
        "technical-check",
        spec=spec,
        device=device,
        reference_path=reference["path"],
        reference_sha256=reference["sha256"],
    )
    summaries["U"] = r.run_fit(
        "U", root / "U", "technical-check", spec=spec, device=device
    )
    return summaries


@pytest.fixture(scope="module")
def batch(tmp_path_factory, spec):
    root = tmp_path_factory.mktemp("b07-batch")
    return root, _run_batch(root / "outputs", spec, "cpu")


def _make_agent(tmp_path: Path, spec: r.Spec, arm: str):
    envs = r.make_envs(spec, spec.lanes, spec.train_world_base)
    try:
        config = r.make_config(spec, envs, arm)
    finally:
        for env in envs:
            env.close()
    r.seed_rng(spec.init_seed)
    return r._build_agent(spec, config, arm, tmp_path, torch.device("cpu")), config


def test_fixed_protocol_and_only_e_config_change(tmp_path, spec):
    assert r.ARMS == ("M", "E", "U")
    assert r.S_SEEDS == {f"S{i}": 260924101 + i for i in range(4)}
    assert r.R_SEEDS == {f"R{i}": 262625201 + i for i in range(4)}
    assert r.NON_LABEL_SEED == 260924105
    assert (
        r.DEFAULT_SPEC.init_seed,
        r.DEFAULT_SPEC.head_seed,
        r.DEFAULT_SPEC.train_rng_seed,
        r.DEFAULT_SPEC.aux_seed,
        r.DEFAULT_SPEC.low_action_seed,
        r.DEFAULT_SPEC.high_collection_seed,
        r.DEFAULT_SPEC.high_update_seed,
    ) == tuple(range(260924001, 260924008))
    assert r.DEFAULT_SPEC.train_world_base == 2300000

    e, e_config = _make_agent(tmp_path / "E", spec, "E")
    m, m_config = _make_agent(tmp_path / "M", spec, "M")
    u, u_config = _make_agent(tmp_path / "U", spec, "U")
    assert (e.arm, m.arm, u.arm) == ("E", "M", "U")
    assert (e_config.lambda_h, m_config.lambda_h, u_config.lambda_h) == (0.0, 0.07, 0.07)
    assert not e_config.disable_high_level_training
    assert not m_config.disable_high_level_training
    assert u_config.disable_high_level_training
    e_fields, m_fields = effective_config(e_config), effective_config(m_config)
    differing = {key for key in e_fields if e_fields[key] != m_fields[key]}
    assert differing == {"lambda_h"}


def test_native_decoder_mixes_individual_once_and_never_team(tmp_path, spec):
    agent, _ = _make_agent(tmp_path, spec, "E")
    decoder = agent.skill_coordinator.skill_decoder
    assert isinstance(decoder, MixtureSkillDecoder)
    batch, width = 3, agent.config.embedding_dim
    encoded_state = torch.randn(batch, 1, width)
    encoded_observations = torch.randn(batch, spec.n_agents, width)
    team = torch.tensor([0, 1, 2])
    prefix = torch.tensor([[0, 1], [2, 3], [4, 5]])
    query = encoded_observations[:, 2:3]
    with torch.no_grad():
        native_team = SkillDecoder.forward(decoder, encoded_state, encoded_observations)
        actual_team = decoder(encoded_state, encoded_observations)
        native_individual = SkillDecoder.forward(
            decoder,
            encoded_state,
            encoded_observations,
            team,
            prefix,
            step=3,
            agent_specific_query=query,
        )
        actual_individual = decoder(
            encoded_state,
            encoded_observations,
            team,
            prefix,
            step=3,
            agent_specific_query=query,
        )
    torch.testing.assert_close(actual_team, native_team, rtol=0, atol=0)
    expected = (
        MIXTURE_POLICY_WEIGHT * torch.softmax(native_individual, dim=-1)
        + MIXTURE_UNIFORM_WEIGHT / 6.0
    )
    torch.testing.assert_close(torch.exp(actual_individual), expected, rtol=1e-6, atol=1e-7)


def test_entropy_is_finite_with_zero_probability_from_extreme_team_logits():
    probabilities = np.asarray([[1.0, 0.0, 0.0, 0.0, 0.0, 0.0]], np.float32)
    entropy = r._entropy_from_probabilities(probabilities)
    assert np.array_equal(entropy, np.asarray([-0.0], np.float32))
    logits = torch.tensor([[50.0, -50.0, -50.0, -50.0, -50.0, -50.0]])
    distribution = torch.distributions.Categorical(logits=logits)
    assert torch.isfinite(distribution.entropy()).all()
    assert distribution.probs[0, 1:].min() >= 0.0


def test_full_batch_initialization_streams_counts_and_outputs(batch, spec):
    root, summaries = batch
    assert [summaries[arm]["arm"] for arm in ("M", "E", "U")] == ["M", "E", "U"]
    assert len(summaries["M"]["panels"]) == 10
    assert len(summaries["E"]["panels"]) == 10
    assert len(summaries["U"]["panels"]) == 5
    assert sum(len(summary["panels"]) for summary in summaries.values()) == 25
    assert len({summary["initial_native_digest"] for summary in summaries.values()}) == 1
    assert len({summary["initial_frozen_digest"] for summary in summaries.values()}) == 1
    assert len({summary["initial_default_rng_state_sha256"] for summary in summaries.values()}) == 1
    assert len({json.dumps(summary["initial_private_rng_streams"], sort_keys=True) for summary in summaries.values()}) == 1
    assert len({json.dumps(summary["initial_sampler_rng_streams"], sort_keys=True) for summary in summaries.values()}) == 1

    for arm, summary in summaries.items():
        assert summary["status"] == "complete"
        assert summary["object_id"] == "complementary_skill_b07"
        assert summary["counts"]["training_transitions"] == 40
        assert summary["counts"]["native_updates"] == 1
        expected_eval = (10 if arm in {"M", "E"} else 5) * 40
        assert summary["counts"]["evaluation_transitions"] == expected_eval
        assert summary["counts"]["evaluation_episodes"] == (10 if arm in {"M", "E"} else 5) * 2
        assert summary["label_flow_checks"]["failures"] == 0
        assert (root / "outputs" / arm / "initial.pt").is_file()
        assert (root / "outputs" / arm / "final.pt").is_file()
        assert (root / "outputs" / arm / "training.jsonl").is_file()
        assert (root / "outputs" / arm / "auxiliary_predictions.jsonl").is_file()
        saved = json.loads((root / "outputs" / arm / "summary.json").read_text())
        assert saved["summary_storage"]["kind"] == "compact_versionable_view"
        assert "actual_joint_occupancy" not in saved
        assert "auxiliary_history" not in saved
        assert "d2_retained_work" not in saved
        assert len(saved["training_rows"]) == 1
        assert saved["bulk_locators"]["training_rows"]["sha256"] == summary[
            "training_log"
        ]["sha256"]
        assert saved["bulk_locators"]["training_occupancy"]["sha256"] == summary[
            "training_occupancy"
        ]["sha256"]

    for name in ("initial_R0", "final_R0", "final_R1", "final_R2", "final_R3"):
        assert len({summary["panels"][name]["selected_label_stream_sha256"] for summary in summaries.values()}) == 1
    assert summaries["M"]["panels"]["initial_S0"]["selected_label_stream_sha256"] == summaries["E"]["panels"]["initial_S0"]["selected_label_stream_sha256"]
    for name in ("native_scores_J", "connected_users_per_step"):
        np.testing.assert_array_equal(
            summaries["M"]["panels"]["initial_R0"][name],
            summaries["E"]["panels"]["initial_R0"][name],
        )
        np.testing.assert_array_equal(
            summaries["M"]["panels"]["initial_R0"][name],
            summaries["U"]["panels"]["initial_R0"][name],
        )
        np.testing.assert_array_equal(
            summaries["M"]["panels"]["initial_S0"][name],
            summaries["E"]["panels"]["initial_S0"][name],
        )
    for summary in summaries.values():
        assert len({panel["physical_initial_state_sha256"] for panel in summary["panels"].values()}) == 1
        assert all(not any(panel["observed_mutation_calls"].values()) for panel in summary["panels"].values())


def test_actual_entropy_intervention_training_and_isolation(batch):
    _, summaries = batch
    m, e, u = summaries["M"], summaries["E"], summaries["U"]
    assert m["first_rollout_facts_sha256"] == e["first_rollout_facts_sha256"]
    m_read = m["training_rows"][0]["coordinator_update_reading"]
    e_read = e["training_rows"][0]["coordinator_update_reading"]
    assert m_read["lambda_h"] == 0.07 and e_read["lambda_h"] == 0.0
    assert abs(e_read["entropy_objective_reconstructed"]) < 1e-6
    assert abs(m_read["entropy_objective_reconstructed"]) > 1e-6
    assert m_read["total_loss"] != e_read["total_loss"]
    assert m_read["post_update_gradient_norm"] != e_read["post_update_gradient_norm"]
    for summary in (m, e):
        assert summary["native_optimizer_calls"]["coordinator"] > 0
        assert summary["training_rows"][0]["relative_initialization_displacement"]["coordinator"] > 0
    assert u["native_optimizer_calls"]["coordinator"] == 0
    assert u["training_rows"][0]["relative_initialization_displacement"]["coordinator"] == 0
    assert u["uniform_factor_audits"]
    assert m["final_private_rng_streams"]["low_actions"] == e["final_private_rng_streams"]["low_actions"]
    assert m["final_sampler_rng_streams"]["remaining_learner"] == e["final_sampler_rng_streams"]["remaining_learner"]


def test_completed_contract_allows_s0_labels_to_change_with_policy(batch, spec):
    _, summaries = batch
    changed = copy.deepcopy(summaries["M"])
    changed["panels"]["final_S0"]["selected_label_stream_sha256"] = "changed-policy-labels"
    r._validate_completed_contract(changed, spec)


def test_recurrent_hidden_carries_within_panel_and_resets_between_panels(
    tmp_path, spec, monkeypatch
):
    agent, _ = _make_agent(tmp_path / "agent", spec, "M")
    out = tmp_path / "eval"
    (out / "raw").mkdir(parents=True)
    original = b01.low_actions
    inputs, outputs = [], []

    def observed(*args, **kwargs):
        inputs.append(np.asarray(args[3]).copy())
        result = original(*args, **kwargs)
        outputs.append(np.asarray(result[1]).copy())
        return result

    monkeypatch.setattr(b01, "low_actions", observed)
    counts = defaultdict(int)
    with r.b05.EvaluationCallAudit(agent) as audit:
        r.evaluate_panel(
            agent, spec, "initial", "R0", out,
            counter=counts, call_audit=audit,
        )
    assert len(inputs) == spec.horizon
    np.testing.assert_array_equal(inputs[0], np.zeros_like(inputs[0]))
    for t in range(1, spec.horizon):
        np.testing.assert_array_equal(inputs[t], outputs[t - 1])
    assert np.any(inputs[spec.k] != 0)

    inputs.clear()
    outputs.clear()
    with r.b05.EvaluationCallAudit(agent) as audit:
        r.evaluate_panel(
            agent, spec, "final", "R1", out,
            counter=counts, call_audit=audit,
        )
    np.testing.assert_array_equal(inputs[0], np.zeros_like(inputs[0]))


def test_s_probabilities_reference_and_common_context_scoring(batch, spec):
    root, summaries = batch
    m, e = summaries["M"], summaries["E"]
    reference = m["M_final_S_reference"]
    assert reference["context_rows"] == 4 * 2 * 2
    assert reference["factor_distributions"] == 4 * 2 * 2 * 7
    validated = r.validate_reference(
        reference["path"], reference["sha256"], spec,
        expected_source_launch_sha="technical-check",
    )
    assert validated["metadata"]["source_final_native_digest"] == m["final_native_digest"]
    score = e["common_context_scoring"]
    assert score["batches"] == 8
    assert score["context_rows"] == 16
    assert score["factor_distributions"] == 112
    assert score["environment_transitions"] == score["rng_draws"] == 0
    assert (root / "outputs" / "E" / "raw" / "E_on_M_final_S_reference.npz").is_file()
    trajectory = root / "outputs" / "M" / "raw" / "final_S0_trajectory.npz"
    with np.load(trajectory) as data:
        renewal = data["renewal"]
        team = data["team_labels"][renewal]
        individual = data["individual_labels"][renewal]
        team_probs = data["team_factor_probabilities"][renewal]
        individual_probs = data["individual_factor_probabilities"][renewal]
        selected_team = np.take_along_axis(team_probs, team[..., None], axis=-1).squeeze(-1)
        selected_individual = np.take_along_axis(
            individual_probs, individual[..., None], axis=-1
        ).squeeze(-1)
        np.testing.assert_allclose(
            np.log(selected_team), data["team_factor_log_probs"][renewal], rtol=0, atol=2e-6
        )
        np.testing.assert_allclose(
            np.log(selected_individual),
            data["individual_factor_log_probs"][renewal],
            rtol=0,
            atol=2e-6,
        )


def test_actual_primary_and_contrast_arrays(batch, spec):
    _, summaries = batch
    result = r.aggregate_batch(summaries["M"], summaries["E"], summaries["U"])
    for metric in ("J", "users", "coverage", "quality", "height"):
        row = result[metric]
        assert row["P_E_S_minus_U_R_world"].shape == (spec.eval_lanes,)
        assert row["D_E_S_minus_M_S_world"].shape == (spec.eval_lanes,)
        assert row["G_E_world"].shape == (spec.eval_lanes,)
        assert row["G_M_world"].shape == (spec.eval_lanes,)
        assert row["I_world"].shape == (spec.eval_lanes,)
        assert row["identity_residual"] == 0.0


def test_reference_refuses_bad_digest_and_metadata_before_output(tmp_path, batch, spec):
    _, summaries = batch
    reference = summaries["M"]["M_final_S_reference"]
    out = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="SHA256 differs"):
        r.run_fit(
            "E", out, "technical-check", spec=spec, device="cpu",
            reference_path=reference["path"], reference_sha256="0" * 64,
        )
    assert not out.exists()

    validated = r.validate_reference(
        reference["path"], reference["sha256"], spec,
        expected_source_launch_sha="technical-check",
    )
    arrays = validated["arrays"]
    metadata = dict(validated["metadata"])
    metadata["arm"] = "E"
    corrupt = tmp_path / "corrupt.npz"
    np.savez_compressed(corrupt, **arrays, metadata_json=np.asarray(json.dumps(metadata)))
    with pytest.raises(ValueError, match="metadata differs: arm"):
        r.run_fit(
            "E", out, "technical-check", spec=spec, device="cpu",
            reference_path=corrupt, reference_sha256=r._sha256_file(corrupt),
        )
    assert not out.exists()


def test_reference_refuses_wrong_source_before_output_or_model(
    tmp_path, batch, spec, monkeypatch
):
    _, summaries = batch
    reference = summaries["M"]["M_final_S_reference"]
    validated = r.validate_reference(
        reference["path"], reference["sha256"], spec,
        expected_source_launch_sha="technical-check",
    )
    metadata = dict(validated["metadata"])
    metadata["source_launch_sha"] = "different-published-source"
    wrong_source = tmp_path / "wrong-source.npz"
    np.savez_compressed(
        wrong_source,
        **validated["arrays"],
        metadata_json=np.asarray(json.dumps(metadata)),
    )
    model_calls = []

    def forbidden_model_construction(*args, **kwargs):
        model_calls.append((args, kwargs))
        raise AssertionError("wrong-source reference reached model construction")

    monkeypatch.setattr(r, "_build_agent", forbidden_model_construction)
    out = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="source_launch_sha differs"):
        r.run_fit(
            "E", out, "technical-check", spec=spec, device="cpu",
            reference_path=wrong_source,
            reference_sha256=r._sha256_file(wrong_source),
        )
    assert model_calls == []
    assert not out.exists()


@pytest.mark.parametrize(
    "field",
    (
        "source_final_native_digest",
        "source_final_frozen_digest",
        "source_final_checkpoint_sha256",
    ),
)
def test_reference_refuses_malformed_final_sha256_before_output(
    tmp_path, batch, spec, field
):
    _, summaries = batch
    reference = summaries["M"]["M_final_S_reference"]
    validated = r.validate_reference(
        reference["path"], reference["sha256"], spec,
        expected_source_launch_sha="technical-check",
    )
    metadata = dict(validated["metadata"])
    metadata[field] = "not-a-sha256"
    malformed = tmp_path / f"malformed-{field}.npz"
    np.savez_compressed(
        malformed,
        **validated["arrays"],
        metadata_json=np.asarray(json.dumps(metadata)),
    )
    out = tmp_path / f"must-not-exist-{field}"
    with pytest.raises(ValueError, match=f"malformed {field}"):
        r.run_fit(
            "E", out, "technical-check", spec=spec, device="cpu",
            reference_path=malformed,
            reference_sha256=r._sha256_file(malformed),
        )
    assert not out.exists()


def test_reference_accepts_team_zero_and_rejects_labels_dimensions_and_mass(
    tmp_path, batch, spec
):
    _, summaries = batch
    reference = summaries["M"]["M_final_S_reference"]
    validated = r.validate_reference(
        reference["path"], reference["sha256"], spec,
        expected_source_launch_sha="technical-check",
    )

    def save(name, arrays, metadata):
        path = tmp_path / f"{name}.npz"
        np.savez_compressed(
            path, **arrays, metadata_json=np.asarray(json.dumps(metadata))
        )
        return path

    arrays = copy.deepcopy(validated["arrays"])
    team = arrays["team_probabilities"]
    team[(0,) * (team.ndim - 1)] = np.asarray([1, 0, 0, 0, 0, 0], team.dtype)
    team_zero = save("team-zero", arrays, validated["metadata"])
    accepted = r.validate_reference(
        team_zero, r._sha256_file(team_zero), spec,
        expected_source_launch_sha="technical-check",
    )
    assert accepted["arrays"]["team_probabilities"].min() == 0.0

    bad_labels = copy.deepcopy(validated["arrays"])
    bad_labels["team_labels"] = bad_labels["team_labels"].astype(np.float32)
    label_path = save("float-labels", bad_labels, validated["metadata"])
    with pytest.raises(ValueError, match="integer support"):
        r.validate_reference(
            label_path, r._sha256_file(label_path), spec,
            expected_source_launch_sha="technical-check",
        )

    bad_dimensions = dict(validated["metadata"])
    bad_dimensions["state_dim"] += 1
    dimension_path = save("bad-dimensions", validated["arrays"], bad_dimensions)
    with pytest.raises(ValueError, match="metadata differs: state_dim"):
        r.validate_reference(
            dimension_path, r._sha256_file(dimension_path), spec,
            expected_source_launch_sha="technical-check",
        )

    bad_mass = copy.deepcopy(validated["arrays"])
    bad_mass["team_probabilities"] *= 0.5
    mass_path = save("bad-mass", bad_mass, validated["metadata"])
    with pytest.raises(ValueError, match="not normalized"):
        r.validate_reference(
            mass_path, r._sha256_file(mass_path), spec,
            expected_source_launch_sha="technical-check",
        )


def test_started_output_failure_retains_honest_summary(tmp_path, spec, monkeypatch):
    out = tmp_path / "failed-fit"

    def fail_environment_construction(*args, **kwargs):
        raise RuntimeError("deliberate environment construction failure")

    monkeypatch.setattr(r, "make_envs", fail_environment_construction)
    with pytest.raises(RuntimeError, match="deliberate environment construction failure"):
        r.run_fit("M", out, "technical-check", spec=spec, device="cpu")

    saved = json.loads((out / "summary.json").read_text())
    assert saved["status"] == "failed"
    assert saved["failure"]["type"] == "RuntimeError"
    assert saved["counts"]["started_fits"] == 0
    assert (out / "config.json").is_file()
    assert saved["summary_storage"]["kind"] == "compact_versionable_view"


@pytest.mark.parametrize(
    "args",
    (
        ["--arm", "X", "--seed", str(r.FIXED_SEED)],
        ["--arm", "M", "--seed", "1"],
        ["--arm", "E", "--seed", str(r.FIXED_SEED)],
        ["--arm", "M", "--seed", str(r.FIXED_SEED), "--reference", "x", "--reference-sha256", "0"],
    ),
)
def test_cli_rejects_bad_fixed_inputs_before_admission(tmp_path, args):
    out = tmp_path / "must-not-exist"
    result = subprocess.run(
        [
            sys.executable,
            str(b01.ROOT / "scripts/run_complementary_skill_learning_b07.py"),
            *args,
            "--launch-sha",
            "unadmitted",
            "--out",
            str(out),
        ],
        cwd=b01.ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "missing HMASD admission" not in result.stderr
    assert not out.exists()


def test_cli_refuses_valid_unadmitted_invocation_before_output(tmp_path):
    out = tmp_path / "must-not-exist"
    result = subprocess.run(
        [
            sys.executable,
            str(b01.ROOT / "scripts/run_complementary_skill_learning_b07.py"),
            "--arm", "M", "--seed", str(r.FIXED_SEED),
            "--launch-sha", "unadmitted", "--out", str(out),
        ],
        cwd=b01.ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "missing HMASD admission" in result.stderr
    assert not out.exists()


@pytest.mark.skipif(not torch.cuda.is_available(), reason="requires actual CUDA runtime")
def test_actual_cuda_full_b07_batch(tmp_path, spec):
    summaries = _run_batch(tmp_path / "cuda-batch", spec, "cuda")
    result = r.aggregate_batch(summaries["M"], summaries["E"], summaries["U"])
    assert summaries["M"]["status"] == summaries["E"]["status"] == summaries["U"]["status"] == "complete"
    assert result["J"]["P_E_S_minus_U_R_world"].shape == (spec.eval_lanes,)

