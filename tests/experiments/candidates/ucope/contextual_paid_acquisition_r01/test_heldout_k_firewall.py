import ast
import gzip
import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.ucope.contextual_paid_acquisition_r01 import contract
from experiments.candidates.ucope.contextual_paid_acquisition_r01.training import _load_seed_rows


PACKAGE_ROOT = Path("experiments/candidates/ucope/contextual_paid_acquisition_r01")
TRAINING_PATHS = ("support.py", "training.py", "model.py", "checkpoint.py")


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]


def test_heldout_periods_never_enter_support_training_or_checkpoint_selection():
    for filename in TRAINING_PATHS:
        source = (PACKAGE_ROOT / filename).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=filename)
        loaded = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
        assert "K_TEST" not in loaded, f"held-out K loaded by {filename}"
    training = (PACKAGE_ROOT / "training.py").read_text(encoding="utf-8").lower()
    assert "validation selection" not in training or "no validation selection" in training
    assert "early_stop" not in training
    assert "best_checkpoint" not in training


def test_training_loader_runtime_rejects_even_period_rows(tmp_path):
    materialized = tmp_path / "materialized"
    materialized.mkdir()
    support = {
        "mode": contract.TEST_ONLY_MODE,
        "episodes_per_context": 160,
        "materialized_files": {},
    }
    seed = contract.SEED_SLOTS[0]
    for index, cell in enumerate(contract.default_manifest()["context_ids"]):
        filename = f"cell-{index}.jsonl.gz"
        with gzip.open(materialized / filename, "wt", encoding="utf-8") as stream:
            stream.write(json.dumps({"seed_slot": seed, "context_id": cell, "period": contract.K_TEST[0]}) + "\n")
        support["materialized_files"][f"{seed}|{cell}"] = {"filename": filename}
    with pytest.raises(ValueError, match="held-out"):
        _load_seed_rows(tmp_path / "support-preflight.json", seed, support)


def test_dependency_firewall_has_no_historical_import_edges():
    forbidden = (
        "variable_k_paid_probe_r01_r03", "production_validation", "production_contract",
        "native_backend", "s2_construction", "endogenous_paid_count_acquisition",
        "persistent_count_state", "crossed_evaluation",
    )
    for path in PACKAGE_ROOT.glob("*.py"):
        for node in _imports(path):
            names = [alias.name for alias in node.names]
            module = getattr(node, "module", "") or ""
            rendered = " ".join((module, *names)).lower()
            assert not any(token in rendered for token in forbidden), f"forbidden dependency in {path.name}: {rendered}"


def test_hash_primitives_and_digest_fields_are_confined_to_counter_rng():
    forbidden_fields = {
        "contract_spec_digest", "manifest_digest", "tape_digest", "dataset_digest", "support_digest",
        "artifact_digest", "state_digest", "checkpoint_digests", "rng_contract_digest",
    }
    for path in PACKAGE_ROOT.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        if path.name == "rng.py":
            assert "hashlib" in source and "sha256" in source
            continue
        assert forbidden_fields.isdisjoint(source.split())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                rendered = " ".join((getattr(node, "module", "") or "", *(alias.name for alias in node.names)))
                assert "hashlib" not in rendered
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                assert name not in {"hash", "sha256", "md5", "blake2b", "blake2s", "digest", "hexdigest"}
        assert not any(field in source for field in forbidden_fields)


def test_importing_cli_and_preflight_loads_neither_torch_nor_old_runtime():
    code = r'''
import sys
import experiments.candidates.ucope.contextual_paid_acquisition_r01.cli
import experiments.candidates.ucope.contextual_paid_acquisition_r01.support
bad = [name for name in sys.modules if name == "torch" or name.startswith("torch.") or "variable_k_paid_probe_r01_r03" in name or name.endswith("native_backend")]
assert not bad, bad
'''
    result = subprocess.run([sys.executable, "-c", code], cwd=Path.cwd(), text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_evaluation_is_not_executed_on_import(monkeypatch):
    module = importlib.import_module("experiments.candidates.ucope.contextual_paid_acquisition_r01.evaluation")
    monkeypatch.setattr(module, "evaluate_heldout_cells", lambda *args, **kwargs: pytest.fail("evaluation executed"))
    importlib.reload(importlib.import_module("experiments.candidates.ucope.contextual_paid_acquisition_r01.cli"))


def test_checkpoint_evaluation_loads_one_validated_snapshot_only():
    source = (PACKAGE_ROOT / "evaluation.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "load_checkpoint"
    ]
    assert len(calls) == 1
