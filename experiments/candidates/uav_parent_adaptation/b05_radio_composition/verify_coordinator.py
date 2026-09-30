"""Saved-wire/arrival/search audit with the predeclared bounded radio recomputation."""
from __future__ import annotations

import numpy as np

from envs.pettingzoo.uav_radio import (free_space_user_path_loss, greedy_connection_assignment,
                                     service_metrics, user_sinr_from_path_loss)
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.read import equal, require
from experiments.candidates.uav_radio_activation.b01 import protocol as ep
from experiments.candidates.uav_radio_activation.b03 import protocol as jp
from .collection import COORD_COUNTERS, allocate_raw
from .contract import arm_parts


def coordinator_counts():
    return {key: 0 for key in ("candidate_pair_requests", "candidate_geometry_requests",
                               "candidate_geometry_attempts", "candidate_geometry_completed",
                               "candidate_user_links_attempts", "candidate_user_links_completed",
                               "candidate_reduction_attempts", "candidate_reduction_completed",
                               "forecast_motion_agent_ticks", "wire_report_rounds", "search_arithmetic_requests")}


def ordering(q, mask, value, proposal_q):
    return (float(value[0]), float(value[1]), q == proposal_q,
            int(mask).bit_count(), -int(mask), -int(q))


class _SearchStopped(Exception):
    pass


def sequential_from_saved(scores, current_mask, proposal_q, calls, *, limit=None):
    """Independent explicit coordinate orders; no scheduler or physics call."""
    requests, first_seen = [], []

    def query(q, mask):
        if limit is not None and len(requests) >= limit:
            raise _SearchStopped
        calls["search_arithmetic_requests"] += 1
        requests.append((q, mask))
        if not np.isfinite(scores[q, mask]).all():
            raise _SearchStopped
        if (q, mask) not in first_seen:
            first_seen.append((q, mask))
        return ordering(q, mask, scores[q, mask], proposal_q)

    try:
        q1 = max(range(27), key=lambda q: query(q, current_mask))
        m1 = max(range(1, 32), key=lambda mask: query(q1, mask))
        m2 = max(range(1, 32), key=lambda mask: query(proposal_q, mask))
        q2 = max(range(27), key=lambda q: query(q, m2))
        a, b = (q1, m1), (q2, m2)
        chosen = a if ordering(*a, scores[a], proposal_q) >= ordering(*b, scores[b], proposal_q) else b
    except _SearchStopped:
        chosen = None
    return chosen, requests, first_seen


class _CandidateReader:
    def __init__(self, forecast, sites, calls, check):
        self.forecast, self.sites, self.calls, self.check = forecast, sites, calls, check
        self.geometry, self.values = {}, {}

    def score(self, q, mask):
        """One declared distinct pair; geometry only reused within this exact round."""
        self.check()
        c = self.calls
        c["candidate_pair_requests"] += 1
        c["candidate_geometry_requests"] += len(self.forecast[q])
        if q not in self.geometry:
            losses = []
            for positions in self.forecast[q]:
                self.check()
                c["candidate_geometry_attempts"] += 1
                c["candidate_user_links_attempts"] += 250
                losses.append(free_space_user_path_loss(positions, self.sites))
                c["candidate_geometry_completed"] += 1
                c["candidate_user_links_completed"] += 250
            self.geometry[q] = losses
        states = []
        for loss in self.geometry[q]:
            self.check()
            c["candidate_reduction_attempts"] += 1
            sinr = user_sinr_from_path_loss(loss, transmitter_mask=ep.mask_array(mask))
            connections = greedy_connection_assignment(sinr)
            metrics = service_metrics(sinr, connections)
            states.append([metrics["J"], metrics["served"], metrics["quality"]])
            c["candidate_reduction_completed"] += 1
        self.values[q, mask] = np.asarray(states)
        return self.values[q, mask]


def _forecast(positions, actual, proposals, tick, coordinator, horizon, calls):
    prefix = 1 if coordinator == "E" else 2
    length = min(4, horizon - tick - prefix)
    state = positions.copy()
    calls["forecast_motion_agent_ticks"] += prefix * 5
    for _ in range(prefix):
        state = np.clip(state + actual * 30., ep.LOW, ep.HIGH)
    commands = [actual] if coordinator == "E" else [proposals.copy() for _ in range(27)]
    if coordinator != "E":
        for q, commands_q in enumerate(commands):
            commands_q[(tick // 4) % 5] = COMMANDS[q]
    result = []
    for commands_q in commands:
        positions_q, values = state.copy(), []
        calls["forecast_motion_agent_ticks"] += length * 5
        for _ in range(length):
            positions_q = np.clip(positions_q + commands_q * 30., ep.LOW, ep.HIGH)
            values.append(positions_q.copy())
        result.append(values)
    return np.asarray(result)


def _array_shapes(raw, horizon, coordinator):
    for key, exemplar in allocate_raw(horizon, coordinator).items():
        if not key.startswith("coord_"):
            continue
        require(key in raw and raw[key].shape == exemplar.shape and raw[key].dtype == exemplar.dtype,
                "coordinator array schema " + key)
        require(not np.isinf(raw[key]).any(), "infinite coordinator field " + key)
        if key not in ("coord_forecast", "coord_scores", "coord_per_state", "coord_sequential_score"):
            require(np.isfinite(raw[key]).all(), "nonfinite coordinator field " + key)


def verify_coordinator(raw, row, protocol, calls, check):
    _, coordinator = arm_parts(row["arm"])
    h, d = protocol.horizon, protocol.horizon // 4
    _array_shapes(raw, h, coordinator)
    require(bool(raw["episode_complete"]) and int(raw["completed_rounds"]) == (0 if coordinator == "all" else d),
            "complete coordinator rounds")
    expected_cost = {key: int(raw["coord_" + key].sum()) for key in COORD_COUNTERS}
    require(row["coordinator_counts"] == expected_cost, "saved coordinator cost totals")
    equal(row["scheduler_wall_seconds"], raw["coord_wall_seconds"].sum(), "scheduler wall sum", 1e-12)
    equal(row["scheduler_cpu_seconds"], raw["coord_cpu_seconds"].sum(), "scheduler CPU sum", 1e-12)
    if coordinator == "all":
        require(raw["map_packet"].size == 0, "all-on policy has no provisioned map")
        equal(raw["commands"], np.repeat(raw["proposals"], 4, axis=0), "immediate all-on motion")
        require(raw["transmitter_mask"].all() and raw["terminal_mask"].all(), "all-on transmitter contract")
        return dict(rounds=[], forecast_errors_by_offset={})
    require(raw["map_packet"].dtype == np.uint8 and raw["map_packet"].tobytes() == ep.encode_map(raw["initial_users"]),
            "one provisioned rounded map")
    sites = ep.decode_map(raw["map_packet"].tobytes())
    equal(raw["coord_tick"], np.arange(0, h, 4), "coordinator clock")
    require(raw["coord_started"].all(), "missing coordinator invocation")
    for name in COORD_COUNTERS + ("wall_seconds", "cpu_seconds"):
        require(np.all(raw["coord_" + name] >= 0), "negative coordinator work/time " + name)
    mask, actual = 31, np.zeros((5, 3), np.float32)
    audits, errors = [], {}
    for j, tick in enumerate(range(0, h, 4)):
        check()
        proposal = raw["proposals"][j]
        if coordinator == "E" or tick == 0:
            actual = proposal.copy()
        prefix = 1 if coordinator == "E" else 2
        due, length = tick + prefix, min(4, h - tick - prefix)
        require(raw["coord_due"][j] == due and raw["coord_mask_before"][j] == mask, "arrival/previous-mask identity")
        equal(raw["coord_actual"][j], actual, "reported actual commitment")
        equal(raw["commands"][tick:due], np.broadcast_to(actual, (prefix, 5, 3)), "prearrival commitment")
        equal(raw["transmitter_mask"][tick:due], np.broadcast_to(ep.mask_array(mask), (prefix, 5)), "prearrival mask")
        timely = bool(raw["coord_timely"][j])
        deadline = ep.DEADLINE_SECONDS if coordinator == "E" else jp.DEADLINE_SECONDS
        require(timely == (raw["coord_wall_seconds"][j] <= deadline), "deadline/fallback inconsistency")
        reports = int(raw["coord_report_count"][j])
        require(reports == 5 if coordinator == "E" else reports in (0, 5), "partial report count")
        require(bool(raw["coord_has_command"][j]) == timely, "packet existence follows timely delivery")
        require(raw["coord_recurring_bytes"][j] == 24 * reports + 16 * timely, "actual recurring byte exposure")
        if reports:
            expected_packets = (ep.encode_reports(raw["observations"][tick, :, :3], actual, tick)
                                if coordinator == "E" else jp.encode_reports(
                                    raw["observations"][tick, :, :3], actual, proposal, tick))
            require(tuple(p.tobytes() for p in raw["coord_reports"][j]) == expected_packets, "report state/command provenance")
            decoded = ep.decode_reports(expected_packets, tick) if coordinator == "E" else jp.decode_reports(expected_packets, tick)
            calls["wire_report_rounds"] += 1
        else:
            require(not raw["coord_reports"][j].any() and not timely, "untransmitted report bytes")
            decoded = None
        score = raw["coord_scores"][j]
        present = np.isfinite(score).all(axis=-1)
        require(np.array_equal(present, ~np.isnan(score).all(axis=-1)), "partial candidate score triple")
        require(not present[..., 0].any(), "empty transmitter mask was scored")
        scored = score[present]
        require(np.all((scored[:, 1] >= 0) & (scored[:, 1] <= 50))
                and np.all((scored[:, 2] >= 0) & (scored[:, 2] <= 1)), "candidate outcome range")
        equal(scored[:, 0], .7 * scored[:, 1] / 50. + .3 * scored[:, 2], "candidate reward reduction", 1e-12)
        plans = int(raw["coord_candidate_plans"][j])
        reductions = int(raw["coord_state_reductions"][j])
        geometries = int(raw["coord_geometry_snapshots"][j])
        requests = int(raw["coord_candidate_requests"][j])
        upper = int(raw["coord_candidate_request_upper"][j])
        require(plans == int(present.sum()), "completed score count")
        order = raw["coord_order"][j, :plans].tolist()
        require(np.all(raw["coord_order"][j, plans:] == -1), "nonempty candidate order padding")
        stored_length = int(raw["coord_forecast_lengths"][j])
        expected_forecast = None
        if coordinator == "E":
            require(stored_length in (0, length), "E forecast horizon")
            if stored_length:
                require(decoded is not None, "forecast without wire reports")
                expected_forecast = _forecast(decoded[0], decoded[1], proposal, tick, coordinator, h, calls)
                equal(raw["coord_forecast"][j, :length], expected_forecast[0], "E continued-command forecast")
            require(np.isnan(raw["coord_forecast"][j, stored_length:]).all(), "E forecast padding")
            require(order == list(range(1, plans + 1)), "E exhaustive search prefix")
            equal(present, np.isin(np.arange(32), order), "E score/order identities")
            require(0 <= geometries <= stored_length and (geometries == length if plans or reductions else True), "E geometry work")
            require(plans * length <= reductions <= min((plans + 1) * length, 31 * length), "E partial state reductions")
            lower = max(plans, (reductions + max(stored_length, 1) - 1) // max(stored_length, 1))
            require(requests == lower and upper == (lower if timely else min(31, lower + 1)), "E request observation interval")
            require(raw["coord_prefix_ticks"][j] == 0 and raw["coord_selected_q"][j] == -1, "E has no joint prefix/command selection")
            require(np.all(raw["coord_sequential_pair"][j] == -1) and np.isnan(raw["coord_sequential_score"][j]).all(), "E has no sequential joint reference")
            if timely:
                require(plans == 31 and reductions == 31 * length, "incomplete E search applied")
                chosen_mask = max(order, key=lambda m: (score[m, 0], score[m, 1], m.bit_count(), -m))
                selected = (0, chosen_mask)
            else:
                selected = None
            pairs = [(0, m) for m in order]
            source_scores = score[None]
        else:
            require(stored_length == length and requests == upper, "joint fixed horizon/exact requests")
            forecast_paid = int(raw["coord_prefix_ticks"][j]) == 2
            require(raw["coord_prefix_ticks"][j] in (0, 2), "joint prefix work")
            if forecast_paid:
                require(decoded is not None, "joint forecast without reports")
                expected_forecast = _forecast(decoded[0], decoded[1], decoded[2], tick, coordinator, h, calls)
                equal(raw["coord_forecast"][j, :, :length], expected_forecast, "two-tick committed prefix/one-member forecast")
            else:
                require(np.isnan(raw["coord_forecast"][j]).all() and not (plans or requests or reductions or geometries), "work before completed prefix")
            require(np.isnan(raw["coord_forecast"][j, :, length:]).all(), "joint forecast padding")
            paid_order = [tuple(pair) for pair in order]
            require(len(set(paid_order)) == plans and set(paid_order) == set(map(tuple, np.argwhere(present))), "joint score/order identities")
            require(plans * length <= reductions <= (plans + 1) * length, "joint partial state reductions")
            q_count = len(set(q for q, _ in paid_order))
            require(q_count * length <= geometries <= min(27, q_count + 1) * length, "joint partial geometry work")
            proposal_q = int(np.flatnonzero(np.all(COMMANDS == proposal[j % 5], axis=1))[0])
            if coordinator == "S2":
                require(requests <= 116 and plans <= 112, "S2 work ceiling")
                seq, requested, seen = sequential_from_saved(score, mask, proposal_q, calls, limit=requests)
                require(len(requested) == requests and seen == paid_order, "S2 two-order request/cache prefix")
                selected = seq
            else:
                require(plans <= requests <= min(plans + 1, 837), "T2 exact request count")
                require(paid_order == [(q, m) for q in range(27) for m in range(1, 32)][:plans], "T2 exhaustive order")
                if plans == 837:
                    seq, _, _ = sequential_from_saved(score, mask, proposal_q, calls)
                    selected = max(paid_order, key=lambda pair: ordering(*pair, score[pair], proposal_q))
                else:
                    seq = selected = None
            sequential_pair = tuple(int(x) for x in raw["coord_sequential_pair"][j])
            if sequential_pair != (-1, -1):
                require(seq is not None and sequential_pair == seq, "sequential diagnostic decision")
                equal(raw["coord_sequential_score"][j], score[seq], "sequential diagnostic score")
            else:
                require(np.isnan(raw["coord_sequential_score"][j]).all(), "absent sequential score")
            if timely:
                require(selected is not None and seq is not None and sequential_pair == seq
                        and geometries == 27 * length and reductions == plans * length,
                        "incomplete joint search applied")
                require(requests == (116 if coordinator == "S2" else 837), "complete joint requests")
            else:
                selected = None
            chosen = (int(raw["coord_selected_q"][j]), int(raw["coord_selected_mask"][j]))
            candidates = [(proposal_q, 31), (proposal_q, mask), chosen, sequential_pair, (j % 27, 1 + j % 31)]
            pairs = list(dict.fromkeys(pair for pair in candidates if pair in set(paid_order)))
            require(len(pairs) <= 5, "reader pair ceiling")
            source_scores = score
        if timely:
            require(raw["coord_selected_mask"][j] == selected[1], "selected mask")
            if coordinator == "E":
                require(raw["coord_command_packet"][j].tobytes() == ep.encode_command(selected[1], tick), "E delivered packet")
                delivered = actual.copy()
            else:
                require(raw["coord_selected_q"][j] == selected[0], "selected command")
                require(raw["coord_command_packet"][j].tobytes() == jp.encode_command(selected[1], j % 5, selected[0], tick), "joint delivered packet")
                delivered = proposal.copy()
                delivered[j % 5] = COMMANDS[selected[0]]
            delivered_mask = selected[1]
        else:
            require(raw["coord_selected_q"][j] == -1 and raw["coord_selected_mask"][j] == -1
                    and not raw["coord_command_packet"][j].any(), "late command absence")
            delivered, delivered_mask = actual.copy(), mask
        equal(raw["coord_commands"][j], delivered, "delivered/fallback commands")
        require(raw["coord_mask"][j] == delivered_mask, "delivered/fallback mask")
        equal(raw["commands"][due:tick + 4], np.broadcast_to(delivered, (4 - prefix, 5, 3)), "postarrival commitment")
        equal(raw["transmitter_mask"][due:tick + 4], np.broadcast_to(ep.mask_array(delivered_mask), (4 - prefix, 5)), "postarrival mask")
        checker = None
        if pairs:
            require(expected_forecast is not None, "scored pair without completed forecast")
            checker = _CandidateReader(expected_forecast, sites, calls, check)
            for q, candidate_mask in pairs:
                states = checker.score(q, candidate_mask)
                equal(source_scores[q, candidate_mask], states.mean(axis=0), "bounded independent candidate score", 1e-12)
                if coordinator == "E":
                    equal(raw["coord_per_state"][j, candidate_mask, :length], states, "E saved state score", 1e-12)
        if coordinator == "E":
            keep = np.zeros((32, 4), bool)
            keep[order, :length] = True
            require(np.isnan(raw["coord_per_state"][j][~keep]).all(), "unpaid E state padding")
        round_errors = []
        if timely:
            states = checker.values[selected]
            for slot in range(length):
                offset = prefix + slot + 1
                distance = np.linalg.norm(expected_forecast[selected[0], slot] - raw["positions"][tick + offset], axis=-1)
                values = dict(mean_position_error_m=float(distance.mean()), max_position_error_m=float(distance.max()),
                              J_error=float(states[slot, 0] - raw["reward"][tick + offset - 1]),
                              served_error=float(states[slot, 1] - raw["served"][tick + offset - 1]))
                errors.setdefault(str(offset), []).append(values)
                round_errors.append(dict(offset=offset, **values))
        audits.append(dict(tick=tick, timely=timely, selected=selected, independently_checked_pairs=pairs,
                           requests_lower=requests, requests_upper=upper, completed_plans=plans,
                           reductions=reductions, geometries=geometries, forecast_errors=round_errors))
        actual, mask = delivered, delivered_mask
    equal(raw["terminal_mask"], ep.mask_array(mask), "terminal delivered mask")
    return dict(rounds=audits, forecast_errors_by_offset=errors)
