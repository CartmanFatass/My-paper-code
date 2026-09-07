"""Paired final-modal evaluation; float64/Python-float moments."""

import math
import statistics

import torch

from .learner import ancestry, count_execution, new_counts
from ..conditioning_discriminator_r01 import host
from ..conditioning_discriminator_r01.contract import CONTEXTS, K_EVAL, context_id


def paired_moments(actor_returns, reference_returns):
    differences = [a - b for a, b in zip(actor_returns, reference_returns)]
    return {"episodes_per_policy": len(differences),
            "actor_mean_return": statistics.mean(actor_returns),
            "reference_mean_return": statistics.mean(reference_returns),
            "difference": statistics.mean(differences),
            "paired_sample_variance": statistics.variance(differences) if len(differences) > 1 else None}


def reading_rule(seed_results):
    if (len(seed_results) != 2 or {s["seed"] for s in seed_results} != {6301, 6302}
            or any(s["status"] != "COMPLETE" or s["profile"] != "science" for s in seed_results)):
        return {"branch": "INCOMPLETE", "delta_bar": None}
    delta = statistics.mean(s["evaluation"]["delta"] for s in seed_results)
    return {"branch": "NR-A" if delta > .001 else "NR-C" if delta < -.001 else "NR-B", "delta_bar": delta}


@torch.no_grad()
def evaluate(actor, seed, episodes, output, check_time):
    roots = actor.root.argmax(-1).tolist()
    tails = actor.tail_table().argmax(-1).tolist()
    output.update(contexts=[], actor_counts=new_counts(), reference_counts=new_counts(),
                  modal_root_actions=roots, modal_tail_periods=[[K_EVAL[k] for k in row] for row in tails])
    for c, context in enumerate(CONTEXTS):
        actor_returns, reference_returns, paid = [], [], []
        row = {"context": context_id(context), "complete": False, "episodes_per_policy": 0,
               "actor_return_sum": 0., "reference_return_sum": 0., "paid_component_sum": 0.}
        output["contexts"].append(row)
        for index in range(episodes):
            check_time()
            probe = roots[c] == 1
            result = host.execute_episode(
                context, ancestry=ancestry(seed, context), episode_index=index, evaluation=True,
                root_action="PROBE" if probe else "IMMEDIATE", support=K_EVAL,
                immediate_period=None if probe else 4,
                tail_selector=(lambda count: K_EVAL[tails[c][count]]) if probe else None,
            )
            count_execution(output["actor_counts"], result)
            reference = host.execute_episode(
                context, ancestry=ancestry(seed, context), episode_index=index, evaluation=True,
                root_action="IMMEDIATE", immediate_period=4, support=K_EVAL,
            )
            count_execution(output["reference_counts"], reference)
            actor_returns.append(result.external_return)
            reference_returns.append(reference.external_return)
            paid.append(result.probe_primitive)
            row["episodes_per_policy"] += 1
            # Retain direct paired moments if the cap/host interrupts this context.
            row["actor_return_sum"] += result.external_return
            row["reference_return_sum"] += reference.external_return
            row["paid_component_sum"] += result.probe_primitive
        row.update(paired_moments(actor_returns, reference_returns), complete=True,
                   actor_probe_frequency=float(probe), reference_probe_frequency=0.,
                   actor_mean_paid_component=statistics.mean(paid), reference_mean_paid_component=0.)
    rows = output["contexts"]
    output["delta"] = statistics.mean(row["difference"] for row in rows)
    output["conditional_mc_se"] = math.sqrt(sum(row["paired_sample_variance"] / episodes for row in rows)) / 8
    for name in ("actor_mean_return", "reference_mean_return", "actor_probe_frequency",
                 "reference_probe_frequency", "actor_mean_paid_component", "reference_mean_paid_component"):
        output[name] = statistics.mean(row[name] for row in rows)
