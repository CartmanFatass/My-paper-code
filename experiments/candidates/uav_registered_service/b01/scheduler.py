"""Finite two-order O/P search with private prefix and candidate histories."""

import time

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b02.scheduler import rank as native_rank
from experiments.candidates.uav_radio_activation.b03.protocol import (
    ALL_ON, DEADLINE_SECONDS, DELIVERY, HOLD, HORIZON, N, U, LOW, HIGH,
    command_index, decode_command, decode_map, decode_reports, encode_command,
    encode_reports, forecast_positions, mask_array,
)
from experiments.candidates.uav_radio_activation.b03.scheduler import DeadlineExceeded
from .history import ExecutionHistory, age_groups, model


def ordering(arm, q, mask, native, age_counts, new_pairs, proposal_q):
    base = tuple(int(x) for x in age_counts) + native_rank(q, mask, native, proposal_q)
    return (int(new_pairs),) + base if arm == 'P' else base


def sequential_search(score, key, current_mask, proposal_q):
    """Every inner and final choice uses the same history ordering."""
    def choose(pairs):
        best, best_key = None, None
        for pair in pairs:
            score(*pair)
            value = key(*pair)
            if best_key is None or value > best_key:
                best, best_key = pair, value
        return best
    first_q, _ = choose((q, current_mask) for q in range(len(COMMANDS)))
    motion_first = choose((first_q, mask) for mask in range(1, ALL_ON + 1))
    _, first_mask = choose((proposal_q, mask) for mask in range(1, ALL_ON + 1))
    mask_first = choose((q, first_mask) for q in range(len(COMMANDS)))
    return max((motion_first, mask_first), key=lambda pair: key(*pair))


class Scheduler:
    def __init__(self, arm, map_packet, clock=time.perf_counter,
                 cpu_clock=time.process_time, *, horizon=HORIZON):
        if arm not in ('O', 'P') or not isinstance(horizon, (int, np.integer)) or not 8 <= horizon <= HORIZON or horizon % HOLD:
            raise ValueError('O/P require a four-tick horizon from8 to256')
        self.arm, self.sites = arm, decode_map(map_packet)
        self.clock, self.cpu_clock, self.horizon = clock, cpu_clock, int(horizon)
        self.execution = ExecutionHistory(self.sites)

    def executed(self, tick, commands, mask):
        self.execution.append(tick, commands, mask)

    def decide(self, own_observation, actual_commands, proposals, tick, current_mask,
               *, started=None, cpu_started=None):
        start = self.clock() if started is None else started
        cpu_start = self.cpu_clock() if cpu_started is None else cpu_started
        if tick not in range(0, self.horizon, HOLD) or len(self.execution.actions) != tick:
            raise ValueError('report clock and execution log disagree')
        mask_array(current_mask)
        actual, proposed = np.asarray(actual_commands), np.asarray(proposals)
        member = (tick // HOLD) % N
        proposal_q = command_index(proposed[member])
        length = min(HOLD, self.horizon - tick - DELIVERY)
        forecast = np.full((27, length, N, 3), np.nan)
        scores = np.full((27, 32, 3), np.nan)
        contacts = np.zeros((27, 32, length, U), dtype=bool)
        keys = np.full((27, 32, U + 7), np.nan)
        key_length = 0
        snapshot_valid = prefix_valid = False
        packets, command_packet, selected = (), b'', None
        decoded_anchor = False
        fallback_reason = 'deadline'
        evaluated_pairs, geometry = [], {}
        cache_hits = uncached_requests = 0
        candidate_requests = reductions = prefix_ticks = history_reductions = 0
        history_wall = history_cpu = prefix_wall = prefix_cpu = candidate_wall = candidate_cpu = 0.
        snapshot_last = np.full(U, -2, dtype=int)
        snapshot_windows = np.zeros((4, U), dtype=bool)
        prefix_last, prefix_windows = snapshot_last.copy(), snapshot_windows.copy()
        before = self.execution.next_unsettled
        before_count = len(self.execution.predicted)

        def check():
            if self.clock() - start > DEADLINE_SECONDS:
                raise DeadlineExceeded

        try:
            check()
            packets = encode_reports(own_observation, actual, proposed, tick)
            check()  # An encode overrun never supplies an unreceived position anchor.
            positions, actual_wire, proposed_wire = decode_reports(packets, tick)
            self.execution.anchor(tick, positions)
            decoded_anchor = True
            check()
            hs, hc = self.clock(), self.cpu_clock()
            try:
                _, ready = self.execution.settle(tick, check)
            finally:
                history_wall, history_cpu = self.clock() - hs, self.cpu_clock() - hc
                history_reductions = len(self.execution.predicted) - before_count
            if not ready:
                fallback_reason = 'history_unavailable'
                raise DeadlineExceeded  # No causal pre-task/startup anchor; retain pending work.
            settled = self.execution.history.copy()
            snapshot_last, snapshot_windows = settled.last.copy(), settled.windows.copy()
            snapshot_valid = True
            ps, pc = self.clock(), self.cpu_clock()
            try:
                prefix = settled.copy()
                position = positions.copy()
                for offset in range(DELIVERY):
                    check()
                    position = np.clip(position + actual_wire * 30., LOW, HIGH)
                    served, _ = model(position, self.sites, current_mask)
                    prefix.update(tick + offset, served)
                    prefix_ticks += 1
                    check()
                prefix_last, prefix_windows = prefix.last.copy(), prefix.windows.copy()
                prefix_valid = True
                groups = age_groups(prefix)
                key_length = len(groups) + 6 + int(self.arm == 'P')
                forecast = forecast_positions(positions, actual_wire, proposed_wire, tick, member,
                                              horizon=self.horizon)
                check()
            finally:
                prefix_wall, prefix_cpu = self.clock() - ps, self.cpu_clock() - pc
            cs, cc = self.clock(), self.cpu_clock()
            try:
                def score(q, mask):
                    nonlocal candidate_requests, reductions, cache_hits, uncached_requests
                    candidate_requests += 1
                    if np.isfinite(scores[q, mask, 0]):
                        cache_hits += 1
                        return scores[q, mask]
                    uncached_requests += 1
                    if q not in geometry:
                        from envs.pettingzoo.uav_radio import free_space_user_path_loss
                        geometry[q] = []
                        for position in forecast[q]:
                            check()
                            geometry[q].append(free_space_user_path_loss(position, self.sites))
                            check()
                    from envs.pettingzoo.uav_radio import (
                        user_sinr_from_path_loss, greedy_connection_assignment, service_metrics,
                    )
                    private = prefix.copy()
                    values, served_rows, new_pairs = [], [], 0
                    for slot, losses in enumerate(geometry[q]):
                        check()
                        sinr = user_sinr_from_path_loss(losses, transmitter_mask=mask_array(mask))
                        connections = greedy_connection_assignment(sinr)
                        metrics = service_metrics(sinr, connections)
                        served = connections.any(axis=0)
                        new_pairs += private.update(tick + DELIVERY + slot, served)
                        served_rows.append(served)
                        values.append((metrics['J'], metrics['served'], metrics['quality']))
                        reductions += 1
                        check()
                    native = np.mean(values, axis=0)
                    contact = np.array(served_rows)
                    distinct = contact.any(axis=0)
                    counts = [int((distinct & group).sum()) for group in groups]
                    key = ordering(self.arm, q, mask, native, counts, new_pairs, proposal_q)
                    check()
                    scores[q, mask] = native
                    contacts[q, mask] = contact
                    keys[q, mask, :key_length] = key
                    evaluated_pairs.append((q, mask))
                    return scores[q, mask]
                selected = sequential_search(score, lambda q, mask: tuple(keys[q, mask, :key_length]),
                                             current_mask, proposal_q)
                check()
                command_packet = encode_command(selected[1], member, selected[0], tick)
                received_mask, received_member, received_q = decode_command(command_packet, tick)
                commands = proposed_wire.copy()
                commands[received_member] = COMMANDS[received_q]
                check()
            finally:
                candidate_wall, candidate_cpu = self.clock() - cs, self.cpu_clock() - cc
        except DeadlineExceeded:
            selected = None
        elapsed = self.clock() - start
        if elapsed > DEADLINE_SECONDS:
            selected = None
        if selected is None:
            commands, received_mask, command_packet = actual.copy(), int(current_mask), b''
        return dict(commands=commands, mask=received_mask,
                    selected_q=None if selected is None else selected[0],
                    selected_mask=None if selected is None else selected[1], timely=selected is not None,
                    reports=packets, command_packet=command_packet, forecast=forecast, scores=scores,
                    scored_length=length, evaluated_pairs=evaluated_pairs,
                    candidate_plans=len(evaluated_pairs), candidate_requests=candidate_requests,
                    candidate_cache_hits=cache_hits, candidate_uncached_requests=uncached_requests,
                    interrupted_candidate_requests=uncached_requests-len(evaluated_pairs),
                    state_reductions=reductions, geometry_snapshots=sum(map(len, geometry.values())),
                    prefix_ticks=prefix_ticks, wall_seconds=elapsed, cpu_seconds=self.cpu_clock() - cpu_start,
                    recurring_bytes=sum(map(len, packets)) + len(command_packet),
                    sequential_pair=selected, sequential_score=None if selected is None else scores[selected].copy(),
                    ordering_keys=keys, key_length=key_length, candidate_contacts=contacts,
                    history_start=-1 if self.execution.start_tick is None else self.execution.start_tick,
                    window_valid=np.arange(4)*64 >= (256 if self.execution.start_tick is None else self.execution.start_tick),
                    unknown_age=(self.execution.history.last == -1) & (self.execution.start_tick is not None and self.execution.start_tick > 0),
                    actual_timeout=elapsed > DEADLINE_SECONDS,
                    decoded_anchor=decoded_anchor, fallback_reason='' if selected is not None else fallback_reason, history_before=before,
                    history_after=self.execution.next_unsettled,
                    snapshot_valid=snapshot_valid, prefix_valid=prefix_valid,
                    snapshot_last=snapshot_last, snapshot_windows=snapshot_windows,
                    prefix_last=prefix_last, prefix_windows=prefix_windows,
                    history_reductions=history_reductions, history_wall=history_wall, history_cpu=history_cpu,
                    prefix_wall=prefix_wall, prefix_cpu=prefix_cpu,
                    candidate_wall=candidate_wall, candidate_cpu=candidate_cpu)
