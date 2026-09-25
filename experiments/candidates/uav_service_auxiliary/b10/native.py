"""B10 fixed-policy O+F versus station-continuity C+F evaluator."""

from __future__ import annotations

import copy
import hashlib
import json
import resource
import time
from pathlib import Path

import numpy as np
import torch

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from hmasd.agent import HMASDAgent
from ..b01.native import active_config, initialization_fingerprint, optimizer_steps, preserved_rng, seed_everything, sha256_file, _sync_agent
from ..b04.evaluation import TRACE_FIELDS
from ..b07.native import evaluate_world, aggregate_worlds
from ..b08.metrics import recovery_opportunity_summary, aggregate_opportunity_summaries
from ..b08.native import ENDPOINT_FIELDS, initialization_identity
from ..b09.native import B09Spec, make_b09_config, fixed_config_record
from ..b09.persistence import append_progress, compact_opportunity, write_raw_json, write_summary
from .metrics import aggregate_station_summaries, station_intervals
from .station import ContinuityStationEnv

OBJECT_ID = "UAV-SERVICE-STATION-CONTINUITY-B10"
POLICY_SEED = 925031
WORLD_SEEDS = tuple(range(953001, 953033))
RULES = ("O", "C")
SOURCE_SHA = "e5e53534c2c0c4a059cfdfa5f3aff4cbc2166f46"
SOURCE_DIGESTS = {
    "config.json": "176fa470ae682a6218b4690de33f4727afe0ee7c4cf2f22508bd0f1ddfd96084",
    "summary.json": "a96db3a1e945af8099e54ad2a22173ff050df134bb95918818357f16502458cf",
    "N/endpoint/agent.pt": "2ba395b9f2761a9a761bd648d399b525c61b7babdb84edbe293319d269eeff5a",
}


def _json_active(config):
    return json.loads(json.dumps(active_config(config)), parse_constant=str)


def verify_source(root: Path):
    root = Path(root)
    for name, digest in SOURCE_DIGESTS.items():
        path = root / name
        if not path.is_file() or sha256_file(path) != digest:
            raise ValueError(f"B10 bound source digest mismatch: {name}")
    record = json.loads((root / "config.json").read_text())
    source_summary = json.loads((root / "summary.json").read_text())
    config = make_b09_config(B09Spec())
    # The source was created in a node snapshot. Preserve its recorded path
    # field while comparing every executable scalar against this implementation.
    config.scenario7_baseline_metrics_path = record["active"]["scenario7_baseline_metrics_path"]
    expected_record = json.loads(json.dumps(fixed_config_record(B09Spec(), config)))
    if record != expected_record:
        raise ValueError("B10 B09 source config identity mismatch")
    if (source_summary.get("launch_sha") != SOURCE_SHA
            or source_summary.get("status") != "COMPLETE"
            or source_summary.get("artifacts", {}).get("N/endpoint/agent.pt") != SOURCE_DIGESTS["N/endpoint/agent.pt"]
            or source_summary.get("artifacts", {}).get("config.json") != SOURCE_DIGESTS["config.json"]
            or source_summary.get("evaluations", {}).get("N_primary", {}).get("evaluation_mode") != "F"):
        raise ValueError("B10 source execution/arm identity mismatch")
    saved_config = torch.load(root / "N/endpoint/agent.pt", map_location="cpu", weights_only=False)["config"]
    if _json_active(saved_config) != record["active"]:
        raise ValueError("B10 checkpoint-saved config differs from bound source record")
    config = saved_config
    evaluation = copy.deepcopy(saved_config)
    evaluation.num_envs = 1
    evaluation.calculate_and_set_buffer_sizes()
    before = active_config(config)
    after = active_config(evaluation)
    if {key for key in before if before[key] != after[key]} != {"num_envs", "batch_size", "buffer_size", "high_level_buffer_size", "low_level_buffer_size"}:
        raise ValueError("B10 evaluation config changed more than one-lane storage")
    if (evaluation.episode_length != 3000 or evaluation.max_steps != 3000
            or evaluation.n_agents != 8 or evaluation.k != 10
            or evaluation.lambda_return != 2.0 or evaluation.use_obsnorm or evaluation.use_statenorm):
        raise ValueError("B10 fixed task identity mismatch")
    return config, evaluation, source_summary


def _full_state(agent):
    identity = initialization_identity(agent)["components"]
    identity = {key: value for key, value in identity.items() if key != "rng_state"}
    digest = hashlib.sha256()
    for name in ("coordinator_optimizer", "discoverer_actor_optimizer", "discoverer_critic_optimizer",
                 "team_discriminator_optimizer", "individual_discriminator_optimizer"):
        optimizer = getattr(agent, name, None)
        digest.update(name.encode())
        if optimizer is not None:
            state = optimizer.state_dict()
            def feed(value):
                if torch.is_tensor(value):
                    array = value.detach().cpu().contiguous().numpy()
                    digest.update(str(array.dtype).encode()); digest.update(str(array.shape).encode()); digest.update(array.tobytes())
                elif isinstance(value, dict):
                    for key in sorted(value, key=str):
                        digest.update(str(key).encode()); feed(value[key])
                elif isinstance(value, (list, tuple)):
                    for item in value: feed(item)
                else:
                    digest.update(repr(value).encode())
            feed(state)
    return {"learner_components": identity, "optimizer_sha256": digest.hexdigest(),
            "optimizer_steps": optimizer_steps(agent)}


def _station_arrays(snapshots):
    n = len(snapshots)
    if not n:
        raise ValueError("empty station selection trace")
    return {
        "station_prior_actual": np.asarray([row["prior_actual_station"] for row in snapshots], dtype=np.int16),
        "station_current_target": np.asarray([row["current_target_station"] for row in snapshots], dtype=np.int16),
        "station_battery_selection": np.asarray([row["battery_after_consumption"] for row in snapshots], dtype=np.float64),
        "station_wait_before": np.asarray([row["wait_age_before_selection"] for row in snapshots], dtype=np.int32),
    }


def verify_prefix(original_npz: Path, candidate_npz: Path, original_snapshots: list[dict], candidate_snapshots: list[dict]):
    def same_membership(a, b):
        return set(a) == set(b) and all(set(a[key]) == set(b[key]) for key in a)
    first = next((tick for tick, (a, b) in enumerate(zip(original_snapshots, candidate_snapshots))
                  if not same_membership(a["actual_selected"], b["actual_selected"])), None)
    if first is None and len(original_snapshots) != len(candidate_snapshots):
        raise RuntimeError("paired episodes have different lengths before any allocation difference")
    common = min(len(original_snapshots), len(candidate_snapshots)) if first is None else first
    for tick in range(common):
        a = dict(original_snapshots[tick]); b = dict(candidate_snapshots[tick])
        a.pop("actual_selected"); b.pop("actual_selected")
        if a != b or not same_membership(original_snapshots[tick]["actual_selected"],
                                         candidate_snapshots[tick]["actual_selected"]):
            raise RuntimeError(f"paired station prefix differs before allocation at tick {tick}")
    if first is not None:
        for key in ("prior_actual_station", "current_target_station", "battery_after_consumption",
                    "wait_age_before_selection", "eligible_by_station", "original_selected"):
            if original_snapshots[first][key] != candidate_snapshots[first][key]:
                raise RuntimeError(f"paired station inputs differ at first allocation tick {first}: {key}")
    with np.load(original_npz, allow_pickle=False) as old, np.load(candidate_npz, allow_pickle=False) as new:
        before_keys = ("native_reward", "metrics", "ends", "actions", "physical_post_battery",
                       "charger_input_wh", "mode", "entry", "exit", "pre_position_m", "post_position_m")
        for key in before_keys:
            if not np.array_equal(old[key][:common], new[key][:common], equal_nan=True):
                raise RuntimeError(f"paired physical/feedback prefix differs before allocation: {key}")
        if first is not None:
            for key in ("original_action", "submitted_action", "mode_before", "mode", "entry", "exit",
                        "pre_position_m", "pre_legal_battery", "agent_skills", "team_skills"):
                if not np.array_equal(old[key][first:first+1], new[key][first:first+1], equal_nan=True):
                    raise RuntimeError(f"paired decision prefix differs at first allocation: {key}")
    return {"first_differing_allocation_tick": first, "verified_complete_transition_prefix_steps": common,
            "earlier_common_F_overrides_allowed": True}


def evaluate_one(evaluator, config, seed: int, rule: str, *, out: Path, progress=None):
    env = ParallelToArrayAdapter(ContinuityStationEnv(config=config, seed=seed, station_rule=rule))
    raw = env.env
    partial = None
    def retain_partial(payload):
        nonlocal partial
        partial = payload
    try:
        result = evaluate_world(evaluator, env, config, seed, "F", progress=progress,
                                partial_sink=retain_partial)
        world, rewards, metrics, actions, ends, diagnostics = result
        snapshots = raw.selection_snapshots
        if len(snapshots) != len(rewards):
            raise RuntimeError("selection and native transition counts differ")
        raw_path = out / "raw" / f"{rule}_{seed}.npz"
        detail_path = out / "raw" / f"{rule}_{seed}.json.gz"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        # Preserve the completed physical trace even if later diagnostic
        # calculation or serialization fails.
        np.savez_compressed(raw_path, metric_fields=np.asarray(TRACE_FIELDS), native_reward=rewards,
                            metrics=metrics, actions=actions, ends=ends,
                            **diagnostics, **_station_arrays(snapshots))
        station = station_intervals(snapshots, diagnostics, terminal_type=world["terminal_type"])
        opportunity = recovery_opportunity_summary(diagnostics, metrics, time_step_seconds=float(config.time_step))
        anchor = opportunity["first_qualifying_exit_anchor"]
        if anchor is not None:
            member, start = int(anchor["member"]), int(anchor["anchor_step"])
            stop = int(anchor["window_stop_exclusive"])
            pre_exit_service = diagnostics["joint_team_qos"][int(anchor["start_step"]):start]
            anchor["pre_exit_joint_qos_sum"] = float(pre_exit_service.sum())
            anchor["any_pre_exit_joint_service"] = bool(np.any(pre_exit_service > 0.0))
            input_steps = np.flatnonzero(diagnostics["charger_input_wh"][int(anchor["start_step"]):start + 1, member] > 0.0)
            target_station = int(snapshots[int(anchor["start_step"]) + int(input_steps[-1])]["current_target_station"][member])
            positions = diagnostics["post_position_m"][start:stop, member]
            if 0 <= target_station < raw.n_charging_stations:
                distances = np.linalg.norm(positions - raw.charging_station_positions[target_station], axis=1)
                anchor["actual_station_departure_in_window"] = bool(np.any(distances > raw.charging_capture_radius_m))
                anchor["still_within_capture_at_window_end"] = bool(distances[-1] <= raw.charging_capture_radius_m)
                anchor["anchor_station"] = target_station
                anchor["post_exit_signed_stored_wh"] = float(diagnostics["signed_stored_energy_delta_wh"][start:stop, member].sum())
            else:
                anchor["actual_station_departure_in_window"] = None
                anchor["still_within_capture_at_window_end"] = None
                anchor["anchor_station"] = None
                anchor["post_exit_signed_stored_wh"] = float(diagnostics["signed_stored_energy_delta_wh"][start:stop, member].sum())
        world["actual_delivered_megabits"] = float(world["cumulative_throughput_mbps"] * config.time_step)
        world["actual_delivered_megabytes"] = world["actual_delivered_megabits"] / 8.0
        world["recovery_opportunity"] = compact_opportunity(opportunity)
        world["station"] = {key: value for key, value in station.items() if key not in {"waiting_intervals", "charging_spells"}}
        write_raw_json(detail_path, {"seed": seed, "rule": rule, "station_selection_snapshots": snapshots,
                                     "station": station, "recovery_opportunity": opportunity,
                                     "service_free_intervals": world["service_free_intervals"]})
        world["raw_npz"] = str(raw_path.relative_to(out))
        world["raw_detail"] = str(detail_path.relative_to(out))
        world["raw_sha256"] = {world["raw_npz"]: sha256_file(raw_path),
                                world["raw_detail"]: sha256_file(detail_path)}
        world.pop("service_free_intervals", None)
        world.pop("mode_durations_by_uav", None)
        world.pop("descriptive_250_step_bins", None)
        return world, snapshots, raw_path
    except Exception as exc:
        if partial is not None:
            partial_path = out / "raw" / f"{rule}_{seed}_partial.npz"
            partial_path.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(partial_path, **partial)
        if raw.selection_snapshots:
            write_raw_json(out / "raw" / f"{rule}_{seed}_partial_station.json.gz",
                           {"selection_snapshots": raw.selection_snapshots,
                            "failure": {"type": type(exc).__name__, "message": str(exc)}})
        raise
    finally:
        env.close()


def paired_summary(old: list[dict], new: list[dict]):
    if [row["seed"] for row in old] != [row["seed"] for row in new]:
        raise RuntimeError("paired world order mismatch")
    fields = ENDPOINT_FIELDS + ("maximum_service_free_interval_steps",)
    rows = []
    for o, c in zip(old, new, strict=True):
        effects = {field: float(c[field] - o[field]) for field in fields}
        rows.append({"seed": o["seed"], "effects_C_minus_O": effects,
                     "new_zero_service_world": bool(c["zero_service_episode"] and not o["zero_service_episode"]),
                     "removed_zero_service_world": bool(o["zero_service_episode"] and not c["zero_service_episode"])})
    aggregate = {}
    for field in fields:
        values = np.asarray([row["effects_C_minus_O"][field] for row in rows])
        aggregate[field] = {"mean": float(values.mean()), "median": float(np.median(values)),
                            "wins": int((values > 0).sum()), "losses": int((values < 0).sum()),
                            "ties": int((values == 0).sum()), "min": float(values.min()), "max": float(values.max())}
    return {"worlds": rows, "aggregate": aggregate}


def run_native(*, source_root: Path, out: Path, launch_sha: str,
               device_name: str = "cuda", threads: int = 4,
               _fixture_seeds=None, _fixture_config=None):
    fixture = _fixture_seeds is not None
    if not fixture and (device_name != "cuda" or threads != 4):
        raise ValueError("B10 production requires CUDA FP32 and four torch threads")
    seeds = tuple(_fixture_seeds) if fixture else WORLD_SEEDS
    if not fixture and seeds != WORLD_SEEDS:
        raise ValueError("B10 fixed world panel changed")
    if not seeds:
        raise ValueError("empty B10 world panel")
    out = Path(out)
    admission_files = {"launch-manifest.json", "launch-status.json", "admission-preflight.json",
                       "stdout.log", "stderr.log", "process-exit.json"}
    if out.exists() and any(path.name not in admission_files for path in out.iterdir()):
        raise FileExistsError(f"B10 scientific output already exists: {out}")
    config, evaluation, source_summary = verify_source(source_root)
    if _fixture_config is not None:
        if not fixture:
            raise ValueError("fixture config requires internal fixture seeds")
        evaluation = _fixture_config
    if torch.get_default_dtype() != torch.float32:
        raise RuntimeError("B10 requires Torch FP32 default dtype")
    device = torch.device(device_name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("B10 CUDA unavailable")
    torch.set_num_threads(threads)
    if torch.get_num_threads() != threads:
        raise RuntimeError("B10 torch threads differ")
    if device.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        if torch.backends.cuda.matmul.allow_tf32 or torch.backends.cudnn.allow_tf32:
            raise RuntimeError("B10 TF32 must be disabled")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    usage_start = resource.getrusage(resource.RUSAGE_SELF)
    summary = {"object_id": OBJECT_ID, "status": "INCOMPLETE", "failure": None,
               "launch_sha": launch_sha, "source_execution_sha": SOURCE_SHA,
               "source_root": str(source_root), "source_digest": SOURCE_DIGESTS,
               "source_original_node_root": "/home/wu/hmasd-worktrees/usa-b09-48388289d/runs/uav_service_auxiliary/b09_an_925031_a01",
               "policy_seed": POLICY_SEED, "world_seeds": list(seeds), "rule_order": list(RULES),
               "device": str(device), "torch_threads": threads, "tf32_disabled": True,
               "counts": {"fits": 0, "training_transitions": 0, "optimizer_updates": 0,
                          "episode_attempts": 0, "completed_episodes": 0, "evaluation_transitions": 0,
                          "uav_action_rows": 0},
               "panels": {rule: {"worlds": []} for rule in RULES}, "prefixes": [], "artifacts": {}}
    write_summary(out / "config.json", {"object_id": OBJECT_ID, "launch_sha": launch_sha,
        "source_sha": SOURCE_SHA, "source_digests": SOURCE_DIGESTS,
        "saved_training_active": _json_active(config), "evaluation_active": _json_active(evaluation),
        "policy_seed": POLICY_SEED, "world_seeds": list(seeds), "rules": list(RULES),
        "device": str(device), "threads": threads, "F": "unchanged B06 feedback in both arms"})
    summary["artifacts"]["config.json"] = sha256_file(out / "config.json")
    write_summary(out / "summary.json", summary)
    def progress(event):
        append_progress(out, event, dict(summary["counts"]))
        if event["event"] != "transition":
            write_summary(out / "summary.json", summary)
    try:
        with preserved_rng():
            seed_everything(POLICY_SEED, device)
            agent = HMASDAgent(config, log_dir=str(out / "loader"), device=device)
            agent.load_model(Path(source_root) / "N/endpoint/agent.pt")
            agent.train(False)
            saved_policy = source_summary["evaluations"]["N_primary"]["policy_sha256_before_after"]
            if initialization_fingerprint(agent) != saved_policy:
                raise RuntimeError("restored B09 N policy fingerprint mismatch")
            source_state = _full_state(agent)
            summary["source_learner_state"] = source_state
            for rule in RULES:
                panel_start = time.perf_counter()
                panel_state = _full_state(agent)
                seed_everything(POLICY_SEED, device)
                evaluator = HMASDAgent(copy.deepcopy(evaluation), log_dir=str(out / "evaluator" / rule), device=device)
                _sync_agent(agent, evaluator)
                evaluator.train(False)
                evaluator_state = _full_state(evaluator)
                for seed in seeds:
                    summary["counts"]["episode_attempts"] += 1
                    progress({"event": "episode_attempt", "rule": rule, "seed": seed})
                    def advance(kind, count):
                        if kind == "transition":
                            summary["counts"]["evaluation_transitions"] += count
                            summary["counts"]["uav_action_rows"] += count * 8
                            if summary["counts"]["evaluation_transitions"] % 100 == 0:
                                progress({"event": "transition", "rule": rule, "seed": seed})
                    world, snapshots, trace = evaluate_one(evaluator, evaluation, seed, rule, out=out, progress=advance)
                    if rule == "C":
                        old_trace = out / "raw" / f"O_{seed}.npz"
                        old_detail = out / "raw" / f"O_{seed}.json.gz"
                        import gzip
                        with gzip.open(old_detail, "rt", encoding="utf-8") as handle:
                            old_snapshots = json.load(handle)["station_selection_snapshots"]
                        summary["prefixes"].append({"seed": seed, **verify_prefix(old_trace, trace, old_snapshots, snapshots)})
                    summary["panels"][rule]["worlds"].append(world)
                    summary["artifacts"].update(world["raw_sha256"])
                    summary["counts"]["completed_episodes"] += 1
                    progress({"event": "episode_complete", "rule": rule, "seed": seed})
                if _full_state(evaluator) != evaluator_state or _full_state(agent) != panel_state:
                    raise RuntimeError(f"B10 {rule} mutated learner/optimizer/normalizer state")
                worlds = summary["panels"][rule]["worlds"]
                summary["panels"][rule]["aggregate"] = aggregate_worlds(worlds)
                summary["panels"][rule]["station_aggregate"] = aggregate_station_summaries(worlds)
                summary["panels"][rule]["recovery_opportunity_aggregate"] = aggregate_opportunity_summaries(
                    [row["recovery_opportunity"] for row in worlds])
                summary["panels"][rule]["wall_seconds"] = time.perf_counter() - panel_start
                summary["panels"][rule]["learner_state_immutable"] = True
                progress({"event": "panel_complete", "rule": rule})
            if _full_state(agent) != source_state:
                raise RuntimeError("B10 source policy mutated")
        summary["paired"] = paired_summary(summary["panels"]["O"]["worlds"], summary["panels"]["C"]["worlds"])
        if (summary["counts"]["completed_episodes"] != 2 * len(seeds)
                or summary["counts"]["episode_attempts"] != 2 * len(seeds)
                or summary["counts"]["evaluation_transitions"] > 2 * len(seeds) * evaluation.episode_length):
            raise RuntimeError("B10 exposure count mismatch")
        summary["status"] = "COMPLETE"
        return summary
    except Exception as exc:
        for path in sorted((out / "raw").glob("*")) if (out / "raw").exists() else ():
            if path.is_file():
                summary["artifacts"][str(path.relative_to(out))] = sha256_file(path)
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary.update(wall_seconds=time.perf_counter() - started,
                       cpu_user_seconds=usage.ru_utime - usage_start.ru_utime,
                       cpu_system_seconds=usage.ru_stime - usage_start.ru_stime,
                       peak_rss_kib=int(usage.ru_maxrss), rss_scope="B10 runner process high-water mark")
        summary["raw_artifact_bytes"] = sum(
            path.stat().st_size for path in (out / "raw").rglob("*") if path.is_file()
        ) if (out / "raw").exists() else 0
        progress({"event": "batch_exit", "status": summary["status"]})
