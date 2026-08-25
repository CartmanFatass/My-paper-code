from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from envs.native.production_backend import (
    ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST,
)
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90 import coordinates
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90 import host
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90 import preactivity
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90.config import (
    PRODUCTION_NAMESPACE,
)


def _unexpected_activity(*_args, **_kwargs):
    raise AssertionError("preactivity identity attempted coordinate/RNG/tick activity")


def test_identity_collects_exact_native_facts_without_activity(monkeypatch) -> None:
    monkeypatch.setattr(coordinates, "materialize_uniform", _unexpected_activity)
    monkeypatch.setattr(coordinates, "materialize_normal", _unexpected_activity)
    monkeypatch.setattr(coordinates, "materialize_normal_pair", _unexpected_activity)
    monkeypatch.setattr(coordinates.Coordinate, "fields", _unexpected_activity)
    monkeypatch.setattr(host.Headland90Host, "run", _unexpected_activity)

    packet = preactivity.collect_preactivity_identity()
    identity = packet["identity"]
    assert packet["activity_boundary"] == {
        "preactivity_only": True,
        "production_coordinate_rows_bound": False,
        "production_random_words_materialized": False,
        "production_controller_ticks_executed": False,
        "calibration_or_hold_manifest_created": False,
    }
    assert len(packet["identity_sha256"]) == 64
    assert packet["compile_observation"]["status"] in {
        "measured_first_compile", "cache_present_unknown"
    }
    if packet["compile_observation"]["status"] == "measured_first_compile":
        assert packet["compile_observation"]["first_compile_seconds"] >= 0.0
    else:
        assert packet["compile_observation"]["first_compile_seconds"] is None

    toolchain = identity["toolchain"]
    assert toolchain["compile_flags"] == [
        "/nologo", "/std:c++17", "/O2", "/EHsc", "/LD", "/fp:strict"
    ]
    assert toolchain["abi_version"] == 1
    compiler = Path(toolchain["compiler_path"])
    assert compiler.is_file()
    assert toolchain["compiler_size"] == compiler.stat().st_size
    assert toolchain["compiler_mtime_ns"] == compiler.stat().st_mtime_ns
    assert toolchain["compiler_sha256"] == hashlib.sha256(compiler.read_bytes()).hexdigest()
    assert "Microsoft" in toolchain["compiler_version_output"]

    native = identity["native_artifact"]
    artifact = Path(native["artifact_path"])
    assert artifact.is_file()
    assert native["artifact_sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert native["abi_version"] == 1
    assert native["python_fallback"] is False


def test_source_event_registry_serializer_and_platform_identities_are_complete() -> None:
    first = preactivity.collect_preactivity_identity()
    second = preactivity.collect_preactivity_identity()
    assert first["identity_sha256"] == second["identity_sha256"]
    identity = first["identity"]
    sources = identity["native_sources"]
    assert len(sources["aggregate_sha256"]) == 64
    for label in ("cpp", "event_table_header"):
        source = sources[label]
        path = Path(source["path"])
        assert source["bytes"] == len(path.read_bytes())
        assert source["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    event = identity["event_table"]
    assert event["reachable_rate_count"] == 456
    assert event["maximum_denominator"] == 1024
    assert event["generation_precision_decimal_digits"] == 220
    assert len(event["reachable_vectors_sha256"]) == 64
    registry = identity["controller_registry"]
    assert registry["members"] == 192
    assert registry["lookup_members"] == 64
    assert registry["timing_members"] == 128
    assert len(registry["ordered_content_sha256"]) == 64
    serializer = identity["serializer_schema"]
    assert serializer["serializer"] == preactivity.SERIALIZER_ID
    assert len(serializer["schema_sha256"]) == 64
    python = identity["python_platform"]
    assert Path(python["executable"]).is_file()
    assert python["float_mant_dig"] == 53
    assert python["float_rounds"] == 1


def test_coordinate_binding_is_an_unbound_exact_proposal_only() -> None:
    proposal = preactivity.coordinate_binding_proposal()
    assert proposal["namespace"] == PRODUCTION_NAMESPACE
    assert proposal["bound"] is False
    assert proposal["production_rows_present"] is False
    assert proposal["production_words_present"] is False
    assert proposal["splits"]["CAL"]["replicates"] == 48
    assert proposal["splits"]["CAL"]["controller_replicates"] == 9216
    assert proposal["splits"]["HOLD"]["replicates"] == 128
    assert proposal["splits"]["HOLD"]["logical_controller_replicates"] == 640
    assert proposal["total_controller_replicates"] == 9856
    assert proposal["total_physical_ticks"] == 37847040
    assert proposal["cross_field_laws"]["template"] == "(replicate+3*block) mod 4"
    digest = proposal.pop("proposal_schema_sha256")
    assert digest == hashlib.sha256(preactivity.canonical_json_bytes(proposal)).hexdigest()
    serialized = json.dumps(proposal, sort_keys=True)
    assert "uniform_values" not in serialized
    assert "normal_values" not in serialized
    assert "coordinate_rows\"" not in serialized


def test_canonical_serializer_rejects_nonfinite_values() -> None:
    assert preactivity.canonical_json_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}\n'
    with pytest.raises(preactivity.PreactivityError, match="canonical JSON"):
        preactivity.canonical_json_bytes({"bad": float("nan")})


@pytest.mark.parametrize("batch_width", (1, 8, 32))
def test_live_shared_direction_guard_matches_local_frozen_artifact(
    batch_width, monkeypatch,
) -> None:
    monkeypatch.setattr(coordinates, "materialize_uniform", _unexpected_activity)
    monkeypatch.setattr(coordinates, "materialize_normal", _unexpected_activity)
    monkeypatch.setattr(coordinates, "materialize_normal_pair", _unexpected_activity)
    monkeypatch.setattr(coordinates.Coordinate, "fields", _unexpected_activity)
    monkeypatch.setattr(host.Headland90Host, "run", _unexpected_activity)
    local = preactivity.native_artifact_identity()
    receipt = preactivity.require_direction_cpp_batched_production(
        batch_width=batch_width
    )
    shared = receipt["shared"]
    assert shared["component"] == ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST
    assert shared["batch_width"] == batch_width
    assert shared["backend"] == "cpp"
    assert shared["full_reset_step_cpp"] is True
    assert shared["python_fallback"] is False
    assert shared["native"]["artifact_sha256"] == local["artifact_sha256"]
    assert receipt["direction_native"]["artifact_sha256"] == local["artifact_sha256"]
    assert receipt["python_fallback"] is False


def test_direction_guard_rejects_an_incomplete_shared_receipt(monkeypatch) -> None:
    monkeypatch.setattr(preactivity, "native_artifact_identity", _unexpected_activity)

    def incomplete_guard(*_args, **_kwargs):
        return {
            "component": ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST,
            "backend": "cpp",
            "python_fallback": False,
            "full_reset_step_cpp": False,
        }

    with pytest.raises(preactivity.PreactivityError, match="not HEADLAND-90 full-native"):
        preactivity.require_direction_cpp_batched_production(
            batch_width=8, shared_guard=incomplete_guard
        )


def test_future_registry_loader_exposes_only_the_native_artifact() -> None:
    module = preactivity.load_headland90_cpp_backend()
    assert Path(module.__file__).is_file()
    assert module.abi_version == 1
    assert module.python_fallback is False
    assert module.library.headland90_abi_version() == 1
