from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections.abc import Callable

from .config import REVISION


@dataclass
class Lifecycle:
    phase: str = "static_support_preparation"
    scientific_activity_started: bool = False
    question_relevant_output_exists: bool = False
    events: list[dict[str, object]] = field(default_factory=list)
    persist: Callable[[dict[str, object]], None] | None = field(
        default=None, repr=False, compare=False,
    )

    def record(self, event: str, *, persist_event: bool = True, **facts: object) -> None:
        self.events.append({
            "event": event,
            "utc": datetime.now(timezone.utc).isoformat(),
            **facts,
        })
        if persist_event and self.persist is not None:
            self.persist(self.facts())

    def begin_update_zero(self, *, support_certificate: dict[str, object]) -> None:
        if not bool(support_certificate.get("conforming")):
            raise RuntimeError("cannot begin SCDMP update zero on a nonconforming locked batch")
        self.phase = "training"
        if not self.scientific_activity_started:
            self.scientific_activity_started = True
            self.record(
                "scientific_activity_started",
                criterion=(
                    "SCDMP forward for optimizer update zero invoked after exact common-batch "
                    "materialization and coverage conformance"
                ),
            )

    def seed_complete(self, algorithm_seed: int) -> None:
        self.record("algorithm_seed_complete", algorithm_seed=algorithm_seed)

    def abort(self, reason: str) -> None:
        self.phase = "aborted"
        self.record("production_aborted", reason=reason)

    def complete_result(self, *, completed_seeds: list[int]) -> None:
        if not self.scientific_activity_started:
            raise RuntimeError("cannot complete a result before scientific activity")
        if completed_seeds != list(range(8)):
            raise RuntimeError("complete result requires algorithm seeds 0..7")
        self.phase = "complete"
        self.question_relevant_output_exists = True
        # The final result is installed atomically by the CLI after packet
        # serialization.  Defer the sidecar's terminal transition until that
        # rename succeeds, so interruption cannot advertise a missing result.
        self.record("complete_question_relevant_output_installed", persist_event=False)

    def facts(self) -> dict[str, object]:
        return {
            "revision": REVISION,
            "phase": self.phase,
            "scientific_activity_started": self.scientific_activity_started,
            "question_relevant_output_exists": self.question_relevant_output_exists,
            "complete": self.question_relevant_output_exists,
            "events": list(self.events),
        }
