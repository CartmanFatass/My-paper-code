# Scientific ruling — research direction and exploration ledger

**Stage reviewed:** `05887e0d3b3d31879861d807ef91ea8542adf718`

## Overall disposition

**MODIFY THE THESIS FRAMING; SELECT R30 KEEP/SET AS THE PRIMARY CARRIER; HOLD G20R3; REPLACE D1 AS THE FIRST SCIENTIFIC ACTION.**

The branch should return to variable individual lifetime, but not under the current ledger’s causal story.

The defensible research question is not:

> Can a duration head be prevented from collapsing?

It is:

> Can a low-cardinality, learned structure over **per-agent renewal urgency** improve the finite-budget tradeoff between one shared fixed lifetime and unrestricted per-agent renewal?

That framing survives whether duration collapse occurs. Collapse is one possible failure mode of unrestricted lifetime learning, not the thesis itself.

The repository evidence also requires one terminology correction. The project principles distinguish the observation/check clock, the renewal opportunity, the realized skill segment, and the learning-credit window.  R30 keeps a shared check clock but produces a variable per-agent **realized commitment lifetime** through KEEP runs. Therefore, if R30 carries the paper, the paper should claim untied realized lifetime or renewal interval—not literally independent per-agent check clocks.

The user-intent portion of `RESEARCH_GOAL.md` is clear and load-bearing: agents face genuinely heterogeneous timescales, and the proposed contribution trades unrestricted temporal flexibility for tractable search.  Its “current state of the codebase” subsection must not be used as factual authority, however: the current round corrects its statements that legacy is the live research default, R30 did not complete, and collapse had never been observed.

---

# Q1. Is the framing a contribution?

## Ruling

**As stated, it is a standard design principle, not yet a paper contribution. It becomes defensible when the constraint is learned, role-agnostic, dynamically applicable, and shown to improve a registered search-efficiency tradeoff.**

“An unrestricted action space is expensive, so we constrain it and accept approximation error” is too generic. Discretized duration candidates, termination policies, and restricted temporal abstractions all instantiate that idea.

The non-obvious part would have to be the particular structural claim:

1. heterogeneous per-agent renewal timescales are causally present;
2. they can be predicted from decision-time information without supplied relay/service labels;
3. a small number of renewal regimes captures enough of that heterogeneity;
4. this structure improves finite-budget learning relative to both:

   * the best shared fixed lifetime; and
   * an unrestricted per-agent lifetime controller;
5. the result transports across anonymous roster changes and role reassignment.

The action-space-expansion premise itself is currently a hypothesis, not evidence. The legacy controller already restricts duration to four candidates, `(3, 7, 13, 24)`, and the policy is factorized rather than enumerating the entire joint action table.  It is plausible that the temporal sequence space remains prohibitively large, but the paper must measure that burden rather than infer it solely from cardinality.

## Q1a — smallest defensible paper claim

A suitably narrow claim would be:

> **On anonymous cooperative MARL tasks with heterogeneous per-agent renewal urgency, a decision-time-learned, low-cardinality renewal-class policy attains higher held-out external return than the best shared fixed renewal period and reaches a registered utility level with fewer environment interactions or high-level decision samples than an unrestricted per-agent renewal policy, under matched information, action support, and optimizer exposure.**

Necessary qualifiers:

* no hand-coded relay/service labels;
* no role-specific reward or lifetime reward;
* no claim of global or asymptotic optimality;
* “search cost” measured as interaction and optimization exposure, not merely wall time or nominal action-space size;
* role and membership permutations included in held-out evaluation;
* fixed-(k), unrestricted variable-lifetime, and constrained variable-lifetime comparators matched to their respective claims.

The durable evidence contract already requires environment interaction and optimizer exposure to be reported separately, because equal environment steps do not imply equal learning opportunity.

I would replace “we accept a suboptimal result” with:

> **We introduce a structured approximation that sacrifices unrestricted temporal expressivity for finite-budget learnability.**

“Suboptimal” relative to an unknown optimum cannot be established merely because the controller is constrained.

## Q1b — what would make the result non-obvious?

At least one of the following must hold:

* **Learned dynamic structure:** the stability class is inferred from generic decision-time state and can change for the same agent as its function changes.
* **Transport:** the learned renewal structure survives anonymous slot permutations, join/leave/rejoin, held-out team sizes, and role swaps.
* **Strong matched reductions fail:** a recurrent flat policy, best fixed-(k) sweep, unrestricted R30, and a simple two-clock gate cannot reproduce the result under matched exposure.
* **Measured search benefit:** constrained renewal reaches a utility target materially earlier or at lower high-level sampling cost than unrestricted renewal.
* **Intervention-sensitive use:** forcing a stable-class agent into the flexible renewal regime, or vice versa, changes persistence and external utility in the predicted direction.
* **Constraint usefulness without collapse:** the method helps even when unrestricted lifetime usage remains broad, establishing that the contribution is structural search efficiency rather than merely anti-collapse regularization.

A hard-coded rule “relay gets long, service gets short” would remain a UAV-specific heuristic, not a general MARL contribution.

---

# Q2. Is role stability the right primitive?

## Ruling

**The right primitive is not role identity and not selected duration. It is per-agent, state-dependent renewal urgency—or equivalently commitment stability.**

“Stable role” is useful intuition, but it risks turning relay/service names into supplied semantics. The algorithmically reusable quantity is:

[
\mathcal U_i(t,\Delta)
======================

## \mathbb E[G_t\mid \text{agent }i\text{ re-decides now}]

\mathbb E[G_t\mid \text{agent }i\text{ keeps its current commitment for }\Delta].
]

The two expectations must begin from the same pre-decision history and use the same continuation semantics.

Interpretation:

* **stable commitment:** withholding re-decision has negligible value loss over the relevant window;
* **flexible commitment:** an immediate re-decision has material expected value;
* the same lifecycle may move between these regimes;
* long or short realized lifetime is a consequence of this quantity, not its definition.

A hazard form is equivalent:

[
\lambda_i(t)
============

\Pr(\text{renewal is beneficial}\mid h_{i,t}).
]

A low-cardinality constraint can quantize this into two or a few renewal regimes.

## Q2a — which measurement is soundest?

| Proposed measurement                                     | Disposition                                                                                                                   |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Skill-assignment churn                                   | Diagnostic outcome only. It conflates true flexibility, exploration noise, skill-label symmetry, and a bad controller.        |
| Dwell time or realized lifetime                          | Diagnostic outcome only. It is circular if used to define the property the duration controller is supposed to learn.          |
| Duration-posterior entropy                               | Measures confidence or concentration, not whether re-decision is valuable.                                                    |
| Reward sensitivity to re-decision frequency              | Closest of the listed options, provided it is member-resolved, conditional on the same history, and based on external return. |
| Counterfactual renewal value / beneficial-renewal hazard | Preferred definition.                                                                                                         |

The first source-level evidence should therefore be an intervention or paired diagnostic that compares KEEP/hold against re-decision under the same decision history. It need not initially use a learned critic; a source-level counterfactual or controlled evaluation can establish whether the heterogeneous-timescale property exists before asking the policy to discover it.

The learned policy may later predict this quantity from decision-time information. It must not read named role labels, future events unavailable at decision time, or task-specific shaping.

## Q2b — does the first half stand alone?

**It stands alone as a source and representation lemma, not as the paper’s main algorithmic contribution.**

A meaningful first-half result would be:

> The registered environment contains at least two statistically distinguishable renewal-urgency regimes; the regime is predictable from permitted decision-time information, is invariant to anonymous slot permutation, and changes with an agent’s current function rather than fixed identity.

That result would:

* validate the benchmark as a carrier of heterogeneous temporal duties;
* justify a low-cardinality temporal abstraction;
* reject the simpler explanation that all agents should share one renewal frequency.

It would not establish that a learned period controller is useful. The second half is still required for the algorithm claim:

> Conditioning renewal on the learned regime improves external value or search efficiency over fixed and unrestricted alternatives.

A finding based only on churn clusters would not make the first half meaningful. It must be tied to counterfactual renewal value or another causal consequence.

---

# Q3. Order the exploration ledger

## Ruling

The existing ordering is not scientifically valid because D1 is cheap but does not settle what it claims to settle. The ledger’s own policy says a cheap probe that resolves nothing is worse than a slightly costlier one that separates directions.

The current D1 assumes legacy is the primary carrier, assumes collapse is still unobserved, and treats churn as role stability. All three premises need correction.

## Revised ordering

| Order | Direction                                            | Scientific role                                                                                                                                                                                                                                                                         |
| ----: | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **0** | **D0 — renewal-urgency and carrier derivation**      | Zero-compute. Freeze what “variable (k)” means—check clock versus realized lifetime—define renewal urgency, define search cost, and state how legacy and R30 instantiate the claim.                                                                                                     |
| **1** | **D7 — instrumented R30 renewal-process diagnostic** | First resource-consuming scientific action. Measure natural KEEP/SET hazard, realized lifetimes, renewal urgency evidence, truncation, exposure, and external value under the current reward-pure contract. Include the strongest shared fixed-lifetime control under matched exposure. |
| **2** | **D8 — learned two-regime renewal gate**             | Strongest simple constrained realization and ordinary reduction: a decision-time gate between stable and flexible renewal regimes, without a general duration catalogue.                                                                                                                |
| **3** | **Revised D3 — role-conditioned renewal on R30**     | Only if D7 establishes source heterogeneity and D8 is insufficient. Uses the same renewal-urgency primitive but allows richer state-dependent KEEP/SET behavior.                                                                                                                        |
| **4** | **Revised D1 — legacy-duration bias diagnostic**     | Diagnostic comparator only. Determine whether sampled-duration behavior differs because of short-segment sampling geometry or candidate truncation. It no longer “settles both premises.”                                                                                               |
| **5** | **D4 — self-learned low-cardinality convergence**    | Retain, but late. Without a causal stability condition it can reproduce pathological collapse and call it convergence.                                                                                                                                                                  |
| **6** | **D5 — G20R3 identification fragment**               | Parked. Reactivate only when a selected variable-lifetime mechanism is blocked by member-resolved delayed-credit identification.                                                                                                                                                        |

### D6

D6, workflow-grill validation, should not compete in the scientific exploration ordering. It is governance infrastructure. It may be completed operationally before scientific work resumes, but it does not answer a variable-(k) question and should live on a separate workflow lane.

## Missing direction: D8

The ledger needs the strongest simple reduction:

> A learned gate selects between two fixed renewal regimes using the same decision-time information, while the primitive skill policy remains unchanged.

This can falsify the need for a duration head or richer KEEP/SET model. If it succeeds, it may itself carry the paper’s constrained-search contribution. If it matches a more complex role-conditioned controller, the complex controller adds no demonstrated value.

## Q3a — what would change the ordering?

The ordering changes under the following observations:

* **No source heterogeneity:** paired KEEP-versus-redecide effects are indistinguishable across active agents and contexts. D8/D3 lose priority; the source is not identifying the intended claim.
* **Unrestricted R30 already succeeds cheaply:** heterogeneous lifetimes emerge naturally, fixed-(k) is beaten, and search cost is acceptable. The tractability constraint loses motivation; D3/D4 weaken sharply.
* **R30 cannot express the user’s literal target:** if the intended claim requires per-agent check opportunities rather than variable realized lifetimes, R30 becomes a comparator rather than the carrier.
* **Simple gate succeeds:** if D8 gives the full performance/search benefit, do not proceed automatically to richer D3.
* **Legacy and R30 disagree:** a collapse in legacy but not R30 would support the short-segment-bias explanation and demote collapse as a general variable-lifetime phenomenon.
* **Credit becomes the blocker:** if the selected renewal controller has source access and capacity but cannot assign delayed value to renewal decisions, reactivate only the minimum necessary part of D5.
* **Existing R30 artifacts permit a valid no-training audit:** if a qualified checkpoint and reproducible trajectory path can answer D7 without another training run, that cheaper route moves ahead.

## Q3b — drop or defer?

* **Drop D1 as currently stated.** Retain only the revised legacy-specific diagnostic.
* **Move D6 out of the scientific ledger.**
* **Do not drop D3, D4, or D5 as directions.**
* **D4 should be parked behind D8/D3**, because “convergence onto few durations” is observationally close to the known collapse pathology.
* **D5 remains held with an explicit reactivation condition.**

The current ledger says D1 is first because legacy is the live default, a completed legacy arm proves the current path trains, and collapse is unobserved.  The current fence corrects all three: legacy is the frozen comparator, the completed arm used a different candidate set, and collapse was recorded at R16.5.

---

# Q4. Is measuring collapse first the right move?

## Ruling

**No—not through D1 as written.**

A zero-compute carrier and estimand derivation is cheaper and already changes the question:

* collapse has been observed under R16.5 intrinsic pressure;
* the current open question is whether pathological concentration recurs under the current reward-pure contract;
* legacy can fabricate or amplify a short-duration reading through its sampling geometry;
* team-intent boundaries can structurally truncate long choices;
* the current `(3, 7, 13, 24)` legacy configuration has no completed run.

The config records both the R16.5 collapse pathology and the Z-boundary truncation condition.  It also marks the duration entropy floor as default-off stabilization rather than evidence that unconstrained learning is sound.

The first new behavioral diagnostic should be run on R30, because R30 is the more credible carrier of variable effective lifetime and does not inherit the precise legacy bias that the diagnostic is supposed to interpret.

## Q4a — what must be logged?

### Clock and carrier semantics

* observation/check interval;
* renewal opportunity count;
* selected KEEP/SET or intended duration;
* realized lifetime in:

  * check opportunities;
  * primitive steps;
* segment start and end reason;
* episode-end censoring;
* temporary leave, terminal leave, and rejoin treatment;
* team-intent/Z boundary events;
* whether a long segment was voluntarily ended or structurally truncated.

### Intended policy versus realized process

For legacy:

* duration logits and probabilities;
* sampled duration candidate;
* realized duration after all truncation;
* decision-time candidate histogram;
* primitive-time-weighted occupancy histogram.

For R30:

* KEEP and SET probabilities by age;
* realized KEEP-run distribution;
* age-conditioned renewal hazard;
* SET destination and whether behavior actually changes after SET.

### Exposure and bias

* number of high-level samples generated by each lifetime stratum;
* optimizer contribution and gradient weight by lifetime;
* environment steps per high-level sample;
* segment-count-weighted and primitive-time-weighted summaries;
* right-censored segments;
* decision opportunities per active-agent-time;
* environment interactions and optimizer updates separately.

This is necessary because the legacy path can overrepresent short segments in high-level learning even when primitive-time occupancy is not short-dominated.

### Concentration decomposition

* global normalized entropy and effective number of lifetime modes;
* per-agent-lifecycle entropy;
* within-lifecycle versus between-lifecycle variation;
* context- or renewal-urgency-conditioned entropy;
* minimum-lifetime concentration;
* maximum-lifetime lock-in;
* mode mass with confidence intervals;
* slot-permutation and membership-event strata.

A global histogram alone is ambiguous. Diversity may arise because stable and flexible agents each use one different lifetime—the desired result—or because every agent randomly mixes durations. Conversely, globally low entropy may be correct in a homogeneous scenario.

### Reward and mechanism evidence

* external task return;
* applied intrinsic-reward counts and magnitudes, not only configuration flags;
* entropy-floor application count;
* natural versus forced renewal behavior;
* counterfactual KEEP-versus-redecide effect on a held-out audit;
* search-cost curve or at least exposure-to-utility trajectory.

### When is a collapse reading genuine?

A collapse reading is genuine **for the studied controller** when:

1. concentration exists in the intended policy probabilities, not only in truncated realized segments;
2. it remains after separating segment-count weighting from primitive-time weighting;
3. long choices are not clipped by episode, membership, or Z boundaries;
4. the duration/renewal head has valid support and gradients;
5. it is reproduced across the registered episode and seed structure;
6. it is not merely correct specialization hidden by global pooling;
7. it has a consequence for external value, exploration coverage, or search efficiency.

A legacy collapse caused by short-segment high-sample bias would be a real property of **legacy’s update geometry**. It would not establish that unrestricted variable lifetime generally collapses.

### When is a no-collapse reading genuine?

A no-collapse result can refute a meaningful concentration claim only when:

1. all options or run-length regimes are reachable;
2. training and renewal opportunities are sufficient under a frozen budget;
3. no entropy floor or intrinsic pressure is propping up diversity;
4. the source actually contains heterogeneous renewal urgency;
5. the confidence interval excludes the registered degree of harmful concentration;
6. decision-time and primitive-time distributions agree sufficiently;
7. the result transports beyond one seed and one scenario.

One descriptive run may establish “no collapse observed.” It cannot establish “collapse does not occur.”

## Q4b — what is now open?

The open question is:

> **Does pathological lifetime concentration recur under the current reward-pure defaults and under a carrier whose own sampling geometry does not manufacture the reading?**

The question is no longer whether duration collapse has ever occurred. The config explicitly records that it occurred under `0.1` intrinsic pressure and that `0.05` was adopted as a cleaner stabilized base.

D1 must therefore be restated if retained.

## Q4c — if duration does not collapse

The contribution is not automatically dead.

It survives if unrestricted variable lifetime still suffers from one of the following:

* slower learning than the constrained controller;
* poor held-out generalization;
* excessive renewal-sequence entropy;
* unstable role switching;
* worse external return under the same budget;
* sensitivity to team-size or role-distribution shift.

The contribution is substantially weakened only if unrestricted R30:

* naturally learns the required heterogeneous lifetimes;
* beats the best fixed-(k);
* matches or exceeds the constrained controller;
* and does so at comparable search and optimization cost.

That result would refute the **tractability constraint’s necessity**, not the existence of heterogeneous timescales.

---

# Q5. Is holding the identification line correct?

## Ruling

**Yes. Hold G20R3. A complete member-resolved delayed-credit identification programme is not a prerequisite for the variable-lifetime claim.**

The previous branch drift treated identification as the research target. The bootstrap brief had only proposed variable lifetime as one possible response to the fast/slow conflict; it explicitly allowed a different root cause and described the round as exploratory.  Current active state records that the earlier diagnosis was action authority and credit factorization with a temporal manifestation—not that variable period had already been selected as the remedy.

## Minimum credit semantics required

Before a variable-lifetime result is interpretable, the chosen carrier must establish only:

1. **Probability ownership:** which KEEP/SET, duration, or renewal action was sampled and under what history.
2. **Clock ownership:** distinction among check opportunity, realized segment, and learning-credit window.
3. **Return semantics:** external-return horizon, discount, bootstrap, and terminal/censoring behavior.
4. **Replay correctness:** exact probability and active-mask reconstruction.
5. **Exposure accounting:** no unreported advantage from more high-level samples or optimizer steps.
6. **Comparator equivalence:** fixed, unrestricted, and constrained arms receive matched information and registered resource exposure.
7. **No structural truncation:** realized lifetime is not silently clipped into the measured result.

R30 already declares an SMDP high-level advantage mode, and the general configuration retains SMDP discount and bootstrap support.   That makes R30 eligible for a bounded variable-lifetime investigation; it does not prove the resulting credit is sufficient.

## Reactivate G20R3 only if

* the selected algorithm learns renewal classes from a member-specific delayed-effect signal;
* team return cannot orient the renewal policy despite verified source access and policy capacity;
* renewal decisions move but in systematically wrong member directions;
* or a result claim requires causal attribution to individual renewal decisions rather than end-to-end external performance.

Even then, build only the blocking fragment:

> a valid member-local renewal advantage at the KEEP/SET decision boundary.

Do not resume the entire G20R3 programme by default.

---

# Q6. Which mechanism should carry the variable-(k) line?

## Ruling

**Use R30 KEEP/SET as the primary carrier and unrestricted comparator. Keep `legacy_duration` as a frozen sampled-duration comparator and bias diagnostic.**

The config explicitly says legacy duration editing remains available only as the frozen comparator and R30 must be selected explicitly.  The current round further establishes that R30 was introduced to permit lifetimes beyond the former four-block cap without short-segment high-sample bias, and that an adaptive R30 arm completed and anchored R31–R33.  The experiment dashboard records completed R31, R32, and R33 gates, with R33 reporting R30 safety PASS, while only the separate 320k fixed-clock pairing was stopped without an M1–M4 outcome.

R30 is preferable because:

* a lifetime emerges from an agent’s repeated KEEP decisions;
* renewal is a local binary decision at a shared opportunity clock;
* lifetimes are not capped by the current candidate catalogue;
* the mechanism aligns naturally with renewal urgency;
* the known legacy short-segment sampling bias is avoided at the carrier level;
* existing downstream evidence establishes that R30 is not merely an unexecuted proposal.

## Important claim boundary

R30 does **not** untie the observation/check clock itself. It unties the realized renewal interval.

Therefore:

* if the user’s functional target is that relay-like commitments persist while service-like commitments renew frequently, R30 is suitable;
* if the intended claim literally requires different agents to be offered decisions at different physical clock times, R30 is not the final mechanism.

The examples in `RESEARCH_GOAL.md` concern persistence and re-decision frequency, so I read the functional realized-lifetime interpretation as the intended one.

## Q6a — role stability under R30

The underlying quantity is unchanged, but its observable changes.

Under R30:

* stable commitment → low beneficial-renewal hazard, high age-conditioned KEEP probability, persistent executable behavior;
* flexible commitment → high renewal urgency, higher SET hazard when context changes;
* realized lifetime → the resulting KEEP-run length.

The primary measurement should therefore be:

* renewal urgency or forced KEEP-versus-SET value;
* age- and context-conditioned hazard;
* natural run lengths;
* intervention-sensitive behavior after SET.

Raw run length is an outcome. KEEP frequency alone is not enough: a controller can KEEP because it is inert, not because the commitment is useful.

The role should be per-agent-time and dynamically changeable, not a fixed relay/service identity.

## Q6b — if legacy is retained as a comparator

Yes, short-segment high-sample bias contaminates any attempt to infer general duration preference from the legacy path.

The minimum correction is to report separately:

1. **decision-time choice distribution** over duration candidates;
2. **realized segment distribution** after censoring and truncation;
3. **primitive-time occupancy** by chosen duration;
4. **high-level sample count** by duration;
5. **gradient and optimizer contribution** by duration;
6. **segment termination reason**;
7. **team-intent/Z-boundary truncation**;
8. **episode and membership censoring**.

For analysis, use both:

* segment-count weighting, which describes what the duration head chooses per decision;
* primitive-time or per-agent-episode weighting, which describes experienced temporal occupancy.

A post hoc reweighting can correct the **measurement** of occupancy. It cannot erase the fact that the policy itself was trained under short-segment oversampling. Therefore, even a perfectly instrumented legacy run supports only:

> behavior of the legacy sampled-duration controller under its own update geometry.

It cannot support a general conclusion about unrestricted variable lifetime.

The completed legacy arm also used `(1,2,3,4)` at `k0=10`, whereas the current `(3,7,13,24)` candidate set has no completed run.  Operational competence of the old arm does not automatically transfer to D1’s current configuration.

## Q6c — effect of the earlier R30 ruling

Within the present evidence fence, the earlier ruling’s full raw scope is not included, so I do not infer that it proved R30 superior to legacy.

The evidence here supports the narrower conclusions:

* R30 is an eligible, exercised mechanism;
* the incomplete fixed-clock 320k pairing is not a valid negative against it;
* later R31–R33 work relied on it and passed its registered safety conditions;
* legacy retains a known structural bias that R30 was designed to avoid.

The previous R30 work therefore settled **eligibility and specific corrections**, not the present carrier-selection question. Selecting R30 for a new role-conditioned renewal thesis does not reopen a closed negative or contradict an accepted result.

---

# Retained candidate portfolio

| Candidate                                                 | Mechanism                                                                                               | Strongest simpler explanation or contradiction                                           | Reactivation / lowering observation                                                                                 |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **A. R30 role-conditioned renewal hazard** — preferred    | Fixed check opportunities; per-agent KEEP/SET; learned low-cardinality renewal-urgency regimes          | Unrestricted R30 or a two-clock gate matches it under matched exposure                   | Raise if held-out role swaps show regime-specific persistence and utility; lower if no renewal heterogeneity exists |
| **B. Two-clock learned gate** — strongest reduction       | Decision-time gate selects stable or flexible renewal regime; no general duration catalogue             | A recurrent fixed-clock controller may encode the same behavior without explicit regimes | Raise if it beats best shared fixed (k); select over A if it matches A                                              |
| **C. Corrected legacy sampled duration** — comparator     | Samples from discrete duration candidates; reports intended and realized lifetimes with bias accounting | Its effect may be entirely due to short-segment sample geometry or Z truncation          | Retain only if a sampled-duration claim is separately desired or if it beats R30 after matched correction           |
| **D. Self-learned low-cardinality lifetime set** — parked | Learns period prototypes or a sparse duration distribution                                              | Pathological collapse can satisfy the surface metric without useful role structure       | Reactivate after source heterogeneity and a non-collapse semantic gate are established                              |

---

# Scheduled evidence action

## Zero-compute action first

Complete a carrier-and-estimand derivation that freezes:

* check clock versus realized lifetime;
* renewal urgency;
* search-cost estimand;
* R30, fixed-(k), and legacy comparator roles;
* censoring and exposure semantics.

## First proposed resource-consuming action

One **instrumented, reward-pure R30 renewal-process diagnostic**, paired with the strongest shared fixed-lifetime controller under matched information and exposure.

Its purpose is limited to:

1. establish whether the source exhibits heterogeneous renewal urgency;
2. describe natural R30 lifetime and hazard behavior;
3. rule out truncation, exposure, and reward-pressure artefacts;
4. determine whether D8/D3 is worth building.

It does not test the final constrained algorithm and does not authorize a bounded or formal run by this review alone.

---

# Smallest portfolio updates

### Retained lemmas

* Different agents may require different realized commitment lifetimes; this remains the branch’s user-owned target.
* Collapse has occurred under at least one prior intrinsic-pressure regime; it is not an entirely hypothetical pathology.
* The legacy and R30 carriers are not equivalent: legacy has recorded short-segment sampling risk, while R30 produces lifetime through KEEP/SET.
* R30’s stopped 320k pairing does not constitute a scientific failure of the adaptive R30 line.

### Refuted or modified units

* Refute: “D1 settles both collapse and role separability in one legacy run.”
* Refute: “Collapse has never been observed.”
* Refute: “A completed legacy arm proves the current `(3,7,13,24)` path trains.”
* Modify: “The contribution is anti-collapse.” The contribution must be finite-budget structured renewal.
* Modify: “Role stability is churn.” Churn is an outcome; renewal urgency is the primitive.
* Modify: “Untied (k)” under R30 means variable realized lifetime, not variable check opportunity.

### Held

* G20R3 identification remains held.
* D4 remains live but parked.
* Legacy remains a comparator, not the primary carrier.
* The portfolio remains plural; R30 is the selected first carrier, not the only legal future mechanism.

**This review selects a research ordering and separating evidence. It does not authorize implementation, bounded compute, or formal compute.**
