"""Fresh single-pass production transaction for the frozen CRTO object."""

from __future__ import annotations

from collections import Counter
import base64
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
from typing import Any, Mapping, Sequence


_THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)
PRODUCTION_CAPABILITY_VERSION = "CRTO_SINGLE_PASS_PRODUCTION_V1"
PRODUCTION_WORKER_ENV = "HMASD_CRTO_PRODUCTION_WORKER"
PRODUCTION_WORKER_SENTINEL = "CRTO-COMMON-HISTORY-GATE-20260830-01"
_PREFLIGHT_GATE_KEYS = frozenset({
    "resource_4gib", "resource_run_envelope", "exact_population_schedule",
    "fresh_scientific_targets", "runtime_envelope", "result_blind_structural_scan",
    "single_pass_production_pipeline", "long_production_efficiency_review",
})
_LONG_PRODUCTION_WITHHOLD_ISSUE = (
    "WITHHOLD_LONG_PRODUCTION: transaction conformance is implemented, but the "
    "eight-slot Python/native-host route lacks an accepted stage-throughput and "
    "efficiency review; only the fixed two-slot RAW pilot is launch-eligible"
)


def production_capability() -> dict[str, object]:
    """Declare result-blind production stages without importing Torch or constructing state."""
    return {
        "version": PRODUCTION_CAPABILITY_VERSION,
        "single_pass_population_traversal": True,
        "second_launch_admission_before_science": True,
        "raw_long_k8_staged_gate": True,
        "residual_evaluation_only_after_competence": True,
        "validated_create_only_publication": True,
    }


@dataclass
class _SlotState:
    replicate: int
    predictor_audit: object
    calibration_table: object
    calibration_report: Mapping[str, object]
    training_rows: tuple[object, ...]
    evaluation_rows: tuple[object, ...]
    support_failures: tuple[str, ...] = ()
    paths: Mapping[object, object] | None = None
    evaluation_packets: Mapping[object, object] | None = None
    derangement_plans: Mapping[str, object] | None = None


class _TransactionPayload(dict[str, object]):
    """JSON mapping carrying a private live runtime monitor to the publisher."""

    def __init__(self, payload: Mapping[str, object], ledger: object) -> None:
        super().__init__(payload)
        self._ledger = ledger

    def terminal_runtime_snapshot(self) -> object:
        self._ledger.check_limits()
        return self._ledger.snapshot()

    def require_terminal_limits(self) -> None:
        self._ledger.check_limits()


def _require_first_preflight(preflight: Mapping[str, object]) -> int:
    from .preflight import EXPECTED_PRODUCTION_CAPABILITY

    if preflight.get("format") != "CRTO_COMMON_HISTORY_PROSPECTIVE_PREFLIGHT_V1":
        raise PermissionError("production requires the exact prospective preflight format")
    if (
        preflight.get("object_id") != "CRTO-COMMON-HISTORY-GATE-20260830-01"
        or preflight.get("rng_namespace") != 2_026_083_001
        or preflight.get("replicates") != list(range(8))
    ):
        raise PermissionError("production preflight identity or fixed address census drifted")
    current_capability = production_capability()
    expected_capability = dict(EXPECTED_PRODUCTION_CAPABILITY)
    if current_capability != expected_capability or preflight.get(
        "production_capability"
    ) != expected_capability:
        raise PermissionError(
            "production capability drifted from the exact passed preflight receipt"
        )
    gates = preflight.get("gates")
    if not isinstance(gates, Mapping) or set(gates) != _PREFLIGHT_GATE_KEYS:
        raise PermissionError(
            "WITHHOLD_LONG_PRODUCTION: prospective receipt lacks the exact current gate set"
        )
    for name in _PREFLIGHT_GATE_KEYS - {"long_production_efficiency_review"}:
        gate = gates[name]
        if not isinstance(gate, Mapping) or gate.get("passed") is not True or gate.get(
            "issues"
        ) != []:
            raise PermissionError(
                f"WITHHOLD_LONG_PRODUCTION: prerequisite gate {name} is not exact-pass"
            )
    efficiency = gates["long_production_efficiency_review"]
    if (
        not isinstance(efficiency, Mapping)
        or efficiency.get("passed") is not False
        or efficiency.get("issues") != [_LONG_PRODUCTION_WITHHOLD_ISSUE]
        or preflight.get("ready_for_optimizer") is not False
    ):
        raise PermissionError(
            "WITHHOLD_LONG_PRODUCTION: forged or drifted efficiency gate cannot authorize launch"
        )
    structural = preflight.get("structural_scan")
    ledger = structural.get("ledger") if isinstance(structural, Mapping) else None
    expected = ledger.get("actual_common_future_branch_count") if isinstance(ledger, Mapping) else None
    if (
        isinstance(expected, bool) or not isinstance(expected, int) or expected <= 0
        or ledger.get("pre_result_exact") is not True or ledger.get("within_ceiling") is not True
    ):
        raise PermissionError("preflight lacks an exact passing common-future branch ledger")
    raise PermissionError(_LONG_PRODUCTION_WITHHOLD_ISSUE)


def _configure_one_thread_environment() -> None:
    """Fail closed unless the isolated worker bound native libraries before import."""
    failures = [name for name in _THREAD_ENVIRONMENT if os.environ.get(name) != "1"]
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        failures.append("CUDA_VISIBLE_DEVICES")
    if failures:
        raise RuntimeError(
            "CRTO production requires the isolated one-thread CPU worker environment: "
            + ", ".join(failures)
        )


def _bind_torch_one_thread(torch_module: object) -> None:
    torch_module.set_num_threads(1)  # type: ignore[attr-defined]
    try:
        torch_module.set_num_interop_threads(1)  # type: ignore[attr-defined]
    except RuntimeError:
        if int(torch_module.get_num_interop_threads()) != 1:  # type: ignore[attr-defined]
            raise
    if (
        int(torch_module.get_num_threads()) != 1  # type: ignore[attr-defined]
        or int(torch_module.get_num_interop_threads()) != 1  # type: ignore[attr-defined]
    ):
        raise RuntimeError("CRTO production requires exactly one Torch thread")


def _load_components() -> SimpleNamespace:
    """Import Torch/scientific components only after second admission and thread binding."""
    import torch

    _bind_torch_one_thread(torch)
    from .analysis import analyze, assess_raw_long_competence
    from .calibration import assess_calibration, fit_calibration_from_examples, slot_calibration_diagnostics
    from .config import REPLICATES
    from .contracts import Budget, Panel, Representation, Split, assert_disjoint_panels
    from .derangement import build_derangement
    from .evaluation import evaluate_checkpoint
    from .host_bridge import (
        build_balanced_tapes, canonical_calibration_tapes, evaluation_tape_batches,
        materialize_episode_observables,
    )
    from .ledger import BASE_POPULATION_EPISODES, PrimitiveTeamStepLedger
    from .packets import construct_packet_views
    from .run import result_skeleton, validate_result
    from .training import fit_fresh_predictor, train_matched_paths

    return SimpleNamespace(**locals())


def _collect_batch(
    tapes: Sequence[object], *, replicate: int, split: object, forecast: object | None,
    collect_common_history: bool, ledger: object, components: SimpleNamespace,
) -> tuple[tuple[object, ...], tuple[object, ...]]:
    examples: list[object] = []
    rows: list[object] = []
    for tape in tapes:
        ledger.check_limits()
        observable = components.materialize_episode_observables(
            tape, replicate=replicate, split=split, forecast=forecast,
            collect_common_history=collect_common_history,
            ledger=ledger if collect_common_history else None,
        )
        examples.extend(observable.predictor_examples)
        if observable.common_history_row is not None:
            rows.append(observable.common_history_row)
        ledger.check_limits()
    examples.sort(key=lambda row: row.canonical_key)
    rows.sort(key=lambda row: row.key.canonical)
    return tuple(examples), tuple(rows)


def _retain_supported_rows(
    rows: tuple[object, ...], *, split: object, components: SimpleNamespace,
) -> tuple[tuple[object, ...], tuple[str, ...]]:
    failures: list[str] = []
    if not rows:
        return (), (f"{split.value} retained no common-history rows",)
    counts = Counter(row.derangement_cell for row in rows)
    supported = {cell for cell, count in counts.items() if count >= 8}
    retained = tuple(row for row in rows if row.derangement_cell in supported)
    if len(retained) < math.ceil(0.80 * len(rows)):
        failures.append(
            f"{split.value} supported-cell rows {len(retained)}/{len(rows)} (<80%)"
        )
    if split is components.Split.EVALUATION:
        by_regime = Counter(row.key.regime for row in retained)
        for regime in ("K8", "K16", "K4_TO_16", "K16_TO_4"):
            if by_regime[regime] < 48:
                failures.append(f"EVALUATION/{regime} retained {by_regime[regime]}/64 (<48)")
        target_rows = tuple(
            row for row in retained if row.key.regime in ("K16", "K4_TO_16", "K16_TO_4")
        )
        for regime in ("K16", "K4_TO_16", "K16_TO_4"):
            if not any(
                abs(float(row.g16[0]) - float(row.g16[row.legal_mask].max())) <= 1e-12
                for row in target_rows if row.key.regime == regime
            ):
                failures.append(f"EVALUATION/{regime} lacks positive KEEP-optimal support")
        headroom = 0
        for row in target_rows:
            replacements = row.g16[1:][row.legal_mask[1:]]
            if replacements.size == 0:
                failures.append(f"EVALUATION/{row.key.regime} row lacks a legal replacement")
            else:
                headroom += float(replacements.max() - row.g16[0]) >= 0.02
        if not target_rows or headroom < math.ceil(0.20 * len(target_rows)):
            failures.append(
                f"EVALUATION target replacement-headroom rows {headroom}/{len(target_rows)} (<20%)"
            )
    return retained, tuple(failures)


def _population_tapes(replicate: int, components: SimpleNamespace) -> tuple[
    tuple[object, ...], tuple[object, ...], tuple[object, ...], Mapping[str, tuple[object, ...]]
]:
    predictor = (
        *components.build_balanced_tapes(
            replicate=replicate, split=components.Split.PREDICTOR_FIT, regime="K4",
            count=128, first_episode_index=0,
        ),
        *components.build_balanced_tapes(
            replicate=replicate, split=components.Split.PREDICTOR_FIT, regime="K8",
            count=128, first_episode_index=128,
        ),
    )
    calibration = (
        *components.canonical_calibration_tapes(replicate=replicate, regime="K4"),
        *components.canonical_calibration_tapes(replicate=replicate, regime="K8"),
    )
    training = components.build_balanced_tapes(
        replicate=replicate, split=components.Split.TRAIN, regime="K8",
        count=512, first_episode_index=320,
    )
    evaluation = components.evaluation_tape_batches(
        replicate=replicate, split=components.Split.EVALUATION,
        count_per_regime=64, first_episode_index=832,
    )
    return tuple(predictor), tuple(calibration), tuple(training), evaluation


def _collect_slot(replicate: int, *, ledger: object, components: SimpleNamespace) -> _SlotState:
    predictor_tapes, calibration_tapes, training_tapes, evaluation_batches = _population_tapes(
        replicate, components
    )
    predictor_examples, _ = _collect_batch(
        predictor_tapes, replicate=replicate, split=components.Split.PREDICTOR_FIT,
        forecast=None, collect_common_history=False, ledger=ledger, components=components,
    )
    ledger.record_physically_executed_base_steps("PREDICTOR_FIT", len(predictor_tapes) * 256)
    predictor, predictor_audit = components.fit_fresh_predictor(
        predictor_examples, replicate=replicate, resource_monitor=ledger.check_limits,
    )
    forecast = predictor.packet_forecast
    calibration_examples, _ = _collect_batch(
        calibration_tapes, replicate=replicate, split=components.Split.CALIBRATION,
        forecast=forecast, collect_common_history=False, ledger=ledger, components=components,
    )
    ledger.record_physically_executed_base_steps("CALIBRATION", len(calibration_tapes) * 256)
    calibration_table, fit_audit = components.fit_calibration_from_examples(
        calibration_examples, forecast,
    )
    _, training_rows = _collect_batch(
        training_tapes, replicate=replicate, split=components.Split.TRAIN,
        forecast=forecast, collect_common_history=True, ledger=ledger, components=components,
    )
    ledger.record_physically_executed_base_steps("TRAIN", len(training_tapes) * 256)
    evaluation_examples: dict[str, tuple[object, ...]] = {}
    evaluation_rows: list[object] = []
    for regime in ("K8", "K16", "K4_TO_16", "K16_TO_4"):
        examples, rows = _collect_batch(
            evaluation_batches[regime], replicate=replicate, split=components.Split.EVALUATION,
            forecast=forecast, collect_common_history=True, ledger=ledger, components=components,
        )
        evaluation_examples[regime] = examples
        evaluation_rows.extend(rows)
    ledger.record_physically_executed_base_steps(
        "EVALUATION", sum(len(batch) for batch in evaluation_batches.values()) * 256,
    )
    evaluation_rows.sort(key=lambda row: row.key.canonical)
    retained_training, training_failures = _retain_supported_rows(
        training_rows, split=components.Split.TRAIN, components=components,
    )
    retained_evaluation, evaluation_failures = _retain_supported_rows(
        tuple(evaluation_rows), split=components.Split.EVALUATION, components=components,
    )
    components.assert_disjoint_panels({
        components.Split.TRAIN: components.Panel(components.Split.TRAIN, retained_training),
        components.Split.EVALUATION: components.Panel(components.Split.EVALUATION, retained_evaluation),
    })
    diagnostics = components.slot_calibration_diagnostics(
        calibration_table,
        {regime: evaluation_examples[regime] for regime in ("K16", "K4_TO_16", "K16_TO_4")},
        forecast,
        replicate=replicate,
    )
    return _SlotState(
        replicate, predictor_audit, calibration_table,
        {"fit": fit_audit, "diagnostics": diagnostics},
        retained_training, retained_evaluation,
        tuple(
            f"slot {replicate} {failure}"
            for failure in (*training_failures, *evaluation_failures)
        ),
    )


def _prepare_matched_paths(state: _SlotState, components: SimpleNamespace, ledger: object) -> None:
    train_views = components.construct_packet_views(state.training_rows, state.calibration_table)
    eval_views = components.construct_packet_views(state.evaluation_rows, state.calibration_table)
    train_deranged, train_plan = components.build_derangement(
        state.training_rows, train_views.true_residual_dataset, replicate=state.replicate,
    )
    eval_deranged, eval_plan = components.build_derangement(
        state.evaluation_rows, eval_views.true_residual_dataset, replicate=state.replicate,
    )
    state.evaluation_packets = {
        components.Representation.RAW: eval_views.raw_dataset,
        components.Representation.TRUE_RESIDUAL: eval_views.true_residual_dataset,
        components.Representation.CALIBRATED_DERANGEMENT: eval_deranged,
    }
    state.derangement_plans = {"TRAIN": train_plan, "EVALUATION": eval_plan}
    state.paths = components.train_matched_paths(
        state.training_rows,
        {
            components.Representation.RAW: train_views.raw_dataset,
            components.Representation.TRUE_RESIDUAL: train_views.true_residual_dataset,
            components.Representation.CALIBRATED_DERANGEMENT: train_deranged,
        },
        replicate=state.replicate, resource_monitor=ledger.check_limits,
    )


def _serialize_derangements(state: _SlotState) -> dict[str, object]:
    """Cross the persistence boundary only after staged competence has passed."""
    if state.derangement_plans is None or set(state.derangement_plans) != {
        "TRAIN", "EVALUATION",
    }:
        raise RuntimeError("complete in-memory TRAIN/EVALUATION derangement plans are required")
    return {
        name: state.derangement_plans[name].to_json()
        for name in ("TRAIN", "EVALUATION")
    }


def _evaluate_raw_long(
    states: Sequence[_SlotState], components: SimpleNamespace,
) -> tuple[list[object], Mapping[str, object]]:
    summaries: list[object] = []
    for state in states:
        assert state.paths is not None and state.evaluation_packets is not None
        rows = tuple(row for row in state.evaluation_rows if row.key.regime == "K8")
        raw = state.evaluation_packets[components.Representation.RAW]
        indices = [i for i, row in enumerate(state.evaluation_rows) if row.key.regime == "K8"]
        packets = type(raw)(tuple(row.key.text for row in rows), raw.values[indices])
        summaries.append(components.evaluate_checkpoint(
            state.paths[components.Representation.RAW].checkpoints[components.Budget.LONG],
            rows, packets, representation=components.Representation.RAW,
            budget=components.Budget.LONG, target_regimes=("K8",),
        ))
    return summaries, components.assess_raw_long_competence(summaries)


def _evaluate_after_competence(
    states: Sequence[_SlotState], components: SimpleNamespace,
) -> list[dict[tuple[object, object], object]]:
    complete: list[dict[tuple[object, object], object]] = []
    for state in states:
        assert state.paths is not None and state.evaluation_packets is not None
        cells: dict[tuple[object, object], object] = {}
        for representation in components.Representation:
            for budget in components.Budget:
                cells[(representation, budget)] = components.evaluate_checkpoint(
                    state.paths[representation].checkpoints[budget], state.evaluation_rows,
                    state.evaluation_packets[representation], representation=representation,
                    budget=budget,
                )
        complete.append(cells)
    return complete


def _route_staged_evaluation(
    states: Sequence[_SlotState], components: SimpleNamespace,
) -> tuple[list[Mapping[tuple[object, object], object]], Mapping[str, object], Mapping[str, object]]:
    """Inspect only eight RAW-LONG/K8 cells until the competence gate passes."""
    raw_long, competence = _evaluate_raw_long(states, components)
    if competence.get("status") != "PASS":
        summaries = [
            {(components.Representation.RAW, components.Budget.LONG): item}
            for item in raw_long
        ]
    else:
        summaries = _evaluate_after_competence(states, components)
    return summaries, competence, components.analyze(summaries)


def _jsonable(value: object) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(_jsonable(key)): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, bytes):
        return {"encoding": "base64", "data": base64.b64encode(value).decode("ascii")}
    if hasattr(value, "item") and callable(value.item):
        return value.item()
    return value


def _summary_record(summary: object) -> dict[str, object]:
    value = asdict(summary) if is_dataclass(summary) else dict(summary)  # type: ignore[arg-type]
    return _jsonable(value)


def _ledger_records(ledger: object, expected: int) -> tuple[dict[str, object], dict[str, object]]:
    snapshot = ledger.snapshot()
    record = {
        "formula": "8*1088*256 + 16*actual_common_future_branch_count",
        "charged_full_tape_primitive_team_steps": 2_228_224,
        "common_future_steps_per_actual_branch": 16,
        "expected_common_future_branch_count": expected,
        "actual_common_future_branch_count": snapshot.common_future_branches,
        "actual_common_future_steps": snapshot.common_future_steps,
        "pre_result_exact": True,
        "within_ceiling": snapshot.actual_total_steps <= snapshot.ceiling,
        "actual_total_steps": snapshot.actual_total_steps,
        "ceiling": snapshot.ceiling,
        "charged_base_steps_by_population": dict(snapshot.charged_base_steps_by_population),
        "physically_executed_base_steps_by_population": dict(snapshot.physically_executed_base_steps_by_population),
    }
    # The self-describing result cannot contain an exact observation taken after its
    # own final encoding.  Publish the registered conservative envelope here and a
    # separate terminal observation after final result fsync, before either target is exposed.
    runtime = {
        "workers": snapshot.workers,
        "threads_per_worker": snapshot.threads_per_worker,
        "peak_rss_bytes": 2 * 1024**3,
        "wall_seconds": 7_200.0,
        "reported_as_conservative_envelope": True,
        "prepublication_observed_peak_rss_bytes": snapshot.peak_rss_bytes,
        "prepublication_observed_wall_seconds": snapshot.wall_seconds,
        "terminal_observation": "terminal-runtime.json",
        "terminal_observation_boundary": "AFTER_FINAL_RESULT_ENCODE_AND_FSYNC_BEFORE_PUBLICATION",
    }
    return record, runtime


def _resource_record(
    launch_resource: Mapping[str, object], launch_run: Mapping[str, object],
) -> dict[str, object]:
    return {
        **dict(launch_resource),
        "memory_floor_pass": (
            launch_resource.get("passed") is True
            and launch_run.get("memory_floor_pass") is True
            and launch_run.get("memory_safe") is True
        ),
        "available_physical_bytes": int(launch_resource["available_physical_bytes"]),
        "effective_available_bytes": int(launch_resource["effective_available_bytes"]),
        "assess_run": dict(launch_run),
    }


def _run_scientific_transaction(
    stage_root: Path, *, preflight: Mapping[str, object], launch_resource: Mapping[str, object],
    launch_run_resource: Mapping[str, object], expected_branches: int,
    components: SimpleNamespace,
) -> dict[str, object]:
    ledger = components.PrimitiveTeamStepLedger(
        expected_common_future_branches=expected_branches, workers=1, threads_per_worker=1,
    )
    for name, count in components.BASE_POPULATION_EPISODES.items():
        ledger.charge_base_population(name, count)
    states = [_collect_slot(r, ledger=ledger, components=components) for r in components.REPLICATES]
    calibration = components.assess_calibration([
        state.calibration_report["diagnostics"] for state in states
    ])
    support_failures = tuple(
        failure for state in states for failure in state.support_failures
    )
    competence: Mapping[str, object] | None = None
    summaries: list[Mapping[tuple[object, object], object]] | None = None
    if support_failures:
        failures = support_failures + tuple(
            str(issue) for issue in calibration.get("issues", [])
        )
        analysis = components.analyze([], structural_failures=failures)
    elif calibration.get("passed") is not True:
        failures = tuple(str(issue) for issue in calibration.get("issues", [])) or (
            "NONIDENTIFYING_CALIBRATION_ADMISSION_FAILED",
        )
        analysis = components.analyze([], structural_failures=failures)
    else:
        for state in states:
            _prepare_matched_paths(state, components, ledger)
        summaries, competence, analysis = _route_staged_evaluation(states, components)
    ledger.assert_complete()
    ledger_record, runtime = _ledger_records(ledger, expected_branches)
    paths_completed = not support_failures and calibration.get("passed") is True
    k8_support = (
        not support_failures
        and competence is not None
        and competence.get("status") != "NONIDENTIFYING"
    )
    admission = {
        "disjoint_panels": True,
        "matched_inputs": paths_completed,
        "derangement_valid": paths_completed,
        "common_future_valid": ledger_record["actual_common_future_branch_count"] == expected_branches,
        "raw_long_competent": competence is not None and competence.get("status") == "PASS",
        "resource_valid": True, "ledger_valid": True, "runtime_valid": True,
        "calibration_valid": calibration.get("passed") is True,
        "k8_competence_support_valid": k8_support,
    }
    if analysis.get("status") == "IDENTIFYING" and not all(admission.values()):
        raise RuntimeError("IDENTIFYING analysis cannot follow failed admission")
    replicate_records: list[dict[str, object]] = []
    for index, state in enumerate(states):
        record: dict[str, object] = {
            "replicate": state.replicate,
            "predictor_fit": {
                "examples": int(state.predictor_audit.examples),
                "updates": int(state.predictor_audit.updates),
                "processed_examples": int(state.predictor_audit.processed_examples),
            },
            "calibration": _jsonable(state.calibration_report),
            "retained_rows": {"TRAIN": len(state.training_rows), "EVALUATION": len(state.evaluation_rows)},
            "support_failures": list(state.support_failures),
        }
        if summaries is not None and (
            analysis.get("status") == "IDENTIFYING"
            or analysis.get("interpretation") in {
                "STOP_RAW_LONG_INCOMPETENT", "NONIDENTIFYING_K8_COMPETENCE_SUPPORT",
            }
        ):
            # A STOP/support route contains only RAW-LONG/K8.  A complete six-cell
            # record is serialized only for an identifying fixed-census analysis.
            record["evaluations"] = [_summary_record(item) for item in summaries[index].values()]
        if competence is not None and competence.get("status") == "PASS" and analysis.get(
            "status"
        ) == "IDENTIFYING":
            record["derangements"] = _jsonable(_serialize_derangements(state))
        replicate_records.append(record)
    payload = components.result_skeleton(
        analysis=analysis, replicates=replicate_records,
        resource=_resource_record(launch_resource, launch_run_resource),
        ledger=ledger_record, runtime=runtime, admission=admission,
    )
    payload["provenance"].update({
        "first_preflight_format": preflight["format"],
        "production_capability": dict(preflight["production_capability"]),
        "launch_resource_receipt": dict(launch_resource),
        "launch_run_resource_receipt": dict(launch_run_resource),
    })
    components.validate_result(payload)
    return _TransactionPayload(payload, ledger)


def _publish_create_only(output_root: Path, result_path: Path, *, transaction: object) -> dict[str, object]:
    output, result = Path(output_root).resolve(), Path(result_path).resolve()
    if os.name != "nt":
        raise RuntimeError("registered create-only publication is Windows-only")
    if output.exists() or result.exists():
        raise FileExistsError("output root and result path must both be fresh")
    if output == result or output in result.parents:
        raise ValueError("result path must be outside the atomic output root")
    output.parent.mkdir(parents=True, exist_ok=True)
    result.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=output.name + ".stage.", dir=output.parent))
    descriptor, name = tempfile.mkstemp(prefix=result.name + ".", suffix=".tmp", dir=result.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        payload = transaction(stage)  # type: ignore[operator]
        encoded = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
        stage_result = stage / "production-result.json"
        with stage_result.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        if isinstance(payload, _TransactionPayload):
            terminal = payload.terminal_runtime_snapshot()
            terminal_record = {
                "format": "CRTO_TERMINAL_RUNTIME_V1",
                "boundary": "AFTER_FINAL_RESULT_ENCODE_AND_FSYNC_BEFORE_PUBLICATION",
                "workers": terminal.workers,
                "threads_per_worker": terminal.threads_per_worker,
                "observed_peak_rss_bytes": terminal.peak_rss_bytes,
                "observed_wall_seconds": terminal.wall_seconds,
                "peak_rss_ceiling_bytes": 2 * 1024**3,
                "wall_ceiling_seconds": 7_200,
                "passed": True,
            }
            terminal_path = stage / "terminal-runtime.json"
            with terminal_path.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(terminal_record, stream, indent=2, sort_keys=True, allow_nan=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            # Receipt writing is not part of the scientific result encoding boundary,
            # but it also may not push the process outside the registered envelope.
            payload.require_terminal_limits()
        if output.exists() or result.exists():
            raise FileExistsError("fresh publication target appeared during execution")
        os.rename(stage, output)
        try:
            os.rename(temporary, result)
        except BaseException:
            os.rename(output, stage)
            raise
        return payload
    finally:
        if stage.exists():
            if stage.parent.resolve() != output.parent.resolve() or not stage.name.startswith(output.name + ".stage."):
                raise RuntimeError("refusing to clean an unexpected staging path")
            shutil.rmtree(stage)
        if temporary.exists():
            temporary.unlink()


def _execute_admitted_pipeline(
    *, output_root: Path, result_path: Path, preflight: Mapping[str, object],
    launch_resource_receipt_path: Path, launch_run_resource_receipt_path: Path,
    expected_branches: int,
) -> Mapping[str, object]:
    """Private conformance seam reached only by a future accepted revision."""
    output, result = Path(output_root).resolve(), Path(result_path).resolve()
    memory = Path(launch_resource_receipt_path).resolve()
    assessment = Path(launch_run_resource_receipt_path).resolve()
    if len({output, result, memory, assessment}) != 4:
        raise ValueError("scientific targets and second launch receipts must be distinct")
    if any(path.exists() for path in (output, result, memory, assessment)):
        raise FileExistsError("production and second-admission targets must all be fresh")
    if output in memory.parents or output in assessment.parents:
        raise ValueError("second launch receipts must remain outside scientific output root")
    from .preflight import create_shared_resource_receipt, create_shared_run_assessment

    launch_resource = create_shared_resource_receipt(memory)
    launch_run = create_shared_run_assessment(
        assessment, run_id="crto_common_history_gate_r01_launch",
    )
    _configure_one_thread_environment()
    components = _load_components()
    return _publish_create_only(
        output, result,
        transaction=lambda stage: _run_scientific_transaction(
            stage, preflight=preflight, launch_resource=launch_resource,
            launch_run_resource=launch_run, expected_branches=expected_branches,
            components=components,
        ),
    )


def execute_fresh_pipeline(
    *, output_root: Path, result_path: Path, preflight: Mapping[str, object],
    launch_resource_receipt_path: Path, launch_run_resource_receipt_path: Path,
) -> Mapping[str, object]:
    """Withhold current long production before second admission or scientific roots."""
    if os.environ.get(PRODUCTION_WORKER_ENV) != PRODUCTION_WORKER_SENTINEL:
        raise PermissionError("CRTO production is callable only inside its isolated worker")
    _require_first_preflight(preflight)
    raise AssertionError("current frozen production preflight must always withhold")


__all__ = [
    "PRODUCTION_CAPABILITY_VERSION", "PRODUCTION_WORKER_ENV", "PRODUCTION_WORKER_SENTINEL",
    "execute_fresh_pipeline", "production_capability",
]
