"""Section-11 recast of UCOPE (2026-09-02): gates became recorded fields.

Authority: owner decision 2 and decision 7 of
``docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md`` A.4, the portfolio
record ``docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md``, and
the direction intake
``docs/research/candidates/ucope/UCOPE_SECTION11_RECAST_INTAKE_20260902.md``, against
``docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`` §11.4/§11.6, §5.2 and §6.2.

Five properties, one per demoted condition class:

i.   a dirty working-tree source inventory is recorded, not refused;
ii.  a missing or contract-ineligible performance assessment is recorded, not refused;
iii. the exact-oracle competence predicate is computed and reported but changes neither the
     run's completion nor its publication;
iv.  a missing resource measurement sets ``resources_unmeasured`` and does not quarantine;
v.   a learner-side failure still quarantines under §6.2.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
from pathlib import Path
import subprocess

import pytest

from experiments.candidates.ucope.competence_first_scout_r01.contract import (
    ARM_IDS,
    B1_SEEDS,
    LADDER_ARMS,
    LADDER_RUNG_1_ID,
    LADDER_RUNG_1_LEARNING_RATE,
    ScoutConfig,
)
from experiments.candidates.ucope.competence_first_scout_r01.evaluation import PolicyEvaluation
from experiments.candidates.ucope.competence_first_scout_r01.gates import apply_gates

PROJECT_ROOT = Path(__file__).resolve().parents[4]

EXACT_TOPOLOGY = {
    "deterministic_algorithms": True,
    "intraop_threads": 1,
    "interop_threads": 1,
    "interop_supported": True,
    "configured_once": True,
    "static_no_spawn": {"files_checked": 3, "spawn_imports": 0, "topology": "single_inline_root_process"},
}


def _load(name: str, relative: str):
    path = PROJECT_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def discriminator():
    return _load("ucope_recast_discriminator", "scripts/run_ucope_bc_conditioning_discriminator_r01.py")


@pytest.fixture(scope="module")
def ladder():
    return _load("ucope_recast_ladder", "scripts/run_ucope_exposure_ladder_rung1.py")


# ---------------------------------------------------------------------------------------
# The named exposure-ladder object itself
# ---------------------------------------------------------------------------------------


def test_exposure_ladder_rung_1_is_a_named_object_changing_only_its_declared_axis():
    rung = ScoutConfig.ladder_rung_1()
    b1 = ScoutConfig.b1()
    assert rung.mode == "LADDER1"
    assert rung.learning_rate == LADDER_RUNG_1_LEARNING_RATE == 3e-3
    assert rung.arms == LADDER_ARMS == ("FT-XF-FLEX", "FT-XF-BC")
    assert set(rung.arms).issubset(set(ARM_IDS))
    # Everything else is the frozen B1 object, unchanged.
    for field in (
        "seed_ids", "episodes_per_context", "tail_updates", "root_updates",
        "evaluation_root_updates", "sampled_evaluation_episodes", "batch_size",
        "object_id", "rng_version",
    ):
        assert getattr(rung, field) == getattr(b1, field), field
    assert rung.seed_ids == B1_SEEDS
    assert (rung.tail_updates, rung.root_updates) == (160, 320)
    assert LADDER_RUNG_1_ID.endswith("RUNG-1")


def test_pre_recast_artifacts_still_load_without_a_learning_rate_field():
    """The recast added a config field; it must not orphan the frozen B1 artifacts."""
    legacy = {key: value for key, value in ScoutConfig.b1().to_dict().items() if key != "learning_rate"}
    assert ScoutConfig.from_dict(legacy) == ScoutConfig.b1()


# ---------------------------------------------------------------------------------------
# (i) dirty source is recorded, not refused
# ---------------------------------------------------------------------------------------


def _dirty_git(monkeypatch, module, lines):
    real = subprocess.run

    def fake(command, *args, **kwargs):
        if command[:2] == ["git", "status"]:
            return subprocess.CompletedProcess(command, 0, stdout="\n".join(lines) + "\n", stderr="")
        if command[:2] == ["git", "rev-parse"]:
            return subprocess.CompletedProcess(command, 0, stdout="a" * 40 + "\n", stderr="")
        return real(command, *args, **kwargs)

    monkeypatch.setattr(module.subprocess, "run", fake)


def test_dirty_source_is_recorded_not_refused_by_the_discriminator(discriminator, monkeypatch):
    dirty = [" M scripts/run_ucope_bc_conditioning_discriminator_r01.py"]
    _dirty_git(monkeypatch, discriminator, dirty)
    record = discriminator.source_binding()
    assert record["status"]["clean"] is False
    assert record["status"]["porcelain"] == dirty
    assert record["status"]["gating"] is False
    assert record["revision"] == "a" * 40
    assert record["inventory"], "the source byte inventory is still recorded"
    # The pre-recast refusal string is gone from the runner entirely.
    text = (PROJECT_ROOT / "scripts/run_ucope_bc_conditioning_discriminator_r01.py").read_text(encoding="utf-8")
    assert 'raise RunnerRefusal("prepare-run requires clean committed source inventory")' not in text


def test_dirty_source_is_recorded_not_refused_by_the_ladder(ladder, monkeypatch):
    dirty = [" M experiments/candidates/ucope/competence_first_scout_r01/contract.py"]
    _dirty_git(monkeypatch, ladder, dirty)
    record = ladder.source_status_record()
    assert record["clean"] is False
    assert record["porcelain_status"] == dirty
    assert record["gating"] is False
    assert record["git_head"] == "a" * 40
    assert len(record["aggregate_sha256"]) == 64


def test_prepare_run_creates_a_manifest_over_a_dirty_tree(discriminator, monkeypatch, tmp_path):
    _dirty_git(monkeypatch, discriminator, [" M scripts/run_ucope_bc_conditioning_discriminator_r01.py"])
    manifest_path = tmp_path / "manifests" / "result-01.json"
    manifest_path.parent.mkdir(parents=True)
    output = tmp_path / "output"
    monkeypatch.setattr(discriminator, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(discriminator, "OUTPUT_ROOT", output)
    monkeypatch.setattr(discriminator, "configure_torch_topology_once", lambda: dict(EXACT_TOPOLOGY))
    created = discriminator.prepare_run(manifest_path, output)
    value = json.loads(Path(created).read_text(encoding="utf-8"))
    assert value["format"] == discriminator.RECAST_MANIFEST_FORMAT
    assert value["source_status"]["clean"] is False
    assert value["source_status"]["gating"] is False
    assert value["performance_assessment"]["gating"] is False
    # It still validates, and still detects tampering.
    discriminator.validate_manifest(value)
    with pytest.raises(ValueError, match="binding"):
        discriminator.validate_manifest(dict(value, output_root="changed"))


# ---------------------------------------------------------------------------------------
# (ii) missing / ineligible assessment is recorded, not refused
# ---------------------------------------------------------------------------------------


def test_ineligible_assessment_02_is_recorded_with_both_facts(discriminator, monkeypatch, tmp_path):
    monkeypatch.setattr(discriminator, "ASSESSMENT_PATH", tmp_path / "absent-assessment-03.json")
    record = discriminator.recorded_assessment()
    assert record["present"] is True
    assert record["path"].endswith("assessment-02.json")
    # Both facts, per the owner decision: the file says PERFORMANCE_READY, the contract
    # declares it INVALID_NOT_ADOPTED, and neither gates.
    assert record["disposition"] == "PERFORMANCE_READY"
    assert record["contract_declaration"] == "INVALID_NOT_ADOPTED"
    assert record["gating"] is False


def test_a_wholly_absent_assessment_is_recorded_not_refused(discriminator, monkeypatch, tmp_path):
    for name in ("ASSESSMENT_PATH", "RETAINED_ASSESSMENT_02_PATH", "RETAINED_ASSESSMENT_01_PATH"):
        monkeypatch.setattr(discriminator, name, tmp_path / f"absent-{name}.json")
    record = discriminator.recorded_assessment()
    assert record["present"] is False
    assert record["disposition"] == "NOT_ASSESSED"
    assert record["contract_declaration"] == "REQUIRED_BY_CONTRACT_ABSENT_ON_DISK"
    assert record["gating"] is False
    assert discriminator.recorded_caps(record) == discriminator.NO_CAP
    _dirty_git(monkeypatch, discriminator, [])
    manifest_path = tmp_path / "manifests" / "result-01.json"
    manifest_path.parent.mkdir(parents=True)
    output = tmp_path / "output"
    monkeypatch.setattr(discriminator, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(discriminator, "OUTPUT_ROOT", output)
    monkeypatch.setattr(discriminator, "configure_torch_topology_once", lambda: dict(EXACT_TOPOLOGY))
    value = json.loads(Path(discriminator.prepare_run(manifest_path, output)).read_text(encoding="utf-8"))
    assert value["performance_assessment"]["disposition"] == "NOT_ASSESSED"
    discriminator.validate_manifest(value)


def test_the_bound_assessment_check_records_instead_of_raising(discriminator):
    live = discriminator.recorded_assessment()
    manifest = {"performance_assessment": {"sha256": "0" * 64, "assessment_id": "stale"}}
    record = discriminator._validate_bound_assessment(manifest)
    assert record["gating"] is False
    assert record["matches_manifest"] is False
    assert record["live_record"]["disposition"] == live["disposition"]
    text = (PROJECT_ROOT / "scripts/run_ucope_bc_conditioning_discriminator_r01.py").read_text(encoding="utf-8")
    assert 'raise RunnerRefusal("manifest assessment-03 binding mismatch")' not in text
    assert 'raise RunnerRefusal("result resource cap exceeded")' not in text


def test_the_ladder_records_the_absence_of_a_performance_assessment(ladder):
    record = ladder.performance_assessment_record()
    assert record["gating"] is False
    assert record["assessment_present"] is False
    assert record["disposition"] == "NOT_ASSESSED"
    assert "performance_ready_assessment" in ladder.RECAST_LEDGER["recorded_not_gating"]


# ---------------------------------------------------------------------------------------
# (iii) the competence predicate is reported, and decides nothing
# ---------------------------------------------------------------------------------------


def _evaluation(arm, seed, fold, *, competent, acquisition=False):
    return PolicyEvaluation(
        arm_id=arm, seed_id=seed, fold_id=fold, root_update=320,
        root_actions={}, root_selected_labels={}, tail_periods={}, root_scores={}, tail_scores={},
        all_finite=True, all_unique=True, oracle_root_match=competent,
        max_regret=0.0 if competent else 0.9, minimum_tail_agreement=1.0 if competent else 0.0,
        target_delta_acquisition=None, direct_probe_component=None,
        competence_pass=competent, acquisition_pass=acquisition,
        exact_policy_evaluations=8, sampled_evaluation_episodes=8, sampled_evaluation_transitions=8,
        sampled_external_return_sum=0.0, sampled_context_diagnostics={},
    )


def _ladder_evaluations(*, competent, acquisition=False):
    return tuple(
        _evaluation(arm, seed, fold, competent=competent, acquisition=acquisition)
        for arm in LADDER_ARMS for seed in B1_SEEDS for fold in (0, 1)
    )


def test_competence_is_reported_for_both_outcomes_and_never_raises():
    none = apply_gates(_ladder_evaluations(competent=False), seed_ids=B1_SEEDS, final_root_update=320, arms=LADDER_ARMS)
    every = apply_gates(_ladder_evaluations(competent=True, acquisition=True), seed_ids=B1_SEEDS, final_root_update=320, arms=LADDER_ARMS)
    assert none["branch"] == "NO_ARM_COMPETENT"
    assert every["branch"] == "FLEX_COMPETENCE_PLUS_ACQUISITION"
    # Reported per arm and per seed either way, over the ladder's own two-arm inventory.
    for reduced in (none, every):
        assert set(reduced["arm_competent"]) == set(LADDER_ARMS)
        assert set(reduced["arm_seed_competence"]["FT-XF-BC"]) == set(B1_SEEDS)
    assert none["arm_competent"] == {arm: False for arm in LADDER_ARMS}
    assert every["arm_competent"] == {arm: True for arm in LADDER_ARMS}


def test_publication_does_not_read_the_competence_outcome(ladder, discriminator):
    """Nothing on either publication path branches on competence, regret or agreement."""
    for source in (inspect.getsource(ladder.run_rung_1), inspect.getsource(discriminator.run_result)):
        for token in ("competence", "competent", "max_regret", "tail_agreement", "falsifier", "conditioning_positive"):
            for line in source.splitlines():
                stripped = line.strip()
                if token in stripped and (stripped.startswith("if ") or stripped.startswith("elif ")):
                    raise AssertionError(f"publication branches on {token}: {stripped}")
    assert "exact_oracle_competence_predicate" in ladder.RECAST_LEDGER["recorded_not_gating"]
    assert "acquisition_and_count_raw_locks" in ladder.RECAST_LEDGER["recorded_not_gating"]


def test_the_launch_conditions_the_recast_keeps_are_declared(ladder):
    kept = ladder.RECAST_LEDGER["still_gating"]
    assert "central_4gib_memory_admission" in kept
    assert "section_4_integrity_items" in kept
    assert "section_5_2_nonzero_counts" in kept
    assert "machine_generated_exposure_line" in kept
    assert "section_6_2_learner_side_quarantine" in kept


# ---------------------------------------------------------------------------------------
# (iv) missing telemetry downgrades; it never quarantines
# ---------------------------------------------------------------------------------------


def test_missing_ladder_telemetry_downgrades_only(ladder):
    complete = ladder.resource_record(
        wall_seconds=1.0, cpu_seconds=1.0, peak_rss_bytes=2, scratch_bytes=3, durable_bytes=4,
    )
    assert complete["resources_unmeasured"] is False and complete["unmeasured_reasons"] == []
    partial = ladder.resource_record(
        wall_seconds=1.0, cpu_seconds=1.0, peak_rss_bytes=None, scratch_bytes=3, durable_bytes=None,
    )
    assert partial["resources_unmeasured"] is True
    assert partial["unmeasured_reasons"] == ["durable_bytes_missing", "peak_rss_bytes_missing"]
    assert partial["downgrade_only"] is True and partial["gating"] is False


def test_a_failing_rss_probe_is_recorded_and_the_run_is_not_stopped(ladder, monkeypatch, tmp_path):
    def broken():
        raise OSError("GetProcessMemoryInfo failed")

    monkeypatch.setattr(ladder, "_peak_working_set_bytes", broken)
    scratch = tmp_path / "scratch"
    durable = tmp_path / "durable"
    scratch.mkdir()
    durable.mkdir()
    record = ladder.measure_resources({"wall": 0.0, "cpu": 0.0}, scratch, durable)
    assert record["resources_unmeasured"] is True
    assert any(reason.startswith("peak_rss_unavailable") for reason in record["unmeasured_reasons"])
    assert record["wall_seconds"] is not None and record["scratch_bytes"] == 0


def test_discriminator_records_missing_telemetry_and_cap_exceedance(discriminator):
    caps = {"wall_seconds": 10.0, "cpu_seconds": 10.0, "process_tree_rss_bytes": 100, "scratch_bytes": 100,
            "durable_bytes": 100, "io_read_bytes": 100, "io_write_bytes": 100, "aggregate_io_bytes": 200,
            "thread_cap": 32, "process_cap": 1, "child_process_cap": 0}
    telemetry = {"wall_seconds": 1.0, "cpu_seconds": 1.0, "process_tree_peak_rss_bytes": 50,
                 "scratch_high_water_bytes": 10, "durable_high_water_bytes": 10, "io_read_bytes": 10,
                 "io_write_bytes": 10, "aggregate_io_bytes": 20, "thread_count_peak": 4,
                 "process_count_peak": 1, "child_process_count_peak": 0}
    ledger = discriminator.recast_resource_ledger(telemetry, caps, cap_source="assessment-02.json")
    assert ledger["within_caps"] is True and ledger["resources_unmeasured"] is False and ledger["gating"] is False
    # A measured exceedance is recorded, not raised.
    over = discriminator.recast_resource_ledger(dict(telemetry, wall_seconds=999.0), caps, cap_source="assessment-02.json")
    assert over["cap_exceedances"] == ["wall_seconds"] and over["within_caps"] is False
    # A missing measurement downgrades, and is not counted as an exceedance.
    missing = dict(telemetry)
    missing["process_tree_peak_rss_bytes"] = None
    downgraded = discriminator.recast_resource_ledger(missing, caps, cap_source="assessment-02.json")
    assert downgraded["resources_unmeasured"] is True
    assert downgraded["unmeasured_reasons"] == ["process_tree_peak_rss_bytes_missing"]
    assert downgraded["cap_exceedances"] == []


# ---------------------------------------------------------------------------------------
# (v) learner-side failure still quarantines (§6.2)
# ---------------------------------------------------------------------------------------


def test_learner_side_failure_still_quarantines_the_ladder(ladder, monkeypatch, tmp_path):
    monkeypatch.setattr(ladder, "admit_memory", lambda receipt: {"passed": True, "stub": True})

    def failing(*args, **kwargs):
        raise RuntimeError("learner-instrumentation-failure")

    monkeypatch.setattr(ladder, "run_workload", failing)
    output = tmp_path / "run"
    with pytest.raises(RuntimeError, match="learner-instrumentation-failure"):
        ladder.run_rung_1(output)
    assert not (output / "complete").exists()
    quarantines = list(output.glob("quarantine-*"))
    assert len(quarantines) == 1
    failure = json.loads((quarantines[0] / "failure.json").read_text(encoding="utf-8"))
    assert failure["quarantined"] is True
    assert failure["complete"] is False
    assert failure["quarantine_rule"] == "MARL_EMPIRICAL_EVIDENCE_SPEC.md#6.2"
    assert failure["error_type"] == "RuntimeError"
    assert (quarantines[0] / "work").is_dir()


def test_a_failed_memory_admission_still_refuses_the_ladder(ladder, monkeypatch, tmp_path):
    """The one launch condition §11.4 keeps must still stop the run."""
    def refuse(receipt):
        raise ladder.LaunchRefusal("central admission receipt does not establish both 4 GiB floors")

    monkeypatch.setattr(ladder, "admit_memory", refuse)
    output = tmp_path / "run"
    with pytest.raises(ladder.LaunchRefusal, match="4 GiB"):
        ladder.run_rung_1(output)
    assert not (output / "complete").exists()
