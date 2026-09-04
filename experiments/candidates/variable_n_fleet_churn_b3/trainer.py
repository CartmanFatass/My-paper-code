from __future__ import annotations

import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import torch
from torch.distributions import Normal

from .allocator import sp_rda
from .config import CHURNS, GEOMETRIES, MASSES, REGISTERED, TRAIN_SCHEDULES
from .generator import SeedBanks, World, training_row_order
from .host import evaluate_physical
from .models import SetBidActorCritic, parameter_counts
from .rng import counter_seed, generator


@dataclass
class Trial:
    agents: torch.Tensor
    tasks: torch.Tensor
    global_row: torch.Tensor
    lease_vector: torch.Tensor
    latent: torch.Tensor
    old_log_probability: torch.Tensor
    old_value: torch.Tensor
    reward: torch.Tensor


def _collect_trial(model: SetBidActorCritic, world: World, update: int, action_replica: int) -> tuple[Trial, dict, int]:
    start_ns = time.perf_counter_ns()
    order = training_row_order(world, action_replica)
    handles, agents_np, tasks_np, global_np = world.observation(order)
    agents, tasks, global_row = map(torch.from_numpy, (agents_np, tasks_np, global_np))
    leases = torch.zeros(world.n, dtype=agents.dtype)
    with torch.no_grad():
        output = model(agents, tasks, global_row, lease_vector=leases)
        torch_rng = torch.Generator(device="cpu")
        torch_rng.manual_seed(counter_seed(
            "G-RELEASE", "action", world.seed, update, world.schedule_index,
            world.raw_index, world.mass, world.geometry, world.churn, action_replica,
        ))
        latent, old_logp, _ = model.sample_release_latent(output, REGISTERED.bid_sigma, torch_rng)
        bids = torch.tanh(latent).cpu().numpy()
    capacities = world.capacities[order]
    assignment, counters = sp_rda(handles, capacities, world.demand, bids, world.tie_ranks)
    outcome = evaluate_physical(handles, capacities, world.demand, world.previous_roles, assignment)
    return Trial(
        agents, tasks, global_row, leases, latent.detach(), old_logp.detach(), output.value.detach(),
        torch.tensor(outcome.J, dtype=torch.float32),
    ), counters, time.perf_counter_ns() - start_ns


def _atomic_checkpoint(model: SetBidActorCritic, path: Path, metadata: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    try:
        torch.save({"model": model.state_dict(), "metadata": metadata}, temporary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def train_seed(
    seed: int, banks: SeedBanks, checkpoint_path: Path,
    on_first_optimizer_step: Callable[[dict], None] | None = None,
) -> tuple[SetBidActorCritic, dict]:
    torch.manual_seed(counter_seed("model-init", seed))
    torch.set_num_threads(1)
    model = SetBidActorCritic()
    optimizer = torch.optim.Adam(
        model.parameters(), lr=REGISTERED.learning_rate,
        betas=(REGISTERED.adam_beta1, REGISTERED.adam_beta2), eps=REGISTERED.adam_eps,
        weight_decay=0.0,
    )
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    curves: list[dict] = []
    trials_seen = optimizer_steps = 0
    allocator_totals = {name: 0 for name in (
        "edges", "edge_key_evaluations", "heap_build_records", "heap_builds", "heap_pops",
        "heap_key_comparisons", "residual_updates", "task_agent_attention_scores",
        "bid_latents", "agent_agent_scores",
    )}
    latency_samples: dict[int, list[float]] = {6: [], 9: [], 12: []}
    for update in range(REGISTERED.updates):
        trials: list[Trial] = []
        exposure: dict[str, int] = {}
        for schedule_index, schedule in enumerate(TRAIN_SCHEDULES):
            panel = banks.training[schedule_index][update]
            for mass in MASSES:
                for geometry in GEOMETRIES:
                    for churn in CHURNS:
                        world = panel.worlds[(mass, geometry, churn)]
                        key = f"{schedule[0]}->{schedule[1]}|{mass}|{geometry}|{churn}"
                        for action_replica in range(REGISTERED.trials_per_cell_update):
                            trial, counters, full_ns = _collect_trial(model, world, update, action_replica)
                            trials.append(trial); exposure[key] = exposure.get(key, 0) + 1
                            latency_samples[world.n].append(full_ns / 1e6)
                            for name in ("edges", "edge_key_evaluations", "heap_build_records", "heap_builds",
                                         "heap_pops", "heap_key_comparisons", "residual_updates"):
                                allocator_totals[name] += int(counters[name])
                            allocator_totals["task_agent_attention_scores"] += 12 * world.n
                            allocator_totals["bid_latents"] += 3 * world.n
        if len(trials) != 128 or set(exposure.values()) != {4}:
            raise RuntimeError("registered 128-trial update exposure was not realized")
        rewards = torch.stack([trial.reward for trial in trials])
        advantages = torch.stack([trial.reward - trial.old_value for trial in trials])
        advantages = (advantages - advantages.mean()) / torch.sqrt(advantages.var(unbiased=True) + 1e-8)
        epoch_losses: list[tuple[float, float, float, float]] = []
        for epoch in range(REGISTERED.ppo_epochs):
            indices = generator(seed, "training", "minibatch-order", update, epoch).permutation(128)
            for begin in range(0, 128, REGISTERED.minibatch_trials):
                selected = indices[begin:begin + REGISTERED.minibatch_trials]
                policy_terms = []; value_terms = []; trial_entropies = []
                for raw_index in selected:
                    index = int(raw_index); trial = trials[index]
                    output = model(
                        trial.agents, trial.tasks, trial.global_row, lease_vector=trial.lease_vector,
                    )
                    distribution = Normal(output.mu, REGISTERED.bid_sigma)
                    logp = distribution.log_prob(trial.latent).sum()  # one unnormalized joint ratio
                    ratio = torch.exp(logp - trial.old_log_probability)
                    unclipped = ratio * advantages[index]
                    clipped = torch.clamp(ratio, .80, 1.20) * advantages[index]
                    policy_terms.append(-torch.minimum(unclipped, clipped))
                    value_terms.append((output.value - trial.reward).square())
                    trial_entropies.append(distribution.entropy().mean())
                policy_loss = torch.stack(policy_terms).mean()
                value_loss = torch.stack(value_terms).mean()
                entropy = torch.stack(trial_entropies).sum() / 8.0
                loss = policy_loss + .50 * value_loss - .01 * entropy
                optimizer.zero_grad(set_to_none=True); loss.backward()
                grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), REGISTERED.gradient_clip)
                optimizer.step(); optimizer_steps += 1
                if optimizer_steps == 1 and on_first_optimizer_step is not None:
                    on_first_optimizer_step({"seed": seed, "update": 1, "optimizer_step": 1})
                epoch_losses.append((float(policy_loss.detach()), float(value_loss.detach()),
                                     float(entropy.detach()), float(grad_norm)))
        trials_seen += 128
        curves.append({
            "update": update + 1, "trials": 128, "mean_J": float(rewards.mean()),
            "policy_loss": float(np.mean([x[0] for x in epoch_losses])),
            "value_loss": float(np.mean([x[1] for x in epoch_losses])),
            "entropy_per_trial_then_minibatch": float(np.mean([x[2] for x in epoch_losses])),
            "gradient_norm": float(np.mean([x[3] for x in epoch_losses])), "cell_exposure": exposure,
        })
    if trials_seen != 4096 or optimizer_steps != 4096:
        raise RuntimeError(f"training budget mismatch trials={trials_seen}, steps={optimizer_steps}")
    metadata = {
        "schema": "VNFC-B3-G-RELEASE-CHECKPOINT-v6", "seed": seed, "arm": "G-RELEASE",
        "final_update": 32, "trials": trials_seen, "optimizer_steps": optimizer_steps,
        "parameter_count": parameter_counts(model)["total"],
    }
    _atomic_checkpoint(model, checkpoint_path, metadata)
    return model, {
        **metadata, "wall_seconds": time.perf_counter() - start_wall,
        "cpu_seconds": time.process_time() - start_cpu, "curves": curves,
        "allocator_totals": allocator_totals,
        "training_event_decision_latency": {str(n): {"count": len(values),
            "p50_ms": float(np.percentile(values, 50)), "p95_ms": float(np.percentile(values, 95))}
            for n, values in latency_samples.items() if values},
    }


def load_checkpoint(path: Path) -> tuple[SetBidActorCritic, dict]:
    payload = torch.load(path, map_location="cpu", weights_only=True)
    model = SetBidActorCritic(); model.load_state_dict(payload["model"], strict=True); model.eval()
    return model, dict(payload["metadata"])
