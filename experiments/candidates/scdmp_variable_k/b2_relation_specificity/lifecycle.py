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

    def record(self, event: str, **facts: object) -> None:
        self.events.append({"event": event, "utc": datetime.now(timezone.utc).isoformat(), **facts})
        if self.persist is not None:
            self.persist(self.facts())

    def begin_b100(self) -> None:
        if self.scientific_activity_started:
            raise RuntimeError("B2 activity boundary may be crossed only once")
        self.scientific_activity_started = True
        self.phase = "training"
        self.record("scientific_activity_started", criterion="immediately before first torch.autograd.grad(L0) for B_100")

    def complete(self) -> None:
        self.phase = "complete"
        self.question_relevant_output_exists = True
        self.record("complete")

    def abort(self, reason: str) -> None:
        self.phase = "aborted"
        self.record("aborted", reason=reason)

    def facts(self) -> dict[str, object]:
        return {"phase": self.phase, "scientific_activity_started": self.scientific_activity_started,
                "question_relevant_output_exists": self.question_relevant_output_exists,
                "events": list(self.events)}
