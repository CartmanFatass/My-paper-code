# RISP-B1 revision-07 ChatGPT External Pro mathematical/causal rereview

```text
direction_id=renewal_indexed_score_plasticity
candidate=RISP-B1
science_revision=RISP-B1-SCIENCE-20260813-07
request_kind=SAME_CONVERSATION_PREPRODUCTION_MATHEMATICAL_CAUSAL_CLOSURE
provider_role=ChatGPT External Pro
conversation_relationship=continue_exact_r04_r05_r06_conversation
artifact_status=FROZEN_FOR_ROOT_PUBLICATION_NOT_SENT
provider_contacted_for_r07=false
owner=/root/em_renewal_indexed_score_plasticity
```

Please rereview complete prospective revision 07 in the same conversation that
returned `REVISION_REQUIRED` on revisions 04, 05 and 06. No RISP stochastic
object, training, evaluation, test or result exists. The reviewer-visible source
is the GitHub repository on branch `aggressive`, restricted to:

```text
docs/research/candidates/renewal_indexed_score_plasticity/RISP_B1_SCIENCE_CARD.md
```

Revision 07 accepts the sole revision-06 defect without changing its algorithm,
comparator, rational policy head, counts, terminal law, estimands or protected
claim family:

1. The science-level categorical probability space is now explicitly
   `R[e,v,j] iid Uniform({0,...,2^64-1})`, where `e` is the complete typed event
   tuple, `v` the rejection attempt and `j` the little-endian word position.
2. Typed event kinds and every zero-based field are frozen. Equality of complete
   tuples means deliberate common-tape reuse; unequal tuples are independent.
   Twin tuples are distinct from and independent of recipient environment,
   action and fork tuples. Fork branches deliberately share their fork tuples.
3. `ExactCat` is mathematically defined on those product coordinates, so its
   multiword block is exactly uniform, attempts are iid, rejection terminates
   almost surely, and the accepted residue realizes the declared rational law.
4. The existing injective `key(e)` formulas and `PCG64(key(e))` are only the
   reproducible implementation/coupling convention. They are not the proof or
   source of stochastic uniformity or independence. Lock 1 may verify only tuple
   domains, injectivity, reuse graph, namespace separation and deterministic
   ExactCat arithmetic; it cannot run or certify a PRNG.
5. Algorithm seed remains the uncertainty unit. Product coordinates define the
   registered DGP and conditional yoke, not extra inferential replicates.

Please scrutinize the entire revision and return exactly one disposition at the
top:

```text
CLOSED
```

if the complete revision is mathematically and causally coherent for its stated
finite claim, or

```text
REVISION_REQUIRED
```

followed by every exact remaining defect, necessary correction and resulting
claim ceiling. In particular, check that the typed product space and coupling
graph suffice for exact behavior-law sampling, exact conditional marginality,
recipient-lineage independence, multiword retries and seed-level inference;
that no implementation PRNG claim is smuggled back into Lock 1; and that all
previously accepted rational-head, terminal, count, containment, timing,
inference and two-lock conclusions remain intact. Also name the strongest
remaining alternative and most informative post-result discriminator.

This ruling concerns science only. Do not review implementation/tests, accept
runtime, select the portfolio, or infer arbitrary-`k`, UAV or deployment value.
