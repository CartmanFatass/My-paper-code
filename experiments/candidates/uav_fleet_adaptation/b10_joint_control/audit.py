"""Scalar physical reconstruction and separate saved-state policy decisions."""
import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.audit import equal, require, _radio
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import original_layout
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.physics import scalar_state
from .contract import JOINT, array_digest
from .reading import episode_metrics
from .reference import Reference


def _schema(raw, horizon, program, training):
    d = horizon // 4
    shapes = dict(positions=(horizon + 1, 5, 3), observations=(horizon, 5, 104), commands=(horizon, 5, 3),
                  reward=(horizon,), served=(horizon,), sinr_quality=(horizon,), sinr=(horizon, 5, 50),
                  peer_sinr=(horizon, 5, 5), connections=(horizon, 5, 50), transmitter_mask=(horizon, 5),
                  terminated=(horizon,), truncated=(horizon,), step_generation=(horizon,), step_path_loss_misses=(horizon,),
                  nav_pre=(d, 5), nav_next=(d, 5), features=(d, 5, 114),
                  probabilities=(d, 5, 54 if program in JOINT else 27),
                  old_decision_mask=(d, 5), installed_mask=(d, 5),
                  refresh_sinr=(d, 5, 50), refresh_peer_sinr=(d, 5, 5), refresh_connections=(d, 5, 50),
                  refresh_observations=(d, 5, 104), initial_users=(50, 2), initial_sinr=(5, 50),
                  initial_peer_sinr=(5, 5), initial_connections=(5, 50), initial_generation=(),
                  terminal_observation=(5, 104), decision_ticks=(d,))
    for key in ("fallback", "action_index", "motion_index", "memo_hit", "n_current", "n_peers", "innovation", "entropy",
                "eligible", "requested_off", "hidden_preferred_off", "off_probability", "motion_entropy", "gate_entropy",
                "logp", "off_score", "off_service", "off_evaluated", "init_logit_max_abs", "init_probability_max_abs",
                "init_tv", "initial_fidelity", "count_all", "prediction_all"):
        shapes[key] = (d, 5)
    for key in ("eligible_agent", "gate_count", "gate_innovation", "gate_prediction", "gate_requested_off", "gate_off",
                "gate_forced", "refresh_generation", "refresh_path_loss_misses"):
        shapes[key] = (d,)
    if program in JOINT:
        shapes.update(logits=(d, 5, 54), prior=(d, 5, 2), prior_logits=(d, 5, 27), prior_hidden=(d, 5, 128))
    else:
        family = "C" if program == "CJ" else program.split("_", 1)[0]
        if family in ("P0", "Bstar0", "Hdirect"):
            shapes.update(logits=(d, 5, 27), hidden=(d, 5, 128))
        if family not in ("P0", "Bstar0"):
            shapes.update(policy_scores=(d, 5, 27), policy_served=(d, 5, 27), c_index=(d, 5))
        if family == "Hdirect":
            shapes["parent_probabilities"] = (d, 5, 27)
    if training:
        shapes.update(critic_states=(d, 116), critic_features=(d, 146), values=(d,), macro_rewards=(d,))
    require(set(raw) == set(shapes), "complete B10 raw field roster")
    booleans = {"connections", "transmitter_mask", "terminated", "truncated", "fallback", "memo_hit", "eligible",
                "requested_off", "hidden_preferred_off", "off_evaluated", "initial_fidelity", "old_decision_mask",
                "installed_mask", "gate_requested_off", "gate_off", "gate_forced", "refresh_connections", "initial_connections"}
    integers = {"served", "step_generation", "step_path_loss_misses", "nav_pre", "nav_next", "action_index", "motion_index",
                "n_current", "n_peers", "eligible_agent", "gate_count", "count_all", "refresh_generation",
                "refresh_path_loss_misses", "initial_generation", "decision_ticks", "c_index"}
    fp32 = {"observations", "commands", "features", "refresh_observations", "terminal_observation", "logits", "hidden",
            "prior_logits", "prior_hidden", "critic_states", "critic_features", "values"}
    for key, shape in shapes.items():
        value = raw[key]
        require(value.shape == shape, key + ": shape")
        dtype = np.bool_ if key in booleans else np.int64 if key in integers else np.float32 if key in fp32 else np.float64
        require(value.dtype == dtype, key + ": dtype")
        if "sinr" not in key or key == "sinr_quality":
            require(np.isfinite(value).all(), key + ": finite")
    equal(raw["decision_ticks"], np.arange(0, horizon, 4), "complete four-tick decision clocks")


def _critic_input(positions, users, tick, horizon, previous, old_mask, eligible):
    native = np.concatenate((positions.ravel(), users.ravel(), [tick / horizon])).astype(np.float32)
    normalized = native.copy()
    xyz = normalized[:15].reshape(5, 3)
    xyz[:, :2] /= 1000.
    xyz[:, 2] = (xyz[:, 2] - 50.) / 100.
    normalized[15:115] /= 1000.
    commitments = np.column_stack((previous, np.zeros(5))).ravel()
    onehot = np.array([float(i == eligible) for i in range(5)], dtype=np.float32)
    return native, np.concatenate((normalized, commitments, old_mask, onehot)).astype(np.float32)


def audit_episode(raw, row, protocol, parent, gate, *, actor=None, critic=None, counts=None, inflight=None):
    counts = {} if counts is None else counts
    training = row["kind"] == "training"
    program, world, horizon = row["program"], row["world"], protocol.horizon
    require(training == (critic is not None) and (program in JOINT) == (actor is not None), "reader checkpoint role")
    _schema(raw, horizon, program, training)
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
    maxima = dict(radio=0., observation=0., reward=0., prediction=0., critic=0., policy=0.)
    mask = np.ones(5, dtype=bool)
    state = scalar_state(positions, users, mask, 0, horizon, counts=counts)
    _radio(raw, "initial_", None, state, maxima)
    navs = [initial_nav(raw["observations"][0, i]) for i in range(5)]
    policies = [Reference(program, parent, gate, actor=actor, world=world, agent=i, sampling_root=row["motion_root"],
                          initial=program == "INIT90" or (training and row["group"] == 0)) for i in range(5)]
    previous = np.zeros((5, 3), dtype=np.float32)
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
            if training:
                native, feature = _critic_input(positions, users, tick, horizon, previous, mask, eligible)
                equal(raw["critic_states"][di], native, "critic physical state")
                equal(raw["critic_features"][di], feature, "critic pre-action old-mask/eligible feature")
                with torch.inference_mode():
                    value = critic(torch.from_numpy(feature).reshape(1, 146)).reshape(-1)[0].item()
                counts["critic_rows"] = counts.get("critic_rows", 0) + 1
                error = abs(value - float(raw["values"][di]))
                require(np.isfinite(value) and error <= 2e-6 * max(1., abs(value)), "saved critic value")
                maxima["critic"] = max(maxima["critic"], error)
            answers = []
            for i, policy in enumerate(policies):
                answer = policy.query(raw["observations"][tick, i].copy(), tick, int(navs[i]))
                answers.append(answer)
                navs[i] = answer["next_nav"]
                for field in ("features", "fallback", "action_index", "motion_index", "memo_hit", "n_current", "n_peers",
                              "innovation", "eligible", "requested_off", "hidden_preferred_off", "off_evaluated", "initial_fidelity"):
                    equal(raw[field][di, i], answer[field], "policy " + field)
                equal(raw["count_all"][di, i], answer["gate_count"], "observed capped count")
                equal(raw["prediction_all"][di, i], answer["gate_prediction"], "frozen gate prediction", tolerance=1e-13)
                for field in ("probabilities", "entropy", "off_probability", "motion_entropy", "gate_entropy",
                              "init_logit_max_abs", "init_probability_max_abs", "init_tv"):
                    equal(raw[field][di, i], answer[field], "policy " + field, tolerance=5e-14)
                    maxima["policy"] = max(maxima["policy"], float(np.abs(raw[field][di, i] - answer[field]).max()))
                equal(raw["logp"][di, i], answer["logp"], "chosen joint/ordinary logp", tolerance=1e-10)
                for field in ("off_score", "off_service"):
                    equal(raw[field][di, i], answer[field], "independent CJ " + field, tolerance=1e-12)
                for field in ("logits", "hidden", "prior", "prior_logits", "prior_hidden"):
                    if field in raw:
                        equal(raw[field][di, i], answer[field], "complete original/saved forward " + field)
                if "policy_scores" in raw:
                    equal(raw["policy_scores"][di, i], answer["scores"], "C ON scores", tolerance=1e-12)
                    equal(raw["policy_served"][di, i], answer["served"], "C ON service")
                    equal(raw["c_index"][di, i], answer["c_index"], "C original choice/nav before gate")
                if "parent_probabilities" in raw:
                    equal(raw["parent_probabilities"][di, i], answer["parent_probabilities"], "Hdirect parent density", tolerance=5e-14)
                expected = COMMANDS[answer["motion_index"]]
                equal(raw["commands"][tick:tick + 4, i], np.tile(expected, (4, 1)), "four held physical commands")
                require(not answer["requested_off"] or i == eligible, "noneligible OFF unavailable")
            equal(raw["nav_next"][di], navs, "navigation update")
            chosen = answers[eligible]
            for key, value in (("gate_count", chosen["gate_count"]), ("gate_innovation", -1.),
                               ("gate_requested_off", chosen["requested_off"]), ("gate_off", chosen["requested_off"]),
                               ("gate_forced", False)):
                equal(raw[key][di], value, "executed gate " + key)
            equal(raw["gate_prediction"][di], chosen["gate_prediction"], "boundary frozen prediction", tolerance=1e-13)
            maxima["prediction"] = max(maxima["prediction"], abs(float(raw["gate_prediction"][di]) - chosen["gate_prediction"]))
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
        previous = raw["commands"][tick].copy()
        state = scalar_state(positions, users, mask, tick + 1, horizon, counts=counts)
        _radio(raw, "", tick, state, maxima)
        equal(raw["served"][tick], state["served"], "native service")
        for key in ("reward", "sinr_quality"):
            equal(raw[key][tick], state[key], "native " + key, tolerance=2e-13)
            maxima["reward"] = max(maxima["reward"], abs(float(raw[key][tick]) - state[key]))
    equal(raw["terminal_observation"], state["observations"], "terminal rows", tolerance=1e-7)
    if training:
        equal(raw["macro_rewards"], raw["reward"].reshape(-1, 4).sum(axis=1), "four-tick training J sums")
    for key, value in episode_metrics(raw).items():
        equal(row[key], value, "episode metric " + key, tolerance=1e-12 if type(value) is float else None)
    policy_counts = sum_counts(p.counters for p in policies)
    require(policy_counts == row["policy_counts"], "complete policy/private-cache work")
    for key, amount in (("saved_episodes", 1), ("saved_native_ticks", horizon), ("policy_requests", horizon // 4 * 5),
                        ("gate_requests", horizon // 4)):
        counts[key] = counts.get(key, 0) + amount
    if inflight is not None:
        inflight.clear()
    return dict(max_abs_errors=maxima, policy_counts=policy_counts)
