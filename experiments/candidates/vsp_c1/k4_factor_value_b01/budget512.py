"""B02 512-update loop. Host, models and update copied from experiment.run; not refactored there."""
from collections import Counter
import time

import numpy as np
import torch
from torch import nn

from .experiment import CONTEXTS, STREAM_TAGS, Value, action_rows, evaluate, rollout
from .reporting import budget512_metrics, write_read

CHECKPOINTS = tuple(range(0, 513, 16))


def epsilon_at(update):
    """Zero-based cycle index; B01 formula through update 127, then 0.1."""
    if update < 128:
        return 1 - 0.9 * update / 127
    return 0.1


def run(arm, seed, out, launch):
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    started = time.perf_counter()
    summary = {"object": "VSPC1-K4-FACTOR-VALUE-B02-BUDGET512", "arm": arm, "seed": seed,
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
        for update in range(513):
            if update in CHECKPOINTS:
                before = time.perf_counter()
                summary["curve"].append(evaluate(model, update, eval_counts, eval_actions, checks))
                times["evaluation_wall_seconds"] += time.perf_counter() - before
                if update == 128:
                    theta128 = torch.cat([v.detach().flatten().clone() for v in model.parameters()])
                    summary["theta128_norm"] = float(theta128.norm())
                    summary["theta0_to_128_displacement_norm"] = float((theta128 - theta0).norm())
                snapshot()
            if update == 512:
                break
            before = time.perf_counter()
            context = np.repeat(np.array(CONTEXTS, dtype=np.int64), 4, axis=0)
            context = context[context_rng.permutation(32)]
            # Fixed [episode, primitive tick, explore/action] draw slots on every cycle.
            # Held steps still own slots, so action choices cannot shift another draw.
            draws = exploration_rng.random((32, 6, 2))
            batch, _ = rollout(model, context, epsilon_at(update), draws,
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
        theta512 = torch.cat([v.detach().flatten() for v in model.parameters()])
        movement = float((theta512 - theta0).norm())
        summary.update(theta512_norm=float(theta512.norm()),
                       theta0_to_512_displacement_norm=movement,
                       theta128_to_512_displacement_norm=float((theta512 - theta128).norm()),
                       displacement_to_initial_norm=movement / summary["theta0_norm"],
                       metrics=budget512_metrics(summary["curve"]))
        summary["primary_dependency_defects"] = [k for k, v in checks.items() if k.endswith("violations") and v]
        expected = {"episodes": 16384, "joint_steps": 98304, "renewals": 32768,
                    "legal_decisions": 32768, "renewals_p2": 24576, "renewals_p6": 8192}
        if dict(train_counts) != expected or summary["optimizer_steps"] != 512:
            summary["primary_dependency_defects"].append("training exposure differs from card")
        if eval_counts != Counter(episodes=264, joint_steps=1584, renewals=528,
                                  legal_decisions=528, renewals_p2=396, renewals_p6=132):
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
        "work": "init + rollout(98304 joint ticks,32768 renewals) + 512 updates(64 rows) + eval(1584 joint ticks) + checks/publication",
        "measured_rollout_seconds_per_cycle": times["rollout_wall_seconds"] / 512,
        "measured_update_seconds_per_step": times["update_wall_seconds"] / summary["optimizer_steps"],
        "measured_evaluation_seconds_per_checkpoint": times["evaluation_wall_seconds"] / 33,
        "scope": "actual fixed batch32/H6; not an extrapolation to other shapes; rollout includes trajectory checks",
    }
    return summary
