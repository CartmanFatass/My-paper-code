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
        self.events.append({"event": event, "utc": datetime.now(timezone.utc).isoformat(), **facts})

    def begin_panel(self) -> None:
        if self.scientific_activity_started:
            raise RuntimeError("r07 Stage-A activity boundary may be crossed only once")
        self.scientific_activity_started = True
        self.phase = "identity_and_materialization"
        self.record(
            "scientific_activity_started",
            criterion="immediately before first master-M candidate",
        )

    def begin_training(self) -> None:
        self.phase = "checkpoint_training"
        self.record("complete_manifest_and_scalers_before_checkpoint_training")

    def begin_assay(self) -> None:
        self.phase = "target_support_and_assay"
        self.record("checkpoint_theta_600_complete")

    def complete(self) -> None:
        self.phase = "complete"
        self.question_relevant_output_exists = True
        self.record("complete_atomic_stage_a_packet")

    def facts(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "scientific_activity_started": self.scientific_activity_started,
            "question_relevant_output_exists": self.question_relevant_output_exists,
            "events": list(self.events),
        }

    @classmethod
    def from_facts(cls, value: dict[str, object]) -> "Lifecycle":
        return cls(str(value["phase"]), bool(value["scientific_activity_started"]),
                   bool(value["question_relevant_output_exists"]), list(value["events"]))
