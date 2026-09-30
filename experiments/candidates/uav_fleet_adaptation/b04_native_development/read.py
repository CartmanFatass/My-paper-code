"""Verify complete B04 saved evidence without native, radio or optimizer replay."""
import argparse
import json
import math
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if __package__ in (None, ""):
    __package__ = "experiments.candidates.uav_fleet_adaptation.b04_native_development"

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, WAYPOINTS
from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_digest, movement
from experiments.candidates.uav_fleet_adaptation.b02.read import equal, identity, own_position, check_memo, saved_ranking_choice
from experiments.candidates.uav_fleet_adaptation.b02.reading import episode_metrics
from experiments.candidates.uav_fleet_adaptation.b02.policies import categorical_index, indexed_uniform
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import critic_features
from .assets import load_initial_assets
from .contract import OBJECT, FROZEN, STAGED_ASSETS, Protocol, candidate_spec, policy_identity, evaluation_plan, source_identities, array_digest
from .learning import fresh_critic
from .reading import calibration_result, comparisons, validate_counts


def _finite_tree(value):
    if isinstance(value, dict):
        for child in value.values():
            _finite_tree(child)
    elif isinstance(value, list):
        for child in value:
            _finite_tree(child)
    elif isinstance(value, float) and not math.isfinite(value):
        raise AssertionError("nonfinite summary value")


def _array(raw, key, shape, dtype=None):
    value = raw[key]
    if value.shape != shape or not np.isfinite(value).all() or (dtype is not None and value.dtype != np.dtype(dtype)):
        raise AssertionError(f"invalid finite raw shape/dtype: {key}")
    return value


def _probabilities(logits, temperature=1.):
    z = logits.astype(np.float64) / temperature
    weights = np.exp(z - z.max(axis=-1, keepdims=True))
    return weights / weights.sum(axis=-1, keepdims=True, dtype=np.float64)


def _entropy(p):
    logp = np.zeros_like(p)
    np.log(p, out=logp, where=p > 0)
    return -(p * logp).sum(-1)


def _actor_logits(actor, features, work, key):
    outputs = []
    for feature in features.reshape(-1, 114):
        if work["actor_forward_rows"] >= 81920:
            raise AssertionError("reader actor allowance exceeded")
        work["actor_forward_rows"] += 1
        work[key] += 1
        with torch.inference_mode():
            output = actor(torch.from_numpy(np.ascontiguousarray(feature)).reshape(1, 114))[0].numpy().copy()
        outputs.append(output)
    return np.stack(outputs).reshape(*features.shape[:-1], 27)


def _shadow(raw, row, actor, protocol, work):
    d = protocol.horizon // 4
    logits = _array(raw, "shadow_logits", (d, 5, 27), np.float32)
    equal(logits, _actor_logits(actor, raw["features"], work, "shadow_actor_rows"), "frozen S shadow logits")
    probabilities = _probabilities(logits)
    equal(_array(raw, "shadow_probabilities", (d, 5, 27), np.float64), probabilities, "shadow density", 2e-16)
    actions = _array(raw, "shadow_action_index", (d, 5), np.int64)
    if np.any((actions < 0) | (actions >= 27)):
        raise AssertionError("invalid shadow category")
    for di in range(d):
        for agent in range(5):
            equal(actions[di, agent], categorical_index(probabilities[di, agent], raw["innovation"][di, agent]), "shadow same private innovation")
    path = []
    for di in range(d):
        position = raw["positions"][4 * di].copy()
        ticks = []
        for _ in range(4):
            if work["shadow_motion_ticks"] + 5 > 81920:
                raise AssertionError("reader shadow motion allowance exceeded")
            position = np.clip(position + COMMANDS[actions[di]].astype(np.float64) * 30., [0., 0., 50.], [1000., 1000., 150.])
            work["shadow_motion_ticks"] += 5
            ticks.append(position.copy())
        path.append(ticks)
    equal(_array(raw, "shadow_positions", (d, 4, 5, 3), np.float64), path, "shadow four-tick motion")
    requested = actions != raw["action_index"]
    physical = np.any(np.asarray(path) != raw["positions"][1:].reshape(d, 4, 5, 3), axis=(1, 3))
    modal = logits.argmax(-1) != raw["logits"].argmax(-1)
    tv = .5 * np.abs(probabilities - raw["probabilities"]).sum(-1)
    for key, value in (("requested_change", requested), ("physical_change", physical), ("modal_change", modal), ("total_variation", tv)):
        equal(_array(raw, "shadow_" + key, (d, 5), np.float64 if key == "total_variation" else bool), value, "shadow " + key, 2e-16)
    expected = dict(rows=d * 5, requested_changes=int(requested.sum()), physical_changes=int(physical.sum()),
                    modal_changes=int(modal.sum()), total_variation_mean=float(tv.mean()), total_variation_max=float(tv.max()))
    if row["shadow"] != expected:
        raise AssertionError("shadow aggregate mismatch")


def _episode(raw, row, protocol, actor, shadow_actor, work):
    h, d = protocol.horizon, protocol.horizon // 4
    shapes = dict(observations=((h, 5, 104), np.float32), commands=((h, 5, 3), np.float32),
                  positions=((h + 1, 5, 3), np.float64), reward=((h,), np.float64),
                  served=((h,), None), sinr_quality=((h,), np.float64), sinr=((h, 5, 50), np.float64),
                  connections=((h, 5, 50), bool), transmitter_mask=((h, 5), bool),
                  features=((d, 5, 114), np.float32), terminal_observation=((5, 104), np.float32),
                  nav_pre=((d, 5), np.int64), nav_next=((d, 5), np.int64), fallback=((d, 5), bool),
                  action_index=((d, 5), np.int64), memo_hit=((d, 5), bool), n_current=((d, 5), None),
                  n_peers=((d, 5), None), initial_users=((50, 2), np.float64),
                  decision_ticks=((d,), np.int64), macro_rewards=((d,), np.float64),
                  probabilities=((d, 5, 27), np.float64), innovation=((d, 5), np.float64),
                  entropy=((d, 5), np.float64), behavior_entropy=((d, 5), np.float64),
                  chosen_probability=((d, 5), np.float64), logp=((d, 5), np.float64))
    for key, (shape, dtype) in shapes.items():
        _array(raw, key, shape, dtype)
    allowed = set(shapes)
    allowed.update(("logits",) if candidate_spec(row["candidate"])["family"] == "S" else
                   ("c_index", "policy_scores", "policy_served"))
    if row["kind"] == "training":
        allowed.update(("critic_states", "critic_features", "values"))
    if row["kind"] == "evaluation" and row["arm"] == "R":
        allowed.update("shadow_" + key for key in ("logits", "probabilities", "action_index", "positions",
                                                    "requested_change", "physical_change", "modal_change", "total_variation"))
    if set(raw) != allowed:
        raise AssertionError("missing/unexpected saved episode fields")
    actions, nav_pre = raw["action_index"], raw["nav_pre"]
    if np.any((actions < 0) | (actions >= 27)) or np.any((nav_pre < 0) | (nav_pre >= 10)):
        raise AssertionError("invalid action or navigation indices")
    if not raw["transmitter_mask"].all():
        raise AssertionError("all-on host changed")
    equal(raw["decision_ticks"], np.arange(0, h, 4), "decision clocks")
    equal(raw["commands"], np.repeat(COMMANDS[actions], 4, axis=0), "all-category four-tick holds")
    equal(raw["positions"][1:], np.clip(raw["positions"][:-1] + raw["commands"].astype(np.float64) * 30.,
                                      [0., 0., 50.], [1000., 1000., 150.]), "saved native motion")
    work["native_team_ticks_verified"] += h
    work["native_agent_motion_ticks_verified"] += h * 5
    positions = raw["positions"].copy()
    positions[..., :2] /= 1000.
    positions[..., 2] = (positions[..., 2] - 50.) / 100.
    equal(raw["observations"][..., :3], positions[:-1].astype(np.float32), "own observation position provenance")
    equal(raw["terminal_observation"][..., :3], positions[-1].astype(np.float32), "terminal own positions")
    equal(raw["observations"][..., -1], np.broadcast_to((np.arange(h) / h).astype(np.float32)[:, None], (h, 5)), "observation clock")
    equal(raw["terminal_observation"][..., -1], np.ones(5), "terminal clock")
    served = raw["connections"].sum(axis=(1, 2))
    equal(raw["served"], served, "saved service reduction")
    if np.any(raw["connections"].sum(axis=1) > 1) or np.any(raw["connections"].sum(axis=2) > 10) or np.any(raw["sinr"][raw["connections"]] < 3.):
        raise AssertionError("native connection capacity/eligibility changed")
    quality = np.where(raw["connections"], np.clip((raw["sinr"] - 3.) / 30., 0., 1.), 0.).sum(axis=(1, 2)) / np.maximum(served, 1)
    equal(raw["sinr_quality"], quality, "native quality", 1e-14)
    equal(raw["reward"], .7 * served / 50. + .3 * quality, "native reward", 1e-12)
    equal(raw["macro_rewards"], raw["reward"].reshape(d, 4).sum(axis=1, dtype=np.float64), "macro rewards")
    obs = raw["observations"][::4]
    equal(raw["features"][..., :103], obs[..., :103], "own actual lawful features")
    equal(raw["features"][..., 103:113], np.eye(10, dtype=np.float32)[nav_pre], "own pre-navigation features")
    equal(raw["features"][..., 113], raw["fallback"], "analytic ineligibility feature")
    equal(raw["n_current"], np.count_nonzero(obs[..., 3:63].reshape(d, 5, 20, 3)[..., 2] > 0, axis=-1), "local user count")
    equal(raw["n_peers"], np.count_nonzero(obs[..., 63:103].reshape(d, 5, 10, 4)[..., 3] > 0, axis=-1), "local peer count")
    if np.any(raw["n_peers"] > 4):
        raise AssertionError("nonlocal peer exposure")
    nav = np.array([np.argmin(np.sum((WAYPOINTS - own_position(r)[:2]) ** 2, axis=1)) for r in obs[0]])
    for di in range(d):
        equal(nav_pre[di], nav, "own navigation continuity")
        own = np.array([own_position(r) for r in obs[di]])
        arrival = np.linalg.norm(WAYPOINTS[nav] - own[:, :2], axis=1) <= 60.
        nav = np.where(raw["fallback"][di] & arrival, (nav + 1) % 10, nav)
        equal(raw["nav_next"][di], nav, "source navigation transition")
    spec = candidate_spec(row["candidate"])
    sampled = spec["epsilon"] > 0 if spec["family"] == "C" else spec["temperature"] is not None
    if spec["family"] == "S":
        logits = _array(raw, "logits", (d, 5, 27), np.float32)
        if actor is not None:
            equal(logits, _actor_logits(actor, raw["features"], work, "evaluation_actor_rows"), "evaluation endpoint logits")
        probabilities = _probabilities(logits, spec["temperature"] or 1.)
        deterministic_choice = logits.argmax(-1)
        proxy = {**row, "arm": "S_sampled" if sampled else "S_greedy"}
        measured = check_memo(raw, proxy, "", "student")
    else:
        scores = _array(raw, "policy_scores", (d, 5, 27), np.float64)
        services = _array(raw, "policy_served", (d, 5, 27), None)
        deterministic_choice = _array(raw, "c_index", (d, 5), np.int64)
        if np.any((deterministic_choice < 0) | (deterministic_choice >= 27)):
            raise AssertionError("invalid C category")
        equal(np.all(services == 0, axis=-1), raw["fallback"], "full-support C fallback")
        for di in range(d):
            for agent in range(5):
                expected = saved_ranking_choice(obs[di, agent], int(raw["nav_next"][di, agent]), bool(raw["fallback"][di, agent]), scores[di, agent], np.arange(27))
                equal(deterministic_choice[di, agent], expected, "saved C ranking/fallback geometry")
                if raw["fallback"][di, agent]:
                    work["fallback_ranking_motion_ticks"] += 27 * 4
        probabilities = np.full((d, 5, 27), spec["epsilon"] / 26., dtype=np.float64)
        np.put_along_axis(probabilities, deterministic_choice[..., None], 1. - spec["epsilon"], axis=-1)
        measured = check_memo({**raw, "action_index": deterministic_choice}, row, "", "C")
        measured["sampled_draws"] = d * 5 if sampled else 0
    if measured != row["policy_counts"]:
        raise AssertionError("episode-local memo/query cost mismatch")
    equal(raw["probabilities"], probabilities, "nominal policy density", 2e-16)
    entropy = _entropy(probabilities)
    equal(raw["entropy"], entropy, "nominal entropy", 2e-14)
    equal(raw["behavior_entropy"], entropy if sampled else np.zeros((d, 5)), "behavior entropy", 2e-14)
    if sampled:
        for di, tick in enumerate(raw["decision_ticks"]):
            for agent in range(5):
                u = indexed_uniform(row["sampling_root"], row["world"], int(tick), agent)
                equal(raw["innovation"][di, agent], u, "fresh original private uniform")
                equal(actions[di, agent], categorical_index(probabilities[di, agent], u), "requested inverse-CDF category")
        chosen = np.take_along_axis(probabilities, actions[..., None], axis=-1)[..., 0]
    else:
        equal(raw["innovation"], np.full((d, 5), -1.), "deterministic innovation")
        equal(actions, deterministic_choice, "deterministic category")
        chosen = np.ones((d, 5), dtype=np.float64)
    if np.any(chosen <= 0):
        raise AssertionError("invalid chosen behavior density")
    equal(raw["chosen_probability"], chosen, "old chosen probability")
    equal(raw["logp"], np.log(chosen), "independent old chosen logp", 1e-14)
    equal(row["nominal_entropy_mean"], entropy.mean(), "row nominal entropy", 2e-14)
    equal(row["behavior_entropy_mean"], raw["behavior_entropy"].mean(), "row behavior entropy", 2e-14)
    for key, value in episode_metrics(raw).items():
        equal(row[key], value, "saved metric " + key, 1e-12)
    if row["initial_state_sha256"] != array_digest(raw["positions"][0], raw["initial_users"]):
        raise AssertionError("initial reset identity")
    if row["kind"] == "training":
        states = _array(raw, "critic_states", (d, 116), np.float32)
        cx = _array(raw, "critic_features", (d, 136), np.float32)
        _array(raw, "values", (d,), np.float32)
        for di, tick in enumerate(raw["decision_ticks"]):
            expected_state = np.r_[raw["positions"][tick].ravel(), raw["initial_users"].ravel(), tick / h].astype(np.float32)
            equal(states[di], expected_state, "central state position/user/clock provenance")
            previous = np.zeros((5, 3), dtype=np.float32) if tick == 0 else raw["commands"][tick - 1]
            equal(cx[di], critic_features(states[di], previous, np.zeros(5, dtype=np.int64)), "separate critic input provenance")
    elif any(key in raw for key in ("critic_features", "critic_states", "values")):
        raise AssertionError("critic exposure outside training")
    if row["arm"] == "R" and row["kind"] == "evaluation":
        _shadow(raw, row, shadow_actor, protocol, work)
    elif row.get("shadow_sha256") is not None or any(key.startswith("shadow_") for key in raw):
        raise AssertionError("shadow outside final R history")


def _adam(saved, state, steps):
    if len(saved["param_groups"]) != 1:
        raise AssertionError("separate single-group Adam required")
    group = saved["param_groups"][0]
    for key, expected in dict(lr=3e-4, betas=(.9, .999), eps=1e-8, weight_decay=0,
                               amsgrad=False, foreach=False, fused=False, maximize=False).items():
        if group[key] != expected:
            raise AssertionError("final Adam law changed: " + key)
    parameters = list(state.values())
    ids = group["params"]
    if len(ids) != len(parameters) or len(set(ids)) != len(ids) or set(saved["state"]) != set(ids):
        raise AssertionError("Adam parameter/state coverage changed")
    for identifier, parameter in zip(ids, parameters):
        entry = saved["state"][identifier]
        if float(entry["step"]) != steps:
            raise AssertionError("Adam step continuity changed")
        for key in ("exp_avg", "exp_avg_sq"):
            value = entry[key]
            if value.dtype != torch.float32 or value.shape != parameter.shape or not torch.isfinite(value).all():
                raise AssertionError("invalid Adam moment")
        if (entry["exp_avg_sq"] < 0).any():
            raise AssertionError("invalid Adam second moment")


def _final_assets(out, batch, protocol, initial_models):
    models, payloads = [], []
    if len(batch["final_assets"]) != 2 or len(batch["updates"]) != 2:
        raise AssertionError("both final lineages are required")
    for lineage, record in enumerate(batch["final_assets"]):
        payload = torch.load(identity(out, record), map_location="cpu", weights_only=True)
        initial_sha = batch["initial_assets"][lineage]["state_sha256"]
        steps = len(protocol.training_worlds[lineage]) // 2 * 4
        if (record["lineage"] != lineage or record["initial_sha256"] != initial_sha or
                record["optimizer_steps"] != steps or payload["endpoint"] != "R" or payload["lineage"] != lineage or
                payload["initial_sha256"] != initial_sha or payload["launch_sha"] != batch["launch_sha"] or
                payload["protocol"] != batch["protocol"] or payload["optimizer_steps"] != steps or
                payload["architecture"] != [114, 128, 128, 27] or payload["activation"] != "relu" or payload["dtype"] != "float32"):
            raise AssertionError("final checkpoint identity/architecture/exposure changed")
        for key in ("state_dict", "critic_initial_state", "critic_state"):
            if not payload[key] or any(x.dtype != torch.float32 or not torch.isfinite(x).all() for x in payload[key].values()):
                raise AssertionError("invalid final checkpoint tensors")
        if state_digest(payload["state_dict"]) != record["state_sha256"] or payload["state_sha256"] != record["state_sha256"]:
            raise AssertionError("final actor state identity")
        actor = make_student(protocol.actor_constructor_seeds[lineage]).eval()
        actor.load_state_dict(payload["state_dict"], strict=True)
        critic = fresh_critic(protocol.critic_seeds[lineage])
        initial_critic_sha = state_digest(critic.state_dict())
        if (state_digest(payload["critic_initial_state"]) != initial_critic_sha or
                record["critic_initial_sha256"] != initial_critic_sha or
                record["critic_final_sha256"] != state_digest(payload["critic_state"])):
            raise AssertionError("fresh/final critic identity")
        critic.load_state_dict(payload["critic_state"], strict=True)
        _adam(payload["actor_optimizer"], payload["state_dict"], steps)
        _adam(payload["critic_optimizer"], payload["critic_state"], steps)
        update = batch["updates"][lineage]
        if (update["lineage"] != lineage or update["initial_sha256"] != initial_sha or
                update["final_sha256"] != record["state_sha256"] or update["critic_initial_sha256"] != initial_critic_sha or
                update["critic_final_sha256"] != record["critic_final_sha256"] or
                update["initial_actor_optimizer_entries"] != 0 or update["initial_critic_optimizer_entries"] != 0 or
                update["groups"] != payload["groups"]):
            raise AssertionError("saved training lineage/optimizer initialization changed")
        if update["actor_movement"] != movement(initial_models[lineage].state_dict(), payload["state_dict"]):
            raise AssertionError("actor movement reduction changed")
        if update["critic_movement"] != movement(payload["critic_initial_state"], payload["critic_state"]):
            raise AssertionError("critic movement reduction changed")
        models.append(actor)
        payloads.append(payload)
    return models, payloads


def _update_evidence(batch, payloads, protocol, training):
    for lineage in range(2):
        update = batch["updates"][lineage]
        groups = update["groups"]
        worlds = protocol.training_worlds[lineage]
        if len(groups) != len(worlds) // 2:
            raise AssertionError("group count changed")
        actor_sha, critic_sha = update["initial_sha256"], update["critic_initial_sha256"]
        for number, group in enumerate(groups):
            if group["status"] != "COMPLETE":
                raise AssertionError("incomplete optimizer group")
            selected_worlds = worlds[2 * number:2 * number + 2]
            if (group["group"] != number or group["worlds"] != list(selected_worlds) or
                    group["actor_before_sha"] != actor_sha or group["critic_before_sha"] != critic_sha):
                raise AssertionError("group actor/critic hash chain changed")
            for sha in (group["actor_after_sha"], group["critic_after_sha"]):
                if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
                    raise AssertionError("invalid update state hash")
            episodes = [training[lineage, world] for world in selected_worlds]
            rewards = torch.tensor(np.stack([ep["macro_rewards"] for ep in episodes]), dtype=torch.float32)
            targets = rewards.flip(-1).cumsum(-1).flip(-1) / protocol.horizon
            values = torch.tensor(np.stack([ep["values"] for ep in episodes]), dtype=torch.float32)
            raw = targets - values
            advantage = (raw - raw.mean()) / (raw.std(unbiased=False) + 1e-8)
            for key, tensor in (("target_summary", targets), ("advantage_summary", advantage)):
                expected = dict(min=float(tensor.min()), max=float(tensor.max()), mean=float(tensor.mean()),
                                std=float(tensor.std(unbiased=False)), dtype="torch.float32")
                if group[key] != expected:
                    raise AssertionError("fixed target/advantage reduction changed")
            density = group["initial_identity"]
            rows = 2 * protocol.horizon // 4 * 5
            if (density["logits_exact"] is not True or density["rows"] != rows or
                    not 0 <= density["max_probability_abs"] <= 5e-14 or
                    not 0 <= density["max_chosen_logp_abs"] <= 1e-10 or not 0 <= density["max_ratio_from_one"] <= 1e-10):
                raise AssertionError("recorded first-epoch density identity failed")
            epochs = group["epochs"]
            if len(epochs) != 4:
                raise AssertionError("four paid epochs required")
            old_logp = np.stack([ep["logp"] for ep in episodes])
            for epoch, record in enumerate(epochs):
                if record["actor_step_completed"] is not True or record["critic_step_completed"] is not True:
                    raise AssertionError("incomplete paid optimizer epoch")
                steps = 4 * number + epoch + 1
                if record["epoch"] != epoch:
                    raise AssertionError("epoch order changed")
                for prefix, state_key in (("actor", "state_dict"), ("critic", "critic_state")):
                    expected_steps = [steps] * len(payloads[lineage][state_key])
                    if record[prefix + "_optimizer_step_values"] != expected_steps:
                        raise AssertionError("paid Adam epoch steps changed")
                    if (record[prefix + "_grad_norm"] < 0 or
                            not 0 <= record[prefix + "_clipped_grad_norm"] <= .500001 or
                            record[prefix + "_movement_l2"] < 0):
                        raise AssertionError("invalid gradient/movement evidence")
                if (record["critic_loss"] < 0 or record["ratio_min"] < 0 or record["ratio_max"] < record["ratio_min"] or
                        not record["ratio_min"] <= record["ratio_mean"] <= record["ratio_max"] or
                        not 0 <= record["clip_fraction"] <= 1):
                    raise AssertionError("invalid loss/ratio evidence")
                equal(record["old_logp_mean"], old_logp.mean(), "saved density mean", 1e-14)
                if epoch == 0:
                    equal(record["ratio_min"], 1., "initial ratio minimum", 1e-10)
                    equal(record["ratio_max"], 1., "initial ratio maximum", 1e-10)
                    equal(record["new_logp_mean"], old_logp.mean(), "initial chosen logp mean", 1e-10)
                    equal(record["clip_fraction"], 0., "initial clipping")
                    equal(record["actor_loss"], -5 * float(advantage.double().mean()), "initial smooth surrogate loss", 1e-9)
                    # Collected one-row critic values can differ slightly from
                    # full-rollout FP32 GEMM; this checks the saved first loss
                    # algebra without another critic query.
                    equal(record["critic_loss"], .5 * float((values - targets).square().mean()),
                          "initial saved-value critic loss", 1e-6)
            for prefix, state_key in (("actor", "state_dict"), ("critic", "critic_state")):
                if group[prefix + "_optimizer_step_values"] != [4 * (number + 1)] * len(payloads[lineage][state_key]):
                    raise AssertionError("group Adam steps changed")
            actor_sha, critic_sha = group["actor_after_sha"], group["critic_after_sha"]
        if actor_sha != update["final_sha256"] or critic_sha != update["critic_final_sha256"]:
            raise AssertionError("final hash chain changed")


def _read_result(out, repo, *, allow_fixture, work, start_wall, start_cpu):
    out, repo = Path(out).resolve(), Path(repo).resolve()
    batch = json.loads((out / "summary.json").read_text())
    _finite_tree(batch)
    if batch["object"] != OBJECT or batch["state"] != "COMPLETE" or batch["status"] != "COMPLETE" or "failure" in batch:
        raise ValueError("only the complete fixed B04 object can be read")
    protocol = Protocol.from_dict(batch["protocol"])
    scientific = batch["scientific_execution"]
    if allow_fixture:
        if scientific is not False or protocol == FROZEN:
            raise ValueError("fixture reader requires explicit nonproduction nonscientific evidence")
    elif scientific is not True or protocol != FROZEN:
        raise ValueError("production reader requires frozen scientific execution")
    if source_identities(repo) != batch["sources"]:
        raise AssertionError("recorded source identities changed")
    runtime = batch["runtime"]
    if runtime["device"] != "cpu" or runtime["actor_dtype"] != "float32" or runtime["density_dtype"] != "float64" or runtime["torch_threads"] != 1 or torch.get_num_threads() != 1:
        raise AssertionError("one-thread CPU FP32/FP64 numerical contract changed")
    for key in ("worker_wall_seconds", "worker_cpu_seconds", "worker_max_rss_kib"):
        if batch[key] < 0:
            raise AssertionError("invalid worker resource reading")
    records = batch["initial_assets"]
    if len(records) != 2:
        raise AssertionError("both immutable S assets required")
    bindings = []
    for lineage, record in enumerate(records):
        base = {key: record[key] for key in ("path", "bytes", "sha256", "state_sha256", "launch_sha")}
        if not allow_fixture:
            base.update(canonical_path=record["canonical_path"], canonical_node=record["canonical_node"])
        if record["lineage"] != lineage or record["inherited_optimizer_loaded_for_training"] is not False:
            raise AssertionError("initial asset lineage/optimizer provenance changed")
        if not allow_fixture and base != STAGED_ASSETS[lineage]:
            raise AssertionError("canonical immutable S binding changed")
        bindings.append(base)
    initial_models, checked_records = load_initial_assets(protocol, bindings=bindings, permit_fixture=allow_fixture)
    if checked_records != records:
        raise AssertionError("initial asset metadata changed")
    final_models, payloads = _final_assets(out, batch, protocol, initial_models)
    calibrations = [calibration_result(batch["rows"], lineage, protocol) for lineage in range(2)]
    if calibrations != batch["calibrations"]:
        raise AssertionError("calibration means/winner/tie rule changed")
    evaluations = [evaluation_plan(calibrations[lineage]["winner"], records[lineage]["state_sha256"],
                                    batch["final_assets"][lineage]["state_sha256"], protocol.evaluation_roots[lineage])[1]
                   for lineage in range(2)]
    if evaluations != batch["evaluations"]:
        raise AssertionError("exact identity reuse changed")
    validate_counts(batch, protocol)
    required_forward_rows = protocol.horizon // 4 * 5 * (
        sum(candidate_spec(r["candidate"])["family"] == "S" for r in batch["rows"] if r["kind"] == "evaluation")
        + sum(map(len, protocol.evaluation_worlds)))
    if required_forward_rows > 81920:
        raise AssertionError("reader actor allowance would be exceeded")
    paired_resets, training, verified, raw_paths = {}, {}, [], set()
    for row in batch["rows"]:
        lineage, kind = row["lineage"], row["kind"]
        expected_root = {"training": protocol.training_roots, "calibration": protocol.calibration_roots,
                         "evaluation": protocol.evaluation_roots}[kind][lineage]
        family = candidate_spec(row["candidate"])["family"]
        if kind == "training":
            expected_sha = batch["updates"][lineage]["groups"][row["group"]]["actor_before_sha"]
        else:
            expected_sha = (batch["final_assets"][lineage]["state_sha256"] if row["arm"] == "R"
                            else records[lineage]["state_sha256"]) if family == "S" else None
        if (row["policy_sha256"] != expected_sha or row["sampling_root"] != expected_root or
                row["policy_identity"] != policy_identity(row["candidate"], expected_sha, expected_root)):
            raise AssertionError("row policy/draw source identity changed")
        shadow_sha = records[lineage]["state_sha256"] if kind == "evaluation" and row["arm"] == "R" else None
        if row["shadow_sha256"] != shadow_sha:
            raise AssertionError("row shadow actor identity changed")
        path = identity(out, row["raw"])
        if path in raw_paths:
            raise AssertionError("duplicated raw evidence")
        raw_paths.add(path)
        with np.load(path, allow_pickle=False) as archive:
            raw = {key: archive[key] for key in archive.files}
        actor = (final_models[lineage] if row["arm"] == "R" else initial_models[lineage]) if kind == "evaluation" and family == "S" else None
        _episode(raw, row, protocol, actor, initial_models[lineage], work)
        previous = paired_resets.setdefault(row["world"], row["initial_state_sha256"])
        if previous != row["initial_state_sha256"]:
            raise AssertionError("same-world training/calibration/final reset identity changed")
        if kind == "training":
            training[lineage, row["world"]] = {key: raw[key] for key in ("macro_rewards", "values", "logp")}
        verified.append(dict(lineage=lineage, kind=kind, arm=row["arm"], world=row["world"], raw_sha256=row["raw"]["sha256"]))
    if set((out / "raw").glob("*.npz")) != raw_paths:
        raise AssertionError("unreferenced/missing raw NPZ evidence")
    _update_evidence(batch, payloads, protocol, training)
    reduced = comparisons(batch["rows"], protocol, evaluations)
    if reduced != batch["comparisons"]:
        raise AssertionError("comparison reductions changed")
    if work["actor_forward_rows"] != required_forward_rows or work["shadow_motion_ticks"] != protocol.expected()["shadow_motion_ticks"]:
        raise AssertionError("reader work accounting mismatch")
    return dict(object=OBJECT, status="VERIFIED", launch_sha=batch["launch_sha"], scientific_execution=scientific,
                summary=file_identity(out / "summary.json"), sources=batch["sources"], initial_assets=records,
                final_assets=batch["final_assets"], raw_files=len(raw_paths), raw_bytes=sum(r["raw"]["bytes"] for r in batch["rows"]),
                expected_maximum=batch["expected_maximum"], expected_realized=batch["expected_realized"], actual=batch["actual"],
                calibrations=calibrations, evaluations=evaluations, comparisons=reduced, costs=batch["costs"],
                per_row=verified, reader_calls=work,
                scope="all saved identities, clocks, holds, native metric/motion reductions, local feature/navigation provenance, "
                      "memo costs, private draws, calibration/reuse/comparison reductions, endpoint/shadow logits and kinematics, "
                      "critic input provenance and saved update/Adam/hash-chain evidence; no radio, native or optimization replay; "
                      "training/calibration logits and all critic outputs are algebra-checked saved evidence only",
                reader_wall_seconds=time.perf_counter() - start_wall, reader_cpu_seconds=time.process_time() - start_cpu,
                reader_rss_scope="process high-water RSS; includes any preceding worker in the same process, not incremental reader RSS",
                reader_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def read_result(out: Path, repo: Path, *, allow_fixture=False):
    """Verify once in production, preserving paid work on failure in reading.json.

    Explicit synthetic fixtures may repeat, and do not write a reading record.
    Failure exceptions also carry ``reader_work`` for their calling runner.
    """
    out, repo = Path(out).resolve(), Path(repo).resolve()
    work = dict(actor_forward_rows=0, evaluation_actor_rows=0, shadow_actor_rows=0, shadow_motion_ticks=0,
                native_team_ticks_verified=0, native_agent_motion_ticks_verified=0, fallback_ranking_motion_ticks=0,
                native=0, radio_power_model=0, expert_queries=0, training_actor_rows=0,
                calibration_actor_rows=0, critic_forward_rows=0, optimizer=0)
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    reading_path = out / "reading.json"
    if not allow_fixture:
        # Exclusive creation guards this selected read even before any actor query.
        try:
            with reading_path.open("x", encoding="utf-8") as stream:
                json.dump(dict(object=OBJECT, status="INCOMPLETE", reader_calls=dict(work)), stream)
                stream.write("\n")
        except OSError as error:
            error.reader_work = dict(object=OBJECT, status="REFUSED", reader_calls=dict(work),
                                     reader_wall_seconds=time.perf_counter() - start_wall,
                                     reader_cpu_seconds=time.process_time() - start_cpu)
            raise
    try:
        result = _read_result(out, repo, allow_fixture=allow_fixture, work=work,
                              start_wall=start_wall, start_cpu=start_cpu)
        if not allow_fixture:
            write_json(reading_path, result)
        return result
    except BaseException as error:
        failure = dict(object=OBJECT, status="FAILED", failure=dict(type=type(error).__name__, message=str(error)),
                       interrupted_call_work_may_be_unmeasured=True,
                       reader_calls=dict(work), reader_wall_seconds=time.perf_counter() - start_wall,
                       reader_cpu_seconds=time.process_time() - start_cpu,
                       reader_rss_scope="process high-water RSS; includes any preceding worker in the same process, not incremental reader RSS",
                       reader_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        error.reader_work = failure
        if not allow_fixture:
            try:
                write_json(reading_path, failure)
            except OSError as write_error:
                error.reader_record_write_error = str(write_error)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    torch.set_num_threads(1)
    result = read_result(args.out, ROOT)
    print(json.dumps({key: result[key] for key in ("status", "raw_files", "reader_cpu_seconds")}))


if __name__ == "__main__":
    main()
