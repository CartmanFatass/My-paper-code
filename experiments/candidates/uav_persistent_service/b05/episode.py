"""B05 native evidence with the scheduler installed before the first prepare."""

from __future__ import annotations

from experiments.candidates.uav_persistent_service.b03.episode import (
    LongMissionEpisode, rng_state_digest,
)
from experiments.candidates.uav_persistent_service.macro_env import NativeEpisode

from .controller import ServiceShiftController
from .readout import HORIZON, continuity_readings, recovery_readings


class ServiceShiftEpisode(LongMissionEpisode):
    def __init__(self, seed: int):
        # The retained R evidence methods apply to S's unchanged transfer execution.
        self.external_arm = "R"
        NativeEpisode.__init__(self, seed, "O", horizon=HORIZON,
                               controller_factory=ServiceShiftController)
        self.rng_state_sha256_by_step = [rng_state_digest(self.env.env)]
        for key in ("station_xyz", "legal_station_capacity_w", "native_station_request",
                    "native_station_target", "native_post_nearest_station",
                    "native_eligible_station_count", "native_eligible_station_demand_w",
                    "native_station_input_wh", "native_station_stock_wh"):
            self.data[key] = []

    def row(self):
        row = super().row()
        arrays = self.arrays()
        decisions = [item["scheduler"] for item in self.controller.diagnostics]
        row.update(arm="S", **continuity_readings(arrays),
                   **recovery_readings(arrays, self.controller.events))
        row.update(
            scheduler_changed_from_r=sum(d["executed_action"] != d["r_action"] for d in decisions),
            scheduler_transfer_opportunities=sum(d["defer"]["transfer_access_now"] for d in decisions),
            scheduler_deferred_transfers=sum(d["defer"]["transfer_access_now"]
                                             and d["executed_action"] == 0 for d in decisions),
            scheduler_fallbacks=sum(d["fallback"] is not None for d in decisions),
            scheduler_snapshot_calls=int(self.controller.costs["scheduler_snapshot_calls"]),
            scheduler_member_bin_updates=int(self.controller.costs["member_bin_updates"]),
        )
        return row
