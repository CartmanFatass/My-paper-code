"""Tests for the metric catalog.

These check the properties a later figure depends on: one declared reducer per kind of
quantity, ratios that name their components, the repository's real metric names covered,
and a refusal to silently redefine a name. The expected names and units are written as
literals taken from ``envs/uav_service_restoration/metrics.py`` and
``envs/uav_service_restoration/evaluation.py``, so the test fails if the catalog drifts
from the producing code rather than agreeing with it by construction.
"""

from __future__ import annotations

import pathlib
import re
import sys
from typing import Iterator

import pytest

# ``tests/tools/research_support/__init__.py`` makes this directory a package, so pytest puts
# ``tests/tools`` on ``sys.path``; the repository's own ``tools`` has no ``__init__.py`` and is
# therefore a namespace package whose portions are searched in ``sys.path`` order. Without the
# repository root first, ``tools.research_support`` would resolve to this *test* package. The
# reordering is local to the interpreter running the tests and touches no source file.
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)


from tools.research_support import catalog as cat
from tools.research_support.records import dumps, loads

# Scalar keys of envs/uav_service_restoration/metrics.py EpisodeAccumulator.summary() that
# carry a measurement. The remaining keys are per-point arrays, per-domain dictionaries or
# explanatory strings (offered_mbit_per_point, domain_peak_utilization, energy_status,
# scheduler_change_attribution, collision_avoidance, ...), which are not scalar metrics.
_SUMMARY_METRIC_KEYS = (
    "total_time_s",
    "offered_mbit_total",
    "delivered_mbit_total",
    "unmet_mbit_total",
    "mean_offered_mbps",
    "mean_delivered_mbps",
    "peak_unmet_mbps",
    "satisfaction_all",
    "satisfaction_affected",
    "disconnected_time_s_max",
    "flight_distance_m_total",
    "motion_effort_integral_s",
    "energy_joules",
    "max_constraint_residual",
    "scheduler_path_signature_changes",
    "scheduler_allocation_change_events",
    "min_uav_separation_m",
)

# evaluate_rollout()["references"] keys.
_REFERENCE_KEYS = (
    "healthy_no_uav_delivered_mbit",
    "failed_no_uav_delivered_mbit",
    "controller_delivered_mbit",
    "offered_mbit",
    "healthy_satisfaction",
    "failed_satisfaction",
    "controller_satisfaction",
)

# recovery_report() keys that are measurements. recovery_fraction_rho and
# recovery_sustain_s echo the configured recovery definition, "applicable" and "censored"
# are flags, so they are deliberately not metrics.
_RECOVERY_METRIC_KEYS = (
    "failure_start_s",
    "first_repair_s",
    "recovery_time_s",
    "time_to_recovery_s",
    "censoring_reason",
    "n_affected_points",
    "not_applicable_instants",
    "controller_delivered_mbit_affected",
    "failed_no_uav_delivered_mbit_affected",
    "healthy_delivered_mbit_affected",
    "improvement_over_no_uav_mbit",
    "fraction_of_lost_service_restored",
)


@pytest.fixture()
def isolated_catalog() -> Iterator[None]:
    """Restore the process-wide catalog, so a registration test cannot leak."""

    snapshot = dict(cat.DEFAULT_CATALOG)
    try:
        yield
    finally:
        cat.DEFAULT_CATALOG.clear()
        cat.DEFAULT_CATALOG.update(snapshot)


def test_every_definition_is_internally_consistent() -> None:
    assert cat.DEFAULT_CATALOG, "the catalog must be seeded"
    for name, defn in cat.DEFAULT_CATALOG.items():
        assert defn.name == name
        assert defn.direction in cat.DIRECTIONS
        assert defn.reducer in cat.REDUCERS
        assert defn.missingness_policy in cat.MISSINGNESS_POLICIES
        assert defn.unit, f"{name} must declare a unit"
        assert defn.description.strip(), f"{name} must describe itself"
        assert re.fullmatch(r"[a-z_]+\." + re.escape(name) + r"\.v\d+", defn.definition_id), (
            f"{name}: definition_id {defn.definition_id!r} must be "
            "<namespace>.<name>.v<version>"
        )
        expected_flag = {
            "higher_is_better": True,
            "lower_is_better": False,
            "neutral": None,
        }[defn.direction]
        assert defn.higher_is_better is expected_flag


def test_ratio_metrics_declare_components_that_resolve() -> None:
    ratios = [d for d in cat.DEFAULT_CATALOG.values() if d.reducer == "ratio_of_sums"]
    assert ratios, "the catalog must contain ratio metrics"
    for defn in ratios:
        assert defn.numerator in cat.DEFAULT_CATALOG, f"{defn.name}: numerator undeclared"
        assert defn.denominator in cat.DEFAULT_CATALOG, f"{defn.name}: denominator undeclared"
        assert defn.numerator != defn.denominator


def test_rates_volumes_ratios_extrema_and_labels_use_different_reducers() -> None:
    rate = cat.metric_definition("mean_delivered_mbps")
    volume = cat.metric_definition("delivered_mbit")
    ratio = cat.metric_definition("satisfaction_ratio")
    extremum = cat.metric_definition("peak_unmet_mbps")
    label = cat.metric_definition("team_skill_id")

    assert rate.unit == "Mbps" and rate.reducer == "mean"
    assert volume.unit == "Mbit" and volume.reducer == "sum"
    assert ratio.reducer == "ratio_of_sums"
    assert extremum.reducer == "median"
    assert label.reducer == "categorical"
    assert len({rate.reducer, volume.reducer, ratio.reducer, extremum.reducer, label.reducer}) == 5

    loss = cat.metric_definition("unmet_mbit")
    assert loss.direction == "lower_is_better" and loss.reducer == "sum"


@pytest.mark.parametrize(
    "name", _SUMMARY_METRIC_KEYS + _REFERENCE_KEYS + _RECOVERY_METRIC_KEYS
)
def test_repository_metric_names_are_declared(name: str) -> None:
    assert name in cat.DEFAULT_CATALOG, f"{name} is emitted by the environment but undeclared"


def test_required_seed_metrics_have_the_declared_semantics() -> None:
    for name in (
        "episode_reward_sum",
        "episode_reward_mean",
        "unmet_mbit",
        "delivered_mbit",
        "offered_mbit",
        "motion_effort_integral_s",
        "flight_distance_m",
    ):
        assert name in cat.DEFAULT_CATALOG

    for name in ("episode_reward_sum", "episode_reward_mean"):
        defn = cat.metric_definition(name)
        assert defn.unit == "native_reward"
        assert defn.direction == "neutral"
        assert "not a common performance scale" in defn.description.lower()
    assert cat.metric_definition("episode_reward_sum").reducer == "sum"
    assert cat.metric_definition("episode_reward_mean").reducer == "mean"

    ttr = cat.metric_definition("time_to_recovery_s")
    assert ttr.direction == "lower_is_better"
    assert ttr.higher_is_better is False
    assert ttr.valid_domain == (0.0, None)

    fraction = cat.metric_definition("recovery_fraction_at_deadline")
    assert fraction.reducer == "ratio_of_sums"
    assert fraction.valid_domain == (0.0, 1.0)

    satisfaction = cat.metric_definition("satisfaction_ratio")
    assert satisfaction.reducer == "ratio_of_sums"
    assert satisfaction.numerator == "delivered_mbit"
    assert satisfaction.denominator == "offered_mbit"
    assert satisfaction.valid_domain == (0.0, 1.0)


def test_energy_is_absent_by_design_not_estimated() -> None:
    energy = cat.metric_definition("energy_joules")
    assert energy.missingness_policy == "absent_by_design"
    assert "no battery" in energy.description.lower()


def test_valid_domain_membership() -> None:
    ratio = cat.metric_definition("satisfaction_ratio")
    assert ratio.contains(0.0)
    assert ratio.contains(1.0)
    assert not ratio.contains(-0.001)
    assert not ratio.contains(1.001)
    unbounded = cat.metric_definition("improvement_over_no_uav_mbit")
    assert unbounded.contains(-1e9) and unbounded.contains(1e9)


def test_lookup_raises_for_an_unknown_metric() -> None:
    assert cat.try_metric_definition("not_a_metric") is None
    with pytest.raises(cat.UnknownMetricError):
        cat.metric_definition("not_a_metric")
    assert issubclass(cat.UnknownMetricError, KeyError)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"direction": "bigger_is_nicer"},
        {"reducer": "average"},
        {"missingness_policy": "guess"},
        {"higher_is_better": False},  # contradicts direction="higher_is_better"
        {"reducer": "ratio_of_sums"},  # ratio without components
        {"numerator": "a", "denominator": "b"},  # components on a non-ratio reducer
        {"valid_domain": (1.0, 0.0)},  # empty domain
    ],
)
def test_definition_validation_refuses_incoherent_declarations(kwargs: dict) -> None:
    base = dict(
        name="probe",
        unit="Mbit",
        direction="higher_is_better",
        reducer="sum",
        definition_id="test.probe.v1",
        description="probe",
    )
    base.update(kwargs)
    with pytest.raises(ValueError):
        cat.MetricDefinition(**base)


def test_register_refuses_a_conflicting_redefinition(isolated_catalog: None) -> None:
    first = cat.MetricDefinition(
        name="probe_metric",
        unit="Mbit",
        direction="higher_is_better",
        reducer="sum",
        definition_id="test.probe_metric.v1",
        description="probe",
    )
    cat.register(first)
    assert cat.metric_definition("probe_metric") is first
    cat.register(first)  # identical re-registration is harmless

    conflicting = cat.MetricDefinition(
        name="probe_metric",
        unit="Mbps",
        direction="lower_is_better",
        reducer="mean",
        definition_id="test.probe_metric.v2",
        description="a different meaning for the same name",
    )
    with pytest.raises(ValueError):
        cat.register(conflicting)
    assert cat.metric_definition("probe_metric").unit == "Mbit"

    cat.register(conflicting, replace=True)
    assert cat.metric_definition("probe_metric").unit == "Mbps"


def test_json_payloads_are_strict_json() -> None:
    payload = cat.metric_definition("satisfaction_ratio").to_json()
    assert payload["valid_domain"] == {"min": 0.0, "max": 1.0}
    assert payload["numerator"] == "delivered_mbit"
    round_trip = loads(dumps(payload))
    assert round_trip["definition_id"] == "uavsr.satisfaction_ratio.v1"

    whole = loads(dumps(cat.catalog_to_json()))
    assert set(whole["metrics"]) == set(cat.DEFAULT_CATALOG)
    assert whole["vocabularies"]["reducers"] == sorted(cat.REDUCERS)
