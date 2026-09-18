"""Scenario report tests: static means static, and an executed value says so.

Two properties carry the weight here:

* with ``execute=False`` nothing is constructed - the environment class is monkeypatched to
  raise, and the diagnostic probe is replaced by a function that fails the test if it is
  called - and every runtime quantity comes back UNKNOWN with a reason;
* with ``execute=True`` the observed quantities are marked ``verified_runtime``, the bounded
  run announces ``optimizer updates : 0`` first, and a run that hits its step cap reports the
  episode length as unverified rather than as the number of steps that happened to run.

The executed tests use the committed self-contained smoke preset with a small step budget,
so they exercise the real environment without becoming a long job.
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

from tools.research_support import scenario_report as scenario_module  # noqa: E402
from tools.research_support.cli import CliError  # noqa: E402
from tools.research_support.scenario_report import (  # noqa: E402
    NOT_EXECUTED_REASON,
    PROVENANCE_DECLARED_ONLY,
    PROVENANCE_WITH_RUNTIME,
    SCENARIO_REPORT_SCHEMA,
    inspect_scenario,
    scenario_report,
)

SMOKE_CONFIG = _REPO_ROOT / "configs" / "uav_service_restoration" / "smoke_fixture.json"
MILAN_CONFIG = _REPO_ROOT / "configs" / "uav_service_restoration" / "milan_site_outage.json"


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------


def _quantity(report, name):
    return next(item for item in report.runtime if item.name == name)


def _declared(report, name):
    return next(item for item in report.declared_fields if item.name == name)


def _short_config(tmp_path: Path, *, duration_s: float = 40.0) -> Path:
    """The committed smoke preset with a shorter episode, so a full episode is cheap."""

    payload = json.loads(SMOKE_CONFIG.read_text(encoding="utf-8"))
    payload["episode"]["duration_s"] = duration_s
    path = tmp_path / "short_smoke.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.fixture
def forbid_execution(monkeypatch):
    """Make any in-process construction or child probe a loud failure."""

    import envs.uav_service_restoration.env as env_module

    def _constructed(*args, **kwargs):
        raise AssertionError("the environment must not be constructed by a static report")

    def _probed(*args, **kwargs):
        raise AssertionError("the diagnostic probe must not run for a static report")

    monkeypatch.setattr(env_module, "UAVServiceRestorationEnv", _constructed)
    monkeypatch.setattr(scenario_module, "run_diagnostic_probe", _probed)


# --------------------------------------------------------------------------------------
# Refusals
# --------------------------------------------------------------------------------------


def test_missing_config_is_refused(tmp_path):
    with pytest.raises(CliError) as error:
        inspect_scenario(config_path=tmp_path / "no_such_config.json")
    assert "not found" in str(error.value)
    assert "No preset is substituted" in str(error.value)


def test_foreign_environment_id_is_refused(tmp_path):
    path = tmp_path / "other.json"
    path.write_text(json.dumps({"environment_id": "some_other_env_v3"}), encoding="utf-8")
    with pytest.raises(CliError) as error:
        inspect_scenario(config_path=path)
    assert "uav_service_restoration_v0" in str(error.value)


def test_missing_episodes_file_is_refused(tmp_path):
    with pytest.raises(CliError) as error:
        inspect_scenario(config_path=SMOKE_CONFIG, episodes_file=tmp_path / "seeds.json")
    assert "not an empty one" in str(error.value)


def test_real_data_config_refuses_to_execute_without_a_dataset():
    declared_root = _REPO_ROOT / "prepared_datasets" / "milan_internet_v1"
    if declared_root.is_dir():
        pytest.skip("the declared Milan cache exists in this checkout; the refusal cannot fire")
    with pytest.raises(CliError) as error:
        inspect_scenario(config_path=MILAN_CONFIG, execute=True)
    assert "no synthetic fallback" in str(error.value)


def test_real_data_config_still_reports_statically_without_a_dataset():
    report = inspect_scenario(config_path=MILAN_CONFIG)
    assert report.provenance == PROVENANCE_DECLARED_ONLY
    assert report.dataset["status"] == "not_provided"
    assert report.dataset["used_by_this_scenario"] is True
    assert report.dataset["declared_dataset_root"]


# --------------------------------------------------------------------------------------
# Static mode
# --------------------------------------------------------------------------------------


def test_static_report_executes_nothing(forbid_execution, tmp_path):
    path = scenario_report(
        config_path=SMOKE_CONFIG,
        dataset=None,
        episodes_file=None,
        output_dir=tmp_path / "out",
        execute=False,
    )
    payload = json.loads((path.parent / "scenario_report.json").read_text(encoding="utf-8"))
    assert payload["schema"] == SCENARIO_REPORT_SCHEMA
    assert payload["provenance"] == PROVENANCE_DECLARED_ONLY
    assert payload["diagnostic_set"]["status"] == "not_run"
    assert payload["diagnostic_set"]["optimizer_updates"] == 0
    assert payload["diagnostic_set"]["formal_training_fits"] == 0


def test_static_report_marks_every_runtime_quantity_unknown(forbid_execution):
    report = inspect_scenario(config_path=SMOKE_CONFIG)
    assert report.runtime, "the static report must name the holes, not omit them"
    for item in report.runtime:
        assert item.value.value is None
        assert item.value.validity.value == "unknown"
        assert item.value.reason == NOT_EXECUTED_REASON
        assert item.provenance == PROVENANCE_DECLARED_ONLY
    for name in ("episode_length_steps", "n_episodes_truncated", "uav_altitude_max_m",
                 "n_non_finite_rewards", "dataset_hash_at_runtime"):
        assert _quantity(report, name).value.validity.value == "unknown"


def test_static_report_reads_the_declared_scenario(forbid_execution):
    report = inspect_scenario(config_path=SMOKE_CONFIG)

    assert report.preset_name == "smoke_fixture"
    assert report.config_hash.startswith("sha256:")
    assert _declared(report, "n_uavs").effective.value == 3
    assert _declared(report, "episode.duration_s").effective.value == pytest.approx(600.0)
    assert _declared(report, "derived.n_decision_steps").effective.value == 60
    assert _declared(report, "derived.region_extent_x_m").effective.value == pytest.approx(3000.0)
    assert _declared(report, "dynamics.altitude_range_m").effective.value == "[90.0, 160.0]"
    assert _declared(report, "observations.telemetry_ttl_s").effective.unit == "s"

    assert report.entities["n_uavs_declared"] == 3
    assert report.entities["n_terrestrial_sites_declared"] == 2
    assert [site["site_id"] for site in report.entities["sites"]] == ["site_west", "site_east"]

    # Aggregate demand points are labelled as aggregates, and their true count is unknown
    # until something runs.
    demand_points = report.entities["aggregate_demand_points"]
    assert demand_points["entity_kind"] == "aggregate_demand_point"
    assert "not a person" in demand_points["label_rule"]
    assert demand_points["actual_count"]["value"] is None
    assert demand_points["actual_count"]["validity"] == "unknown"


def test_static_report_reads_the_failure_schedule(forbid_execution):
    report = inspect_scenario(config_path=SMOKE_CONFIG)
    schedule = report.failure_schedule
    assert schedule["source_kind"] == "explicit"
    assert schedule["n_declared_events"] == 1
    event = schedule["events"][0]
    assert event["event_type"] == "full_site_failure"
    assert event["site_id"] == "site_east"
    # A point range is a fixed time and is recorded; a sampling range would be unknown.
    assert event["realised_time_s"]["validity"] == "ok"
    assert event["realised_time_s"]["value"] == pytest.approx(120.0)
    assert event["never_repaired_within_episode"] is True


def test_static_report_reads_radio_parameters_and_their_calibration(forbid_execution):
    report = inspect_scenario(config_path=SMOKE_CONFIG)
    classes = {model["link_class"] for model in report.radio_models}
    assert {"site_access", "uav_access", "site_uav_backhaul", "uav_uav_backhaul"} <= classes
    access = next(m for m in report.radio_models if m["link_class"] == "uav_access")
    assert access["bandwidth_hz"]["value"] == pytest.approx(20_000_000.0)
    assert access["bandwidth_hz"]["unit"] == "Hz"
    assert access["calibration_status"]["value"] == "engineering_assumption"
    assert report.calibration["empirically_calibrated"] == []
    assert report.calibration["engineering_assumptions"]
    assert any("engineering assumption" in note for note in report.notes)


def test_static_report_records_the_episode_list_and_its_statistical_unit(
    forbid_execution, tmp_path
):
    episodes = tmp_path / "heldout.json"
    episodes.write_text(json.dumps({"episode_seeds": [5, 6, 6]}), encoding="utf-8")
    report = inspect_scenario(config_path=SMOKE_CONFIG, episodes_file=episodes)

    assert report.episodes_file["n_seeds"] == 3
    assert report.episodes_file["n_duplicated_seeds"] == 1
    assert any("repeated" in text for text in report.errors)
    assert "not independent replicates" in report.episodes_file["note"]

    units = report.statistical_units
    assert units["n_scenario_configurations"] == 1
    assert units["dispersion_across_scenarios"]["value"] is None
    assert units["dispersion_across_scenarios"]["validity"] == "not_applicable"
    assert "not zero-width" in units["dispersion_across_scenarios"]["reason"]
    assert units["dispersion_across_episodes"]["status"] == "absent"


def test_a_dataset_beside_a_fixture_config_is_not_claimed_to_be_used(
    forbid_execution, tmp_path
):
    cache = tmp_path / "cache"
    cache.mkdir()
    report = inspect_scenario(config_path=SMOKE_CONFIG, dataset=cache)
    assert report.dataset["used_by_this_scenario"] is False
    assert any("is NOT read by this scenario" in text for text in report.warnings)
    # An unreadable path is reported as unreadable rather than silently ignored.
    assert report.dataset["status"] == "unreadable"


# --------------------------------------------------------------------------------------
# Executed mode
# --------------------------------------------------------------------------------------


def test_execute_marks_observed_quantities_verified_runtime(tmp_path, capsys):
    config = _short_config(tmp_path)
    report = inspect_scenario(
        config_path=config, execute=True, episodes=1, max_steps=20, output_dir=tmp_path
    )

    announced = capsys.readouterr().err
    assert "EXECUTION SCOPE" in announced
    assert "optimizer updates   : 0" in announced
    assert "formal training fits: 0" in announced

    assert report.provenance == PROVENANCE_WITH_RUNTIME
    assert report.diagnostic_set["status"] == "ok"
    assert report.diagnostic_set["episodes_executed"] == 1

    agents = _quantity(report, "n_agents")
    assert agents.provenance == "verified_runtime"
    assert agents.value.value == 3
    assert agents.agreement == "match"

    length = _quantity(report, "episode_length_steps")
    assert length.provenance == "verified_runtime"
    assert length.value.value == 4
    assert length.agreement == "match"

    boundary = _quantity(report, "boundary_kind_at_horizon")
    assert boundary.value.value == "truncation"
    assert boundary.agreement == "match"

    slots = _quantity(report, "n_aggregate_demand_slots")
    assert slots.value.value == 9
    assert slots.agreement == "within_declared_bound"
    assert "not people" in slots.note

    for name in ("n_non_finite_observation_vectors", "n_non_finite_state_vectors",
                 "n_non_finite_rewards", "n_action_shape_violations",
                 "n_action_range_violations", "n_non_finite_actions"):
        item = _quantity(report, name)
        assert item.value.validity.value == "ok"
        assert item.value.value == 0

    assert _quantity(report, "optimizer_updates").value.value == 0
    assert _quantity(report, "checkpoints_loaded").value.value == 0
    assert _quantity(report, "torch_imported").value.value is False
    assert _quantity(report, "is_real_activity_data").value.value is False
    assert report.errors == []


def test_execute_reports_bounds_and_identity_from_the_run(tmp_path):
    config = _short_config(tmp_path)
    report = inspect_scenario(config_path=config, execute=True, episodes=1, max_steps=20)

    for name in ("uav_x_min_m", "uav_x_max_m", "uav_y_min_m", "uav_y_max_m",
                 "uav_altitude_min_m", "uav_altitude_max_m"):
        item = _quantity(report, name)
        assert item.value.validity.value == "ok"
        assert item.agreement == "within_declared_bound"
    speed = _quantity(report, "max_interval_mean_speed_mps")
    assert speed.agreement == "within_declared_bound"
    assert "decision-interval average" in speed.note

    assert _quantity(report, "episode_split").agreement == "match"
    assert _quantity(report, "dataset_hash_at_runtime").value.validity.value == "ok"
    assert _quantity(report, "scheduler_status").value.value == "optimal"
    assert "full_site_failure" in str(_quantity(report, "realised_event_times_s").value.value)


def test_a_capped_run_does_not_claim_the_episode_length(tmp_path):
    report = inspect_scenario(config_path=SMOKE_CONFIG, execute=True, episodes=1, max_steps=3)

    steps = _quantity(report, "episode_steps_observed")
    assert steps.value.value == 3

    length = _quantity(report, "episode_length_steps")
    assert length.value.value is None
    assert length.value.validity.value == "unknown"
    assert "lower bound" in length.value.reason
    assert any("step cap" in text for text in report.warnings)


def test_a_failed_diagnostic_run_is_never_a_pass(monkeypatch, tmp_path):
    def _failed(**kwargs):
        return "failed", {"returncode": 1, "stderr_tail": "DemandDataError: dataset_root missing"}

    monkeypatch.setattr(scenario_module, "run_diagnostic_probe", _failed)
    report = inspect_scenario(
        config_path=SMOKE_CONFIG, execute=True, episodes=1, max_steps=3, output_dir=tmp_path
    )

    assert report.provenance == PROVENANCE_DECLARED_ONLY
    assert report.diagnostic_set["status"] == "failed"
    assert any("did not complete" in text for text in report.errors)
    for item in report.runtime:
        assert item.value.value is None
        assert item.value.validity.value == "missing_artifact"
        assert "diagnostic run failed" in item.value.reason


# --------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------


def test_report_writes_json_and_html_and_returns_the_html(forbid_execution, tmp_path):
    output = tmp_path / "out"
    path = scenario_report(
        config_path=SMOKE_CONFIG,
        dataset=None,
        episodes_file=None,
        output_dir=output,
        execute=False,
    )
    assert path == output / "scenario_report.html"
    assert path.is_file()
    payload = json.loads((output / "scenario_report.json").read_text(encoding="utf-8"))
    assert payload["report_content_hash"].startswith("sha256:")
    assert payload["config_path"].endswith("smoke_fixture.json")


def test_html_is_self_contained_and_says_nothing_ran(forbid_execution, tmp_path):
    path = scenario_report(
        config_path=SMOKE_CONFIG,
        dataset=None,
        episodes_file=None,
        output_dir=tmp_path / "out",
        execute=False,
    )
    html = path.read_text(encoding="utf-8")

    assert "http://" not in html
    assert "https://" not in html
    for fragment in ("<script", "<link ", "<img ", "@import", "url("):
        assert fragment not in html
    assert "DECLARED ONLY" in html
    assert "an unknown is not a passed check" in html.lower()
