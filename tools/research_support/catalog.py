"""Metric catalog: the declared semantics of every number the suite summarises.

Why this module exists at all: a reducer chosen at the call site is a reducer nobody can
audit.  The same figure code is asked to summarise a *rate* (Mbps), an *accumulated
volume* (Mbit), a *ratio* of two volumes, a *loss*, a *duration* and a *categorical skill
identifier*.  Those cannot share one aggregation rule without producing numbers that look
like measurements and are not:

* averaging per-episode ratios answers a different question than the ratio of the summed
  numerator and denominator, and the two disagree whenever the denominators differ;
* summing a rate over episodes produces a quantity with no unit;
* averaging skill identifiers produces "skill 2.4", which does not exist
  (plan section 7.3 rule 9);
* native environment reward is not a common performance scale across environments or
  reward definitions, so a percentage gain computed over it is not comparable
  (plan section 4.2 and 7.3 rule 7).

So each metric declares, once and next to the code that produces it: unit, direction,
reducer, valid domain, missingness policy and - for a ratio - the numerator and
denominator metric names, so a consumer recomputes the ratio from summed denominators
instead of averaging ratios.

The seeded entries are the quantities this repository actually emits today.  Sources read
to build them (cited per entry in ``description``):

``envs/uav_service_restoration/metrics.py``
    ``EpisodeAccumulator.summary()`` keys and ``service_ratio_distribution()``.  That
    module's own docstring states the unit discipline this catalog encodes: ``*_mbps``
    fields are rates, ``*_mbit`` fields are their time integrals, energy is unavailable in
    v0 rather than estimated, and the scheduler change counters are properties of the
    fixed path-flow scheduler rather than evidence of learned behaviour.
``envs/uav_service_restoration/evaluation.py``
    ``evaluate_rollout()`` -> ``references`` and ``recovery_report()`` keys, including the
    strict recovery definition in which an automatic site repair censors the episode with
    its reason instead of counting as UAV recovery.

A few entries name component metrics that no reader emits *yet* (for example
``offered_mbit_affected``).  They are declared here because the ratio semantics are known
even when the component rows are missing; the description says so explicitly, and
``statistics.aggregate_episodes_to_units`` then falls back to averaging per-episode ratios
with a visible note rather than pretending the components existed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# --------------------------------------------------------------------------------------
# Declared vocabularies
# --------------------------------------------------------------------------------------

#: Which way is "better".  ``neutral`` means the metric is exogenous (offered demand), a
#: reference counterfactual, or a descriptor whose ordering carries no claim.
DIRECTIONS = frozenset({"higher_is_better", "lower_is_better", "neutral"})

#: How values of this metric combine when several rows fall inside one statistical unit.
#:
#: ``mean``            intensive quantity (a rate, a per-point ratio, a loss);
#: ``sum``             extensive quantity (an accumulated volume, a count, an integral);
#: ``ratio_of_sums``   recomputed as ``sum(numerator) / sum(denominator)``;
#: ``median``          value whose mean is not meaningful (already an extremum, or a
#:                     skewed/censored duration);
#: ``categorical``     identifier or label; never averaged.
REDUCERS = frozenset({"mean", "sum", "ratio_of_sums", "median", "categorical"})

#: What a consumer must do when a row for this metric is missing.
#:
#: ``report_missing``    default: show the gap, never substitute a value;
#: ``exclude_and_count`` drop the row from the reduction but carry its count;
#: ``absent_by_design``  the producer cannot measure this at all (no battery model);
#: ``expected_absent_when_not_applicable``
#:                       absence is an ordinary outcome (a censored recovery, an episode
#:                       with no capability loss) and is not a defect.
MISSINGNESS_POLICIES = frozenset(
    {
        "report_missing",
        "exclude_and_count",
        "absent_by_design",
        "expected_absent_when_not_applicable",
    }
)


class UnknownMetricError(KeyError):
    """Raised when a metric name has no declared definition.

    A ``KeyError`` subclass so existing ``except KeyError`` paths keep working, but a
    distinct type so a caller can tell "this metric is undeclared" from "this dictionary
    lacked a key".
    """


@dataclass(frozen=True)
class MetricDefinition:
    """Declared semantics of one metric name.

    ``higher_is_better`` is derived from ``direction`` (``None`` for a neutral metric) so
    the two can never drift apart; passing a contradicting value is an error rather than a
    silent override.
    """

    name: str
    unit: str
    direction: str
    reducer: str
    definition_id: str
    description: str
    valid_domain: tuple[float | None, float | None] = (None, None)
    missingness_policy: str = "report_missing"
    numerator: str | None = None
    denominator: str | None = None
    higher_is_better: bool | None = None

    def __post_init__(self) -> None:
        if self.direction not in DIRECTIONS:
            raise ValueError(f"{self.name}: unknown direction {self.direction!r}")
        if self.reducer not in REDUCERS:
            raise ValueError(f"{self.name}: unknown reducer {self.reducer!r}")
        if self.missingness_policy not in MISSINGNESS_POLICIES:
            raise ValueError(
                f"{self.name}: unknown missingness_policy {self.missingness_policy!r}"
            )
        derived = _direction_to_flag(self.direction)
        if self.higher_is_better is None:
            object.__setattr__(self, "higher_is_better", derived)
        elif self.higher_is_better != derived:
            raise ValueError(
                f"{self.name}: higher_is_better={self.higher_is_better!r} contradicts "
                f"direction={self.direction!r}"
            )
        if self.reducer == "ratio_of_sums":
            if self.numerator is None or self.denominator is None:
                raise ValueError(
                    f"{self.name}: a ratio_of_sums metric must declare both numerator and "
                    "denominator so a consumer can recompute it from summed denominators "
                    "instead of averaging per-episode ratios"
                )
        elif self.numerator is not None or self.denominator is not None:
            raise ValueError(
                f"{self.name}: numerator/denominator are only meaningful for a "
                f"ratio_of_sums metric, not for reducer={self.reducer!r}"
            )
        low, high = self.valid_domain
        if low is not None and high is not None and float(low) > float(high):
            raise ValueError(f"{self.name}: empty valid_domain {self.valid_domain!r}")

    def contains(self, value: float) -> bool:
        """Whether ``value`` lies inside the declared valid domain (inclusive)."""

        low, high = self.valid_domain
        if low is not None and float(value) < float(low):
            return False
        if high is not None and float(value) > float(high):
            return False
        return True

    def to_json(self) -> dict[str, Any]:
        low, high = self.valid_domain
        return {
            "name": self.name,
            "unit": self.unit,
            "direction": self.direction,
            "higher_is_better": self.higher_is_better,
            "reducer": self.reducer,
            "definition_id": self.definition_id,
            "description": self.description,
            "valid_domain": {
                "min": None if low is None else float(low),
                "max": None if high is None else float(high),
            },
            "missingness_policy": self.missingness_policy,
            "numerator": self.numerator,
            "denominator": self.denominator,
        }


def _direction_to_flag(direction: str) -> bool | None:
    if direction == "higher_is_better":
        return True
    if direction == "lower_is_better":
        return False
    return None


def _defn(
    name: str,
    unit: str,
    direction: str,
    reducer: str,
    description: str,
    *,
    namespace: str = "uavsr",
    domain: tuple[float | None, float | None] = (None, None),
    missingness: str = "report_missing",
    numerator: str | None = None,
    denominator: str | None = None,
    version: int = 1,
) -> MetricDefinition:
    """Build one definition with a mechanically derived ``definition_id``.

    The id is ``<namespace>.<name>.v<version>``: stable, greppable, and bumped by hand when
    the meaning of a name changes, which is what lets a figure state which definition it
    plotted.
    """

    return MetricDefinition(
        name=name,
        unit=unit,
        direction=direction,
        reducer=reducer,
        definition_id=f"{namespace}.{name}.v{version}",
        description=description,
        valid_domain=domain,
        missingness_policy=missingness,
        numerator=numerator,
        denominator=denominator,
    )


_NON_NEGATIVE: tuple[float | None, float | None] = (0.0, None)
_UNIT_RATIO: tuple[float | None, float | None] = (0.0, 1.0)

_SEED: tuple[MetricDefinition, ...] = (
    # -- training-side reward ----------------------------------------------------------
    _defn(
        "episode_reward_sum",
        "native_reward",
        "neutral",
        "sum",
        "Sum of the native per-step environment reward over one episode. Native reward "
        "from different environments, reward weightings or shaping terms is NOT a common "
        "performance scale (plan 4.2), so this metric may be compared only across methods "
        "that share one reward definition, and a relative percentage gain computed over it "
        "cannot rescue mismatched reward definitions (plan 7.3 rule 7).",
        namespace="train",
    ),
    _defn(
        "episode_reward_mean",
        "native_reward",
        "neutral",
        "mean",
        "Per-step mean of the native environment reward over one episode. Same scale "
        "warning as episode_reward_sum: native reward from different environments is not a "
        "common performance scale. It is also not interchangeable with episode_reward_sum, "
        "because episodes of different length weight the steps differently.",
        namespace="train",
    ),
    # -- accumulated service volumes ---------------------------------------------------
    _defn(
        "offered_mbit",
        "Mbit",
        "neutral",
        "sum",
        "Offered traffic volume over the episode, i.e. the time integral of the offered "
        "rate (envs/uav_service_restoration/metrics.py: EpisodeAccumulator.summary()"
        "['offered_mbit_total'], also evaluate_rollout()['references']['offered_mbit']). "
        "Exogenous demand, not an outcome: it is neutral by direction and is the standard "
        "denominator for satisfaction ratios.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "delivered_mbit",
        "Mbit",
        "higher_is_better",
        "sum",
        "Delivered traffic volume over the episode (metrics.py: summary()"
        "['delivered_mbit_total']). An accumulated volume: it grows with episode length, so "
        "it is comparable only across units evaluated over the same episode set.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "unmet_mbit",
        "Mbit",
        "lower_is_better",
        "sum",
        "Undelivered demand volume, the time integral of max(offered - delivered, 0) "
        "(metrics.py: summary()['unmet_mbit_total']). A loss quantity; it is not "
        "1 - delivered and must not be reduced with a ratio rule.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "offered_mbit_total",
        "Mbit",
        "neutral",
        "sum",
        "Exact key emitted by metrics.py EpisodeAccumulator.summary(); same quantity as "
        "offered_mbit, kept under the producer's own name so a reader need not rename rows.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "delivered_mbit_total",
        "Mbit",
        "higher_is_better",
        "sum",
        "Exact key emitted by metrics.py EpisodeAccumulator.summary(); same quantity as "
        "delivered_mbit.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "unmet_mbit_total",
        "Mbit",
        "lower_is_better",
        "sum",
        "Exact key emitted by metrics.py EpisodeAccumulator.summary(); same quantity as "
        "unmet_mbit.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "total_time_s",
        "s",
        "neutral",
        "sum",
        "Simulated time accumulated by the episode (metrics.py: summary()['total_time_s']). "
        "Needed to tell a rate from a volume and to detect unequal-length episodes; it is "
        "not a performance metric.",
        domain=_NON_NEGATIVE,
    ),
    # -- rates -------------------------------------------------------------------------
    _defn(
        "mean_offered_mbps",
        "Mbps",
        "neutral",
        "mean",
        "Duration-weighted mean offered rate, computed by metrics.py as offered_mbit_total "
        "/ total_time_s. A rate: never add it to a Mbit volume and never sum it over "
        "episodes.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "mean_delivered_mbps",
        "Mbps",
        "higher_is_better",
        "mean",
        "Duration-weighted mean delivered rate (metrics.py: delivered_mbit_total / "
        "total_time_s). A rate, reduced by mean rather than sum; episodes of unequal "
        "duration are weighted equally unless declared weights say otherwise.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "peak_unmet_mbps",
        "Mbps",
        "lower_is_better",
        "median",
        "Worst instantaneous unmet rate inside one episode (metrics.py: summary()"
        "['peak_unmet_mbps']). The per-episode value is already a maximum; across episodes "
        "it is summarised by a median of per-episode peaks, because a mean of maxima is "
        "neither a maximum nor a typical value.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "max_constraint_residual",
        "Mbps",
        "lower_is_better",
        "median",
        "Largest scheduler constraint residual seen in the episode (metrics.py: summary()"
        "['max_constraint_residual']). A solver-feasibility diagnostic, not a service "
        "outcome; summarised by median for the same reason as peak_unmet_mbps.",
        domain=_NON_NEGATIVE,
    ),
    # -- satisfaction ratios -----------------------------------------------------------
    _defn(
        "satisfaction_ratio",
        "ratio",
        "higher_is_better",
        "ratio_of_sums",
        "Delivered volume over offered volume. Recomputed as sum(delivered_mbit) / "
        "sum(offered_mbit) across the rows inside a statistical unit; averaging per-episode "
        "ratios answers a different question and disagrees whenever offered volumes differ. "
        "A zero offered volume yields an absent value with reason zero_denominator, never "
        "0.0 and never a perfectly served user (metrics.py EpisodeAccumulator.satisfaction()"
        " returns NaN in that case).",
        domain=_UNIT_RATIO,
        numerator="delivered_mbit",
        denominator="offered_mbit",
    ),
    _defn(
        "satisfaction_all",
        "ratio",
        "higher_is_better",
        "ratio_of_sums",
        "Demand-weighted satisfaction over all demand points (metrics.py: summary()"
        "['satisfaction_all']). Components are the producer's own total keys.",
        domain=_UNIT_RATIO,
        numerator="delivered_mbit_total",
        denominator="offered_mbit_total",
    ),
    _defn(
        "satisfaction_affected",
        "ratio",
        "higher_is_better",
        "ratio_of_sums",
        "Demand-weighted satisfaction restricted to the affected demand points (metrics.py: "
        "summary()['satisfaction_affected']). The declared components "
        "delivered_mbit_affected / offered_mbit_affected are NOT emitted as scalar keys by "
        "the repository today, so a reduction over these records falls back to averaging "
        "per-episode ratios and says so in its notes until a reader emits the component "
        "sums over the affected mask.",
        domain=_UNIT_RATIO,
        numerator="delivered_mbit_affected",
        denominator="offered_mbit_affected",
    ),
    _defn(
        "service_ratio_distribution.mean",
        "ratio",
        "higher_is_better",
        "mean",
        "Mean per-demand-point service ratio, restricted to points with positive offered "
        "volume (metrics.py: service_ratio_distribution()['mean']). A mean over points, not "
        "a demand-weighted satisfaction: it treats a tiny and a large demand point alike.",
        domain=_UNIT_RATIO,
    ),
    _defn(
        "service_ratio_distribution.median",
        "ratio",
        "higher_is_better",
        "median",
        "Median per-demand-point service ratio over points with positive offered volume "
        "(metrics.py: service_ratio_distribution()['median']).",
        domain=_UNIT_RATIO,
    ),
    _defn(
        "service_ratio_distribution.min",
        "ratio",
        "higher_is_better",
        "median",
        "Worst-served demand point of the episode (metrics.py: "
        "service_ratio_distribution()['min']). Already an extremum, so across episodes it "
        "is summarised by a median of per-episode minima.",
        domain=_UNIT_RATIO,
    ),
    _defn(
        "disconnected_time_s_max",
        "s",
        "lower_is_better",
        "median",
        "Longest time any demand point spent with positive demand and no delivery "
        "(metrics.py: summary()['disconnected_time_s_max']). Per-episode extremum, "
        "summarised across episodes by median.",
        domain=_NON_NEGATIVE,
    ),
    # -- flight cost -------------------------------------------------------------------
    _defn(
        "flight_distance_m",
        "m",
        "lower_is_better",
        "sum",
        "Total distance flown by all UAVs in the episode (metrics.py: summary()"
        "['flight_distance_m_total']). A cost proxy only: a shorter flight is not better if "
        "service is worse, so this metric is read beside a service metric, never alone.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "flight_distance_m_total",
        "m",
        "lower_is_better",
        "sum",
        "Exact key emitted by metrics.py EpisodeAccumulator.summary(); same quantity as "
        "flight_distance_m.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "motion_effort_integral_s",
        "effort_s",
        "lower_is_better",
        "sum",
        "Time integral of the dimensionless motion-effort term (metrics.py: summary()"
        "['motion_effort_integral_s']); its unit is therefore dimensionless effort times "
        "seconds. That module states explicitly that v0 has no battery model, so this is "
        "the honest effort field and is NOT energy in joules.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "energy_joules",
        "J",
        "lower_is_better",
        "sum",
        "Consumed energy. metrics.py emits None together with energy_status 'unavailable: "
        "v0 implements no battery or hover-power model', so this value is absent by design "
        "and must never be filled from an estimate, a datasheet or motion_effort.",
        domain=_NON_NEGATIVE,
        missingness="absent_by_design",
    ),
    # -- scheduler descriptors ---------------------------------------------------------
    _defn(
        "scheduler_path_signature_changes",
        "count",
        "neutral",
        "sum",
        "Number of times the active path signature changed (metrics.py: summary()"
        "['scheduler_path_signature_changes']). metrics.py states this is produced by the "
        "fixed path-flow scheduler and is not evidence of skill switching or learned "
        "routing, so it carries no direction.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "scheduler_allocation_change_events",
        "count",
        "neutral",
        "sum",
        "Number of substeps whose delivered allocation differed from the previous one "
        "(metrics.py: summary()['scheduler_allocation_change_events']). A property of the "
        "fixed scheduler, not of the policy.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "min_uav_separation_m",
        "m",
        "neutral",
        "median",
        "Smallest UAV-to-UAV separation observed (metrics.py: summary()"
        "['min_uav_separation_m'], None when no finite separation was observed). Neutral by "
        "direction because metrics.py records that collision avoidance is not implemented "
        "and no safe-flight guarantee is claimed; this is a diagnostic, not a safety score.",
        domain=_NON_NEGATIVE,
        missingness="expected_absent_when_not_applicable",
    ),
    _defn(
        "team_skill_id",
        "skill_identifier",
        "neutral",
        "categorical",
        "Team skill identifier selected by the high level. A categorical label: it is never "
        "averaged, and skill 3 of one training fit is not the same behaviour as skill 3 of "
        "a separately trained fit (plan 7.3 rule 9).",
        namespace="hmasd",
    ),
    _defn(
        "individual_skill_id",
        "skill_identifier",
        "neutral",
        "categorical",
        "Per-agent skill identifier. Categorical, like team_skill_id; an operational "
        "meaning such as 'relay skill' requires a separately verified definition.",
        namespace="hmasd",
    ),
    # -- counterfactual references (evaluation.py evaluate_rollout()['references']) -----
    _defn(
        "healthy_no_uav_delivered_mbit",
        "Mbit",
        "neutral",
        "sum",
        "Delivered volume of the healthy terrestrial network with no events and no UAVs "
        "(evaluation.py: evaluate_rollout()['references']['healthy_no_uav_delivered_mbit'])."
        " A counterfactual reference computed without looking at the evaluated controller; "
        "neutral by direction because no policy can change it.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "failed_no_uav_delivered_mbit",
        "Mbit",
        "neutral",
        "sum",
        "Delivered volume of the failed terrestrial network with no UAVs "
        "(evaluation.py: references['failed_no_uav_delivered_mbit']). The no-UAV baseline of "
        "the same episode, including the same automatic repairs.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "controller_delivered_mbit",
        "Mbit",
        "higher_is_better",
        "sum",
        "Delivered volume of the failed network with the evaluated controller flying "
        "(evaluation.py: references['controller_delivered_mbit']).",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "healthy_satisfaction",
        "ratio",
        "neutral",
        "ratio_of_sums",
        "Healthy-reference delivered volume over offered volume (evaluation.py: "
        "references['healthy_satisfaction']; NaN there when no demand was offered, which a "
        "reader must carry as an absent value). Neutral: it is the achievable reference, "
        "not a score.",
        domain=_UNIT_RATIO,
        numerator="healthy_no_uav_delivered_mbit",
        denominator="offered_mbit",
    ),
    _defn(
        "failed_satisfaction",
        "ratio",
        "neutral",
        "ratio_of_sums",
        "No-UAV failed-network delivered volume over offered volume (evaluation.py: "
        "references['failed_satisfaction']). The floor the controller must beat.",
        domain=_UNIT_RATIO,
        numerator="failed_no_uav_delivered_mbit",
        denominator="offered_mbit",
    ),
    _defn(
        "controller_satisfaction",
        "ratio",
        "higher_is_better",
        "ratio_of_sums",
        "Controller delivered volume over offered volume (evaluation.py: "
        "references['controller_satisfaction']). Recomputed from summed volumes; read "
        "against healthy_satisfaction and failed_satisfaction of the same episodes, since "
        "the reachable range is bounded by them.",
        domain=_UNIT_RATIO,
        numerator="controller_delivered_mbit",
        denominator="offered_mbit",
    ),
    # -- recovery (evaluation.py recovery_report()) ------------------------------------
    _defn(
        "time_to_recovery_s",
        "s",
        "lower_is_better",
        "median",
        "Simulated seconds from the first capability loss until the sustained recovery "
        "threshold is met (evaluation.py: recovery_report()['time_to_recovery_s'] = "
        "recovery_time_s - failure_start_s). None whenever the episode is censored, which "
        "includes an automatic repair reaching the threshold first; an unrecovered episode "
        "has NO time, and substituting 0 or the episode length would invent a measurement. "
        "Summarised by median over recovered episodes only, and any such summary is "
        "conditional on recovery - use statistics.recovery_summary() for the outcome mix.",
        domain=_NON_NEGATIVE,
        missingness="expected_absent_when_not_applicable",
    ),
    _defn(
        "recovery_time_s",
        "s",
        "lower_is_better",
        "median",
        "Absolute simulated time at which the sustained recovery threshold was first met "
        "(evaluation.py: recovery_report()['recovery_time_s']). Comparable only across "
        "episodes with an identical failure schedule; time_to_recovery_s is the quantity "
        "to compare otherwise.",
        domain=_NON_NEGATIVE,
        missingness="expected_absent_when_not_applicable",
    ),
    _defn(
        "failure_start_s",
        "s",
        "neutral",
        "median",
        "Time of the first capability loss in the episode (evaluation.py: "
        "recovery_report()['failure_start_s']). Exogenous.",
        domain=_NON_NEGATIVE,
        missingness="expected_absent_when_not_applicable",
    ),
    _defn(
        "first_repair_s",
        "s",
        "neutral",
        "median",
        "Time of the first automatic site repair (evaluation.py: "
        "recovery_report()['first_repair_s'], None when the episode has no repair). "
        "Exogenous, and a competing event rather than harmless censoring: the repair can "
        "restore service that the UAVs did not.",
        domain=_NON_NEGATIVE,
        missingness="expected_absent_when_not_applicable",
    ),
    _defn(
        "censoring_reason",
        "label",
        "neutral",
        "categorical",
        "Why a recovery observation is censored (evaluation.py: "
        "recovery_report()['censoring_reason']): repaired_before_recovery_threshold_reached,"
        " threshold_first_met_after_automatic_repair, episode_ended_before_failure or "
        "threshold_not_reached_within_episode. A label: counted per category, never "
        "averaged, and never collapsed into one 'failed' bucket.",
        missingness="expected_absent_when_not_applicable",
    ),
    _defn(
        "n_affected_points",
        "count",
        "neutral",
        "sum",
        "Number of demand points the failure actually harmed, defined from the healthy "
        "versus failed references without the evaluated policy (evaluation.py: "
        "recovery_report()['n_affected_points']).",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "not_applicable_instants",
        "count",
        "neutral",
        "sum",
        "Instants where the healthy reference delivered nothing on the affected set, so no "
        "recovery ratio was defined (evaluation.py: "
        "recovery_report()['not_applicable_instants']). A coverage diagnostic for the "
        "recovery criterion.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "controller_delivered_mbit_affected",
        "Mbit",
        "higher_is_better",
        "sum",
        "Controller delivered volume restricted to the affected demand points "
        "(evaluation.py: recovery_report()['controller_delivered_mbit_affected']).",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "failed_no_uav_delivered_mbit_affected",
        "Mbit",
        "neutral",
        "sum",
        "No-UAV delivered volume on the affected demand points (evaluation.py: "
        "recovery_report()['failed_no_uav_delivered_mbit_affected']).",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "healthy_delivered_mbit_affected",
        "Mbit",
        "neutral",
        "sum",
        "Healthy-reference delivered volume on the affected demand points (evaluation.py: "
        "recovery_report()['healthy_delivered_mbit_affected']).",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "improvement_over_no_uav_mbit",
        "Mbit",
        "higher_is_better",
        "sum",
        "controller_delivered_mbit_affected - failed_no_uav_delivered_mbit_affected "
        "(evaluation.py: recovery_report()['improvement_over_no_uav_mbit']). May be "
        "negative, so it has no lower bound: the controller can deliver less than the "
        "no-UAV baseline.",
    ),
    _defn(
        "lost_service_mbit_affected",
        "Mbit",
        "neutral",
        "sum",
        "Service the failure removed on the affected set, i.e. "
        "healthy_delivered_mbit_affected - failed_no_uav_delivered_mbit_affected. "
        "evaluation.py uses this difference as the denominator of "
        "fraction_of_lost_service_restored but does not emit it as its own key; a reader "
        "that wants the ratio recomputed from summed denominators must emit it.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "fraction_of_lost_service_restored",
        "ratio",
        "higher_is_better",
        "ratio_of_sums",
        "improvement_over_no_uav_mbit divided by the service the failure removed "
        "(evaluation.py: recovery_report()['fraction_of_lost_service_restored'], NaN when "
        "the gap is not positive - a reader must carry that as an absent value, not 0.0). "
        "Unbounded on both sides: negative when the controller hurts, above 1 when it "
        "delivers more than the healthy reference on the affected set.",
        numerator="improvement_over_no_uav_mbit",
        denominator="lost_service_mbit_affected",
    ),
    _defn(
        "recovered_by_deadline_count",
        "count",
        "higher_is_better",
        "sum",
        "Episodes whose time_to_recovery_s is present and within the prespecified deadline. "
        "Numerator of recovery_fraction_at_deadline; produced by "
        "statistics.recovery_summary() from raw episode outcomes.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "affected_episode_count",
        "count",
        "neutral",
        "sum",
        "Episodes the failure actually affected and whose outcome is determinable "
        "(recovered or censored). Denominator of recovery_fraction_at_deadline; episodes "
        "with no capability loss and technically failed episodes are counted separately.",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "recovery_fraction_at_deadline",
        "ratio",
        "higher_is_better",
        "ratio_of_sums",
        "Fraction of affected episodes recovered within a prespecified deadline, recomputed "
        "as recovered_by_deadline_count / affected_episode_count. It is a descriptive "
        "fraction with explicit censoring counts beside it, not a survival probability: "
        "automatic repair is a competing event, so no Kaplan-Meier style estimate is "
        "implied (plan 7.3, Recovery paragraph).",
        domain=_UNIT_RATIO,
        numerator="recovered_by_deadline_count",
        denominator="affected_episode_count",
    ),
    _defn(
        "delivered_mbit_affected",
        "Mbit",
        "higher_is_better",
        "sum",
        "Delivered volume summed over the affected demand points. Declared because "
        "satisfaction_affected needs it as a numerator; NOT emitted as a scalar key by the "
        "repository today (metrics.py keeps only the per-point arrays and the ratio).",
        domain=_NON_NEGATIVE,
    ),
    _defn(
        "offered_mbit_affected",
        "Mbit",
        "neutral",
        "sum",
        "Offered volume summed over the affected demand points. Declared because "
        "satisfaction_affected needs it as a denominator; NOT emitted as a scalar key by "
        "the repository today.",
        domain=_NON_NEGATIVE,
    ),
)

#: Process-wide catalog.  Seeded with the metrics this repository actually emits; extend it
#: through :func:`register` rather than by mutating the dict, so a conflicting redefinition
#: is refused instead of silently changing the meaning of an existing name.
DEFAULT_CATALOG: dict[str, MetricDefinition] = {defn.name: defn for defn in _SEED}

if len(DEFAULT_CATALOG) != len(_SEED):  # pragma: no cover - guards a typo in the seed
    raise RuntimeError("duplicate metric name in the seeded catalog")


def metric_definition(name: str) -> MetricDefinition:
    """Return the declared definition of ``name`` or raise :class:`UnknownMetricError`."""

    try:
        return DEFAULT_CATALOG[name]
    except KeyError:
        raise UnknownMetricError(
            f"no metric definition for {name!r}; register one before reducing it, so the "
            "reducer, direction and unit of the plotted number are declared"
        ) from None


def try_metric_definition(name: str) -> MetricDefinition | None:
    """Look ``name`` up without raising.

    This is the ``catalog_lookup`` shape the statistics layer expects: an undeclared metric
    yields ``None`` there and is reduced with a conservative default plus a visible note,
    instead of failing a whole report.
    """

    return DEFAULT_CATALOG.get(name)


def register(defn: MetricDefinition, *, replace: bool = False) -> None:
    """Add ``defn`` to :data:`DEFAULT_CATALOG`.

    Re-registering an identical definition is a no-op, which keeps module reimport and
    repeated setup harmless. A *different* definition for an existing name is refused
    unless ``replace=True``, because two meanings for one metric name is exactly how a
    figure ends up mislabelled.
    """

    existing = DEFAULT_CATALOG.get(defn.name)
    if existing is not None and existing != defn and not replace:
        raise ValueError(
            f"{defn.name} is already registered with a different definition "
            f"({existing.definition_id}); pass replace=True to override deliberately"
        )
    DEFAULT_CATALOG[defn.name] = defn


def catalog_to_json() -> dict[str, Any]:
    """Serialise the whole catalog, for the figure-specification JSON of plan 7.2.

    A figure records the reducer and metric definition it used; embedding the definitions
    themselves means a later reader does not have to trust that the catalog is unchanged.
    """

    return {
        "vocabularies": {
            "directions": sorted(DIRECTIONS),
            "reducers": sorted(REDUCERS),
            "missingness_policies": sorted(MISSINGNESS_POLICIES),
        },
        "metrics": {
            name: DEFAULT_CATALOG[name].to_json() for name in sorted(DEFAULT_CATALOG)
        },
    }
