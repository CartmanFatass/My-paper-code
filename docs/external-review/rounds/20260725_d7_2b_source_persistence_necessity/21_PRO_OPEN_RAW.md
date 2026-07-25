# Scientific ruling — D7.2B source persistence necessity

**Stage reviewed:** `c4c14175184f7fc31d7f15fae4e9d6e97e078bd2`

## Overall disposition

**ACCEPT the retirement of `two_timescale_role_free_actions` as D7’s carrier positive control, but broaden the correction in two ways.**

1. The source–benchmark pair is retired because the source admits an optimal full-sync swap policy in which every commitment lasts exactly one check interval. A negative result therefore cannot distinguish carrier incapacity from rational selection of an equally optimal non-persistent solution. The exact derivation and the final audit agree: the policy achieved perfect task competence while taking SET for both agents at every check.
2. The carrier remains scientifically live, but the result exposes a concrete **optimization-bias risk**: the zero-weight, state-independent KEEP head can reach the all-SET solution by moving mainly its scalar bias, whereas the persistent solution requires the KEEP head to acquire state-dependent weights. The current single training realization demonstrates that this basin was selected; it does not yet prove that R30 generically prefers it.
3. The existing `U_opp`/`U_pi` calculations remain valid policy-conditional quantities, but `U_opp` must no longer be described as a policy-independent **source opportunity**. Both currently continue under the frozen learned joint policy, so they can measure dependence on that policy’s coordination convention. A separate source-level persistence-necessity estimand is required before a source can qualify as a positive control.

## Q0 — Is a replacement positive control the immediate successor?

**Not automatically. The immediate successor should be a zero-compute persistence-necessity audit of the intended main scenario.**

The branch is:

* **If the main scenario structurally requires individual persistence and has a constructive access path**, proceed directly to D7.3. In that branch, a replacement toy is unnecessary.
* **If the main scenario admits the same zero-cost role-exchange solution**, D7.3 is non-identifying and a replacement positive control is required before further carrier interpretation.
* **If the main-scenario property cannot be established from derivation or constructive controls**, a replacement positive control remains useful for isolating carrier capacity, but D8 must still remain blocked until the main source is separately qualified.

The present evidence fence does not contain the main-scenario environment or its transition/reward contract. The statement that it is “largely indifferent” to which member serves demand is therefore an inference in the question, not a repository fact I can confirm here. A direct ruling that it does or does not share the toy’s degeneracy would exceed the listed evidence.

Thus **Q2 remains conditionally relevant**, but no replacement source should be built until the main-scenario necessity audit is complete.

---

# Q1 — Retirement scope

## Formal retirement

The proposed formal scope is correct:

> Retire `two_timescale_role_free_actions × D7 learned-keep positive-control interpretation`.

The source reward selects the better of the direct and swapped assignments, so only the unordered pair of correct axis skills matters. The environment does not distinguish which agent carries which duty.

The following remain intact:

* R30 learned KEEP/SET as a candidate carrier;
* the forced-token hook;
* CRN replay;
* the event ledger;
* `B_H`;
* the raw policy-conditional `U_pi` and focal-best-SET quantity currently named `U_opp`;
* D8-coadaptive and the wider variable-lifetime portfolio.

The audit correctly instantiated its frozen policy and produced an interpretable observation. The problem is that the source cannot identify the intended carrier-capacity proposition. Under the project’s result semantics, that updates the benchmark–comparator pair, not the algorithm family.

## One additional estimand correction

The current distinction is:

[
U_i^\pi(h;H)
============

\mathbb E_{z\sim\pi_{\mathrm{SET}}}
Q_H^\pi(h,\mathrm{SET}_i(z))
----------------------------

Q_H^\pi(h,\mathrm{KEEP}_i),
]

[
U_{i,\max}^{\pi}(h;H)
=====================

\max_{z\ne z_i}
Q_H^\pi(h,\mathrm{SET}_i(z))
----------------------------

Q_H^\pi(h,\mathrm{KEEP}_i).
]

The second quantity is the current `U_opp`. Because later agents and future decisions still follow the frozen learned policy, it is the **best focal SET under policy continuation**, not an oracle property of the source.

Add a source-level quantity:

[
U_{i,\mathrm{src}}^\star(h;H)
=============================

\max_{\substack{z_i\ne z_i^{\mathrm{old}}\
\text{joint continuation}}}
\mathbb E[G_H\mid \mathrm{SET}_i(z_i)]
--------------------------------------

\max_{\text{joint continuation}}
\mathbb E[G_H\mid \mathrm{KEEP}_i].
]

The other agents and later decisions are reoptimized or supplied by a constructive oracle in both terms.

For a persistence-essential mixed-urgency history, require a material margin:

[
U_{\mathrm{stable,src}}^\star/B_H\le -0.10,
\qquad
U_{\mathrm{flex,src}}^\star/B_H\ge 0.10.
]

Equivalently, the best all-SET continuation must remain materially below the optimal mixed KEEP/SET continuation. The current toy has

[
U_{\mathrm{stable,src}}^\star=0
]

because both persistence and full-sync swapping attain the ceiling. That is the precise reason it fails as a positive control.

This does not discard the policy-conditional estimands. It separates:

* **source necessity**;
* **current policy competence**;
* and **natural policy use**.

## Is the optimum-selection reading legitimate?

**Yes as a retained hypothesis, not as a concluded carrier result.**

The evidence supports:

> In this training realization, R30 selected the all-SET member of two equal-return optima, and the selected solution used only a nearly state-independent KEEP probability.

The evidence does not yet support:

> R30 generally prefers non-persistent optima.

The latter would require a fresh pre-registration with:

* multiple independent training seeds;
* one fixed competence budget;
* a fixed final-checkpoint rule;
* basin classification defined before training;
* and no source or threshold changes after seeing basin frequencies.

The appropriate ledger status is therefore:

> `R30_ALL_SET_BASIN_INDUCTIVE_BIAS — retained hypothesis, parked`.

It should be reactivated if a persistence-essential source also yields:

* state-independent KEEP logits;
* all-SET natural behavior;
* or failure to acquire KEEP/SET separation despite identified source necessity.

There is no reason to spend runs on this equal-optimum source solely to establish that bias now.

---

## Q1a — Was the competence-budget change legitimate?

**It was acceptable for the narrow result obtained, but it cannot become the default procedure for future evidence-bearing comparisons.**

Why it is acceptable here:

* Condition A was explicitly a competence prerequisite, not a renewal conclusion.
* The low-budget run had barely left initialization: KEEP probability remained near `0.6` and the skill distribution remained near maximum entropy.
* The routing rule that a flat A buys more competence exposure rather than a scientific negative was written before the flat result.
* The A/B/C thresholds were unchanged.
* The final checkpoint was selected as the audited object before the audit was run.
* Most importantly, the source’s swap-equivalence retirement follows by derivation and is independent of optimizer settings.

The final config used three PPO epochs, `lr_coordinator=1e-3`, and 1,000 updates after the original one-epoch, `1e-4` attempt.

What this run cannot support:

* a search-efficiency comparison;
* a claim that the default R30 budget is sufficient;
* or the general optimum-selection claim above.

### Rule for the replacement source

The replacement must use a pre-registered finite competence ladder, for example:

1. fixed initial exposure (B_0);
2. one or more predetermined escalation stages (B_1,B_2);
3. a fixed maximum exposure;
4. escalation only when the competence gate fails and pre-registered liveness diagnostics show the policy has not materially moved;
5. no threshold, source, optimizer family, or checkpoint-selection changes between stages;
6. separate competence-development episodes and final audit episodes.

If the maximum stage fails, report source/controller no-access. Do not continue increasing budget until A passes.

---

# Q2 — What must a replacement source satisfy?

## Core requirement

“Persistence must be necessary” is correct, but **“no optimal all-SET policy exists” is necessary rather than sufficient**.

A replacement positive control must have all of the following:

1. **Mixed temporal duties:** at supported histories, one active commitment should beneficially persist while another should beneficially renew.
2. **Strict source necessity:** under optimal joint continuation:
   [
   U_{\mathrm{stable,src}}^\star/B_H\le -0.10,
   \qquad
   U_{\mathrm{flex,src}}^\star/B_H\ge 0.10.
   ]
3. **No all-SET ceiling policy:** every full-sync SET continuation is materially below the optimal mixed action.
4. **No all-KEEP ceiling policy:** the fast duty genuinely requires renewal.
5. **Both actions remain in support:** the desired result cannot be forced by masking KEEP or SET.
6. **Decision-time identifiability:** generic current state contains enough information to infer the distinction, without future events or named stable/flexible labels.
7. **Anonymous permutation semantics:** fixed agent identity cannot be the sole carrier of the distinction.
8. **Dynamic role possibility:** the same lifecycle can occupy different temporal regimes in different contexts or episodes.
9. **External task consequence:** persistence matters through transition/service dynamics, not a direct lifetime bonus or an algorithmic shaping term.
10. **Constructive access:** a supplied or verified executor demonstrates that the ceiling and both mixed-duty behaviors are reachable before R30 is judged.

The source gate should be solved analytically or by exhaustive/constructive controls **before training**. A source that fails it should never consume a carrier run.

## Selected mechanism: (a), modified

**Select tenure-dependent effectiveness, expressed as non-transferable agent–duty state in the dynamics.**

The clean form is:

* any agent may serve either duty;
* the stable duty’s effectiveness depends on continuous tenure of the current agent–duty pairing;
* transferring that duty to another agent resets or degrades the accumulated state;
* the flexible duty still requires frequent re-decision;
* no fixed agent is permanently designated stable or flexible.

This preserves global permutation equivariance: simultaneously permuting agents and their local state leaves the source unchanged. What is broken is **zero-cost assignment exchange**, not anonymity.

The consequence should enter external return through executed service or dynamics. It should not be a separate reward term such as `-β·SET`.

### May the tenure signal enter the controller state?

**Yes. It should be available as generic decision-time state.**

A hidden tenure variable would make a negative result ambiguous between temporal-control failure and missing information. The high controller may receive:

* current commitment age;
* current realized effectiveness/setup state;
* incumbent skill;
* and current task context.

It may not receive:

* `stable_role`;
* `relay`;
* `service`;
* the future target change;
* or an oracle recommendation to KEEP or SET.

R30 already conditions on the focal commitment age and on roster ages, so exposing a generic current tenure state is consistent with its existing information contract.

Ground-truth stable/flexible labels may be used in the evaluator only.

## Disposition of the other candidates

### (b) Agent-specific duty affinity

Do not use fixed identities.

A secondary source may draw per-agent capability vectors each episode and expose those capabilities in the corresponding anonymous observation rows. Simultaneously permuting agents and capability rows must preserve the source. This can create non-transferable state, but it primarily tests persistent heterogeneous capabilities rather than dynamically changing role stability, so it is weaker than tenure dynamics for the first positive control.

### (c) Direct switch cost

Reject as the primary source.

A direct `-cost·SET` term manufactures the measured renewal effect inside the reward definition and conflicts with the existing reward-pure R30 contract. The audit’s `U` would then contain the same penalty introduced to make `U` separate.

A physically realized setup delay or temporary service degradation may be admissible under mechanism (a), because it changes task dynamics rather than adding an edit penalty.

### (d) Asymmetric action support

Reject.

If one agent cannot express the swap, persistence is obtained by removing the alternative rather than by learning to prefer it. That makes the positive control tautological and abandons role-free assignment.

---

# Q3 — Does the proposed class constraint generalize?

## Ruling

The proposed statement is **too broad**:

> Reward invariance to agent identity alone does not imply that role exchange substitutes for persistence at zero cost.

A source can have permutation-invariant reward and still require persistence because:

* position, energy, queue state, or internal memory stays with the agent;
* changing the duty holder incurs transition latency;
* accumulated service or communication state is not transferable;
* or action effects depend on agent-local state.

The narrow valid statement is:

> **At a supported mixed-urgency history, if the reward and transition are equivariant under agent permutation, the relevant agent states and capabilities are exchangeable at zero cost, the joint action support is closed under that permutation, and every optimal post-check duty allocation can be reached by a full-sync SET permutation with the same future state and return, then individual persistence is not necessary. Such a source cannot be a positive control for individual renewal urgency.**

The reusable pre-freeze check should therefore be:

1. Does an optimal all-SET continuation exist?
2. Does role exchange preserve not only immediate reward but the complete future state relevant over (H)?
3. Is any agent-local or assignment-local state lost on exchange?
4. Is the best full-sync SET return materially below the optimal mixed KEEP/SET return?

A globally anonymous source remains usable when assignment history is non-transferable. The replacement tenure source is exactly such a case.

---

# Q4 — Does this reach D7.3, D8, or the main scenario?

## Current ruling

**The main scenario is unresolved within this evidence fence. D8 remains blocked.**

The next scientific action is not D8 and not automatically a new toy. It is:

> **D7.S — zero-compute main-scenario persistence-necessity audit.**

That audit should locate one candidate mixed-urgency history and compare:

[
V_H^\star(h\mid \mathrm{KEEP}*{\mathrm{stable}})
\quad\text{against}\quad
V_H^\star(h\mid \mathrm{SET}*{\mathrm{stable}}),
]

with all other agents and later decisions allowed their best legal continuation.

It should explicitly test whether a full-sync role permutation preserves:

* external return;
* physical state;
* energy;
* position;
* queue/service state;
* communication or topology state;
* and any other state carried across the relevant horizon.

These are examples of possible symmetry breakers, not claims that the current main scenario contains them.

## Branches

### Main scenario passes persistence necessity

Proceed directly to D7.3, provided a constructive or ordinary access control shows that the relevant behavior is reachable.

In this branch, **Q2 is unnecessary for the immediate sequence**. The main scenario serves both as the persistence-essential carrier test and the target source.

### Main scenario fails

The variable-individual-lifetime claim has a source problem on the intended benchmark.

Then:

1. build the tenure-based replacement positive control from Q2 to test carrier capacity;
2. redesign or select a main source with non-transferable assignment state;
3. keep D8 blocked until that main-source problem is solved.

A positive toy cannot rescue a main benchmark that does not require individual persistence.

### Main scenario unresolved

Run the tenure positive control if it is the cheaper way to test the carrier, but record that it advances only carrier capacity. D8 remains blocked because the paper-level source is not yet identified.

---

# Q5 — Should the estimand remain agent-level?

**Yes. Keep it agent-level.**

The paper’s target is variable **individual** realized lifetime. R30’s carrier likewise maintains per-agent skills and ages.

A duty-level estimand would declare the current swap policy successful:

* the slow x-duty continues to be represented in the team;
* the fast y-duty continues to renew;
* but the individual carrying each duty changes every check.

That is a claim about team role occupancy or duty continuity, not untied individual (k). The event ledger shows exactly why the distinction matters: team-level duty composition is correct while each individual commitment lifetime is fixed at one check interval.

Do not reframe the thesis to duty-level persistence.

Instead retain three layers:

1. **Source-level agent persistence necessity**
   [
   U_{i,\mathrm{src}}^\star.
   ]
2. **Policy-conditional focal renewal effect**
   [
   U_i^\pi,\quad U_{i,\max}^{\pi}.
   ]
3. **Natural behavior**
   KEEP/SET hazard and realized individual lifetime.

The current result demonstrates why all three are needed:

* the duty has a slow timescale;
* the source does not require one individual to carry it;
* and the learned policy coordinates through swapping.

---

# Q6 — Revised ordering

|  Order | Action                                                                             | Scientific consequence                                                                                                        |
| -----: | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
|  **0** | **Reconcile D0/D7 result semantics**                                               | Add `U_src*`; relabel current `U_opp` as focal-best SET under policy continuation; add the persistence-necessity source gate. |
|  **1** | **D7.S main-scenario persistence-necessity audit**                                 | Determine whether the paper’s intended source requires individual persistence. Zero compute or constructive-only.             |
| **2A** | **D7.3 directly**, if D7.S passes and source access is established                 | Replacement positive control is skipped.                                                                                      |
| **2B** | **Tenure-based replacement positive control**, if D7.S fails or remains unresolved | Test carrier capacity on a source where persistence is provably necessary.                                                    |
|  **3** | **Main-source redesign or qualification**, if D7.S failed                          | A positive control cannot substitute for a non-identifying paper source.                                                      |
|  **4** | **D8-coadaptive**                                                                  | Only after D7.3 establishes decision-time-predictable, low-cardinality agent-level urgency.                                   |
|  **5** | D3′ richer R30 conditioning                                                        | Only if D8 is insufficient.                                                                                                   |
|  **6** | Legacy and self-learned-duration diagnostics                                       | Off the critical path unless a specific comparison requires them.                                                             |
|  **7** | Blocking credit fragment                                                           | Only if source necessity, carrier capacity, and policy support are established but learning remains credit-limited.           |

The current ledger should also be reconciled before the next boundary:

* it still records the two-episode machinery values `0.214/0.232`, whereas the registered full-power result is `0.430/0.252`;
* the evidence-note header says the final audit is pending even though the final result appears later in the same file.

These do not change the ruling, but leaving them inconsistent would allow the small-sample sign artifact to survive as the active summary.

---

# Retained portfolio

| Candidate                               | Causal mechanism                                                  | Strongest contradiction                                                  | Reactivation evidence                                    |
| --------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------- |
| **Main-scenario direct**                | Existing non-transferable agent state makes persistence necessary | A zero-cost full-sync role permutation reaches the same state and return | D7.S proves strict persistence margin                    |
| **Tenure-dynamics positive control**    | Agent–duty continuity builds non-transferable effectiveness       | Effect is merely a disguised reward penalty or hidden label              | Source oracle proves mixed KEEP/SET uniquely optimal     |
| **Randomized capability source**        | Per-episode anonymous capability rows make swapping lossy         | Produces fixed specialist identities rather than dynamic regimes         | Same agent changes regime across contexts                |
| **R30 optimum-selection bias** — parked | Zero-weight KEEP head creates an easy bias-only all-SET basin     | Persistence-essential source learns state-dependent KEEP reliably        | Repeated collapse after source necessity and access pass |

## Scheduled action

**D7.S: derive whether the main scenario has a material, agent-level persistence-necessity margin under optimal joint continuation.**

Freeze before that audit:

* the mixed-urgency history class;
* the external-return horizon;
* the legal joint continuation;
* the source-level oracle or constructive controls;
* the normalized persistence margin;
* and the branch meanings:

  * `PERSISTENCE_NECESSARY_SOURCE`,
  * `ZERO_COST_ROLE_EXCHANGE_SOURCE`,
  * `SOURCE_NECESSITY_UNRESOLVED`.

This review authorizes neither implementation nor compute.
