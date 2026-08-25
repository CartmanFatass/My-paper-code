from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Lifecycle:
    phase: str = "preactivity"
    scientific_activity_started: bool = False
    question_relevant_output_exists: bool = False
    events: list[dict[str, object]] = field(default_factory=list)
    persist: Callable[[dict[str, object]], None] | None = field(default=None, repr=False)

    @classmethod
    def from_facts(cls, facts: dict[str, object],
                   persist: Callable[[dict[str, object]], None] | None = None) -> "Lifecycle":
        return cls(phase=str(facts["phase"]),
                   scientific_activity_started=bool(facts["scientific_activity_started"]),
                   question_relevant_output_exists=bool(facts["question_relevant_output_exists"]),
                   events=list(facts["events"]), persist=persist)

    def record(self, event: str, **facts: object) -> None:
        self.events.append({"event": event, "utc": datetime.now(timezone.utc).isoformat(), **facts})
        if self.persist is not None:
            self.persist(self.facts())

    def begin_seed_200_calibration(self) -> None:
        if self.scientific_activity_started:
            raise RuntimeError("B3 activity boundary may be crossed only once")
        self.scientific_activity_started = True
        self.phase = "calibration"
        self.record("scientific_activity_started",
                    criterion="immediately before first seed-200 calibration endpoint-gradient")

    def begin_training(self) -> None:
        self.phase = "training"
        self.record("complete_24_cell_calibration_before_training")

    def begin_evaluation(self) -> None:
        self.phase = "evaluation"
        self.record("all_24_arm_seed_training_cells_complete")

    def complete(self) -> None:
        self.phase = "complete"
        self.question_relevant_output_exists = True
        self.record("complete_atomic_packet")

    def complete_invalid_calibration(self, invalid_cells: int) -> None:
        self.phase = "complete_invalid_calibration_discriminator"
        self.question_relevant_output_exists = True
        self.record("complete_invalid_calibration_discriminator", invalid_cells=invalid_cells,
                    training_invoked=False, evaluation_invoked=False)

    def facts(self) -> dict[str, object]:
        return {"phase": self.phase,
                "scientific_activity_started": self.scientific_activity_started,
                "question_relevant_output_exists": self.question_relevant_output_exists,
                "events": list(self.events)}
