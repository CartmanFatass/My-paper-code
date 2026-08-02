"""Calibration tests for `scripts/report_vk0d_reference_digests.py` (A-VD-7
reference-arm digest report producer).

Each test targets one invariant that would make the report's A-VD-7 number
wrong if it silently broke:

- digest parity with the scratchpad recipe that produced the recorded
  witness digests on the truncated run (comparability across the run);
- exact-byte sensitivity of the state_dict digest (a numeric drift the
  comparison must not miss), proven against a deliberately weakened mutant
  that drops the bytes and calls the perturbed pair equal;
- exact-hyperparameter sensitivity of the optimizer digest (an lr drift the
  comparison must not miss);
- the A-VD-4 order-stream-draws accounting the reference arm's condition 4
  hinges on;
- the report's frozen field set is exactly what
  `scripts/analyze_vk0d_result.py` -- the actual, on-disk, frozen consumer
  -- reads, proven by importing and calling its own validator and
  `compute_reference_conforms`, never by re-describing the schema by hand;
- write-once output semantics.

Run with an explicit --basetemp (the default is broken on this machine):
  C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest
    tests/report_vk0d_reference_digests_test.py
    --basetemp=<scratch>/pytest_tmp -q
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import torch
import torch.nn as nn

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import report_vk0d_reference_digests as rvd
from scripts.analyze_vk0d_result import (
    compute_reference_conforms,
    validate_reference_digest_report_shape,
)
from scripts.run_vk0b_training import INTRINSIC_SHAPING_OFF
from ha_ctse_process.standalone_agent import (
    VK0D_ORDER_STREAM_NONE,
    VK0D_ORDER_STREAM_VERSION,
)

SCRATCHPAD_DIGEST_RECIPE = Path(
    r"C:\Users\fires\AppData\Local\Temp\claude\C--projects-My-paper-code"
    r"\4c20178a-f062-40b8-a625-f385d2c65136\scratchpad\vk0d_digest.py"
)
TRUNCATED_RUN_CHECKPOINT = Path(r"C:\tmp\vk0d_baseline_run\standalone_process_core_final.pt")

PYTHON = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"


# =============================================================================
# Fixture builders
# =============================================================================


def _make_synthetic_checkpoint(path: Path, *, seed: int = 0) -> None:
    """A small but real R30-shaped checkpoint: an actor, a value head and one
    Adam step over their combined parameters, so `high_opt["state"]` carries
    genuine `exp_avg`/`exp_avg_sq`/`step` tensors to digest -- not an empty
    optimizer with no per-parameter state to be insensitive to."""
    torch.manual_seed(seed)
    actor = nn.Linear(4, 3)
    value = nn.Linear(4, 1)
    opt = torch.optim.Adam(list(actor.parameters()) + list(value.parameters()), lr=1e-3)
    x = torch.randn(5, 4)
    loss = actor(x).sum() + value(x).sum()
    loss.backward()
    opt.step()
    torch.save(
        {"high": actor.state_dict(), "r30_high_value": value.state_dict(), "high_opt": opt.state_dict()},
        path,
    )


def _copy_checkpoint(src: Path, dst: Path) -> None:
    ck = torch.load(src, map_location="cpu", weights_only=False)
    torch.save(ck, dst)


def _copy_with_perturbed_actor_param(src: Path, dst: Path) -> None:
    ck = torch.load(src, map_location="cpu", weights_only=False)
    first_key = next(iter(ck["high"].keys()))
    ck["high"][first_key] = ck["high"][first_key] + 1e-3
    torch.save(ck, dst)


def _copy_with_perturbed_lr(src: Path, dst: Path) -> None:
    ck = torch.load(src, map_location="cpu", weights_only=False)
    ck["high_opt"]["param_groups"][0]["lr"] = float(ck["high_opt"]["param_groups"][0]["lr"]) * 2.0 + 1e-4
    torch.save(ck, dst)


def _valid_resolved(seed: int) -> dict:
    return {
        "scenario": "two_timescale_role_free_actions",
        "controller": "r30_fixed_clock_ar_edit",
        "k0": {"skill_interval": 5, "r39_toy_k0": 5},
        "n_agents": 2,
        "n_skills": 4,
        "num_envs": 16,
        "rollout_length": 40,
        "total_timesteps": 640_000,
        "device": "cpu",
        "low_optimizer_absence": {
            "use_recurrent_low_level": False,
            "r39_toy_fixed_skill_primitives": True,
        },
        "intrinsic_shaping_disabled": dict(INTRINSIC_SHAPING_OFF),
        "r30_training_order_policy": "canonical",
        "training_seed": seed,
    }


def _valid_manifest(seed: int, *, arm: str = "reference", nonscientific: bool = False) -> dict:
    return {"resolved": _valid_resolved(seed), "arm": arm, "nonscientific": nonscientific}


def _exposure_entry(value):
    return {"value": value, "source": "runtime_counter"}


def _valid_exposure_block(
    *, order_stream_version: str = VK0D_ORDER_STREAM_NONE, reversed_count: int = 0, total: int = 6000
) -> dict:
    return {
        "environment_interactions": _exposure_entry(640_000),
        "completed_outer_updates": _exposure_entry(1000),
        "high_epoch_passes_attempted": _exposure_entry(3000),
        "high_epoch_passes_stepped": _exposure_entry(3000),
        "high_epoch_passes_skipped": _exposure_entry(0),
        "high_epoch_passes_aborted": _exposure_entry(0),
        "high_optimizer_steps_shared": _exposure_entry(3000),
        "low_level_optimizer_steps": _exposure_entry(0),
        "high_optimizer_parameter_coverage_ok": {"value": True, "source": "runtime_counter"},
        "agent_tokens_keep": _exposure_entry(3000),
        "agent_tokens_set": _exposure_entry(3000),
        "high_check_sequences_completed": _exposure_entry(3000),
        "order_stream_version": order_stream_version,
        "r30_training_order_policy": "canonical",
        "schedule_digest": "0" * 64,
        "completed_reversed_sequences": _exposure_entry(reversed_count),
        "completed_sequence_total": _exposure_entry(total),
    }


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


# =============================================================================
# Digest parity with the scratchpad recipe
# =============================================================================


def test_digest_parity_with_scratchpad_recipe(tmp_path):
    assert SCRATCHPAD_DIGEST_RECIPE.is_file(), f"scratchpad recipe missing: {SCRATCHPAD_DIGEST_RECIPE}"
    spec = importlib.util.spec_from_file_location("vk0d_digest_scratchpad_recipe", SCRATCHPAD_DIGEST_RECIPE)
    scratchpad = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scratchpad)

    if TRUNCATED_RUN_CHECKPOINT.is_file():
        checkpoint_path = TRUNCATED_RUN_CHECKPOINT
    else:
        checkpoint_path = tmp_path / "fixture_checkpoint.pt"
        _make_synthetic_checkpoint(checkpoint_path)

    ck = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    actor, value, high_opt = ck["high"], ck["r30_high_value"], ck["high_opt"]
    param_names = [f"actor.{n}" for n in actor.keys()] + [f"value.{n}" for n in value.keys()]

    expected_actor = scratchpad._state_dict_digest(actor)
    expected_value = scratchpad._state_dict_digest(value)
    expected_opt = scratchpad._optimizer_digest(high_opt, param_names)

    mine = rvd.digest_checkpoint(checkpoint_path)

    assert mine["actor"] == expected_actor
    assert mine["value"] == expected_value
    assert mine["optimizer"] == expected_opt


# =============================================================================
# Equal checkpoints -> all_digests_equal True; report schema accepted by the
# real analyzer's own validator and `compute_reference_conforms`.
# =============================================================================


def test_equal_checkpoints_all_equal_true_and_analyzer_consumes_report(tmp_path):
    seed = 2026080101  # a real V-K0B scientific seed
    base = tmp_path / "base.pt"
    _make_synthetic_checkpoint(base, seed=1)
    vk0d_ckpt = tmp_path / "vk0d.pt"
    vk0b_ckpt = tmp_path / "vk0b.pt"
    _copy_checkpoint(base, vk0d_ckpt)
    _copy_checkpoint(base, vk0b_ckpt)

    exposure_path = tmp_path / "exposure.json"
    _write_json(exposure_path, _valid_exposure_block())
    manifest_path = tmp_path / "manifest.json"
    _write_json(manifest_path, _valid_manifest(seed))

    report = rvd.build_report(
        vk0d_checkpoint=vk0d_ckpt, vk0b_checkpoint=vk0b_ckpt, exposure_path=exposure_path, manifest_path=manifest_path
    )

    assert report["all_digests_equal"] is True
    assert report["components_equal"] == {"high_actor": True, "high_value": True, "high_optimizer": True}
    assert report["actor_state_dict_sha256"] == report["vk0b_actor_state_dict_sha256"]
    assert report["value_state_dict_sha256"] == report["vk0b_value_state_dict_sha256"]
    assert report["optimizer_state_sha256"] == report["vk0b_optimizer_state_sha256"]
    assert report["semantics_match"] is True, report["semantics_violations"]
    assert report["exposure_match"] is True, report["exposure_violations"]
    assert report["order_stream_draws_consumed"] == 0

    # The real, on-disk, frozen consumer's own schema validator -- never a
    # hand-written restatement of its field set.
    shape_errors = validate_reference_digest_report_shape(report, "reference_digest[test]")
    assert shape_errors == [], shape_errors

    # And the actual reference-gate arithmetic: a fabricated bundle wired
    # exactly the way `load_arm_bundle` wires one, showing the analyzer's
    # own `compute_reference_conforms` reads this report's fields correctly
    # and reaches REFERENCE_CONFORMS -- not merely shape-valid, genuinely
    # consumed.
    bundle = {
        "seeds": {str(seed): {"reference_digest_report": report}},
        "evaluation_summary": {
            "result": {"row": 4},
            "competence_floor": {
                "canonical": {
                    "slow_match": {"lower_95": 0.90, "upper_95": 0.95},
                    "fast_match": {"lower_95": 0.90, "upper_95": 0.95},
                },
                "reversed": {
                    "slow_match": {"lower_95": 0.10, "upper_95": 0.40},
                    "fast_match": {"lower_95": 0.10, "upper_95": 0.40},
                },
            },
        },
    }
    conforms, mismatches = compute_reference_conforms(bundle)
    assert conforms is True, mismatches


def test_output_is_write_once(tmp_path):
    seed = 2026080101
    base = tmp_path / "base.pt"
    _make_synthetic_checkpoint(base, seed=2)
    vk0d_ckpt = tmp_path / "vk0d.pt"
    vk0b_ckpt = tmp_path / "vk0b.pt"
    _copy_checkpoint(base, vk0d_ckpt)
    _copy_checkpoint(base, vk0b_ckpt)
    exposure_path = tmp_path / "exposure.json"
    _write_json(exposure_path, _valid_exposure_block())
    manifest_path = tmp_path / "manifest.json"
    _write_json(manifest_path, _valid_manifest(seed))

    report = rvd.build_report(
        vk0d_checkpoint=vk0d_ckpt, vk0b_checkpoint=vk0b_ckpt, exposure_path=exposure_path, manifest_path=manifest_path
    )
    out_path = tmp_path / "report.json"
    rvd.write_report_once(out_path, report)
    assert json.loads(out_path.read_text(encoding="utf-8"))["all_digests_equal"] is True

    with pytest.raises(rvd.Vk0dReferenceDigestRefusalError):
        rvd.write_report_once(out_path, report)


# =============================================================================
# Byte-perturbed checkpoint -> the affected component unequal, all_equal
# False. The watched red: a deliberately weakened comparison (bytes dropped
# from the hash) must call the SAME perturbed pair equal -- proving the
# bytes, not the name/shape/dtype header, are what carries the finding.
# =============================================================================


def test_byte_perturbation_flips_only_actor_equality(tmp_path):
    seed = 2026080101
    base = tmp_path / "base.pt"
    _make_synthetic_checkpoint(base, seed=3)
    vk0d_ckpt = tmp_path / "vk0d.pt"
    vk0b_ckpt = tmp_path / "vk0b.pt"
    _copy_checkpoint(base, vk0d_ckpt)
    _copy_with_perturbed_actor_param(base, vk0b_ckpt)

    exposure_path = tmp_path / "exposure.json"
    _write_json(exposure_path, _valid_exposure_block())
    manifest_path = tmp_path / "manifest.json"
    _write_json(manifest_path, _valid_manifest(seed))

    report = rvd.build_report(
        vk0d_checkpoint=vk0d_ckpt, vk0b_checkpoint=vk0b_ckpt, exposure_path=exposure_path, manifest_path=manifest_path
    )

    assert report["components_equal"]["high_actor"] is False
    assert report["components_equal"]["high_value"] is True
    assert report["components_equal"]["high_optimizer"] is True
    assert report["all_digests_equal"] is False
    assert report["actor_state_dict_sha256"] != report["vk0b_actor_state_dict_sha256"]


def test_watched_red_weakened_comparison_misses_the_byte_perturbation(tmp_path):
    """The tripwire: a deliberately weakened digest that binds only
    name|shape|dtype and NEVER hashes the tensor bytes must call the
    byte-perturbed pair equal. If it did not, the perturbation test above
    would not be proof that bytes are load-bearing in the real function."""
    base = tmp_path / "base.pt"
    _make_synthetic_checkpoint(base, seed=4)
    vk0d_ckpt = tmp_path / "vk0d.pt"
    vk0b_ckpt = tmp_path / "vk0b.pt"
    _copy_checkpoint(base, vk0d_ckpt)
    _copy_with_perturbed_actor_param(base, vk0b_ckpt)

    def weakened_digest_dropping_bytes(state_dict) -> str:
        import hashlib

        h = hashlib.sha256()
        for name in sorted(state_dict.keys()):
            t = state_dict[name]
            h.update(name.encode("utf-8"))
            h.update(b"|")
            h.update(str(tuple(t.shape)).encode("utf-8"))
            h.update(b"|")
            h.update(str(t.dtype).encode("utf-8"))
            h.update(b"\n")  # bytes deliberately never hashed
        return h.hexdigest()

    ck_d = torch.load(vk0d_ckpt, map_location="cpu", weights_only=False)
    ck_b = torch.load(vk0b_ckpt, map_location="cpu", weights_only=False)

    # The real comparison correctly disagrees...
    assert rvd.canonical_state_dict_digest(ck_d["high"]) != rvd.canonical_state_dict_digest(ck_b["high"])
    # ...but the weakened mutant, which drops the bytes, calls it equal --
    # the guard this test watches is precisely "bytes are compared", and this
    # shows what happens when that guard is removed.
    assert weakened_digest_dropping_bytes(ck_d["high"]) == weakened_digest_dropping_bytes(ck_b["high"])


# =============================================================================
# Optimizer digest sensitive to a hyperparameter (lr) change.
# =============================================================================


def test_optimizer_digest_sensitive_to_lr_perturbation(tmp_path):
    seed = 2026080101
    base = tmp_path / "base.pt"
    _make_synthetic_checkpoint(base, seed=5)
    vk0d_ckpt = tmp_path / "vk0d.pt"
    vk0b_ckpt = tmp_path / "vk0b.pt"
    _copy_checkpoint(base, vk0d_ckpt)
    _copy_with_perturbed_lr(base, vk0b_ckpt)

    exposure_path = tmp_path / "exposure.json"
    _write_json(exposure_path, _valid_exposure_block())
    manifest_path = tmp_path / "manifest.json"
    _write_json(manifest_path, _valid_manifest(seed))

    report = rvd.build_report(
        vk0d_checkpoint=vk0d_ckpt, vk0b_checkpoint=vk0b_ckpt, exposure_path=exposure_path, manifest_path=manifest_path
    )

    assert report["components_equal"]["high_optimizer"] is False
    assert report["components_equal"]["high_actor"] is True
    assert report["components_equal"]["high_value"] is True
    assert report["all_digests_equal"] is False


# =============================================================================
# order_stream_draws_consumed / A-VD-4 exposure accounting.
# =============================================================================


def test_order_stream_none_yields_zero_draws_consumed():
    block = _valid_exposure_block(order_stream_version=VK0D_ORDER_STREAM_NONE, reversed_count=0, total=6000)
    assert rvd.compute_order_stream_draws_consumed(block) == 0


def test_order_stream_present_yields_nonzero_draws_consumed():
    block = _valid_exposure_block(order_stream_version=VK0D_ORDER_STREAM_VERSION, reversed_count=2400, total=6000)
    draws = rvd.compute_order_stream_draws_consumed(block)
    assert draws == 6000
    assert draws != 0


def test_order_stream_none_with_nonzero_reversed_is_a_hard_refusal():
    block = _valid_exposure_block(order_stream_version=VK0D_ORDER_STREAM_NONE, reversed_count=3, total=6000)
    with pytest.raises(rvd.Vk0dReferenceDigestRefusalError):
        rvd.compute_order_stream_draws_consumed(block)


def test_malformed_exposure_block_is_a_hard_refusal_never_a_default_zero():
    with pytest.raises(rvd.Vk0dReferenceDigestRefusalError):
        rvd.compute_order_stream_draws_consumed({"order_stream_version": "not-a-real-identity"})
    with pytest.raises(rvd.Vk0dReferenceDigestRefusalError):
        rvd.compute_order_stream_draws_consumed(None)


def test_reference_full_pipeline_rejects_when_order_stream_present(tmp_path):
    """End-to-end: an exposure block that shows the order-randomization
    stream fired (a bug that would leak the CONTROL arm's behavior into a
    REFERENCE run) must make the built report fail A-VD-7 condition 4 in the
    real analyzer's own arithmetic, not just locally."""
    seed = 2026080101
    base = tmp_path / "base.pt"
    _make_synthetic_checkpoint(base, seed=6)
    vk0d_ckpt = tmp_path / "vk0d.pt"
    vk0b_ckpt = tmp_path / "vk0b.pt"
    _copy_checkpoint(base, vk0d_ckpt)
    _copy_checkpoint(base, vk0b_ckpt)

    exposure_path = tmp_path / "exposure.json"
    _write_json(
        exposure_path,
        _valid_exposure_block(order_stream_version=VK0D_ORDER_STREAM_VERSION, reversed_count=2400, total=6000),
    )
    manifest_path = tmp_path / "manifest.json"
    _write_json(manifest_path, _valid_manifest(seed))

    report = rvd.build_report(
        vk0d_checkpoint=vk0d_ckpt, vk0b_checkpoint=vk0b_ckpt, exposure_path=exposure_path, manifest_path=manifest_path
    )
    assert report["order_stream_draws_consumed"] == 6000

    shape_errors = validate_reference_digest_report_shape(report, "reference_digest[test]")
    assert shape_errors == [], shape_errors

    bundle = {
        "seeds": {str(seed): {"reference_digest_report": report}},
        "evaluation_summary": {
            "result": {"row": 4},
            "competence_floor": {
                "canonical": {
                    "slow_match": {"lower_95": 0.90, "upper_95": 0.95},
                    "fast_match": {"lower_95": 0.90, "upper_95": 0.95},
                },
                "reversed": {
                    "slow_match": {"lower_95": 0.10, "upper_95": 0.40},
                    "fast_match": {"lower_95": 0.10, "upper_95": 0.40},
                },
            },
        },
    }
    conforms, mismatches = compute_reference_conforms(bundle)
    assert conforms is False
    assert any("order-stream draw" in m for m in mismatches), mismatches


# =============================================================================
# semantics_match / exposure_match wiring (A-VD-7 condition 4)
# =============================================================================


def test_semantics_mismatch_flips_flag_false(tmp_path):
    seed = 2026080101
    base = tmp_path / "base.pt"
    _make_synthetic_checkpoint(base, seed=7)
    vk0d_ckpt = tmp_path / "vk0d.pt"
    vk0b_ckpt = tmp_path / "vk0b.pt"
    _copy_checkpoint(base, vk0d_ckpt)
    _copy_checkpoint(base, vk0b_ckpt)

    exposure_path = tmp_path / "exposure.json"
    _write_json(exposure_path, _valid_exposure_block())

    bad_resolved = _valid_resolved(seed)
    bad_resolved["total_timesteps"] = 1  # violates the frozen VK-D8 expectation
    manifest_path = tmp_path / "manifest.json"
    _write_json(manifest_path, {"resolved": bad_resolved, "arm": "reference", "nonscientific": False})

    report = rvd.build_report(
        vk0d_checkpoint=vk0d_ckpt, vk0b_checkpoint=vk0b_ckpt, exposure_path=exposure_path, manifest_path=manifest_path
    )
    assert report["semantics_match"] is False
    assert report["semantics_violations"]


def test_exposure_identical_contract_mismatch_flips_flag_false(tmp_path):
    seed = 2026080101
    base = tmp_path / "base.pt"
    _make_synthetic_checkpoint(base, seed=8)
    vk0d_ckpt = tmp_path / "vk0d.pt"
    vk0b_ckpt = tmp_path / "vk0b.pt"
    _copy_checkpoint(base, vk0d_ckpt)
    _copy_checkpoint(base, vk0b_ckpt)

    bad_block = _valid_exposure_block()
    bad_block["completed_outer_updates"] = _exposure_entry(1)  # violates A-W6-2 exact identity
    exposure_path = tmp_path / "exposure.json"
    _write_json(exposure_path, bad_block)
    manifest_path = tmp_path / "manifest.json"
    _write_json(manifest_path, _valid_manifest(seed))

    report = rvd.build_report(
        vk0d_checkpoint=vk0d_ckpt, vk0b_checkpoint=vk0b_ckpt, exposure_path=exposure_path, manifest_path=manifest_path
    )
    assert report["exposure_match"] is False
    assert report["exposure_violations"]


# =============================================================================
# One bounded end-to-end CLI exercise (material integration: argparse ->
# build_report -> write-once, via the real project interpreter).
# =============================================================================


def test_cli_end_to_end(tmp_path):
    seed = 2026080101
    base = tmp_path / "base.pt"
    _make_synthetic_checkpoint(base, seed=9)
    vk0d_ckpt = tmp_path / "vk0d.pt"
    vk0b_ckpt = tmp_path / "vk0b.pt"
    _copy_checkpoint(base, vk0d_ckpt)
    _copy_checkpoint(base, vk0b_ckpt)

    exposure_path = tmp_path / "exposure.json"
    _write_json(exposure_path, _valid_exposure_block())
    manifest_path = tmp_path / "manifest.json"
    _write_json(manifest_path, _valid_manifest(seed))
    out_path = tmp_path / "out" / "report.json"

    result = subprocess.run(
        [
            PYTHON,
            "-B",
            str(PROJECT_ROOT / "scripts" / "report_vk0d_reference_digests.py"),
            "--vk0d-checkpoint",
            str(vk0d_ckpt),
            "--vk0b-checkpoint",
            str(vk0b_ckpt),
            "--exposure",
            str(exposure_path),
            "--manifest",
            str(manifest_path),
            "--out",
            str(out_path),
        ],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VK0D_REFERENCE_DIGEST_ALL_EQUAL=True" in result.stdout, result.stdout
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written["all_digests_equal"] is True
    assert validate_reference_digest_report_shape(written, "reference_digest[cli]") == []
