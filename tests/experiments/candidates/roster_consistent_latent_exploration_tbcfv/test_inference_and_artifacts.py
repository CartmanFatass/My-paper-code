from __future__ import annotations

import copy
from dataclasses import replace
import math

import pytest
from scipy.stats import t as student_t

from experiments.candidates.roster_consistent_latent_exploration_tbcfv.artifacts import (
    ArtifactError,
    LEARNED_ARMS,
    MODEL_PARAMETER_COUNT,
    MODEL_TENSOR_SPECS,
    REVISION_DIGEST,
    SCIENCE_REVISION,
    SCRIPTED_PACKAGES,
    SyntheticFrontier,
    compute_source_digest,
    create_fixture_root,
    make_aggregate_manifest,
    make_baseline_manifest,
    make_scripted_panel_manifest,
    make_semantic_position_manifest,
    make_synthetic_model_state_manifest,
    publish_synthetic_frontier,
    restore_synthetic_frontier,
    scan_resume_root,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.inference import (
    BLOCK_COUNT,
    BRANCHES,
    ANALYZER_SCHEMA_VERSION,
    DEGREES_OF_FREEDOM,
    DIRECT_VALUE_VARIABLES,
    GAMMA_GLOBAL,
    HELDOUT_CELLS,
    MECHANISM_VARIABLES,
    PREREQUISITE_VARIABLES,
    TRAINING_CELLS,
    TAIL_COUNT,
    analyze_fixture_records,
)

TEST_SOURCE_DIGEST = "a" * 64


def _record() -> dict[str, object]:
    return {
        "schema_version": ANALYZER_SCHEMA_VERSION,
        "revision": SCIENCE_REVISION,
        "source_digest": TEST_SOURCE_DIGEST,
        "fixture_only": True,
        "non_scientific": True,
        "construction_guards": {
            "complete_construction": True,
            "host_component": "rcle.tbcfv.r04.synthetic_fixture_host",
            "host_source_digest": TEST_SOURCE_DIGEST,
            "treatment_fidelity": True,
            "analytic_containment": True,
            "evaluation_adaptation": False,
            "forbidden_information": False,
            "unregistered_coordinate": False,
            "learned_arms": list(LEARNED_ARMS),
            "scripted_packages": list(SCRIPTED_PACKAGES),
            "training_cells": list(TRAINING_CELLS),
            "heldout_cells": list(HELDOUT_CELLS),
        },
        "prerequisite": {name: 1.0 for name in PREREQUISITE_VARIABLES},
        "direct_value": {name: 0.0 for name in DIRECT_VALUE_VARIABLES},
        "mechanism": {name: 0.0 for name in MECHANISM_VARIABLES},
    }


def _constant_records(
    *,
    prerequisite: dict[str, float] | None = None,
    direct: dict[str, float] | None = None,
    mechanism: dict[str, float] | None = None,
) -> list[dict[str, object]]:
    records = [_record() for _ in range(BLOCK_COUNT)]
    for record in records:
        record["prerequisite"].update(prerequisite or {})  # type: ignore[union-attr]
        record["direct_value"].update(direct or {})  # type: ignore[union-attr]
        record["mechanism"].update(mechanism or {})  # type: ignore[union-attr]
    return records


def _analyze(records):
    return analyze_fixture_records(records, expected_source_digest=TEST_SOURCE_DIGEST)


def _c1p1_win() -> dict[str, float]:
    return {
        "time.8_to_12": 5.0,
        "time.12_to_8": 0.0,
        "loss.8_to_12": 0.0,
        "loss.12_to_8": 0.0,
    }


def _combined_mechanism() -> dict[str, float]:
    return {
        "churn_specificity.8_to_12": 3.0,
        "fragmentation.8_to_12": 0.06,
        "commonality.8_to_12": 3.0,
        "persistence.8_to_12": 3.0,
        "bundle.8_to_12": 5.0,
    }


@pytest.mark.parametrize(
    ("records", "expected_branch"),
    [
        (lambda: _constant_records()[:-1], BRANCHES[0]),
        (
            lambda: _constant_records(prerequisite={"opportunity.time.8_to_12": 0.0}),
            BRANCHES[1],
        ),
        (
            lambda: _constant_records(
                prerequisite={"scaffold.time.8_to_8.active_continuation": 0.0}
            ),
            BRANCHES[2],
        ),
        (
            lambda: _constant_records(
                prerequisite={"flex.time_gap.8_to_8.active_continuation": 0.0}
            ),
            BRANCHES[3],
        ),
        (
            lambda: _constant_records(direct=_c1p1_win(), mechanism=_combined_mechanism()),
            BRANCHES[4],
        ),
        (
            lambda: _constant_records(
                direct=_c1p1_win(),
                mechanism={**_combined_mechanism(), "persistence.8_to_12": 0.0},
            ),
            BRANCHES[5],
        ),
        (lambda: _constant_records(direct=_c1p1_win()), BRANCHES[6]),
        (
            lambda: _constant_records(
                direct=_c1p1_win(), mechanism={"churn_specificity.8_to_12": 3.0}
            ),
            BRANCHES[7],
        ),
        (
            lambda: _constant_records(
                direct={
                    "time.8_to_12": -5.0,
                    "time.12_to_8": 0.0,
                    "loss.8_to_12": 0.0,
                    "loss.12_to_8": 0.0,
                }
            ),
            BRANCHES[8],
        ),
        (
            lambda: _constant_records(mechanism={"fragmentation.8_to_12": 0.06}),
            BRANCHES[9],
        ),
        (lambda: _constant_records(), BRANCHES[10]),
        (
            lambda: _constant_records(direct={"time.8_to_12": 3.0}),
            BRANCHES[11],
        ),
    ],
)
def test_handwritten_non_scientific_aggregates_cover_every_first_match_branch(
    records, expected_branch
) -> None:
    outcome = _analyze(records())
    assert outcome.branch == expected_branch
    assert outcome.fixture_only is True
    assert outcome.non_scientific is True
    if expected_branch == "INVALID_OR_INCOMPLETE":
        assert outcome.scientific_branch is None
        assert outcome.valid_complete_fixture is False
    else:
        assert outcome.scientific_branch is None
        assert outcome.valid_complete_fixture is True


def test_exact_family_schema_global_gamma_and_student_t_bound() -> None:
    assert len(PREREQUISITE_VARIABLES) == 44
    assert len(DIRECT_VALUE_VARIABLES) == 4
    assert len(MECHANISM_VARIABLES) == 10
    assert TAIL_COUNT == 44 + 2 * 4 + 2 * 10 == 72
    assert GAMMA_GLOBAL == 1.0 - 0.05 / 72
    assert DEGREES_OF_FREEDOM == 19

    records = _constant_records()
    for index, record in enumerate(records):
        record["direct_value"]["time.8_to_12"] = float(index)  # type: ignore[index]
    outcome = _analyze(records)
    bound = outcome.bounds["direct_value"]["time.8_to_12"]
    expected_mean = 9.5
    expected_sd = math.sqrt(sum((value - expected_mean) ** 2 for value in range(20)) / 19)
    expected_half_width = (
        float(student_t.ppf(GAMMA_GLOBAL, df=19)) * expected_sd / math.sqrt(20)
    )
    assert bound.mean == pytest.approx(expected_mean)
    assert bound.standard_deviation == pytest.approx(expected_sd)
    assert bound.lower == pytest.approx(expected_mean - expected_half_width)
    assert bound.upper == pytest.approx(expected_mean + expected_half_width)


def test_zero_variance_bounds_and_inclusive_strict_boundaries() -> None:
    records = _constant_records(
        direct={
            "time.8_to_12": 2.0,
            "time.12_to_8": -2.0,
            "loss.8_to_12": 0.02,
            "loss.12_to_8": -0.02,
        },
        mechanism={
            "churn_specificity.8_to_12": 2.0,
            "fragmentation.8_to_12": 0.05,
            "commonality.8_to_12": 2.0,
            "persistence.8_to_12": 2.0,
            "bundle.8_to_12": 4.0,
        },
    )
    outcome = _analyze(records)
    assert outcome.branch == "TARGET_SPECIFIC_NO_MATERIAL"
    for family_name, family in outcome.bounds.items():
        for bound in family.values():
            assert bound.standard_deviation == 0.0
            assert bound.lower == bound.mean
            if family_name != "prerequisite":
                assert bound.mean == bound.upper
    assert outcome.predicates["combined_commitment_paths"] == ()

    strict_win_boundary = _analyze(
        _constant_records(direct={"time.8_to_12": 4.0})
    )
    assert strict_win_boundary.predicates["c1p1_target_win"] is False


@pytest.mark.parametrize(
    "mutate",
    [
        lambda records: records.pop(),
        lambda records: records[0]["direct_value"].__setitem__("time.8_to_12", math.nan),
        lambda records: records[0]["mechanism"].pop("bundle.12_to_8"),
        lambda records: records[0].__setitem__("fixture_only", False),
        lambda records: records[0].__setitem__("unexpected", 1),
    ],
)
def test_malformed_incomplete_or_nonfinite_input_fails_closed_without_scientific_branch(
    mutate,
) -> None:
    records = _constant_records()
    mutate(records)
    outcome = _analyze(records)
    assert outcome.branch == "INVALID_OR_INCOMPLETE"
    assert outcome.scientific_branch is None
    assert outcome.valid_complete_fixture is False
    assert outcome.bounds == {}
    assert outcome.gates == {}
    assert outcome.predicates == {}
    assert outcome.failure_reason


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("host_source_digest", "b" * 64),
        ("treatment_fidelity", False),
        ("analytic_containment", False),
        ("evaluation_adaptation", True),
        ("forbidden_information", True),
        ("unregistered_coordinate", True),
        ("learned_arms", list(LEARNED_ARMS[:-1])),
        ("scripted_packages", list(SCRIPTED_PACKAGES[:-1])),
        ("training_cells", list(TRAINING_CELLS[:-1])),
        ("heldout_cells", list(HELDOUT_CELLS[:-1])),
    ],
)
def test_construction_guard_failure_precedes_every_scientific_fixture_branch(
    field, bad_value
) -> None:
    records = _constant_records(direct=_c1p1_win(), mechanism=_combined_mechanism())
    records[0]["construction_guards"][field] = bad_value  # type: ignore[index]
    outcome = _analyze(records)
    assert outcome.branch == "INVALID_OR_INCOMPLETE"
    assert outcome.scientific_branch is None
    assert outcome.bounds == {}
    assert outcome.predicates == {}


def test_revision_source_and_guard_group_are_mandatory_before_reduction() -> None:
    for mutation in (
        lambda record: record.__setitem__("source_digest", "b" * 64),
        lambda record: record.__setitem__("revision", "wrong-revision"),
        lambda record: record.pop("construction_guards"),
        lambda record: record["construction_guards"].__setitem__("extra", True),
    ):
        records = _constant_records(direct=_c1p1_win(), mechanism=_combined_mechanism())
        mutation(records[0])
        assert _analyze(records).branch == "INVALID_OR_INCOMPLETE"


def _frontier(label: str = "synthetic_fixture_alpha") -> SyntheticFrontier:
    source_digest = compute_source_digest(
        {"artifacts.py": b"deterministic artifact source", "inference.py": b"analyzer source"}
    )
    return SyntheticFrontier(
        fixture_label=label,
        source_digest=source_digest,
        learned_model_state={
            arm: make_synthetic_model_state_manifest(arm, source_digest)
            for arm in LEARNED_ARMS
        },
        scripted_payloads={
            package: make_scripted_panel_manifest(package, source_digest)
            for package in SCRIPTED_PACKAGES
        },
        baselines=make_baseline_manifest(source_digest, value=0.25),
        semantic_position=make_semantic_position_manifest(
            source_digest,
            phase="fixture_after_synthetic_step",
            update_block_offset=17,
            episode_offset=9,
            host_tick_offset=13,
            claim_clock_offset=4,
            arm_cursor=2,
        ),
        arm_order=LEARNED_ARMS,
        aggregates=make_aggregate_manifest(source_digest, count=11, value=0.25),
    )


def test_atomic_complete_publication_and_exact_resume(tmp_path) -> None:
    root = create_fixture_root(tmp_path)
    expected = _frontier()
    published = publish_synthetic_frontier(root, expected)

    assert published.parent == root
    assert (published / "COMPLETE").is_file()
    assert not any(".tmp-" in path.name for path in root.rglob("*"))
    restored = restore_synthetic_frontier(
        published, expected_source_digest=expected.source_digest
    )
    assert restored == expected
    assert scan_resume_root(root, expected_source_digest=expected.source_digest) == (expected,)
    assert restored.fixture_only is True
    assert restored.non_scientific is True
    assert restored.revision == SCIENCE_REVISION
    assert restored.arm_order == LEARNED_ARMS
    assert len(REVISION_DIGEST) == 64


def test_duplicate_incomplete_tamper_and_source_mismatch_are_rejected(tmp_path) -> None:
    root = create_fixture_root(tmp_path)
    expected = _frontier()
    published = publish_synthetic_frontier(root, expected)
    with pytest.raises(ArtifactError, match="duplicate"):
        publish_synthetic_frontier(root, expected)
    with pytest.raises(ArtifactError, match="source digest mismatch"):
        restore_synthetic_frontier(published, expected_source_digest="0" * 64)

    learned_file = published / "learned" / f"{LEARNED_ARMS[0]}.json"
    learned_file.write_text('{"weights":[999]}\n', encoding="ascii")
    with pytest.raises(ArtifactError, match="tamper or corruption"):
        restore_synthetic_frontier(published)

    incomplete = root / "synthetic_fixture_incomplete"
    incomplete.mkdir()
    with pytest.raises(ArtifactError, match="required regular file is missing"):
        restore_synthetic_frontier(incomplete)


def test_completeness_frozen_order_and_nonempirical_fields_fail_closed(tmp_path) -> None:
    root = create_fixture_root(tmp_path)
    expected = _frontier()
    missing_arm = dict(expected.learned_model_state)
    missing_arm.pop(LEARNED_ARMS[-1])
    with pytest.raises(ArtifactError, match="exactly"):
        publish_synthetic_frontier(root, replace(expected, learned_model_state=missing_arm))
    with pytest.raises(ArtifactError, match="frozen five-arm order"):
        publish_synthetic_frontier(root, replace(expected, arm_order=tuple(reversed(LEARNED_ARMS))))
    with pytest.raises(ArtifactError):
        publish_synthetic_frontier(
            root, replace(expected, semantic_position={"coordinate": "not-allowed"})
        )
    malformed_aggregates = copy.deepcopy(expected.aggregates)
    malformed_aggregates["families"]["direct_value"]["time.8_to_12"]["sum"] = (1.0, 2.0)
    with pytest.raises(ArtifactError):
        publish_synthetic_frontier(
            root, replace(expected, aggregates=malformed_aggregates)
        )


def test_exact_compact_model_inventory_is_26161_float64_entries_per_arm() -> None:
    assert MODEL_PARAMETER_COUNT == 26_161
    assert sum(math.prod(shape) for _, shape in MODEL_TENSOR_SPECS) == 26_161
    frontier = _frontier()
    for arm in LEARNED_ARMS:
        state = frontier.learned_model_state[arm]
        assert state["parameter_count"] == 26_161
        assert state["arm"] == arm
        assert state["training_cells"] == list(TRAINING_CELLS)
        assert state["heldout_cells"] == list(HELDOUT_CELLS)
        assert sum(tensor["numel"] for tensor in state["tensors"]) == 26_161
        assert all(tensor["dtype"] == "float64" for tensor in state["tensors"])
        assert [(tensor["name"], tuple(tensor["shape"])) for tensor in state["tensors"]] == list(
            MODEL_TENSOR_SPECS
        )


def test_every_versioned_frontier_subschema_rejects_omission_extra_nonfinite_or_failed_flag(
    tmp_path,
) -> None:
    root = create_fixture_root(tmp_path)
    expected = _frontier()
    malformed: list[SyntheticFrontier] = []

    learned_missing_tensor = copy.deepcopy(expected.learned_model_state)
    learned_missing_tensor[LEARNED_ARMS[0]]["tensors"].pop()
    malformed.append(replace(expected, learned_model_state=learned_missing_tensor))

    learned_wrong_dtype = copy.deepcopy(expected.learned_model_state)
    learned_wrong_dtype[LEARNED_ARMS[0]]["tensors"][0]["dtype"] = "float32"
    malformed.append(replace(expected, learned_model_state=learned_wrong_dtype))

    learned_extra = copy.deepcopy(expected.learned_model_state)
    learned_extra[LEARNED_ARMS[0]]["unexpected"] = True
    malformed.append(replace(expected, learned_model_state=learned_extra))

    learned_wrong_source = copy.deepcopy(expected.learned_model_state)
    learned_wrong_source[LEARNED_ARMS[0]]["source_digest"] = "b" * 64
    malformed.append(replace(expected, learned_model_state=learned_wrong_source))

    scripted_missing_cell = copy.deepcopy(expected.scripted_payloads)
    scripted_missing_cell[SCRIPTED_PACKAGES[0]]["heldout_cells"].pop()
    malformed.append(replace(expected, scripted_payloads=scripted_missing_cell))

    baselines_missing = copy.deepcopy(expected.baselines)
    baselines_missing["cells"][LEARNED_ARMS[0]].pop(TRAINING_CELLS[0])
    malformed.append(replace(expected, baselines=baselines_missing))

    baselines_extra = copy.deepcopy(expected.baselines)
    baselines_extra["cells"][LEARNED_ARMS[0]]["extra.cell"] = 0.0
    malformed.append(replace(expected, baselines=baselines_extra))

    baselines_nonfinite = copy.deepcopy(expected.baselines)
    baselines_nonfinite["cells"][LEARNED_ARMS[0]][TRAINING_CELLS[0]] = math.inf
    malformed.append(replace(expected, baselines=baselines_nonfinite))

    position_out_of_range = copy.deepcopy(expected.semantic_position)
    position_out_of_range["update_block_offset"] = 801
    malformed.append(replace(expected, semantic_position=position_out_of_range))

    position_extra = copy.deepcopy(expected.semantic_position)
    position_extra["extra"] = 0
    malformed.append(replace(expected, semantic_position=position_extra))

    aggregate_missing = copy.deepcopy(expected.aggregates)
    aggregate_missing["families"]["prerequisite"].pop(PREREQUISITE_VARIABLES[0])
    malformed.append(replace(expected, aggregates=aggregate_missing))

    aggregate_nonfinite = copy.deepcopy(expected.aggregates)
    aggregate_nonfinite["families"]["mechanism"][MECHANISM_VARIABLES[0]]["sum"] = math.nan
    malformed.append(replace(expected, aggregates=aggregate_nonfinite))

    aggregate_failed_validity = copy.deepcopy(expected.aggregates)
    aggregate_failed_validity["validity"]["complete_fixture"] = False
    malformed.append(replace(expected, aggregates=aggregate_failed_validity))

    for candidate in malformed:
        with pytest.raises(ArtifactError):
            publish_synthetic_frontier(root, candidate)
    assert not any(root.iterdir())


def test_source_digest_is_name_and_content_bound() -> None:
    first = compute_source_digest({"a": b"one", "b": "two"})
    reordered = compute_source_digest({"b": "two", "a": b"one"})
    changed_name = compute_source_digest({"a": b"one", "c": "two"})
    changed_content = compute_source_digest({"a": b"one", "b": "three"})
    assert first == reordered
    assert first != changed_name
    assert first != changed_content
    assert len(first) == 64
