"""One full saved-data reading; no native branch or later-epoch optimizer replay."""
from copy import deepcopy
import json
from pathlib import Path
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.audit import equal, require
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.assets import checked_path
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.study import load_raw
from experiments.candidates.uav_local_history.b01.study import write_json
from .assets import load_assets
from .audit import audit_episode
from .contract import ENDPOINTS, FROZEN, OBJECT, Protocol, source_identities
from .learning import JointActor, fresh_critic
from .reading import comparisons
from .records import artifact, movement, nested_digest
from .study import validate_counts


def _state(out, identity, *, program, group, launch_sha):
    saved = torch.load(checked_path(out, identity["path"], identity), map_location="cpu", weights_only=True)
    require(saved["program"] == program and saved["block"] == ENDPOINTS.index(program)
            and saved["launch_sha"] == launch_sha, "saved state identity")
    if group is not None:
        require(saved["group"] == group, "pregroup identity")
    for name, input_size, output_size in (("actor", 114, 54), ("critic", 146, 1)):
        shapes = {"network.0.weight": (128, input_size), "network.0.bias": (128,),
                  "network.2.weight": (128, 128), "network.2.bias": (128,),
                  "network.4.weight": (output_size, 128), "network.4.bias": (output_size,)}
        state = saved[name + "_state"]
        require(set(state) == set(shapes), "complete " + name + " parameter roster")
        for key, shape in shapes.items():
            require(state[key].shape == shape and state[key].dtype == torch.float32 and torch.isfinite(state[key]).all(),
                    "finite FP32 " + name + " parameter")
        require(state_digest(state) == saved[name + "_sha256"], "saved parameter digest")
    return saved


def _summary(value):
    return dict(min=float(value.min()), max=float(value.max()), mean=float(value.mean()),
                std=float(value.std(unbiased=False)), dtype=str(value.dtype))


def _group_read(record, raws, horizon, previous_state, next_state, expected_offset):
    require(record["status"] == "COMPLETE" and len(record["epochs"]) == 4, "complete four-epoch ledger")
    rewards = torch.from_numpy(np.stack([raw["macro_rewards"] for raw in raws])).to(torch.float32)
    target = torch.flip(torch.cumsum(torch.flip(rewards, [-1]), dim=-1), [-1]) / horizon
    values = torch.from_numpy(np.stack([raw["values"] for raw in raws]))
    residual = target - values
    advantage = (residual - residual.mean()) / (residual.std(unbiased=False) + 1e-8)
    for field, tensor in (("target_summary", target), ("advantage_summary", advantage)):
        expected = _summary(tensor)
        require(record[field]["dtype"] == expected["dtype"], "target/advantage dtype")
        for key in ("min", "max", "mean", "std"):
            equal(record[field][key], expected[key], "independent " + field + " " + key)
    # Policy/critic forwards have already been independently reconstructed from
    # the pregroup tensors. Rebuild first-epoch algebra without another forward.
    z = torch.from_numpy(np.stack([raw["logits"] for raw in raws])).double()
    prior = torch.from_numpy(np.stack([raw["prior"] for raw in raws]))
    eligible = torch.from_numpy(np.stack([raw["eligible"] for raw in raws]))
    available = torch.cat((torch.ones_like(z[..., :27], dtype=torch.bool), eligible[..., None].expand(*eligible.shape, 27)), -1)
    maximum = z.masked_fill(~available, -float("inf")).max(-1, keepdim=True).values
    exponentials = torch.where(available, torch.exp(torch.where(available, z - maximum, torch.zeros_like(z))), 0.)
    factors = torch.repeat_interleave(prior, 27, dim=-1)
    weights = exponentials * factors
    probability = weights / weights.sum(-1, keepdim=True)
    old = torch.from_numpy(np.stack([raw["probabilities"] for raw in raws]))
    actions = torch.from_numpy(np.stack([raw["action_index"] for raw in raws]))
    chosen = probability.gather(-1, actions[..., None]).squeeze(-1)
    old_chosen = old.gather(-1, actions[..., None]).squeeze(-1)
    logp = torch.from_numpy(np.stack([raw["logp"] for raw in raws]))
    identity = dict(logits_exact=True, rows=chosen.numel(), max_probability_abs=float((probability - old).abs().max()),
                    max_chosen_logp_abs=float((chosen.log() - logp).abs().max()),
                    max_ratio_from_one=float((chosen / old_chosen - 1.).abs().max()))
    for key, value in identity.items():
        equal(record["initial_identity"][key], value, "first-epoch density " + key, tolerance=1e-15 if type(value) is float else None)
    ratio = chosen / old_chosen
    first_loss = -torch.minimum(ratio * advantage[..., None], ratio.clamp(.8, 1.2) * advantage[..., None]).sum(-1).mean()
    equal(record["epochs"][0]["actor_loss"], float(first_loss), "first all-five sum-surrogate loss", tolerance=1e-14)
    first_critic_loss = float(.5 * (values - target).square().mean())
    equal(record["epochs"][0]["critic_loss"], first_critic_loss, "first critic loss from independently checked row values",
          tolerance=3e-6 * max(1., first_critic_loss))
    for epoch, value in enumerate(record["epochs"]):
        require(value["epoch"] == epoch and value["actor_step_completed"] and value["critic_step_completed"], "ordered completed steps")
        for field in ("actor_loss", "critic_loss", "actor_grad_norm", "critic_grad_norm", "actor_clipped_grad_norm",
                      "critic_clipped_grad_norm", "actor_movement_l2", "critic_movement_l2", "ratio_min", "ratio_max",
                      "ratio_mean", "clip_fraction", "old_logp_mean", "new_logp_mean"):
            require(np.isfinite(value[field]), "finite update ledger " + field)
        require(value["critic_loss"] >= 0 and 0 <= value["clip_fraction"] <= 1 and value["ratio_min"] > 0
                and value["ratio_min"] <= value["ratio_mean"] <= value["ratio_max"], "loss/ratio ledger domain")
        for name in ("actor", "critic"):
            equal(value[name + "_optimizer_step_values"], np.full(6, record["group"] * 4 + epoch + 1), "continuing Adam steps")
            # B04 uses FP32 clip_grad_norm_: synthetic FP64 reconstruction
            # measured a 1.45e-6 excess. This is a numerical ledger tolerance,
            # not a changed clip threshold or a gradient replay claim.
            require(0 <= value[name + "_clipped_grad_norm"] <= .50001, "separate clipped-gradient diagnostic")
    for name in ("actor", "critic"):
        equal(record[name + "_optimizer_step_values"], np.full(6, (record["group"] + 1) * 4), "terminal group Adam steps")
        require(record[name + "_before_sha256"] == previous_state[name + "_sha256"]
                and record[name + "_after_sha256"] == next_state[name + "_sha256"], "group parameter chain")
        delta = torch.cat([(next_state[name + "_state"][key] - previous_state[name + "_state"][key]).reshape(-1)
                           for key in previous_state[name + "_state"]])
        l2 = float(torch.linalg.vector_norm(delta))
        equal(record[name + "_movement_l2"], l2, "group parameter movement", tolerance=2e-7 * max(1., l2))
    clocks = 2 * horizon // 4
    increments = dict(actor_optimizer_steps=4, critic_optimizer_steps=4, actor_replay_rows=clocks * 5 * 4,
                      critic_replay_rows=clocks * 4, density_identity_rows=clocks * 5)
    for key, increment in increments.items():
        equal(record["completed_counts"][key], expected_offset * increment, "cumulative update exposure " + key)
    return dict(target_summary=_summary(target), advantage_summary=_summary(advantage), initial_identity=identity,
                first_actor_loss=float(first_loss), first_critic_loss_from_row_values=first_critic_loss, no_optimizer_replay=True)


def _read_all(batch, out, parent, gate, protocol, report, publish):
    out = Path(out)
    expected_order = [("training", program, world, None, block, wi // 2) for block, program in enumerate(ENDPOINTS)
                      for wi, world in enumerate(protocol.training_worlds[block])]
    expected_order.extend(("evaluation", program, world, tape, None, None) for wi, world in enumerate(protocol.worlds)
                          for program, tape in protocol.episode_order(wi))
    keys = ("kind", "program", "world", "tape", "block", "group")
    require([tuple(row[key] for key in keys) for row in batch["rows"]] == expected_order, "complete frozen execution order")
    require([(fit["block"], fit["program"]) for fit in batch["fits"]] == list(enumerate(ENDPOINTS)), "fixed two-fit order")
    counts, inflight = report["actual"], report["inflight"]
    audits, cursor, group_offset = [], 0, 0
    endpoints, initial_layouts = {}, {}
    initial_actor = JointActor(parent, seed=protocol.actor_constructor_seed).eval().requires_grad_(False)
    require(state_digest(initial_actor.state_dict()) == batch["initial_joint_state"], "original exact warm-copy identity")
    report["fit_audits"] = {}
    def episode(row, actor=None, critic=None):
        raw = load_raw(checked_path(out, row["raw"]["path"], row["raw"]))
        require(row["raw_array_bytes"] == sum(value.nbytes for value in raw.values()), "complete array byte count")
        report["progress"] = dict(stage="episode", id=row["id"])
        audits.append(audit_episode(raw, row, protocol, parent, gate, actor=actor, critic=critic, counts=counts, inflight=inflight))
        report["policy_costs"] = sum_counts(item["policy_counts"] for item in audits)
        layout = raw["positions"][0].tobytes() + raw["initial_users"].tobytes()
        if row["world"] in initial_layouts:
            require(initial_layouts[row["world"]] == layout, "common paired layout")
        else:
            require(layout not in initial_layouts.values(), "distinct world layout")
            initial_layouts[row["world"]] = layout
        publish()
        return raw
    for block, program in enumerate(ENDPOINTS):
        fit, worlds = batch["fits"][block], protocol.training_worlds[block]
        require(fit["status"] == "COMPLETE" and len(fit["groups"]) == len(worlds) // 2, "all training groups complete")
        states = [_state(out, record["precollection_state"], program=program, group=i, launch_sha=batch.get("launch_sha"))
                  for i, record in enumerate(fit["groups"])]
        final = _state(out, fit["endpoint"], program=program, group=None, launch_sha=batch.get("launch_sha"))
        states.append(final)
        actor = JointActor(parent, seed=protocol.actor_constructor_seed).eval().requires_grad_(False)
        # Prescribed Critic146 forward retains B04's trainable-parameter guard;
        # inference_mode in the episode reader prevents graph/update effects.
        critic = fresh_critic(protocol.critic_seeds[block]).eval()
        require(state_digest(actor.state_dict()) == states[0]["actor_sha256"] == fit["initial_actor_sha256"], "shared original joint initialization")
        require(state_digest(critic.state_dict()) == states[0]["critic_sha256"] == fit["initial_critic_sha256"], "fresh independent critic")
        for name in ("actor", "critic"):
            optimizer = final[name + "_optimizer"]
            empty = deepcopy(optimizer); empty["state"] = {}
            require(nested_digest(empty) == fit["initial_" + name + "_optimizer_sha256"], "fresh optimizer identity")
            previous_hash = fit["initial_" + name + "_optimizer_sha256"]
            for record in fit["groups"]:
                require(record[name + "_optimizer_before_sha256"] == previous_hash, "optimizer hash continuity")
                previous_hash = record[name + "_optimizer_after_sha256"]
            require(previous_hash == nested_digest(optimizer), "final actual optimizer digest")
            require(len(optimizer["param_groups"]) == 1 and optimizer["param_groups"][0]["params"] == list(range(6))
                    and set(optimizer["state"]) == set(range(6)), "final optimizer parameter ownership")
            for index, tensor in enumerate(final[name + "_state"].values()):
                value = optimizer["state"][index]
                require(set(value) == {"step", "exp_avg", "exp_avg_sq"} and value["step"].shape == ()
                        and float(value["step"]) == len(worlds) // 2 * 4, "complete final Adam fields/steps")
                for moment in ("exp_avg", "exp_avg_sq"):
                    require(value[moment].shape == tensor.shape and value[moment].dtype == tensor.dtype
                            and torch.isfinite(value[moment]).all(), "finite matching Adam moment")
                require((value["exp_avg_sq"] >= 0).all(), "nonnegative Adam second moment")
        groups = []
        for group, record in enumerate(fit["groups"]):
            require(record["group"] == group and record["worlds"] == list(worlds[group * 2:group * 2 + 2]), "group worlds")
            actor.load_state_dict(states[group]["actor_state"], strict=True)
            critic.load_state_dict(states[group]["critic_state"], strict=True)
            raws = []
            for _ in range(2):
                row = batch["rows"][cursor]
                require(row["policy_sha256"] == states[group]["actor_sha256"], "pregroup actual policy binding")
                require(row["motion_root"] == protocol.training_motion_roots[block], "training private innovation root")
                raws.append(episode(row, actor, critic)); cursor += 1
            group_offset += 1
            groups.append(_group_read(record, raws, protocol.horizon, states[group], states[group + 1], group_offset))
            counts["saved_update_groups"] = counts.get("saved_update_groups", 0) + 1
            publish()
        for name in ("actor", "critic"):
            require(fit["final_" + name + "_sha256"] == final[name + "_sha256"], "endpoint digest")
            for key, value in movement(states[0][name + "_state"], final[name + "_state"]).items():
                equal(fit[name + "_movement"][key], value, "full-fit parameter movement")
        actor.load_state_dict(final["actor_state"], strict=True)
        endpoints[program] = actor
        report["fit_audits"][program] = dict(groups=groups, actor_movement=fit["actor_movement"],
                                            critic_movement=fit["critic_movement"], final_sha256=final["actor_sha256"])
    endpoints["INIT90"] = initial_actor
    for row in batch["rows"][cursor:]:
        actor = endpoints.get(row["program"])
        require(row["policy_sha256"] == (state_digest(actor.state_dict()) if actor is not None else None), "final policy binding")
        require(row["motion_root"] == (None if row["tape"] is None else protocol.evaluation_motion_roots[row["tape"]]), "final private root")
        episode(row, actor)
    expected = protocol.expected()
    for key, reference in (("saved_episodes", "complete_episodes"), ("saved_native_ticks", "native_steps"),
                           ("scalar_states", "reader_scalar_states"), ("observation_rows", "reader_local_rows"),
                           ("policy_requests", "motion_requests"), ("gate_requests", "gate_opportunities"),
                           ("critic_rows", "reader_critic_rows"), ("saved_update_groups", "group_states")):
        require(counts[key] == expected[reference], "complete reader exposure " + key)
    counts["scalar_power_links"] = counts["scalar_states"] * 270
    require(counts["scalar_power_links"] == expected["reader_scalar_power_links"], "scalar power work")
    require(report["policy_costs"] == batch["costs"]["all_policy"], "replayed policy work ledger")
    validate_counts(batch["actual"], batch["costs"], protocol)
    require(state_digest(parent.state_dict()) == batch["initial_parent_state"] == batch["final_parent_state"], "retained parent identity")
    require(nested_digest(gate) == batch["initial_gate_state"] == batch["final_gate_state"], "retained complete prior identity")
    result = comparisons(batch["rows"], protocol)
    require(result == batch["comparisons"], "all levels/contrasts/vectors/uncertainty")
    report["max_abs_errors"] = {key: max(item["max_abs_errors"][key] for item in audits) for key in audits[0]["max_abs_errors"]}
    report["episodes"], report["comparisons"] = audits, result
    return result


def read_result(out, repo, *, asset_paths=None):
    out, repo = Path(out).resolve(), Path(repo).resolve()
    if (out / "reading.json").exists():
        raise FileExistsError("reader output exists; preserve and reconcile before new reading")
    wall, cpu = time.perf_counter(), time.process_time()
    report = dict(status="INCOMPLETE", actual=dict(native_steps=0, optimizer_steps=0, refits=0), inflight={}, policy_costs={})
    def publish(full=False):
        report.update(reader_wall_seconds=time.perf_counter() - wall, reader_cpu_seconds=time.process_time() - cpu,
                      process_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        if full:
            write_json(out / "reading.json", report)
        write_json(out / "reading-progress.json", {key: report.get(key) for key in
                   ("status", "actual", "progress", "reader_wall_seconds", "reader_cpu_seconds")})
    try:
        batch = json.loads((out / "summary.json").read_text())
        require(batch["object"] == OBJECT and batch["state"] == "COMPLETE" and batch["scientific_execution"] is True
                and Protocol.from_dict(batch["protocol"]) == FROZEN, "fixed complete production result")
        report["worker_summary"] = artifact(out / "summary.json", out)
        require(source_identities(repo) == batch["sources"], "full source identity")
        if asset_paths is None:
            asset_paths = {name: value["path"] for name, value in batch["inputs"].items()}
        parent, gate, identities = load_assets(asset_paths)
        for name in identities:
            for key in ("bytes", "sha256", "canonical_path", "source_launch_sha"):
                require(identities[name][key] == batch["inputs"][name][key], "original consumed asset identity")
        log = checked_path(out, batch["episode_log"]["path"], batch["episode_log"])
        require([json.loads(line) for line in log.read_text().splitlines()] == batch["rows"], "complete append ledger")
        _read_all(batch, out, parent, gate, FROZEN, report, publish)
        report.update(status="VERIFIED", sources=batch["sources"], launch_sha=batch["launch_sha"],
                      timing_scope="Full scalar physics, policy/prior/CJ, pregroup critic/model and first-epoch algebra plus all ledger/state identities. "
                                   "No new native branch, later-epoch gradient/Adam replay or extra fit.")
    except BaseException:
        report.update(status="FAILED", failure=traceback.format_exc(), interrupted_call_work_may_be_unmeasured=True)
        if report["inflight"].get("policy_agents"):
            report["incurred_policy_costs"] = sum_counts((report["policy_costs"], sum_counts(report["inflight"]["policy_agents"])))
        raise
    finally:
        publish(full=True)
    return report


def publication(batch, reading, out):
    fields = ("J", "mean_served", "mean_sinr_quality", "service_p10", "min_served", "zero_service_steps",
              "longest_zero_service_streak", "mean_path_length_m", "active_transmitter_fraction", "mask_bit_switches",
              "off_fraction", "mean_motion_entropy", "mean_category_entropy", "eligible_mean_off_probability",
              "silent_travel_m", "first_J", "later_J", "cpu_seconds")
    compact = {kind: {key: {metric: item[metric] for metric in fields} for key, item in reading["comparisons"][kind].items()}
               for kind in ("levels", "contrasts")}
    paths = [path for path in Path(out).rglob("*") if path.is_file()]
    return dict(object=OBJECT, launch_sha=batch["launch_sha"], worker_state=batch["state"], reader_status=reading["status"],
                actual=batch["actual"], worker_costs=batch["costs"], reader_actual=reading["actual"],
                worker_wall_seconds=batch["worker_wall_seconds"], worker_cpu_seconds=batch["worker_cpu_seconds"],
                reader_wall_seconds=reading["reader_wall_seconds"], reader_cpu_seconds=reading["reader_cpu_seconds"],
                chain_wall_seconds=reading.get("chain_wall_seconds"), chain_cpu_seconds=reading.get("chain_cpu_seconds"),
                process_max_rss_kib=reading["process_max_rss_kib"], max_abs_errors=reading["max_abs_errors"],
                fits=[{key: fit[key] for key in ("program", "block", "status", "actor_movement", "critic_movement",
                                               "final_actor_sha256", "wall_seconds", "cpu_seconds")} for fit in batch["fits"]],
                **compact, adverses=reading["comparisons"]["adverses"], uncertainty=reading["comparisons"]["uncertainty"],
                summary=artifact(Path(out) / "summary.json", out), reading=artifact(Path(out) / "reading.json", out),
                canonical_output=str(Path(out).resolve()), storage_before_publication=dict(files=len(paths),
                    logical_bytes=sum(path.stat().st_size for path in paths), allocated_bytes=sum(path.stat().st_blocks * 512 for path in paths)),
                evidence_scope="Complete raw, all pregroup/final model states and actual final Adam state, full reader and original retained inputs "
                               "remain in their canonical durable locations; no later-epoch gradient/Adam replay is claimed.")
