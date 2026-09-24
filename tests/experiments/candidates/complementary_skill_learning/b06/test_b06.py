from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner as b01
from experiments.candidates.complementary_skill_learning.b04 import runner as b04
from experiments.candidates.complementary_skill_learning.b06 import runner as r
from scripts import run_complementary_skill_learning_b06 as entry


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


@pytest.fixture(scope="module")
def pair(tmp_path_factory, spec):
    root = tmp_path_factory.mktemp("b06-pair")
    summaries = {
        arm: r.run_fit(arm, root / arm, "technical-check", spec=spec, device="cpu")
        for arm in ("M", "U")
    }
    return root, summaries


def _build_initial_agent(root: Path, spec: b04.Spec):
    envs = b04.make_envs(spec, spec.lanes, spec.train_world_base)
    try:
        config = b04.make_config(spec, envs, "M")
    finally:
        for env in envs:
            env.close()
    b04.seed_rng(spec.init_seed)
    return b04.TrainingLawAgent(
        config=config,
        arm="M",
        head_seed=spec.head_seed,
        aux_seed=spec.aux_seed,
        low_action_seed=spec.low_action_seed,
        high_collection_seed=spec.high_collection_seed,
        high_update_seed=spec.high_update_seed,
        log_dir=str(root),
        device=torch.device("cpu"),
    )


def test_fixed_spec_is_only_the_prescribed_b04_replacement():
    changed = {
        name
        for name, value in asdict(r.DEFAULT_SPEC).items()
        if value != asdict(b04.DEFAULT_SPEC)[name]
    }
    assert changed == {
        "init_seed",
        "head_seed",
        "train_rng_seed",
        "aux_seed",
        "low_action_seed",
        "high_collection_seed",
        "high_update_seed",
        "train_world_base",
    }
    assert (
        r.DEFAULT_SPEC.init_seed,
        r.DEFAULT_SPEC.head_seed,
        r.DEFAULT_SPEC.train_rng_seed,
        r.DEFAULT_SPEC.aux_seed,
        r.DEFAULT_SPEC.low_action_seed,
        r.DEFAULT_SPEC.high_collection_seed,
        r.DEFAULT_SPEC.high_update_seed,
    ) == tuple(range(260923961, 260923968))
    assert r.DEFAULT_SPEC.train_world_base == 2200000
    assert not r.DEFAULT_SPEC.small_model
    assert (
        b04._uniform_stream_digest(r.DEFAULT_SPEC)
        == b04.EXPECTED_UNIFORM_LABEL_STREAM_SHA256
    )


def test_actual_new_initial_head_private_and_sampler_states_differ_from_b04(
    tmp_path, spec
):
    old_spec = replace(
        spec,
        init_seed=b04.DEFAULT_SPEC.init_seed,
        head_seed=b04.DEFAULT_SPEC.head_seed,
        train_rng_seed=b04.DEFAULT_SPEC.train_rng_seed,
        aux_seed=b04.DEFAULT_SPEC.aux_seed,
        low_action_seed=b04.DEFAULT_SPEC.low_action_seed,
        high_collection_seed=b04.DEFAULT_SPEC.high_collection_seed,
        high_update_seed=b04.DEFAULT_SPEC.high_update_seed,
        train_world_base=b04.DEFAULT_SPEC.train_world_base,
    )
    old = _build_initial_agent(tmp_path / "old", old_spec)
    new = _build_initial_agent(tmp_path / "new", spec)
    assert b04.native_digest(old) != b04.native_digest(new)
    for head in ("g_head", "p_head"):
        old_state = getattr(old, head).state_dict()
        new_state = getattr(new, head).state_dict()
        assert any(not torch.equal(old_state[name], new_state[name]) for name in old_state)
    assert old.rng_stream_telemetry() != new.rng_stream_telemetry()
    assert old.sampler_rng_telemetry() != new.sampler_rng_telemetry()


def test_real_cpu_pair_preserves_pairing_learning_counts_and_six_panels(pair, spec):
    root, summaries = pair
    learned, uniform = summaries["M"], summaries["U"]
    assert sum(len(summary["panels"]) for summary in summaries.values()) == 6
    assert learned["initial_native_digest"] == uniform["initial_native_digest"]
    assert learned["initial_frozen_digest"] == uniform["initial_frozen_digest"]
    assert learned["initial_default_rng_state_sha256"] == uniform[
        "initial_default_rng_state_sha256"
    ]
    assert learned["initial_private_rng_streams"] == uniform["initial_private_rng_streams"]
    assert learned["initial_sampler_rng_streams"] == uniform["initial_sampler_rng_streams"]

    for arm, summary in summaries.items():
        assert summary["status"] == "complete"
        assert summary["object_id"] == "complementary_skill_b04"
        assert summary["spec"] == asdict(spec)
        panel_count = 4 if arm == "M" else 2
        assert summary["counts"] == {
            "started_fits": 1,
            "model_constructions": 1,
            "training_transitions": 40,
            "stored_transitions": 40,
            "training_episodes": 2,
            "native_updates": 1,
            "evaluation_transitions": panel_count * 40,
            "evaluation_episodes": panel_count * 2,
        }
        assert summary["label_flow_checks"] == {
            "action_batches": 20,
            "reward_batches": 20,
            "factual_batches": 20,
            "storage_batches": 20,
            "failures": 0,
        }
        movement = summary["training_rows"][0]["relative_initialization_displacement"]
        assert all(
            movement[name] > 0
            for name in (
                "discoverer_actor",
                "discoverer_critic",
                "team_discriminator",
                "individual_discriminator",
            )
        )
        assert all(
            summary["training_rows"][0]["auxiliary_head_relative_movement"][name] > 0
            for name in ("G", "P")
        )
        assert all(
            not panel["optimizer_calls"] and not panel["normalizer_updates"]
            for panel in summary["panels"].values()
        )
        checkpoint = torch.load(
            root / arm / "initial.pt", map_location="cpu", weights_only=False
        )
        assert checkpoint["object_id"] == "complementary_skill_b04"

    assert learned["training_rows"][0]["relative_initialization_displacement"][
        "coordinator"
    ] > 0
    assert uniform["training_rows"][0]["relative_initialization_displacement"][
        "coordinator"
    ] == 0
    assert uniform["native_optimizer_calls"]["coordinator"] == 0
    assert uniform["uniform_factor_audits"]
    assert all(
        row["canonical_rows_checked"] > 0
        and row["team_factors_checked"] > 0
        and row["individual_factors_checked"]
        == spec.n_agents * row["team_factors_checked"]
        for row in uniform["uniform_factor_audits"]
    )
    assert learned["final_private_rng_streams"]["low_actions"] == uniform[
        "final_private_rng_streams"
    ]["low_actions"]
    assert learned["final_private_rng_streams"]["high_collection"] == uniform[
        "final_private_rng_streams"
    ]["high_collection"]
    assert uniform["final_private_rng_streams"]["high_updates"] == uniform[
        "initial_private_rng_streams"
    ]["high_updates"]
    assert learned["training_rows"][0]["default_rng_state_sha256_after"] == uniform[
        "training_rows"
    ][0]["default_rng_state_sha256_after"]
    assert learned["final_sampler_rng_streams"]["remaining_learner"] == uniform[
        "final_sampler_rng_streams"
    ]["remaining_learner"]
    assert uniform["final_sampler_rng_streams"]["high_updates"] == uniform[
        "initial_sampler_rng_streams"
    ]["high_updates"]
    assert learned["final_sampler_rng_streams"]["high_updates"] != learned[
        "initial_sampler_rng_streams"
    ]["high_updates"]

    m_panel = learned["panels"]["initial_uniform"]
    u_panel = uniform["panels"]["initial_uniform"]
    for name in (
        "native_scores_J",
        "physical_initial_state_sha256",
        "selected_label_stream_sha256",
    ):
        assert b04.jsonable(m_panel[name]) == b04.jsonable(u_panel[name])
    expected = b04._uniform_stream_digest(spec)
    assert all(
        summary["panels"][name]["selected_label_stream_sha256"] == expected
        for summary in summaries.values()
        for name in ("initial_uniform", "final_uniform")
    )


def test_adapter_guard_failure_preserves_output_and_marks_failed(tmp_path, monkeypatch):
    out = tmp_path / "failed"

    def fake_engine(arm, output, launch_sha, **kwargs):
        output = Path(output)
        output.mkdir(parents=True)
        (output / "retained.bin").write_bytes(b"preserve-me")
        summary = {
            "status": "complete",
            "object_id": b04.OBJECT,
            "arm": arm,
            "spec": asdict(kwargs["spec"]),
            "panels": {
                "initial_uniform": {"selected_label_stream_sha256": "wrong"},
                "final_uniform": {"selected_label_stream_sha256": "wrong"},
            },
        }
        b04.write_json(output / "summary.json", summary)
        return summary

    monkeypatch.setattr(b04, "run_fit", fake_engine)
    with pytest.raises(ValueError, match="prescribed uniform factors"):
        r.run_fit("U", out, "technical-check", spec=replace(r.DEFAULT_SPEC, small_model=True))
    saved = json.loads((out / "summary.json").read_text())
    assert saved["status"] == "failed"
    assert saved["failure"]["stage"] == "b06_adapter_completed_contract"
    assert (out / "retained.bin").read_bytes() == b"preserve-me"


def test_prework_guards_refuse_spec_or_stream_drift_without_engine_effects(
    tmp_path, monkeypatch
):
    called = False

    def forbidden_engine(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(b04, "run_fit", forbidden_engine)
    out = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="fixed RNG/world addresses differ"):
        r.run_fit("M", out, "technical-check", spec=replace(r.DEFAULT_SPEC, init_seed=1))
    assert not called and not out.exists()

    monkeypatch.setattr(b04, "_uniform_stream_digest", lambda spec: "wrong")
    with pytest.raises(ValueError, match="uniform evaluation stream digest differs"):
        r.run_fit("M", out, "technical-check")
    assert not called and not out.exists()


@pytest.mark.parametrize(
    "extra_args",
    (["--arm", "X", "--seed", str(r.FIXED_SEED)], ["--arm", "U", "--seed", "1"]),
)
def test_entry_refuses_invalid_arm_or_seed_before_admission(tmp_path, extra_args):
    out = tmp_path / "must-not-exist"
    result = subprocess.run(
        [
            sys.executable,
            str(b01.ROOT / "scripts/run_complementary_skill_learning_b06.py"),
            *extra_args,
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


def test_entry_refuses_unadmitted_call_before_outputs(tmp_path):
    out = tmp_path / "must-not-exist"
    result = subprocess.run(
        [
            sys.executable,
            str(b01.ROOT / "scripts/run_complementary_skill_learning_b06.py"),
            "--arm",
            "U",
            "--seed",
            str(r.FIXED_SEED),
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
    assert "missing HMASD admission" in result.stderr
    assert not out.exists()


def test_entry_checks_launch_sha_and_passes_actual_spec(tmp_path, monkeypatch):
    admission = {"sha": "a" * 40}
    monkeypatch.setattr(entry, "require_admission", lambda *args, **kwargs: admission)
    with pytest.raises(ValueError, match="launch SHA differs"):
        entry.main(
            [
                "--arm",
                "M",
                "--seed",
                str(r.FIXED_SEED),
                "--launch-sha",
                "b" * 40,
                "--out",
                str(tmp_path / "wrong-sha"),
            ]
        )
    assert not (tmp_path / "wrong-sha").exists()

    captured = {}

    def fake_fit(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(r, "run_fit", fake_fit)
    assert (
        entry.main(
            [
                "--arm",
                "M",
                "--seed",
                str(r.FIXED_SEED),
                "--launch-sha",
                admission["sha"],
                "--out",
                str(tmp_path / "accepted"),
            ]
        )
        == 0
    )
    assert captured["kwargs"]["spec"] is r.DEFAULT_SPEC
    assert captured["kwargs"]["admission"] is admission
    assert captured["kwargs"]["device"] == "cuda"


@pytest.mark.skipif(not torch.cuda.is_available(), reason="requires actual CUDA runtime")
def test_actual_cuda_pair_uses_new_adapter(tmp_path, spec):
    cuda_spec = replace(spec, rollouts=2)
    summaries = {
        arm: r.run_fit(
            arm,
            tmp_path / arm,
            "technical-check",
            spec=cuda_spec,
            device="cuda",
        )
        for arm in ("M", "U")
    }
    assert sum(len(summary["panels"]) for summary in summaries.values()) == 6
    assert summaries["M"]["initial_native_digest"] == summaries["U"][
        "initial_native_digest"
    ]
    for arm, summary in summaries.items():
        assert summary["status"] == "complete"
        assert summary["counts"]["native_updates"] == 2
        assert summary["label_flow_checks"]["failures"] == 0
        assert all(
            summary["training_rows"][-1]["relative_initialization_displacement"][name]
            > 0
            for name in (
                "discoverer_actor",
                "discoverer_critic",
                "team_discriminator",
                "individual_discriminator",
            )
        )
    assert summaries["M"]["native_optimizer_calls"]["coordinator"] > 0
    assert summaries["U"]["native_optimizer_calls"]["coordinator"] == 0
    assert summaries["U"]["uniform_factor_audits"]

