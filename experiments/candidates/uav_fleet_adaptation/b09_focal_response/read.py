"""One complete deterministic reading; no native step or optimizer replay."""
from copy import deepcopy
import json
from pathlib import Path
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import movement, state_digest
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.audit import equal, require
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.study import artifact, load_raw
from experiments.candidates.uav_local_history.b01.study import write_json
from .assets import checked_path, load_parents
from .audit import audit_episode
from .contract import ENDPOINTS, FROZEN, OBJECT, Protocol, source_identities
from .learning import fresh_critic
from .reading import comparisons
from .study import nested_digest, validate_counts


def _state(out, identity, *, ego, group, launch_sha):
    saved = torch.load(checked_path(out, identity["path"], identity), map_location="cpu", weights_only=True)
    require(saved["ego"] == ego and saved["block"] == int(ego[1]) and saved["launch_sha"] == launch_sha,
            "saved state identity")
    if group is not None:
        require(saved["group"] == group, "precollection group identity")
    for name, shapes in (("head", {"W": (27, 259), "b": (27,)}),
                          ("critic", {key: value.shape for key, value in fresh_critic(1).state_dict().items()})):
        state = saved[name + "_state"]
        require(set(state) == set(shapes), "complete " + name + " parameters")
        for key, shape in shapes.items():
            require(state[key].shape == shape and state[key].dtype == torch.float32 and torch.isfinite(state[key]).all(),
                    "finite FP32 saved parameters")
        require(state_digest(state) == saved[name + "_sha256"], "saved parameter digest")
    if ego.startswith("F"):
        require(torch.count_nonzero(saved["head_state"]["W"][:, 243:]).item() == 0, "F unused history weights remain zero")
    return saved


def _summary(value):
    return dict(min=float(value.min()), max=float(value.max()), mean=float(value.mean()),
                std=float(value.std(unbiased=False)), dtype=str(value.dtype))


def _group_read(record, raws, horizon, previous_state, next_state, expected_offset):
    require(record["status"] == "COMPLETE" and len(record["epochs"]) == 4, "complete four-epoch update ledger")
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
    # The actual precollection policy forwards were already checked. Rebuild
    # torch's nominal update density from those verified collected logits.
    z = torch.from_numpy(np.stack([raw["logits"][:, 0] for raw in raws])).double()
    w = torch.exp(z - torch.max(z, dim=-1, keepdim=True).values)
    probability = w / torch.sum(w, dim=-1, keepdim=True)
    old = torch.from_numpy(np.stack([raw["probabilities"][:, 0] for raw in raws]))
    actions = torch.from_numpy(np.stack([raw["action_index"][:, 0] for raw in raws]))
    chosen = probability.gather(-1, actions[..., None]).squeeze(-1)
    old_chosen = old.gather(-1, actions[..., None]).squeeze(-1)
    logp = torch.from_numpy(np.stack([raw["logp"][:, 0] for raw in raws]))
    identity = dict(logits_exact=True, rows=chosen.numel(), max_probability_abs=float((probability - old).abs().max()),
                    max_chosen_logp_abs=float((chosen.log() - logp).abs().max()),
                    max_ratio_from_one=float((chosen / old_chosen - 1.).abs().max()))
    for key, value in identity.items():
        equal(record["initial_identity"][key], value, "initial update density " + key, tolerance=1e-15 if type(value) is float else None)
    first_ratio = chosen / old_chosen
    first_loss = -torch.minimum(first_ratio * advantage, first_ratio.clamp(.8, 1.2) * advantage).mean()
    equal(record["epochs"][0]["head_loss"], float(first_loss), "first ego-only PPO loss", tolerance=1e-14)
    # Deliberately no later head/critic forwards or gradient/Adam replay here.
    for epoch, value in enumerate(record["epochs"]):
        require(value["epoch"] == epoch and value["head_step_completed"] and value["critic_step_completed"], "ordered completed optimizer steps")
        for field in ("head_loss", "critic_loss", "head_grad_norm", "critic_grad_norm", "head_clipped_grad_norm", "critic_clipped_grad_norm",
                      "head_movement_l2", "critic_movement_l2", "ratio_min", "ratio_max", "ratio_mean", "clip_fraction", "old_logp_mean", "new_logp_mean"):
            require(np.isfinite(value[field]), "finite update ledger " + field)
        require(value["critic_loss"] >= 0 and 0 <= value["clip_fraction"] <= 1
                and value["ratio_min"] > 0 and value["ratio_min"] <= value["ratio_mean"] <= value["ratio_max"], "valid loss/ratio ledger")
        for name, size in (("head", 2), ("critic", 6)):
            equal(value[name + "_optimizer_step_values"], np.full(size, record["group"] * 4 + epoch + 1), "continuing Adam steps")
            require(0 <= value[name + "_clipped_grad_norm"] <= .500001, "separate clipped gradients")
    for name, size in (("head", 2), ("critic", 6)):
        equal(record[name + "_optimizer_step_values"], np.full(size, (record["group"] + 1) * 4), "terminal group Adam steps")
        require(record[name + "_before_sha256"] == previous_state[name + "_sha256"]
                and record[name + "_after_sha256"] == next_state[name + "_sha256"], "group parameter chain")
        delta = torch.cat([(next_state[name + "_state"][key] - previous_state[name + "_state"][key]).reshape(-1)
                           for key in previous_state[name + "_state"]])
        l2 = float(torch.linalg.vector_norm(delta))
        equal(record[name + "_movement_l2"], l2, "group parameter movement", tolerance=2e-7 * max(1., l2))
    group_rows = 2 * horizon // 4
    increments = dict(head_optimizer_steps=4, critic_optimizer_steps=4, head_replay_rows=4 * group_rows,
                      critic_replay_rows=4 * group_rows, density_identity_rows=group_rows)
    for key, increment in increments.items():
        equal(record["completed_counts"][key], expected_offset * increment, "cumulative update exposure " + key)
    return dict(target_summary=_summary(target), advantage_summary=_summary(advantage), initial_identity=identity,
                first_ego_loss=float(first_loss), no_optimizer_replay=True)


def _read_all(batch, out, actors, protocol, report, publish):
    out = Path(out)
    expected_order = []
    for block, kind in protocol.fit_order():
        for wi, world in enumerate(protocol.training_worlds[block]):
            expected_order.append(("training", kind + str(block), "T", world, 0, block, wi // 2))
    for wi, world in enumerate(protocol.worlds):
        for ego, panel, tape in protocol.episode_order(wi):
            expected_order.append(("evaluation", ego, panel, world, tape, None, None))
    keys = ("kind", "ego", "panel", "world", "tape", "block", "group")
    require([tuple(row[key] for key in keys) for row in batch["rows"]] == expected_order, "complete frozen execution order")
    require([(fit["block"], fit["kind"]) for fit in batch["fits"]] == list(protocol.fit_order()), "four fixed fit order")
    counts, inflight = report["actual"], report["inflight"]
    fit_by_ego = {fit["ego"]: fit for fit in batch["fits"]}
    all_audits, cursor, group_offset = [], 0, 0
    endpoints = {}
    initial_critics = {}
    assignment_addresses = set()
    initial_layouts = {}
    report["fit_audits"], report["history_sensitivity"] = {}, []

    def episode(row, head_state=None, critic=None):
        raw = load_raw(checked_path(out, row["raw"]["path"], row["raw"]))
        report["progress"] = dict(stage="episode", id=row["id"])
        audited, sensitivity = audit_episode(raw, row, protocol, actors, head_state=head_state, critic=critic,
                                             counts=counts, inflight=inflight)
        all_audits.append(audited)
        # Completed cost is retained before any pairing/group/aggregation failure.
        report["policy_costs"] = sum_counts(item["policy_counts"] for item in all_audits)
        if sensitivity is not None:
            path = out / "diagnostics" / (row["id"] + "_history_zero.npz")
            if path.exists():
                raise FileExistsError("history sensitivity artifact exists")
            np.savez_compressed(path, **sensitivity)
            value = dict(ego=row["ego"], panel=row["panel"], world=row["world"], tape=row["tape"],
                         **audited["history_sensitivity"], artifact=artifact(path, out))
            report["history_sensitivity"].append(value)
        address = (row["assignment_root"], row["world"], row["tape"], row["panel"])
        assignment_addresses.add(address)
        layout = raw["positions"][0].tobytes() + raw["initial_users"].tobytes()
        if row["world"] in initial_layouts:
            require(initial_layouts[row["world"]] == layout, "paired common layout")
        else:
            require(layout not in initial_layouts.values(), "distinct world layout")
            initial_layouts[row["world"]] = layout
        publish()
        return raw

    for block, kind in protocol.fit_order():
        ego = kind + str(block)
        fit = fit_by_ego[ego]
        worlds = protocol.training_worlds[block]
        require(fit["status"] == "COMPLETE" and len(fit["groups"]) == len(worlds) // 2, "complete training groups")
        states = [_state(out, item["precollection_state"], ego=ego, group=i, launch_sha=batch.get("launch_sha"))
                  for i, item in enumerate(fit["groups"])]
        final = _state(out, fit["endpoint"], ego=ego, group=None, launch_sha=batch.get("launch_sha"))
        states.append(final)
        require(all(torch.count_nonzero(value).item() == 0 for value in states[0]["head_state"].values()), "zero response initialization")
        critic = fresh_critic(protocol.critic_seeds[block]).eval().requires_grad_(False)
        require(state_digest(critic.state_dict()) == states[0]["critic_sha256"] == fit["initial_critic_sha256"], "declared fresh critic initialization")
        if block in initial_critics:
            require(initial_critics[block] == states[0]["critic_sha256"], "matched pair critic initialization")
        initial_critics[block] = states[0]["critic_sha256"]
        require(fit["initial_head_sha256"] == states[0]["head_sha256"], "initial head digest")
        for name in ("head", "critic"):
            optimizer = final[name + "_optimizer"]
            empty = deepcopy(optimizer)
            empty["state"] = {}
            require(nested_digest(empty) == fit["initial_" + name + "_optimizer_sha256"], "fresh optimizer identity")
            previous_hash = fit["initial_" + name + "_optimizer_sha256"]
            for record in fit["groups"]:
                require(record[name + "_optimizer_before_sha256"] == previous_hash, "optimizer ledger continuity")
                previous_hash = record[name + "_optimizer_after_sha256"]
            require(previous_hash == nested_digest(optimizer), "final actual optimizer identity")
            require(len(optimizer["state"]) == (2 if name == "head" else 6), "final optimizer parameter ownership")
            for value in optimizer["state"].values():
                require(float(value["step"]) == len(worlds) // 2 * 4
                        and all(torch.isfinite(tensor).all() for tensor in value.values()), "final finite Adam state and steps")
        audited_groups = []
        for group, record in enumerate(fit["groups"]):
            require(record["group"] == group and record["worlds"] == list(worlds[2 * group:2 * group + 2]), "group world binding")
            critic.load_state_dict(states[group]["critic_state"], strict=True)
            raws = []
            for _ in range(2):
                row = batch["rows"][cursor]
                require(row["policy_sha256"] == states[group]["head_sha256"], "actual precollection policy binding")
                raws.append(episode(row, states[group]["head_state"], critic))
                cursor += 1
            group_offset += 1
            audited_groups.append(_group_read(record, raws, protocol.horizon, states[group], states[group + 1], group_offset))
            counts["saved_update_groups"] = counts.get("saved_update_groups", 0) + 1
            publish()
        for name in ("head", "critic"):
            require(fit["final_" + name + "_sha256"] == final[name + "_sha256"], "final endpoint digest")
            recomputed = movement(states[0][name + "_state"], final[name + "_state"])
            for key, value in recomputed.items():
                equal(fit[name + "_movement"][key], value, "full fit movement " + name + " " + key)
        endpoints[ego] = final["head_state"]
        report["fit_audits"][ego] = dict(groups=audited_groups, head_movement=fit["head_movement"],
                                        critic_movement=fit["critic_movement"], final_sha256=final["head_sha256"])
    for row in batch["rows"][cursor:]:
        if row["ego"] in ENDPOINTS:
            require(row["policy_sha256"] == state_digest(endpoints[row["ego"]]), "final endpoint episode binding")
        else:
            require(row["policy_sha256"] is None, "fixed control binding comes from original assets/source")
        episode(row, endpoints.get(row["ego"]))
    expected = protocol.expected()
    require(len(assignment_addresses) == expected["roster_unique_addresses"], "paired assignment address count")
    for key, reference in (("saved_episodes", "complete_episodes"), ("saved_native_ticks", "native_steps"),
                           ("scalar_states", "reader_scalar_states"), ("observation_rows", "reader_local_rows"),
                           ("policy_requests", "motion_requests"), ("roster_draws", "roster_draws"),
                           ("critic_rows", "reader_critic_rows"), ("saved_update_groups", "group_states")):
        require(counts[key] == expected[reference], "complete reader exposure " + key)
    counts["scalar_power_links"] = counts["scalar_states"] * 270
    counts["head_rows"] = report["policy_costs"]["head_rows"] + counts.get("history_zero_head_rows", 0)
    require(counts["head_rows"] == expected["reader_head_rows"] and counts["scalar_power_links"] == expected["reader_scalar_links"], "full selected diagnostic/physics work")
    require(report["policy_costs"] == batch["costs"]["all_policy"], "complete replayed policy cost ledger")
    validate_counts(batch["actual"], batch["costs"], protocol)
    for name, actor in actors.items():
        require(state_digest(actor.state_dict()) == batch["initial_parent_states"][name] == batch["final_parent_states"][name], "retained original parent identity")
    result = comparisons(batch["rows"], protocol)
    require(result == batch["comparisons"], "full recorded levels/contrasts/vectors/uncertainty")
    report["max_abs_errors"] = {key: max(item["max_abs_errors"][key] for item in all_audits) for key in all_audits[0]["max_abs_errors"]}
    report["episodes"] = all_audits
    report["comparisons"] = result
    return result


def read_result(out, repo, *, parent_paths=None):
    out, repo = Path(out).resolve(), Path(repo).resolve()
    if (out / "reading.json").exists() or (out / "diagnostics").exists():
        raise FileExistsError("reader output exists; preserve/reconcile it before any new reading")
    wall, cpu = time.perf_counter(), time.process_time()
    report = dict(status="INCOMPLETE", actual=dict(native_steps=0, optimizer_steps=0, refits=0), inflight={}, policy_costs={})
    (out / "diagnostics").mkdir()
    def publish(full=False):
        report.update(reader_wall_seconds=time.perf_counter() - wall, reader_cpu_seconds=time.process_time() - cpu,
                      process_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        if full:
            write_json(out / "reading.json", report)
        write_json(out / "reading-progress.json", {key: report.get(key) for key in ("status", "actual", "progress", "reader_wall_seconds", "reader_cpu_seconds")})
    try:
        batch = json.loads((out / "summary.json").read_text())
        require(batch["object"] == OBJECT and batch["state"] == "COMPLETE" and batch["scientific_execution"] is True
                and Protocol.from_dict(batch["protocol"]) == FROZEN, "fixed complete production result")
        report["worker_summary"] = artifact(out / "summary.json", out)
        require(source_identities(repo) == batch["sources"], "full source identity")
        if parent_paths is None:
            parent_paths = {name: value["path"] for name, value in batch["parents"].items()}
        actors, identities = load_parents(parent_paths)
        for name in identities:
            for key in ("bytes", "sha256", "state_sha256", "canonical_path", "source_launch_sha"):
                require(identities[name][key] == batch["parents"][name][key], "original parent consumption identity")
        episode_log = checked_path(out, batch["episode_log"]["path"], batch["episode_log"])
        require([json.loads(line) for line in episode_log.read_text().splitlines()] == batch["rows"], "episode append ledger")
        _read_all(batch, out, actors, FROZEN, report, publish)
        report.update(status="VERIFIED", sources=batch["sources"], launch_sha=batch["launch_sha"],
                      timing_scope="One full scalar physical, policy, precollection critic/state and algebra/ledger replay, with "
                                   "conditional reductions and history-zero head calls; no native branch, optimizer replay or extra fit.")
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
              "longest_zero_service_streak", "mean_path_length_m", "uav0_travel_m", "ego_mean_entropy",
              "ego_mean_visible_peers", "tracked_nonzero_decisions", "tracked_moving_decisions")
    compact = {}
    for kind in ("levels", "contrasts"):
        compact[kind] = {key: {metric: {name: value for name, value in item[metric].items()
                                     if name != "world_values" or (kind == "contrasts" and key in reading["comparisons"]["primary"])}
                               for metric in fields} for key, item in reading["comparisons"][kind].items()}
    paths = [path for path in Path(out).rglob("*") if path.is_file()]
    return dict(object=OBJECT, launch_sha=batch["launch_sha"], worker_state=batch["state"], reader_status=reading["status"],
                actual=batch["actual"], worker_costs=batch["costs"], reader_actual=reading["actual"],
                worker_wall_seconds=batch["worker_wall_seconds"], worker_cpu_seconds=batch["worker_cpu_seconds"],
                reader_wall_seconds=reading["reader_wall_seconds"], reader_cpu_seconds=reading["reader_cpu_seconds"],
                process_max_rss_kib=reading["process_max_rss_kib"],
                fits=[{key: fit[key] for key in ("ego", "block", "status", "head_movement", "critic_movement", "final_head_sha256", "wall_seconds", "cpu_seconds")}
                      for fit in batch["fits"]],
                **compact, primary=reading["comparisons"]["primary"], uncertainty=reading["comparisons"]["uncertainty"],
                history_sensitivity=reading["history_sensitivity"],
                summary=artifact(Path(out) / "summary.json", out), reading=artifact(Path(out) / "reading.json", out),
                canonical_output=str(Path(out).resolve()), storage_before_publication=dict(files=len(paths),
                    logical_bytes=sum(path.stat().st_size for path in paths), allocated_bytes=sum(path.stat().st_blocks * 512 for path in paths)),
                evidence_scope="Full raw, all precollection states and finals, complete reader and both original retained assets "
                               "stay in their canonical durable locations; this file is a compact conditional result.")
