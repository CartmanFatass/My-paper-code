from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01 import (
    b4_induction_pilot as pilot_module, trainer as trainer_module,
    training_shards as shards_module,
)

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.b4_induction_pilot import (
    _append_paired_rows_transaction, _execute_actual_b4_checkpoint_induction_pilot,
    _active_ceiling_breach, _fixture_work, _persist_checkpoint_transaction,
    _configure_child_native_build_directory,
    _cleanup_exited_worker_native_artifacts, _quarantine_supervised_transaction,
    _accept_supervised_worker_result, _supervised_storage_bytes,
    _terminate_cleanup_quarantine, _worker_native_artifact_paths,
    _publish_create_once_transaction, _resumed_probe_worker,
    run_actual_b4_checkpoint_induction_pilot,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
    B01ContractError,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.training_runner import (
    PILOT_PEAK_RSS_BYTES, PILOT_SCRATCH_DURABLE_BYTES, PILOT_WALL_SECONDS,
    exact512_induction_contract,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.trainer import (
    PairedB01Trainer,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.training_shards import (
    ActualDirectTrainingRow, actual_direct_training_row,
)


PILOT_ROOT = Path(
    "temp/frrie_b01_b4_induction_pilot_20260901_01"
).resolve()


def test_pilot_seam_is_one_root_and_admission_precedes_every_runtime_constructor():
    assert list(inspect.signature(run_actual_b4_checkpoint_induction_pilot).parameters) == [
        "root"
    ]
    source = inspect.getsource(_execute_actual_b4_checkpoint_induction_pilot)
    admission = source.index("_fresh_admission")
    for constructor in (
        "create_test_seed_packet", "build_package_native_artifact",
        "load_package_native_adapter", "_runtime_at(",
    ):
        assert admission < source.index(constructor)
    assert "worker_fn" not in source and "adapter_factory" not in source
    assert "_publish_create_once_transaction" in source
    assert "validate_b4_induction_receipt(final_receipt)" in source
    assert "artifact.unlink" not in source
    resume_source = inspect.getsource(_resumed_probe_worker)
    resume_admission = resume_source.index("_fresh_admission")
    for constructor in ("load_package_native_adapter", "_runtime_at("):
        assert resume_admission < resume_source.index(constructor)
    assert resume_source.index("build_package_native_artifact") < resume_source.index(
        "load_package_native_adapter"
    )
    supervisor = inspect.getsource(run_actual_b4_checkpoint_induction_pilot)
    assert "_terminate_cleanup_quarantine" in supervisor
    assert "_cleanup_exited_worker_native_artifacts" in supervisor
    assert "_accept_supervised_worker_result" in supervisor
    accept_source = inspect.getsource(_accept_supervised_worker_result)
    assert "except EOFError" in accept_source
    assert "parent.close()" in accept_source
    assert "_quarantine_supervised_transaction" in accept_source
    assert "_active_ceiling_breach" in supervisor
    ceiling_source = inspect.getsource(_active_ceiling_breach)
    assert "PILOT_WALL_SECONDS" in ceiling_source
    assert "PILOT_PEAK_RSS_BYTES" in ceiling_source
    assert "PILOT_SCRATCH_DURABLE_BYTES" in ceiling_source
    contract = exact512_induction_contract()
    assert contract["pilot_ceiling"] == {
        "wall_seconds": PILOT_WALL_SECONDS,
        "scratch_durable_bytes": PILOT_SCRATCH_DURABLE_BYTES,
        "peak_rss_bytes": PILOT_PEAK_RSS_BYTES,
        "memory_admission_minimum_bytes": 4 * 1024 * 1024 * 1024,
        "active_parent_process_tree_termination": True,
    }
    assert contract["launch_capable"] is False
    assert contract["scientific_values"] is None


def test_spawned_resume_native_build_is_child_local_fresh_and_fail_closed(tmp_path):
    module = SimpleNamespace(
        _LIVE_ADAPTER=None, _FRESH_ARTIFACT_PATH=None,
        _FRESH_ARTIFACT_BYTES=None, _NATIVE_DIR=Path("ignored"),
    )
    target = tmp_path / "resume-native"
    assert _configure_child_native_build_directory(module, target) == target.resolve()
    assert module._NATIVE_DIR == target.resolve()
    target.mkdir()
    with pytest.raises(B01ContractError, match="native build state is not fresh"):
        _configure_child_native_build_directory(
            SimpleNamespace(
                _LIVE_ADAPTER=None, _FRESH_ARTIFACT_PATH=None,
                _FRESH_ARTIFACT_BYTES=None,
            ), target,
        )


def test_supervising_parent_cleans_exited_worker_artifacts_and_quarantines(tmp_path):
    artifact = tmp_path / "native" / "adapter.dll"
    artifact.parent.mkdir()
    artifact.write_bytes(b"dll")
    worker_pid = 1234
    temporary = artifact.with_name(
        f"{artifact.stem}.building-{worker_pid}{artifact.suffix}"
    )
    for path in (
        temporary,
        *(temporary.with_suffix(suffix) for suffix in (".obj", ".pdb", ".lib", ".exp")),
    ):
        path.write_bytes(b"build")
    _cleanup_exited_worker_native_artifacts(
        artifact, worker_pid=worker_pid, artifact_preexisted=False,
    )
    assert not artifact.exists()
    assert not temporary.exists()
    preserved = tmp_path / "preserved.dll"
    preserved.write_bytes(b"existing")
    _cleanup_exited_worker_native_artifacts(
        preserved, worker_pid=worker_pid, artifact_preexisted=True,
    )
    assert preserved.read_bytes() == b"existing"

    final = tmp_path / "pilot"
    staging = tmp_path / "pilot.creating"
    incomplete = tmp_path / "pilot.incomplete"
    final.mkdir()
    _quarantine_supervised_transaction(
        final=final, staging=staging, incomplete=incomplete,
    )
    assert not final.exists() and incomplete.is_dir()


def test_supervisor_eof_always_closes_pipe_and_quarantines(tmp_path):
    class Pipe:
        closed = False

        def poll(self, timeout):
            assert timeout == 1
            return True

        def recv(self):
            raise EOFError("injected child close")

        def close(self):
            self.closed = True

    parent = Pipe()
    process = SimpleNamespace(exitcode=0)
    final = tmp_path / "pilot"
    staging = tmp_path / "pilot.creating"
    incomplete = tmp_path / "pilot.incomplete"
    staging.mkdir()
    with pytest.raises(B01ContractError, match="pipe closed before receipt"):
        _accept_supervised_worker_result(
            parent, process, final=final, staging=staging, incomplete=incomplete,
            peak_rss=0, peak_storage=0,
        )
    assert parent.closed is True
    assert not staging.exists() and incomplete.is_dir()


def test_termination_failure_still_quarantines_and_reports(monkeypatch, tmp_path):
    class Process:
        pid = 4321

        def join(self, timeout):
            assert timeout == 30

        def is_alive(self):
            return False

    monkeypatch.setattr(
        pilot_module, "_terminate_owned_process_tree",
        lambda pid: (_ for _ in ()).throw(OSError("injected taskkill failure")),
    )
    final = tmp_path / "pilot"
    staging = tmp_path / "pilot.creating"
    incomplete = tmp_path / "pilot.incomplete"
    staging.mkdir()
    with pytest.raises(B01ContractError, match="termination/cleanup/quarantine failed"):
        _terminate_cleanup_quarantine(
            Process(), artifact=tmp_path / "artifact.dll", artifact_preexisted=False,
            final=final, staging=staging, incomplete=incomplete,
        )
    assert not staging.exists() and incomplete.is_dir()


def test_storage_ceiling_counts_outer_artifact_and_pid_build_sidecars(tmp_path):
    artifact = tmp_path / "adapter.dll"
    paths = _worker_native_artifact_paths(artifact, worker_pid=55)
    for index, path in enumerate(paths, start=1):
        path.write_bytes(bytes(index))
    transaction = tmp_path / "pilot.creating"
    transaction.mkdir()
    (transaction / "row.bin").write_bytes(b"transaction")
    assert _supervised_storage_bytes((transaction, *paths)) == (
        len(b"transaction") + sum(range(1, len(paths) + 1))
    )


def test_boundary_prefix_work_is_explicit_coordinate_fixture_not_native_evidence():
    work = _fixture_work(256)
    assert set(work) == {"PHY_TRUST", "EDGE_FLEX"}
    assert work["PHY_TRUST"] == work["EDGE_FLEX"]
    assert work["PHY_TRUST"]["training_update"] == 256
    assert work["PHY_TRUST"]["environment_slots"] == 256 * 4_928
    assert work["PHY_TRUST"]["native_batch_calls"] == 256


@pytest.mark.parametrize(
    ("elapsed", "rss", "storage", "expected"),
    [
        (PILOT_WALL_SECONDS + 0.001, 0, 0, "WALL_SECONDS"),
        (0, PILOT_PEAK_RSS_BYTES + 1, 0, "PROCESS_TREE_RSS"),
        (0, 0, PILOT_SCRATCH_DURABLE_BYTES + 1, "SCRATCH_DURABLE_BYTES"),
        (PILOT_WALL_SECONDS, PILOT_PEAK_RSS_BYTES, PILOT_SCRATCH_DURABLE_BYTES, None),
    ],
)
def test_active_supervisor_ceiling_predicate_is_hard_and_inclusive(
    elapsed, rss, storage, expected,
):
    assert _active_ceiling_breach(
        elapsed=elapsed, rss=rss, storage=storage,
    ) == expected


def test_typed_direct_row_seam_rejects_untyped_or_forged_objects_before_payload_use():
    with pytest.raises(B01ContractError, match="typed trainer/collector"):
        actual_direct_training_row(
            receipt=object(), batch=object(), collection_audit=object(),
        )


def test_trainer_continuation_api_restores_exact_audit_and_has_no_hidden_live_state():
    trainer = object.__new__(PairedB01Trainer)
    trainer.models = {arm: object() for arm in ("PHY_TRUST", "EDGE_FLEX")}
    trainer.trainers = {
        arm: SimpleNamespace(model=trainer.models[arm], optimizer=object())
        for arm in trainer.models
    }
    trainer.first_tight_contact_update = None
    trainer.precontact_full_state_equal = True
    trainer.changed_coordinates = set()
    trainer.maximum_tight_overshoot = 0.0
    trainer.cumulative_tight_displacement = 0.0
    trainer.wide_boundary_contact = False
    trainer._continuation_seed_label = None
    trainer._continuation_update = 0
    trainer._continuation_work = None
    trainer._continuation_frontier = None
    state = {
        "schema": "FRRIE_B01_TRAINER_CONTINUATION_STATE_V1",
        "seed_label": "FRRIE-B01-TEST-ONLY-BLOCK-001", "update": 64,
        "first_tight_contact_update": 33, "precontact_full_state_equal": True,
        "tight_projection_changed_indices": [1, 7, 17],
        "wide_boundary_contact": False, "maximum_tight_overshoot": 0.1,
        "cumulative_tight_displacement": 0.2,
        "work": _fixture_work(64),
        "frontier": {
            "training_update": 64, "training_episode_cursor": 4_096,
            "evaluation_checkpoint_cursor": 0,
            "completed_checkpoints": [0, 32, 64],
        },
    }
    trainer.restore_checkpoint_continuation_state(state)
    assert trainer.checkpoint_continuation_state() == state
    boundary = trainer.checkpoint_boundary_state_inventory()
    assert boundary["no_live_episode_state"] is True
    assert boundary["no_live_native_state"] is True
    assert boundary["no_live_iterator_state"] is True
    assert boundary["no_mutable_rng_cursor_state"] is True


def test_direct_transaction_advances_actual_native_work_and_frontier_readback(monkeypatch):
    class Model:
        def __init__(self, arm):
            self.arm_id = arm

        def parameter_bytes(self):
            return (self.arm_id + "-model").encode()

    trainer = object.__new__(PairedB01Trainer)
    trainer.models = {arm: Model(arm) for arm in ("PHY_TRUST", "EDGE_FLEX")}
    trainer.trainers = {
        arm: SimpleNamespace(model=trainer.models[arm], optimizer=object())
        for arm in trainer.models
    }
    trainer.first_tight_contact_update = None
    trainer.precontact_full_state_equal = True
    trainer.changed_coordinates = set()
    trainer.maximum_tight_overshoot = 0.0
    trainer.cumulative_tight_displacement = 0.0
    trainer.wide_boundary_contact = False
    trainer._continuation_seed_label = "FRRIE-B01-TEST-ONLY-BLOCK-001"
    trainer._continuation_update = 0
    trainer._continuation_work = _fixture_work(0)
    trainer._continuation_frontier = {
        "training_update": 0, "training_episode_cursor": 0,
        "evaluation_checkpoint_cursor": 0, "completed_checkpoints": [0],
    }
    monkeypatch.setattr(
        trainer_module, "encode_optimizer_state",
        lambda model, optimizer: (model.arm_id + "-optimizer").encode(),
    )
    trainer.update = lambda batches, update: {arm: object() for arm in trainer.models}
    monkeypatch.setattr(
        shards_module, "actual_direct_training_row",
        lambda **kwargs: SimpleNamespace(arm=kwargs["batch"].arm),
    )
    monkeypatch.setattr(
        shards_module, "validate_actual_paired_direct_rows",
        lambda *args, **kwargs: {"schema": "paired"},
    )
    monkeypatch.setattr(
        shards_module, "validate_actual_direct_row_chain_step",
        lambda row, **kwargs: {"schema": "chain"},
    )
    ledgers = [SimpleNamespace(
        native_reset_calls=2, native_observe_calls=3,
        native_step_calls=4, environment_slots=4_928,
    )]
    batches = {
        arm: SimpleNamespace(arm=arm, collection_ledgers=ledgers)
        for arm in trainer.models
    }
    result = trainer.update_with_direct_rows(
        batches, collection_audits={arm: object() for arm in trainer.models},
        update=1, expected_seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001",
        expected_root=b"R" * 32,
    )
    state = result["continuation"]
    assert state["update"] == 1
    assert state["frontier"]["training_episode_cursor"] == 64
    assert state["frontier"]["completed_checkpoints"] == [0]
    for arm in trainer.models:
        assert state["work"][arm]["native_batch_calls"] == 9
        assert state["work"][arm]["native_batch_ledger"] == {
            "reset_calls": 2, "observe_calls": 3, "step_calls": 4,
            "environment_slots": 4_928,
        }


def _persistence_row(arm: str) -> ActualDirectTrainingRow:
    return ActualDirectTrainingRow(
        update=1, arm=arm, array_shards={"a": b"array"},
        state_blobs={"s": b"state"}, typed_exogenous_receipts=(),
    )


@pytest.mark.parametrize("fault", ["AFTER_ARM_1", "AFTER_ARM_2", "READBACK"])
def test_paired_append_fault_truncates_both_arms_to_prior_offsets(tmp_path, fault):
    rows = {arm: _persistence_row(arm) for arm in ("PHY_TRUST", "EDGE_FLEX")}
    directory = tmp_path / "paired"
    _append_paired_rows_transaction(directory, rows)
    before = {
        arm: (directory / f"{arm}.paired-rows.bin").read_bytes() for arm in rows
    }
    with pytest.raises(OSError):
        _append_paired_rows_transaction(directory, rows, fault=fault)
    assert {
        arm: (directory / f"{arm}.paired-rows.bin").read_bytes() for arm in rows
    } == before


@pytest.mark.parametrize("fault", ["WRITE", "READBACK"])
def test_checkpoint_fault_leaves_no_visible_or_staging_checkpoint(tmp_path, fault):
    target = tmp_path / "checkpoint.json"
    with pytest.raises(OSError):
        _persist_checkpoint_transaction(target, b"checkpoint", fault=fault)
    assert not target.exists()
    assert not target.with_name(target.name + ".creating").exists()


@pytest.mark.parametrize("collision", ["target", "staging"])
def test_checkpoint_create_once_collision_preserves_preexisting_bytes(tmp_path, collision):
    target = tmp_path / "checkpoint.json"
    staging = target.with_name(target.name + ".creating")
    occupied = target if collision == "target" else staging
    occupied.write_bytes(b"preexisting")
    with pytest.raises(FileExistsError, match="create-once"):
        _persist_checkpoint_transaction(target, b"new")
    assert occupied.read_bytes() == b"preexisting"
    other = staging if collision == "target" else target
    assert not other.exists()


@pytest.mark.parametrize("fault", ["BEFORE_RENAME", "AFTER_RENAME", "READBACK"])
def test_publication_fault_quarantines_and_never_leaves_final(tmp_path, fault):
    final = tmp_path / "pilot"
    creating = tmp_path / "pilot.creating"
    incomplete = tmp_path / "pilot.incomplete"
    creating.mkdir()
    (creating / "B4-induction-receipt.json").write_bytes(b"{}")
    with pytest.raises(OSError):
        _publish_create_once_transaction(creating, final, incomplete, fault=fault)
    assert not final.exists()
    assert incomplete.is_dir()


def test_actual_b4_checkpoint_induction_pilot():
    """Explicitly selected future pilot; excluded from safe suites with ``-k not actual``."""

    receipt = run_actual_b4_checkpoint_induction_pilot(PILOT_ROOT)
    assert receipt["b4_complete"] is True
    assert receipt["test_component_only"] is True
    assert receipt["production_token"] is False
