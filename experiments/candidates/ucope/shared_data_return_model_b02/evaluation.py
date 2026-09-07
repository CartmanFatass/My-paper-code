"""Final three-policy evaluation and the card's paired native-return comparisons."""

import math

from .model import CONTEXTS, K_EVAL, ancestry, context_id, count_execution, host, new_counts

POLICIES = ("FULL", "BLIND", "IMMEDIATE-4")
PAIRS = {"delta_native": ("FULL", "IMMEDIATE-4"),
         "delta_information": ("FULL", "BLIND"), "blind_minus_immediate": ("BLIND", "IMMEDIATE-4")}


def moments(values):
    mean = math.fsum(values) / len(values)
    variance = math.fsum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return {"mean": mean, "sample_variance": variance}


def reading_rule(native, information, full_probe_count, complete=True):
    if not complete or native is None or information is None:
        return {"branch": "INCOMPLETE"}
    if native > 0 and full_probe_count == 0:
        return {"branch": "INCOMPLETE", "integrity_gap": "positive native gain without FULL acquisition"}
    if native > .001:
        return {"branch": "RM-A" if information > .001 else "RM-D"}
    return {"branch": "RM-B" if native >= -.001 else "RM-C"}


def execute_policy(name, plan, context, index):
    probe = plan["root_action"] == "PROBE"
    selector = None
    if probe:
        selector = (lambda n: plan["tail_periods"][n]) if name == "FULL" else (lambda _n: plan["tail_period"])
    return host.execute_episode(
        context, ancestry=ancestry(context), episode_index=index, evaluation=True,
        root_action=plan["root_action"], support=K_EVAL,
        immediate_period=None if probe else 4, tail_selector=selector,
    )


def evaluate(plans, episodes, output, check_time):
    output.update(contexts=[], counts={name: new_counts() for name in POLICIES})
    for c, context in enumerate(CONTEXTS):
        row = {"context": context_id(context), "complete": False, "paired_episodes": 0,
               "policies": {name: dict(episodes=0, probe_count=0, paid_sum=0.0, return_sum=0.0)
                            for name in POLICIES}}
        output["contexts"].append(row)
        returns = {name: [] for name in POLICIES}
        paid = {name: [] for name in POLICIES}
        differences = {name: [] for name in PAIRS}
        for index in range(episodes):
            check_time()
            for name in POLICIES:
                result = execute_policy(name, plans[name][c], context, index)
                count_execution(output["counts"][name], result)
                returns[name].append(result.external_return)
                paid[name].append(result.probe_primitive)
                policy = row["policies"][name]
                policy["episodes"] += 1
                policy["probe_count"] += int(result.root_action == "PROBE")
                policy["paid_sum"] += result.probe_primitive
                policy["return_sum"] += result.external_return
            for key, (a, b) in PAIRS.items():
                differences[key].append(returns[a][-1] - returns[b][-1])
            row["paired_episodes"] += 1
        for name in POLICIES:
            policy = row["policies"][name]
            policy.update(mean_return=math.fsum(returns[name]) / episodes,
                          mean_paid_component=math.fsum(paid[name]) / episodes,
                          probe_frequency=policy["probe_count"] / episodes)
        row.update(differences={key: moments(values) for key, values in differences.items()}, complete=True)
    rows = output["contexts"]
    output["differences"] = {
        key: {"mean": math.fsum(row["differences"][key]["mean"] for row in rows) / len(CONTEXTS),
              "conditional_mc_se": math.sqrt(math.fsum(row["differences"][key]["sample_variance"] / episodes
                                                       for row in rows)) / len(CONTEXTS)}
        for key in PAIRS}
    output["policies"] = {
        name: {key: math.fsum(row["policies"][name][key] for row in rows) / len(CONTEXTS)
               for key in ("mean_return", "mean_paid_component", "probe_frequency")}
        for name in POLICIES}
