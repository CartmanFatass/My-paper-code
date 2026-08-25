from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

import pytest

from experiments.candidates.vsp_02 import crossed_physical_value_support as a2
from scripts import run_vsp02_a2_crossed_physical_value_support as runner


ROOT = Path(__file__).resolve().parents[4]
CLI = ROOT / "scripts" / "run_vsp02_a2_crossed_physical_value_support.py"


def _manifest(*, technical_only: bool = True):
    return a2.build_a2_manifest(
        source_revision="a" * 40,
        run_id="technical-test",
        technical_only=technical_only,
    )


def _report():
    return a2.run_physical_value_audit(_manifest())


def _with_deltas(delta_1: Fraction, delta_0: Fraction):
    report = deepcopy(_report())
    report["q_values"] = {
        "X_b=1|RELEASE": delta_1,
        "X_b=1|HOLD": Fraction(0),
        "X_b=0|RELEASE": delta_0,
        "X_b=0|HOLD": Fraction(0),
    }
    report["deltas"] = {"Delta_1": delta_1, "Delta_0": delta_0}
    for key, value in report["q_values"].items():
        report["cells"][key]["q_value"] = value
        report["cells"][key]["target"] = value
        report["cells"][key]["score"] = value
    return report


def test_manifest_is_prospective_exact_and_contains_no_result():
    manifest = _manifest()
    assert a2.validate_a2_manifest(manifest) == ()
    assert not ({"q_values", "deltas", "branch", "result"} & set(manifest))
    assert manifest["frozen_contract"]["cue"]["mapping"] == {
        "true": "X_b=1",
        "false": "X_b=0",
    }
    assert manifest["support_design"]["joint_support"] == {
        key: Fraction(1, 4) for key in a2.CELL_KEYS
    }
    round_tripped = json.loads(json.dumps(a2.json_ready(manifest), sort_keys=True))
    assert a2.validate_a2_manifest(round_tripped) == ()


def test_exact_four_fraction_cells_and_registered_component_signs():
    report = _report()
    assert tuple(report["q_values"]) == a2.CELL_KEYS
    assert all(isinstance(value, Fraction) for value in report["q_values"].values())
    assert report["q_values"] == {
        "X_b=1|RELEASE": Fraction(1),
        "X_b=1|HOLD": Fraction(-1),
        "X_b=0|RELEASE": Fraction(1),
        "X_b=0|HOLD": Fraction(2),
    }
    assert report["deltas"] == {
        "Delta_1": Fraction(2),
        "Delta_0": Fraction(-1),
    }
    assert report["branch"] == "A2_REGISTERED_STRICT_CROSSING_SUPPORTED"


def test_cue_and_action_support_witnesses_are_positive_legal_and_matched():
    report = _report()
    support = report["support"]
    assert support["cue_probability"] == {
        "X_b=1": Fraction(1, 2),
        "X_b=0": Fraction(1, 2),
    }
    assert all(value == Fraction(1, 2) for value in support["forced_action_propensity"].values())
    assert all(witness["legal"] is True for witness in support["witnesses"].values())
    for cue in a2.CueState:
        release = support["witnesses"][f"{cue.value}|RELEASE"]
        hold = support["witnesses"][f"{cue.value}|HOLD"]
        assert release["tape_id"] == hold["tape_id"]
        assert release["owner_id"] == hold["owner_id"] == "owner-A"
        assert release["owner_epoch"] == hold["owner_epoch"] == 17
        assert release["behavior_version"] == hold["behavior_version"] == 8


def test_lifecycle_and_target_score_semantics_are_action_exact():
    report = _report()
    for key, cell in report["cells"].items():
        assert cell["target"] == cell["score"] == report["q_values"][key]
        assert cell["observation"]["observation_clock"] < cell["observation"]["decision_clock"]
        assert cell["observation"]["a1_observation_firewall_valid"] is True
        if key.endswith("|RELEASE"):
            assert cell["lifecycle"]["postdecision_phase"] == "ENDED_RELEASE"
            assert cell["lifecycle"]["final_phase"] == "ENDED_RELEASE"
            assert cell["lifecycle"]["final_end_cause"] == "RELEASE"
        else:
            assert cell["lifecycle"]["postdecision_phase"] == "ACTIVE"
            assert cell["lifecycle"]["final_phase"] == "ENDED_NATURAL"
            assert cell["lifecycle"]["final_end_cause"] == "NATURAL"


def test_six_branch_precedence_is_exact_and_fail_closed():
    invalid = _with_deltas(Fraction(2), Fraction(-1))
    invalid["contract_checks"]["cue_source_is_predecision_only"] = False
    invalid["support"]["witnesses"] = {}
    assert a2.classify_a2(invalid) == "A2_INVALID_CONTRACT_OR_INFORMATION_LEAK"

    unsupported = _with_deltas(Fraction(2), Fraction(-1))
    unsupported["support"]["forced_action_propensity"]["X_b=0|HOLD"] = Fraction(0)
    assert a2.classify_a2(unsupported) == "A2_CUE_OR_ACTION_SUPPORT_ABSENT"

    assert a2.classify_a2(_with_deltas(Fraction(2), Fraction(-1))) == "A2_REGISTERED_STRICT_CROSSING_SUPPORTED"
    assert a2.classify_a2(_with_deltas(Fraction(-1), Fraction(2))) == "A2_REVERSED_STRICT_CROSSING"
    assert a2.classify_a2(_with_deltas(Fraction(1), Fraction(1))) == "A2_NONZERO_BUT_NOT_CROSSED"
    assert a2.classify_a2(_with_deltas(Fraction(0), Fraction(-1))) == "A2_NONZERO_BUT_NOT_CROSSED"
    assert a2.classify_a2(_with_deltas(Fraction(0), Fraction(0))) == "A2_BOTH_DELTAS_ZERO"


def test_swapping_registered_cue_labels_is_reversed_not_repaired():
    report = deepcopy(_report())
    original = report["q_values"]
    report["q_values"] = {
        "X_b=1|RELEASE": original["X_b=0|RELEASE"],
        "X_b=1|HOLD": original["X_b=0|HOLD"],
        "X_b=0|RELEASE": original["X_b=1|RELEASE"],
        "X_b=0|HOLD": original["X_b=1|HOLD"],
    }
    report["deltas"] = {
        "Delta_1": Fraction(-1),
        "Delta_0": Fraction(2),
    }
    for key, value in report["q_values"].items():
        report["cells"][key]["q_value"] = value
        report["cells"][key]["target"] = value
        report["cells"][key]["score"] = value
    assert a2.classify_a2(report) == "A2_REVERSED_STRICT_CROSSING"


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-cell",
        "non-fraction-cell",
        "delta-mismatch",
        "cue-relabel",
    ],
)
def test_contract_and_value_mutations_fail_closed(mutation):
    report = deepcopy(_report())
    if mutation == "missing-cell":
        del report["q_values"]["X_b=0|HOLD"]
    elif mutation == "non-fraction-cell":
        report["q_values"]["X_b=0|HOLD"] = 2.0
    elif mutation == "delta-mismatch":
        report["deltas"]["Delta_0"] = Fraction(1)
    else:
        manifest = _manifest()
        manifest["frozen_contract"]["cue"]["mapping"] = {
            "true": "X_b=0",
            "false": "X_b=1",
        }
        assert "frozen_contract mismatch" in a2.validate_a2_manifest(manifest)
        return
    assert a2.classify_a2(report) == "A2_INVALID_CONTRACT_OR_INFORMATION_LEAK"


def test_artifact_is_deterministic_tamper_evident_and_zero_runtime():
    manifest = _manifest()
    first = a2.run_a2_probe(manifest)
    second = a2.run_a2_probe(manifest)
    assert first == second
    assert a2.validate_a2_artifact(first) == ()
    round_tripped = json.loads(json.dumps(a2.json_ready(first), sort_keys=True))
    assert a2.validate_a2_artifact(round_tripped) == ()
    assert first["activity"]["registered_a_invocations"] == 0
    assert first["activity"]["exact_fraction_cells"] == 4
    for field in a2.ACTIVITY_ZERO_FIELDS:
        assert first["activity"][field] == 0

    tampered = deepcopy(first)
    tampered["report"]["q_values"]["X_b=1|RELEASE"] = Fraction(9)
    tampered["report"]["deltas"]["Delta_1"] = Fraction(10)
    assert "artifact differs from deterministic canonical reconstruction" in a2.validate_a2_artifact(tampered)


def test_runner_one_shot_writers_refuse_overwrite():
    with tempfile.TemporaryDirectory(prefix="vsp02-a2-test-") as temporary:
        root = Path(temporary)
        output = root / "artifact.json"
        runner._write_once(output, {"first": True})
        with pytest.raises(FileExistsError, match="refusing to overwrite"):
            runner._write_once(output, {"second": True})

        claim = root / "registered" / "registered_claim.json"
        runner._exclusive_claim(claim, {"claim": 1})
        with pytest.raises(FileExistsError):
            runner._exclusive_claim(claim, {"claim": 2})


@pytest.mark.parametrize("dependency_state", ["absent", "dirty"])
def test_registered_source_preflight_covers_immediate_a1_dependency(
    monkeypatch, dependency_state
):
    dependency = runner.RUNTIME_DEPENDENCY_PATHS[0]
    commands = []

    def fake_run(command, **kwargs):
        commands.append(tuple(command))
        if command[1] == "ls-files":
            paths = (
                runner.CLAIM_PATHS
                if dependency_state == "absent"
                else runner.REGISTERED_SOURCE_PATHS
            )
            return SimpleNamespace(stdout="\n".join(paths) + "\n")
        assert command[1] == "status"
        dirty = f" M {dependency}\n" if dependency_state == "dirty" else ""
        return SimpleNamespace(stdout=dirty)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    expected = "untracked or absent" if dependency_state == "absent" else "differs from HEAD"
    with pytest.raises(ValueError, match=expected):
        runner._require_clean_registered_sources()
    assert dependency in commands[0]
    if dependency_state == "dirty":
        assert dependency in commands[1]


def test_registered_source_failure_precedes_exclusive_claim(monkeypatch):
    manifest = _manifest(technical_only=False)
    claimed = False

    monkeypatch.setattr(runner, "_read_json", lambda path: manifest)
    monkeypatch.setattr(runner, "_require_source_revision", lambda value: None)

    def fail_source_preflight():
        raise ValueError("dirty immediate A1 runtime dependency")

    def forbidden_claim(path, payload):
        nonlocal claimed
        claimed = True

    monkeypatch.setattr(runner, "_require_clean_registered_sources", fail_source_preflight)
    monkeypatch.setattr(runner, "_exclusive_claim", forbidden_claim)
    args = SimpleNamespace(manifest=Path("unused.json"), run_root=Path("unused-run"))
    with pytest.raises(ValueError, match="dirty immediate A1 runtime dependency"):
        runner._registered_audit_command(args)
    assert claimed is False


def test_cli_help_is_available_without_consuming_registered_audit():
    completed = subprocess.run(
        [sys.executable, "-B", str(CLI), "--help"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "registered-audit" in completed.stdout
