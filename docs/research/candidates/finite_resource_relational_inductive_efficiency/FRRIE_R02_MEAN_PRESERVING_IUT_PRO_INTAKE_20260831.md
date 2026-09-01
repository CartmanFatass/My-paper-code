# FRRIE R02 mean-preserving IUT Pro intake — 2026-08-31

## Conclusion

Disposition: `CONDITIONAL_MATHEMATICAL_PASS / NEW_PROSPECTIVE_OBJECT /
BLOCKED_EXACT_LAW_AND_RESOURCE`.

The archived Pro memorandum supplies a valid existence construction for a distribution-free,
expected-native-return successor: conditionally Bernoulliize each of four root-level contrasts and
apply a four-component intersection-union test over exactly 916 complete blocks. Independent
recalculation reproduces its count thresholds, type-I errors, marginal powers, dependence-robust
joint-power lower bound, necessary component counts, and work totals.

This is not an inference repair, activation, continuation, or result for R01. It changes the root
population and sampling law, adds ancillary inference randomization, deletes most R01 estimands and
branches, and requires a new result map. R01 remains closed before production with no
`PHY_TRUST`/`EDGE_FLEX` polarity.

The proposed R02 is not yet a frozen conclusion-bearing object. Before registration it must replace
the memorandum's non-unique randomization wording with one finite exact law, select one complete
root/`seed_block` population law, and define how structural completion and any support gate enter
the power claim. After those repairs, resource feasibility would still block execution: the exact
work is known, but result-process wall time, peak RSS, scratch, durable I/O, serialization cost, and
concurrency scaling are unobserved. Direction-local advice therefore remains `PARK`; Root alone
owns any Portfolio action.

## Question and non-goals

The smallest decision-changing question is whether the R01 reentry search has found a prospective
expected-return design with at least 80% power at the registered material alternative under the
protected arbitrary bounded root class, without substituting sign prevalence for mean native
return.

The treatment remains `PHY_TRUST`; the competent containing comparator remains `EDGE_FLEX`; and
`UNIFORM_LEGAL` remains an evaluation-only seen-size competence floor. One complete addressed key
and its full update-512 training/evaluation computation is one observational unit. Episodes,
agents, roles, actions, suffixes, and evaluation opportunities remain within-block computations.

This intake does not observe a treatment value, authorize roots or models, establish resource
feasibility, reopen R01, or decide Portfolio lifecycle. It does not seek semantic correctness,
relational-mechanism attribution, action sensitivity, seen-to-held-out interaction, arbitrary-`N`
transfer, churn, variable lifetime, UAV value, deployment, or safety.

## Inputs

- `temp/sessions/hmasd-chatgpt-pro-transport/archive/finite_resource_relational_inductive_efficiency/portfolio-frrie-reentry-20260831-01/RESPONSE.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/DIRECTION.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/IMPLEMENTATION_THRESHOLD.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/INFERENCE_AND_EXECUTION_FREEZE.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R01_INFERENCE_RESOLUTION_EVIDENCE_20260831.md`
- `docs/research/legacy/directions/semantic_graphon_shared_policy/SGSP_RSCF_SHORT_GATE_R01_SYNTHESIS_EVIDENCE_20260829.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- the 2026-08-31 FRRIE row in `docs/research/portfolio/PORTFOLIO.md`

Only the archived response was used as the new Transport-delivered input. No Transport registry,
browser, conversation state, or send process was inspected.

## Direct observations and evidence interpretation

The current accepted evidence supplies only the root-level support

\[
X_{sj}\in[-1,1]
\]

for the four direct/competence contrasts. Pairing makes each contrast well-defined under matched
work but proves neither positive arm covariance nor a variance bound below one. No cited
actual-DGP invariant narrows that class. This is an absence of a proved narrower class, not proof
that endpoint variance one is realized.

The current V2 surface accepts arbitrary distinct root strings plus provenance rather than directly
generating the required population sample. It also uses `seed_block` in RNG addresses. Therefore
different record labels cannot be presumed scientifically inert, and the existing unique-root R01
packet is not the iid R02 law.

The accepted per-arm, per-block work ledger is `2,547,712` complete-panel environment slots and
`1,979,786,229,248` conventional static FLOPs. Current evidence explicitly leaves result-process
resource conformance unobserved. Structural tests and the bounded native smoke are not throughput,
RSS, scratch, or durable-storage measurements for the complete workload.

The Pro construction is prospective design mathematics. It contains no return, contact, support,
competence, or package-polarity observation.

## Independent mathematical audit

Let the four block statistics be

\[
X_{s,d6},\ X_{s,d21},\ X_{s,e9},\ X_{s,e15}\in[-1,1],
\]

with corresponding population means `mu_d6`, `mu_d21`, `mu_e9`, and `mu_e15`. If, independently
for every `(s,j)`,

\[
Y_{sj}\mid X_{sj}\sim\operatorname{Bernoulli}((1+X_{sj})/2),
\]

then

\[
P(Y_{sj}=1)=(1+\mu_j)/2,\qquad \mu_j=2E[Y_{sj}]-1.
\]

Thus the transformation preserves expected numeric native return, not the sign, median, or
prevalence of a root contrast. With iid complete keys and independent ancillary randomization, the
`Y_sj` values are iid Bernoulli across blocks even when the original bounded contrast distribution
is otherwise arbitrary.

At `B=916`, reject each direct null `mu_d <= 0.04` when `K_d >= 502` and each
competence null `mu_e <= 0.08` when `K_e >= 520`. Independent recalculation gives:

| Component | Null size | Power at margin plus `13/120` |
| --- | ---: | ---: |
| direct | `0.047824073806` | `0.948491485085` |
| competence | `0.049485605489` | `0.951777016860` |

Reject the global union null only when both direct and both competence tests reject. The global
size is at most `0.05`: whenever the union null is true, the joint rejection event is a subset of
the rejection event for at least one true component null. No Bonferroni division and no
cross-component independence assumption are required. At the four-component alternative, the
union bound gives

\[
1-2(1-0.948491485085)-2(1-0.951777016860)
=0.800537003890.
\]

The existing least-favorable endpoint calculation is also reproduced: 523 blocks are necessary
for the direct component and 518 for competence to reach 80% marginal power. They are not a
sufficient joint design. The 916 count is the first count found for this fixed, nonrandomized
binomial count cutoff plus the displayed union-bound certificate; it is not a global lower bound
over all multivariate tests. A second randomized count boundary reaches the analogous certificate
at 909 blocks but adds another random decision layer.

The material power separation must be described as the preregistered expected per-episode `J`
scale quantity `13/120`, not as one realized delivery in a 256-episode panel.

## Exact-law blockers before registration

### 1. Ancillary Bernoulli randomization

The memorandum's abstract continuous-uniform identity is correct, but “fair-bit streams sufficient
to realize `U`” does not uniquely define a finite executable law. In particular, using the usual
grid `U=B/2^K` with `U <= q` adds one success atom.

One exact repair is available. Treat each registered `X` as the exact real value of its final finite
binary64 bit pattern. Then `q=(X+1)/2=M/2^1075` for an exact integer `M`. Before any outcome, seal
independent

\[
B_{sj}\sim\operatorname{Uniform}\{0,\ldots,2^{1075}-1\}
\]

and set `Y_sj = 1{B_sj < M_sj}`. This consumes exactly 3,938,800 independent fair bits, or
492,350 bytes, for 916 blocks and four components. An equivalent `<=` convention may use
`U_plus=(B+1)/2^1075`. A frozen object must choose one formulation and bind bit order, fixed bit
consumption, endpoints, nonfinite handling, exact binary64 decoding, output disconnection, and no
decimal recomputation, reroll, or result-dependent seed choice.

### 2. Complete-key population and generation

The simplest candidate population fixes one exact scientific `seed_block=L_star` value in every
RNG address, keeps filesystem/record block IDs outside RNG, and samples 916 roots independently
and uniformly with replacement from `{0,1}^256`. Duplicate roots are valid and retain ordinary
sample weight; duplicate records remain invalid.

The direct generation law must have the full product probability

\[
P(R_{1:916}=r_{1:916})=2^{-256\cdot916}.
\]

Expanding one 256-bit master through a PRF does not establish that product law without adding a
different RNG assumption. A direct implementation can preseal 916 independent 256-bit root rows.
The alternative proposal to sample `(seed_block,root)` pairs is not complete until the
`seed_block` domain, encoding, distribution, and joint replacement law are fixed.

This with-replacement population deliberately differs from R01's unique-root law and from the
current DIRECTION reentry wording that names ordered uniform sampling without replacement. It can
be adopted only as an explicit new scientific object and authority revision, never as an R01
activation.

### 3. Support, completion, and power semantics

The `0.800537003890` bound is the probability that all four count tests reject under the stated
four-mean alternative. If an additional random support gate, root-dependent completion event, or
retry-to-success law precedes the supported terminal state, the displayed number is not
automatically that terminal state's power. Registration must either make every extra admission a
deterministic pre-root condition, include its failure probability in the power event, or narrow the
claim accordingly.

No missing, filtered, replaced, or selectively retried outcome-bearing block is permitted. A
root/path-dependent technical failure cannot be repaired by repeatedly drawing panels until one
completes. Incomplete attempts remain invalid and quarantined under the repository rule; a valid
fresh replacement still requires a prospectively repaired completion law and supplies no salvage
from earlier values.

The exact support predicate also needs to be named or deleted. A generic reference to a “required
event/basin/role opportunity” is insufficient for a conclusion-bearing result map.

## Resource boundary

For 916 blocks and both learned arms, the accepted ledger implies:

- `4,667,408,384` environment slots;
- `3,626,968,371,982,336` conventional static FLOPs;
- `937,984` backward calls and Adam steps;
- `3,751,936` evaluation opportunities;
- `48,990,904,320` learned policy decisions;
- `3,301,703,680` suffix future actor steps; and
- 1,832 update-512 arm checkpoints, with at least `780,717,792` raw parameter-plus-Adam-moment
  bytes before serialization and metadata.

These are exact work facts, not feasibility evidence. The envelope is approximately 38.17 times
the two-arm work of R01. No listed observation supports either “feasible” or “infeasible.” A fresh
4 GiB admission remains necessary for every eventual result-bearing invocation but cannot by
itself establish the wall-time, I/O, scratch, concurrency, or complete-panel execution envelope.

## Claim ceiling and surviving alternatives

If the exact-law blockers are repaired and the registered test later passes validly, the maximum
positive interpretation is:

> Under one exact fixed-`L_star` addressed-root population and the fixed update-512
> `RIDGEGATE-2Z/RSCF` work vector, the tight projection/optimizer package had a material mean
> numeric native-return advantage over a mean-competent wide package at both evaluated
> `N={6,21}` cells.

This would be a package effect only. Deleting seen equivalence and held-out-minus-seen interaction
means it would not establish that the advantage is specific to the roster shift. Deleting basin,
cut-return, action-TV, and differential-attenuation conditions means it would not establish action
sensitivity, semantic-column use, relational-mechanism value, or host-independent inductive
efficiency. Partner co-adaptation, the shared `K0` convention, ordinary shrinkage, optimizer
geometry, and host alignment remain inside or alongside the package explanation. No broader
representation, information, arbitrary-seed-block, arbitrary-`N`, churn, lifetime, MARL,
deployment, or safety claim follows.

The universal projection-noncontact theorem remains a logically decisive alternative: a sound
proof that every reachable EDGE preprojection proposal stays inside the tight box through update
512 would close the package at exact equality for every root. A concrete admissible contact
witness would refute only that theorem and would provide no return polarity. Existing evidence
contains neither result and supplies no sound reachable-set abstraction or proof-size bound.
Consequently, the theorem has not been shown to be the cheapest actionable discriminator and must
not become an indefinite prerequisite.

## Judgment impact and next observation

- Keep R01 `CLOSE_CURRENT_OBJECT`; do not create its roots, RNG, models, checkpoints, or results.
- Treat `FRRIE-R02-MEAN-PRESERVING-BERNOULLI-IUT` as a candidate new object, not yet a frozen
  registration. Freeze the exact ancillary sampler, one fixed-`L_star` population, direct iid root
  packet, completion/support law, result map, and claim wording first.
- Once those scientific semantics are unique, the object may be registered as
  `BLOCKED_RESOURCE_RUNTIME_CONFORMANCE`; resource uncertainty blocks execution rather than
  negating the derivation.
- Retain direction-level `PARK` advice. Do not update Portfolio from this intake.
- The cheapest concrete next observation after exact-law repair is a production-conformant,
  value-blind resource probe that measures wall time, peak RSS, scratch, durable I/O, and
  checkpoint serialization under one prospectively fixed execution/concurrency plan. A single
  probe may reject obvious infeasibility but cannot alone prove the complete 916-block envelope.
- A bounded reachability reconnaissance may search for one actual admissible contact witness, but
  failure to find one is not evidence of universal noncontact and the full theorem is not a hard
  gate.

A sound universal noncontact proof would close the treatment. A demonstrated disproportionate or
unsafe resource envelope would remove the 916-block purchase while preserving package
uncertainty. A valid resource/conformance observation plus the exact-law repairs would change the
recommendation from parked design work to a Root-owned decision on registering and funding R02.

`DIRECTION.md` is not changed by this intake because the new information is an inference-design
construction with unresolved population/randomization semantics, not accepted mechanism-level
science.

## Exact evidence paths

- `temp/sessions/hmasd-chatgpt-pro-transport/archive/finite_resource_relational_inductive_efficiency/portfolio-frrie-reentry-20260831-01/RESPONSE.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/DIRECTION.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/IMPLEMENTATION_THRESHOLD.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/INFERENCE_AND_EXECUTION_FREEZE.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R01_INFERENCE_RESOLUTION_EVIDENCE_20260831.md`
- `docs/research/legacy/directions/semantic_graphon_shared_policy/SGSP_RSCF_SHORT_GATE_R01_SYNTHESIS_EVIDENCE_20260829.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/research/portfolio/PORTFOLIO.md`
