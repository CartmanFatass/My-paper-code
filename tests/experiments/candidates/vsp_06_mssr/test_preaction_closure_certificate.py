from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path

import pytest

from experiments.candidates.vsp_06_mssr import preaction_closure_certificate as cert


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "experiments/candidates/vsp_06_mssr/preaction_closure_certificate.py"
INDEX = ROOT / "docs/research/candidates/vsp_06_mssr/CODE_SCIENCE_INDEX.md"


def assert_failure(label: str, callback) -> None:
    with pytest.raises(cert.ContractFailure) as caught:
        callback()
    assert caught.value.label == label


def test_manifest_is_complete_nonoverlapping_and_explicit() -> None:
    manifest = cert.frozen_manifest()
    cert.validate_manifest(manifest)
    assert tuple(entry.name for entry in manifest.states) == ("S", "P", "F")
    assert [(entry.byte_offset, entry.byte_width) for entry in manifest.states] == [(0, 16), (16, 16), (32, 16)]
    assert {item.category for item in manifest.inventory} == set(cert.REQUIRED_INVENTORY_CATEGORIES)
    assert dict(manifest.descendant_closure)["P"] == (
        "P", "F", "partner_interaction_cell", "fast_control_cell", "fast_feature_cache"
    )
    assert {
        root: set(names) for root, names in manifest.descendant_closure
    } == cert.derive_descendant_closure(manifest)


def test_incomplete_and_overlapping_manifests_fail_closed() -> None:
    manifest = cert.frozen_manifest()
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_manifest(replace(manifest, states=manifest.states[:-1])))
    overlap = replace(manifest.states[1], byte_offset=8)
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_manifest(replace(manifest, states=(manifest.states[0], overlap, manifest.states[2]))))


def test_unknown_and_unlisted_p_descendants_fail_closed() -> None:
    manifest = cert.frozen_manifest()
    closures = dict(manifest.descendant_closure)
    closures["P"] = closures["P"] + ("unknown_p_cache",)
    assert_failure(
        "UNREGISTERED_PERSISTENT_DESCENDANT",
        lambda: cert.validate_manifest(replace(manifest, descendant_closure=tuple(closures.items()))),
    )
    shadow = cert.InventoryEntry("p_shadow", "caches", "unit.shadow", ("P",), True)
    assert_failure(
        "CONTRACT_NOT_CLOSED",
        lambda: cert.validate_manifest(replace(manifest, inventory=manifest.inventory + (shadow,))),
    )


def test_declared_closure_rejects_missing_f_and_extra_registered_non_descendant() -> None:
    manifest = cert.frozen_manifest()
    closures = dict(manifest.descendant_closure)
    closures["P"] = tuple(name for name in closures["P"] if name != "F")
    assert_failure(
        "CONTRACT_NOT_CLOSED",
        lambda: cert.validate_manifest(replace(manifest, descendant_closure=tuple(closures.items()))),
    )
    closures = dict(manifest.descendant_closure)
    closures["P"] = closures["P"] + ("input_normalizer",)
    assert_failure(
        "CONTRACT_NOT_CLOSED",
        lambda: cert.validate_manifest(replace(manifest, descendant_closure=tuple(closures.items()))),
    )


def test_declared_closure_rejects_duplicate_root() -> None:
    manifest = cert.frozen_manifest()
    duplicate = manifest.descendant_closure + (manifest.descendant_closure[1],)
    assert_failure(
        "CONTRACT_NOT_CLOSED",
        lambda: cert.validate_manifest(replace(manifest, descendant_closure=duplicate)),
    )


@pytest.mark.parametrize("mask", [(0, 0, 1), (1, 0, 0), (1, 0, 1), (1, 1, 0)])
def test_every_illegal_mask_fails_closed(mask: tuple[int, int, int]) -> None:
    assert_failure("ILLEGAL_VALIDITY_OR_MASK", lambda: cert.validate_mask(mask))


def test_all_and_only_legal_worlds_have_expected_content() -> None:
    history = {"S": F(7), "P": F(1), "F": F(3)}
    worlds = {name: cert.construct_world(mask, history, cert.default_initializers()) for name, mask in cert.LEGAL_MASKS.items()}
    assert worlds == {
        "SAME": {"S": F(7), "P": F(1), "F": F(3)},
        "CHANGE_F": {"S": F(7), "P": F(1), "F": F(0)},
        "CHANGE_P": {"S": F(7), "P": F(0), "F": F(0)},
        "CHANGE_S": {"S": F(2), "P": F(0), "F": F(0)},
    }
    assert worlds["CHANGE_P"] != worlds["CHANGE_S"]


def test_initializers_are_current_free_and_n_s_is_frozen_only() -> None:
    cert.validate_initializers(cert.default_initializers())
    bad_p = (cert.Initializer("S", ("frozen_schema_constant",), F(2)), cert.Initializer("P", ("current_partner",), F(0)), cert.Initializer("F", (), F(0)))
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_initializers(bad_p))
    bad_s = (cert.Initializer("S", ("current_roster",), F(2)), cert.Initializer("P", (), F(0)), cert.Initializer("F", (), F(0)))
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_initializers(bad_s))


def test_current_rebuild_reads_exact_full_current_context_only() -> None:
    pair = cert.registered_pair()
    assert cert.rebuild_p(pair.x0, cert.CurrentRebuild(cert.CURRENT_FIELDS)) == 0
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.rebuild_p(pair.x0, cert.CurrentRebuild(("x0_self",))))
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.rebuild_p(pair.x0, cert.CurrentRebuild(cert.CURRENT_FIELDS, ("history_P",))))


def test_registered_pair_has_exact_context_positive_support_and_frozen_non_targets() -> None:
    pair = cert.registered_pair()
    cert.validate_pair(pair)
    assert [arm.historical_p for arm in pair.arms] == [F(-1), F(1)]
    assert [arm.support_weight for arm in pair.arms] == [F(1, 2), F(1, 2)]
    assert len({arm.provenance for arm in pair.arms}) == 1
    assert len({(arm.environment, arm.rng, arm.non_target_state) for arm in pair.arms}) == 1


def test_missing_zero_support_or_duplicate_p_pair_fails_closed() -> None:
    pair = cert.registered_pair()
    zero = replace(pair.arms[0], support_weight=F(0))
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_pair(replace(pair, arms=(zero, pair.arms[1]))))
    duplicate = replace(pair.arms[1], historical_p=pair.arms[0].historical_p)
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_pair(replace(pair, arms=(pair.arms[0], duplicate))))


def test_non_target_drift_and_metadata_arm_side_channels_fail_closed() -> None:
    pair = cert.registered_pair()
    drift = replace(pair.arms[1], non_target_state=(F(3), F(6)))
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_pair(replace(pair, arms=(pair.arms[0], drift))))
    leak = replace(pair.arms[1], side_channel_reads=("arm_label",))
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_pair(replace(pair, arms=(pair.arms[0], leak))))


def test_action_must_precede_recurrence_and_d0_must_not_update() -> None:
    cert.validate_trace(cert.EvaluationTrace(0, 1))
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_trace(cert.EvaluationTrace(1, 1)))
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_trace(cert.EvaluationTrace(0, 1, state_updates=1)))
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_trace(cert.EvaluationTrace(0, 1, model_updates=1)))
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_trace(cert.EvaluationTrace(0, 1, optimizer_updates=1)))
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_trace(cert.EvaluationTrace(0, 1, rng_after=(17, 24))))
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.validate_trace(cert.EvaluationTrace(0, 1, non_target_drift=(F(0), F(1)))))


def test_synthetic_preaction_residual_is_exact_and_probability_witness_matches() -> None:
    pair = cert.registered_pair()
    rebuild = cert.CurrentRebuild(cert.CURRENT_FIELDS)
    reports = [cert.evaluate_arm(arm, pair.x0, F(1), cert.EvaluationTrace(0, 1), rebuild) for arm in pair.arms]
    assert [row["delta_kb"] for row in reports] == [["1/2", "-1/2"], ["-1/2", "1/2"]]
    assert [row["keep_logits"] for row in reports] == [["7/8", "-1/8"], ["-1/8", "7/8"]]
    assert [row["rebuild_logits"] for row in reports] == [["3/8", "3/8"], ["3/8", "3/8"]]
    assert reports[0]["keep_action1_probability"] == pytest.approx(1 / (1 + 2.718281828459045))
    assert reports[1]["keep_action1_probability"] == pytest.approx(1 / (1 + 2.718281828459045 ** -1))
    for row in reports:
        logits = [F(value) for value in row["keep_logits"]]
        derived = 1 / (1 + math.exp(float(logits[0] - logits[1])))
        assert row["keep_action1_probability"] == pytest.approx(derived)
    assert all(row["rebuild_action1_probability"] == 0.5 for row in reports)
    assert cert.residual_output(reports) == "P_PREACTION_RESIDUAL_PATH_EXISTS"


def test_centered_policy_null_is_reported_exactly() -> None:
    pair = cert.registered_pair()
    reports = [
        cert.evaluate_arm(arm, pair.x0, F(0), cert.EvaluationTrace(0, 1), cert.CurrentRebuild(cert.CURRENT_FIELDS))
        for arm in pair.arms
    ]
    assert cert.residual_output(reports) == "P_PREACTION_PATH_NULL"
    assert all(row["policy_equivalent"] is True for row in reports)


def test_gate_truth_table_is_honestly_exactly_factorized() -> None:
    census = cert.gate_census()
    assert census["output"] == "GATE_EXACTLY_FACTORIZED"
    assert census["rows"] == {
        "SAME": {"mask": [1, 1, 1], "g_mssr": [1, 1, 1], "g_fact": [1, 1, 1]},
        "CHANGE_F": {"mask": [0, 1, 1], "g_mssr": [0, 1, 1], "g_fact": [0, 1, 1]},
        "CHANGE_P": {"mask": [0, 1, 0], "g_mssr": [0, 1, 0], "g_fact": [0, 1, 0]},
        "CHANGE_S": {"mask": [0, 0, 0], "g_mssr": [0, 0, 0], "g_fact": [0, 0, 0]},
    }


def test_primary_change_f_unreachable_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cert, "LEGAL_MASKS", {name: mask for name, mask in cert.LEGAL_MASKS.items() if name != "CHANGE_F"})
    assert_failure("CONTRACT_NOT_CLOSED", cert.build_report)


def test_bounded_active_production_probes_report_contract_not_closed() -> None:
    report = cert.active_binding_report(ROOT)
    assert report["output"] == "CONTRACT_NOT_CLOSED"
    assert report["no_direct_binding_in_inspected_surfaces"] is True
    assert [row["fact"] for row in report["inspection_scope"]] == [
        "ordinary_hidden_state", "recurrence_precedes_action_distribution", "recurrence_precedes_action_distribution"
    ]
    assert report["scope_limit"] == "bounded active-surface probes, not exhaustive repository absence"


def test_active_probe_drifts_fail_closed(tmp_path: Path) -> None:
    for relative, first, second in cert.PRODUCTION_PROBES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(first + "\n" + (second or "") + "\n", encoding="utf-8")
    target = tmp_path / cert.PRODUCTION_PROBES[1][0]
    target.write_text(cert.PRODUCTION_PROBES[1][2] + "\n" + cert.PRODUCTION_PROBES[1][1], encoding="utf-8")
    assert_failure("CONTRACT_NOT_CLOSED", lambda: cert.active_binding_report(tmp_path))


def test_report_keeps_unit_mechanics_separate_from_active_terminal() -> None:
    report = cert.build_report(ROOT)
    assert report["synthetic_unit"]["output"] == "P_PREACTION_RESIDUAL_PATH_EXISTS"
    assert report["synthetic_unit"]["gate"]["output"] == "GATE_EXACTLY_FACTORIZED"
    assert report["active_binding"]["output"] == "CONTRACT_NOT_CLOSED"
    assert report["terminal"] == "CONTRACT_NOT_CLOSED"
    assert report["outputs"] == ["P_PREACTION_RESIDUAL_PATH_EXISTS", "GATE_EXACTLY_FACTORIZED", "CONTRACT_NOT_CLOSED"]
    assert report["complexity"] == {"legal_masks": 4, "supported_arms": 2, "hypothetical_transitions": 0, "training": False}
    assert report["synthetic_unit"]["no_state_model_optimizer_rng_update"] is True


def run_cli() -> str:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-B", str(SOURCE)], cwd=ROOT, env=env, check=True,
        capture_output=True, text=True, timeout=30,
    ).stdout.strip()


def test_cli_is_stable_compact_json() -> None:
    first, second = run_cli(), run_cli()
    assert first == second
    expected = json.loads(json.dumps(cert.build_report(ROOT), sort_keys=True))
    assert json.loads(first) == expected
    assert "\n" not in first


def test_index_binds_exact_cli_output_and_claim_boundary() -> None:
    raw = run_cli()
    index = INDEX.read_text(encoding="utf-8")
    assert f"```json\n{raw}\n```" in index
    assert str(SOURCE.relative_to(ROOT)).replace("\\", "/") in index
    assert str(Path(__file__).relative_to(ROOT)).replace("\\", "/") in index
    assert "unit-fixture possibility" in index
    assert "bounded active-surface" in index
    for prohibited in ("task value", "semantic memory", "partner transport", "training benefit", "return", "deployment"):
        assert prohibited in index


def test_source_is_small_and_has_no_production_import_or_training_path() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    active = [line for line in lines if line.strip() and not line.lstrip().startswith("#")]
    assert len(active) <= 500
    text = "\n".join(lines)
    assert "import torch" not in text
    assert "ha_ctse_process" in text  # fixed source probes only
    assert "train(" not in text
