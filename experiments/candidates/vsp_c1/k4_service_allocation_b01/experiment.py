"""Service allocation B01: three queues, held control, actual-segment Double Q.

Adapted from the accepted reactive-B01 path without changing that historical source.
"""
from copy import deepcopy
from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

PERIODS = (2, 6)
HORIZON = 48
ACTIONS = 3
NAMESPACES = {"init_FACTOR": 11, "init_GENERIC": 12, "train_arrivals": 21,
              "train_h": 22, "explore_coin": 23, "explore_action": 24,
              "eval_arrivals": 31, "eval_h": 32}


@dataclass(frozen=True)
class Budget:
    seed: int = 402
    updates: int = 256
    train_per_period: int = 8
    eval_per_period: int = 128
    checkpoints: tuple = (0, 64, 128, 192, 256)


def rng(seed, namespace, period=0, update=0):
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(
        [seed, NAMESPACES[namespace], period, update])))


def tapes(seed, period, episodes, update=0, evaluation=False):
    prefix = "eval" if evaluation else "train"
    # Arrays are assigned before policy branching, by episode and primitive tick.
    return {
        "arrivals": rng(seed, prefix + "_arrivals", period, update).random(
            (episodes, HORIZON, ACTIONS)) < 0.5,
        "h": rng(seed, prefix + "_h", period, update).integers(0, ACTIONS, episodes),
        "coin": None if evaluation else rng(seed, "explore_coin", period, update).random(
            (episodes, HORIZON)),
        "action": None if evaluation else rng(seed, "explore_action", period, update).integers(
            0, ACTIONS, (episodes, HORIZON)),
    }


def partner_action(queues, old_h):
    order = (old_h[:, None] + np.array([1, 2, 0])) % ACTIONS
    in_tie_order = np.take_along_axis(queues, order, axis=1)
    return order[np.arange(len(queues)), in_tie_order.argmax(axis=1)]


def lq_exclude(queues, old_h):
    """Renewal-only rule; exclusion applies to this rule, never to learner actions."""
    partner = partner_action(queues, old_h)
    available = np.where(np.arange(ACTIONS)[None, :] == partner[:, None], -1, queues)
    return available.argmax(axis=1)  # Remaining queue ties use the smallest index.


def tick(queues, old_h, held_action, arrivals):
    partner = partner_action(queues, old_h)
    selected = (np.arange(ACTIONS)[None, :] == held_action[:, None]) | (
        np.arange(ACTIONS)[None, :] == partner[:, None])
    service = selected & (queues > 0)
    before_clip = queues - service + arrivals
    overflow = np.maximum(before_clip - 4, 0).sum(axis=1)
    return np.minimum(before_clip, 4), held_action.copy(), service.sum(axis=1), overflow, partner


def states(queues, h, t):
    return torch.tensor(np.column_stack((queues, h, np.full(len(h), t))), dtype=torch.float32)


def features(state, action):
    # Stored q0,q1,q2,h,t -> normalized queues,time,h one-hot,action one-hot.
    return torch.cat((state[:, :3] / 4, state[:, 4:5] / 48,
                      nn.functional.one_hot(state[:, 3].long(), ACTIONS).float(),
                      nn.functional.one_hot(action.long(), ACTIONS).float()), dim=1)


class QNetwork(nn.Module):
    def __init__(self, arm, seed):
        super().__init__()
        self.arm = arm
        init_seed = int(np.random.SeedSequence(
            [seed, NAMESPACES["init_" + arm], 0, 0]).generate_state(1, dtype=np.uint64)[0])
        # Preserve prior hidden/output construction, then explicit dense/embedding init order.
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(init_seed)
            self.hidden = nn.Linear(10 if arm == "FACTOR" else 12, 24 if arm == "FACTOR" else 28)
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

    def all_actions(self, state, period):
        n = len(state)
        return self(state.repeat_interleave(ACTIONS, dim=0), torch.arange(ACTIONS).repeat(n),
                    period.repeat_interleave(ACTIONS)).reshape(n, ACTIONS)


@torch.no_grad()
def collect(model, period, tape, epsilon):
    """Fresh endogenous state every call. model=None evaluates only LQ-EXCLUDE."""
    n = len(tape["h"])
    queues = np.full((n, ACTIONS), 2, dtype=np.int64)
    h = tape["h"].copy()
    totals = np.zeros(n, dtype=np.int64)
    overflows = np.zeros(n, dtype=np.int64)
    rows = {key: [] for key in ("state", "action", "reward", "next_state", "terminal")}
    for t in range(0, HORIZON, period):
        state = states(queues, h, t)
        if model is None:
            action = lq_exclude(queues, h)
        else:
            # All three actions are scored, even when exploration is taken.
            action = model.all_actions(state, torch.full((n,), period)).argmax(1).numpy()
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
    state, period = batch["next_state"][live], batch["period"][live]
    if len(state):
        action = online.all_actions(state, period).argmax(1)
        y[live] += target(state, action, period)
    return y


def update(online, target, optimizer, batches):
    losses = []
    for batch in batches:
        error = online(batch["state"], batch["action"], batch["period"]) - targets(online, target, batch)
        losses.append(error.square().reshape(batch["episodes"], -1).mean(1).mean())
    loss = torch.stack(losses).mean()  # Equal episode counts in the two period groups.
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
    live = train_rows - train_episodes
    return {"training_episodes": train_episodes, "training_joint_ticks": train_episodes * HORIZON,
            "training_renewal_rows": train_rows, "nonterminal_rows": live,
            "optimizer_steps": budget.updates, "evaluation_episodes": eval_episodes,
            "evaluation_joint_ticks": eval_episodes * HORIZON, "evaluation_decisions": eval_rows,
            "all_joint_ticks": (train_episodes + eval_episodes) * HORIZON,
            "behavior_Q_predictions": ACTIONS * train_rows,
            "online_bootstrap_Q_predictions": ACTIONS * live, "target_bootstrap_Q_predictions": live,
            "loss_Q_predictions": train_rows, "evaluation_Q_predictions": ACTIONS * eval_rows,
            "scalar_Q_predictions": (ACTIONS + 1) * (train_rows + live) + ACTIONS * eval_rows,
            "target_copies": 1 + budget.updates // 16, "model_selection_steps": 0}


def rule_counts(budget):
    return {"trained_models": 0, "trainable_parameters": 0, "optimizer_steps": 0,
            "evaluation_episodes": 2 * budget.eval_per_period,
            "evaluation_joint_ticks": 2 * budget.eval_per_period * HORIZON,
            "evaluation_decisions": budget.eval_per_period * sum(HORIZON // d for d in PERIODS),
            "nested_search_calls": 0}


def configuration(model, budget):
    return {"object": "VSPC1-K4-SERVICE-ALLOCATION-B01", "arm": model.arm, "seed": budget.seed,
            "online_parameters": sum(p.numel() for p in model.parameters()),
            "dtype": "float32", "device": "cpu", "compute_threads": 1,
            "training_batch_episodes": 2 * budget.train_per_period, "budget": vars(budget),
            "counts": counts(budget), "rule_counts_in_GENERIC": rule_counts(budget),
            "rng_namespaces": NAMESPACES,
            "rng_mapping": "PCG64(SeedSequence([seed,namespace,period,update])); evaluation update=0; episode/tick/queue slots. Initialization: first uint64 SeedSequence word with period=update=0 as Torch seed; hidden/output construction then dense init then embedding init.",
            "can_move": "Trainable online parameters; 256 actual-segment detached Double-Q Adam steps at lr=0.01, clip=5 in the selected budget. Actual initial norm/final movement measured in the selected call.",
            "cost_law": "Per learner: initialization + U*(2*N_train*48 host ticks + three-action scoring on N_train*(24+8) rows + three online/one target scores on N_train*(23+7) live rows + loss/one Adam step) + C*2*N_eval*48 evaluation ticks + publication/exit. GENERIC adds one 2*N_eval*48 rule evaluation and paired publication. Unit times unknown for this host."}


def evaluation_result(consequences):
    means = {d: float(np.mean(values["J"])) for d, values in consequences.items()}
    return {"period_means": means, "mean_J": float(np.mean(list(means.values()))),
            "consequence_means": {d: {k: float(np.mean(v)) for k, v in values.items()}
                                  for d, values in consequences.items()}}


def endpoint_episodes(consequences):
    return {d: [{"episode": i, **{k: v[i] for k, v in values.items()}}
                for i in range(len(values["J"]))] for d, values in consequences.items()}


def evaluate_rule(budget):
    # Reconstruct only exogenous evaluation tapes; collect starts the rule's own queues/h.
    consequences = {str(d): collect(None, d, tapes(budget.seed, d, budget.eval_per_period,
                                                evaluation=True), 0)[1] for d in PERIODS}
    observed = {"trained_models": 0, "trainable_parameters": 0, "optimizer_steps": 0,
                "evaluation_episodes": sum(len(v["J"]) for v in consequences.values()),
                "evaluation_joint_ticks": sum(len(v["J"]) * HORIZON for v in consequences.values()),
                "evaluation_decisions": sum(len(v["J"]) * (HORIZON // int(d)) for d, v in consequences.items()),
                "nested_search_calls": 0}
    return {"arm": "LQ-EXCLUDE", "seed": budget.seed, "status": "complete",
            "counts": rule_counts(budget), "observed_counts": observed,
            **evaluation_result(consequences), "endpoint_episodes": endpoint_episodes(consequences)}


def run(arm, budget, publish):
    """One learner only. The runner adds rule/paired publication within the GENERIC call."""
    torch.set_num_threads(1)
    online = QNetwork(arm, budget.seed)
    initial = parameters(online).clone()
    target = deepcopy(online).requires_grad_(False)
    optimizer = torch.optim.Adam(online.parameters(), lr=0.01, betas=(0.9, 0.999), eps=1e-8,
                                 weight_decay=0)
    evaluation = {d: tapes(budget.seed, d, budget.eval_per_period, evaluation=True) for d in PERIODS}
    summary = configuration(online, budget)
    summary.update(status="running", completed_updates=0, curve=[], td_losses=[],
                   target_copy_updates=[0], initial_parameter_norm=float(initial.norm()),
                   final_parameter_displacement=None, observed_counts={key: 0 for key in counts(budget)})
    summary["observed_counts"]["target_copies"] = 1

    def evaluate(u):
        consequences = {str(d): collect(online, d, evaluation[d], 0)[1] for d in PERIODS}
        summary["curve"].append({"update": u, **evaluation_result(consequences)})
        if u == budget.updates:
            summary["endpoint_episodes"] = endpoint_episodes(consequences)
        observed = summary["observed_counts"]
        episodes = sum(len(v["J"]) for v in consequences.values())
        decisions = budget.eval_per_period * sum(HORIZON // d for d in PERIODS)
        observed["evaluation_episodes"] += episodes
        observed["evaluation_joint_ticks"] += episodes * HORIZON
        observed["all_joint_ticks"] += episodes * HORIZON
        observed["evaluation_decisions"] += decisions
        observed["evaluation_Q_predictions"] += ACTIONS * decisions
        observed["scalar_Q_predictions"] += ACTIONS * decisions
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
        observed["training_joint_ticks"] += episodes * HORIZON
        observed["all_joint_ticks"] += episodes * HORIZON
        observed["training_renewal_rows"] += rows
        observed["nonterminal_rows"] += live
        observed["optimizer_steps"] += 1
        observed["behavior_Q_predictions"] += ACTIONS * rows
        observed["online_bootstrap_Q_predictions"] += ACTIONS * live
        observed["target_bootstrap_Q_predictions"] += live
        observed["loss_Q_predictions"] += rows
        observed["scalar_Q_predictions"] += (ACTIONS + 1) * (rows + live)
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
