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
from experiments.candidates.complementary_skill_learning.b07 import runner as b07
from experiments.candidates.complementary_skill_learning.b08 import runner as r
from scripts import run_complementary_skill_learning_b08 as entry


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


def _run_batch(root: Path, spec: b07.Spec, device: str):
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
    root = tmp_path_factory.mktemp("b08-batch")
    return root, _run_batch(root / "outputs", spec, "cpu")


def _make_agent(root: Path, spec: b07.Spec, arm: str):
    envs = b07.make_envs(spec, spec.lanes, spec.train_world_base)
    try:
        config = b07.make_config(spec, envs, arm)
    finally:
        for env in envs:
            env.close()
    b07.seed_rng(spec.init_seed)
    return b07._build_agent(spec, config, arm, root, torch.device("cpu"))


def _initial_world(spec: b07.Spec):
    envs = b07.make_envs(spec, spec.lanes, spec.train_world_base)
    try:
        return tuple(array.copy() for array in b01.native._reset_all(envs))
    finally:
        for env in envs:
            env.close()


def test_fixed_spec_changes_only_new_training_addresses_and_reuses_engine():
    changed = {
        name
        for name, value in asdict(r.DEFAULT_SPEC).items()
        if value != asdict(b07.DEFAULT_SPEC)[name]
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
    ) == tuple(range(260924041, 260924048))
    assert r.DEFAULT_SPEC.train_world_base == 2400000
    assert r.DEFAULT_SPEC.eval_world_base == 1700200
    assert r.S_SEEDS == b07.S_SEEDS == {f"S{i}": 260924101 + i for i in range(4)}
    assert r.R_SEEDS == b07.R_SEEDS == {f"R{i}": 262625201 + i for i in range(4)}
    assert r.NON_LABEL_SEED == b07.NON_LABEL_SEED == 260924105
    assert r.ENGINE_RUN_FIT is b07.run_fit
    assert r.PROTOCOL.default_spec is r.DEFAULT_SPEC


def test_actual_new_native_heads_rng_and_world_inputs_differ_from_b07(
    tmp_path, spec
):
    old_spec = replace(
        spec,
        init_seed=b07.DEFAULT_SPEC.init_seed,
        head_seed=b07.DEFAULT_SPEC.head_seed,
        train_rng_seed=b07.DEFAULT_SPEC.train_rng_seed,
        aux_seed=b07.DEFAULT_SPEC.aux_seed,
        low_action_seed=b07.DEFAULT_SPEC.low_action_seed,
        high_collection_seed=b07.DEFAULT_SPEC.high_collection_seed,
        high_update_seed=b07.DEFAULT_SPEC.high_update_seed,
        train_world_base=b07.DEFAULT_SPEC.train_world_base,
    )
    old = _make_agent(tmp_path / "old", old_spec, "M")
    new = _make_agent(tmp_path / "new", spec, "M")
    assert b07.native_digest(old) != b07.native_digest(new)
    for name in ("g_head", "p_head"):
        old_state = getattr(old, name).state_dict()
        new_state = getattr(new, name).state_dict()
        assert any(not torch.equal(old_state[key], new_state[key]) for key in old_state)
    assert old.aux_seed == b07.DEFAULT_SPEC.aux_seed
    assert new.aux_seed == r.DEFAULT_SPEC.aux_seed
    assert old.rng_stream_telemetry() != new.rng_stream_telemetry()
    assert old.sampler_rng_telemetry() != new.sampler_rng_telemetry()
    b07.seed_rng(old_spec.train_rng_seed)
    old_default = b04.rng_state_digest()
    b07.seed_rng(spec.train_rng_seed)
    assert b04.rng_state_digest() != old_default
    old_states, old_observations = _initial_world(old_spec)
    new_states, new_observations = _initial_world(spec)
    assert not np.array_equal(old_states, new_states)
    assert not np.array_equal(old_observations, new_observations)


def test_real_cpu_batch_has_b08_identity_pairing_counts_and_update_exposure(
    batch, spec
):
    root, summaries = batch
    m, e, u = (summaries[name] for name in ("M", "E", "U"))
    assert [len(summaries[name]["panels"]) for name in ("M", "E", "U")] == [10, 10, 5]
    assert len({summary["initial_native_digest"] for summary in summaries.values()}) == 1
    assert len({summary["initial_frozen_digest"] for summary in summaries.values()}) == 1
    assert len({summary["initial_default_rng_state_sha256"] for summary in summaries.values()}) == 1
    assert len({json.dumps(summary["initial_private_rng_streams"], sort_keys=True) for summary in summaries.values()}) == 1
    assert len({json.dumps(summary["initial_sampler_rng_streams"], sort_keys=True) for summary in summaries.values()}) == 1

    for arm, summary in summaries.items():
        assert summary["status"] == "complete"
        assert summary["object_id"] == b07.OBJECT
        assert summary["adapter_protocol"]["protocol_id"] == r.OBJECT
        assert summary["adapter_protocol"]["reused_engine"]["object_id"] == b07.OBJECT
        assert summary["spec"] == asdict(spec)
        assert summary["counts"]["training_transitions"] == 40
        assert summary["counts"]["native_updates"] == 1
        assert summary["counts"]["evaluation_transitions"] == (
            400 if arm in {"M", "E"} else 200
        )
        assert summary["label_flow_checks"]["failures"] == 0
        saved = json.loads((root / "outputs" / arm / "summary.json").read_text())
        config = json.loads((root / "outputs" / arm / "config.json").read_text())
        assert saved["adapter_protocol"] == config["adapter_protocol"]
        checkpoint = torch.load(
            root / "outputs" / arm / "initial.pt",
            map_location="cpu",
            weights_only=False,
        )
        assert checkpoint["object_id"] == b07.OBJECT

    assert m["intervention"]["lambda_h"] == 0.07
    assert e["intervention"]["lambda_h"] == 0.0
    assert not m["intervention"]["disable_high_level_training"]
    assert not e["intervention"]["disable_high_level_training"]
    assert u["intervention"]["disable_high_level_training"]
    assert m["native_optimizer_calls"]["coordinator"] > 0
    assert e["native_optimizer_calls"]["coordinator"] > 0
    assert u["native_optimizer_calls"]["coordinator"] == 0
    for summary in summaries.values():
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
    assert u["training_rows"][0]["relative_initialization_displacement"]["coordinator"] == 0

    for name in ("initial_R0", "final_R0", "final_R1", "final_R2", "final_R3"):
        assert len({summary["panels"][name]["selected_label_stream_sha256"] for summary in summaries.values()}) == 1
    for metric in ("native_scores_J", "connected_users_per_step"):
        np.testing.assert_array_equal(
            m["panels"]["initial_R0"][metric],
            e["panels"]["initial_R0"][metric],
        )
        np.testing.assert_array_equal(
            m["panels"]["initial_R0"][metric],
            u["panels"]["initial_R0"][metric],
        )
        np.testing.assert_array_equal(
            m["panels"]["initial_S0"][metric],
            e["panels"]["initial_S0"][metric],
        )

    metadata = m["M_final_S_reference"]["metadata"]
    assert metadata["adapter_protocol_id"] == r.OBJECT
    assert metadata["adapter_source_module"] == r.__name__
    assert metadata["source_launch_sha"] == "technical-check"
    assert metadata["spec"] == asdict(spec)
    assert e["reference_binding"]["sha256"] == m["M_final_S_reference"]["sha256"]
    assert e["common_context_scoring"]["context_rows"] == 16


def test_old_b07_reference_contract_is_rejected_before_output_or_native_work(
    tmp_path, batch, spec, monkeypatch
):
    _, summaries = batch
    reference = summaries["M"]["M_final_S_reference"]
    validated = r.validate_reference(
        reference["path"],
        reference["sha256"],
        spec,
        expected_source_launch_sha="technical-check",
    )
    old_metadata = dict(validated["metadata"])
    old_metadata.pop("adapter_protocol_id")
    old_metadata.pop("adapter_source_module")
    old_reference = tmp_path / "old-b07-reference.npz"
    np.savez_compressed(
        old_reference,
        **validated["arrays"],
        metadata_json=np.asarray(json.dumps(old_metadata)),
    )

    def forbidden_native_work(*args, **kwargs):
        raise AssertionError("old B07 reference reached native environment construction")

    monkeypatch.setattr(b07, "make_envs", forbidden_native_work)
    out = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="adapter_protocol_id"):
        r.run_fit(
            "E",
            out,
            "technical-check",
            spec=spec,
            device="cpu",
            reference_path=old_reference,
            reference_sha256=b07._sha256_file(old_reference),
        )
    assert not out.exists()


@pytest.mark.parametrize(
    "field,value",
    (
        ("init_seed", 1),
        ("train_rng_seed", 1),
        ("train_world_base", 1),
        ("eval_world_base", 1),
    ),
)
def test_wrong_fixed_address_is_rejected_before_engine_or_output(
    tmp_path, spec, monkeypatch, field, value
):
    calls = []
    monkeypatch.setattr(r, "ENGINE_RUN_FIT", lambda *args, **kwargs: calls.append(1))
    out = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="fixed RNG/world addresses differ"):
        r.run_fit("M", out, "technical-check", spec=replace(spec, **{field: value}))
    assert calls == []
    assert not out.exists()


def test_adapter_completion_failure_retains_failed_summary(tmp_path, spec, monkeypatch):
    out = tmp_path / "failed"

    def incomplete_engine(arm, output, launch_sha, **kwargs):
        output = Path(output)
        output.mkdir(parents=True)
        (output / "retained.bin").write_bytes(b"preserve-me")
        summary = {
            "status": "complete",
            "object_id": b07.OBJECT,
            "arm": arm,
            "spec": asdict(kwargs["spec"]),
            "counts": {},
            "training_rows": [],
        }
        b07.write_json(output / "summary.json", summary)
        return summary

    monkeypatch.setattr(r, "ENGINE_RUN_FIT", incomplete_engine)
    with pytest.raises(ValueError, match="adapter protocol"):
        r.run_fit("M", out, "technical-check", spec=spec, device="cpu")
    saved = json.loads((out / "summary.json").read_text())
    assert saved["status"] == "failed"
    assert saved["failure"]["stage"] == "b08_adapter_completed_contract"
    assert (out / "retained.bin").read_bytes() == b"preserve-me"


@pytest.mark.parametrize(
    "args",
    (
        ["--arm", "X", "--seed", str(r.FIXED_SEED)],
        ["--arm", "M", "--seed", "1"],
        ["--arm", "E", "--seed", str(r.FIXED_SEED)],
        [
            "--arm",
            "M",
            "--seed",
            str(r.FIXED_SEED),
            "--reference",
            "x",
            "--reference-sha256",
            "0",
        ],
    ),
)
def test_cli_rejects_bad_fixed_inputs_before_admission(tmp_path, args):
    out = tmp_path / "must-not-exist"
    result = subprocess.run(
        [
            sys.executable,
            str(b01.ROOT / "scripts/run_complementary_skill_learning_b08.py"),
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
            str(b01.ROOT / "scripts/run_complementary_skill_learning_b08.py"),
            "--arm",
            "M",
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


def test_cli_checks_launch_sha_and_passes_actual_spec(tmp_path, monkeypatch):
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
    assert entry.main(
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
    ) == 0
    assert captured["kwargs"]["spec"] is r.DEFAULT_SPEC
    assert captured["kwargs"]["admission"] is admission
    assert captured["kwargs"]["device"] == "cuda"


@pytest.mark.skipif(not torch.cuda.is_available(), reason="requires actual CUDA runtime")
def test_actual_4070_cuda_fixture_uses_b08_adapter(tmp_path, spec):
    summaries = _run_batch(tmp_path / "cuda-batch", replace(spec, rollouts=2), "cuda")
    assert [summaries[arm]["status"] for arm in ("M", "E", "U")] == [
        "complete",
        "complete",
        "complete",
    ]
    assert all(
        summaries[arm]["adapter_protocol"]["protocol_id"] == r.OBJECT
        for arm in summaries
    )
    assert summaries["M"]["native_optimizer_calls"]["coordinator"] > 0
    assert summaries["E"]["native_optimizer_calls"]["coordinator"] > 0
    assert summaries["U"]["native_optimizer_calls"]["coordinator"] == 0
