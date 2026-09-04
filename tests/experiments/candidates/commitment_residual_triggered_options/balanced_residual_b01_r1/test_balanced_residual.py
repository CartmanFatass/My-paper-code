from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from experiments.candidates.commitment_residual_triggered_options.balanced_residual_b01_r1 import experiment
from scripts import run_crto_balanced_residual_b01_r1 as runner


def test_exact_selected_population_and_frozen_source_coordinates() -> None:
    rows = experiment.selected_population_spec()
    assert len(rows) == 64
    assert sum(row["split"] == "TRAIN" for row in rows) == 48
    assert sum(row["split"] == "EVAL" for row in rows) == 16
    assert sum(row["side"] == "KEEP" for row in rows) == 32
    assert sum(row["side"] == "REPLAN" for row in rows) == 32
    assert all(row["source_slot"] in range(8) and 832 <= row["episode_index"] <= 895
               for row in rows)
    assert all((row["prior_advantage"] <= -0.01 if row["side"] == "KEEP"
                else row["prior_advantage"] >= 0.01) for row in rows)
    expected_pairs = [
        ("EVAL", "COMMON-SENSOR", 50, (0, 867), (1, 887)),
        ("TRAIN", "COMMON-SENSOR", 66, (1, 861), (5, 852)),
        ("TRAIN", "COMMON-SENSOR", 82, (3, 868), (1, 867)),
        ("TRAIN", "COMMON-SENSOR", 98, (2, 858), (7, 864)),
        ("EVAL", "COMMON-SENSOR", 146, (3, 846), (1, 858)),
        ("TRAIN", "CUED-DIFFERENTIAL", 50, (2, 845), (5, 860)),
        ("TRAIN", "CUED-DIFFERENTIAL", 82, (5, 886), (3, 882)),
        ("TRAIN", "CUED-DIFFERENTIAL", 178, (6, 892), (4, 856)),
        ("EVAL", "NONE", 50, (5, 833), (7, 866)),
        ("TRAIN", "NONE", 66, (2, 883), (5, 871)),
        ("TRAIN", "NONE", 82, (0, 852), (6, 834)),
        ("TRAIN", "NONE", 98, (3, 832), (5, 842)),
        ("EVAL", "NONE", 146, (4, 838), (0, 850)),
        ("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 50, (4, 852), (0, 832)),
        ("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 66, (1, 893), (6, 835)),
        ("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 82, (1, 844), (4, 867)),
        ("EVAL", "UNANNOUNCED-DIFFERENTIAL", 98, (0, 870), (7, 879)),
        ("TRAIN", "COMMON-SENSOR", 50, (4, 832), (7, 853)),
        ("TRAIN", "COMMON-SENSOR", 66, (3, 890), (0, 849)),
        ("TRAIN", "COMMON-SENSOR", 82, (2, 836), (7, 839)),
        ("EVAL", "COMMON-SENSOR", 98, (6, 838), (1, 869)),
        ("TRAIN", "CUED-DIFFERENTIAL", 50, (6, 848), (0, 841)),
        ("TRAIN", "CUED-DIFFERENTIAL", 82, (6, 833), (1, 881)),
        ("TRAIN", "NONE", 50, (0, 875), (2, 834)),
        ("EVAL", "NONE", 66, (6, 888), (4, 846)),
        ("TRAIN", "NONE", 82, (4, 887), (1, 888)),
        ("TRAIN", "NONE", 98, (0, 877), (7, 888)),
        ("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 50, (2, 866), (6, 854)),
        ("EVAL", "UNANNOUNCED-DIFFERENTIAL", 66, (2, 888), (4, 868)),
        ("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 82, (0, 839), (6, 884)),
        ("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 50, (5, 840), (3, 847)),
        ("TRAIN", "UNANNOUNCED-DIFFERENTIAL", 66, (5, 841), (3, 872)),
    ]
    observed_pairs = []
    for keep, replan in zip(rows[0::2], rows[1::2]):
        observed_pairs.append((
            keep["split"], keep["event"], keep["onset"],
            (keep["source_slot"], keep["episode_index"]),
            (replan["source_slot"], replan["episode_index"]),
        ))
        assert keep["split"] == replan["split"]
        assert (keep["event"], keep["onset"]) == (replan["event"], replan["onset"])
    assert observed_pairs == expected_pairs
    assert experiment.SOURCE_NAMESPACE == 2026083192
    assert experiment.LEARNER_NAMESPACE == 2026090401


def test_selected_addresses_match_direct_evaluation_k8_source_manifests() -> None:
    observed = experiment.selected_source_manifest()
    assert len(observed) == 64
    assert all(row["observed_regime"] == "K8" for row in observed)
    assert all(row["observed_event"] == row["event"] for row in observed)
    assert all(row["observed_onset"] == row["onset"] for row in observed)
    assert all(row["observed_cost"] == 4.0 for row in observed)


def _metrics(values: dict[str, tuple[float, float]], *, competent: bool = True):
    result = {}
    for path in ("RAW", "TRUE_RESIDUAL", "CALIBRATED_DERANGEMENT"):
        result[path] = {}
        for budget, regret in zip(("SHORT", "LONG"), values[path]):
            exact = 8 if competent or path != "RAW" or budget != "LONG" else 5
            result[path][budget] = {
                "equal_side_regret": regret,
                "sides": {
                    side: {"row_count": 8, "mean_regret": regret,
                           "exact_action_count": exact}
                    for side in ("KEEP", "REPLAN")
                },
            }
    return result


@pytest.mark.parametrize(("values", "competent", "expected"), [
    ({"RAW": (.010, .001), "TRUE_RESIDUAL": (.000, .001),
      "CALIBRATED_DERANGEMENT": (.008, .001)}, True, "BR-A — ALIGNED_SHORT_ONLY"),
    ({"RAW": (.010, .005), "TRUE_RESIDUAL": (.000, .000),
      "CALIBRATED_DERANGEMENT": (.008, .004)}, True, "BR-B — PERSISTENT_ALIGNED_SIGNAL"),
    ({"RAW": (.010, .001), "TRUE_RESIDUAL": (.000, .001),
      "CALIBRATED_DERANGEMENT": (.001, .001)}, True, "BR-C — GENERIC_PREPROCESSING"),
    ({"RAW": (.001, .001), "TRUE_RESIDUAL": (.000, .000),
      "CALIBRATED_DERANGEMENT": (.010, .010)}, True, "BR-D — NO_TRUE_GAIN"),
    ({"RAW": (.010, .010), "TRUE_RESIDUAL": (.000, .000),
      "CALIBRATED_DERANGEMENT": (.008, .008)}, False, "BR-E — COMPARATOR_WEAK"),
    ({"RAW": (.010, .001), "TRUE_RESIDUAL": (.006, .006),
      "CALIBRATED_DERANGEMENT": (.010, .001)}, True, "BR-F — MIXED_OR_UNRESOLVED"),
])
def test_first_matching_result_rule(values, competent, expected) -> None:
    assert experiment.apply_result_rule(_metrics(values, competent=competent)) == expected
    assert experiment.apply_result_rule(
        _metrics(values, competent=competent), ["missing measurement"],
    ) == "INVALID_INCOMPLETE_NO_SCIENTIFIC_BRANCH"


def test_toy_runner_end_to_end_under_60_seconds(tmp_path: Path) -> None:
    receipt = tmp_path / "admission.json"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    receipt.write_text(json.dumps({
        "passed": True, "physical_floor_pass": True, "effective_floor_pass": True,
        "available_physical_bytes": 8 * 1024**3,
        "effective_available_bytes": 8 * 1024**3, "assessed_at": now,
    }), encoding="utf-8")
    output = tmp_path / "run"
    code = runner.main([
        "run", "--seed", "0", "--admission-receipt", str(receipt),
        "--output-dir", str(output), "--toy",
    ])
    assert code == 0
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["toy"] is True
    assert len(summary["launch_sha"]) == 40
    assert Path(summary["exact_argv"][1]).resolve() == Path(runner.__file__).resolve()
    assert summary["result_branch"] == "INVALID_INCOMPLETE_NO_SCIENTIFIC_BRANCH"
    assert set(summary["representations"]) == {
        "RAW", "TRUE_RESIDUAL", "CALIBRATED_DERANGEMENT",
    }
    assert summary["derangement_donor_maps"]["TRAIN"]
    assert summary["resources"]["wall_seconds"] < 60.0
