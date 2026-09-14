"""Two fresh MAPR learners differing only in retrospective native reward timing."""

import math
from time import perf_counter

import torch

from ...variable_n_fleet_churn_n7_direct_b01 import learning as original
from ...variable_n_fleet_churn_bpcr_r09.numeric import canonical_stiefel
from ...variable_n_fleet_churn_bpcr_r09.training import gae_terminal

ARMS = ("INTERVAL", "TERMINAL")
rng = original.rng
worlds = original.worlds
parameter_state = original.parameter_state


def initialize(seed, namespace):
    source = rng(seed, namespace, "initialization")
    parameters = {}
    for name, shape in original.mapr_parameter_shapes().items():
        if name == "null.embedding" or len(shape) == 1:
            parameters[name] = torch.zeros(shape, dtype=torch.float64)
            continue
        domain = "model-initialization/base"
        builder = lambda draw, name=name: original.coordinate(namespace, domain, name, draw=draw)
        normal = source.normal_array(original._normal_source_shape(shape), builder, now=None)
        gain = 1.0 if name == "token.embedding" else (0.01 if name.endswith("out.weight") else math.sqrt(2.0))
        parameters[name] = torch.from_numpy((canonical_stiefel(normal, shape) * gain).copy())
    models = {arm: original.MAPR(parameters) for arm in ARMS}
    # The model constructor clones the supplied tensors; no shared trainable storage.
    return models, {arm: original.make_optimizer(model) for arm, model in models.items()}


def interval_rewards(episodes):
    counters = torch.tensor([row["service_counters"] for row in episodes], dtype=torch.float64)
    if tuple(counters.shape[1:]) != (7, 4) or bool((counters[:, 0] != 0).any()):
        raise AssertionError("service counters require seven snapshots with a zero post-loss start")
    if bool((counters[:, -1, (1, 3)] <= 0).any()) or bool((counters[:, 1:] < counters[:, :-1]).any()):
        raise AssertionError("service demands must end positive and cumulative counters cannot decrease")
    if not torch.equal(counters[:, 3:, :2], counters[:, 3:4, :2].expand(-1, 4, -1)):
        raise AssertionError("failed-zone delivered/demand counters did not freeze at60s")
    endpoints = torch.tensor([row["fail_endpoint"] + row["total_endpoint"] for row in episodes], dtype=torch.float64)
    if not torch.equal(counters[:, -1], endpoints):
        raise AssertionError("credit counters and published native terminal endpoints differ")
    increments = counters[:, 1:] - counters[:, :-1]
    rewards = .5 * increments[:, :, 0] / counters[:, -1, 1, None]
    rewards += .5 * increments[:, :, 2] / counters[:, -1, 3, None]
    objectives = torch.tensor([row["J_ext"] for row in episodes], dtype=torch.float64)
    if not torch.allclose(rewards.sum(1), objectives, atol=1e-9, rtol=0):
        raise AssertionError("interval rewards do not sum to the complete native objective")
    return rewards


def gae_interval(values, rewards):
    stopped, rewards = values.detach(), rewards.detach()
    advantages = torch.empty_like(stopped)
    next_value = torch.zeros_like(stopped[:, 0])
    next_advantage = torch.zeros_like(next_value)
    for index in range(5, -1, -1):
        delta = rewards[:, index] + next_value - stopped[:, index]
        next_advantage = delta if index == 5 else delta + .95 * next_advantage
        advantages[:, index] = next_advantage
        next_value = stopped[:, index]
    return advantages.detach(), (advantages + stopped).detach()


def rollout(library, fixtures, model, arm, namespace, action_source, round_index, training,
            check_presentation=False):
    return original.rollout(library, fixtures, model, arm, namespace, action_source,
                            round_index, training, check_presentation=check_presentation,
                            collect_service=True)


def update(model, optimizer, rollout_data, seed, namespace, arm, round_index):
    started = perf_counter()
    rewards = interval_rewards(rollout_data["episodes"])
    values = torch.stack([row["old_value"] for row in rollout_data["records"]]).reshape(-1, 6)
    objectives = torch.tensor([row["J_ext"] for row in rollout_data["episodes"]], dtype=torch.float64)
    # Both arms check their own counters; TERMINAL still uses the unchanged real recursion.
    targets = gae_interval(values, rewards) if arm == "INTERVAL" else gae_terminal(values, objectives)
    result = original.update(model, optimizer, rollout_data, seed, namespace, arm, round_index, targets=targets)
    result["credit"] = dict(label=arm, checked_episodes=len(objectives),
                          max_return_difference=float((rewards.sum(1) - objectives).abs().max()),
                          interval_reward_means=rewards.mean(0).tolist(),
                          critic_target_mean=float(targets[1].mean()))
    result["seconds"] = perf_counter() - started
    return result
