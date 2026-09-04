"""B02 sampling and learning; the inherited numerical primitives stay unchanged."""

from time import perf_counter

import numpy as np
import torch

from ..config import ENTROPY_COEFFICIENT, GRAD_CLIP, LOADS, ORDERED_PAIRS, TRAIN_SIZES, demand
from ..decoder import decode
from ..environment import canonical_roles, canonicalize_task_values, reward
from ..oracle import canonical_oracle
from ..rng import generator, tapes_for_decisions


TRAIN_PHASE = "mgtap_b02_training"
EVAL_PHASE = "mgtap_b02_evaluation"


def make_group(n, demand_rows, epochs, tapes):
    demands = np.asarray(demand_rows, dtype=np.int16)
    demands = canonicalize_task_values(
        np.take_along_axis(demands, tapes["task_permutations"], axis=1),
        tapes["task_permutations"],
    )
    roles = np.broadcast_to(canonical_roles(n), (len(demands), n))
    return {
        "features": np.column_stack((np.ones(len(demands)), demands / float(n), np.asarray(epochs) - 1.0)),
        "demands": demands,
        "roles": np.take_along_axis(roles, tapes["row_permutations"], axis=1),
        "priorities": np.take_along_axis(tapes["priority_ranks"], tapes["row_permutations"], axis=1),
        "uniforms": tapes["action_uniforms"],
    }


def training_group(seed, update, n):
    episodes = [(nn, pair, load) for nn in TRAIN_SIZES for pair in ORDERED_PAIRS for load in LOADS]
    order = generator(f"{TRAIN_PHASE}_episode_order", seed, update).permutation(len(episodes))
    selected = [episodes[i] for i in order if episodes[i][0] == n]
    rows = [(pair, load, epoch) for _, pair, load in selected for epoch in (1, 2)]
    tapes = tapes_for_decisions(TRAIN_PHASE, seed, (update, n), len(rows), n,
                                include_training_presentations=True)
    group = make_group(n, [demand(n, pair, load, epoch) for pair, load, epoch in rows],
                       [epoch for _, _, epoch in rows], tapes)
    group["pairs"] = np.asarray([pair for pair, _, _ in rows], dtype=np.int8)
    group["loads"] = np.asarray([LOADS.index(load) for _, load, _ in rows], dtype=np.int8)
    group["epochs"] = np.asarray([epoch for _, _, epoch in rows], dtype=np.int8)
    return group


def decode_group(actor, group):
    _, mapped, idle = actor.scores(torch.as_tensor(group["features"], dtype=torch.float64))
    decoded = decode(mapped, idle, torch.as_tensor(group["roles"], dtype=torch.long),
                     torch.as_tensor(group["demands"], dtype=torch.long),
                     torch.as_tensor(group["priorities"], dtype=torch.long),
                     torch.as_tensor(group["uniforms"], dtype=torch.float64))
    rewards = reward(group["roles"], decoded.actions.detach().numpy(), decoded.residual.detach().numpy())
    return decoded, torch.as_tensor(rewards, dtype=torch.float64)


def training_loss(actor, groups):
    loss = torch.zeros((), dtype=torch.float64)
    for n in TRAIN_SIZES:
        decoded, rewards = decode_group(actor, groups[n])
        loss = loss + torch.sum(-0.5 * (rewards / n) * decoded.log_probability
                                - 0.5 * ENTROPY_COEFFICIENT * decoded.mean_entropy)
    return loss / 48.0


def training_step(actor, optimizer, seed, update):
    before = actor.parameter_vector()
    groups = {n: training_group(seed, update, n) for n in TRAIN_SIZES}
    optimizer.zero_grad(set_to_none=True)
    loss = training_loss(actor, groups)
    loss.backward()
    grad_norm = float(torch.nn.utils.clip_grad_norm_(actor.parameters(), GRAD_CLIP))
    optimizer.step()
    after = actor.parameter_vector()
    return {
        "update": update, "loss": float(loss.detach()), "preclip_gradient_norm": grad_norm,
        "step_displacement_l2": float(np.linalg.norm(after - before)),
        "distance_from_zero_l2": float(np.linalg.norm(after)),
        "training_decisions": sum(len(g["roles"]) for g in groups.values()),
        "training_agent_steps": sum(g["roles"].size for g in groups.values()),
    }


def evaluation_groups(seed, tapes_per_episode):
    """Rows are pair, load, epoch, tape; no arm or checkpoint in an address."""
    groups = {}
    for n in TRAIN_SIZES:
        pieces = []
        for pi, pair in enumerate(ORDERED_PAIRS):
            for li, load in enumerate(LOADS):
                for epoch in (1, 2):
                    tapes = tapes_for_decisions(EVAL_PHASE, seed, (n, pi, li, epoch), tapes_per_episode, n)
                    pieces.append(make_group(n, [demand(n, pair, load, epoch)] * tapes_per_episode,
                                             [epoch] * tapes_per_episode, tapes))
        groups[n] = {key: np.concatenate([piece[key] for piece in pieces]) for key in pieces[0]}
    return groups


def evaluate(actor, groups, tapes_per_episode):
    """Return normalized episodes indexed N, pair, load, tape."""
    returns = []
    with torch.no_grad():
        for n in TRAIN_SIZES:
            _, rewards = decode_group(actor, groups[n])
            epochs = rewards.numpy().reshape(len(ORDERED_PAIRS), len(LOADS), 2, tapes_per_episode)
            returns.append(epochs.sum(axis=2) / (2.0 * n))
    return np.stack(returns)


def oracle_population(deadline):
    """Compute each immediate demand once, with no oracle data in policy groups."""
    cache = {}
    returns = np.empty((len(TRAIN_SIZES), len(ORDERED_PAIRS), len(LOADS)), dtype=np.float64)
    for ni, n in enumerate(TRAIN_SIZES):
        for pi, pair in enumerate(ORDERED_PAIRS):
            for li, load in enumerate(LOADS):
                values = []
                for epoch in (1, 2):
                    if perf_counter() >= deadline:
                        raise TimeoutError("B02 shared setup exceeded 60 seconds")
                    demands = demand(n, pair, load, epoch)
                    key = (n, demands)
                    if key not in cache:
                        cache[key] = canonical_oracle(n, demands)["reward"]
                    values.append(cache[key])
                returns[ni, pi, li] = sum(values) / (2.0 * n)
    return returns
