"""Complete scalar physics and independent source-row memory recurrence."""
import numpy as np
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.audit import equal, require, _radio
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import original_layout
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.physics import scalar_state
from .contract import array_digest
from .schema import DECISIONS, check
from .reading import episode_metrics
from .reference import Reference

def audit_episode(raw, row, protocol, parent, *, counts=None, inflight=None):
    counts = {} if counts is None else counts
    program, world, horizon = row["program"], row["world"], protocol.horizon
    require(row["kind"] == "evaluation", "fixed-policy evaluation only")
    check(raw, horizon, program)
    positions, users = original_layout(world)
    equal(raw["positions"][0], positions, "original reset positions")
    equal(raw["initial_users"], users, "original reset users")
    require(row["initial_state_sha256"] == array_digest(positions, users), "initial digest")
    initial_generation = int(raw["initial_generation"])
    equal(raw["step_generation"], initial_generation + np.arange(1, horizon + 1), "one generation per tick")
    equal(raw["refresh_generation"], initial_generation + np.arange(0, horizon, 4), "setter reuses generation")
    equal(raw["step_path_loss_misses"], np.full(horizon, 260), "native distance cache counts")
    equal(raw["refresh_path_loss_misses"], np.zeros(horizon // 4, dtype=int), "setter distance reuse")
    equal(raw["terminated"], np.arange(horizon) == horizon - 1, "terminal clock")
    equal(raw["truncated"], np.zeros(horizon, dtype=bool), "no truncation")
    maxima = dict(radio=0., observation=0., reward=0., policy=0.)
    mask = np.ones(5, dtype=bool)
    state = scalar_state(positions, users, mask, 0, horizon, counts=counts)
    _radio(raw, "initial_", None, state, maxima)
    navs = [initial_nav(raw["observations"][0, i]) for i in range(5)]
    policies = [Reference(program, parent, world=world, agent=i, sampling_root=row["motion_root"]) for i in range(5)]
    if inflight is not None:
        inflight.update(id=row["id"], program=program, policy_agents=[p.counters for p in policies])
    for tick in range(horizon):
        if inflight is not None:
            inflight["tick"] = tick
        equal(raw["observations"][tick], state["observations"], "old returned rows", tolerance=1e-7)
        maxima["observation"] = max(maxima["observation"], float(np.abs(raw["observations"][tick] - state["observations"]).max()))
        if tick % 4 == 0:
            di, eligible = tick // 4, (tick // 4) % 5
            equal(raw["old_decision_mask"][di], mask, "decision old mask")
            require(bool(mask[eligible]), "current eligible was transmitting")
            equal(raw["nav_pre"][di], navs, "private navigation recurrence")
            equal(raw["eligible_agent"][di], eligible, "public rotating index")
            answers = []
            for i, policy in enumerate(policies):
                answer = policy.query(raw["observations"][tick, i].copy(), tick, int(navs[i]))
                answers.append(answer)
                navs[i] = answer["next_nav"]
                if answer["memory_consumed"]:
                    require(not mask[i] and not answer["requested_off"] and not answer["c_available"], "consume old-silent row before setter")
                for field in DECISIONS:
                    source={"policy_scores":"scores","policy_served":"served"}.get(field,field)
                    expected_value=answer[source]
                    actual_value=raw[field][di,i]
                    if field in ("features","policy_scores","policy_served","off_score","off_service"):
                        available=answer["off_evaluated"] if field in ("off_score","off_service") else answer["c_available"]
                        if not available:
                            require(np.isnan(actual_value).all(), "independent unavailable " + field)
                            continue
                    tolerance=1e-12 if field in ("policy_scores","off_score","off_service") else 5e-14 if field in ("probabilities","entropy") else None
                    equal(actual_value,expected_value,"independent policy/memory " + field,tolerance=tolerance)
                    if tolerance is not None:
                        maxima["policy"]=max(maxima["policy"],float(np.max(np.abs(actual_value-expected_value))))
                for field in ("logits","hidden","parent_probabilities"):
                    if field in raw:
                        equal(raw[field][di,i],answer[field],"original Hdirect " + field,tolerance=5e-14 if field=="parent_probabilities" else None)
                expected = COMMANDS[answer["motion_index"]]
                equal(raw["commands"][tick:tick + 4, i], np.tile(expected, (4, 1)), "four held physical commands")
                require(not answer["requested_off"] or i == eligible, "noneligible OFF unavailable")
            equal(raw["nav_next"][di], navs, "navigation update")
            chosen = answers[eligible]
            for key, value in (("gate_count_boundary", chosen["gate_count"]), ("gate_innovation", -1.),
                               ("gate_requested_off", chosen["requested_off"]), ("gate_off", chosen["requested_off"]),
                               ("gate_forced", False)):
                equal(raw[key][di], value, "executed gate " + key)
            equal(raw["gate_prediction_boundary"][di], chosen["gate_prediction"], "boundary frozen prediction", tolerance=1e-13)
            mask = np.ones(5, dtype=bool)
            mask[eligible] = not chosen["requested_off"]
            equal(raw["installed_mask"][di], mask, "one installed eligible bit")
            refreshed = scalar_state(positions, users, mask, tick, horizon, counts=counts)
            _radio(raw, "refresh_", di, refreshed, maxima)
            equal(raw["refresh_observations"][di], refreshed["observations"], "discarded decision refresh rows", tolerance=1e-7)
            maxima["observation"] = max(maxima["observation"], float(np.abs(raw["refresh_observations"][di] - refreshed["observations"]).max()))
        equal(raw["transmitter_mask"][tick], mask, "four held mask ticks")
        positions = np.clip(positions + raw["commands"][tick].astype(np.float64) * 30., [0., 0., 50.], [1000., 1000., 150.])
        equal(raw["positions"][tick + 1], positions, "silent and active native motion")
        state = scalar_state(positions, users, mask, tick + 1, horizon, counts=counts)
        _radio(raw, "", tick, state, maxima)
        equal(raw["served"][tick], state["served"], "native service")
        for key in ("reward", "sinr_quality"):
            equal(raw[key][tick], state[key], "native " + key, tolerance=2e-13)
            maxima["reward"] = max(maxima["reward"], abs(float(raw[key][tick]) - state[key]))
    equal(raw["terminal_observation"], state["observations"], "terminal rows", tolerance=1e-7)
    equal(raw["terminal_pending"], [policy.remembered is not None for policy in policies], "independent terminal pending")
    require(int(raw["memory_created"].sum())-int(raw["memory_consumed"].sum())==int(raw["terminal_pending"].sum()), "one-use memory conservation")
    for key, value in episode_metrics(raw).items():
        equal(row[key], value, "episode metric " + key, tolerance=1e-12 if type(value) is float else None)
    policy_counts = sum_counts(p.counters for p in policies)
    require(policy_counts == row["policy_counts"], "complete policy/private-cache work")
    for key, amount in (("saved_episodes", 1), ("saved_native_ticks", horizon), ("policy_requests", horizon // 4 * 5),
                        ("gate_requests", horizon // 4)):
        counts[key] = counts.get(key, 0) + amount
    if inflight is not None:
        inflight.clear()
    events=[]
    for di,agent in np.argwhere(raw["memory_created"]):
        consume_di=di+1
        terminal=consume_di==horizon//4
        event=dict(program=program,world=world,agent=int(agent),origin_tick=int(di*4),origin_decision_index=int(di),
            original_c_index=int(raw["origin_c_index"][di,agent]),issued_index=int(raw["origin_issued_index"][di,agent]),
            stored_index=int(raw["stored_index"][di,agent]),origin_count=int(raw["origin_count"][di,agent]),
            origin_post_nav=int(raw["origin_nav"][di,agent]),terminal_pending=bool(terminal),
            raw_path=row["raw"]["path"])
        if not terminal:
            tick=int(consume_di*4)
            delta=np.diff(raw["positions"][tick:tick+5,agent],axis=0)
            intended=raw["commands"][tick:tick+4,agent].astype(np.float64)*30.
            event.update(consumed_tick=tick,consumed_decision_index=int(consume_di),
                executed_category=int(raw["action_index"][consume_di,agent]),
                consumed_hold_net_displacement_m=delta.sum(axis=0).tolist(),
                consumed_hold_travel_m=float(np.linalg.norm(delta,axis=-1).sum()),
                consumed_hold_moving_ticks=int(np.count_nonzero(np.any(delta!=0.,axis=-1))),
                consumed_hold_clipped_ticks=int(np.count_nonzero(np.any(delta!=intended,axis=-1))))
        events.append(event)
    return dict(max_abs_errors=maxima, policy_counts=policy_counts, memory_events=events)
