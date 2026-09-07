"""Frozen reactive queues B01: renewal-only control and actual-segment Double Q."""
from copy import deepcopy
from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

PERIODS = (2, 6)
HORIZON = 48
NAMESPACES = {"init_FACTOR": 11, "init_GENERIC": 12, "train_arrivals": 21,
              "train_h": 22, "explore_coin": 23, "explore_action": 24,
              "eval_arrivals": 31, "eval_h": 32}


@dataclass(frozen=True)
class Budget:
    seed: int = 401
    updates: int = 256
    train_per_period: int = 8
    eval_per_period: int = 128
    checkpoints: tuple = tuple(range(0, 257, 32))


def rng(seed, namespace, period=0, update=0):
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(
        [seed, NAMESPACES[namespace], period, update])))


def tapes(seed, period, episodes, update=0, evaluation=False):
    prefix = "eval" if evaluation else "train"
    # All arrays are assigned by episode and primitive tick, never policy draw order.
    return {
        "arrivals": rng(seed, prefix + "_arrivals", period, update).random(
            (episodes, HORIZON, 2)) < 0.7,
        "h": rng(seed, prefix + "_h", period, update).integers(0, 2, episodes),
        "coin": None if evaluation else rng(seed, "explore_coin", period, update).random(
            (episodes, HORIZON)),
        "action": None if evaluation else rng(seed, "explore_action", period, update).integers(
            0, 2, (episodes, HORIZON)),
    }


def tick(queues, old_h, held_action, arrivals):
    """Simultaneous service, then arrivals/clipping, then focal h update."""
    partner = np.where(queues[:, 0] == queues[:, 1], 1 - old_h,
                       (queues[:, 1] > queues[:, 0]).astype(np.int64))
    selected = (np.arange(2)[None, :] == held_action[:, None]) | (
        np.arange(2)[None, :] == partner[:, None])
    service = selected & (queues > 0)
    before_clip = queues - service + arrivals
    overflow = np.maximum(before_clip - 4, 0).sum(axis=1)
    return np.minimum(before_clip, 4), held_action.copy(), service.sum(axis=1), overflow, partner


def states(queues, h, t):
    return torch.tensor(np.column_stack((queues, h, np.full(len(h), t))), dtype=torch.float32)


def features(state, action):
    # Stored state order q0,q1,h,t; feature order is the card's seven coordinates.
    return torch.cat((state[:, :2] / 4, state[:, 3:4] / 48,
                      nn.functional.one_hot(state[:, 2].long(), 2).float(),
                      nn.functional.one_hot(action.long(), 2).float()), dim=1)


class QNetwork(nn.Module):
    def __init__(self, arm, seed):
        super().__init__()
        self.arm = arm
        init_seed = int(np.random.SeedSequence(
            [seed, NAMESPACES["init_" + arm], 0, 0]).generate_state(1, dtype=np.uint64)[0])
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(init_seed)
            self.hidden = nn.Linear(7 if arm == "FACTOR" else 9, 24 if arm == "FACTOR" else 28)
            self.output = nn.Linear(24 if arm == "FACTOR" else 28, 4 if arm == "FACTOR" else 1)
            if arm == "FACTOR":
                self.duration = nn.Parameter(torch.empty(2, 4))
            for layer in (self.hidden, self.output):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.zeros_(layer.bias)
            if arm == "FACTOR":
                nn.init.normal_(self.duration, mean=0, std=0.5)
        self.float()

    def forward(self, state, action, period):
        x = features(state, action)
        index = (period == 6).long()
        if self.arm == "GENERIC":
            x = torch.cat((x, nn.functional.one_hot(index, 2).float()), dim=1)
        value = self.output(torch.tanh(self.hidden(x)))
        return (value * self.duration[index]).sum(1) if self.arm == "FACTOR" else value[:, 0]

    def both(self, state, period):
        n = len(state)
        return self(state.repeat_interleave(2, dim=0), torch.arange(2).repeat(n),
                    period.repeat_interleave(2)).reshape(n, 2)


@torch.no_grad()
def collect(model, period, tape, epsilon):
    n = len(tape["h"])
    queues = np.full((n, 2), 2, dtype=np.int64)
    h = tape["h"].copy()
    totals = np.zeros(n, dtype=np.int64)
    overflows = np.zeros(n, dtype=np.int64)
    rows = {key: [] for key in ("state", "action", "reward", "next_state", "terminal")}
    for t in range(0, HORIZON, period):
        state = states(queues, h, t)
        # Both Qs are scored before exploration; argmax selects action zero on ties.
        action = model.both(state, torch.full((n,), period)).argmax(1).numpy()
        if tape["coin"] is not None:
            action = np.where(tape["coin"][:, t] < epsilon, tape["action"][:, t], action)
        segment = np.zeros(n, dtype=np.int64)
        for offset in range(period):
            queues, h, served, overflow, _ = tick(queues, h, action, tape["arrivals"][:, t + offset])
            segment += served
            overflows += overflow
        totals += segment
        rows["state"].append(state)
        rows["action"].append(torch.from_numpy(action.copy()))
        rows["reward"].append(torch.tensor(segment / 96, dtype=torch.float32))
        rows["next_state"].append(states(queues, h, t + period))
        rows["terminal"].append(torch.full((n,), t + period == HORIZON))
    batch = {key: torch.stack(value, dim=1).flatten(0, 1) for key, value in rows.items()}
    batch["period"] = torch.full((n * (HORIZON // period),), period)
    batch["episodes"] = n
    return batch, {"J": (totals / 96).tolist(), "overflow": overflows.tolist(),
                   "final_backlog": queues.sum(1).tolist(), "unused_service": (96 - totals).tolist()}


@torch.no_grad()
def targets(online, target, batch):
    y = batch["reward"].clone()
    live = ~batch["terminal"]
    # Terminal successors are never passed to either network.
    state, period = batch["next_state"][live], batch["period"][live]
    if len(state):
        action = online.both(state, period).argmax(1)
        y[live] += target(state, action, period)
    return y


def update(online, target, optimizer, batches):
    losses = []
    for batch in batches:
        error = online(batch["state"], batch["action"], batch["period"]) - targets(online, target, batch)
        losses.append(error.square().reshape(batch["episodes"], -1).mean(1).mean())
    # Two equal-size period groups: mean of their per-episode means.
    loss = torch.stack(losses).mean()
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(online.parameters(), 5)
    optimizer.step()
    return {str(d): float(value.detach()) for d, value in zip(PERIODS, losses)}


def parameters(model):
    return torch.cat([p.detach().flatten() for p in model.parameters()])


def counts(budget):
    train_episodes = 2 * budget.train_per_period * budget.updates
    eval_episodes = 2 * budget.eval_per_period * len(budget.checkpoints)
    train_rows = budget.train_per_period * sum(HORIZON // d for d in PERIODS) * budget.updates
    eval_rows = budget.eval_per_period * sum(HORIZON // d for d in PERIODS) * len(budget.checkpoints)
    nonterminal = train_rows - train_episodes
    return {"training_episodes": train_episodes, "training_joint_steps": train_episodes * HORIZON,
            "training_renewal_rows": train_rows, "optimizer_steps": budget.updates,
            "training_nonterminal_rows": nonterminal, "evaluation_episodes": eval_episodes,
            "evaluation_joint_steps": eval_episodes * HORIZON, "evaluation_decisions": eval_rows,
            "all_focal_decisions": train_rows + eval_rows,
            "scalar_q_predictions": 3 * train_rows + 3 * nonterminal + 2 * eval_rows,
            "target_copies": 1 + budget.updates // 16, "model_selection_steps": 0}


def configuration(arm, budget=Budget()):
    model = QNetwork(arm, budget.seed)
    return {"arm": arm, "seed": budget.seed, "online_parameters": sum(p.numel() for p in model.parameters()),
            "dtype": "float32", "device": "cpu", "compute_threads": 1,
            "training_batch_episodes": 2 * budget.train_per_period,
            "budget": vars(budget), "counts": counts(budget), "rng_namespaces": NAMESPACES,
            "rng_mapping": "PCG64(SeedSequence([root_seed, namespace_id, period, update])); evaluation update=0; arrays indexed episode,tick,queue. Initialization uses uint64 SeedSequence word as torch seed, period=update=0.",
            "can_move": "Trainable online parameters; one detached actual-segment Double-Q squared-loss Adam step per update, lr=0.01, clip=5; target unoptimized. Actual movement measured in run.",
            "cost_law": "T_init + U*(2*N_train*48 host ticks + N_train*(24+8) behavior/loss rows + N_train*(23+7) backups + one Adam step) + C*2*N_eval*48 evaluation ticks + publication/exit; unit seconds unknown before execution."}


def run(arm, budget, publish):
    """One arm; publish callback writes partial facts after each update/curve point."""
    torch.set_num_threads(1)
    online = QNetwork(arm, budget.seed)
    initial = parameters(online).clone()
    target = deepcopy(online).requires_grad_(False)
    optimizer = torch.optim.Adam(online.parameters(), lr=0.01, betas=(0.9, 0.999), eps=1e-8,
                                 weight_decay=0)
    evaluation = {d: tapes(budget.seed, d, budget.eval_per_period, evaluation=True) for d in PERIODS}
    summary = configuration(arm, budget)
    summary.update(status="running", completed_updates=0, curve=[], td_losses=[],
                   target_copy_updates=[0], initial_parameter_norm=float(initial.norm()),
                   final_parameter_displacement=None, observed_counts={key: 0 for key in counts(budget)})
    summary["observed_counts"]["target_copies"] = 1

    def evaluate(u):
        consequences = {str(d): collect(online, d, evaluation[d], 0)[1] for d in PERIODS}
        means = {d: float(np.mean(value["J"])) for d, value in consequences.items()}
        summary["curve"].append({"update": u, "period_means": means,
                                 "mean_J": float(np.mean(list(means.values()))),
                                 "consequence_means": {d: {k: float(np.mean(v)) for k, v in values.items()}
                                                       for d, values in consequences.items()}})
        if u == budget.updates:
            summary["endpoint_episodes"] = {d: [{"episode": i, **{k: v[i] for k, v in values.items()}}
                                                for i in range(budget.eval_per_period)]
                                            for d, values in consequences.items()}
        observed = summary["observed_counts"]
        observed["evaluation_episodes"] += 2 * budget.eval_per_period
        observed["evaluation_joint_steps"] += 2 * budget.eval_per_period * HORIZON
        decisions = budget.eval_per_period * sum(HORIZON // d for d in PERIODS)
        observed["evaluation_decisions"] += decisions
        observed["all_focal_decisions"] += decisions
        observed["scalar_q_predictions"] += 2 * decisions
        publish(summary)

    evaluate(0)
    for u in range(1, budget.updates + 1):
        epsilon = 1 - 0.9 * (u - 1) / 255
        batches = [collect(online, d, tapes(budget.seed, d, budget.train_per_period, u), epsilon)[0]
                   for d in PERIODS]
        period_loss = update(online, target, optimizer, batches)
        summary["td_losses"].append({"update": u, "epsilon": epsilon, "period_mse": period_loss})
        observed = summary["observed_counts"]
        episodes = sum(batch["episodes"] for batch in batches)
        rows = sum(len(batch["reward"]) for batch in batches)
        live = sum(int((~batch["terminal"]).sum()) for batch in batches)
        observed["training_episodes"] += episodes
        observed["training_joint_steps"] += episodes * HORIZON
        observed["training_renewal_rows"] += rows
        observed["training_nonterminal_rows"] += live
        observed["optimizer_steps"] += 1
        observed["all_focal_decisions"] += rows
        observed["scalar_q_predictions"] += 3 * rows + 3 * live
        if u % 16 == 0:
            target.load_state_dict(online.state_dict())
            summary["target_copy_updates"].append(u)
            observed["target_copies"] += 1
        summary["completed_updates"] = u
        if u in budget.checkpoints:
            evaluate(u)
        else:
            publish(summary)
    summary["final_parameter_displacement"] = float((parameters(online) - initial).norm())
    summary["status"] = "complete"
    publish(summary)
    return summary
