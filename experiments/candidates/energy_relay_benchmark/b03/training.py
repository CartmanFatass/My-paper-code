"""B03 training: B02's loop, checkpoint rule, records and resume with the GAS learner.

``run_training`` is ``b02/training.py::run_training`` with ``b03_recipe()``: config
``make_b03_config``, agent ``build_agent`` (``GASHMASDAgent``) after the same seeding, records
carrying ``arm: "gas"`` and the programme, and a per-rollout decision flush:
raw rows to ``decisions.jsonl`` (one JSON object per team decision; gitignored bulk under
``runs/``) and the summary ``gas_decisions`` in the rollout record (``progress.jsonl`` rollout
event and ``summary.json``).  The flush draws no random number.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from ..b02 import training as b02_training
from ..b02.configuration import B02Spec
from .agent import build_agent
from .anchors import AREA_M, FREE_LABEL, N_LABELS, RELAY_LABELS, SERVICE_LABELS
from .configuration import (
    ARM, OBJECT_ID, PROGRAMME, RECIPE_NOTES, actor_input_width, config_dict, make_b03_config,
)

DECISIONS_FILE = "decisions.jsonl"
RESUME_RE_SEEDED = ("environment world streams", "label and action sampling (torch)",
                    "numpy global RNG (placeholder skill draws for new lanes, n_Z = 1, n_z = 9)")
SUMMARY_DEFINITIONS = {
    "decisions": "team decisions (rows) flushed in this rollout",
    "label_share": "share of agent-decisions by label type: relay 0-1, service 2-7, free 8",
    "duplicate_rate": "share of decisions with two or more agents on the same non-FREE label",
    "stability": ("share of agent-decisions keeping the label of the lane's previous decision "
                  "in the same episode (decisions at episode step 0 have no previous one)"),
    "previous_anchor_distance_m": ("mean distance (metres) between each agent's own xy at a "
                                   "decision and the anchor it held since the lane's previous "
                                   "decision in the same episode; non-FREE previous labels only"),
}


class DecisionFlusher:
    """Per-rollout flush of ``agent.decision_log``; the previous decision per lane carries over."""

    def __init__(self, out: Path, agent):
        self.path = Path(out) / DECISIONS_FILE
        if self.path.exists():
            raise FileExistsError(f"decision log already exists: {self.path}")
        self.agent = agent
        self.previous: dict[int, dict[str, Any]] = {}

    def __call__(self, rollout: int) -> dict[str, Any]:
        rows = self.agent.pop_decision_log()
        with self.path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps({"rollout": int(rollout), **row}, allow_nan=False) + "\n")
        summary, self.previous = decision_summary(rows, self.previous)
        return {"gas_decisions": summary}


def decision_summary(rows: list[dict[str, Any]], previous: dict[int, dict[str, Any]] | None = None
                     ) -> tuple[dict[str, Any], dict[int, dict[str, Any]]]:
    """Summary of one rollout's decision rows; returns it and the last row per lane."""
    previous = dict(previous or {})
    counts = np.zeros(N_LABELS, dtype=np.int64)
    duplicates = 0
    kept = compared = 0
    kept_by_lane: dict[int, list[int]] = {}
    distances: list[float] = []
    for row in rows:
        lane = int(row["env"])
        labels = np.asarray(row["labels"], dtype=np.int64)
        counts += np.bincount(labels, minlength=N_LABELS)
        held = labels[labels != FREE_LABEL]
        if held.size and np.unique(held).size < held.size:
            duplicates += 1
        before = previous.get(lane)
        if before is not None and row["step"] is not None and int(row["step"]) > 0:
            old = np.asarray(before["labels"], dtype=np.int64)
            same = int(np.sum(old == labels))
            kept += same
            compared += labels.size
            lane_counts = kept_by_lane.setdefault(lane, [0, 0])
            lane_counts[0] += same
            lane_counts[1] += labels.size
            anchors = np.asarray(before["anchors"], dtype=np.float64)
            own = np.asarray(row["own_xy"], dtype=np.float64)
            for agent, label in enumerate(old):
                if label != FREE_LABEL:
                    delta = own[agent] - anchors[label]
                    distances.append(float(np.hypot(delta[0], delta[1]) * AREA_M))
        previous[lane] = row
    total = int(counts.sum())

    def share(labels) -> float | None:
        return float(counts[list(labels)].sum() / total) if total else None

    summary = {
        "decisions": len(rows), "agent_decisions": total, "label_counts": counts.tolist(),
        "label_share": {"relay": share(RELAY_LABELS), "service": share(SERVICE_LABELS),
                        "free": share((FREE_LABEL,))},
        "duplicate_rate": duplicates / len(rows) if rows else None,
        "stability": {"kept_share": kept / compared if compared else None,
                      "compared_agent_decisions": compared,
                      "by_lane": {str(lane): (value[0] / value[1] if value[1] else None)
                                  for lane, value in sorted(kept_by_lane.items())}},
        "previous_anchor_distance_m": {"mean": float(np.mean(distances)) if distances else None,
                                       "count": len(distances)},
    }
    return summary, previous


def b03_recipe() -> b02_training.Recipe:
    return b02_training.Recipe(
        object_id=OBJECT_ID, programme=PROGRAMME, make_config=make_b03_config,
        config_dict=config_dict, actor_input_width=actor_input_width,
        recipe_notes=RECIPE_NOTES | {"decision_summary": SUMMARY_DEFINITIONS}, label="B03",
        construct_agent=build_agent, record_fields={"arm": ARM},
        rollout_hook=DecisionFlusher, required_steps=("high", "low_actor", "low_critic"),
        resume_re_seeded=RESUME_RE_SEEDED)


def run_training(*, out: Path, launch_sha: str, spec: B02Spec, device_name: str = "cuda",
                 threads: int = 4, argv=None, resume_from: Path | None = None,
                 resume_source_sha: str | None = None) -> dict[str, Any]:
    """One GAS fit on B02's loop (see ``b02/training.py::run_training``)."""
    return b02_training.run_training(out=out, launch_sha=launch_sha, spec=spec,
                                     device_name=device_name, threads=threads, argv=argv,
                                     resume_from=resume_from,
                                     resume_source_sha=resume_source_sha, recipe=b03_recipe())
