"""Original native capture with a complete typed E/B planning record."""
import numpy as np
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.capture import (
    Recorder as OriginalRecorder, CaptureEnv, TimedController, plan_record as original_plan_record,
)


def plan_record(controller, step):
    record = original_plan_record(controller, step)
    detail = controller.last_decision
    fields = ("m", "base_index", "selected_alias", "eligible_uavs", "target_columns",
              "base_columns", "selected_columns", "legal_xyz",
              "legal_battery", "legal_stations", "edge_first", "edge_count",
              "return_first", "return_count")
    for name in fields:
        record["plan_" + name] = np.asarray(detail[name]).copy()
    # Edge/return values live once in their complete typed attempt tables.
    # Controller-local matrices remain available for selection and finite checks.
    return record


class Recorder(OriginalRecorder):
    def on_step(self, *, t, proposal_t, submitted_t, controller, **unused):
        if t != self.decision_steps or self.native_steps != t + 1:
            raise AssertionError("native/decision chronology differs")
        self.proposed[t] = proposal_t
        if not np.array_equal(self.submitted[t], submitted_t):
            raise AssertionError("captured command differs from actual submission")
        if controller.heuristic.calls != t + 1:
            raise AssertionError("single C clock differs")
        xyz = np.column_stack((controller.heuristic.targets_xy, np.full(8, 100.0)))
        self._store(self.decisions, "decision_targets_xyz", t, self.limit, xyz)
        if t % 30 == 0:
            for name, value in plan_record(controller, t).items():
                self._store(self.plans, name, self.plan_count, (self.limit + 29) // 30, value)
            self.plan_count += 1
        self.decision_steps += 1
