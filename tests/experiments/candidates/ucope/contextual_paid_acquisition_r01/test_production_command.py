from copy import deepcopy
import ast
import inspect
import json
from pathlib import Path

import pytest

from experiments.candidates.ucope.contextual_paid_acquisition_r01 import contract
from experiments.candidates.ucope.contextual_paid_acquisition_r01 import production
from experiments.candidates.ucope.contextual_paid_acquisition_r01 import training


def _accepted_resource_record():
    return {
        "python_major_minor": [3, 10],
        "torch_version": "2.7.0+cpu",
        "torch_cuda_version": None,
        "torch_cuda_available": False,
        "workers": 1,
        "torch_intraop_threads": 1,
        "torch_interop_threads": 1,
        "batch_size": 256,
        "model_checkpoints_per_seed": 1,
        "checkpoint_cadence_batches": 1,
        "deterministic_algorithms": True,
        "estimated_peak_memory_bytes": 2 * 1024**3,
        "minimum_live_available_memory_bytes": 4 * 1024**3,
        "minimum_free_disk_bytes": 4 * 1024**3,
        "projected_scratch_bytes": 64 * 1024**2,
        "projected_durable_bytes": 64 * 1024**2,
        "scratch_ceiling_bytes": 256 * 1024**2,
        "durable_ceiling_bytes": 256 * 1024**2,
        "scratch_safe": True,
        "durable_safe": True,
        "live_available_memory_bytes": 5 * 1024**3,
        "live_free_disk_bytes": 20 * 1024**3,
        "projected_result_wall_seconds": 3_600,
        "maximum_result_wall_seconds": 3_600,
        "wall_safe": True,
    }


def _displayed_support_record(manifest, minimum=361):
    return {
        "complete": True,
        "mode": "PRODUCTION",
        "contract_spec": manifest["contract_spec"],
        "seed_context_counts": {
            "representative": {"displayed_short_count": {str(index): minimum + index for index in range(7)}}
        },
    }


class _FakeCuda:
    @staticmethod
    def is_available():
        return False


class _FakeTorch:
    __version__ = "2.7.0+cpu"
    version = type("Version", (), {"cuda": None})()
    cuda = _FakeCuda()
    threads = None
    interop_threads = None
    deterministic = False

    @classmethod
    def set_num_threads(cls, value):
        cls.threads = value

    @classmethod
    def get_num_threads(cls):
        return cls.threads

    @classmethod
    def set_num_interop_threads(cls, value):
        cls.interop_threads = value

    @classmethod
    def get_num_interop_threads(cls):
        return cls.interop_threads

    @classmethod
    def use_deterministic_algorithms(cls, value):
        cls.deterministic = value

    @classmethod
    def are_deterministic_algorithms_enabled(cls):
        return cls.deterministic


def _patch_runtime(monkeypatch, *, available_memory, free_disk):
    _FakeTorch.threads = None
    _FakeTorch.interop_threads = None
    _FakeTorch.deterministic = False
    monkeypatch.setattr(production.sys, "version_info", (3, 10, 20))
    monkeypatch.setattr(production.importlib, "import_module", lambda name: _FakeTorch)
    monkeypatch.setattr(production, "_available_memory_bytes", lambda: available_memory)
    monkeypatch.setattr(
        production.shutil,
        "disk_usage",
        lambda path: type("Usage", (), {"free": free_disk})(),
    )
    monkeypatch.setattr(production, "PROJECTED_RESULT_WALL_SECONDS", 3_600)


def test_production_manifest_is_direct_create_once_and_freezes_total_work(tmp_path):
    path = tmp_path / "production-manifest.json"
    assert production.create_production_manifest(path) == path
    value = json.loads(path.read_text(encoding="utf-8"))
    assert value == contract.default_manifest(contract.PRODUCTION_MODE)
    assert value["contract_spec"]["workload_totals"] == {
        "seeds": 10,
        "contexts": 8,
        "root_episodes": 1_638_400,
        "conditional_probe_tails": 819_200,
        "optimizer_updates": 6_400,
    }
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        production.create_production_manifest(path)
    assert path.read_bytes() == original


def test_runtime_failure_lists_issues_before_support_materialization(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(contract.default_manifest()), encoding="utf-8")
    called = []
    monkeypatch.setattr(production, "_runtime_resource_record", lambda output: (_ for _ in ()).throw(
        production.ProductionPreflightError("Python 3.10 required; torch 2.7.0+cpu unavailable; insufficient live memory; insufficient free disk")
    ))
    monkeypatch.setattr(production, "_materialize_support", lambda *args: called.append(args))
    with pytest.raises(production.ProductionPreflightError, match="Python 3.10 required") as caught:
        production.preflight_production(manifest, tmp_path / "preflight")
    assert "insufficient live memory" in str(caught.value)
    assert "insufficient free disk" in str(caught.value)
    assert called == []
    assert not (tmp_path / "preflight").exists()


def test_runtime_record_enforces_deterministic_cpu_torch_and_wall_gate(tmp_path, monkeypatch):
    _patch_runtime(
        monkeypatch,
        available_memory=5 * 1024**3,
        free_disk=5 * 1024**3,
    )
    value = production._runtime_resource_record(tmp_path / "output")
    assert value["deterministic_algorithms"] is True
    assert value["wall_safe"] is True
    assert value["projected_result_wall_seconds"] == 3600
    assert value["scratch_ceiling_bytes"] == 256 * 1024**2
    assert value["durable_ceiling_bytes"] == 256 * 1024**2
    assert value["projected_scratch_bytes"] == 64 * 1024**2
    assert value["projected_durable_bytes"] == 64 * 1024**2
    assert value["scratch_safe"] is value["durable_safe"] is True
    monkeypatch.setattr(production, "PROJECTED_RESULT_WALL_SECONDS", 3601)
    with pytest.raises(production.ProductionPreflightError, match="observed 3601"):
        production._runtime_resource_record(tmp_path / "output")


@pytest.mark.parametrize(
    "available_memory,accepted",
    [(4 * 1024**3 - 1, False), (4 * 1024**3, True)],
)
def test_live_physical_memory_boundary_is_exact(tmp_path, monkeypatch, available_memory, accepted):
    _patch_runtime(
        monkeypatch,
        available_memory=available_memory,
        free_disk=4 * 1024**3,
    )
    if accepted:
        value = production._runtime_resource_record(tmp_path / "output")
        assert value["live_available_memory_bytes"] == 4 * 1024**3
    else:
        with pytest.raises(production.ProductionPreflightError, match="insufficient live memory"):
            production._runtime_resource_record(tmp_path / "output")


@pytest.mark.parametrize(
    "free_disk,accepted",
    [(4 * 1024**3 - 1, False), (4 * 1024**3, True)],
)
def test_free_disk_boundary_is_exact(tmp_path, monkeypatch, free_disk, accepted):
    _patch_runtime(
        monkeypatch,
        available_memory=4 * 1024**3,
        free_disk=free_disk,
    )
    if accepted:
        value = production._runtime_resource_record(tmp_path / "output")
        assert value["live_free_disk_bytes"] == 4 * 1024**3
    else:
        with pytest.raises(production.ProductionPreflightError, match="insufficient free disk"):
            production._runtime_resource_record(tmp_path / "output")


@pytest.mark.parametrize(
    "projection_name,ceiling,message",
    [
        ("PROJECTED_SCRATCH_BYTES", 256 * 1024**2, "projected scratch"),
        ("PROJECTED_DURABLE_BYTES", 256 * 1024**2, "projected durable"),
    ],
)
def test_projected_storage_failure_precedes_support_activity(
    tmp_path, monkeypatch, projection_name, ceiling, message
):
    _patch_runtime(
        monkeypatch,
        available_memory=5 * 1024**3,
        free_disk=5 * 1024**3,
    )
    monkeypatch.setattr(production, projection_name, ceiling + 1)
    materialized = []
    monkeypatch.setattr(
        production, "_materialize_support", lambda *args: materialized.append(args)
    )
    output_root = tmp_path / "preflight"
    with pytest.raises(production.ProductionPreflightError, match=message):
        production.preflight_production(contract.default_manifest(), output_root)
    assert materialized == []
    assert not output_root.exists()


def test_run_belief_rechecks_fresh_memory_before_old_preflight_or_training(tmp_path, monkeypatch):
    events = []

    def refuse_resources(_output_root):
        events.append("resources")
        raise production.ProductionPreflightError("insufficient live memory")

    monkeypatch.setattr(production, "_runtime_resource_record", refuse_resources)
    monkeypatch.setattr(
        production,
        "validate_production_preflight",
        lambda *args: pytest.fail("old preflight validated before fresh resources"),
    )
    monkeypatch.setattr(
        production,
        "_complete_production_checkpoints",
        lambda *args: pytest.fail("training reached after resource refusal"),
    )
    with pytest.raises(production.ProductionPreflightError, match="live memory"):
        production.run_belief(
            contract.default_manifest(),
            tmp_path / "old-preflight.json",
            tmp_path / "result",
        )
    assert events == ["resources"]
    assert not (tmp_path / "result").exists()


def test_public_single_seed_training_cannot_bypass_production_resources(monkeypatch):
    monkeypatch.setattr(
        training,
        "validate_support",
        lambda *args: {"mode": contract.PRODUCTION_MODE},
    )
    monkeypatch.setattr(
        training,
        "_train_one_seed_from_validated_support",
        lambda *args, **kwargs: pytest.fail("production learner constructed through public seam"),
    )
    with pytest.raises(ValueError, match="TEST_ONLY"):
        training.train_one_seed(
            contract.SEED_SLOTS[0],
            "unused-support.json",
            "unused-checkpoint.pt",
        )


def test_resource_revision_admits_the_guarded_projection_exactly():
    assert production.PROJECTED_RESULT_WALL_SECONDS == 3_600
    assert production.PROJECTED_RESULT_WALL_SECONDS == production.MAXIMUM_RESULT_WALL_SECONDS
    assert production.PROJECTED_SCRATCH_BYTES < production.SCRATCH_CEILING_BYTES
    assert production.PROJECTED_DURABLE_BYTES < production.DURABLE_CEILING_BYTES
    assert production.PRODUCTION_PREFLIGHT_FORMAT.endswith("_V3")


def test_production_preflight_publishes_one_complete_atomic_envelope(tmp_path, monkeypatch):
    manifest_path = tmp_path / "manifest.json"
    manifest = contract.default_manifest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    support_record = _displayed_support_record(manifest)

    monkeypatch.setattr(production, "_runtime_resource_record", lambda output: _accepted_resource_record())
    monkeypatch.setattr(production, "PROJECTED_RESULT_WALL_SECONDS", 3600)

    def materialize(manifest_arg, root):
        root = Path(root)
        root.mkdir()
        artifact = root / "support-preflight.json"
        artifact.write_text(json.dumps(support_record), encoding="utf-8")
        return artifact

    monkeypatch.setattr(production, "_materialize_support", materialize)
    monkeypatch.setattr(production, "_validate_support", lambda path, manifest_arg: deepcopy(support_record))
    output = tmp_path / "accepted-preflight"
    artifact = production.preflight_production(manifest_path, output)
    assert artifact == output / "production-preflight.json"
    envelope = json.loads(artifact.read_text(encoding="utf-8"))
    assert envelope == {
        "format": production.PRODUCTION_PREFLIGHT_FORMAT,
        "schema_version": contract.SCHEMA_VERSION,
        "contract_id": contract.CONTRACT_ID,
        "mode": "PRODUCTION",
        "manifest": manifest,
        "resources": _accepted_resource_record(),
        "workload": production.PRODUCTION_WORKLOAD,
        "displayed_count_support": {"floor": 256, "global_minimum": 361},
        "support_artifact": "support/support-preflight.json",
        "support_record": support_record,
        "complete": True,
        "optimizer_updates": 0,
    }
    keys = set(production._all_mapping_keys(envelope))
    assert not any(token in key.lower() for key in keys for token in ("hash", "digest", "lease", "approval", "identity"))
    assert not list(tmp_path.glob(".accepted-preflight.staging-*"))


def test_run_production_uses_fixed_complete_seed_checkpoints_then_one_result(tmp_path, monkeypatch):
    manifest = contract.default_manifest()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    preflight_path = tmp_path / "accepted" / "production-preflight.json"
    preflight_path.parent.mkdir()
    preflight_path.write_text("{}", encoding="utf-8")
    support_path = preflight_path.parent / "support" / "support-preflight.json"
    support_path.parent.mkdir()
    support_path.write_text("{}", encoding="utf-8")
    support_record = {"mode": "PRODUCTION", "contract_spec": manifest["contract_spec"]}
    envelope = {"support_record": support_record}
    calls = []

    monkeypatch.setattr(production, "validate_production_preflight", lambda path, manifest_arg: deepcopy(envelope))
    monkeypatch.setattr(production, "_runtime_resource_record", lambda output: _accepted_resource_record())

    records = {}

    def train(seed, support_artifact, checkpoint, support, rows, resume_from=None):
        assert rows == [seed]
        checkpoint = Path(checkpoint)
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text(seed, encoding="utf-8")
        calls.append(("train", seed, checkpoint.name))
        records[seed] = {
            "seed_slot": seed, "mode": "PRODUCTION", "support_record": support_record,
            "completed_batches": 640, "total_batches": 640, "optimizer_updates": 640,
            "model_state": {}, "optimizer_state": {},
        }
        return {"complete_pass": True, "checkpoint_record": production._checkpoint_record(records[seed])}

    def evaluate(checkpoint):
        seed = Path(checkpoint).read_text(encoding="utf-8")
        calls.append(("evaluate", seed, Path(checkpoint).name))
        return type("Evaluation", (), {
            "seed_slot": seed,
            "checkpoint_record": production._checkpoint_record(records[seed]),
            "result_eligible": True,
        })()

    monkeypatch.setattr(production, "_train_seed", train)
    monkeypatch.setattr(production, "_load_seed_training_rows", lambda path, seed, support: [seed])
    monkeypatch.setattr(production, "_load_checkpoint", lambda path: deepcopy(records[Path(path).read_text(encoding="utf-8")]))
    monkeypatch.setattr(production, "_evaluate_checkpoint", evaluate)
    monkeypatch.setattr(production, "_build_complete_result", lambda **kwargs: {"format": "complete", "result": {"complete": True}})
    monkeypatch.setattr(production, "_publish_complete_result", lambda value, path: Path(path).write_text(json.dumps(value), encoding="utf-8") or Path(path))

    output_root = tmp_path / "run"
    result = production.run_belief(manifest_path, preflight_path, output_root)
    assert result == output_root / production.RESULT_FILENAME
    assert [event[0] for event in calls] == ["train"] * 10 + ["evaluate"] * 10
    for index, seed in enumerate(contract.SEED_SLOTS):
        name = f"checkpoint-{index:02d}.pt"
        assert calls[index] == ("train", seed, name)
        assert calls[10 + index] == ("evaluate", seed, name)
    assert json.loads(result.read_text(encoding="utf-8"))["result"]["complete"] is True


def test_run_production_rejects_partial_seed_before_heldout_evaluation(tmp_path, monkeypatch):
    manifest = contract.default_manifest()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    preflight_path = tmp_path / "production-preflight.json"
    preflight_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(production, "validate_production_preflight", lambda *args: {"support_record": {"mode": "PRODUCTION"}})
    monkeypatch.setattr(production, "_runtime_resource_record", lambda output: _accepted_resource_record())
    monkeypatch.setattr(production, "_train_seed", lambda *args, **kwargs: {"complete_pass": False, "checkpoint_record": {}})
    monkeypatch.setattr(production, "_load_seed_training_rows", lambda path, seed, support: [seed])
    evaluated = []
    monkeypatch.setattr(production, "_evaluate_checkpoint", lambda path: evaluated.append(path))
    with pytest.raises(RuntimeError, match="complete deterministic checkpoint"):
        production.run_belief(manifest_path, preflight_path, tmp_path / "run")
    assert evaluated == []
    assert not (tmp_path / "run" / production.RESULT_FILENAME).exists()


def test_run_production_resumes_mixed_complete_partial_and_missing_checkpoints(tmp_path, monkeypatch):
    manifest = contract.default_manifest()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    preflight_path = tmp_path / "production-preflight.json"
    preflight_path.write_text("{}", encoding="utf-8")
    support_record = {"mode": "PRODUCTION"}
    monkeypatch.setattr(production, "validate_production_preflight", lambda *args: {"support_record": support_record})
    monkeypatch.setattr(production, "_runtime_resource_record", lambda output: _accepted_resource_record())
    output_root = tmp_path / "run"
    existing = set(contract.SEED_SLOTS[::2])
    partial_seed = contract.SEED_SLOTS[1]
    complete_raw = {}
    for seed in existing:
        path = production.checkpoint_path(output_root, seed)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(seed, encoding="utf-8")
        complete_raw[seed] = {
            "seed_slot": seed,
            "mode": "PRODUCTION",
            "support_record": support_record,
            "completed_batches": 640,
            "total_batches": 640,
            "optimizer_updates": 640,
            "model_state": {},
            "optimizer_state": {},
        }
    partial_path = production.checkpoint_path(output_root, partial_seed)
    partial_path.write_text(partial_seed, encoding="utf-8")
    partial_raw = {
        "seed_slot": partial_seed, "mode": "PRODUCTION", "support_record": support_record,
        "completed_batches": 13, "total_batches": 640, "optimizer_updates": 13,
        "model_state": {}, "optimizer_state": {},
    }
    trained = []
    resume_arguments = {}

    fresh_raw = {}

    def train(seed, support_artifact, checkpoint, support, rows, resume_from=None):
        assert rows == [seed]
        checkpoint = Path(checkpoint)
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text(seed, encoding="utf-8")
        trained.append(seed)
        resume_arguments[seed] = resume_from
        fresh_raw[seed] = {
            "seed_slot": seed, "mode": "PRODUCTION", "support_record": support_record,
            "completed_batches": 640, "total_batches": 640, "optimizer_updates": 640,
            "model_state": {}, "optimizer_state": {},
        }
        return {"complete_pass": True, "checkpoint_record": production._checkpoint_record(fresh_raw[seed])}

    monkeypatch.setattr(production, "_train_seed", train)
    monkeypatch.setattr(production, "_load_seed_training_rows", lambda path, seed, support: [seed])
    def load(path):
        seed = Path(path).read_text(encoding="utf-8")
        if seed in fresh_raw:
            return deepcopy(fresh_raw[seed])
        if seed == partial_seed:
            return deepcopy(partial_raw)
        return deepcopy(complete_raw[seed])

    monkeypatch.setattr(production, "_load_checkpoint", load)

    def evaluate(path):
        seed = Path(path).read_text(encoding="utf-8")
        record = production._checkpoint_record(complete_raw[seed] if seed in existing else fresh_raw[seed])
        return type("Evaluation", (), {"seed_slot": seed, "checkpoint_record": record, "result_eligible": True})()

    monkeypatch.setattr(production, "_evaluate_checkpoint", evaluate)
    monkeypatch.setattr(production, "_build_complete_result", lambda **kwargs: {"result": {"complete": True}})
    monkeypatch.setattr(production, "_publish_complete_result", lambda value, path: Path(path).write_text("complete", encoding="utf-8"))
    production.run_belief(manifest_path, preflight_path, output_root)
    assert trained == [seed for seed in contract.SEED_SLOTS if seed not in existing]
    assert resume_arguments[partial_seed] == partial_path
    assert all(resume_arguments[seed] is None for seed in trained if seed != partial_seed)


@pytest.mark.parametrize("mutation", [
    lambda raw: raw.update(seed_slot=contract.SEED_SLOTS[1]),
    lambda raw: raw.update(support_record={"mode": "DRIFT"}),
])
def test_run_production_rejects_partial_or_mismatched_existing_checkpoint(tmp_path, monkeypatch, mutation):
    manifest = contract.default_manifest()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    preflight_path = tmp_path / "production-preflight.json"
    preflight_path.write_text("{}", encoding="utf-8")
    support_record = {"mode": "PRODUCTION"}
    monkeypatch.setattr(production, "validate_production_preflight", lambda *args: {"support_record": support_record})
    monkeypatch.setattr(production, "_runtime_resource_record", lambda output: _accepted_resource_record())
    destination = production.checkpoint_path(tmp_path / "run", contract.SEED_SLOTS[0])
    destination.parent.mkdir(parents=True)
    destination.write_text("checkpoint", encoding="utf-8")
    raw = {
        "seed_slot": contract.SEED_SLOTS[0], "mode": "PRODUCTION", "support_record": support_record,
        "completed_batches": 640, "total_batches": 640, "optimizer_updates": 640,
        "model_state": {}, "optimizer_state": {},
    }
    mutation(raw)
    monkeypatch.setattr(production, "_load_checkpoint", lambda path: raw)
    monkeypatch.setattr(production, "_load_seed_training_rows", lambda path, seed, support: [seed])
    evaluated = []
    monkeypatch.setattr(production, "_evaluate_checkpoint", lambda path: evaluated.append(path))
    with pytest.raises(RuntimeError, match="not a .*deterministic checkpoint"):
        production.run_belief(manifest_path, preflight_path, tmp_path / "run")
    assert evaluated == []


def test_phase_one_source_has_no_heldout_or_artifact_dependency():
    phase_one = inspect.getsource(production._complete_production_checkpoints).lower()
    for forbidden in ("evaluation", "artifact", "k_test", "evaluate_heldout_cells", "build_complete_result"):
        assert forbidden not in phase_one
    tree = ast.parse(Path(production.__file__).read_text(encoding="utf-8"))
    top_level_imports = [
        node.module or ""
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
    ]
    assert not any(name.endswith(("evaluation", "artifact")) for name in top_level_imports)
