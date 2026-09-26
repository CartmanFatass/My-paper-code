import inspect
import json
import os
from pathlib import Path
import subprocess

import numpy as np
import pytest

from scripts import run_skill_drift_unknown_law_b05 as b05
from scripts import run_skill_drift_unknown_law_b06 as b06
from tools.research_support.interpreters import (
    control_plane_interpreter,
    scientific_interpreter,
)


def synthetic_comparisons(primary_values):
    rows = []
    for seed, primary in zip(b06.SEEDS, primary_values):
        by_endpoint = {}
        for endpoint, offset in (("first64", 0.0), ("full", 0.01), ("late64", -0.01)):
            by_endpoint[endpoint] = {
                "response_minus_fingerprint_full": {
                    "task_value_difference": primary + offset,
                    "regret_difference": -(primary + offset),
                    "sign_mistake_difference": 0,
                },
                "response_minus_fingerprint_recent": {
                    "task_value_difference": primary + offset + 0.002,
                    "regret_difference": -(primary + offset + 0.002),
                    "sign_mistake_difference": 1,
                },
            }
        rows.append({"seed": seed, "by_endpoint": by_endpoint})
    return rows


def test_primary_reduction_uses_five_block_t_interval_and_fixed_rule():
    values = np.array([0.006, 0.007, 0.008, 0.009, 0.010])
    reduced = b06.reduce_confirmation(synthetic_comparisons(values))
    primary = reduced["primary"]
    mean = float(values.mean())
    sample_sd = float(values.std(ddof=1))
    half_width = b06.T95_DF4 * sample_sd / np.sqrt(5)
    assert primary["paired_values"] == values.tolist()
    assert primary["mean"] == pytest.approx(mean)
    assert primary["sample_sd"] == pytest.approx(sample_sd)
    assert primary["t95_interval"] == pytest.approx(
        [mean - half_width, mean + half_width]
    )
    assert primary["degrees_of_freedom"] == 4
    assert primary["critical_value"] == b06.T95_DF4
    assert primary["scale_flag"]
    assert primary["interval_lower_above_zero"]
    assert primary["proposed_support"]
    assert "approximately normal" in primary["small_n_assumption"]
    assert len(reduced["secondary"]) == 5
    assert all(
        row["role"] == "descriptive_only"
        for row in reduced["secondary"].values()
    )


@pytest.mark.parametrize(
    "values,scale,interval,support",
    [
        ([0.004] * 5, False, True, False),
        ([-0.02, 0.0, 0.01, 0.02, 0.04], True, False, False),
    ],
)
def test_proposed_support_requires_both_scale_and_positive_lower_bound(
    values, scale, interval, support
):
    primary = b06.reduce_confirmation(synthetic_comparisons(values))["primary"]
    assert primary["scale_flag"] is scale
    assert primary["interval_lower_above_zero"] is interval
    assert primary["proposed_support"] is support


def test_reduction_requires_each_fixed_seed_once_and_finite_values():
    rows = synthetic_comparisons([0.01] * 5)
    with pytest.raises(ValueError, match="five fixed seeds"):
        b06.reduce_confirmation(rows[:-1])
    rows[0]["by_endpoint"]["first64"]["response_minus_fingerprint_full"][
        "task_value_difference"
    ] = np.nan
    with pytest.raises(ValueError, match="finite"):
        b06.reduce_confirmation(rows)


def test_main_rejects_wrong_seed_and_digest_before_admission(monkeypatch, tmp_path):
    admission_calls = []
    monkeypatch.setattr(
        b06, "require_admission", lambda *args, **kwargs: admission_calls.append(True)
    )
    selection = tmp_path / "selection.json"
    selection.write_text("{}")
    base = [
        "--launch-sha",
        "a" * 40,
        "--out",
        str(tmp_path / "out"),
        "--selection",
        str(selection),
    ]
    with pytest.raises(SystemExit):
        b06.main(["--seeds", "1", *base])
    assert not admission_calls
    with pytest.raises(SystemExit):
        b06.main(["--seeds", *map(str, b06.SEEDS), *base])
    assert not admission_calls
    assert not (tmp_path / "out").exists()


def test_literal_guard_passes_actual_kernel_inspector():
    source = Path(b06.__file__)
    program = (
        "from pathlib import Path; import sys; "
        "from scripts.hmasd_launch import _validate_guard_contract; "
        "_validate_guard_contract(Path(sys.argv[1]), 'skill_teammate_drift_learning')"
    )
    checked = subprocess.run(
        [control_plane_interpreter(), "-B", "-c", program, str(source)],
        cwd=b05.ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert checked.returncode == 0, checked.stderr


def test_direct_script_help_resolves_repository_from_an_unrelated_directory(tmp_path):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    checked = subprocess.run(
        [scientific_interpreter(), "-B", str(Path(b06.__file__)), "--help"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert checked.returncode == 0, checked.stderr
    assert "--selection" in checked.stdout
    assert not list(tmp_path.iterdir())


def test_b05_publication_identity_default_is_preserved_and_b06_is_explicit(tmp_path):
    result = {
        "summary": {"counts": {"decision_fits": 1}},
        "common": {"reward": np.array([1], dtype=np.int8)},
        "fits": {
            "fixture": {
                "summary": {"movement": 0.1},
                "curves": {"greedy_action": np.array([0], dtype=np.int8)},
                "state": {"estimate": np.array([0.5])},
            }
        },
    }
    assert inspect.signature(b05.save_block).parameters["result_object"].default == b05.OBJECT
    (tmp_path / "b05").mkdir()
    (tmp_path / "b06").mkdir()
    b05.save_block(tmp_path / "b05", result, 1, "heldout", "a" * 40)
    b05.save_block(
        tmp_path / "b06",
        result,
        2,
        b06.STAGE,
        "b" * 40,
        result_object=b06.OBJECT,
    )
    old = json.loads((tmp_path / "b05" / "seed_1" / "summary.json").read_text())
    new = json.loads((tmp_path / "b06" / "seed_2" / "summary.json").read_text())
    new_fit = json.loads(
        (tmp_path / "b06" / "seed_2" / "fixture" / "summary.json").read_text()
    )
    assert (old["object"], old["stage"]) == (b05.OBJECT, "heldout")
    assert (new["object"], new["stage"]) == (b06.OBJECT, b06.STAGE)
    assert new_fit["object"] == b06.OBJECT


def test_wrapper_passes_fixed_identity_and_appends_reduction_without_fits(
    monkeypatch, tmp_path
):
    selection = tmp_path / "selection.json"
    selection.write_bytes(b"fixture")
    captured = {}

    monkeypatch.setattr(b06, "_fixed_selection_bytes", lambda path: path.read_bytes())
    monkeypatch.setattr(
        b06,
        "require_admission",
        lambda *args, **kwargs: {"sha": "a" * 40},
    )
    monkeypatch.setattr(
        b05,
        "resource_fields",
        lambda: {"runner_wall_seconds": 1.0, "runner_cpu_seconds": 0.5},
    )

    def fake_stage(args, admission, **kwargs):
        captured.update(args=args, admission=admission, kwargs=kwargs)
        args.out.mkdir()
        b05.write_json(
            args.out / "summary.json",
            {
                "object": kwargs["result_object"],
                "stage": kwargs["result_stage"],
                "status": "COMPLETE",
                "comparisons_by_seed": synthetic_comparisons([0.008] * 5),
            },
        )

    monkeypatch.setattr(b05, "run_stage", fake_stage)
    b06.main(
        [
            "--seeds",
            *map(str, b06.SEEDS),
            "--launch-sha",
            "a" * 40,
            "--out",
            str(tmp_path / "out"),
            "--selection",
            str(selection),
        ]
    )
    summary = json.loads((tmp_path / "out" / "summary.json").read_text())
    assert captured["args"].stage == "heldout"
    assert captured["args"].selection_sha256 == b06.SELECTION_SHA256
    assert captured["kwargs"]["result_object"] == b06.OBJECT
    assert captured["kwargs"]["result_stage"] == b06.STAGE
    assert captured["kwargs"]["batch_metadata"]["fixed_seeds"] == list(b06.SEEDS)
    assert summary["object"] == b06.OBJECT
    assert summary["stage"] == b06.STAGE
    assert summary["proposed_support"]
    assert summary["confirmation_reduction"]["primary"]["paired_values"] == [
        0.008
    ] * 5
    assert summary["runner_wall_seconds"] == 1.0


def test_reduction_failure_invalidates_complete_root_summary(monkeypatch, tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    b05.write_json(
        out / "summary.json", {"object": b06.OBJECT, "status": "COMPLETE"}
    )
    monkeypatch.setattr(
        b05,
        "resource_fields",
        lambda: {"runner_wall_seconds": 2.0, "runner_cpu_seconds": 1.0},
    )
    b06._mark_reduction_failure(out, RuntimeError("missing reduction"))
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "TECHNICAL_FAILURE"
    assert summary["reduction_error_type"] == "RuntimeError"
    assert summary["reduction_error"] == "missing reduction"
    assert summary["runner_wall_seconds"] == 2.0


def test_fixed_confirmation_identity_constants():
    assert b06.SEEDS == (95201, 95202, 95203, 95204, 95205)
    assert b06.SELECTION_SHA256 == (
        "ca32b21255d9bc60efb2c17fb1a7757d506d7fcaa49594db9a5ed9e3d3bd16e5"
    )
    assert b06.PRIMARY_ENDPOINT == "first64"
    assert b06.PRIMARY_REFERENCE == "fingerprint_full"
    assert b06.SECONDARY_REFERENCE == "fingerprint_recent"
    assert b06.SCALE_THRESHOLD == 0.005
    assert b06.T95_DF4 == 2.7764451051977987
