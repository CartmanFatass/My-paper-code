"""One admitted fit followed by the exact complete L/O/P panel."""

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import faulthandler
import json
import multiprocessing
from pathlib import Path
import time
import traceback

from experiments.candidates.energy_relay_availability.runner import _cpu_seconds, _rss_kib, _sha256, _write_json, execute_bounded, orphan_raw_files
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from .constants import BATCH, DIRECTION, HORIZON, N_ACTIONS, N_ENVS, OPTIMIZER_STEPS, POLICY_SEED, TRAIN_SEEDS, plan
from .controllers import FEATURE_DIM
from .macro_env import NativeEpisode
from .policy import policy_statistics
from .readout import summarize
from .training import PPO_PARAMS, fingerprint, train


def choose_action(episode, model=None):
    if episode.arm == "P":
        return 0, None
    if episode.arm == "O":
        return episode.controller.ordinary_action(), None
    action, _ = model.predict(episode.features, deterministic=True)
    action = int(action)
    return action, policy_statistics(model, episode.features, action)


def worker(payload):
    job, out_string, checkpoint = payload
    out = Path(out_string)
    stem = job["job_key"].replace("/", "_")
    raw_path = out / "raw" / f"{stem}.npz"
    progress_path = out / "raw" / f"{stem}.progress.json"
    started, cpu_started = time.monotonic(), _cpu_seconds()
    episode = None
    try:
        if job not in plan():
            raise ValueError("undeclared evaluation world")
        import torch
        from stable_baselines3 import PPO
        torch.set_num_threads(1)
        faulthandler.enable()
        identity, model = {}, None
        if job["arm"] == "L":
            path = out / checkpoint["checkpoint"]
            if _sha256(path) != checkpoint["sha256"]:
                raise ValueError("checkpoint digest changed")
            model = PPO.load(path, device="cpu")
            identity = dict(checkpoint_sha256=checkpoint["sha256"], policy_fingerprint=fingerprint(model.policy))
            if identity["policy_fingerprint"] != checkpoint["fingerprint"]:
                raise ValueError("restored policy differs from the final asset")
        episode = NativeEpisode(job["seed"], job["arm"])
        while not episode.done:
            action, statistics = choose_action(episode, model)
            episode.macro_step(action, statistics)
            _write_json(progress_path, job | dict(steps=episode.t, status="running"))
        row = episode.row() | job | identity
        if model is not None and fingerprint(model.policy) != identity["policy_fingerprint"]:
            raise RuntimeError("evaluation changed the policy")
        row.update(episode.save(raw_path, complete=True))
        _write_json(progress_path, job | dict(steps=episode.t, status="completed"))
    except BaseException as error:
        row = job | dict(status="failed", error_type=type(error).__name__, error=str(error),
                         traceback=traceback.format_exc(), partial_observed_steps=episode.t if episode else 0)
        _write_json(progress_path, job | dict(steps=episode.t if episode else 0, status="failed"))
        if episode is not None and episode.t and not raw_path.exists():
            partial = raw_path.with_suffix(".partial.npz")
            row.update(episode.save(partial, complete=False))
    finally:
        if episode is not None:
            episode.close()
    for field in ("raw_path", "decisions_path"):
        if field in row:
            row[field] = str(Path(row[field]).relative_to(out))
    return row | dict(worker_wall_seconds=time.monotonic()-started,
                      worker_cpu_seconds=_cpu_seconds()-cpu_started, worker_peak_rss_kib=_rss_kib())


def run(out, launch_sha, workers=4):
    out = Path(out).resolve()
    if workers not in range(1, 5):
        raise ValueError("one to four single-thread evaluation workers required")
    if any((out / name).exists() for name in ("config.json", "training", "raw", "summary.json")):
        raise FileExistsError("scientific artifacts already exist")
    started, cpu_started = time.monotonic(), _cpu_seconds()
    jobs = plan()
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    _write_json(out / "config.json", dict(
        direction=DIRECTION, batch=BATCH, launch_sha=launch_sha, fits=1, policy_seed=POLICY_SEED,
        training_seeds=TRAIN_SEEDS, jobs=jobs, horizon=HORIZON, macro_steps=30,
        max_native_transitions=336000, ppo=PPO_PARAMS, feature_dim=FEATURE_DIM, actions=N_ACTIONS,
        train_envs=N_ENVS, evaluation_workers=workers, numeric_threads=1, optimizer_steps=OPTIMIZER_STEPS,
        network=dict(pi=[128,128], vf=[128,128], activation="tanh"),
        shield=asdict(PRODUCTION_PARAMS),
        finite_horizon="native H3000 terminated; no continuation bootstrap",
        checkpoint="final only; initialization retained but not a scored arm",
        evaluation_mode="gate>=0 service, else eligible member argmax then duration argmax; lower-index ties",
        information="central current users/BS at P10 clock; legal energy/stations each step; same actor and critic history",
        action_law="service sigmoid(g); dispatch sigmoid(-g) times masked member softmax times duration softmax",
        duration_meaning="elapsed since first geometric arrival, including waiting and later outside capture",
        ordinary="D urgency, competitor D+tau_in, occupancy and finite restoration bounds; see committed NOTES",
    ))
    rows, submitted, pool_errors = [], [], []
    _write_json(out / "perworld.json", rows)
    _write_json(out / "summary.json", summarize(rows, jobs))
    fit = train(out)
    runner_error = None
    if fit["status"] == "complete":
        checkpoint = fit["endpoint"] | dict(fingerprint=fit["endpoint_fingerprint"])
        expected_keys = [job["job_key"] for job in jobs]
        def on_result(row):
            rows.append(row)
            rows.sort(key=lambda item: expected_keys.index(item["job_key"]))
            _write_json(out / "perworld.json", rows)
            _write_json(out / "summary.json", summarize(rows, jobs))
        try:
            with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as executor:
                _, pool_errors = execute_bounded(executor, jobs, workers,
                    lambda job: (job, str(out), checkpoint), on_result, submitted, worker_fn=worker)
        except BaseException as error:
            runner_error = dict(error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
    summary = summarize(rows, jobs)
    orphans = orphan_raw_files(out, rows)
    if fit["status"] != "complete" or runner_error or pool_errors or orphans:
        summary.update(status="incomplete", contrasts={})
    progress = [json.loads(path.read_text()) for path in sorted((out / "raw").glob("*.progress.json"))]
    completed = {row["job_key"]: row["actual_length"] for row in rows if row["status"] == "completed"}
    lower_bound = sum(completed.values()) + sum(row["steps"] for row in progress if row["job_key"] not in completed)
    summary.update(launch_sha=launch_sha, fits_started=fit["fits_started"], training_status=fit["status"],
        optimizer_steps=fit.get("optimizer_steps"), submitted_jobs=submitted,
        unstarted_jobs=[job["job_key"] for job in jobs if job["job_key"] not in submitted],
        training_native_step_lower_bound=fit["recorded_native_step_lower_bound"],
        evaluation_native_step_lower_bound=lower_bound,
        actual_native_steps=336000 if summary["status"] == "complete" else None,
        known_native_step_lower_bound=fit["recorded_native_step_lower_bound"]+lower_bound,
        runner_error=runner_error, pool_errors=pool_errors, orphan_raw=orphans,
        parent_wall_seconds=time.monotonic()-started, parent_cpu_seconds=_cpu_seconds()-cpu_started,
        parent_peak_rss_kib=_rss_kib(),
        evaluation_worker_cpu_seconds_sum=sum(row.get("worker_cpu_seconds", 0) for row in rows),
        evaluation_worker_wall_seconds_sum=sum(row.get("worker_wall_seconds", 0) for row in rows))
    _write_json(out / "summary.json", summary)
    paths = [out/name for name in ("config.json", "training.json", "perworld.json", "summary.json", "initial.zip", "endpoint.zip")]
    paths += list((out/"raw").glob("*")) + list((out/"training").glob("*"))
    artifacts = {str(path.relative_to(out)): dict(sha256=_sha256(path), bytes=path.stat().st_size)
                 for path in sorted(paths) if path.is_file()}
    _write_json(out/"manifest.json", dict(launch_sha=launch_sha, artifacts=artifacts,
                                         storage_bytes=sum(row["bytes"] for row in artifacts.values())))
    return summary
