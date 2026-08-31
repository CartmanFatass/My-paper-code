from copy import deepcopy

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts import core


def test_exact_manifest_cells_and_literal_containment(manifest_factory):
    manifest = manifest_factory(checkpoints=(64, 512))
    manifest["work_parity"]["PHY_TRUST"]["checkpoint_io"] = 2
    manifest["work_parity"]["EDGE_FLEX"]["checkpoint_io"] = 2
    validated = core.validate_manifest(manifest)
    assert len(validated["cells"]) == 10
    assert validated["arms"][0]["beta_projection"] == [-0.15, 0.15]
    assert validated["arms"][1]["beta_projection"] == [-1.5, 1.5]
    assert -0.15 < 0.60 < 1.5 and not (-0.15 <= 0.60 <= 0.15)


def test_manifest_rejects_undeclared_fields_and_missing_threshold(manifest_factory):
    manifest = manifest_factory()
    manifest["host"]["result_override"] = 1
    with pytest.raises(core.ContractError, match="undeclared"):
        core.validate_manifest(manifest)
    manifest = manifest_factory()
    del manifest["thresholds"][core.THRESHOLD_FIELDS[0]]
    with pytest.raises(core.ContractError):
        core.validate_manifest(manifest)


def test_manifest_packet_contract_excludes_only_its_locator(manifest_factory):
    manifest = manifest_factory()
    first = core.manifest_packet_contract(manifest)
    manifest["sealed_seed_packet"] = {"path": "elsewhere"}
    assert core.manifest_packet_contract(manifest) == first
    manifest["thresholds"][core.THRESHOLD_FIELDS[0]] = 0.2
    assert core.manifest_packet_contract(manifest) != first
