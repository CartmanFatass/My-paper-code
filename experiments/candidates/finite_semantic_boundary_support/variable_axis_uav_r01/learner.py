from __future__ import annotations

import hashlib
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping, Sequence

from .counter import address, categorical


REGISTERED_SEEDS = {11, 23, 37, 53, 71, 89, 107, 127}
TECHNICAL_ARMS = {"TECHNICAL_A", "TECHNICAL_B"}


@dataclass(frozen=True)
class TechnicalDecision:
    action: int
    features: tuple[Fraction, Fraction, Fraction, Fraction]
    pre_window_score: Fraction
    canned_common_signal: Fraction


def _zeros() -> list[list[Fraction]]:
    return [[Fraction(0) for _ in range(4)] for _ in range(2)]


def _encoded(value: Fraction) -> list[int]:
    return [value.numerator, value.denominator]


class TechnicalLinearLearner:
    """Exact R01 heads restricted to explicit nonregistered technical fixtures."""

    def __init__(self, arm: str, seed: int) -> None:
        if seed in REGISTERED_SEEDS:
            raise PermissionError("registered R01 seeds are forbidden in S2 fixtures")
        if arm not in TECHNICAL_ARMS:
            raise PermissionError("S2 accepts only nonregistered technical arms")
        self.arm = arm
        self.seed = seed
        self._selector = _zeros()
        self._controller = _zeros()
        self._completed_windows: set[str] = set()

    @property
    def selector_weights(self) -> tuple[tuple[Fraction, ...], ...]:
        return tuple(tuple(row) for row in self._selector)

    @property
    def controller_weights(self) -> tuple[tuple[Fraction, ...], ...]:
        return tuple(tuple(row) for row in self._controller)

    @staticmethod
    def _features(value: Mapping[str, int], bit_name: str) -> tuple[Fraction, ...]:
        expected = {bit_name, "i", "r"}
        if set(value) != expected:
            raise ValueError(f"feature input must contain exactly {sorted(expected)}")
        if any(value[name] not in (0, 1) for name in expected):
            raise ValueError("technical feature values must be binary")
        return (
            Fraction(1),
            Fraction(2 * value[bit_name] - 1),
            Fraction(2 * value["i"] - 1),
            Fraction(2 * value["r"] - 1),
        )

    def selector_features(self, value: Mapping[str, int]) -> tuple[Fraction, ...]:
        return self._features(value, "surface_bit")

    def controller_features(self, value: Mapping[str, int]) -> tuple[Fraction, ...]:
        return self._features(value, "payload_bit")

    @staticmethod
    def action_names(head: str) -> tuple[str, str]:
        if head == "selector":
            return ("OPEN_0", "OPEN_1")
        if head == "controller":
            return ("LANE_0", "LANE_1")
        raise ValueError("head must be selector or controller")

    @staticmethod
    def epsilon(completed_decisions: int) -> Fraction:
        if completed_decisions < 0 or completed_decisions > 1_984:
            raise ValueError("completed decisions must be in [0,1984]")
        return Fraction(2, 5) - Fraction(7, 20) * Fraction(
            completed_decisions, 1_984
        )

    def paired_address(self, family: str, coordinates: Sequence[str | int]) -> str:
        return hashlib.sha256(address(self.seed, family, coordinates, 0)).hexdigest()

    def choose_action(
        self,
        head: str,
        features: Sequence[Fraction],
        *,
        completed_decisions: int,
        coordinates: Sequence[str | int],
    ) -> tuple[int, Fraction, dict[str, str]]:
        epsilon = self.epsilon(completed_decisions)
        exploration_rank = categorical(
            10_000, self.seed, "exploration", (*coordinates, head)
        )
        exploration_address = self.paired_address(
            "exploration", (*coordinates, head)
        )
        feature_coordinates = tuple(
            f"{value.numerator}/{value.denominator}" for value in features
        )
        tie_address = self.paired_address(
            "tie-rank", (*coordinates, head, *feature_coordinates)
        )
        scores = (self.score(head, 0, features), self.score(head, 1, features))
        if exploration_rank * epsilon.denominator < epsilon.numerator * 10_000:
            action = categorical(
                2, self.seed, "exploration-action", (*coordinates, head)
            )
        elif scores[0] == scores[1]:
            action = categorical(
                2,
                self.seed,
                "tie-rank",
                (*coordinates, head, *feature_coordinates),
            )
        else:
            action = int(scores[1] > scores[0])
        return action, scores[action], {
            "exploration": exploration_address,
            "tie_rank": tie_address,
        }

    def _weights(self, head: str) -> list[list[Fraction]]:
        if head == "selector":
            return self._selector
        if head == "controller":
            return self._controller
        raise ValueError("head must be selector or controller")

    def score(
        self, head: str, action: int, features: Sequence[Fraction]
    ) -> Fraction:
        if action not in (0, 1) or len(features) != 4:
            raise ValueError("technical score requires one legal action and four features")
        return sum(
            (weight * feature for weight, feature in zip(self._weights(head)[action], features)),
            start=Fraction(0),
        )

    def apply_grouped_window_update(
        self,
        head: str,
        decisions: Sequence[TechnicalDecision],
        *,
        pair_count: int,
        window_id: str,
    ) -> dict[str, Any]:
        completed_key = f"{head}:{window_id}"
        if completed_key in self._completed_windows:
            raise ValueError(f"window already applied: {window_id}")
        if pair_count not in (2, 3, 4, 5) or not decisions:
            raise ValueError("technical grouped update requires a registered pair-count shape")
        weights = self._weights(head)
        coefficient = Fraction(1, 80 * pair_count)
        grouped = [[Fraction(0) for _ in range(4)] for _ in range(2)]
        pre_window_digest = self.snapshot_digest()
        for decision in decisions:
            if decision.action not in (0, 1) or len(decision.features) != 4:
                raise ValueError("technical decision shape is invalid")
            if decision.pre_window_score != self.score(
                head, decision.action, decision.features
            ):
                raise ValueError("decision was not sampled from the same pre-window generation")
            residual = decision.canned_common_signal - decision.pre_window_score
            for index, feature in enumerate(decision.features):
                grouped[decision.action][index] += residual * feature
        for action in (0, 1):
            for index in range(4):
                weights[action][index] += coefficient * grouped[action][index]
        self._completed_windows.add(completed_key)
        return {
            "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
            "window_id": window_id,
            "head": head,
            "coefficient": _encoded(coefficient),
            "same_pre_window_generation": True,
            "reduction": "COMMUTATIVE_SUM_GROUPED_BY_ACTION",
            "applications": 1,
            "pre_window_digest": pre_window_digest,
            "post_window_digest": self.snapshot_digest(),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
            "arm": self.arm,
            "seed": self.seed,
            "selector": [[_encoded(value) for value in row] for row in self._selector],
            "controller": [[_encoded(value) for value in row] for row in self._controller],
            "completed_windows": sorted(self._completed_windows),
        }

    def snapshot_digest(self) -> str:
        import json

        payload = json.dumps(
            self.snapshot(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any]) -> "TechnicalLinearLearner":
        if snapshot.get("fixture_kind") != "NONREGISTERED_TECHNICAL_ONLY":
            raise ValueError("snapshot is not a nonregistered technical fixture")
        learner = cls(str(snapshot["arm"]), int(snapshot["seed"]))
        for name, target in (("selector", learner._selector), ("controller", learner._controller)):
            rows = snapshot.get(name)
            if not isinstance(rows, list) or len(rows) != 2 or any(
                not isinstance(row, list) or len(row) != 4 for row in rows
            ):
                raise ValueError("technical snapshot head shape is invalid")
            for action, row in enumerate(rows):
                for index, encoded in enumerate(row):
                    target[action][index] = Fraction(int(encoded[0]), int(encoded[1]))
        completed = snapshot.get("completed_windows")
        if not isinstance(completed, list) or len(completed) != len(set(completed)):
            raise ValueError("technical snapshot completed-window ledger is invalid")
        learner._completed_windows = {str(value) for value in completed}
        return learner


@dataclass(frozen=True)
class ProductionDecision:
    action: int
    features: tuple[float, float, float, float]
    pre_window_score: float


class _ProductionLinearCore:
    """Shared numerical kernel for released execution and result-blind mirrors."""

    fixture_kind = "REGISTERED"

    def __init__(self, arm: str, seed: int) -> None:
        self.arm = arm
        self.seed = seed
        self._selector = [[0.0] * 4 for _ in range(2)]
        self._controller = [[0.0] * 4 for _ in range(2)]
        self.completed_decisions = 0
        self._completed_windows: set[str] = set()

    @property
    def selector_weights(self) -> tuple[tuple[float, ...], ...]:
        return tuple(tuple(row) for row in self._selector)

    @property
    def controller_weights(self) -> tuple[tuple[float, ...], ...]:
        return tuple(tuple(row) for row in self._controller)

    @staticmethod
    def features(bit: int, i: int, r: int) -> tuple[float, float, float, float]:
        if {bit, i, r} - {0, 1}:
            raise ValueError("production features are binary")
        return (1.0, float(2 * bit - 1), float(2 * i - 1), float(2 * r - 1))

    @staticmethod
    def epsilon(completed_decisions: int) -> float:
        if completed_decisions < 0 or completed_decisions > 1_984:
            raise ValueError("completed decisions must be in [0,1984]")
        return 0.40 - 0.35 * completed_decisions / 1_984

    def _weights(self, head: str) -> list[list[float]]:
        if head == "selector":
            return self._selector
        if head == "controller":
            return self._controller
        raise ValueError("head must be selector or controller")

    def score(self, head: str, action: int, features: Sequence[float]) -> float:
        if action not in (0, 1) or len(features) != 4:
            raise ValueError("production score requires one legal action and four features")
        return sum(
            weight * feature
            for weight, feature in zip(self._weights(head)[action], features)
        )

    def choose_training_action(
        self,
        head: str,
        features: Sequence[float],
        *,
        coordinates: Sequence[str | int],
    ) -> tuple[int, float]:
        scores = (self.score(head, 0, features), self.score(head, 1, features))
        epsilon = Fraction(2, 5) - Fraction(7, 20) * Fraction(
            self.completed_decisions, 1_984
        )
        rank = categorical(10_000, self.seed, "exploration", (*coordinates, head))
        if rank * epsilon.denominator < epsilon.numerator * 10_000:
            action = categorical(
                2, self.seed, "exploration", (*coordinates, head, "action")
            )
        elif scores[0] == scores[1]:
            action = categorical(
                2,
                self.seed,
                "tie-rank",
                (head, *(f"{value:.17g}" for value in features)),
            )
        else:
            action = int(scores[1] > scores[0])
        return action, scores[action]

    def choose_greedy_action(
        self, head: str, features: Sequence[float]
    ) -> tuple[int, float]:
        scores = (self.score(head, 0, features), self.score(head, 1, features))
        if scores[0] == scores[1]:
            action = categorical(
                2,
                self.seed,
                "tie-rank",
                (head, *(f"{value:.17g}" for value in features)),
            )
        else:
            action = int(scores[1] > scores[0])
        return action, scores[action]

    def apply_window(
        self,
        selector: Sequence[ProductionDecision],
        controller: Sequence[ProductionDecision],
        *,
        pair_count: int,
        window_id: str,
        common_team_return: float,
    ) -> dict[str, Any]:
        if window_id in self._completed_windows:
            raise ValueError(f"window already applied: {window_id}")
        if pair_count not in (2, 3, 4, 5):
            raise ValueError("production window pair_count is outside registered support")
        if len(selector) != pair_count or len(controller) != pair_count:
            raise ValueError("production window requires one selector/controller row per pair")
        coefficient = 1.0 / (80.0 * pair_count)
        for head, decisions in (("selector", selector), ("controller", controller)):
            grouped = [[0.0] * 4 for _ in range(2)]
            for decision in decisions:
                if decision.pre_window_score != self.score(
                    head, decision.action, decision.features
                ):
                    raise ValueError("decision does not belong to the pre-window generation")
                residual = common_team_return - decision.pre_window_score
                for index, feature in enumerate(decision.features):
                    grouped[decision.action][index] += residual * feature
            weights = self._weights(head)
            for action in (0, 1):
                for index in range(4):
                    weights[action][index] += coefficient * grouped[action][index]
        self.completed_decisions += pair_count
        if self.completed_decisions > 1_984:
            raise ValueError("registered learner exceeded 1984 training decisions")
        self._completed_windows.add(window_id)
        return {
            "window_id": window_id,
            "coefficient": coefficient,
            "same_pre_window_generation": True,
            "applications": 1,
            "completed_decisions": self.completed_decisions,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": "FSBS_R01_PRODUCTION_LEARNER_SNAPSHOT_V2",
            "fixture_kind": self.fixture_kind,
            "arm": self.arm,
            "seed": self.seed,
            "selector": self._selector,
            "controller": self._controller,
            "completed_decisions": self.completed_decisions,
            "completed_windows": sorted(self._completed_windows),
        }

    def snapshot_digest(self) -> str:
        import json

        return hashlib.sha256(
            json.dumps(
                self.snapshot(), sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()

    def _restore(self, snapshot: Mapping[str, Any]) -> None:
        if snapshot.get("schema") != "FSBS_R01_PRODUCTION_LEARNER_SNAPSHOT_V2":
            raise ValueError("production snapshot schema is invalid")
        for name, target in (("selector", self._selector), ("controller", self._controller)):
            rows = snapshot.get(name)
            if not isinstance(rows, list) or len(rows) != 2 or any(
                not isinstance(row, list) or len(row) != 4 for row in rows
            ):
                raise ValueError("production snapshot head shape is invalid")
            for action, row in enumerate(rows):
                target[action][:] = [float(value) for value in row]
        completed = snapshot.get("completed_windows")
        if not isinstance(completed, list) or len(completed) != len(set(completed)):
            raise ValueError("production completed-window ledger is invalid")
        self._completed_windows = {str(value) for value in completed}
        self.completed_decisions = int(snapshot.get("completed_decisions", -1))
        if not 0 <= self.completed_decisions <= 1_984:
            raise ValueError("production completed decision count is invalid")


class RegisteredLinearLearner(_ProductionLinearCore):
    fixture_kind = "REGISTERED_R01_RELEASED"

    def __init__(self, arm: str, seed: int, *, release: Mapping[str, Any] | None) -> None:
        if not release or release.get("released") is not True:
            raise PermissionError("registered learner requires a validated release")
        if arm not in {"AUTHENTIC", "REASSOCIATED"} or seed not in REGISTERED_SEEDS:
            raise ValueError("registered learner arm/seed is outside R01")
        super().__init__(arm, seed)

    @classmethod
    def from_snapshot(
        cls, snapshot: Mapping[str, Any], *, release: Mapping[str, Any]
    ) -> "RegisteredLinearLearner":
        learner = cls(str(snapshot["arm"]), int(snapshot["seed"]), release=release)
        if snapshot.get("fixture_kind") != cls.fixture_kind:
            raise ValueError("registered snapshot fixture kind is invalid")
        learner._restore(snapshot)
        return learner


class ResultBlindLinearMirror(_ProductionLinearCore):
    fixture_kind = "NONREGISTERED_RESULT_BLIND_MIRROR"

    def __init__(self, arm: str, seed: int) -> None:
        if not arm.startswith("MIRROR_") or seed in REGISTERED_SEEDS:
            raise PermissionError("result-blind mirror forbids registered arm/seed")
        super().__init__(arm, seed)

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, Any]) -> "ResultBlindLinearMirror":
        if snapshot.get("fixture_kind") != cls.fixture_kind:
            raise ValueError("result-blind mirror snapshot kind is invalid")
        learner = cls(str(snapshot["arm"]), int(snapshot["seed"]))
        learner._restore(snapshot)
        return learner
