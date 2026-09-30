"""Age W and dual O/W search over one causal, privately forecast history.

Physical evaluations are shared; O then W retain their separate 116-request
search order and exact keys. Completed plans survive in diagnostics after a
deadline, but only a complete timely whole-team request can be delivered.
"""

import time

import numpy as np

from envs.pettingzoo.uav_radio import (
    free_space_user_path_loss, greedy_connection_assignment,
    service_metrics, user_sinr_from_path_loss,
)
from experiments.candidates.uav_local_history.b01.controller import COMMANDS
from experiments.candidates.uav_radio_activation.b02.scheduler import rank as native_rank
from experiments.candidates.uav_radio_activation.b03.protocol import (
    ALL_ON, DEADLINE_SECONDS, DELIVERY, HOLD, HORIZON, N, U, LOW, HIGH,
    command_index, decode_command, decode_map, decode_reports, encode_command,
    encode_reports, forecast_positions, mask_array,
)
from experiments.candidates.uav_radio_activation.b03.scheduler import DeadlineExceeded
from experiments.candidates.uav_registered_service.b01.history import ExecutionHistory, age_groups, model
from experiments.candidates.uav_registered_service.b01.scheduler import sequential_search

from .features import model_ages, pack_features


EXTRA_RECORD_FIELDS = (
    'features', 'feature_available', 'feature_availability',
    'o_ordering_keys', 'w_ordering_keys', 'o_key_length', 'w_key_length',
    'candidate_age_costs', 'candidate_endpoint_last', 'prefix_contacts',
    'ordering_requests', 'request_pairs', 'request_orderings', 'request_count',
    'decoded_positions', 'decoded_proposals', 'model_last', 'model_tick', 'prefix_unknown',
    'plan_available', 'plan_pairs', 'plan_commands', 'plan_masks', 'plan_scores',
    'plan_costs', 'plan_o_keys', 'plan_w_keys', 'plan_endpoint_last',
    'plan_endpoint_ages', 'plan_endpoint_unknown',
    'pending_commands', 'pending_mask', 'pending_available',
    'alias', 'sampled', 'actor_weight', 'effective_actor_row', 'sampled_choice',
    'probabilities', 'logp', 'm_choice', 'requested_choice', 'actual_choice',
    'requested_q', 'requested_mask', 'requested_commands', 'requested_available',
    'sampled_late', 'forced_before_sampling', 'forced_reason',
    'feature_wall', 'feature_cpu', 'actor_wall', 'actor_cpu', 'actual_commands', 'actual_mask',
)


def age_cost(prefix, contacts, first_tick):
    """Independent private age reduction, including every post-move tick."""
    private, cost = prefix.copy(), 0
    for offset, served in enumerate(contacts):
        tick = first_tick + offset
        private.update(tick, served)
        cost += int(model_ages(private.last, tick).sum())
    return cost, private.last.copy()


def ordering_w(q, mask, native, cumulative_age, proposal_q):
    return (-int(cumulative_age),) + native_rank(q, mask, native, proposal_q)


def full_plan_alias(commands, masks, available):
    return bool(np.all(available) and masks[0] == masks[1]
                and np.array_equal(commands[0], commands[1]))


class Scheduler:
    def __init__(self, arm, map_packet, clock=time.perf_counter,
                 cpu_clock=time.process_time, *, horizon=HORIZON):
        if arm not in ('W', 'M', 'L') or not isinstance(horizon, (int, np.integer)) or not 8 <= horizon <= HORIZON or horizon % HOLD:
            raise ValueError('W/M/L require a four-tick horizon from8 to256')
        self.arm, self.sites = arm, decode_map(map_packet)
        self.clock, self.cpu_clock, self.horizon = clock, cpu_clock, int(horizon)
        self.execution = ExecutionHistory(self.sites)

    def executed(self, tick, commands, mask):
        self.execution.append(tick, commands, mask)

    def decide(self, own_observation, actual_commands, proposals, tick, current_mask,
               *, started=None, cpu_started=None, selector=None, innovation=None):
        start = self.clock() if started is None else started
        cpu_start = self.cpu_clock() if cpu_started is None else cpu_started
        if tick not in range(0, self.horizon, HOLD) or len(self.execution.actions) != tick:
            raise ValueError('report clock and execution log disagree')
        mask_array(current_mask)
        actual, proposed = np.asarray(actual_commands), np.asarray(proposals)
        if actual.shape != (N, 3) or proposed.shape != (N, 3):
            raise ValueError('expected five actual commands and proposals')
        for command in actual:
            command_index(command)
        member = (tick // HOLD) % N
        proposal_q = command_index(proposed[member])
        length = min(HOLD, self.horizon - tick - DELIVERY)
        scores = np.full((27, 32, 3), np.nan)
        o_keys = np.full((27, 32, U + 7), np.nan)
        w_keys = np.full((27, 32, 7), np.nan)
        contacts = np.zeros((27, 32, length, U), dtype=bool)
        costs = np.full((27, 32), np.nan)
        endpoints = np.full((27, 32, U), -2, dtype=np.int64)
        r = dict(
            reports=(), command_packet=b'', forecast=np.full((27, length, N, 3), np.nan),
            scores=scores, candidate_contacts=contacts, candidate_age_costs=costs,
            candidate_endpoint_last=endpoints, o_ordering_keys=o_keys, w_ordering_keys=w_keys,
            o_key_length=0, w_key_length=7, scored_length=length,
            evaluated_pairs=[], candidate_requests=0, candidate_cache_hits=0,
            candidate_uncached_requests=0, state_reductions=0, prefix_ticks=0,
            ordering_requests=np.zeros(2, dtype=np.int64), request_pairs=[], request_orderings=[],
            history_before=self.execution.next_unsettled, history_after=self.execution.next_unsettled,
            snapshot_valid=False, prefix_valid=False, decoded_anchor=False,
            decoded_positions=np.zeros((N, 3)), decoded_proposals=np.zeros((N, 3)),
            snapshot_last=np.full(U, -2, dtype=np.int64), snapshot_windows=np.zeros((4, U), bool),
            prefix_last=np.full(U, -2, dtype=np.int64), prefix_windows=np.zeros((4, U), bool),
            prefix_unknown=np.zeros(U, bool), prefix_contacts=np.zeros((DELIVERY, U), bool),
            plan_available=np.zeros(2, bool), plan_pairs=np.full((2, 2), -1, dtype=np.int64),
            plan_commands=np.zeros((2, N, 3)), plan_masks=np.zeros(2, dtype=np.int64),
            plan_scores=np.zeros((2, 3)), plan_costs=np.zeros(2),
            plan_o_keys=np.zeros((2, U + 7)), plan_w_keys=np.zeros((2, 7)),
            plan_endpoint_last=np.full((2, U), -2, dtype=np.int64),
            plan_endpoint_ages=np.zeros((2, U)), plan_endpoint_unknown=np.zeros((2, U), bool),
            pending_commands=np.zeros((N, 3)), pending_mask=0, pending_available=False,
            alias=False, sampled=False, actor_weight=0., effective_actor_row=False,
            sampled_choice=-1, probabilities=np.zeros(2), logp=0., m_choice=-1,
            requested_choice=-1, actual_choice=-1, requested_q=-1, requested_mask=-1,
            requested_commands=np.zeros((N, 3)), requested_available=False,
            sampled_late=False, forced_reason='', fallback_reason='deadline',
            history_reductions=0, history_wall=0., history_cpu=0.,
            prefix_wall=0., prefix_cpu=0., candidate_wall=0., candidate_cpu=0.,
            feature_wall=0., feature_cpu=0., actor_wall=0., actor_cpu=0.)
        geometry, selected, feature_vector = {}, None, None
        before_count = len(self.execution.predicted)

        def check():
            if self.clock() - start > DEADLINE_SECONDS:
                raise DeadlineExceeded

        def causal_state():
            history = self.execution.history
            r['history_start'] = -1 if self.execution.start_tick is None else self.execution.start_tick
            r['history_after'] = self.execution.next_unsettled
            r['model_tick'] = self.execution.next_unsettled - 1
            r['model_last'] = history.last.copy()
            r['unknown_age'] = (history.last == -1) & (r['history_start'] > 0)
            r['window_valid'] = np.arange(4) * 64 >= (256 if r['history_start'] < 0 else r['history_start'])

        def features():
            causal_state()
            fs, fc = self.clock(), self.cpu_clock()
            try:
                return pack_features(r, self.sites, actual, current_mask, tick=tick, horizon=self.horizon)
            finally:
                r['feature_wall'] += self.clock() - fs
                r['feature_cpu'] += self.cpu_clock() - fc

        try:
            check()
            r['reports'] = encode_reports(own_observation, actual, proposed, tick)
            check()  # An unreceived encode overrun must not create a position anchor.
            positions, actual_wire, proposed_wire = decode_reports(r['reports'], tick)
            self.execution.anchor(tick, positions)
            r.update(decoded_anchor=True, decoded_positions=positions, decoded_proposals=proposed_wire)
            check()
            hs, hc = self.clock(), self.cpu_clock()
            try:
                _, ready = self.execution.settle(tick, check)
            finally:
                r['history_wall'], r['history_cpu'] = self.clock() - hs, self.cpu_clock() - hc
                r['history_reductions'] = len(self.execution.predicted) - before_count
            if not ready:
                r['fallback_reason'] = 'history_unavailable'
                raise DeadlineExceeded
            settled = self.execution.history.copy()
            r.update(snapshot_valid=True, snapshot_last=settled.last.copy(), snapshot_windows=settled.windows.copy())
            ps, pc = self.clock(), self.cpu_clock()
            try:
                prefix, position = settled.copy(), positions.copy()
                for offset in range(DELIVERY):
                    check()
                    position = np.clip(position + actual_wire * 30., LOW, HIGH)
                    served, _ = model(position, self.sites, current_mask)
                    prefix.update(tick + offset, served)
                    r['prefix_contacts'][offset] = served
                    r['prefix_ticks'] += 1
                    check()
                r.update(prefix_valid=True, prefix_last=prefix.last.copy(), prefix_windows=prefix.windows.copy(),
                         prefix_unknown=(prefix.last == -1) & (prefix.start_tick > 0))
                groups = age_groups(prefix) if self.arm != 'W' else ()
                r['o_key_length'] = len(groups) + 6 if self.arm != 'W' else 0
                r['forecast'] = forecast_positions(positions, actual_wire, proposed_wire, tick, member,
                                                   horizon=self.horizon)
                check()
            finally:
                r['prefix_wall'], r['prefix_cpu'] = self.clock() - ps, self.cpu_clock() - pc

            cs, cc = self.clock(), self.cpu_clock()
            try:
                def score(q, mask):
                    r['candidate_requests'] += 1
                    r['ordering_requests'][ordering_index] += 1
                    r['request_pairs'].append((q, mask))
                    r['request_orderings'].append(ordering_index)
                    if np.isfinite(scores[q, mask, 0]):
                        r['candidate_cache_hits'] += 1
                        return scores[q, mask]
                    r['candidate_uncached_requests'] += 1
                    if q not in geometry:
                        geometry[q] = []
                        for position in r['forecast'][q]:
                            check()
                            geometry[q].append(free_space_user_path_loss(position, self.sites))
                            check()
                    private, cumulative_age = prefix.copy(), 0
                    values, served_rows = [], []
                    for slot, losses in enumerate(geometry[q]):
                        check()
                        sinr = user_sinr_from_path_loss(losses, transmitter_mask=mask_array(mask))
                        connections = greedy_connection_assignment(sinr)
                        metrics = service_metrics(sinr, connections)
                        served = connections.any(axis=0)
                        at_tick = tick + DELIVERY + slot
                        private.update(at_tick, served)
                        cumulative_age += int(model_ages(private.last, at_tick).sum())
                        served_rows.append(served)
                        values.append((metrics['J'], metrics['served'], metrics['quality']))
                        r['state_reductions'] += 1
                        check()
                    native, contact = np.mean(values, axis=0), np.array(served_rows)
                    if self.arm != 'W':
                        distinct = contact.any(axis=0)
                        counts = tuple(int((distinct & group).sum()) for group in groups)
                        o_key = counts + native_rank(q, mask, native, proposal_q)
                    w_key = ordering_w(q, mask, native, cumulative_age, proposal_q)
                    check()
                    scores[q, mask], contacts[q, mask], costs[q, mask] = native, contact, cumulative_age
                    endpoints[q, mask] = private.last
                    if self.arm != 'W':
                        o_keys[q, mask, :r['o_key_length']] = o_key
                    w_keys[q, mask] = w_key
                    r['evaluated_pairs'].append((q, mask))
                    return scores[q, mask]

                for ordering_index in ((1,) if self.arm == 'W' else (0, 1)):
                    matrix = o_keys if ordering_index == 0 else w_keys
                    size = r['o_key_length'] if ordering_index == 0 else 7
                    pair = sequential_search(score, lambda q, mask: tuple(matrix[q, mask, :size]),
                                             current_mask, proposal_q)
                    commands = proposed_wire.copy()
                    commands[member] = COMMANDS[pair[0]]
                    r['plan_pairs'][ordering_index] = pair
                    r['plan_commands'][ordering_index] = commands
                    r['plan_masks'][ordering_index] = pair[1]
                    r['plan_scores'][ordering_index] = scores[pair]
                    r['plan_costs'][ordering_index] = costs[pair]
                    r['plan_o_keys'][ordering_index, :r['o_key_length']] = o_keys[pair][:r['o_key_length']]
                    r['plan_w_keys'][ordering_index] = w_keys[pair]
                    r['plan_endpoint_last'][ordering_index] = endpoints[pair]
                    r['plan_endpoint_ages'][ordering_index] = model_ages(endpoints[pair], tick + DELIVERY + length - 1)
                    r['plan_endpoint_unknown'][ordering_index] = (endpoints[pair] == -1) & (prefix.start_tick > 0)
                    r['plan_available'][ordering_index] = True
                    check()
            finally:
                r['candidate_wall'], r['candidate_cpu'] = self.clock() - cs, self.cpu_clock() - cc

            r['alias'] = full_plan_alias(r['plan_commands'], r['plan_masks'], r['plan_available'])
            if np.all(r['plan_available']):
                r['m_choice'] = max(range(2), key=lambda i: tuple(r['plan_w_keys'][i]))
            feature_vector = features()
            check()  # Packing is deployment work; overrun before sampling has zero actor weight.
            if self.arm == 'L' and not r['alias']:
                if selector is None or innovation is None or not np.isfinite(innovation) or not 0 <= innovation < 1:
                    raise ValueError('distinct L plans need a selector and prebound uniform in [0,1)')
                actor_start, actor_cpu = self.clock(), self.cpu_clock()
                try:
                    probabilities = np.asarray(selector(feature_vector.copy()), dtype=np.float64)
                    if probabilities.shape != (2,) or not np.isfinite(probabilities).all() or np.any(probabilities < 0) or not np.isclose(probabilities.sum(), 1., rtol=0, atol=1e-6):
                        raise ValueError('selector must return two finite probabilities summing to1')
                    probabilities = probabilities / probabilities.sum()
                    probabilities[1] = 1. - probabilities[0]
                    # Record the completed sample before checking inference/deployment time.
                    choice = int(float(innovation) >= probabilities[0])
                    if probabilities[choice] <= 0:
                        raise ValueError('sampled choice has zero probability')
                    r.update(sampled=True, actor_weight=1., effective_actor_row=True,
                             sampled_choice=choice, probabilities=probabilities.copy(),
                             logp=float(np.log(probabilities[choice])))
                finally:
                    r['actor_wall'], r['actor_cpu'] = self.clock() - actor_start, self.cpu_clock() - actor_cpu
            else:
                choice = 1 if self.arm == 'W' else r['m_choice']
                if self.arm == 'L':
                    r['forced_reason'] = 'alias'
            r.update(requested_choice=choice, requested_available=True,
                     requested_commands=r['plan_commands'][choice].copy(),
                     requested_q=int(r['plan_pairs'][choice, 0]), requested_mask=int(r['plan_masks'][choice]))
            check()
            packet = encode_command(r['requested_mask'], member, r['requested_q'], tick)
            received_mask, received_member, received_q = decode_command(packet, tick)
            commands = proposed_wire.copy()
            commands[received_member] = COMMANDS[received_q]
            check()
            selected = (received_q, received_mask)
            r['command_packet'] = packet
        except DeadlineExceeded:
            selected = None

        # Capture forced critic rows from decision-end information; preserve sampling
        # features verbatim even if inference/encoding subsequently missed the deadline.
        causal_state()
        r['alias'] = full_plan_alias(r['plan_commands'], r['plan_masks'], r['plan_available'])
        if np.all(r['plan_available']) and r['m_choice'] < 0:
            r['m_choice'] = max(range(2), key=lambda i: tuple(r['plan_w_keys'][i]))
        if feature_vector is None:
            feature_vector = features()
        choice_index = r['requested_choice'] if r['requested_choice'] >= 0 else (1 if self.arm == 'W' else 0)
        legacy_keys = np.full((27, 32, U + 7), np.nan)
        legacy_size = r['o_key_length'] if choice_index == 0 else 7
        legacy_source = o_keys if choice_index == 0 else w_keys
        legacy_keys[:, :, :legacy_size] = legacy_source[:, :, :legacy_size]
        request_count = len(r['request_pairs'])
        requests = np.full((232, 2), -1, dtype=np.int64)
        orders = np.full(232, -1, dtype=np.int64)
        if request_count:
            requests[:request_count] = r['request_pairs']
            orders[:request_count] = r['request_orderings']
        r.update(request_pairs=requests, request_orderings=orders, request_count=request_count)
        # Include diagnostic packing in deployment timing before the whole-plan
        # delivery decision. Already sampled rows keep their likelihood on a miss.
        elapsed = self.clock() - start
        if elapsed > DEADLINE_SECONDS:
            selected = None
        if selected is None:
            commands, received_mask = actual.copy(), int(current_mask)
            r['command_packet'] = b''
            if not r['sampled']:
                r['forced_reason'] = r['fallback_reason']
        else:
            r['fallback_reason'] = ''
            r['actual_choice'] = r['requested_choice']
        r['sampled_late'] = bool(r['sampled'] and selected is None)
        r['forced_before_sampling'] = bool(self.arm == 'L' and not r['sampled'])
        r['forced_reason'] = np.array(r['forced_reason'], dtype='<U32')
        r.update(commands=commands, mask=received_mask, timely=selected is not None,
                 selected_q=None if selected is None else selected[0],
                 selected_mask=None if selected is None else selected[1],
                 sequential_pair=selected, sequential_score=None if selected is None else scores[selected].copy(),
                 ordering_keys=legacy_keys, key_length=legacy_size,
                 candidate_plans=len(r['evaluated_pairs']),
                 interrupted_candidate_requests=r['candidate_uncached_requests'] - len(r['evaluated_pairs']),
                 geometry_snapshots=sum(map(len, geometry.values())),
                 actual_timeout=elapsed > DEADLINE_SECONDS, wall_seconds=elapsed,
                 cpu_seconds=self.cpu_clock() - cpu_start,
                 recurring_bytes=sum(map(len, r['reports'])) + len(r['command_packet']),
                 features=feature_vector, feature_available=True,
                 feature_availability=np.array([r['decoded_anchor'], r['history_start'] >= 0,
                                                r['prefix_valid'], *r['plan_available']], dtype=bool),
                 actual_commands=actual.copy(), actual_mask=int(current_mask))
        r['extra_record_fields'] = EXTRA_RECORD_FIELDS
        return r
