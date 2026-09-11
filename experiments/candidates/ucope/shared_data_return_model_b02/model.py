"""Binary64 incremental means, streamed real episodes, and deterministic policies."""

import math
import random

from ..conditioning_discriminator_r01 import host
from ..conditioning_discriminator_r01.contract import CONTEXTS, K_EVAL, MARKS, context_id

OBJECT_ID = "UCOPE-SHARED-DATA-RETURN-MODEL-B02"
SEED = 6401
BATCHES = 1024
EVAL_EPISODES = 4096


def ancestry(context, seed=SEED):
    return (OBJECT_ID, f"seed-{seed}", context_id(context))


def increment(value, count, reward):
    count += 1
    value = value + (reward - value) / count
    return value, count


class ReturnModel:
    def __init__(self):
        self.q_immediate = [0.0 for _ in CONTEXTS]
        self.n_immediate = [0 for _ in CONTEXTS]
        self.q_full = [[[0.0 for _ in K_EVAL] for _ in range(MARKS + 1)] for _ in CONTEXTS]
        self.n_full = [[[0 for _ in K_EVAL] for _ in range(MARKS + 1)] for _ in CONTEXTS]
        self.q_blind = [[0.0 for _ in K_EVAL] for _ in CONTEXTS]
        self.n_blind = [[0 for _ in K_EVAL] for _ in CONTEXTS]
        self.histogram = [[0 for _ in range(MARKS + 1)] for _ in CONTEXTS]

    def observe(self, context_index, execution):
        c, reward = context_index, execution.external_return
        if execution.root_action == "IMMEDIATE":
            self.q_immediate[c], self.n_immediate[c] = increment(
                self.q_immediate[c], self.n_immediate[c], reward)
        else:
            n, k = execution.displayed_short_count, K_EVAL.index(execution.tail_period)
            self.q_full[c][n][k], self.n_full[c][n][k] = increment(
                self.q_full[c][n][k], self.n_full[c][n][k], reward)
            self.q_blind[c][k], self.n_blind[c][k] = increment(
                self.q_blind[c][k], self.n_blind[c][k], reward)
            self.histogram[c][n] += 1

    def full_values(self, c, n):
        return [self.q_full[c][n][k] if self.n_full[c][n][k] else self.q_blind[c][k]
                for k in range(len(K_EVAL))]

    def final_policies(self):
        plans = {"FULL": [], "BLIND": [], "IMMEDIATE-4": []}
        for c in range(len(CONTEXTS)):
            full_values = [self.full_values(c, n) for n in range(MARKS + 1)]
            tails = [max(range(len(K_EVAL)), key=values.__getitem__) for values in full_values]
            probes = sum(self.histogram[c])
            expectation = (math.fsum(self.histogram[c][n] / probes * full_values[n][tails[n]]
                                     for n in range(MARKS + 1)) if probes else None)
            plans["FULL"].append({
                "root_action": "PROBE" if probes and expectation > self.q_immediate[c] else "IMMEDIATE",
                "tail_periods": [K_EVAL[k] for k in tails], "estimated_probe_return": expectation,
            })
            blind = max(range(len(K_EVAL)), key=self.q_blind[c].__getitem__)
            plans["BLIND"].append({
                "root_action": "PROBE" if self.q_blind[c][blind] > self.q_immediate[c] else "IMMEDIATE",
                "tail_period": K_EVAL[blind], "estimated_probe_return": self.q_blind[c][blind],
            })
            plans["IMMEDIATE-4"].append({"root_action": "IMMEDIATE", "immediate_period": 4})
        return plans

    def exposure(self):
        report = {"initial_value_l2": 0.0, "first_observation_step_size": 1.0,
                  "histogram_updates": sum(map(sum, self.histogram)),
                  "occupied_histogram_entries": sum(n > 0 for row in self.histogram for n in row)}
        values_and_counts = {
            "shared_immediate": (self.q_immediate, self.n_immediate),
            "full": ([q for row in self.q_full for cell in row for q in cell],
                     [n for row in self.n_full for cell in row for n in cell]),
            "blind": ([q for row in self.q_blind for q in row], [n for row in self.n_blind for n in row]),
        }
        for name, (values, counts) in values_and_counts.items():
            report[name] = {"value_entries": len(values), "scalar_updates": sum(counts),
                            "occupied_entries": sum(n > 0 for n in counts), "initial_l2": 0.0,
                            "displacement_l2": math.sqrt(math.fsum(q * q for q in values)),
                            "max_absolute_movement": max(map(abs, values))}
        report["scalar_value_updates"] = sum(report[name]["scalar_updates"] for name in values_and_counts)
        return report


def new_counts():
    return dict(episodes=0, transitions=0, probe_episodes=0, immediate_episodes=0,
                committed_period_units=0, probe_time_units=0)


def count_execution(counts, execution):
    probe = execution.root_action == "PROBE"
    counts["episodes"] += 1
    counts["transitions"] += execution.transition_count
    counts["probe_episodes"] += int(probe)
    counts["immediate_episodes"] += int(not probe)
    counts["committed_period_units"] += execution.tail_period
    counts["probe_time_units"] += 2 * int(probe)


def collect(model, training, check_time, batches=BATCHES, seed=SEED):
    behavior = random.Random(seed + 2_000_000)
    training.update(new_counts(), behavior_uniforms=0, batches_completed=0)
    for u in range(batches):
        check_time()
        for c, context in enumerate(CONTEXTS):
            for j in range(32):
                uniform = behavior.random()
                training["behavior_uniforms"] += 1
                period = K_EVAL[int(4 * uniform)]
                probe = j >= 16
                execution = host.execute_episode(
                    context, ancestry=ancestry(context, seed), episode_index=32 * u + j, evaluation=False,
                    root_action="PROBE" if probe else "IMMEDIATE", support=K_EVAL,
                    immediate_period=None if probe else 4,
                    tail_selector=(lambda _count: period) if probe else None,
                )
                count_execution(training, execution)
                model.observe(c, execution)
        training["batches_completed"] += 1
