import copy
import json
from fractions import Fraction
from pathlib import Path

import pytest

from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.analysis import (
    AnalysisError,
    analyze_complete_census,
    validate_complete_result,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.artifact import (
    ArtifactError,
    atomic_write_once,
    publish_complete_result,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.cli import (
    _peak_rss_bytes,
    build_parser,
    main,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.contract import (
    RESULT_NAME,
    canonical_json_bytes,
    make_test_history,
    registered_spec,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.controllers import (
    evaluate_test_census,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.reachable_twins import (
    make_test_twin,
)


def _complete_test_result():
    first = make_test_history(
        "TEST_ONLY_ANALYSIS_A",
        (4, 4, 4),
        ("LEFT", "LEFT", "CENTER"),
        ("+", "+", "+"),
    )
    second = make_test_history(
        "TEST_ONLY_ANALYSIS_B",
        (4, 4, 4),
        ("LEFT", "LEFT", "CENTER"),
        ("+", "-", "+"),
    )
    twin = make_test_twin(
        "TEST_ONLY_LAST_ACK_TWIN",
        "LAST_ACK_BAYES",
        (first, second),
        expected_raw_actions=("LEFT", "CENTER"),
    )
    census = evaluate_test_census((twin,))
    return analyze_complete_census(census, binding_class="TEST_ONLY")


def test_complete_only_analysis_rejects_partial_census():
    result = _complete_test_result()
    partial = copy.deepcopy(result["census"])
    partial["complete"] = False
    with pytest.raises((AnalysisError, ValueError), match="complete|const"):
        analyze_complete_census(partial, binding_class="TEST_ONLY")
    assert result["status"] == "TEST_ONLY_COMPLETE_CONFORMANCE"
    assert result["acceptance"]["all_controller_actions_unique"] is True
    assert any(
        Fraction(*row["controllers"]["LAST_ACK_BAYES"]["value"])
        != Fraction(*row["controllers"]["LAST_ACK_BAYES"]["endpoint_value"])
        for row in result["census"]["rows"]
    )
    for row in result["census"]["rows"]:
        duration = row["endpoint"]["next_duration"]
        for record in row["controllers"].values():
            assert Fraction(*record["physical_time_normalized_endpoint_return"]) == (
                Fraction(*record["endpoint_value"]) / duration
            )


def test_atomic_complete_publication_is_canonical_and_no_overwrite(tmp_path: Path):
    result = _complete_test_result()
    output_root = tmp_path / "TEST_ONLY_COMPLETE_ROOT"
    path = publish_complete_result(output_root, result)
    assert path == output_root / RESULT_NAME
    assert path.read_bytes() == canonical_json_bytes(result)
    assert validate_complete_result(json.loads(path.read_bytes())) == result
    with pytest.raises(ArtifactError, match="overwrite"):
        publish_complete_result(output_root, result)


def test_malformed_or_partial_result_never_publishes_root(tmp_path: Path):
    result = _complete_test_result()
    result["complete"] = False
    output_root = tmp_path / "TEST_ONLY_PARTIAL_ROOT"
    with pytest.raises((ArtifactError, ValueError)):
        publish_complete_result(output_root, result)
    assert not output_root.exists()
    assert not list(tmp_path.glob(".*pending*"))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda result: result["census"]["rows"][0]["controllers"].pop("FULL_BAYES_K"),
        lambda result: result["census"]["rows"].__setitem__(
            1, copy.deepcopy(result["census"]["rows"][0])
        ),
        lambda result: result["census"]["twin_summaries"].clear(),
        lambda result: result["acceptance"].pop("raw_full_rowwise_equality"),
        lambda result: result["census"]["rows"][0].__setitem__(
            "reference_path_mass", [1, 1]
        ),
        lambda result: result["census"]["rows"][0]["physical_accounting"].__setitem__(
            "realized_utility",
            result["census"]["rows"][0]["physical_accounting"]["realized_utility"]
            + 1,
        ),
        lambda result: result["census"]["rows"][0]["controllers"][
            "LAST_ACK_BAYES"
        ]["q_values"].__setitem__("LEFT", [999, 1]),
    ],
)
def test_publication_rejects_missing_duplicate_or_partial_nested_inventory(
    tmp_path: Path, mutate
):
    result = _complete_test_result()
    mutate(result)
    output_root = tmp_path / "TEST_ONLY_FORGED_COMPLETE_ROOT"
    with pytest.raises(ArtifactError, match="complete-result validation"):
        publish_complete_result(output_root, result)
    assert not output_root.exists()
    assert not list(tmp_path.glob(".*pending*"))


def test_describe_and_check_are_pre_result_only(tmp_path: Path, capsysbinary):
    assert main(["describe"]) == 0
    described = json.loads(capsysbinary.readouterr().out)
    assert described["registered_actions_evaluated"] == 0
    assert described["registered_returns_evaluated"] == 0

    spec_path = tmp_path / "RISP_ECR_R01_SPEC.json"
    spec_path.write_bytes(canonical_json_bytes(registered_spec()))
    receipt_path = tmp_path / "STRUCTURAL_CHECK.json"
    assert main(["check", "--spec", str(spec_path), "--output", str(receipt_path)]) == 0
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt["controller_actions_evaluated"] == 0
    assert receipt["controller_returns_evaluated"] == 0
    assert receipt["certification_executed"] is False


def test_cli_exposes_no_scientific_override_or_retry_surface():
    parser = build_parser()
    help_text = parser.format_help()
    for forbidden in (
        "--seed",
        "--witness",
        "--subset",
        "--duration",
        "--weight",
        "--tie",
        "--endpoint",
        "--threshold",
        "--retry",
        "--resume",
        "--legacy-result",
    ):
        assert forbidden not in help_text
    certify = parser.parse_args(["certify", "--spec", "S", "--output-root", "O"])
    assert vars(certify) == {
        "command": "certify",
        "spec": Path("S"),
        "output_root": Path("O"),
    }


def test_peak_rss_observation_is_available_on_the_runtime_platform():
    observed = _peak_rss_bytes()
    assert isinstance(observed, int)
    assert observed > 0


def test_atomic_check_output_refuses_existing_target(tmp_path: Path):
    target = tmp_path / "TEST_ONLY_RECEIPT.json"
    atomic_write_once(target, {"schema": "TEST_ONLY", "complete": True})
    with pytest.raises(ArtifactError, match="overwrite"):
        atomic_write_once(target, {"schema": "TEST_ONLY", "complete": True})
