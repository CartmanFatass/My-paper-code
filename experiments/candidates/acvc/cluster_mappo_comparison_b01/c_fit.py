"""Reuse the accepted C learner and its private C/F/own-dwell deployment laws."""
from .protocol import MASTER, EVALUATION_NAMESPACE, TRAIN_EPISODES, EVAL_EPISODES, HORIZON, OBJECT, make_cluster


def execute(output, summary, emit, emit_update, progress):
    from scripts import run_acvc_fresh_dense_reuse_b01 as shared

    counts = summary["counts"]
    check = lambda: None
    common_actor, critic = shared.templates(MASTER)
    actor = shared.NativeGeometryActor(common_actor, shared.DENSE, 100000 * MASTER + 12)
    summary["fit_started"] = True
    counts["fresh_dense_initializations"] += 1
    initial = shared.geometry_snapshot(actor, critic)
    optimizer = shared.optimizer_for(actor, critic)
    for group in optimizer.param_groups:
        group["lr"] = 3e-4
    summary["configuration"].update(learning_rate=3e-4, opti_eps=1e-8, ratio_grouping="agent_compound",
                                     value_moments=None, renewal=False, duration_support=[1, 4],
                                     velocity_mode="sampled", entropy_coef=.01)
    train_velocity = shared.generator(100000 * MASTER + 21)
    env = make_cluster(100000 * MASTER + 1000)
    counts["environment_constructors"] += 1
    counts["unscored_constructor_resets"] += 1
    for rollout in range(TRAIN_EPISODES // 2):
        episodes = []
        for episode_id in (2 * rollout, 2 * rollout + 1):
            before = counts["recurrent_observations"]
            try:
                episode = shared.collect_episode(
                    env, actor, critic, HORIZON, 100000 * MASTER + 1000 + episode_id,
                    train_velocity, shared.generator(100000 * MASTER + 4000 + episode_id),
                    dict(master=MASTER, base=MASTER, arm="C", phase="train", episode=episode_id),
                    check, counts, lambda row: emit(dict(row, S=row["reward_sum"])),
                    lambda _row: None, summary["limits"], real=True, diagnostics=False,
                    ratio_grouping="agent_compound", value_moments=None, renewal=False,
                    duration_support=(1, 4), velocity_mode="sampled")
            finally:
                forwards = counts["recurrent_observations"] - before
                counts["base_agent_forwards"] += forwards
                counts["train_actor_agent_forwards"] += forwards
                counts["critic_forwards"] += forwards // 5
            episodes.append(episode)
        before = counts["optimizer_steps"]
        try:
            records = shared.update(actor, critic, optimizer, episodes, 32, check, counts,
                                    ratio_grouping="agent_compound", entropy_coef=.01, value_moments=None)
        except Exception:
            summary["interrupted_update"] = dict(rollout=rollout,
                completed_adam_steps=counts["optimizer_steps"] - before,
                limitation="Protected helper returns epoch records only after all four epochs.")
            raise
        performed = counts["optimizer_steps"] - before
        counts["backward_calls"] += performed
        counts["replayed_actor_agent_steps"] += performed * 2 * HORIZON * 5
        counts["critic_update_rows"] += performed * 2 * HORIZON
        for record in records:
            emit_update(dict(record, rollout=rollout, episodes=[2 * rollout, 2 * rollout + 1]))
        counts["rollouts"] += 1
        if (rollout + 1) % 16 == 0:
            progress()
    summary["fit_complete"] = True
    counts["new_fits"] += 1
    summary["exposure"] = shared.geometry_exposure(initial, actor, critic)
    path = output / "final.pt"
    shared.torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(), object=OBJECT,
                           master=MASTER, checkpoint_episode=TRAIN_EPISODES,
                           optimizer_steps=counts["optimizer_steps"]), path)
    counts["final_checkpoints"] += 1
    summary["checkpoint"] = path.name
    for arm in ("C", "F", "dwell"):
        base = shared.load_base(path, EVALUATION_NAMESPACE)
        counts["post_fit_loads"] += 1
        env = make_cluster(100000 * EVALUATION_NAMESPACE + 60 + {"C": 2, "F": 3, "dwell": 4}[arm])
        counts["environment_constructors"] += 1
        counts["unscored_constructor_resets"] += 1
        for episode in range(EVAL_EPISODES):
            before_steps, before_forwards = counts["team_steps"], counts["base_agent_forwards"]
            complete = False
            try:
                shared.collect(env, base, None, None, EVALUATION_NAMESPACE, arm, "eval",
                               episode, HORIZON, check, counts, emit)
                complete = True
            finally:
                steps = counts["team_steps"] - before_steps
                counts["eval_team_steps"] += steps
                counts["scientific_uav_calls"] += steps
                counts["eval_actor_agent_forwards"] += counts["base_agent_forwards"] - before_forwards
                if complete:
                    counts["completed_episode_steps"] += steps
        progress()
