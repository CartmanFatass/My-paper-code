"""Native outcomes, execution exposure and fixed paired-world comparisons."""
from __future__ import annotations

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS
from experiments.candidates.uav_fleet_adaptation.b02.reading import numeric_summary, sum_counts
from .contract import ARMS, arm_parts

LOW = np.array([0., 0., 50.])
HIGH = np.array([1000., 1000., 150.])
METRICS = (
    "J", "mean_served", "service_p10", "min_served", "zero_service_steps",
    "longest_zero_service_gap", "mean_sinr_quality", "mean_path_length_m",
    "transmitter_on_ticks", "mean_active_transmitters", "all_on_steps", "transmitter_switches",
    "mean_no_eligible_users", "mean_eligible_unassigned_users", "fallback_decisions",
    "silent_decision_rows", "empty_decision_rows", "active_empty_decision_rows",
    "requested_departures", "proposal_one_step_physical_departures", "proposal_clipping_aliases",
    "delivered_proposal_overrides", "delivered_one_step_physical_overrides", "late_proposal_carries",
    "actual_command_changes", "actual_one_step_physical_changes", "deadline_misses",
    "recurring_bytes", "map_provisioned_bytes", "decision_query_cpu_seconds",
    "decision_query_wall_seconds", "sampler_cpu_seconds", "sampler_wall_seconds",
    "local_block_cpu_seconds", "local_block_wall_seconds", "scheduler_cpu_seconds",
    "scheduler_wall_seconds", "cpu_seconds", "wall_seconds",
)
PAIRS = (
    ("S_I_S2", "C_S2"), ("S_I_S2", "Q_I_S2"), ("S_I_S2", "C_T2"),
    ("S_I_E", "C_E"), ("S_I_E", "Q_I_E"),
    ("S_I_all", "C_all"), ("S_I_all", "Q_I_all"),
    ("Q_I_S2", "C_S2"), ("Q_I_E", "C_E"), ("Q_I_all", "C_all"),
    ("C_T2", "C_S2"),
) + tuple((f + "_" + deployment, f + "_all")
          for f in ("C", "Q_I", "S_I") for deployment in ("E", "S2")) + tuple(
              (f + "_S2", f + "_E") for f in ("C", "Q_I", "S_I"))


def episode_metrics(raw, arm):
    _, coordinator = arm_parts(arm)
    served = raw["served"]
    masks = raw["transmitter_mask"]
    path = np.linalg.norm(np.diff(raw["positions"], axis=0), axis=-1).sum(axis=0)
    eligible = np.any(raw["sinr"] >= 3., axis=1)
    assigned = np.any(raw["connections"], axis=1)
    no_server = 50 - eligible.sum(axis=1)
    unassigned = (eligible & ~assigned).sum(axis=1)
    if not np.array_equal(50 - served, no_server + unassigned):
        raise AssertionError("eligibility/assignment accounting identity changed")
    longest = current = 0
    for value in served:
        current = current + 1 if value == 0 else 0
        longest = max(longest, current)
    requested = raw["action_index"] != raw["modal_index"]
    decision_positions = raw["positions"][raw["decision_ticks"]]
    proposed = np.clip(decision_positions + raw["proposals"].astype(np.float64) * 30., LOW, HIGH)
    modal = np.clip(decision_positions + COMMANDS[raw["modal_index"]].astype(np.float64) * 30., LOW, HIGH)
    proposal_physical = np.any(proposed != modal, axis=-1)
    old_commands = np.concatenate((np.zeros((1, 5, 3), np.float32), raw["commands"][:-1]))
    actual_changed = np.any(raw["commands"] != old_commands, axis=-1)
    continued = np.clip(raw["positions"][:-1] + old_commands.astype(np.float64) * 30., LOW, HIGH)
    actual_physical = np.any(raw["positions"][1:] != continued, axis=-1)
    overrides = physical_overrides = late_carries = 0
    if coordinator in ("S2", "T2"):
        edited = np.any(raw["coord_commands"] != raw["proposals"], axis=-1)
        overrides = int((edited & raw["coord_timely"][:, None]).sum())
        late_carries = int((edited & ~raw["coord_timely"][:, None]).sum())
        delivery_positions = raw["positions"][raw["coord_due"]]
        delivered = np.clip(delivery_positions + raw["coord_commands"].astype(np.float64) * 30., LOW, HIGH)
        uncorrected = np.clip(delivery_positions + raw["proposals"].astype(np.float64) * 30., LOW, HIGH)
        physical_overrides = int((np.any(delivered != uncorrected, axis=-1)
                                  & raw["coord_timely"][:, None]).sum())
    return dict(
        J=float(raw["reward"].mean()), return_sum=float(raw["reward"].sum()),
        mean_served=float(served.mean()), service_p10=float(np.quantile(served, .1)),
        min_served=int(served.min()), zero_service_steps=int(np.count_nonzero(served == 0)),
        longest_zero_service_gap=longest, mean_sinr_quality=float(raw["sinr_quality"].mean()),
        mean_path_length_m=float(path.mean()), per_agent_path_length_m=path.tolist(),
        transmitter_on_ticks=int(masks.sum()), mean_active_transmitters=float(masks.sum(axis=1).mean()),
        all_on_steps=int(np.count_nonzero(masks.all(axis=1))),
        transmitter_switches=int(np.count_nonzero(masks[1:] != masks[:-1])),
        mean_no_eligible_users=float(no_server.mean()), mean_eligible_unassigned_users=float(unassigned.mean()),
        fallback_decisions=int(raw["fallback"].sum()),
        silent_decision_rows=int(np.count_nonzero(~masks[::4])),
        empty_decision_rows=int(np.count_nonzero(raw["n_current"] == 0)),
        active_empty_decision_rows=int(np.count_nonzero((raw["n_current"] == 0) & masks[::4])),
        requested_departures=int(requested.sum()),
        multi_departure_blocks=int(np.count_nonzero(requested.sum(axis=1) >= 2)),
        proposal_one_step_physical_departures=int(proposal_physical.sum()),
        proposal_clipping_aliases=int(np.count_nonzero(requested & ~proposal_physical)),
        delivered_proposal_overrides=overrides, delivered_one_step_physical_overrides=physical_overrides,
        late_proposal_carries=late_carries, actual_command_changes=int(actual_changed.sum()),
        actual_one_step_physical_changes=int(actual_physical.sum()),
        deadline_misses=int(np.count_nonzero(~raw["coord_timely"])),
        recurring_bytes=int(raw["coord_recurring_bytes"].sum()),
        map_provisioned_bytes=int(raw["map_packet"].nbytes),
        xy_boundary_uav_steps=int(np.any((raw["positions"][1:, :, :2] <= .001)
                                        | (raw["positions"][1:, :, :2] >= 999.999), axis=-1).sum()),
        lower_altitude_uav_steps=int((raw["positions"][1:, :, 2] <= 50.001).sum()),
    )


def cost_totals(rows):
    result = {family: sum_counts(r["policy_counts"] for r in rows
                                if ("S" if arm_parts(r["arm"])[0] == "S_I" else "C") == family)
              for family in ("C", "S")}
    result.update({coordinator: sum_counts(r["coordinator_counts"] for r in rows
                                          if arm_parts(r["arm"])[1] == coordinator)
                   for coordinator in ("E", "S2", "T2")})
    return result


def read_comparisons(rows, protocol):
    by_key = {(r["arm"], r["world"], r["tape"]): r for r in rows}
    if len(by_key) != len(rows) or set(by_key) != set(protocol.schedule()):
        raise ValueError("incomplete or duplicated B05 schedule")

    def at(arm, world, metric, tape=None):
        deterministic = arm_parts(arm)[0] == "C"
        tapes = (-1,) if deterministic else protocol.tapes if tape is None else (tape,)
        return float(np.mean([by_key[arm, world, t][metric] for t in tapes]))

    means = {arm: {m: numeric_summary([at(arm, w, m) for w in protocol.worlds]) for m in METRICS}
             for arm in ARMS}
    paired = {}
    for left, right in PAIRS:
        values = {}
        tapes = (-1,) if arm_parts(left)[0] == arm_parts(right)[0] == "C" else protocol.tapes
        for metric in METRICS:
            delta = np.array([at(left, w, metric) - at(right, w, metric) for w in protocol.worlds])
            values[metric] = dict(
                **numeric_summary(delta), differences=delta.tolist(),
                per_tape_differences={str(t): [at(left, w, metric, t) - at(right, w, metric, t)
                                              for w in protocol.worlds] for t in tapes},
                positive=int(np.count_nonzero(delta > 0)), negative=int(np.count_nonzero(delta < 0)),
                zero=int(np.count_nonzero(delta == 0)),
                worst_world=protocol.worlds[int(np.argmin(delta))],
                best_world=protocol.worlds[int(np.argmax(delta))],
            )
        paired[left + "-" + right] = values
    primary = [paired[name]["J"] for name in ("S_I_S2-C_S2", "S_I_S2-Q_I_S2")]
    interaction = {}
    for coordinator in ("E", "S2"):
        for reference in ("C", "Q_I"):
            key = f"(S_I_{coordinator}-{reference}_{coordinator})-(S_I_all-{reference}_all)"
            interaction[key] = {}
            for metric in ("J", "mean_served", "service_p10", "mean_path_length_m"):
                values = [at("S_I_" + coordinator, w, metric) - at(reference + "_" + coordinator, w, metric)
                          - at("S_I_all", w, metric) + at(reference + "_all", w, metric)
                          for w in protocol.worlds]
                interaction[key][metric] = dict(**numeric_summary(values), differences=values)
    return dict(worlds=list(protocol.worlds), means=means, paired=paired, interaction=interaction,
                primary=dict(point_prediction_met=all(p["mean"] > 0 for p in primary),
                             positive_descriptive_support=all(p["descriptive_t95"] is not None
                                                              and p["descriptive_t95"][0] > 0 for p in primary)),
                scope="Two tapes averaged within each of 32 equally weighted worlds; two-sided descriptive95% "
                      "df31 t intervals in production. One fixed asset; no training replication, simultaneous "
                      "guarantee, equivalence or causally isolated motion/radio effect. E remains secondary; "
                      "C_T2 constrains any broader ordinary-control preference.")
