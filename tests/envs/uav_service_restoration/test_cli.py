"""The command-line tools: help, invalid arguments, missing data, and one real round trip.

Every tool is invoked as a subprocess with this interpreter, exactly as the README
documents it, so the checks cover the argument parsing and the exit codes a user would
actually see.  The refusal cases are the important ones: a real-data configuration must
never quietly fall back to a fixture.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = ("inspect_data", "prepare_milan", "validate_dataset", "smoke", "evaluate_baselines")

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_DATA = 3


def _script(repo_root: Path, name: str) -> Path:
    return repo_root / "scripts" / "uav_service_restoration" / f"{name}.py"


def _run(repo_root: Path, name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_script(repo_root, name)), *args],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
        timeout=900,
    )


def _payload(completed: subprocess.CompletedProcess) -> dict:
    assert completed.stdout.strip(), f"no stdout; stderr={completed.stderr}"
    return json.loads(completed.stdout)


# --------------------------------------------------------------------------------------
# Help and argument validation
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", SCRIPTS)
def test_help_succeeds_and_names_the_tool(name, repo_root):
    completed = _run(repo_root, name, "--help")
    assert completed.returncode == EXIT_OK, completed.stderr
    assert f"{name}.py" in completed.stdout


@pytest.mark.parametrize("name", ("smoke", "evaluate_baselines"))
def test_a_configuration_is_mandatory(name, repo_root):
    """A fixture is never a hidden default: --config has no fallback value."""

    completed = _run(repo_root, name)
    assert completed.returncode == EXIT_USAGE
    assert "--config" in completed.stderr


def test_the_provenance_claim_is_mandatory(repo_root):
    """``prepare_milan`` must not be able to stamp a cache as real data by omission."""

    completed = _run(repo_root, "prepare_milan", "--input", "a", "--grid", "b", "--config", "c", "--output", "d")
    assert completed.returncode == EXIT_USAGE
    assert "--real-data" in completed.stderr and "--not-real-data" in completed.stderr


@pytest.mark.parametrize(
    ("name", "args", "expected"),
    [
        ("smoke", ("--steps", "0"), "--steps must be positive"),
        ("evaluate_baselines", ("--episodes", "0"), "--episodes must be positive"),
    ],
)
def test_invalid_numeric_arguments_are_refused(name, args, expected, repo_root, preset_dir):
    completed = _run(
        repo_root, name, "--config", str(preset_dir / "smoke_fixture.json"), *args
    )
    assert completed.returncode == EXIT_USAGE
    assert expected in completed.stderr


def test_an_unknown_controller_is_refused_by_the_parser(repo_root, preset_dir):
    completed = _run(
        repo_root,
        "evaluate_baselines",
        "--config",
        str(preset_dir / "smoke_fixture.json"),
        "--controllers",
        "oracle",
    )
    assert completed.returncode == EXIT_USAGE
    assert "invalid choice" in completed.stderr


# --------------------------------------------------------------------------------------
# Missing data
# --------------------------------------------------------------------------------------


def test_a_missing_configuration_file_is_a_data_error(repo_root):
    completed = _run(repo_root, "smoke", "--config", "configs/does_not_exist.json")
    assert completed.returncode == EXIT_DATA
    assert "not found" in completed.stderr


def test_a_missing_dataset_directory_is_a_data_error(repo_root):
    completed = _run(repo_root, "validate_dataset", "--dataset", "temp/does_not_exist")
    assert completed.returncode == EXIT_DATA
    assert "not found" in completed.stderr


def test_an_incomplete_cache_names_the_missing_file(repo_root, milan_sample_dir):
    """A directory without the completion marker is not a usable cache."""

    completed = _run(repo_root, "validate_dataset", "--dataset", str(milan_sample_dir))
    assert completed.returncode == EXIT_DATA
    assert "_PREPARED_COMPLETE.json" in completed.stderr


def test_a_milan_preset_without_a_prepared_cache_refuses(repo_root, preset_dir):
    """No synthetic fallback: the real-data preset raises instead of using a fixture."""

    completed = _run(
        repo_root, "smoke", "--config", str(preset_dir / "milan_rush_hour.json"), "--steps", "2"
    )
    assert completed.returncode == EXIT_DATA
    assert "a fixture is not a substitute" in completed.stderr


# --------------------------------------------------------------------------------------
# Real runs
# --------------------------------------------------------------------------------------


def test_smoke_runs_the_fixture_and_reports_zero_fits(repo_root, preset_dir, tmp_path):
    completed = _run(
        repo_root,
        "smoke",
        "--config",
        str(preset_dir / "smoke_fixture.json"),
        "--steps",
        "8",
        "--output",
        str(tmp_path / "smoke.json"),
    )
    assert completed.returncode == EXIT_OK, completed.stderr
    report = _payload(completed)
    assert report["training_fits_performed"] == 0
    assert report["optimizer_updates"] == 0
    assert report["data_status"] == "NOT_REAL_DATA"
    assert report["stepping"]["decision_steps_taken"] == 8
    assert report["api_test"]["performed"] is True
    assert report["shapes"]["obs_dim"] > 0 and report["shapes"]["state_dim"] > 0
    assert set(report["scheduler_status_counts"]) == {"optimal"}
    assert json.loads((tmp_path / "smoke.json").read_text(encoding="utf-8")) == report


def test_smoke_refuses_to_overwrite_an_existing_report(repo_root, preset_dir, tmp_path):
    output = tmp_path / "existing.json"
    output.write_text("{}", encoding="utf-8")
    completed = _run(
        repo_root,
        "smoke",
        "--config",
        str(preset_dir / "smoke_fixture.json"),
        "--steps",
        "2",
        "--skip-api-test",
        "--output",
        str(output),
    )
    assert completed.returncode == EXIT_USAGE
    assert "already exists" in completed.stderr
    assert output.read_text(encoding="utf-8") == "{}"


def test_evaluate_baselines_separates_the_controllers(repo_root, preset_dir):
    completed = _run(
        repo_root,
        "evaluate_baselines",
        "--config",
        str(preset_dir / "smoke_fixture.json"),
        "--episodes",
        "1",
        "--controllers",
        "static_uav",
        "backhaul_aware_greedy",
    )
    assert completed.returncode == EXIT_OK, completed.stderr
    report = _payload(completed)
    assert report["training_fits_performed"] == 0
    assert report["data_status"] == "NOT_REAL_DATA"
    static = report["controllers"]["static_uav"]
    aware = report["controllers"]["backhaul_aware_greedy"]
    assert static["n_recovered"] == 0 and static["n_censored"] == 1
    assert aware["controller_satisfaction_mean"] > static["controller_satisfaction_mean"]


def test_an_episodes_file_drives_the_seed_list(repo_root, preset_dir, tmp_path):
    episodes = tmp_path / "heldout.json"
    episodes.write_text(json.dumps({"episode_seeds": [11, 12]}), encoding="utf-8")
    completed = _run(
        repo_root,
        "evaluate_baselines",
        "--config",
        str(preset_dir / "smoke_fixture.json"),
        "--controllers",
        "static_uav",
        "--episodes-file",
        str(episodes),
    )
    assert completed.returncode == EXIT_OK, completed.stderr
    report = _payload(completed)
    assert report["episode_seeds"] == [11, 12]
    assert report["controllers"]["static_uav"]["n_episodes"] == 2


def test_inspect_data_verifies_the_declared_column_mapping(repo_root, milan_sample_dir):
    completed = _run(
        repo_root,
        "inspect_data",
        "--input",
        str(milan_sample_dir / "activity_2013-11-01.txt"),
        "--grid",
        str(milan_sample_dir / "grid_small.geojson"),
        "--config",
        str(milan_sample_dir / "preprocess_small.json"),
    )
    assert completed.returncode == EXIT_OK, completed.stderr
    report = _payload(completed)
    assert report["activity"]["column_count_matches_declared"] is True
    assert report["activity"]["timestamps_aligned_to_interval"] is True
    assert report["activity"]["distinct_country_codes"] >= 2
    assert report["grid"]["source_crs"].endswith("CRS84")
    # The grid must be projected into metres, not stretched: the fixture's cells are
    # deliberately kilometres apart so a degrees-as-metres bug would be obvious.
    assert 1000.0 < report["grid"]["nearest_neighbour_spacing_m"]["median"] < 5000.0


def test_a_fixture_derived_cache_round_trips_and_stays_marked_not_real(
    repo_root, milan_sample_dir, tmp_path
):
    """prepare -> validate -> refusal, on a self-authored fixture.

    This exercises the real-data *code path* end to end while proving the provenance flag
    survives it: the resulting cache is structurally ``VALID`` and still ``NOT_REAL_DATA``,
    and a ``milan_activity`` configuration refuses to open it.
    """

    cache = tmp_path / "fixture_cache"
    prepared = _run(
        repo_root,
        "prepare_milan",
        "--input",
        str(milan_sample_dir / "activity_2013-11-01.txt"),
        str(milan_sample_dir / "activity_2013-11-02.txt"),
        "--grid",
        str(milan_sample_dir / "grid_small.geojson"),
        "--config",
        str(milan_sample_dir / "preprocess_small.json"),
        "--output",
        str(cache),
        "--not-real-data",
    )
    assert prepared.returncode == EXIT_OK, prepared.stderr
    metadata = _payload(prepared)
    assert metadata["is_real_activity_data"] is False
    assert metadata["metadata"]["kind"] == "prepared_dataset"
    assert metadata["metadata"]["activity_reference_scale"] > 0.0

    validated = _run(repo_root, "validate_dataset", "--dataset", str(cache))
    assert validated.returncode == EXIT_OK, validated.stderr
    report = _payload(validated)
    assert report["verdict"] == "VALID"
    assert report["data_status"] == "NOT_REAL_DATA"
    assert all(report["checks"].values())
    assert report["splits"]["disjoint"] is True
    assert report["quality_report"]["missing_rows"] >= 0
    assert report["quality_report"]["n_missing_intervals"] > 0

    refused = _run(
        repo_root,
        "validate_dataset",
        "--dataset",
        str(cache),
        "--config",
        "configs/uav_service_restoration/milan_site_outage.json",
    )
    assert refused.returncode == EXIT_DATA
    refusal = _payload(refused)
    assert refusal["verdict"] == "INVALID"
    assert "never presented as real" in refusal["reason"]


def test_prepare_milan_refuses_a_duplicate_input_and_an_existing_output(
    repo_root, milan_sample_dir, tmp_path
):
    activity = str(milan_sample_dir / "activity_2013-11-01.txt")
    duplicate = _run(
        repo_root,
        "prepare_milan",
        "--input",
        activity,
        activity,
        "--grid",
        str(milan_sample_dir / "grid_small.geojson"),
        "--config",
        str(milan_sample_dir / "preprocess_small.json"),
        "--output",
        str(tmp_path / "dup"),
        "--not-real-data",
    )
    assert duplicate.returncode == EXIT_USAGE
    assert "never double-counted" in duplicate.stderr
    assert not (tmp_path / "dup").exists()

    existing = tmp_path / "already_there"
    existing.mkdir()
    occupied = _run(
        repo_root,
        "prepare_milan",
        "--input",
        activity,
        "--grid",
        str(milan_sample_dir / "grid_small.geojson"),
        "--config",
        str(milan_sample_dir / "preprocess_small.json"),
        "--output",
        str(existing),
        "--not-real-data",
    )
    assert occupied.returncode == EXIT_USAGE
    assert "already exists" in occupied.stderr
