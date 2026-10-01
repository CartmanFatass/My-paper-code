"""Causal cap-two mask selection from the frozen quantized public reports."""

from contextlib import contextmanager
import time

import numpy as np

from envs.pettingzoo.uav_radio import free_space_user_path_loss, user_sinr_from_path_loss
from experiments.candidates.uav_user_waiting.b02 import protocol as p
from experiments.candidates.uav_radio_activation.b03.scheduler import DeadlineExceeded

MASK_MENU = tuple(mask for mask in range(1, 32) if mask.bit_count() <= 2)
KEY_SENTINEL = np.iinfo(np.int64).min


class Scheduler:
    def __init__(self, map_packet, *, horizon=p.HORIZON, clock=time.perf_counter, cpu_clock=time.process_time):
        if not isinstance(horizon, (int, np.integer)) or not 8 <= horizon <= p.HORIZON or horizon % p.HOLD:
            raise ValueError('horizon must be a four-tick multiple from8 to256')
        self.sites = p.decode_map(map_packet)
        self.horizon, self.clock, self.cpu_clock = int(horizon), clock, cpu_clock
        self.last_record = {}

    def _finish_record(self, record):
        record['request_masks'] = np.asarray(MASK_MENU[:record['counts']['candidate_requests']], np.int64)

    def decide(self, own_observation, actual, proposals, tick, current_mask, nav_indices,
               *, started=None, cpu_started=None):
        start = self.clock() if started is None else started
        cpu_start = self.cpu_clock() if cpu_started is None else cpu_started
        self.last_record = {}
        p.report_tick(tick)
        if tick >= self.horizon:
            raise ValueError('report outside configured horizon')
        p.mask_array(current_mask)
        length = min(p.HOLD, self.horizon - int(tick) - p.DELIVERY)
        size = max(0, length)
        counts = dict.fromkeys(('candidate_requests', 'candidate_plans', 'state_reductions',
            'geometry_attempts', 'geometry_snapshots', 'geometry_link_entries',
            'radio_calls_attempted', 'radio_calls_completed', 'sinr_link_entries',
            'prefix_attempts', 'prefix_ticks', 'forecast_ticks'), 0)
        record = dict(tick=int(tick), horizon=self.horizon, length=length, member=(int(tick)//p.HOLD)%p.N,
            current_mask=int(current_mask), report_packets=np.empty((0, p.REPORT.size), np.uint8),
            command_packet=np.empty(0, np.uint8), delivered_command_packet=np.empty(0, np.uint8),
            decoded=False, decoded_positions=np.full((p.N, 3), np.nan), decoded_actual=np.full((p.N, 3), np.nan),
            decoded_proposals=np.full((p.N, 3), np.nan), decoded_nav=np.full(p.N, -1, np.int64),
            prefix_positions=np.full((p.DELIVERY, p.N, 3), np.nan), prefix_count=0,
            forecast=np.full((size, p.N, 3), np.nan), forecast_count=0, mask_menu=np.asarray(MASK_MENU, np.int64),
            eligible_counts=np.full((len(MASK_MENU), size, p.N), -1, np.int64),
            completed_slots=np.zeros(len(MASK_MENU), np.int64), distinct_users=np.zeros((len(MASK_MENU), p.U), bool),
            keys=np.full((len(MASK_MENU), 4), KEY_SENTINEL, np.int64),
            candidate_completed=np.zeros(len(MASK_MENU), bool), request_masks=np.empty(0, np.int64),
            selected_mask=-1, selected_index=-1, requested_q=-1, requested_mask=-1,
            completed_calculation=False, timely=False, actual_timeout=False, fallback_reason='deadline',
            returned_commands=np.full((p.N, 3), np.nan), returned_mask=int(current_mask),
            phase_wall={}, phase_cpu={}, counts=counts, partial={}, wall_seconds=0., cpu_seconds=0.)
        self.last_record = record
        packets, delivered, selected = (), b'', False
        returned, mask = np.asarray(actual).copy(), current_mask

        def check():
            if self.clock() - start > p.DEADLINE_SECONDS:
                raise DeadlineExceeded

        @contextmanager
        def phase(name):
            wall, cpu = self.clock(), self.cpu_clock()
            try:
                yield
            finally:
                record['phase_wall'][name] = self.clock() - wall
                record['phase_cpu'][name] = self.cpu_clock() - cpu

        try:
            p.report_tick(tick)
            if tick >= self.horizon:
                raise ValueError('report outside configured horizon')
            p.mask_array(current_mask)
            actual, proposals, nav_indices = p.commands(actual), p.commands(proposals), p.navigation(nav_indices)
            own = np.asarray(own_observation)
            if own.shape != (p.N, 3) or not np.isfinite(own).all():
                raise ValueError('only five finite own-position rows may be reported')
            rounded = np.rint(own.astype(np.float64) * (1000., 1000., 100.) + (0., 0., 50.))
            if np.any(rounded < p.LOW) or np.any(rounded > p.HIGH):
                raise ValueError('report position outside native bounds')
            returned = actual.copy()
            record['returned_commands'] = returned.copy()
            check()
            with phase('reports'):
                record['partial'] = dict(phase='reports')
                packets = p.encode_reports(own_observation, actual, proposals, tick, nav_indices)
                record['report_packets'] = np.asarray([np.frombuffer(packet, np.uint8) for packet in packets])
                check()
                positions, actual_wire, proposed_wire, nav_wire = p.decode_reports(packets, tick)
                record.update(decoded=True, decoded_positions=positions.copy(), decoded_actual=actual_wire.copy(),
                              decoded_proposals=proposed_wire.copy(), decoded_nav=nav_wire.copy(),
                              requested_q=p.command_index(proposed_wire[record['member']]), partial={})
                check()
            with phase('prefix'):
                for offset in range(p.DELIVERY):
                    check()
                    record['partial'] = dict(phase='prefix', slot=offset)
                    counts['prefix_attempts'] += 1
                    positions = np.clip(positions + 30.*actual_wire, p.LOW, p.HIGH)
                    record['prefix_positions'][offset] = positions
                    record['prefix_count'] += 1
                    counts['prefix_ticks'] += 1
                    record['partial'] = {}
                    check()
            with phase('geometry'):
                geometry = []
                for slot in range(length):
                    check()
                    record['partial'] = dict(phase='geometry', slot=slot, geometry_returned=False)
                    positions = np.clip(positions + 30.*proposed_wire, p.LOW, p.HIGH)
                    record['forecast'][slot] = positions
                    record['forecast_count'] += 1
                    counts['forecast_ticks'] += 1
                    counts['geometry_attempts'] += 1
                    counts['geometry_link_entries'] += p.N*p.U
                    losses = free_space_user_path_loss(positions, self.sites)
                    counts['geometry_snapshots'] += 1
                    record['partial']['geometry_returned'] = True
                    losses = np.asarray(losses)
                    if losses.shape != (p.N, p.U) or not np.isfinite(losses).all():
                        raise ValueError('invalid modeled geometry')
                    geometry.append(losses)
                    record['partial'] = {}
                    check()
            with phase('candidates'):
                for index, candidate in enumerate(MASK_MENU):
                    check()
                    counts['candidate_requests'] += 1
                    record['partial'] = dict(phase='candidate', mask_index=index, mask=candidate, slot=0)
                    active = p.mask_array(candidate)
                    for slot, losses in enumerate(geometry):
                        check()
                        partial = dict(phase='radio', mask_index=index, mask=candidate, slot=slot, radio_returned=False,
                                       eligible_counts=np.full(p.N, -1, np.int64), multiplicity=np.full(p.U, -1, np.int64))
                        record['partial'] = partial
                        counts['radio_calls_attempted'] += 1
                        counts['sinr_link_entries'] += p.N*p.U
                        values = user_sinr_from_path_loss(losses, transmitter_mask=active)
                        counts['radio_calls_completed'] += 1
                        partial['radio_returned'] = True
                        values = np.asarray(values)
                        if values.shape != (p.N, p.U) or not np.isfinite(values[active]).all() or not np.isneginf(values[~active]).all():
                            raise ValueError('invalid modeled SINR or inactive rows')
                        eligible = values >= 3.
                        row_counts = eligible.sum(axis=1, dtype=np.int64)
                        multiplicity = eligible.sum(axis=0, dtype=np.int64)
                        partial.update(eligible_counts=row_counts.copy(), multiplicity=multiplicity.copy())
                        if np.any(multiplicity > 1):
                            raise ValueError('modeled eligibility must be disjoint across UAVs')
                        record['eligible_counts'][index, slot] = row_counts
                        record['distinct_users'][index] |= eligible.any(axis=0)
                        record['completed_slots'][index] += 1
                        counts['state_reductions'] += 1
                        record['partial'] = dict(phase='candidate', mask_index=index, mask=candidate, slot=slot+1)
                        check()
                    total = int(np.minimum(10, record['eligible_counts'][index]).sum(dtype=np.int64))
                    distinct = int(record['distinct_users'][index].sum())
                    record['keys'][index] = (total, distinct, -(candidate ^ int(current_mask)).bit_count(), -candidate)
                    record['candidate_completed'][index] = True
                    counts['candidate_plans'] += 1
                    record['partial'] = {}
                    check()
            with phase('ranking'):
                check()
                index = max(range(len(MASK_MENU)), key=lambda i: tuple(record['keys'][i]))
                record.update(selected_index=index, selected_mask=MASK_MENU[index], requested_mask=MASK_MENU[index],
                              completed_calculation=True)
                check()
            with phase('command'):
                record['partial'] = dict(phase='command', mask=record['requested_mask'], q=record['requested_q'])
                check()
                delivered = p.encode_command(record['requested_mask'], record['member'], record['requested_q'], tick)
                record['command_packet'] = np.frombuffer(delivered, np.uint8).copy()
                mask, member, q = p.decode_command(delivered, tick)
                if (mask, member, q) != (record['requested_mask'], record['member'], record['requested_q']):
                    raise ValueError('command changed calculated program')
                returned = proposed_wire.copy()
                selected = True
                record['partial'] = {}
                check()
        except DeadlineExceeded:
            selected = False
        except Exception as exc:
            record.update(fallback_reason='exception', failure_type=type(exc).__name__, failure_message=str(exc))
            raise
        finally:
            self._finish_record(record)
            record['wall_seconds'] = self.clock() - start
            record['cpu_seconds'] = self.cpu_clock() - cpu_start
            record['actual_timeout'] = record['wall_seconds'] > p.DEADLINE_SECONDS
        if not selected:
            returned, mask, delivered = actual.copy(), int(current_mask), b''
        record.update(returned_commands=returned.copy(), returned_mask=int(mask), timely=selected,
                      delivered_command_packet=np.frombuffer(delivered, np.uint8).copy(),
                      fallback_reason='' if selected else 'deadline')
        arrival = dict(commands=returned, mask=int(mask), timely=selected,
            selected_q=record['requested_q'] if selected else None, selected_mask=int(mask) if selected else None,
            reports=packets, command_packet=delivered, recurring_bytes=sum(map(len, packets))+len(delivered),
            counts=counts, record=record, **{key: counts[key] for key in (
                'candidate_requests', 'candidate_plans', 'state_reductions', 'geometry_snapshots', 'prefix_ticks')})
        elapsed, cpu_elapsed = self.clock() - start, self.cpu_clock() - cpu_start
        record.update(actual_timeout=elapsed > p.DEADLINE_SECONDS, wall_seconds=elapsed, cpu_seconds=cpu_elapsed)
        if elapsed > p.DEADLINE_SECONDS:
            returned, mask, delivered = actual.copy(), int(current_mask), b''
            record.update(returned_commands=returned.copy(), returned_mask=mask, timely=False, fallback_reason='deadline',
                          delivered_command_packet=np.empty(0, np.uint8))
            arrival.update(commands=returned, mask=mask, timely=False, selected_q=None, selected_mask=None,
                           command_packet=delivered, recurring_bytes=sum(map(len, packets)))
        arrival.update(wall_seconds=elapsed, cpu_seconds=cpu_elapsed, scheduler_wall=elapsed, scheduler_cpu=cpu_elapsed)
        return arrival
