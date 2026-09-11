"""The selected B01 host, two Q parameterizations, and renewal learner.

Only run() creates random streams, models or scientific exposure. No reference
policy, extra training episode, tuning pass or evaluation smoke is executed.
"""
from collections import Counter
import itertools
import time

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from .reporting import curve_metrics, write_read

CONTEXTS = tuple(itertools.product((2, 6), (2, 4), (0, 1)))
CHECKPOINTS = tuple(range(0, 129, 16))
# Named streams use stable integer tags, never Python's process-randomized hash.
STREAM_TAGS = {"context": 101, "exploration": 102,
               "FACTOR_dense": 201, "FACTOR_embedding": 202,
               "GENERIC_dense": 301, "evaluation": 401}


class Value(nn.Module):
    def __init__(self, arm, seed):
        super().__init__()
        self.arm = arm
        width, inputs, outputs = (16, 6, 4) if arm == "FACTOR" else (19, 8, 1)
        # Empty Parameters avoid the discarded RNG draws of Linear constructors.
        self.w1 = nn.Parameter(torch.empty(width, inputs, dtype=torch.float32))
        self.b1 = nn.Parameter(torch.zeros(width, dtype=torch.float32))
        self.w2 = nn.Parameter(torch.empty(outputs, width, dtype=torch.float32))
        self.b2 = nn.Parameter(torch.zeros(outputs, dtype=torch.float32))
        dense = torch.Generator(device="cpu").manual_seed(seed * 1000 + STREAM_TAGS[arm + "_dense"])
        nn.init.xavier_uniform_(self.w1, gain=1, generator=dense)
        nn.init.xavier_uniform_(self.w2, gain=1, generator=dense)
        if arm == "FACTOR":
            self.embedding = nn.Parameter(torch.empty(2, 4, dtype=torch.float32))
            embedding = torch.Generator(device="cpu").manual_seed(
                seed * 1000 + STREAM_TAGS["FACTOR_embedding"])
            nn.init.normal_(self.embedding, mean=0, std=0.5, generator=embedding)

    def forward(self, state, action, period):
        action_code = F.one_hot(action, 2).to(torch.float32)
        x = torch.cat((state, action_code), dim=1)
        if self.arm == "GENERIC":
            x = torch.cat((x, F.one_hot(period, 2).to(torch.float32)), dim=1)
        hidden = torch.tanh(F.linear(x, self.w1, self.b1))
        out = F.linear(hidden, self.w2, self.b2)
        if self.arm == "FACTOR":
            return (out * self.embedding[period]).sum(dim=1)
        return out[:, 0]

    def both(self, state, period):
        n = len(state)
        return self(state.repeat_interleave(2, dim=0),
                    torch.arange(2).repeat(n), period.repeat_interleave(2)).reshape(n, 2)


def state_at(context, tick):
    p, tau, c = context.T
    previous = np.where(tick - 1 < tau, c, 1 - c)
    last = np.zeros(len(c)) if tick == 0 else 2 * previous - 1
    return torch.tensor(np.column_stack((2 * c - 1, tau - 3,
                                        np.full(len(c), tick / 6), last)), dtype=torch.float32)


def rollout(model, context, epsilon, draws, actions, counts, checks):
    """Execute six joint ticks, batching only the independent episode axis."""
    n = len(context)
    p, tau, c = context.T
    held = np.zeros(n, dtype=np.int64)
    start_state = torch.empty(n, 4)
    segment_reward = np.zeros(n, dtype=np.int64)
    total_reward = np.zeros(n, dtype=np.int64)
    focal_trace, partner_trace, reward_trace = [], [], []
    rows = []
    for tick in range(6):
        boundary = tick % p == 0
        indices = np.flatnonzero(boundary)
        previous_held = held.copy()
        if len(indices):
            s = state_at(context[indices], tick)
            period = torch.tensor((p[indices] == 6).astype(np.int64))
            with torch.no_grad():
                q = model.both(s, period)
                # torch.argmax returns the first action in an exact tie.
                chosen = q.argmax(dim=1).numpy()
            if draws is not None:
                explore = draws[indices, tick, 0] < epsilon
                random_action = (draws[indices, tick, 1] >= 0.5).astype(np.int64)
                chosen = np.where(explore, random_action, chosen)
            held[indices] = chosen
            start_state[indices] = s
            for idx in indices:
                actions[(*map(int, context[idx]), tick, int(held[idx]))] += 1
            counts["legal_decisions"] += len(indices)
        checks["held_action_violations"] += int(np.count_nonzero(held[~boundary] != previous_held[~boundary]))
        partner = np.where(tick < tau, c, 1 - c)
        reward = (held == partner).astype(np.int64)
        segment_reward += reward
        total_reward += reward
        focal_trace.append(held.copy())
        partner_trace.append(partner.copy())
        reward_trace.append(reward.copy())
        counts["joint_steps"] += n
        finished = np.flatnonzero((tick + 1) % p == 0)
        if len(finished):
            rows.append((start_state[finished].clone(),
                         torch.tensor(held[finished]),
                         torch.tensor((p[finished] == 6).astype(np.int64)),
                         torch.tensor(segment_reward[finished] / 6, dtype=torch.float32),
                         state_at(context[finished], tick + 1),
                         torch.full((len(finished),), tick == 5, dtype=torch.bool),
                         torch.tensor(p[finished] / (6 * n), dtype=torch.float32)))
            for idx in finished:
                counts["renewals_p" + str(p[idx])] += 1
            counts["renewals"] += len(finished)
            segment_reward[finished] = 0
    # Direct checks consume the actual six ticks, never a second host rollout.
    focal, partner, rewards = map(np.stack, (focal_trace, partner_trace, reward_trace))
    expected_partner = np.stack([np.where(t < tau, c, 1 - c) for t in range(6)])
    checks["partner_timing_violations"] += int(np.count_nonzero(partner != expected_partner))
    checks["reward_violations"] += int(np.count_nonzero(rewards != (focal == partner)))
    checks["return_violations"] += int(np.count_nonzero(total_reward != rewards.sum(axis=0)))
    checks["episodes_checked"] += n
    counts["episodes"] += n
    return tuple(torch.cat([row[k] for row in rows]) for k in range(7)), total_reward / 6


def evaluate(model, update, counts, actions, checks):
    context = np.array(CONTEXTS, dtype=np.int64)
    _, returns = rollout(model, context, 0, None, actions, counts, checks)
    return {"update": update, "mean_return": float(returns.mean()),
            "contexts": [{"p": int(p), "tau": int(tau), "c": int(c), "return": float(r)}
                         for (p, tau, c), r in zip(context, returns)],
            "by_period": {str(p): float(returns[context[:, 0] == p].mean()) for p in (2, 6)},
            "by_partner": {str(tau): float(returns[context[:, 1] == tau].mean()) for tau in (2, 4)}}


def action_rows(counter):
    return [{"p": p, "tau": tau, "c": c, "tick": t, "action": a, "count": count}
            for p, tau, c in CONTEXTS for t in range(0, 6, p) for a in (0, 1)
            for count in (counter[(p, tau, c, t, a)],)]


def run(arm, seed, out, launch):
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    started = time.perf_counter()
    summary = {"object": "VSPC1-K4-FACTOR-VALUE-B01", "arm": arm, "seed": seed,
               "launch": launch, "device": "cpu", "dtype": "float32", "compute_threads": 1,
               "batch_episodes": 32, "status": "incomplete", "curve": [],
               "primary_dependency_defects": [], "optimizer_steps": 0}
    train_counts, eval_counts = Counter(), Counter()
    train_actions, eval_actions, context_counts = Counter(), Counter(), Counter()
    checks = Counter({name: 0 for name in ("held_action_violations", "partner_timing_violations",
                     "reward_violations", "return_violations", "terminal_bootstrap_violations",
                     "loss_weight_violations", "episodes_checked")})
    times = {"rollout_wall_seconds": 0.0, "update_wall_seconds": 0.0, "evaluation_wall_seconds": 0.0}
    model = Value(arm, seed)
    theta0 = torch.cat([v.detach().flatten().clone() for v in model.parameters()])
    summary["parameter_count"] = theta0.numel()
    summary["theta0_norm"] = float(theta0.norm())
    summary["streams"] = {"numpy": {name: [seed, STREAM_TAGS[name]] for name in ("context", "exploration")},
                          "torch": {name: seed * 1000 + tag for name, tag in STREAM_TAGS.items()
                                    if name.startswith(arm)},
                          "evaluation": "greedy deterministic; no random draws or training stream consumption"}
    context_rng = np.random.default_rng(np.random.SeedSequence([seed, STREAM_TAGS["context"]]))
    exploration_rng = np.random.default_rng(np.random.SeedSequence([seed, STREAM_TAGS["exploration"]]))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, betas=(0.9, 0.999), eps=1e-8, weight_decay=0)
    summary["initialization_wall_seconds"] = time.perf_counter() - started

    def snapshot():
        summary.update(training_counts=dict(train_counts), evaluation_counts=dict(eval_counts),
                       training_action_counts=action_rows(train_actions), evaluation_action_counts=action_rows(eval_actions),
                       training_context_counts=[{"p": p, "tau": tau, "c": c, "episodes": n}
                                                for (p, tau, c), n in sorted(context_counts.items())],
                       checks=dict(checks), measured_phase_cost=dict(times))
        write_read(out / "summary.json", summary)

    try:
        for update in range(129):
            if update in CHECKPOINTS:
                before = time.perf_counter()
                summary["curve"].append(evaluate(model, update, eval_counts, eval_actions, checks))
                times["evaluation_wall_seconds"] += time.perf_counter() - before
                snapshot()
            if update == 128:
                break
            before = time.perf_counter()
            context = np.repeat(np.array(CONTEXTS, dtype=np.int64), 4, axis=0)
            context = context[context_rng.permutation(32)]
            # Fixed [episode, primitive tick, explore/action] draw slots on every cycle.
            # Held steps still own slots, so action choices cannot shift another draw.
            draws = exploration_rng.random((32, 6, 2))
            batch, _ = rollout(model, context, 1 - 0.9 * update / 127, draws,
                               train_actions, train_counts, checks)
            context_counts.update(map(tuple, context.tolist()))
            times["rollout_wall_seconds"] += time.perf_counter() - before
            before = time.perf_counter()
            s, action, period, reward, next_s, done, weight = batch
            with torch.no_grad():
                continuation = torch.zeros_like(reward)
                continuation[~done] = model.both(next_s[~done], period[~done]).max(dim=1).values
                target = reward + continuation
                checks["terminal_bootstrap_violations"] += int(torch.count_nonzero(continuation[done]))
            checks["loss_weight_violations"] += int(not torch.allclose(
                torch.stack([weight[period == p].sum() for p in (0, 1)]), torch.tensor([0.5, 0.5]),
                atol=1e-6, rtol=1e-6))
            loss = ((model(s, action, period) - target).square() * weight).sum()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5)
            optimizer.step()
            summary["optimizer_steps"] += 1
            times["update_wall_seconds"] += time.perf_counter() - before
        theta = torch.cat([v.detach().flatten() for v in model.parameters()])
        movement = float((theta - theta0).norm())
        summary.update(theta_displacement_norm=movement,
                       theta128_norm=float(theta.norm()),
                       displacement_to_initial_norm=movement / summary["theta0_norm"],
                       metrics=curve_metrics(summary["curve"]))
        summary["primary_dependency_defects"] = [k for k, v in checks.items() if k.endswith("violations") and v]
        expected = {"episodes": 4096, "joint_steps": 24576, "renewals": 8192,
                    "legal_decisions": 8192, "renewals_p2": 6144, "renewals_p6": 2048}
        if dict(train_counts) != expected or summary["optimizer_steps"] != 128:
            summary["primary_dependency_defects"].append("training exposure differs from card")
        if eval_counts != Counter(episodes=72, joint_steps=432, renewals=144,
                                  legal_decisions=144, renewals_p2=108, renewals_p6=36):
            summary["primary_dependency_defects"].append("evaluation exposure differs from card")
        if summary["parameter_count"] != (188 if arm == "FACTOR" else 191):
            summary["primary_dependency_defects"].append("parameter count differs from card")
        summary["status"] = "complete" if not summary["primary_dependency_defects"] else "dependent_claim_incomplete"
    except Exception as exc:
        summary["primary_dependency_defects"].append(type(exc).__name__ + ": " + str(exc))
        snapshot()
        raise
    snapshot()
    summary["cost_law"] = {
        "work": "init + rollout(24576 joint ticks,8192 renewals) + 128 updates(64 rows) + eval(432 joint ticks) + checks/publication",
        "measured_rollout_seconds_per_cycle": times["rollout_wall_seconds"] / 128,
        "measured_update_seconds_per_step": times["update_wall_seconds"] / summary["optimizer_steps"],
        "measured_evaluation_seconds_per_checkpoint": times["evaluation_wall_seconds"] / 9,
        "scope": "actual fixed batch32/H6; not an extrapolation to other shapes; rollout includes trajectory checks",
    }
    return summary
