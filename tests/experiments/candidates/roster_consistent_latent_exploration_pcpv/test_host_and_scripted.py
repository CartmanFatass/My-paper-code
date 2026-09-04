import hashlib
import itertools

from experiments.candidates.roster_consistent_latent_exploration_pcpv.config import (
    EVAL_CELLS, beacon_positions, demands,
)
from experiments.candidates.roster_consistent_latent_exploration_pcpv.host import (
    EntityState, PublicState, circular_displacement, construct_public_state,
    endpoints, fragmentation, mutate_entities, service_delay,
)
from experiments.candidates.roster_consistent_latent_exploration_pcpv.scripted import (
    coherent_claims, fragmented_claims, run_scripted_episode,
)


def _state(positions, previous, tick=20):
    entities = {i: EntityState(position, claim, 0, False)
                for i, (position, claim) in enumerate(zip(positions, previous))}
    ties = {i: (i + 1) / (len(entities) + 1) for i in entities}
    return PublicState(tick, 1, 1, entities, ties)


def test_host_clocks_demand_signed_tie_and_endpoints():
    assert beacon_positions(0) == (0, 20, 40, 60)
    assert beacon_positions(20) == (5, 25, 45, 65)
    assert demands(5, 20) == (1, 1, 2, 1)
    assert demands(10, 20) == (2, 2, 3, 3)
    assert sum(demands(10, 55)) == 10
    assert circular_displacement(0, 40) == 40
    assert circular_displacement(40, 0) == 40
    u = [1.0] * 56
    u[23:26] = [0.0, 0.0, 0.0]
    result = endpoints(u, [0.25] * 9)
    assert result["tau"] == 3.0
    assert result["U"] == sum(u[20:]) / 36
    assert result["F"] == 0.25


def test_event_order_cleanup_tie_renewal_and_no_identity_feature():
    cell = (5, 10)
    entities = {i: EntityState(i * 3, i % 4, 2, False) for i in range(5)}
    mutate_entities(entities, 10, 0, cell, 7, "fixture")
    assert len(entities) == 10
    newcomers = [entity for entity in entities.values() if entity.newcomer]
    assert len(newcomers) == 5
    assert all(e.previous_claim is None and e.previous_displacement == 0
               for e in newcomers)
    state20 = construct_public_state(entities, 20, True, 0, cell, 7, "fixture")
    state24 = construct_public_state(entities, 24, True, 0, cell, 7, "fixture")
    assert state20.roster_event == 1 and state20.post_boundary == 1
    assert state24.roster_event == 0 and state24.post_boundary == 1
    assert state20.tie_marks != state24.tie_marks
    assert state20.agent_elements().shape == (10, 6)
    assert state20.own_features(state20.angular_order[0]).shape == (8,)
    # Renaming internal dynamics keys cannot enter public serialized state.
    renamed = state20.clone()
    renamed.entities = {key + 1000: value for key, value in renamed.entities.items()}
    renamed.tie_marks = {key + 1000: value for key, value in renamed.tie_marks.items()}
    assert renamed.canonical_bytes() == state20.canonical_bytes()


def _brute_optimum(state, priority):
    order = state.angular_order
    demand = demands(state.n, state.tick)
    best = None
    for assignment in itertools.product(range(4), repeat=state.n):
        if tuple(assignment.count(j) for j in range(4)) != demand:
            continue
        changes = sum(state.entities[key].previous_claim is not None and
                      state.entities[key].previous_claim != beacon
                      for key, beacon in zip(order, assignment))
        delay = sum(service_delay(state.entities[key].position, beacon, state.tick)
                    for key, beacon in zip(order, assignment))
        objective = ((changes, delay, assignment) if priority == "CARRY"
                     else (delay, changes, assignment))
        if best is None or objective < best[0]:
            best = objective, assignment
    return dict(zip(order, best[1]))


def test_exact_scripted_priorities_and_forced_shortfalls_excesses():
    state = _state((3, 17, 39, 57, 71), (0, 0, 1, 2, 3))
    assert coherent_claims(state, "CARRY") == _brute_optimum(state, "CARRY")
    assert coherent_claims(state, "REPLAN") == _brute_optimum(state, "REPLAN")
    fragmented = fragmented_claims(state, churn=True)
    counts = tuple(list(fragmented.values()).count(j) for j in range(4))
    target = demands(5, 20)
    assert counts == (target[0] + 1, target[1] - 1,
                      target[2] + 1, target[3] - 1)
    assert fragmentation(fragmented, 5, 20) == 2 / 5


def test_carry_replan_receive_byte_equal_event_state():
    carry, carry_hash = run_scripted_episode("CARRY", 0, (5, 10), 3)
    replan, replan_hash = run_scripted_episode("REPLAN", 0, (5, 10), 3)
    assert carry_hash == replan_hash
    assert len(carry_hash) == 64
    assert set(carry) == set(replan) == {"tau", "U", "F", "Y"}
