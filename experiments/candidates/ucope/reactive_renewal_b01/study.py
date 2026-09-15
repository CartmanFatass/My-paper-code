"""One continuous fresh R/F/G instance with a single shared final-world panel."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import statistics
import subprocess
import time
import traceback

from ..uav_motion_prefix_b01.study import difference_stats, new_counts, write_summary

CARD = "docs/research/candidates/ucope/UCOPE_REACTIVE_RENEWAL_B01_CARD_20260913.md"
OBJECT = "UCOPE-REACTIVE-RENEWAL-B01"
LABELS = ("R", "F", "G", "H")


@dataclass
class Config:
    seed: int = 8901
    horizon: int = 256
    train_episodes: int = 2048
    eval_episodes: int = 64
    chunk: int = 32
    watchdog_seconds: float = 6000
    fixture: bool = False

    @classmethod
    def engineering(cls):
        return cls(seed=9901, horizon=8, train_episodes=4, eval_episodes=3, chunk=8,
                   watchdog_seconds=180, fixture=True)


def final_panel(rows, expected, invocation_complete):
    values = {arm: {r["episode"]: r["J"] for r in rows
                    if r["arm"] == arm and r["phase"] == "eval"} for arm in LABELS}
    full = {arm: sorted(value) == list(range(expected)) for arm, value in values.items()}
    result = dict(arm_means={arm: statistics.mean(value.values()) if value else None
                            for arm, value in values.items()},
                  returns={arm: [value[i] for i in sorted(value)] for arm, value in values.items()},
                  all_panels_complete=all(full.values()), selected_contrast="R_minus_F")
    for first, second in (("R", "F"), ("R", "G"), ("R", "H"),
                          ("F", "H"), ("G", "H"), ("F", "G")):
        ids = sorted(values[first].keys() & values[second].keys())
        delta = [values[first][i] - values[second][i] for i in ids]
        item = difference_stats(delta)
        item.update(episode_ids=ids, complete=full[first] and full[second],
                    favorable=sum(x > 0 for x in delta), adverse=sum(x < 0 for x in delta),
                    tied=sum(x == 0 for x in delta))
        result[f"{first}_minus_{second}"] = item
    primary = result["R_minus_F"]
    result["complete"] = invocation_complete and result["all_panels_complete"]
    result["reading"] = ("UP" if primary["mean"] > .01 else
                         "DOWN" if primary["mean"] < -.01 else "WITHIN") if result["complete"] else None
    return result


def run(config, out, start=None, factory=None):
    import torch
    from ..uav_motion_prefix_b01.environment import SyntheticAdapter, make_real
    from ..uav_motion_prefix_b01.learner import collect_episode, optimizer_for, update
    from ..uav_motion_prefix_b01.policy import arm_copy, exposure, generator, snapshot, templates
    from . import reactive

    if config.train_episodes % 2 or config.horizon % config.chunk:
        raise ValueError("complete two-episode rollouts and recurrent chunks are required")
    start = time.monotonic() if start is None else start
    cpu_start = time.process_time()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    factory = factory or ((lambda seed: SyntheticAdapter(seed, config.horizon))
                          if config.fixture else make_real)
    rows, limits, arms = [], [], {}
    summary = dict(object=OBJECT, card=CARD, configuration=asdict(config), seed=config.seed,
                   launch_sha=subprocess.check_output(["git", "rev-parse", "HEAD"],
                       cwd=Path(__file__).resolve().parents[4], text=True).strip(),
                   mode="ENGINEERING_FIXTURE" if config.fixture else "UAV_B_EXPLORE",
                   status="INCOMPLETE", arms=arms, limits=limits,
                   independent_training_instances=1, new_fits=3, checkpoints_selected=1,
                   ratio_grouping="agent_compound", entropy_coef=0., value_moments=None,
                   device="cpu", dtype="float32", torch_threads=torch.get_num_threads())
    base = config.seed * 100000
    streams = {"R": (41, 42, 70000, 80000), "F": (31, 32, 30000, 40000),
               "G": (21, 22, 50000, 60000)}
    summary["seeds"] = dict(base=base, initialization=base + 11, gates=base + 12,
                            train_world_start=base + 10000, eval_world_start=base + 20000,
                            stream_offsets=streams)

    def check():
        if time.monotonic() - start > config.watchdog_seconds:
            raise TimeoutError("ordinary invocation watchdog expired; preserve incomplete work")

    with (out / "episodes.jsonl").open("w", encoding="utf-8") as episodes_file, \
            (out / "updates.jsonl").open("w", encoding="utf-8") as updates_file:
        def emit(row):
            rows.append(row)
            episodes_file.write(json.dumps(row, allow_nan=False) + "\n")
            episodes_file.flush()

        try:
            check()
            common = templates(config.seed)
            for arm in LABELS[:-1]:
                arm_start = time.monotonic()
                counts = new_counts(renewal=True, short=True)
                record = dict(counts=counts, train_complete=False, eval_complete=False)
                arms[arm] = record
                actor, critic = arm_copy(common, arm != "G", duration_head_seed=base + 12,
                                         freeze_duration=arm == "F")
                initial = snapshot(actor, critic)
                record["trainable_parameters"] = sum(p.numel() for model in (actor, critic)
                                                       for p in model.parameters() if p.requires_grad)
                optimizer = optimizer_for(actor, critic)
                vrng, grng = (generator(base + offset) for offset in streams[arm][:2])
                check()
                env = factory(base + 10000)
                counts["constructors"] += 1
                counts["constructor_resets"] += 1

                def episode(phase, e, label, model, value_model, velocity, gate, active_counts):
                    reset = base + (10000 if phase == "train" else 20000) + e
                    metadata = dict(pair_master=config.seed, arm=label, phase=phase, episode=e)
                    if label == "R":
                        return reactive.collect_episode(env, model, value_model, config.horizon,
                            reset, velocity, gate, metadata, check, active_counts, emit,
                            real=not config.fixture)
                    return collect_episode(env, model, value_model, config.horizon, reset,
                        velocity, gate, metadata, check, active_counts, emit, lambda row: None,
                        limits, real=not config.fixture, ratio_grouping="agent_compound",
                        value_moments=None, renewal=True, duration_support=(1, 2))

                try:
                    for rollout in range(config.train_episodes // 2):
                        data = [episode("train", 2 * rollout + i, arm, actor, critic,
                                        vrng, grng, counts) for i in range(2)]
                        if arm == "R":
                            losses = reactive.update(actor, critic, optimizer, data,
                                                     config.chunk, check, counts)
                        else:
                            losses = update(actor, critic, optimizer, data, config.chunk,
                                            check, counts, ratio_grouping="agent_compound",
                                            entropy_coef=0., value_moments=None)
                        counts["rollouts"] += 1
                        updates_file.write(json.dumps(dict(arm=arm, rollout=rollout, epochs=losses),
                                                      allow_nan=False) + "\n")
                        updates_file.flush()
                        if (rollout + 1) % 128 == 0:
                            print(f"{arm} episodes={2 * (rollout + 1)} elapsed={time.monotonic()-start:.2f}s",
                                  flush=True)
                    record["train_complete"] = True
                    record["exposure"] = exposure(initial, actor, critic)
                    before_eval = snapshot(actor, critic)
                    before_v, before_g = vrng.get_state().clone(), grng.get_state().clone()
                    for e in range(config.eval_episodes):
                        episode("eval", e, arm, actor, critic,
                                generator(base + streams[arm][2] + e),
                                generator(base + streams[arm][3] + e), counts)
                    record["eval_complete"] = True
                    record["evaluation_parameter_exposure"] = exposure(before_eval, actor, critic)
                    record["training_generators_unchanged_by_evaluation"] = bool(
                        torch.equal(before_v, vrng.get_state()) and torch.equal(before_g, grng.get_state()))
                    torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(), arm=arm,
                                    seed=config.seed, train_episodes=config.train_episodes),
                               out / f"{arm}_final.pt")
                    if arm == "G":
                        hover_counts = new_counts(renewal=True, short=True)
                        arms["H"] = dict(counts=hover_counts, trained=False, eval_complete=False)
                        for e in range(config.eval_episodes):
                            episode("eval", e, "H", None, None, None, None, hover_counts)
                        arms["H"]["eval_complete"] = True
                finally:
                    record["exposure"] = exposure(initial, actor, critic)
                    record["elapsed_wall_seconds"] = time.monotonic() - arm_start
                    if hasattr(env, "close"):
                        env.close()
            summary["status"] = "COMPLETE"
        except Exception as error:
            traceback.print_exc()
            summary["error"] = dict(type=type(error).__name__, message=str(error))

    summary["panel"] = final_panel(rows, config.eval_episodes, summary["status"] == "COMPLETE")
    keys = {key for record in arms.values() for key in record["counts"]}
    summary["counts"] = {key: sum(record["counts"].get(key, 0) for record in arms.values())
                         for key in sorted(keys)}
    summary["elapsed_wall_seconds"] = time.monotonic() - start
    summary["aggregate_process_cpu_seconds"] = time.process_time() - cpu_start
    summary["resource_note"] = "Peak RSS and complete supervisor wall are collected separately; support cost is not included here."
    write_summary(out / "summary.json", summary)
    return summary
