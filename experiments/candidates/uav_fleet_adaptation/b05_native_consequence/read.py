"""One priced B05 read: full saved provenance, partial neural replay, no fits."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if __package__ in (None, ""):
    __package__ = "experiments.candidates.uav_fleet_adaptation.b05_native_consequence"

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, WAYPOINTS
from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest, movement
from experiments.candidates.uav_fleet_adaptation.b02.policies import categorical_index, indexed_uniform
from experiments.candidates.uav_fleet_adaptation.b02.read import equal, identity, own_position, check_memo, saved_ranking_choice
from experiments.candidates.uav_fleet_adaptation.b02.reading import episode_metrics
from experiments.candidates.uav_fleet_adaptation.b04_native_development.read import _array, _finite_tree, _probabilities, _entropy
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from .assets import load_initial_assets, verify_initial_assets
from .contract import CALIBRATION_SOURCE, FROZEN, HEADS, INITIAL_ASSETS, OBJECT, Protocol, array_digest, policy_identity, source_identities
from .learning import DATA_KEYS, Head
from .policies import frozen_forward
from .reading import acquisition_summary, comparisons, validate_counts


def _forward(actor, feature, protocol, work, category):
    limit = sum(map(len, protocol.acquisition_worlds)) + (
        4 * len(protocol.evaluation_worlds[0]) + 3 * len(protocol.evaluation_worlds[1])) * protocol.horizon // 4 * 5
    if work["backbone_rows"] >= limit:
        raise AssertionError("reader backbone scope exceeded")
    work["backbone_rows"] += 1
    work[category] += 1
    return frozen_forward(actor, feature)


def _shadow(raw, row, protocol, work):
    d = protocol.horizon // 4
    motion_limit = 2 * sum(map(len, protocol.evaluation_worlds)) * protocol.horizon * 5
    p = _probabilities(raw["base_logits"])
    equal(_array(raw, "shadow_probabilities", (d, 5, 27), np.float64), p, "shadow density", 2e-16)
    actions = _array(raw, "shadow_action_index", (d, 5), np.int64)
    if np.any((actions < 0) | (actions >= 27)):
        raise AssertionError("invalid shadow category")
    for di in range(d):
        for i in range(5):
            equal(actions[di, i], categorical_index(p[di, i], raw["innovation"][di, i]), "same-uniform S shadow")
    path = []
    for di in range(d):
        position, ticks = raw["positions"][4 * di].copy(), []
        for _ in range(4):
            if work["shadow_motion_ticks"] + 5 > motion_limit:
                raise AssertionError("reader shadow motion scope exceeded")
            position = np.clip(position + COMMANDS[actions[di]].astype(np.float64) * 30.,
                               [0., 0., 50.], [1000., 1000., 150.])
            ticks.append(position.copy())
            work["shadow_motion_ticks"] += 5
        path.append(ticks)
    equal(_array(raw, "shadow_positions", (d, 4, 5, 3), np.float64), path, "shadow geometry")
    requested = actions != raw["action_index"]
    physical = np.any(np.asarray(path) != raw["positions"][1:].reshape(d, 4, 5, 3), axis=(1, 3))
    modal = raw["base_logits"].argmax(-1) != raw["logits"].argmax(-1)
    tv = .5 * np.abs(p - raw["probabilities"]).sum(-1)
    for key, value in (("requested_change", requested), ("physical_change", physical),
                       ("modal_change", modal), ("total_variation", tv)):
        equal(_array(raw, "shadow_" + key, (d, 5), np.float64 if key == "total_variation" else bool),
              value, "shadow " + key, 2e-16)
    expected = dict(rows=d * 5, requested_changes=int(requested.sum()), physical_changes=int(physical.sum()),
                    modal_changes=int(modal.sum()), total_variation_mean=float(tv.mean()), total_variation_max=float(tv.max()))
    if row["shadow"] != expected:
        raise AssertionError("shadow summary changed")


def _episode(raw, row, protocol, actor, head, work):
    h, d = protocol.horizon, protocol.horizon // 4
    acquisition, ordinary = row["kind"] == "acquisition", row["arm"] in ("C", "Q")
    shapes = dict(observations=((h, 5, 104), np.float32), commands=((h, 5, 3), np.float32),
                  positions=((h + 1, 5, 3), np.float64), reward=((h,), np.float64), served=((h,), np.int64),
                  sinr_quality=((h,), np.float64), sinr=((h, 5, 50), np.float64), connections=((h, 5, 50), bool),
                  transmitter_mask=((h, 5), bool), features=((d, 5, 114), np.float32),
                  terminal_observation=((5, 104), np.float32), nav_pre=((d, 5), np.int64),
                  nav_next=((d, 5), np.int64), fallback=((d, 5), bool), action_index=((d, 5), np.int64),
                  nominal_action_index=((d, 5), np.int64), memo_hit=((d, 5), bool), n_current=((d, 5), np.int64),
                  n_peers=((d, 5), np.int64), initial_users=((50, 2), np.float64),
                  decision_ticks=((d,), np.int64), probabilities=((d, 5, 27), np.float64),
                  innovation=((d, 5), np.float64), entropy=((d, 5), np.float64),
                  behavior_entropy=((d, 5), np.float64), chosen_probability=((d, 5), np.float64), logp=((d, 5), np.float64))
    if ordinary:
        shapes.update(c_index=((d, 5), np.int64), policy_scores=((d, 5, 27), np.float64),
                      policy_served=((d, 5, 27), None))
    else:
        shapes["logits"] = ((d, 5, 27), np.float32)
    if head is not None:
        shapes.update(base_logits=((d, 5, 27), np.float32), shadow_probabilities=((d, 5, 27), np.float64),
                      shadow_action_index=((d, 5), np.int64), shadow_positions=((d, 4, 5, 3), np.float64),
                      shadow_requested_change=((d, 5), bool), shadow_physical_change=((d, 5), bool),
                      shadow_modal_change=((d, 5), bool), shadow_total_variation=((d, 5), np.float64))
    if acquisition:
        shapes.update(intervention_features=((114,), np.float32), intervention_hidden=((128,), np.float32),
                      intervention_logits=((27,), np.float32), intervention_mu=((27,), np.float64),
                      intervention_action=((), np.int64), intervention_nominal_action=((), np.int64),
                      intervention_uniform=((), np.float64))
    if set(raw) != set(shapes):
        raise AssertionError("saved raw field contract changed")
    for key, (shape, dtype) in shapes.items():
        _array(raw, key, shape, dtype)
    actions, nominal, nav_pre = raw["action_index"], raw["nominal_action_index"], raw["nav_pre"]
    if (np.any((actions < 0) | (actions >= 27)) or np.any((nominal < 0) | (nominal >= 27))
            or np.any((nav_pre < 0) | (nav_pre >= 10)) or not raw["transmitter_mask"].all()):
        raise AssertionError("command/navigation/all-on contract changed")
    equal(raw["decision_ticks"], np.arange(0, h, 4), "decision clocks")
    equal(raw["commands"], np.repeat(COMMANDS[actions], 4, axis=0), "actual four-tick holds")
    equal(raw["positions"][1:], np.clip(raw["positions"][:-1] + raw["commands"].astype(np.float64) * 30.,
                                      [0., 0., 50.], [1000., 1000., 150.]), "actual native motion")
    work["native_team_ticks_verified"] += h
    work["native_agent_motion_ticks_verified"] += 5 * h
    normalized = raw["positions"].copy()
    normalized[..., :2] /= 1000.
    normalized[..., 2] = (normalized[..., 2] - 50.) / 100.
    equal(raw["observations"][..., :3], normalized[:-1].astype(np.float32), "own observation positions")
    equal(raw["terminal_observation"][..., :3], normalized[-1].astype(np.float32), "own terminal positions")
    equal(raw["observations"][..., -1], np.broadcast_to((np.arange(h) / h).astype(np.float32)[:, None], (h, 5)), "observation clock")
    equal(raw["terminal_observation"][..., -1], np.ones(5), "terminal clock")
    served = raw["connections"].sum(axis=(1, 2))
    equal(raw["served"], served, "native served reduction")
    if (np.any(raw["connections"].sum(axis=1) > 1) or np.any(raw["connections"].sum(axis=2) > 10)
            or np.any(raw["sinr"][raw["connections"]] < 3.)):
        raise AssertionError("native capacity/eligibility changed")
    quality = np.where(raw["connections"], np.clip((raw["sinr"] - 3.) / 30., 0, 1), 0.).sum(axis=(1, 2)) / np.maximum(served, 1)
    equal(raw["sinr_quality"], quality, "native quality", 1e-14)
    equal(raw["reward"], .7 * served / 50. + .3 * quality, "native complete reward", 1e-12)
    obs = raw["observations"][::4]
    equal(raw["features"][..., :103], obs[..., :103], "own actual local features")
    equal(raw["features"][..., 103:113], np.eye(10, dtype=np.float32)[nav_pre], "pre-navigation features")
    equal(raw["features"][..., 113], raw["fallback"], "helper fallback bit")
    equal(raw["n_current"], np.count_nonzero(obs[..., 3:63].reshape(d, 5, 20, 3)[..., 2] > 0, axis=-1), "user count")
    equal(raw["n_peers"], np.count_nonzero(obs[..., 63:103].reshape(d, 5, 10, 4)[..., 3] > 0, axis=-1), "peer count")
    if np.any(raw["n_peers"] > 4):
        raise AssertionError("nonlocal peer information")
    nav = np.array([np.argmin(np.sum((WAYPOINTS - own_position(r)[:2]) ** 2, axis=1)) for r in obs[0]])
    for di in range(d):
        equal(nav_pre[di], nav, "own navigation continuity")
        own = np.array([own_position(r) for r in obs[di]])
        arrival = np.linalg.norm(WAYPOINTS[nav] - own[:, :2], axis=1) <= 60.
        nav = np.where(raw["fallback"][di] & arrival, (nav + 1) % 10, nav)
        equal(raw["nav_next"][di], nav, "normal pre-command helper transition")
    if ordinary:
        epsilon = .1 if row["arm"] == "Q" else 0.
        deterministic = raw["c_index"]
        if np.any((deterministic < 0) | (deterministic >= 27)):
            raise AssertionError("invalid ordinary winner")
        equal(np.all(raw["policy_served"] == 0, axis=-1), raw["fallback"], "C full-support fallback")
        for di in range(d):
            for i in range(5):
                chosen = saved_ranking_choice(obs[di, i], int(raw["nav_next"][di, i]),
                                              bool(raw["fallback"][di, i]), raw["policy_scores"][di, i], np.arange(27))
                equal(deterministic[di, i], chosen, "saved ordinary ranking/fallback")
                if raw["fallback"][di, i]:
                    work["fallback_ranking_motion_ticks"] += 27 * 4
        p = np.full((d, 5, 27), epsilon / 26., dtype=np.float64)
        np.put_along_axis(p, deterministic[..., None], 1. - epsilon, axis=-1)
        measured = check_memo({**raw, "action_index": deterministic}, row, "", "C")
        measured["sampled_draws"] = d * 5 if epsilon else 0
    else:
        if not acquisition:
            if actor is None:
                raise AssertionError("every final student decision needs paid neural replay")
            for di in range(d):
                for i in range(5):
                    hidden, z = _forward(actor, raw["features"][di, i], protocol, work, "final_backbone_rows")
                    if head is None:
                        equal(raw["logits"][di, i], z, "final original logits")
                    else:
                        equal(raw["base_logits"][di, i], z, "final frozen backbone logits")
                        work["head_rows"] += 1
                        with torch.inference_mode():
                            deployed = head(torch.from_numpy(hidden), torch.from_numpy(z)).numpy()
                        equal(raw["logits"][di, i], deployed, "final one-row head logits")
        temperature = 2. if row["arm"] == "Bstar" and row["lineage"] == 0 else 1.
        p = _probabilities(raw["logits"], temperature)
        measured = check_memo(raw, {**row, "arm": "S_sampled"}, "", "student")
        measured["cache_array_bytes"] += measured["misses"] * (128 * 4 + (27 * 4 if head is not None else 0))
        measured["head_rows"] = measured["misses"] if head is not None else 0
    if measured != row["policy_counts"]:
        raise AssertionError(f"local memo/query cost changed: {measured} != {row['policy_counts']}")
    equal(raw["probabilities"], p, "nominal density", 2e-16)
    entropy = _entropy(p)
    equal(raw["entropy"], entropy, "nominal entropy", 2e-14)
    sampled = row["arm"] != "C"
    equal(raw["behavior_entropy"], entropy if sampled else np.zeros((d, 5)), "behavior entropy", 2e-14)
    if sampled:
        for di, tick in enumerate(raw["decision_ticks"]):
            for i in range(5):
                u = indexed_uniform(row["sampling_root"], row["world"], int(tick), i)
                equal(raw["innovation"][di, i], u, "original indexed private innovation")
                equal(nominal[di, i], categorical_index(p[di, i], u), "normal policy proposal")
        chosen = np.take_along_axis(p, nominal[..., None], axis=-1)[..., 0]
    else:
        equal(raw["innovation"], np.full((d, 5), -1.), "deterministic controller")
        equal(nominal, raw["c_index"], "ordinary deterministic proposal")
        chosen = np.ones((d, 5), dtype=np.float64)
    equal(raw["chosen_probability"], chosen, "normal proposal density")
    equal(raw["logp"], np.log(chosen), "normal proposal log density", 1e-14)
    expected_actual = nominal.copy()
    if acquisition:
        intervention = row["intervention"]
        di, i = intervention["tick"] // 4, intervention["agent"]
        mu = .5 * p[di, i] + .5 / 27.
        u = indexed_uniform(intervention["root"], row["world"], intervention["tick"], i)
        forced = categorical_index(mu, u)
        expected_actual[di, i] = forced
        for key, expected in (("features", raw["features"][di, i]), ("logits", raw["logits"][di, i]),
                               ("mu", mu), ("uniform", u), ("action", forced), ("nominal_action", nominal[di, i])):
            equal(raw["intervention_" + key], expected, "forced context " + key)
        record = dict(action=forced, nominal_action=int(nominal[di, i]), uniform=u,
                      context_sha256=array_digest(*(raw["intervention_" + key] for key in ("features", "hidden", "logits", "mu"))))
        if row["intervention_result"] != record:
            raise AssertionError("forced-context metadata/hash changed")
        work["intervention_draws_verified"] += 1
    elif row["intervention"] is not None:
        raise AssertionError("intervention outside acquisition")
    equal(actions, expected_actual, "only the declared actual category changes")
    if head is not None:
        _shadow(raw, row, protocol, work)
    elif "shadow" in row:
        raise AssertionError("unexpected shadow exposure")
    for key, value in episode_metrics(raw).items():
        equal(row[key], value, "native metric " + key, 1e-12)
    equal(row["nominal_entropy_mean"], entropy.mean(), "mean entropy", 2e-14)
    equal(row["behavior_entropy_mean"], raw["behavior_entropy"].mean(), "mean behavior entropy", 2e-14)
    if row["initial_state_sha256"] != array_digest(raw["positions"][0], raw["initial_users"]):
        raise AssertionError("initial reset identity changed")


def _pair(a, b, row_a, row_b, protocol, actor, data, j, work):
    intervention = row_a["intervention"]
    tick, i, di = intervention["tick"], intervention["agent"], intervention["tick"] // 4
    for key in ("positions", "observations"):
        equal(a[key][:tick + 1], b[key][:tick + 1], "paired original prefix " + key)
    for key in ("commands", "reward", "served", "sinr_quality", "sinr", "connections", "transmitter_mask"):
        equal(a[key][:tick], b[key][:tick], "paired original prefix " + key)
    for key in ("nav_pre", "nav_next", "fallback", "nominal_action_index", "memo_hit", "features", "n_current",
                "n_peers", "probabilities", "innovation", "entropy", "behavior_entropy", "chosen_probability", "logp", "logits"):
        equal(a[key][:di + 1], b[key][:di + 1], "paired original decision prefix " + key)
    equal(a["action_index"][:di], b["action_index"][:di], "paired actual prefix")
    peers = [agent for agent in range(5) if agent != i]
    equal(a["action_index"][di, peers], b["action_index"][di, peers], "other four current actions fixed")
    for key in ("features", "hidden", "logits", "mu", "nominal_action"):
        equal(a["intervention_" + key], b["intervention_" + key], "identical paired source context " + key)
    h, z = _forward(actor, a["intervention_features"], protocol, work, "pair_backbone_rows")
    equal(a["intervention_hidden"], h, "intervention hidden provenance")
    equal(a["intervention_logits"], z, "intervention original logits")
    values = dict(features=a["intervention_features"], hidden=h, logits=z, mu=a["intervention_mu"],
                  action_a=int(a["intervention_action"]), action_b=int(b["intervention_action"]),
                  delta_j=row_a["J"] - row_b["J"], weight=intervention["weight"], world=row_a["world"],
                  address=intervention["address"], J_a=row_a["J"], J_b=row_b["J"],
                  uniform_a=float(a["intervention_uniform"]), uniform_b=float(b["intervention_uniform"]),
                  nominal_action=int(a["intervention_nominal_action"]))
    if set(values) != set(data):
        raise AssertionError("training dataset field contract changed")
    for key, value in values.items():
        equal(data[key][j], value, "cached paired training value " + key)
    if values["action_a"] == values["action_b"]:
        # Equal interventions are retained and must not shift any subsequent private address.
        for key in ("positions", "observations", "commands", "reward", "action_index", "nav_pre", "nav_next", "logits", "innovation"):
            equal(a[key], b[key], "same-category complete branch identity " + key)
    work["pairs_verified"] += 1


def _adam(saved, state, steps):
    if len(saved["param_groups"]) != 1:
        raise AssertionError("one head Adam group required")
    group = saved["param_groups"][0]
    for key, expected in dict(lr=.001, betas=(.9, .999), eps=1e-8, weight_decay=0,
                               amsgrad=False, foreach=False, fused=False, maximize=False).items():
        if group[key] != expected:
            raise AssertionError("head Adam law changed: " + key)
    ids = group["params"]
    if len(ids) != len(state) or len(set(ids)) != len(ids) or set(saved["state"]) != set(ids):
        raise AssertionError("head optimizer coverage changed")
    for identifier, parameter in zip(ids, state.values()):
        entry = saved["state"][identifier]
        if float(entry["step"]) != steps:
            raise AssertionError("head Adam step count changed")
        for key in ("exp_avg", "exp_avg_sq"):
            value = entry[key]
            if value.dtype != torch.float32 or value.shape != parameter.shape or not torch.isfinite(value).all():
                raise AssertionError("invalid head Adam moments")
        if (entry["exp_avg_sq"] < 0).any():
            raise AssertionError("negative head second moment")


def _heads(out, batch, protocol, datasets):
    """Endpoint and saved update auditing; no additional optimization or head forwards."""
    models, evidence = {}, []
    expected = [(l, k) for l in range(2) for k in HEADS]
    if [(r["lineage"], r["kind"]) for r in batch["heads"]] != expected:
        raise AssertionError("four final head identities required")
    if [(r["lineage"], r["kind"]) for r in batch["fits"]] != expected:
        raise AssertionError("four fit identities required")
    for record, fit in zip(batch["heads"], batch["fits"]):
        lineage, kind = record["lineage"], record["kind"]
        payload = torch.load(identity(out, record), map_location="cpu", weights_only=True)
        initial_sha = batch["initial_assets"][lineage]["state_sha256"]
        expected_fields = dict(schema="uav_fleet_adaptation.b05.head.v1", endpoint=kind, lineage=lineage,
                               launch_sha=batch["launch_sha"], protocol=batch["protocol"],
                               original_student_sha256=initial_sha, optimizer_steps=protocol.updates,
                               dtype="float32", hidden_size=128, output_size=27,
                               trainable_parameters=28 if kind == "CAL" else 3483, training_trace=record["training_trace"])
        if any(payload.get(k) != v for k, v in expected_fields.items()):
            raise AssertionError("head checkpoint provenance changed")
        if (record["original_student_sha256"] != initial_sha or record["optimizer_steps"] != protocol.updates
                or record["trainable_parameters"] != expected_fields["trainable_parameters"]
                or fit["seed"] != protocol.minibatch_roots[lineage] or fit["trace"] != record["training_trace"]):
            raise AssertionError("head/fit lineage provenance changed")
        state = payload["state_dict"]
        if any(v.dtype != torch.float32 or not torch.isfinite(v).all() for v in state.values()):
            raise AssertionError("nonfinite or non-FP32 head")
        if state_digest(state) != record["state_sha256"] or payload["state_sha256"] != record["state_sha256"]:
            raise AssertionError("head tensor identity changed")
        head = Head(kind)
        initial = {k: v.detach().clone() for k, v in head.state_dict().items()}
        head.load_state_dict(state, strict=True)
        head.eval()
        _adam(payload["optimizer"], state, protocol.updates)
        trace = json.loads(identity(out, record["training_trace"]).read_text())
        _finite_tree(trace)
        # The concrete trace schema is checked by _fit_trace, without replaying it.
        _fit_trace(trace, protocol, lineage, kind, initial, state, datasets[lineage])
        evidence.append(dict(lineage=lineage, kind=kind, state_sha256=record["state_sha256"],
                             movement=movement(initial, state), trace=record["training_trace"],
                             optimizer_steps=protocol.updates))
        models[lineage, kind] = head
    return models, evidence


def _fit_trace(trace, protocol, lineage, kind, initial, final, data):
    n, steps = len(protocol.acquisition_worlds[lineage]), protocol.updates
    expected = dict(kind=kind, status="COMPLETE", seed=protocol.minibatch_roots[lineage],
                    contexts=n, planned_updates=steps, batch_size=128, parameters=28 if kind == "CAL" else 3483,
                    data_sha256=array_digest(*(data[key] for key in DATA_KEYS)),
                    initial_state_sha256=state_digest(initial), final_state_sha256=state_digest(final),
                    initial_optimizer_entries=0, optimizer_steps=steps, training_rows=steps * 128,
                    adam_step_values=[float(steps)] * len(initial), parameters_finite=True,
                    movement=movement(initial, final),
                    counts=dict(head_fits_started=1, head_fits_completed=1, head_optimizer_steps=steps,
                                head_training_rows=steps * 128))
    if any(trace.get(k) != v for k, v in expected.items()) or len(trace["updates"]) != steps:
        raise AssertionError("saved fit identity, exposure or movement changed")
    for name in ("wall_seconds", "cpu_seconds"):
        if trace[name] < 0:
            raise AssertionError("invalid fit timing")
    rng = np.random.default_rng(protocol.minibatch_roots[lineage])
    order = hashlib.sha256()
    final_sha = None
    for step, record in enumerate(trace["updates"]):
        indices = rng.integers(0, n, size=128)
        payload = indices.astype("<i8", copy=False).tobytes()
        order.update(payload)
        if (record["update"] != step or record["status"] != "COMPLETE"
                or record["optimizer_step_completed"] is not True
                or record["batch_sha256"] != hashlib.sha256(payload).hexdigest()
                or record["adam_step_values"] != [float(step + 1)] * len(initial)):
            raise AssertionError("saved minibatch/update/Adam sequence changed")
        sha = record["state_sha256"]
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            raise AssertionError("invalid saved update tensor digest")
        final_sha = sha
        equal(record["loss"], -record["F"] + .01 * record["KL"], "saved weighted objective", 1e-13)
        if step == 0:
            p = _probabilities(data["logits"][indices])
            a, b = data["action_a"][indices], data["action_b"][indices]
            mu = data["mu"][indices]
            rows = np.arange(128)
            score = .5 * data["delta_j"][indices] * (p[rows, a] / mu[rows, a] - p[rows, b] / mu[rows, b])
            equal(record["F"], (data["weight"][indices] * score).mean(), "zero-head first paired score", 5e-14)
            equal(record["KL"], 0., "zero-head first KL", 1e-14)
        if (record["KL"] < -1e-12 or not -1e-12 <= record["entropy"] <= np.log(27.) + 1e-12
                or record["weighted_entropy"] < -1e-12
                or not 0 <= record["gradient_max_abs"] <= record["gradient_l2"] + 1e-12
                or any(not 0 <= record[key] <= 54. + 1e-12 for key in ("ratio_a_mean", "ratio_b_mean"))):
            raise AssertionError("invalid saved gradient/density/loss evidence")
    if final_sha != state_digest(final) or trace["batch_order_sha256"] != order.hexdigest():
        raise AssertionError("final update/order digest changed")


def _read_result(out, repo, *, allow_fixture, work, started, cpu_started):
    batch = json.loads((out / "summary.json").read_text())
    _finite_tree(batch)
    if batch["object"] != OBJECT or batch["state"] != "COMPLETE" or batch["status"] != "COMPLETE" or "failure" in batch:
        raise ValueError("only a complete fixed B05 batch can be read")
    protocol = Protocol.from_dict(batch["protocol"])
    if allow_fixture:
        if batch["scientific_execution"] is not False or protocol == FROZEN:
            raise ValueError("fixture reading must remain nonproduction and nonscientific")
    elif batch["scientific_execution"] is not True or protocol != FROZEN:
        raise ValueError("production reading requires the fixed scientific object")
    if source_identities(repo) != batch["sources"]:
        raise AssertionError("reader is not running the recorded source bytes")
    if batch["inherited_calibration"] != CALIBRATION_SOURCE:
        raise AssertionError("old paid calibration selection changed")
    if not allow_fixture and file_identity(repo / CALIBRATION_SOURCE["reading_path"])["sha256"] != CALIBRATION_SOURCE["reading_sha256"]:
        raise AssertionError("old paid calibration evidence changed")
    runtime = batch["runtime"]
    if (runtime["device"] != "cpu" or runtime["actor_dtype"] != "float32" or runtime["density_dtype"] != "float64"
            or runtime["torch_threads"] != 1 or torch.get_num_threads() != 1):
        raise AssertionError("CPU one-thread FP32/FP64 contract changed")
    config = json.loads((out / "config.json").read_text())
    config_keys = {"object", "launch_sha", "scientific_execution", "protocol", "expected",
                   "sources", "initial_assets", "runtime", "inherited_calibration"}
    if set(config) != config_keys or any(config[k] != batch[k] for k in config):
        raise AssertionError("worker config disagrees with final summary")
    bindings = []
    for record in batch["initial_assets"]:
        keys = ("path", "bytes", "sha256", "state_sha256", "launch_sha")
        if not allow_fixture:
            keys += ("canonical_path", "canonical_node")
        bindings.append({key: record[key] for key in keys})
    if not allow_fixture and tuple(bindings) != INITIAL_ASSETS:
        raise AssertionError("initial assets were substituted")
    originals, checked = load_initial_assets(protocol, bindings=bindings, permit_fixture=allow_fixture)
    if checked != batch["initial_assets"]:
        raise AssertionError("initial asset metadata differs")
    validate_counts(batch, protocol)
    datasets = {}
    if len(batch["datasets"]) != 2:
        raise AssertionError("both paired datasets required")
    for lineage, record in enumerate(batch["datasets"]):
        if record["lineage"] != lineage:
            raise AssertionError("dataset lineage changed")
        with np.load(identity(out, record["artifact"]), allow_pickle=False) as saved:
            data = {key: saved[key] for key in saved.files}
        n = len(protocol.acquisition_worlds[lineage])
        shapes = dict(features=((n, 114), np.float32), hidden=((n, 128), np.float32),
                      logits=((n, 27), np.float32), mu=((n, 27), np.float64))
        for key in ("action_a", "action_b", "world", "address", "nominal_action"):
            shapes[key] = ((n,), np.int64)
        for key in ("delta_j", "weight", "J_a", "J_b", "uniform_a", "uniform_b"):
            shapes[key] = ((n,), np.float64)
        if set(data) != set(shapes) or record["array_keys"] != sorted(data):
            raise AssertionError("cached dataset field contract changed")
        for key, (shape, dtype) in shapes.items():
            _array(data, key, shape, dtype)
        if (array_digest(*(data[key] for key in sorted(data))) != record["data_sha256"]
                or acquisition_summary(data) != record["summary"]):
            raise AssertionError("cached training dataset/summary changed")
        datasets[lineage] = data
    heads, fit_readings = _heads(out, batch, protocol, datasets)
    recorded_assets = {identity(out, r) for r in batch["heads"]}
    recorded_data = {identity(out, r["artifact"]) for r in batch["datasets"]}
    recorded_data.update(identity(out, r["trace"]) for r in batch["fits"])
    if set((out / "assets").iterdir()) != recorded_assets or set((out / "data").iterdir()) != recorded_data:
        raise AssertionError("missing or unrecorded asset/training evidence")
    addresses = [protocol.addresses(l) for l in range(2)]
    pending, raw_paths, resets = None, set(), {}
    for row in batch["rows"]:
        lineage, acquisition = row["lineage"], row["kind"] == "acquisition"
        ordinary = row["arm"] in ("C", "Q")
        root = (protocol.acquisition_roots if acquisition else protocol.evaluation_roots)[lineage]
        original_sha = None if ordinary else checked[lineage]["state_sha256"]
        head_sha = state_digest(heads[lineage, row["arm"]].state_dict()) if row["arm"] in HEADS else None
        if (row["sampling_root"] != root or row["initial_sha256"] != original_sha or row["head_sha256"] != head_sha
                or row["policy_identity"] != policy_identity(row["arm"], lineage, original_sha, head_sha, root)):
            raise AssertionError("episode policy/randomness provenance changed")
        if acquisition:
            j = protocol.acquisition_worlds[lineage].index(row["world"])
            address = int(addresses[lineage][0][j])
            branch = row["intervention"]["branch"]
            forced_root = (protocol.intervention_a_roots if branch == "a" else protocol.intervention_b_roots)[lineage]
            expected = dict(pair_index=j, address=address, tick=4 * (address // 5), agent=address % 5, branch=branch,
                            root=forced_root, weight=float(addresses[lineage][1][j]))
            if row["intervention"] != expected:
                raise AssertionError("intervention/address/weight provenance changed")
        path = identity(out, row["raw"])
        if path in raw_paths:
            raise AssertionError("raw episode evidence reused")
        raw_paths.add(path)
        with np.load(path, allow_pickle=False) as saved:
            raw = {key: saved[key] for key in saved.files}
        _episode(raw, row, protocol, None if acquisition or ordinary else originals[lineage],
                 heads.get((lineage, row["arm"])), work)
        old_reset = resets.setdefault(row["world"], row["initial_state_sha256"])
        if old_reset != row["initial_state_sha256"]:
            raise AssertionError("same-world complete reset differs")
        if acquisition:
            if branch == "a":
                if pending is not None:
                    raise AssertionError("an acquisition branch is missing")
                pending = (raw, row)
            else:
                if pending is None or pending[1]["world"] != row["world"]:
                    raise AssertionError("wrong acquisition branch pair")
                _pair(pending[0], raw, pending[1], row, protocol, originals[lineage], datasets[lineage], j, work)
                pending = None
    if pending is not None or set((out / "raw").glob("*.npz")) != raw_paths:
        raise AssertionError("missing/unreferenced/partial raw evidence")
    reduced = comparisons(batch["rows"], protocol)
    if reduced != batch["comparisons"]:
        raise AssertionError("final paired reductions changed")
    expected = protocol.expected()
    for actual, key in (("backbone_rows", "reader_backbone_rows"), ("pair_backbone_rows", "reader_pair_backbone_rows"),
                        ("final_backbone_rows", "reader_final_backbone_rows"), ("head_rows", "reader_head_rows"),
                        ("shadow_motion_ticks", "shadow_motion_ticks"), ("pairs_verified", "acquisition_contexts"),
                        ("intervention_draws_verified", "intervention_draws")):
        if work[actual] != expected[key]:
            raise AssertionError("reader completed-work scope differs: " + actual)
    verify_initial_assets(originals, checked)
    return dict(object=OBJECT, status="VERIFIED", launch_sha=batch["launch_sha"], scientific_execution=batch["scientific_execution"],
                summary=file_identity(out / "summary.json"), sources=batch["sources"], initial_assets=checked, heads=batch["heads"],
                datasets=batch["datasets"], fit_readings=fit_readings, inherited_calibration=CALIBRATION_SOURCE,
                raw_files=len(raw_paths), raw_bytes=sum(r["raw"]["bytes"] for r in batch["rows"]),
                expected=expected, actual=batch["actual"], costs=batch["costs"], comparisons=reduced, reader_calls=work,
                worker_wall_seconds=batch["worker_wall_seconds"], worker_cpu_seconds=batch["worker_cpu_seconds"],
                worker_max_rss_kib=batch["worker_max_rss_kib"],
                reader_wall_seconds=time.perf_counter() - started, reader_cpu_seconds=time.process_time() - cpu_started,
                reader_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                reader_rss_scope="whole-process high-water mark including preceding worker, not incremental reader RSS",
                scope="all raw/source identities, native metric/motion and local provenance, pair prefixes/forced draws/weights/data labels; one neural context per identical pair and every final student/head decision; acquisition nonintervention logits and optimizer gradients/updates are saved evidence, not neural/optimizer replay")


def read_result(out, repo, *, allow_fixture=False):
    out, repo = Path(out).resolve(), Path(repo).resolve()
    work = dict(backbone_rows=0, pair_backbone_rows=0, final_backbone_rows=0, head_rows=0,
                shadow_motion_ticks=0, pairs_verified=0, intervention_draws_verified=0,
                native_team_ticks_verified=0, native_agent_motion_ticks_verified=0, fallback_ranking_motion_ticks=0,
                native=0, radio_power_model=0, critic_rows=0, optimizer=0)
    started, cpu_started = time.perf_counter(), time.process_time()
    target = out / "reading.json"
    if not allow_fixture:
        with target.open("x", encoding="utf-8") as stream:
            json.dump(dict(object=OBJECT, status="INCOMPLETE", reader_calls=work), stream)
            stream.write("\n")
    try:
        reading = _read_result(out, repo, allow_fixture=allow_fixture, work=work, started=started, cpu_started=cpu_started)
        if not allow_fixture:
            write_json(target, reading)
        return reading
    except BaseException as error:
        failed = dict(object=OBJECT, status="FAILED", failure=dict(type=type(error).__name__, message=str(error)),
                      reader_calls=work, reader_wall_seconds=time.perf_counter() - started,
                      reader_cpu_seconds=time.process_time() - cpu_started,
                      reader_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                      interrupted_call_work_may_be_unmeasured=True)
        error.reader_work = failed
        if not allow_fixture:
            try:
                write_json(target, failed)
            except OSError as write_error:
                error.reader_record_write_error = str(write_error)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    torch.set_num_threads(1)
    reading = read_result(args.out, ROOT)
    print(json.dumps({key: reading[key] for key in ("status", "raw_files", "reader_cpu_seconds")}))


if __name__ == "__main__":
    main()
