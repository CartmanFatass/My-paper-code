"""Complete N1 episodes and the selected joint episodic actor-critic.

RNG: PCG64 SeedSequence([seed, split, episode]), 40 draws per episode;
train split 100, evaluation split 200+update. Torch initialization 10000+seed,
T/G action streams 20000+seed/30000+seed, active rows in boundary/episode order.
The eight check tapes are deterministic constants and consume no RNG stream.
scope: none
"""
import json
import math
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn


class Model(nn.Module):
    def __init__(self, seed, arm):
        super().__init__()
        torch.manual_seed(10000 + seed)
        self.actor = nn.Sequential(nn.Linear(6, 32), nn.Tanh(), nn.Linear(32, 32),
                                   nn.Tanh(), nn.Linear(32, 1))
        self.direct_b = nn.Parameter(torch.tensor(0.0))
        self.critic = nn.Sequential(nn.Linear(6, 32), nn.Tanh(), nn.Linear(32, 1))
        nn.init.zeros_(self.actor[-1].weight)
        nn.init.zeros_(self.actor[-1].bias)
        if arm == "T":
            with torch.no_grad():
                self.direct_b.fill_(2 * math.log(3))
                self.actor[-1].bias.fill_(-math.log(3))

    def logits(self, x):
        return self.actor(x).squeeze(-1) + self.direct_b * x[:, 5]


def tapes(seed, split, first, count):
    return np.stack([np.random.Generator(np.random.PCG64(
        np.random.SeedSequence([seed, split, episode]))).random(40)
        for episode in range(first, first + count)])


def return_to_go(units, episode_ids, times):
    """Remove sunk waiting costs from the native terminal utility, gamma=1."""
    return (units[episode_ids] + times).astype(np.float32) / 200


def rollout(draws, model=None, generator=None, scripted=None, deadline=float("inf"), activity=None):
    """Advance every tick. Policy sees only the current state, never the tape.

    scripted is used only by the one eight-episode check; values are submit times.
    Packed decision rows avoid any padding/post-submit gradient samples.
    """
    n = len(draws)
    if activity is not None:
        activity["episodes_started"] += n
    y = np.ones(n, dtype=bool)
    d = np.zeros(n, dtype=np.int64)
    a = np.zeros(n, dtype=bool)
    e = np.zeros(n, dtype=bool)
    submit = np.full(n, -1, dtype=np.int64)
    success = np.ones(n, dtype=bool)
    departures = np.zeros(n, dtype=np.int64)
    reentries = np.zeros(n, dtype=np.int64)
    prior_departures = np.zeros(n, dtype=np.int64)
    prior_reentries = np.zeros(n, dtype=np.int64)
    submit_b = np.full(n, -1, dtype=np.int64)
    submit_e = np.full(n, -1, dtype=np.int64)
    observations, actions, episode_ids, times = [], [], [], []
    forwards = ticks = 0
    for t in range(40):
        if time.perf_counter() >= deadline:
            raise TimeoutError("whole invocation cap during complete episode batch")
        if t <= 32 and t % 4 == 0:
            ids = np.flatnonzero(submit < 0)
            if len(ids):
                b = a[ids] & y[ids] & ~e[ids]
                x = np.column_stack((np.full(len(ids), t / 40), y[ids], d[ids] / 40,
                                     a[ids], e[ids], b)).astype(np.float32)
                if scripted is not None:
                    action = scripted[ids] == t
                elif model is None:
                    action = b
                else:
                    with torch.no_grad():
                        logits = model.logits(torch.from_numpy(x))
                        forwards += 1
                        if activity is not None:
                            activity["rollout_policy_forwards"] += 1
                        action = ((logits > 0) if generator is None else
                                  (torch.rand(len(ids), generator=generator) < logits.sigmoid()))
                        action = action.numpy()
                observations.append(x)
                actions.append(action.astype(np.float32))
                episode_ids.append(ids)
                times.append(np.full(len(ids), t, dtype=np.int64))
                if activity is not None:
                    activity["decision_rows"] += len(ids)
                chosen = ids[action]
                submit[chosen] = t
                prior_departures[chosen] = departures[chosen]
                prior_reentries[chosen] = reentries[chosen]
                submit_b[chosen] = b[action]
                submit_e[chosen] = e[chosen]
                a[ids] = y[ids] & ~action
                e[ids] = False
        leave = y & (draws[:, t] < 1 / (d + 4))
        enter = ~y & (draws[:, t] < 0.5)
        d = np.where(y & ~leave, d + 1, 0)
        y = (y & ~leave) | enter
        e |= leave & a & (submit < 0)
        departures += leave
        reentries += enter
        service = (submit >= 0) & (t >= submit) & (t < submit + 8)
        success[service] &= y[service]
        ticks += n
        if activity is not None:
            activity["ticks"] += n
    if activity is not None:
        activity["episodes_completed"] += n
    attempt = submit >= 0
    success &= attempt
    waiting = np.where(attempt, submit, 40)
    units = 200 * success.astype(np.int64) - 10 * attempt.astype(np.int64) - waiting
    ids, ts = np.concatenate(episode_ids), np.concatenate(times)
    durations = np.where((submit[ids] == ts) | (ts == 32), 40 - ts, 4)
    # Before each valid boundary, exactly t waiting units have already been paid.
    returns = return_to_go(units, ids, ts)
    rows = [{"episode": i, "return_units": int(units[i]), "return": float(units[i] / 200),
             "success": int(success[i]), "attempt": int(attempt[i]),
             "failed_attempt": int(attempt[i] and not success[i]),
             "non_submission": int(not attempt[i]), "waiting_ticks": int(waiting[i]),
             "submission_time": int(submit[i]), "departures": int(departures[i]),
             "reentries": int(reentries[i]), "pre_submit_departures": int(prior_departures[i]),
             "pre_submit_reentries": int(prior_reentries[i]),
             "submission_b": int(submit_b[i]), "submission_e": int(submit_e[i])}
            for i in range(n)]
    return {"x": np.concatenate(observations), "actions": np.concatenate(actions),
            "episode_ids": ids, "times": ts, "durations": durations, "returns": returns,
            "rows": rows, "episodes": n, "ticks": ticks, "decision_rows": len(ids),
            "policy_forwards": forwards}


def objective(model, batch, update):
    x = torch.from_numpy(batch["x"])
    distribution = torch.distributions.Bernoulli(logits=model.logits(x))
    values = model.critic(x).squeeze(-1)
    error = torch.from_numpy(batch["returns"]) - values
    actor = -(distribution.log_prob(torch.from_numpy(batch["actions"])) *
              error.detach()).sum() / batch["episodes"]
    critic = 0.5 * error.square().mean()
    entropy = distribution.entropy().sum() / batch["episodes"]
    coefficient = 0.01 * max(0, (64 - update) / 63)
    return actor + critic - coefficient * entropy, {
        "actor_loss": float(actor.detach()), "critic_loss": float(critic.detach()),
        "entropy_per_episode": float(entropy.detach()), "entropy_coefficient": coefficient}


def vectors(model):
    actor = torch.cat([p.detach().flatten() for p in model.actor.parameters()] +
                      [model.direct_b.detach().reshape(1)]).clone()
    critic = torch.cat([p.detach().flatten() for p in model.critic.parameters()]).clone()
    return {"actor": actor, "critic": critic, "total": torch.cat((actor, critic))}


def scales(model, initial):
    result = {}
    for name, value in vectors(model).items():
        base = initial[name]
        norm = float(base.norm())
        displacement = float((value - base).norm())
        result[name] = {"parameters": value.numel(), "initial_l2": norm,
                        "initial_rms": float(base.square().mean().sqrt()),
                        "current_l2": float(value.norm()), "displacement_l2": displacement,
                        "displacement_over_initial_l2": displacement / norm if norm else None}
    return result


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def metrics(rows):
    fields = ("return", "success", "attempt", "failed_attempt", "non_submission",
              "waiting_ticks", "departures", "reentries")
    result = {field: float(np.mean([row[field] for row in rows])) for field in fields}
    result["episodes"] = len(rows)
    for name, key in (("submitted_after_departure", "pre_submit_departures"),
                      ("submitted_after_reentry", "pre_submit_reentries")):
        selected = [row for row in rows if row["attempt"] and row[key] > 0]
        result[name] = {"episodes": len(selected),
                        "mean_return": float(np.mean([r["return"] for r in selected]))
                        if selected else None}
    return result


def focused_check(model, out, deadline, activity):
    # 0 clean F-like t4; 1 depart/reenter before t4, submit t8;
    # 2 first service sample fails; 3 last service sample fails;
    # 4 submit t32; 5 never submit; 6 reentry at first service sample;
    # 7 unarmed interval (t4 absent), reentry/departure before t8.
    draws = np.full((8, 40), 0.99)
    draws[1, [0, 1]] = 0
    draws[2, 4] = 0
    draws[3, 11] = 0
    draws[6, [0, 4]] = 0
    draws[7, [0, 4, 5, 6]] = 0
    batch = rollout(draws, scripted=np.array([4, 8, 4, 4, 32, -1, 4, 8]),
                    deadline=deadline, activity=activity)
    assert batch["ticks"] == 320
    assert [r["return_units"] for r in batch["rows"]] == [186, 182, -14, -14, 158, -40, 186, 182]
    def obs(episode, t):
        mask = (batch["episode_ids"] == episode) & (batch["times"] == t)
        return batch["x"][mask][0]
    assert np.array_equal(obs(0, 0)[3:], [0, 0, 0])
    assert np.array_equal(obs(0, 4)[3:], [1, 0, 1])
    assert np.array_equal(obs(1, 4)[3:], [1, 1, 0])
    assert np.array_equal(obs(1, 8)[3:], [1, 0, 1])
    assert np.array_equal(obs(7, 8)[3:], [0, 0, 0])
    assert batch["durations"][(batch["episode_ids"] == 5) & (batch["times"] == 32)][0] == 8
    loss, info = objective(model, batch, 1)
    loss.backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
    model.zero_grad(set_to_none=True)
    result = {"episodes": 8, "ticks": 320, "decision_rows": batch["decision_rows"],
              "gradient_rows": batch["decision_rows"], "policy_forwards": 1,
              "critic_forwards": 1, "backward_calls": 1, "optimizer_steps": 0,
              "loss": info, "rows": batch["rows"]}
    assert write_json(out / "focused_check.json", result) == result
    return result


def peak_rss():
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except ImportError:
        import psutil
        return psutil.Process().memory_info().peak_wset


def run(seed, out, launch_sha, started):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    deadline = started + 1800
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    summary = {"object": "VSP03_B01_EVENT_RULE_INITIALIZATION", "seed": seed,
               "launch_sha": launch_sha, "status": "incomplete", "arms": {},
               "configuration_count": 1, "device": "cpu", "dtype": "float32",
               "compute_threads": 1, "rng": {"initialization": 10000 + seed,
               "T_actions": 20000 + seed, "G_actions": 30000 + seed,
               "environment": "PCG64 SeedSequence([seed, split, episode]); 40 draws",
               "training_split": 100, "evaluation_split": "200+update"},
               "cost_law": "sum_q(I_q+128*C_q(128,40)+10*E_q(128,40)+O_q)"
                           "+imports/check+8*F(128,40)+summary/publication/readback"}
    summary["actual_rollouts"] = {"episodes_started": 0, "episodes_completed": 0,
                                 "ticks": 0, "decision_rows": 0, "rollout_policy_forwards": 0}
    summary["model_constructions"] = 0
    endpoint_rows = {}
    try:
        for arm in ("T", "G"):
            if time.perf_counter() >= deadline:
                raise TimeoutError("whole invocation cap before arm initialization")
            init_start = time.perf_counter()
            if arm == "T":
                summary["imports_setup_wall_s"] = init_start - started
            model = Model(seed, arm)
            summary["model_constructions"] += 1
            initial = vectors(model)
            optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, betas=(0.9, 0.999),
                                         eps=1e-8, weight_decay=0)
            generator = torch.Generator().manual_seed((20000 if arm == "T" else 30000) + seed)
            record = {"initial": scales(model, initial), "training_episodes": 0,
                      "training_ticks": 0, "training_decision_rows": 0, "gradient_rows": 0,
                      "optimizer_steps": 0, "backward_calls": 0, "policy_forwards": 0,
                      "critic_forwards": 0, "evaluation_episodes": 0, "evaluation_ticks": 0,
                      "evaluation_decision_rows": 0, "evaluation_policy_forwards": 0,
                      "endpoints": {}, "initialization_wall_s": time.perf_counter() - init_start,
                      "training_batch_wall_s": [], "evaluation_batch_wall_s": []}
            summary["arms"][arm] = record
            if arm == "T":
                check_start = time.perf_counter()
                summary["focused_check"] = focused_check(model, out, deadline, summary["actual_rollouts"])
                summary["check_wall_s"] = time.perf_counter() - check_start
            with (out / f"{arm}_curve.jsonl").open("w", encoding="utf-8") as curve:
                for update in range(1, 129):
                    batch_start = time.perf_counter()
                    if batch_start >= deadline:
                        raise TimeoutError("whole invocation cap before training batch")
                    batch = rollout(tapes(seed, 100, (update - 1) * 128, 128), model,
                                    generator, deadline=deadline, activity=summary["actual_rollouts"])
                    loss, info = objective(model, batch, update)
                    optimizer.zero_grad(set_to_none=True)
                    loss.backward()
                    optimizer.step()
                    record["training_batch_wall_s"].append(time.perf_counter() - batch_start)
                    for key, value in (("training_episodes", batch["episodes"]),
                                       ("training_ticks", batch["ticks"]),
                                       ("training_decision_rows", batch["decision_rows"]),
                                       ("gradient_rows", batch["decision_rows"]),
                                       ("policy_forwards", batch["policy_forwards"] + 1),
                                       ("critic_forwards", 1), ("optimizer_steps", 1),
                                       ("backward_calls", 1)):
                        record[key] += value
                    entry = {"update": update, **info, **metrics(batch["rows"]),
                             "decision_rows": batch["decision_rows"],
                             "batch_wall_s": record["training_batch_wall_s"][-1]}
                    curve.write(json.dumps(entry, allow_nan=False) + "\n")
                    curve.flush()
                    if update in (1, 128):
                        record["first" if update == 1 else "final"] = scales(model, initial)
                    if update in (32, 64, 128):
                        rows = []
                        for first in range(0, 1024 if update == 128 else 128, 128):
                            eval_start = time.perf_counter()
                            evaluated = rollout(tapes(seed, 200 + update, first, 128),
                                                model, deadline=deadline, activity=summary["actual_rollouts"])
                            record["evaluation_batch_wall_s"].append(time.perf_counter() - eval_start)
                            for row in evaluated["rows"]:
                                row["episode"] += first
                            rows.extend(evaluated["rows"])
                            record["evaluation_episodes"] += evaluated["episodes"]
                            record["evaluation_ticks"] += evaluated["ticks"]
                            record["evaluation_decision_rows"] += evaluated["decision_rows"]
                            record["evaluation_policy_forwards"] += evaluated["policy_forwards"]
                        assert write_json(out / f"{arm}_endpoint_{update}.json", rows) == rows
                        endpoint_rows[arm, update] = rows
                        record["endpoints"][str(update)] = metrics(rows)
                    record["measured_partial_cost_projection_s"] = (record["initialization_wall_s"] +
                        128 * float(np.mean(record["training_batch_wall_s"])) +
                        (10 * float(np.mean(record["evaluation_batch_wall_s"]))
                         if record["evaluation_batch_wall_s"] else 0))
                    record["projection_unmeasured_terms"] = (["evaluation", "publication"]
                        if not record["evaluation_batch_wall_s"] else ["publication"])
                    record["full_cost_projection_s"] = None
                    if update in (1, 32, 64, 128):
                        print(json.dumps({"arm": arm, "update": update,
                            "C_128_40_s": float(np.mean(record["training_batch_wall_s"])),
                            "E_128_40_s": float(np.mean(record["evaluation_batch_wall_s"]))
                            if record["evaluation_batch_wall_s"] else None,
                            "measured_partial_cost_projection_s": record["measured_partial_cost_projection_s"],
                            "unmeasured_terms": record["projection_unmeasured_terms"]}), flush=True)
                    if time.perf_counter() >= deadline:
                        raise TimeoutError("whole invocation cap after update/evaluation")
            publication_start = time.perf_counter()
            state_path = out / f"{arm}_final.pt"
            torch.save(model.state_dict(), state_path)
            restored = torch.load(state_path, map_location="cpu", weights_only=True)
            assert all(torch.equal(value, restored[key]) for key, value in model.state_dict().items())
            assert len((out / f"{arm}_curve.jsonl").read_text(encoding="utf-8").splitlines()) == 128
            record["publication_wall_s"] = time.perf_counter() - publication_start
            record["arm_wall_s_excluding_shared_check"] = (time.perf_counter() - init_start -
                (summary["check_wall_s"] if arm == "T" else 0))
            record["O_curve_endpoint_state_publication_s"] = (
                record["arm_wall_s_excluding_shared_check"] - record["initialization_wall_s"] -
                sum(record["training_batch_wall_s"]) - sum(record["evaluation_batch_wall_s"]))
            record["full_cost_projection_s"] = (record["measured_partial_cost_projection_s"] +
                                               record["O_curve_endpoint_state_publication_s"])
            record["projection_unmeasured_terms"] = []
        fixed_rows = []
        fixed_decisions = 0
        summary["fixed_batch_wall_s"] = []
        for first in range(0, 1024, 128):
            fixed_start = time.perf_counter()
            batch = rollout(tapes(seed, 328, first, 128), deadline=deadline,
                            activity=summary["actual_rollouts"])
            fixed_decisions += batch["decision_rows"]
            summary["fixed_batch_wall_s"].append(time.perf_counter() - fixed_start)
            for row in batch["rows"]:
                row["episode"] += first
            fixed_rows.extend(batch["rows"])
        assert write_json(out / "F_endpoint_128.json", fixed_rows) == fixed_rows
        summary["F"] = metrics(fixed_rows)
        summary["F"]["ticks"] = len(fixed_rows) * 40
        summary["F"]["decision_rows"] = fixed_decisions
        summary["F"]["policy_forwards"] = 0
        summary["status"] = "complete"
    except Exception as error:
        summary["failure"] = {"type": type(error).__name__, "message": str(error)}
        raise
    finally:
        summary["paired_endpoints"] = {}
        summary["joint_optimizer_steps"] = sum(r["optimizer_steps"] for r in summary["arms"].values())
        for update in (32, 64, 128):
            if ("T", update) in endpoint_rows and ("G", update) in endpoint_rows:
                delta = np.array([t["return"] - g["return"] for t, g in
                                  zip(endpoint_rows["T", update], endpoint_rows["G", update])])
                summary["paired_endpoints"][str(update)] = {"mean_T_minus_G": float(delta.mean()),
                    "conditional_episode_se": float(delta.std(ddof=1) / np.sqrt(len(delta))),
                    "episodes": len(delta), "training_seed_pairs": 1}
        try:
            summary["peak_rss_bytes"] = peak_rss()
            summary["rss_scope"] = "main process OS high-water mark"
        except (ImportError, AttributeError, OSError):
            summary["peak_rss_bytes"] = None
            summary["resources_unmeasured"] = True
        summary["wall_s_before_summary"] = time.perf_counter() - started
        if summary["wall_s_before_summary"] >= 1800:
            summary["status"] = "incomplete_cap"
        assert write_json(out / "summary.json", summary) == summary
        # Terminal log closes the timing boundary after summary publication/read-back.
        whole_wall = time.perf_counter() - started
        if whole_wall > 1800:
            summary["status"] = "incomplete_cap"
            write_json(out / "summary.json", summary)
            whole_wall = time.perf_counter() - started
        print(json.dumps({"whole_wall_s": whole_wall, "cap_seconds": 1800,
                          "within_cap": whole_wall <= 1800, "status": summary["status"],
                          "peak_rss_bytes": summary["peak_rss_bytes"]}), flush=True)
        if whole_wall > 1800 and "failure" not in summary:
            raise TimeoutError("whole invocation cap includes final publication/readback")
    return summary
