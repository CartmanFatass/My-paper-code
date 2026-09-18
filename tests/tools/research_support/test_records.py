"""Contract tests for ``tools/research_support/records.py``.

The invariants checked here are the ones the rest of the suite depends on:

* a value is readable only when its :class:`Validity` says so, and a *measured zero* is
  never confusable with a missing number;
* identity survives array-slot reuse, so a departing entity cannot inherit the history of
  a later arrival;
* a link is identified by its endpoints, not by a solver enumeration index that is local
  to one solve;
* the JSON encoding is strict (no ``NaN``/``Infinity`` tokens) and hashes are stable.

The numbers and messages asserted here are read from the module under test, except where a
literal is the contract itself (schema strings, refusal wording), which is deliberate: a
silent change to those must fail a test rather than agree with itself.
"""

from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import pytest

# The repository's ``tools`` package must win over anything on the test path. This mirrors
# the guard the sibling test modules use and touches no source file.
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[3])
if _REPO_ROOT in sys.path:
    sys.path.remove(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)

from tools.research_support import records as R  # noqa: E402


# --------------------------------------------------------------------------------------
# Fixture frame
# --------------------------------------------------------------------------------------


def _scene_frame() -> R.SceneFrame:
    """A small but complete, contract-valid frame."""

    registry = R.LifetimeRegistry()
    registry.observe(R.EntityKind.UAV, [0])
    registry.observe(R.EntityKind.SITE, [0])
    registry.observe(R.EntityKind.AGGREGATE_DEMAND_POINT, [0, 1])

    uav = registry.entity(R.EntityKind.UAV, 0, label="uav-0")
    site = registry.entity(R.EntityKind.SITE, 0, label="site-0")
    cell_a = registry.entity(R.EntityKind.AGGREGATE_DEMAND_POINT, 0, label="cell-0")
    cell_b = registry.entity(R.EntityKind.AGGREGATE_DEMAND_POINT, 1, label="cell-1")

    link_key = R.canonical_link_key(uav, cell_a, "uav_access", resource_domain="uav_0_access")
    link = R.LinkRecord(
        link_key=link_key,
        source=uav,
        target=cell_a,
        link_class="uav_access",
        activity=R.LinkActivity.ACTIVE,
        capacity_mbps=R.Measured.ok(20.0, unit="Mbps"),
        flow_mbps=R.Measured.ok(0.0, unit="Mbps"),
        utilization=R.Measured.ok(0.0),
        resource_domain="uav_0_access",
        producer_local_id=7,
    )
    return R.SceneFrame(
        identity=R.SceneIdentity(
            run_id="run-1",
            trace_id="trace-1",
            episode_id="ep-1",
            world_id="world-1",
            lane_id=0,
            sequence=3,
        ),
        clock=R.SceneClock(
            simulation_time_s=12.5,
            geometry_time_s=12.5,
            decision_step=5,
            capture_wall_time_utc="2026-09-18T00:00:00Z",
            producer_monotonic_s=1.0,
            measurement_start_s=12.0,
            measurement_end_s=12.5,
        ),
        provenance=R.SceneProvenance(
            route="unit_test",
            environment_id="fixture",
            source_kind=R.SourceKind.SYNTHETIC_FIXTURE,
            policy_kind=R.PolicyKind.RULE_CONTROLLER,
            information_condition="privileged_truth",
            frame_kind=R.FrameKind.TRANSITION,
            capture_resolution="decision_boundary",
        ),
        geometry=R.SceneGeometry(bounds_m=(0.0, 0.0, 1000.0, 1000.0)),
        capability=R.SceneCapability(
            has_uav_positions=True, has_aggregate_demand=True, has_links=True
        ),
        uavs=(R.UavState(entity=uav, position_m=(100.0, 100.0, 120.0)),),
        ground_entities=(
            R.GroundEntityState(
                entity=cell_a,
                position_m=(300.0, 300.0, 0.0),
                offered_mbps=R.Measured.ok(0.0, unit="Mbps"),
                delivered_mbps=R.Measured.ok(0.0, unit="Mbps"),
                service_status="zero_demand",
            ),
            R.GroundEntityState(
                entity=cell_b,
                position_m=(700.0, 400.0, 0.0),
                offered_mbps=R.Measured.unknown("not_observed"),
                service_status="unknown_demand",
            ),
        ),
        sites=(R.SiteStateRecord(entity=site, position_m=(500.0, 500.0, 25.0)),),
        links=(link,),
        paths=(
            R.PathRecord(
                demand_entity=cell_a.key,
                node_keys=(uav.key, cell_a.key),
                link_keys=(link_key,),
                backhaul_hops=0,
                selected=True,
            ),
        ),
        interval_metrics={"delivered_mbps": R.Measured.ok(0.0, unit="Mbps")},
    )


# --------------------------------------------------------------------------------------
# Measured
# --------------------------------------------------------------------------------------


def test_ok_without_a_value_is_refused() -> None:
    with pytest.raises(ValueError, match="requires a value"):
        R.Measured(value=None, validity=R.Validity.OK)


@pytest.mark.parametrize(
    "validity",
    [
        R.Validity.UNKNOWN,
        R.Validity.UNSUPPORTED,
        R.Validity.NOT_APPLICABLE,
        R.Validity.MISSING_ARTIFACT,
        R.Validity.INVALID,
        R.Validity.NOT_RECORDED,
    ],
)
def test_non_ok_with_a_value_is_refused(validity: R.Validity) -> None:
    with pytest.raises(ValueError, match="must not carry a value"):
        R.Measured(value=1.0, validity=validity)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_float_is_refused(bad: float) -> None:
    with pytest.raises(ValueError, match="non-finite"):
        R.Measured(value=bad)
    with pytest.raises(ValueError, match="non-finite"):
        R.Measured.ok(bad)


def test_absent_refuses_ok_validity() -> None:
    with pytest.raises(ValueError, match="non-OK validity"):
        R.Measured.absent(R.Validity.OK, "nonsense")


def test_measured_zero_stays_distinct_from_unknown() -> None:
    zero = R.Measured.ok(0.0, unit="Mbps")
    unknown = R.Measured.unknown("not_observed", unit="Mbps")

    # A measured zero is readable as a measurement.
    assert zero.validity is R.Validity.OK
    assert zero.validity.is_value is True
    assert zero.value == 0.0

    # An unknown is not, and carries the reason instead.
    assert unknown.validity.is_value is False
    assert unknown.value is None
    assert unknown.reason == "not_observed"

    # They are different objects by value equality, in both directions.
    assert zero != unknown
    assert unknown != zero
    assert zero.to_json() != unknown.to_json()
    assert zero.to_json()["value"] == 0.0
    assert unknown.to_json()["value"] is None
    assert unknown.to_json()["validity"] == "unknown"

    # ... and the reason the validity flag exists: the raw values are both falsy, so a
    # consumer that tests ``if measured.value:`` conflates the two.
    assert not bool(zero.value)
    assert not bool(unknown.value)


def test_unknown_is_not_equal_to_another_absent_reason() -> None:
    assert R.Measured.unknown("a") != R.Measured.unknown("b")
    assert R.Measured.unknown("a") != R.Measured.not_recorded("a")
    assert R.Measured.unknown("a") == R.Measured.unknown("a")


@pytest.mark.parametrize(
    "factory, validity",
    [
        (R.Measured.unknown, R.Validity.UNKNOWN),
        (R.Measured.unsupported, R.Validity.UNSUPPORTED),
        (R.Measured.not_recorded, R.Validity.NOT_RECORDED),
        (R.Measured.missing_artifact, R.Validity.MISSING_ARTIFACT),
        (R.Measured.invalid, R.Validity.INVALID),
        (R.Measured.not_applicable, R.Validity.NOT_APPLICABLE),
    ],
)
def test_absent_constructors_set_their_validity(factory, validity) -> None:
    measured = factory("because")
    assert measured.validity is validity
    assert measured.value is None
    assert measured.reason == "because"


def test_from_float_never_invents_a_number() -> None:
    assert R.Measured.from_float(None).validity is R.Validity.UNKNOWN
    assert R.Measured.from_float(None).value is None
    assert R.Measured.from_float(float("nan")).validity is R.Validity.INVALID
    assert R.Measured.from_float(float("nan")).reason == "non_finite"
    assert R.Measured.from_float("not a number").validity is R.Validity.INVALID
    zero = R.Measured.from_float(0.0)
    assert zero.validity is R.Validity.OK and zero.value == 0.0
    assert R.Measured.from_float(np.float64(2.5)).value == 2.5


def test_measured_array_keeps_unobserved_absent_and_observed_zero_measured() -> None:
    values = np.array([0.0, 5.0, float("nan"), 7.0])
    observed = np.array([True, False, True, True])
    out = R.measured_array(values, observed=observed, unit="Mbps")
    assert [m.validity for m in out] == [
        R.Validity.OK,
        R.Validity.UNKNOWN,
        R.Validity.INVALID,
        R.Validity.OK,
    ]
    assert out[0].value == 0.0  # measured zero, not "missing"
    assert out[1].value is None  # unobserved, not zero
    assert out[2].reason == "non_finite"
    assert all(m.unit == "Mbps" for m in out)
    with pytest.raises(ValueError, match="observed mask shape"):
        R.measured_array(values, observed=np.array([True, False]))


# --------------------------------------------------------------------------------------
# Identity
# --------------------------------------------------------------------------------------


def test_reused_slot_with_a_new_generation_is_a_different_entity() -> None:
    kind = R.EntityKind.INDIVIDUAL_UE
    registry = R.LifetimeRegistry()

    registry.observe(kind, [0, 1, 2])
    departing = registry.entity(kind, 1, label="ue-A")
    assert departing.generation == 0
    assert registry.generation(kind, 1) == 0

    registry.observe(kind, [0, 2])  # slot 1 goes away
    registry.observe(kind, [0, 1, 2])  # a different entity reuses slot 1

    arriving = registry.entity(kind, 1, label="ue-B")
    assert registry.generation(kind, 1) == 1, "registry must increment the generation"
    assert arriving.generation == 1
    assert arriving != departing
    assert arriving.key != departing.key
    assert departing.key == "individual_ue:1:0"
    assert arriving.key == "individual_ue:1:1"

    # Slots that never went inactive keep generation 0.
    assert registry.generation(kind, 0) == 0
    assert registry.generation(kind, 2) == 0

    snapshot = registry.snapshot()
    assert snapshot["generation"]["individual_ue:1"] == 1
    assert "individual_ue:1" in snapshot["active"]


def test_generations_are_tracked_per_kind() -> None:
    registry = R.LifetimeRegistry()
    registry.observe(R.EntityKind.UAV, [0])
    registry.observe(R.EntityKind.SITE, [0])
    registry.observe(R.EntityKind.UAV, [])
    registry.observe(R.EntityKind.UAV, [0])
    assert registry.generation(R.EntityKind.UAV, 0) == 1
    assert registry.generation(R.EntityKind.SITE, 0) == 0


def test_entity_id_key_round_trips() -> None:
    entity = R.EntityId(kind=R.EntityKind.UAV, slot=3, generation=2, label="uav-3")
    parsed = R.EntityId.parse(entity.key)
    assert (parsed.kind, parsed.slot, parsed.generation) == (R.EntityKind.UAV, 3, 2)
    assert parsed.label is None  # the key carries identity, not presentation
    assert entity.to_json() == {
        "key": "uav:3:2",
        "kind": "uav",
        "slot": 3,
        "generation": 2,
        "label": "uav-3",
    }


def test_entity_kind_aggregates_are_flagged() -> None:
    assert R.EntityKind.AGGREGATE_DEMAND_POINT.is_aggregate
    assert R.EntityKind.SOURCE_GRID_CELL.is_aggregate
    assert not R.EntityKind.INDIVIDUAL_UE.is_aggregate


# --------------------------------------------------------------------------------------
# canonical_link_key
# --------------------------------------------------------------------------------------


def test_link_key_is_stable_under_a_changed_solver_index() -> None:
    """The key is derived from endpoints + class + domain; ``producer_local_id`` is not in it."""

    source = R.EntityId(kind=R.EntityKind.UAV, slot=0)
    target = R.EntityId(kind=R.EntityKind.AGGREGATE_DEMAND_POINT, slot=4)
    first = R.canonical_link_key(source, target, "uav_access", resource_domain="uav_0_access")
    second = R.canonical_link_key(source, target, "uav_access", resource_domain="uav_0_access")
    assert first == second == "uav:0:0->aggregate_demand_point:4:0|uav_access@uav_0_access"

    early = R.LinkRecord(
        link_key=first, source=source, target=target, link_class="uav_access",
        activity=R.LinkActivity.ACTIVE, producer_local_id=7,
    )
    late = R.LinkRecord(
        link_key=second, source=source, target=target, link_class="uav_access",
        activity=R.LinkActivity.ACTIVE, producer_local_id=91,
    )
    assert early.link_key == late.link_key
    assert early.producer_local_id != late.producer_local_id


def test_link_key_is_order_sensitive_as_documented() -> None:
    """The docstring says *directed* link identity, so swapping endpoints is a new link."""

    a = R.EntityId(kind=R.EntityKind.UAV, slot=0)
    b = R.EntityId(kind=R.EntityKind.UAV, slot=1)
    forward = R.canonical_link_key(a, b, "uav_uav_backhaul")
    reverse = R.canonical_link_key(b, a, "uav_uav_backhaul")
    assert forward != reverse
    assert forward == "uav:0:0->uav:1:0|uav_uav_backhaul"
    assert reverse == "uav:1:0->uav:0:0|uav_uav_backhaul"


def test_link_key_separates_class_domain_and_generation() -> None:
    a = R.EntityId(kind=R.EntityKind.UAV, slot=0)
    b = R.EntityId(kind=R.EntityKind.SITE, slot=2)
    base = R.canonical_link_key(a, b, "site_uav_backhaul")
    assert base == "uav:0:0->site:2:0|site_uav_backhaul"
    assert R.canonical_link_key(a, b, "uav_access") != base
    assert R.canonical_link_key(a, b, "site_uav_backhaul", resource_domain="d1") != base
    assert R.canonical_link_key(
        a, b, "site_uav_backhaul", resource_domain="d1"
    ) != R.canonical_link_key(a, b, "site_uav_backhaul", resource_domain="d2")
    # An empty/None domain is simply omitted rather than encoded.
    assert R.canonical_link_key(a, b, "site_uav_backhaul", resource_domain="") == base
    # A later lifetime in the same slot is a different link.
    b2 = R.EntityId(kind=R.EntityKind.SITE, slot=2, generation=1)
    assert R.canonical_link_key(a, b2, "site_uav_backhaul") != base


def test_link_key_accepts_tuple_endpoints_equivalently() -> None:
    entity = R.EntityId(kind=R.EntityKind.UAV, slot=0)
    other = R.EntityId(kind=R.EntityKind.CORE, slot=0)
    assert R.canonical_link_key(entity, other, "wired_core") == R.canonical_link_key(
        ("uav", 0), ("core", 0), "wired_core"
    )


# --------------------------------------------------------------------------------------
# validate_scene_json
# --------------------------------------------------------------------------------------


def test_validate_accepts_a_well_formed_frame() -> None:
    assert R.validate_scene_json(_scene_frame().to_json()) == []


def test_validate_names_a_wrong_schema() -> None:
    payload = _scene_frame().to_json()
    payload["schema"] = "research_support.scene.0"
    problems = R.validate_scene_json(payload)
    assert any("schema" in p for p in problems)
    assert any(R.SCENE_SCHEMA in p for p in problems)


@pytest.mark.parametrize("section", ["identity", "clock", "provenance", "geometry", "capability"])
def test_validate_names_a_missing_section(section: str) -> None:
    payload = _scene_frame().to_json()
    payload[section] = None
    problems = R.validate_scene_json(payload)
    assert [p for p in problems if section in p], problems
    assert any(p.startswith("missing or malformed section") for p in problems)


def test_validate_names_a_reversed_measurement_interval() -> None:
    payload = _scene_frame().to_json()
    payload["clock"]["measurement_end_s"] = payload["clock"]["measurement_start_s"] - 1.0
    problems = R.validate_scene_json(payload)
    assert "measurement interval ends before it starts" in problems


def test_validate_names_a_duplicate_link_key() -> None:
    payload = _scene_frame().to_json()
    payload["links"].append(dict(payload["links"][0]))
    problems = R.validate_scene_json(payload)
    assert any(p.startswith("duplicate link_key:") for p in problems)
    assert any(payload["links"][0]["link_key"] in p for p in problems)


def test_validate_names_a_duplicate_entity_key() -> None:
    payload = _scene_frame().to_json()
    payload["ground_entities"].append(dict(payload["ground_entities"][0]))
    problems = R.validate_scene_json(payload)
    assert any(p.startswith("duplicate entity key:") for p in problems)


def test_validate_names_an_entity_without_a_key() -> None:
    payload = _scene_frame().to_json()
    payload["uavs"][0]["entity"] = {}
    problems = R.validate_scene_json(payload)
    assert "uavs entry without an entity key" in problems


def test_validate_names_a_path_referencing_an_unknown_link() -> None:
    payload = _scene_frame().to_json()
    payload["paths"][0]["link_keys"] = ["uav:9:0->site:9:0|ghost"]
    problems = R.validate_scene_json(payload)
    assert any(p.startswith("path references unknown link_key:") for p in problems)


def test_validate_names_a_malformed_link_entry() -> None:
    payload = _scene_frame().to_json()
    payload["links"].append("not a mapping")
    assert "malformed link entry" in R.validate_scene_json(payload)


# --------------------------------------------------------------------------------------
# JSON encoding and hashes
# --------------------------------------------------------------------------------------


def test_frame_round_trips_through_dumps_and_loads() -> None:
    frame = _scene_frame()
    payload = frame.to_json()
    restored = R.loads(R.dumps(payload))
    assert restored == payload
    assert R.validate_scene_json(restored) == []
    assert R.loads(frame.to_bytes()) == payload
    # The measured zero survives the round trip as a measured zero.
    ground = restored["ground_entities"][0]
    assert ground["offered_mbps"]["value"] == 0.0
    assert ground["offered_mbps"]["validity"] == "ok"
    assert restored["ground_entities"][1]["offered_mbps"]["value"] is None
    assert restored["ground_entities"][1]["offered_mbps"]["validity"] == "unknown"


def test_dumps_escapes_html_sensitive_characters() -> None:
    text = R.dumps({"note": "</script><!-- & -->"})
    assert "<" not in text and ">" not in text and "&" not in text
    assert R.loads(text)["note"] == "</script><!-- & -->"


def test_dumps_writes_null_for_non_finite_numbers() -> None:
    text = R.dumps({"a": float("nan"), "b": np.float64("inf"), "c": np.array([1.0, np.nan])})
    assert "NaN" not in text and "Infinity" not in text
    assert R.loads(text) == {"a": None, "b": None, "c": [1.0, None]}


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_loads_rejects_non_standard_json_constants(token: str) -> None:
    with pytest.raises(ValueError, match="non-standard JSON constant"):
        R.loads('{"value": %s}' % token)


def test_dumps_encodes_records_and_numpy_scalars() -> None:
    payload = {
        "measured": R.Measured.ok(1.5, unit="Mbps"),
        "entity": R.EntityId(kind=R.EntityKind.UAV, slot=1),
        "kind": R.FrameKind.EVENT,
        "int": np.int64(4),
        "bool": np.bool_(True),
        "set": {"b", "a"},
        "bytes": b"\x00\x01",
    }
    restored = R.loads(R.dumps(payload))
    assert restored["measured"] == {"value": 1.5, "validity": "ok", "unit": "Mbps"}
    assert restored["entity"]["key"] == "uav:1:0"
    assert restored["kind"] == "event"
    assert restored["int"] == 4 and restored["bool"] is True
    assert restored["set"] == ["a", "b"]
    assert restored["bytes"] == "AAE="


def test_content_hash_is_stable_and_key_order_independent() -> None:
    frame = _scene_frame().to_json()
    first = R.content_hash(frame)
    assert first == R.content_hash(_scene_frame().to_json())
    assert first.startswith("sha256:") and len(first) == len("sha256:") + 64
    assert R.content_hash({"a": 1, "b": 2}) == R.content_hash({"b": 2, "a": 1})


def test_content_hash_changes_when_a_value_changes() -> None:
    frame = _scene_frame().to_json()
    before = R.content_hash(frame)
    frame["clock"]["simulation_time_s"] = 12.6
    assert R.content_hash(frame) != before
    # ... including a change from a measured zero to a missing value.
    frame = _scene_frame().to_json()
    frame["ground_entities"][0]["offered_mbps"] = R.Measured.unknown("gone").to_json()
    assert R.content_hash(frame) != before


def test_file_hash_is_stable_and_differs_on_a_changed_byte(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "artifact.bin"
    path.write_bytes(b"alpha-beta-gamma")
    first = R.file_hash(str(path))
    assert first == R.file_hash(str(path))
    assert first == R.file_hash(str(path), chunk=4)  # chunking must not change the digest
    assert first.startswith("sha256:")

    other = tmp_path / "artifact2.bin"
    other.write_bytes(b"alpha-beta-gamma")
    assert R.file_hash(str(other)) == first

    path.write_bytes(b"alpha-beta-gammb")  # exactly one byte differs
    assert R.file_hash(str(path)) != first


def test_schema_constants_are_the_published_strings() -> None:
    assert R.SCENE_SCHEMA == "research_support.scene.1"
    assert R.METRIC_SCHEMA == "research_support.metric.1"
    assert R.RUN_SCHEMA == "research_support.run.1"
    assert R.TRACE_INDEX_SCHEMA == "research_support.trace_index.1"


# --------------------------------------------------------------------------------------
# Derived records built on Measured
# --------------------------------------------------------------------------------------


def test_metric_record_round_trip_preserves_absence() -> None:
    absent = R.MetricRecord(
        run_id="r", method_id="m", metric_name="satisfaction_all",
        value=R.Measured.not_recorded("never written by this reader"),
        x_kind=R.XKind.EPISODE_INDEX, x_value=0, phase=R.Phase.EVALUATION,
        aggregation_level=R.AggregationLevel.EPISODE,
    )
    payload = absent.to_json()
    assert payload["value"] is None
    assert payload["validity"] == "not_recorded"
    assert payload["reason"] == "never written by this reader"
    restored = R.MetricRecord.from_json(payload)
    assert restored.value.validity is R.Validity.NOT_RECORDED
    assert restored.value.value is None

    zero = R.MetricRecord(
        run_id="r", method_id="m", metric_name="satisfaction_all",
        value=R.Measured.ok(0.0), x_kind=R.XKind.EPISODE_INDEX, x_value=0,
        phase=R.Phase.EVALUATION, aggregation_level=R.AggregationLevel.EPISODE,
    )
    assert zero.to_json()["value"] == 0.0
    assert R.MetricRecord.from_json(zero.to_json()).value.value == 0.0


def test_run_record_reports_an_unread_field_as_unknown() -> None:
    record = R.RunRecord(run_id="r", reader="unit", reader_version="1")
    missing = record.get("total_timesteps")
    assert missing.validity is R.Validity.UNKNOWN
    assert missing.reason == "field_not_read:total_timesteps"
    record.set("total_timesteps", R.Measured.ok(0))
    assert record.field_status["total_timesteps"] == "recorded"
    record.set("gamma", R.Measured.not_recorded("absent in config"))
    assert record.field_status["gamma"] == "not_recorded"
    assert R.loads(R.dumps(record.to_json()))["fields"]["total_timesteps"]["value"] == 0


def test_scene_capability_round_trips() -> None:
    capability = R.SceneCapability(has_links=True, has_sinr=True, notes=("legacy route",))
    restored = R.SceneCapability.from_json(capability.to_json())
    assert restored == capability
    assert R.SceneCapability.from_json({}).has_links is False


def test_helpers_reject_nothing_they_should_keep() -> None:
    assert R._opt_float(0.0) == 0.0
    assert R._opt_float(float("nan")) is None
    assert R._opt_float(None) is None
    assert R._opt_int(None) is None
    assert R._opt_vec(None) is None
    assert R._opt_vec((1, 2, 3)) == [1.0, 2.0, 3.0]
    assert R._opt_measured(None) is None
    assert math.isclose(R._opt_measured(R.Measured.ok(2.0))["value"], 2.0)
