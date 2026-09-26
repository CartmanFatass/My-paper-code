from __future__ import annotations

from dataclasses import replace
import copy
import json
from pathlib import Path
import random
import subprocess
import sys
import types

import numpy as np
import pytest
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner as b01
from experiments.candidates.complementary_skill_learning.b02.runner import effective_config
from experiments.candidates.complementary_skill_learning.b04 import runner as b04
from experiments.candidates.complementary_skill_learning.b04.learning import TrainingLawAgent
from experiments.candidates.complementary_skill_learning.b05 import runner as r


@pytest.fixture(scope="module")
def spec():
    return replace(
        r.DEFAULT_SPEC,
        n_users=8,
        horizon=20,
        eval_lanes=2,
        training_lanes=2,
        training_rollouts=1,
        threads=1,
        small_model=True,
    )


def _build_agent(root: Path, spec: r.Spec, device: str):
    envs = b01.make_envs(spec, 1, spec.world_base)
    try:
        config = r.make_config(spec, envs)
    finally:
        for env in envs:
            env.close()
    b01.seed_rng(260923931)
    agent = TrainingLawAgent(
        config=config,
        arm="M",
        head_seed=260923932,
        aux_seed=260923934,
        low_action_seed=260923935,
        high_collection_seed=260923936,
        high_update_seed=260923937,
        log_dir=str(root / "logs"),
        device=torch.device(device),
    )
    return agent, config


def _artificial_input(root: Path, spec: r.Spec, device: str = "cpu"):
    root.mkdir(parents=True, exist_ok=True)
    outer_process = b04._capture_process_rng_state()
    agent, config = _build_agent(root, spec, device)
    config_snapshot = effective_config(config)
    # Deterministic non-training perturbations make every restored family differ
    # from a same-seed fresh construction, so an omitted load cannot pass.
    with torch.no_grad():
        for index, name in enumerate((*b01.MODULES, "g_head", "p_head"), start=1):
            parameter = next(getattr(agent, name).parameters())
            parameter.view(-1)[0].add_(index / 1000.0)
    for index, name in enumerate(("value_norm_coordinator", "value_norm_discoverer"), start=1):
        normalizer = getattr(agent, name)
        normalizer.mean = np.full_like(normalizer.mean, index * 0.125)
        normalizer.var = np.full_like(normalizer.var, 1.0 + index * 0.25)
        normalizer.count = float(100 + index)
    agent.target_mean = 1.25
    agent.target_std = 0.75
    for stream in agent._rng_streams.values():
        with stream.use():
            random.random()
            np.random.random()
            torch.rand(3, device=agent.device)

    remaining = np.random.default_rng()
    remaining.bit_generator.state = agent.rollout_buffer.get_sampler_rng_state()
    remaining.integers(0, 100, size=7)
    agent.rollout_buffer.set_sampler_rng_state(remaining.bit_generator.state)
    high = np.random.default_rng()
    high.bit_generator.state = copy.deepcopy(agent._high_sampler_state)
    high.integers(0, 100, size=11)
    agent._high_sampler_state = copy.deepcopy(high.bit_generator.state)
    b01.seed_rng(991337)
    random.random()
    np.random.random()
    torch.rand(5, device=agent.device)
    checkpoint = {
        "object_id": "complementary_skill_b04",
        "arm": "M",
        "stage": spec.training_rollouts,
        "config": config_snapshot,
        "native": {name: getattr(agent, name).state_dict() for name in b01.MODULES},
        "normalizers": {name: copy.deepcopy(getattr(agent, name)) for name in b01.NORMALIZERS},
        "auxiliary": agent.auxiliary_state_dict(),
        "rng": {
            "schema": "complementary_skill_b04_rng_v1",
            "default_process": copy.deepcopy(b04._capture_process_rng_state()),
            "private_streams": agent.rng_stream_state_dict(),
            "rollout_samplers": agent.sampler_rng_state_dict(),
        },
    }
    torch.save(checkpoint, root / "final.pt")
    r._restore_process_rng_state(outer_process)
    reference_root = root / "references"
    reference_root.mkdir()
    legacy_spec = b04.Spec(
        n_agents=spec.n_agents,
        n_users=spec.n_users,
        k=spec.k,
        horizon=spec.horizon,
        lanes=spec.training_lanes,
        rollouts=spec.training_rollouts,
        eval_lanes=spec.eval_lanes,
        small_model=spec.small_model,
    )
    own = b04.evaluate_panel(agent, legacy_spec, "own")
    uniform = b04.evaluate_panel(agent, legacy_spec, "uniform")
    final_identity = r._file_identity(root / "final.pt")
    summary = {
        "object_id": "complementary_skill_b04",
        "arm": "M",
        "status": "complete",
        "learner_config": config_snapshot,
        "final_private_rng_streams": agent.rng_stream_telemetry(),
        "final_sampler_rng_streams": agent.sampler_rng_telemetry(),
        "checkpoints": {"final": {
            **final_identity,
            "native_digest": b04.native_digest(agent),
            "frozen_digest": b04.frozen_digest(agent),
        }},
        "panels": {"final_own": own, "final_uniform": uniform},
    }
    b01.write_json(root / "summary.json", summary)
    b01.write_json(root / "config.json", {"object_id": "complementary_skill_b04", "arm": "M"})
    summary_identity = r._file_identity(root / "summary.json")
    config_identity = r._file_identity(root / "config.json")
    contract = r.InputContract(
        final_bytes=final_identity["bytes"],
        final_sha256=final_identity["sha256"],
        summary_bytes=summary_identity["bytes"],
        summary_sha256=summary_identity["sha256"],
        config_bytes=config_identity["bytes"],
        config_sha256=config_identity["sha256"],
        native_digest=b04.native_digest(agent),
        frozen_digest=b04.frozen_digest(agent),
        physical_sha256=own["physical_initial_state_sha256"],
        r0_label_sha256=uniform["selected_label_stream_sha256"],
    )
    return contract, agent


@pytest.fixture(scope="module")
def completed(tmp_path_factory, spec):
    root = tmp_path_factory.mktemp("b05-source")
    contract, _ = _artificial_input(root, spec)
    out = root.parent / "b05-output"
    summary = r.run_evaluation(
        root, out, "technical-check", spec=spec, contract=contract, device="cpu"
    )
    return root, out, contract, summary


def test_fixed_protocol_and_production_input_binding():
    assert r.PANELS == ("O", "R0", "S0", "R1", "S1", "R2", "S2", "R3", "S3")
    assert r.S_SEEDS == {"S0": 260923951, "S1": 260923952, "S2": 260923953, "S3": 260923954}
    assert r.R_SEEDS == {"R0": 262624105, "R1": 262624106, "R2": 262624107, "R3": 262624108}
    assert r.NON_LABEL_SEED == 262624105
    assert r.PRODUCTION_INPUT.final_bytes == 27_128_511
    assert r.PRODUCTION_INPUT.final_sha256 == "df222836fca1b4a4aaf87408d4f024fbb796e7107c004a40f1f5ecc64201c39f"
    assert r.DEFAULT_SPEC.eval_lanes * r.DEFAULT_SPEC.horizon * len(r.PANELS) == 144_000


def test_complete_real_path_restores_freezes_and_counts(completed, spec):
    _, _, _, summary = completed
    assert summary["status"] == "complete"
    assert summary["scientific_reading_status"] == "valid"
    assert tuple(summary["panels"]) == r.PANELS
    assert summary["restored"]["frozen_digest"] == summary["frozen_after"]["frozen_digest"]
    assert summary["restored"]["private_rng_streams"] == summary["frozen_after"]["private_rng"]
    assert summary["restored"]["sampler_rng_streams"] == summary["frozen_after"]["sampler_rng"]
    assert summary["counts"] == {
        "started_fits": 0,
        "model_constructions": 1,
        "checkpoint_loads": 1,
        "training_transitions": 0,
        "stored_transitions": 0,
        "native_updates": 0,
        "optimizer_calls": 0,
        "normalizer_updates": 0,
        "evaluation_transitions": 9 * spec.eval_lanes * spec.horizon,
        "evaluation_episodes": 9 * spec.eval_lanes,
        "O_transitions": spec.eval_lanes * spec.horizon,
        "S_transitions": 4 * spec.eval_lanes * spec.horizon,
        "R_transitions": 4 * spec.eval_lanes * spec.horizon,
    }
    assert summary["observed_mutation_calls"] == {
        "native_update_calls": 0,
        "auxiliary_fit_calls": 0,
        "optimizer_steps": 0,
        "store_calls": 0,
        "normalizer_updates": 0,
    }
    assert all(
        not any(panel["observed_mutation_calls"].values())
        for panel in summary["panels"].values()
    )
    assert all(row["exact"] for row in summary["identity_controls"].values())


def test_restore_matches_checkpoint_weights_heads_and_normalizers(completed, spec, tmp_path):
    source, _, contract, source_run = completed
    outer = b04._capture_process_rng_state()
    try:
        agent, restored = r.restore_agent(
            source / "final.pt", spec, "cpu", tmp_path / "restore-logs",
            json.loads((source / "summary.json").read_text()), contract,
        )
    finally:
        r._restore_process_rng_state(outer)
    checkpoint = torch.load(source / "final.pt", map_location="cpu", weights_only=False)
    for module_name, expected_state in checkpoint["native"].items():
        actual_state = getattr(agent, module_name).state_dict()
        assert actual_state.keys() == expected_state.keys()
        assert all(torch.equal(actual_state[name], expected_state[name]) for name in actual_state)
    for head in ("g_head", "p_head"):
        actual_state = getattr(agent, head).state_dict()
        expected_state = checkpoint["auxiliary"][head]
        assert all(torch.equal(actual_state[name], expected_state[name]) for name in actual_state)
    for name in b01.NORMALIZERS:
        actual, expected = getattr(agent, name), checkpoint["normalizers"][name]
        assert (actual is None) == (expected is None)
        if actual is not None:
            assert actual.__dict__.keys() == expected.__dict__.keys()
            for key in actual.__dict__:
                np.testing.assert_array_equal(actual.__dict__[key], expected.__dict__[key])
    assert agent.target_mean == checkpoint["auxiliary"]["target_mean"] == 1.25
    assert agent.target_std == checkpoint["auxiliary"]["target_std"] == 0.75
    assert not restored["optimizer_restore"]["native"]["checkpoint_state_present"]
    assert not any(restored["optimizer_restore"]["native"]["state_entries"].values())
    assert restored["optimizer_restore"]["auxiliary"]["checkpoint_state_present"]
    assert restored["frozen_digest"] == source_run["restored"]["frozen_digest"]


def test_full_trajectory_and_summary_arithmetic(completed, spec):
    _, out, _, summary = completed
    for panel in r.PANELS:
        row = summary["panels"][panel]
        with np.load(out / row["trajectory"]["file"]) as data:
            assert data["states"].shape[0] == spec.horizon + 1
            assert data["observations"].shape[0] == spec.horizon + 1
            assert data["raw_mean_actions"].shape[:3] == (spec.horizon, spec.eval_lanes, spec.n_agents)
            np.testing.assert_array_equal(data["clipped_actions"], np.clip(data["raw_mean_actions"], -1, 1))
            assert data["episode_ends"][:-1].sum() == 0
            assert data["episode_ends"][-1].all()
            assert data["renewal"].sum() == spec.horizon // spec.k
            returns = data["rewards"].sum(axis=0)
            np.testing.assert_allclose(returns, row["returns_U"], rtol=0, atol=0)
            total = data["total_reward"].sum(axis=0) / spec.horizon
            np.testing.assert_allclose(total, row["native_scores_J"], rtol=1e-7, atol=1e-7)
            # Skills persist through the boundary and the trajectory contains no
            # hidden-reset operation or hidden-state substitute.
            for t in range(spec.horizon):
                if t % spec.k:
                    np.testing.assert_array_equal(data["individual_labels"][t], data["individual_labels"][t - 1])


def test_real_gru_hidden_carries_across_skill_boundary(tmp_path, spec, monkeypatch):
    agent, _ = _build_agent(tmp_path, spec, "cpu")
    original = b01.low_actions
    hidden_inputs, hidden_outputs = [], []

    def observed(agent_arg, observations, skills, hidden, *, deterministic):
        hidden_inputs.append(np.asarray(hidden).copy())
        result = original(
            agent_arg, observations, skills, hidden, deterministic=deterministic
        )
        hidden_outputs.append(np.asarray(result[1]).copy())
        return result

    monkeypatch.setattr(b01, "low_actions", observed)
    r.evaluate_panel(agent, spec, "O", tmp_path)
    assert len(hidden_inputs) == spec.horizon
    np.testing.assert_array_equal(hidden_inputs[0], np.zeros_like(hidden_inputs[0]))
    for t in range(1, spec.horizon):
        np.testing.assert_array_equal(hidden_inputs[t], hidden_outputs[t - 1])
    assert np.any(hidden_inputs[spec.k] != 0)


def test_mutation_audit_counts_and_prohibits_real_entry_paths(tmp_path, spec):
    agent, _ = _build_agent(tmp_path, spec, "cpu")
    with r.EvaluationCallAudit(agent) as audit:
        with pytest.raises(RuntimeError, match="prohibited call reached update"):
            agent.update()
        with pytest.raises(RuntimeError, match="prohibited call reached store_transition_batch"):
            agent.store_transition_batch()
        with pytest.raises(RuntimeError, match="prohibited call reached step"):
            agent.coordinator_optimizer.step()
        with pytest.raises(RuntimeError, match="prohibited call reached update"):
            agent.value_norm_coordinator.update(np.asarray([1.0]))
        assert audit.snapshot() == {
            "native_update_calls": 1,
            "auxiliary_fit_calls": 0,
            "optimizer_steps": 1,
            "store_calls": 1,
            "normalizer_updates": 1,
        }


def test_s_streams_are_isolated_persistent_and_real_factors(completed, spec):
    _, out, _, summary = completed
    for panel in ("S0", "S1", "S2", "S3"):
        row = summary["panels"][panel]
        assert row["outer_process_rng"]["restored"]
        assert row["outer_process_rng"]["before"] == row["outer_process_rng"]["after"]
        assert row["label_rng"]["after"]["uses"] == spec.horizon // spec.k
        assert row["label_rng"]["before"]["state_sha256"] != row["label_rng"]["after"]["state_sha256"]
        with np.load(out / row["trajectory"]["file"]) as data:
            renewal = data["renewal"]
            assert np.isfinite(data["team_factor_log_probs"][renewal]).all()
            assert np.isfinite(data["individual_factor_log_probs"][renewal]).all()
            assert np.isnan(data["team_factor_log_probs"][~renewal]).all()
            order = data["renewal_order"][renewal]
            expected = np.broadcast_to(np.arange(spec.n_agents), order.shape)
            np.testing.assert_array_equal(order, expected)


def test_s_uses_unchanged_team_law_and_actual_ar_prefix(tmp_path, spec):
    agent, _ = _build_agent(tmp_path, spec, "cpu")
    envs = b01.make_envs(spec, spec.eval_lanes, spec.world_base)
    decoder = agent.skill_coordinator.skill_decoder
    original = decoder.forward
    calls = []

    def observed(_self, *args, **kwargs):
        result = original(*args, **kwargs)
        step = int(kwargs.get("step", args[4] if len(args) > 4 else 0))
        prefix = kwargs.get("agent_skills_so_far", args[3] if len(args) > 3 else None)
        calls.append((step, None if prefix is None else prefix.detach().cpu().clone(), result.detach().cpu().clone()))
        return result

    decoder.forward = types.MethodType(observed, decoder)
    try:
        b01.seed_rng(r.NON_LABEL_SEED)
        states, observations = b01.native._reset_all(envs)
        stream = r.PersistentTorchRNG(r.S_SEEDS["S0"])
        outer_before = r._process_telemetry()
        team, individual, team_lp, individual_lp, order = r._select_labels(
            "S0", agent, states, observations, None, stream
        )
        assert r._process_telemetry() == outer_before
        assert [step for step, _, _ in calls] == list(range(spec.n_agents + 1))
        assert calls[0][1] is None  # step zero is the unchanged learned team law
        np.testing.assert_array_equal(order, np.broadcast_to(np.arange(spec.n_agents), order.shape))
        for position in range(spec.n_agents):
            prefix = calls[position + 1][1]
            expected_prefix = torch.as_tensor(individual[:, :position], dtype=torch.long)
            assert torch.equal(prefix, expected_prefix) if position else prefix is None
        team_dist = torch.distributions.Categorical(logits=calls[0][2])
        np.testing.assert_allclose(team_lp, team_dist.log_prob(torch.as_tensor(team)).numpy(), rtol=0, atol=1e-7)
        for position in range(spec.n_agents):
            dist = torch.distributions.Categorical(logits=calls[position + 1][2])
            expected = dist.log_prob(torch.as_tensor(individual[:, position])).numpy()
            np.testing.assert_allclose(individual_lp[:, position], expected, rtol=0, atol=1e-7)
        decoder.forward = original
        repeated = r._select_labels(
            "S0", agent, states, observations, None,
            r.PersistentTorchRNG(r.S_SEEDS["S0"]),
        )
        for actual, expected in zip(repeated, (team, individual, team_lp, individual_lp, order)):
            np.testing.assert_array_equal(actual, expected)
    finally:
        decoder.forward = original
        for env in envs:
            env.close()


def test_r0_draw_order_and_reproducible_label_digest(completed, spec):
    _, out, _, summary = completed
    row = summary["panels"]["R0"]
    assert row["label_rng"]["before_state_sha256"] != row["label_rng"]["after_state_sha256"]
    rng = np.random.Generator(np.random.PCG64(r.R_SEEDS["R0"]))
    with np.load(out / row["trajectory"]["file"]) as data:
        for t in range(0, spec.horizon, spec.k):
            team = rng.integers(0, 6, size=spec.eval_lanes, dtype=np.int64)
            individual = rng.integers(0, 6, size=(spec.eval_lanes, spec.n_agents), dtype=np.int64)
            np.testing.assert_array_equal(data["team_labels"][t], team)
            np.testing.assert_array_equal(data["individual_labels"][t], individual)
            np.testing.assert_allclose(data["team_factor_log_probs"][t], r.UNIFORM_LOG_FACTOR, rtol=0, atol=2e-7)
            np.testing.assert_allclose(data["individual_factor_log_probs"][t], r.UNIFORM_LOG_FACTOR, rtol=0, atol=2e-7)


def test_fixed_aggregate_and_r0_sensitivity_identity(completed):
    _, _, _, summary = completed
    for metric, row in summary["aggregates"].items():
        s = np.stack([r._metric_arrays(summary["panels"][f"S{i}"])[metric] for i in range(4)])
        rr = np.stack([r._metric_arrays(summary["panels"][f"R{i}"])[metric] for i in range(4)])
        o = r._metric_arrays(summary["panels"]["O"])[metric]
        np.testing.assert_allclose(row["Delta_SR4_world"], s.mean(0) - rr.mean(0), rtol=0, atol=0)
        np.testing.assert_allclose(row["Delta_SO_world"], s.mean(0) - o, rtol=0, atol=0)
        assert abs(row["R0_sensitivity_identity"]["residual"]) <= 1e-12


def test_input_identity_refusal_happens_before_output(tmp_path, spec):
    source = tmp_path / "source"
    contract, _ = _artificial_input(source, spec)
    (source / "config.json").write_text("{}\n")
    out = tmp_path / "never-created"
    with pytest.raises(ValueError, match="input identity differs"):
        r.run_evaluation(source, out, "technical", spec=spec, contract=contract, device="cpu")
    assert not out.exists()


def _write_admitted_root(out: Path):
    out.mkdir()
    sha = "a" * 40
    command = "b" * 64
    claim = "claim-fixture"
    admission = {
        "schema_version": 1,
        "direction": r.DIRECTION,
        "sha": sha,
        "command_sha256": command,
        "parent_pid": 1,
        "child_pid": 2,
    }
    b01.write_json(out / "launch-manifest.json", {
        "direction": r.DIRECTION,
        "sha": sha,
        "command_sha256": command,
        "output_root": str(out.resolve()),
        "claim_key": claim,
    })
    b01.write_json(out / "launch-status.json", {
        "status": "release_unknown", "claim_key": claim,
    })
    b01.write_json(out / "admission-preflight.json", {
        "passed": True,
        "direction": r.DIRECTION,
        "sha": sha,
        "claim_key": claim,
    })
    (out / "stdout.log").write_bytes(b"")
    (out / "stderr.log").write_bytes(b"")
    return admission


def test_admitted_metadata_root_runs_once_and_preserves_launcher_files(completed, spec, tmp_path):
    source, _, contract, _ = completed
    out = tmp_path / "admitted-output"
    admission = _write_admitted_root(out)
    summary = r.run_evaluation(
        source,
        out,
        admission["sha"],
        spec=spec,
        contract=contract,
        device="cpu",
        admission=admission,
    )
    assert summary["status"] == "complete"
    assert r._ADMITTED_METADATA.issubset({path.name for path in out.iterdir()})
    with pytest.raises(FileExistsError, match="scientific content"):
        r.prepare_output_root(out, admission)


def test_partial_panel_artifact_survives_failure(tmp_path, spec, monkeypatch):
    agent, _ = _build_agent(tmp_path, spec, "cpu")
    original = b01.physical_step
    calls = 0

    def fail_after_rows(env, action):
        nonlocal calls
        calls += 1
        if calls == spec.eval_lanes * 3 + 1:
            raise RuntimeError("injected physical failure")
        return original(env, action)

    monkeypatch.setattr(b01, "physical_step", fail_after_rows)
    counts = {"evaluation_transitions": 0, "evaluation_episodes": 0, "O_transitions": 0}
    with pytest.raises(RuntimeError, match="injected physical failure"):
        r.evaluate_panel(agent, spec, "O", tmp_path, counter=counts)
    row = json.loads((tmp_path / "panel_O.json").read_text())
    assert row["status"] == "failed"
    assert row["completed_steps"] == 3
    assert counts == {
        "evaluation_transitions": spec.eval_lanes * 3,
        "evaluation_episodes": 0,
        "O_transitions": spec.eval_lanes * 3,
    }
    assert row["actual_counts_at_failure"] == counts
    assert (tmp_path / row["trajectory"]["file"]).is_file()


def test_cli_refuses_unadmitted_invocation_before_output(tmp_path):
    script = Path(r.__file__).resolve().parents[4] / "scripts" / "run_complementary_skill_learning_b05.py"
    out = tmp_path / "out"
    completed = subprocess.run(
        [sys.executable, str(script), "--input-root", str(tmp_path), "--launch-sha", "0" * 40, "--out", str(out)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert completed.returncode != 0
    assert "missing HMASD admission" in completed.stderr
    assert not out.exists()


@pytest.mark.skipif(not torch.cuda.is_available(), reason="requires actual CUDA runtime")
def test_bounded_cuda_artificial_restore_identity_and_rng(tmp_path, spec):
    source = tmp_path / "cuda-source"
    contract, _ = _artificial_input(source, spec, device="cuda")
    summary = r.run_evaluation(
        source, tmp_path / "cuda-out", "technical-cuda", spec=spec,
        contract=contract, device="cuda",
    )
    assert summary["status"] == "complete"
    assert all(row["exact"] for row in summary["identity_controls"].values())
    assert summary["resources"]["cuda_peak_allocated_bytes"] > 0
    assert summary["restored"]["private_rng_streams"] == summary["frozen_after"]["private_rng"]
    assert summary["restored"]["sampler_rng_streams"] == summary["frozen_after"]["sampler_rng"]
