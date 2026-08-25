"""Complete 24-by-6,990 block reducer and joint-inference flow for r06."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import inspect
from typing import Final, Mapping, Sequence

import numpy as np

from .production_contract import BLOCKS, BOOTSTRAP_RESAMPLES
from .production_inference import (
    HARD_EVENTS,
    InferenceError,
    complete_estimand_manifest,
    fractional_cvar_10,
    run_production_inference,
)


SOURCE_BY_FAMILY: Final = {
    "COMPETENCE_NO_DEGRADATION": "full_episode_mask_off_rows",
    "COMPETENCE_PRE_ONSET": "pre_onset_mask_on_rows",
    "OPPORTUNITY": "opportunity_witness_rows",
    "ADAPTIVE_SUPPORT": "trigger_support_rows",
    "NEVER_HEADROOM": "never_and_witness_event_rows",
    "ENDPOINT_EFFECT": "full_or_fork_endpoint_rows",
    "ENERGY_RATIO": "full_or_fork_energy_rows",
    "HARD_EVENT_RATE": "full_or_fork_hard_event_rows",
    "PHASE_ENDPOINT_DIFFERENCE": "unconditioned_phase_endpoint_rows",
    "PHASE_ENERGY_DIFFERENCE": "unconditioned_phase_energy_rows",
}


class ReducerFlowError(RuntimeError):
    pass


def _fractional_cvar_10_any(values: np.ndarray) -> float:
    rows = np.sort(np.asarray(values, dtype=np.float64))
    if rows.ndim != 1 or rows.size == 0 or not np.isfinite(rows).all():
        raise ReducerFlowError("fork CVaR input differs")
    mass = 0.1 * rows.size; whole = int(np.floor(mass))
    total = float(rows[:whole].sum())
    if whole < rows.size:
        total += (mass - whole) * float(rows[whole])
    return total / mass


def complete_estimand_source_map() -> tuple[tuple[str, str], ...]:
    rows = complete_estimand_manifest()
    assignments = tuple((identity, SOURCE_BY_FAMILY[identity.split("/", 1)[0]]) for identity in rows)
    if len(assignments) != 6_990 or len({identity for identity, _ in assignments}) != 6_990:
        raise ReducerFlowError("complete estimand source map differs")
    return assignments


@dataclass(frozen=True)
class FullCellRows:
    service: np.ndarray
    onset_ticks: np.ndarray
    total_energy: np.ndarray
    hard_event_presence: np.ndarray

    def reduce(self) -> Mapping[str, object]:
        service = np.asarray(self.service, dtype=np.int8)
        onset = np.asarray(self.onset_ticks, dtype=np.int64)
        energy = np.asarray(self.total_energy, dtype=np.float64)
        hard = np.asarray(self.hard_event_presence, dtype=np.int8)
        if service.shape != (16, 1_200) or onset.shape != (16,) or energy.shape != (16,) or hard.shape != (16, 7):
            raise ReducerFlowError("full speed-cell input shape differs")
        if not np.isin(service, (0, 1)).all() or not np.isfinite(energy).all() or not np.isin(hard, (0, 1)).all():
            raise ReducerFlowError("full speed-cell input is malformed")
        windows = np.stack([service[index, tick:tick + 200] for index, tick in enumerate(onset)])
        if windows.shape != (16, 200):
            raise ReducerFlowError("full speed-cell event window differs")
        fractions = windows.mean(axis=1)
        deficits = 0.1 * (200 - windows.sum(axis=1))
        delays = []
        for row in windows:
            first = np.flatnonzero(row == 0)
            delay = 0.0 if first.size == 0 else 20.0
            if first.size:
                for tick in range(int(first[0]), 191):
                    if bool(np.all(row[tick:tick + 10] == 1)):
                        delay = 0.1 * (tick - int(first[0])); break
            delays.append(delay)
        return {
            "MEAN": float(fractions.mean()), "TAIL": fractional_cvar_10(fractions),
            "DEFICIT": float(deficits.mean()), "DELAY": float(np.mean(delays)),
            "ENERGY": float(energy.mean()),
            "HARD_EVENTS": dict(zip(HARD_EVENTS, hard.mean(axis=0).tolist())),
            "row_count": 16,
        }


@dataclass(frozen=True)
class ForkCellRows:
    service: np.ndarray
    total_energy: np.ndarray
    hard_event_presence: np.ndarray
    supported: bool

    def reduce(self) -> Mapping[str, object]:
        service = np.asarray(self.service, dtype=np.int8)
        energy = np.asarray(self.total_energy, dtype=np.float64)
        hard = np.asarray(self.hard_event_presence, dtype=np.int8)
        if not self.supported:
            if service.size or energy.size or hard.size:
                raise ReducerFlowError("unsupported fork cell must carry no trigger rows")
            return {
                "MEAN": 0.0, "TAIL": 0.0, "DEFICIT": 0.0, "DELAY": 0.0,
                "ENERGY": 0.0, "HARD_EVENTS": {name: 0.0 for name in HARD_EVENTS},
                "row_count": 0, "fork_supported": False,
            }
        if service.ndim != 2 or service.shape[0] == 0 or service.shape[1] != 100:
            raise ReducerFlowError("supported fork rows differ")
        if energy.shape != (service.shape[0],) or hard.shape != (service.shape[0], 100, 7):
            raise ReducerFlowError("fork energy or hard-event rows differ")
        fractions = service.mean(axis=1); deficits = 0.1 * (100 - service.sum(axis=1))
        delays = []
        for row in service:
            first = np.flatnonzero(row == 0); delay = 0.0 if first.size == 0 else 10.0
            if first.size:
                for tick in range(int(first[0]), 91):
                    if bool(np.all(row[tick:tick + 10] == 1)):
                        delay = 0.1 * (tick - int(first[0])); break
            delays.append(delay)
        hard_presence = np.any(hard != 0, axis=1).astype(np.int8)
        return {
            "MEAN": float(fractions.mean()), "TAIL": _fractional_cvar_10_any(fractions),
            "DEFICIT": float(deficits.mean()), "DELAY": float(np.mean(delays)),
            "ENERGY": float(energy.mean()),
            "HARD_EVENTS": dict(zip(HARD_EVENTS, hard_presence.mean(axis=0).tolist())),
            "row_count": int(service.shape[0]), "fork_supported": True,
        }


class CompleteBlockEstimandReducer:
    """Fail closed until every block value for every frozen estimand exists."""

    def __init__(self) -> None:
        self.identities = complete_estimand_manifest()
        self.index = {identity: ordinal for ordinal, identity in enumerate(self.identities)}
        self.values = np.full((BLOCKS, len(self.identities)), np.nan, dtype=np.float64)
        self.written = np.zeros(self.values.shape, dtype=bool)

    def put(self, *, block: int, identity: str, value: float) -> None:
        if not 0 <= block < BLOCKS or identity not in self.index or not np.isfinite(value):
            raise ReducerFlowError("block-estimand row differs")
        column = self.index[identity]
        if self.written[block, column]:
            raise ReducerFlowError("duplicate block-estimand row")
        self.values[block, column] = float(value); self.written[block, column] = True

    def put_block(self, block: int, rows: Mapping[str, float]) -> None:
        if set(rows) != set(self.identities):
            raise ReducerFlowError("complete block reducer inventory differs")
        for identity in self.identities:
            self.put(block=block, identity=identity, value=float(rows[identity]))

    def complete(self) -> bool:
        return bool(np.all(self.written) and np.isfinite(self.values).all())

    def matrix(self) -> np.ndarray:
        if not self.complete() or self.values.shape != (24, 6_990):
            raise ReducerFlowError("24x6990 reducer is incomplete")
        return self.values.copy()

    def infer(self, *, master: bytes) -> Mapping[str, object]:
        """Run only the frozen joint 99,999-resample complete inference."""

        try:
            return run_production_inference(self.matrix(), master=master)
        except InferenceError as error:
            raise ReducerFlowError("complete joint inference rejected reducer matrix") from error


def flow_local_reducer_self_audit() -> dict[str, object]:
    assignments = complete_estimand_source_map()
    encoded = ("\n".join(f"{identity}\t{source}" for identity, source in assignments) + "\n").encode("ascii")
    reducer_source = inspect.getsource(CompleteBlockEstimandReducer)
    return {
        "schema": "DISH_RBHR_R06_E1_COMPLETE_REDUCER_FLOW_LOCAL_SELF_AUDIT_V1",
        "blocks": BLOCKS, "estimands": len(assignments), "matrix_shape": [24, 6_990],
        "source_families": dict(SOURCE_BY_FAMILY),
        "all_estimands_source_bound": all(source in SOURCE_BY_FAMILY.values() for _, source in assignments),
        "duplicates_fail_closed": "duplicate block-estimand row" in reducer_source,
        "incomplete_fail_closed": "24x6990 reducer is incomplete" in reducer_source,
        "joint_resamples": BOOTSTRAP_RESAMPLES,
        "source_map_sha256": hashlib.sha256(encoded).hexdigest(),
        "matrix_materialized": False, "inference_run": False, "inference_output": False,
        "partial_value": False, "question_relevant_output": False,
    }


__all__ = [
    "CompleteBlockEstimandReducer", "ForkCellRows", "FullCellRows", "ReducerFlowError",
    "complete_estimand_source_map", "flow_local_reducer_self_audit",
]
