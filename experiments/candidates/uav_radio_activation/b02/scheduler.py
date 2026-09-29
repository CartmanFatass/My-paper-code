"""Delayed sequential and exhaustive motion/activation search on public reports."""

import time

import numpy as np

from envs.pettingzoo.uav_radio import (
    free_space_user_path_loss, greedy_connection_assignment,
    service_metrics, user_sinr_from_path_loss,
)
from experiments.candidates.uav_local_history.b01.controller import COMMANDS

from .protocol import (
    ALL_ON, DEADLINE_SECONDS, HOLD, N, command_index, decode_command, decode_map,
    decode_reports, encode_command, encode_reports, forecast_positions, mask_array,
)


class DeadlineExceeded(Exception):
    pass


def rank(q, mask, score, proposal_q):
    return (float(score[0]), float(score[1]), int(q == proposal_q),
            int(mask).bit_count(), -int(mask), -int(q))


def sequential_search(score, current_mask, proposal_q):
    """Run both full-team orders; score(q, mask) may cache or read a matrix."""
    def best_q(mask):
        best = None
        best_rank = None
        best_score = None
        for q in range(len(COMMANDS)):
            value = score(q, mask)
            ordering = rank(q, mask, value, proposal_q)
            if best_rank is None or ordering > best_rank:
                best, best_rank, best_score = q, ordering, value
        return best, best_score

    def best_mask(q):
        best = None
        best_rank = None
        best_score = None
        for mask in range(1, ALL_ON + 1):
            value = score(q, mask)
            ordering = rank(q, mask, value, proposal_q)
            if best_rank is None or ordering > best_rank:
                best, best_rank, best_score = mask, ordering, value
        return best, best_score

    first_q, _ = best_q(current_mask)
    motion_mask, motion_score = best_mask(first_q)
    motion_first = (first_q, motion_mask)
    first_mask, _ = best_mask(proposal_q)
    mask_q, mask_score = best_q(first_mask)
    mask_first = (mask_q, first_mask)
    if rank(*motion_first, motion_score, proposal_q) >= rank(*mask_first, mask_score, proposal_q):
        return motion_first
    return mask_first


class Scheduler:
    def __init__(self, arm, map_packet, clock=time.perf_counter,
                 cpu_clock=time.process_time):
        if arm not in ('S', 'T'):
            raise ValueError('scheduler arm must be S or T')
        self.arm = arm
        self.sites = decode_map(map_packet)
        self.clock = clock
        self.cpu_clock = cpu_clock

    def decide(self, own_observation, actual_commands, proposals, tick, current_mask,
               *, started=None, cpu_started=None):
        start = self.clock() if started is None else started
        cpu_start = self.cpu_clock() if cpu_started is None else cpu_started
        mask_array(current_mask)
        actual = np.asarray(actual_commands)
        proposed = np.asarray(proposals)
        if actual.shape != (N, 3) or proposed.shape != (N, 3):
            raise ValueError('expected five actual commands and five proposals')
        member = (tick // HOLD) % N
        proposal_q = command_index(proposed[member])
        packets = ()
        command_packet = b''
        forecast = np.full((len(COMMANDS), HOLD, N, 3), np.nan)
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
                                          tick, member)
            prefix_ticks = HOLD
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

            if self.arm == 'S':
                selected = sequential_search(score, current_mask, proposal_q)
                sequential_pair = selected
                sequential_score = scores[selected].copy()
            else:
                for q in range(len(COMMANDS)):
                    for mask in range(1, ALL_ON + 1):
                        score(q, mask)
                selected = max(evaluated_pairs,
                               key=lambda pair: rank(*pair, scores[pair], proposal_q))
                # Reading the completed T matrix adds no physics or candidate work.
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
                    evaluated_pairs=evaluated_pairs, candidate_plans=len(evaluated_pairs),
                    candidate_requests=candidate_requests, state_reductions=reductions,
                    geometry_snapshots=sum(map(len, geometry.values())),
                    prefix_ticks=prefix_ticks, wall_seconds=elapsed,
                    cpu_seconds=self.cpu_clock() - cpu_start,
                    recurring_bytes=sum(map(len, packets)) + len(command_packet),
                    sequential_pair=sequential_pair, sequential_score=sequential_score)
