from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Lifecycle:
    phase: str = "preactivity"
    scientific_activity_started: bool = False
    question_relevant_output_exists: bool = False
    events: list[dict[str, object]] = field(default_factory=list)

    def record(self, event: str, **facts: object) -> None:
        self.events.append({
            "event": event,
            "utc": datetime.now(timezone.utc).isoformat(),
            **facts,
        })

    def begin_panel(self) -> None:
        if self.scientific_activity_started:
            raise RuntimeError("SRF r03 activity boundary may be crossed only once")
        self.scientific_activity_started = True
        self.phase = "identity_and_materialization"
        self.record(
            "scientific_activity_started",
            criterion="immediately before first fresh master candidate",
        )

    def begin_training(self, seed_index: int, cell: str) -> None:
        self.phase = "checkpoint_training"
        self.record("cell_training_entered", seed_index=seed_index, cell=cell)

    def complete_cell(self, seed_index: int, cell: str) -> None:
        self.phase = "blinded_cell_evaluation"
        self.record("blinded_cell_packet_retained", seed_index=seed_index, cell=cell)

    def complete(self) -> None:
        self.phase = "complete"
        self.question_relevant_output_exists = True
        self.record("complete_atomic_four_cell_ten_seed_packet")

    def facts(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "scientific_activity_started": self.scientific_activity_started,
            "question_relevant_output_exists": self.question_relevant_output_exists,
            "events": list(self.events),
        }

    @classmethod
    def from_facts(cls, value: dict[str, object]) -> "Lifecycle":
        return cls(
            str(value["phase"]),
            bool(value["scientific_activity_started"]),
            bool(value["question_relevant_output_exists"]),
            list(value["events"]),
        )
