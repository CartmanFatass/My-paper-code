import ast
from pathlib import Path

from experiments.candidates.capability_bound_semantic_currentness.factorial import construct_world
from experiments.candidates.capability_bound_semantic_currentness.rng import canonical_bytes, nuisance_id
from experiments.candidates.capability_bound_semantic_currentness.schema import (
    AccessState,
    BindingState,
    NuisanceCoordinate,
    OwnerState,
    PayloadState,
    SemanticState,
)


def test_counter_address_is_stable_and_has_no_intervention_inputs():
    coordinate = NuisanceCoordinate(1, 0, 1, 0, 1, 0, 1)
    left = construct_world(OwnerState.LIVE, SemanticState.PERSIST, BindingState.AUTHENTIC, AccessState.OPEN, PayloadState.RECEIVER_CORRECT, coordinate)
    right = construct_world(OwnerState.BROKEN, SemanticState.REFRESH, BindingState.WHOLE_CARRIER_REASSOCIATED, AccessState.BINDING_GATED, PayloadState.NATIVE_NEUTRAL, coordinate)
    assert left.nuisance_id == right.nuisance_id == nuisance_id(coordinate)
    assert nuisance_id(coordinate) != nuisance_id(NuisanceCoordinate(1, 0, 1, 0, 1, 0, 0))


def test_phase_changes_value_not_provenance_and_payload_inventory_is_paired():
    zero = NuisanceCoordinate(0, 0, 1, 1, 0, 0, 0)
    phased = NuisanceCoordinate(0, 0, 1, 1, 1, 0, 0)
    left = construct_world(OwnerState.LIVE, SemanticState.PERSIST, BindingState.AUTHENTIC, AccessState.OPEN, PayloadState.RECEIVER_CORRECT, zero)
    right = construct_world(OwnerState.LIVE, SemanticState.PERSIST, BindingState.AUTHENTIC, AccessState.OPEN, PayloadState.RECEIVER_CORRECT, phased)
    assert left.routed_carrier.body.payload_source_receiver == right.routed_carrier.body.payload_source_receiver == 0
    assert left.focal_need_value != right.focal_need_value
    swapped = construct_world(OwnerState.LIVE, SemanticState.PERSIST, BindingState.AUTHENTIC, AccessState.OPEN, PayloadState.SWAPPED, zero)
    assert left.issued_inventory == swapped.issued_inventory


def test_canonical_serialization_is_mapping_and_traversal_order_invariant_and_rng_imports_are_banned():
    assert canonical_bytes({"b": 2, "a": 1}) == canonical_bytes({"a": 1, "b": 2})
    package = Path("experiments/candidates/capability_bound_semantic_currentness")
    source = "\n".join(path.read_text(encoding="utf-8") for path in package.glob("*.py"))
    for banned in ("import random", "from random", "import numpy", "import torch", "np.random", "torch.rand"):
        assert banned not in source


def test_hashing_exists_only_in_the_private_typed_nuisance_primitive():
    package = Path("experiments/candidates/capability_bound_semantic_currentness")
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        hash_imports = [
            node for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            and (
                (isinstance(node, ast.Import) and any(alias.name == "hashlib" for alias in node.names))
                or (isinstance(node, ast.ImportFrom) and node.module == "hashlib")
            )
        ]
        if path.name == "rng.py":
            assert len(hash_imports) == 1
            counter = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_nuisance_digest")
            assert [argument.arg for argument in counter.args.args] == ["coordinate"]
            assert any(
                isinstance(node, ast.Attribute) and node.attr == "sha256"
                for node in ast.walk(counter)
            )
            assert not any(isinstance(node, ast.FunctionDef) and node.name == "counter_digest" for node in tree.body)
            exported = next(node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets))
            assert "counter_digest" not in ast.unparse(exported)
        else:
            assert not hash_imports
            assert "sha256" not in path.read_text(encoding="utf-8")
