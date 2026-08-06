"""Cross-seed replication of the UCOPE count-information contrast.

External Pro closed the alignment review with `ALIGNED` and named exactly one
statistical gap:

    it does not yet establish that PPO reliably discovers the mechanism across
    initializations

The single-seed artifact reports a between-arm contrast of 4.4730 +- 0.0035.
That standard error is a *within-run* precision figure computed over evaluation
ledgers with the trained weights held fixed; it describes how precisely this
one pair of checkpoints was measured and says nothing at all about how much the
result would move under a different training seed.  Reporting it as though it
bounded across-seed variability would be the same class of error as the ceiling
guard Pro falsified: a number that is correct about one thing being read as
though it settled another.

So this module re-runs the whole registered experiment at several training
seeds and **treats the seed as the unit of analysis**.  With ``n`` seeds the
across-seed interval has ``n - 1`` degrees of freedom, and pooling the
``64 * n`` per-ledger values would be wrong -- ledgers within a seed share one
set of weights and are not independent replications of training.

What varies and what does not
-----------------------------

``paired_training.run_arm`` derives the episode stream from the training seed
(``regime_seed = seed + 2``, ``evidence_seed = seed + 3``), so changing the seed
changes the policy initialization *and* the training episode stream together.
This module therefore replicates over the **training seed**, not over
initialization alone; the two factors are not decomposed here.  Whether Pro
wants that decomposition (hold the stream, vary only ``torch.manual_seed``) is
a design question for the capability conversation, not one to settle locally.

The *evaluation* support is deliberately held fixed: every replication is scored
on the same ``ledger_seed`` and the same exactly-weighted crossed support, so
per-seed contrasts are measured against one common yardstick and the spread
across seeds is training variability rather than evaluation noise.

The reliability statistic
-------------------------

"Discovers the mechanism" is sharper than "has a positive contrast".  The
certified optimum is a *switching* rule with two arms, 1/4 and 3/4, so the
mechanism question is whether the learned policy lands on the correct side of
the switch at every reachable count state.  That classification needs no
tolerance to be invented for it -- which matters, because a tolerance chosen
after seeing the numbers is a gate chosen to be passed.  The distance to the
Bayes effort is reported alongside as a descriptive quantity only.
"""

from __future__ import annotations

import hashlib
import math
import statistics
import subprocess
from dataclasses import dataclass
from typing import Sequence

from experiments.candidates.ucope import capability_certificate as cc
from experiments.candidates.ucope import crossed_evaluation as ce
from experiments.candidates.ucope import paired_training as pt


RAW_OUTPUT_BINDING = "ucope.cross_seed.v1"

#: Training seeds for the replication.  Spaced by 1000 because ``run_arm``
#: consumes ``seed + 1``, ``seed + 2`` and ``seed + 3`` as the torch generator,
#: regime and evidence seeds -- adjacent seeds would hand one replication's
#: evidence stream to the next replication's regime stream.  The first entry is
#: the seed of the already-archived single-seed artifact, so that run is one of
#: the replications rather than a separate claim.
REPLICATION_SEEDS = (
    20_260_806,
    20_261_806,
    20_262_806,
    20_263_806,
    20_264_806,
    20_265_806,
    20_266_806,
    20_267_806,
)

#: The switch point of the certified optimal rule.  Both certified efforts
#: (1/4 and 3/4) sit on opposite sides of it, so "which side" is a property of
#: the rule and not a threshold chosen for this analysis.
SWITCH_POINT = 0.5

#: This module's own path, relative to the repository root.
_SELF_SOURCE = "experiments/candidates/ucope/cross_seed.py"


def provenance(*, run_arguments: dict[str, object]) -> dict[str, object]:
    """The single-seed provenance record, extended with this module's digest.

    ``crossed_evaluation._PROVENANCE_SOURCES`` is deliberately left alone: it
    is the source set of the *registered single-seed experiment*, and adding a
    file to it would silently change the digest set that the archived v3
    artifact is compared against.  The replication adds its own digest instead.
    """
    record = ce.provenance(run_arguments=run_arguments)
    root = ce._repository_root()
    path = root / _SELF_SOURCE
    record["source_digests"] = {
        **record["source_digests"],
        # LF-normalized, matching the convention in crossed_evaluation.
        _SELF_SOURCE: hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
    }
    # The inherited dirtiness flag was computed over the single-seed source set
    # only, so an uncommitted edit to THIS file would have been reported as a
    # clean tree -- the same defect the flag exists to prevent.
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", _SELF_SOURCE],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        ).stdout
        self_dirty: bool | None = bool(status.strip())
    except (OSError, subprocess.SubprocessError):
        self_dirty = None

    inherited = record["source_tree_dirty"]
    if inherited is None or self_dirty is None:
        record["source_tree_dirty"] = None
    else:
        record["source_tree_dirty"] = bool(inherited or self_dirty)
    record["commit_authenticates_the_run"] = (
        record["source_commit"] != "UNAVAILABLE"
        and record["source_tree_dirty"] is False
    )
    return record


@dataclass(frozen=True)
class SeedResult:
    seed: int
    terminal: str
    guard_passed: bool
    informed_mean: float
    blind_mean: float
    contrast: float
    within_run_contrast_standard_error: float
    severance: float
    informed_regret: float
    blind_regret: float
    severed_is_bit_identical_to_blind: bool
    state_conditional_mean_correct_at_every_state: bool
    incorrect_states: tuple[str, ...]
    maximum_absolute_deviation_from_bayes: float
    checkpoint_digests: dict[str, str]


def classify_switching_rule(
    realized_readout: dict[str, dict[str, float]],
) -> dict[str, object]:
    """Is the STATE-CONDITIONAL MEAN effort on the correct side of the switch?

    ``realized_readout`` rows carry the mean effort actually played at a count
    state and that state's certified Bayes-optimal effort.  A row is correct
    when both fall on the same side of ``SWITCH_POINT``.

    The word "mean" is load-bearing, and the first version of this docstring
    dropped it.  External Pro:

        The implementation first averages all played efforts associated with a
        count state and then classifies that state-conditional mean relative to
        the action midpoint. It does not check that every individual
        ledger/time/context realization remained on the correct side. […]
        Admissible: "the on-manifold mean effort at every reachable count state
        was on the correct side." Not yet admissible: "every action at every
        reachable context was on the correct side."

    Per-instance coverage would need the minimum/maximum over played efforts, or
    the fraction of individual efforts on the Bayes-correct side, neither of
    which this computes.  The returned keys are named for what is measured.
    """
    incorrect: list[str] = []
    deviations: list[float] = []
    for state, row in realized_readout.items():
        played = float(row["mean_effort"])
        bayes = float(row["bayes_optimal_effort"])
        deviations.append(abs(played - bayes))
        if (played < SWITCH_POINT) != (bayes < SWITCH_POINT):
            incorrect.append(state)
    return {
        "state_conditional_mean_correct_at_every_state": not incorrect,
        "incorrect_states": tuple(incorrect),
        "states_checked": len(realized_readout),
        "maximum_absolute_deviation_from_bayes": max(deviations) if deviations else 0.0,
        "measures": (
            "the side of the switch point taken by the MEAN effort at each count "
            "state, not per-instance coverage over ledgers, times or contexts"
        ),
    }


def _summarize_seed(seed: int, report: dict[str, object]) -> SeedResult:
    arms = report["arms"]
    classification = classify_switching_rule(report["effort_readout_realized"])
    admissible = report["terminal"] == "UCOPE_MEASUREMENT_ADMISSIBLE"
    contrast = report.get("between_arm_contrast", {})
    severance = report.get("within_checkpoint_severance", {})
    return SeedResult(
        seed=seed,
        terminal=str(report["terminal"]),
        guard_passed=bool(report["blind_ceiling_guard"]["passed"]),
        informed_mean=float(arms[pt.INFORMED]["crossed_mean"]) if admissible else math.nan,
        blind_mean=float(arms[pt.BLIND]["crossed_mean"]) if admissible else math.nan,
        contrast=float(contrast.get("mean", math.nan)),
        within_run_contrast_standard_error=float(
            contrast.get("standard_error", math.nan)
        ),
        severance=float(severance.get("paired_difference_mean", math.nan)),
        informed_regret=float(arms[pt.INFORMED]["optimization_regret"]),
        blind_regret=float(arms[pt.BLIND]["optimization_regret"]),
        severed_is_bit_identical_to_blind=bool(
            report["training_side_severed_arm"]["checkpoints_are_bit_identical"]
        ),
        state_conditional_mean_correct_at_every_state=bool(
            classification["state_conditional_mean_correct_at_every_state"]
        ),
        incorrect_states=tuple(classification["incorrect_states"]),
        maximum_absolute_deviation_from_bayes=float(
            classification["maximum_absolute_deviation_from_bayes"]
        ),
        checkpoint_digests={
            arm: str(row["checkpoint_digest"]) for arm, row in arms.items()
        },
    )


def across_seed_summary(values: Sequence[float]) -> dict[str, float | int]:
    """Seed-level summary.  ``n`` is the number of SEEDS, never the ledgers.

    A 95% interval is reported from the Student-t critical value at ``n - 1``
    degrees of freedom rather than 1.96, because at these sample sizes the
    normal approximation is optimistic by a wide margin (t(.975, 7) = 2.365).
    """
    count = len(values)
    mean = statistics.fmean(values)
    if count < 2:
        return {
            "seeds": count,
            "mean": mean,
            "standard_deviation": math.nan,
            "standard_error": math.nan,
            "degrees_of_freedom": 0,
            "half_width_95": math.nan,
            "minimum": mean,
            "maximum": mean,
        }
    deviation = statistics.stdev(values)
    error = deviation / math.sqrt(count)
    # t(0.975, df) for the small df this design can reach.  A table rather than
    # a distribution call keeps the dependency surface at numpy + torch.
    critical = {
        1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447,
        7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179,
        13: 2.160, 14: 2.145, 15: 2.131,
    }.get(count - 1, 1.96)
    return {
        "seeds": count,
        "mean": mean,
        "standard_deviation": deviation,
        "standard_error": error,
        "degrees_of_freedom": count - 1,
        "t_critical_975": critical,
        "half_width_95": critical * error,
        "minimum": min(values),
        "maximum": max(values),
    }


def run_replication(
    *,
    seeds: Sequence[int] = REPLICATION_SEEDS,
    evaluation_ledgers: int = 64,
    ledger_seed: int = 20_260_808,
    ledger_base: int = ce.DEFAULT_LEDGER_BASE,
    **training_kwargs,
) -> dict[str, object]:
    """Run the registered experiment once per training seed and summarize.

    Training arguments not supplied fall through to
    ``crossed_evaluation.REGISTERED_TRAINING``, so a replication trains to the
    same budget as the archived single-seed run.  The first version of this
    module did not, and every arm was trained to 40% of the registered budget;
    the across-seed spread it produced was a statement about the short budget,
    not about the seed.  ``run_arguments`` in the artifact records the budget
    actually used, so the two can always be compared after the fact.
    """
    if len(set(seeds)) != len(seeds):
        raise ValueError("replication seeds must be distinct")
    for left in seeds:
        for right in seeds:
            if left != right and abs(left - right) <= 3:
                raise ValueError(
                    f"seeds {left} and {right} are within the derived-seed span "
                    "(seed+1..seed+3); their streams would overlap"
                )

    # Resolved here rather than left to the callee, so the artifact records the
    # budget that actually ran instead of the (possibly empty) override set.
    training_kwargs = {**ce.REGISTERED_TRAINING, **training_kwargs}

    # Pro found that the evaluation support was NOT held out for seed 20260806:
    # run_arm uses regime_seed = seed + 2 as the training ledger's master seed,
    # and 20260806 + 2 == 20260808 == ledger_seed, while training episode ids
    # start at 0 and the evaluation ledger ids are 0..63.  Reported rather than
    # raised, because the archived run must stay reproducible under the exact
    # constants it used; `ledger_base=ce.CLEAN_LEDGER_BASE` clears it for every
    # seed at once.
    disjointness = ce.evaluation_support_disjointness(
        seeds=seeds,
        ledger_seed=ledger_seed,
        evaluation_ledgers=evaluation_ledgers,
        iterations=training_kwargs["iterations"],
        episodes_per_iteration=training_kwargs["episodes_per_iteration"],
        ledger_base=ledger_base,
    )

    results: list[SeedResult] = []
    per_seed_reports: dict[str, object] = {}
    for seed in seeds:
        report = ce.run_registered_experiment(
            evaluation_ledgers=evaluation_ledgers,
            ledger_seed=ledger_seed,
            ledger_base=ledger_base,
            seed=seed,
            **training_kwargs,
        )
        # The per-seed checkpoint tensors are dropped: eight copies would be
        # ~4 MB of JSON, and the digest already names the model exactly.
        report.pop("checkpoints", None)
        per_seed_reports[str(seed)] = report
        results.append(_summarize_seed(seed, report))

    admissible = [row for row in results if row.terminal == "UCOPE_MEASUREMENT_ADMISSIBLE"]

    summary: dict[str, object] = {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "per_seed_reports": per_seed_reports,
        "provenance": provenance(
            run_arguments={
                "seeds": list(seeds),
                "evaluation_ledgers": evaluation_ledgers,
                "ledger_seed": ledger_seed,
                "ledger_base": ledger_base,
                **training_kwargs,
            }
        ),
        "evaluation_support_disjointness": disjointness,
        "design": {
            "unit_of_analysis": "training seed",
            "replications": len(seeds),
            "what_varies": (
                "policy initialization AND the training episode stream together, "
                "because run_arm derives regime_seed = seed + 2 and "
                "evidence_seed = seed + 3 from the same training seed"
            ),
            "what_is_held_fixed": (
                "the evaluation support: the same ledger_seed, ledger_base and "
                "exactly-weighted crossed cells score every replication"
            ),
            "held_out": (
                "NOT held out for a seed whose derived roots contain ledger_seed "
                "while the ledger ids overlap the training episode-id range -- "
                "see evaluation_support_disjointness, which reports exactly which"
            ),
            "not_decomposed": (
                "initialization variance is not separated from training-stream "
                "variance. A decomposition would hold the stream and vary only "
                "torch.manual_seed; External Pro ruled it is NOT required for the "
                "licensed sentence -- only for attributing variance specifically "
                "to initialization."
            ),
        },
        "per_seed": [row.__dict__ for row in results],
        "all_seeds_admissible": len(admissible) == len(results),
        "all_seeds_passed_the_blind_ceiling_guard": all(
            row.guard_passed for row in results
        ),
        "all_seeds_severed_bit_identical_to_blind": all(
            row.severed_is_bit_identical_to_blind for row in results
        ),
    }

    if not admissible:
        summary["terminal"] = "CROSS_SEED_REFUSED"
        summary["refusal"] = "No replication produced an admissible measurement."
        return summary

    contrasts = [row.contrast for row in admissible]
    summary["between_arm_contrast_across_seeds"] = across_seed_summary(contrasts)
    summary["within_checkpoint_severance_across_seeds"] = across_seed_summary(
        [row.severance for row in admissible]
    )
    summary["informed_regret_across_seeds"] = across_seed_summary(
        [row.informed_regret for row in admissible]
    )
    summary["blind_regret_across_seeds"] = across_seed_summary(
        [row.blind_regret for row in admissible]
    )
    summary["seeds_with_a_positive_contrast"] = sum(
        1 for value in contrasts if value > 0.0
    )
    summary["seeds_whose_state_conditional_mean_is_correct_at_every_state"] = sum(
        1 for row in admissible if row.state_conditional_mean_correct_at_every_state
    )
    summary["states_missed_by_seed"] = {
        str(row.seed): list(row.incorrect_states)
        for row in admissible
        if row.incorrect_states
    }
    summary["maximum_absolute_deviation_from_bayes_over_all_seeds"] = max(
        row.maximum_absolute_deviation_from_bayes for row in admissible
    )
    # Pro's distribution-free companion to the Student-t interval: under an
    # equal-sign null with independent seed outcomes, all-positive has
    # probability 2^-n.  Reported alongside the interval, not instead of it.
    summary["all_positive_sign_probability_under_the_equal_sign_null"] = (
        0.5 ** len(contrasts)
        if summary["seeds_with_a_positive_contrast"] == len(contrasts)
        else None
    )
    summary["distinct_informed_checkpoints"] = len(
        {row.checkpoint_digests[pt.INFORMED] for row in admissible}
    )
    # Pro: this is plumbing, not a behavioral result.  Recorded next to the
    # number so it cannot be quoted as evidence of behavioral diversity.
    summary["distinct_informed_checkpoints_status"] = (
        "an end-to-end seed-propagation safeguard: it shows the seed reached the "
        "training process and the runs did not collapse to byte-identical "
        "parameters. It does NOT establish that the policies implement different "
        "functions, that the streams are statistically independent, or that "
        "behavioral diversity exists -- distinct weights can represent nearly "
        "identical policies. The behavioral evidence is the per-seed contrasts "
        "and state-conditioned effort readouts. Final-checkpoint distinctness "
        "alone also conflates initialization and stream; a future artifact "
        "should record an initial-checkpoint digest and a training-stream "
        "manifest digest separately."
    )
    # Pro: the current severance is OFF-MANIFOLD, so its magnitude is not an
    # information-value estimate.  The caveat travels with the number.
    summary["within_checkpoint_severance_status"] = (
        "SEVERED replaces (positive count, completed epochs) with (0.0, 0.0) "
        "while retaining the real later-episode time coordinate, creating inputs "
        "such as 'completed epochs = 0 but time is in the second or third epoch' "
        "that the informed checkpoint never saw in training. The magnitude "
        "therefore combines genuine evidence dependence with out-of-distribution "
        "behavior and must NOT be used as an information-value estimate or a "
        "clean causal effect. A support-preserving severance would retain the "
        "actual completed-epoch channel, replace the positive count with a draw "
        "from its prior-predictive marginal conditional on completed epoch "
        "independently of the actual regime, and average exactly over those "
        "replacements on the crossed support."
    )

    if len(admissible) != len(results):
        summary["terminal"] = "CROSS_SEED_PARTIAL"
    else:
        summary["terminal"] = "CROSS_SEED_MEASURED"

    # Pro's replacement for reading the contrast against the certified 4.5.
    # The separately-trained-arm contrast is 4.5 - eps_I + eps_B, so its
    # proximity to 4.5 means the two arms have SIMILAR OPTIMIZATION REGRET -- not
    # that the informed policies captured 99% of the information value.  Three
    # individual contrasts exceeding 4.5 makes that decisive: the contrast can
    # exceed the oracle gap whenever the blind arm sits farther below its own
    # ceiling than the informed arm does.
    informed_mean_across_seeds = statistics.fmean(
        row.informed_mean for row in admissible
    )
    summary["oracle_ceiling_performance_normalization"] = {
        "value": (informed_mean_across_seeds - pt.BLIND_OPTIMUM)
        / (pt.INFORMED_OPTIMUM - pt.BLIND_OPTIMUM),
        "definition": "(mean informed crossed value - 32) / (36.5 - 32)",
        "status": (
            "an oracle-ceiling PERFORMANCE normalization, not a literal "
            "percentage of information captured. Do NOT compute "
            "contrast/4.5: that ratio conflates information capture with the "
            "difference in optimization regret between the two arms."
        ),
    }

    summary["scope"] = (
        "Code-side measurement over training seeds. External Pro ruled on the "
        "reading: the closed statement is reproducibility across eight JOINT "
        "initialization-and-training-stream seed realizations at the registered "
        "budget -- not initialization-only robustness, and not universal PPO "
        "reliability. 8/8 must not be translated into a 100% success "
        "probability: treated as Bernoulli draws, eight successes give an exact "
        "two-sided 95% lower bound of only about 0.631. Nothing here is a claim "
        "about information acquisition, which this sibling cannot identify at "
        f"all: the evidence distribution does not depend on the chosen effort "
        f"(PERIODS={cc.PERIODS})."
    )
    return summary


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(run_replication(), indent=2, default=str))
