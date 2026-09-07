"""Count-only real-host collection and the card's joint score-function learner."""

import torch
from torch import nn
from torch.nn import functional as F

from ..conditioning_discriminator_r01 import host
from ..conditioning_discriminator_r01.contract import CONTEXTS, K_EVAL, context_id

OBJECT_ID = "UCOPE-NATIVE-RETURN-ACQUISITION-B01"


def ancestry(seed, context):
    return (OBJECT_ID, f"seed-{seed}", context_id(context))


class Actor(nn.Module):
    def __init__(self, seed):
        super().__init__()
        self.root = nn.Parameter(torch.zeros(8, 2, dtype=torch.float32))
        # Explicit parameters avoid Linear's otherwise-unused global RNG draws.
        self.w1 = nn.Parameter(torch.empty(32, 9, dtype=torch.float32))
        self.b1 = nn.Parameter(torch.zeros(32, dtype=torch.float32))
        self.w2 = nn.Parameter(torch.empty(4, 32, dtype=torch.float32))
        self.b2 = nn.Parameter(torch.zeros(4, dtype=torch.float32))
        generator = torch.Generator(device="cpu").manual_seed(seed)
        nn.init.xavier_uniform_(self.w1, gain=1, generator=generator)
        nn.init.xavier_uniform_(self.w2, gain=1, generator=generator)

    def tail(self, contexts, counts):
        inputs = torch.cat((F.one_hot(contexts, 8).float(), counts.float()[:, None] / 6), dim=1)
        return F.linear(torch.tanh(F.linear(inputs, self.w1, self.b1)), self.w2, self.b2)

    def tail_table(self):
        return self.tail(torch.arange(8).repeat_interleave(7), torch.arange(7).repeat(8)).reshape(8, 7, 4)


def categorical(probabilities, uniforms):
    # Equality skips that bin; any terminal rounding remainder goes to the last.
    return (uniforms[..., None] >= probabilities.cumsum(-1)).sum(-1).clamp_max(probabilities.shape[-1] - 1)


def score_loss(returns, root_log_terms, tail_log_terms):
    grouped = returns.detach().reshape(8, 32)
    advantage = (grouped - (grouped.sum(1, keepdim=True) - grouped) / 31).reshape(256)
    return -(advantage * (root_log_terms + tail_log_terms)).mean()


def new_counts():
    return dict(episodes=0, transitions=0, probe_episodes=0, committed_period_units=0, probe_time_units=0)


def count_execution(counts, execution):
    probe = execution.root_action == "PROBE"
    counts["episodes"] += 1
    counts["transitions"] += execution.transition_count
    counts["probe_episodes"] += int(probe)
    counts["committed_period_units"] += execution.tail_period
    counts["probe_time_units"] += 2 * int(probe)


def collect_batch(actor, seed, update, root_generator, tail_generator, counts):
    context_rows = torch.arange(8).repeat_interleave(32)
    root_logits = actor.root[context_rows]
    root_uniforms = torch.rand(256, generator=root_generator, dtype=torch.float32)
    tail_uniforms = torch.rand(256, generator=tail_generator, dtype=torch.float32)
    actions = categorical(root_logits.detach().softmax(-1), root_uniforms)
    tail_logits = actor.tail_table()
    tail_probabilities = tail_logits.detach().softmax(-1)
    returns, visited_rows, visited_counts, visited_actions = [], [], [], []
    for row, c in enumerate(context_rows.tolist()):
        def choose(displayed_count):
            action = int(categorical(tail_probabilities[c, displayed_count], tail_uniforms[row]))
            visited_rows.append(row)
            visited_counts.append(displayed_count)
            visited_actions.append(action)
            return K_EVAL[action]

        probe = bool(actions[row])
        execution = host.execute_episode(
            CONTEXTS[c], ancestry=ancestry(seed, CONTEXTS[c]), episode_index=32 * update + row % 32,
            root_action="PROBE" if probe else "IMMEDIATE", support=K_EVAL,
            immediate_period=None if probe else 4, tail_selector=choose if probe else None,
        )
        count_execution(counts, execution)
        returns.append(execution.external_return)
    root_terms = root_logits.log_softmax(-1).gather(1, actions[:, None]).squeeze(1)
    tail_terms = torch.zeros(256, dtype=torch.float32)
    if visited_rows:
        selected = tail_logits[context_rows[visited_rows], visited_counts].log_softmax(-1)
        tail_terms[visited_rows] = selected.gather(1, torch.tensor(visited_actions)[:, None]).squeeze(1)
    rewards = torch.tensor(returns, dtype=torch.float32)
    return score_loss(rewards, root_terms, tail_terms), rewards, len(visited_rows)


def parameter_vectors(actor):
    return {"root": actor.root.detach().flatten().clone(),
            "tail": torch.cat([p.detach().flatten() for name, p in actor.named_parameters() if name != "root"])}


def movement(actor, initial, steps):
    report = {"joint_optimizer_steps": steps}
    for name, final in parameter_vectors(actor).items():
        origin = initial[name]
        displacement = final - origin
        norm = float(origin.norm())
        report[name] = {"initial_l2": norm, "displacement_l2": float(displacement.norm()),
                        "max_absolute_movement": float(displacement.abs().max())}
        if name == "tail":
            report[name]["displacement_over_initial_l2"] = float(displacement.norm()) / norm
    return report
