# FRRIE R02 exact-law and smaller-object synthesis — 2026-08-31

Status: `LOCAL_EXACT_CONSTRUCTION / NO_RESULT / NOT_REGISTERED /
BLOCKED_RUNTIME_COMPLETION_CONFORMANCE_AND_EXTERNAL_CHALLENGE`

## Conclusion

The four-condition 916-block R02 statistical construction can be made finite and exact without
changing its expected-numeric-native-return estimands. This note fixes the local candidate law as
follows:

- the exact address constant is the 27-byte ASCII string
  `L_star = "FRRIE-R02-LSTAR-20260831-01"` for every initialization, training, and evaluation RNG
  address;
- 916 root rows are sampled directly iid and uniformly with replacement from `{0,1}^256`, sealed
  before any outcome, and kept in packet order; duplicate root bytes are legal and keep ordinary
  row weight, while unique record IDs are storage labels only and never enter `AddressedRNG`;
- four independent 1075-bit ancillary words per row are packed without padding in row-major order,
  are independent of all roots and execution randomness, and are used only after the complete
  binary64 contrasts exist;
- a final finite binary64 contrast `X in [-1,1]` is decoded from its bits to an exact integer
  `M in {0,...,2^1075}` and transformed by `Y = 1{B < M}` for
  `B ~ Uniform{0,...,2^1075-1}`; and
- R01's stochastic event/basin/role support branch is deleted. The four R02 contrasts are total
  for every root under the frozen mathematical DGP. Missing, nonfinite, partial, resource-failed,
  or otherwise nonconforming execution is `INVALID_NO_SCIENTIFIC_RESULT`; it is not a support
  outcome and does not enter the power event.

Under a conforming complete-panel implementation, the fixed nonrandomized cutoffs remain
`K_d6,K_d21 >= 502` and `K_e9,K_e15 >= 520`. Their global IUT size is at most `0.05`, and their
dependence-robust joint-power lower bound at all four margin-plus-`13/120` alternatives is
`0.800537003890475350`. This is statistical power for the total 916-row mathematical object, not an
observed probability of operational completion. Current runtime completion/resource conformance
is unobserved, and the pinned V2 surface still hard-codes R01's 24 distinct roots, 28-member
analysis, support receipt, and inactive inference. R02 therefore remains unregistered and no root,
ancillary word, model, checkpoint, episode, or result may be created from this note.

The number 916 is not a proved global minimum. Three meanings of “smaller” must remain separate:

1. for the same update-512 four-roster claim, an exact-size randomized-boundary candidate reaches
   the displayed guarantee at 909 blocks, only seven fewer, but its additional non-dyadic decision
   coins still need a finite executable law and independent minimax review;
2. an equal-weight roster-mixture direct-plus-competence claim reaches an analogous randomized
   two-test certificate at about 720 blocks, but it no longer guarantees either roster separately;
   and
3. a lower update/work vector, competence-first schedule, or capped sequential design changes the
   budget object or only expected cost. In particular, single-component sequential ASN cannot be
   reported as four-component panel cost because each expensive block is shared and a successful
   IUT waits for the slowest component.

No arm polarity, mechanism value, resource feasibility, or Portfolio action follows. Seven fewer
rows do not materially change the 916-row resource question. The only presently named scientific
objects that could change the direction evidence are a sound universal first-native-action
noncontact proof, which would resolve the treatment without a result run, or a prospectively
total-cost-bounded mean-return discriminator that is materially cheaper and can genuinely select
between architectures. Root owns lifecycle and investment.

## Question and non-goals

The local decision-changing question is:

> Is there one finite, outcome-blind population/randomization/completion/result law for the
> 916-block four-condition R02, and is a materially smaller object possible without silently
> changing expected numeric native return, global level, dependence-robust power, or the claim?

The treatment is `PHY_TRUST`; the strongest current same-information containing comparator is
`EDGE_FLEX`; `UNIFORM_LEGAL` is the seen-roster competence floor. One complete addressed root and
its full update-512 training/evaluation computation is one observational unit. Episodes, agents,
roles, slots, actions, suffixes, and evaluation opportunities are within-row computations.

This note does not reopen R01, run an experiment, establish feasibility, inspect a treatment
value, implement R02, or decide lifecycle. It does not seek sign/prevalence, semantic correctness,
relational-mechanism attribution, action sensitivity, held-out-specific interaction, arbitrary
rosters, churn, variable lifetime, UAV value, deployment, or safety.

## Direct observations from the pinned repository

At `aa50efc9f61af7a558e1373ea445f97ff0784b56`:

1. The native numeric endpoint lies in `[0,1]`, so each direct or competence contrast lies in
   `[-1,1]`. No proved actual-DGP invariant supplies Gaussianity, symmetry, sign exchangeability,
   or a smaller variance/support class.
2. `contracts/core.py` fixes the R01 experiment ID, exactly 24 record labels, an inactive
   28-member mean-inference contract, and the update-512 work vector.
3. `preflight.py` accepts a nonempty provenance string but requires 24 *unique* lowercase-hex roots.
   It neither generates nor witnesses a with-replacement product root law.
4. `rng.py` puts `seed_block` in both legacy and semantic addresses. A semantic value must begin
   with `FRRIE-`; the fixed `L_star` above satisfies that local syntax. The current callers still
   use the per-record block label, so compatibility of the string is not R02 conformance.
5. `analysis.py` consumes the R01 28-member family and one global support receipt. It has no
   Bernoulli ancillary input, four-count R02 IUT, or reduced R02 result map.
6. The accepted exact learned-arm ledger for 916 blocks is `4,667,408,384` environment slots,
   `3,626,968,371,982,336` conventional static FLOPs, `937,984` backward/Adam steps,
   `3,751,936` evaluation opportunities, `48,990,904,320` learned decisions, and
   `3,301,703,680` suffix future actor steps. Wall time, peak RSS, scratch, durable I/O,
   serialization, and concurrency scaling remain unobserved.

These are code/document observations and work identities. They are not treatment evidence or a
runtime-feasibility observation.

## Exact fixed-`L_star` root population

Let rows be indexed prospectively by `s=1,...,916`. The root packet contains exactly 916 contiguous
32-byte rows. Before any model, outcome, or result exists, sample

\[
R_s \overset{iid}{\sim} \operatorname{Uniform}(\{0,1\}^{256}),
\qquad
P(R_{1:916}=r_{1:916})=2^{-256\cdot916}.
\]

The raw packet therefore contains exactly `916 * 32 = 29,312` root bytes. No master seed, PRF
expansion, uniqueness filter, collision reroll, result-dependent replacement, or optional stop is
part of this population law. A root may equal an earlier root. The repeated row is still a legal
iid draw and retains its row weight.

Each row may carry a unique storage record ID such as `FRRIE-R02-ROW-0001` through
`FRRIE-R02-ROW-0916`. The record ID and row ordinal may locate a packet row, checkpoint, or result
record, but neither is a field, salt, domain tag, draw value, or byte in an `AddressedRNG` input.
Every RNG address instead receives the same exact
`seed_block="FRRIE-R02-LSTAR-20260831-01"`; only the directly stored 256-bit root differs by row.
The fixed string is ASCII/UTF-8 byte-identical and is not normalized, case-folded, timestamped, or
derived from a record ID.

Root sampling is independent of the ancillary packet below. The execution remains deterministic
given `(R_s,L_star)` and the frozen implementation/work contract. Two equal roots therefore induce
equal execution paths; their independently sampled ancillary words remain distinct iid draws.

## Exact binary64-to-Bernoulli law

### Accepted input and integer threshold

For each row, the four inputs, in this exact order, are

```text
1 d_N6  = J_PHY,int(N=6)  - J_EDGE,int(N=6)
2 d_N21 = J_PHY,int(N=21) - J_EDGE,int(N=21)
3 e_N9  = J_EDGE,int(N=9) - J_UNIFORM,int(N=9)
4 e_N15 = J_EDGE,int(N=15)- J_UNIFORM,int(N=15)
```

Each `X_sj` is the exact real value represented by the final finite IEEE-754 binary64 bit pattern
emitted by the frozen manifest-order `math.fsum` reduction and binary64 contrast operation. No
decimal text, re-evaluation, higher-precision substitute, or post-hoc clamp defines `X`.

Interpret the canonical 64-bit pattern as unsigned `W`, with

```text
s = W >> 63
e = (W >> 52) & 0x7ff
f = W & (2^52 - 1)
```

Reject the entire attempt if `e=2047`, if the decoded value is nonfinite, or if it lies outside
`[-1,1]`. For an accepted pattern define

\[
T(W)=
\begin{cases}
(-1)^s f, & e=0,\\
(-1)^s(2^{52}+f)2^{e-1}, & 1\le e\le1023,
\end{cases}
\qquad
M(W)=2^{1074}+T(W).
\]

The explicit range check permits `e=1023` only at `f=0`; larger magnitudes are invalid. Both
signed-zero patterns map to `M=2^1074`. The endpoints map as `X=-1 -> M=0` and
`X=+1 -> M=2^1075`. For every accepted pattern,

\[
\frac{1+X}{2}=\frac{M}{2^{1075}},\qquad 0\le M\le2^{1075}.
\]

For a subnormal, this follows from `X=(-1)^s f 2^-1074`; for a normal it follows from
`X=(-1)^s(2^52+f)2^(e-1075)`. Thus 1075 fair bits are sufficient and exact for every accepted
binary64 input.

### Ancillary packet, bit order, and endpoint behavior

Before outcomes, directly sample `916 * 4 * 1075 = 3,938,800` mutually independent fair bits,
independent of all root and execution randomness. Pack them as one uninterrupted
`492,350`-byte stream; there is no per-word padding. Bytes occur in file order and bits within
each byte occur most-significant-bit first. Partition the bit stream first by row `s=1,...,916`,
then by the four-component order above, then by bit position `r=0,...,1074`. Interpret one word as

\[
B_{sj}=\sum_{r=0}^{1074} b_{sjr}2^{1074-r}.
\]

Set

\[
Y_{sj}=\mathbf 1\{B_{sj}<M(X_{sj})\}.
\]

The strict `<` rule is fixed. Exactly 1075 bits are consumed even when `M=0` or `M=2^1075`; there
is no shortcut, `<=`, reroll, rejection, decimal probability, or result-dependent seed choice.
The ancillary packet is output-disconnected from roots, model initialization, DGP tapes, training,
completion, checkpoints, and native evaluation. It is opened for this mapping only after the full
916-row numeric panel has passed structural validation.

The complete prospective random input is therefore `29,312 + 492,350 = 521,662` direct bytes,
apart from nonrandom metadata. A PRF expansion from a shorter master does not instantiate the
stated product law without a different pseudorandomness assumption.

### Mean preservation and independence

For every row and component,

\[
P(Y_{sj}=1\mid X_{sj})=\frac{1+X_{sj}}2,
\qquad
E[Y_{sj}]=\frac{1+\mu_j}2,
\qquad
\mu_j=E[X_{sj}].
\]

Because `(R_s,B_{s1},...,B_{s4})` are iid across rows, each component sequence is iid Bernoulli
with parameter `(1+mu_j)/2`, even though the four components within a row may have arbitrary
dependence. Conditional on a realized root packet the success probabilities may differ by row;
the exact binomial law is the prospective unconditional law over the direct iid root-and-ancillary
population. Duplicate root bytes do not alter it.

The transformation preserves the expectation of the frozen *numeric binary64 contrast*. It does
not preserve root-wise sign, median, prevalence, an unrounded real-arithmetic estimand, or a
mechanism attribution.

## Support and completion law

The four simple R02 contrasts require no R01 event/basin/role support predicate. For every root,
the frozen mathematical host has fixed rosters, events, roles, actions, and a total native endpoint;
the complete evaluation defines all four contrasts. Realized absence of a favorable action,
delivery, projection contact, or basin success is an outcome and must remain in `X`, not a support
filter.

Accordingly, R02 has no random scientific support gate and no
`NONIDENTIFICATION_ENDPOINT_SUPPORT` branch. The following are instead whole-attempt structural
invalidity:

- a missing, extra, filtered, reordered, or selectively retried row;
- a missing/partial cell, episode, checkpoint, work receipt, or ancillary word;
- a nonfinite or out-of-range endpoint/contrast, malformed binary64 pattern, or numeric drift;
- a root/ancillary law, `L_star`, address, information, work, RNG, checkpoint, or bit-order mismatch;
- a resource abort, process failure, unavailable native path, or partially published panel; or
- reading ancillary bits during execution or using any observed value to alter completion.

Such an attempt returns `INVALID_NO_SCIENTIFIC_RESULT`, publishes no scientific component value or
count, and supplies no arm polarity. Under the repository incomplete-assignment rule it does not
consume the scientific object. If malformed input is detected before either packet is unsealed and
before any scientific computation starts, the unopened packets may be discarded and the entire
input drawn afresh. Once either packet is unsealed or any scientific computation starts, the
916 root rows and all ancillary words are immutable: after an outcome-blind technical repair, a
replacement evidence attempt must rerun the same full packet from zero. It may not redraw,
substitute, retain only completed rows, or salvage partial scientific values. This same-packet law
prevents retry-to-success from conditioning the root population. A root-dependent technical defect
must still be eliminated or explicitly bounded before the rerun can instantiate the total object.

The `0.800537003890475350` number is the power of the total mathematical 916-row test. It is not a lower
bound on the operational probability of reaching a supported terminal. If an additional support or
completion event with failure probability `delta` is admitted, the assumption-free bound becomes
at best `0.800537003890475350 - delta`. Retaining terminal power at least `0.80` would require
`delta <= 0.000537003890475350`, and no current evidence supplies such a bound. This is why runtime
completion/resource conformance remains a registration blocker rather than a fifth statistical
gate.

## Fixed 916-block IUT and result map

Let `K_j=sum_s Y_sj`. For direct components the null boundary is `mu_d=0.04`, hence
`p_d0=0.52`; for competence components it is `mu_e=0.08`, hence `p_e0=0.54`. The material
alternative adds

\[
\eta=13/120
\]

to each applicable mean, giving `p_d1=0.574166666666...` and
`p_e1=0.594166666666...`.

At `B=916`, use the deterministic component rules

```text
d_N6:  reject mu_d6  <= 0.04 iff K_d6  >= 502
d_N21: reject mu_d21 <= 0.04 iff K_d21 >= 502
e_N9:  reject mu_e9  <= 0.08 iff K_e9  >= 520
e_N15: reject mu_e15 <= 0.08 iff K_e15 >= 520
```

The exact boundary calculations are:

| Component type | Null size | Power at margin plus `13/120` |
| --- | ---: | ---: |
| direct | `0.0478240738057681852` | `0.948491485084943734` |
| competence | `0.0494856054885349336` | `0.951777016860293941` |

The global null is the union of the four component nulls. Reject it only when all four component
rules reject. Under any global-null joint law, the rejection event is contained in at least one
true component's rejection event, so global size is at most `0.05` without Bonferroni division or
cross-component independence. At the four-component material alternative, the union bound gives

\[
1-2(1-0.948491485084943734)-2(1-0.951777016860293941)
=0.800537003890475350.
\]

After structural validity, the result map is exhaustive:

1. all four component tests reject:
   `SUPPORTED_FIXED_LSTAR_FIXED_UPDATE_MEAN_PACKAGE_EFFECT`;
2. either competence component does not reject:
   `VALID_NONPASS_COMPETENCE_NOT_ESTABLISHED`;
3. both competence components reject but either direct component does not:
   `VALID_NONPASS_DIRECT_EFFECT_NOT_ESTABLISHED`.

Every valid terminal reports all four counts and fixed flags. A nonpass is not equality, harm,
wide-package superiority, lack of projection contact, absence of a package effect, or direction
closure. There is no seen-equivalence, interaction, basin, cut, TV, attenuation, semantic, or
mechanism branch in R02.

## Three noninterchangeable meanings of a smaller object

### A. Same update-512 four-roster claim, fewer than 916 rows

The fixed nonrandomized 916 construction is not certified minimal. An independently recalculated
exact-size randomized-boundary candidate at `B=909` is:

```text
direct:     always reject at K>=498; at K=497 reject with gamma_d
competence: always reject at K>=517; at K=516 reject with gamma_e

gamma_d = (1/20 - P_Bin(909,13/25)[K>=498]) / P_Bin(909,13/25)[K=497]
        ~= 0.0562820658416534381
gamma_e = (1/20 - P_Bin(909,27/50)[K>=517]) / P_Bin(909,27/50)[K=516]
        ~= 0.947608365061704631
```

It gives marginal powers approximately `0.949385474464315069` and
`0.950966073633907577`, hence the same dependence-robust union-bound certificate is approximately
`0.800703096196445291`. It retains the four individual roster conditions and update-512 claim, but
saves only seven rows (`0.764%`).

This is a mathematical candidate, not yet the selected exact object. Each `gamma` is rational but
not shown to be dyadic; a valid executable design must supply finite exact decision randomization,
fixed consumption/order, independence, endpoints, and no reroll selected by results. Pro must also
decide whether a different multivariate bounded-mean test can beat 909 uniformly, or prove an
appropriate lower bound. The known 523-block single-component necessity does not prove a
four-component minimum.

### B. Equal-weight roster-mixture mean claim

A scientifically narrower object may preregister

\[
D_s=\tfrac12[d_s(6)+d_s(21)],\qquad
E_s=\tfrac12[e_s(9)+e_s(15)]
\]

and test only `E[D]>0.04` and `E[E]>0.08`. With the same material increment, a locally
recalculated exact-size randomized two-component certificate first crosses 80% at about `B=720`:

```text
direct mixture:     always reject at K>=397; at K=396 randomize with ~=0.0617388471662627759
competence mixture: always reject at K>=412; at K=411 randomize with ~=0.717502889656126778
marginal powers:    ~=0.899218905289616720 and ~=0.901353156843207080
joint lower bound:  ~=0.800572062132823800
```

A deterministic-boundary version first reaches the analogous local certificate at about 732
rows. These counts are arithmetic checks, not a frozen new object.

The mixture law itself must be exact. If `D_s` and `E_s` are exact averages of two binary64
contrasts rather than a newly rounded binary64 number, the dyadic denominator can require one more
bit and the ancillary threshold law must be revised. Alternatively, a final binary64 rounding or
an independent preregistered roster-selection coin defines a different exact numeric estimand.
Pro must specify which law it certifies.

The claim loss is material: a passing average may mask a null, negative, or incompetent individual
roster. It supports only the predeclared equal-weight roster-mixture expected numeric return, not
both `N=6` and `N=21` direct effects or both `N=9` and `N=15` competence conditions.

### C. Different update/work or staged/sequential execution

A lower fixed update count or cheaper trainer changes the root-to-contrast law and yields a new
package/budget object. It may retain a mean-return endpoint, but it cannot inherit update-512
package polarity, the material alternative's actual attainability, or resource conclusions. Its
exact work, comparator competence, block law, margins, and claim must be frozen anew.

A competence-first execution can preserve the four-test statistical object only if all root and
ancillary rows, cutoffs, stage rules, and later paired computations are sealed prospectively, with
no row replacement or result-selected change. It may reduce expected work under incompetence, but
does not reduce the maximum successful-object row count or the positive-branch work.

A supplied sequential candidate Bernoulliizes the same components, uses SPRT boundaries
`+/-log(20)`, caps at 2048 rows, and makes a cap-undecided component a nonpass. Its reported
single-component alternative ASN is about `463--467` and its four-condition joint-power lower
bound is about `0.8078`. Those facts do not imply a cheaper four-condition panel. All components
share each expensive update-512 block; the positive IUT waits for `max_j T_j`, not one `T_j`.
The supplied dependence-robust upper bound for `E[max_j T_j]` is about `920.95`, already above
916, while `822.19` is only an independence approximation. Worst-case use is 2048 rows, about
`2.236` times the 916-row work. Until exact finite boundary-crossing errors, joint dependence,
whole-panel stopping, invalid completion, and `E[max T]` are certified, this is a counterexample
to ASN-based cost rhetoric, not a robust reduction. A truly smaller sequential object needs a
dependence-robust expected and maximum-work statement with its claim loss made explicit.

Sign, median, majority, or prevalence is not an answer to A, B, or C because none contains or is
contained by expected numeric native return over the protected bounded class.

## Observation, inference, and claim ceiling

The repository incompatibilities and absent runtime measurements above are direct observations.
The binary64 integer decoder, bit count/order, binomial sizes/powers, IUT level proof, 909 and 720
candidate calculations, and completion-power penalty are mathematical inferences from the stated
laws. No result-bearing experiment, root generation, model initialization, evaluation, or
treatment observation occurred.

If a conforming 916-row R02 later passes validly, the maximum positive interpretation is:

> Under the exact uniform 256-bit root population with replacement, fixed
> `L_star="FRRIE-R02-LSTAR-20260831-01"`, exact binary64 ancillary law, and fixed update-512
> `RIDGEGATE-2Z/RSCF` work vector, the tight projection/optimizer package had a material mean
> numeric native-return advantage over a mean-competent wide package at each evaluated held-out
> `N={6,21}` cell and each seen competence `N={9,15}` cell.

This is a projection/optimizer-package effect at one host and work vector. It does not establish
held-out-specific interaction, action sensitivity, semantic-column use, relational-mechanism
value, generic representation or information advantage, arbitrary `L_star`, arbitrary roster,
churn, lifetime, asymptotic efficiency, deployment, or safety. Partner co-adaptation, the shared
`K0` chart, shrinkage, optimizer geometry, and host alignment remain live explanations.

For alternative B the ceiling is narrower still: only the equal-weight roster-mixture mean is
supported. For alternative C the ceiling must name its different update/work/stopping object.

## Remaining blockers and next discriminator

Before any R02 registration or result activity, the following remain unresolved:

1. independent Pro review must validate or refute the exact binary64/root/support/completion/result
   law and separately adjudicate smaller-object levels A, B, and C;
2. the randomized 909 object does not materially improve the deterministic 916 resource question;
   only a materially cheaper, preregistered-total-cost mean-return discriminator that can really
   select an architecture is a distinct decision-relevant scientific alternative;
3. CM would need a new R02 implementation contract that decouples record IDs from `seed_block`,
   accepts duplicate roots, binds the direct ancillary packet, deletes the R01 support/28-family
   analyzer, and implements the new result map; current V2 is evidence only;
4. a value-blind production-conformant resource observation must bound wall time, peak process-tree
   RSS, scratch, durable I/O, checkpoint serialization, and concurrency under a prospectively fixed
   plan; and
5. any root-dependent completion risk must be eliminated or explicitly included without erasing
   the 80% guarantee.

A sound universal first-native-action noncontact proof would close the treatment without this
purchase. A valid dependence-robust smaller mean-return object with clearly lower preregistered
total cost and an architecture-selecting result map could change the preferred scientific design.
A resource observation showing disproportionate or unsafe cost could remove the 916-row purchase
without supplying arm polarity. Failure to complete a technical attempt is not scientific
evidence.

## Exact evidence paths

- `AGENTS.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/research/portfolio/PORTFOLIO.md`
- `docs/research/portfolio/FIVE_DIRECTION_HANDOFF_20260831.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/DIRECTION.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/IMPLEMENTATION_THRESHOLD.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/INFERENCE_AND_EXECUTION_FREEZE.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R01_INFERENCE_RESOLUTION_EVIDENCE_20260831.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R02_MEAN_PRESERVING_IUT_PRO_INTAKE_20260831.md`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/contracts/core.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/preflight.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/analysis.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/rng.py`
