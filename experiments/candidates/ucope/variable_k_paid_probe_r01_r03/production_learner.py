"""Registered R03 learner seam with an explicit nonregistered test boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import torch

from envs.native.production_backend import require_cpp_batched_production

from . import native_backend
from .contract import COMPONENT, REGISTERED_MASTER_SEEDS
from .model import LearnerBundle
from .training import ReductionFrontier, SupportCounters, _array_digest, _torch, reduction_frontier, support_delta


REGISTERED_NAMESPACE = "REGISTERED_UCOPE_R01_R03_COMPLETE_TRANSACTION_V1"
TECHNICAL_NAMESPACE = "TEST_ONLY_UCOPE_R01_R03_PRODUCTION_EXECUTOR_V1"
TECHNICAL_SEEDS = tuple(0xE300000000000000 + index for index in range(10))


class ProductionLearningRefusal(PermissionError):
    pass


@dataclass(frozen=True)
class LearningBoundary:
    namespace: str
    seeds: tuple[int, ...]
    registered: bool

    @classmethod
    def registered_runtime(cls) -> "LearningBoundary":
        return cls(REGISTERED_NAMESPACE, tuple(sorted(REGISTERED_MASTER_SEEDS)), True)

    @classmethod
    def technical_fixture(cls) -> "LearningBoundary":
        return cls(TECHNICAL_NAMESPACE, TECHNICAL_SEEDS, False)

    def require(self, seed: int) -> None:
        if type(seed) is not int or seed not in self.seeds:
            raise ProductionLearningRefusal("master seed is outside the immutable boundary")
        if self.registered:
            if self.namespace != REGISTERED_NAMESPACE or seed not in REGISTERED_MASTER_SEEDS:
                raise ProductionLearningRefusal("registered learning boundary differs")
        elif self.namespace != TECHNICAL_NAMESPACE or seed in REGISTERED_MASTER_SEEDS:
            raise ProductionLearningRefusal("technical fixture crossed the registered boundary")


def prepare_production_batch(
    bundles: Sequence[LearnerBundle],
    *,
    boundary: LearningBoundary,
    master_seed: int,
    panel: int,
    batch_index: int,
    build_root: Path | None = None,
) -> dict[str, object]:
    """Prepare the exact accepted 768-lane batch without the S1 TEST-only gate."""

    boundary.require(master_seed)
    if len(bundles) != 3 or panel not in (0, 1, 2) or not 0 <= batch_index < 320:
        raise ValueError("production work unit requires three arms, panel 0..2 and batch 0..319")
    require_cpp_batched_production(
        COMPONENT, backend="cpp", batch_width=768, build_root=build_root
    )
    arms = np.repeat(np.arange(3, dtype=np.int32), 256)
    population = native_backend.counter_population(
        seed=master_seed,
        panel=panel,
        batch_index=batch_index,
        width=768,
        build_root=build_root,
    )
    native = native_backend.reset_batch(
        seed=master_seed,
        panel=panel,
        batch_index=batch_index,
        arms=arms,
        build_root=build_root,
    )
    try:
        root_probabilities = np.empty((768, 6), dtype=np.float32)
        with torch.no_grad():
            for arm in range(3):
                start, stop = arm * 256, (arm + 1) * 256
                logits = bundles[arm].scorer(_torch(native.root_features[start:stop]))
                root_probabilities[start:stop] = torch.softmax(logits, dim=-1).cpu().numpy()
        root_actions = native_backend.sample_actions(
            root_probabilities,
            seed=master_seed,
            panel=panel,
            batch_index=batch_index,
            arms=arms,
            decision_code=0,
            legal_counts=np.full(768, 6, dtype=np.int32),
            build_root=build_root,
        )
        root = native.root_step(root_actions)
        tail_probabilities = np.empty((768, 5), dtype=np.float32)
        with torch.no_grad():
            for arm in range(3):
                start, stop = arm * 256, (arm + 1) * 256
                logits = bundles[arm].scorer(_torch(root["tail_features"][start:stop]))
                tail_probabilities[start:stop] = torch.softmax(logits, dim=-1).cpu().numpy()
        probe_mask_np = root_actions == 0
        tail_actions = native_backend.sample_actions(
            tail_probabilities,
            seed=master_seed,
            panel=panel,
            batch_index=batch_index,
            arms=arms,
            decision_code=1,
            legal_counts=np.where(probe_mask_np, 5, 0).astype(np.int32),
            build_root=build_root,
        )
        native.tail_step(tail_actions)
        terminal = native.terminal()
        if not np.array_equal(population["regimes"], native.regimes):
            raise RuntimeError("complete counter population roster differs from reset")
        if not np.array_equal(
            population["actual_marks"][probe_mask_np], root["actual_marks"][probe_mask_np]
        ) or not np.array_equal(
            population["displayed_marks"][probe_mask_np], root["displayed_marks"][probe_mask_np]
        ):
            raise RuntimeError("paired probe population differs")
        rows: list[dict[str, torch.Tensor]] = []
        for arm in range(3):
            start, stop = arm * 256, (arm + 1) * 256
            components = terminal["components"][start:stop]
            rows.append(
                {
                    "root_features": _torch(native.root_features[start:stop]),
                    "root_baseline": _torch(native.root_baselines[start:stop]),
                    "root_actions": torch.from_numpy(root_actions[start:stop].astype(np.int64)),
                    "root_returns": _torch(terminal["totals"][start:stop]),
                    "tail_features": _torch(root["tail_features"][start:stop]),
                    "tail_baseline": _torch(root["tail_baselines"][start:stop]),
                    "tail_actions": torch.from_numpy(
                        np.maximum(tail_actions[start:stop], 0).astype(np.int64)
                    ),
                    "tail_returns": _torch(components[:, :3].sum(axis=1, dtype=np.float32)),
                    "probe_mask": _torch(probe_mask_np[start:stop].astype(np.float32)),
                }
            )
        support = support_delta(
            panel=panel,
            root_actions=root_actions,
            tail_actions=tail_actions,
            regimes=native.regimes,
            displayed_marks=root["displayed_marks"],
        )
        reduction = reduction_frontier(((0, terminal["totals"]),))
        return {
            "data": rows,
            "support_delta": support,
            "reduction_frontier": reduction,
            "counter_frontier": _array_digest(
                population["regimes"],
                population["actual_marks"],
                population["displayed_marks"],
                population["potential_tail"],
                root_actions,
                tail_actions,
            ),
            "population_digest": _array_digest(
                population["regimes"],
                population["actual_marks"],
                population["displayed_marks"],
                population["potential_tail"],
            ),
            "action_digest": _array_digest(root_actions, tail_actions),
            "terminal_digest": _array_digest(terminal["components"], terminal["totals"]),
            "question_relevant_output": False,
        }
    finally:
        native.close()


def support_for_arm(support: SupportCounters, *, arm: int, panel: int) -> dict[str, object]:
    support.validate()
    if arm not in (0, 1, 2) or panel not in (0, 1, 2):
        raise ValueError("arm/panel outside the exact learned roster")
    balances = support.panel_roster_cells[arm, : 2 if panel == 0 else 4]
    return {
        "root_visits": support.root_actions[arm].tolist(),
        "tail_visits": support.tail_actions[arm].tolist(),
        "displayed_count_visits": support.displayed_counts[arm].tolist(),
        "balanced_totals": balances.tolist(),
    }
