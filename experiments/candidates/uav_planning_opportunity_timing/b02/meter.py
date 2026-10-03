"""B02 cumulative billing, owned allocation scope and explicit reserve overshoot."""
import json
import math
from pathlib import Path

from experiments.candidates.uav_planning_opportunity_timing.b01 import meter as inherited

OperationLimit = inherited.OperationLimit
resources = inherited.resources
allocated_bytes = inherited.allocated_bytes


class Meter(inherited.Meter):
    def __init__(self, *, start_wall, source, out, preparation_cpu, limits):
        self.runner_start_wall = start_wall
        self.bound_preparation_cpu = float(preparation_cpu)
        self.external_cpu = 0.
        self.launch_meter_path = Path(out) / "formal-launch-resources.json"
        self.launch_meter = None
        super().__init__(start_wall=start_wall, source=source, out=out,
                         preparation_cpu=preparation_cpu, limits=limits)
        author = Path(out).parents[2]
        direction = "uav_planning_opportunity_timing"
        self.roots += (author / "experiments/candidates" / direction / "b02",
                       author / "tests/experiments/candidates" / direction / "b02",
                       author / "temp/directions" / direction)
        self.check(force_disk=True)

    def _refresh_external(self):
        if not self.launch_meter_path.exists():
            return
        record = json.loads(self.launch_meter_path.read_text())
        value = record["cpu_seconds"]
        if not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
            raise ValueError("invalid formal launcher CPU reading")
        if value < self.external_cpu:
            raise ValueError("formal launcher CPU reading regressed")
        launched = record.get("started_monotonic")
        if launched is not None:
            if (not isinstance(launched, (int, float)) or not math.isfinite(launched)
                    or launched < 0 or launched > self.runner_start_wall):
                raise ValueError("invalid same-host formal-request start clock")
            self.start_wall = float(launched)
        self.launch_meter, self.external_cpu = record, float(value)
        self.preparation_cpu = self.bound_preparation_cpu + self.external_cpu

    def check(self, *, force_disk=False):
        self._refresh_external()
        return super().check(force_disk=force_disk)

    def record(self, *, final=False):
        self._refresh_external()
        result = super().record(final=final)
        result.update(bound_preparation_cpu_seconds=self.bound_preparation_cpu,
                      formal_launcher_cpu_seconds=self.external_cpu if self.launch_meter else None,
                      formal_launcher_meter=self.launch_meter, stop_reason=self.stop_reason,
                      operation_wall_origin="formal_request" if self.launch_meter and "started_monotonic" in self.launch_meter
                                            else "runner_import_scope_before_formal_request_meter_available",
                      preparation_cpu_seconds=self.bound_preparation_cpu)
        pairs = {"cpu_seconds": (result["aggregate_metered_cpu_seconds"],
                    self.limits["aggregate_metered_cpu_seconds"], self.limits["finalization_cpu_reserve_seconds"]),
                 "wall_seconds": (result["operation_wall_seconds"], self.limits["operation_wall_seconds"],
                    self.limits["finalization_wall_reserve_seconds"]),
                 "allocated_bytes": (result["allocated_bytes_latest"], self.limits["allocated_bytes"],
                    self.limits["allocation_reserve_bytes"])}
        result["science_boundary_excess_at_sample"] = {k: max(0, value - (limit - reserve))
                                                         for k, (value, limit, reserve) in pairs.items()}
        result["hard_envelope_excess_at_sample"] = {k: max(0, value - limit)
                                                      for k, (value, limit, _) in pairs.items()}
        result["disk_scope"] = ("unique allocated inodes in accepted source snapshot, canonical output,"
                                " authored B02 implementation/tests and owned direction scratch; no symlink traversal")
        result["scope"] = ("runner process including imports and numerical threads; reaped children separately;"
                           " bound preparation once plus reported formal launcher once; post-sample closure separately")
        return result
