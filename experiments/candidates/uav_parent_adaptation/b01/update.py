"""Reuse the two distinct historical update laws, with explicit call accounting."""

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.learner import (
    optimizer_for as parent_optimizer, update as joint_update,
)
from experiments.candidates.uav_message_content.b06.update import optimizers_for
from experiments.candidates.uav_message_content.b05.update import update_motion


def update_parent(actor, critic, optimizer, episodes, counts, check, emit_update):
    if len(episodes) != 2 or episodes[0]["obs"].shape[0] % 32:
        raise ValueError("two whole episodes and chunk32 required")
    horizon = episodes[0]["obs"].shape[0]
    before = counts["optimizer_steps"]
    try:
        records = joint_update(actor, critic, optimizer, episodes, counts, check, chunk=32)
    finally:
        calls = counts["optimizer_steps"] - before
        counts["joint_optimizer_steps"] += calls
        counts["actual_adam_calls"] += calls
        counts["replayed_actor_rows"] += calls * 2 * horizon * 5
        counts["replayed_critic_rows"] += calls * 2 * horizon
        counts["ppo_actor_forward_calls"] += calls
        counts["ppo_actor_forward_rows"] += calls * 2 * horizon * 5
        counts["ppo_critic_forward_calls"] += calls
        counts["ppo_critic_forward_rows"] += calls * 2 * horizon
    for record in records:
        emit_update(dict(kind="joint_ppo", **record))


def update_adaptation(actor, critic, actor_opt, critic_opt, episodes, counts, check, emit_update):
    actor_before, critic_before = counts["actor_optimizer_steps"], counts["critic_optimizer_steps"]
    try:
        update_motion(actor, critic, actor_opt, critic_opt, episodes, counts, check, emit_update)
    finally:
        counts["actual_adam_calls"] += (counts["actor_optimizer_steps"] - actor_before
                                        + counts["critic_optimizer_steps"] - critic_before)
        counts["replayed_critic_rows"] = counts["ppo_critic_forward_rows"]
