from copy import deepcopy
from pathlib import Path

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts import core


def test_exact_manifest_cells_and_literal_containment(manifest_factory):
    manifest = manifest_factory()
    validated = core.validate_manifest(manifest)
    assert len(validated["cells"]) == 10
    assert validated["training"]["checkpoints"] == [512]
    assert validated["seed_blocks"] == list(core.REQUIRED_SEED_BLOCKS)
    assert validated["inference"]["status"] == "SIMULTANEOUS_MEAN_INFERENCE_UNRESOLVED_AT_24_BLOCKS"
    assert validated["inference"]["active_method"] is None
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
    manifest = manifest_factory()
    manifest["training"]["checkpoints"] = [64, 512]
    with pytest.raises(core.ContractError, match="exactly.*512"):
        core.validate_manifest(manifest)
    manifest = manifest_factory()
    manifest["schema"] = core.FRRIE_MANIFEST_V1
    with pytest.raises(core.ContractError, match="V2"):
        core.validate_manifest(manifest)
    manifest = manifest_factory()
    manifest["implementation_contract"]["rscf"]["factual_identity_audit"]["new_rng_addresses"] = 1
    with pytest.raises(core.ContractError, match="implementation_contract"):
        core.validate_manifest(manifest)
    manifest = manifest_factory()
    manifest["implementation_contract"]["dgp_native"]["within_slot_order"][0] = "OBSERVE"
    with pytest.raises(core.ContractError, match="implementation_contract"):
        core.validate_manifest(manifest)
    manifest = manifest_factory()
    manifest["implementation_contract"]["actor"]["gru"]["candidate"] = "RESET_AFTER_CANDIDATE"
    with pytest.raises(core.ContractError, match="implementation_contract"):
        core.validate_manifest(manifest)


def test_manifest_binds_minibatch_order_and_absolute_non_nested_roots(manifest_factory, tmp_path):
    manifest = manifest_factory()
    manifest["training"]["episode_roster_order"] = [9] * 32 + [15] * 31 + [9]
    with pytest.raises(core.ContractError, match="episode_roster_order"):
        core.validate_manifest(manifest)

    manifest = manifest_factory()
    manifest["roots"]["checkpoint"] = str(Path(manifest["roots"]["output"]) / "checkpoints")
    with pytest.raises(core.ContractError, match="nested"):
        core.validate_manifest(manifest)

    manifest = manifest_factory()
    manifest["roots"]["checkpoint"] = manifest["roots"]["output"]
    with pytest.raises(core.ContractError, match="distinct"):
        core.validate_manifest(manifest)


def test_manifest_packet_contract_excludes_only_its_locator(manifest_factory):
    manifest = manifest_factory()
    first = core.manifest_packet_contract(manifest)
    manifest["sealed_seed_packet"] = {"path": "elsewhere"}
    assert core.manifest_packet_contract(manifest) == first
    manifest["thresholds"][core.THRESHOLD_FIELDS[0]] = 0.2
    assert core.manifest_packet_contract(manifest) != first
