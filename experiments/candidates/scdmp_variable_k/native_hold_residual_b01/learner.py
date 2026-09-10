"""Source full-MC PPO with the sole selected two-ended held-segment term."""
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    returns_to_go, recurrent_outputs, clipped_policy_loss)
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import joint_terms

R_COLUMNS = (119, 123, 127, 131, 135)


def segment_pairs(rollout):
    # The leading axis is the episode; t4 is its stored pre-action successor.
    eligible = (rollout["critic"][:, 1:4, R_COLUMNS] != 0).any(-1)
    pair_index = eligible.nonzero(as_tuple=False)
    pair_index[:, 1] += 1
    rewards = rollout["reward"][:, 1:4].detach().flip(-1).cumsum(-1).flip(-1)
    return pair_index, rewards[eligible]


def residual_loss(values, pair_index, pair_rewards):
    if len(pair_index) == 0:
        return values.sum() * 0
    episode, time = pair_index.unbind(-1)
    return (values[episode, time] - pair_rewards - values[episode, 4]).square().mean()


def update(actor, critic, optimizer, episodes, chunk, check, counts, ratio_grouping="agent_compound", residual=False):
    rollout = {key: torch.stack([ep[key] for ep in episodes]) for key in episodes[0]}
    targets = returns_to_go(rollout["reward"])
    raw = targets - rollout["value"]
    advantages = ((raw - raw.mean()) / (raw.std(unbiased=False) + 1e-8)).detach()
    pair_index, pair_rewards = segment_pairs(rollout)
    parameters = list(actor.parameters()) + list(critic.parameters())
    records = []
    for epoch in range(4):
        check()
        mean, recurrent = recurrent_outputs(actor, rollout, chunk)
        logp, entropy = joint_terms(actor, mean, recurrent, rollout["u"], rollout["durations"],
                                    rollout["velocity_mask"], rollout["duration_mask"], ratio_grouping)
        policy_loss = clipped_policy_loss(logp, rollout["logp"], advantages,
                                          rollout["velocity_mask"] if ratio_grouping == "agent_compound" else None)
        values = critic(rollout["critic"])
        value_loss = (values - targets).square().mean()
        segment_loss = residual_loss(values, pair_index, pair_rewards) if residual else values.new_zeros(())
        loss = policy_loss + .5 * (value_loss + segment_loss) - .01 * entropy.mean()
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite PPO loss")
        optimizer.zero_grad()
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(parameters, .5)
        if not torch.isfinite(grad_norm):
            raise FloatingPointError("nonfinite PPO gradient")
        check()
        optimizer.step()
        counts["optimizer_steps"] += 1
        if not all(torch.isfinite(p).all() for p in parameters):
            raise FloatingPointError("nonfinite parameters after Adam")
        records.append({"epoch": epoch, "loss": float(loss.detach()),
                        "policy_loss": float(policy_loss.detach()),
                        "value_loss": float(value_loss.detach()),
                        "segment_loss": float(segment_loss.detach()), "eligible_pairs": len(pair_index),
                        "residual_terms": len(pair_index) if residual else 0,
                        "entropy": float(entropy.mean().detach()), "grad_norm": float(grad_norm)})
        check()
    return records
