"""M/S and fixed terminal-value search on the lawful delayed host.

The finite M/S physics/search and deadline transaction derive from frozen B02.
No future C action is queried, and private candidates never alter executed history.
"""
from contextlib import contextmanager
import time

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b03.scheduler import DeadlineExceeded
from experiments.candidates.uav_user_waiting.b02 import protocol as p
from experiments.candidates.uav_user_waiting.b02.scheduler import _Stage
from .features import pack_features
from .history import ExecutionHistory


class Stage(_Stage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_maximum = self.prefix.maximum.copy()
        self.record['input_maximum'] = self.input_maximum.copy()
        self.record['prefix_maximum'] = self.prefix.maximum.copy()
        self.prefix_age_cost = 0

    def prepare(self):
        try:
            super().prepare()
        finally:
            self.record['prefix_maximum'] = self.prefix.maximum.copy()
            last = self.record['input_history']['last'].copy()
            for offset, contacts in enumerate(self.record['prefix_contacts'][:self.record['prefix_count']]):
                last[contacts] = self.tick + offset
                self.prefix_age_cost += int((self.tick + offset - last).sum())
            self.record['elapsed_prefix_age_cost'] = self.prefix_age_cost

    def score(self, q, mask):
        index = super().score(q, mask)
        row = self.data[index]
        if 'midpoint_maximum' not in row:
            midpoint, endpoint = self.states[index]
            row.update(midpoint_maximum=midpoint.maximum.copy(), endpoint_maximum=endpoint.maximum.copy(),
                       elapsed_increment=float((midpoint.maximum - self.input_maximum).mean()),
                       elapsed_age_cost=self.prefix_age_cost + sum(row['age_sum'][:2]),
                       value_valid=False, value_raw=np.nan, value_clipped=np.nan,
                       value_was_clipped=False, total_cost=np.nan, zero_key=np.full(8, np.nan))
            row['zero_key'] = (-row['elapsed_increment'], -int(row['elapsed_age_cost'])) + row['keys']['W'][1:]
        if self.label == 'G' and not row['value_valid']:
            self.check()
            future = self.tick + p.HOLD
            if future >= self.scheduler.horizon:
                raw_value = value = 0.
                self.counts['terminal_value_zeros'] += 1
            elif self.scheduler.arm == 'G0':
                raw_value = value = 0.
            else:
                midpoint = self.states[index][0]
                # Native report codec is round-to-nearest integer xyz. Forecasts already
                # lie on this grid; round explicitly rather than use an unquantized future.
                positions = np.rint(self.record['forecast'][q, 1])
                x = pack_features(sites=self.scheduler.sites, positions=positions,
                    commands=self.commands((q, mask)), mask=mask, previous_nav=self.record['nav'],
                    last=midpoint.last, maximum=midpoint.maximum, windows=midpoint.windows,
                    tick=future, history_start=midpoint.start_tick, history_after=future)
                self.counts['feature_rows'] += 1
                self.counts['value_queries'] += 1
                raw_value, value = self.scheduler.value.evaluate(x, future)
            if not np.isfinite([raw_value, value]).all():
                raise FloatingPointError('nonfinite deployed continuation value')
            row.update(value_valid=True, value_raw=float(raw_value), value_clipped=float(value),
                       value_was_clipped=bool(raw_value != value),
                       total_cost=float(row['elapsed_increment'] + value))
            ties = row['keys']['W'][1:]
            row['keys']['G'] = (-row['total_cost'], -int(row['elapsed_age_cost'])) + ties
            row['zero_key'] = (-row['elapsed_increment'], -int(row['elapsed_age_cost'])) + ties
            self.check()
        return index

    def finish_record(self):
        super().finish_record()
        count = len(self.data)
        for name, shape, dtype in (
            ('midpoint_maximum', (p.U,), np.int64), ('endpoint_maximum', (p.U,), np.int64),
            ('elapsed_increment', (), float), ('elapsed_age_cost', (), np.int64),
            ('value_valid', (), bool), ('value_raw', (), float), ('value_clipped', (), float),
            ('value_was_clipped', (), bool), ('total_cost', (), float), ('zero_key', (8,), float),
        ):
            self.record[name] = np.array([row[name] for row in self.data], dtype=dtype).reshape((count,) + shape)
        self.record['keys']['G'] = np.array([row['keys'].get('G', (np.nan,) * 8)
                                                for row in self.data], dtype=float).reshape(count, 8)


class Scheduler:
    def __init__(self, arm, map_packet, clock=time.perf_counter, cpu_clock=time.process_time,
                 *, horizon=p.HORIZON, value=None, perturbation=None):
        if arm not in ('M', 'S', 'G0', 'LR', 'LN') or not isinstance(horizon, (int, np.integer)) or not 8 <= horizon <= 256 or horizon % 4:
            raise ValueError('fixed M/S/G0/LR/LN arm and complete four-tick horizon required')
        if (arm in ('LR', 'LN')) != (value is not None):
            raise ValueError('only learned arms require a frozen value')
        if perturbation is not None and (arm != 'M' or perturbation[0] not in range(0, horizon - 4, 4)):
            raise ValueError('one prebound nonterminal M acquisition perturbation only')
        if perturbation is not None:
            q, mask = perturbation[1]
            if not 0 <= q < 27:
                raise ValueError('invalid perturbation command')
            p.mask_array(mask)
        self.arm, self.sites, self.horizon = arm, p.decode_map(map_packet), int(horizon)
        self.clock, self.cpu_clock, self.value = clock, cpu_clock, value
        self.perturbation = perturbation
        self.execution = ExecutionHistory(self.sites)

    def executed(self, tick, commands, mask):
        self.execution.append(tick, commands, mask)

    def decide(self, own_observation, actual, proposals, tick, current_mask, nav_indices,
               *, started=None, cpu_started=None):
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
                  'observation_peer_links', 'value_queries', 'feature_rows', 'terminal_value_zeros')}
        r = dict(arm=self.arm, tick=int(tick), horizon=self.horizon,
                 history_before=self.execution.next_unsettled, history_after=self.execution.next_unsettled,
                 snapshot_valid=False, decoded_anchor=False, decoded_positions=np.full((p.N, 3), np.nan),
                 decoded_actual=np.zeros((p.N, 3)), decoded_proposals=np.zeros((p.N, 3)),
                 decoded_nav=np.zeros(p.N, np.uint8), report_packets=np.empty((0, p.REPORT.size), np.uint8),
                 command_packet=np.empty(0, np.uint8), requested_pair=np.full(2, -1, np.int64),
                 current={}, branches={}, phase_wall={}, phase_cpu={}, counts=counts,
                 s_pair=np.full(2, -1, np.int64), first_finalists=np.empty((0, 2), np.int64),
                 continuation_used=False, selected_branch=-1, fallback_reason='deadline',
                 m_pair=np.full(2, -1, np.int64), visited_zero_pair=np.full(2, -1, np.int64),
                 value_eligible=False, missing_maximum_m_fallback=False, perturbation_applied=False,
                 c0_pair=np.full(2, -1, np.int64), c1_pair=np.full(2, -1, np.int64),
                 c0_current_q2=-1, c1_current_q2=-1, c0_continuation_q2=-1, c1_continuation_q2=-1,
                 c0_q8=-1, c1_q8=-1, c_diagnostics_valid=False)
        packets, command_packet, selected = (), b'', None
        stages = []
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

        try:
            check()
            with phase('reports'):
                packets = p.encode_reports(own_observation, actual, proposals, tick, nav_indices)
                r['report_packets'] = np.array([np.frombuffer(packet, np.uint8) for packet in packets])
                check()  # Encoding overrun does not create an unreceived anchor.
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
            current = Stage(self, r['current'], positions, actual_wire, proposed_wire, nav_wire,
                             tick, current_mask, self.execution.history, check, counts)
            stages.append(current)
            with phase('current_prefix'):
                current.prepare()
            with phase('current_search'):
                if self.arm == 'S':
                    selected, _ = current.search('S')
                    r['s_pair'] = np.array(selected, np.int64)
                else:
                    o_pair, _ = current.search('O')
                    w_pair, _ = current.search('W')
                    m_pair = max((o_pair, w_pair), key=lambda pair: current.key(pair, 'W'))
                    r['m_pair'] = np.array(m_pair, np.int64)
                    selected = m_pair
                    if self.arm in ('G0', 'LR', 'LN'):
                        if self.execution.start_tick == 0 and self.execution.next_unsettled == tick:
                            g_pair, _ = current.search('G')
                            current.label = 'G'
                            current.score(*m_pair)  # Explicit inclusion; a cached value is reused.
                            selected = max((g_pair, m_pair), key=lambda pair: current.key(pair, 'G'))
                            r['value_eligible'] = True
                            zero_pair = max(current.data, key=lambda row: row['zero_key'])['pair']
                            r['visited_zero_pair'] = np.array(zero_pair, np.int64)
                        else:
                            r['missing_maximum_m_fallback'] = True
                    if self.perturbation is not None and tick == self.perturbation[0]:
                        selected = tuple(self.perturbation[1])
                        r['perturbation_applied'] = True
            current.record['completed'] = True
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
                     history_burden=self.execution.history.burden.copy(),
                     history_maximum=self.execution.history.maximum.copy(), burden_unknown=bool(self.execution.history.burden_unknown))
            for stage in stages:
                stage.finish_record()
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
