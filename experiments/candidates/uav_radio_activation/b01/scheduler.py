"""Bounded ordinary mask search from encoded public reports only."""

import time

import numpy as np

from envs.pettingzoo.uav_radio import (
    free_space_user_path_loss, greedy_connection_assignment,
    service_metrics, user_sinr_from_path_loss,
)

from .protocol import (
    ALL_ON, DEADLINE_SECONDS, N, decode_command, decode_map, decode_reports,
    encode_command, encode_reports, forecast_positions, mask_array,
)


class DeadlineExceeded(Exception):
    pass


def rank(mask, score):
    return (float(score[0]), float(score[1]), int(mask).bit_count(), -int(mask))


class Scheduler:
    def __init__(self, arm, map_packet, *, clock=time.perf_counter, cpu_clock=time.process_time):
        if arm not in ('G', 'E'):
            raise ValueError('scheduler arm must be G or E')
        self.arm = arm
        self.sites = decode_map(map_packet)
        self.clock = clock
        self.cpu_clock = cpu_clock

    def decide(self, own_observation, commands, tick, current_mask):
        start = self.clock()
        cpu_start = self.cpu_clock()
        packets = ()
        packet = b''
        trajectory = np.empty((0, N, 3))
        offsets = ()
        scores = np.full((32, 3), np.nan)
        per_state = np.full((32, 4, 3), np.nan)
        evaluated = []
        reductions = 0
        geometries = 0
        chosen = None

        def check():
            if self.clock() - start > DEADLINE_SECONDS:
                raise DeadlineExceeded

        try:
            packets = encode_reports(own_observation, commands, tick)
            positions, velocity = decode_reports(packets, tick)
            check()
            trajectory, offsets = forecast_positions(positions, velocity, tick)
            losses = []
            for predicted in trajectory:
                check()
                losses.append(free_space_user_path_loss(predicted, self.sites))
                geometries += 1
                check()

            def evaluate(mask):
                nonlocal reductions
                check()
                values = []
                for loss in losses:
                    check()
                    sinr = user_sinr_from_path_loss(loss, transmitter_mask=mask_array(mask))
                    connections = greedy_connection_assignment(sinr)
                    metrics = service_metrics(sinr, connections)
                    values.append((metrics['J'], metrics['served'], metrics['quality']))
                    reductions += 1
                    check()
                value = np.asarray(values)
                per_state[mask, :len(offsets)] = value
                scores[mask] = value.mean(axis=0)
                evaluated.append(mask)
                check()
                return scores[mask]

            if self.arm == 'E':
                for mask in range(1, ALL_ON + 1):
                    evaluate(mask)
                chosen = max(evaluated, key=lambda mask: rank(mask, scores[mask]))
            else:
                chosen = ALL_ON
                evaluate(chosen)
                while chosen.bit_count() > 1:
                    removals = sorted(chosen ^ (1 << i) for i in range(N) if chosen & (1 << i))
                    for mask in removals:
                        evaluate(mask)
                    best = max(removals, key=lambda mask: rank(mask, scores[mask]))
                    if rank(best, scores[best]) <= rank(chosen, scores[chosen]):
                        break
                    chosen = best
            check()
            packet = encode_command(chosen, tick)
            decoded = decode_command(packet, tick)
            check()
        except DeadlineExceeded:
            chosen = None
            decoded = current_mask
            packet = b''
        elapsed = self.clock() - start
        # The final check covers clock/return-boundary overhead too.
        if elapsed > DEADLINE_SECONDS:
            chosen = None
            decoded = current_mask
            packet = b''
        return dict(mask=decoded, selected_mask=chosen, timely=chosen is not None,
                    reports=packets, command_packet=packet, forecast=trajectory,
                    offsets=offsets, scores=scores, per_state=per_state,
                    evaluated_masks=evaluated, candidate_plans=len(evaluated),
                    state_reductions=reductions, geometry_snapshots=geometries,
                    wall_seconds=elapsed, cpu_seconds=self.cpu_clock() - cpu_start,
                    recurring_bytes=sum(map(len, packets)) + len(packet))
