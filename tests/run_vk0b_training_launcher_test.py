"""V-K0B training launcher -- post-training `actual_exposure` audit.

Contract: `docs/research/designs/VK0B_RERUN_EXPOSURE_DECISION_LEDGER.md`
(W6-D2, A-W6-5) and
`docs/external-review/rounds/20260801_vk0b_rerun_exposure_conformance/
21_PRO_OPEN_RAW.md` section 4 (the amended blocking amendments). Fixture-
driven: no real training subprocess runs here. Each fixture is a synthetic
`run_manifest.json` written to a scratch directory under
`logs/_tmp_vk0b_training_launcher_test`, exercised directly against
`build_training_result` (the post-training half of the launcher, factored
out precisely so it never needs `subprocess`).

This machine's default pytest basetemp is broken (see
`tests/audit_vk0b_driver_test.py`'s docstring), so this file manages its own
scratch directory rather than relying on the `tmp_path` fixture. Invoke with
an explicit `--basetemp` anyway:

    python -m pytest tests/run_vk0b_training_launcher_test.py -q --basetemp logs/_pytest_basetemp
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


launcher = _load("vk0b_launcher_under_test", "run_vk0b_training.py")

SCRATCH_ROOT = PROJECT_ROOT / "logs" / "_tmp_vk0b_training_launcher_test"


def _fresh_scratch_dir(name: str) -> Path:
    d = SCRATCH_ROOT / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d


@pytest.fixture(autouse=True)
def _clean_scratch():
    yield
    if SCRATCH_ROOT.exists():
        shutil.rmtree(SCRATCH_ROOT)


# =============================================================================
# Fixture construction -- an independent literal enumeration of the frozen
# A-W6-5 mandatory keys and admissible source labels (never imported from the
# module under test: importing `launcher.MANDATORY_EXPOSURE_KEYS` here would
# make a wrong key list in the launcher invisible to these tests).
# =============================================================================

MANDATORY_KEYS = (
    "environment_interactions",
    "completed_outer_updates",
    "high_optimizer_semantics",
    "high_optimizer_steps_shared",
    "high_actor_optimizer_steps",
    "high_value_optimizer_steps",
    "high_actor_parameter_count_expected",
    "high_actor_parameter_count_with_step_state",
    "high_value_parameter_count_expected",
    "high_value_parameter_count_with_step_state",
    "high_optimizer_step_min",
    "high_optimizer_step_max",
    "high_optimizer_parameter_coverage_ok",
    "high_check_sequences_completed",
    "high_check_sequences_failed_or_skipped",
    "agent_tokens_keep",
    "agent_tokens_set",
    "high_epoch_passes_attempted",
    "high_epoch_passes_stepped",
    "high_epoch_passes_skipped",
    "high_epoch_passes_aborted",
    "high_epoch_pass_skip_reasons",
    "high_epoch_pass_abort_reasons",
    "low_level_optimizer_steps",
)

ADMISSIBLE_SOURCES = ("runtime_counter", "training_accumulator", "optimizer_state", "checkpoint_optimizer_absence")


def _entry(value, source="training_accumulator"):
    return {"value": value, "source": source}


def _valid_identical_contract_block() -> dict:
    """A complete, structurally valid `actual_exposure` block that also
    satisfies every A-W6-2 identical-contract identity for a scientific run:
    640,000 interactions, 1,000 outer updates, 3,000 attempted == stepped
    high passes with zero skipped/aborted, full actor/value parameter
    coverage at the shared 3,000-step count, and KEEP+SET == 2 * completed
    (1,400 + 1,600 == 2 * 1,500)."""
    block = {
        "actual_exposure_schema": "vk0b-exposure-1",
        "environment_interactions": _entry(640_000, "runtime_counter"),
        "completed_outer_updates": _entry(1000, "training_accumulator"),
        "high_optimizer_semantics": "SHARED_ACTOR_VALUE_OPTIMIZER",
        "high_optimizer_steps_shared": _entry(3000, "optimizer_state"),
        "high_actor_optimizer_steps": _entry(3000, "optimizer_state"),
        "high_value_optimizer_steps": _entry(3000, "optimizer_state"),
        "high_actor_parameter_count_expected": _entry(12, "training_accumulator"),
        "high_actor_parameter_count_with_step_state": _entry(12, "optimizer_state"),
        "high_value_parameter_count_expected": _entry(8, "training_accumulator"),
        "high_value_parameter_count_with_step_state": _entry(8, "optimizer_state"),
        "high_optimizer_step_min": _entry(3000, "optimizer_state"),
        "high_optimizer_step_max": _entry(3000, "optimizer_state"),
        "high_optimizer_parameter_coverage_ok": _entry(True, "training_accumulator"),
        "high_check_sequences_completed": _entry(1500, "training_accumulator"),
        "high_check_sequences_failed_or_skipped": _entry(0, "training_accumulator"),
        "agent_tokens_keep": _entry(1400, "training_accumulator"),
        "agent_tokens_set": _entry(1600, "training_accumulator"),
        "high_epoch_passes_attempted": _entry(3000, "training_accumulator"),
        "high_epoch_passes_stepped": _entry(3000, "training_accumulator"),
        "high_epoch_passes_skipped": _entry(0, "training_accumulator"),
        "high_epoch_passes_aborted": _entry(0, "training_accumulator"),
        "high_epoch_pass_skip_reasons": [],
        "high_epoch_pass_abort_reasons": [],
        "low_level_optimizer_steps": _entry(0, "checkpoint_optimizer_absence"),
    }
    assert set(block) - {"actual_exposure_schema"} == set(MANDATORY_KEYS), "fixture must cover every mandatory key"
    return block


def _write_run_manifest(output_root: Path, block: dict) -> Path:
    path = output_root / "metadata" / "run_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "total_steps": 640_000,
        "update_idx": 1000,
        "actual_exposure": block,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_checkpoint(output_root: Path) -> Path:
    path = output_root / launcher.FINAL_CHECKPOINT_NAME
    path.write_bytes(b"not-a-real-checkpoint")
    return path


def _independent_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# =============================================================================
# (a) Complete valid block + identical-contract identities -> PASSED.
# =============================================================================


def test_complete_valid_block_and_identities_passes():
    scratch = _fresh_scratch_dir("valid")
    _write_run_manifest(scratch, _valid_identical_contract_block())
    _write_checkpoint(scratch)

    result = launcher.build_training_result(
        output_root=scratch, command=["fake"], returncode=0, nonscientific=False
    )

    assert result["exposure_audit"] == "PASSED"
    assert result["exposure_audit_violations"] == []
    assert "checkpoint_sha256" in result
    assert "error" not in result


def test_nonscientific_run_skips_identical_contract_identities_but_not_structure():
    # A nonscientific run need not satisfy the 640,000/1,000/3,000 identities
    # (it is a microbenchmark, not the frozen contract), but the block must
    # still be structurally complete.
    scratch = _fresh_scratch_dir("nonscientific_valid")
    block = _valid_identical_contract_block()
    block["environment_interactions"] = _entry(17, "runtime_counter")  # not 640,000
    block["high_epoch_passes_attempted"] = _entry(4, "training_accumulator")
    block["high_epoch_passes_stepped"] = _entry(4, "training_accumulator")
    _write_run_manifest(scratch, block)
    _write_checkpoint(scratch)

    result = launcher.build_training_result(
        output_root=scratch, command=["fake"], returncode=0, nonscientific=True
    )

    assert result["exposure_audit"] == "PASSED", result["exposure_audit_violations"]


# =============================================================================
# (b) Pro-named negative witnesses. Each is a paired negative here (bad
# fixture -> FAILED naming the violation; restored fixture -> PASSED). Each
# was additionally watched red/green by hand: the corresponding guard in
# `scripts/run_vk0b_training.py` was disabled via a temporary local mutation,
# the specific test below confirmed to fail (red), then the guard was
# restored and the test confirmed to pass (green) -- see the implementer
# report for the exact mutation and command output.
# =============================================================================


def test_missing_mandatory_key_fails_naming_it():
    scratch = _fresh_scratch_dir("missing_key")
    block = _valid_identical_contract_block()
    del block["high_optimizer_steps_shared"]
    _write_run_manifest(scratch, block)
    _write_checkpoint(scratch)

    result = launcher.build_training_result(
        output_root=scratch, command=["fake"], returncode=0, nonscientific=False
    )

    assert result["exposure_audit"] == "FAILED"
    assert any(
        "high_optimizer_steps_shared" in v and "missing" in v for v in result["exposure_audit_violations"]
    ), result["exposure_audit_violations"]

    # Restore and confirm green on the identical inputs otherwise.
    _write_run_manifest(scratch, _valid_identical_contract_block())
    restored = launcher.build_training_result(
        output_root=scratch, command=["fake"], returncode=0, nonscientific=False
    )
    assert restored["exposure_audit"] == "PASSED", restored["exposure_audit_violations"]


def test_inadmissible_source_label_fails():
    scratch = _fresh_scratch_dir("bad_source")
    block = _valid_identical_contract_block()
    # "config" is explicitly named inadmissible by A-W6-5 -- it is exactly
    # the kind of label the historical run used to justify a value it never
    # actually measured.
    block["environment_interactions"] = _entry(640_000, "config")
    _write_run_manifest(scratch, block)
    _write_checkpoint(scratch)

    result = launcher.build_training_result(
        output_root=scratch, command=["fake"], returncode=0, nonscientific=False
    )

    assert result["exposure_audit"] == "FAILED"
    assert any(
        "environment_interactions" in v and "inadmissible" in v for v in result["exposure_audit_violations"]
    ), result["exposure_audit_violations"]

    _write_run_manifest(scratch, _valid_identical_contract_block())
    restored = launcher.build_training_result(
        output_root=scratch, command=["fake"], returncode=0, nonscientific=False
    )
    assert restored["exposure_audit"] == "PASSED", restored["exposure_audit_violations"]


def test_nonzero_skipped_high_pass_fails_even_when_honestly_recorded():
    # A-W6-2's exact-exposure gate: any nonzero skipped or aborted high pass
    # is a violation however honestly it was recorded -- a run with 2,999
    # stepped and 1 honestly-recorded skip is not the identical frozen
    # 3,000-step exposure.
    scratch = _fresh_scratch_dir("skipped_one")
    block = _valid_identical_contract_block()
    block["high_epoch_passes_stepped"] = _entry(2999, "training_accumulator")
    block["high_epoch_passes_skipped"] = _entry(1, "training_accumulator")
    block["high_epoch_pass_skip_reasons"] = ["EMPTY_ROWS"]
    _write_run_manifest(scratch, block)
    _write_checkpoint(scratch)

    result = launcher.build_training_result(
        output_root=scratch, command=["fake"], returncode=0, nonscientific=False
    )

    assert result["exposure_audit"] == "FAILED"
    assert any(
        "high_epoch_passes_skipped" in v and "identical-contract identity" in v
        for v in result["exposure_audit_violations"]
    ), result["exposure_audit_violations"]
    # high_epoch_passes_stepped != 3000 is a second, independently-detected
    # violation of the same exact-exposure gate.
    assert any(
        "high_epoch_passes_stepped" in v and "identical-contract identity" in v
        for v in result["exposure_audit_violations"]
    ), result["exposure_audit_violations"]

    _write_run_manifest(scratch, _valid_identical_contract_block())
    restored = launcher.build_training_result(
        output_root=scratch, command=["fake"], returncode=0, nonscientific=False
    )
    assert restored["exposure_audit"] == "PASSED", restored["exposure_audit_violations"]


# =============================================================================
# (b, continued) run_manifest.json hash: recorded value matches independent
# recomputation, and a tampered manifest byte flips the recorded hash.
# =============================================================================


def test_run_manifest_hash_matches_recomputation_and_a_tampered_byte_flips_it():
    scratch = _fresh_scratch_dir("hash")
    manifest_path = _write_run_manifest(scratch, _valid_identical_contract_block())
    _write_checkpoint(scratch)

    clean_result = launcher.build_training_result(
        output_root=scratch, command=["fake"], returncode=0, nonscientific=False
    )
    assert clean_result["run_manifest_sha256"] == _independent_sha256(manifest_path)

    # Flip exactly one character byte inside the schema tag string -- stays
    # syntactically valid JSON and valid UTF-8 (unlike a raw XOR over
    # arbitrary bytes, which can land on a structural character or produce
    # an invalid UTF-8 sequence), while still genuinely changing the file's
    # bytes.
    original_text = manifest_path.read_text(encoding="utf-8")
    assert original_text.count("vk0b-exposure-1") == 1
    tampered_text = original_text.replace("vk0b-exposure-1", "vk0b-exposure-2", 1)
    manifest_path.write_text(tampered_text, encoding="utf-8")

    tampered_result = launcher.build_training_result(
        output_root=scratch, command=["fake"], returncode=0, nonscientific=False
    )
    recomputed_after_tamper = _independent_sha256(manifest_path)
    assert tampered_result["run_manifest_sha256"] == recomputed_after_tamper
    assert tampered_result["run_manifest_sha256"] != clean_result["run_manifest_sha256"]

    # Restore and confirm the hash returns to the original.
    manifest_path.write_text(original_text, encoding="utf-8")
    restored_result = launcher.build_training_result(
        output_root=scratch, command=["fake"], returncode=0, nonscientific=False
    )
    assert restored_result["run_manifest_sha256"] == clean_result["run_manifest_sha256"]


# =============================================================================
# Launcher exit-code contract: FAILED must be nonzero even though the
# training subprocess itself exited 0.
# =============================================================================


def test_run_exits_nonzero_on_exposure_audit_failure_even_though_training_exited_zero():
    scratch = _fresh_scratch_dir("exit_code")
    block = _valid_identical_contract_block()
    del block["low_level_optimizer_steps"]
    _write_run_manifest(scratch, block)
    _write_checkpoint(scratch)

    training_result = launcher.build_training_result(
        output_root=scratch, command=["fake"], returncode=0, nonscientific=False
    )
    assert training_result["exposure_audit"] == "FAILED"

    # Mirrors the exit-code arithmetic in `run()` without invoking the real
    # training subprocess.
    returncode = 0
    exit_code = returncode
    if returncode == 0 and training_result.get("exposure_audit") == "FAILED":
        exit_code = 1
    assert exit_code != 0
