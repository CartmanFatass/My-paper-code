# Scientific ruling — D7 design and the R42–R45 lineage

**Stage reviewed:** `9c63bea797142d2882a99699666532a46c2984b1`

## Overall disposition

**MODIFY D7 BEFORE EXECUTION.**

The R42–R45 lineage does **not** retire D7 and does not retire the co-adaptive R30 variable-lifetime line. It does, however, retire or sharply constrain one D8 realization:

> A renewal gate attached to a frozen skill controller and trained from next-check or natural-support credit is not a live successor; that combination has already produced an identified negative.

D7 should be split into a carrier/source positive control and a target-source audit. Its interventional half is mandatory for any claim that heterogeneous renewal urgency has been established. A frozen-policy evaluation can carry both the descriptive and interventional halves; learning feedback is not required for a policy-conditional causal diagnostic.

Before D7 runs, two unresolved estimand choices must be added to D0/D7:

1. what “force SET” does with the new-skill factor;
2. the primary continuation horizon (H).

The existing D0 formula does not fully specify either.

---

# Q1 — Does the R42–R45 lineage bind this line?

## Decision

### D7: not retired

D7 is a diagnostic asking whether renewal urgency exists and whether R30 can express it. R44 was a valid negative for a **frozen-source K50 renewal-timing route**, while R45 retired natural-support renewal-credit identification on the Alice–Bob K50 substrate. The recorded decisions are explicitly local: R44 retires the frozen-source route, and R45 retires that substrate/estimand pair.

The R30 learned-keep carrier differs materially:

* KEEP is an explicit learned factor rather than an incumbent-skill collision;
* the skill and renewal decisions share one autoregressive controller;
* the controller observes current skill, age, roster context, local observation, compact context, and team context;
* a SET necessarily selects a non-incumbent skill in the learned-keep branch.

That is enough to keep D7 live, but not enough to assume that co-adaptation solves the old failure.

### D8: one realization is bound, the class is not

R44 refutes the proposition:

> A trainable binary renewal factor with a live gradient path, attached to the frozen source and credited under the registered K50/next-check construction, is sufficient to produce heterogeneous renewal behavior.

Its actor moved, all registered gradient exposures were finite and nonzero, yet deterministic behavior remained full-sync renewal with zero minimum per-agent marginal.

Therefore:

* **D8-frozen**—freeze the primitive skill controller and train only a stable/flexible renewal gate—is not a valid successor unless its credit/action authority is structurally different from R44.
* **D8-coadaptive**—retain the R30 architecture, jointly train skill selection and renewal, and constrain only the renewal-regime representation—remains live.

The phrase “primitive skill policy unchanged” in D8 must mean **unchanged architecture and information contract**, not frozen weights. If it means frozen weights, D8 is currently too close to R44 and should be dropped rather than built.

## The correct lessons from R44 and R45

“Do not freeze the controller” is too broad as a durable theorem. R44 did not isolate freezing from:

* next-check credit;
* its K50 temporal substrate;
* the frozen source distribution;
* or the overlay factorization.

The narrower rule is:

> Do not reproduce the combination of frozen skill policy, renewal-only adaptation, and the R44 credit horizon as the proposed mechanism. If a frozen controller is retained, it is a negative or mechanism-matched control, not the preferred candidate.

The three constraints in D7 are otherwise directionally correct:

1. **Natural renewal frequency is descriptive, not causal identification.** R45’s natural-support overlap failure means D7 cannot infer renewal value merely from what the current policy happened to sample.
2. **Nonzero gradients and parameter drift are insufficient.** Collapse gates must precede behavioral interpretation.
3. **The old collapse statistics should be reused where their semantics transfer.**

## Missing constraints

### 1. Separate source opportunity from current-policy competence

D0 currently writes:

[
U_i(t,\Delta)
=============

## E[G\mid \text{re-decide}]

E[G\mid \text{KEEP}],
]

but “re-decide” is underspecified. Under learned-keep R30, SET excludes the incumbent skill, so the return depends on which non-incumbent skill is selected.

D7 should record two estimands:

[
U_i^{\mathrm{opp}}(h;H)
=======================

\max_{z\neq z_i}
Q^\pi_H(h,\mathrm{SET}(z))
--------------------------

Q^\pi_H(h,\mathrm{KEEP}),
]

[
U_i^\pi(h;H)
============

E_{z\sim\pi_{\mathrm{SET}}(\cdot\mid h)}
Q^\pi_H(h,\mathrm{SET}(z))
--------------------------

Q^\pi_H(h,\mathrm{KEEP}).
]

* (U^{\mathrm{opp}}) asks whether the source and available skill support contain a valuable renewal.
* (U^\pi) asks whether the current conditional SET policy can exploit it.

For (U^{\mathrm{opp}}), the maximizing skill must be selected on one replicate set and evaluated on an independent replicate set. Otherwise maximization over noisy returns produces an optimistic source effect.

### 2. Freeze the intervention horizon

For R30, a KEEP token commits only until the next shared check opportunity. Therefore:

* (\Delta) should be one check interval;
* the policy resumes normally at the following check;
* the return horizon (H) must be long enough to include the claimed downstream consequence.

For the toy, the primary (H) should be one complete slow period, (30) primitive steps, with the next-check (H=5) contrast retained as a secondary temporal localization. The source itself sets these two clocks at (5) and (30) steps.

The main-scenario (H) must be frozen from its causal duty window before D7-main runs.

### 3. Add a source/access prerequisite

A negative D7 result is not interpretable if the policy cannot produce useful individual skills. The previous toy run was a credit-anchor negative under native categorical edit, where KEEP was not a decision; it did not establish learned-keep carrier failure.

D7 therefore needs an upstream competence condition:

* the low-level skill/action channel can realize both temporal duties;
* the high controller can assign those behaviors;
* both slow and fast task components are above a registered access floor.

A supplied or verified primitive executor is acceptable for this **carrier positive control**, but any result using it supports only temporal-controller capacity, not naturally learned skill semantics.

### 4. Condition the collapse statistics on opportunity type

Full-sync SET can be correct at a history where all commitments need renewal. Discordance must therefore be reported:

* globally;
* and specifically on **mixed-urgency histories**, where at least one commitment should persist and another should renew.

Otherwise an average full-sync statistic can misclassify legitimate synchronized changes as collapse.

---

# Q2 — Which source should D7 use?

## Decision

**Accept the two-timescale toy as the default carrier positive control. It does not replace the main-scenario D7 audit.**

The toy has several properties that make it unusually suitable:

* identical constant local observations;
* centralized slow and fast targets;
* one target changes every five steps, the other every thirty;
* a shared permutation-invariant reward chooses the better assignment;
* no environment-provided agent role identity.

The shared reward is not an objection. At a particular history, current assignments and commitments break the instantaneous symmetry, so a focal KEEP/SET intervention has a well-defined team-return effect. The property is per-agent-time renewal urgency, not a permanent agent identity.

The toy proves only:

> Given genuine heterogeneous temporal duties, can the learned-keep carrier form different renewal behavior?

It cannot prove that the main scenario naturally contains such duties. The main scenario remains necessary before D8 is promoted.

## Positive-control pass condition

Use the toy’s known temporal structure only in the evaluator. Do not feed “fast” or “slow” to the policy.

Normalize paired return effects by the feasible (H)-window task-utility range, so that (\tilde U) is expressed on a unit external-utility scale. Evaluate primarily at checks where the fast target changes while the slow target does not.

### A. Competence prerequisite

Before reading renewal behavior:

[
\operatorname{LCB}_{95}(\text{slow-match}) \ge 0.75,
]

[
\operatorname{LCB}_{95}(\text{fast-match}) \ge 0.75.
]

The source defines an exact match as (1) and a zero action as (0.5), so (0.75) is a meaningful halfway access floor rather than a threshold fitted to the result.

Failure here is:

> `NO_ACCESS_D7_TOY_POSITIVE_CONTROL`

It does not update R30 renewal capacity.

### B. Interventional urgency separation

On mixed-urgency checks:

[
\operatorname{LCB}*{95}
\left(
E[\tilde U*{\mathrm{flex}}-\tilde U_{\mathrm{stable}}]
\right)
\ge 0.20,
]

[
\operatorname{LCB}*{95}
\left(
E[\tilde U*{\mathrm{flex}}]
\right)
\ge 0.10,
]

[
\operatorname{UCB}*{95}
\left(
E[\tilde U*{\mathrm{stable}}]
\right)
\le 0.05.
]

This requires:

* renewal is materially useful for the fast commitment;
* it is not materially useful for the stable commitment;
* and the difference is not just a tiny statistically detectable effect.

### C. Natural learned-keep alignment

On those same checks:

[
\operatorname{LCB}_{95}
\left(
P(\mathrm{SET}\mid\mathrm{flex})
--------------------------------

P(\mathrm{SET}\mid\mathrm{stable})
\right)
\ge 0.50,
]

with

[
\operatorname{LCB}_{95}P(\mathrm{SET}\mid\mathrm{flex})\ge0.75,
]

[
\operatorname{LCB}_{95}P(\mathrm{KEEP}\mid\mathrm{stable})\ge0.75.
]

Also require:

[
\operatorname{UCB}_{95}
P(\text{full-sync SET}\mid\text{mixed urgency})
\le0.25.
]

These are deliberately stronger than “nonzero discordance.” A positive control should demonstrate the behavior clearly enough to separate carrier access from a weak noisy tendency.

### Interpretation

* Interventional separation passes, natural hazard fails: the source and action support contain the capability, but the current policy/credit does not use it.
* Both pass: carrier positive control passes; proceed to the main source.
* Competence fails: upstream access failure; no renewal conclusion.
* Interventional separation fails despite competence: the learned skill support or chosen source does not expose renewal urgency as registered.

---

# Q3 — Is the interventional half required?

## Decision

**Yes. It is mandatory for the claim that heterogeneous renewal urgency has been established.**

Natural hazard, KEEP frequency, and realized lifetime remain valuable descriptions, but they cannot distinguish:

* useful persistence;
* controller inertia;
* insufficient exploration;
* bad skill semantics;
* or a reward-insensitive gate.

That is exactly why D0 defines renewal urgency counterfactually, and why R45’s natural-support result matters.

## CRN replay versus state restoration

**Exact common-random-number replay from a shared prefix is an acceptable substitute for an environment snapshot hook.**

A snapshot hook is not scientifically privileged. What matters is equality of the pre-intervention history.

CRN replay is valid only if all of the following are established:

1. reset seed, environment ledger, policy snapshot, recurrent state initialization, active skills, ages, masks, and team context are identical;
2. all actions and random draws before the focal token are reproduced exactly;
3. at the focal token:

   * KEEP is forced in one branch;
   * SET is forced in the other;
   * the SET skill is generated under the frozen registered rule;
4. later autoregressive factors are **regenerated** under the modified prefix using the same base random variables—they are not held at factual values;
5. environment and primitive-policy randomness after the intervention use matched counter-based or replayable streams;
6. the state immediately before the intervention has an exact equality check or a registered numerical tolerance;
7. no optimizer or policy update occurs between paired branches.

R30 helps with this because the conditional skill sample is drawn even when KEEP is selected; RNG consumption need not depend on the KEEP/SET outcome.

The forced implementation must nevertheless consume the same Bernoulli and categorical base draws in both branches. A teacher-forced path that bypasses one draw can silently shift every later random choice.

For the two-timescale toy, CRN replay is particularly strong: its only environment randomness is the seeded initial target signs; subsequent targets and transitions are deterministic functions of time and actions.

If the main environment contains hidden mutable state or RNG consumption that cannot be reconstructed and checked from reset plus prefix replay, then a snapshot/restore hook becomes mandatory for D7-main.

## Continuation semantics

D7 should estimate the **total policy-mediated effect**:

* positions before focal token (i): fixed;
* focal token: forced KEEP or SET;
* later same-check agents: allowed to react to the changed autoregressive prefix;
* later checks and primitive actions: generated by the same frozen policy under CRN.

Holding later factual actions fixed would estimate a different direct effect and would not match the deployed autoregressive policy.

## Is descriptive-first sufficient for D8?

No.

Descriptive-only evidence may justify implementing the interventional audit, but cannot authorize D8. At most it supports:

> The current policy naturally produces nonuniform renewal behavior.

It does not establish that the behavior tracks beneficial re-decision.

---

# Q4 — Does the frozen-checkpoint route qualify?

## Decision

**Yes, conditionally. A fresh rollout from a qualified frozen R30 checkpoint can carry both D7’s descriptive and interventional halves.**

The absence of `active_skills`, `skill_age`, and `has_active_skill` from the checkpoint prevents reconstruction of **past training-time commitment trajectories**. It does not prevent fresh evaluation rollouts:

* load policy weights;
* reset the environment and agent commitment state;
* generate a reproducible prefix;
* branch at a selected check;
* measure (U^\pi) and (U^{\mathrm{opp}}).

The existing exporter already demonstrates the basic checkpoint-to-fresh-environment path: it loads weights without optimizers, constructs a new evaluation environment, resets agent state for each episode, and runs deterministic fresh rollouts.

A checkpoint is eligible only if the evidence record establishes:

* it uses `r30_fixed_clock_ar_edit`;
* learned-keep is live, not native categorical edit or force-refresh;
* the source matches the D7 source being audited;
* external reward is pure;
* entropy floors and forced-renewal interventions are disabled or explicitly separated;
* the checkpoint has adequate task/skill access;
* exact configuration and policy snapshot are known.

The current evidence establishes that adaptive R30 arms existed, but does not establish that a qualified checkpoint satisfying those conditions is available. That remains a preflight fact to determine.

## Does frozen evaluation carry the interventional half?

Yes.

The interventional quantity is policy-conditional:

[
U_i^\pi(h;H).
]

The intervention need not feed back into learning. In fact, freezing the policy while estimating the causal effect is desirable: both branches then refer to one policy snapshot.

What it does **not** establish:

* how the renewal behavior emerged during training;
* a search-cost curve;
* stability of urgency across training;
* or whether D8 can learn faster than unrestricted R30.

A positive frozen-checkpoint D7 can establish source heterogeneity and current-policy use. A negative frozen-checkpoint result cannot distinguish:

* absent source heterogeneity;
* an insufficient checkpoint;
* a bad skill policy;
* or renewal-credit failure.

A negative therefore sends the line to the toy positive control rather than retiring the carrier.

## Export-host cautions

`export_substrate_gate.py` is a host, not an acceptable D7 metric path as written:

* it exports completed `SegmentManager` records, which D0 shows are the wrong unit for R30 lifetime;
* its primary role rows contain named `role_label`, `role_name`, and relay/service scores.

D7 must instead emit an event ledger keyed to genuine SET decisions and `skill_age`.

Named relay/service fields may be retained only as a **secondary post-hoc validation** after label-free urgency has been established. They must not:

* define the primary strata;
* enter the controller;
* set the acceptance branch;
* or substitute for the paired urgency estimand.

---

# Q5 — Comparator and acceptance

## Is the best-fixed sweep required for D7?

**No. Defer the full sweep to D8 or the first arm that makes the paper-level comparative claim.**

D7 asks whether:

* the carrier can express heterogeneous renewal;
* the source contains heterogeneous urgency;
* and natural R30 behavior aligns with it.

None requires identifying the globally best shared fixed lifetime.

For the toy positive control, use two analytically meaningful fixed controls:

1. refresh every check—the fast-duty extreme;
2. refresh every six checks—the slow-duty extreme.

A small complete sweep over shared lifetimes (1,\ldots,6) is acceptable if it is evaluation-only and cheap, but it is a source characterization, not yet the paper’s “best fixed” comparator.

For the main D7 diagnostic, one pre-existing defensible fixed controller is enough as an access/context control. The final constrained-variable-(k) comparison must later conduct the registered best-fixed sweep under matched training and optimizer exposure, as the research goal requires.

The D7 ledger entry should therefore no longer say it is paired against the “strongest shared fixed-lifetime control” in the paper-level sense.

## General acceptance criterion for heterogeneous renewal urgency

For the target source, define a source-independent normalization:

[
\tilde U = U/B_H,
]

where (B_H) is frozen before the audit as either:

* the feasible external-utility range over (H); or
* a constructive-minus-null external-return gap obtained from a separate source control.

It must not be estimated from the D7 treatment outcome.

Use episode- or ledger-disjoint discovery and audit splits.

### Label-free regime discovery

On the discovery split, fit a two-regime predictor using only permitted decision-time information. This is diagnostic; it does not update the policy.

On the untouched audit split, require:

1. each predicted regime contains at least (20%) of supported opportunities;
2. for the high-urgency class:

[
\operatorname{LCB}*{95}E[\tilde U*{\mathrm{high}}]\ge0.10;
]

3. for the low-urgency class:

[
\operatorname{UCB}*{95}E[\tilde U*{\mathrm{low}}]\le0.05;
]

4. class separation:

[
\operatorname{LCB}*{95}
E[\tilde U*{\mathrm{high}}-\tilde U_{\mathrm{low}}]
\ge0.20.
]

This supports:

> The source contains two decision-time-predictable renewal-urgency regimes of material size.

If interventional (U) varies but no decision-time predictor transports to held-out episodes, report:

> `HETEROGENEOUS_BUT_NOT_LOW_CARDINALITY_PREDICTABLE`

That result establishes heterogeneous opportunity but does not support D8.

If no source competence or action support exists, report no-access rather than no heterogeneity.

Natural SET probabilities are read only after source urgency is identified:

* aligned;
* unresolved;
* anti-aligned.

Current-policy alignment is not part of the source-heterogeneity gate.

## R43/R44 M3 quantities

Report the transferable quantities, but not “verbatim” without semantic adaptation.

### Transfer directly

* discordance rate;
* full-sync SET rate;
* per-agent KEEP/SET marginals;
* normalized entropy of SET targets;
* actor/critic gradient-exposure counts;
* parameter drift.

The old summarizer computes per-agent rates, discordance, full-sync renewal, and normalized renewal-target entropy.

### Modify

* condition discordance and full-sync rates on mixed-urgency opportunities;
* report both full-sync SET **and full-sync KEEP**;
* add per-urgency-regime marginals, not only fixed-agent marginals;
* retain branch identity and censoring reason.

### Do not interpret

“Same-label renewal” is structurally unavailable in learned-keep R30 because the incumbent skill is masked from the SET distribution. A reported value of zero would be a tautology, not evidence against collapse.

Record it as:

> `NOT_APPLICABLE_STRUCTURALLY_EXCLUDED`

Under native-categorical edit, incumbent collisions should be reported separately as categorical collision rate, never as KEEP behavior.

---

# Q6 — Revised ordering

The prior-art line and checkpoint route change the ordering. The revised scientific sequence is:

|  Order | Action                                                                                     | Interpretation                                                                                                                                                 |
| -----: | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|  **0** | **D7 estimand completion**                                                                 | Freeze SET-skill semantics, (U^{\mathrm{opp}}) versus (U^\pi), (\Delta), primary (H), continuation semantics, and the source-normalization scale.              |
|  **1** | **Qualified-checkpoint preflight**                                                         | Determine whether an eligible learned-keep checkpoint exists on the toy or intended main source. This is a repository/evidence check, not a result.            |
| **2A** | **Frozen-policy D7 audit on the intended source**, if an eligible checkpoint exists        | Evaluation-only descriptive plus interventional audit. A positive result may establish both carrier use and source heterogeneity without another training run. |
| **2B** | **D7 toy positive control**, if no eligible checkpoint exists or 2A is negative/unresolved | Test learned-keep carrier capacity under known heterogeneous timescales, with an upstream skill/access prerequisite.                                           |
|  **3** | **D7 main-scenario urgency audit**, unless already settled positively by 2A                | Establish label-free, intervention-identified source heterogeneity.                                                                                            |
|  **4** | **D8-coadaptive two-regime gate**                                                          | Build only if D7-main establishes predictable low-cardinality urgency. D8-frozen is dropped.                                                                   |
|  **5** | **D3′ richer R30 renewal conditioning**                                                    | Only if D8 is insufficient under identified source conditions.                                                                                                 |
|  **6** | **D1′ legacy bias diagnostic**                                                             | Comparator-specific; not on the critical path unless legacy behavior must be explained.                                                                        |
|  **7** | **D4 self-learned duration set**                                                           | Parked behind a causal non-collapse criterion.                                                                                                                 |
|  **8** | **D5 blocking credit fragment**                                                            | Reactivate only if identified source opportunity and policy capacity exist but renewal learning remains credit-limited.                                        |

The main change is that D7 is no longer one paired training run. It is a staged diagnostic:

1. cheapest qualified frozen-policy audit;
2. carrier positive control if needed;
3. target-source evidence.

---

# Smallest portfolio updates

## Retired

* A frozen-controller D8 whose only learned component is a binary renewal gate under R44-like next-check credit.
* Natural KEEP/SET frequency as evidence that renewal is beneficial.
* Same-label renewal as an R30 learned-keep collapse statistic.
* A full best-fixed sweep as a prerequisite for D7.

## Retained

* D7 as a descriptive and interventional diagnostic.
* Co-adaptive R30 as the primary unrestricted carrier.
* D8 as a co-adaptive low-cardinality renewal constraint.
* Legacy duration as a frozen comparator and bias diagnostic.
* G20R3 as parked infrastructure.

## New retained lemma

> The source opportunity to renew and the current policy’s ability to select a useful replacement skill are different estimands and must not be collapsed into one D7 number.

## Reactivation condition for a structurally different carrier

If the toy passes under a supplied/verified executor but jointly learned R30 repeatedly cannot produce urgency-aligned renewal despite identified source effects and valid credit, reopen:

* true per-agent event-triggered check opportunities;
* rather than another shared-check renewal overlay.

That would alter the physical decision clock rather than only the realized KEEP run.

**This review selects and modifies the evidence sequence. It does not authorize implementation, a bounded run, or formal compute.**
