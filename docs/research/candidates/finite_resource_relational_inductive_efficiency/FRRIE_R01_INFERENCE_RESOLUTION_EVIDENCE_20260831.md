# FRRIE R01 inference-resolution evidence

## Conclusion

Close the current 24-root R01 conclusion-bearing result object before production. Do not replace
its decision-incapable 56-tail mean/equivalence design with a 24-root one-sided run, and do not choose a larger
block count without a new root-law or power contract. This conclusion has no `PHY_TRUST` versus
`EDGE_FLEX` polarity. Direction-level advice to Root is `PARK`, not broad scientific closure.

The decisive result is resolution, not cost: under the only protected assumption--independent but
otherwise arbitrary bounded root-level statistics--24 roots have at most about 13% power against
a scientifically material one-native-delivery alternative even for the smallest one-sided object.
The original practical-equivalence condition cannot be certified even on an all-zero 24-root
sample. A result run would therefore have no prospectively defensible chance of answering the
registered question.
The independent inference audit agrees that an IUT is formally level-valid and arithmetically
reachable; formal validity is not decision-capable power.

## Question and inputs

**Question.** Is there a prospective inference repair that makes the current 24-root R01 object
decision-capable without changing its scientific target, or should that result object stop before
production?

**Inputs.** `DIRECTION.md`, `IMPLEMENTATION_THRESHOLD.md`,
`INFERENCE_AND_EXECUTION_FREEZE.md`, the current Portfolio row, the cited SGSP R03/RSCF definitions
and 28-family clarification, the CCIC/EGRCR/VQFP controls, and the current V2 contract, preflight,
analysis, and result surfaces. No production root, model, checkpoint, episode, or result was
created or observed in this audit.

The inferential unit remains one complete fresh 32-byte root block. The two learned arms are paired
within a root and differ only in their residual projection boxes. The 256 evaluation episodes,
agents, roles, slots, and counterfactual continuations are within-block computations.

## Direct observations

1. `J` lies in `[0,1]`; every arm contrast therefore lies in `[-1,1]`. The frozen root law supplies
   independence but no Gaussianity, symmetry, sign exchangeability, variance bound, or parametric
   family.
2. The current positive branch depends on seen practical equivalence in addition to held-out
   efficacy and component gates. With 24 roots, an all-zero sample cannot certify
   `|E[d_seen]| <= 0.04` under arbitrary bounded laws. For
   `P(X=1)=q`, `P(X=0)=1-q`, with `q` just above `0.04`, the all-zero sample has probability
   approaching `0.96^24 = 0.3754132467`, already far above `0.05` before multiplicity.
3. A 28-quantity simultaneous confidence rectangle would allocate 56 tails. That allocation is
   relevant only when retaining the selectable original multi-branch family. It is not required
   for a positive conjunction made solely of one-sided component tests.
   Keeping every positive support, competence, interaction, basin, and cut predicate as one IUT is
   likewise level-valid, but adding necessary predicates cannot improve the power bound below.
4. The smallest efficacy-only mean claim would require all four population conditions

   \[
   \mu_{e,9}>0.08,\quad \mu_{e,15}>0.08,\quad
   \mu_{d,6}>0.04,\quad \mu_{d,21}>0.04.
   \]

   Here `e=EDGE_FLEX-UNIFORM_LEGAL` is wide-package competence and
   `d=PHY_TRUST-EDGE_FLEX` is held-out efficacy. The global null is the union of the four component
   nulls. Rejecting it only when every component level-`0.05` one-sided test rejects is an
   intersection-union test: under any global-null distribution at least one component null is true,
   so

   \[
   P(\text{all four reject})\le P(\text{that true component rejects})\le0.05.
   \]

   No Bonferroni correction is needed for that single conjunction. The four component bounds would
   not, however, be a simultaneous 95% confidence rectangle and could not be reused to select
   equality, harm, cut, interaction, or superiority branches.
5. A valid one-sided Hoeffding test at 24 blocks has radius

   \[
   2\sqrt{\log(20)/(2\cdot24)}=0.4996442270.
   \]

   It could pass only if both observed direct means exceed `0.5396442270` and both competence means
   exceed `0.5796442270`. Formal reachability is therefore not reasonable resolution.
6. Current V2 packet validation would accept any 24 different 64-hex strings and any nonempty
   `generation_provenance` string. It does not directly generate or observe a uniform ordered
   without-replacement root procedure. Consequently, even a future repaired root-population object
   needs a direct prospective root-generation surface; otherwise the artifact identifies only its
   literal fixed 24-root panel. This is a sampling-law defect, not authentication or identity work.

## Exact finite-sample power bound

Let the scientifically material alternative be one additional native distinct-delivery
consequence beyond the applicable margin:

\[
\eta=0.65/6=13/120=0.108333\ldots.
\]

For any component with null boundary `m`, the protected bounded class contains the two simple laws

\[
X\in\{-1,+1\},\qquad
p_0=P_0(X=1)=(1+m)/2,qquad
p_1=P_1(X=1)=(1+m+\eta)/2.
\]

Arbitrarily close dyadic probabilities instantiate the same witness under a uniform 256-bit root.
Any distribution-free level-`0.05` mean test must control `P0`. By the Neyman--Pearson lemma, its
power against `P1` cannot exceed the most-powerful randomized upper-tail binomial test.
If uniqueness is retained by sampling the finite root population without replacement, the exact
witness is hypergeometric; at 24 draws from `2^256` roots its difference from the displayed
binomial power is bounded at the root-collision scale and cannot change any shown decimal.

For `B` blocks, compute this bound reproducibly as follows:

```text
size = 0; power = 0
for k = B, B-1, ..., 0:
    b0 = BinomialPMF(B, p0, k)
    b1 = BinomialPMF(B, p1, k)
    if size + b0 <= 0.05:
        size += b0; power += b1
    else:
        gamma = (0.05 - size) / b0
        power += gamma * b1
        stop
```

At `B=24` this gives:

| component boundary | `p0` | `p1` | maximum possible power |
| --- | ---: | ---: | ---: |
| held-out direct, `m=0.04` | `0.52` | `0.5741666667` | `0.1323360180` |
| competence, `m=0.08` | `0.54` | `0.5941666667` | `0.1302412162` |

The four-condition conjunction cannot have power greater than its least powerful necessary
component. This is a bound on every valid distribution-free method, not a criticism of Hoeffding.

Iterating the same exact algorithm over `B=1,2,...` gives the first component counts reaching 80%
power as `523` for `m=0.04` and `518` for `m=0.08`. Thus at least 523 blocks are necessary even
before requiring joint 80% power for all four conditions; 523 is not a sufficient design.

For comparison, a conservative distribution-free design can guarantee family power at least 80%
for the four-condition IUT by giving each condition type-II error at most `0.05` and applying the
union bound. A one-sided Hoeffding design requires

\[
B\ge
\left\lceil\frac{2(2)^2\log(20)}{(13/120)^2}\right\rceil=2043.
\]

This is a mathematical sufficient count for effects at least one delivery consequence beyond every
margin, not a recommendation. The accepted ledger would then require, for the two learned arms
alone, `10,409,951,232` environment slots and about `8.0894e15` conventional FLOPs. No current
root-variance class, joint alternative law, or single-host runtime observation justifies choosing
523, 2043, or any intermediate count.

## Majority, sign, and prevalence are not a repair

A sign design could replace each mean by a prevalence such as
`P(d_s(N)>0.04)>1/2`. At 24 roots a nonrandomized level-`0.05` binomial test would require at least
17 successes (`P_{0.5}(K>=17)=0.0319573`; `K>=16` has probability `0.0757948`). It is executable,
but it answers a different question.

Prevalence does not contain mean native return. For example,

- `P(X=0.05)=0.51`, `P(X=-1)=0.49` has a majority above `0.04` but mean `-0.4645`; and
- `P(X=1)=0.49`, `P(X=0)=0.51` lacks a majority above `0.04` but has mean `0.49`.

Therefore a majority/sign result can neither retain nor close the current expected-return package
effect. There is also no independent scientific rationale for a prevalence margin or for treating
root slots rather than native return as the utility population. It may be registered later only as
a new object with its own decision target, not as an inference repair for R01.

## Exact projection-contact discriminator

The cheapest outcome-bearing proposition is universal projection non-contact, but it is not
currently proved. If, for every root and every reachable supported training history through update
512, every pre-projection `beta` proposal lies in `[-0.15,0.15]`, induction gives byte-identical
parameters, optimizer states, policies, trajectories, and endpoints for the two arms. That theorem
would close the exact treatment without sampled-return inference.

The literal `beta=0.60` witness proves only that the two projection operators have different
domains: `EDGE_FLEX` accepts that tensor value and `PHY_TRUST` does not. It does not prove that
`0.60`, or any value outside the tight box, is reachable from the frozen initialization under the
512-update RSCF trainer. Conversely, the generic clipped-Adam constants do not prove non-contact.
Optimizer-algebraic zero-gradient histories never contact, while optimizer-algebraic sustained
clipped-gradient histories can move about `512 * 0.0003 = 0.1536` in one sign and reach the tight
boundary within the frozen update budget. Thus optimizer-supported universal equality is false. A task-specific
invariant would have to control the actual full-suffix actor/critic gradients over every reachable history;
no such bound exists in the current evidence.

Observing no contact on the declared 24 roots is not the universal theorem. It still requires a
complete 512-update full-suffix training trajectory for every root (one arm can suffice by induction
if every pre-projection proposal and complete state equality are directly audited). It closes only
those literal paths, not unsampled-root population effects, and therefore cannot replace the missing
mean inference. Observing contact is also not return evidence: it proves only that the package
trajectories can diverge. Any continuation after contact needs a new prospectively powered package
estimand and root law. Contact cannot be used post hoc to delete seen equivalence or cut gates in
order to preserve a relational-mechanism claim.

## Options and judgment

- **24-root efficacy-only mean object:** legal as a four-condition IUT, but minimax power is at most
  about 13% at the native one-delivery alternative. A nonpass would be only `UNRESOLVED`; it could
  not establish equality, harm, wide superiority, cut insensitivity, or absence. Deleting the
  current seen-specificity or cut predicates also creates a new package estimand; it cannot preserve
  a relational-mechanism claim by relabeling R01.
- **More blocks for the original object:** 24 cannot certify equivalence. The contamination witness
  needs at least 74 blocks for an unadjusted `0.05` tail and at least 172 under the old `0.05/56`
  allocation. Simple simultaneous Hoeffding radii make the narrowest `c/I=0.03` gates require
  62,410 blocks merely for arithmetic resolution. These are lower or sufficient precision counts,
  not a prospective power design.
- **Majority/prevalence:** executable but changes the estimand and package decision.
- **Resolution stop:** preserves the mean-return question, records the exact obstruction, and
  spends no conclusion-bearing roots on a design that cannot answer it.

The unique recommendation is the resolution stop. Current R01 is exhausted as a result object.
The exact `CLOSED_EXACT_NO_PROJECTION_CONTACT` theorem remains valid only if universal reachable-set
non-contact is proved. A sampled 24-root no-contact observation is finite-panel description, and
projection contact alone is not efficacy evidence.

## Frozen disposition and reentry

- No R01 production root, RNG master, model, optimizer, checkpoint, evaluation, or scientific result
  may be created.
- V1 and V2 remain TEST/non-result engineering evidence; do not implement a polarity analyzer or
  reinterpret a 24-root descriptive panel.
- The current R01 lifecycle recommendation is `CLOSE_CURRENT_OBJECT`.
- The FRRIE direction recommendation to Root is `PARK`, because the package mechanism remains
  scientifically possible but has no proportionate, decision-capable next observation.
- Reentry requires one genuinely new prospective object that supplies at least one of:
  1. a proved narrower paired-root support/variance class plus a valid inference and power law;
  2. an independently justified block count, joint alternative, resource/runtime contract, and
     direct ordered uniform-without-replacement root generator; or
  3. a scientifically motivated non-mean estimand with its own native decision value.

A contrary result that would change this recommendation is a prospective proof that the actual
paired root contrast class is sufficiently narrower than `[-1,1]` to give at least 80% power at the
one-delivery alternative within an independently feasible block/resource contract.

## Exact evidence paths

- `docs/research/candidates/finite_resource_relational_inductive_efficiency/DIRECTION.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/IMPLEMENTATION_THRESHOLD.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/INFERENCE_AND_EXECUTION_FREEZE.md`
- `docs/research/legacy/directions/semantic_graphon_shared_policy/SGSP_RG2Z_R03_DEFINITION_SCIENCE_CARD.md`
- `docs/research/legacy/directions/semantic_graphon_shared_policy/SGSP_RG2Z_ROLE_SAMPLED_CF_R01_SCIENCE_CARD.md`
- `docs/research/legacy/directions/semantic_graphon_shared_policy/SGSP_RG2Z_RSCF_R01_28_FAMILY_SUPPORT_SLACKS_NONREVISION_CLARIFICATION_20260821.md`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/contracts/core.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/preflight.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/analysis.py`
- `docs/research/legacy/directions/semantic_graphon_shared_policy/SGSP_RSCF_SHORT_GATE_R01_SYNTHESIS_EVIDENCE_20260829.md`
