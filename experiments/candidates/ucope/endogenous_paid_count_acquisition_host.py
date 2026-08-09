"""Five-trial real host for frozen UCOPE-B2 paid count acquisition.

The host owns the physical clock, latent regime lifecycle, immutable acquisition
ledger, and all policy callbacks.  Callers may force a root or tail action only
by supplying a callback; actions and rewards are never injected into a row.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
import hashlib
import json
from typing import Callable


S = "S"
L = "L"
PERIODS = (S, L)
COMMIT_S = "COMMIT_S"
COMMIT_L = "COMMIT_L"
BUY_SL = "BUY_SL"
ROOT_ACTIONS = (COMMIT_S, COMMIT_L, BUY_SL)
THETA_S = "THETA_S"
THETA_L = "THETA_L"
REGIMES = (THETA_S, THETA_L)
PERSISTENT_TARGET = "PERSISTENT_TARGET"
PERSISTENT_POSITIVE = "PERSISTENT_POSITIVE"
REDRAW_AFTER_TWO = "REDRAW_AFTER_TWO"
STRATA = (PERSISTENT_TARGET, PERSISTENT_POSITIVE, REDRAW_AFTER_TWO)
TRIALS = 5
PHYSICAL_HORIZON = 3
DURATIONS = {S: 1, L: 2}
TARGET_HAZARDS = {
    (THETA_S, S): Fraction(9, 10),
    (THETA_S, L): Fraction(1, 10),
    (THETA_L, S): Fraction(1, 10),
    (THETA_L, L): Fraction(9, 10),
}
POSITIVE_HAZARDS = {
    (THETA_S, S): Fraction(1),
    (THETA_S, L): Fraction(0),
    (THETA_L, S): Fraction(0),
    (THETA_L, L): Fraction(1),
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def fraction_string(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def parse_fraction(value: str) -> Fraction:
    return Fraction(value)


def threshold_hit(uniform: Fraction, hazard: Fraction) -> bool:
    if not isinstance(uniform, Fraction) or uniform < 0 or uniform >= 1:
        raise ValueError("uniform must be an exact rational in [0,1)")
    return uniform < hazard


def uniform_for_mark(*, hit: bool, hazard: Fraction) -> Fraction:
    if hazard == 0:
        if hit:
            raise ValueError("cannot construct a hit under zero hazard")
        return Fraction(1, 2)
    if hazard == 1:
        if not hit:
            raise ValueError("cannot construct a miss under unit hazard")
        return Fraction(1, 2)
    return hazard / 2 if hit else (hazard + 1) / 2


def hazard_for(stratum: str, regime: str, period: str) -> Fraction:
    if stratum not in STRATA or regime not in REGIMES or period not in PERIODS:
        raise ValueError("unknown stratum, regime, or period")
    table = POSITIVE_HAZARDS if stratum == PERSISTENT_POSITIVE else TARGET_HAZARDS
    return table[(regime, period)]


@dataclass(frozen=True)
class Generation:
    executor: int
    partner_policy: int
    scheduler: int

    def to_json(self) -> dict[str, int]:
        return {"executor": self.executor, "partner_policy": self.partner_policy, "scheduler": self.scheduler}


@dataclass(frozen=True)
class AcquisitionLedger:
    generation: Generation
    e_s: int = 1
    e_l: int = 1
    n_s: int = 0
    n_l: int = 0
    frozen_d: int | None = None

    def to_json(self) -> dict[str, object]:
        return {
            "generation": self.generation.to_json(),
            "E_S": self.e_s,
            "E_L": self.e_l,
            "N_S": self.n_s,
            "N_L": self.n_l,
            "d": self.frozen_d,
        }

    def to_bytes(self) -> bytes:
        return canonical_bytes(self.to_json())


@dataclass(frozen=True)
class TrialRecord:
    trial: int
    action: str
    regime: str
    uniform: Fraction
    hazard: Fraction
    hit: bool
    duration: int
    physical_auc: int
    phase: str
    ledger_before_sha: str | None
    ledger_after_sha: str | None

    def to_json(self) -> dict[str, object]:
        return {
            "trial": self.trial,
            "action": self.action,
            "regime": self.regime,
            "uniform": fraction_string(self.uniform),
            "hazard": fraction_string(self.hazard),
            "hit": self.hit,
            "duration": self.duration,
            "physical_auc": self.physical_auc,
            "phase": self.phase,
            "ledger_before_sha": self.ledger_before_sha,
            "ledger_after_sha": self.ledger_after_sha,
        }


class EndogenousPaidCountHost:
    """One version-closed five-transition episode."""

    def __init__(self, *, stratum: str, prefix_regime: str, tail_regime: str, generation: Generation) -> None:
        if stratum not in STRATA or prefix_regime not in REGIMES or tail_regime not in REGIMES:
            raise ValueError("unknown host literal")
        if stratum != REDRAW_AFTER_TWO and prefix_regime != tail_regime:
            raise ValueError("persistent strata retain one regime")
        self.stratum = stratum
        self._prefix_regime = prefix_regime
        self._tail_regime = tail_regime
        self._generation = generation
        self._ledger: AcquisitionLedger | None = None
        self._root_action: str | None = None
        self._tail_action: str | None = None
        self._records: list[TrialRecord] = []
        self._root_calls = 0
        self._tail_calls = 0
        self._closed = False

    @property
    def records(self) -> tuple[TrialRecord, ...]:
        return tuple(self._records)

    @property
    def transition_count(self) -> int:
        return len(self._records)

    @property
    def policy_calls(self) -> int:
        return self._root_calls + self._tail_calls

    @property
    def acquisition_auc(self) -> int:
        return sum(row.physical_auc for row in self._records[:2]) if self._root_action == BUY_SL else 0

    @property
    def tail_auc(self) -> int:
        return sum(row.physical_auc for row in self._records[2:]) if self._root_action == BUY_SL else 0

    @property
    def total_auc(self) -> int:
        return sum(row.physical_auc for row in self._records)

    def _require_generation(self, generation: Generation) -> None:
        if generation != self._generation:
            raise ValueError("mixed generation rejected before policy")
        if self._closed:
            raise RuntimeError("episode is closed")

    def root_policy_call(self, controller: Callable[[bytes], str], *, generation: Generation) -> tuple[str, bytes]:
        self._require_generation(generation)
        if self._root_action is not None or self._records:
            raise RuntimeError("root policy must be called exactly once before transitions")
        observation = canonical_bytes({"phase": "ROOT", "remaining_trials": 5})
        action = controller(observation)
        if action not in ROOT_ACTIONS:
            raise ValueError("invalid root action")
        self._root_action = action
        self._root_calls = 1
        if action == BUY_SL:
            self._ledger = AcquisitionLedger(generation=generation)
        return action, observation

    def force_root(self, action: str, *, generation: Generation) -> tuple[str, bytes]:
        return self.root_policy_call(lambda _observation: action, generation=generation)

    def begin_forced_buy_training(self, *, generation: Generation) -> None:
        """Enter the prospectively forced BUY tail-fit intervention.

        This is the sole path without a root policy call.  It exists only for
        the registered tail-fit phase, where BUY is experimental protocol and
        the one counted policy call is the sealed tail-action callback.
        """

        self._require_generation(generation)
        if self._root_action is not None or self._records:
            raise RuntimeError("forced tail fit must begin from a fresh episode")
        self._root_action = BUY_SL
        self._ledger = AcquisitionLedger(generation=generation)

    def _regime_for_trial(self, trial: int) -> str:
        return self._prefix_regime if trial <= 2 else self._tail_regime

    def _append_trial(self, *, action: str, uniform: Fraction, phase: str, generation: Generation) -> TrialRecord:
        self._require_generation(generation)
        trial = len(self._records) + 1
        if not 1 <= trial <= TRIALS:
            raise RuntimeError("five-transition clock exceeded")
        if action not in PERIODS:
            raise ValueError("invalid trial action")
        regime = self._regime_for_trial(trial)
        hazard = hazard_for(self.stratum, regime, action)
        hit = threshold_hit(uniform, hazard)
        before_sha = after_sha = None
        ledger = self._ledger
        if ledger is not None:
            before = ledger.to_bytes()
            if trial == 1:
                if action != S:
                    raise RuntimeError("BUY_SL trial 1 must be S")
                ledger = replace(ledger, n_s=int(hit))
            elif trial == 2:
                if action != L:
                    raise RuntimeError("BUY_SL trial 2 must be L")
                ledger = replace(ledger, n_l=int(hit))
            after = ledger.to_bytes()
            before_sha, after_sha = hashlib.sha256(before).hexdigest(), hashlib.sha256(after).hexdigest()
            self._ledger = ledger
        record = TrialRecord(
            trial=trial,
            action=action,
            regime=regime,
            uniform=uniform,
            hazard=hazard,
            hit=hit,
            duration=DURATIONS[action],
            physical_auc=int(hit) * (2 if action == S else 1),
            phase=phase,
            ledger_before_sha=before_sha,
            ledger_after_sha=after_sha,
        )
        self._records.append(record)
        return record

    def execute_acquisition(self, *, uniforms: tuple[Fraction, Fraction], generation: Generation) -> tuple[TrialRecord, TrialRecord]:
        if self._root_action != BUY_SL or self._records:
            raise RuntimeError("acquisition requires fresh BUY_SL episode")
        return (
            self._append_trial(action=S, uniform=uniforms[0], phase="ACQUISITION", generation=generation),
            self._append_trial(action=L, uniform=uniforms[1], phase="ACQUISITION", generation=generation),
        )

    def freeze_count(self, *, generation: Generation) -> tuple[int, bytes]:
        self._require_generation(generation)
        if self._root_action != BUY_SL or len(self._records) != 2 or self._ledger is None or self._tail_calls:
            raise RuntimeError("count freezes after exactly two acquisition trials")
        if self._ledger.e_s != 1 or self._ledger.e_l != 1:
            raise RuntimeError("acquisition exposures were not precommitted")
        frozen = replace(self._ledger, frozen_d=self._ledger.n_l - self._ledger.n_s)
        if frozen.frozen_d not in (-1, 0, 1):
            raise RuntimeError("count outside protected support")
        self._ledger = frozen
        return int(frozen.frozen_d), frozen.to_bytes()

    def tail_policy_call(self, controller: Callable[[bytes], str], *, visible_d: int, generation: Generation) -> tuple[str, bytes, bytes]:
        self._require_generation(generation)
        if self._root_action != BUY_SL or len(self._records) != 2 or self._ledger is None or self._ledger.frozen_d is None:
            raise RuntimeError("tail policy requires frozen acquisition ledger")
        if self._tail_calls:
            raise RuntimeError("tail policy may be called once")
        observation = canonical_bytes({"phase": "TAIL", "remaining_trials": 3, "d": int(visible_d)})
        before = self._ledger.to_bytes()
        action = controller(observation)
        if action not in PERIODS:
            raise ValueError("invalid tail action")
        after = self._ledger.to_bytes()
        if before != after:
            raise RuntimeError("tail policy mutated ledger")
        self._tail_action = action
        self._tail_calls = 1
        return action, observation, before

    def execute_remaining(self, *, uniforms: tuple[Fraction, ...], generation: Generation, task_reward_placeholder: object | None = None) -> tuple[TrialRecord, ...]:
        self._require_generation(generation)
        _ = task_reward_placeholder
        if self._root_action is None:
            raise RuntimeError("root policy was not called")
        if self._root_action == BUY_SL:
            if len(uniforms) != 3 or len(self._records) != 2 or self._tail_action is None:
                raise RuntimeError("BUY_SL requires three committed tail trials")
            action = self._tail_action
            phase = "TAIL"
        else:
            if len(uniforms) != 5 or self._records:
                raise RuntimeError("immediate commit requires five trials")
            action = S if self._root_action == COMMIT_S else L
            phase = "COMMIT"
        ledger_before = self._ledger.to_bytes() if self._ledger is not None else None
        rows = tuple(self._append_trial(action=action, uniform=u, phase=phase, generation=generation) for u in uniforms)
        if self._ledger is not None and ledger_before != self._ledger.to_bytes():
            raise RuntimeError("tail outcomes or reward mutated acquisition ledger")
        return rows

    def close_episode(self) -> None:
        if len(self._records) != TRIALS:
            raise RuntimeError("only complete five-transition episodes may close")
        self._ledger = None
        self._closed = True


def generation_for_episode(index: int) -> Generation:
    return Generation(index, index, index)
