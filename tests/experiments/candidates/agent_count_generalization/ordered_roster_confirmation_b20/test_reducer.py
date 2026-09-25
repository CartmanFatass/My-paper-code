"""Fixed three-block artifact validation and unrounded t decision."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.agent_count_generalization.ordered_roster_confirmation_b20 import reducer
from experiments.candidates.agent_count_generalization.ordered_roster_confirmation_b20.bindings import (
    BLOCKS, EVALUATION_ORDER, OBJECT_ID, PRODUCTION_SPEC_VALUES, SCHEDULES, WORLD_SEED_BASES,
)


def _json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, allow_nan=False), encoding="utf-8")


def _identity(path: Path, relative: str) -> dict:
    raw = path.read_bytes()
    return {"path": path.name, "relative_to_arm": relative,
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _synthetic_panel(arm_out: Path, arm: str, stage: int, n: int,
                     coverage: float) -> dict:
    worlds = list(range(WORLD_SEED_BASES[n], WORLD_SEED_BASES[n] + 32))
    j = coverage - .1
    trace_rel = f"raw/trace_stage{stage:02d}_n{n}.npz"
    trace_path = arm_out / trace_rel
    trace_path.write_bytes(f"synthetic trace {arm} {stage} {n}".encode())
    row = {
        "status": "complete", "arm": arm, "policy_stage": stage,
        "after_rollout": stage, "test_n": n, "world_seeds": worlds,
        "runtime_seed": WORLD_SEED_BASES[n] + 51,
        "steps": 16_000, "episodes": 32, "resets": 32, "policy_step_calls": 500,
        "initial_world_identity": {
            name: {"shape": [32], "dtype": "float32", "sha256": f"fixed-{name}-n{n}"}
            for name in ("states", "observations", "uav_positions", "user_positions")
        },
        "J": [j] * 32, "scalar_returns": [j * 500 / n] * 32,
        "uav_height_means_per_world": [100.0] * 32,
        "component_means": {
            "coverage_reward": [coverage] * 32, "quality_reward": [coverage] * 32,
            "energy_penalty": [.1] * 32, "total_reward": [j] * 32,
        },
        "service_arrays": {
            "E_eligible_users_per_step": [40.0] * 32,
            "S_served_users_per_step": [50 * coverage] * 32,
            "U_eligible_unserved_users_per_step": [40 - 50 * coverage] * 32,
        },
        "optimizer_calls": {"discoverer_actor": 0, "discoverer_critic": 0},
        "training_storage_calls": 0, "frozen_weights_and_normalizers": True,
        "parameter_normalizer_digest_before": f"frozen-{arm}-{stage}",
        "parameter_normalizer_digest_after": f"frozen-{arm}-{stage}",
        "normalizers_before": {}, "normalizers_after": {},
        "post_transition_semantics": True,
        "trace": _identity(trace_path, trace_rel),
    }
    _json(arm_out / f"panel_stage{stage:02d}_n{n}.json", row)
    return row


def _synthetic_production_block(root: Path, block: int, sources: dict) -> Path:
    binding = BLOCKS[block]
    out = root / binding.tag
    launch_sha = "a" * 40
    admission = {"sha": launch_sha}
    arm_summaries = {}
    for arm in ("F", "M"):
        arm_out = out / arm
        raw = arm_out / "raw"
        raw.mkdir(parents=True)
        config = {**reducer.REQUIRED_INITIAL_CONFIG, "seed": binding.seed}
        configuration = {
            "object_id": OBJECT_ID, "tag": binding.tag, "block": block,
            "arm": arm, "seed": binding.seed, "spec": PRODUCTION_SPEC_VALUES,
            "schedule": list(SCHEDULES[arm]), "config": config,
            "world_seed_bases": {str(n): base for n, base in WORLD_SEED_BASES.items()},
            "training_world_seed_formula":
                f"{binding.training_world_base} + 100 * rollout + lane",
        }
        _json(arm_out / "config.json", configuration)
        initial = {key: {"fixed": key} for key in reducer.INITIAL_EQUAL_FIELDS}
        initial["parameter_normalizer_digest"] = "same-in-pair"
        initial["actual_config"] = config
        _json(raw / "initialization.json", initial)
        init_identity = _identity(raw / "initialization.json", "raw/initialization.json")
        rows, compact_rows, resets = [], [], []
        for rollout, n in enumerate(SCHEDULES[arm], start=1):
            calls = {4: 1_500, 6: 2_250, 8: 3_000}[n]
            rows.append({"rollout": rollout, "n": n,
                         "optimizer_delta": {"discoverer_actor": calls,
                                             "discoverer_critic": calls},
                         "sampler": {"recurrent_minibatches": calls}})
            compact_rows.append({"rollout": rollout, "n": n})
            scene_path = raw / f"training_reset_r{rollout:02d}_n{n}.npz"
            with scene_path.open("wb") as stream:
                np.savez(stream, rollout=np.asarray(rollout), n=np.asarray(n),
                         lane_world_seeds=np.asarray([
                             binding.training_world_base + 100 * rollout + lane
                             for lane in range(16)]),
                         states=np.zeros((16, 1)), observations=np.zeros((16, n, 1)),
                         uav_positions=np.zeros((16, n, 3)),
                         user_positions=np.zeros((16, 50, 2)))
            reset_identity = _identity(scene_path, f"raw/{scene_path.name}")
            resets.append({"path": reset_identity["relative_to_arm"],
                           "bytes": reset_identity["bytes"],
                           "sha256": reset_identity["sha256"],
                           "rollout": rollout, "n": n})
        training_path = raw / "training.jsonl"
        training_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        stream_identity = _identity(training_path, "raw/training.jsonl")
        panels = []
        for stage in ((0, 45) if arm == "F" else (45,)):
            for n in EVALUATION_ORDER:
                coverage = .5 if stage == 0 else .55 if arm == "F" else .6 + .01 * block
                panels.append(_synthetic_panel(arm_out, arm, stage, n, coverage))
        checkpoints = []
        for stage in (0, 45):
            path = raw / f"checkpoint_{stage:02d}.pt"
            path.write_bytes(f"synthetic checkpoint {arm} {stage}".encode())
            checkpoints.append(_identity(path, f"raw/checkpoint_{stage:02d}.pt"))
        summary = {
            "status": "complete", "block": block, "arm": arm, "tag": binding.tag,
            "seed": binding.seed, "spec": PRODUCTION_SPEC_VALUES,
            "schedule": list(SCHEDULES[arm]),
            "counts": reducer._expected_counts(arm),
            "expected_counts": reducer._expected_counts(arm),
            "source_hashes_before": sources, "source_hashes_after": sources,
            "source_hashes_unchanged": True,
            "initial_config": config,
            "final_config": {**config, "n_agents": SCHEDULES[arm][-1]},
            "initialization": {"parameter_normalizer_digest": "same-in-pair",
                               "raw": {"path": "raw/initialization.json",
                                       "bytes": init_identity["bytes"],
                                       "sha256": init_identity["sha256"]}},
            "training_stream": {"path": "raw/training.jsonl",
                                "bytes": stream_identity["bytes"],
                                "sha256": stream_identity["sha256"],
                                "completed_rows": 45},
            "rollouts": compact_rows,
            "optimizer_calls": {"coordinator": 0,
                                "discoverer_actor": 101_250,
                                "discoverer_critic": 101_250,
                                "team_discriminator": 0,
                                "individual_discriminator": 0},
            "training_reset_scenes": resets, "panels": panels,
            "stage_isolation": {str(stage): {"global_rng_preserved": True}
                                for stage in ((0, 45) if arm == "F" else (45,))},
            "checkpoints": checkpoints,
            "launch_sha": launch_sha, "admission": admission,
        }
        if arm == "F":
            summary["initial_evaluation_trace_sha256"] = {
                str(n): panels[index]["trace"]["sha256"]
                for index, n in enumerate(EVALUATION_ORDER)
            }
        else:
            f_summary = arm_summaries["F"]
            summary["common_stage0"] = {
                "new_environment_steps": 0,
                "reused_after_full_initial_identity": True,
                "trace_sha256": f_summary["initial_evaluation_trace_sha256"],
                "panel_paths": [f"../F/panel_stage00_n{n}.json" for n in EVALUATION_ORDER],
            }
        _json(arm_out / "summary.json", summary)
        arm_summaries[arm] = summary
    f, m = arm_summaries["F"], arm_summaries["M"]
    counts = {key: f["counts"][key] + m["counts"][key] for key in f["counts"]}
    readings = {"by_test_n": {}}
    for index, n in enumerate(EVALUATION_ORDER):
        f_final = f["panels"][3 + index]
        m_final = m["panels"][index]
        readings["by_test_n"][str(n)] = {"final_M_minus_F": {
            "J": {"per_world": [a - b for a, b in zip(m_final["J"], f_final["J"])]},
            "S": {"per_world": [a - b for a, b in zip(
                m_final["service_arrays"]["S_served_users_per_step"],
                f_final["service_arrays"]["S_served_users_per_step"])]},
        }}
    batch = {
        "status": "complete", "production_contract": True, "object_id": OBJECT_ID,
        "block": block, "tag": binding.tag, "seed": binding.seed,
        "training_world_base": binding.training_world_base,
        "evaluation_world_bases": {str(n): base for n, base in WORLD_SEED_BASES.items()},
        "arm_order": ["F", "M"], "arms": {
            arm: {"status": "complete", "counts": summary["counts"],
                  "summary": f"{arm}/summary.json"}
            for arm, summary in arm_summaries.items()},
        "source_hashes_before": sources, "source_hashes_after": sources,
        "source_hashes_unchanged": True,
        "launch_sha": launch_sha, "admission": admission,
        "counts": counts,
        "initial_identity": {key + "_equal": True for key in reducer.INITIAL_EQUAL_FIELDS}
                            | {"common_stage0_reused_without_new_steps": True},
        "common_n6_training_world_identity": {"all_equal": True},
        "readings": readings,
    }
    _json(out / "summary.json", batch)
    return out


def _synthetic_block(block: int, effects: dict[str, list[float]]) -> dict:
    by_n = {}
    for n in (5, 7):
        by_n[str(n)] = {"M_minus_F": {
            quantity: {"mean": effects[f"N{n}_{quantity}"][block - 1]}
            for quantity in ("J", "S")
        }}
    return {"block": block, "launch_sha": "a" * 40,
            "by_n": by_n, "counts": {"fits": 2, "panels": 9},
            "arm_optimizer_calls": {
                arm: {"coordinator": 0, "discoverer_actor": 101_250,
                      "discoverer_critic": 101_250,
                      "team_discriminator": 0, "individual_discriminator": 0}
                for arm in ("F", "M")},
            "learner_contract": {"fixed": "LOCAL1"}}


def _run_mock_reduction(tmp_path, monkeypatch, effects):
    monkeypatch.setattr(reducer, "_source_hashes", lambda: {"fixed": "source"})
    monkeypatch.setattr(reducer, "_block_reading",
                        lambda block, _path, _sources: _synthetic_block(block, effects))
    inputs = {block: tmp_path / f"input{block}" for block in BLOCKS}
    return reducer.reduce_blocks(inputs, tmp_path / "reduced")


def test_full_artifact_reader_and_reducer_accept_fixed_synthetic_schema(tmp_path):
    sources = reducer._source_hashes()
    inputs = {block: _synthetic_production_block(tmp_path, block, sources)
              for block in BLOCKS}
    result = reducer.reduce_blocks(inputs, tmp_path / "reduced")
    assert result["status"] == "complete" and result["joint_supported"]
    assert result["launch_sha"] == "a" * 40
    assert result["counts"]["fits"] == 6
    assert result["counts"]["training_team_steps"] == 2_160_000
    assert result["counts"]["evaluation_team_steps"] == 432_000
    assert result["counts"]["panels"] == 27
    assert result["optimizer_calls_total"]["discoverer_actor"] == 607_500
    assert result["optimizer_calls_total"]["discoverer_critic"] == 607_500
    assert result["primary"]["N5_J"]["block_effects"] == pytest.approx([.06, .07, .08])
    assert set(result["blocks"][0]["by_n"]["6"]["M_minus_F"]) == set(reducer.QUANTITIES)
    assert json.loads((tmp_path / "reduced/summary.json").read_text()) == result
    command = [sys.executable, str(Path(reducer.__file__).resolve())]
    for block in BLOCKS:
        command.extend([f"--block{block}", str(inputs[block])])
    command.extend(["--out", str(tmp_path / "cli-reduced")])
    process = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert process.returncode == 0, process.stderr
    assert json.loads((tmp_path / "cli-reduced/summary.json").read_text()) == result


def test_reducer_refuses_mixed_full_launch_shas_with_matching_file_hashes(tmp_path):
    sources = reducer._source_hashes()
    inputs = {block: _synthetic_production_block(tmp_path, block, sources)
              for block in BLOCKS}
    block2 = inputs[2]
    for path in (block2 / "summary.json", block2 / "F/summary.json",
                 block2 / "M/summary.json"):
        summary = json.loads(path.read_text())
        assert summary["source_hashes_before"] == sources
        summary["launch_sha"] = "b" * 40
        summary["admission"]["sha"] = "b" * 40
        _json(path, summary)
    with pytest.raises(ValueError, match="mixed launch SHA"):
        reducer.reduce_blocks(inputs, tmp_path / "reduced")
    assert not (tmp_path / "reduced").exists()


@pytest.mark.parametrize("sha", [None, "bad", "A" * 40])
def test_reducer_refuses_missing_or_invalid_full_launch_sha(tmp_path, sha):
    sources = reducer._source_hashes()
    inputs = {block: _synthetic_production_block(tmp_path, block, sources)
              for block in BLOCKS}
    path = inputs[1] / "summary.json"
    summary = json.loads(path.read_text())
    if sha is None:
        summary.pop("launch_sha")
    else:
        summary["launch_sha"] = sha
    _json(path, summary)
    with pytest.raises(ValueError, match="missing or invalid full launch SHA"):
        reducer.reduce_blocks(inputs, tmp_path / "reduced")
    assert not (tmp_path / "reduced").exists()


def test_direct_reducer_entry_imports_no_learner_or_environment():
    script = """
import importlib.abc
import runpy
import sys
class RejectScientific(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'torch' or fullname.startswith('torch.') or \\
                fullname == 'envs' or fullname.startswith('envs.') or \\
                fullname.startswith('experiments.candidates.agent_count_generalization'):
            raise RuntimeError('scientific import in reducer: ' + fullname)
        return None
sys.meta_path.insert(0, RejectScientific())
module = runpy.run_path(sys.argv[1], run_name='b20_reducer_read_only')
assert callable(module['reduce_blocks'])
assert 'torch' not in sys.modules
"""
    process = subprocess.run(
        [sys.executable, "-c", script, str(Path(reducer.__file__).resolve())],
        capture_output=True, text=True, timeout=30,
    )
    assert process.returncode == 0, process.stderr


@pytest.mark.parametrize("mutation, expected", [
    ("world", "wrong fixed panel"),
    ("endpoint", "wrong actual panel set"),
    ("nonfinite", "nonfinite value"),
    ("reset_nonfinite", "invalid reset arrays"),
    ("source", "source mismatch"),
    ("pairing", "physical pairing mismatch"),
])
def test_full_artifact_reader_refuses_invalid_inputs(tmp_path, mutation, expected):
    sources = reducer._source_hashes()
    inputs = {block: _synthetic_production_block(tmp_path, block, sources)
              for block in BLOCKS}
    block1 = inputs[1]
    if mutation == "source":
        path = block1 / "summary.json"
        value = json.loads(path.read_text())
        value["source_hashes_before"] = {"wrong": "source"}
        _json(path, value)
    elif mutation == "reset_nonfinite":
        arm_path = block1 / "F/summary.json"
        summary = json.loads(arm_path.read_text())
        path = block1 / "F/raw/training_reset_r01_n6.npz"
        with np.load(path, allow_pickle=False) as scene:
            arrays = {key: scene[key].copy() for key in scene.files}
        arrays["states"][0, 0] = float("nan")
        with path.open("wb") as stream:
            np.savez(stream, **arrays)
        identity = _identity(path, f"raw/{path.name}")
        summary["training_reset_scenes"][0]["bytes"] = identity["bytes"]
        summary["training_reset_scenes"][0]["sha256"] = identity["sha256"]
        _json(arm_path, summary)
    else:
        arm = "M" if mutation == "pairing" else "F"
        stage = 45
        panel_path = block1 / arm / f"panel_stage{stage:02d}_n5.json"
        arm_path = block1 / arm / "summary.json"
        panel = json.loads(panel_path.read_text())
        summary = json.loads(arm_path.read_text())
        index = 0 if arm == "M" else 3
        if mutation == "world":
            panel["world_seeds"][0] += 1
        elif mutation == "endpoint":
            panel["policy_stage"] = 44
        elif mutation == "nonfinite":
            panel["executed_action_bounds"] = {"minimum": float("nan")}
        elif mutation == "pairing":
            panel["initial_world_identity"]["states"]["sha256"] = "other-world"
        summary["panels"][index] = panel
        if mutation == "nonfinite":
            panel_path.write_text(json.dumps(panel, allow_nan=True), encoding="utf-8")
            arm_path.write_text(json.dumps(summary, allow_nan=True), encoding="utf-8")
        else:
            _json(panel_path, panel)
            _json(arm_path, summary)
    with pytest.raises(ValueError, match=expected):
        reducer.reduce_blocks(inputs, tmp_path / "reduced")
    assert not (tmp_path / "reduced").exists()


def test_fixed_t_interval_all_positive_block_effects_can_fail_joint(tmp_path, monkeypatch):
    effects = {"N5_J": [1.0, 1.0, 10.0], "N5_S": [1.0, 1.0, 1.0],
               "N7_J": [1.0, 1.0, 1.0], "N7_S": [1.0, 1.0, 1.0]}
    result = _run_mock_reduction(tmp_path, monkeypatch, effects)
    interval = result["primary"]["N5_J"]
    assert interval["block_effects"] == [1.0, 1.0, 10.0]
    assert interval["mean"] == 4.0
    assert interval["sd_ddof1"] == pytest.approx(3**.5 * 3)
    assert interval["t975_df2"] == 4.302652729696142
    assert interval["lower"] < 0 < interval["upper"]
    assert interval["reading"] == "unresolved"
    assert not result["joint_supported"] and result["joint_verdict"] == "claim_not_established"
    assert result["training_block_unit_n"] == 3
    assert result["counts"] == {"fits": 6, "panels": 27}
    assert json.loads((tmp_path / "reduced/summary.json").read_text()) == result


def test_joint_strict_zero_boundary_and_adverse_interval(tmp_path, monkeypatch):
    positive = {name: [1.0, 1.0, 1.0] for name in ("N5_J", "N5_S", "N7_J", "N7_S")}
    result = _run_mock_reduction(tmp_path, monkeypatch, positive)
    assert result["joint_supported"]
    assert all(row["lower"] == 1.0 for row in result["primary"].values())
    # A zero lower bound never passes the strict conjunction.
    zero = dict(positive, N7_S=[0.0, 0.0, 0.0])
    result = _run_mock_reduction(tmp_path / "zero", monkeypatch, zero)
    assert not result["joint_supported"]
    assert result["primary"]["N7_S"]["reading"] == "unresolved"
    adverse = dict(positive, N7_S=[-1.0, -1.0, -1.0])
    result = _run_mock_reduction(tmp_path / "adverse", monkeypatch, adverse)
    assert not result["joint_supported"]
    assert result["primary"]["N7_S"]["reading"] == "adverse"


def test_reducer_refuses_missing_duplicate_and_existing_outputs(tmp_path):
    with pytest.raises(ValueError, match="exactly blocks"):
        reducer.reduce_blocks({1: tmp_path / "b1", 2: tmp_path / "b2"}, tmp_path / "out")
    with pytest.raises(ValueError, match="duplicate block"):
        reducer.reduce_blocks({1: tmp_path / "same", 2: tmp_path / "same",
                               3: tmp_path / "b3"}, tmp_path / "out")
    out = tmp_path / "out"
    out.mkdir()
    with pytest.raises(ValueError, match="already exists"):
        reducer.reduce_blocks({i: tmp_path / f"b{i}" for i in BLOCKS}, out)


def test_reducer_refuses_reduced_technical_pair(tmp_path):
    pair = tmp_path / f"technical_{BLOCKS[1].tag}_s9201019"
    pair.mkdir()
    with pytest.raises(ValueError, match="wrong block 1 output tag"):
        reducer.reduce_blocks({1: pair, 2: tmp_path / BLOCKS[2].tag,
                               3: tmp_path / BLOCKS[3].tag}, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_wrong_world_endpoint_nonfinite_and_source_rejected(tmp_path):
    row = {"status": "complete", "arm": "F", "policy_stage": 0,
           "after_rollout": 0, "test_n": 5,
           "world_seeds": list(range(WORLD_SEED_BASES[5], WORLD_SEED_BASES[5] + 32)),
           "runtime_seed": WORLD_SEED_BASES[5] + 51}
    with pytest.raises(ValueError, match="wrong endpoint"):
        reducer._check_panel(tmp_path, row, "F", 45, 5)
    row["world_seeds"] = list(range(32))
    with pytest.raises(ValueError, match="wrong fixed panel"):
        reducer._check_panel(tmp_path, row, "F", 0, 5)
    with pytest.raises(ValueError, match="nonfinite array"):
        reducer._numbers([float("nan")] + [0.0] * 31, "test-J")
    production_name = tmp_path / BLOCKS[1].tag
    production_name.mkdir()
    batch = {
        "status": "complete", "production_contract": True,
        "object_id": OBJECT_ID, "block": 1, "tag": BLOCKS[1].tag,
        "seed": BLOCKS[1].seed, "training_world_base": BLOCKS[1].training_world_base,
        "evaluation_world_bases": {str(n): base for n, base in WORLD_SEED_BASES.items()},
        "arm_order": ["F", "M"], "arms": {"F": {}, "M": {}},
        "source_hashes_before": {"wrong": "source"},
        "source_hashes_after": {"wrong": "source"},
        "source_hashes_unchanged": True,
    }
    (production_name / "summary.json").write_text(json.dumps(batch), encoding="utf-8")
    with pytest.raises(ValueError, match="source mismatch"):
        reducer._block_reading(1, production_name, reducer._source_hashes())
