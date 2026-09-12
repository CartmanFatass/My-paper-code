"""One whole-arm run and the declared paired endpoint; no retry or search."""

import json
import math
from pathlib import Path
import statistics
import subprocess
import time

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from experiments.candidates.ucope.uav_motion_prefix_b01.study import Deadline, write_summary
from .model import build_arm, snapshot, exposure
from .learner import collect_episode, optimizer_for, update

MASTER, HORIZON, TRAIN, FINAL = 9302, 256, 512, 32
ARMS = ("LEARNED", "RR")


def new_counts():
    return dict.fromkeys(("train_episodes", "eval_episodes", "train_team_steps", "eval_team_steps",
                          "team_steps", "optimizer_steps", "rollouts", "explicit_resets", "motion_decisions",
                          "send_decisions", "attempts", "constructors"), 0)


def run_arm(master, arm, output, started, *, factory=make_real, horizon=HORIZON, train=TRAIN, final=FINAL, chunk=32):
    deadline = Deadline(started, 600, 600, first_arm=arm)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    rows, limits, counts = [], [], new_counts()
    summary = dict(object="CADC-B01", arm=arm, master=master, rows=rows, counts=counts,
                   scientific_invocation=factory is make_real,
                   status="INCOMPLETE", limits=limits, evaluation_optimizer_steps=0,
                   source_sha=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                   configuration=dict(horizon=horizon, train=train, final=final, chunk=chunk,
                                      dtype="float32", device="cpu", threads=1, whole_arm_cap=600),
                   cost_law="imports/admission/construction + 512*256 collection + 1024 Adam/replay + 32*256 final + checkpoint/publication/readback/exit")
    initial = actor = critic = None
    with (out / "episodes.jsonl").open("w", encoding="utf-8") as episodes_file, (out / "updates.jsonl").open("w", encoding="utf-8") as updates_file:
        def emit(row):
            rows.append(row)
            episodes_file.write(json.dumps(row, allow_nan=False) + "\n")
            episodes_file.flush()
        try:
            deadline.check()
            actor, critic = build_arm(master, arm)
            initial = snapshot(actor, critic)
            optimizer = optimizer_for(actor, critic)
            base = master * 100000
            env = factory(base+1000)
            counts["constructors"] += 1
            motion_rng, send_rng = generator(base+21), generator(base+22)
            for rollout in range(train // 2):
                episodes = []
                for e in range(2*rollout, 2*rollout+2):
                    episodes.append(collect_episode(env, actor, critic, horizon, base+1000+e,
                        base+6000+e, motion_rng, send_rng,
                        dict(arm=arm, master=master, phase="train", episode=e,
                             motion_seed=base+21, send_seed=base+22), counts, emit, deadline.check))
                records = update(actor, critic, optimizer, episodes, counts, deadline.check, chunk)
                counts["rollouts"] += 1
                updates_file.write(json.dumps(dict(rollout=rollout, epochs=records), allow_nan=False)+"\n")
                updates_file.flush()
            summary["exposure"] = exposure(initial, actor, critic)
            torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(), arm=arm,
                            master=master, input_size=171, critic_size=451), out / "final.pt")
            for e in range(final):
                collect_episode(env, actor, critic, horizon, base+2000+e, base+7000+e,
                    generator(base+3000+e), generator(base+4000+e),
                    dict(arm=arm, master=master, phase="eval", episode=e,
                         motion_seed=base+3000+e, send_seed=base+4000+e), counts, emit, deadline.check)
            summary["status"] = "COMPLETE"
        except Exception as error:
            limits.append(f"{type(error).__name__}: {error}")
            if initial is not None:
                summary["exposure"] = exposure(initial, actor, critic)
    summary["elapsed_wall"] = time.monotonic()-started
    if summary["elapsed_wall"] > 600:
        summary["status"] = "CAP_BREACH"
    write_summary(out / "summary.json", summary)
    # Exercise/read the actual primary publication before final timing/exit.
    published = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    summary["publication_readback"] = published["counts"] == counts and len(published["rows"]) == len(rows)
    summary["elapsed_wall"] = time.monotonic()-started
    if summary["elapsed_wall"] > 600:
        summary["status"] = "CAP_BREACH"
    write_summary(out / "summary.json", summary)
    return summary


def paired_primary(summaries, expected=FINAL):
    indexed = {s["arm"]: s for s in summaries}
    panels = {arm: [r for r in indexed.get(arm, {}).get("rows", []) if r["phase"] == "eval"] for arm in ARMS}
    complete = all(indexed.get(a, {}).get("status") == "COMPLETE"
                   and [r["episode"] for r in panels[a]] == list(range(expected)) for a in ARMS)
    if complete:
        complete = all(l["master"] == r["master"] and l["reset_seed"] == r["reset_seed"]
                       and l["channel_seed"] == r["channel_seed"] and l["steps"] == r["steps"]
                       for l, r in zip(panels["LEARNED"], panels["RR"]))
    if complete and expected == FINAL:
        required = dict(train_episodes=512, eval_episodes=32, train_team_steps=131072,
                        eval_team_steps=8192, optimizer_steps=1024, rollouts=256)
        complete = all(all(indexed[a]["counts"].get(k) == v for k, v in required.items()) for a in ARMS)
    result = dict(complete=complete, reading="INCOMPLETE", conditional_on="one paired training history", panels=panels)
    if not complete:
        return result
    for metric in ("J_net", "J_physical", "charge_per_tick"):
        values = [l[metric]-r[metric] for l, r in zip(panels["LEARNED"], panels["RR"])]
        if not all(math.isfinite(x) for x in values):
            result.update(complete=False, reading="INCOMPLETE")
            return result
        mean = statistics.mean(values)
        sd = statistics.stdev(values) if len(values)>1 else None
        result[metric] = dict(differences=values, mean=mean, conditional_sd=sd,
                             conditional_se=sd/math.sqrt(len(values)) if sd is not None else None,
                             positive=sum(x>0 for x in values), adverse=sum(x<0 for x in values))
    delta = result["J_net"]["mean"]
    result["reading"] = "ABOVE_MEI" if delta>.01 else "ADVERSE" if delta<-.01 else "INSIDE_MEI"
    return result
