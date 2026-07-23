from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import run_ehc_sequence_mediation_prototype_g1 as runner


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _branch(kind: str, controller: str) -> dict[str, object]:
    if kind == "event":
        contrast = {
            "left": {"event": "KEEP", "mark": "current"},
            "right": {"event": "RENEW", "mark": "opposite"},
        }
    else:
        contrast = {
            "left": {"event": "RENEW", "mark": "current"},
            "right": {"event": "RENEW", "mark": "opposite"},
        }
    branch = {
        "intervention_event": "RENEW",
        "intervention_mark": 1,
        "intervention_time": 3,
        "intervention_action": 1,
        "intervention_probabilities": (0.0, 0.0, 1.0),
        "downstream_actions": (1,),
        "downstream_correct": (True,),
        "downstream_times": (4,),
        "terminal_time": 80,
        "terminal_outcome": {"utility": 0.5},
        "final_rng_draws": {"event": 0, "mark": 0, "action": 0},
    }
    return {
        "kind": kind,
        "controller": controller,
        "snapshot_provenance": {
            "time": 3,
            "age": 3,
            "cue_present": False,
            "remaining_active_opportunities": 10,
            "terminal_event_same_step": False,
            "current_mark": 1,
        },
        "target_slot": 0,
        "contrast": contrast,
        "branch_origin_equal": True,
        "common_random_numbers": {
            "equal": True,
            "left_draws": {"event": 0, "mark": 0, "action": 0},
            "right_draws": {"event": 0, "mark": 0, "action": 0},
        },
        "metrics": {
            "instantaneous_tv": 0.0,
            "sequence_hamming": 0.0,
            "sequence_correctness_difference": 0.0,
            "terminal_utility_delta": 0.0,
        },
        "branches": {"left": deepcopy(branch), "right": deepcopy(branch)},
    }


def _records() -> list[dict[str, object]]:
    records = []
    for cell in runner.enumerate_registered_cells():
        controller = str(cell["controller"])
        records.append(
            {
                "controller": controller,
                "spec": {
                    key: value
                    for key, value in cell.items()
                    if key
                    in {"split", "roster_size", "duration", "sign_start", "rotation"}
                },
                "seeds": dict(runner.SEED_INVENTORY),
                "rows": [
                    {
                        "provenance": "natural",
                        "forced": False,
                        "controller": controller,
                        "time": 0,
                        "slot": 0,
                        "observation": (1.0, 1.0, 1.0, 0.0, 0.0, 0.5),
                        "event": "RENEW",
                        "evaluation_correct": True,
                    },
                    {
                        "provenance": "natural",
                        "forced": False,
                        "controller": controller,
                        "time": 1,
                        "slot": 0,
                        "observation": (0.0, 0.0, 0.0, 0.0, 0.0, 0.5),
                        "event": "KEEP",
                        "evaluation_correct": True,
                    },
                ],
                "branch_snapshots": [
                    {
                        "version": 1,
                        "controller": controller,
                        "target_slot": 0,
                        "selection": {
                            "time": 3,
                            "age": 3,
                            "cue_present": False,
                            "remaining_active_opportunities": 10,
                            "terminal_event_same_step": False,
                            "current_mark": 1,
                        },
                        "environment_state": {},
                        "controller_state": {},
                    }
                ],
                "event_interventions": [_branch("event", controller)],
                "mark_interventions": [_branch("mark", controller)],
                "outcome": {"utility": 0.5},
            }
        )
    return records


def _analysis() -> dict[str, object]:
    policy = {
        "renew_given_new_segment": 0.0,
        "renew_given_mid_segment": 0.0,
        "difference": 0.0,
        "commitment_lifetime_support": [1],
    }
    sequence = {
        "event_keep_vs_renew": {"hamming": 0.0, "correctness_difference": 0.0},
        "mark_current_vs_opposite": {"hamming": 0.0, "correctness_difference": 0.0},
    }
    terminal = {
        "event_keep_vs_renew": 0.0,
        "mark_current_vs_opposite": 0.0,
    }
    natural = {
        "boundary_renew_rate": 0.0,
        "mid_segment_keep_rate": 0.0,
        "hidden_post_cue_correctness": 0.0,
        "natural_utility": 0.0,
    }
    split_values = {
        "policy_dependence": policy,
        "instantaneous_tv": 0.0,
        "sequence_hamming": sequence,
        "terminal_utility_delta": terminal,
        "natural_mediation": natural,
    }
    return {
        "status": "COMPLETE",
        "measurement_tuple": {
            family: {
                controller: {
                    "fitting": deepcopy(split_values[family]),
                    "heldout": deepcopy(split_values[family]),
                }
                for controller in runner.CONTROLLERS
            }
            for family in split_values
        }
        | {
            "heldout_robustness": {
                controller: deepcopy(split_values) for controller in runner.CONTROLLERS
            },
        },
        "controller_provenance": {
            controller: {
                "natural_provenance": "natural",
                "fitting_cells": 16,
                "heldout_cells": 16,
                "event_contrast": "KEEP/current_vs_RENEW/opposite",
                "mark_contrast": "RENEW/current_vs_RENEW/opposite",
            }
            for controller in runner.CONTROLLERS
        },
    }


def _artifacts() -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    records = _records()
    manifest, analysis = runner.build_artifacts(
        records,
        _analysis(),
        runtime_provenance=runner.current_runtime_provenance(),
    )
    return manifest, analysis, records


def test_exact_seed_inventory_and_registered_episode_inventory() -> None:
    assert runner.SEED_INVENTORY == {
        "task": 731001,
        "membership": 731002,
        "duty": 731003,
        "opportunity": 731004,
        "event": 731005,
        "mark": 731006,
        "action": 731007,
        "evaluation": 731008,
        "audit": 731009,
    }
    cells = runner.enumerate_registered_cells()
    assert len(cells) == 192
    assert len({tuple(cell.items()) for cell in cells}) == 192
    assert {cell["controller"] for cell in cells} == set(runner.CONTROLLERS)
    assert all(sum(cell["controller"] == name for cell in cells) == 32 for name in runner.CONTROLLERS)
    assert {
        (cell["split"], cell["duration"])
        for cell in cells
    } == {("fitting", 6), ("fitting", 14), ("heldout", 10), ("heldout", 18)}


def test_artifacts_bind_exact_identity_cells_hashes_and_nonformal_provenance() -> None:
    manifest, analysis, records = _artifacts()
    runner.validate_prototype_artifacts(manifest, analysis, records=records)

    shared = {
        "schema_version",
        "formal",
        "conclusion_bearing",
        "assignment_id",
        "source_family",
        "design_identity",
        "source_identity",
        "seed_inventory",
        "runtime_provenance",
        "cell_inventory",
        "records_sha256",
    }
    assert shared.issubset(manifest)
    assert shared.issubset(analysis)
    assert all(manifest[key] == analysis[key] for key in shared)
    assert manifest["formal"] is analysis["formal"] is False
    assert manifest["conclusion_bearing"] is analysis["conclusion_bearing"] is False
    assert manifest["assignment_id"] == "EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1"
    assert manifest["source_family"] == "ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1"
    assert len(manifest["cell_inventory"]) == 192
    assert max(cell["branch_snapshot_count"] for cell in manifest["cell_inventory"]) <= 2
    assert all(
        cell["branch_snapshot_count"]
        == cell["event_intervention_pair_count"]
        == cell["mark_intervention_pair_count"]
        for cell in manifest["cell_inventory"]
    )
    assert manifest["analysis_sha256"] == _canonical_sha256(analysis)


def test_json_disk_round_trip_preserves_valid_measurement_family_inventory(
    tmp_path: Path,
) -> None:
    manifest, analysis, _records_value = _artifacts()
    manifest_path = tmp_path / "prototype_manifest.json"
    analysis_path = tmp_path / "prototype_analysis.json"
    runner._write_json(manifest_path, manifest)
    runner._write_json(analysis_path, analysis)

    reloaded_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    reloaded_analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    assert set(reloaded_analysis["measurement_tuple"]) == set(
        analysis["measurement_tuple"]
    )
    runner.validate_prototype_artifacts(reloaded_manifest, reloaded_analysis)


def test_disk_loader_validates_exact_bytes_against_required_trusted_hashes(
    tmp_path: Path,
) -> None:
    manifest, analysis, _records_value = _artifacts()
    manifest_path = tmp_path / "prototype_manifest.json"
    analysis_path = tmp_path / "prototype_analysis.json"
    runner._write_json(manifest_path, manifest)
    runner._write_json(analysis_path, analysis)

    loaded_manifest, loaded_analysis = runner.load_and_validate_prototype_artifacts(
        manifest_path,
        analysis_path,
        expected_manifest_sha256=runner._file_sha256(manifest_path),
        expected_analysis_sha256=runner._file_sha256(analysis_path),
    )
    assert loaded_manifest == manifest
    assert loaded_analysis == analysis


@pytest.mark.parametrize("invalid_hash", ("0" * 63, "A" * 64, "g" * 64))
def test_disk_loader_rejects_malformed_trusted_hashes(
    tmp_path: Path, invalid_hash: str
) -> None:
    manifest, analysis, _records_value = _artifacts()
    manifest_path = tmp_path / "prototype_manifest.json"
    analysis_path = tmp_path / "prototype_analysis.json"
    runner._write_json(manifest_path, manifest)
    runner._write_json(analysis_path, analysis)

    with pytest.raises(ValueError, match="expected manifest.*lowercase"):
        runner.load_and_validate_prototype_artifacts(
            manifest_path,
            analysis_path,
            expected_manifest_sha256=invalid_hash,
            expected_analysis_sha256=runner._file_sha256(analysis_path),
        )


def test_disk_loader_rejects_analysis_tampering_even_with_updated_internal_hash(
    tmp_path: Path,
) -> None:
    manifest, analysis, _records_value = _artifacts()
    manifest_path = tmp_path / "prototype_manifest.json"
    analysis_path = tmp_path / "prototype_analysis.json"
    runner._write_json(manifest_path, manifest)
    runner._write_json(analysis_path, analysis)
    trusted_analysis_sha256 = runner._file_sha256(analysis_path)

    analysis["measurement_tuple"]["natural_mediation"][runner.CONTROLLERS[0]][
        "fitting"
    ]["natural_utility"] = 0.25
    manifest["analysis_sha256"] = _canonical_sha256(analysis)
    runner._write_json(analysis_path, analysis)
    runner._write_json(manifest_path, manifest)

    with pytest.raises(ValueError, match="analysis file hash"):
        runner.load_and_validate_prototype_artifacts(
            manifest_path,
            analysis_path,
            expected_manifest_sha256=runner._file_sha256(manifest_path),
            expected_analysis_sha256=trusted_analysis_sha256,
        )


@pytest.mark.parametrize("mutation", ("missing", "extra", "renamed"))
def test_measurement_family_inventory_rejects_missing_extra_and_renamed(
    mutation: str,
) -> None:
    value = _analysis()
    families = value["measurement_tuple"]
    if mutation == "missing":
        families.pop("policy_dependence")
    elif mutation == "extra":
        families["unexpected_family"] = {}
    else:
        families["renamed_policy_dependence"] = families.pop("policy_dependence")

    with pytest.raises(ValueError, match="family inventory"):
        runner._validate_analysis_result(value)


@pytest.mark.parametrize(
    ("family", "path", "mutation"),
    (
        ("policy_dependence", (), "missing"),
        ("policy_dependence", (), "extra"),
        ("policy_dependence", (), "renamed"),
        ("sequence_hamming", ("event_keep_vs_renew",), "missing"),
        ("sequence_hamming", ("event_keep_vs_renew",), "extra"),
        ("sequence_hamming", ("event_keep_vs_renew",), "renamed"),
        ("terminal_utility_delta", (), "missing"),
        ("terminal_utility_delta", (), "extra"),
        ("terminal_utility_delta", (), "renamed"),
        ("natural_mediation", (), "missing"),
        ("natural_mediation", (), "extra"),
        ("natural_mediation", (), "renamed"),
    ),
)
def test_measurement_nested_schema_rejects_missing_extra_and_renamed_keys(
    family: str, path: tuple[str, ...], mutation: str
) -> None:
    value = _analysis()
    leaf = value["measurement_tuple"][family][runner.CONTROLLERS[0]]["fitting"]
    for key in path:
        leaf = leaf[key]
    original_key = next(iter(leaf))
    if mutation == "missing":
        leaf.pop(original_key)
    elif mutation == "extra":
        leaf["unexpected_key"] = 0.0
    else:
        leaf[f"renamed_{original_key}"] = leaf.pop(original_key)

    with pytest.raises(ValueError, match="schema"):
        runner._validate_analysis_result(value)


@pytest.mark.parametrize(
    ("family", "path", "invalid"),
    (
        ("policy_dependence", ("renew_given_new_segment",), True),
        ("policy_dependence", ("renew_given_mid_segment",), "0.0"),
        ("policy_dependence", ("difference",), 0),
        ("policy_dependence", ("difference",), 1.01),
        ("instantaneous_tv", (), -0.01),
        ("instantaneous_tv", (), float("inf")),
        (
            "sequence_hamming",
            ("event_keep_vs_renew", "hamming"),
            1.01,
        ),
        (
            "sequence_hamming",
            ("mark_current_vs_opposite", "correctness_difference"),
            -1.01,
        ),
        ("terminal_utility_delta", ("event_keep_vs_renew",), -1.01),
        ("natural_mediation", ("hidden_post_cue_correctness",), 2.0),
        ("natural_mediation", ("natural_utility",), float("nan")),
    ),
)
def test_measurement_values_reject_non_float_nonfinite_and_out_of_domain(
    family: str, path: tuple[str, ...], invalid: object
) -> None:
    value = _analysis()
    controller_value = value["measurement_tuple"][family][runner.CONTROLLERS[0]]
    if path:
        leaf = controller_value["fitting"]
        for key in path[:-1]:
            leaf = leaf[key]
        leaf[path[-1]] = invalid
    else:
        controller_value["fitting"] = invalid

    with pytest.raises(ValueError, match="finite|float|domain"):
        runner._validate_analysis_result(value)


@pytest.mark.parametrize(
    "support",
    (
        [],
        [0],
        [81],
        [1, 1],
        [2, 1],
        [True],
        [1.0],
        ["1"],
    ),
)
def test_commitment_lifetime_support_requires_sorted_unique_positive_ints_within_horizon(
    support: list[object],
) -> None:
    value = _analysis()
    value["measurement_tuple"]["policy_dependence"][runner.CONTROLLERS[0]][
        "heldout"
    ]["commitment_lifetime_support"] = support

    with pytest.raises(ValueError, match="lifetime support"):
        runner._validate_analysis_result(value)


def test_heldout_robustness_must_exactly_repeat_every_primary_heldout_family() -> None:
    value = _analysis()
    value["measurement_tuple"]["heldout_robustness"][runner.CONTROLLERS[0]][
        "natural_mediation"
    ]["natural_utility"] = 0.25

    with pytest.raises(ValueError, match="heldout robustness"):
        runner._validate_analysis_result(value)


@pytest.mark.parametrize(
    ("target", "mutate", "match"),
    (
        ("manifest", lambda value: value.__setitem__("formal", True), "formal"),
        (
            "analysis",
            lambda value: value.__setitem__("conclusion_bearing", True),
            "conclusion",
        ),
        (
            "manifest",
            lambda value: value["design_identity"].__setitem__("sha256", "0" * 64),
            "design",
        ),
        (
            "analysis",
            lambda value: value["source_identity"]["files"][0].__setitem__(
                "sha256", "1" * 64
            ),
            "source",
        ),
        (
            "manifest",
            lambda value: value["cell_inventory"].pop(),
            "inventory",
        ),
        (
            "analysis",
            lambda value: value["cell_inventory"].append(
                deepcopy(value["cell_inventory"][0])
            ),
            "inventory",
        ),
        (
            "analysis",
            lambda value: value["measurement_tuple"].__setitem__(
                "instantaneous_tv", float("nan")
            ),
            "finite",
        ),
    ),
)
def test_artifact_validation_fails_closed_on_tampering(
    target: str, mutate, match: str
) -> None:
    manifest, analysis, records = _artifacts()
    mutate(manifest if target == "manifest" else analysis)
    if target == "analysis" and match not in {"finite", "source", "inventory", "conclusion"}:
        manifest["analysis_sha256"] = _canonical_sha256(analysis)
    with pytest.raises(ValueError, match=match):
        runner.validate_prototype_artifacts(manifest, analysis, records=records)


def test_record_validation_rejects_malformed_hashes_cells_and_branch_overflow() -> None:
    manifest, analysis, records = _artifacts()

    malformed = deepcopy(records)
    malformed[0]["rows"] = "not rows"
    with pytest.raises(ValueError, match="record"):
        runner.validate_prototype_artifacts(manifest, analysis, records=malformed)

    wrong_cell_type = deepcopy(records)
    wrong_cell_type[0]["spec"]["roster_size"] = 2.0
    with pytest.raises(ValueError, match="record spec"):
        runner.validate_records(wrong_cell_type)

    overflow = deepcopy(records)
    overflow[0]["branch_snapshots"] *= 3
    overflow[0]["event_interventions"] *= 3
    overflow[0]["mark_interventions"] *= 3
    with pytest.raises(ValueError, match="branch"):
        runner.validate_records(overflow)

    malformed_snapshot = deepcopy(records)
    malformed_snapshot[0]["branch_snapshots"][0].pop("selection")
    with pytest.raises(ValueError, match="snapshot"):
        runner.validate_records(malformed_snapshot)

    malformed_branch = deepcopy(records)
    malformed_branch[0]["event_interventions"][0].pop("branches")
    with pytest.raises(ValueError, match="branch"):
        runner.validate_records(malformed_branch)

    incomplete = deepcopy(records[:-1])
    with pytest.raises(ValueError, match="inventory"):
        runner.validate_records(incomplete)

    extra = deepcopy(records)
    extra.append(deepcopy(records[0]))
    with pytest.raises(ValueError, match="inventory|duplicate"):
        runner.validate_records(extra)

    wrong_hash = deepcopy(manifest)
    wrong_hash["records_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="record"):
        runner.validate_prototype_artifacts(wrong_hash, analysis, records=records)


def test_analysis_validation_rejects_incomplete_controller_inventory() -> None:
    value = _analysis()
    value["controller_provenance"].pop(runner.CONTROLLERS[-1])
    with pytest.raises(ValueError, match="controller provenance"):
        runner.build_artifacts(
            _records(),
            value,
            runtime_provenance=runner.current_runtime_provenance(),
        )

    value = _analysis()
    value["measurement_tuple"]["instantaneous_tv"].pop(runner.CONTROLLERS[-1])
    with pytest.raises(ValueError, match="measurement.*controller"):
        runner.build_artifacts(
            _records(),
            value,
            runtime_provenance=runner.current_runtime_provenance(),
        )


def test_formal_evidence_surface_explicitly_rejects_valid_exercise_artifacts() -> None:
    manifest, analysis, records = _artifacts()
    with pytest.raises(ValueError, match="nonformal.*conclusion-bearing"):
        runner.validate_conclusion_bearing_evidence(manifest, analysis, records=records)
    with pytest.raises(ValueError, match="nonformal.*formal evidence"):
        runner.validate_formal_evidence(manifest, analysis, records=records)


def test_thin_runner_writes_only_two_deterministic_json_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    records_by_cell = iter(_records())

    def fake_collect(*_args, **_kwargs):
        episode = deepcopy(next(records_by_cell))
        episode.pop("event_interventions")
        episode.pop("mark_interventions")
        return episode

    monkeypatch.setattr(runner, "collect_natural_episode", fake_collect)
    monkeypatch.setattr(
        runner,
        "run_event_intervention",
        lambda _snapshot, controller, window=6: _branch("event", controller),
    )
    monkeypatch.setattr(
        runner,
        "run_mark_intervention",
        lambda _snapshot, controller, window=6: _branch("mark", controller),
    )
    monkeypatch.setattr(runner, "analyze_prototype", lambda _records: _analysis())

    output = tmp_path / "caller-owned"
    manifest, analysis = runner.run_prototype(output)
    assert sorted(path.name for path in output.iterdir()) == [
        "prototype_analysis.json",
        "prototype_manifest.json",
    ]
    assert json.loads((output / "prototype_manifest.json").read_text(encoding="utf-8")) == manifest
    assert json.loads((output / "prototype_analysis.json").read_text(encoding="utf-8")) == analysis
    assert not any("threshold" in path.read_text(encoding="utf-8").lower() for path in output.iterdir())


def test_runner_source_has_no_closed_source_import_or_branch_selector() -> None:
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert "formal_path_exercise" not in source
    assert "select_result_branch" not in source
    assert "noncalendar_commitment_benchmark_" + "g0" not in source.lower()
