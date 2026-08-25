"""Concrete lease-bound R06 production data plane.

The object is constructed only by :mod:`production_lease`.  It binds the
native 32-lane host, persistent 1,024-update jobs, checkpoint-loaded evaluation,
REAL/SHAM fork receipts, failure-atomic metrics, 24x6,990 inference, and the
complete branch payload behind a single nonreplaceable identity.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import threading
from typing import Iterable, Mapping, Sequence

import numpy as np
import torch

from .production_backend import NativeBatch, native_batch_from_rows
from .production_contract import ARMS, COMPONENT, UPDATES
from .production_evaluator import (
    CheckpointLoadedFiveArmEvaluator, MasterAddressedEvaluationBatchFactory,
    complete_evaluation_plan,
)
from .production_inference import complete_branch_payload, complete_estimand_manifest, run_production_inference
from .production_metrics import FailureAtomicMetricStore, RawMetricRow
from .production_population import complete_evaluation_coordinates
from .production_recurrent_trainer import (
    MasterAddressedPolicySampler, MasterAddressedTrainResetFactory,
    NativePersistentTrainingFlow, RecurrentRolloutState,
    build_master_addressed_initial_state,
)
from .production_real_sham import FirstApplicationValidRealShamRunner


class ProductionDataPlaneError(RuntimeError):
    pass


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _replace(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    with temporary.open("xb") as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


class _ForkCollector:
    """Capture each CLAIM/DEGRADED tape at its first valid application."""

    def __init__(self, *, items: tuple[object, ...], checkpoint: bytes, sampler: MasterAddressedPolicySampler) -> None:
        self.items = items; self.runner = FirstApplicationValidRealShamRunner(checkpoint_bytes=checkpoint, sampler=sampler)
        self.eligible = np.asarray([
            item.arm == "STRUCTURED" and item.mask_view == "DEGRADED" and item.coordinate.split == "CLAIM"
            for item in items
        ], dtype=bool)
        self.already = ~self.eligible.copy(); self.receipts: dict[int, Mapping[str, object]] = {}

    def observe(self, *, tick: int, native: NativeBatch, step_rows: np.ndarray,
                observation: Mapping[str, np.ndarray], policy_state: RecurrentRolloutState) -> None:
        valid = native.first_application_valid(step_rows) & ~self.already
        support = {}
        for lane in np.flatnonzero(valid):
            owner = int(np.asarray(observation["owner"])[lane]); standby = 1 - owner
            hidden = policy_state.hidden.detach().cpu().numpy()
            d_h = float(np.linalg.norm(hidden[lane, 2 * standby + 1] - hidden[lane, 2 * owner]) / np.sqrt(128.0))
            actions = np.asarray(step_rows["raw_action"], dtype=np.float64)
            promoted = actions[lane, 2 * standby:2 * standby + 2]
            retained = actions[lane, 2 * owner:2 * owner + 2]
            d_a = float(np.linalg.norm(promoted - retained) / 6.0)
            support[int(lane)] = (d_h, d_a)
        telemetry = self.runner.run(native=native, step_rows=step_rows, observation=observation,
                                    policy_state=policy_state, already_forked=self.already, origin_tick=tick)
        if telemetry is not None:
            for local, lane in enumerate(telemetry.source_lanes):
                d_h, d_a = support[int(lane)]
                self.receipts[int(lane)] = {
                    "item": self.items[lane].canonical_key(), "trigger_valid": True, "origin_tick": tick,
                    "d_h": d_h, "d_a": d_a,
                    "behavior_changing": bool(d_h >= 1e-3 and d_a >= 1e-3),
                    "real_service": telemetry.real_service[local].tolist(),
                    "sham_service": telemetry.sham_service[local].tolist(),
                    "real_energy_delta": float(telemetry.real_energy_delta[local]),
                    "sham_energy_delta": float(telemetry.sham_energy_delta[local]),
                    "real_hard_events": telemetry.real_hard_events[local].tolist(),
                    "sham_hard_events": telemetry.sham_hard_events[local].tolist(),
                    "transaction_telemetry_sha256": telemetry.transaction_telemetry_sha256,
                }
            self.already[np.asarray(telemetry.source_lanes, dtype=np.int64)] = True

    def complete(self) -> tuple[Mapping[str, object], ...]:
        rows = []
        for lane in np.flatnonzero(self.eligible):
            rows.append(self.receipts.get(int(lane), {"item": self.items[lane].canonical_key(),
                                                      "trigger_valid": False, "d_h": 0.0, "d_a": 0.0,
                                                      "behavior_changing": False}))
        return tuple(rows)


class R06ProductionDataPlane:
    """One-identity production flow with no scalar Python environment loop."""

    supports_parallel_scheduler = True

    def __init__(self, *, authority: object, master: bytes, run_root: Path,
                 process_worker_spec: Mapping[str, object] | None = None) -> None:
        require = getattr(authority, "require_active", None)
        if not callable(require):
            raise ProductionDataPlaneError("active Root lease authority is required")
        require()
        if getattr(authority, "component", None) != COMPONENT:
            raise ProductionDataPlaneError("lease component differs")
        self.authority = authority; self.master = bytes(master); self.run_root = run_root.resolve()
        identity = hashlib.sha256(self.master).hexdigest()
        if identity != getattr(authority, "identity_sha256", None):
            raise ProductionDataPlaneError("master/identity binding differs")
        self.identity_sha256 = identity
        self.scratch_root = self.run_root / "scratch"
        self.durable_root = self.run_root
        self.metric_store = FailureAtomicMetricStore(self.run_root / "metrics", binding_sha256=identity)
        self._evaluation_batches: tuple[tuple[object, ...], ...] | None = None
        self._checkpoint_cache: dict[tuple[int, str], bytes] | None = None
        self._cache_lock = threading.RLock()
        self._threads_configured = False
        self.process_worker_spec = None if process_worker_spec is None else dict(process_worker_spec)

    @staticmethod
    def preferred_batch(stage: str, start: int, remaining: int) -> int:
        widths = {"POPULATION": 32, "TRAINING": 1, "EVALUATION": 32, "FORK": 32, "INFERENCE": 1}
        width = widths.get(stage)
        if width is None or start < 0 or remaining <= 0:
            raise ProductionDataPlaneError("production batch request differs")
        return min(width, remaining)

    def execute_units(self, stage: str, start: int, count: int) -> Sequence[bytes]:
        if stage == "POPULATION": return self._population_batch(start, count)
        if stage == "TRAINING": return self._training_batch(start, count)
        if stage == "EVALUATION": return self._evaluation_batch(start, count)
        if stage == "FORK": return self._fork_batch(start, count)
        if stage == "INFERENCE" and start == 0 and count == 1: return (_canonical(self.inference_unit()),)
        raise ProductionDataPlaneError("production stage batch differs")

    def _scheduled_receipt_path(self, stage: str, start: int, count: int) -> Path:
        return self.run_root / "scheduler_receipts" / stage.lower() / f"{start:06d}-{count:02d}.json"

    def _recover_training_receipt(self, start: int) -> bytes:
        job, update = divmod(start, UPDATES); block, arm_index = divmod(job, len(ARMS)); arm = ARMS[arm_index]
        native_path, state_path, checkpoint_path = self._job_paths(block, arm)
        if not all(path.exists() for path in (native_path, state_path, checkpoint_path)):
            raise ProductionDataPlaneError("training recovery persistence is incomplete")
        state = RecurrentRolloutState.from_bytes(state_path.read_bytes())
        if state.updates_completed != update + 1:
            raise ProductionDataPlaneError("training recovery frontier differs")
        payloads = (native_path.read_bytes(), state_path.read_bytes(), checkpoint_path.read_bytes())
        return _canonical({"block": block, "arm": arm, "update": state.updates_completed,
                           "native": hashlib.sha256(payloads[0]).hexdigest(),
                           "state": hashlib.sha256(payloads[1]).hexdigest(),
                           "checkpoint": hashlib.sha256(payloads[2]).hexdigest()})

    def execute_scheduled(self, stage: str, start: int, count: int) -> Sequence[bytes]:
        """Idempotent scheduler boundary covering the persist→journal crash window."""

        target = self._scheduled_receipt_path(stage, start, count)
        if target.exists():
            value = json.loads(target.read_text(encoding="ascii"))
            rows = tuple(bytes.fromhex(row) for row in value.get("receipt_hex", ()))
            if value.get("identity_sha256") != self.identity_sha256 or len(rows) != count or any(not row for row in rows):
                raise ProductionDataPlaneError("scheduled receipt cache differs")
            return rows
        try:
            rows = tuple(bytes(row) for row in self.execute_units(stage, start, count))
        except ProductionDataPlaneError:
            if stage != "TRAINING" or count != 1:
                raise
            rows = (self._recover_training_receipt(start),)
        if len(rows) != count or any(not row for row in rows):
            raise ProductionDataPlaneError("scheduled receipt result differs")
        _replace(target, _canonical({"schema": "DISH_RBHR_R06_SCHEDULED_RECEIPT_V1",
                                     "identity_sha256": self.identity_sha256,
                                     "stage": stage, "start": start, "count": count,
                                     "receipt_hex": [row.hex() for row in rows]}))
        return rows

    def prepare_parallel_stage(self, *, stage: str, workers: int, total_cores: int) -> None:
        if stage not in ("POPULATION", "TRAINING", "EVALUATION", "FORK", "INFERENCE"):
            raise ProductionDataPlaneError("parallel stage differs")
        if not 6 <= workers <= 8 or not 6 <= total_cores <= 8 or workers > total_cores:
            raise ProductionDataPlaneError("parallel worker/core shape differs")
        # Prevent nested 8x8 oversubscription. Native calls release the GIL;
        # frozen PyTorch work is explicitly one intra-op core per worker.
        if self.process_worker_spec is None and not self._threads_configured:
            torch.set_num_threads(1); torch.set_num_interop_threads(1)
            self._threads_configured = True
        if stage == "EVALUATION":
            self._checkpoints(); self._ordered_evaluation_batches()

    def _population_batch(self, start: int, count: int) -> tuple[bytes, ...]:
        rows = complete_evaluation_coordinates()[start:start + count]
        if len(rows) != count:
            raise ProductionDataPlaneError("population batch exceeds inventory")
        return tuple(_canonical({"stage": "POPULATION", "index": start + offset,
                                 "coordinate_sha256": hashlib.sha256(row.canonical_key().encode("ascii")).hexdigest()})
                     for offset, row in enumerate(rows))

    def _job_paths(self, block: int, arm: str) -> tuple[Path, Path, Path]:
        root = self.run_root / "training" / f"block-{block:02d}" / arm.lower()
        return root / "native_state.bin", root / "rollout_state.bin", root / "checkpoint.pt"

    def _open_training_job(self, block: int, arm: str) -> tuple[NativePersistentTrainingFlow, Mapping[str, np.ndarray]]:
        native_path, state_path, checkpoint_path = self._job_paths(block, arm)
        if native_path.exists() or state_path.exists() or checkpoint_path.exists():
            if not all(path.exists() for path in (native_path, state_path, checkpoint_path)):
                raise ProductionDataPlaneError("training job persistence is incomplete")
            native = NativeBatch.from_snapshot_bytes(native_path.read_bytes())
            state = RecurrentRolloutState.from_bytes(state_path.read_bytes())
            checkpoint = checkpoint_path.read_bytes()
        else:
            checkpoint = build_master_addressed_initial_state(master=self.master, block=block, arm=arm)
            state = RecurrentRolloutState.fresh(arm)
            factory = MasterAddressedTrainResetFactory(master=self.master, block=block, arm=arm)
            native = native_batch_from_rows(factory.rows(state.lane_episode_wave))
        flow = NativePersistentTrainingFlow(native=native, arm=arm, master=self.master, block=block,
                                            checkpoint_bytes=checkpoint, state=state)
        return flow, native.observe()

    def _persist_training_job(self, block: int, arm: str, flow: NativePersistentTrainingFlow) -> bytes:
        native_path, state_path, checkpoint_path = self._job_paths(block, arm)
        payloads = (flow.native.snapshot_bytes(), flow.state.to_bytes(), flow.trainer.checkpoint_bytes)
        for path, payload in zip((native_path, state_path, checkpoint_path), payloads):
            _replace(path, bytes(payload))
        receipt = _canonical({"block": block, "arm": arm, "update": flow.state.updates_completed,
                              "native": hashlib.sha256(payloads[0]).hexdigest(),
                              "state": hashlib.sha256(payloads[1]).hexdigest(),
                              "checkpoint": hashlib.sha256(payloads[2]).hexdigest()})
        return receipt

    def _training_batch(self, start: int, count: int) -> tuple[bytes, ...]:
        if count != 1 or not 0 <= start < 24 * len(ARMS) * UPDATES:
            raise ProductionDataPlaneError("training batch must be one atomic update")
        job, update = divmod(start, UPDATES); block, arm_index = divmod(job, len(ARMS)); arm = ARMS[arm_index]
        flow, observation = self._open_training_job(block, arm)
        if flow.state.updates_completed != update:
            raise ProductionDataPlaneError("training resume frontier differs")
        fragments = flow.collect_update(observation); flow.apply_update(fragments)
        return (self._persist_training_job(block, arm, flow),)

    def _checkpoints(self) -> dict[tuple[int, str], bytes]:
        with self._cache_lock:
            if self._checkpoint_cache is None:
                result = {}
                for block in range(24):
                    for arm in ARMS:
                        _, state_path, checkpoint_path = self._job_paths(block, arm)
                        if not state_path.exists() or not checkpoint_path.exists():
                            raise ProductionDataPlaneError("evaluation checkpoint inventory is incomplete")
                        state = RecurrentRolloutState.from_bytes(state_path.read_bytes())
                        if state.updates_completed != UPDATES:
                            raise ProductionDataPlaneError("evaluation checkpoint is not update 1,024")
                        result[(block, arm)] = checkpoint_path.read_bytes()
                self._checkpoint_cache = result
            return dict(self._checkpoint_cache)

    def _ordered_evaluation_batches(self) -> tuple[tuple[object, ...], ...]:
        with self._cache_lock:
            if self._evaluation_batches is None:
                plan = complete_evaluation_plan(); groups = []
                for block in range(24):
                    for arm in ARMS:
                        items = tuple(row for row in plan if row.coordinate.block == block and row.arm == arm)
                        groups.extend(items[offset:offset + 32] for offset in range(0, len(items), 32))
                if len(groups) != 3_600 or any(len(row) != 32 for row in groups):
                    raise ProductionDataPlaneError("evaluation native batch inventory differs")
                self._evaluation_batches = tuple(groups)
            return self._evaluation_batches

    def _evaluation_batch(self, start: int, count: int) -> tuple[bytes, ...]:
        if count != 32 or start % 32:
            raise ProductionDataPlaneError("evaluation frontier is not native-batch aligned")
        items = self._ordered_evaluation_batches()[start // 32]
        block = items[0].coordinate.block; arm = items[0].arm
        checkpoint = self._checkpoints()[(block, arm)]
        sampler = MasterAddressedPolicySampler(master=self.master, block=block, arm=arm,
                                               episode_wave=np.zeros(32, dtype=np.int64), episode_tick=np.zeros(32, dtype=np.int64))
        observer = _ForkCollector(items=items, checkpoint=checkpoint, sampler=sampler) if arm == "STRUCTURED" else None
        evaluator = CheckpointLoadedFiveArmEvaluator(
            checkpoints=self._checkpoints(), batch_factory=MasterAddressedEvaluationBatchFactory(authority=self.authority, master=self.master),
            deterministic_sampler=sampler, fork_observer=observer,
        )
        telemetry = evaluator.run_batch(items)
        if telemetry.fork_receipts:
            claim_keys = {
                coordinate.canonical_key(): index for index, coordinate in enumerate(
                    row for row in complete_evaluation_coordinates() if row.split == "CLAIM"
                )
            }
            for row in telemetry.fork_receipts:
                item_key = str(row["item"])
                coordinate_key = item_key.rsplit("/", 2)[0]
                index = claim_keys.get(coordinate_key)
                if index is None:
                    raise ProductionDataPlaneError("REAL/SHAM receipt is outside CLAIM inventory")
                _replace(self.run_root / "fork_receipts" / f"{index:06d}.json", _canonical(row))
        receipt = hashlib.sha256(telemetry.service.tobytes() + telemetry.energy.tobytes() + telemetry.hard_events.tobytes()).hexdigest()
        return tuple(_canonical({"stage": "EVALUATION", "index": start + offset,
                                 "item": telemetry.item_keys[offset], "batch_sha256": receipt}) for offset in range(32))

    def _fork_batch(self, start: int, count: int) -> tuple[bytes, ...]:
        # First-application-valid REAL/SHAM execution is performed in the
        # evaluation flow and persisted as complete fork receipts.  The FORK
        # frontier only seals those already-paired receipts; it never reruns a
        # branch after a crash.
        paths = tuple(self.run_root / "fork_receipts" / f"{index:06d}.json" for index in range(start, start + count))
        if len(paths) != count or any(not path.is_file() for path in paths):
            raise ProductionDataPlaneError("complete paired REAL/SHAM fork receipt is absent")
        rows = tuple(path.read_bytes() for path in paths)
        return rows

    def ingest_raw_metric_rows(self, shard_id: str, rows: Iterable[RawMetricRow]) -> Mapping[str, object]:
        return self.metric_store.append_shard(shard_id, rows)

    def inference_unit(self) -> Mapping[str, object]:
        matrix = np.asarray(self.metric_store.complete_estimand_matrix(), dtype=np.float64)
        inference = run_production_inference(matrix, master=self.master)
        branch_input_path = self.run_root / "metrics" / "complete_branch_predicates.json"
        if not branch_input_path.is_file():
            raise ProductionDataPlaneError("complete branch predicate payload is absent")
        raw = json.loads(branch_input_path.read_text(encoding="ascii"))
        vectors = {(row["regime"], row["schedule"]): row["vector"] for row in raw["cells"]}
        branches = complete_branch_payload(vectors)
        payload = {"inference": inference, "branch_result": branches, "manifest": list(complete_estimand_manifest())}
        _replace(self.run_root / "sealed_inference.json", _canonical(payload)); return payload

    def complete_result(self) -> Mapping[str, object]:
        path = self.run_root / "sealed_inference.json"
        if not path.is_file():
            raise ProductionDataPlaneError("complete inference is absent")
        payload = json.loads(path.read_text(encoding="ascii"))
        return {"branch_result": payload["branch_result"], "inference": payload["inference"]}

    # Compatibility methods are intentionally one-unit wrappers; production
    # orchestration calls execute_units and therefore preserves native batches.
    def population_unit(self, index: int) -> bytes: return self._population_batch(index, 1)[0]
    def training_unit(self, index: int) -> bytes: return self._training_batch(index, 1)[0]
    def evaluation_unit(self, index: int) -> bytes: return self._evaluation_batch(index, 32)[0]
    def fork_unit(self, index: int) -> bytes: return self._fork_batch(index, 1)[0]


__all__ = ["ProductionDataPlaneError", "R06ProductionDataPlane"]
