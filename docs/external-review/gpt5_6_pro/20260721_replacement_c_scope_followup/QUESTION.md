# Follow-up: Replacement C Scope And Feasibility

Sent to GPT-5.6 Pro on 2026-07-21, after adopting Replacements A, B and D into
the frozen contract and deferring C.

Prior exchange:
`docs/external-review/gpt5_6_pro/20260721_lifetime_battery_contract_question/`

## Correction to the question as sent

Question 1 asserted that the "general contract" reading would newly alter
training-time mark-RNG consumption, and therefore force a rewrite of the
collector, replay and checkpoint paths. **That premise is wrong.** The reviewer
corrected it and the correction is verified against
`ha_ctse_process/event_held_commitment_link.py` at `7ba056e`:

- lines 488-495 draw `mark_eps` for every request unconditionally in the
  stochastic branch and compute `u = mu + sigma * mark_eps`, before
  `derived_mark_mask` exists at line 498;
- line 518 stores `u` where the mask holds and zeros elsewhere;
- line 507 discards `tanh(u)` on KEEP, retaining `packed_z_pre`.

The mark stream is therefore already consumed once per opportunity regardless
of the categorical outcome, and the candidate mark already exists in flight and
is thrown away. Replacement C requires retention only: no additional RNG draw,
no training change, and no checkpoint rewrite. The cost objection that
motivated deferring C does not apply in the form it was stated.

---

```
Use the GitHub connector on private repository CartmanFatass/My-paper-code,
branch `aggressive`, commit c540878. Do not take the claims below on trust —
verify them against the code. The relevant paths are:

  ha_ctse_process/event_held_commitment_link.py
    initialize_arms            - per-stream seeding and DUM/EHC cloning
    collect_trajectory         - opportunity processing and mark sampling
    _replay_event_heads        - teacher replay from stored u
    save_checkpoint            - which RNG streams are round-tripped
    load_checkpoint
  ha_ctse_process/noncalendar_commitment_testbed.py
    registered seeds and thresholds near the top of the file
  docs/project/IMPLEMENTATION_PLAN.md
    sections "Probability and trajectory contract", "RNG and pairing",
    "Checkpoint and runner package", "Statistical and result contract"

The measurement in Replacement C is defined on the frozen held-out policy, so
the question is what the candidate-mark draw must do to the TRAINING path, if
anything.

Replacements A, B and D are adopted into the frozen contract. Replacement C,
the paired natural KEEP-versus-RENEW counterfactual advantage, is deferred on
two unresolved points. Both are implementation-determining, so please answer
before we build it.

QUESTION 1 — TRAINING OR EVALUATION SCOPE.
You wrote: "generate and store a candidate renew mark at every eligible
opportunity before categorical action selection. Its density enters the
behavior likelihood only when RENEW is selected."

That admits two readings with very different cost:

(a) EVALUATION-ONLY. Candidate marks are drawn only during held-out evaluation
    of the frozen final policy. Training is untouched. The behavior-likelihood
    clause is then vacuous, since no loss is computed at evaluation.

(b) GENERAL CONTRACT. Candidate marks are drawn at every eligible opportunity
    during training as well, and the likelihood must score the mark density
    only on RENEW rows.

Reading (b) changes mark-RNG stream consumption at every opportunity rather
than only at CREATE/RENEW. In the current implementation the mark stream is
paired between the DUM and EHC arms, replay must reproduce stored likelihoods
to <=1e-6, and the checkpoint round-trips every dedicated RNG stream exactly.
So (b) forces a rewrite of the collector, replay and checkpoint paths of an
implementation that is complete and verified, and requires re-establishing
DUM/EHC pairing. Reading (a) is purely additive.

Which did you intend? If (b), what does drawing the candidate during training
buy that (a) does not, given that the measurement is defined on the frozen
held-out policy?

QUESTION 2 — ESTIMAND UNDER BATCHED EVALUATION.
Measured cost on the target hardware: eligible non-CREATE opportunities occur
at roughly 0.02 per transition. Held-out stochastic evaluation of EHC over five
replicates is about 102,000 transitions, giving roughly 2,080 eligible
opportunities. Forking each into two branches run to episode termination at
about 40 remaining steps averages roughly 166,000 extra environment steps.

Executed as sequential single-environment forks this is about 4.6 hours, which
exceeds the entire 8.65-hour training run's evaluation budget and is dominated
by per-step interpreter overhead rather than compute. Executed as batched forks
-- collecting many opportunity snapshots and advancing them as one vectorised
batch of environments -- it is roughly 18 minutes.

Does batching in this way preserve your estimand exactly? Specifically:

  - Each forked pair must retain identical future demand and membership ledger,
    future opportunity gaps, primitive-order tables and policy-action random
    number tables. Under batching these come from per-fork owned RNG state
    rather than a single sequential stream. Is per-fork owned state sufficient
    for the common-randomness requirement, or does the estimand require that
    both branches of a pair consume from one shared stream in lockstep?

  - Clustering is "by original sign-paired base episode, not by event row."
    With batched forks, multiple opportunities from the same base episode are
    evaluated in the same batch. Does that create any dependence your
    cluster-bootstrap does not already absorb?

QUESTION 3 — MINIMUM VIABLE FORM.
If full per-opportunity forking is not affordable, is there a reduced version
that preserves the scientific content? For example, a pre-registered random
subsample of eligible opportunities per episode, or truncating each branch to a
fixed horizon rather than running to episode termination. If a subsample is
acceptable, what minimum count and what selection rule keep the paired
advantage estimator unbiased?

CONSTRAINT. No result has been observed. Thresholds and estimands are frozen
once the formal run starts.
```
