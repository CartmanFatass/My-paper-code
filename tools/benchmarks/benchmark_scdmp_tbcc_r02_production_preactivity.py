"""Result-blind production-chain benchmark for the frozen TBCC r02 object.

All activity in this module is conspicuously TEST-only and disposable.  It
does not issue a Root lease, bind an empirical identity, draw an empirical
master, or retain question-relevant values.
"""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from dataclasses import asdict
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Iterable, Mapping, Sequence

import torch

from envs.native.production_backend import require_cpp_batched_production
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value import (
    benchmark as fixture_benchmark,
    native_backend,
    production,
    runner,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.artifacts import (
    AdapterFinalReceipt,
    FinalPanelReceipt,
    FoundationFinalReceipt,
    FoundationGate,
    OpportunityReceipt,
    ResultCode,
    atomic_create_json,
    final_panel_barrier_digest,
    foundation_barrier_digest,
    require_foundation_checkpoint_barrier,
    test_only_bindings,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.empirical_contract import (
    PANEL_COUNTS,
    canonical_digest,
    canonical_json_bytes,
    coordinate_proposal,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.evaluation import (
    AcceptedControllerBinding,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.frontier import (
    FrontierGeneration,
    FrontierStage,
    FrontierState,
    create_frontier_generation,
    frontier_generation_digest,
    load_resume_chain,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.lifecycle import (
    GateOutcome,
    TechnicalFinal,
    issue_opportunity_execution_permit,
    snapshot,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.opportunity import (
    ReplicateOpportunityMetrics,
    analyze_gate,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.oracle import (
    TestOnlyState,
    test_only_primitive as oracle_primitive,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.preactivity import (
    build_preactivity_acceptance,
    require_direction_cpp_batched_production,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.production_services import (
    NativeProductionServices,
    test_only_service_authority,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.source_manifest import (
    build_source_manifest,
    manifest_bytes,
    manifest_digest,
)
from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.training import (
    DurationCorrectPPOTrainer,
)


SCHEMA = "SCDMP-TBCC-R02-PRODUCTION-PREACTIVITY-BENCHMARK-V1"
MODULE = "tools.benchmarks.benchmark_scdmp_tbcc_r02_production_preactivity"
CHAIN_COVERAGE = (
    "environment",
    "loader",
    "batch",
    "forward_backward",
    "rollout",
    "evaluation",
    "io",
    "resume",
)
WIDTHS = (12, 120, 144)
TEST_MASTER = bytes(range(32))
RETAINED_SPEEDUP = 3.034772909220757
EFFICIENCY_RECORD = Path("runtime/benchmarks/scdmp_tbcc_r02_efficiency_20260821.json")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def _fake(label: str) -> str:
    return "TEST_ONLY_FAKE_SHA256:" + hashlib.sha256(label.encode("ascii")).hexdigest()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _create_exact(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(f".{path.name}.{os.getpid()}.pending")
    with pending.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(pending, path)
    finally:
        pending.unlink(missing_ok=True)


class _TrackingNativeSession:
    def __init__(self, resets: Iterable[object], collector: dict[str, object]) -> None:
        materialized = tuple(resets)
        self._collector = collector
        self._batch = native_backend.NativeBatch(materialized)
        self.initial = self._batch.initial
        collector["sessions"] = int(collector.get("sessions", 0)) + 1
        collector.setdefault("widths", []).append(len(materialized))

    def renew(self, rows: Iterable[object]):
        materialized = tuple(rows)
        active = sum(bool(getattr(row, "active", False)) for row in materialized)
        output = self._batch.renew(materialized)
        self._collector["active_rows"] = int(self._collector.get("active_rows", 0)) + active
        self._collector["primitive_transitions"] = int(
            self._collector.get("primitive_transitions", 0)
        ) + sum(
            int(value.ticks_advanced)
            for row, value in zip(materialized, output)
            if bool(getattr(row, "active", False))
        )
        tails_canonical = all(
            value.last_hold_reward_count == value.ticks_advanced
            and value.last_hold_rewards[value.last_hold_reward_count :] == (0.0,) * (
                13 - value.last_hold_reward_count
            )
            for value in output
        )
        self._collector["reward_trace_contract"] = bool(
            self._collector.get("reward_trace_contract", True)
        ) and tails_canonical
        return output

    def close(self) -> None:
        self._batch.close()


def _shared_guard(component: str, **kwargs: object) -> Mapping[str, object]:
    return require_cpp_batched_production(component, **kwargs)


def _cold_child() -> dict[str, object]:
    torch.set_num_threads(1)
    receipt, measurement = fixture_benchmark._measure(
        lambda: require_direction_cpp_batched_production(batch_width=144)
    )
    return {
        "schema": "TEST_ONLY_TBCC_SHARED_ABI2_PROCESS_COLD_LOADER_V1",
        "receipt": receipt,
        "measurement": measurement,
        "torch_threads": torch.get_num_threads(),
    }


def _process_cold_loader() -> dict[str, object]:
    process = subprocess.run(
        [sys.executable, "-m", MODULE, "--cold-child"],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(process.stdout)


def _warm_loader() -> dict[str, object]:
    native_backend.clear_process_local_cache_for_tests()
    initial, initial_measurement = fixture_benchmark._measure(
        lambda: require_direction_cpp_batched_production(batch_width=144)
    )
    repeated, repeated_measurement = fixture_benchmark._measure(
        lambda: tuple(
            require_direction_cpp_batched_production(batch_width=width)
            for _ in range(20)
            for width in WIDTHS
        )
    )
    return {
        "initial_receipt": initial,
        "initial_measurement": initial_measurement,
        "repeated_calls": len(repeated),
        "repeated_measurement": repeated_measurement,
        "seconds_per_repeated_call": float(repeated_measurement["wall_seconds"]) / len(repeated),
        "all_receipts_abi2_equal": all(
            row["native"]["artifact_sha256"] == initial["native"]["artifact_sha256"]
            and row["shared"]["native"]["binding_kind"] == "ctypes_cdll"
            and row["native"]["abi_version"] == 2
            for row in repeated
        ),
    }


def _primitive_reward_trace() -> dict[str, object]:
    arguments = {
        "q": 1,
        "tick": 40,
        "x": 3.0,
        "v": 0.5,
        "y": 0.02,
        "w": -0.01,
        "phi": 0.03,
        "omega": -0.02,
        "z": (0.01, 0.02, 0.03, 0.04),
        "formation": 0.02,
        "prior_a": 1,
        "prior_r": (0, 0, 0, 0),
        "action": 10,
        "eta_v": -0.003,
        "eta_y": 0.002,
        "eta_omega": -0.004,
    }
    native = native_backend.test_only_primitive(**arguments)
    state = TestOnlyState(
        x=arguments["x"], v=arguments["v"], y=arguments["y"], w=arguments["w"],
        phi=arguments["phi"], omega=arguments["omega"], z=arguments["z"],
        formation=arguments["formation"], prior_a=arguments["prior_a"],
        prior_r=arguments["prior_r"], p=(4, 2, 1, 3), q=arguments["q"],
        tick=arguments["tick"], current_k=7, k_after=7, switch_tick=0, switched=False,
    )
    oracle = oracle_primitive(
        state,
        int(arguments["action"]),
        float(arguments["eta_v"]),
        float(arguments["eta_y"]),
        float(arguments["eta_omega"]),
    )
    equal = (
        native.last_hold_reward_count == native.ticks_advanced == 1
        and native.last_hold_rewards[1:] == (0.0,) * 12
        and abs(native.last_hold_rewards[0] - oracle.last_primitive_reward) <= 2e-14
        and abs(native.cumulative_reward - oracle.cumulative_reward) <= 2e-14
    )
    if not equal:
        raise RuntimeError("ABI2 native primitive reward trace differs from the TEST oracle")
    return {
        "abi_version": 2,
        "capacity": 13,
        "count_equals_ticks_advanced": True,
        "inactive_tail_canonical_zero": True,
        "oracle_native_reward_equal": True,
        "maximum_absolute_difference": max(
            abs(native.last_hold_rewards[0] - oracle.last_primitive_reward),
            abs(native.cumulative_reward - oracle.cumulative_reward),
        ),
        "reward_values_exposed": False,
    }


def _source_and_preflight(repository_root: Path, result_root: Path) -> dict[str, object]:
    receipt = require_direction_cpp_batched_production(batch_width=144)
    native_identity = dict(receipt["native"])
    source_manifest = build_source_manifest(
        repository_root, native_identity=native_identity
    )
    source_sha = manifest_digest(source_manifest)
    coordinate = coordinate_proposal(source_sha)
    evidence_path = (repository_root / EFFICIENCY_RECORD).resolve()
    if not evidence_path.is_file():
        raise RuntimeError("retained result-blind efficiency evidence is absent")
    validation = {
        "runner_to_card_counts": True,
        "controller_and_optimizer_arithmetic": True,
        "analyzer_branch_inventory": True,
        "worker_equivalence_1_2_4": True,
        "malformed_input_fail_closed": True,
        "interrupted_frontier_fail_closed": True,
        "atomic_io_and_resume": True,
        "end_to_end_result_blind_efficiency": True,
    }
    acceptance = build_preactivity_acceptance(
        repository_root=repository_root,
        source_manifest=source_manifest,
        native_identity=native_identity,
        native_receipt=receipt,
        coordinate=coordinate,
        efficiency_evidence_sha256=_sha(evidence_path),
        validation=validation,
    )
    paths = {key: Path(value) for key, value in runner._paths(result_root).items()}
    _create_exact(paths["source_manifest_path"], manifest_bytes(source_manifest))
    _create_exact(
        paths["preactivity_acceptance_path"], canonical_json_bytes(acceptance)
    )
    state, direct_measurement = fixture_benchmark._measure(
        lambda: production.preflight_only(
            repository_root=repository_root,
            source_manifest_path=paths["source_manifest_path"],
            preactivity_acceptance_path=paths["preactivity_acceptance_path"],
            output_paths={key: str(value) for key, value in paths.items()},
            native_identity_loader=native_backend.native_artifact_identity,
            shared_guard=_shared_guard,
        )
    )
    cli_output = io.StringIO()

    def execute_cli() -> int:
        with redirect_stdout(cli_output):
            return runner.main(
                [
                    "--preflight-only",
                    "--repository-root",
                    str(repository_root),
                    "--result-root",
                    str(result_root),
                ]
            )

    return_code, cli_measurement = fixture_benchmark._measure(execute_cli)
    cli_payload = json.loads(cli_output.getvalue())
    if return_code != 0 or cli_payload.get("scientific_activity_started") is not False:
        raise RuntimeError("foreground identity-free preflight CLI differs")
    return {
        "state": state,
        "paths": paths,
        "source_manifest": source_manifest,
        "source_manifest_sha256": source_sha,
        "source_file_set_sha256": canonical_digest(source_manifest["files"]),
        "native_identity": native_identity,
        "shared_receipt": state.shared_receipt,
        "shared_receipt_sha256": state.shared_receipt_sha256,
        "direct_measurement": direct_measurement,
        "foreground_cli_measurement": cli_measurement,
        "foreground_cli_identity_free": True,
        "source_file_count": len(source_manifest["files"]),
    }


def _model_digest(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in model.named_parameters():
        digest.update(name.encode("utf-8"))
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def _test_only_opportunity_permit():
    finals = tuple(
        TechnicalFinal(index, "FOUNDATION", _fake(f"opportunity-foundation:{index}"))
        for index in range(24)
    )
    return issue_opportunity_execution_permit(
        snapshot(finals, foundation_gate=GateOutcome.PASS)
    )


def _service_chain() -> dict[str, object]:
    torch.set_num_threads(1)
    collector: dict[str, object] = {
        "sessions": 0,
        "widths": [],
        "active_rows": 0,
        "primitive_transitions": 0,
        "reward_trace_contract": True,
    }
    authority = test_only_service_authority(TEST_MASTER, token="production-preactivity")
    services = NativeProductionServices(
        authority=authority,
        master=TEST_MASTER,
        shared_guard=_shared_guard,
        session_factory=lambda resets: _TrackingNativeSession(resets, collector),
    )
    foundation = services.materialize_foundation(replicate=0)
    trainer = DurationCorrectPPOTrainer(foundation, permit=authority)

    before = dict(collector)
    training, training_measurement = fixture_benchmark._measure(
        lambda: services.collect_and_train_update(trainer=trainer, update=1)
    )
    training_rows = training.frozen_batch.record_count
    training_transitions = sum(len(row) for row in training.frozen_batch.primitive_rewards)
    if (
        training.update_receipt.optimizer_step != 12
        or len(training.update_receipt.steps) != 12
        or training_rows != int(collector["active_rows"]) - int(before["active_rows"])
        or training_transitions
        != int(collector["primitive_transitions"]) - int(before["primitive_transitions"])
    ):
        raise RuntimeError(
            "bounded production training service count identity differs: "
            f"steps={training.update_receipt.optimizer_step}/"
            f"{len(training.update_receipt.steps)}, rows={training_rows}/"
            f"{int(collector['active_rows']) - int(before['active_rows'])}, "
            f"transitions={training_transitions}/"
            f"{int(collector['primitive_transitions']) - int(before['primitive_transitions'])}"
        )

    binding = AcceptedControllerBinding(
        controller="FOUNDATION",
        source_arm="FOUNDATION",
        model_digest=_model_digest(foundation),
        model=foundation,
        technically_accepted=True,
        frozen=True,
    )
    evaluations = []
    for stage in ("foundation-competence", "final"):
        scenarios = services.evaluation_scenarios(replicate=0, stage=stage)
        adapter = services.evaluation_adapter(stage=stage, replicate=0, scenarios=scenarios)
        scenario = next(
            row for row in scenarios if row.regime == "fixed-5" and row.scenario_index == 0
        )
        prior_rows = int(collector["active_rows"])
        prior_transitions = int(collector["primitive_transitions"])
        endpoint, measurement = fixture_benchmark._measure(
            lambda: adapter.evaluate_scenario(
                binding=binding,
                replicate=0,
                controller="FOUNDATION",
                scenario=scenario,
            )
        )
        endpoint.validate()
        evaluations.append(
            {
                "stage": stage,
                "width": 120,
                "scenario_inventory_count": len(scenarios),
                "measurement": measurement,
                "active_policy_rows": int(collector["active_rows"]) - prior_rows,
                "primitive_transitions": int(collector["primitive_transitions"])
                - prior_transitions,
                "complete_adapter_cell": True,
                "endpoint_values_exposed": False,
            }
        )

    prior_rows = int(collector["active_rows"])
    prior_transitions = int(collector["primitive_transitions"])
    opportunity, opportunity_measurement = fixture_benchmark._measure(
        lambda: services.run_opportunity_pair(
            replicate=0,
            k=7,
            state_index=0,
            permit=_test_only_opportunity_permit(),
            foundation=foundation,
        )
    )
    opportunity_active_rows = int(collector["active_rows"]) - prior_rows
    opportunity_queries = opportunity_active_rows - 144
    opportunity_transitions = int(collector["primitive_transitions"]) - prior_transitions
    if opportunity.rollout_count != 144 or opportunity_queries < 0:
        raise RuntimeError("bounded Stage-1b service inventory differs")
    return {
        "training": {
            "width": 12,
            "episode_count": 12,
            "policy_rows": training_rows,
            "primitive_transitions": training_transitions,
            "adamw_steps": 12,
            "measurement": training_measurement,
            "receipt_private_sha256": hashlib.sha256(
                _canonical(asdict(training.update_receipt))
            ).hexdigest(),
            "primitive_reward_rows_complete": all(
                1 <= len(row) <= 13 for row in training.frozen_batch.primitive_rewards
            ),
            "checkpoint_shape_in_memory_only": True,
            "question_relevant_values_exposed": False,
        },
        "checkpoint_payloads": {
            "FOUNDATION": training.checkpoint_payload,
            **{
                arm: DurationCorrectPPOTrainer(
                    services.materialize_order_arm(foundation=foundation, arm=arm),
                    permit=authority,
                ).checkpoint_payload(completed_updates=0)
                for arm in ("TREAT", "FREE", "SET")
            },
        },
        "evaluation_adapters": evaluations,
        "opportunity": {
            "width": 144,
            "pair_count": 1,
            "rollout_count": opportunity.rollout_count,
            "primitive_transitions": opportunity_transitions,
            "policy_rows": opportunity_queries,
            "measurement": opportunity_measurement,
            "full_stage_pair_count": 24 * 32,
            "q_d_s_values_exposed": False,
        },
        "native_session_inventory": {
            "session_count": collector["sessions"],
            "widths": collector["widths"],
            "reward_trace_contract": collector["reward_trace_contract"],
        },
        "serial_analyzer_measurement": fixture_benchmark._measure(
            lambda: analyze_gate(
                tuple(
                    ReplicateOpportunityMetrics(index, 0.0, 0.0, 0.0)
                    for index in range(24)
                )
            )
        )[1],
    }


class _MockCompleteServices:
    def __init__(self) -> None:
        self.calls = 0

    def foundation_final(self, context: production.RunContext, replicate: int):
        self.calls += 1
        return FoundationFinalReceipt(
            replicate,
            context.bindings.coordinate_manifest_sha256,
            _fake(f"foundation-checkpoint:{replicate}"),
            _fake(f"foundation-optimizer:{replicate}"),
        )

    def foundation_competence(self, context: production.RunContext, receipts: Sequence[object]):
        self.calls += 1
        barrier = require_foundation_checkpoint_barrier(receipts, context.bindings)
        return (
            FoundationGate(
                GateOutcome.PASS,
                _fake("foundation-panel"),
                foundation_barrier_digest(barrier),
            ),
            _fake("foundation-inference"),
        )

    def opportunity(self, context: production.RunContext, foundation_gate: FoundationGate):
        self.calls += 1
        return (
            OpportunityReceipt(GateOutcome.PASS, _fake("opportunity-stage"), "0" * 64),
            _fake("opportunity-inference"),
        )

    def adapter_final(self, context: production.RunContext, replicate: int, arm: str, adapter_permit: object):
        self.calls += 1
        return AdapterFinalReceipt(
            replicate,
            arm,
            context.bindings.coordinate_manifest_sha256,
            _fake(f"adapter-checkpoint:{replicate}:{arm}"),
            _fake(f"adapter-optimizer:{replicate}:{arm}"),
        )

    def final_evaluation(self, context: production.RunContext, final_permit: object, final_barrier: object):
        self.calls += 1
        return (
            FinalPanelReceipt(
                _fake("final-panel"), final_panel_barrier_digest(final_barrier)
            ),
            ResultCode.NONIDENTIFIED,
            _fake("final-inference"),
        )


def _checkpoint_payload_for_update(
    template: Mapping[str, object], *, update: int
) -> dict[str, object]:
    payload = dict(template)
    payload["completed_updates"] = update
    optimizer = dict(payload["optimizer"])
    optimizer["step_index"] = update * 12
    payload["optimizer"] = optimizer
    return payload


def _serialized_checkpoint_bytes(payload: Mapping[str, object]) -> int:
    stream = io.BytesIO()
    torch.save(payload, stream)
    return len(stream.getvalue())


def _frontier_values(arm: str, *, token: str) -> tuple[FrontierGeneration, ...]:
    bindings = test_only_bindings(token=token)
    stage = FrontierStage.FOUNDATION if arm == "FOUNDATION" else FrontierStage.ADAPTER
    limit = 160 if arm == "FOUNDATION" else 96
    values = [
        FrontierGeneration(
            stage=stage,
            replicate=0,
            arm=arm,
            lineage_digest=bindings.lineage_digest,
            coordinate_manifest_sha256=bindings.coordinate_manifest_sha256,
            generation=0,
            previous_generation_sha256=None,
            state=FrontierState.CREATED,
            update_index=0,
            optimizer_step=0,
        )
    ]
    predecessor = frontier_generation_digest(values[0], bindings)
    for update in range(1, limit + 1):
        final = update == limit
        value = FrontierGeneration(
            stage=stage,
            replicate=0,
            arm=arm,
            lineage_digest=bindings.lineage_digest,
            coordinate_manifest_sha256=bindings.coordinate_manifest_sha256,
            generation=update,
            previous_generation_sha256=predecessor,
            state=FrontierState.FINAL_CHECKPOINT if final else FrontierState.TRAINING,
            update_index=update,
            optimizer_step=update * 12,
            checkpoint_sha256=_fake(f"{arm}:final-checkpoint") if final else None,
            optimizer_state_sha256=_fake(f"{arm}:final-optimizer") if final else None,
        )
        values.append(value)
        predecessor = frontier_generation_digest(value, bindings)
    return tuple(values)


def _checkpoint_receipt_payload(
    arm: str, update: int, *, token: str
) -> dict[str, object]:
    bindings = test_only_bindings(token=token)
    return {
        "schema": "SCDMP_TBCC_R02_BLINDED_CHECKPOINT_GENERATION_RECEIPT_V1",
        "lineage_digest": bindings.lineage_digest,
        "coordinate_manifest_sha256": bindings.coordinate_manifest_sha256,
        "replicate": 0,
        "arm": arm,
        "generation": update,
        "checkpoint_sha256": hashlib.sha256(f"{arm}:{update}:checkpoint".encode("ascii")).hexdigest(),
        "optimizer_state_sha256": hashlib.sha256(f"{arm}:{update}:optimizer".encode("ascii")).hexdigest(),
        "frontier_generation_sha256": _fake(f"{arm}:{update}:frontier"),
        "partial_inspection_permitted": False,
    }


def _exact_generation_storage(
    checkpoint_payloads: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    def build() -> dict[str, object]:
        arms: dict[str, object] = {}
        total = 0
        update_generations = 0
        initial_frontiers = 0
        for arm in ("FOUNDATION", "TREAT", "FREE", "SET"):
            limit = 160 if arm == "FOUNDATION" else 96
            slots = 24
            token = f"production-preactivity-storage-{arm.lower()}"
            bindings = test_only_bindings(token=token)
            frontiers = _frontier_values(arm, token=token)
            checkpoint_sizes = [
                _serialized_checkpoint_bytes(
                    _checkpoint_payload_for_update(checkpoint_payloads[arm], update=update)
                )
                for update in range(1, limit + 1)
            ]
            receipt_sizes = [
                len(_canonical(_checkpoint_receipt_payload(arm, update, token=token)))
                for update in range(1, limit + 1)
            ]
            frontier_sizes = [
                len(_canonical(value.payload(bindings))) for value in frontiers[1:]
            ]
            initial_size = len(_canonical(frontiers[0].payload(bindings)))
            per_slot = sum(checkpoint_sizes) + sum(receipt_sizes) + sum(frontier_sizes) + initial_size
            arm_total = per_slot * slots
            total += arm_total
            update_generations += limit * slots
            initial_frontiers += slots
            arms[arm] = {
                "updates_per_slot": limit,
                "slot_count": slots,
                "update_generation_count": limit * slots,
                "initial_frontier_count": slots,
                "checkpoint_size_min_bytes": min(checkpoint_sizes),
                "checkpoint_size_max_bytes": max(checkpoint_sizes),
                "checkpoint_bytes_exact": sum(checkpoint_sizes) * slots,
                "receipt_size_min_bytes": min(receipt_sizes),
                "receipt_size_max_bytes": max(receipt_sizes),
                "receipt_bytes_exact": sum(receipt_sizes) * slots,
                "update_frontier_size_min_bytes": min(frontier_sizes),
                "update_frontier_size_max_bytes": max(frontier_sizes),
                "update_frontier_bytes_exact": sum(frontier_sizes) * slots,
                "initial_frontier_size_bytes": initial_size,
                "initial_frontier_bytes_exact": initial_size * slots,
                "total_bytes_exact": arm_total,
            }
        return {
            "arms": arms,
            "exact_update_generation_count": update_generations,
            "exact_initial_frontier_count": initial_frontiers,
            "checkpoint_receipt_update_frontier_bytes_exact": total,
        }

    payload, measurement = fixture_benchmark._measure(build)
    payload["inventory_construction_measurement"] = measurement
    return payload


def _write_representative_arm_chain(
    root: Path, arm: str, checkpoint_payload: Mapping[str, object]
) -> dict[str, object]:
    token = f"production-preactivity-io-{arm.lower()}"
    bindings = test_only_bindings(token=token)
    arm_root = root / f"representative-{arm.lower()}"
    checkpoint_path = arm_root / "checkpoint.pt"
    receipt_path = arm_root / "receipt.json"
    frontier_paths = [
        arm_root / f"generation-{value.generation:04d}.json"
        for value in _frontier_values(arm, token=token)
    ]
    checkpoint_digest, checkpoint_write = fixture_benchmark._measure(
        lambda: production._atomic_create_binary(
            checkpoint_path,
            _checkpoint_payload_for_update(checkpoint_payload, update=1),
            root=root,
        )
    )
    receipt = _checkpoint_receipt_payload(arm, 1, token=token)
    _, receipt_write = fixture_benchmark._measure(
        lambda: atomic_create_json(receipt_path, receipt, artifact_root=root)
    )
    values = _frontier_values(arm, token=token)

    def write_frontiers() -> None:
        for path, value in zip(frontier_paths, values):
            atomic_create_json(path, value.payload(bindings), artifact_root=root)

    _, frontier_write = fixture_benchmark._measure(write_frontiers)

    def load_all() -> tuple[object, object, object]:
        checkpoint = production._load_checkpoint(checkpoint_path, root=root)
        receipt_value = production.load_canonical_json(receipt_path, artifact_root=root)
        chain = load_resume_chain(frontier_paths, artifact_root=root, bindings=bindings)
        return checkpoint, receipt_value, chain

    loaded, full_resume = fixture_benchmark._measure(load_all)
    if loaded[0][1] != checkpoint_digest or loaded[1] != receipt or loaded[2] != values:
        raise RuntimeError(f"representative {arm} checkpoint/receipt/frontier resume differs")
    return {
        "checkpoint_path": checkpoint_path,
        "receipt_path": receipt_path,
        "frontier_paths": frontier_paths,
        "checkpoint_sha256": checkpoint_digest,
        "frontier_final_digest": frontier_generation_digest(values[-1], bindings),
        "checkpoint_bytes": checkpoint_path.stat().st_size,
        "receipt_bytes": receipt_path.stat().st_size,
        "frontier_chain_bytes": sum(path.stat().st_size for path in frontier_paths),
        "frontier_generation_count": len(frontier_paths),
        "checkpoint_write_measurement": checkpoint_write,
        "receipt_write_measurement": receipt_write,
        "frontier_chain_write_measurement": frontier_write,
        "full_resume_measurement": full_resume,
    }


def _io_and_mocked_runner(
    root: Path, checkpoint_payloads: Mapping[str, Mapping[str, object]]
) -> dict[str, object]:
    token = "production-preactivity-mocked-complete"
    context = production.test_only_run_context(root, token=token)
    services = _MockCompleteServices()
    result_digest, branch_measurement = fixture_benchmark._measure(
        lambda: production.execute_realized_path(context, services=services)
    )
    if services.calls != 99:
        raise RuntimeError("mocked complete branch did not traverse the exact complete inventory")
    resumed_services = _MockCompleteServices()
    resumed_digest, local_resume_measurement = fixture_benchmark._measure(
        lambda: production.execute_realized_path(context, services=resumed_services)
    )
    if resumed_digest != result_digest or resumed_services.calls != 0:
        raise RuntimeError("complete-result same-coordinate resume differs")
    generation_storage = _exact_generation_storage(checkpoint_payloads)
    representative = {
        arm: _write_representative_arm_chain(root, arm, checkpoint_payloads[arm])
        for arm in ("FOUNDATION", "TREAT", "FREE", "SET")
    }
    child = subprocess.run(
        [
            sys.executable,
            "-m",
            MODULE,
            "--resume-child",
            "--resume-root",
            str(root),
        ],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )
    cold = json.loads(child.stdout)
    if (
        cold["complete_result_sha256"] != result_digest
        or any(
            cold["arms"][arm]["frontier_final_digest"]
            != representative[arm]["frontier_final_digest"]
            or cold["arms"][arm]["checkpoint_sha256"]
            != representative[arm]["checkpoint_sha256"]
            for arm in representative
        )
    ):
        raise RuntimeError("cold production-shaped resume differs")
    durable_bytes = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    final_paths = tuple(
        root / name
        for name in (
            production.FOUNDATION_GATE_NAME,
            production.OPPORTUNITY_RECEIPT_NAME,
            production.COMPLETION_INVENTORY_NAME,
            production.FINAL_RESULT_NAME,
        )
    )
    final_gate_result_bytes = sum(path.stat().st_size for path in final_paths)
    installed_preactivity_bytes = sum(
        (root / name).stat().st_size
        for name in ("empirical_source_manifest.json", "CM_PREACTIVITY_ACCEPTANCE.json")
        if (root / name).is_file()
    )
    return {
        "mocked_complete_branch_measurement": branch_measurement,
        "same_process_resume_measurement": local_resume_measurement,
        "mocked_complete_service_calls": services.calls,
        "branch_values_exposed": False,
        "complete_result_values_exposed": False,
        "generation_storage": generation_storage,
        "representative_arm_io": {
            arm: {key: value for key, value in row.items() if not key.endswith("_path") and key != "frontier_paths"}
            for arm, row in representative.items()
        },
        "checkpoint_payload_values_exposed": False,
        "exact_update_generation_count": generation_storage["exact_update_generation_count"],
        "exact_initial_frontier_count": generation_storage["exact_initial_frontier_count"],
        "frontier_values_exposed": False,
        "cold_resume": cold,
        "durable_fixture_bytes": durable_bytes,
        "final_gate_result_file_count": len(final_paths),
        "final_gate_result_bytes": final_gate_result_bytes,
        "installed_manifest_preactivity_bytes": installed_preactivity_bytes,
        "atomic_create_only": True,
        "same_coordinate_resume": True,
    }


def _resume_child(root: Path) -> dict[str, object]:
    context = production.test_only_run_context(
        root, token="production-preactivity-mocked-complete"
    )
    services = _MockCompleteServices()
    result = production.execute_realized_path(context, services=services)
    if services.calls != 0:
        raise RuntimeError("cold complete-result resume re-executed mocked services")
    arms = {}
    for arm in ("FOUNDATION", "TREAT", "FREE", "SET"):
        token = f"production-preactivity-io-{arm.lower()}"
        bindings = test_only_bindings(token=token)
        arm_root = root / f"representative-{arm.lower()}"
        paths = [
            arm_root / f"generation-{value.generation:04d}.json"
            for value in _frontier_values(arm, token=token)
        ]
        frontier = load_resume_chain(paths, artifact_root=root, bindings=bindings)
        checkpoint, checkpoint_sha = production._load_checkpoint(
            arm_root / "checkpoint.pt", root=root
        )
        receipt = production.load_canonical_json(arm_root / "receipt.json", artifact_root=root)
        if not isinstance(checkpoint, Mapping) or not isinstance(receipt, Mapping):
            raise RuntimeError("cold checkpoint/receipt payload differs")
        arms[arm] = {
            "frontier_final_digest": frontier_generation_digest(frontier[-1], bindings),
            "checkpoint_sha256": checkpoint_sha,
            "frontier_generation_count": len(frontier),
        }
    return {
        "complete_result_sha256": result,
        "arms": arms,
        "mocked_services_reexecuted": False,
    }


def _optimizer_proof_digest(trainer: DurationCorrectPPOTrainer) -> str:
    payload = trainer.optimizer.moment_payload()
    rows = {
        "arm": trainer.arm,
        "parameter_names": list(payload["parameter_names"]),
        "step_index": payload["step_index"],
        "first": {
            name: fixture_benchmark._tensor_digest((value,))
            for name, value in payload["first_moments"].items()
        },
        "second": {
            name: fixture_benchmark._tensor_digest((value,))
            for name, value in payload["second_moments"].items()
        },
    }
    return hashlib.sha256(_canonical(rows)).hexdigest()


def _production_thread_topology() -> tuple[list[dict[str, object]], dict[str, object]]:
    torch.set_num_threads(1)
    ordinal_count = 64
    topology_rows = []
    for workers in (1, 2, 4):
        authority = test_only_service_authority(TEST_MASTER, token=f"thread-topology-{workers}")
        services = NativeProductionServices(
            authority=authority,
            master=TEST_MASTER,
            shared_guard=_shared_guard,
        )
        services._guard(12)
        block = ordinal_count // workers
        ranges = tuple((index * block, (index + 1) * block) for index in range(workers))
        bindings = test_only_bindings(token="production-thread-topology-proof")

        def execute_range(value: object) -> list[dict[str, object]]:
            start, stop = value
            result = []
            for ordinal in range(int(start), int(stop)):
                foundation = services.materialize_foundation(replicate=ordinal % 24)
                arm = ("FOUNDATION", "TREAT", "FREE", "SET")[ordinal % 4]
                model = (
                    foundation
                    if arm == "FOUNDATION"
                    else services.materialize_order_arm(foundation=foundation, arm=arm)
                )
                trainer = DurationCorrectPPOTrainer(model, permit=authority)
                endpoint = native_backend.test_only_primitive(
                    q=ordinal % 2,
                    tick=40 + ordinal % 7,
                    x=3.0,
                    v=0.5,
                    y=0.02,
                    w=-0.01,
                    phi=0.03,
                    omega=-0.02,
                    z=(0.01, 0.02, 0.03, 0.04),
                    formation=0.02,
                    prior_a=1,
                    prior_r=(0, 0, 0, 0),
                    action=ordinal % 18,
                    eta_v=-0.003 if ordinal % 2 else 0.003,
                    eta_y=0.002,
                    eta_omega=-0.004 if ordinal % 3 else 0.004,
                )
                frontier = FrontierGeneration(
                    stage=FrontierStage.FOUNDATION if arm == "FOUNDATION" else FrontierStage.ADAPTER,
                    replicate=ordinal % 24,
                    arm=arm,
                    lineage_digest=bindings.lineage_digest,
                    coordinate_manifest_sha256=bindings.coordinate_manifest_sha256,
                    generation=1,
                    previous_generation_sha256=_fake(f"thread-topology-predecessor:{ordinal}"),
                    state=FrontierState.TRAINING,
                    update_index=1,
                    optimizer_step=12,
                )
                endpoint_payload = {
                    "advanced": endpoint.advanced,
                    "active": endpoint.active,
                    "terminal": endpoint.terminal,
                    "ticks_advanced": endpoint.ticks_advanced,
                    "tick": endpoint.tick,
                    "reward_count": endpoint.last_hold_reward_count,
                    "reward_trace": list(endpoint.last_hold_rewards),
                }
                result.append(
                    {
                        "global_ordinal": ordinal,
                        "arm": arm,
                        "native_service_artifact_sha256": services._guard(12)["native"]["artifact_sha256"],
                        "model_sha256": _model_digest(model),
                        "optimizer_sha256": _optimizer_proof_digest(trainer),
                        "frontier_sha256": hashlib.sha256(
                            _canonical(frontier.payload(bindings))
                        ).hexdigest(),
                        "endpoint_sha256": hashlib.sha256(
                            _canonical(endpoint_payload)
                        ).hexdigest(),
                    }
                )
            return result

        grouped, measurement = fixture_benchmark._measure(
            lambda: production._parallel_ordered(workers, execute_range, ranges)
        )
        merged = [row for group in grouped for row in group]
        ordinals = [int(row["global_ordinal"]) for row in merged]
        complete = ordinals == list(range(ordinal_count)) and len(set(ordinals)) == ordinal_count
        if not complete:
            raise RuntimeError("production thread topology ordinal partition differs")
        topology_rows.append(
            {
                "workers": workers,
                "ordinal_ranges": [list(value) for value in ranges],
                "ordinal_inventory_complete": complete,
                "concrete_native_service": True,
                "model_optimizer_frontier_endpoint_proof": True,
                "merged_semantic_sha256": hashlib.sha256(_canonical(merged)).hexdigest(),
                "measurement": measurement,
                "aggregate_units_per_second": ordinal_count / float(measurement["wall_seconds"]),
            }
        )
    reference = topology_rows[0]["merged_semantic_sha256"]
    if any(row["merged_semantic_sha256"] != reference for row in topology_rows):
        raise RuntimeError("production ThreadPoolExecutor semantic frontier differs")
    baseline = float(topology_rows[0]["measurement"]["wall_seconds"])
    for row in topology_rows:
        workers = int(row["workers"])
        raw = baseline / float(row["measurement"]["wall_seconds"])
        effective = min(float(workers), raw)
        row["raw_speedup_vs_one_thread"] = raw
        row["effective_speedup_vs_one_thread"] = effective
        row["parallel_efficiency"] = effective / workers
    selected = max(topology_rows, key=lambda row: float(row["aggregate_units_per_second"]))
    return topology_rows, {
        "schema": "TEST_ONLY_TBCC_PRODUCTION_THREADPOOL_TOPOLOGY_V1",
        "uses_production_parallel_ordered": True,
        "uses_thread_pool_executor": True,
        "exact_disjoint_unique_ordinal_count": ordinal_count,
        "all_merged_semantic_frontiers_equal": True,
        "merged_semantic_sha256": reference,
        "selected_worker_count": selected["workers"],
        "measured_effective_speedup": selected["effective_speedup_vs_one_thread"],
        "parallel_efficiency": selected["parallel_efficiency"],
        "acceptance_speedup_source": "current_production_threadpool_measurement",
        "old_subprocess_worker_evidence_used_for_acceptance": False,
    }


def _projection(
    widths: Sequence[Mapping[str, object]],
    forwards: Sequence[Mapping[str, object]],
    kernels: Sequence[Mapping[str, object]],
    service: Mapping[str, object],
    preflight: Mapping[str, object],
    io_row: Mapping[str, object],
    worker_proof: Mapping[str, object],
) -> dict[str, object]:
    environment_rate = min(float(row["native_transitions_per_second"]) for row in widths)
    query_rate = min(
        float(controller["batched_rows_per_second"])
        for row in forwards
        for controller in row["controllers"].values()
    )
    adamw_rate = min(
        int(row["adamw_steps"]) / float(row["measurement"]["wall_seconds"])
        for row in kernels
    )
    environment = PANEL_COUNTS["complete_allocated_slots"] / environment_rate
    queries = PANEL_COUNTS["complete_max_policy_queries"] / query_rate
    adamw = PANEL_COUNTS["complete_adamw_steps"] / adamw_rate

    training = service["training"]
    training_kernel = (
        int(training["primitive_transitions"]) / environment_rate
        + int(training["policy_rows"]) / query_rate
        + int(training["adamw_steps"]) / adamw_rate
    )
    training_net = max(
        0.0, float(training["measurement"]["wall_seconds"]) - training_kernel
    ) * (24 * 160 + 24 * 3 * 96)
    evaluation_net = 0.0
    for row in service["evaluation_adapters"]:
        measured_kernel = (
            int(row["primitive_transitions"]) / environment_rate
            + int(row["active_policy_rows"]) / query_rate
        )
        evaluation_net += max(
            0.0, float(row["measurement"]["wall_seconds"]) - measured_kernel
        )
    evaluation_net = evaluation_net / 2.0 * (24 * 6 + 24 * 5 * 6)
    opportunity = service["opportunity"]
    opportunity_kernel = (
        int(opportunity["primitive_transitions"]) / environment_rate
        + int(opportunity["policy_rows"]) / query_rate
    )
    opportunity_net = max(
        0.0, float(opportunity["measurement"]["wall_seconds"]) - opportunity_kernel
    ) * int(opportunity["full_stage_pair_count"])
    foreground_once = (
        float(preflight["direct_measurement"]["wall_seconds"])
        + float(preflight["foreground_cli_measurement"]["wall_seconds"])
    )
    io_totals = {
        "wall_seconds": float(io_row["mocked_complete_branch_measurement"]["wall_seconds"])
        + float(io_row["same_process_resume_measurement"]["wall_seconds"]),
        "cpu_seconds": float(io_row["mocked_complete_branch_measurement"]["cpu_seconds"])
        + float(io_row["same_process_resume_measurement"]["cpu_seconds"]),
        "read_bytes": int(io_row["mocked_complete_branch_measurement"]["io_read_bytes"])
        + int(io_row["same_process_resume_measurement"]["io_read_bytes"]),
        "write_bytes": int(io_row["mocked_complete_branch_measurement"]["io_write_bytes"])
        + int(io_row["same_process_resume_measurement"]["io_write_bytes"]),
    }
    worst_resume_wall = 0.0
    for arm, row in io_row["representative_arm_io"].items():
        update_count = int(io_row["generation_storage"]["arms"][arm]["update_generation_count"])
        slot_count = int(io_row["generation_storage"]["arms"][arm]["slot_count"])
        for key, multiplier in (
            ("checkpoint_write_measurement", update_count),
            ("receipt_write_measurement", update_count),
            ("frontier_chain_write_measurement", slot_count),
            ("full_resume_measurement", slot_count),
        ):
            measurement = row[key]
            io_totals["wall_seconds"] += float(measurement["wall_seconds"]) * multiplier
            io_totals["cpu_seconds"] += float(measurement["cpu_seconds"]) * multiplier
            io_totals["read_bytes"] += int(measurement["io_read_bytes"]) * multiplier
            io_totals["write_bytes"] += int(measurement["io_write_bytes"]) * multiplier
        worst_resume_wall += float(row["full_resume_measurement"]["wall_seconds"]) * slot_count
    analyzer_wall = float(service["serial_analyzer_measurement"]["wall_seconds"])
    analyzer_cpu = float(service["serial_analyzer_measurement"]["cpu_seconds"])
    parallel_components = {
        "native_environment_slots": environment,
        "batched_policy_queries": queries,
        "adamw_steps": adamw,
        "production_training_orchestration": training_net,
        "production_evaluation_orchestration": evaluation_net,
        "production_opportunity_orchestration": opportunity_net,
    }
    serial_components = {
        "foreground_preactivity_orchestration": foreground_once,
        "serial_analyzer_orchestration": analyzer_wall,
        "production_checkpoint_receipt_frontier_gate_result_io_and_worst_resume": io_totals["wall_seconds"],
    }
    total = sum(parallel_components.values()) + sum(serial_components.values())
    speedup = float(worker_proof["measured_effective_speedup"])
    storage = (
        int(io_row["generation_storage"]["checkpoint_receipt_update_frontier_bytes_exact"])
        + int(io_row["final_gate_result_bytes"])
        + int(io_row["installed_manifest_preactivity_bytes"])
    )
    peak_rss = max(
        [int(row["fixture_oracle"][0]["peak_rss_bytes"]) for row in widths]
        + [int(row["optimized_native"][0]["peak_rss_bytes"]) for row in widths]
        + [int(training["measurement"]["peak_rss_bytes"])]
        + [int(row["measurement"]["peak_rss_bytes"]) for row in service["evaluation_adapters"]]
        + [int(opportunity["measurement"]["peak_rss_bytes"])]
    )
    wall = sum(parallel_components.values()) / speedup + sum(serial_components.values())
    wall_components = {
        **{key: value / speedup for key, value in parallel_components.items()},
        **serial_components,
    }
    return {
        "method": "exact_card_slots_queries_adamw_and_parallel_service_orchestration_divided_only_by_current_measured_production_ThreadPoolExecutor_effective_speedup; loader_preactivity_analyzer_checkpoint_receipt_frontier_gate_result_atomic_io_and_one_worst_resume_remain_serial",
        "exact_counts": dict(PANEL_COUNTS),
        "environment_transitions_per_second": environment_rate,
        "conservative_batched_policy_rows_per_second": query_rate,
        "conservative_adamw_steps_per_second": adamw_rate,
        "parallel_component_cpu_equivalent_seconds": parallel_components,
        "serial_component_seconds": serial_components,
        "projected_wall_component_seconds": wall_components,
        "serial_components_divided_by_thread_speedup": False,
        "kernel_double_counting": False,
        "composed_cpu_seconds": total,
        "composed_cpu_core_hours": total / 3600.0,
        "measured_effective_speedup": speedup,
        "projected_wall_seconds": wall,
        "projected_wall_hours": wall / 3600.0,
        "peak_rss_bytes": peak_rss,
        "projected_storage_bytes": storage,
        "projected_storage_gib": storage / float(1 << 30),
        "exact_update_generation_count": io_row["exact_update_generation_count"],
        "exact_initial_frontier_count": io_row["exact_initial_frontier_count"],
        "projected_io": {
            "cpu_seconds": io_totals["cpu_seconds"],
            "wall_seconds": io_totals["wall_seconds"],
            "read_bytes": io_totals["read_bytes"],
            "write_bytes": io_totals["write_bytes"],
            "worst_resume_wall_seconds": worst_resume_wall,
            "serial": True,
        },
        "serial_analyzer_cpu_seconds": analyzer_cpu,
        "dominant_bottleneck": max(wall_components, key=wall_components.get),
        "resource_class_remains_credible": (
            total <= 240 * 3600
            and wall <= 72 * 3600
            and peak_rss <= 20 * (1 << 30)
            and storage <= 4 * (1 << 30)
        ),
        "production_runner_formally_executed": False,
        "residual_uncertainty": "foreground production runner was not formally executed; TEST-only sealed preflight, concrete bounded services, and a mocked complete branch measure its mechanics without empirical activity",
    }


def run_benchmark(*, repeats: int = 1, temp_root: Path | None = None) -> dict[str, object]:
    if repeats < 1:
        raise ValueError("repeats must be positive")
    torch.set_num_threads(1)
    repository_root = Path(__file__).resolve().parents[2]
    parent = None if temp_root is None else Path(temp_root).resolve()
    if parent is not None:
        parent.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="scdmp_tbcc_r02_production_preactivity_", dir=parent))
    try:
        cold_loader = _process_cold_loader()
        warm_loader = _warm_loader()
        widths = [fixture_benchmark._width_measurement(width, repeats) for width in WIDTHS]
        forwards = [fixture_benchmark._forward_measurement(width, max(2, repeats)) for width in WIDTHS]
        kernels = [
            fixture_benchmark._training_kernel(kind, 12, 12)
            for kind in ("FOUNDATION", "ORDER")
        ]
        primitive = _primitive_reward_trace()
        preflight = _source_and_preflight(repository_root, workspace)
        service = _service_chain()
        io_row = _io_and_mocked_runner(workspace, service.pop("checkpoint_payloads"))
        worker_rows, worker_proof = _production_thread_topology()
        projection = _projection(
            widths, forwards, kernels, service, preflight, io_row, worker_proof
        )
        semantic = {
            "oracle_native_all_widths": all(row["oracle_native_equal"] for row in widths),
            "fixed_lane_positions_and_masks": all(row["lane_positions_preserved"] for row in widths),
            "scalar_unbatched_vs_batched_torch": all(
                controller["rowwise_semantic_equal"]
                for row in forwards
                for controller in row["controllers"].values()
            ),
            "abi2_primitive_reward_trace": primitive["oracle_native_reward_equal"],
            "production_training_update_complete": service["training"]["adamw_steps"] == 12,
            "competence_and_final_evaluation_adapters_complete": all(
                row["complete_adapter_cell"] for row in service["evaluation_adapters"]
            ),
            "stage1b_service_complete": service["opportunity"]["rollout_count"] == 144,
            "production_thread_partitions_complete": (
                worker_proof["exact_disjoint_unique_ordinal_count"] == 64
            ),
            "production_thread_frontiers_equal": worker_proof[
                "all_merged_semantic_frontiers_equal"
            ],
            "atomic_io_and_cold_resume": io_row["same_coordinate_resume"],
            "question_relevant_values_absent": True,
        }
        if not all(value is True for value in semantic.values()):
            raise RuntimeError("production preactivity semantic equivalence is incomplete")
        source_manifest = preflight["source_manifest"]
        record = {
            "schema": SCHEMA,
            "fixture_only": True,
            "question_relevant_output": False,
            "formal_compute": False,
            "scientific_activity": False,
            "chain_coverage": list(CHAIN_COVERAGE),
            "prohibited_empirical_objects": {
                "identity": False,
                "coordinate": False,
                "master": False,
                "model": False,
                "checkpoint": False,
                "training": False,
                "evaluation": False,
                "result": False,
                "lease": False,
                "activity": False,
            },
            "os_entropy_for_science_or_addressing": False,
            "test_only_fixed_bytes_for_mechanics": True,
            "command": {
                "interpreter": sys.executable,
                "module": MODULE,
                "repeats": repeats,
                "torch_threads": 1,
            },
            "production_source_set": {
                "manifest_schema": source_manifest["schema"],
                "manifest_sha256": preflight["source_manifest_sha256"],
                "source_file_set_sha256": preflight["source_file_set_sha256"],
                "source_file_count": preflight["source_file_count"],
                "files": source_manifest["files"],
            },
            "abi2_shared_receipt": preflight["shared_receipt"],
            "abi2_shared_receipt_sha256": preflight["shared_receipt_sha256"],
            "loader": {
                "process_cold_shared_abi2": cold_loader,
                "process_local_warm_shared_abi2": warm_loader,
            },
            "environment_scalar_oracle_vs_native": widths,
            "controller_scalar_vs_batched": forwards,
            "forward_backward_adamw": kernels,
            "abi2_primitive_reward_trace": primitive,
            "bounded_test_only_production_services": service,
            "foreground_runner_preactivity": {
                "direct_measurement": preflight["direct_measurement"],
                "foreground_cli_measurement": preflight["foreground_cli_measurement"],
                "identity_free": preflight["foreground_cli_identity_free"],
                "production_runner_formally_executed": False,
            },
            "checkpoint_frontier_gate_result_atomic_io_resume": io_row,
            "production_thread_topology_scaling": worker_rows,
            "production_thread_topology_equivalence": worker_proof,
            "historical_subprocess_worker_provenance": {
                "acceptance_use": False,
                "retained_measured_effective_speedup": RETAINED_SPEEDUP,
                "reason": "subprocess topology differs from production _parallel_ordered ThreadPoolExecutor",
            },
            "semantic_equivalence": semantic,
            "full_panel_projection": projection,
            "dominant_bottleneck": projection["dominant_bottleneck"],
            "efficiency_review": (
                "COMPLETE" if projection["resource_class_remains_credible"] else "REPAIR_REQUIRED"
            ),
            "production_runner_not_formally_executed": True,
            "scientific_values_retained_or_exposed": False,
        }
        return record
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def write_record(path: Path, value: Mapping[str, object]) -> None:
    target = Path(path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    pending = target.with_name(f".{target.name}.{os.getpid()}.pending")
    payload = _canonical(value)
    with pending.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, target)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--temp-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cold-child", action="store_true")
    parser.add_argument("--resume-child", action="store_true")
    parser.add_argument("--resume-root", type=Path)
    arguments = parser.parse_args(argv)
    if arguments.cold_child:
        print(_canonical(_cold_child()).decode("ascii"), end="")
        return 0
    if arguments.resume_child:
        if arguments.resume_root is None:
            parser.error("--resume-child requires --resume-root")
        print(_canonical(_resume_child(arguments.resume_root.resolve())).decode("ascii"), end="")
        return 0
    record = run_benchmark(repeats=arguments.repeats, temp_root=arguments.temp_root)
    record["command"]["argv"] = list(sys.argv)
    if arguments.output is not None:
        write_record(arguments.output, record)
    print(_canonical(record).decode("ascii"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
