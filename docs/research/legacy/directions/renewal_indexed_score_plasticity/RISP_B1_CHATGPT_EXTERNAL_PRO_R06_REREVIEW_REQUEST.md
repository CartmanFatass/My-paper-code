# RISP-B1 revision-06 ChatGPT External Pro mathematical/causal rereview

```text
direction_id=renewal_indexed_score_plasticity
candidate=RISP-B1
science_revision=RISP-B1-SCIENCE-20260813-06
request_kind=SAME_CONVERSATION_PREPRODUCTION_MATHEMATICAL_CAUSAL_CLOSURE
provider_role=ChatGPT External Pro
conversation_relationship=continue_exact_r04_r05_conversation
artifact_status=FROZEN_FOR_ROOT_PUBLICATION_NOT_SENT
provider_contacted_for_r06=false
owner=/root/em_renewal_indexed_score_plasticity
```

Please rereview complete prospective revision 06 in the same conversation that
returned `REVISION_REQUIRED` on revisions 04 and 05. No RISP stochastic object,
training, evaluation, test or result exists. The reviewer-visible source is the
GitHub repository on branch `aggressive`, restricted to:

```text
docs/research/candidates/renewal_indexed_score_plasticity/RISP_B1_SCIENCE_CARD.md
```

Revision 06 accepts both revision-05 defects without changing the protected
RISP-versus-containing-SIGN-RNN family:

1. The common policy head is now an exact rational law. Binary32 operands are
   canonically interpreted as dyadic rationals; raw low-rank logits are formed
   exactly; `z=6r/(6+|r|)`, `w=16+(z+6)^2`, and `pi=w/sum w`. This same `pi`
   is used for categorical action sampling, log probability, entropy,
   score/Fisher/eligibility, baseline, TV clones and forks. The explicit
   derivative at zero is frozen, so the selected-action score is literally the
   behavior-law score rather than a rounded-CDF surrogate.
2. Every categorical event uses a frozen exact-rational `ExactCat` primitive.
   It clears rational masses to reduced integers, assembles little-endian raw
   PCG64 words into a sufficiently wide integer, rejects at the strict
   `floor(S/M)M` boundary, and retries on the event's isolated keyed tape without
   a cap. This samples exact uniform-three, `3/4`, `1/4`, uniform-two, rational
   action and recursively rational `pbar` laws. Event counts and keys are fixed;
   only raw-word attempts are variable and descriptive.
3. The marginal intervention is explicitly nonterminal-update-only. A terminal
   completion contributes recipient reward/residual diagnostics but creates no
   supplied sign, replicate packet, fast update, controller-belief/`rho`
   advance, or TWIN event. The exact total remains `301,056`.
4. Lock 1 now checks canonical rational conversion, integer masses, rejection
   boundaries, multiword assembly, event/key ledgers and the rational-head
   reachability fixture using hand-authored constants only. It still certifies
   no learned competence or outcome.

Please scrutinize the entire revision, not only this summary. In particular:

- prove or refute that the rational head is C1, has the stated common support,
  and makes the stored analytic score exactly the sampled behavior-law score;
- prove or refute `ExactCat` uniformity for arbitrary finite rational masses,
  including its bit width, strict rejection boundary, modulo/category rule,
  event isolation and unbounded-retry semantics;
- check that exact uniform initialization plus exact recipient/twin categorical
  kernels restores the literal conditional-marginal `rho` induction;
- check terminal ownership, all invocation/key counts, deterministic fixtures,
  parity, two-lock activity, inference and claim ceiling for any hidden choice;
  and
- identify the strongest remaining alternative and the next most informative
  post-result discriminator.

Return exactly one disposition at the top:

```text
CLOSED
```

if the complete revision is mathematically and causally coherent for its stated
finite claim, or

```text
REVISION_REQUIRED
```

followed by every exact defect, necessary correction and resulting claim
ceiling. This ruling concerns science only. Do not review implementation/tests,
accept runtime, select the portfolio, or infer arbitrary-`k`, UAV or deployment
value.
