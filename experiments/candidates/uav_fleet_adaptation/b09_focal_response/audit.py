"""Complete saved-state, private-policy and training-row reconstruction."""
import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.audit import equal, require
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import original_layout
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.physics import assert_radio_equal, scalar_state
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.reference import _softmax
from .contract import ENDPOINTS, PANELS, ROSTERS, SLOT_PAIRS, array_digest
from .reading import episode_metrics
from .reference import ReferenceMember, decode_law, focal_logits


def schema(raw, horizon, learned, training):
    d = horizon // 4
    shapes = dict(positions=(horizon + 1, 5, 3), observations=(horizon, 5, 104), commands=(horizon, 5, 3),
                  reward=(horizon,), served=(horizon,), sinr_quality=(horizon,), sinr=(horizon, 5, 50),
                  peer_sinr=(horizon, 5, 5), connections=(horizon, 5, 50), transmitter_mask=(horizon, 5),
                  terminated=(horizon,), truncated=(horizon,), step_generation=(horizon,), step_path_loss_misses=(horizon,),
                  history_descriptor=(horizon, 16), history_matches=(horizon, 4), history_delta=(horizon, 4, 3),
                  history_gate_counts=(horizon, 4), history_n_peers=(horizon,),
                  nav_pre=(d, 5), nav_next=(d, 5), features=(d, 5, 114), logits=(d, 5, 27), hidden=(d, 5, 128),
                  probabilities=(d, 5, 27), action_index=(d, 5), fallback=(d, 5), memo_hit=(d, 5),
                  n_current=(d, 5), n_peers=(d, 5), innovation=(d, 5), entropy=(d, 5), logp=(d, 5),
                  policy_scores=(d, 5, 27), policy_served=(d, 5, 27), c_index=(d, 5), parent_probabilities=(d, 5, 27),
                  initial_users=(50, 2), initial_sinr=(5, 50), initial_peer_sinr=(5, 5), initial_connections=(5, 50),
                  initial_generation=(), terminal_observation=(5, 104), decision_ticks=(d,), macro_rewards=(d,))
    if learned:
        shapes.update(contexts=(d, 259), base_logits=(d, 27))
    if training:
        shapes.update(critic_states=(d, 116), critic_features=(d, 136), values=(d,))
    require(set(raw) == set(shapes), "complete B09 raw field roster")
    boolean = {"connections", "transmitter_mask", "terminated", "truncated", "fallback", "memo_hit", "initial_connections"}
    integer = {"served", "step_generation", "step_path_loss_misses", "history_matches", "history_gate_counts", "history_n_peers",
               "nav_pre", "nav_next", "action_index", "n_current", "n_peers", "c_index", "initial_generation", "decision_ticks"}
    fp32 = {"observations", "commands", "history_descriptor", "features", "logits", "hidden", "terminal_observation",
            "contexts", "base_logits", "critic_states", "critic_features", "values"}
    for key, shape in shapes.items():
        value = raw[key]
        dtype = np.bool_ if key in boolean else np.int64 if key in integer else np.float32 if key in fp32 else np.float64
        require(value.shape == shape and value.dtype == dtype, "raw shape/dtype " + key)
        if key not in ("sinr", "peer_sinr", "initial_sinr", "initial_peer_sinr"):
            require(np.isfinite(value).all(), "nonfinite raw " + key)
    equal(raw["decision_ticks"], np.arange(0, horizon, 4), "complete decision clocks")


def _radio(raw, prefix, index, state, maxima):
    for key in ("sinr", "peer_sinr"):
        value = raw[prefix + key] if index is None else raw[prefix + key][index]
        maxima["radio"] = max(maxima["radio"], assert_radio_equal(value, state[key]))
    value = raw[prefix + "connections"] if index is None else raw[prefix + "connections"][index]
    equal(value, state["connections"], "complete greedy association")


def _critic_input(positions, users, tick, previous):
    state = np.concatenate((positions.ravel(), users.ravel(), [tick / 256.])).astype(np.float32)
    features = state.copy()
    xyz = features[:15].reshape(5, 3)
    xyz[:, :2] /= 1000.
    xyz[:, 2] = (xyz[:, 2] - 50.) / 100.
    features[15:115] /= 1000.
    commitments = np.column_stack((previous, np.zeros(5))).ravel()
    return state, np.concatenate((features, commitments)).astype(np.float32)


def audit_episode(raw, row, protocol, actors, *, head_state=None, critic=None, counts=None, inflight=None):
    counts = {} if counts is None else counts
    inflight = {} if inflight is None else inflight
    members = []
    try:
        return _audit_episode(raw, row, protocol, actors, head_state=head_state, critic=critic,
                              counts=counts, inflight=inflight, members=members)
    except BaseException:
        # Properties return copies. Refresh even when ingest/query or its first
        # validation fails after already performing known reference work.
        if members:
            inflight["policy_agents"] = [member.counters for member in members]
        raise


def _audit_episode(raw, row, protocol, actors, *, head_state, critic, counts, inflight, members):
    learned, training = row["ego"] in ENDPOINTS, row["kind"] == "training"
    schema(raw, protocol.horizon, learned, training)
    require(learned == (head_state is not None) and training == (critic is not None), "reader checkpoint role")
    world, horizon = row["world"], protocol.horizon
    panel, tape = row["panel"], row["tape"]
    roster_root = protocol.training_assignment_roots[row["block"]] if training else protocol.evaluation_assignment_root
    motion_root = protocol.training_roots[row["block"]] if training else protocol.evaluation_roots[tape]
    index = int(np.random.default_rng(np.random.SeedSequence([roster_root, world, tape, PANELS.index(panel)])).integers(0, 6))
    first, second = ROSTERS[panel]
    laws = (row["ego"][0] if learned else row["ego"], *(first if i in SLOT_PAIRS[index] else second for i in range(1, 5)))
    require(row["assignment_index"] == index and row["laws"] == list(laws)
            and row["motion_root"] == motion_root and row["assignment_root"] == roster_root, "private assignment/address contract")
    positions, users = original_layout(world)
    equal(raw["positions"][0], positions, "original layout positions")
    equal(raw["initial_users"], users, "original layout users")
    require(row["initial_state_sha256"] == array_digest(positions, users), "initial layout digest")
    equal(raw["step_generation"], raw["initial_generation"] + np.arange(1, horizon + 1), "native physical generations")
    equal(raw["step_path_loss_misses"], np.full(horizon, 260), "native distance slots")
    equal(raw["terminated"], np.arange(horizon) == horizon - 1, "complete terminal clock")
    equal(raw["truncated"], np.zeros(horizon, dtype=bool), "no truncation")
    equal(raw["transmitter_mask"], np.ones((horizon, 5), dtype=bool), "all-on host")
    maxima = dict(radio=0., observation=0., reward=0., critic=0., planner=0.)
    mask = np.ones(5, dtype=bool)
    state = scalar_state(positions, users, mask, 0, 256, counts=counts)
    _radio(raw, "initial_", None, state, maxima)
    navs = [initial_nav(row) for row in raw["observations"][0]]
    members.extend(ReferenceMember(law, actors, world=world, agent=i, root=motion_root,
                                   head_state=head_state if i == 0 else None) for i, law in enumerate(laws))
    sensitivity = {key: [] for key in ("logits", "probabilities", "action_index", "modal_changed", "category_changed",
                                       "physical_changed", "total_variation", "max_abs_logit_change")}
    inflight.update(id=row["id"], policy_agents=[m.counters for m in members], tick=None)
    for tick in range(horizon):
        inflight["tick"] = tick
        equal(raw["observations"][tick], state["observations"], "saved local observations", tolerance=1e-7)
        maxima["observation"] = max(maxima["observation"], float(np.max(np.abs(raw["observations"][tick] - state["observations"]))))
        history = members[0].ingest(raw["observations"][tick, 0].copy(), tick)
        for key in ("descriptor", "matches", "delta", "gate_counts", "n_peers"):
            equal(raw["history_" + key][tick], history[key], "private ego history " + key)
        if tick % 4 == 0:
            d = tick // 4
            equal(raw["nav_pre"][d], navs, "private navigation recurrence")
            if training:
                previous = np.zeros((5, 3), dtype=np.float32) if tick == 0 else raw["commands"][tick - 1]
                native, feature = _critic_input(positions, users, tick, previous)
                equal(raw["critic_states"][d], native, "critic global state")
                equal(raw["critic_features"][d], feature, "critic normalized state/previous commands/expired holds")
                with torch.inference_mode():
                    value = critic(torch.from_numpy(feature).reshape(1, 136)).reshape(-1)[0].item()
                counts["critic_rows"] = counts.get("critic_rows", 0) + 1
                error = abs(value - float(raw["values"][d]))
                # FP32 three-layer critic reconstruction; policy probabilities/categories remain exact.
                require(np.isfinite(value) and error <= 2e-6 * max(1., abs(value)), "saved precollection critic forward")
                maxima["critic"] = max(maxima["critic"], error)
            for i, member in enumerate(members):
                answer = member.query(raw["observations"][tick, i], tick, navs[i])
                navs[i] = int(answer["next_nav"])
                # Publish incurred reference work before an audit may fail.
                inflight["policy_agents"] = [m.counters for m in members]
                for key in ("features", "logits", "hidden", "action_index", "fallback", "memo_hit", "n_current", "n_peers",
                            "innovation", "c_index"):
                    equal(raw[key][d, i], answer[key], "private law " + key)
                for key in ("probabilities", "entropy", "logp", "parent_probabilities"):
                    equal(raw[key][d, i], answer[key], "private density " + key, tolerance=5e-14)
                for saved, source in (("policy_scores", "scores"), ("policy_served", "served")):
                    equal(raw[saved][d, i], answer[source], "planner " + source, tolerance=2e-12)
                    maxima["planner"] = max(maxima["planner"], float(np.max(np.abs(raw[saved][d, i] - answer[source]))))
                command = COMMANDS[answer["action_index"]]
                equal(raw["commands"][tick:tick + 4, i], np.tile(command, (4, 1)), "private four-tick held commands")
                if i == 0 and learned:
                    equal(raw["contexts"][d], answer["context"], "lawful focal context")
                    equal(raw["base_logits"][d], answer["base_logits"], "frozen P0 logits")
                    if row["ego"].startswith("H") and not training:
                        zero = answer["context"].copy()
                        zero[243:] = 0.
                        zero_logits = focal_logits(zero, answer["base_logits"], head_state)
                        counts["history_zero_head_rows"] = counts.get("history_zero_head_rows", 0) + 1
                        zero_probability = _softmax(zero_logits)
                        zero_choice = decode_law(zero_probability, answer["innovation"])
                        zero_path, point = [], positions[0].copy()
                        for _ in range(4):
                            point = np.clip(point + COMMANDS[zero_choice].astype(np.float64) * 30., [0., 0., 50.], [1000., 1000., 150.])
                            zero_path.append(point.copy())
                        values = dict(logits=zero_logits, probabilities=zero_probability, action_index=zero_choice,
                                      modal_changed=bool(zero_logits.argmax() != answer["logits"].argmax()),
                                      category_changed=bool(zero_choice != answer["action_index"]),
                                      physical_changed=not np.array_equal(zero_path, raw["positions"][tick + 1:tick + 5, 0]),
                                      total_variation=float(.5 * np.abs(zero_probability - answer["probabilities"]).sum()),
                                      max_abs_logit_change=float(np.max(np.abs(zero_logits - answer["logits"]))))
                        for key, value in values.items():
                            sensitivity[key].append(value)
            equal(raw["nav_next"][d], navs, "updated private navigation")
        positions = np.clip(positions + raw["commands"][tick].astype(np.float64) * 30., [0., 0., 50.], [1000., 1000., 150.])
        equal(raw["positions"][tick + 1], positions, "native physical moves")
        state = scalar_state(positions, users, mask, tick + 1, 256, counts=counts)
        _radio(raw, "", tick, state, maxima)
        equal(raw["served"][tick], state["served"], "native team service")
        for key in ("reward", "sinr_quality"):
            equal(raw[key][tick], state[key], "native " + key, tolerance=2e-13)
            maxima["reward"] = max(maxima["reward"], abs(float(raw[key][tick]) - state[key]))
    equal(raw["terminal_observation"], state["observations"], "terminal private rows", tolerance=1e-7)
    equal(raw["macro_rewards"], raw["reward"].reshape(-1, 4).sum(axis=-1, dtype=np.float64), "four-step macro rewards")
    for key, value in episode_metrics(raw).items():
        equal(row[key], value, "complete metric " + key, tolerance=1e-12 if type(value) is float else None)
    agent_counts = [m.counters for m in members]
    policy_counts = sum_counts(agent_counts)
    require(agent_counts == row["agent_policy_counts"] and policy_counts == row["policy_counts"], "all private policy/tracker/cache costs")
    require(row["raw_array_bytes"] == sum(value.nbytes for value in raw.values()), "uncompressed evidence bytes")
    counts["saved_episodes"] = counts.get("saved_episodes", 0) + 1
    counts["saved_native_ticks"] = counts.get("saved_native_ticks", 0) + horizon
    counts["policy_requests"] = counts.get("policy_requests", 0) + 5 * horizon // 4
    counts["roster_draws"] = counts.get("roster_draws", 0) + 1
    inflight.clear()
    arrays = {key: np.asarray(value) for key, value in sensitivity.items()} if sensitivity["action_index"] else None
    summary = None if arrays is None else dict(rows=len(arrays["action_index"]),
        modal_changes=int(arrays["modal_changed"].sum()), category_changes=int(arrays["category_changed"].sum()),
        physical_changes=int(arrays["physical_changed"].sum()), mean_total_variation=float(arrays["total_variation"].mean()),
        max_total_variation=float(arrays["total_variation"].max()),
        max_abs_logit_change=float(arrays["max_abs_logit_change"].max()),
        scope="Same observed history/current context and action innovation; no ablated native branch or value estimate.")
    return dict(id=row["id"], max_abs_errors=maxima, policy_counts=policy_counts, history_sensitivity=summary), arrays
