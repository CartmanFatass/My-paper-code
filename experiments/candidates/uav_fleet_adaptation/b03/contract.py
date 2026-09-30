"""Fixed recurrence identities; retained controls never create new exposure."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from experiments.candidates.uav_fleet_adaptation.b02.contract import (
    ARMS as COMPARISON_ARMS, PHASES, SOURCE_PINS, Protocol as OriginalProtocol,
    source_identities as original_sources,
)


NEW_ARMS = ("S0", "BC", "S_greedy", "S_sampled")
RETAINED_ARMS = ("C_memo", "C7_memo")
OBJECT = "UAV-LOCAL-C-INHERITANCE-RECURRENCE-B03"


@dataclass(frozen=True)
class Protocol(OriginalProtocol):
    training_worlds: tuple[tuple[int, ...], ...] = (
        tuple(range(29343000, 29343128)),
        tuple(range(29343128, 29343192)),
        tuple(range(29343192, 29343256)),
    )
    init_seed: int = 29344001
    shuffle_root: int = 29344002

    def expected(self):
        result = super().expected()
        decisions = self.horizon // self.period * self.n_agents
        retained = len(RETAINED_ARMS) * len(self.evaluation_worlds)
        result["evaluation_episodes"] = len(NEW_ARMS) * len(self.evaluation_worlds)
        result["complete_episodes"] = result["training_episodes"] + result["evaluation_episodes"]
        result["evaluation_native_steps"] = result["evaluation_episodes"] * self.horizon
        result["native_steps"] = result["complete_episodes"] * self.horizon
        result["full_C_requests"] = result["expert_label_requests"]
        result["C7_requests"] = 0
        result["helper_request_ceiling"] = result["expert_label_requests"] + len(NEW_ARMS) * len(self.evaluation_worlds) * decisions
        result["retained_evaluation_episodes"] = retained
        result["retained_native_steps"] = retained * self.horizon
        return result


FROZEN = Protocol().validate()


def source_identities(repo: Path):
    identities = original_sources(repo)
    for path in sorted((repo / "experiments/candidates/uav_fleet_adaptation/b03").glob("*.py")):
        identities[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return identities


def validate_counts(batch):
    expected, actual = batch["expected"], batch["actual"]
    for key in ("native_steps", "training_native_steps", "evaluation_native_steps", "complete_episodes",
                "training_episodes", "evaluation_episodes", "sample_presentations", "expert_label_requests"):
        if actual[key] != expected[key]:
            raise AssertionError(f"new exposure mismatch for {key}: {actual[key]} != {expected[key]}")
    if (actual["fit_started"] != 1 or actual["constructors"] != 1 or actual["constructor_resets"] != 1
            or actual["explicit_resets"] != expected["complete_episodes"]
            or actual["native_step_calls"] != expected["native_steps"]
            or actual["optimizer_steps"] != expected["optimizer_updates"]):
        raise AssertionError("new fit/reset/call/update contract mismatch")
    cost = batch["costs"]
    if (cost["full_C"].get("requests", 0) != expected["full_C_requests"]
            or cost["C7"].get("requests", 0) != 0):
        raise AssertionError("new ordinary-controller query exposure changed")
    if cost["helper"].get("helper_calls", 0) > expected["helper_request_ceiling"]:
        raise AssertionError("undeclared new helper calls")
    if (cost["neural"].get("neural_rows", 0) > expected["neural_rollout_row_ceiling"]
            or cost["neural"].get("sampled_draws", 0) != expected["sampled_draws"]):
        raise AssertionError("new neural forward/sampling exposure changed")
    retained = batch["retained"]
    if (len(retained["rows"]) != expected["retained_evaluation_episodes"]
            or retained["new_native_steps"] != 0 or not retained["already_paid"]):
        raise AssertionError("retained controls were omitted or counted as new execution")
