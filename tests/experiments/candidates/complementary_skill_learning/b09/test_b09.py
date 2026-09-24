from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, replace
import json
import math
from pathlib import Path
import shutil

import numpy as np
import pytest
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner as b01
from experiments.candidates.complementary_skill_learning.b02.runner import effective_config
from experiments.candidates.complementary_skill_learning.b05 import runner as b05
from experiments.candidates.complementary_skill_learning.b07 import runner as b07
from experiments.candidates.complementary_skill_learning.b09 import runner as r
from scripts import run_complementary_skill_b09 as entry


@pytest.fixture(scope="module")
def specs():
    common = replace(
        b07.DEFAULT_SPEC,
        n_users=8,
        horizon=20,
        lanes=2,
        rollouts=1,
        eval_lanes=2,
        threads=1,
        small_model=True,
    )
    return {
        "B07": common,
        "B08": replace(
            common,
            init_seed=260924041,
            head_seed=260924042,
            train_rng_seed=260924043,
            aux_seed=260924044,
            low_action_seed=260924045,
            high_collection_seed=260924046,
            high_update_seed=260924047,
            train_world_base=2400000,
        ),
    }


def _artifact(path: Path, root: Path) -> r.ArtifactContract:
    identity = r._file_identity(path, str(path.relative_to(root)))
    return r.ArtifactContract(
        identity["path"], identity["bytes"], identity["sha256"]
    )


def _make_source(
    root: Path, bank: str, spec: b07.Spec
) -> tuple[r.BankContract, dict[str, object]]:
    root.mkdir(parents=True)
    (root / "raw").mkdir()
    outer_rng = b07._capture_process_rng_state()
    try:
        envs = b07.make_envs(spec, 1, spec.eval_world_base)
        try:
            config = b07.make_config(spec, envs, "U")
        finally:
            for env in envs:
                env.close()
        b07.seed_rng(spec.init_seed)
        agent = b07._build_agent(spec, config, "U", root, torch.device("cpu"))
        learner_config = effective_config(config)
        final = b07.save_checkpoint(agent, root / "final.pt", learner_config, spec.rollouts)
        counts = defaultdict(int)
        panels = {}
        with b05.EvaluationCallAudit(agent) as audit:
            for stream in r.STREAM_ORDER:
                panel, _ = b07.evaluate_panel(
                    agent,
                    spec,
                    "final",
                    stream,
                    root,
                    counter=counts,
                    call_audit=audit,
                )
                panels[f"final_{stream}"] = panel
        launch_sha = f"technical-{bank.lower()}"
        protocol = (
            None
            if bank == "B07"
            else {
                "protocol_id": "complementary_skill_b08",
                "source_module": "technical.fixture",
                "launch_sha": launch_sha,
                "spec": asdict(spec),
            }
        )
        config_body = {
            "object_id": b07.OBJECT,
            "arm": "U",
            "launch_sha": launch_sha,
            "spec": asdict(spec),
        }
        summary = {
            "object_id": b07.OBJECT,
            "direction": r.DIRECTION,
            "arm": "U",
            "launch_sha": launch_sha,
            "spec": asdict(spec),
            "status": "complete",
            "learner_config": learner_config,
            "checkpoints": {"final": final},
            "final_native_digest": b07.native_digest(agent),
            "final_frozen_digest": b07.frozen_digest(agent),
            "final_private_rng_streams": agent.rng_stream_telemetry(),
            "final_sampler_rng_streams": agent.sampler_rng_telemetry(),
            "panels": panels,
        }
        if protocol is not None:
            config_body["adapter_protocol"] = protocol
            summary["adapter_protocol"] = protocol
        b07.write_json(root / "config.json", config_body)
        b07.write_json(root / "summary.json", summary)
        artifact_paths = [root / "config.json", root / "summary.json", root / "final.pt"]
        for stream in r.STREAM_ORDER:
            artifact_paths.extend(
                [
                    root / "raw" / f"final_{stream}.json",
                    root / "raw" / f"final_{stream}_trajectory.npz",
                ]
            )
        contract = r.BankContract(
            bank=bank,
            source_launch_sha=launch_sha,
            adapter_protocol_id=(None if bank == "B07" else "complementary_skill_b08"),
            source_spec=asdict(spec),
            final_native_digest=summary["final_native_digest"],
            final_frozen_digest=summary["final_frozen_digest"],
            artifacts=tuple(_artifact(path, root) for path in artifact_paths),
        )
        return contract, summary
    finally:
        b07._restore_process_rng_state(outer_rng)


@pytest.fixture(scope="module")
def completed(tmp_path_factory, specs):
    root = tmp_path_factory.mktemp("b09-real-policy")
    contracts = {}
    source_summaries = {}
    source_roots = {}
    for bank in r.BANK_ORDER:
        source_roots[bank] = root / bank
        contracts[bank], source_summaries[bank] = _make_source(
            source_roots[bank], bank, specs[bank]
        )
    out = root / "out"
    summary = r.run_evaluation(
        source_roots["B07"],
        source_roots["B08"],
        out,
        "technical-b09",
        device="cpu",
        contracts=contracts,
    )
    return root, out, summary, contracts, source_summaries


def test_production_protocol_and_asset_identities_are_fixed():
    assert r.FIXED_SEED == 260924051
    assert r.NON_LABEL_SEED == 260924105
    assert r.R_SEEDS == {f"R{i}": 262625201 + i for i in range(4)}
    assert r.PANEL_ORDER == tuple(
        [f"B07_R{i}" for i in range(4)]
        + [f"B08_R{i}" for i in range(4)]
        + [f"B07_H{i}" for i in range(4)]
        + [f"B08_H{i}" for i in range(4)]
    )
    assert sum(len(contract.artifacts) for contract in r.PRODUCTION_CONTRACTS.values()) == 22
    assert r.PRODUCTION_CONTRACTS["B07"].adapter_protocol_id is None
    assert r.PRODUCTION_CONTRACTS["B08"].adapter_protocol_id == "complementary_skill_b08"
    assert all(
        contract.source_spec["threads"] == 4
        for contract in r.PRODUCTION_CONTRACTS.values()
    )


def test_real_policy_batch_reproduces_original_b07_r_before_h_and_freezes(completed):
    _, out, summary, _, _ = completed
    assert summary["status"] == "complete"
    assert summary["completed_panels"] == list(r.PANEL_ORDER)
    assert summary["r_reproduction_gate"] == {
        "required": 8,
        "passed": 8,
        "released_H": True,
    }
    assert all(row["exact"] for row in summary["r_reproductions"].values())
    assert all(
        all(item["exact"] for item in row["arrays"].values())
        for row in summary["r_reproductions"].values()
    )
    assert summary["zero_learning"] == {
        "new_fits": 0,
        "training_transitions": 0,
        "optimizer_updates": 0,
        "storage_calls": 0,
        "normalizer_updates": 0,
    }
    assert summary["counts"]["evaluation_transitions"] == 640
    assert summary["counts"]["evaluation_agent_transitions"] == 3840
    assert summary["counts"]["low_action_forward_batches"] == 320
    assert summary["counts"]["proposal_batches"] == 32
    assert all(not any(row.values()) for row in summary["observed_mutation_calls"].values())
    for bank in r.BANK_ORDER:
        assert (
            summary["restored"][bank]["frozen_digest"]
            == summary["frozen_after"][bank]["frozen_digest"]
        )
        assert all(
            value == 0
            for value in summary["restored"][bank]["optimizer_restore"]["native"]["state_entries"].values()
        )
        assert summary["restored"][bank]["optimizer_restore"]["auxiliary"]["checkpoint_state_present"]
    saved = json.loads((out / "summary.json").read_text())
    assert saved["status"] == "complete"
    assert (out / "config.json").is_file()
    assert (out / "source.json").is_file()
    assert (out / "progress.json").is_file()


def test_independent_pcg64_proposals_and_h_delivery_law(completed, specs):
    _, out, summary, _, _ = completed
    for bank in r.BANK_ORDER:
        spec = specs[bank]
        for index, stream in enumerate(r.STREAM_ORDER):
            rng = np.random.Generator(np.random.PCG64(r.R_SEEDS[stream]))
            expected_team, expected_individual = [], []
            for _ in range(spec.horizon // spec.k):
                expected_team.append(rng.integers(0, 6, spec.eval_lanes, dtype=np.int64))
                expected_individual.append(
                    rng.integers(
                        0, 6, (spec.eval_lanes, spec.n_agents), dtype=np.int64
                    )
                )
            expected_team = np.asarray(expected_team)
            expected_individual = np.asarray(expected_individual)
            with np.load(out / "raw" / f"{bank}_H{index}_proposal_delivery.npz") as h:
                np.testing.assert_array_equal(h["team_proposals"], expected_team)
                np.testing.assert_array_equal(h["individual_proposals"], expected_individual)
                np.testing.assert_array_equal(h["delivered_team_labels"], expected_team)
                np.testing.assert_array_equal(
                    h["delivered_individual_labels"],
                    np.broadcast_to(expected_individual[:1], expected_individual.shape),
                )
                np.testing.assert_array_equal(
                    h["individual_proposal_log_probs"],
                    np.full(expected_individual.shape, -math.log(6), np.float32),
                )
                np.testing.assert_array_equal(
                    h["delivered_individual_log_probs"][0],
                    np.full(expected_individual.shape[1:], -math.log(6), np.float32),
                )
                np.testing.assert_array_equal(
                    h["delivered_individual_log_probs"][1:], 0.0
                )
            with np.load(out / "raw" / f"{bank}_R{index}_proposal_delivery.npz") as redraw:
                np.testing.assert_array_equal(
                    redraw["individual_proposals"], redraw["delivered_individual_labels"]
                )
            assert summary["pair_divergence"][f"{bank}_H{index}"]["proposal_stream_exact"]


def test_first_k_identity_recurrent_carry_clipping_and_later_behaviour(completed):
    _, out, summary, _, _ = completed
    for bank in r.BANK_ORDER:
        for index in range(4):
            divergence = summary["pair_divergence"][f"{bank}_H{index}"]
            assert divergence["first_k"] == 10
            assert all(divergence["first_k_exact"].values())
            assert divergence["first_changed_step"]["individual_labels"] in {10, 20, None}
            with np.load(out / "raw" / f"{bank}_H{index}_recurrent_flow.npz") as flow:
                np.testing.assert_array_equal(
                    flow["hidden_input_sha256"][1:], flow["hidden_output_sha256"][:-1]
                )
            with np.load(out / "raw" / f"{bank}_H{index}_trajectory.npz") as trajectory:
                np.testing.assert_array_equal(
                    trajectory["clipped_actions"],
                    np.clip(trajectory["raw_mean_actions"], -1.0, 1.0),
                )
    assert any(
        row["changed_step_counts"]["raw_mean_actions"] > 0
        for row in summary["pair_divergence"].values()
    )
    assert any(
        row["changed_step_counts"]["physical_states"] > 0
        for row in summary["pair_divergence"].values()
    )


def test_r_trajectory_schema_unchanged_and_bulk_diagnostics_stay_out_of_summary(completed):
    _, out, summary, _, _ = completed
    for bank in r.BANK_ORDER:
        for index in range(4):
            with np.load(out / "raw" / f"{bank}_R{index}_trajectory.npz") as trajectory:
                assert tuple(trajectory.files) == r.OLD_TRAJECTORY_KEYS
                assert trajectory["states"].shape[0] == 21
                assert trajectory["team_labels"].shape[0] == 20
    rendered = json.dumps(b01.jsonable(summary))
    assert '"team_proposals": [' not in rendered
    assert '"individual_proposals": [' not in rendered
    assert '"hidden_input_l2": [' not in rendered
    assert "proposal_delivery.npz" in rendered
    assert len(rendered) < 1_000_000


def test_aggregation_keeps_bank_world_stream_and_tail_units(completed, specs):
    _, _, summary, _, _ = completed
    for bank in r.BANK_ORDER:
        for metric in ("J", "users", "coverage", "quality", "height"):
            row = summary["aggregates"][bank][metric]
            assert np.asarray(row["H_minus_R_world"]).shape == (specs[bank].eval_lanes,)
            assert set(row["R_stream_world_values"]) == {f"R{i}" for i in range(4)}
            assert set(row["H_stream_world_values"]) == {f"H{i}" for i in range(4)}
            expected = np.asarray(row["world_mean_H4"]) - np.asarray(row["world_mean_R4"])
            np.testing.assert_array_equal(row["H_minus_R_world"], expected)
            assert row["H_minus_R"] == float(expected.mean())


def test_wrong_artifact_refuses_before_output(completed, tmp_path):
    root, _, _, contracts, _ = completed
    damaged = tmp_path / "damaged-B07"
    shutil.copytree(root / "B07", damaged)
    with (damaged / "config.json").open("ab") as stream:
        stream.write(b"\n")
    out = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="B07 input identity differs: config.json"):
        r.run_evaluation(
            damaged,
            root / "B08",
            out,
            "technical-b09",
            device="cpu",
            contracts=contracts,
        )
    assert not out.exists()


def test_wrong_source_spec_arm_stage_and_adapter_are_rejected(completed):
    root, _, _, contracts, _ = completed
    info = r.validate_bank_input(root / "B08", contracts["B08"])
    summary = json.loads(json.dumps(info["summary"]))
    config = json.loads(json.dumps(info["config"]))
    checkpoint = info["checkpoint"]

    wrong = dict(summary)
    wrong["arm"] = "M"
    with pytest.raises(ValueError, match="not the frozen B07-engine U asset"):
        r._validate_source_semantics(contracts["B08"], wrong, config, checkpoint)
    wrong = json.loads(json.dumps(summary))
    wrong["spec"]["horizon"] += 1
    with pytest.raises(ValueError, match="summary Spec differs"):
        r._validate_source_semantics(contracts["B08"], wrong, config, checkpoint)
    wrong_checkpoint = dict(checkpoint)
    wrong_checkpoint["stage"] = 0
    with pytest.raises(ValueError, match="checkpoint source/arm/stage/config differs"):
        r._validate_source_semantics(
            contracts["B08"], summary, config, wrong_checkpoint
        )
    wrong = json.loads(json.dumps(config))
    wrong["adapter_protocol"]["protocol_id"] = "complementary_skill_b07"
    with pytest.raises(ValueError, match="config adapter provenance differs"):
        r._validate_source_semantics(contracts["B08"], summary, wrong, checkpoint)


def test_panel_failure_retains_readable_partial_facts(completed, tmp_path, monkeypatch):
    root, _, _, contracts, _ = completed
    info = r.validate_bank_input(root / "B07", contracts["B07"])
    panel_out = tmp_path / "panel-failure"
    (panel_out / "raw").mkdir(parents=True)
    agent, spec, _ = r._restore_agent(info, panel_out, torch.device("cpu"))
    original = b01.low_actions
    calls = 0

    def fail_after_one(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("fixture low-policy failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(b01, "low_actions", fail_after_one)
    with b05.EvaluationCallAudit(agent) as audit:
        with pytest.raises(RuntimeError, match="fixture low-policy failure"):
            r.evaluate_panel(
                agent,
                spec,
                "B07",
                "H",
                "R0",
                panel_out,
                counter=defaultdict(int),
                call_audit=audit,
            )
    partial = json.loads((panel_out / "raw" / "B07_H0.json").read_text())
    assert partial["status"] == "failed"
    assert partial["completed_steps"] == 1
    assert "fixture low-policy failure" in partial["error"]
    assert (panel_out / "raw" / "B07_H0_trajectory.npz").is_file()


def test_cli_requires_admission_before_dispatch(monkeypatch, tmp_path):
    calls = []

    def admitted(*args, **kwargs):
        calls.append("admission")
        return {"sha": "abc"}

    def dispatched(*args, **kwargs):
        calls.append("evaluation")

    monkeypatch.setattr(entry, "require_admission", admitted)
    monkeypatch.setattr(r, "run_evaluation", dispatched)
    assert entry.main(
        [
            "--seed", "260924051",
            "--launch-sha", "abc",
            "--b07-input-root", str(tmp_path / "B07"),
            "--b08-input-root", str(tmp_path / "B08"),
            "--out", str(tmp_path / "out"),
            "--device", "cuda",
        ]
    ) == 0
    assert calls == ["admission", "evaluation"]
