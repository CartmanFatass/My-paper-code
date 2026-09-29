"""Two-tick sequential and exhaustive motion/activation search."""

import time

import numpy as np

from envs.pettingzoo.uav_radio import (
    free_space_user_path_loss, greedy_connection_assignment,
    service_metrics, user_sinr_from_path_loss,
)
from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b02.scheduler import rank, sequential_search

from .protocol import (
    ALL_ON, DEADLINE_SECONDS, DELIVERY, HOLD, HORIZON, N, command_index,
    decode_command, decode_map, decode_reports, encode_command, encode_reports,
    forecast_positions, mask_array,
)


class DeadlineExceeded(Exception):
    pass


class Scheduler:
    def __init__(self, arm, map_packet, clock=time.perf_counter,
                 cpu_clock=time.process_time, *, horizon=HORIZON):
        if arm not in ('S2', 'T2'):
            raise ValueError('scheduler arm must be S2 or T2')
        if not isinstance(horizon, (int, np.integer)) or not 8 <= horizon <= HORIZON or horizon % HOLD:
            raise ValueError('horizon must be a four-tick multiple from 8 to 256')
        self.arm = arm
        self.sites = decode_map(map_packet)
        self.clock = clock
        self.cpu_clock = cpu_clock
        self.horizon = int(horizon)

    def decide(self, own_observation, actual_commands, proposals, tick, current_mask,
               *, started=None, cpu_started=None):
        start = self.clock() if started is None else started
        cpu_start = self.cpu_clock() if cpu_started is None else cpu_started
        if tick not in range(0, self.horizon, HOLD):
            raise ValueError('decision outside the report clock')
        mask_array(current_mask)
        actual = np.asarray(actual_commands)
        proposed = np.asarray(proposals)
        if actual.shape != (N, 3) or proposed.shape != (N, 3):
            raise ValueError('expected five actual commands and five proposals')
        member = (tick // HOLD) % N
        proposal_q = command_index(proposed[member])
        packets = ()
        command_packet = b''
        scored_length = min(HOLD, self.horizon - tick - DELIVERY)
        forecast = np.full((len(COMMANDS), scored_length, N, 3), np.nan)
        scores = np.full((len(COMMANDS), ALL_ON + 1, 3), np.nan)
        evaluated_pairs = []
        geometry = {}
        candidate_requests = 0
        reductions = 0
        prefix_ticks = 0
        selected = None
        sequential_pair = None
        sequential_score = None
        decoded_commands = actual.copy()
        decoded_mask = int(current_mask)

        def check():
            if self.clock() - start > DEADLINE_SECONDS:
                raise DeadlineExceeded

        try:
            check()
            packets = encode_reports(own_observation, actual, proposed, tick)
            positions, actual_wire, proposed_wire = decode_reports(packets, tick)
            check()
            forecast = forecast_positions(positions, actual_wire, proposed_wire,
                                          tick, member, horizon=self.horizon)
            prefix_ticks = DELIVERY
            check()

            def score(q, mask):
                nonlocal candidate_requests, reductions
                candidate_requests += 1
                if not np.isnan(scores[q, mask, 0]):
                    return scores[q, mask]
                if q not in geometry:
                    geometry[q] = []
                    for positions_at_tick in forecast[q]:
                        check()
                        geometry[q].append(free_space_user_path_loss(
                            positions_at_tick, self.sites))
                        check()
                values = []
                for losses in geometry[q]:
                    check()
                    sinr = user_sinr_from_path_loss(losses, transmitter_mask=mask_array(mask))
                    connections = greedy_connection_assignment(sinr)
                    metrics = service_metrics(sinr, connections)
                    values.append((metrics['J'], metrics['served'], metrics['quality']))
                    reductions += 1
                    check()
                scores[q, mask] = np.asarray(values).mean(axis=0)
                evaluated_pairs.append((q, mask))
                check()
                return scores[q, mask]

            if self.arm == 'S2':
                selected = sequential_search(score, current_mask, proposal_q)
                sequential_pair = selected
                sequential_score = scores[selected].copy()
            else:
                for q in range(len(COMMANDS)):
                    for mask in range(1, ALL_ON + 1):
                        score(q, mask)
                selected = max(evaluated_pairs,
                               key=lambda pair: rank(*pair, scores[pair], proposal_q))
                sequential_pair = sequential_search(lambda q, mask: scores[q, mask],
                                                    current_mask, proposal_q)
                sequential_score = scores[sequential_pair].copy()
            check()
            command_packet = encode_command(selected[1], member, selected[0], tick)
            received_mask, received_member, received_q = decode_command(command_packet, tick)
            decoded_commands = proposed_wire.copy()
            decoded_commands[received_member] = COMMANDS[received_q]
            decoded_mask = received_mask
            check()
        except DeadlineExceeded:
            selected = None
            command_packet = b''
            decoded_commands = actual.copy()
            decoded_mask = int(current_mask)

        elapsed = self.clock() - start
        if elapsed > DEADLINE_SECONDS:
            selected = None
            command_packet = b''
            decoded_commands = actual.copy()
            decoded_mask = int(current_mask)
        return dict(commands=decoded_commands, mask=decoded_mask,
                    selected_q=None if selected is None else selected[0],
                    selected_mask=None if selected is None else selected[1],
                    timely=selected is not None, reports=packets,
                    command_packet=command_packet, forecast=forecast, scores=scores,
                    scored_length=scored_length,
                    evaluated_pairs=evaluated_pairs, candidate_plans=len(evaluated_pairs),
                    candidate_requests=candidate_requests, state_reductions=reductions,
                    geometry_snapshots=sum(map(len, geometry.values())),
                    prefix_ticks=prefix_ticks, wall_seconds=elapsed,
                    cpu_seconds=self.cpu_clock() - cpu_start,
                    recurring_bytes=sum(map(len, packets)) + len(command_packet),
                    sequential_pair=sequential_pair, sequential_score=sequential_score)
