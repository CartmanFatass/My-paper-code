"""Serial source-style epsilon-greedy collection and complete-episode replay."""
import numpy as np
import torch
from torch.distributions import Categorical


def epsilon_at(ticks):
    return max(0.05, 1.0 - ticks * 0.95 / 50000)


def select_action(q, epsilon):
    # CAMA EpsilonGreedyActionSelector: preserve draws even for greedy/terminal.
    random_numbers = torch.rand_like(q[:, :, 0])
    pick_random = (random_numbers < epsilon).long()
    random_actions = Categorical(torch.ones_like(q)).sample().long()
    return pick_random * random_actions + (1 - pick_random) * q.max(dim=2)[1]


@torch.no_grad()
def collect(env, actor, epsilon):
    from .environment import count_transition
    env.reset()  # Deliberately no curriculum t_env argument.
    hidden = None
    previous = np.zeros(5, dtype=np.int64)
    observations, actions, rewards, terminals = [], [], [], []
    counts = dict(births=0, departures=0, survivor_opportunities=0, survivor_resets=0)
    for t in range(21):
        obs = env.observation(previous)
        observations.append(obs)
        batch = {k: torch.as_tensor(v)[None, None] for k, v in obs.items()}
        q, hs = actor(batch, hidden)
        hidden = hs[:, -1]
        chosen = select_action(q[:, 0], epsilon)[0].numpy()
        if t == 20:  # Source terminal controller pass, no 21st native step.
            break
        reward, done, _ = env.step(chosen)
        actions.append(chosen)
        rewards.append(reward)
        terminals.append(done)
        previous = chosen
        for k, v in count_transition(env, actor.arm).items():
            counts[k] += v
    episode = {k: np.stack([obs[k] for obs in observations]) for k in observations[0]}
    episode.update(actions=np.asarray(actions), reward=np.asarray(rewards, dtype=np.float32),
                   terminated=np.asarray(terminals, dtype=np.float32))
    # Primary preserves native float64 scalar sums, independent of learner FP32 casts.
    return episode, float(sum(rewards)), counts


def sample(replay):
    # Source EpisodeBuffer.sample uses global NumPy without replacement.
    ids = range(32) if len(replay) == 32 else np.random.choice(len(replay), 32, replace=False)
    return {k: torch.as_tensor(np.stack([replay[i][k] for i in ids])) for k in replay[0]}


def primary(retain, reset):
    d = float(np.mean(retain) - np.mean(reset))
    rule = 'RETAIN_ABOVE_MEI' if d >= 1 else 'RESET_ABOVE_MEI' if d <= -1 else 'WITHIN_MEI'
    return dict(J_RETAIN=float(np.mean(retain)), J_RESET=float(np.mean(reset)), difference=d, rule=rule)
