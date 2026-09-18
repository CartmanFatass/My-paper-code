"""Strict configuration decoding: unknown fields and unit errors must fail loudly."""

from __future__ import annotations

import json

import pytest

from envs.uav_service_restoration import ConfigError, config_from_dict, config_to_dict
from envs.uav_service_restoration.config import ENVIRONMENT_ID, SCHEMA_VERSION, load_config


def test_smoke_config_round_trips(smoke_config):
    document = config_to_dict(smoke_config)
    again = config_from_dict(document)
    assert config_to_dict(again) == document
    assert smoke_config.environment_id == ENVIRONMENT_ID
    assert smoke_config.schema_version == SCHEMA_VERSION


def test_unknown_top_level_field_is_rejected(config_doc):
    config_doc["learning_rate"] = 3e-4
    with pytest.raises(ConfigError, match="unknown fields"):
        config_from_dict(config_doc)


def test_unknown_nested_field_is_rejected(config_doc):
    config_doc["network"]["radio_models"]["site_access"]["shadowing_sigma_db"] = 4.0
    with pytest.raises(ConfigError, match="unknown fields"):
        config_from_dict(config_doc)


def test_misspelled_field_does_not_silently_use_a_default(config_doc):
    config_doc["observations"]["telemetry_dely_s"] = 5.0
    with pytest.raises(ConfigError, match="telemetry_dely_s"):
        config_from_dict(config_doc)


@pytest.mark.parametrize(
    "path,value,message",
    [
        (("n_uavs",), 0, "n_uavs"),
        (("episode", "physics_dt_s"), 30.0, "physics_dt_s"),
        (("episode", "duration_s"), 615.0, "integer multiple"),
        (("source", "demand_scale_mbps"), -1.0, "demand_scale_mbps"),
        (("dynamics", "max_speed_mps"), 0.0, "max_speed_mps"),
        (("observations", "telemetry_ttl_s"), 0.0, "telemetry_ttl_s"),
        (("reward", "reference_scale_mbps"), 0.0, "reference_scale_mbps"),
        (("network", "max_backhaul_hops"), -1, "max_backhaul_hops"),
        (("scheduler", "secondary_weight"), 0.5, "secondary_weight"),
        (("evaluation", "recovery_fraction_rho"), 1.5, "recovery_fraction_rho"),
    ],
)
def test_out_of_range_values_are_rejected(config_doc, path, value, message):
    target = config_doc
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ConfigError, match=message):
        config_from_dict(config_doc)


def test_activity_sum_is_refused(config_doc):
    config_doc["source"]["activity_field"] = "sms_plus_call_plus_internet"
    with pytest.raises(ConfigError, match="activity_field"):
        config_from_dict(config_doc)


def test_real_data_kind_requires_a_dataset_root(config_doc):
    config_doc["source"]["kind"] = "milan_activity"
    with pytest.raises(ConfigError, match="dataset_root is required"):
        config_from_dict(config_doc)


def test_fixture_kind_refuses_a_dataset_root(config_doc):
    config_doc["source"]["dataset_root"] = "somewhere"
    with pytest.raises(ConfigError, match="dataset_root must not be set"):
        config_from_dict(config_doc)


def test_motion_weight_requires_a_rationale(config_doc):
    config_doc["reward"]["motion_weight"] = 0.1
    with pytest.raises(ConfigError, match="motion_weight_rationale"):
        config_from_dict(config_doc)
    config_doc["reward"]["motion_weight_rationale"] = "probing the motion/service trade-off"
    assert config_from_dict(config_doc).reward.motion_weight == pytest.approx(0.1)


def test_ideal_demand_diagnostic_requires_recorded_notes(config_doc):
    config_doc["observations"]["mode"] = "ideal_full_current_demand"
    config_doc["notes"] = ""
    with pytest.raises(ConfigError, match="diagnostic"):
        config_from_dict(config_doc)


def test_sites_must_lie_inside_the_region(config_doc):
    config_doc["network"]["sites"][0]["position_m"] = [9999.0, 1500.0, 25.0]
    with pytest.raises(ConfigError, match="outside the configured region"):
        config_from_dict(config_doc)


def test_deployment_altitude_must_respect_the_flight_box(config_doc):
    config_doc["deployment"]["positions_m"][0] = [1500.0, 1500.0, 5.0]
    with pytest.raises(ConfigError, match="altitude"):
        config_from_dict(config_doc)


def test_deployment_position_count_must_match_n_uavs(config_doc):
    config_doc["deployment"]["positions_m"] = config_doc["deployment"]["positions_m"][:2]
    with pytest.raises(ConfigError, match="exactly n_uavs"):
        config_from_dict(config_doc)


def test_reactive_launch_requires_standby_positions(config_doc):
    config_doc["deployment"]["mode"] = "reactive_launch"
    with pytest.raises(ConfigError, match="standby_positions_m"):
        config_from_dict(config_doc)


def test_event_site_index_must_exist(config_doc):
    config_doc["events"]["events"][0]["site_index"] = 7
    with pytest.raises(ConfigError, match="unknown site index"):
        config_from_dict(config_doc)


def test_missing_radio_class_is_rejected(config_doc):
    config_doc["network"]["radio_models"].pop("uav_uav_backhaul")
    with pytest.raises(ConfigError, match="missing classes"):
        config_from_dict(config_doc)


def test_calibration_status_is_reported_separately(smoke_config):
    summary = smoke_config.calibration_summary()
    assert set(summary) == {"empirically_calibrated", "engineering_assumptions"}
    # Nothing in the shipped fixture preset claims empirical calibration.
    assert summary["empirically_calibrated"] == []
    assert any("radio_models" in entry for entry in summary["engineering_assumptions"])


def test_bad_json_and_missing_file_report_the_path(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "absent.json")
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid JSON"):
        load_config(broken)


def test_type_errors_are_rejected(config_doc):
    config_doc["n_uavs"] = "three"
    with pytest.raises(ConfigError, match="must be an integer"):
        config_from_dict(config_doc)


# The preprocessing reference lives in the same directory but is a *preprocessing*
# configuration, loaded by a different strict decoder.  It is named here rather than
# filtered by a guess, so adding a preset cannot silently skip it.
NON_ENVIRONMENT_PRESETS = frozenset({"preprocess_milan_reference.json"})


def test_shipped_presets_all_load(preset_dir):
    from envs.uav_service_restoration.config import load_config as loader

    presets = sorted(
        path for path in preset_dir.glob("*.json") if path.name not in NON_ENVIRONMENT_PRESETS
    )
    assert presets, "no presets found"
    for path in presets:
        document = json.loads(path.read_text(encoding="utf-8"))
        assert "source" in document, f"{path.name} declares no source"
        config = loader(path)
        if document["source"]["kind"] != "synthetic_fixture":
            # A real-data preset must demand an explicit dataset; loading the document
            # itself must still succeed so the preset is checkable offline.
            assert config.source.dataset_root, path.name


def test_the_preprocessing_reference_loads_with_its_own_decoder(preset_dir):
    """The one non-environment document in the preset directory is still validated."""

    from envs.uav_service_restoration.preprocess_milan import load_preprocess_config

    path = preset_dir / "preprocess_milan_reference.json"
    assert path.is_file()
    config = load_preprocess_config(path)
    assert config.activity_field == "internet"
    assert config.interval_duration_ms == 600_000
    assert config.columns.n_columns >= 5
    assert config.split_of_date is not None
