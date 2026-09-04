"""Version-closed five-trial real host for UCOPE-B1.

The host owns environment dynamics and the immutable within-block count ledger.
It deliberately exposes no latent regime, raw prefix history, identity, or
version token to a controller.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
import json
from typing import Callable


S = "S"
L = "L"
PERIODS = (S, L)
THETA_S = "THETA_S"
THETA_L = "THETA_L"
REGIMES = (THETA_S, THETA_L)
PERSISTENT = "PERSISTENT"
TRIAL5_REDRAW = "TRIAL5_REDRAW"
STRATA = (PERSISTENT, TRIAL5_REDRAW)
PREFIX_PERIODS = (S, S, L, L)
PREFIX_CELLS = ("c1", "c2", "c1", "c2")
HORIZON = 3
DURATIONS = {S: 1, L: 2}
HAZARDS = {
    (THETA_S, S): Fraction(9, 10),
    (THETA_S, L): Fraction(1, 10),
    (THETA_L, S): Fraction(1, 10),
    (THETA_L, L): Fraction(9, 10),
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


@dataclass(frozen=True)
class Generation:
    executor: int
    partner_policy: int
    scheduler: int

    def to_json(self) -> dict[str, int]:
        return {
            "executor": int(self.executor),
            "partner_policy": int(self.partner_policy),
            "scheduler": int(self.scheduler),
        }


@dataclass(frozen=True)
class CountLedger:
    generation: Generation
    e_s: int = 2
    e_l: int = 2
    n_s: int = 0
    n_l: int = 0
    frozen_d: int | None = None

    def to_json(self) -> dict[str, object]:
        return {
            "generation": self.generation.to_json(),
            "E_S": int(self.e_s),
            "E_L": int(self.e_l),
            "N_S": int(self.n_s),
            "N_L": int(self.n_l),
            "d": self.frozen_d,
        }

    def to_bytes(self) -> bytes:
        return canonical_bytes(self.to_json())


@dataclass(frozen=True)
class TrialRecord:
    trial: int
    cell: str
    period: str
    regime: str
    uniform: Fraction
    hazard: Fraction
    hit: bool
    duration: int
    physical_auc: int
    ledger_before_sha: str
    ledger_after_sha: str

    def to_json(self) -> dict[str, object]:
        return {
            "trial": self.trial,
            "cell": self.cell,
            "period": self.period,
            "regime": self.regime,
            "uniform": fraction_string(self.uniform),
            "hazard": fraction_string(self.hazard),
            "hit": self.hit,
            "duration": self.duration,
            "physical_auc": self.physical_auc,
            "ledger_before_sha": self.ledger_before_sha,
            "ledger_after_sha": self.ledger_after_sha,
        }


def fraction_string(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _sha(value: bytes) -> str:
    import hashlib

    return hashlib.sha256(value).hexdigest()


class PersistentCountStateHost:
    """One stateful five-transition block with a version-closed prefix ledger."""

    def __init__(
        self,
        *,
        stratum: str,
        prefix_regime: str,
        trial5_regime: str,
        generation: Generation,
    ) -> None:
        if stratum not in STRATA:
            raise ValueError("unknown stratum")
        if prefix_regime not in REGIMES or trial5_regime not in REGIMES:
            raise ValueError("unknown regime")
        if stratum == PERSISTENT and trial5_regime != prefix_regime:
            raise ValueError("persistent blocks retain one regime")
        self.stratum = stratum
        self._prefix_regime = prefix_regime
        self._trial5_regime = trial5_regime
        self._generation = generation
        self._ledger: CountLedger | None = CountLedger(generation=generation)
        self._records: list[TrialRecord] = []
        self._next_trial = 1
        self._policy_called = False
        self._closed = False

    @property
    def transition_count(self) -> int:
        return len(self._records)

    @property
    def records(self) -> tuple[TrialRecord, ...]:
        return tuple(self._records)

    def _require_generation(self, generation: Generation) -> CountLedger:
        if generation != self._generation:
            raise ValueError("mixed or mid-block generation rejected before policy")
        if self._closed or self._ledger is None:
            raise RuntimeError("block ledger is closed")
        return self._ledger

    def step_prefix(self, *, uniform: Fraction, generation: Generation) -> TrialRecord:
        ledger = self._require_generation(generation)
        if not 1 <= self._next_trial <= 4:
            raise RuntimeError("prefix transition out of order")
        trial = self._next_trial
        period = PREFIX_PERIODS[trial - 1]
        hazard = HAZARDS[(self._prefix_regime, period)]
        hit = threshold_hit(uniform, hazard)
        before = ledger.to_bytes()
        if period == S:
            updated = replace(ledger, n_s=ledger.n_s + int(hit))
        else:
            updated = replace(ledger, n_l=ledger.n_l + int(hit))
        after = updated.to_bytes()
        record = TrialRecord(
            trial=trial,
            cell=PREFIX_CELLS[trial - 1],
            period=period,
            regime=self._prefix_regime,
            uniform=uniform,
            hazard=hazard,
            hit=hit,
            duration=DURATIONS[period],
            physical_auc=0,
            ledger_before_sha=_sha(before),
            ledger_after_sha=_sha(after),
        )
        self._ledger = updated
        self._records.append(record)
        self._next_trial += 1
        return record

    def freeze_count(self, *, generation: Generation) -> tuple[int, bytes]:
        ledger = self._require_generation(generation)
        if self._next_trial != 5 or self._policy_called:
            raise RuntimeError("count must freeze exactly before trial-5 policy")
        if ledger.e_s != 2 or ledger.e_l != 2:
            raise RuntimeError("prefix exposures were not precommitted")
        frozen = replace(ledger, frozen_d=ledger.n_l - ledger.n_s)
        if frozen.frozen_d not in (-2, -1, 0, 1, 2):
            raise RuntimeError("frozen count state is outside support")
        self._ledger = frozen
        return int(frozen.frozen_d), frozen.to_bytes()

    def policy_call(
        self,
        controller: Callable[[int], str],
        *,
        visible_d: int,
        generation: Generation,
    ) -> tuple[str, bytes, bytes]:
        ledger = self._require_generation(generation)
        if self._next_trial != 5 or ledger.frozen_d is None or self._policy_called:
            raise RuntimeError("trial-5 policy call requires one frozen ledger")
        before = ledger.to_bytes()
        action = controller(int(visible_d))
        if action not in PERIODS:
            raise ValueError("controller returned an invalid period")
        self._policy_called = True
        after = self._require_generation(generation).to_bytes()
        if before != after:
            raise RuntimeError("policy call mutated ledger bytes")
        return action, before, after

    def step_trial5(
        self,
        *,
        action: str,
        uniform: Fraction,
        generation: Generation,
        task_reward_placeholder: object | None = None,
    ) -> TrialRecord:
        ledger = self._require_generation(generation)
        if self._next_trial != 5 or not self._policy_called or ledger.frozen_d is None:
            raise RuntimeError("trial-5 transition out of order")
        if action not in PERIODS:
            raise ValueError("invalid trial-5 action")
        before = ledger.to_bytes()
        hazard = HAZARDS[(self._trial5_regime, action)]
        hit = threshold_hit(uniform, hazard)
        auc = int(hit) * (2 if action == S else 1)
        # The placeholder is accepted solely to prove that it has no ledger path.
        _ = task_reward_placeholder
        after = self._require_generation(generation).to_bytes()
        if before != after:
            raise RuntimeError("trial-5 outcome or reward mutated ledger bytes")
        record = TrialRecord(
            trial=5,
            cell="c1",
            period=action,
            regime=self._trial5_regime,
            uniform=uniform,
            hazard=hazard,
            hit=hit,
            duration=DURATIONS[action],
            physical_auc=auc,
            ledger_before_sha=_sha(before),
            ledger_after_sha=_sha(after),
        )
        self._records.append(record)
        self._next_trial = 6
        return record

    def close_block(self) -> None:
        if self._next_trial != 6 or len(self._records) != 5:
            raise RuntimeError("only a complete five-transition block may close")
        self._ledger = None
        self._closed = True


def threshold_hit(uniform: Fraction, hazard: Fraction) -> bool:
    if not isinstance(uniform, Fraction) or uniform < 0 or uniform >= 1:
        raise ValueError("uniform must be an exact rational in [0,1)")
    return uniform < hazard


def uniform_for_mark(*, hit: bool, hazard: Fraction) -> Fraction:
    """Return an interior uniform that generates the requested mark normally."""

    return hazard / 2 if hit else (hazard + 1) / 2


def history_probability(history: tuple[int, int, int, int], regime: str) -> Fraction:
    if len(history) != 4 or any(bit not in (0, 1) for bit in history):
        raise ValueError("history must contain four binary marks")
    value = Fraction(1)
    for bit, period in zip(history, PREFIX_PERIODS):
        hazard = HAZARDS[(regime, period)]
        value *= hazard if bit else 1 - hazard
    return value


def generation_for_block(block: int) -> Generation:
    generation = int(block)
    return Generation(generation, generation, generation)
