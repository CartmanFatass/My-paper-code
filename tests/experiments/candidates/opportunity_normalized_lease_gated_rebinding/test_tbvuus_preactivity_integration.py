"""Cross-module, result-blind integration checks for TBVUUS r03 preactivity."""

from __future__ import annotations

from pathlib import Path

import pytest

from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import (
    Arm,
    EncounterSpec,
    FixtureCase,
    FixtureTape,
    RouteClass,
    native_artifact_identity,
    native_toolchain_identity,
    require_cpp_batched_backend,
    run_native_batch,
)
from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import (
    config,
    contracts,
    preactivity,
)


def _literal_native_identity() -> dict[str, object]:
    return {
        "backend": "cpp",
        "python_fallback": False,
        "full_reset_step_cpp": True,
        "abi_version": "TBVUUS-R03-ABI-v1",
        "source_sha256": "1" * 64,
        "artifact_sha256": "2" * 64,
        "toolchain": {"compiler": "literal-test", "strict_fp": True},
    }


def _literal_cases(batch_width: int) -> tuple[FixtureCase, ...]:
    cases: list[FixtureCase] = []
    for index in range(batch_width):
        route = RouteClass.SHORT if index % 2 == 0 else RouteClass.LONG
        spec = EncounterSpec(
            route,
            1 if index % 4 < 2 else -1,
            8 if index % 8 < 4 else -8,
        )
        cases.append(
            FixtureCase(
                spec=spec,
                tape=FixtureTape.constant(spec, normal=0.0, uniform=0.5),
                arm=Arm(index % 4),
                logical_tag=f"literal-fixture-{batch_width}-{index}",
            )
        )
    return tuple(cases)


def _with_resealed_identity(*, identity: dict[str, object]) -> dict[str, object]:
    return {
        "identity": identity,
        "identity_sha256": contracts.document_sha256(identity),
    }


def test_exact_contract_config_shape_and_fixture_boundary_agree() -> None:
    assert contracts.SCIENCE_REVISION == config.SCIENCE_REVISION
    assert contracts.STAGE == config.OBJECT_REVISION
    assert contracts.HOST_ID == config.HOST_PACKAGE
    assert contracts.ARMS == tuple(arm.name.replace("_", "-") for arm in Arm)
    assert contracts.REPLICATES == 128
    assert contracts.BLOCKS_PER_CONTROLLER_REPLICATE == 20
    assert contracts.ENCOUNTERS_PER_BLOCK == 2
    assert contracts.SHORT_PHYSICAL_TICKS == config.PREROLL_TICKS + config.SHORT_SCORED_TICKS
    assert contracts.LONG_PHYSICAL_TICKS == config.PREROLL_TICKS + config.LONG_SCORED_TICKS
    assert contracts.PHYSICAL_TICKS_PER_CONTROLLER_REPLICATE == 3_840
    assert contracts.TOTAL_PHYSICAL_TICKS == 1_966_080
    assert contracts.TOTAL_ARM_ENCOUNTERS == 20_480
    assert contracts.ACTION_WORD_DOMAIN is None
    assert "action" not in contracts.DISTURBANCE_STREAMS

    spec = EncounterSpec(RouteClass.SHORT, 1, 8)
    tape = FixtureTape.constant(spec, normal=0.0, uniform=0.5)
    assert not hasattr(tape, "action")
    assert not hasattr(tape, "action_word")


def test_native_toolchain_artifact_and_abi_are_admitted_by_preactivity() -> None:
    toolchain = native_toolchain_identity()
    artifact = native_artifact_identity()
    native = preactivity.canonical_native_identity(
        toolchain_identity=toolchain,
        artifact_identity=artifact,
    )

    assert native["backend"] == "cpp"
    assert native["python_fallback"] is False
    assert native["full_reset_step_cpp"] is True
    assert native["abi_version"] == str(artifact["abi"]["abi_version"])
    assert native["source_sha256"] == artifact["source_sha256"]
    assert native["artifact_sha256"] == artifact["sha256"]
    assert "/fp:strict" in native["toolchain"]["compile_flags"]


def test_coordinate_proposal_remains_unbound_and_controller_free() -> None:
    proposal = contracts.coordinate_proposal()
    assert contracts.validate_coordinate_proposal(proposal) == proposal
    assert proposal["bound"] is False
    assert proposal["coordinate_rows_present"] is False
    assert proposal["production_words_present"] is False
    assert proposal["controller_free_tape_law"] == {
        "streams": list(contracts.DISTURBANCE_STREAMS),
        "action_stream_present": False,
        "action_word_generated": False,
        "action_word_consumed": False,
        "shared_across_arms_within_replicate": True,
        "counter_law": (
            "SHA-256(length-prefixed UTF-8 tuple); uniform=(uint32be+0.5)/2^32; "
            "fixed Box-Muller lower-lane pairs"
        ),
        "future_binding": "Root-authored exact row-set digest; absent from this proposal",
    }


@pytest.mark.parametrize("batch_width", (1, 8, 32))
def test_candidate_local_cpp_loader_preserves_literal_fixture_order(batch_width: int) -> None:
    cases = _literal_cases(batch_width)
    library = require_cpp_batched_backend()
    results = run_native_batch(cases)

    assert require_cpp_batched_backend() is library
    assert len(results) == batch_width
    assert [result.logical_tag for result in results] == [case.logical_tag for case in cases]
    assert [result.spec for result in results] == [case.spec for case in cases]
    assert [result.arm for result in results] == [case.arm for case in cases]


def test_preactivity_identities_change_or_fail_closed_when_tampered(tmp_path: Path) -> None:
    source = tmp_path / "literal_native_source"
    source.write_bytes(b"int literal_fixture = 1;\n")
    native = _literal_native_identity()
    value = preactivity.collect_preactivity_identity(
        source_paths={"fixture/native_source": source},
        config_facts={"batch_widths": [1, 8, 32], "literal_fixture": True},
        native_identity=native,
    )
    assert preactivity.validate_preactivity_identity(value) == value

    initial_source = preactivity.canonical_source_identity({"fixture/native_source": source})
    source.write_bytes(b"int literal_fixture = 2;\n")
    changed_source = preactivity.canonical_source_identity({"fixture/native_source": source})
    assert changed_source["source_set_sha256"] != initial_source["source_set_sha256"]

    tampered_config_identity = dict(value["identity"])
    tampered_config_identity["config"] = {"batch_widths": [1, 8], "literal_fixture": True}
    with pytest.raises(preactivity.PreactivityError, match="config digest differs"):
        preactivity.validate_preactivity_identity(
            _with_resealed_identity(identity=tampered_config_identity)
        )

    tampered_schema_identity = dict(value["identity"])
    tampered_schema_identity["schema_identity"] = {"serializer": "tampered"}
    with pytest.raises(preactivity.PreactivityError, match="schema identity differs"):
        preactivity.validate_preactivity_identity(
            _with_resealed_identity(identity=tampered_schema_identity)
        )

    with pytest.raises(preactivity.PreactivityError, match="not full-host C\\+\\+"):
        preactivity.validate_native_identity({**native, "python_fallback": True})


def test_preactivity_collects_only_identity_and_creates_no_activity_objects(tmp_path: Path) -> None:
    source = tmp_path / "literal_native_source"
    source.write_bytes(b"int preactivity_only = 1;\n")
    identity = preactivity.collect_preactivity_identity(
        source_paths={"fixture/native_source": source},
        config_facts={"batch_widths": [1, 8, 32], "fixture_mode": "literal"},
        native_identity=_literal_native_identity(),
    )
    assert preactivity.validate_preactivity_identity(identity) == identity
    assert identity["identity"]["activity_boundary"] == {
        "preactivity_only": True,
        "coordinate_binding_present": False,
        "coordinate_rows_present": False,
        "production_words_materialized": False,
        "action_word_domain_present": False,
        "controller_ticks_executed": False,
        "scientific_results_present": False,
    }
    assert sorted(path.name for path in tmp_path.iterdir()) == ["literal_native_source"]
