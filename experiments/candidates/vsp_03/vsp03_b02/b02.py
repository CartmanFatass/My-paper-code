"""VSP03 B02 shared service, fixed seed4 pair. scope: none"""
import json
import math
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from experiments.candidates.vsp_03.vsp03_b01.b01 import (
    objective, vectors, scales, write_json, peak_rss,
)


class Model(nn.Module):
    def __init__(self, seed, arm):
        super().__init__()
        torch.manual_seed(40000 + seed)
        self.actor = nn.Sequential(nn.Linear(14, 32), nn.Tanh(), nn.Linear(32, 32),
                                   nn.Tanh(), nn.Linear(32, 1))
        self.direct_b = nn.Parameter(torch.tensor(0.0))
        self.critic = nn.Sequential(nn.Linear(14, 32), nn.Tanh(), nn.Linear(32, 1))
        nn.init.zeros_(self.actor[-1].weight)
        nn.init.zeros_(self.actor[-1].bias)
        if arm == "T":
            with torch.no_grad():
                self.actor[-1].bias.fill_(-math.log(3))
                self.direct_b.fill_(2 * math.log(3))

    def logits(self, x):
        return self.actor(x).squeeze(-1) + self.direct_b * x[:, 5]


def rng(address):
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(address)))


def worlds(seed, split, first, count):
    draws = np.empty((count, 40, 2), dtype=np.float64)
    phase = np.empty(count, dtype=np.int64)
    for i, episode in enumerate(range(first, first + count)):
        for target in (0, 1):
            draws[i, :, target] = rng([302, seed, split, episode, target]).random(40)
        phase[i] = rng([302, seed, split, episode, 2]).integers(0, 2)
    return draws, phase


def action_tapes(seed, split, mode, arm, first, count):
    return np.stack([rng([303, seed, split, mode, arm, episode]).random(17)
                     for episode in range(first, first + count)])


def rule_actions(x, rule):
    ready = x[:, 5] == 1
    if rule == "R0":
        return ready
    yield_to_partner = ((x[:, 11] == 1) & (x[:, 13] < 1) &
                        (x[:, 10] == 1) & (x[:, 7] > x[:, 2]))
    return ready & ~yield_to_partner


def return_to_go(units, episode_ids, prefixes):
    return (units.sum(axis=1)[episode_ids] - prefixes).astype(np.float32) / 400


def rollout(draws, phase, model=None, uniforms=None, rule="R0", scripted=None,
            deadline=float("inf"), activity=None, trace=False):
    """Batched independent worlds; causal time stays serial. No future tape in x.

    State arrays [world,target] live for all forty transitions. slot_until [world]
    is free at its boundary, after the preceding interval's completion reward.
    Only eligible decisions are packed; forced waits still update event latches.
    """
    n = len(draws)
    if activity is not None:
        activity["episodes_started"] += n
    y = np.ones((n, 2), dtype=bool)
    d = np.zeros((n, 2), dtype=np.int64)
    a = np.zeros((n, 2), dtype=bool)
    e = np.zeros((n, 2), dtype=bool)
    submit = np.full((n, 2), -1, dtype=np.int64)
    success = np.ones((n, 2), dtype=bool)
    slot_until = np.zeros(n, dtype=np.int64)
    accrued = np.zeros(n, dtype=np.int64)
    counts = np.zeros((n, 5), dtype=np.int64)
    observations, actions, episode_ids, times, prefixes = [], [], [], [], []
    audit = []
    forwards = 0
    all_ids = np.arange(n)
    interval_units = np.zeros((n, 40), dtype=np.int64)
    for t in range(40):
        if time.perf_counter() >= deadline:
            raise TimeoutError("complete invocation cap during rollout")
        reward = np.zeros(n, dtype=np.int64)
        if t <= 32 and t % 2 == 0:
            own = np.where(t % 4 == 0, phase, 1 - phase)
            partner = 1 - own
            pending = submit[all_ids, own] < 0
            free = t >= slot_until
            eligible = pending & free
            blocked = pending & ~free
            counts[:, 0] += 1
            counts[:, 1] += pending
            counts[:, 2] += eligible
            counts[:, 3] += blocked
            counts[:, 4] += blocked & (t >= 30)
            ids = np.flatnonzero(eligible)
            o, p = own[ids], partner[ids]
            b = a & y & ~e
            next_partner = t + 2 if t < 32 else 40
            x = np.column_stack((np.full(len(ids), t / 40),
                y[ids, o], d[ids, o] / 40, a[ids, o], e[ids, o], b[ids, o],
                y[ids, p], d[ids, p] / 40, a[ids, p], e[ids, p], b[ids, p],
                submit[ids, p] < 0, o != phase[ids],
                np.full(len(ids), next_partner / 40))).astype(np.float32)
            # At t30 the partner's next clock is32; at t32 phase-two has none.
            action = np.zeros(len(ids), dtype=bool)
            if len(ids):
                if scripted is not None:
                    action = scripted(ids, t, o, x)
                elif model is None:
                    action = rule_actions(x, rule)
                else:
                    with torch.no_grad():
                        logits = model.logits(torch.from_numpy(x))
                        action = ((logits > 0).numpy() if uniforms is None else
                                  uniforms[ids, t // 2] < logits.sigmoid().numpy())
                    forwards += 1
                observations.append(x)
                actions.append(action.astype(np.float32))
                episode_ids.append(ids)
                times.append(np.full(len(ids), t, dtype=np.int64))
                prefixes.append(accrued[ids].copy())
                chosen = ids[action]
                submit[chosen, o[action]] = t
                slot_until[chosen] = t + 8
                reward[chosen] -= 10
            if trace:
                audit.append({"t": t, "eligible": eligible.copy(), "blocked": blocked.copy(),
                              "free_before": free.copy(), "a_before": a.copy(),
                              "e_before": e.copy(), "b_before": b.copy()})
            # Both real CONTINUE and forced waiting rearm, with no blocked row.
            waiting_ids = np.flatnonzero(pending)
            waiting_own = own[waiting_ids]
            still_pending = submit[waiting_ids, waiting_own] < 0
            a[waiting_ids, waiting_own] = y[waiting_ids, waiting_own] & still_pending
            e[waiting_ids, waiting_own] = False
        reward -= (submit < 0).sum(axis=1)
        leave = y & (draws[:, t, :] < 1 / (d + 4))
        enter = ~y & (draws[:, t, :] < 0.5)
        d = np.where(y & ~leave, d + 1, 0)
        y = (y & ~leave) | enter
        e |= leave & a & (submit < 0)
        service = (submit >= 0) & (t >= submit) & (t < submit + 8)
        success[service] &= y[service]
        completed = (submit >= 0) & (t + 1 == submit + 8)
        reward += 200 * (completed & success).sum(axis=1)
        interval_units[:, t] = reward
        accrued += reward
        if activity is not None:
            activity["team_ticks"] += n
            activity["target_transitions"] += 2 * n
    attempt = submit >= 0
    success &= attempt
    waiting = np.where(attempt, submit, 40)
    units = 200 * success.astype(np.int64) - 10 * attempt.astype(np.int64) - waiting
    ids, ts, prefix = map(np.concatenate, (episode_ids, times, prefixes))
    rows = []
    fields = ("fixed_clocks", "pending_clocks", "eligible_decisions", "blocked_pending",
              "blocked_final_clocks")
    for i in range(n):
        rows.append({"world": i, "phase_zero_identity": int(phase[i]),
            "return": float(units[i].sum() / 400),
            "jobs": [{"units": int(units[i, j]), "success": int(success[i, j]),
                "attempt": int(attempt[i, j]), "failed_attempt": int(attempt[i, j] and not success[i, j]),
                "non_submission": int(not attempt[i, j]), "waiting_ticks": int(waiting[i, j]),
                "submission_time": int(submit[i, j])} for j in (0, 1)],
            **dict(zip(fields, map(int, counts[i])))})
    if activity is not None:
        activity["episodes_completed"] += n
        activity["decision_rows"] += len(ids)
        activity["rollout_policy_forwards"] += forwards
    return {"x": np.concatenate(observations), "actions": np.concatenate(actions),
            "episode_ids": ids, "times": ts, "prefixes": prefix,
            "returns": return_to_go(units, ids, prefix), "units": units,
            "interval_units": interval_units, "trace": audit, "rows": rows,
            "episodes": n, "decision_rows": len(ids), "policy_forwards": forwards}


def metrics(rows):
    fields = ("return", "fixed_clocks", "pending_clocks", "eligible_decisions",
              "blocked_pending", "blocked_final_clocks")
    result = {key: float(np.mean([r[key] for r in rows])) for key in fields}
    for key in ("success", "attempt", "failed_attempt", "non_submission", "waiting_ticks"):
        result[key + "_per_team"] = float(np.mean([sum(j[key] for j in r["jobs"]) for r in rows]))
    return {"episodes": len(rows), **result}


def difference(left, right):
    values = np.array([a["return"] - b["return"] for a, b in zip(left, right)])
    sd = float(values.std(ddof=1))
    return {"mean": float(values.mean()), "conditional_world_sd": sd,
            "conditional_world_se": sd / math.sqrt(len(values)), "worlds": len(values)}


def run(seed, out, launch_sha, started, node, command):
    from .check import focused_check

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    deadline = started + 120
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    activity = {"episodes_started": 0, "episodes_completed": 0, "team_ticks": 0,
                "target_transitions": 0, "decision_rows": 0, "rollout_policy_forwards": 0}
    summary = {"object": "VSP03_B02", "seed": seed, "launch_sha": launch_sha,
        "node": node, "command": command, "status": "incomplete", "arms": {},
        "actual_rollouts": activity, "model_constructions": 0, "optimizer_steps": 0,
        "device": "cpu", "dtype": "float32", "compute_threads": 1,
        "rng": {"worlds": "PCG64 SeedSequence([302,seed,split,episode,target]);40 uniforms",
            "phase": "[302,seed,split,episode,2];one integers(0,2)",
            "actions": "[303,seed,split,mode,arm,episode];17 calendar-position uniforms",
            "splits": "train100/evaluation200", "modes": "train0/stochastic-final1",
            "arms": "T0/G1", "initialization": 40000 + seed},
        "cost_law": "admission+imports+2*(init+128*batch128x40x2+2*eval1024x40x2+weights)"
                    "+2*rule1024x40x2+check8x40x2+publication/readback/exit",
        "aggregate_cpu_s": None}
    endpoints = {}
    try:
        eval_draws, eval_phase = worlds(seed, 200, 0, 1024)
        for arm_index, arm in enumerate(("T", "G")):
            arm_started = time.perf_counter()
            model = Model(seed, arm)
            summary["model_constructions"] += 1
            initial = vectors(model)
            record = {"initial": scales(model, initial), "training_episodes": 0,
                      "training_team_ticks": 0, "training_target_transitions": 0,
                      "training_valid_rows": 0, "gradient_rows": 0, "optimizer_steps": 0,
                      "backward_calls": 0, "evaluation_episodes": 0}
            summary["arms"][arm] = record
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001, betas=(0.9, 0.999),
                                         eps=1e-8, weight_decay=0)
            if arm == "T":
                summary["focused_check"] = focused_check(model, out, deadline, activity)
            with (out / f"{arm}_curve.jsonl").open("w", encoding="utf-8") as curve:
                for update in range(1, 129):
                    first = (update - 1) * 128
                    draws, phase = worlds(seed, 100, first, 128)
                    batch = rollout(draws, phase, model,
                        action_tapes(seed, 100, 0, arm_index, first, 128),
                        deadline=deadline, activity=activity)
                    loss, info = objective(model, batch, update)
                    optimizer.zero_grad(set_to_none=True)
                    loss.backward()
                    optimizer.step()
                    record["training_episodes"] += 128
                    record["training_team_ticks"] += 5120
                    record["training_target_transitions"] += 10240
                    record["training_valid_rows"] += batch["decision_rows"]
                    record["gradient_rows"] += batch["decision_rows"]
                    record["optimizer_steps"] += 1
                    record["backward_calls"] += 1
                    summary["optimizer_steps"] += 1
                    curve.write(json.dumps({"update": update, **info, **metrics(batch["rows"]),
                        "valid_rows": batch["decision_rows"], "gradient_rows": batch["decision_rows"]},
                        allow_nan=False) + "\n")
                    curve.flush()
                    if update in (1, 128):
                        record["first" if update == 1 else "final"] = scales(model, initial)
                    if update in (1, 32, 64, 128):
                        print(json.dumps({"arm": arm, "update": update,
                            "elapsed_s": time.perf_counter() - started,
                            "actual_rollouts": activity,
                            "optimizer_steps": summary["optimizer_steps"]}), flush=True)
            for mode in ("greedy", "stochastic"):
                uniforms = (None if mode == "greedy" else
                            action_tapes(seed, 200, 1, arm_index, 0, 1024))
                batch = rollout(eval_draws, eval_phase, model, uniforms,
                                deadline=deadline, activity=activity)
                name = arm + "_" + mode
                endpoints[name] = write_json(out / (name + ".json"), batch["rows"])
                record["evaluation_episodes"] += 1024
            state = model.state_dict()
            torch.save(state, out / f"{arm}_final.pt")
            persisted = torch.load(out / f"{arm}_final.pt", map_location="cpu", weights_only=True)
            assert all(torch.equal(state[k], persisted[k]) for k in state)
            record["weights_readback"] = True
            record["arm_wall_s"] = time.perf_counter() - arm_started
        for rule in ("R", "R0"):
            batch = rollout(eval_draws, eval_phase, rule=rule, deadline=deadline, activity=activity)
            endpoints[rule] = write_json(out / (rule + ".json"), batch["rows"])
        summary["absolute"] = {name: metrics(rows) for name, rows in endpoints.items()}
        contrasts = [("T_greedy", "R"), ("T_greedy", "G_greedy"), ("G_greedy", "R"),
                     ("T_greedy", "R0"), ("G_greedy", "R0")]
        for arm in ("T", "G"):
            contrasts.extend((arm + "_stochastic", ref) for ref in ("R", "R0", arm + "_greedy"))
        write_json(out / "paired_differences.json", [
            {"world": i, "phase_zero_identity": int(eval_phase[i]),
             **{a + "-" + b: endpoints[a][i]["return"] - endpoints[b][i]["return"]
                for a, b in contrasts}} for i in range(1024)])
        summary["comparisons"] = {a + "-" + b: difference(endpoints[a], endpoints[b]) for a, b in contrasts}
        summary["primary"] = summary["comparisons"]["T_greedy-R"]
        summary["independent_training_pairs"] = 1
        summary["status"] = "complete"
    except Exception as exc:
        summary["error"] = repr(exc)
        raise
    finally:
        summary["elapsed_through_output_start_s"] = time.perf_counter() - started
        summary["peak_rss_bytes"] = peak_rss()
        persisted = write_json(out / "summary.json", summary)
        assert persisted["actual_rollouts"] == activity
        if summary["status"] == "complete":
            assert persisted["primary"] == summary["primary"]
        print(json.dumps({"status": summary["status"], "counts": activity,
                          "elapsed_through_readback_s": time.perf_counter() - started}), flush=True)
        if time.perf_counter() >= deadline:
            raise TimeoutError("complete invocation cap through publication/readback")
