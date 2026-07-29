# Scientific disposition — D7.S R4 formal result

**Stage reviewed:** `3e5624fa908c5fdf33f0fb6e06025f252aeb2f94`

## Overall verdict

# **THE FORMAL BRANCH STANDS, BUT ITS SCIENTIFIC UPDATE IS AN INSTRUMENT VERDICT**

Preserve the historical artifact exactly as emitted:

```text
PART_A_CONTRADICTION
```

Do not relabel it as the masked combined branch.

However, the equivalence result does **not** currently identify the proposition:

> Individual persistence is unnecessary because a genuine full-sync renewal controller is materially equivalent to `constructive_mixed`.

The implemented `full_sync_SET` arm does not guarantee that active agents actually leave their incumbent duties. It recomputes a nearest-agent assignment from scratch, but may return the same incumbents. The instrument also records no treatment-exposure statistic establishing how much individual renewal occurred. Therefore the observed equivalence cannot distinguish:

1. genuine zero-cost full-sync renewal;
2. a recomputation policy that mostly reproduces the incumbent assignment;
3. different duty maps whose physical targets or actions remain nearly identical;
4. genuine renewal whose external consequence is below five (G)-units.

The smallest update is consequently:

```text
PART_A_CONTROL_NON_IDENTIFYING_FOR_FORCED_INDIVIDUAL_RENEWAL
```

This is an interpretive disposition attached to the immutable artifact, not a replacement branch written back into its JSON.

The masked focal measurements remain readable as pre-registered **diagnostics**:

```text
stable = AFFIRMATIVE_NONMATERIAL
flex   = UNRESOLVED
```

They do not become the formal R4 result, and they do not authorize D7.3 or D8.

---

# 1. 5a — invalidation or mask?

## The binary in the question is too coarse

The result is neither:

* a total invalidation of all measurements; nor
* a merely cosmetic mask beneath which the combined source result can be promoted unchanged.

The correct separation is:

### A. The Part-A branch invalidates the **source-necessity interpretation**

The frozen first-match order places `PART_A_CONTRADICTION` before the combined focal result. The Part-A block asks whether `full_sync_SET` and `constructive_mixed` are return-equivalent within the five-unit margin. That branch therefore prevents the focal limbs from being interpreted as proof that the source requires heterogeneous individual renewal.

That registered precedence remains authoritative. The formal result is not:

```text
NO_MATERIAL_STABLE_PERSISTENCE_IDENTIFIED
```

### B. The focal estimates themselves remain diagnostically readable

The focal and Part-A quantities come from distinct blocks and distinct interventions. The formal run reports:

* support passed;
* conformance passed;
* the focal component audit completed;
* neither focal limb was component-invariant.

The contract also deliberately requires independent limb states to remain in the payload even when a higher-precedence branch masks the combined name.

Therefore the following narrow observation survives:

> On the registered eight-topology R4 population, the best empirical focal SET on the stable class was affirmatively not worse than KEEP by the pre-registered five-unit materiality margin; the flex contrast remained unresolved.

Numerically:

[
U^**{\mathrm{stable}}\text{ LCB}*{95}=-3.1781>-5,
]

so stable persistence did not clear the five-unit focal gate. The flex interval crossed both sides needed for a material or affirmatively nonmaterial conclusion.

This is a **local focal-intervention diagnostic**, not the registered global source-necessity result.

## Reuse of the eight topologies

### Permitted

The eight topologies and completed artifact may be reused for:

* artifact-only reanalysis;
* control-exposure diagnostics, if reconstructible from already stored data;
* methodological analysis of the implemented recompute-every-check controller;
* an explicitly labelled conditional or development replication.

### Not permitted as the primary confirmatory population

They may not carry a new formal result after redefining or repairing the Part-A control.

The topologies are now observed and have directly informed the diagnosis that the Part-A comparator lacked an exposure guarantee. R4 defined topology as the highest inferential unit and required an untouched topology population precisely because new episode draws under an observed topology panel are not a fresh confirmatory population.

A new protected definition such as “every eligible incumbent must actually change duty” is not a branch-string repair. It changes the intervention support. A conclusion-bearing successor using that control therefore requires a newly frozen, untouched topology panel.

A same-topology rerun may be retained only as a conditional diagnostic and must not be pooled with the successor’s confirmatory population.

---

# 2. 5b — mechanism evidence or instrument verdict?

# **Select (ii): instrument verdict**

The bootstrap result is a valid equivalence finding for the **two schedules actually executed**:

> The equal-topology-weighted external-return difference between the implemented greedy recompute-every-check schedule and `constructive_mixed` was contained within ([-5,+5]).

The point and reconstructed interval are:

[
D_A=0.484,
\qquad
95%\text{ interval approximately }[-0.681,1.686].
]

What is not established is that the first schedule instantiated full individual renewal.

## Repository fact: `full_sync_SET` does not enforce SET away from the incumbent

The implementation takes only:

* current duty positions;
* current airborne positions.

It greedily assigns the nearest remaining UAV to each duty. It receives no incumbent map and contains no prohibition against assigning a duty to its current holder. A fresh computation can therefore return the incumbent assignment unchanged.

The surrounding code says that the schedule “never preserves any incumbent,” but the executable meaning is only:

> no incumbent is explicitly locked.

That is different from:

> no incumbent can be selected again.

At each check, `full_sync_SET` calls that greedy routine; between checks it carries the resulting map forward.

The physical action is then synthesized from the duty map. If the recomputed map retains the incumbent—or assigns a geometrically equivalent target—the corresponding UAV action can remain the same.

## The conformance gate did not measure this exposure

`conformance.ok` includes an arm-distinctness check, but that check compares:

```text
constructive_mixed post-LEAVE map
versus
the pre-LEAVE ownership map
```

It establishes that `constructive_mixed` actually rematched the vacancy. It does **not** compare `full_sync_SET` against `constructive_mixed`, and it does not measure:

* incumbent retention;
* duty-map Hamming distance;
* target displacement;
* action divergence;
* or realized individual assignment lifetime.

Thus `conformance.ok=True` does not close the treatment-exposure question on which the Part-A causal interpretation depends.

## Secondary realization mismatch: the first action precedes the recomputation

`step_once` synthesizes and executes actions from the incoming duty map and only afterward calls `update_duty_map_on_transitions`. Consequently, at `step_index=0`, the first primitive action of the alleged full-sync check uses the pre-existing map; the full-sync map becomes effective after that action.

This one-step phase shift is unlikely by itself to explain the whole equivalence result, but it is another reason the executed arm is not yet an exact realization of “reassign every active commitment at the check boundary.”

## Scientific meaning that may be retained

The equivalence has a legitimate narrower interpretation:

> A stateless greedy assignment recomputation every shared check produced an average external return equivalent, within five (G)-units, to the event-driven `constructive_mixed` schedule on the R4 topology population.

That is potentially useful as an ordinary-controller reduction. It may indicate that current geometry and state feedback let a simple frequent-replanning controller reconstruct much of the persistent behavior.

It is not yet evidence that **actual full-sync individual renewal** is harmless, because the amount of renewal was not identified.

## Publication weight

In its current form, the result may carry methodological or baseline weight:

* recomputation frequency is not the same as realized individual renewal;
* a control named “full sync SET” must report whether it actually changed incumbents;
* return equivalence without exposure identification cannot establish equivalence of the intended mechanisms.

It does not independently support a publication claim that S7-S3 refutes individual persistence necessity.

If a corrected, exposure-certified forced-renewal control remains equivalent on a fresh population, that later result would carry substantive publication weight as a benchmark-identification negative.

---

# 3. Where does the defect sit?

# **The defect sits in the Part-A control construction and its missing exposure contract—not in the five-unit margin**

## Primary defect: comparator support

The intended causal contrast requires a controller that removes individual persistence. The implemented controller only removes **explicit incumbent protection**. It does not exclude the incumbent from the new assignment.

The frozen scientific target and the executable control are therefore different:

| Intended Part-A intervention                                        | Executed intervention                                                            |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| every eligible individual renews away from its incumbent commitment | every check recomputes a nearest assignment, possibly returning incumbents       |
| realized lifetime forced to one check                               | realized lifetime unmeasured and potentially longer                              |
| control exposure guaranteed                                         | control exposure not serialized                                                  |
| equivalence tests persistence necessity                             | equivalence tests recomputation frequency plus whatever churn happened naturally |

This is a comparator-identification failure. The project principles require a comparator to match the claim and require a positive control to make the target behavior necessary rather than merely permit it.

## The five-unit anchor remains valid

The current result does not show that five (G)-units is the wrong Part-A margin.

The Part-A contrast is, like the focal contrasts, a cumulative difference in the same primary external objective over (H_{\mathrm{stable}}=139). One cutoff-equivalent remains an interpretable total task consequence. The measured interval lying well inside (\pm5) says the executed schedules were close under that pre-registered unit; it does not diagnose why.

Changing the margin after observing the equivalence would be metric rescue. No threshold move is selected.

The correct order is:

1. first establish that the control actually forces the intended renewal;
2. then retain the frozen five-unit equivalence test;
3. only a separate pre-data task-semantic argument could reopen the anchor.

---

# 4. Challenges to §§1–4

## A. “This is a positive equivalence finding” — correct only for the implemented schedules

The statistical statement is correct. Both one-sided equivalence conditions passed.

The mechanism-level paraphrase is not yet justified because actual renewal exposure was unmeasured.

## B. “Every gate upstream passed” — true but incomplete

Every registered gate passed. No registered gate checked whether the Part-A controller changed every incumbent or produced a materially different action trajectory.

The run therefore passed the gates it had, while exposing a missing protected gate.

## C. The topology-cancellation explanation is overstated

The topology means are:

```text
-1.91 to +3.03
```

All eight topology point estimates are themselves inside the registered (\pm5) equivalence region. Thus the result is not solely a positive/negative cancellation in which large topology effects average to zero.

More precisely:

* sign cancellation helps place the pooled point near (0.484);
* it does **not** explain why the confidence interval is “tight”;
* between-topology heterogeneity generally widens the uncertainty interval rather than narrowing it;
* within-topology observations were averaged before equal topology weighting, and the hierarchical bootstrap resampled both levels.

The formal statement is:

> The equal-topology-weighted mean contrast was equivalent within (\pm5).

It is not:

> every episode, every topology, or every physical regime was equivalent.

The wide individual contributions show event-level heterogeneity. They do not invalidate a population-mean equivalence test, but they prevent a uniform-equivalence interpretation.

No variance decomposition supplied here establishes that topology cancellation, rather than ordinary averaging of multiple events within each topology, is the dominant reason for the interval width.

## D. “The source-control contrast appears systematically near zero” — narrow this

A defensible statement is:

> Every observed topology-level point contrast was smaller than five (G)-units in magnitude, and the equal-topology-weighted population interval was comfortably contained inside the five-unit margin.

“Systematically near zero” is too strong without:

* topology-specific confidence intervals;
* treatment-exposure measurements;
* and a definition of “near zero” separate from the already registered five-unit margin.

## E. The development topology did not contaminate the formal population

The development topology’s (D_A\approx0.46) was numerically predictive, but it was not included in the formal population. Steering synthetic branch witnesses during the non-conclusion-bearing assembled-path exercise does not alter the formal data.

It is instead a workflow lesson:

> a naturally occurring branch witness should be investigated before being treated merely as an obstacle to test coverage.

## F. The masked stable state is informative but does not become the formal result

`AFFIRMATIVE_NONMATERIAL` is an identified focal statement on this population. It lowers the plausibility that stable KEEP has a cutoff-equivalent advantage under the current focal estimand.

It cannot be promoted into the registered top-level branch after the fact, and it does not by itself settle whether a coordinated forced-renewal policy can compensate for unilateral SET costs.

---

# 5. Next action and portfolio

## Scheduled action

# **Derive an exposure-certified Part-A control before any further source run**

The next action is zero-compute: define the joint intervention that actually removes individual persistence.

A scientifically adequate candidate is:

> **Minimum-cost full derangement control:** at every shared check, assign every eligible active incumbent to a non-incumbent duty/target, using a one-to-one minimum-total-transit assignment subject to the incumbent-exclusion constraint.

The control should retain:

* the same physical duty set;
* the same information;
* the same energy and charging policy;
* the same shared check clock;
* the same CRN continuation;
* the same (H_{\mathrm{stable}}=139);
* the same five-(G)-unit Part-A equivalence margin.

It should replace:

* greedy unconstrained recomputation;
* the assumption that “computed from scratch” implies actual SET.

## Exposure semantics to freeze

At every registered full-sync check:

1. every eligible active agent must receive a target geometrically different from its incumbent target under the existing target-identity tolerance;
2. no eligible incumbent may remain;
3. if a full derangement is infeasible, the event is not silently accepted—the control reports an explicit support/instrument failure;
4. the artifact records:

   * incumbent-retention count;
   * assignment Hamming distance;
   * target displacement per agent;
   * action-vector divergence from `constructive_mixed`;
   * realized individual assignment run lengths.

No empirical fraction threshold should be invented. The core exposure predicate is exact: zero retained eligible incumbents.

A proof-sized development exercise should establish that this intervention genuinely produces one-check individual lifetimes before any conclusion-bearing population is selected.

## Separating outcomes

### Corrected forced-renewal control is still equivalent

Then the result becomes genuine source/mechanism evidence:

> S7-S3 does not require persistent individual duty ownership at the registered cutoff-equivalent scale; coordinated full renewal can compensate.

At that point, S7-S3 should be retired as the carrier of the individual-persistence-necessity proposition, although it may remain useful for other roster or coordination questions.

### Corrected forced-renewal control is materially worse

Then Part A passes, and the source remains eligible for a fresh focal audit.

### Full derangement cannot be defined without arbitrary or source-breaking restrictions

Then the Part-A premise is not operationally identifiable on this source. The appropriate response is to move the carrier-capacity test to a source with non-transferable tenure state, rather than continue renaming recomputation as renewal.

## Retained alternatives

| Route                                               | Status                            | Raising or lowering observation                                                                   |
| --------------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Exposure-certified minimum-cost derangement**     | **Selected for derivation**       | Raised if it guarantees zero incumbent retention without changing information or physical support |
| Current greedy recompute-every-check control        | Retained as an ordinary reduction | Useful as a frequent-replanning baseline, but not as forced renewal                               |
| Narrow the thesis to unilateral focal renewal value | Parked                            | Requires explicit abandonment of the global source-necessity claim                                |
| Tenure/non-transferable-state source                | Retained fallback                 | Raised if S7-S3 cannot support a valid forced-renewal comparator                                  |

## D7.3 and D8

# **Both remain blocked**

The current run does not establish:

```text
PERSISTENCE_NECESSARY_SOURCE
```

and the Part-A control does not identify the intended full-renewal counterexample.

The masked focal states do not unblock the ladder:

* stable is affirmatively nonmaterial;
* flex is unresolved;
* global source necessity is unestablished.

No R30, D7.3, D8, or broader variable-lifetime conclusion follows.

---

## Smallest retained result

The durable result from run `30403322062` is:

> On eight fresh S7-S3 topologies, the implemented greedy duty-map recomputation at every shared check was externally equivalent within five (G)-units to the event-driven `constructive_mixed` schedule, while the focal stable contrast was affirmatively nonmaterial and the focal flex contrast unresolved. Because actual individual-renewal exposure in the Part-A arm was neither guaranteed nor measured, this is an instrument/baseline result rather than evidence that individual persistence is unnecessary.

This review authorizes neither a corrected implementation nor further compute.
