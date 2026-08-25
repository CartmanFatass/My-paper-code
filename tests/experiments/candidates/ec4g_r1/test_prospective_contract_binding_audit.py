from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

from experiments.candidates.ec4g_r1.prospective_contract_binding_audit import (
    AuditBranch,
    COHERENCE_FIELDS,
    DECLARATION_KIND,
    INDEX_PATH,
    MappingSnapshotReader,
    PostFreezeEvent,
    PUBLICATION_COMMIT,
    RESULT_PATH,
    ROLE_IDS,
    RUNNER_PATH,
    SEED_INVENTORY_PATHS,
    SOURCE_PATH,
    TEST_PATH,
    audit_frozen_inventory,
    freeze_inventory,
    freeze_publication_inventory,
)


SOURCE_REVISION = "a" * 40


def _base_blobs(*, result: str = "{}", index: str | None = None) -> dict[str, str]:
    if index is None:
        index = "\n".join(f"`{path}`" for path in SEED_INVENTORY_PATHS[:-1])
    return {
        RESULT_PATH: result,
        SOURCE_PATH: "# source fixture\n",
        RUNNER_PATH: "# runner fixture\n",
        TEST_PATH: "# test fixture\n",
        INDEX_PATH: index,
    }


def _coherence() -> dict[str, str]:
    values = {
        "population_id": "fixture-population",
        "horizon_id": "fixture-horizon",
        "unit_id": "fixture-unit",
        "snapshot_commit": PUBLICATION_COMMIT,
        "domain_id": "fixture-domain",
        "ordering_id": "fixture-ordering",
        "serialization_id": "fixture-serialization",
        "freeze_order_id": "fixture-freeze-order",
    }
    assert tuple(values) == COHERENCE_FIELDS
    return values


def _complete_document(*, duplicate_role: str | None = None) -> dict[str, object]:
    inventory_paths = list(SEED_INVENTORY_PATHS)
    source_blob_sha256 = hashlib.sha256(b"# source fixture\n").hexdigest()
    objects: list[dict[str, object]] = []
    for ordinal, role in enumerate(ROLE_IDS):
        item = {
            "coherence": _coherence(),
            "freeze_ordinal": ordinal,
            "frozen_before_inspection": True,
            "object_id": f"fixture:{role}:v1",
            "role": role,
            "source_blob_sha256": source_blob_sha256,
            "source_commit": PUBLICATION_COMMIT,
            "source_path": SOURCE_PATH,
            "source_fragment": f"fixture-object-{ordinal}",
            "total": True,
        }
        objects.append(item)
        if duplicate_role == role:
            duplicate = dict(item)
            duplicate["object_id"] = f"fixture:{role}:duplicate"
            objects.append(duplicate)
    return {
        "document_kind": DECLARATION_KIND,
        "freeze_manifest": {
            "inventory_paths": inventory_paths,
            "publication_commit": PUBLICATION_COMMIT,
            "role_order": list(ROLE_IDS),
        },
        "objects": objects,
        "schema_version": 1,
    }


def _inventory(document: dict[str, object] | None = None):
    result = "{}" if document is None else json.dumps(document, separators=(",", ":"))
    return freeze_inventory(MappingSnapshotReader(_base_blobs(result=result)))


def _audit(inventory, **kwargs):
    return audit_frozen_inventory(
        inventory,
        source_revision=SOURCE_REVISION,
        run_id="fixture-run",
        **kwargs,
    ).payload()


def test_real_publication_inventory_freezes_exact_five_paths_before_role_inspection():
    repository_root = Path(__file__).resolve().parents[4]
    inventory = freeze_publication_inventory(repository_root)

    assert inventory.valid
    assert inventory.paths == SEED_INVENTORY_PATHS
    assert inventory.resolved_commit == PUBLICATION_COMMIT
    assert len({entry.path for entry in inventory.entries}) == 5
    assert all(entry.public_locator.endswith(entry.path) for entry in inventory.entries)


def test_publication_snapshot_technical_smoke_is_partial_and_retains_fourteen_missing_witnesses():
    repository_root = Path(__file__).resolve().parents[4]
    payload = _audit(freeze_publication_inventory(repository_root))

    assert payload["terminal_branch"] == AuditBranch.PARTIAL_OR_INCOHERENT_BINDING.value
    assert len(payload["role_witness_table"]) == 14
    assert len(payload["missing_witnesses"]) == 14
    assert payload["first_failure"]["role"] == "objective_contract"
    assert payload["activity_counts"]["registered_audit_runs"] == 0
    assert payload["activity_counts"]["role_inspections"] == 14
    assert all(
        witness["negative_evidence"][0]["note"]
        == "A1 result is negative evidence only, never a role object"
        for witness in payload["missing_witnesses"]
    )


def test_invalid_freeze_has_first_precedence_and_never_inspects_roles():
    blobs = _base_blobs()
    del blobs[TEST_PATH]
    payload = _audit(freeze_inventory(MappingSnapshotReader(blobs)))

    assert payload["terminal_branch"] == AuditBranch.INVENTORY_FREEZE_INVALID.value
    assert payload["freeze_failures"]
    assert payload["activity_counts"]["role_inspections"] == 0
    assert {row["status"] for row in payload["role_witness_table"]} == {"NOT_INSPECTED"}


def test_post_freeze_event_precedes_binding_inspection_and_is_retained():
    event = PostFreezeEvent("ADD_PATH", "attempted post-inspection inventory extension", "docs/new.json")
    payload = _audit(_inventory(_complete_document()), post_freeze_events=(event,))

    assert payload["terminal_branch"] == AuditBranch.POST_FREEZE_OBJECT_OR_REPAIR.value
    assert payload["post_freeze_witnesses"] == [event.payload()]
    assert payload["activity_counts"]["role_inspections"] == 0


def test_ambiguous_binding_precedes_missing_and_retains_both_witness_sets():
    document = _complete_document(duplicate_role="objective_contract")
    document["objects"] = [
        item for item in document["objects"] if item["role"] != "deployed_measure_m"
    ]
    payload = _audit(_inventory(document))

    assert payload["terminal_branch"] == AuditBranch.AMBIGUOUS_BINDING.value
    assert payload["first_failure"]["role"] == "objective_contract"
    assert len(payload["ambiguous_witnesses"]) == 1
    assert [item["role"] for item in payload["missing_witnesses"]] == ["deployed_measure_m"]


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    (
        (lambda item: item.update(total=False), "NON_TOTAL_OBJECT"),
        (lambda item: item.update(source_path="docs/post-freeze.json"), "SOURCE_OUTSIDE_FROZEN_INVENTORY"),
        (lambda item: item["coherence"].update(horizon_id="other-horizon"), "CROSS_OBJECT_COHERENCE_MISMATCH"),
        (lambda item: item.update(source_blob_sha256="0" * 64), "SOURCE_BLOB_DIGEST_MISMATCH"),
    ),
)
def test_partial_or_incoherent_binding_fails_closed_without_repair(mutation, expected_code):
    document = _complete_document()
    target = document["objects"][6]
    mutation(target)
    payload = _audit(_inventory(document))

    codes = {item["code"] for item in payload["incoherent_witnesses"]}
    assert payload["terminal_branch"] == AuditBranch.PARTIAL_OR_INCOHERENT_BINDING.value
    assert expected_code in codes
    assert payload["eligible_to_consider_new_frozen_census"] is False
    assert payload["route_status"] == "PARKED_PENDING_FUTURE_COMPLETE_PROSPECTIVE_CONTRACT"


def test_complete_preexisting_binding_requires_all_fourteen_exact_coherent_objects():
    payload = _audit(_inventory(_complete_document()))

    assert payload["terminal_branch"] == AuditBranch.COMPLETE_PREEXISTING_BINDING.value
    assert payload["first_failure"] is None
    assert {row["status"] for row in payload["role_witness_table"]} == {"BOUND"}
    assert payload["eligible_to_consider_new_frozen_census"] is True
    assert payload["route_status"] == "ELIGIBLE_TO_CONSIDER_NEW_FROZEN_CENSUS"
    assert payload["result_revision"] is None
    assert payload["technical_acceptance"]["owner"] == "code_project_manager"


def test_all_runtime_and_stochastic_activity_is_exactly_zero():
    payload = _audit(_inventory())
    counts = payload["activity_counts"]
    for key in (
        "environment_transitions",
        "policy_calls",
        "learner_calls",
        "trainer_calls",
        "optimizer_updates",
        "return_evaluations",
        "model_fits",
        "stochastic_calls",
    ):
        assert counts[key] == 0


def test_runner_existing_output_aborts_before_inventory_freeze(monkeypatch, tmp_path):
    from scripts import run_ec4g_a2_prospective_contract_binding_audit as runner

    output = tmp_path / "existing.json"
    output.write_text("existing", encoding="utf-8")
    monkeypatch.setattr(runner, "_source_revision", lambda: SOURCE_REVISION)
    monkeypatch.setattr(
        runner,
        "freeze_publication_inventory",
        lambda _root: pytest.fail("freeze must not run after output preflight failure"),
    )

    with pytest.raises(SystemExit, match="refusing to overwrite"):
        runner.main(
            [
                "--source-revision",
                SOURCE_REVISION,
                "--run-id",
                "fixture-run",
                "--output",
                str(output),
            ]
        )
    assert output.read_text(encoding="utf-8") == "existing"


def test_runner_writes_one_canonical_registered_artifact(monkeypatch, tmp_path):
    from scripts import run_ec4g_a2_prospective_contract_binding_audit as runner

    output = tmp_path / "result.json"
    inventory = _inventory()
    monkeypatch.setattr(runner, "_source_revision", lambda: SOURCE_REVISION)
    monkeypatch.setattr(runner, "freeze_publication_inventory", lambda _root: inventory)

    assert runner.main(
        [
            "--source-revision",
            SOURCE_REVISION,
            "--run-id",
            "fixture-run",
            "--output",
            str(output),
        ]
    ) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["activity_counts"]["registered_audit_runs"] == 1
    assert payload["terminal_branch"] == AuditBranch.PARTIAL_OR_INCOHERENT_BINDING.value
    assert payload["publication_commit"] == PUBLICATION_COMMIT
    assert payload["source_commit"] == SOURCE_REVISION
    assert output.read_bytes().endswith(b"\n")
