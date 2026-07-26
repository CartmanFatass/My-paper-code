# Scientific ruling — D7.S Part B flex arm and instrument

**Stage reviewed:** `62dcd92155a9bf0bf9be0f72cbf167bc7596ab65`

## Overall verdict

**The current Part B instrument does not instantiate the frozen (U^*_{i,\mathrm{src}}) gate. Preserve its numerical output as a narrow, single-topology controller diagnostic; do not close `PERSISTENCE_NECESSARY_SOURCE`. Re-register and rerun one event-aligned, two-limb source audit. D8 remains blocked.**

The pooled arithmetic and provenance are credible **for the instrument that actually ran**: the pooler concatenates seed-contiguous per-episode observations, checks topology and configuration identity, and recomputes all statistics using the monolithic-run functions rather than averaging shard ratios.

The problem is semantic realization, not pooling or episode count. At least seven discrepancies prevent a source-gate reading:

1. The frozen design’s constructive controller **holds stable assignments while renewing flexible ones**, whereas the implementation’s `constructive` arm re-decides every duty at every check—the design’s full-sync alternative, not its constructive mixed policy.
2. `set_flex` is exactly the implemented `constructive` arm, including identical energy diagnostics and returns.
3. KEEP is imposed for all (H), while D0 freezes the focal action’s commitment to one (\Delta).
4. The frozen history class is an evaluator-certified mixed-urgency history with active commitments; the code chooses UAV indices `0` and `n_relay` at reset, before any incumbent commitment exists.
5. The SET term uses one fixed exchange partner rather than the required maximization over legal alternatives and joint continuations.
6. (B_H) is measured from one reset-to-end window, while the freeze requires event/check-aligned windows and treatment-independent source controls.
7. The instrument’s primary return is an unclipped rate-ratio proxy, while the registered S7-S3 source identifies controls using the PBRS-free task safety score containing QoS, return cost, cutoff and depletion terms.

The exact six-arm table was not enumerated in the protected freeze; it appeared in the realization. Correcting it is therefore not a change to the high-level source hypothesis, but it **is** a protected implementation binding and must be registered before another conclusion-bearing measurement.

---

# Q1 — Repair, drop, or re-scope `set_flex`?

## Ruling: **repair the two-sided gate**

Do not drop the flex limb. The paper’s source prerequisite is not merely that some assignment should persist; it is that one current commitment should beneficially persist **while another should beneficially renew**. A stable-only result cannot establish heterogeneous individual renewal urgency.

The repaired stable and flex limbs should use **the same formal focal intervention**. Their difference should come only from the evaluator-certified history class.

For mechanism (m\in{\mathrm{stable},\mathrm{flex}}), at a qualified check history (h_m):

[
V^{\mathrm{KEEP}}_m(h_m)
========================

\max_{\text{legal joint continuation}}
E[G_{H_m}\mid
\text{focal commitment held for exactly }\Delta],
]

[
V^{\mathrm{SET}}_m(h_m)
=======================

\max_{\substack{z\neq z_i\
\text{legal joint continuation}}}
E[G_{H_m}\mid
\text{focal agent reassigned to }z\text{ for exactly }\Delta],
]

[
U^*_{m,\mathrm{src}}
====================

V^{\mathrm{SET}}_m-
V^{\mathrm{KEEP}}_m.
]

After the single (\Delta)-interval intervention, all constraints are released and both branches receive the same best legal continuation.

### Exact flex realization

The flexible history should be an **actual energy-driven handoff opportunity**, not “the first service UAV at reset”:

* a current duty is about to be or has just been vacated by a UAV entering its charge-return/absence process;
* at least one active survivor has a legal alternative assignment that can cover the vacated duty;
* the focal flexible agent is selected by an evaluator from current physical state, not by fixed slot;
* `SET_flex` forces that focal survivor to take the best legal alternative duty for one (\Delta);
* `KEEP_flex` forces it to retain its incumbent duty for one (\Delta);
* every non-focal assignment is optimized in both arms.

Do **not** freeze the non-focal duties. That would compute a direct effect under an artificial continuation rather than the source-level best joint continuation.

A forced SET need not do something behaviorally “beyond constructive.” If the optimal mixed constructive continuation contains the focal SET, then the focal SET branch may coincide with that controller. The requirements are:

1. the focal decision is explicit;
2. the arm is evaluated on the audit split;
3. (B_H) is estimated from separate source-control data;
4. the current `constructive` label is corrected so that it actually means mixed stable/renewal behavior rather than full-sync reassignment.

## Q1.1 — CRN and fresh environments

**Retain both.**

Every arm must start from an identical pre-intervention history, topology, energy assignment, user-motion stream and random state. Fresh environment instances remain necessary because the environment reset has already been shown to leave mutable state behind, while topology is generated outside ordinary episode seeding.

For each focal history:

* selection replicates choose the maximizing legal SET alternative;
* independent evaluation replicates estimate its return;
* KEEP and the selected SET continuation use common random numbers;
* the complete pre-intervention physical and assignment state must be checked, not assumed.

## Q1.2 — Do the (\pm0.10) thresholds survive?

**The numerical magnitude may survive as a common materiality convention, but not through one shared denominator or a point-only ratio gate.**

Once repaired, stable and flex are the same mathematical action contrast evaluated on different history classes. It is therefore coherent to retain a ten-per-cent materiality standard:

[
U^**{\mathrm{stable}}/B*{\mathrm{stable}}\le -0.10,
\qquad
U^**{\mathrm{flex}}/B*{\mathrm{flex}}\ge +0.10.
]

But each limb requires:

* its own causal horizon (H_m);
* its own independently measured (B_m);
* and its own confidence-bound decision.

The gate should operate on linear threshold contrasts rather than unstable ratios:

[
T_{\mathrm{stable}}
===================

U^**{\mathrm{stable}}+0.10B*{\mathrm{stable}},
]

[
T_{\mathrm{flex}}
=================

U^**{\mathrm{flex}}-0.10B*{\mathrm{flex}}.
]

Require:

[
\operatorname{UCB}*{95}(T*{\mathrm{stable}})<0,
]

[
\operatorname{LCB}*{95}(T*{\mathrm{flex}})>0,
]

and independently:

[
\operatorname{LCB}_{95}(B_m)>0.
]

This directly tests the registered thresholds without dividing by bootstrap samples whose denominators may cross zero.

## Q1.3 — stable-only close

My ruling selects repair, so the proposed stable-only gate is not the successor.

A repaired stable limb may nevertheless emit a partial source result such as:

> `MATERIAL_STABLE_PERSISTENCE_IDENTIFIED`

That means only that maintaining one class of commitment has material source value. It does not establish heterogeneous renewal urgency and does not unblock D8.

The current ep64 record cannot close even that repaired limb because Q1.4, Q1.5, Q2 and Q2.3 all come out adverse. No conclusion may rest on the point ratio clearing `−0.10`.

## Q1.4 — history class

**The hard-coded role-index selection is not an acceptable realization of the frozen history class.**

The fact that slot `0` is generated as a relay-like target does not make fixed-slot selection compatible with:

* evaluator-only classification;
* anonymous individual semantics;
* or the requirement that an incumbent commitment already exist.

The repaired audit must certify each history from realized state. At minimum:

* a stable incumbent’s current backhaul/service target remains locally optimal or materially unchanged over the relevant (\Delta);
* a flexible opportunity is currently present because of a charge-driven vacancy or another registered state transition;
* both exist at the same supported check;
* the selected focal agents are active and have valid incumbent commitments.

The ep64 observation is therefore evidence about the fixed protocol “UAV 0 versus UAV 2 from reset,” not about the frozen mixed-urgency history population.

## Q1.5 — max over (z)

**The max is mandatory. One fixed exchange partner does not realize (U^*_{\mathrm{src}}).**

For stable persistence:

[
\max_z V(\mathrm{SET}(z))\ge
V(\text{the one tested swap}).
]

Consequently, a negative fixed-partner contrast can overstate the cost of SET and falsely establish persistence necessity. The measured `−40.602` says that **one exchange is costly**; it does not say the best legal exchange is costly.

Where the legal alternative set is finite, enumerate all supported alternatives. Selection and evaluation must be separated unless the continuation is exactly deterministic and analytically evaluated.

## Registration and branch reachability

Part A has already structurally rejected zero-cost exchange. Part B should not silently advertise `ZERO_COST_ROLE_EXCHANGE_SOURCE` as an executable branch that no code can emit.

The corrected structure should be:

* Part A records the non-transferable-state certificate.
* Part B emits stable/flex limb outcomes and the combined source outcome.
* A `full_sync_SET` arm remains as a conformance diagnostic.
* If it unexpectedly matches the mixed constructive optimum, emit an invalidating **Part-A contradiction** and reopen the structural ruling.

---

# Q2 — Must KEEP last exactly one (\Delta)?

## Ruling: **yes**

A KEEP decision under R30 commits only until the next shared check. D0 therefore correctly freezes:

[
\Delta = 10\text{ primitive steps}.
]

Holding a focal target for all (H=1500) measures:

> permanent or whole-window assignment locking versus one initial exchange.

It does not measure the consequence of one KEEP action.

The repaired arms must:

1. force KEEP or SET for one (\Delta);
2. release the constraint at (t+\Delta);
3. use identical optimal continuation afterward.

### Standing of the ep64 result

The following survive:

* cross-day/process reproducibility of the implemented instrument;
* evidence that energy and charging activity occur at (H=1500);
* the existence of a large cost for the specific whole-window UAV0/UAV2 exchange protocol;
* the single-topology whole-episode constructive-null difference.

The following do not survive:

* either (U^*_{\mathrm{src}}) margin;
* either normalized margin;
* the two-sided gate;
* or `PERSISTENCE_NECESSARY_SOURCE`.

The corrected stable and flex arms should be rerun **once, jointly**, after all Q1–Q5 changes. Do not run one repair per defect.

The old per-episode variance is not transferable to the new estimands. It was generated by whole-window holds, a fixed exchange partner, reset histories and a different treatment definition.

## Q2.3 — (B_H) window

**The reset-to-end (B_{1500}) is not the frozen denominator.**

The denominator must begin at the same type of qualified check history as its corresponding treatment. It must also come from a disjoint source-control sample.

Use:

* (B_{\mathrm{stable}}): stable-mechanism source controls beginning at a certified stable check;
* (B_{\mathrm{flex}}): charge-handoff source controls beginning at the certified energy-driven renewal event.

Select at most one pre-registered qualifying event of each type per episode, or cluster all included events at episode and topology level.

The current reset-to-end (B_H=65.965) remains a whole-episode descriptive headroom measure. It cannot normalize the repaired event-conditioned margins.

---

# Q3 — May (H=1500) remain the gate horizon?

## Ruling: **no, not as one common focal-action horizon**

D0 already recognizes that this source contains two different causal windows:

* relay/duty exchange: approximately (139) steps;
* energy-driven roster change: first event plus charge dynamics, observed only at long horizons.

The earlier (H=1500) derivation includes the long waiting time from reset until the first charge event. Once the audit begins at the actual qualified event, that waiting time is no longer part of the focal action’s consequence.

Register:

[
H_{\mathrm{stable}}=139,
]

beginning at the stable mixed-urgency check, and

[
H_{\mathrm{flex}}=450,
]

beginning at the first qualified charge-handoff check.

The 450-step flex horizon is tied to the registered charge-duration/transit mechanism, not selected from the observed effect. If the event does not have a full 450 steps of remaining source support, that episode is right-censored or ineligible under a frozen support rule; the horizon must not be shortened post hoc.

### Status of (H=1500)

Retain it as a secondary whole-episode diagnostic:

* verifies that energy binds;
* describes total rotation-system consequences;
* and can support end-to-end G2 source controls.

It is not the primary D7.S focal-action gate.

The (H=139) result should not be demoted to a generic descriptive number: it is the appropriate stable-exchange limb once the history and (\Delta) are repaired.

The projected “52 episodes at (H=450)” came from the old reset-start, six-arm instrument and must not set the new budget.

---

# Q4 — topology scope

## Q4.1 — current record

The current result is acceptable only as:

> a topology-20260725, fixed-protocol diagnostic.

It is not a population statement about S7-S3.

The pooled record confirms that all 64 episodes used one topology seed and one fixed set of focal indices.

## Required paper-level scope

Use at least **eight fresh topology seeds**, excluding `20260725`, which has already influenced instrument development.

A suitable minimum audit allocation is:

* eight held-out topologies;
* eight audit episodes per topology;
* a disjoint source-control/calibration episode block for (B_{\mathrm{stable}}) and (B_{\mathrm{flex}});
* equal topology weighting.

Topology is the top-level independent unit. Use a hierarchical bootstrap:

1. resample topologies;
2. within each selected topology, resample episodes or qualifying events.

The primary gate is on the topology-population contrasts, not a requirement that every topology individually clear the threshold. Per-topology margins remain mandatory diagnostics; between-topology variability enters the hierarchical interval rather than being hidden by pooling 64 episodes from one geometry.

Record the actual BS/station coordinates or a hash of them, not merely the topology seed.

If this minimum design remains unresolved, report unresolved. Do not automatically increase the budget unless an expansion rule is frozen before the run.

## Q4.2 — wider repository effect

Do not invalidate every historical result globally.

Instead add a standing provenance rule:

> Any Scenario-7 result reused as a causal comparator, paper-level result or premise must establish whether all compared arms shared one topology or whether topology was sampled and analysed as an independent factor.

When topology equality is unprovable:

* preserve the historical artifact;
* scope its conclusion to its realized/unknown topology;
* do not use it as a matched causal control.

This audit should be performed as affected experiments are reused. It need not block unrelated research or reopen every closed historical line.

---

# Q5 — instrument caveats

## Q5.1 — saturation probe

The present reset-state clipped saturation probe is **obsolete as a validity test for the unclipped rate-ratio output**. A clipped fraction of `1.0` does not make an unclipped rate mean invariant; the 64-episode arm returns demonstrably differ.

Retain the probe only as evidence explaining why the clipped QoS proxy was retired.

There is, however, a more fundamental correction:

> The repaired source gate should use the registered G2 PBRS-free external safety score as primary (G), not the post hoc unclipped rate-ratio proxy.

The G2 source contract defines:

[
G_t=
\text{QoS satisfaction}
-2\cdot\text{return cost}
-5\cdot\text{new cutoff}
-10\cdot\text{new depletion}.
]

Use the unclipped rate ratio as a secondary mechanism-localization metric and report the safety-score components separately. This preserves the registered external task objective while avoiding PBRS or algorithmic shaping.

No extra measurement is needed to “rescue” the current unclipped arm separation. It remains valid for that proxy; it simply cannot carry the paper-level external-return claim.

## Q5.2 — ratio uncertainty

Do not retain a point-only gate.

The current code explicitly leaves uncertainty diagnostic and fires branches from point ratios.  The pooled result shows why that is insufficient: (B_H)’s ordinary 95% interval is positive, yet far-tail bootstrap resamples change denominator sign and the normalized stable interval reaches `−0.0566`.

The ratio may remain descriptive when (B_H) is identified. The gate must use the linear threshold contrasts specified under Q1.2.

This is a prospective measurement correction. It does not retroactively relabel the ep64 branch.

---

# Q6 — smallest supported claim and D8

## Smallest defensible claim from the current record

The record supports:

> On one pinned S7-S3 topology (`20260725`) and 64 paired episode seeds, the specific protocol that swapped duty indices 0 and 2 at reset and then followed the implemented whole-window target rules produced a mean 1,500-step unclipped-rate return (40.602) below the protocol that held UAV0’s initial target; the paired episode-bootstrap interval was ([-76.111,-4.736]). The whole-episode implemented `constructive-minus-null` difference was (65.965), with interval ([29.073,103.515]).

This establishes:

* the tested fixed exchange is costly under that topology and controller;
* energy and charging were active;
* the implemented source controls separate.

It does **not** establish:

* the best legal SET alternative is costly;
* a real incumbent’s one-(\Delta) KEEP is valuable;
* the frozen mixed-urgency history class;
* flexible renewal benefit;
* normalized source necessity;
* or a population claim across topologies.

## May the point condition close anything?

**No.**

Even without the realization defects, a stochastic source-threshold claim cannot be closed by a point estimate whose uncertainty does not establish threshold clearance. Mixed or underpowered evidence must remain unresolved under the project result semantics.

The stable point clearing by roughly six times is encouraging for the repaired stable limb; it is not a branch close.

## D8

**D8 remains blocked in every branch of this ruling.**

A repaired D7.S source gate would permit the next source-identification stage, D7.3. It would not itself authorize D8.

D8 requires, in order:

1. repaired stable and flex source limbs;
2. both materiality contrasts identified across held-out topologies;
3. D7.3 evidence that the urgency regimes are predictable from permitted decision-time information;
4. only then, a co-adaptive constrained renewal policy.

---

# Q7 — revised order

| Order | Action                                        | Why                                                                                                                                                                                                                              |
| ----: | --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **0** | **Reconcile the D7.S contract**               | Replace the current six-arm realization; freeze event-qualified histories, one-(\Delta) interventions, max-over-alternatives, mechanism-specific (H)/(B_H), registered external (G), interval semantics and topology population. |
| **1** | **Source-control conformance derivation**     | Prove that `constructive_mixed`, `full_sync_SET`, null, focal KEEP and focal SET are distinct and that every result branch is reachable or explicitly owned by Part A.                                                           |
| **2** | **Proof-sized development-topology exercise** | On topology `20260725`, establish exact history equality, event availability, max-selection/evaluation separation, arm distinction, and serialization. No scientific reading.                                                    |
| **3** | **One joint repaired D7.S audit**             | Eight fresh topologies, mechanism-specific stable and flex windows, independent (B_H) calibration, hierarchical uncertainty. Both limbs in one evidence action.                                                                  |
| **4** | **D7.3**                                      | Only if the repaired source gate identifies both persistence and renewal necessity. Establish label-free, decision-time-predictable low-cardinality urgency.                                                                     |
| **5** | **D8-coadaptive**                             | Only after D7.3.                                                                                                                                                                                                                 |
| **6** | **D3′ or blocking credit work**               | Only if the simpler gate is insufficient or valid source/capacity evidence isolates credit as the blocker.                                                                                                                       |

---

# Competing explanations preserved

| Explanation                                                                     | Current support                                             | Separating observation                                                            |
| ------------------------------------------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **E1 — stable persistence is genuinely material**                               | The fixed exchange has a large negative raw effect          | Best-over-alternatives, one-(\Delta), event-aligned stable limb across topologies |
| **E2 — flexible renewal exists only at charge-handoff events**                  | Reset-start `set_flex` is definitionally void               | Event-conditioned flex KEEP/SET at a real vacancy                                 |
| **E3 — the main source contains stable value but no material flexible renewal** | Current flex point is negative, but the arm is invalid      | Corrected flex limb under the registered safety score                             |
| **E4 — effects are topology-specific**                                          | Current evidence uses one topology                          | Hierarchical held-out-topology audit                                              |
| **E5 — the heuristic continuation is not the source optimum**                   | Current SET uses one partner and one heuristic continuation | Enumerated/maximized legal alternatives with independent evaluation               |

## Scheduled evidence action

The next scientific artifact should be the **re-registered event-aligned D7.S source contract**, not another run of the current six-arm script.

This review authorizes neither implementation nor compute.
