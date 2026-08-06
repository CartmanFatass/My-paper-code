"""Exactly-weighted crossed evaluation of trained UCOPE policies.

Sequence 03, second measurement pass.  External Pro's ruling
``ALIGNED`` on the first pass
(``local_research/pro_reviews/ucope_training_alignment_v1/40_RAW_RESPONSE.md``,
sha256 ``e8718381…``, VERBATIM_OK) accepted the certificate and the sibling but
rejected three things about how the numbers were produced.  This module answers
all three with one construction.

WHAT PRO REJECTED, AND WHY THIS FIXES IT
----------------------------------------
**1. The blind-ceiling guard was not a validity theorem.**

    The exact blind value 32 is an expectation under the prior, not a pointwise
    maximum for every evaluation sample. The blind oracle earns: 48 in regime S,
    16 in regime L. A finite evaluation block containing more than 50% S episodes
    can therefore have a blind-oracle sample mean above 32 without any policy
    error or leakage.

That is correct and it falsifies the guard as written.  Pro's own remedy is
taken here: *"exact regime-balanced evaluation; crossing every evaluation
ledger/context with both regimes and exact evidence weights."*

Under the crossed estimator the ceiling becomes a real theorem, and per ledger
rather than on average.  With the mix matched, the per-step reward collapses to
the tent ``clip(1 - |e - l|/l, 0, 1)``, so a count-blind policy at belief
``rho = 1/2`` faces, for **every** effort ``e`` in ``(0, 1)``:

    e <= 1/4        f(e) = 8e/3          increasing,  f(1/4) = 2/3
    1/4 < e < 1/2   f(e) = 1 - 4e/3      decreasing,  f(1/4) = 2/3
    e >= 1/2        f(e) <= 1/2

so ``max_e f(e) = 2/3`` exactly, attained at ``e = 1/4``, and no count-blind
policy can exceed ``HORIZON * 2/3 = 32.0`` on any ledger.  The argument is
pointwise in the ledger because the tent collapse is, so the guard applies to
each crossed value and not merely to their mean.  ``blind_ceiling_guard``
enforces it, and unlike its predecessor it actually refuses.

**2. The 83% was not an information-capture fraction.**  Pro decomposed it:

    0.8308 = 1 - (eps_I - eps_B) / 4.5

with optimization regrets ``eps_I = 1.7821`` and ``eps_B = 1.0207``.  It embeds
the blind arm's under-convergence.  Nothing here reports it.  The crossed
estimator removes the *sampling* half of that problem; the *optimization* half
is a property of the trained policies and is reported as regrets, openly.

**3. The training-side SEVERED arm was not a causal ablation.**  Pro:

    They do not contain a causal intervention on the same learned informed
    policy. […] freeze the informed checkpoint and evaluate it twice: same
    weights, actual count versus same weights, count severed.

``within_checkpoint_severance`` is exactly that, on the identical crossed
support.  Pro also ruled explicitly that the training-side SEVERED arm must NOT
be rebuilt to differ from BLIND in a non-information feature -- *"That would make
the control less matched"* -- so it stays as it is and is relabelled a
determinism checksum.

SCOPE
-----
Still a code-side measurement.  The scientific reading belongs to External Pro,
in the existing capability conversation for this direction.
"""

from __future__ import annotations

import hashlib
import pathlib
import statistics
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Any, Sequence

import numpy as np
import torch

from envs.continuous_roster import runtime_capacity as roster_env

from experiments.candidates.ucope import capability_certificate as cc
from experiments.candidates.ucope import paired_training as pt
from experiments.candidates.ucope import regime_roster_env as sibling

RAW_OUTPUT_BINDING = "ucope.crossed_evaluation.v1"

#: The base environment does not reach 1.0 at its own analytic optimum -- it
#: accumulates `served` from per-member float32 products against a float64
#: target aggregate.  Pro accepted this as *"a conservative base-anchored
#: tolerance rather than a formally proved global bound"*, and it is labelled
#: that way here rather than as an exactness claim.
BASE_ANCHORED_TOLERANCE = float(roster_env.HORIZON) * 2.0**-23


# ---------------------------------------------------------------------------
# The crossed support
# ---------------------------------------------------------------------------


def crossed_support() -> tuple[tuple[str, tuple[int, ...], Fraction], ...]:
    """Every (regime, evidence path) cell with its exact rational weight.

    ``PERIODS = 3`` gives 2 regimes x 8 paths = 16 cells whose weights sum to
    exactly 1, checked as a Fraction rather than a float.
    """
    cells = []
    for regime in cc.REGIMES:
        prior = cc.PRIOR_S if regime == cc.S else 1 - cc.PRIOR_S
        positive = cc.EVIDENCE_POSITIVE[regime]
        for bits in product((1, 0), repeat=cc.PERIODS):
            weight = prior
            for bit in bits:
                weight *= positive if bit else (1 - positive)
            cells.append((regime, tuple(bits), weight))
    total = sum(cell[2] for cell in cells)
    if total != Fraction(1):
        raise RuntimeError(f"crossed weights must sum to exactly 1, got {total}")
    return tuple(cells)


CROSSED_SUPPORT = crossed_support()


#: Offset applied to every evaluation ledger id.  ``0`` reproduces the archived
#: runs exactly; ``CLEAN_LEDGER_BASE`` puts the evaluation ids outside any
#: reachable training episode id.  See ``evaluation_support_disjointness``.
DEFAULT_LEDGER_BASE = 0
CLEAN_LEDGER_BASE = 900_000


def evaluation_ledger(
    ledger_id: int, *, ledger_seed: int, ledger_base: int = DEFAULT_LEDGER_BASE
) -> roster_env.CapacityRosterLedger:
    """One evaluation context.  The crossing happens *within* this ledger.

    ``ledger_base`` shifts the ledger id.  It exists because External Pro found
    that the evaluation support was not held out for the first replication seed:
    a ledger is determined by ``(id, master_seed, profile)``, so an evaluation
    ledger coincides with a training episode's ledger whenever the seeds AND the
    ids coincide.  Shifting the ids fixes it for every seed at once, which the
    seed-side fix does not.
    """
    identifier = ledger_base + ledger_id
    return roster_env.make_ledger(
        identifier,
        master_seed=ledger_seed,
        profile=roster_env.TRAIN_PROFILES[identifier % len(roster_env.TRAIN_PROFILES)],
    )


def evaluation_support_disjointness(
    *,
    seeds: Sequence[int],
    ledger_seed: int,
    evaluation_ledgers: int,
    iterations: int,
    episodes_per_iteration: int,
    ledger_base: int = DEFAULT_LEDGER_BASE,
) -> dict[str, Any]:
    """Is the evaluation support held out from training, for every seed?

    External Pro's finding on the 8-seed replication, which this exists to make
    impossible to reproduce silently:

        The first replication seed is 20260806, while the fixed evaluation
        ledger seed is 20260808. run_arm derives regime_seed = seed + 2 and uses
        that same value as the training ledger's master_seed; training episode
        IDs begin at zero. […] Thus, for the first replication, evaluation
        ledgers 0,…,63 are the same ledger contexts encountered during its first
        64 training episodes.

    A training ledger and an evaluation ledger are the same object exactly when
    both the master seed and the id agree, so BOTH conditions are reported.
    Pro named both remedies -- *"A future evaluation seed should be outside every
    training-derived seed root, or evaluation ledger IDs should be outside the
    training episode-ID range"* -- and either one clears the diagnostic.

    This is a diagnostic, not a gate: it is written into the artifact rather
    than raising, because the archived run must stay reproducible under the
    constants it actually used.
    """
    # run_arm consumes seed, seed+1 (generator), seed+2 (regime AND the training
    # ledger master seed) and seed+3 (evidence).
    derived_roots = {int(seed) + offset for seed in seeds for offset in range(4)}
    seed_collision = ledger_seed in derived_roots
    colliding_seeds = [
        int(seed) for seed in seeds if ledger_seed in {int(seed) + o for o in range(4)}
    ]

    training_episode_ids = int(iterations) * int(episodes_per_iteration)
    evaluation_ids = range(ledger_base, ledger_base + int(evaluation_ledgers))
    id_overlap = sorted(
        identifier for identifier in evaluation_ids if identifier < training_episode_ids
    )

    return {
        "ledger_seed": int(ledger_seed),
        "ledger_base": int(ledger_base),
        "training_derived_seed_roots": sorted(derived_roots),
        "ledger_seed_collides_with_a_training_root": bool(seed_collision),
        "colliding_training_seeds": colliding_seeds,
        "training_episode_id_range": [0, training_episode_ids - 1],
        "evaluation_ledger_id_range": [
            evaluation_ids.start,
            evaluation_ids.stop - 1,
        ],
        "overlapping_ledger_ids": id_overlap,
        # Held out iff the two objects cannot coincide: either no shared master
        # seed, or no shared id.
        "evaluation_support_is_held_out_for_every_seed": not (
            seed_collision and id_overlap
        ),
        "remedy_if_not": (
            "either choose a ledger_seed outside training_derived_seed_roots, or "
            f"set ledger_base={CLEAN_LEDGER_BASE} so the evaluation ids sit "
            "outside the training episode-id range; the second is robust to any "
            "seed choice"
        ),
    }


def cell_total(
    policy: pt.EffortPolicy,
    ledger: roster_env.CapacityRosterLedger,
    *,
    arm: str,
    regime: str,
    bits: Sequence[int],
    effort_trace: dict[tuple[int, int], list[float]] | None = None,
) -> float:
    """One deterministic episode in one crossed cell.

    Deterministic throughout: the policy plays its mean action, and the regime
    and evidence are supplied rather than drawn, so this consumes no randomness
    at all.  Two calls with the same arguments are bitwise identical.

    When ``effort_trace`` is supplied, every played effort is recorded against
    the count state it was played at.  That is the on-manifold version of the
    effort readout: it never asks the policy about an input combination the
    environment cannot produce.
    """
    env = sibling.UcopeRegimeRosterEnv(ledger, regime=regime, evidence_bits=bits)
    terminated = False
    while not terminated:
        view = env.observe()
        features = torch.from_numpy(pt.policy_features(view, arm=arm)).unsqueeze(0)
        with torch.no_grad():
            mean, _log_std, _value = policy(features)
        effort = pt._effort_from_action(mean[0])
        if effort_trace is not None:
            key = (int(view.positive_count), int(view.completed_epochs))
            effort_trace.setdefault(key, []).append(effort)
        _reward, terminated, _ = env.step(sibling.uniform_effort_actions(view, effort))
    return env.episode_total()


def crossed_value(
    policy: pt.EffortPolicy,
    ledger: roster_env.CapacityRosterLedger,
    *,
    arm: str,
) -> float:
    """The exactly-weighted expected episode return on one ledger.

    This is an expectation over the *whole* regime/evidence support, not a
    sample mean over drawn episodes.  The regime draw -- the entire source of
    the near-bimodal ~16 episode-total standard deviation -- is integrated out
    rather than cancelled by pairing.
    """
    return float(
        sum(
            float(weight) * cell_total(policy, ledger, arm=arm, regime=regime, bits=bits)
            for regime, bits, weight in CROSSED_SUPPORT
        )
    )


@dataclass(frozen=True)
class CrossedReadout:
    arm: str
    per_ledger: tuple[float, ...]

    @property
    def mean(self) -> float:
        return statistics.fmean(self.per_ledger)

    @property
    def standard_error(self) -> float:
        if len(self.per_ledger) < 2:
            return float("inf")
        return statistics.stdev(self.per_ledger) / len(self.per_ledger) ** 0.5


def crossed_readout(
    policy: pt.EffortPolicy,
    *,
    arm: str,
    ledgers: Sequence[roster_env.CapacityRosterLedger],
) -> CrossedReadout:
    return CrossedReadout(
        arm=arm,
        per_ledger=tuple(crossed_value(policy, ledger, arm=arm) for ledger in ledgers),
    )


# ---------------------------------------------------------------------------
# The guard that replaces the falsified one
# ---------------------------------------------------------------------------


def blind_ceiling_guard(readout: CrossedReadout) -> dict[str, object]:
    """A real refusal, per ledger, not a heuristic on a sample mean.

    Because each crossed value is an exact expectation on its ledger and no
    count-blind policy can exceed ``2/3`` per step on any ledger, a crossed
    value above ``32 + BASE_ANCHORED_TOLERANCE`` cannot be under-sampling.  It
    means the count-blind arm read something it should not have, or the
    evaluation is wrong.  Either way no comparison from the run is readable.
    """
    ceiling = pt.BLIND_OPTIMUM
    breaches = tuple(
        index
        for index, value in enumerate(readout.per_ledger)
        if value > ceiling + BASE_ANCHORED_TOLERANCE
    )
    return {
        "certified_blind_ceiling": ceiling,
        "tolerance": BASE_ANCHORED_TOLERANCE,
        "max_crossed_value": max(readout.per_ledger) if readout.per_ledger else 0.0,
        "breaching_ledger_indices": breaches,
        "passed": not breaches,
    }


# ---------------------------------------------------------------------------
# Pro's mechanistic intervention
# ---------------------------------------------------------------------------


def within_checkpoint_severance(
    policy: pt.EffortPolicy,
    *,
    ledgers: Sequence[roster_env.CapacityRosterLedger],
) -> dict[str, object]:
    """Same weights, actual count vs count severed, on identical support.

    This is the intervention the first pass lacked.  The training-side SEVERED
    arm compared two *separately trained* policies; this compares one frozen
    policy against itself with only its count channels zeroed, so the difference
    cannot be an optimisation artefact.  Every other input -- elapsed epoch,
    time, roster, target mix -- is preserved, because `policy_features` differs
    between the two arms in the two count channels and nowhere else.
    """
    informed = crossed_readout(policy, arm=pt.INFORMED, ledgers=ledgers)
    severed = crossed_readout(policy, arm=pt.SEVERED, ledgers=ledgers)
    differences = [a - b for a, b in zip(informed.per_ledger, severed.per_ledger)]
    mean = statistics.fmean(differences) if differences else 0.0
    error = (
        statistics.stdev(differences) / len(differences) ** 0.5
        if len(differences) > 1
        else float("inf")
    )
    return {
        "informed_crossed_mean": informed.mean,
        "severed_crossed_mean": severed.mean,
        "paired_difference_mean": mean,
        "paired_difference_standard_error": error,
        "t": (mean / error) if error not in (0.0, float("inf")) else float("nan"),
        "per_ledger_difference": tuple(differences),
    }


def effort_readout(
    policy: pt.EffortPolicy, *, context: Sequence[float] | None = None
) -> dict[str, float]:
    """Learned mean effort at each reachable count state, other inputs fixed.

    Pro: *"report the learned mean effort at each reachable (positive count,
    completed epochs) state while holding all other inputs fixed."*

    One channel cannot be held fixed, and getting this wrong produced a
    misleading table on the first attempt.  ``completed_epochs`` *determines*
    elapsed time -- the count state ``(0, 0)`` only ever occurs in the first
    epoch -- so freezing the time channel at a single value asks the policy
    about input combinations the environment can never present, and the answer
    at those points says nothing about behaviour.  The time channel is therefore
    set to each epoch's own midpoint, and the remaining three are frozen.

    ``realized_effort_readout`` is the on-manifold companion and should be
    preferred when the two disagree.
    """
    fixed = (
        (0.5, 0.5, 1.0) if context is None else tuple(float(v) for v in context)
    )
    table: dict[str, float] = {}
    for completed in range(cc.PERIODS):
        # The epoch's midpoint in normalized episode time.
        epoch_time = (completed + 0.5) * sibling.EPOCH_LENGTH / roster_env.HORIZON
        for positive in range(completed + 1):
            features = np.asarray(
                (
                    positive / sibling.PERIODS,
                    completed / sibling.PERIODS,
                    fixed[0],
                    fixed[1],
                    epoch_time,
                    fixed[2],
                ),
                dtype=np.float32,
            )
            with torch.no_grad():
                mean, _log_std, _value = policy(torch.from_numpy(features).unsqueeze(0))
            table[f"positive={positive},completed={completed}"] = pt._effort_from_action(
                mean[0]
            )
    return table


def realized_effort_readout(
    policy: pt.EffortPolicy,
    *,
    ledgers: Sequence[roster_env.CapacityRosterLedger],
    arm: str = pt.INFORMED,
) -> dict[str, dict[str, float]]:
    """Mean effort actually played at each count state, on the real manifold.

    Every input combination here was produced by the environment, so no row
    depends on a synthetic context choice.  This is the readout that supports a
    statement about what the policy does; ``effort_readout`` is the controlled
    probe Pro asked for alongside it.
    """
    trace: dict[tuple[int, int], list[float]] = {}
    for ledger in ledgers:
        for regime, bits, _weight in CROSSED_SUPPORT:
            cell_total(
                policy, ledger, arm=arm, regime=regime, bits=bits, effort_trace=trace
            )
    return {
        f"positive={positive},completed={completed}": {
            "mean_effort": statistics.fmean(efforts),
            "steps": len(efforts),
            "bayes_optimal_effort": float(
                cc.optimal_effort(cc.posterior_s(positive, completed))
            ),
        }
        for (positive, completed), efforts in sorted(trace.items())
    }


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

_PROVENANCE_SOURCES = (
    "experiments/candidates/ucope/capability_certificate.py",
    "experiments/candidates/ucope/regime_roster_env.py",
    "experiments/candidates/ucope/regime_conformance.py",
    "experiments/candidates/ucope/paired_training.py",
    "experiments/candidates/ucope/crossed_evaluation.py",
    "envs/continuous_roster/runtime_capacity.py",
)


def _repository_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]


def checkpoint_digest(policy: torch.nn.Module) -> str:
    """SHA-256 over the trained weights, so a reported number names a model."""
    hasher = hashlib.sha256()
    for name, tensor in sorted(policy.state_dict().items()):
        array = np.ascontiguousarray(tensor.detach().cpu().numpy())
        hasher.update(name.encode("utf-8"))
        hasher.update(str(array.dtype).encode("utf-8"))
        hasher.update(str(array.shape).encode("utf-8"))
        hasher.update(array.tobytes())
    return hasher.hexdigest()


def provenance(*, run_arguments: dict[str, object]) -> dict[str, object]:
    """Bind the artifact to its execution.

    Pro: *"I cannot independently authenticate their execution provenance from
    these files alone."*  Everything needed to re-derive the run travels with
    the result: commit, arguments, seeds, source digests and versions.  The
    source digests are the durable half -- they hold even if the commit is
    unavailable.
    """
    root = _repository_root()

    def _git(*arguments: str) -> str | None:
        try:
            return subprocess.run(
                ["git", *arguments],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            return None

    head = _git("rev-parse", "HEAD")
    commit = head.strip() if head is not None else "UNAVAILABLE"
    # A commit hash taken from a dirty tree authenticates nothing, so say so.
    # The source digests below are the binding that survives either way.
    status = _git("status", "--porcelain", "--", *_PROVENANCE_SOURCES)
    dirty = None if status is None else bool(status.strip())
    digests = {}
    for relative in _PROVENANCE_SOURCES:
        path = root / relative
        # LF-normalized: this worktree runs core.autocrlf=true, so raw bytes
        # would digest differently on a fresh clone.
        digests[relative] = hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
    return {
        "source_commit": commit,
        "source_tree_dirty": dirty,
        "commit_authenticates_the_run": commit != "UNAVAILABLE" and dirty is False,
        "run_arguments": dict(run_arguments),
        "source_digests": digests,
        "numpy_version": np.__version__,
        "torch_version": torch.__version__,
    }


# ---------------------------------------------------------------------------
# The registered experiment
# ---------------------------------------------------------------------------

#: The training budget of the REGISTERED experiment -- the one the archived
#: artifact reports and the one every replication must match.
#:
#: This lives here rather than in a caller's argument list because it already
#: caused a real defect: the archived run was launched with ``iterations=300``
#: while ``run_arm``'s own default is 120, so the first cross-seed replication
#: silently trained every arm to 40% of the registered budget.  Its arms landed
#: at optimization regrets of 5.4 against the registered run's 0.58, and the
#: resulting across-seed spread described the short budget rather than the seed.
#: A budget that is only ever supplied by the caller is a budget two callers can
#: disagree about; naming it makes the disagreement impossible.
REGISTERED_TRAINING: dict[str, int] = {
    "iterations": 300,
    "episodes_per_iteration": 16,
    "evaluation_episodes": 64,
}


def run_registered_experiment(
    *,
    evaluation_ledgers: int = 64,
    ledger_seed: int = 20_260_808,
    ledger_base: int = DEFAULT_LEDGER_BASE,
    **training_kwargs,
) -> dict[str, object]:
    """Train the three arms, then evaluate on the exactly-weighted support.

    Any training argument not supplied comes from ``REGISTERED_TRAINING``, so
    calling this with only a seed reproduces the registered budget rather than
    ``run_arm``'s smaller defaults.
    """
    training_kwargs = {**REGISTERED_TRAINING, **training_kwargs}
    runs = {arm: pt.run_arm(arm, **training_kwargs) for arm in pt.ARMS}
    ledgers = [
        evaluation_ledger(index, ledger_seed=ledger_seed, ledger_base=ledger_base)
        for index in range(evaluation_ledgers)
    ]
    disjointness = evaluation_support_disjointness(
        seeds=(training_kwargs.get("seed", 20_260_806),),
        ledger_seed=ledger_seed,
        evaluation_ledgers=evaluation_ledgers,
        iterations=training_kwargs["iterations"],
        episodes_per_iteration=training_kwargs["episodes_per_iteration"],
        ledger_base=ledger_base,
    )

    readouts = {
        arm: crossed_readout(run.policy, arm=arm, ledgers=ledgers)
        for arm, run in runs.items()
    }
    guard = blind_ceiling_guard(readouts[pt.BLIND])

    informed_minus_blind = [
        a - b
        for a, b in zip(readouts[pt.INFORMED].per_ledger, readouts[pt.BLIND].per_ledger)
    ]
    contrast_mean = statistics.fmean(informed_minus_blind)
    contrast_error = (
        statistics.stdev(informed_minus_blind) / len(informed_minus_blind) ** 0.5
        if len(informed_minus_blind) > 1
        else float("inf")
    )

    report: dict[str, object] = {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "provenance": provenance(
            run_arguments={
                "evaluation_ledgers": evaluation_ledgers,
                "ledger_seed": ledger_seed,
                "ledger_base": ledger_base,
                **training_kwargs,
            }
        ),
        # Pro §"Evaluation support is not held out for the first seed": travels
        # with every artifact so the caveat can never be lost from the numbers.
        "evaluation_support_disjointness": disjointness,
        "blind_ceiling_guard": guard,
        "certified_informed_optimum": pt.INFORMED_OPTIMUM,
        "certified_blind_optimum": pt.BLIND_OPTIMUM,
        "crossed_support_cells": len(CROSSED_SUPPORT),
        "arms": {
            arm: {
                "crossed_mean": readout.mean,
                "crossed_standard_error": readout.standard_error,
                "optimization_regret": (
                    pt.INFORMED_OPTIMUM if arm == pt.INFORMED else pt.BLIND_OPTIMUM
                )
                - readout.mean,
                "checkpoint_digest": checkpoint_digest(runs[arm].policy),
                "per_ledger": readout.per_ledger,
            }
            for arm, readout in readouts.items()
        },
        "between_arm_contrast": {
            "estimand": (
                "effect of the complete finite-budget training protocol: "
                "count-enabled training minus count-disabled training"
            ),
            "mean": contrast_mean,
            "standard_error": contrast_error,
            "note": (
                "Two separately trained policies with different optimization "
                "regrets. This is not the oracle information value, and no "
                "fraction of the certified gap is reported from it."
            ),
        },
        "within_checkpoint_severance": within_checkpoint_severance(
            runs[pt.INFORMED].policy, ledgers=ledgers
        ),
        "training_side_severed_arm": {
            "status": (
                "Determinism checksum only. BLIND and SEVERED receive identical "
                "(0.0, 0.0) count channels under shared seeds, so they are the "
                "same computation and their equality is an implementation "
                "check, not a replicated null. Pro ruled it must NOT be rebuilt "
                "to differ from BLIND in a non-information feature."
            ),
            # Demonstrated rather than asserted: if the two arms are literally
            # the same computation, their trained weights are bit-identical, so
            # the digests must match.  This converts Pro's argument into a
            # mechanical check that would fail if the arms ever diverged.
            "checkpoints_are_bit_identical": (
                checkpoint_digest(runs[pt.BLIND].policy)
                == checkpoint_digest(runs[pt.SEVERED].policy)
            ),
        },
        "effort_readout_controlled_probe": effort_readout(runs[pt.INFORMED].policy),
        "effort_readout_realized": realized_effort_readout(
            runs[pt.INFORMED].policy, ledgers=ledgers
        ),
        "checkpoints": {
            arm: {
                name: tensor.detach().cpu().numpy().tolist()
                for name, tensor in run.policy.state_dict().items()
            }
            for arm, run in runs.items()
        },
        "scope": (
            "Code-side measurement. Scientific interpretation belongs to "
            "External Pro in the existing capability conversation."
        ),
    }
    if not guard["passed"]:
        report["terminal"] = "UCOPE_MEASUREMENT_REFUSED"
        report["refusal"] = (
            "A count-blind policy exceeded its certified per-ledger ceiling on "
            f"{len(guard['breaching_ledger_indices'])} ledgers. No comparison "
            "from this run is readable."
        )
        for arm in report["arms"]:
            report["arms"][arm].pop("crossed_mean", None)
        report.pop("between_arm_contrast", None)
        report.pop("within_checkpoint_severance", None)
    else:
        report["terminal"] = "UCOPE_MEASUREMENT_ADMISSIBLE"
    return report


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(run_registered_experiment(), indent=2, default=str))
