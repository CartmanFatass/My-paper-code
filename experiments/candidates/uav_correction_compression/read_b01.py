#!/usr/bin/env python3
"""Read every B01 trajectory and the fixed asset-retention rule; no policy/host calls."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import resource
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from experiments.candidates.uav_message_content.read_b06 import read_trace

MASTERS = (19701, 19702, 19703)
ARMS = tuple(a for m in MASTERS for a in (f"D{m}", f"C{m}")) + ("B40",)
METRICS = (
    "J_net", "J_physical", "served_users_per_tick", "Q", "worst_tick_service",
    "zero_service_steps", "longest_zero_service", "motion_path_m_per_uav",
    "boundary_fraction", "height_floor_fraction", "height_ceiling_fraction", "mean_height_m",
)
HIGHER = {"J_net", "J_physical", "served_users_per_tick", "Q", "worst_tick_service"}
LOWER = {"zero_service_steps", "longest_zero_service"}
T95_TWO = 2.0395134463964077
T95_ONE = 1.695518782545865


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def interval(values):
    values = list(map(float, values))
    assert len(values) == 32 and all(math.isfinite(v) for v in values)
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    se = sd / math.sqrt(32)
    return dict(mean=mean, sample_sd=sd, standard_error=se, df=31, paired_worlds=32,
                descriptive_t95=[mean - T95_TWO * se, mean + T95_TWO * se],
                one_sided_95_lower=mean - T95_ONE * se)


def contrast(first, second, metric):
    values = [a[metric] - b[metric] for a, b in zip(first, second)]
    result = interval(values)
    adverse = ([i for i, d in enumerate(values) if d < 0] if metric in HIGHER else
               [i for i, d in enumerate(values) if d > 0] if metric in LOWER else None)
    result.update(per_world=values, positive=sum(v > 0 for v in values),
                  zero=sum(v == 0 for v in values), negative=sum(v < 0 for v in values),
                  minimum=dict(world=int(np.argmin(values)), value=min(values)),
                  maximum=dict(world=int(np.argmax(values)), value=max(values)),
                  adverse_worlds=adverse,
                  preference="higher" if metric in HIGHER else "lower" if metric in LOWER else "descriptive")
    return result


def retention(contrasts):
    j = contrasts["J_net"]["one_sided_95_lower"]
    service = contrasts["served_users_per_tick"]["one_sided_95_lower"]
    return dict(J_net_lower=j, service_lower=service, J_net_boundary=-.001,
                service_boundary=-.10, J_pass=j > -.001, service_pass=service > -.10,
                mean_retention_pass=j > -.001 and service > -.10,
                scope="fixed D asset versus its old-panel mean, not equivalence, tails or training population")


def compare_panels(panels, left, right):
    return {metric: contrast(panels[left], panels[right], metric) for metric in METRICS}


def timing_contrast(rows, left, right, phase, clock):
    a = [r["timing"][phase][clock] / 1e9 for r in rows[left]]
    b = [r["timing"][phase][clock] / 1e9 for r in rows[right]]
    result = interval([x - y for x, y in zip(a, b)])
    result.update(left_mean_seconds=statistics.mean(a), right_mean_seconds=statistics.mean(b),
                  ratio_of_means=statistics.mean(a) / statistics.mean(b),
                  per_world_seconds=[x - y for x, y in zip(a, b)])
    return result


def check_counts(counts, episodes=32, constructors=1):
    steps = episodes * 256
    required = dict(constructors=constructors, explicit_resets=episodes, train_episodes=0,
                    final_eval_episodes=episodes, train_team_steps=0, final_eval_team_steps=steps,
                    team_steps=steps, native_step_calls=steps, motion_samples=steps * 5,
                    broadcasts=steps, attempts=steps, fit_started=0, rollouts=0,
                    optimizer_steps=0, actor_optimizer_steps=0, critic_optimizer_steps=0,
                    replayed_actor_rows=0, evaluation_optimizer_steps=0, diagnostic_forward_calls=0,
                    behavior_actor_forward_calls=steps, behavior_actor_forward_rows=steps * 5,
                    behavior_critic_forward_calls=0, behavior_critic_forward_rows=0,
                    ppo_actor_forward_calls=0, ppo_actor_forward_rows=0,
                    ppo_critic_forward_calls=0, ppo_critic_forward_rows=0)
    assert all(counts.get(k) == v for k, v in required.items()), (counts, required)
    assert counts["delivered_packets"] + counts["censored_packets"] == steps


def checked_timing(row):
    timing = row["timing"]
    assert timing["actor_forward"]["calls"] == 256
    for phase in ("actor_forward", "episode_loop"):
        for clock in ("wall_ns", "process_cpu_ns"):
            assert isinstance(timing[phase][clock], int) and timing[phase][clock] > 0
    for clock in ("wall_ns", "process_cpu_ns"):
        assert timing["actor_forward"][clock] <= timing["episode_loop"][clock]


def read_run(root, *, inputs_path=None):
    root = Path(root).resolve()
    source_inputs = Path(inputs_path) if inputs_path is not None else Path(__file__).with_name("b01_inputs.json")
    inputs = load(source_inputs)
    summary = load(root / "summary.json")
    config = load(root / "config.json")
    manifest = load(root / "launch-manifest.json")
    exit_record = load(root / "process-exit.json")
    assert summary["object"] == "UAV-CORRECTION-COMPRESSION-B01"
    assert summary["status"] == "COMPLETE" and not summary["limits"]
    assert summary["launch_sha"] == manifest["sha"]
    assert summary["seed"] == 19801
    assert summary["inputs_sha256"] == digest(source_inputs)
    assert load(root / "inputs.json") == inputs
    assert config["inputs"] == inputs and config["inputs_sha256"] == digest(source_inputs)
    assert config["launch_sha"] == summary["launch_sha"] and config["seed"] == 19801
    assert config["horizon"] == 256 and config["final_eval"] == 32 and config["arms"] == list(ARMS)
    assert config["fits"] == config["optimizer_updates"] == 0
    assert config["device"] == "cpu" and config["dtype"] == "float32"
    assert config["torch_threads"] == config["torch_interop_threads"] == 1
    assert config["blas_threads"] == dict(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    assert {k: config[k] for k in summary["configuration"]} == summary["configuration"]
    assert manifest["direction"] == "uav_correction_compression"
    assert manifest["lead"] == "Codex DM (native child)" and manifest["node"] == "wsl_4070"
    assert exit_record["status"] == "exited" and exit_record["exit_code"] == 0
    assert [c["arm"] for c in summary["cells"]] == list(ARMS)
    assert summary["arm_order"] == [dict(world=w, arms=list(ARMS[w % 7:] + ARMS[:w % 7])) for w in range(32)]
    check_counts(summary["actual"], 224, 7)
    assets = {a["master"]: a for a in inputs["assets"]}
    panels, rows, checks, zero_ticks, timings = {}, {}, {}, {}, {}
    totals = dict.fromkeys(summary["actual"], 0)
    for cell in summary["cells"]:
        arm = cell["arm"]
        assert cell["master"] == (19451 if arm == "B40" else int(arm[1:]))
        assert cell["directory"] == arm
        assert cell["status"] == "COMPLETE" and cell["launch_sha"] == summary["launch_sha"]
        assert cell["actor_trainable_parameters"] == 0 and cell["parameter_displacement"] == 0.
        assert cell["frozen_equal"] and cell["initial_tensor_sha256"] == cell["final_tensor_sha256"]
        check_counts(cell["counts"])
        for k, value in cell["counts"].items():
            totals[k] += value
        stream = root / arm / "episodes.jsonl"
        stream_rows = [json.loads(line) for line in stream.read_text().splitlines()]
        assert stream_rows == cell["rows"]
        assert digest(stream) == cell["episode_stream_sha256"]
        assert [r["episode"] for r in cell["rows"]] == list(range(32))
        panels[arm], checks[arm], zero_ticks[arm] = [], [], []
        rows[arm] = cell["rows"]
        for row, world in zip(cell["rows"], inputs["worlds"]):
            w = world["world"]
            assert (row["arm"], row["master"], row["phase"], row["world"], row["steps"]) == (
                arm, cell["master"], "final_eval", w, 256)
            assert (row["reset_seed"], row["channel_seed"], row["motion_seed"]) == (
                world["scene_seed"], world["channel_seed"], world["motion_seed"])
            assert row["raw"] == f"{arm}/raw/final_{w:02d}.npz"
            path = root / row["raw"]
            assert row["raw_bytes"] == path.stat().st_size
            check = read_trace(dict(row, raw=str(path)), "B40" if arm == "B40" else "D")
            checked_timing(row)
            with np.load(path, allow_pickle=False) as raw:
                assert raw["log_std"].tolist() == cell["log_std"]
                if arm.startswith("C"):
                    constant = np.asarray(assets[cell["master"]]["constant_float32"], dtype=np.float32)
                    assert cell["constant_float32"] == constant.tolist()
                    assert np.array_equal(raw["correction"], np.broadcast_to(constant, (256, 5, 3)))
                zero_ticks[arm].append(np.flatnonzero(raw["served_users"] == 0).tolist())
            assert math.isclose(row["charge_per_tick"], .001, rel_tol=0, abs_tol=1e-15)
            panel = dict(world=w, **check["levels"],
                         motion_path_m_per_uav=check["motion_path_m_per_uav"],
                         correction_mean=check["correction_mean"], correction_std=check["correction_std"],
                         correction_second_moment=check["correction_second_moment"],
                         charge_per_tick=row["charge_per_tick"])
            panels[arm].append(panel)
            checks[arm].append(dict(world=w, raw=row["raw"], sha256=digest(path), bytes=path.stat().st_size,
                                    scene=row["initial_scene_sha256"], channel=row["channel_sequence_sha256"],
                                    innovations=row["innovation_sha256"], action=row["action_sequence_sha256"],
                                    density_max_abs_error=check["density_max_abs_error"]))
        assert cell["raw_bytes"] == sum(c["bytes"] for c in checks[arm])
        stored_cell = load(root / arm / "summary.json")
        assert stored_cell == cell
        timings[arm] = {phase: {clock: dict(
            total_seconds=sum(r["timing"][phase][clock] for r in rows[arm]) / 1e9,
            mean_episode_seconds=statistics.mean(r["timing"][phase][clock] for r in rows[arm]) / 1e9,
            mean_team_tick_seconds=statistics.mean(r["timing"][phase][clock] for r in rows[arm]) / (1e9 * 256),
            per_world_seconds=[r["timing"][phase][clock] / 1e9 for r in rows[arm]])
            for clock in ("wall_ns", "process_cpu_ns")} for phase in ("actor_forward", "episode_loop")}
    assert totals == summary["actual"]
    for w in range(32):
        for key in ("initial_scene_sha256", "channel_sequence_sha256", "innovation_sha256",
                    "motion_rng_start_sha256", "motion_rng_end_sha256"):
            assert len({rows[arm][w][key] for arm in ARMS}) == 1, (key, w)
    effects, decisions, tail_changes, speed = {}, {}, {}, {}
    for m in MASTERS:
        d, c = f"D{m}", f"C{m}"
        for left, right in ((c, d), (c, "B40"), (d, "B40")):
            label = f"{left}-{right}"
            effects[label] = compare_panels(panels, left, right)
            tail_changes[label] = dict(
                new_zero_service_worlds=[w for w in range(32) if zero_ticks[left][w] and not zero_ticks[right][w]],
                removed_zero_service_worlds=[w for w in range(32) if not zero_ticks[left][w] and zero_ticks[right][w]],
                worse_min_service_worlds=[w for w in range(32) if panels[left][w]["worst_tick_service"] < panels[right][w]["worst_tick_service"]])
        decisions[str(m)] = retention(effects[f"{c}-{d}"])
        decisions[str(m)]["constant_B40_joint_mean_positive"] = all(
            effects[f"{c}-B40"][k]["mean"] > 0 for k in ("J_net", "served_users_per_tick"))
        speed[str(m)] = {phase: {clock: timing_contrast(rows, c, d, phase, clock)
                                for clock in ("wall_ns", "process_cpu_ns")}
                         for phase in ("actor_forward", "episode_loop")}
    averaged = {}
    for comparison in ("C-D", "C-B40", "D-B40"):
        left_kind, right_kind = comparison.split("-")
        averaged[comparison] = {}
        for metric in METRICS:
            world_differences = [statistics.mean(
                panels[f"{left_kind}{m}"][w][metric] -
                panels["B40" if right_kind == "B40" else f"{right_kind}{m}"][w][metric]
                for m in MASTERS) for w in range(32)]
            averaged[comparison][metric] = dict(interval(world_differences), per_world=world_differences)
    return dict(
        object="UAV-CORRECTION-COMPRESSION-B01-READING", status="COMPLETE", all_checks_passed=True,
        launch_sha=summary["launch_sha"], inputs_sha256=digest(source_inputs),
        summary_sha256=digest(root / "summary.json"), config_sha256=digest(root / "config.json"),
        manifest_sha256=digest(root / "launch-manifest.json"), exit_sha256=digest(root / "process-exit.json"),
        reader_sha256=digest(__file__), inherited_reader_sha256={name: digest(ROOT / name) for name in (
            "experiments/candidates/uav_message_content/read_b06.py",
            "experiments/candidates/uav_message_content/read_b05.py",
            "experiments/candidates/uav_message_content/read_b04.py")},
        actual=summary["actual"], trajectories_read=224, native_steps_added_by_reader=0,
        optimizer_calls_added_by_reader=0, model_or_policy_calls_added=0,
        resources=summary["resources"], worker_resources=summary.get("worker_resources"),
        configuration=summary["configuration"], checkpoint_bindings=summary["checkpoint_bindings"],
        recorded_batch_timing=summary["timing"], recorded_timing_scope=summary["timing_scope"],
        recorded_cell_json_output={c["arm"]: c["timing"]["json_output"] for c in summary["cells"]},
        levels={a: {m: statistics.mean(p[m] for p in panels[a]) for m in METRICS} for a in ARMS},
        per_world=panels, raw_checks=checks, contrasts=effects, mean_retention=decisions,
        all_three_mean_retention_pass=all(v["mean_retention_pass"] for v in decisions.values()),
        fixed_three_asset_average=averaged, zero_service_ticks=zero_ticks, tail_changes=tail_changes,
        timings=timings, constant_minus_D_timing=speed,
        limitations=["Exploratory fixed assets conditional on one selected parent and all inherited training/calibration.",
                     "32 shared tuples, not 96 independent worlds or new independent training instances.",
                     "Mean-retention is not equivalence, all-world dominance or tail safety.",
                     "One motion realization per scene/channel tuple; no within-scene stochastic risk estimate.",
                     "This old-visitation mean is not an optimized or universally best constant.",
                     "Actual host/thread/instrumentation timing; no physical energy or network-cost claim."])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    args = parser.parse_args(argv)
    start, usage = time.perf_counter(), resource.getrusage(resource.RUSAGE_SELF)
    result = read_run(args.run)
    end = resource.getrusage(resource.RUSAGE_SELF)
    result["reader_resources"] = dict(wall_seconds=time.perf_counter() - start,
        process_user_seconds=end.ru_utime - usage.ru_utime,
        process_system_seconds=end.ru_stime - usage.ru_stime,
        process_cpu_seconds=end.ru_utime + end.ru_stime - usage.ru_utime - usage.ru_stime,
        lifetime_peak_rss_kib_linux=end.ru_maxrss, scope="pure reader after imports, no native or policy calls")
    target = args.run / "reading.json"
    assert not target.exists(), "existing reading must not be silently overwritten"
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=result["status"], trajectories_read=result["trajectories_read"],
                         all_three_mean_retention_pass=result["all_three_mean_retention_pass"],
                         reader_resources=result["reader_resources"])))


if __name__ == "__main__":
    main()
