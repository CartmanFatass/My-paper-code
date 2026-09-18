"""Comparison contract tests.

The cases that matter are the two SHA directions (a declared algorithm change must not
trigger a blanket refusal; an equal SHA must not certify an equal configuration), the
metric/world incomparability that blocks pooling, and the pairing rule that refuses to
accept equal seeds as world identity.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# See the note in ``test_readers.py``: ``tests/tools/`` shadows the checkout's ``tools``
# namespace package, so the checkout root has to come first on ``sys.path``.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_TESTS_TOOLS = str(Path(__file__).resolve().parents[1])
if str(_REPO_ROOT) in sys.path:
    sys.path.remove(str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT))
for _name in [n for n in list(sys.modules) if n == "tools" or n.startswith("tools.")]:
    _origin = getattr(sys.modules[_name], "__file__", None)
    if _origin and _origin.startswith(_TESTS_TOOLS):
        del sys.modules[_name]

from tools.research_support.compare import (  # noqa: E402
    PAIRING_UNPAIRED,
    PAIRING_UNVERIFIED,
    PAIRING_VERIFIED,
    ComparisonSpec,
    DifferenceClass,
    GroupValue,
    classify_pairing,
    compare_runs,
    write_comparison_report,
)
from tools.research_support.readers import WORLD_IDENTITY_FIELDS  # noqa: E402
from tools.research_support.records import loads  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_readers import build_process_core  # noqa: E402

SHA_A = "a" * 40
SHA_B = "c" * 40

CONTROLS = ["environment_identity", "metric_semantics", "simulated_horizon"]


def _spec(tmp_path: Path, left: Path, right: Path, **kwargs) -> ComparisonSpec:
    return ComparisonSpec(groups={"left": [str(left)], "right": [str(right)]}, **kwargs)


def test_equal_sha_with_a_different_reward_scale_is_incomparable(tmp_path: Path) -> None:
    """Equal SHA does not establish equal effective configuration."""

    left = build_process_core(
        tmp_path / "left", source_commit=SHA_A, channel_composition="literal_equal_mean_0.5"
    )
    right = build_process_core(
        tmp_path / "right", source_commit=SHA_A, channel_composition="literal_equal_mean_1.0"
    )
    report = compare_runs(_spec(tmp_path, left, right, controls=CONTROLS))

    assert report.classification_of("source_sha") is DifferenceClass.VERIFIED_MATCH
    assert (
        report.classification_of("metric_semantics")
        is DifferenceClass.INCOMPARABLE_METRIC_OR_WORLD
    )
    assert report.pooling_permitted is False
    assert any("incomparable metric or world" in refusal for refusal in report.refusals)
    assert any(
        "equal source SHA does not establish equal effective configuration" in warning
        for warning in report.warnings
    )
    values = report.by_field("metric_semantics").values
    assert "literal_equal_mean_0.5" in values["left"]["value"]
    assert "literal_equal_mean_1.0" in values["right"]["value"]


def test_different_sha_declared_as_treatment_still_permits_pooling(tmp_path: Path) -> None:
    """A different SHA is often the intended algorithm change, not a confound."""

    left = build_process_core(tmp_path / "left", source_commit=SHA_A, algorithm="ALG_V1")
    right = build_process_core(tmp_path / "right", source_commit=SHA_B, algorithm="ALG_V2")
    report = compare_runs(
        _spec(
            tmp_path,
            left,
            right,
            treatment_factors=["source_sha", "algorithm_label"],
            controls=CONTROLS,
        )
    )

    assert (
        report.classification_of("source_sha") is DifferenceClass.EXPECTED_TREATMENT_DIFFERENCE
    )
    assert (
        report.classification_of("algorithm_label")
        is DifferenceClass.EXPECTED_TREATMENT_DIFFERENCE
    )
    for control in CONTROLS:
        assert report.classification_of(control) is DifferenceClass.VERIFIED_MATCH
    assert report.pooling_permitted is True
    assert any(
        "legitimate algorithm change" in warning for warning in report.warnings
    )
    assert any("advisory" in warning for warning in report.warnings)


def test_different_sha_declared_as_a_control_is_a_confound_but_does_not_block_pooling(
    tmp_path: Path,
) -> None:
    left = build_process_core(tmp_path / "left", source_commit=SHA_A)
    right = build_process_core(tmp_path / "right", source_commit=SHA_B)
    report = compare_runs(
        _spec(tmp_path, left, right, controls=["source_sha", *CONTROLS])
    )

    assert report.classification_of("source_sha") is DifferenceClass.ADDITIONAL_CONFOUND
    assert "proposed as a control" in report.by_field("source_sha").detail
    # A confound is reported, not converted into a blanket refusal.
    assert report.pooling_permitted is True


def test_undeclared_sha_difference_is_reported_without_blocking_pooling(
    tmp_path: Path,
) -> None:
    left = build_process_core(tmp_path / "left", source_commit=SHA_A)
    right = build_process_core(tmp_path / "right", source_commit=SHA_B)
    report = compare_runs(_spec(tmp_path, left, right, controls=CONTROLS))

    difference = report.by_field("source_sha")
    assert difference.classification is DifferenceClass.ADDITIONAL_CONFOUND
    assert "declare it a treatment factor" in difference.detail
    assert report.pooling_permitted is True


def test_missing_required_control_blocks_pooling(tmp_path: Path) -> None:
    left = build_process_core(tmp_path / "left")
    right = build_process_core(tmp_path / "right")
    report = compare_runs(
        _spec(tmp_path, left, right, controls=["information_condition", *CONTROLS])
    )

    assert report.classification_of("information_condition") is DifferenceClass.MISSING_EVIDENCE
    assert report.pooling_permitted is False
    assert any("required control" in refusal for refusal in report.refusals)


def test_equal_seeds_alone_leave_pairing_unverified(tmp_path: Path) -> None:
    """Identical seed bases, no world identity: the comparison is not paired."""

    seeds = {"branch_action": 10442000, "evaluation_action": 10446000}
    left = build_process_core(
        tmp_path / "left", seed_bases=seeds, with_evaluation=False, with_analysis=False
    )
    right = build_process_core(
        tmp_path / "right", seed_bases=seeds, with_evaluation=False, with_analysis=False
    )
    report = compare_runs(_spec(tmp_path, left, right, controls=["training_seed"]))

    assert report.classification_of("training_seed") is DifferenceClass.VERIFIED_MATCH
    assert report.pairing_status == PAIRING_UNVERIFIED
    assert any("paired summary refused" in refusal for refusal in report.refusals)
    assert any(
        "equal integer seeds and equal episode numbers are never accepted" in warning
        for warning in report.warnings
    )


def test_different_event_realisation_is_unpaired(tmp_path: Path) -> None:
    left = build_process_core(
        tmp_path / "left", signatures=("((6, 17), ('L', 'R'), 'small_4_2', (1, 3))",)
    )
    right = build_process_core(
        tmp_path / "right", signatures=("((9, 31), ('R', 'L'), 'small_6_3', (2, 4))",)
    )
    report = compare_runs(_spec(tmp_path, left, right, controls=CONTROLS))

    assert report.pairing_status == PAIRING_UNPAIRED
    assert any("did not run the same world" in warning for warning in report.warnings)


def test_classify_pairing_needs_all_four_world_identity_fields() -> None:
    complete = {
        name: {
            "left": GroupValue(present=True, value=f"{name}-value"),
            "right": GroupValue(present=True, value=f"{name}-value"),
        }
        for name in WORLD_IDENTITY_FIELDS
    }
    status, detail = classify_pairing(complete, group_count=2)
    assert status == PAIRING_VERIFIED
    assert "all world-identity fields present and equal" in detail

    partial = dict(complete)
    partial["dataset_identity"] = {
        "left": GroupValue(present=False, detail="not recorded"),
        "right": GroupValue(present=False, detail="not recorded"),
    }
    status, detail = classify_pairing(partial, group_count=2)
    assert status == PAIRING_UNVERIFIED
    assert "dataset_identity" in detail

    differing = dict(complete)
    differing["event_realization"] = {
        "left": GroupValue(present=True, value="one"),
        "right": GroupValue(present=True, value="two"),
    }
    status, _ = classify_pairing(differing, group_count=2)
    assert status == PAIRING_UNPAIRED

    status, detail = classify_pairing(complete, group_count=1)
    assert status == PAIRING_UNPAIRED
    assert "nothing to pair" in detail


def test_exploratory_display_warns_and_never_promotes_a_match(tmp_path: Path) -> None:
    left = build_process_core(tmp_path / "left", channel_composition="literal_equal_mean_0.5")
    right = build_process_core(tmp_path / "right", channel_composition="literal_equal_mean_1.0")
    report = compare_runs(
        _spec(tmp_path, left, right, controls=CONTROLS, allow_exploratory_display=True)
    )

    assert report.pooling_permitted is False
    assert (
        report.classification_of("metric_semantics")
        is DifferenceClass.INCOMPARABLE_METRIC_OR_WORLD
    )
    assert any("EXPLORATORY DISPLAY ONLY" in warning for warning in report.warnings)
    assert report.refusals, "the refusals stand under an exploratory override"


def test_within_group_disagreement_is_not_averaged_away(tmp_path: Path) -> None:
    one = build_process_core(tmp_path / "one", channel_composition="literal_equal_mean_0.5")
    two = build_process_core(tmp_path / "two", channel_composition="literal_equal_mean_1.0")
    three = build_process_core(tmp_path / "three", channel_composition="literal_equal_mean_0.5")
    spec = ComparisonSpec(
        groups={"mixed": [str(one), str(two)], "clean": [str(three)]},
        controls=CONTROLS,
    )
    report = compare_runs(spec)

    difference = report.by_field("metric_semantics")
    assert difference.classification is DifferenceClass.INCOMPARABLE_METRIC_OR_WORLD
    assert difference.values["mixed"]["heterogeneous"] is True
    assert report.pooling_permitted is False


def test_unreadable_root_is_refused_not_guessed(tmp_path: Path) -> None:
    left = build_process_core(tmp_path / "left")
    empty = tmp_path / "nothing_here"
    empty.mkdir()
    report = compare_runs(_spec(tmp_path, left, empty))

    assert report.runs["right"][0]["status"] == "error"
    assert "UnsupportedSourceError" in report.runs["right"][0]["error"]
    assert report.pooling_permitted is False
    assert any("no readable run record" in refusal for refusal in report.refusals)


def test_requested_metric_availability_is_classified(tmp_path: Path) -> None:
    left = build_process_core(tmp_path / "left")
    right = build_process_core(tmp_path / "right", with_evaluation=False, with_analysis=False)
    report = compare_runs(
        _spec(tmp_path, left, right, controls=CONTROLS, metrics=["utility", "real_transitions"])
    )

    assert report.classification_of("metric:real_transitions") is DifferenceClass.VERIFIED_MATCH
    assert report.classification_of("metric:utility") is DifferenceClass.MISSING_EVIDENCE
    profile = report.by_field("metric:utility").values
    assert profile["left"]["n_records"] == 2
    assert profile["right"]["n_records"] == 0


def test_spec_from_file_round_trip_and_strictness(tmp_path: Path) -> None:
    left = build_process_core(tmp_path / "left")
    right = build_process_core(tmp_path / "right")
    path = tmp_path / "spec.json"
    path.write_text(
        json.dumps(
            {
                "groups": {"left": [str(left)], "right": [str(right)]},
                "treatment_factors": ["source_sha"],
                "controls": CONTROLS,
                "metrics": ["utility"],
            }
        ),
        encoding="utf-8",
    )
    spec = ComparisonSpec.from_file(path)
    assert spec.groups["left"] == [str(left)]
    assert spec.spec_hash.startswith("sha256:")
    assert compare_runs(spec).spec_hash == spec.spec_hash

    bad = tmp_path / "bad.json"
    bad.write_text(
        json.dumps({"groups": {"a": ["x"]}, "control": ["typo"]}), encoding="utf-8"
    )
    with pytest.raises(ValueError) as error:
        ComparisonSpec.from_file(bad)
    assert "unknown specification keys" in str(error.value)

    with pytest.raises(ValueError):
        ComparisonSpec(groups={"empty": []})


def test_write_comparison_report_refuses_a_non_empty_directory(tmp_path: Path) -> None:
    left = build_process_core(tmp_path / "left")
    right = build_process_core(tmp_path / "right", source_commit=SHA_B)
    report = compare_runs(_spec(tmp_path, left, right, treatment_factors=["source_sha"]))

    output = tmp_path / "comparison"
    output.mkdir()
    (output / "keep.txt").write_text("evidence", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_comparison_report(report, output)
    assert (output / "keep.txt").read_text(encoding="utf-8") == "evidence"

    fresh = tmp_path / "comparison-2"
    assert write_comparison_report(report, fresh) == fresh
    payload = loads((fresh / "comparison_report.json").read_text(encoding="utf-8"))
    assert payload["spec_hash"] == report.spec_hash
    assert payload["pairing_status"] == report.pairing_status
    markdown = (fresh / "comparison_report.md").read_text(encoding="utf-8")
    assert "# Comparison report" in markdown
    assert "EXPECTED_TREATMENT_DIFFERENCE" in markdown
