"""The repaired per-decision relabel probe (owner decision F.4(a), 2026-09-03).

Two things are checked here.

1. The diagnostic that produced the decision reproduces: on untrained
   checkpoints over 12 `(N, failed-zone)` cells x 8 worlds x 2 arms = 192
   world-decisions per law, presentation dependence of the inverse-mapped
   physical command is 15/192 under the R01 law and 0/192 under the R02 canonical
   opaque-rank sort, while the batch-position residual is 12/192 under both.
2. The repaired probe -- presentation only, both sides batch 1, same batch
   position -- passes under the R02 law and fails under the R01 law, whereas the
   old conflated probe refuses the R02 law.

These touch the real native host and real fixtures but train nothing, create no
checkpoint, optimizer, endpoint or artifact, and assert no algorithm effect.
"""
from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest
import torch

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

DIAGNOSTIC_TOTALS = {
    "R01_plain": {"batch8_vs_batch1": 12, "presentation_1_vs_1": 15, "runner_probe_8_vs_1": 8},
    "R02_canonical_opaque_rank_sort": {"batch8_vs_batch1": 12, "presentation_1_vs_1": 0, "runner_probe_8_vs_1": 12},
}
WORLD_DECISIONS_PER_LAW = 96  # 6 (N, failed-zone) cells x 8 worlds x 2 arms, per law


@pytest.fixture(scope="module")
def r02():
    path = REPOSITORY_ROOT / "scripts" / "run_vnfc_bpcr_r02.py"
    spec = importlib.util.spec_from_file_location("vnfc_r02_probe_under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["vnfc_r02_probe_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe_panel(r02):
    """One decision panel per cell, with both laws' models on the same states.

    Restores every R01 module global it rebinds, so installing nothing leaks into
    the rest of the session.
    """
    r02.prepare_native_backends()
    r01 = r02.load_r01_runner()
    saved = {name: getattr(r01, name) for name in ("RUN_REVISION", "RUN_NAMESPACE", "DEBUG_SEED")}
    torch.set_num_threads(1)
    try:
        plain = {"MAPR": r01.MAPR4, "DIRECT": r01.DirectSetAR}
        canonical_mapr, canonical_direct = r02.build_canonical_model_classes(r01)
        canonical = {"MAPR": canonical_mapr, "DIRECT": canonical_direct}
        r01.RUN_REVISION = r01.RUN_NAMESPACE = r02.RUN_REVISION
        r01.DEBUG_SEED = r02.DEBUG_SEED
        config = r01.BExploreRunConfig("B0-DEBUG", r02.DEBUG_SEED, 8)
        now = datetime.now(timezone.utc)
        rng = r01._SeedRNG(r01.derive_seed_master(config)["master"])
        learners = r01._initialize_learners(config, rng, now)
        from experiments.candidates.variable_n_fleet_churn_bpcr_r09.empirical_training import _model_inputs
        from experiments.candidates.variable_n_fleet_churn_b_explore import PairedPrimaryShadowBatch

        cells = []
        for roster in (3, 5, 7):
            for zone in (1, 2):
                purpose = "heldout-N7" if roster == 7 else "evaluation-train-support"
                group = tuple(
                    r01._build_world(rng, config, purpose=purpose, roster_size=roster,
                                     failed_zone=zone, row=row, now=now)
                    for row in range(8)
                )
                with PairedPrimaryShadowBatch(group) as batch:
                    observations = tuple(row["next_observation"] for row in batch.initial)
                    failed = tuple(row["failed_rank"] for row in batch.initial)
                    inputs = [_model_inputs(observation, fixture, failed_rank)
                              for observation, fixture, failed_rank in zip(observations, group, failed)]
                stacked = tuple(torch.cat([row[index] for row in inputs], 0) for index in range(6))
                # the fresh relabel is address-derived, so it depends on the arm but
                # not on the law; both laws see the same permutation for a given arm
                permutations = {
                    arm: [
                        r01._fresh_relabel_permutation(rng, config, arm, "final", group[index], index, 0, now)
                        for index in range(8)
                    ]
                    for arm in ("MAPR", "DIRECT")
                }
                cells.append({"roster_size": roster, "failed_zone": zone, "fixtures": group,
                              "inputs": inputs, "stacked": stacked, "permutations": permutations})

        def build(law_table, arm):
            source = learners["models"][arm]
            parameters = {
                name.replace("parameters_by_name.", "").replace("__", "."): value.clone()
                for name, value in source.state_dict().items()
            }
            return law_table[arm](parameters)

        models = {
            ("R01_plain", arm): build(plain, arm) for arm in ("MAPR", "DIRECT")
        }
        models.update({
            ("R02_canonical_opaque_rank_sort", arm): build(canonical, arm) for arm in ("MAPR", "DIRECT")
        })
        return {"cells": cells, "models": models, "r01": r01}
    finally:
        for name, value in saved.items():
            setattr(r01, name, value)


def _measure(panel, law):
    """Return the three counts for one law, over all cells and both arms."""
    totals = {"batch8_vs_batch1": 0, "presentation_1_vs_1": 0, "runner_probe_8_vs_1": 0, "decisions": 0}
    for arm in ("MAPR", "DIRECT"):
        model = panel["models"][(law, arm)]
        for cell in panel["cells"]:
            with torch.no_grad():
                batched = model(*cell["stacked"])["command"]
            for index, item in enumerate(cell["inputs"]):
                permutation = cell["permutations"][arm][index]
                with torch.no_grad():
                    identity = model(*item)["command"][0]
                    permuted = model(*panel["r01"]._permuted_inputs(item, permutation))["command"][0]
                mapped = tuple(
                    len(permutation) if int(choice) == len(permutation) else permutation[int(choice)]
                    for choice in permuted
                )
                reference = tuple(int(choice) for choice in identity)
                batched_row = tuple(int(choice) for choice in batched[index])
                totals["batch8_vs_batch1"] += int(batched_row != reference)
                totals["presentation_1_vs_1"] += int(reference != mapped)
                totals["runner_probe_8_vs_1"] += int(batched_row != mapped)
                totals["decisions"] += 1
    return totals


@pytest.fixture(scope="module")
def measured(probe_panel):
    return {law: _measure(probe_panel, law) for law in DIAGNOSTIC_TOTALS}


@pytest.mark.parametrize("law", sorted(DIAGNOSTIC_TOTALS))
def test_diagnostic_totals_reproduce(measured, law):
    observed = measured[law]
    assert observed["decisions"] == WORLD_DECISIONS_PER_LAW
    for key, expected in DIAGNOSTIC_TOTALS[law].items():
        assert observed[key] == expected, (law, key, observed[key], expected)


def test_batch_residual_is_identical_under_both_laws(measured):
    """The residual is a property of the arithmetic, not of the presentation law."""
    left = measured["R01_plain"]["batch8_vs_batch1"]
    right = measured["R02_canonical_opaque_rank_sort"]["batch8_vs_batch1"]
    assert left == right == 12


def test_repaired_probe_passes_the_r02_law_and_fails_the_r01_law(measured):
    """The gating comparison: presentation only, both sides batch 1."""
    assert measured["R02_canonical_opaque_rank_sort"]["presentation_1_vs_1"] == 0
    assert measured["R01_plain"]["presentation_1_vs_1"] > 0


def test_old_conflated_probe_refuses_the_r02_law(measured):
    """Why the repair was needed, recorded as a direct observation.

    The old probe compares a batch-8 forward against a batch-1 relabelled one, so
    it refuses the R02 law (12 > 0) even though that law's presentation dependence
    is exactly zero, and it under-reports real presentation failure under the R01
    law (8 < 15) because its two error sources partially cancel.
    """
    assert measured["R02_canonical_opaque_rank_sort"]["runner_probe_8_vs_1"] > 0
    assert measured["R01_plain"]["runner_probe_8_vs_1"] < measured["R01_plain"]["presentation_1_vs_1"]


# ---------------------------------------------------------------------------
# the installed probe: exposure accounting and the descriptive residual record
# ---------------------------------------------------------------------------

def test_repaired_probe_exposure_budget(r02):
    assert r02.FROZEN_DIAGNOSTIC_FORWARDS == {"MAPR": 48, "DIRECT": 60}
    assert r02.R02_DIAGNOSTIC_FORWARDS == {"MAPR": 96, "DIRECT": 108}
    # two batch-1 forwards per decision, 6 boundaries x 8 worlds, plus the
    # unchanged 12 DIRECT residual-ablation forwards
    assert r02.R02_DIAGNOSTIC_FORWARDS["MAPR"] == 2 * 6 * 8
    assert r02.R02_DIAGNOSTIC_FORWARDS["DIRECT"] == 2 * 6 * 8 + 12


def test_batch_residual_record_is_descriptive_only(r02):
    sink = [
        {"cell": "N7z1", "checkpoint": "final", "arm": "MAPR", "boundary": 0,
         "world_row": 0, "batch_position_command_differs": True},
        {"cell": "N7z1", "checkpoint": "final", "arm": "MAPR", "boundary": 0,
         "world_row": 1, "batch_position_command_differs": False},
        {"cell": "N3z1", "checkpoint": "final", "arm": "DIRECT", "boundary": 1,
         "world_row": 2, "batch_position_command_differs": True},
    ]
    record = r02.batch_residual_record(sink)
    assert record["gating"] is False
    assert record["decisions"] == 3
    assert record["differing_decisions"] == 2
    assert record["differing_by_cell"] == {"N3z1": 1, "N7z1": 1}
    assert record["probe_law"] == r02.RELABEL_PROBE_LAW
    assert "not a presentation quantity" in record["recorded_only_reason"]


def test_empty_residual_record_is_valid(r02):
    record = r02.batch_residual_record([])
    assert record["decisions"] == 0 and record["differing_decisions"] == 0
    assert record["gating"] is False


def test_recast_record_names_the_repaired_probe(r02):
    record = r02.r02_recast_record()
    assert record["relabel_probe_law"] == "VNFC-R02-RELABEL-LIKE-FOR-LIKE-V1"
    assert "F.4" in record["relabel_probe_decision"]
    assert any("like-for-like" in row for row in record["still_gating"])


def test_installed_probe_replaces_the_r01_comparison(r02):
    """`install_like_for_like_relabel_probe` swaps the function and the validator."""
    r01 = r02.load_r01_runner()
    saved = {
        "_evaluate_learned_batch": r01._evaluate_learned_batch,
        "_validate_runtime_payload_cross_consistency": r01._validate_runtime_payload_cross_consistency,
    }
    installed = getattr(r01, "_r02_relabel_probe_installed", False)
    try:
        r01._r02_relabel_probe_installed = False
        sink: list[dict[str, object]] = []
        r02.install_like_for_like_relabel_probe(r01, sink)
        assert r01._evaluate_learned_batch is not saved["_evaluate_learned_batch"]
        assert r01._validate_runtime_payload_cross_consistency is not saved[
            "_validate_runtime_payload_cross_consistency"
        ]
        assert r01._r02_relabel_probe_law == "VNFC-R02-RELABEL-LIKE-FOR-LIKE-V1"

        terminal = {"evaluation": {"learned": ({"arm": "MAPR", "diagnostic_forward_calls": 48,
                                                "relabel_mismatch_count": 0},)}}
        with pytest.raises(r01.BExploreContractError) as raised:
            r01._validate_runtime_payload_cross_consistency(None, terminal)
        assert "R02 like-for-like relabel probe exposure differs" == str(raised.value)

        terminal = {"evaluation": {"learned": ({"arm": "MAPR", "diagnostic_forward_calls": 96,
                                                "relabel_mismatch_count": 1},)}}
        with pytest.raises(r01.BExploreContractError) as raised:
            r01._validate_runtime_payload_cross_consistency(None, terminal)
        assert "R02 like-for-like relabel probe presentation mismatch" == str(raised.value)
    finally:
        for name, value in saved.items():
            setattr(r01, name, value)
        r01._r02_relabel_probe_installed = installed
        if hasattr(r01, "_r01_validate_runtime_payload_cross_consistency"):
            delattr(r01, "_r01_validate_runtime_payload_cross_consistency")


def test_installed_validator_checks_the_aggregate_exposure(r02):
    """The frozen 48/60 constant appears twice; both are covered.

    `run_vnfc_bpcr_b_explore.py:852` pins it per learned row and `:975` pins the
    aggregate `terminal["exposure"]`.  The wrapper asserts the true R02 budget in
    both places.
    """
    r01 = r02.load_r01_runner()
    saved = {
        "_evaluate_learned_batch": r01._evaluate_learned_batch,
        "_validate_runtime_payload_cross_consistency": r01._validate_runtime_payload_cross_consistency,
    }
    installed = getattr(r01, "_r02_relabel_probe_installed", False)
    try:
        r01._r02_relabel_probe_installed = False
        r02.install_like_for_like_relabel_probe(r01, [])
        learned = tuple(
            {"arm": arm, "diagnostic_forward_calls": r02.R02_DIAGNOSTIC_FORWARDS[arm],
             "relabel_mismatch_count": 0}
            for arm in ("MAPR", "DIRECT")
        )
        terminal = {
            "evaluation": {"learned": learned},
            "exposure": {"evaluation": {
                "MAPR": {"policy_forward_calls": 6, "diagnostic_forward_calls": 48},
                "DIRECT": {"policy_forward_calls": 6, "diagnostic_forward_calls": 108},
                "BCRH": {"policy_forward_calls": 0, "diagnostic_forward_calls": 0},
            }},
        }
        with pytest.raises(r01.BExploreContractError) as raised:
            r01._validate_runtime_payload_cross_consistency(None, terminal)
        assert "R02 like-for-like relabel probe aggregate exposure differs" == str(raised.value)
    finally:
        for name, value in saved.items():
            setattr(r01, name, value)
        r01._r02_relabel_probe_installed = installed
        if hasattr(r01, "_r01_validate_runtime_payload_cross_consistency"):
            delattr(r01, "_r01_validate_runtime_payload_cross_consistency")


def test_r01_runner_source_is_untouched():
    """The repair is installed from the R02 runner; R01 stays read-only substrate."""
    source = (REPOSITORY_ROOT / "scripts" / "run_vnfc_bpcr_b_explore.py").read_text("utf-8")
    assert "RELABEL_PROBE_LAW" not in source
    assert "batch_position_command_differs" not in source
    # the R01 comparison the repair replaces is still present in the R01 source
    assert 'mismatch += int(tuple(int(choice) for choice in output["command"][index]) != mapped)' in source
