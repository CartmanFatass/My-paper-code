from __future__ import annotations

import json
from pathlib import Path

import pytest
import numpy as np

import scripts.run_access_positive_ehc_g1 as runner

from scripts.run_access_positive_ehc_g1 import (
    ARMS,
    BOOTSTRAP_REPETITIONS,
    EVALUATION_EPISODES,
    EVALUATION_PROFILES,
    FORMAL_AUTHORIZATION_TOKEN,
    FORMAL_BUDGET,
    REPLICATES,
    SEED_REGISTRY,
    _compact_analysis_statistics,
    _manifest,
    _predicate_inputs_from_evidence,
    _require_analysis_binding,
    _source_control_summary,
    _validate_source_controls,
    _write_and_validate_analysis,
    hierarchical_bootstrap,
    select_result_branch,
    train,
    validate_formal_result,
    validate_relative_reference,
)


def _passing_predicates() -> dict[str, object]:
    return {
        "operational_valid": True,
        "source_identifiable": True,
        "max_arm_lcb": 0.86,
        "max_arm_ucb": 0.90,
        "g_dum_lcb": 0.14,
        "g_dum_ucb": 0.18,
        "g_or_lcb": 0.13,
        "g_or_ucb": 0.17,
        "k_lcbs": (0.12, 0.13, 0.05),
        "k_ucbs": (0.15, 0.16, 0.09),
        "i_tv_lcb": 0.12,
        "i_tv_ucb": 0.16,
        "c_keep_lcb": 0.01,
        "c_keep_ucb": 0.05,
        "c_renew_lcb": 0.01,
        "c_renew_ucb": 0.05,
        "c_keep_mean": 0.03,
        "c_renew_mean": 0.03,
    }


def test_exact_frozen_registries_and_formal_token_are_independent_g1():
    assert ARMS == ("OR", "DUM", "EHC")
    assert REPLICATES == tuple(range(5))
    assert EVALUATION_PROFILES == (
        "iid_deterministic",
        "iid_stochastic",
        "heldout_deterministic",
        "heldout_stochastic",
    )
    assert EVALUATION_EPISODES == 256
    assert BOOTSTRAP_REPETITIONS == 10_000
    assert FORMAL_BUDGET == {
        "environments": 16,
        "horizon": 80,
        "updates": 250,
        "episodes_per_arm": 4_000,
        "transitions_per_arm": 320_000,
        "base_optimizer_steps": 1_000,
        "event_optimizer_steps": {"OR": 0, "DUM": 1_000, "EHC": 1_000},
        "ppo_passes": 4,
        "evaluation_episodes_per_cell": 256,
        "bootstrap_repetitions": 10_000,
    }
    assert SEED_REGISTRY == {
        "model": 158058,
        "train_task": 168058,
        "train_membership": 169058,
        "train_duty": 170058,
        "train_opportunity": 171058,
        "train_event": 172058,
        "train_mark": 173058,
        "train_primitive": 174058,
        "evaluation_task": 198058,
        "evaluation_membership": 199058,
        "evaluation_duty": 200058,
        "evaluation_opportunity": 201058,
        "evaluation_event": 202058,
        "evaluation_mark": 203058,
        "evaluation_primitive": 204058,
        "audit": 206058,
        "bootstrap": 208058,
        "replicate_offset": 1_000,
    }
    assert "G1" in FORMAL_AUTHORIZATION_TOKEN
    assert "G0" not in FORMAL_AUTHORIZATION_TOKEN


def test_first_match_selector_preserves_exact_precedence_and_point_floor_rule():
    predicates = _passing_predicates()
    assert select_result_branch(**predicates) == "COMMITMENT_SUPPORTED_G1"

    cases = (
        ({"operational_valid": False}, "INVALID_OPERATIONAL_G1"),
        ({"source_identifiable": False}, "SOURCE_NON_IDENTIFIABLE_G1"),
        ({"max_arm_lcb": 0.70, "max_arm_ucb": 0.79}, "NO_ACCESS_THIS_G1_SOURCE"),
        ({"max_arm_lcb": 0.79, "max_arm_ucb": 0.80}, "UNDERPOWERED_ACCESS_G1"),
        ({"i_tv_lcb": 0.09, "i_tv_ucb": 0.10}, "REPRESENTATION_ONLY_G1"),
        ({"g_dum_lcb": 0.09, "g_dum_ucb": 0.10}, "ORDINARY_EXPLANATION_G1"),
        ({"g_dum_lcb": 0.09, "g_dum_ucb": 0.11}, "MIXED_UNDERPOWERED_G1"),
    )
    for changes, expected in cases:
        candidate = predicates | changes
        assert select_result_branch(**candidate) == expected

    point_only = predicates | {"c_keep_mean": 0.019}
    assert select_result_branch(**point_only) == "MIXED_UNDERPOWERED_G1"

    uncertain_interval = predicates | {"i_tv_lcb": 0.09, "i_tv_ucb": 0.11}
    assert select_result_branch(**uncertain_interval) == "MIXED_UNDERPOWERED_G1"

    invalid_and_no_access = predicates | {
        "operational_valid": False,
        "max_arm_lcb": 0.2,
        "max_arm_ucb": 0.3,
    }
    assert select_result_branch(**invalid_and_no_access) == "INVALID_OPERATIONAL_G1"
    malformed = predicates | {"g_dum_lcb": float("nan")}
    assert select_result_branch(**malformed) == "INVALID_OPERATIONAL_G1"


def test_formal_train_requires_exact_token_before_writing(tmp_path: Path):
    with pytest.raises(PermissionError, match="authorization token"):
        train(
            run_dir=tmp_path / "must_not_exist",
            formal=True,
            authorization_token="wrong",
            source_commit="a" * 40,
        )
    assert not (tmp_path / "must_not_exist").exists()


def test_hierarchical_bootstrap_retains_paired_signs_arms_profiles_and_rows():
    rows: list[dict[str, object]] = []
    for replicate in REPLICATES:
        for base_id in range(4):
            for sign_mate in (-1, 1):
                for arm in ARMS:
                    rows.append(
                        {
                            "replicate": replicate,
                            "base_id": base_id,
                            "sign_mate": sign_mate,
                            "arm": arm,
                            "profile": "heldout_stochastic",
                            "utility": float(replicate + base_id / 10),
                            "row_kind": "episode",
                        }
                    )
    samples = hierarchical_bootstrap(
        rows,
        repetitions=7,
        base_ids_per_replicate=4,
        seed=SEED_REGISTRY["bootstrap"],
    )
    assert len(samples) == 7
    for sample in samples:
        assert len(sample) == 5 * 4 * 2 * 3
        clusters: dict[tuple[int, int], list[dict[str, object]]] = {}
        for row in sample:
            clusters.setdefault(
                (int(row["bootstrap_replicate_draw"]), int(row["bootstrap_base_draw"])),
                [],
            ).append(row)
        assert len(clusters) == 20
        for cluster in clusters.values():
            assert {row["sign_mate"] for row in cluster} == {-1, 1}
            assert {row["arm"] for row in cluster} == set(ARMS)


@pytest.mark.parametrize(
    "reference",
    ("../escape.json", "/absolute.json", "C:/absolute.json", "a\\b.json", ""),
)
def test_reference_validation_fails_closed(reference: str):
    with pytest.raises(ValueError):
        validate_relative_reference(reference)


def test_formal_validator_rejects_nonformal_and_malformed_inventory(tmp_path: Path):
    exercise = tmp_path / "exercise"
    exercise.mkdir()
    (exercise / "analysis_result.json").write_text(
        json.dumps(
            {
                "schema": "access_positive_mechanism_matched_ehc_g1_analysis_v1",
                "source_family": "ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1",
                "formal": False,
                "result": "INVALID_OPERATIONAL_G1",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="formal=true"):
        validate_formal_result(exercise)

    malformed = tmp_path / "malformed"
    malformed.mkdir()
    source_commit = "a" * 40
    (malformed / "manifest.json").write_text(
        json.dumps(_manifest(formal=True, source_commit=source_commit, budget=FORMAL_BUDGET)),
        encoding="utf-8",
    )
    (malformed / "analysis_result.json").write_text(
        json.dumps(
            {
                "schema": "access_positive_mechanism_matched_ehc_g1_analysis_v1",
                "source_family": "ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1",
                "formal": True,
                "backend": "cpu",
                "torch_threads": 1,
                "source_commit": source_commit,
                "result": "COMMITMENT_SUPPORTED_G1",
                "authorization_token": FORMAL_AUTHORIZATION_TOKEN,
                "seed_registry": SEED_REGISTRY,
                "budget": FORMAL_BUDGET,
                "checkpoint_references": [],
                "evaluation_references": [],
                "source_control_reference": "source_controls.json",
                "audit_reference": "causal_audit.jsonl",
                "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="checkpoint inventory"):
        validate_formal_result(malformed)


def test_canonical_formal_manifest_is_exact_and_has_no_extra_authority_fields():
    source_commit = "b" * 40
    manifest = _manifest(
        formal=True, source_commit=source_commit, budget=FORMAL_BUDGET
    )
    assert manifest == {
        "schema": "access_positive_mechanism_matched_ehc_g1_manifest_v1",
        "source_family": "ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1",
        "formal": True,
        "backend": "cpu",
        "torch_threads": 1,
        "source_commit": source_commit,
        "authorization_token": FORMAL_AUTHORIZATION_TOKEN,
        "arms": list(ARMS),
        "replicates": list(REPLICATES),
        "evaluation_profiles": list(EVALUATION_PROFILES),
        "seed_registry": SEED_REGISTRY,
        "budget": FORMAL_BUDGET,
    }


def test_source_control_summaries_are_recomputed_from_cluster_evidence():
    values = np.asarray([[[0.8, 0.9], [0.7, 1.0]]], dtype=np.float64)
    summary = _source_control_summary(values, repetitions=8, seed=208058)
    controls = {
        "schema": "access_positive_mechanism_matched_ehc_g1_controls_v1",
        "source_family": "ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1",
        "formal": False,
        "source_commit": "NONFORMAL_EXERCISE",
        "profiles": list(EVALUATION_PROFILES),
        "replicates": [0],
        "base_ids": [0, 1],
        "sign_mates": [-1, 1],
        "bootstrap_repetitions": 8,
        "rows": [],
    }
    for profile_index, profile in enumerate(EVALUATION_PROFILES):
        for controller_index, controller in enumerate(("oracle", "history_free")):
            row_summary = _source_control_summary(
                values,
                repetitions=8,
                seed=SEED_REGISTRY["bootstrap"] + profile_index * 10 + controller_index,
            )
            controls["rows"].append(
                {"profile": profile, "controller": controller, **row_summary}
            )
    assert summary["mean"] == pytest.approx(0.85)
    _validate_source_controls(
        controls, formal=False, source_commit="NONFORMAL_EXERCISE"
    )
    controls["rows"][0]["mean"] += 0.01
    with pytest.raises(ValueError, match="not derived"):
        _validate_source_controls(
            controls, formal=False, source_commit="NONFORMAL_EXERCISE"
        )


def test_analysis_binding_rejects_serialized_metric_or_predicate_drift():
    metrics = {
        "max_arm": {"lcb95": 0.8, "ucb95": 0.9},
        "g_dum": {"lcb95": 0.11, "ucb95": 0.2},
        "g_or": {"lcb95": 0.12, "ucb95": 0.2},
        "k_bins": [
            {"lcb95": 0.11, "ucb95": 0.2},
            {"lcb95": 0.12, "ucb95": 0.2},
            {"lcb95": 0.05, "ucb95": 0.09},
        ],
        "i_tv": {"lcb95": 0.11, "ucb95": 0.2},
        "c_keep": {"mean": 0.02, "lcb95": 0.01, "ucb95": 0.03},
        "c_renew": {"mean": 0.02, "lcb95": 0.01, "ucb95": 0.03},
    }
    predicates = _predicate_inputs_from_evidence(
        metrics, operational_errors=[], source_identifiable=True
    )
    result = {
        "metrics": metrics,
        "predicate_inputs": predicates,
        "operational_errors": [],
    }
    _require_analysis_binding(
        result, metrics=metrics, predicate_inputs=predicates, operational_errors=[]
    )
    result["predicate_inputs"] = dict(predicates, c_keep_mean=0.03)
    with pytest.raises(ValueError, match="predicate_inputs"):
        _require_analysis_binding(
            result, metrics=metrics, predicate_inputs=predicates, operational_errors=[]
        )


def test_c_total_point_mean_uses_observed_rows_not_bootstrap_average():
    episode_rows: list[dict[str, object]] = []
    for base_id in range(2):
        for sign_mate in (-1, 1):
            for arm in ARMS:
                for profile in EVALUATION_PROFILES:
                    episode_rows.append(
                        {
                            "replicate": 0,
                            "base_id": base_id,
                            "sign_mate": sign_mate,
                            "arm": arm,
                            "profile": profile,
                            "utility": 0.5,
                            "spell_k1": 1,
                            "spell_k2": 1,
                            "spell_k3_plus": 1,
                            "non_create_opportunities": 3,
                            "lifecycles_with_two_plus": 1,
                        }
                    )
    audit_rows = [
        {"replicate": 0, "base_id": 0, "action": "KEEP", "i_tv": 0.2, "c_total": 1.0},
        {"replicate": 0, "base_id": 0, "action": "RENEW", "i_tv": 0.2, "c_total": 0.25},
    ]
    metrics = _compact_analysis_statistics(episode_rows, audit_rows, formal=False)
    assert metrics["c_keep"]["mean"] == 1.0
    assert metrics["c_renew"]["mean"] == 0.25
    assert metrics["c_keep"]["lcb95"] < metrics["c_keep"]["mean"]


def test_formal_analysis_writer_invokes_strengthened_validator(tmp_path: Path, monkeypatch):
    calls: list[Path] = []

    def fake_validate(path):
        calls.append(Path(path))
        return {}

    monkeypatch.setattr(runner, "validate_formal_result", fake_validate)
    _write_and_validate_analysis(tmp_path, {"formal": True}, formal=True)
    assert calls == [tmp_path]
    assert json.loads((tmp_path / "analysis_result.json").read_text(encoding="utf-8")) == {"formal": True}
