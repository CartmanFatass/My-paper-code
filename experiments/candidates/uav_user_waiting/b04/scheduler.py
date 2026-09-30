"""Ordinary O/W/S visited union, optionally constrained by modeled M service."""

from contextlib import contextmanager
import time

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_user_waiting.b02 import protocol as p
from experiments.candidates.uav_user_waiting.b02.scheduler import (
    DeadlineExceeded, Scheduler as FrozenScheduler, _Stage,
)


class Scheduler(FrozenScheduler):
    def __init__(self, arm, map_packet, clock=time.perf_counter,
                 cpu_clock=time.process_time, *, horizon=p.HORIZON):
        if arm not in ('M', 'S', 'U', 'K'):
            raise ValueError('B04 requires M/S/U/K')
        super().__init__('M' if arm in ('U', 'K') else arm, map_packet,
                         clock, cpu_clock, horizon=horizon)
        self.arm = arm

    def decide(self, own_observation, actual, proposals, tick, current_mask, nav_indices,
               *, started=None, cpu_started=None):
        if self.arm in ('M', 'S'):
            return super().decide(own_observation, actual, proposals, tick, current_mask,
                                  nav_indices, started=started, cpu_started=cpu_started)
        start = self.clock() if started is None else started
        cpu_start = self.cpu_clock() if cpu_started is None else cpu_started
        if tick not in range(0, self.horizon, p.HOLD) or len(self.execution.actions) != tick:
            raise ValueError('report clock and execution log disagree')
        p.mask_array(current_mask)
        actual, proposals, nav_indices = p.commands(actual), p.commands(proposals), p.navigation(nav_indices)
        counts = {key: 0 for key in ('candidate_requests', 'candidate_cache_hits',
                  'candidate_uncached_requests', 'candidate_plans', 'state_reductions',
                  'geometry_snapshots', 'prefix_ticks', 'current_prefix_ticks',
                  'continuation_prefix_ticks', 'history_reductions', 'virtual_c_decisions',
                  'synthetic_observations', 'synthetic_reports', 'observation_user_links',
                  'observation_peer_links')}
        union = dict(completed=False, pool_pairs=np.empty((0, 2), np.int64),
                     m_pair=np.full(2, -1, np.int64), s_pair=np.full(2, -1, np.int64),
                     u_pair=np.full(2, -1, np.int64), k_pair=np.full(2, -1, np.int64),
                     service_totals=np.empty(0, np.int64), service_floor_total=-1,
                     feasible=np.empty(0, bool))
        r = dict(arm=self.arm, tick=int(tick), horizon=self.horizon,
                 history_before=self.execution.next_unsettled, history_after=self.execution.next_unsettled,
                 snapshot_valid=False, decoded_anchor=False, decoded_positions=np.full((p.N, 3), np.nan),
                 decoded_actual=np.zeros((p.N, 3)), decoded_proposals=np.zeros((p.N, 3)),
                 decoded_nav=np.zeros(p.N, np.uint8), report_packets=np.empty((0, p.REPORT.size), np.uint8),
                 command_packet=np.empty(0, np.uint8), requested_pair=np.full(2, -1, np.int64),
                 current={}, branches={}, phase_wall={}, phase_cpu={}, counts=counts, union=union,
                 s_pair=np.full(2, -1, np.int64), first_finalists=np.empty((0, 2), np.int64),
                 continuation_used=False, selected_branch=-1, fallback_reason='deadline',
                 c0_pair=np.full(2, -1, np.int64), c1_pair=np.full(2, -1, np.int64),
                 c0_current_q2=-1, c1_current_q2=-1, c0_continuation_q2=-1, c1_continuation_q2=-1,
                 c0_q8=-1, c1_q8=-1, c_diagnostics_valid=False)
        packets, command_packet, selected, current = (), b'', None, None
        before_count = len(self.execution.predicted)

        def check():
            if self.clock() - start > p.DEADLINE_SECONDS:
                raise DeadlineExceeded

        @contextmanager
        def phase(name):
            wall, cpu = self.clock(), self.cpu_clock()
            try:
                yield
            finally:
                r['phase_wall'][name] = self.clock() - wall
                r['phase_cpu'][name] = self.cpu_clock() - cpu

        def retain_pool():
            # Also retain completed candidates when generation/ranking was interrupted.
            union['pool_pairs'] = np.array([row['pair'] for row in current.data], np.int64).reshape(-1, 2)
            union['service_totals'] = np.array([row['contacts'].sum(dtype=np.int64) for row in current.data], np.int64)
            union['feasible'] = (union['service_totals'] >= union['service_floor_total']
                                 if union['service_floor_total'] >= 0 else np.zeros(len(current.data), bool))

        try:
            check()
            with phase('reports'):
                packets = p.encode_reports(own_observation, actual, proposals, tick, nav_indices)
                r['report_packets'] = np.array([np.frombuffer(packet, np.uint8) for packet in packets])
                check()
                positions, actual_wire, proposed_wire, nav_wire = p.decode_reports(packets, tick)
                self.execution.anchor(tick, positions)
                r.update(decoded_anchor=True, decoded_positions=positions.copy(), decoded_actual=actual_wire.copy(),
                         decoded_proposals=proposed_wire.copy(), decoded_nav=nav_wire.copy())
                check()
            with phase('history'):
                _, ready = self.execution.settle(tick, check)
            if not ready:
                r['fallback_reason'] = 'history_unavailable'
                raise DeadlineExceeded
            r['snapshot_valid'] = True
            current = _Stage(self, r['current'], positions, actual_wire, proposed_wire, nav_wire,
                             tick, current_mask, self.execution.history, check, counts)
            with phase('current_prefix'):
                current.prepare()
            with phase('current_search'):
                o_pair, _ = current.search('O')
                w_pair, _ = current.search('W')
                m_pair = max((o_pair, w_pair), key=lambda pair: current.key(pair, 'W'))
                union['m_pair'] = np.array(m_pair, np.int64)
                union['service_floor_total'] = int(current.data[current.cache[m_pair]]['contacts'].sum(dtype=np.int64))
                s_pair, finalists = current.search('S')
                r['s_pair'] = union['s_pair'] = np.array(s_pair, np.int64)
                r['first_finalists'] = np.array(list(dict.fromkeys(finalists)), np.int64).reshape(-1, 2)
            current.record['completed'] = True
            with phase('union_ranking'):
                check()
                retain_pool()
                pairs = [tuple(map(int, pair)) for pair in union['pool_pairs']]
                u_pair = max(pairs, key=lambda pair: current.key(pair, 'S'))
                k_pair = max((pair for pair, feasible in zip(pairs, union['feasible']) if feasible),
                             key=lambda pair: current.key(pair, 'S'))
                union.update(u_pair=np.array(u_pair, np.int64), k_pair=np.array(k_pair, np.int64))
                check()
                union['completed'] = True
                selected = u_pair if self.arm == 'U' else k_pair
            r['requested_pair'] = np.array(selected, np.int64)
            with phase('command'):
                check()
                command_packet = p.encode_command(selected[1], current.member, selected[0], tick)
                r['command_packet'] = np.frombuffer(command_packet, np.uint8).copy()
                mask, member, q = p.decode_command(command_packet, tick)
                returned = proposed_wire.copy()
                returned[member] = COMMANDS[q]
                check()
        except DeadlineExceeded:
            selected = None
        finally:
            counts['history_reductions'] = len(self.execution.predicted) - before_count
            r.update(history_after=self.execution.next_unsettled,
                     history_start=-1 if self.execution.start_tick is None else self.execution.start_tick,
                     history_last=self.execution.history.last.copy(), history_windows=self.execution.history.windows.copy(),
                     history_burden=self.execution.history.burden.copy(), burden_unknown=bool(self.execution.history.burden_unknown))
            if current is not None:
                current.finish_record()
                retain_pool()
        elapsed = self.clock() - start
        if elapsed > p.DEADLINE_SECONDS:
            selected = None
        if selected is None:
            returned, mask, command_packet = actual.copy(), int(current_mask), b''
        r.update(returned_commands=returned.copy(), returned_mask=int(mask), timely=selected is not None,
                 actual_timeout=elapsed > p.DEADLINE_SECONDS,
                 fallback_reason='' if selected is not None else r['fallback_reason'],
                 delivered_command_packet=np.frombuffer(command_packet, np.uint8).copy())
        counts['interrupted_candidate_requests'] = counts['candidate_uncached_requests'] - counts['candidate_plans']
        cpu_elapsed = self.cpu_clock() - cpu_start
        r.update(wall_seconds=elapsed, cpu_seconds=cpu_elapsed)
        return dict(commands=returned, mask=mask, timely=selected is not None,
                    selected_q=None if selected is None else selected[0], selected_mask=None if selected is None else selected[1],
                    reports=packets, command_packet=command_packet, wall_seconds=elapsed, cpu_seconds=cpu_elapsed,
                    scheduler_wall=elapsed, scheduler_cpu=cpu_elapsed, counts=counts, record=r,
                    recurring_bytes=sum(map(len, packets)) + len(command_packet),
                    **{key: counts[key] for key in ('candidate_requests', 'candidate_plans', 'state_reductions',
                                                   'geometry_snapshots', 'prefix_ticks')})
