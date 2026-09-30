"""Bounded warm-start training; admission and final evaluation belong to the runner."""
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
import hashlib
import time
import resource

import numpy as np
import torch

from experiments.candidates.load_critical_member_generalization.load_probe import probe as source
from experiments.candidates.agent_count_generalization import runner as shared
from experiments.candidates.agent_count_generalization.action_law_b03 import runner as b03
from experiments.candidates.uav_fleet_transmission.control import choose_mask, decode_public_state, predict_next
from experiments.candidates.uav_fleet_transmission.study import artifact, metrics
from .host import TRAIN_WORLD_IDS, make_env, mask_bits, mask_integer, runtime_seed

FIT_SEED = 29316101
PARENT = source.SourcePolicy("H6", 942201, "s1_action_law_b03_h6_clip_s942201")
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PARENT_SUMMARY_ROOT = Path(__file__).resolve().parent / "inputs"
PARENT_SUMMARY_SHA256 = "55a994c81f49a9b97b52efa4ddaea82579e1068ea3a7ddbd11c8b7645bf88921"
PARENT_SUMMARY_ORIGIN = {
    "path": "runs/agent_count_generalization/" + PARENT.tag + "/summary.json",
    "git_revision": "bf452481d2b951fe4e484e70858704c21eec5ed8",
    "sha256": PARENT_SUMMARY_SHA256,
    "bytes": 737415,
}


@dataclass(frozen=True)
class TrainSpec:
    groups: int = 32
    lanes: int = 16
    horizon: int = 500

    def validate(self):
        if self != TrainSpec():
            raise ValueError("the prospective fit is fixed at 32 groups,16 lanes,H500")


def load_parent(checkpoint_root):
    # Launcher snapshots include this direction's source tree but can omit runs/.
    # Keep the frozen loader's HEAD/working-byte check on an exact bound input.
    summary_bytes = (PARENT_SUMMARY_ROOT / PARENT.tag / "summary.json").read_bytes()
    if (len(summary_bytes) != PARENT_SUMMARY_ORIGIN["bytes"]
            or hashlib.sha256(summary_bytes).hexdigest() != PARENT_SUMMARY_SHA256):
        raise ValueError("bound parent metadata differs from its pinned original")
    record = source.load_source_policy(
        Path(checkpoint_root), PARENT,
        tracked_summary_root=PARENT_SUMMARY_ROOT, repository_root=REPOSITORY_ROOT)
    record["summary_identity"]["origin"] = dict(PARENT_SUMMARY_ORIGIN)
    return record


def _array_digest(value):
    return source._array_digest(np.asarray(value))


def build_warmstart(record, log_dir, *, payload=None):
    """Restore only weights/normalizers, preserving caller RNG and fresh runtime.

    Endpoint payloads use the original checkpoint format. The caller must check
    their file binding and expected parameter/normalizer digest before evaluation.
    No study world is constructed to determine the fixed dimensional contract.
    """
    if record["source"] != PARENT:
        raise ValueError("warm-start requires the selected full-H6 B03 parent")
    before = b03._rng_digest()
    with shared.preserve_rng():
        shared.seed_rng(record["source"].seed)
        shape = SimpleNamespace(n_uavs=8, state_dim=133, obs_dim=104)
        config = source.make_config("H6", [shape] * 16, PARENT.seed, record["source_spec"])
        source._assert_reconstructed_config(config, record, 8)
        if (config.use_obsnorm or config.use_statenorm
                or any(getattr(config, name, False) for name in (
                    "disable_high_level_training", "disable_discriminator_training", "disable_discriminator_rewards"))):
            raise ValueError("full H6 objectives and unnormalized local/state inputs required")
        agent = source.build_agent(config, str(log_dir))
        source.restore_checkpoint(agent, record["payload"] if payload is None else payload)
        for lane in range(config.num_envs):
            agent.reset_env_state(lane)
        agent.train(False)
        digest = source.digest_agent(agent)
        if payload is None and digest != record["summary"]["final_parameter_normalizer_digest"]:
            raise ValueError("warm-start differs from retained final45 modules/normalizers")
        optimizer_states = {
            name: len(getattr(agent, name + "_optimizer").state)
            for name in shared.OPTIMIZERS
            if getattr(agent, name + "_optimizer", None) is not None
        }
        if any(optimizer_states.values()) or np.any(agent.rollout_buffer.env_lengths) or len(agent.discriminator_buffer):
            raise ValueError("warm-start inherited optimizer or replay state")
        initialization = {
            "parameter_normalizer_digest": digest,
            "normalizers": source._normalizer_record(agent),
            "optimizer_state_entries": optimizer_states,
            "buffer_env_lengths": agent.rollout_buffer.env_lengths.tolist(),
            "discriminator_records": len(agent.discriminator_buffer),
            "runtime_digest": b03.runtime_state_digest(agent),
            "rollout_sampler_seed": int(agent.rollout_sampler_seed),
            "sampler_rng_state": agent.rollout_buffer.get_sampler_rng_state(),
            "checkpoint_usage": "weights/normalizers only; fresh Adam,buffers,GRU,skills,RNG",
        }
    if before != b03._rng_digest():
        raise ValueError("construction/restoration changed caller RNG")
    return agent, config, initialization


def _snapshot(envs, states, observations, arrays):
    natives = [env.env.env for env in envs]
    for key, value in {
        "states": states, "observations": observations,
        "positions": np.stack([env.uav_positions for env in natives]),
        "sinr": np.stack([env.sinr_matrix for env in natives]),
        "connections": np.stack([env.connections for env in natives]),
        "visible_users": np.asarray([[len(env._local_user_entries(i)[0][:env.max_observed_users])
                                       for i in range(8)] for env in natives]),
        "visible_peers": np.asarray([[len(env._local_uav_entries(i)[0][:env.max_observed_uavs])
                                       for i in range(8)] for env in natives]),
    }.items():
        arrays[key].append(np.asarray(value).copy())


def collect_group(agent, envs, states, observations, *, arm, world_ids, horizon, progress=None):
    """One complete rollout; synthetic fixtures may supply their own environments."""
    if arm not in {"A", "F"} or len(envs) != agent.config.num_envs or len(world_ids) != len(envs):
        raise ValueError("arm/lane contract mismatch")
    arrays = {key: [] for key in (
        "states", "observations", "positions", "sinr", "connections", "visible_users", "visible_peers",
        "raw_actions", "actions", "action_logprobs", "scalar_reward", "components",
        "terminated", "truncated", "dones", "old_mask", "requested_mask", "mask",
        "skill_changed", "team_skills", "agent_skills", "stored_valid")}
    steps, dones = np.zeros(len(envs), dtype=np.int64), np.zeros(len(envs), dtype=bool)
    masks = np.full(len(envs), 255, dtype=np.int64)
    decisions = []
    _snapshot(envs, states, observations, arrays)
    reset_digest = {"states": _array_digest(states), "observations": _array_digest(observations),
                    "positions": _array_digest(arrays["positions"][0])}
    telemetry = b03._new_motion()
    for t in range(horizon):
        if progress is not None:
            progress("actor_started", t=t)
        raw, _, data = agent.step(states, observations, steps, dones, deterministic=False,
                                  return_step_data=True, build_infos=False)
        if progress is not None:
            progress("actor", t=t)
        shared.finite((raw, data), "warm-start collection")
        raw_before, logprob = raw.copy(), np.asarray(data["action_logprobs"]).copy()
        command = np.clip(raw, -1., 1.)
        old_masks = masks.copy()
        rng_before = b03._rng_digest()
        if t % 10 == 0 and arm == "F":
            for lane, env in enumerate(envs):
                positions, users = decode_public_state(states[lane], 8)
                masks[lane], trace = choose_mask(users, predict_next(positions, command[lane]), int(masks[lane]))
                # Discard setter feedback: the sole actor call consumed old-mask feedback.
                env.env.env.set_transmitter_mask(mask_bits(int(masks[lane]), 8))
                decisions.append({"t": t, "lane": lane, "world_id": int(world_ids[lane]),
                                  "old_mask": int(old_masks[lane]), "selected_mask": int(masks[lane]),
                                  "selected_score": trace["selected_score"], "old_score": trace["old_score"],
                                  "counts": {key: value for key, value in trace.items()
                                             if key.endswith("candidates") or key.startswith("geometry_rows")}})
        if b03._rng_digest() != rng_before:
            raise ValueError("E/diagnostics consumed global fit RNG")
        next_states, next_obs, rewards, terms, truncs, components = [], [], [], [], [], []
        for lane, env in enumerate(envs):
            native = env.env.env
            if mask_integer(native.transmitter_mask) != int(masks[lane]):
                raise ValueError("requested/native transmitter mask mismatch")
            before = native.uav_positions.copy()
            obs, reward, term, trunc, info = env.step(command[lane])
            if progress is not None:
                progress("native", t=t, lane=lane, done=bool(term or trunc))
            if bool(term or trunc) != (t == horizon - 1):
                raise ValueError("native episode boundary differs from complete rollout")
            parts = shared.native_components(info, reward, 8)
            b03._observe_motion(telemetry, native, before, raw[lane], command[lane],
                                native.uav_positions, rollout=0, t=t, lane=lane, reward=reward, components=parts)
            next_states.append(info["next_state"])
            next_obs.append(obs)
            rewards.append(reward)
            terms.append(term)
            truncs.append(trunc)
            components.append([parts[key] for key in shared.COMPONENTS])
        next_states, next_obs = np.stack(next_states), np.stack(next_obs)
        dones = np.logical_or(terms, truncs)
        agent.store_transition_batch(states=states, next_states=next_states.copy(), observations=observations,
                                     next_observations=next_obs.copy(), actions=raw, rewards=np.asarray(rewards),
                                     dones=dones, infos_batch=None, rollout_step_idx=t, step_data=data)
        if progress is not None:
            progress("stored", t=t, team_steps=len(envs))
        buffer = agent.rollout_buffer
        if (not np.array_equal(raw, raw_before) or not np.array_equal(data["action_logprobs"], logprob)
                or not np.array_equal(buffer.actions[t], raw_before)
                or not np.array_equal(buffer.log_probs[t], logprob)
                or not np.array_equal(buffer.obs[t], observations)
                or not np.array_equal(buffer.states[t], states)):
            raise ValueError("raw action/logprob/old feedback changed before or during storage")
        for key, value in {
            "raw_actions": raw_before, "actions": command, "action_logprobs": logprob,
            "scalar_reward": rewards, "components": components, "terminated": terms, "truncated": truncs,
            "dones": dones, "old_mask": old_masks, "requested_mask": masks, "mask": masks,
            "skill_changed": data["skill_changed"], "team_skills": data["team_skills"],
            "agent_skills": data["agent_skills"], "stored_valid": buffer.masks[t],
        }.items():
            arrays[key].append(np.asarray(value).copy())
        states, observations = next_states, next_obs
        _snapshot(envs, states, observations, arrays)
        steps += 1
    arrays = {key: np.asarray(value) for key, value in arrays.items()}
    for key, field in {"reward_env": "reward_env", "reward_team_disc": "reward_team_disc",
                       "reward_ind_disc": "reward_ind_disc", "learner_rewards": "rewards",
                       "values": "values", "high_level_valid": "high_level_valid_mask"}.items():
        arrays[key] = np.asarray(getattr(agent.rollout_buffer, field)[:horizon]).copy()
    arrays["world_ids"] = np.asarray(world_ids, dtype=np.int64)
    arrays["users"] = np.stack([env.env.env.user_positions for env in envs])
    per_world = []
    for lane, world_id in enumerate(world_ids):
        raw_world = {key: arrays[key][:, lane] for key in (
            "connections", "sinr", "components", "positions", "mask", "visible_users", "visible_peers")}
        per_world.append({"world_id": int(world_id), **metrics(raw_world, 8),
                          "scalar_return": float(arrays["scalar_reward"][:, lane].sum())})
    # Source reset occurs after final transition storage, before terminal update.
    # Complete episodes make both GAE terminal indicators true, including H truncation.
    with shared.preserve_rng():
        pairs = []
        for lane, env in enumerate(envs):
            pairs.append(env.reset())
            if progress is not None:
                progress("reset", lane=lane)
    for lane in range(len(envs)):
        agent.reset_env_state(lane)
    update_states = np.stack([info["state"] for obs, info in pairs])
    update_obs = np.stack([obs for obs, info in pairs])
    return arrays, {"reset_digest": reset_digest, "per_world": per_world,
                    "mask_decisions": decisions, "action_motion_telemetry": b03._finish_motion(telemetry, 8)}, update_states, update_obs, dones


def audited_update(agent, last_states, last_observations, dones, horizon, *, audit_target=None):
    """Observe real sampler batches and discriminator training forwards, without extra sampling."""
    buffer = agent.rollout_buffer
    audit = {"discoverer": {"batches": [], "sample_presentations": 0, "valid_presentations": 0},
             "coordinator": {"batch_sizes": [], "sample_presentations": 0},
             "discriminator": {}}
    if audit_target is not None:
        audit_target.update(audit)
        audit = audit_target
    originals, handles = {}, []
    for name in ("get_discoverer_sampler", "get_coordinator_sampler"):
        original = getattr(buffer, name)
        originals[name] = original

        def wrapper(*args, _original=original, _name=name, **kwargs):
            rows = _original(*args, **kwargs)
            if rows is None:
                return
            for batch in rows:
                if _name == "get_discoverer_sampler":
                    t, b = map(int, batch["observations"].shape[:2])
                    row = audit["discoverer"]
                    row["batches"].append([t, b])
                    row["sample_presentations"] += t * b
                    row["valid_presentations"] += int(batch["masks"].sum())
                else:
                    b = int(batch["observations"].shape[0])
                    row = audit["coordinator"]
                    row["batch_sizes"].append(b)
                    row["sample_presentations"] += b
                yield batch

        setattr(buffer, name, wrapper)
    for name, kind in (("team_discriminator", "team"), ("individual_discriminator", "individual")):
        audit["discriminator"][kind] = {
            "records": sum(row["type"] == kind for row in agent.discriminator_buffer.buffer),
            "batch_sizes": [], "sample_presentations": 0}

        def forward(_module, args, _output, _kind=kind):
            if torch.is_grad_enabled():
                b = int(args[0].shape[0])
                row = audit["discriminator"][_kind]
                row["batch_sizes"].append(b)
                row["sample_presentations"] += b

        handles.append(getattr(agent, name).register_forward_hook(forward))
    calls, optimizer_hooks = shared.optimizer_counts(agent)
    audit["optimizer_calls"] = calls
    audit["configured_epochs"] = int(agent.config.ppo_epochs)
    audit["num_actual_time_steps"] = horizon
    audit["dropped_time_tail_steps"] = horizon % agent.config.k if horizon >= agent.config.k else 0
    try:
        losses = agent.update(last_values=np.zeros((len(dones), 8), dtype=np.float32),
                              dones=dones.copy(), steps_in_buffer=horizon,
                              last_state=last_states.copy(), last_observations=last_observations.copy())
        shared.finite(losses, "full H6 update losses")
    finally:
        for name, original in originals.items():
            setattr(buffer, name, original)
        for handle in handles + optimizer_hooks:
            handle.remove()
    return losses, audit


def _assert_production_update(audit):
    expected = {"coordinator": 15, "discoverer_actor": 3000, "discoverer_critic": 3000,
                "team_discriminator": 15, "individual_discriminator": 60}
    if audit["optimizer_calls"] != expected:
        raise ValueError(f"actual full-H6 optimizer exposure changed: {audit['optimizer_calls']}")
    observed = (audit["discoverer"]["sample_presentations"], audit["discoverer"]["valid_presentations"],
                audit["coordinator"]["sample_presentations"],
                audit["discriminator"]["team"]["records"],
                audit["discriminator"]["team"]["sample_presentations"],
                audit["discriminator"]["individual"]["records"],
                audit["discriminator"]["individual"]["sample_presentations"], audit["dropped_time_tail_steps"])
    if observed != (960000, 960000, 12000, 8000, 120000, 64000, 960000, 0):
        raise ValueError(f"actual full-H6 sampler/discriminator exposure changed: {observed}")


def save_endpoint(agent, out, config, launch_sha):
    """Original weights/normalizer checkpoint schema, with direction identity."""
    binding = shared.save_checkpoint(agent, Path(out), 32, config, launch_sha)
    path = Path(out) / binding["path"]
    payload = torch.load(path, map_location="cpu", weights_only=True)
    payload["direction"] = "uav_fleet_adaptation"
    partial = path.with_suffix(".pt.partial")
    torch.save(payload, partial)
    partial.replace(path)
    return artifact(path, Path(out))


def train_arm(arm, record, out, launch_sha, spec=TrainSpec()):
    """Execute the fixed fit only after caller admission; retain final alive eval agent."""
    spec.validate()
    if arm not in {"A", "F"}:
        raise ValueError("only fixed A/F continuations may train")
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError("fit output is not empty; reconcile its original attempt")
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    started, cpu_started = time.perf_counter(), time.process_time()
    summary = {"schema": 1, "direction": "uav_fleet_adaptation", "arm": arm,
               "launch_sha": launch_sha, "fit_seed": FIT_SEED, "spec": asdict(spec),
               "source_checkpoint": record["checkpoint_record"],
               "status": "initializing", "fit_started": False,
               "counts": {"training_team_steps": 0, "stored_team_steps": 0, "training_episodes": 0,
                          "updates": 0, "terminal_resets": 0, "actor_calls": 0,
                          "evaluation_team_steps": 0, "evaluation_episodes": 0, "update_attempts": 0},
               "optimizer_calls": {name: 0 for name in shared.OPTIMIZERS}, "rollouts": [],
               "gae_terminal_semantics": "done=terminated|truncated; zero last low values; inherited source terminal-as-done",
               "action_law": "raw FP32 Gaussian/logprob in replay; componentwise clip for execution"}
    shared.write_json(out / "summary.json", summary)
    envs, agent, row = [], None, None
    try:
        agent, config, initialization = build_warmstart(record, out / "learner_logs")
        shared.seed_rng(FIT_SEED)  # Only after full construction + strict restoration.
        initial = shared.capture_parameters(agent)
        summary.update(config=source.config_dict(config), initialization=initialization,
                       post_restore_fit_rng_digest=b03._rng_digest(), status="training")
        agent.train(True)
        for group in range(1, spec.groups + 1):
            group_start = time.perf_counter()
            ids = TRAIN_WORLD_IDS[(group - 1) * spec.lanes:group * spec.lanes]
            rng_before = b03._rng_digest()
            with shared.preserve_rng():
                for world_id in ids:
                    envs.append(make_env(world_id, spec.horizon))
                pairs = [env.reset(seed=runtime_seed(world_id)) for env, world_id in zip(envs, ids)]
            if rng_before != b03._rng_digest():
                raise ValueError("world construction/reset changed fit RNG")
            states = np.stack([info["state"] for obs, info in pairs])
            observations = np.stack([obs for obs, info in pairs])
            row = {"group": group, "world_ids": list(ids), "status": "collecting",
                   "counts_before": summary["counts"].copy()}
            summary["rollouts"].append(row)

            def progress(event, **values):
                row["last_collection_event"] = {"event": event, **values}
                counts = summary["counts"]
                if event == "actor_started":
                    summary["fit_started"] = True
                elif event == "actor":
                    counts["actor_calls"] += 1
                elif event == "native":
                    counts["training_team_steps"] += 1
                    counts["training_episodes"] += int(values["done"])
                elif event == "stored":
                    counts["stored_team_steps"] += values["team_steps"]
                elif event == "reset":
                    counts["terminal_resets"] += 1

            arrays, collection, last_states, last_obs, dones = collect_group(
                agent, envs, states, observations, arm=arm, world_ids=ids, horizon=spec.horizon, progress=progress)
            row.update(collection, reset_global_rng_digest=rng_before,
                       collection_wall_seconds=time.perf_counter() - group_start)
            path = out / "raw" / f"group_{group:02d}.npz"
            with path.open("xb") as stream:
                np.savez_compressed(stream, **arrays)
            row["collection"] = artifact(path, out)
            del arrays
            for env in envs:
                env.close()
            envs = []
            update_start = time.perf_counter()
            row["status"] = "updating"
            row["sampler_audit"] = {}
            summary["counts"]["update_attempts"] += 1
            shared.write_json(out / "summary.json", summary)
            try:
                losses, audit = audited_update(agent, last_states, last_obs, dones, spec.horizon,
                                                audit_target=row["sampler_audit"])
            finally:
                for name, calls in row["sampler_audit"].get("optimizer_calls", {}).items():
                    summary["optimizer_calls"][name] += calls
            summary["counts"]["updates"] += 1
            row.update(losses=shared.jsonable(losses), sampler_audit=audit,
                       optimizer_delta=audit["optimizer_calls"], parameter_motion=shared.parameter_motion(agent, initial),
                       update_wall_seconds=time.perf_counter() - update_start,
                       group_wall_seconds=time.perf_counter() - group_start)
            _assert_production_update(audit)
            agent.clear_buffers()
            row["status"] = "complete"
            row["counts_delta"] = {key: value - row["counts_before"][key]
                                   for key, value in summary["counts"].items()}
            summary["parameter_motion"] = row["parameter_motion"]
            summary["wall_seconds"] = time.perf_counter() - started
            shared.write_json(out / "summary.json", summary)
        actual = summary["counts"]
        expected = {"training_team_steps": 256000, "stored_team_steps": 256000,
                    "training_episodes": 512, "terminal_resets": 512, "actor_calls": 16000,
                    "updates": 32, "update_attempts": 32, "evaluation_team_steps": 0, "evaluation_episodes": 0}
        if actual != expected:
            raise ValueError(f"fixed fit exposure incomplete: {actual}")
        summary["checkpoint"] = save_endpoint(agent, out, config, launch_sha)
        summary["final_parameter_normalizer_digest"] = shared.digest_agent(agent)
        summary["status"] = "complete"
        agent.train(False)
    except Exception as error:
        summary.update(status="failed", failure=f"{type(error).__name__}: {error}")
        if row is not None:
            failed_phase = row["status"]
            row.update(status="failed", failure=summary["failure"])
            if agent is not None and failed_phase in {"collecting", "updating"}:
                # A failed batch store can have written some lanes before raising.
                summary["counts"]["stored_team_steps"] = (
                    row["counts_before"]["stored_team_steps"] + int(agent.rollout_buffer.env_lengths.sum()))
        raise
    finally:
        for env in envs:
            env.close()
        summary["wall_seconds"] = time.perf_counter() - started
        summary["cpu_seconds"] = time.process_time() - cpu_started
        summary["peak_rss_kib_process"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        summary["rss_scope"] = "current process lifetime, including imports and preceding arms"
        shared.write_json(out / "summary.json", summary)
    return agent, summary
