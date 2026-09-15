"""One original arm, complete final panel, and the card's pair publication."""
from contextlib import contextmanager
import json
import time
import traceback
from pathlib import Path

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import exposure, snapshot
from .learner import (ARMS, BATCH, CHUNK, EPOCHS, EVAL_EPISODES, HORIZON,
                      TRAIN_EPISODES, action_generator, collect_episode, contrast,
                      endpoint, frozen_batch, models, optimizer_for, update)

COST_LAW = ("non-reset initialization + 769 resets + 512*256 training ticks + "
            "32 frozen-baseline batches + 128 updates(16,256,5,32,K) + "
            "256*256 final-evaluation ticks + publication and exit")


def new_counts():
    return dict.fromkeys(("constructor_calls", "constructor_resets", "reset_calls",
                          "explicit_resets", "step_calls", "team_steps", "train_team_steps",
                          "eval_team_steps", "train_episodes", "eval_episodes",
                          "completed_episode_steps", "velocity_decisions",
                          "recurrent_observations", "optimizer_attempts", "optimizer_steps"), 0)


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")


@contextmanager
def phase_time(timings, name):
    started = time.monotonic()
    try:
        yield
    finally:
        timings[name] += time.monotonic() - started


def peak_rss_bytes():
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except ImportError:
        try:
            import psutil
            return getattr(psutil.Process().memory_info(), "peak_wset", None)
        except ImportError:
            return None


def run_arm(arm, master, out, launch_sha, max_seconds, process_start):
    """Fixed scientific endpoint; no retry/resume/checkpoint-selection path."""
    if arm not in ARMS or master != 9601:
        raise ValueError("B01 binds SCALAR/Q32 and unscreened master9601")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    counts = new_counts()
    timings = dict(initialization=0.0, training_collection=0.0, frozen_baselines=0.0,
                   updates=0.0, final_evaluation=0.0, checkpoint_publication=0.0)
    summary = dict(arm=arm, seed=master, launch_sha=launch_sha, status="incomplete",
                   counts=counts, timings_seconds=timings, device="cpu", dtype="float32",
                   torch_threads=torch.get_num_threads(), cost_law=COST_LAW,
                   cost_unit_rates="UNKNOWN before the original invocation",
                   initial_ordinary_runtime_plan_seconds=900, watchdog_seconds=max_seconds,
                   scientific_class="B/EXPLORE", independent_training_instances=1,
                   training_episodes=TRAIN_EPISODES, horizon=HORIZON,
                   batch_episodes=BATCH, epochs=EPOCHS, chunk=CHUNK,
                   alpha=.25, quantiles=(32 if arm == "Q32" else 1))
    env, actor, critic, initial = None, None, None, None
    evaluation_returns = []

    def check():
        if time.monotonic() - process_start >= max_seconds:
            raise TimeoutError(f"whole-arm watchdog {max_seconds}s reached")

    def emit(handle, row):
        handle.write(json.dumps(dict(arm=arm, seed=master, **row), allow_nan=False) + "\n")
        handle.flush()

    print(json.dumps(dict(event="start", arm=arm, seed=master, launch_sha=launch_sha,
                          cost_law=COST_LAW, unit_rates="UNKNOWN")), flush=True)
    try:
        check()
        with phase_time(timings, "initialization"):
            actor, critic = models(master, arm)
            initial = snapshot(actor, critic)
            optimizer = optimizer_for(actor, critic)
            counts["constructor_calls"] += 1
            env = make_real(100000 * master + 1000)
            counts["constructor_resets"] += 1
        velocity_rng = action_generator(master, arm)
        with (out / "episodes.jsonl").open("w", encoding="utf-8") as episodes_file, (
                out / "updates.jsonl").open("w", encoding="utf-8") as updates_file:
            for batch_number in range(TRAIN_EPISODES // BATCH):
                rollouts = []
                with phase_time(timings, "training_collection"):
                    for offset in range(BATCH):
                        episode = batch_number * BATCH + offset
                        rollout, _ = collect_episode(
                            env, actor, 100000 * master + 1000 + episode, velocity_rng,
                            "train", episode, check, counts, lambda row: emit(episodes_file, row))
                        rollouts.append(rollout)
                check()
                with phase_time(timings, "frozen_baselines"):
                    batch = frozen_batch(critic, rollouts)
                with phase_time(timings, "updates"):
                    update(actor, critic, optimizer, batch, check, counts,
                           lambda row: emit(updates_file, dict(batch=batch_number, **row)))
                print(json.dumps(dict(event="batch_complete", arm=arm, batch=batch_number,
                                      counts=counts, elapsed=time.monotonic() - process_start)), flush=True)
            check()
            with phase_time(timings, "checkpoint_publication"):
                actor.eval()
                critic.eval()
                torch.save(dict(arm=arm, seed=master, launch_sha=launch_sha,
                                actor=actor.state_dict(), critic=critic.state_dict(),
                                optimizer_steps=counts["optimizer_steps"]), out / "checkpoint.pt")
            with phase_time(timings, "final_evaluation"):
                for episode in range(EVAL_EPISODES):
                    _, row = collect_episode(
                        env, actor, 100000 * master + 2000 + episode,
                        action_generator(master, arm, episode), "eval", episode,
                        check, counts, lambda result: emit(episodes_file, result))
                    evaluation_returns.append(row["J"])
                    if (episode + 1) % 16 == 0:
                        print(json.dumps(dict(event="eval_progress", arm=arm, episodes=episode + 1,
                                              elapsed=time.monotonic() - process_start)), flush=True)
        summary["endpoint"] = endpoint(evaluation_returns)
        summary["status"] = "complete"
    except Exception as error:
        summary["failure"] = f"{type(error).__name__}: {error}"
        summary["traceback"] = traceback.format_exc()
        print(summary["failure"], flush=True)
    finally:
        summary["complete_final_returns"] = evaluation_returns
        if initial is not None:
            try:
                if all(torch.isfinite(p).all() for module in (actor, critic) for p in module.parameters()):
                    summary["learner_exposure"] = exposure(initial, actor, critic)
                else:
                    summary["learner_exposure_error"] = "nonfinite parameters; displacement unavailable"
            except Exception as error:
                summary["learner_exposure_error"] = str(error)
        if env is not None:
            try:
                env.close()
            except Exception as error:
                summary["close_error"] = str(error)
        summary["peak_rss_bytes"] = peak_rss_bytes()
        summary["resources_unmeasured"] = summary["peak_rss_bytes"] is None
        summary["wall_seconds_through_closeout"] = time.monotonic() - process_start
        summary["wall_note"] = "Includes imports through closeout; final JSON write/exit in supervisor wall."
        write_json(out / "summary.json", summary)
    print(json.dumps(dict(event="terminal", arm=arm, status=summary["status"], counts=counts,
                          wall_seconds=summary["wall_seconds_through_closeout"])), flush=True)
    return summary


def publish_pair(scalar_path, quantile_path, output, launch_sha):
    summaries = [json.loads(Path(path).read_text(encoding="utf-8"))
                 for path in (scalar_path, quantile_path)]
    for arm, summary in zip(ARMS, summaries):
        counts = summary["counts"]
        if (summary["arm"] != arm or summary["seed"] != 9601 or summary["status"] != "complete"
                or counts["train_episodes"] != TRAIN_EPISODES
                or counts["eval_episodes"] != EVAL_EPISODES or counts["optimizer_steps"] != 128):
            raise ValueError("missing complete original B01 arm; preserve independent facts")
    result = contrast(*(summary["endpoint"]["returns"] for summary in summaries))
    result.update(launch_sha=launch_sha, source_summaries=[str(scalar_path), str(quantile_path)],
                  counts={summary["arm"]: summary["counts"] for summary in summaries},
                  summed_arm_wall_seconds=sum(s["wall_seconds_through_closeout"] for s in summaries),
                  claim_ceiling="one paired learning instance, whole-package B/EXPLORE")
    write_json(output, result)
    return result
