"""Deadline-censored common-tape native rollout, only from public state."""
import hashlib
import time

import numpy as np

from . import contract as c
from .ordinary import greedy_action
from .storage import put_state
from .task import PublicState, QueueLedger, candidate_slots, pack_report, pack_reset


def future_tape(state, tape_index, horizon):
    """Include the endpoint arrival used by a nonterminal G tail."""
    times = np.arange(state.tick + c.CONTROL_PERIOD,
                      min(state.tick + horizon, c.LAST_ARRIVAL_TICK) + 1,
                      c.CONTROL_PERIOD, dtype=np.int64)
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(
        c.rng_domain('R', state.world, state.tick // c.CONTROL_PERIOD, tape_index))))
    draws = rng.random((len(times), 4))
    return times, draws < state.probabilities


def state_at(host, original, ledger, slots, tick):
    return PublicState(original.world, tick, original.users, original.rate_codes,
                       host.uav_positions, host.ack(), ledger.counts,
                       ledger.progress, slots, original.pairs)


def cohort_key(state, times, tape, source_identity):
    digest = hashlib.sha256()
    for raw in (source_identity.encode(), int(state.world).to_bytes(8, 'little'), pack_reset(state.users, state.rate_codes),
                pack_report(state), np.asarray(state.pairs, dtype=np.uint8).tobytes(),
                np.asarray(times, dtype='<u2').tobytes(), tape.tobytes()):
        digest.update(len(raw).to_bytes(8, 'little'))
        digest.update(raw)
    return digest.hexdigest()


def search(state, raw_g, trace, publish, source_identity):
    """Publish only complete cohorts; caller owns hard cancellation/reaping."""
    from .native import from_public_state, clone_public_host
    horizon = min(160, c.HORIZON - state.tick)
    candidates = candidate_slots(state)
    trace.add('initial_attempts')
    base = from_public_state(state, event_sink=lambda name, amount: trace.native_event(name, amount))
    put_state(trace.arrays['initial'][0], base.snapshot(), state.counts,
              state.progress, state.active_slots, state.tick)
    trace.add('initial_complete')
    all_scores, cohorts, cache = [], [], {}
    next_branch = 0
    for tape_index in range(4):
        trace.add('tape_attempts')
        times, tape = future_tape(state, tape_index, horizon)
        trace.arrays['tape_times'][tape_index, :len(times)] = times
        trace.arrays['tapes'][tape_index, :len(times)] = tape
        trace.arrays['tape_lengths'][tape_index] = len(times)
        trace.arrays['tape_complete'][tape_index] = 1
        trace.add('tape_draws')
        trace.add('tape_uniforms', int(tape.size))
        key = cohort_key(state, times, tape, source_identity)
        if key in cache:
            previous, scores, branch_ids = cache[key]
            reused = previous
            trace.add('cohorts_reused')
        else:
            arrival_lookup = {int(t): row for t, row in zip(times, tape)}
            scores = np.zeros(4, dtype=np.float64)
            branch_ids = [-1] * 4
            rotation = (state.world + state.tick // 20 + tape_index) % 4
            for action in np.roll(np.arange(4), -rotation):
                action = int(action)
                branch = next_branch
                next_branch += 1
                if branch >= 16:
                    raise RuntimeError('fixed rollout branch ceiling exceeded')
                trace.arrays['branch_action'][branch] = action
                trace.arrays['branch_tape'][branch] = tape_index
                trace.add('clone_attempts')
                host = clone_public_host(base)
                trace.add('clones')
                ledger = QueueLedger.from_public(state.counts, state.progress, state.tick)
                active = state.active_slots.copy()
                pending = candidates[action].copy()
                put_state(trace.arrays['states'][branch, 0], host.snapshot(),
                          ledger.counts, ledger.progress, active, state.tick)
                trace.arrays['rows'][branch] = 1
                for offset in range(horizon):
                    tick = state.tick + offset
                    if offset and offset % 20 == 0:
                        active = pending.copy()
                    arrivals = arrival_lookup.get(tick, np.zeros(4, dtype=bool))
                    trace.arrays['arrivals'][branch, offset] = arrivals
                    charged = ledger.start_tick(tick, arrivals)
                    trace.arrays['tick_cost'][branch, offset] = charged
                    if offset and offset % 20 == 0:
                        public = state_at(host, state, ledger, active, tick)
                        query, costs = trace.g_values(public)
                        trace.arrays['g_links'][branch, offset // 20 - 1] = query
                        pending = candidate_slots(public)[greedy_action(costs)].copy()
                    trace.add('native_attempts')
                    _, _, snap = host.advance(active, state.users)
                    ledger.finish_tick(tick, host.ack())
                    put_state(trace.arrays['states'][branch, offset + 1], snap,
                              ledger.counts, ledger.progress, active, tick + 1)
                    # Payload precedes the integer commit marker.
                    trace.arrays['rows'][branch] = offset + 2
                    trace.add('native_complete')
                end = state.tick + horizon
                if end == c.HORIZON:
                    tail = ledger.terminal_cost()
                else:
                    # The command selected at the last internal boundary is now
                    # active. The end report includes its new arrivals, with the
                    # first residence charge left entirely to the G tail.
                    active = pending.copy()
                    arrivals = arrival_lookup.get(end, np.zeros(4, dtype=bool))
                    trace.arrays['arrivals'][branch, horizon] = arrivals
                    before = ledger.area_cost
                    ledger.start_tick(end, arrivals)
                    public = state_at(host, state, ledger, active, end)
                    query, costs = trace.g_values(public)
                    trace.arrays['g_links'][branch, 8] = query
                    tail = float(np.min(costs))
                    # start_tick is needed for legal head insertion; its charge
                    # belongs to the tail and is not counted a second time.
                    score = before + tail
                if end == c.HORIZON:
                    score = ledger.area_cost + tail
                if not np.isfinite(score):
                    raise FloatingPointError('nonfinite completed rollout score')
                scores[action] = score
                branch_ids[action] = branch
                trace.arrays['branch_cost'][branch] = score
                trace.arrays['branch_complete'][branch] = 1
            reused = None
            cache[key] = (tape_index, scores.copy(), list(branch_ids))
        all_scores.append(scores.copy())
        cohorts.append({'tape': tape_index, 'times': times.tolist(),
                        'bits': tape.astype(int).tolist(), 'input_sha256': key,
                        'reused_cohort': reused, 'branches': list(branch_ids),
                        'costs': scores.tolist()})
        trace.arrays['cohort_reuse'][tape_index] = -1 if reused is None else reused
        trace.arrays['cohort_costs'][tape_index] = scores
        trace.arrays['cohort_branches'][tape_index] = branch_ids
        trace.arrays['cohort_input_sha256'][tape_index] = np.frombuffer(bytes.fromhex(key), dtype=np.uint8)
        trace.arrays['cohort_ready_ns'][tape_index] = time.monotonic_ns()
        trace.arrays['cohort_complete'][tape_index] = 1
        trace.add('cohorts_complete')
        averaged = np.mean(np.stack(all_scores), axis=0, dtype=np.float64)
        action = int(np.lexsort((np.arange(4), raw_g, averaged))[0])
        publish({'action': action, 'command': candidates[action].copy(),
                 'rollout_costs': averaged.copy(), 'cohorts': list(cohorts)})
    return {'cohorts': cohorts, 'initial_native_events': dict(base.event_counts)}
