"""Actor-only final panels of an M-trained proposer under the unchanged fixed deployment laws.

`evaluate_wrapped` reproduces `cluster_mappo_comparison_b01.mappo.evaluate` tick for tick. For the
panel "M" the substitution is disabled and every command, actor input, mask and recurrent state is
identical to the unchanged evaluator. For "F(M)" and "dwell(M)" the C-side laws of
`native_link_loss_b01.learner.collect` are applied to the M proposal: `Binding.observe` (a fresh
Binding per episode, evaluated on this panel's own history) flags link-loss opportunities and the
flagged agents send the retrace command (F) or the zero command (dwell) instead of the proposal. The
actually sent command feeds back into the next actor observation; remaining hold stays zero; one
actor call and its normal draw happen every primitive tick even when the command is replaced. No
critic, global input, ValueNorm or optimizer state is touched.
"""
import numpy as np
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import actor_features, team_reward
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from experiments.candidates.acvc.native_link_loss_b01.binding import Binding

PANELS = ("M", "F(M)", "dwell(M)")


@torch.no_grad()
def evaluate_wrapped(policy, env, episode, counts, emit, arm, namespace, horizon):
    if arm not in PANELS:
        raise ValueError(f"unknown panel {arm!r}")
    policy.actor.eval()
    policy.actor.act.generator = generator(100000 * namespace + 5000 + episode)
    reset_seed = 100000 * namespace + 2000 + episode
    obs, _ = env.reset(seed=reset_seed)
    counts["explicit_resets"] += 1
    last = np.zeros((5, 3), dtype=np.float32)
    hidden, masks = np.zeros((5, 1, 64), dtype=np.float32), np.zeros((5, 1), dtype=np.float32)
    binding = Binding() if arm != "M" else None
    decisions = {"opportunities": 0, "retrace": 0, "dwell": 0, "apply": 0, "distinguishable": 0}
    rewards = []
    for step in range(horizon):
        own = actor_features(obs, last, np.zeros(5, dtype=np.int64))
        raw, hidden_tensor = policy.act(own, hidden, masks)
        proposal = raw.tanh().cpu().numpy()
        hidden = hidden_tensor.cpu().numpy()
        masks.fill(1)
        counts["eval_actor_agent_forwards"] += 5
        if binding is None:
            sent = proposal
        else:
            _, mask, c = binding.observe(obs, proposal)
            if arm == "dwell(M)":
                c = np.zeros_like(c)
            sent = np.where(mask[:, None], c, proposal).astype(np.float32)
            n = int(mask.sum())
            decisions["opportunities"] += n
            decisions["dwell" if arm == "dwell(M)" else "retrace"] += n  # no learned gate: choice == mask
            decisions["distinguishable"] += int((mask & np.any(c != proposal, axis=1)).sum())
        counts["step_calls"] += 1
        counts["scientific_uav_calls"] += 1
        obs, _, terminated, truncated, info = env.step(sent)
        counts["team_steps"] += 1
        counts["eval_team_steps"] += 1
        rewards.append(team_reward(info))
        last = sent.copy()
        if truncated or bool(terminated) != (step + 1 == horizon):
            raise RuntimeError(f"unexpected final native boundary at {step + 1}/{horizon}")
    total = sum(rewards)
    row = dict(phase="eval", arm=arm, episode=episode, reset_seed=reset_seed, steps=horizon,
               S=total, J=total / horizon, terminated=True, truncated=False)
    if binding is not None:
        row.update(decisions)
    emit(row)
    counts["eval_episodes"] += 1
    counts["completed_episode_steps"] += horizon
