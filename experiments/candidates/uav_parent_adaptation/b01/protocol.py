"""The prospectively fixed B01 addresses and scientific exposure."""

HORIZON, TRAIN, EVAL = 256, 512, 32
LINEAGES = (1, 2, 3)
STAGES = ("C", "B", "K", "D")
PROGRAMS = ("I", "P", "K", "D")
FIRST_MASTER = 29811


def masters(lineage):
    if lineage not in LINEAGES:
        raise ValueError("B01 has exactly three fixed root lineages")
    start = 29801 + 10 * lineage
    return dict(C=start, B=start + 1, K=start + 2, D=start + 2, evaluation=start + 3)


def addresses(lineage, stage, *, train=TRAIN, evaluation=EVAL):
    base = 100000 * masters(lineage)[stage]
    if stage == "evaluation":
        return dict(master=base // 100000, scene_start=base + 2000,
                    scene_end=base + 2000 + evaluation - 1,
                    channel_start=base + 7000, channel_end=base + 7000 + evaluation - 1,
                    motion_start=base + 3000, motion_end=base + 3000 + evaluation - 1,
                    motion_mode="fresh_per_episode")
    return dict(master=base // 100000, construction=base + 11,
                scene_start=base + 1000, scene_end=base + 1000 + train - 1,
                channel_start=base + 6000, channel_end=base + 6000 + train - 1,
                motion=base + 21, motion_mode="continuous_across_training_episodes")


def rng_table():
    return {str(lineage): {stage: addresses(lineage, stage)
                          for stage in (*STAGES, "evaluation")} for lineage in LINEAGES}


def expected_training_counts(stage, horizon=HORIZON, train=TRAIN):
    if stage not in STAGES or train % 2 or horizon % 32:
        raise ValueError("fixed full-episode/chunk32 update contract")
    steps, epochs = train * horizon, train // 2 * 4
    parent = stage in ("C", "B")
    return dict(fit_started=1, constructors=1, explicit_resets=train,
                train_episodes=train, final_eval_episodes=0,
                train_team_steps=steps, final_eval_team_steps=0,
                team_steps=steps, native_step_calls=steps, motion_samples=steps * 5,
                broadcasts=steps, attempts=steps, rollouts=train // 2,
                optimizer_steps=epochs, joint_optimizer_steps=epochs if parent else 0,
                actor_optimizer_steps=0 if parent else epochs,
                critic_optimizer_steps=0 if parent else epochs,
                actual_adam_calls=epochs * (1 if parent else 2),
                replayed_actor_rows=epochs * 2 * horizon * 5,
                replayed_critic_rows=epochs * 2 * horizon,
                behavior_actor_forward_calls=steps, behavior_actor_forward_rows=steps * 5,
                behavior_critic_forward_calls=steps, behavior_critic_forward_rows=steps,
                ppo_actor_forward_calls=epochs, ppo_actor_forward_rows=epochs * 2 * horizon * 5,
                ppo_critic_forward_calls=epochs, ppo_critic_forward_rows=epochs * 2 * horizon,
                evaluation_optimizer_steps=0, diagnostic_forward_calls=0)


def expected_evaluation_counts(horizon=HORIZON, evaluation=EVAL):
    counts = {key: 0 for key in expected_training_counts("C", horizon, 2)}
    steps = horizon * evaluation
    counts.update(constructors=1, explicit_resets=evaluation,
                  final_eval_episodes=evaluation, final_eval_team_steps=steps,
                  team_steps=steps, native_step_calls=steps, motion_samples=steps * 5,
                  broadcasts=steps, attempts=steps,
                  behavior_actor_forward_calls=steps, behavior_actor_forward_rows=steps * 5)
    return counts
