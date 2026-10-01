"""Frozen S generation/timing with private modeled B05 LRS local state."""

from contextlib import contextmanager
import time

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_registered_service.b01.history import age_groups
from experiments.candidates.uav_user_waiting.b02 import protocol as p
from experiments.candidates.uav_user_waiting.b02.scheduler import (
    DeadlineExceeded, Scheduler as FrozenScheduler, _Stage, cost_keys,
)
from .history import (ExecutionHistory, WORK_KEYS, advance, free_space_user_path_loss,
                      history_record, model)


class Stage(_Stage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record.update(input_history=history_record(self.prefix), prefix_history=history_record(self.prefix),
                           prefix_grants=np.full((p.DELIVERY, p.N, 10), -1, np.int8), prefix_partial={})

    def prepare(self):
        position = self.positions.copy()
        for offset in range(p.DELIVERY):
            self.check()
            position = np.clip(position + self.actual * 30., p.LOW, p.HIGH)
            partial = dict(tick=self.tick + offset, mask=self.mask, positions=position.copy(),
                           input_history=history_record(self.prefix), grants=np.full((p.N, 10), -1, np.int8), completed_rows=0)
            self.record['prefix_partial'] = partial
            self.prefix, connections, _, grants = model(position, self.scheduler.sites, self.mask,
                self.prefix, self.tick + offset, work=self.counts, partial=partial)
            contacts = connections.any(axis=0)
            self.counts['prefix_ticks'] += 1
            self.counts['current_prefix_ticks'] += 1
            self.record['prefix_positions'][offset] = position
            self.record['prefix_contacts'][offset] = contacts
            self.record['prefix_grants'][offset] = grants
            self.record['prefix_count'] += 1
            self.record['prefix_history'] = history_record(self.prefix)
            self.record['prefix_partial'] = {}
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
                       native=np.empty((0, 3)), age_sum=np.empty(0, np.int64), age_square_sum=np.empty(0, np.int64),
                       history=history_record(self.prefix), grants=np.empty((0, p.N, 10), np.int8), row_partial={})
        self.record['partial'] = partial
        if q not in self.geometry:
            self.geometry[q] = []
            for position in self.record['forecast'][q]:
                self.check()
                self.counts['model_geometry_snapshots'] += 1
                self.geometry[q].append(free_space_user_path_loss(position, self.scheduler.sites))
                self.counts['geometry_snapshots'] += 1
                self.record['geometry_count_by_q'][q] += 1
                self.check()
        private, midpoint = self.prefix.copy(), None
        values, rows, grants_rows, ages, squares = [], [], [], [], []
        for slot, losses in enumerate(self.geometry[q]):
            self.check()
            at_tick = self.tick + p.DELIVERY + slot
            row_partial = dict(tick=at_tick, mask=int(mask), positions=self.record['forecast'][q, slot].copy(),
                input_history=history_record(private), grants=np.full((p.N, 10), -1, np.int8), completed_rows=0)
            partial['row_partial'] = row_partial
            private, connections, native, grants = advance(private, at_tick, losses, mask,
                                                          work=self.counts, partial=row_partial)
            contact = connections.any(axis=0)
            age = np.int64(at_tick) - private.last
            rows.append(contact)
            grants_rows.append(grants)
            values.append(native)
            ages.append(int(age.sum(dtype=np.int64)))
            squares.append(int(np.square(age).sum(dtype=np.int64)))
            if slot == 1:
                midpoint = private.copy()
            self.counts['state_reductions'] += 1
            partial.update(contacts=np.array(rows, bool), native=np.array(values), grants=np.array(grants_rows, np.int8),
                           age_sum=np.array(ages, np.int64), age_square_sum=np.array(squares, np.int64),
                           history=history_record(private), row_partial={})
            self.check()
        native, contact = np.mean(values, axis=0), np.array(rows, bool)
        distinct = contact.any(axis=0)
        grouped = tuple(int((distinct & group).sum()) for group in self.groups)
        keys = cost_keys(q, mask, native, sum(ages), sum(squares), private.burden, grouped, self.proposal_q)
        self.check()
        index = len(self.data)
        self.data.append(dict(pair=(q, mask), native=native, contacts=contact, grants=grants_rows,
                              endpoint_last=private.last.copy(), endpoint_burden=private.burden.copy(),
                              age_sum=ages, age_square_sum=squares, age_cost=sum(ages), q2_cost=sum(squares), keys=keys))
        self.states.append((midpoint, private))
        self.cache[q, mask] = index
        self.request_indices[-1] = index
        self.record['partial'] = {}
        self.counts['candidate_plans'] += 1
        return index

    def finish_record(self):
        super().finish_record()
        self.record['candidate_grants'] = np.array([row['grants'] for row in self.data], np.int8).reshape(
            len(self.data), self.length, p.N, 10)


class Scheduler(FrozenScheduler):
    def __init__(self, arm, map_packet, clock=time.perf_counter, cpu_clock=time.process_time, *, horizon=p.HORIZON):
        if arm != 'S':
            raise ValueError('modeled LRS planner accepts frozen collector arm S only')
        super().__init__(arm, map_packet, clock, cpu_clock, horizon=horizon)
        self.execution = ExecutionHistory(self.sites)
        self.last_record = {}

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
                  'observation_peer_links') + WORK_KEYS}
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
        self.last_record = r  # Retain partial candidate evidence if a nondeadline error propagates.
        packets, command_packet, selected = (), b'', None
        current = None
        before_count = len(self.execution.predicted)
        before_work = self.execution.work_counts.copy()

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
            current = Stage(self, r['current'], positions, actual_wire, proposed_wire, nav_wire,
                            tick, current_mask, self.execution.history, check, counts)
            with phase('current_prefix'):
                current.prepare()
            with phase('current_search'):
                selected, finalists = current.search('S')
                r['s_pair'] = np.array(selected, np.int64)
                r['first_finalists'] = np.array(list(dict.fromkeys(finalists)), np.int64).reshape(-1, 2)
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
        except Exception as exc:
            r.update(decision_failure_type=type(exc).__name__, decision_failure_message=str(exc))
            raise
        finally:
            counts['history_reductions'] = len(self.execution.predicted) - before_count
            counts['interrupted_candidate_requests'] = counts['candidate_uncached_requests'] - counts['candidate_plans']
            for key in WORK_KEYS:
                difference = self.execution.work_counts[key] - before_work[key]
                counts['history_' + key] = difference
                counts[key] += difference
            r.update(history_after=self.execution.next_unsettled,
                     history_start=-1 if self.execution.start_tick is None else self.execution.start_tick,
                     history_last=self.execution.history.last.copy(), history_windows=self.execution.history.windows.copy(),
                     history_burden=self.execution.history.burden.copy(), burden_unknown=bool(self.execution.history.burden_unknown),
                     history_last_grant=self.execution.history.last_grant.copy(),
                     settlement_partial=self.execution.settlement_partial)
            if current is not None:
                current.finish_record()
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
