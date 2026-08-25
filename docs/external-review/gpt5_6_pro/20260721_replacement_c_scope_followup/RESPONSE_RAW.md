# GPT-5.6 Pro Response — Replacement C Scope And Feasibility

Received 2026-07-21. Archived verbatim as delivered. LaTeX markup was mangled
in transport; formulas are reconstructable from context. No content is edited,
reordered or summarized here.

---

1. Training-versus-evaluation scope
Replacement C should be a held-out evaluation-only measurement. It must not change training, the PPO objective, or the behavior-policy likelihood.
The important code fact is that the current collector already draws a mark candidate at every CREATE or due non-CREATE opportunity, independently of whether the categorical decision becomes KEEP or RENEW. It computes `mu/sigma`, draws `mark_eps` for every request, and constructs `u`; only afterward does the mask determine whether the mark is applied and scored. On KEEP rows, the current code masks out the mark factor and writes zero into the stored `event_u`; on CREATE/RENEW rows, the transformed-mark density enters the joint likelihood.
Replay matches that factorization: `mark_mask` is true only for CREATE or RENEW, and the recomputed mark density is zeroed elsewhere. The registered tolerance is `1e-6`.
Therefore the premise that the "general-contract" reading would newly alter training-time mark-RNG consumption is incorrect. Training already consumes the mark stream once per opportunity, regardless of KEEP/RENEW. The missing implementation is only diagnostic retention:

* During held-out stochastic EHC evaluation, retain the already-drawn unmasked `candidate_u` and `candidate_z=tanh(candidate_u)` for every non-CREATE opportunity.
* For a natural RENEW row, this is the executed mark.
* For a natural KEEP row, it is an auxiliary counterfactual mark.
* It must not enter the KEEP behavior likelihood, loss, gradient, or optimizer state.

For a uniform trajectory schema, the candidate fields may be stored in all modes, but they remain audit-only. No extra RNG draw is allowed.
No checkpoint rewrite is required. Existing checkpoints round-trip every dedicated RNG stream, but only at complete update boundaries with an asserted empty rollout buffer; formal evaluation loads the strict update-250 checkpoint. Replacement C can run after that load using in-memory evaluation snapshots.
So the intended scope is:

```text
training behavior and likelihood: unchanged
candidate RNG consumption: already present
new candidate retention and counterfactual forks: held-out EHC evaluation only

```

2. Whether batched forks preserve the common-randomness estimand
Yes. Batched forks preserve the estimand exactly if every fork owns a cloned state and both branches of a pair receive identical realized future random variates. They do not need to share one mutable RNG object.
Sharing one stream object would actually be hazardous: advancing the KEEP branch first would change the draws subsequently seen by the RENEW branch. The required equality is equality of random-number sequences, not object identity.
For each eligible opportunity, create the pair at a precisely frozen boundary:

1. Begin from the same pre-event environment, recurrent, lifecycle, commitment and segment state.
2. Materialize the current candidate mark and the next opportunity gap once.
3. Consume or record the current categorical-event draw so that the future event stream begins at the same position.
4. Clone the resulting future RNG states into two independent branch-owned copies.
5. Apply only the treatment difference:
   * KEEP retains `z`;
   * RENEW applies the same stored candidate `z`.
6. Advance both branches to episode termination with identical future tables or cloned states for:
   * demand and membership;
   * opportunity gaps;
   * primitive order;
   * primitive-action uniforms;
   * later event uniforms;
   * later candidate marks.

The current implementation is compatible with this construction:

* ledger, order, primitive, opportunity, event and mark generators are separately owned;
* primitive sampling consumes a fixed full `(env_count, MAX_LIFECYCLES)` uniform table each step;
* event, candidate-mark and opportunity-gap draws occur once per request, independently of whether the request resolves to KEEP or RENEW;
* demand, membership and order are pre-materialized in the immutable ledger, and the environment has a complete snapshot/restore contract.

Because KEEP versus RENEW does not alter membership or the exogenous opportunity countdown draw, the two branches retain the same future request schedule. Their physical states and policy distributions may diverge—that is the causal effect being measured—but their exogenous and policy-sampling random numbers remain paired.
Batched execution conditions
Batched execution is valid only if:

* every branch has independent environment, lifecycle, hidden, commitment and RNG storage;
* no tensor is written across fork IDs;
* both branches of a pair use the same random tables indexed by pair ID and future step;
* batch position, padding and termination masks do not affect RNG indexing;
* branch pairs are kept together through compaction or represented by stable pair IDs.

A focused equivalence test should compare batched and sequential execution on a fixed preregistered subset:

```text
membership/event/primitive actions: exact equality
terminal outcomes and utilities: exact equality
RNG states after continuation: exact equality
continuous logits/probabilities/state: max error <= 1e-7

```

The natural-action branch must also reproduce the originally collected continuation exactly. If either discrete equality or natural-continuation reproduction fails, the batched engine is invalid; use smaller fixed microbatches or one pair per batch.
Multiple opportunities from one episode
Putting several opportunities from the same original episode in one computational batch introduces no new statistical dependence. Those opportunities were already dependent because they share the same policy checkpoint, ledger and source trajectory. The registered bootstrap resamples replicate seeds and then whole sign-paired episode IDs while preserving all events belonging to each episode cluster. Batch membership is not a statistical unit.
3. Minimum viable form if full forking is unaffordable
Use preregistered opportunity subsampling and still run every selected pair to episode termination. Do not truncate the counterfactual branches to a fixed horizon.
A fixed-horizon fork would estimate a different quantity. This environment pays zero reward until the terminal step and defines utility from whole-episode tracking and completed segments, so a truncated branch cannot recover the unchanged external-utility consequence without introducing a critic surrogate or a new objective.
Full batched evaluation remains the preferred contract: an estimated 18 minutes is modest relative to training and avoids subsampling variance. If a reduced form is operationally necessary, the minimum I would accept is:
Frozen sample size
For each of the five replicates, separately within the natural-action strata:

```text
32 natural KEEP opportunities
32 natural RENEW opportunities

```

This yields:

```text
160 KEEP pairs
160 RENEW pairs
320 opportunity pairs
640 total branch continuations

```

It exceeds the already adopted 128-row support floor for each action and provides a separate estimate in every replicate. No sample size guarantees statistical power; if the resulting interval crosses zero, the outcome remains mixed/underpowered. There is no post-result top-up.
If any replicate has fewer than 32 eligible rows for either natural action, Replacement C is `BENCHMARK_NON_IDENTIFIABLE` for that run rather than being repaired by changing the quota.
Selection rule
After the complete natural held-out EHC trajectories have been collected—but before any fork outcome is computed:

1. Partition eligible non-CREATE rows by `(replicate, natural_action)`.
2. Within each partition, perform simple random sampling without replacement of 32 rows.
3. Use a dedicated deterministic selection stream derived from the registered bootstrap seed, with a separate fixed namespace/coordinate.
4. The selection key may use only stable provenance:
   * replicate;
   * base episode ID and sign parity;
   * physical time;
   * opaque lifecycle key and membership epoch;
   * segment ID;
   * natural KEEP/RENEW action.
5. It must not use observation values, mark values, future trajectory, utility or counterfactual advantage.

Within replicate (r) and action (a), the sample mean
[
\widehat A_{r,a}
\frac{1}{32}\sum_{j\in S_{r,a}} A_j
]
is unbiased for that replicate's finite-population event mean because every eligible row in the stratum has the same inclusion probability. The registered equal-replicate estimand is then
[
\widehat A_a
\frac{1}{5}\sum_{r=0}^{4}\widehat A_{r,a}.
]
The hierarchical bootstrap continues to resample replicate seeds and original sign-paired base episodes; every selected fork row remains attached to its original base-episode cluster. Multiple selected rows from one cluster must travel together in every resample.
The consequence gates can remain those proposed previously:
[
LCB_{95}(A_{\mathrm{KEEP}})>0,\qquad
LCB_{95}(A_{\mathrm{RENEW}})>0,
]
with frozen point-estimate floors
[
\operatorname{mean}(A_{\mathrm{KEEP}})\ge 0.02,\qquad
\operatorname{mean}(A_{\mathrm{RENEW}})\ge 0.02.
]
Thus the recommended disposition is:

```text
default: full per-opportunity batched terminal forks
fallback: 32 KEEP + 32 RENEW uniformly sampled per replicate
not acceptable: fixed-horizon truncation or adaptive post-result resampling

```
