"""Bounded A/S/M/R decisions on one lawful shared model trajectory."""

from contextlib import contextmanager
import time

import numpy as np

from envs.pettingzoo.uav_radio import (
    free_space_user_path_loss, greedy_connection_assignment,
    service_metrics, user_sinr_from_path_loss,
)
from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b02.scheduler import rank as native_rank
from experiments.candidates.uav_radio_activation.b03.scheduler import DeadlineExceeded
from experiments.candidates.uav_registered_service.b01.history import age_groups
from experiments.candidates.uav_user_waiting.b01.history import ExecutionHistory
from . import protocol as p
from .predictor import clone_controller, controller_nav_index, synthetic_observations


def history_record(history):
    return dict(start_tick=int(history.start_tick), last=history.last.copy(),
                windows=history.windows.copy(), burden=history.burden.copy(),
                burden_unknown=bool(history.burden_unknown))


def cost_keys(q, mask, native, age_cost, q2_cost, burden, counts, proposal_q):
    ties = native_rank(q, mask, native, proposal_q)
    return dict(O=tuple(counts) + ties, W=(-int(age_cost),) + ties,
                S=(-int(q2_cost),) + ties,
                R=(-int(burden.max()), -int(burden.sum(dtype=np.int64))) + ties)


class _Stage:
    """One private prefix and shared-physics finite search, with partial evidence."""

    def __init__(self, scheduler, record, positions, actual, proposals, nav, tick,
                 mask, history, check, counts, *, continuation=False):
        self.scheduler, self.record = scheduler, record
        self.tick, self.mask = int(tick), int(mask)
        self.member = (tick // p.HOLD) % p.N
        self.proposal_q = p.command_index(proposals[self.member])
        self.length = min(p.HOLD, scheduler.horizon - tick - p.DELIVERY)
        self.positions, self.actual, self.proposals = positions.copy(), actual.copy(), proposals.copy()
        self.prefix, self.check, self.counts = history.copy(), check, counts
        self.continuation = continuation
        self.geometry, self.cache, self.data, self.states = {}, {}, [], []
        self.requests, self.request_labels, self.request_indices = [], [], []
        self.label = ''
        self.groups = ()
        record.update(tick=int(tick), length=int(self.length), member=int(self.member),
                      current_mask=int(mask), positions=positions.copy(), actual=actual.copy(),
                      proposals=proposals.copy(), nav=nav.copy(), input_history=history_record(history),
                      prefix_positions=np.full((p.DELIVERY, p.N, 3), np.nan),
                      prefix_contacts=np.zeros((p.DELIVERY, p.U), bool), prefix_count=0,
                      prefix_valid=False, prefix_history=history_record(history),
                      forecast=np.full((27, self.length, p.N, 3), np.nan),
                      geometry_count_by_q=np.zeros(27, np.int64), searches={}, partial={}, completed=False)

    def prepare(self):
        position = self.positions.copy()
        for offset in range(p.DELIVERY):
            self.check()
            position = np.clip(position + self.actual * 30., p.LOW, p.HIGH)
            losses = free_space_user_path_loss(position, self.scheduler.sites)
            sinr = user_sinr_from_path_loss(losses, transmitter_mask=p.mask_array(self.mask))
            contacts = greedy_connection_assignment(sinr).any(axis=0)
            self.prefix.update(self.tick + offset, contacts)
            self.counts['prefix_ticks'] += 1
            self.counts['continuation_prefix_ticks' if self.continuation else 'current_prefix_ticks'] += 1
            self.record['prefix_positions'][offset] = position
            self.record['prefix_contacts'][offset] = contacts
            self.record['prefix_count'] += 1
            self.record['prefix_history'] = history_record(self.prefix)
            self.check()
        self.groups = age_groups(self.prefix)
        self.record['prefix_valid'] = True
        self.record['forecast'] = p.forecast_positions(self.positions, self.actual, self.proposals,
                                                      self.tick, self.member, horizon=self.scheduler.horizon)
        self.check()

    def score(self, q, mask):
        self.requests.append((q, mask))
        self.request_labels.append(self.label)
        self.request_indices.append(-1)
        self.counts['candidate_requests'] += 1
        if (q, mask) in self.cache:
            self.counts['candidate_cache_hits'] += 1
            self.request_indices[-1] = self.cache[q, mask]
            return self.cache[q, mask]
        self.counts['candidate_uncached_requests'] += 1
        partial = dict(pair=np.array([q, mask], np.int64), contacts=np.empty((0, p.U), bool),
                       native=np.empty((0, 3)), age_sum=np.empty(0, np.int64),
                       age_square_sum=np.empty(0, np.int64), history=history_record(self.prefix))
        self.record['partial'] = partial
        if q not in self.geometry:
            self.geometry[q] = []
            for position in self.record['forecast'][q]:
                self.check()
                self.geometry[q].append(free_space_user_path_loss(position, self.scheduler.sites))
                self.counts['geometry_snapshots'] += 1
                self.record['geometry_count_by_q'][q] += 1
                self.check()
        private, midpoint = self.prefix.copy(), None
        values, rows, ages, squares = [], [], [], []
        for slot, losses in enumerate(self.geometry[q]):
            self.check()
            sinr = user_sinr_from_path_loss(losses, transmitter_mask=p.mask_array(mask))
            connections = greedy_connection_assignment(sinr)
            metrics = service_metrics(sinr, connections)
            contact = connections.any(axis=0)
            at_tick = self.tick + p.DELIVERY + slot
            private.update(at_tick, contact)
            age = np.int64(at_tick) - private.last
            rows.append(contact)
            values.append((metrics['J'], metrics['served'], metrics['quality']))
            ages.append(int(age.sum(dtype=np.int64)))
            squares.append(int(np.square(age).sum(dtype=np.int64)))
            if slot == 1:
                midpoint = private.copy()
            self.counts['state_reductions'] += 1
            partial.update(contacts=np.array(rows, bool), native=np.array(values),
                           age_sum=np.array(ages, np.int64), age_square_sum=np.array(squares, np.int64),
                           history=history_record(private))
            self.check()
        native, contact = np.mean(values, axis=0), np.array(rows, bool)
        distinct = contact.any(axis=0)
        grouped = tuple(int((distinct & group).sum()) for group in self.groups)
        keys = cost_keys(q, mask, native, sum(ages), sum(squares), private.burden, grouped, self.proposal_q)
        self.check()
        index = len(self.data)
        self.data.append(dict(pair=(q, mask), native=native, contacts=contact,
                              endpoint_last=private.last.copy(), endpoint_burden=private.burden.copy(),
                              age_sum=ages, age_square_sum=squares, age_cost=sum(ages),
                              q2_cost=sum(squares), keys=keys))
        self.states.append((midpoint, private))
        self.cache[q, mask] = index
        self.request_indices[-1] = index
        self.record['partial'] = {}
        self.counts['candidate_plans'] += 1
        return index

    def key(self, pair, label):
        return self.data[self.cache[pair]]['keys'][label]

    def search(self, label):
        self.label = label
        record = dict(request_start=len(self.requests), request_end=len(self.requests),
                      motion_pair=np.full(2, -1, np.int64), mask_pair=np.full(2, -1, np.int64),
                      selected_pair=np.full(2, -1, np.int64), completed=False)
        self.record['searches'][label] = record

        def choose(pairs):
            best, best_key = None, None
            for pair in pairs:
                self.score(*pair)
                value = self.key(pair, label)
                if best_key is None or value > best_key:
                    best, best_key = pair, value
            return best

        try:
            first_q, _ = choose((q, self.mask) for q in range(27))
            motion = choose((first_q, mask) for mask in range(1, p.ALL_ON + 1))
            record['motion_pair'] = np.array(motion, np.int64)
            _, first_mask = choose((self.proposal_q, mask) for mask in range(1, p.ALL_ON + 1))
            mask = choose((q, first_mask) for q in range(27))
            record['mask_pair'] = np.array(mask, np.int64)
            selected = max((motion, mask), key=lambda pair: self.key(pair, label))
            record.update(selected_pair=np.array(selected, np.int64), completed=True)
            self.check()
            return selected, (motion, mask)
        finally:
            record['request_end'] = len(self.requests)

    def finish_record(self):
        count = len(self.data)
        r = self.record
        r['request_pairs'] = np.array(self.requests, np.int64).reshape(-1, 2)
        r['request_orderings'] = np.array(self.request_labels, dtype='<U1')
        r['request_candidate_index'] = np.array(self.request_indices, np.int64)
        r['evaluated_pairs'] = np.array([row['pair'] for row in self.data], np.int64).reshape(-1, 2)
        for name, shape, dtype in (
            ('native', (3,), float), ('contacts', (self.length, p.U), bool),
            ('endpoint_last', (p.U,), np.int64), ('endpoint_burden', (p.U,), np.int64),
            ('age_sum', (self.length,), np.int64), ('age_square_sum', (self.length,), np.int64),
            ('age_cost', (), np.int64), ('q2_cost', (), np.int64),
        ):
            r[name] = np.array([row[name] for row in self.data], dtype=dtype).reshape((count,) + shape)
        r['keys'] = {label: np.array([row['keys'][label] for row in self.data], dtype=float).reshape(count, width)
                     for label, width in (('O', len(self.groups) + 6), ('W', 7), ('S', 7), ('R', 8))}

    def commands(self, pair):
        result = self.proposals.copy()
        result[self.member] = COMMANDS[pair[0]]
        return result


class Scheduler:
    def __init__(self, arm, map_packet, clock=time.perf_counter,
                 cpu_clock=time.process_time, *, horizon=p.HORIZON):
        if arm not in ('A', 'S', 'M', 'R') or not isinstance(horizon, (int, np.integer)) or not 8 <= horizon <= p.HORIZON or horizon % p.HOLD:
            raise ValueError('A/S/M/R require a four-tick horizon from8to256')
        self.arm, self.sites, self.horizon = arm, p.decode_map(map_packet), int(horizon)
        self.clock, self.cpu_clock = clock, cpu_clock
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
                  'observation_peer_links')}
        r = dict(arm=self.arm, tick=int(tick), horizon=self.horizon,
                 history_before=self.execution.next_unsettled, history_after=self.execution.next_unsettled,
                 snapshot_valid=False, decoded_anchor=False, decoded_positions=np.full((p.N, 3), np.nan),
                 decoded_actual=np.zeros((p.N, 3)), decoded_proposals=np.zeros((p.N, 3)),
                 decoded_nav=np.zeros(p.N, np.uint8), report_packets=np.empty((0, p.REPORT.size), np.uint8),
                 command_packet=np.empty(0, np.uint8), requested_pair=np.full(2, -1, np.int64),
                 current={}, branches={}, phase_wall={}, phase_cpu={}, counts=counts,
                 s_pair=np.full(2, -1, np.int64), first_finalists=np.empty((0, 2), np.int64),
                 continuation_used=False, selected_branch=-1, fallback_reason='deadline',
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
            current = _Stage(self, r['current'], positions, actual_wire, proposed_wire, nav_wire,
                             tick, current_mask, self.execution.history, check, counts)
            stages.append(current)
            with phase('current_prefix'):
                current.prepare()
            with phase('current_search'):
                if self.arm == 'M':
                    o_pair, _ = current.search('O')
                    w_pair, _ = current.search('W')
                    selected = max((o_pair, w_pair), key=lambda pair: current.key(pair, 'W'))
                else:
                    selected, finalists = current.search('R' if self.arm == 'R' else 'S')
                    if self.arm in ('A', 'S'):
                        r['s_pair'] = np.array(selected, np.int64)
                        unique = list(dict.fromkeys(finalists))
                        r['first_finalists'] = np.array(unique, np.int64).reshape(-1, 2)
            current.record['completed'] = True
            if self.arm == 'A' and len(r['first_finalists']) == 2 and tick + p.HOLD < self.horizon:
                r['continuation_used'] = True
                ranked = []
                for number, pair_array in enumerate(r['first_finalists']):
                    pair = tuple(map(int, pair_array))
                    index = current.cache[pair]
                    first = current.data[index]
                    mid_history, end_history = current.states[index]
                    future_tick = tick + p.HOLD
                    future_position = current.record['forecast'][pair[0], 1].copy()
                    first_commands = current.commands(pair)
                    branch = dict(first_pair=np.array(pair, np.int64), current_q2=int(first['q2_cost']),
                                  continuation_q2=-1, q8=-1, completed=False, model_tick=future_tick,
                                  model_positions=future_position.copy(), input_history=history_record(mid_history),
                                  synthetic_observations=np.empty((0, 104), np.float32),
                                  virtual_proposals=np.zeros((p.N, 3)), virtual_nav=np.full(p.N, -1, np.int64),
                                  virtual_c_count=0, virtual_c_counters={}, virtual_diagnostics={},
                                  report_packets=np.empty((0, p.REPORT.size), np.uint8), decoded=False,
                                  decoded_positions=np.full((p.N, 3), np.nan),
                                  decoded_proposals=np.zeros((p.N, 3)), decoded_nav=np.zeros(p.N, np.uint8),
                                  continuation={}, prefix_matches=False)
                    r['branches']['branch_' + str(number)] = branch
                    with phase('branch_' + str(number) + '_observation'):
                        check()
                        observation, work = synthetic_observations(future_position, self.sites, pair[1], future_tick,
                                                                   horizon=self.horizon)
                        branch['synthetic_observations'] = observation
                        counts['synthetic_observations'] += 1
                        for name, value in work.items():
                            counts[name] += value
                        check()
                    with phase('branch_' + str(number) + '_c'):
                        for member in range(p.N):
                            check()
                            clone = clone_controller(int(nav_wire[member]))
                            counts['virtual_c_decisions'] += 1
                            command, diagnostics = clone.act(observation[member], future_tick)
                            branch['virtual_proposals'][member] = command
                            branch['virtual_nav'][member] = controller_nav_index(clone)
                            branch['virtual_c_count'] += 1
                            branch['virtual_diagnostics'][str(member)] = {
                                key: value for key, value in diagnostics.items() if value is not None}
                            for name, value in clone.counters.items():
                                branch['virtual_c_counters'][name] = branch['virtual_c_counters'].get(name, 0) + value
                                count_name = 'virtual_c_' + name
                                # virtual_c_decisions is the started-call count above.
                                if name != 'decisions':
                                    counts[count_name] = counts.get(count_name, 0) + value
                            check()
                    with phase('branch_' + str(number) + '_reports'):
                        synthetic = p.encode_reports(observation[:, :3], first_commands,
                                                     branch['virtual_proposals'], future_tick, branch['virtual_nav'])
                        branch['report_packets'] = np.array([np.frombuffer(packet, np.uint8) for packet in synthetic])
                        counts['synthetic_reports'] += 1
                        check()
                        future_wire, committed, future_proposals, future_nav = p.decode_reports(synthetic, future_tick)
                        if not np.array_equal(future_wire, future_position):
                            raise AssertionError('synthetic report changed integer-grid trajectory')
                        branch.update(decoded=True, decoded_positions=future_wire.copy(),
                                      decoded_proposals=future_proposals.copy(), decoded_nav=future_nav.copy())
                        check()
                    next_stage = _Stage(self, branch['continuation'], future_wire, committed, future_proposals,
                                        future_nav, future_tick, pair[1], mid_history, check, counts, continuation=True)
                    stages.append(next_stage)
                    with phase('branch_' + str(number) + '_prefix'):
                        next_stage.prepare()
                        if not (np.array_equal(next_stage.record['prefix_positions'], current.record['forecast'][pair[0], 2:4])
                                and np.array_equal(next_stage.record['prefix_contacts'], first['contacts'][2:4])
                                and np.array_equal(next_stage.prefix.last, end_history.last)
                                and np.array_equal(next_stage.prefix.windows, end_history.windows)
                                and np.array_equal(next_stage.prefix.burden, end_history.burden)):
                            raise AssertionError('continuation prefix is not the first-block suffix')
                        branch['prefix_matches'] = True
                    with phase('branch_' + str(number) + '_search'):
                        next_pair, _ = next_stage.search('S')
                    next_stage.record['completed'] = True
                    future_q2 = next_stage.data[next_stage.cache[next_pair]]['q2_cost']
                    branch.update(continuation_q2=int(future_q2), q8=int(first['q2_cost'] + future_q2), completed=True)
                    ranked.append((-branch['q8'],) + current.key(pair, 'S'))
                    check()
                winner = max(range(2), key=lambda number: ranked[number])
                selected = tuple(map(int, r['first_finalists'][winner]))
                r['selected_branch'] = winner
                baseline = next(number for number, pair in enumerate(r['first_finalists']) if np.array_equal(pair, r['s_pair']))
                for label, number in (('c0', baseline), ('c1', winner)):
                    branch = r['branches']['branch_' + str(number)]
                    r[label + '_pair'] = branch['first_pair'].copy()
                    for suffix in ('current_q2', 'continuation_q2', 'q8'):
                        r[label + '_' + suffix] = branch[suffix]
                r['c_diagnostics_valid'] = True
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
