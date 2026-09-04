"""The section 11 recast, as code: what became a record and what still gates.

Covers the three properties the owner's decisions 4 and 7 require of the R02
runner:

(i)   the A0 byte manifests and the native build key are RECORDED, never REQUIRED;
(ii)  missing RESOURCE telemetry downgrades to `resources_unmeasured: true` with
      reasons and does not quarantine;
(iii) learner-side instrumentation failure still quarantines under evidence-spec
      section 6.2.

Plus the exposure line the recast keeps as a launch condition, and the R02 run
identity.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import torch

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


@pytest.fixture(scope="module")
def r02():
    path = REPOSITORY_ROOT / "scripts" / "run_vnfc_bpcr_r02.py"
    spec = importlib.util.spec_from_file_location("vnfc_r02_recast_under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["vnfc_r02_recast_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def r01(r02):
    """The R01 runner module, with every attribute this file touches restored."""
    module = r02.load_r01_runner()
    saved = {
        name: getattr(module, name)
        for name in ("validate_telemetry_payload", "_train_one_update")
    }
    saved_wrappers = {
        name: getattr(module, name, None)
        for name in ("_r01_validate_telemetry_payload", "_r01_train_one_update")
    }
    try:
        yield module
    finally:
        for name, value in saved.items():
            setattr(module, name, value)
        for name, value in saved_wrappers.items():
            if value is None:
                if hasattr(module, name):
                    delattr(module, name)
            else:
                setattr(module, name, value)


# ---------------------------------------------------------------------------
# (i) byte manifests and the native build key are recorded, not required
# ---------------------------------------------------------------------------

def test_byte_manifest_record_is_recorded_not_required(r02):
    record = r02.byte_manifest_record()
    assert record["gating"] is False
    assert record["required"] is False
    assert "11.4" in record["recorded_only_reason"]
    assert record["a0_disposition"] == "OPTIONAL_ANALYSIS_HOLDS_NOTHING"
    assert record["a0_implementation_started"] is False
    manifests = {row["manifest"]: row for row in record["manifests"]}
    assert len(manifests) == 2
    for row in manifests.values():
        # present-or-absent is a field; neither value raises and neither gates
        assert isinstance(row["present"], bool)
        if row["present"]:
            assert isinstance(row["sha256"], str) and len(row["sha256"]) == 64
        else:
            assert row["sha256"] is None


def test_missing_byte_manifest_does_not_raise(r02, tmp_path, monkeypatch):
    monkeypatch.setattr(r02, "_REPOSITORY_ROOT", tmp_path)
    record = r02.byte_manifest_record()
    assert record["gating"] is False
    assert all(row["present"] is False for row in record["manifests"])
    assert all(row["sha256"] is None for row in record["manifests"])


def test_native_identity_is_recorded_even_when_the_build_key_differs(r02):
    """A DLL rebuilt from unchanged source with a different key holds nothing."""
    binding = {
        "r09_build_key": "0" * 64,
        "primary_artifact_sha256": "1" * 64,
        "primary_artifact_size": 999,
        "primary_artifact_path": "C:/nowhere/bpcr_backend.dll",
        "shadow_build_key": "2" * 64,
        "shadow_artifact_sha256": "3" * 64,
        "shadow_artifact_size": 111,
        "compiler_path": "C:/nowhere/cl.exe",
        "compiler_sha256": "4" * 64,
    }
    record = r02.native_identity_record(binding)
    assert record["gating"] is False
    assert record["build_key_equals_frozen_literal"] is False
    assert record["artifact_sha256_equals_frozen_literal"] is False
    assert record["artifact_size_equals_frozen_literal"] is False
    assert record["rebuild_from_unchanged_source_holds_nothing"] is True
    assert record["frozen_a0_literals"]["bpcr_backend_dll_build_key"] == (
        "7222d990642a7e4cb010b6526f17acdb3f3aa85f11d1b8d34be0eedbe11e9c99"
    )


def test_native_identity_of_the_live_binding_is_recorded(r02):
    """The observed native identity is recorded whether or not it matches A0."""
    binding = r02.prepare_native_backends()
    record = r02.native_identity_record(binding)
    assert record["gating"] is False
    assert len(record["observed_bpcr_backend_dll_build_key"]) == 64
    assert len(record["observed_bpcr_backend_dll_sha256"]) == 64
    assert isinstance(record["build_key_equals_frozen_literal"], bool)
    assert isinstance(record["artifact_sha256_equals_frozen_literal"], bool)


# ---------------------------------------------------------------------------
# (ii) missing resource telemetry downgrades, (iii) learner-side quarantines
# ---------------------------------------------------------------------------

def _install_over(r02, r01, raising_message):
    def raiser(payload):
        raise r01.BExploreContractError(raising_message)

    r01.validate_telemetry_payload = raiser
    r01._r01_validate_telemetry_payload = None
    state = {"resources_unmeasured": False, "resources_unmeasured_reasons": ()}
    r02.install_resource_telemetry_downgrade(r01, state)
    return state


@pytest.mark.parametrize("message", [
    "scientific result telemetry contains unmeasured fields",
    "external telemetry contains nonpositive measured fields",
    "external stage wall/CPU telemetry differs",
    "external storage/I/O telemetry differs",
    "process-tree telemetry measurement source/limitations differ",
    "process-tree telemetry sampling/exposure value differs",
    "process-tree host CPU occupancy differs",
    "process-tree telemetry extended I/O differs",
    "process-tree aggregate I/O binding differs",
    "process-tree scientific throughput binding differs",
])
def test_missing_resource_telemetry_downgrades_and_does_not_quarantine(r02, r01, message):
    assert message in r02.RESOURCE_MEASUREMENT_FAILURES
    state = _install_over(r02, r01, message)
    r01.validate_telemetry_payload({})  # must not raise: the run stays valid
    assert state["resources_unmeasured"] is True
    assert state["resources_unmeasured_reasons"] == (message,)


def test_resource_downgrade_accumulates_distinct_reasons(r02, r01):
    state = _install_over(r02, r01, "process-tree host CPU occupancy differs")
    r01.validate_telemetry_payload({})
    r01.validate_telemetry_payload({})
    assert state["resources_unmeasured_reasons"] == ("process-tree host CPU occupancy differs",)


@pytest.mark.parametrize("message", [
    "scientific result telemetry is incomplete",
    "external telemetry terminal/schema differs",
    "external per-arm exposure telemetry differs",
    "operation-resolved host-call telemetry differs",
    "telemetry memory headroom is below 4 GiB",
    "exact durable artifact inventory/peak binding differs",
    "frozen prebuilt native artifact inventory differs",
    "process-tree telemetry preflight binding differs",
    "process-tree stage observation inventory differs",
    "exact process/storage telemetry readiness differs",
    "process-tree telemetry provenance/inventory is incomplete",
])
def test_learner_side_instrumentation_failure_still_quarantines(r02, r01, message):
    assert message not in r02.RESOURCE_MEASUREMENT_FAILURES
    state = _install_over(r02, r01, message)
    with pytest.raises(r01.BExploreContractError) as raised:
        r01.validate_telemetry_payload({})
    assert str(raised.value) == message
    assert state["resources_unmeasured"] is False
    assert state["resources_unmeasured_reasons"] == ()


def test_resource_failure_set_excludes_scientific_bindings(r02):
    """The downgrade set is resource measurement only, by construction."""
    forbidden = (
        "schema", "terminal", "per-arm exposure", "host-call", "memory headroom",
        "durable artifact", "native artifact", "preflight", "provenance",
    )
    for message in r02.RESOURCE_MEASUREMENT_FAILURES:
        assert not any(token in message for token in forbidden), message


# ---------------------------------------------------------------------------
# the exposure line, which remains a launch condition
# ---------------------------------------------------------------------------

def test_exposure_line_records_relative_parameter_displacement(r02, r01):
    class _Model(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.weight = torch.nn.Parameter(torch.tensor([3.0, 4.0], dtype=torch.float64))

    model = _Model()

    def fake_train_one_update(config, rng, model_, optimizer, arm, update, now):
        with torch.no_grad():
            model_.weight.add_(torch.tensor([0.5, 0.0], dtype=torch.float64))
        return {
            "optimizer_steps": 16,
            "loss_rows": ({"preclip_gradient_norm": 0.25}, {"preclip_gradient_norm": 0.75}),
        }

    r01._train_one_update = fake_train_one_update
    r01._r01_train_one_update = None
    exposure: list[dict[str, object]] = []
    r02.install_exposure_line(r01, exposure)

    for update in range(2):
        r01._train_one_update(None, None, model, None, "MAPR", update, None)

    assert [row["update"] for row in exposure] == [0, 1]
    assert all(row["arm"] == "MAPR" for row in exposure)
    assert exposure[0]["initial_parameter_norm"] == pytest.approx(5.0)
    assert exposure[0]["absolute_parameter_displacement"] == pytest.approx(0.5)
    assert exposure[0]["relative_parameter_displacement"] == pytest.approx(0.1)
    assert exposure[1]["absolute_parameter_displacement"] == pytest.approx(1.0)
    assert exposure[1]["relative_parameter_displacement"] == pytest.approx(0.2)
    assert all(row["mean_preclip_gradient_norm"] == pytest.approx(0.5) for row in exposure)
    assert all(row["optimizer_steps"] == 16 for row in exposure)


# ---------------------------------------------------------------------------
# R02 identity and the recast record
# ---------------------------------------------------------------------------

def test_r02_identity_is_fresh_against_r01(r02):
    r01 = r02.load_r01_runner()
    assert r02.RUN_REVISION == "VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02"
    assert r02.DEBUG_SEED == 2026090301
    assert r02.PRIMARY_SEEDS == (2026090311, 2026090321, 2026090331)
    assert r02.DEBUG_SEED not in (2026090101,)
    assert not set(r02.PRIMARY_SEEDS) & {2026090111, 2026090121, 2026090131}
    assert not set(r02.PRIMARY_SEEDS) & set(r01.OPTIONAL_SEEDS)


def test_recast_record_names_what_still_gates(r02):
    record = r02.r02_recast_record()
    assert record["a0_law_disposition"] == "OPTIONAL_ANALYSIS"
    assert record["conformance_rows"] == 52
    assert record["conformance_object"] == "VNFC-R02-PRESENTATION-CONFORMANCE-52"
    assert "DIRECTION.md:181-182" in record["superseded_launch_condition"]
    gating = record["still_gating"]
    assert any("4 GiB" in row for row in gating)
    assert any("exposure line" in row for row in gating)
    assert any("nonzero" in row for row in gating)
    assert any("leakage" in row for row in gating)
    assert any("quarantine" in row for row in gating)
