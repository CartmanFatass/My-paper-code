# Independent review of the HMASD first investment wave — 2026-09-01

Reviewer: Claude Fable 5.1, local, read-only. Packet:
`docs/research/review_packets/2026-09-01-first-wave-latest-model/`. Packet snapshot `b4d738537`;
HEAD `71b2bba2b` at review close, when the working tree carried 96 uncommitted paths (the packet's
58, mostly CBSC and FRRIE, plus the SCDMP fresh-attempt intake, the VNFC A0 implementation, and
the UCOPE whitening contract and runner written during the review). No repository file was
changed, no experiment, test, or training was run, and no message was dispatched. Four read-only
scouts gathered literature and static code facts; every decision-relevant claim below was checked
against the primary document. Literature labels: `DIRECT`, `CURATOR_OR_PROJECT_INFERENCE`,
`REVIEWER_INFERENCE`, `UNKNOWN`. Evidence standard:
`docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`.

Library state as found: `docs/new-libs` holds 27 curated works with zero PDFs on disk (every
`metadata.json` `source_pdf` dangles); all theorem-bearing chunks cited below are flagged
`equation_text_unreliable` in `docs/new-libs/corpus/qa/EXTRACTION_WARNINGS.md`. InstSci
`metadata/integrity.json` reports 190/190/190 PDFs, structured JSON, metadata records, zero missing;
all 17 mapped InstSci papers were verified at the structured-JSON layer.

## Executive judgment

After roughly two weeks and several hundred documents, the five directions hold exactly one valid
learner observation on a first-wave object (UCOPE B1: every arm `0/3` competent) and one valid
descriptive signal (SCDMP FCEOV `.3`: the graph-matched action beats both the swapped and the common
action on every one of 562 held-out tapes, recorded as a "nonpass" only because a worst-case
distribution-free bound was pre-registered). Everything else is definition, contract, or a
quarantined attempt. The binding constraint is not scientific uncertainty. It is that artifact
contracts written for C-FORMAL claims are being applied to B/EXPLORE runs, so learners that exist
and work do not run. The static code audit makes this concrete: across the five implementations
about 20,000 lines are scientific (host, model, learner, evaluator) and about 44,000 are
contracts, telemetry, publication, and validators; CBSC's complete B1 chain is refused by a literal
`FORMAL_ANALYSIS_BOUND = False`; SCDMP's RUN-01 finished and wrote its held-out analysis before a
telemetry race quarantined it unread.

The repository moved on three of the five while this review was being written, and the sections
below reflect the state at close on 2026-09-01. SCDMP's Innovator ruled the fresh named attempt
lawful (`FRESH_NAMED_ATTEMPT_VALID`) and a fresh readiness assessment now projects about 350 s of
work against an 1,800 s cap. VNFC implemented its A0 law (about 5,600 new lines, including a
source-owned scalar reverse-mode graph) and still has not run it. UCOPE's Convergence chose a
two-arm Cholesky-whitening discriminator on the unchanged host and competence gate; a source audit
done for this review finds a simpler suspect, an optimizer-exposure shortfall of about an order of
magnitude, that no object has tested.

Dispositions, ordered by expected information per unit of effort:

| Direction | Disposition | Scope | One-line reason |
| --- | --- | --- | --- |
| SCDMP | `CONTINUE` | B01 `RUN-01-REPLACEMENT-01` (fresh master) | Clean engineering, real native UAV host, prior every-tape positive signal. The "replacement identity" blocker was a rule collision; the repository's Innovator has since resolved it the same way (`FRESH_NAMED_ATTEMPT_VALID`), and the fresh `A-R2` readiness assessment projects about 350 s against the 1,800 s cap. Only the launch remains. |
| CBSC | `CONTINUE` | OMRC-B01 three-seed B1 | Cheapest real recurrent-PPO run in the portfolio; drop the consumer-recompute and capacity gates, add a budget ladder so a small-budget null is not mistaken for a mechanism null. |
| UCOPE | `RECAST` | Competence-first budget rule, host margin, and criterion | Four consecutive competence failures on ~0.04-utility margins under exact-oracle competence criteria, with an offline fitted-Q learner. A source audit adds a simpler suspect: at lr 3e-4 for 160/320 AdamW updates the Bellman coefficients can move about 0.05–0.1 from a Glorot initialisation of order 1, an exposure shortfall of roughly an order of magnitude. Run the exposure ladder and the already-contracted whitening discriminator now (minutes each), the margin-scaled falsifier next; PARK only if all fail. |
| VNFC | `RECAST` | R02 finite-action law + A0 | Canonical sort by opaque rank already gives presentation safety; the 304-row binary64 law is C-FORMAL machinery on a B question. Replace with a unit-test-scale conformance check and run the R02 DEBUG and three 64-update seeds. A0 has since been implemented (about 5,600 new lines, including a hand-written scalar reverse-mode graph) and still has not run, which is the over-formalization in action. |
| FRRIE | `CONTINUE` | B01 matched curves | Legitimate but narrow question (the arms differ only in a clipping box on 18 of 35,513 parameters); run a stripped 512-update chain, not the ordered-28 / TV / parameter-distance panel. |

Portfolio-level: the wave is over-spending on formal scaffolding relative to learners. Every
direction has at least one exact, bitwise, or telemetry requirement that cannot change a B/EXPLORE
decision and is currently blocking a launch.

---

## 1. FRRIE — finite-resource relational inductive efficiency

### scientific_motivation

Whether a tight, host-aligned relational projection learns faster than a strictly containing wider
one at a fixed update budget is the finite-sample form of the inductive-bias-versus-expressivity
question that underlies every permutation-equivariant, graph, or mean-field MARL architecture. It
matters beyond the artifact because variable-`N` policies are usually argued for on expressivity
grounds, while the practical case for structure is sample and optimization efficiency at the
budgets people actually train with. The held-out `N={6,21}` cells add whether the prior also buys
cross-roster generalization at that budget.

### mechanism_prediction

What the two arms actually are matters here. Per
`FRRIE_B01_INNOVATOR_DECISION_INTAKE_20260901.md` and `arms.py`, `PHY_TRUST` and `EDGE_FLEX` share
the same 35,513-parameter actor/critic and the same `K0`-centered chart and differ only in the
post-Adam projection box: the 18 relational coefficients `beta` are clipped to `[-0.15, 0.15]` in
the tight arm and `[-1.50, 1.50]` in the wide arm. The mechanism is therefore a hard prior around
the host-aligned convention `K0` on 18 parameters. Prediction: keeping `beta` near `K0` prevents
early optimizer excursions the wide arm must later unlearn and preserves the relation alignment
that transfers to held-out `N`. The advantage should appear only after "projection contact" (the
first update at which clipping changes an FP32 value), be largest at held-out `N`, and shrink or
vanish under `SEMANTIC_COLUMN_ROTATE`, which breaks the alignment `K0` encodes. `REVIEWER_INFERENCE`:
this tests whether a *correct* prior helps at a small budget, not relational structure in general;
the informative outcome is actually the negative one, the wide arm recovering alignment on its own
within 512 updates.

### strongest_alternative

1. **No-contact equality.** The arms are byte-paired at update 0 and differ only in the `beta`
   box. If Adam never pushes any of the 18 `beta` values past `±0.15` in 512 updates, both arms
   trace the same path and the comparison is vacuous (`B01_OBSERVED_PATH_EQUIVALENCE`).
   `DIRECTION.md` records that generic clipped Adam admits both contact and non-contact histories
   (~0.1536 same-sign displacement witness), so this is live.
2. **Shrinkage/optimizer geometry.** Any tight advantage is explained by a better-conditioned loss
   surface, not relational semantics. The reassociation cut is the only control that separates
   these; a cut-insensitive gain is the shrinkage explanation.
3. **Wide-package incompetence.** If `EDGE_FLEX` fails the `UNIFORM_LEGAL` bar (`e_512 < 0.08`),
   the object is nonidentifying.

The earlier VNFC-B1 result (`VNFC_B1_SCIENTIFIC_INTAKE.md`, 8 paired seeds) is a portfolio-internal
warning for this class of comparison: a large "structured package" gain was fully explained by
hand-injected action construction, and a zero-bid greedy rule beat every learned arm.
`REVIEWER_INFERENCE`: FRRIE's contrast is exposed to the same failure unless contact and
reassociation are reported alongside return.

### current_evidence

- **Direct observations.** None on B01. R01 (24-root mean object) closed for inference power, no
  polarity. R02 (916/909-row Bernoulli IUT) closed for cost (`4.67e9` environment slots), no
  polarity. Three integrated TEST-only attempts quarantined for outcome-blind conformance defects
  (NaN-sentinel equality, FP32 non-associative loss identity, duplicated FP64 waste ratio).
- **Engineering readiness.** Native A/RECON: 48 scalar/batch rows equal, 24 rows equal across 1/2/4
  workers, 6.9 s wall; FP32 primitive-to-return derivation unified (`5f0e4ef4`, 94 passed); Slice A
  plan gate clean (`1ee17161`, 104 passed). Static audit: 19,560 Python lines, about 5,300
  scientific versus 14,200 scaffolding, and inside `b01/` about 1,500 versus 8,400. The single
  paired update (`PairedB01Trainer.update`), the width-32 collector, the policy, and the evaluator
  cell exist; there is no 512-update loop anywhere (`range(UPDATES)` occurs only inside
  validators). `b01/panel.py` and `b01/analysis.py` raise `PRODUCTION_*_UNAVAILABLE/REPAIR_REQUIRED`;
  `production_runner.py` carries four `_BLOCKERS` and `launch_capable: False`; the native DLL
  directory is empty, so the first real run pays an MSVC compile. Slice B is uncommitted WIP; Slices
  C, D, E are not started.
- **Invalid/quarantined.** The three TEST attempts; nothing readable.
- **Inference.** `REVIEWER_INFERENCE`: what is missing is a loop that calls existing components 512
  times with checkpoints, not new science.

### main_scientific_difficulty

Attribution. A held-out return gap for `PHY_TRUST` can be produced by relation alignment,
shrinkage, an optimizer-path accident on three seeds, or an `EDGE_FLEX` that has not yet contacted
its extra capacity at update 512 and would overtake later. Only the first is the direction's claim.
The design contains the two controls that matter, contact index and reassociation cut, but with
three seeds and one budget the last two alternatives cannot be excluded; the claim ceiling must say
so.

### main_engineering_difficulty

One paired 512-update trainer with checkpoint save/load at six updates and a streamed evaluator
over `{6,9,15,21} x {INTACT, ROTATE} x 2 arms`. That is the whole requirement. The production
plan's Slices C–E (typed shard descriptors, ordered-28 quantities, action-TV sidecar, L-infinity
parameter-distance trace, kappa derivation, `.creating/.incomplete` transactions, seven-stage
process-tree telemetry) are not required for a valid B result.

### overformalization_audit

| Requirement | Class | Reason |
| --- | --- | --- |
| Byte-paired initialization, shared minibatch order, common environment RNG across arms | `SCIENTIFICALLY_NECESSARY` | Defines the paired estimand and makes "contact" meaningful. |
| `SEMANTIC_COLUMN_ROTATE` reassociation cut | `SCIENTIFICALLY_NECESSARY` | Only control separating relational alignment from shrinkage. |
| `UNIFORM_LEGAL` competence bar for `EDGE_FLEX` | `SCIENTIFICALLY_NECESSARY` | Prevents reading comparator incompetence as treatment gain. |
| Projection-contact index `kappa_s` | `ENGINEERING_INTEGRITY` (keep as diagnostic) | Tells whether the comparison is non-vacuous; not a gate. |
| Exact `TOP24/2^24` FP32 uniform lattice, producer/validator duplicate derivation | `REMOVE_OR_DOWNGRADE` | A seeded stream is enough for arm-independent coupling; the lattice law exists to make the closed R01/R02 objects auditable. |
| Physical factual-label suffix replay at every role origin for `J_base` reuse | `REMOVE_OR_DOWNGRADE` | Belongs to the R01/R02 Q-entry objects, not to learning curves. |
| Ordered-28 quantities, intact-vs-shadow V rows, between-arm action-TV sidecar (626,688 raw rows per checkpoint per seed), parameter-distance trace, kappa panel | `REMOVE_OR_DOWNGRADE` | Diagnostics that cannot change a B decision; publish curves, contact, competence, reassociation delta. |
| Uninterrupted-vs-resume byte equality at six checkpoints | `REMOVE_OR_DOWNGRADE` | Checkpoint save/load for evaluation is needed; bit-exact resume is not (run uninterrupted). |
| Create-once seed-local transactions, `.incomplete` quarantine, per-stage process-tree telemetry | `ENGINEERING_INTEGRITY`, downgrade | Manifest, code SHA, and a resource ledger (peak RSS, wall) suffice for B. |
| Fresh 4 GiB admission per invocation | `ENGINEERING_INTEGRITY` | Cheap; keep. |
| Raw-value classifier fixture must score exactly `1/2` | `ENGINEERING_INTEGRITY` | Cheap leakage check; keep. |
| 256 episodes/cell, 98 cells/seed | `ENGINEERING_INTEGRITY` | Fine if the native host is fast; 64/cell is acceptable for a first named run. |

### recommended_disposition

`CONTINUE`

### disposition_scope

`FRRIE-B01-PHY-EDGE-MATCHED-CURVES-20260901`, three initial seeds, executed through a stripped
chain. R01, R02, and the 909/916-row constructions stay closed or deferred as recorded.

### smallest_next_object

Two named B runs, in order:

- **B01-smoke (1 seed, A/RECON-plus).** Seed `001`, 128 updates, checkpoints `{0,32,64,128}`,
  evaluation on `{9,15}` INTACT only, 32 episodes/cell, both arms. Purpose: prove the loop end to
  end, record wall time and RSS, observe whether `EDGE_FLEX` clears `UNIFORM_LEGAL` and whether
  contact occurs by update 128. No polarity.
- **B01 (3 seeds).** As frozen scientifically: seeds `001–003`, 512 updates, 64 episodes/update in
  `(9,15) x 32` order, checkpoints `{0,32,64,128,256,512}`, evaluation at every checkpoint on
  rosters `{6,9,15,21} x {INTACT, SEMANTIC_COLUMN_ROTATE} x {PHY_TRUST, EDGE_FLEX}` with 64
  episodes/cell (256 if the smoke says it is cheap), plus one `UNIFORM_LEGAL` cell at `N=9,15`.
  Report per seed: the twelve held-out return curves, contact update `kappa_s`, competence pass/fail
  (`e_512 >= 0.08`), reassociation delta per checkpoint, wall time, peak RSS. Descriptive 3-seed
  mean and range against the card's own `0.04` task-scale screen; no interval claim. Cost estimate
  from the milestone's measured collector rate (~847 slots/s at width 32): `2,670,592` slots per
  arm-seed is about 53 min, so six arm-seeds are about 5 h serial or 1.5 h on four workers, before
  evaluation.

### contrary_observation

`EDGE_FLEX` and `PHY_TRUST` byte-identical through update 512 in all three seeds (no contact). That
makes the package comparison vacuous on this host and budget, and the correct move is to change
the host or the optimizer exposure, not to add seeds.

### claim_ceiling_and_non_goals

Ceiling: "On `RIDGEGATE-2Z/RSCF` at 512 updates and three seeds, the tight box showed / did not
show a held-out native-return advantage over the containing box, which did / did not survive
reassociation." Cannot support: relational semantics as a mechanism, arbitrary-`N` transfer,
within-episode churn, stable superiority, UAV, safety.

### literature_support_and_gap

- `DIRECT` — P16 (HATRPO, ICLR 2022), `docs/new-libs/corpus/papers/P16/claims.jsonl` P16-CL001,
  Prop. 1: a constructed cooperative game where the best shared-parameter policy is exponentially
  worse than the unrestricted optimum. Supports that expressivity restrictions can cost; it bounds
  sharing itself, and both FRRIE arms are shared, so it does not speak to the `beta` box.
- `DIRECT` — P12 Thm 3.7, P14 Thm 6.3, P21 Thm 12 (`docs/new-libs/corpus/papers/{P12,P14,P21}/`):
  finite-`N` cooperative value approaches the mean-field/graphon value at `O(N^-1/2)` under stated
  assumptions. Supports `N`-independent interfaces as a concept; not a learned-policy held-out-`N`
  guarantee. The corpus index itself corrects an earlier `O(N^-1)` conflation.
- `DIRECT` — MARL-0078 (MARC, AAAI-25, `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0078.json`):
  a spatial-predicate relational abstraction with R-GCN improves sample efficiency (3 seeds) and
  transfers from 4 to 3 and 5 agents; the strictly-more-informative full-grid ablation reaches only
  46.9% at 8e6 steps. This is the closest local analogue of "the containing package loses at finite
  budget", but it is neither budget-matched nor backbone-identical and has no same-information
  non-relational control.
- `DIRECT` — MARL-0104 (ADAPT, AAAI-26, `json/MARL-0104.json`): zero-shot 3m→5m and 5m→7m on SMAC
  and MPE up to 20 agents with an attention set encoder, 5 seeds. Supports that structural
  generalization across `N` is achievable; no matched tight-versus-wide comparison.
- `DIRECT` (recall-verified) — MARL-0571 (equivariant policies, 10 seeds), MARL-0042 (partial
  symmetry), MARL-0622 (HyperMARL): equivariance and agent-conditioned sharing as sample-efficiency
  inductive biases.
- `CURATOR_OR_PROJECT_INFERENCE` — P19-CL007: hold discount/visitation/update-count conventions
  fixed in optimizer comparisons; relevant to FRRIE's matched-work design but not the source's
  conclusion.
- Gap: no local source compares a tight projection box against a strictly containing one at
  matched work with held-out `N`. `REVIEWER_INFERENCE`: the literature prior is that relational
  inductive bias wins at small budgets; a null here would be the more surprising and informative
  result.

---

## 2. VNFC — variable-N fleet churn

### scientific_motivation

Recovery after an unannounced within-episode agent loss is the operational case for variable-`N`
policies: fleets do not shrink between episodes, they shrink mid-mission. The presentation-safety
requirement matters because a shared set policy whose physical command depends on the arbitrary
row order of its input is not a function of physical state, and a return measured under one
serialization is uninterpretable under another. Both halves, learn recovery and be a function of
physical state, are real.

### mechanism_prediction

A presentation-safe shared MAPR-4 policy trained on `N={3,5}` with unshaped
`J_ext = 0.5 R_fail_60 + 0.5 U_total` learns to reassign the lost executor's role, and the recovery
signal transfers directionally to untouched `N=7`. The mechanism is that the four-token physical
action grammar plus a roster-size-agnostic encoder (order-independent mean/max pooling, `O(4N)`)
lets the same parameters express reassignment at any `N`.

### strongest_alternative

1. `DIRECT-SET-AR` (strictly containing, same information) learns recovery at least as well; any
   MAPR edge is finite-budget inductive bias only.
2. `BCRH-PERSIST` (competent bounded receding-horizon controller, up to 1,961 legal commands at
   `N=7`) beats both learners, the UCOPE-style outcome, which would say the host is solved by a
   rule and the learning question is not yet posed. The R01 intake names this itself as the
   strongest alternative.
3. `REVIEWER_INFERENCE` from the lineage: the earlier VNFC-B1 host was "nearly myopic" and a greedy
   reward-complete rule beat the learned packages; R09 failed 277/1024 consistent-relabel checks.
   The BPCR host may again reward hand-structured action construction over learning.

### current_evidence

- **Direct observations.** No valid return result for BPCR R01 or R02. R09 (C-class, 16 replicates)
  is consumed as `EXACT_PACKAGE_INVALID_UNDER_CONSISTENT_RELABEL_CONTROL`; its return coordinates
  are descriptive only. The only R01 fact is the source-only `N=5/reverse` witness: aligned
  differences of `2.22e-16`, `1.39e-16`, `5.55e-17` flip the decoder between physical agent and
  null. It is a synthetic parameter fixture found by search, not a trained checkpoint.
- **Engineering readiness.** The R09 lineage has a complete learner, native C++ host, and evaluator
  that already ran. The R01 B runner `scripts/run_vnfc_bpcr_b_explore.py` (2,303 lines, about 350
  of them science) is executable for the fixed 8-update DEBUG and passes 102 non-result tests; the
  PRIMARY seeds exist as constants but have no CLI path. R02 has zero code
  (`implementation_started=false`). Sizes: R09 about 2,600 scientific versus 1,100 scaffolding
  lines; `_b_explore` about 400 versus 3,000 (telemetry and prebuilt-loader). VNFC is the only one
  of the five coupled into shared `envs/native/production_backend.py`.
- **Invalid/quarantined.** The R01 DEBUG attempt (non-consuming, in an isolated worktree).
- **Inference.** `REVIEWER_INFERENCE`: the witness proves reachability of a reduction-order
  near-tie; it says nothing about frequency in trained policies. In a generic float network with
  continuous inputs, two candidate logits within `1e-16` is a measure-zero event unless the host
  produces byte-identical agent rows, which the A0 `DUPLICATE_TIE` primitive shows it can. Exact
  ties need a tie rule anyway; the R01 design already had one (opaque rank).

### main_scientific_difficulty

Deciding what "same physical state → same physical action" must mean for a B claim. Three levels:
(a) distributional, the policy's action law over physical candidates is presentation-invariant; (b)
pathwise-deterministic, the argmax is invariant; (c) pathwise-stochastic, a fixed RNG word maps to
the same physical candidate. The return estimand needs (a). Canonical ordering gives (b), and gives
(c) once the CDF is built in canonical order. None of the three requires a scalar binary64 kernel,
exact 52-bit apportionment, or hex-constant AdamW. The packet's worry that opaque rank "becomes a
constitutive channel" is answered by exchangeability: rank is a random permutation independent of
features, so conditioning on it changes pathwise coupling but not the policy's law.
Rank-relabel invariance is not a property the claim needs.

### main_engineering_difficulty

Implementing canonical-sort-by-opaque-rank before the first tensor operation in the existing
MAPR/DIRECT forward, with deterministic CPU kernels and one thread, and confirming it with a small
randomized conformance test. That is a day of work, not a 304-row panel.

### overformalization_audit

| Requirement | Class | Reason |
| --- | --- | --- |
| Canonical computational representative (sort by opaque rank before any numeric op) | `SCIENTIFICALLY_NECESSARY` | The one change that makes physical action a function of physical state. |
| Exchangeable, feature-independent opaque rank transported with the entity; never a learner feature | `SCIENTIFICALLY_NECESSARY` | Legitimate tie-break that cannot leak identity. |
| Same law for collection, forced log-prob, entropy, gradient | `ENGINEERING_INTEGRITY` | Follows automatically once inputs are canonical. |
| Scalar batch-width-one binary64 reference, separately rounded affine/activation primitives, hex AdamW constants, no-FMA, denormal preservation | `REMOVE_OR_DOWNGRADE` | Cross-batch ULP drift affects all arms equally and does not touch presentation invariance. |
| Exact 52-bit lattice apportionment, uint64 midpoint CDF, boundary/nextafter probes at every edge | `REMOVE_OR_DOWNGRADE` | A standard categorical sampler over canonically ordered candidates with one uniform is presentation-safe by construction. |
| 288-row descriptor product × fixtures × arms, 74 optimizer steps, 12 primitive rows | `REMOVE_OR_DOWNGRADE` | Replace with about 50 rows: the `N=5` witness, `DUPLICATE_TIE`, `FIXED_PREFIX_NULL`, and 20 random states × 4 presentations × 2 arms. |
| Zero-residual MAPR-in-DIRECT containment check at initialization | `ENGINEERING_INTEGRITY` | One assertion; keep. |
| Content-bound DLL/dependency bytes in the manifest | `REMOVE_OR_DOWNGRADE` | Record versions; byte-binding cannot change a B decision. |
| Address-resolved predicate reporting replacing the R01 combined `structural` Boolean | `ENGINEERING_INTEGRITY` | Cheap observability fix; keep. |
| Load-only native resolver that hashes `cl.exe` candidates and refuses to invoke a compiler | `REMOVE_OR_DOWNGRADE` | Anti-tamper posture with no estimand value. |
| Fresh 4 GiB admission, create-once quarantine | `ENGINEERING_INTEGRITY` | Keep. |

### recommended_disposition

`RECAST`

### disposition_scope

The R02 finite physical-action law `VNFC-R02-ORC-B64-Q52-U64-V1` and the 304-row A0 object. The
direction, the BPCR host, the MAPR / DIRECT-SET-AR / BCRH-PERSIST comparison, and the
`N={3,5} → 7` question continue unchanged.

State at review close (2026-09-01 afternoon): the law is now implemented in
`experiments/candidates/variable_n_fleet_churn_r02/` (13 modules, about 4,700 lines, including
`autodiff.py`, `kernel_gate.py`, `model.py`, and `probability.py`) plus
`scripts/run_vnfc_bpcr_r02_a0.py` (656 lines), with a byte manifest binding the reference kernel
and about 940 dependency sources, and a source-owned scalar reverse-mode graph whose closure the
freeze document now records as complete. `temp/vnfc-r02-a0` does not exist, so A0 has not run.
None of this code touches the learner's exposure or the MAPR / DIRECT / BCRH comparison. The
recast keeps the canonical-sort rule, the deterministic single-thread kernels, and whatever
conformance rows the 50-row test needs, and demotes the rest from gate to record.

### smallest_next_object

- **Recast law (docs, one page).** Canonical sort by opaque rank; deterministic CPU kernels, one
  thread, the dtype the existing code uses; exact-tie by ascending rank, null last; categorical
  sampling over canonical candidate order with one uniform per token; the same forward in
  collection and replay. No scalar reference, no lattice, no hex constants.
- **Conformance test (A/RECON, unit-test scale).** About 50 rows: the registered `N=5/reverse`
  witness, `DUPLICATE_TIE`, `FIXED_PREFIX_NULL`, and 20 random `(N in {3,5,7}, zone, state)` draws
  under `{canonical, reverse, cyclic, random}` presentations for MAPR and zero-residual DIRECT.
  Assert bitwise-equal logits, probabilities, deterministic command, sampled command under a common
  uniform, and one-step gradient/parameter equality. Pass/fail; minutes to run.
- **R02 DEBUG → B1–B3 (B/EXPLORE).** Reuse the R01 exposure law with the reserved R02 seeds: one
  8-update DEBUG, then three 64-update seeds (per seed 6,144 episodes, 36,864 transitions, 6,144
  PPO steps; 16 balanced episodes per update, 4 epochs × 4 minibatches). Arms MAPR-4,
  DIRECT-SET-AR, BCRH-PERSIST; train `N={3,5}`; evaluate updates 0 and 64 on eight fresh worlds in
  each of the six `(N, failed-zone)` cells and BCRH once on 16 `N=7` worlds (208 rollouts/seed).
  Report per seed: `R_fail_60` and `U_total` at `N={3,5,7}` for both checkpoints, MAPR
  final−initial, MAPR−DIRECT and MAPR−BCRH at `N=7`, plus the DIRECT residual-activity flag. The
  runner already exists; it needs the canonical-sort law swapped in and a PRIMARY CLI path, not a
  new codebase.

### contrary_observation

A trained MAPR checkpoint whose held-out return differs materially between two presentations of
the same evaluation tapes after canonical sort is in place. That would mean presentation enters
through a channel other than input order and would justify the deeper audit. Under canonical sort
this is impossible by construction, so its observation would indicate an implementation defect,
not a law gap.

### claim_ceiling_and_non_goals

Ceiling: "On the two-zone one-loss host, with `N={3,5}` training and three seeds, MAPR did / did
not show directional post-loss recovery on `N=7` relative to DIRECT and BCRH-PERSIST." Cannot
support: general permutation invariance, repeated churn, join/rejoin, arbitrary `N`, UAV, safety.

### literature_support_and_gap

- `DIRECT` — MARL-0005 (CIA, AAAI-23, `json/MARL-0005.json`): randomly shuffling the agent-Q input
  order to the QMIX mixer every epoch leaves performance and credit distributions essentially
  unchanged; trained mixers are insensitive to agent identity. Supports the reviewer's inference
  that presentation matters at the return level only through ties. The paper then adds learnable
  identity vectors deliberately, the opposite of VNFC's rule that rank must not become a feature.
- `DIRECT` — MARL-0104 (ADAPT, `json/MARL-0104.json`): zero-shot transfer across team sizes with a
  permutation-equivariant attention set encoder, 5 seeds; no within-episode agent loss. Its
  per-object GRU hidden state presupposes stable object-slot correspondence across timesteps, an
  unstated ordering assumption, which is exactly the presentation problem VNFC is formalizing.
- `DIRECT` (recall-verified) — VS-0004 (STAIRS-Former, token dropout for varying populations),
  MARL-0409 (CAMA, dynamic team composition), MARL-0561 (zero-shot to unseen team compositions, 5
  seeds), MARL-0509 (performance maintained when `N` varies without retraining).
- `DIRECT` — P08, P12, P14 population-aggregation interfaces; P16 Prop. 1 on sharing cost.
- `CURATOR_OR_PROJECT_INFERENCE` — P10-CL006 (one frozen controller evaluated across `N`); P12-CL006
  (graphon-index roles); neither is a source conclusion.
- Gap: neither library contains within-episode agent loss or fault tolerance (zero catalog hits for
  "fault tolerant", "permutation invariant", "agent failure" beyond false positives), and nothing on
  finite-precision presentation ties. `UNKNOWN` globally. `REVIEWER_INFERENCE`: the field treats
  permutation-equivariant architectures as presentation-safe by construction and does not run
  bitwise conformance panels; VNFC's finite-precision concern is real but is addressed by canonical
  ordering, not by exact arithmetic laws.

---

## 3. CBSC — capability-bound semantic currentness

### scientific_motivation

Agents acting on public histories must track which content is current for whom, and whether the
carrier can still execute. The exact factorial established that this matters for one-shot protocol
value (contrasts of `5/8`), and also that an unrestricted RAW controller matches CBSC row for row,
so there is no information or representation necessity. What remains is a genuine, general
learning question: does a typed currentness register accelerate a recurrent learner over the raw
token stream at finite budget, and if so, is the gain semantic (dies under derangement) or generic
(any register helps)? That is a small but clean inductive-bias question with a good control
structure.

### mechanism_prediction

A relation-aligned 4-byte adapter exposes "latest OWNER/epoch for the target receiver" as a directly
readable channel, so a GRU actor-critic needs fewer updates to combine it with body, receiver, and
capability than to learn the same function from 136 raw channels over 152 transitions with delayed
settlement. Prediction: STRUCT reaches RAW-competence earlier (updates 12–24 rather than 48) and
holds a return edge at 48; DERANGED does not; PI-GRU absorbs the OPEN path but not the GATED
residual.

### strongest_alternative

1. **Budget-limited null / RAW incompetent.** 48 PPO updates (384 episodes, 768 Adam steps) is a
   very small budget for a 121,349-parameter GRU on a 24-opportunity POMDP with delayed settlement.
   `REVIEWER_INFERENCE`: the most likely outcome is that RAW fails the mechanical competence gate,
   yielding `NO_B2_INTERPRETATION_BLOCKED` with no learning read at all, a repeat of the UCOPE
   pattern.
2. **Generic conditioning.** Any extra low-entropy channel helps early PPO; DERANGED matches STRUCT.
3. **Predictive-index sufficiency.** PI-GRU equals STRUCT because the gated capability edge is rare
   (binding changes with probability 0.25, GATED access 0.5). The Innovator intake's own cheapest
   contrary observation is this pattern at update 12.

### current_evidence

- **Direct observations.** Exact factorial: `VALID_NARROW_PROTOCOL_VALUE`, 36,864 rows, 15 audits,
  RAW equality. LR01: valid `UNRESOLVED`, worst-block `-0.0751` (STRUCT−RAW), `-0.0751`
  (STRUCT−SHAM), `-0.1389` (gated−open), maxima `+0.116`, `+0.092`, `+0.135`; 0/24 blocks pass.
  Both consumed.
- **Engineering readiness.** Static audit: 22,772 lines, about 5,200 scientific versus 17,500
  scaffolding, roughly 16,000 of them untracked. Host, four adapters, GRU actor-critic,
  `RecurrentPPOTrainer`, the 384-episode/48-update B1 engine with checkpoints at `0/12/24/48`, the
  held-out evaluator, checkpoint/resume, and a 12-slot supervisor all exist and are wired. The CLI
  refuses by literal constant: `b1_metrics_artifact.py` sets `FORMAL_ANALYSIS_BOUND = False` and
  `READINESS_DISPOSITION = "REPAIR_REQUIRED"`, and `run_b1_start` raises before executing; a test
  confirms that flipping the constant authorizes start. No native code on the path.
- **Invalid/quarantined.** None for B01 (B0 is instrumentation).
- **Inference.** `REVIEWER_INFERENCE`: LR01's sign-changing blocks are the expected signature of a
  small, budget-dependent inductive-bias effect, which an online learning curve can show and a
  worst-block finite-panel rule cannot.

### main_scientific_difficulty

Reading a three-seed, 48-update result. STRUCT-minus-RAW differences at this budget will be
dominated by seed and rollout variance; with the DERANGED and PI controls the design can still
localize a signal, but only if RAW is competent. The host is fully stipulated (event probabilities
and payoffs chosen so currentness matters), so even a clean positive is a host-bound statement
about feature engineering for recurrent PPO. That is acceptable at B, and the claim ceiling says
so.

### main_engineering_difficulty

Finish the E2E assembly to the point where 12 arm×seed runs execute and publish per-tape returns
and per-decision actions. Nothing else is required.

### overformalization_audit

| Requirement | Class | Reason |
| --- | --- | --- |
| Identical primitive histories, masks, init outside adapter, parameters, BPTT, PPO exposure across arms within a seed | `SCIENTIFICALLY_NECESSARY` | Defines the paired four-arm estimand. |
| DERANGED and PI-GRU controls with adapter-work parity | `SCIENTIFICALLY_NECESSARY` | The only way to separate semantic from generic gain. |
| Mechanical RAW-competence gate (beat ALWAYS_REFRESH/ALWAYS_SAFE; ≥80% SERVE on easy OPEN cases) | `SCIENTIFICALLY_NECESSARY` | Prevents comparator incompetence being read as STRUCT signal. |
| Held-out stochastic and fixed motif tapes; adaptation-free evaluation | `SCIENTIFICALLY_NECESSARY` | Standard held-out discipline. |
| Literal binding of token codes, preamble, RAW FIFO, adapter timing, PRF, init, GRU equations | `ENGINEERING_INTEGRITY` | Fixes comparator identity; reasonable once, but a spec, not a launch gate. |
| Lossless 15-table publication of every transition, decision, logit bit pattern, optimizer step | `REMOVE_OR_DOWNGRADE` | Per-tape returns, per-decision actions and truth, and per-step losses suffice for a B read. |
| Metrics-only rule (engineering may compute no mean or AUC; all derived fields literal null) | `REMOVE_OR_DOWNGRADE` | Delegating arithmetic to a separate node adds latency without protecting the estimand; compute descriptives and label them non-decisional. |
| Independent consumer recomputation of `compute_b1_mechanical` from bound raw evidence (the open HIGH) | `REMOVE_OR_DOWNGRADE` | Tamper resistance for a single-owner research repo; not decision-relevant at B. |
| Result-blind full-formal canonical payload capacity projection | `REMOVE_OR_DOWNGRADE` | The run is small (about 58k transitions per arm-seed); a measured wall/RSS from B0 is enough. |
| Fresh 4 GiB admission, create-once artifacts, fixed seeds `21101/21121/21143` | `ENGINEERING_INTEGRITY` | Keep. |

### recommended_disposition

`CONTINUE`

### disposition_scope

`CBSC-OMRC-B1-THREE-SEED-SCOUT` on `CBSC-DYNAMIC-CACHE-2R-1C-v1`; the exact factorial and LR01 stay
consumed as recorded.

### smallest_next_object

B1 as frozen scientifically (four arms × seeds `21101/21121/21143`, 384 training episodes, 48
updates, checkpoints `0/12/24/48`, 64 held-out episodes per checkpoint) with two process changes:
(1) launch without the consumer-recompute and capacity-projection gates, publishing per-tape
returns, per-decision actions and truth, and per-step losses; (2) pre-declare a named follow-up
`B1b` at 4× updates (192 updates, same seeds, same everything) to run automatically if any RAW seed
fails the competence gate, labeled outcome-informed. Report: 12 curves, RAW competence per seed,
STRUCT−RAW, STRUCT−DERANGED, STRUCT−PI per checkpoint, descriptive means and ranges. The B1 contract
already caps wall at 120 min; the run should take minutes per arm-seed.

### contrary_observation

RAW competent at update 48 with STRUCT, DERANGED, and PI all within seed range of RAW on both tape
families. That is `GENERIC_FACTORIZATION_OR_CONDITIONING` or `NULL_AT_THIS_BUDGET` and, combined
with the exact factorial's RAW equality and LR01's mixed blocks, would justify `STOP_AFTER_B1` and a
direction-level close at this host.

### claim_ceiling_and_non_goals

Ceiling: "On this host, with this recurrent-PPO package, at 48 (or 192) updates and three seeds,
the typed currentness adapter did / did not produce an earlier or larger held-out return than RAW,
and the gain did / did not survive derangement." Cannot support: representation necessity, natural
frequency of currentness faults, communication or credit value, security, variable population,
UAV, safety.

### literature_support_and_gap

- `DIRECT` — MARL-0066 (CoDe, AAAI-25, `json/MARL-0066.json`): messages carry send timestamps and
  a timeliness alignment down-weights them by age; the ablation without timeliness drops from 62.1
  to 58.5 on `1o_10b_vs_1r`, 5 seeds. The nearest local neighbour of "currentness"; it has no
  epoch or version counter and no receiver-content or capability semantics.
- `DIRECT` — MARL-0006 (DACOM, `json/MARL-0006.json`): delay-aware waiting thresholds; messages
  carry no age; gains only in a 10–70% delay band.
- `DIRECT` (recall-verified) — MARL-0656 (individual stochastic observation delays, NeurIPS 2025).
- `DIRECT` — B03 §8.3 (`docs/new-libs/corpus/papers/B03/claims.jsonl` B03-CL006): instantaneous,
  k-step delayed, costly, and local communication as Dec-POMDP planning models; the curator limit
  notes a fixed delay is not a currentness state.
- `DIRECT` — P15 (IMAC) P15-CL004: both over- and under-compression hurt; no staleness model.
- `DIRECT` — MARL-0034 (IDEAL, `json/MARL-0034.json`): identity-aware, receiver-specific
  communication via order-independent ego-network coloring; each team size trained separately.
- `CURATOR_OR_PROJECT_INFERENCE` — B03-CL008 (communication cost as CBSC analogue).
- Gap: no local source tests a typed currentness register against a same-information raw recurrent
  learner with a deranged control; CoDe's timeliness ablation is the closest and is not a
  same-information design. `UNKNOWN` globally.

---

## 4. SCDMP — semigroup-consistent duration-model policy

### scientific_motivation

Physical multi-agent systems have non-commuting events (hand off a hook, then rotate formation,
versus the reverse) whose order leaves latent state that is invisible in the public observation but
changes which next action is safe. Whether a policy must track event order rather than a
memoryless summary is a real question about what state representation MARL controllers need in
physical tasks. The current B01 asks the prerequisite: does latent order change native action value
at all, across foundations, states, and durations.

### mechanism_prediction

After `HOOK_HANDOFF → FORMATION_ROTATE` versus the reverse, the latent cable assignment `(p,q)`
differs behind byte-identical public states. A first hold matched to the true assignment keeps the
load balanced; the swapped hold overloads a cable. Prediction: the development-selected `A_HR` and
`A_RH` differ, matched beats swapped on held-out tapes, and matched beats the strongest graph-blind
common action, in both `k` and both foundations.

### strongest_alternative

Public state plus `k` already determine all useful first-action variation; apparent order value is
development-selector noise, generic action quality, or downstream foundation recovery. The B01
design answers this with disjoint development and held-out tapes and the common-action arm.
`REVIEWER_INFERENCE`: the `.3` panel already makes this null unlikely at one state, since the
mismatched action scored exactly `0` on every tape (never docks) while matched scored `0.081` and
common `0.045`, but generality across states is open.

### current_evidence

- **Direct observations.** FCEOV `.3` (valid, consumed): competent foundation (120/120 docked); 562
  tapes; all three gap contrasts positive on every tape; cell means RH/A_RH `0.0810`, RH/COMMON
  `0.0452`, RH/A_HR `0`; HR/A_HR `0.0815`, HR/COMMON `0.0448`, HR/A_RH `0`. Frozen disposition
  `NOT_ESTABLISHED_AT_FROZEN_RESOLUTION` because the pre-registered one-sided Bernoulli-KL bounds
  over the full `[-363/364, 363/364]` support required integer sums of `21,046/21,046/42,091` and
  observed `16,665/16,565/14,809` (`p_IUT = 0.69`, `L_theta = -0.033`).
- **Engineering readiness.** Static audit: 8,879 lines, about 4,800 scientific versus 4,060
  scaffolding, the most balanced of the five. Native simulator (`mf_rs_native.cpp`, 18-action table
  asserted), foundation actor-critic, hand-written `ExactAdamW` PPO, the 160-update loop with
  9-point curves, competence gate, source scans, 8-tape development, 16-tape held-out, and a CLI
  `--run-01` all exist; 514 tests passed, reviewer `CLEAN`, commit `92a3b7c2`. RUN-01 executed once
  and wrote `foundation-competence-gate.json`, `development-action-map.json`, and
  `heldout-analysis.json` under `temp/scdmp-b01/RUN-01/` before a Windows atomic-file enumeration
  race in the telemetry quarantined it unread. The design uses two foundation seeds (`1709`,
  `2903`), not three. `docs/research/RESEARCH_MAP.md` still points at the old FCEOV directory
  rather than `multifoundation_reachable_order_value/`.
- **Update at review close.** The Innovator intake of 2026-09-01
  (`SCDMP_B01_FRESH_NAMED_ATTEMPT_INNOVATOR_INTAKE_20260901.md`) decided
  `FRESH_NAMED_ATTEMPT_VALID` and bound `SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01` /
  `...-ATTEMPT-01` with a fresh master, one `q_by_cell` draw, and zero access to the quarantined
  root. A fresh readiness assessment `A-R2` (`temp/scdmp-b01/A-R2/assessment.json`, status
  `PERFORMANCE_OBSERVATION_COMPLETE`, readiness `REVIEW_REQUIRED`) projects a conservative 350 s
  total against the 1,800 s cap (2× safety factor plus 60 s overhead), 209 MB peak process-tree RSS
  against 2 GiB, 126 MB durable against 256 MiB, 322 checkpoint files, and no measurement
  incidents. The replacement run has not been launched.
- **Invalid/quarantined.** RUN-01 (`telemetry_measurement_failed`), unread, non-consuming. Three
  earlier UCOPE roots died the same way (RSS-cap refusal, validator bug, filesystem telemetry race),
  which says the telemetry layer, not the science, is the portfolio's most frequent failure point.
- **Inference.** `REVIEWER_INFERENCE`: the `.3` "nonpass" is an artifact of an inference rule
  designed for worst-case tape laws; a sign test on 562/562 positive tapes would give `p = 2^-562`.
  Under the current empirical standard, `.3` is the strongest preliminary B signal in the
  portfolio. The consumed C object is not reinterpreted; the B family it motivated is the right
  container for that reading.

### main_scientific_difficulty

Two layers. (1) Whether order value generalizes beyond one state: B01 answers with six reachable
states, two foundations, two `k`. (2) The question that actually matters for the direction's name,
whether a *policy* can recognize or track the order from public consequences and exploit it, is
not tested by B01, whose graph label lives only in the offline scheduler. The direction should
state plainly that B01 is an oracle-value scout and that the learner question (order-visible or
history-tracking policy versus the erased foundation) is the next object if B01 is positive.

### main_engineering_difficulty

None. The reported blocker ("retry must reuse the master, but the old master may not be read")
was a rule collision, not an engineering gap: B/EXPLORE has no consumption state (spec §6.1),
RUN-01's outcome was never read, and a fresh named attempt with a fresh master is outcome-blind by
construction. The repository's Innovator reached the same decision on 2026-09-01. What remains is
turning the `A-R2` receipt's `REVIEW_REQUIRED` into a launch, which is a signature.

### overformalization_audit

| Requirement | Class | Reason |
| --- | --- | --- |
| Byte-identical actor-visible public state after HR/RH + `LEVEL_RELEASE`; latent `p,q` never visible to actor/critic/selector | `SCIENTIFICALLY_NECESSARY` | This *is* the intervention; equality is the identification condition. |
| Disjoint development and held-out tape namespaces; atomic action-map freeze before held-out generation | `SCIENTIFICALLY_NECESSARY` | Kills the selector-overfit null. |
| Common-action arm and swapped arm on the same tapes | `SCIENTIFICALLY_NECESSARY` | The two containing nulls. |
| Foundation competence gate (≥24/32 per cell, ≥109/128 pooled) | `SCIENTIFICALLY_NECESSARY` | Prevents reading an incompetent foundation. |
| Sealed `q_by_cell` PRF draw from four admissible vectors; identity `p_pre` | `ENGINEERING_INTEGRITY` | Reasonable design balance; keep, but its invalidity clauses are heavier than needed. |
| Retry must reuse RUN-01 master; quarantine forbids reading it | `REMOVE_OR_DOWNGRADE` | Contradictory for a B object; fresh named attempt with fresh master. Resolved this way by the Innovator intake of 2026-09-01. |
| Missing peak-RSS/scratch/durable telemetry invalidates the attempt | `REMOVE_OR_DOWNGRADE` | Telemetry does not protect the estimand; record if available, never discard returns for it. |
| `PERFORMANCE_READY` receipt requiring a CM `CLEAN` review JSON before `--run-01` | `REMOVE_OR_DOWNGRADE` | A 30-minute B run does not need a separate readiness object; `A-R2` now exists with a 350 s projection and should not wait on a review round. |
| 30-min wall / 2 GiB RSS ceilings | `ENGINEERING_INTEGRITY` | Fine as budgets; not invalidators. |
| Full/public twin-conformance records, `p,q` audit rows | `ENGINEERING_INTEGRITY` | Keep as evidence of the equality boundary. |
| `.3` full-support KL/IUT inference (historical) | `REMOVE_OR_DOWNGRADE` | For future B runs report raw gaps, per-tape sign counts, and descriptive ranges. |

### recommended_disposition

`CONTINUE`

### disposition_scope

`SCDMP-MF-RS-MK-ORDER-VALUE-B01`, executed as the fresh named attempt the Innovator has now bound
(`SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01`, attempt `-ATTEMPT-01`) with a fresh
master; `.3` stays consumed at its frozen meaning.

### smallest_next_object

- **RUN-01-REPLACEMENT-01.** Exactly the frozen card: seeds `1709, 2903`; 160 updates × 12 episodes; 9-point
  learning curves (32 missions each); 128-mission competence; six first-legal-boundary state twins
  at ticks `64/160/256` for `k in {7,13}`; 18-action development sweep on 8 tapes; 16 held-out
  tapes; matched/swapped/common. At most 9,328 missions, at most 30 min. Report the eight ordered
  branches descriptively; treat telemetry as recorded, not gating.
- **If branch 5 or 8:** before RUN-02A's added seeds, register the learner object the direction is
  named for, `RUN-L1`: from each competent foundation checkpoint, fine-tune two policies for 40
  updates at the six states, one receiving the ordered event token (or a last-event register), one
  erased; 3 seeds; compare held-out `U` on the same 16 tapes. That is the first
  "semigroup-consistent policy" evidence.

### contrary_observation

Both foundations produce distinct `A_HR ≠ A_RH` in both `k`, yet held-out matched-minus-swapped and
matched-minus-common are nonpositive in both foundations and both `k` (the card's own contrary
observation). Given `.3`, that would show the one-state result was state-specific and would move
the direction to `PARK`.

### claim_ceiling_and_non_goals

Ceiling: "On `QUAD-UAV-PALLET-GANTRY-24P5M-v1`, across two competent foundations, six reachable
states and `k in {7,13}`, matched first actions did / did not show a repeatable held-out return
advantage over swapped and common." Cannot support: learned order recognition, duration policy,
semigroup composition, arbitrary `k`, transfer, safety.

### literature_support_and_gap

- `DIRECT` — MARL-0032 (MATEA, AAAI-24, `json/MARL-0032.json`): LTL specifications compiled to
  reward machines encode event order as the objective and decompose per agent; tabular
  Q-learning, 5 trials. Supports event order as a first-class temporal object; no counterfactual
  action value under swapped physical order.
- `DIRECT` — MARL-0449 (ACAC, ICML 2025, `json/MARL-0449.json`): MacDec-POMDP with
  environment-determined variable macro-action durations, 5 seeds; event order is encoded
  implicitly and never manipulated.
- `DIRECT` (recall-verified) — MARL-0530 (asynchronous credit assignment) and MARL-0588 (SeqComm,
  explicit decision order, 5 seeds): the nearest neighbours on order among agents.
- `DIRECT` — VS-0002 (VIP, grade B, `json/VS-0002.json`): continuous-time value iteration with
  variable decision gaps, 5 seeds; all agents decide synchronously. VS-0005 (UTE, grade B):
  single-agent uncertainty-aware variable action repetition.
- `DIRECT` — MARL-0553 (HMASD, NeurIPS 2023): the lineage's own baseline, where the skill interval
  `k` is a fixed hyperparameter.
- `DIRECT` — B03 §8.2 macro-actions (B03-CL005); P17 MAVEN episode-persistent latent (P17-CL003).
- External legacy physics references (Sreenath & Kumar RSS 2013 and three others) are not in either
  library and supply broad payload-dynamics provenance only.
- Gap: no local source measures the value to a policy of knowing physical event order.
  `REVIEWER_INFERENCE`: SCDMP's question is closer to latent-state identification from history in a
  POMDP than to options or durations; the right comparator literature is recurrent versus
  memoryless policies under hidden state, which the packet's map does not yet cite.

---

## 5. UCOPE — uncertainty-conditioned observation and paid evidence

### scientific_motivation

Whether an RL agent will pay a real service/time/energy cost for a diagnostic probe when, and only
when, the probe has positive expected value is the finite-budget form of active information
gathering, and it is the piece of UAV autonomy (sense before commit) that fixed-observation MARL
benchmarks do not exercise. The COUNT-versus-RAW representation question is subordinate and the
direction correctly gates it behind competence.

### mechanism_prediction

A competent FLEX learner selects PROBE in the single context where the persistent net acquisition
value is positive (`LINKED x 17/20 x 9/100`, headroom `+0.051`, direct component `-0.020`, unique
margin `0.040`) and commits immediately elsewhere, realizing positive external value on held-out
effective periods.

### strongest_alternative

Common learnability failure: finite AdamW exposure, odd-to-even extrapolation, fold coupling, or
simply that the entire decision lives inside a `0.02–0.05` utility margin that a sampled-return
learner at this budget cannot resolve. The host makes this concrete: eight contexts
(`link x reliability {13/20, 17/20} x probe cost {9/100, 7/50}`), effective-period value
`q(r,k) = 0.95 − (k−center)^2/100` with `R = q − k/100 − k^2/1000`, so adjacent-`k` value gaps are of
order `0.01–0.04`, and the sole positive-probe context has net acquisition value `+0.051`.
`REVIEWER_INFERENCE`: the odd/even audit removes extrapolation as the explanation (zero odd-support
competence too), and the structural certificate shows the *data* supports an exact linear fit
within regret `1/50` in 20/20 policies, so the residual suspects are the host margin and the
exact-oracle competence criterion.

Source check (`REVIEWER_INFERENCE`, from
`experiments/candidates/ucope/competence_first_scout_r01/model.py` and `training.py`): the Bellman
coefficients are Glorot-uniform initialised on a `1 × 5` (tail) or `1 × 7` (root) matrix, so their
initial values are of order 1; the optimizer is AdamW at lr `3e-4` with gradient-norm clipping at
1.0, for 160 tail and 320 root updates at batch 256. Adam moves each coordinate by about lr per
step in the typical regime, so the whole budget can displace a coefficient by roughly 0.05 (tail) to
0.1 (root), against an initial distance from the least-squares solution of order 0.5–1 per
coefficient and a target resolution of 0.01–0.04 between adjacent `k`. That is an exposure
shortfall of about one order of magnitude, before function class, targets, or coordinates enter.
The direction lists finite optimizer exposure first among its alternatives and has never tested
it, because `AUTOMATIC_BUDGET_ENLARGEMENT=false` is applied as if it were a scientific rule.

### current_evidence

- **Direct observations.** R03: 90/90 support failure (min tail visits 715 < 2,048). BELIEF v2:
  0/10 competent (regret 0.021–0.078; tail agreement 0–0.61; descriptive panel-min signed
  specificity `+0.015`). Structural certificate: 17/20 pass tail agreement, 20/20 pass regret. B1:
  3 arms × 3 seeds × 2 folds, 122,880 episodes, 8,640 updates, 0/18 policies competent at any of 72
  checkpoints; closest regret `0.0214` (gate `0.02`); max tail agreement `0.829` (gate `0.95`); MT
  and FT FLEX identical in 5/6 final pairs; BC tail agreement `0` everywhere. Odd/even audit: 0
  odd-competent, 0 odd-near; FT-FLEX:BC dominance `2:3, 2:2, 4:1, 3:2`; MT/FT root distance zero;
  route `MAP_NOT_UNIQUE_NEW_CONVERGENCE_REQUIRED`.
- **Engineering readiness.** Fully executable; B1 ran in 140 s at 455 MB peak; the audit in 18.5
  s. Static audit: 4,639 lines, about 1,420 scientific versus 3,200 scaffolding plus a 1,900-line
  runner. Important detail: the learner is supervised Bellman regression (fitted-Q with AdamW, 320
  root / 160 tail updates) on a fixed behavior population; there is no environment interaction
  during training and no policy-gradient learner in this family. `docs/research/RESEARCH_MAP.md`
  still points at the older `contextual_paid_acquisition_r01`.
- **Invalid/quarantined.** None current; the audit launch was a coordination violation but the
  artifact is validly retained. Three earlier roots (`-01` RSS cap, `-02` validator bug, `-03`
  filesystem telemetry race) were quarantined before `-04` succeeded.
- **Update at review close.** The Convergence intake of 2026-09-01
  (`UCOPE_INVERTIBLE_CONDITIONING_R01_CONVERGENCE_DECISION_INTAKE_20260901.md`) decided `CONTINUE`
  via `UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01`: `FT-XF-BC-RAW` versus
  `FT-XF-BC-WHITENED` (Cholesky whitening of the Bellman basis, `G = XᵀX/n = LLᵀ`, `z_w = L⁻¹z`,
  function-space-identical initialisation `β̃₀ = Lᵀβ₀`), three fresh seeds, two folds, the same
  budget (160/320 updates, batch 256, lr `3e-4`), the same competence gate, and
  `AUTOMATIC_BUDGET_ENLARGEMENT=false`. Positive requires whitened `B_COMPETENT`, raw noncompetent,
  and a stable paired advantage at updates 160 and 320; both arms noncompetent with no stable
  whitened advantage is declared PARK support. The runner
  `scripts/run_ucope_bc_conditioning_discriminator_r01.py` exists and has not run; the contract's
  own projection is about 155 s wall and about 320 MB RSS.
- **Inference.** `REVIEWER_INFERENCE`: four learner families (offline fitted-Q with three target
  schedules and an exact linear certificate), one host family, one outcome. The competence criterion
  (exact oracle root vector in all 8 contexts AND regret ≤ 0.02 AND forced-PROBE tail agreement ≥
  0.95) is a near-exactness bar on a problem whose signal is about 0.04; that design can only fail
  or barely pass. The older CPM-lineage B2 (`CODE_SCIENCE_INDEX.md`) recorded local net
  acquisition support with four seeds on a different host; that is provenance only, but it shows
  the acquisition question is not intrinsically unlearnable.

### main_scientific_difficulty

Separating "the host is too fine-grained for finite-budget learners" from "learners do not acquire
paid information". The current objects cannot separate them because the margin is fixed. A margin
ladder can: if competence and correct acquisition appear at a large margin and vanish as the margin
shrinks, that *is* a finite-budget acquisition result with a measured threshold.

### main_engineering_difficulty

None for the exposure ladder: two constants (learning rate and update counts) under a new object
name. For the margin falsifier, parameterizing the probe-value scale of the host and relaxing the
competence criterion to a relative one. The trainer, evaluator, and gates exist and run in minutes.

### overformalization_audit

| Requirement | Class | Reason |
| --- | --- | --- |
| Competence-first gating of acquisition and COUNT/RAW | `SCIENTIFICALLY_NECESSARY` | Prevents reading incompetence as "no acquisition value". |
| Group-disjoint folds, held-out `K_eval` | `SCIENTIFICALLY_NECESSARY` | Standard leakage control. |
| Exact-oracle root-vector match + regret ≤ 1/50 + tail agreement ≥ 19/20 as competence | `REMOVE_OR_DOWNGRADE` | Replace with a relative criterion (e.g., ≥ 80% of the oracle-minus-immediate-commit gap; PROBE in the target context and in at most one of seven others). |
| Create-once sealed objects, hash chains, 75-row journals, deep checkpoint binding, four tamper reproductions | `REMOVE_OR_DOWNGRADE` | Integrity theatre for a 140-second run; manifest, SHA, and ledger. |
| Exact dyadic-rational arithmetic in the structural certificate | `ENGINEERING_INTEGRITY` (historical) | Appropriate for that exact object; not a template for learners. |
| Fresh 4 GiB admission | `ENGINEERING_INTEGRITY` | Keep. |
| "Do not rerun the audit"; "new Convergence packet required before any recommendation" | `REMOVE_OR_DOWNGRADE` | The audit's reading is unambiguous at B: nobody learns even on training support. |
| `AUTOMATIC_BUDGET_ENLARGEMENT=false` applied as a scientific rule | `REMOVE_OR_DOWNGRADE` | Right as a ban on silently enlarging a running object; wrong as a ban on a named exposure-ladder object, which tests the direction's own first-listed alternative and has never run. |

### recommended_disposition

`RECAST`

### disposition_scope

The competence-first B family's budget rule, host margin, and competence criterion (successor to
`UCOPE-B-EXPLORE-MT-XF-BC-COMPETENCE-FIRST-SCOUT-R01`). The paid-acquisition question stays; the
consumed objects stay consumed. If the exposure ladder, the whitening discriminator, and the recast
falsifier all fail, `PARK`.

On the Convergence's whitening discriminator (`REVIEWER_INFERENCE`): it is a clean single-axis test
of AdamW's dependence on coordinates, it preserves the function class and the initial function, and
it costs minutes, so it should run. Three facts bound what it can say. (1) Its ceiling is the
least-squares fit of the same 12-coefficient basis, which the structural certificate already showed
passes regret in 20/20 policies but tail agreement in only 17/20, so even perfect convergence is
borderline against the frozen gate. (2) Whitening changes the metric of Adam's steps, not their
number or size; the displacement budget stays about 0.05–0.1 per whitened coordinate at lr `3e-4`,
so a raw-versus-whitened null is the expected outcome under the exposure-shortfall reading and would
then be misread as PARK support. (3) By the direction's own rule a BC-only competence pass cannot
open COUNT/RAW or acquisition, so a positive leads to another conditioning object rather than to
the direction's question. The decision-relevant objects remain the exposure ladder and the
margin-scaled falsifier below. Schedule the whitening run alongside them, not instead of them, and
do not read its both-noncompetent outcome as PARK support until the exposure ladder has run.

### smallest_next_object

**Exposure ladder (B/EXPLORE, first).** The existing B1 code with no host or criterion change; arms
`FT-XF-FLEX` and `FT-XF-BC`; 3 seeds; 2 folds; three named runs: lr `3e-3` at the frozen 160/320
updates, lr `3e-4` at 1,600/3,200 updates, and both. Report competence flags, regret, tail
agreement, and PROBE rate per checkpoint. Cost: one to ten B1 wall times (140 s to about 25 min)
per run. This is not "automatic budget enlargement": it is a named object testing the direction's
own first-listed alternative, finite optimizer exposure, which the source audit says is about an
order of magnitude short. If competence appears at ten times the exposure, the whitening question
is moot and the acquisition evaluation can proceed on the existing host; if the ladder's competent
policies also choose PROBE in the sole positive-probe context, that is the first acquisition signal
of the family.

**Margin-scaled competence falsifier (B/EXPLORE, if the ladder fails).** Same eight-context host, same FLEX learner
(offline Bellman regression, AdamW), one arm plus the immediate-commit null, 3 seeds, 2 folds,
5,120 episodes/context, 320 root updates, checkpoints `{80,160,320}`; the probe's information value
scaled so the target-context net acquisition margin is about `0.25` instead of `0.05` (cost
unchanged). Relative competence: mean held-out return ≥ 80% of the oracle-minus-null gap, PROBE
chosen in the target context and in at most one of the seven others. Report per-seed curves and
PROBE rate by context. If competent, run the ladder `{0.25, 0.10, 0.05}` as named follow-ups; the
margin at which acquisition stops is the result. If not competent at `0.25`, one more named run
swaps the learner family for an online policy-gradient learner at the same margin before parking.
Cost: about 3 × B1 wall time per run.

### contrary_observation

Zero competence at ten times the exposure, and then at the `0.25` margin with the relative
criterion, for both the offline and the online learner. That locates the failure in the learner
packages rather than in the budget or the host, and `PARK` becomes the right call with no cheap
discriminator left.

### claim_ceiling_and_non_goals

Ceiling: "On this finite host, a FLEX learner did / did not learn to pay for a probe when the net
acquisition margin was `m`, for `m` in the ladder." Cannot support: COUNT/RAW polarity, general
value of paid information, variable `k` or `N`, UAV.

### literature_support_and_gap

- `DIRECT` — MARL-0203 (VIL2C, AAAI-26, `json/MARL-0203.json`): value of information defined as the
  KL shift in the receiver's policy per unit latency; the cost is waiting time and bandwidth, not
  an explicit paid acquisition; no competence gate.
- `DIRECT` — MARL-0071 (COCOM, `json/MARL-0071.json`): a communication gate trained on teammate
  Q-improvement pseudo-labels, a value-of-communication criterion, 5 seeds.
- `DIRECT` — MARL-0036 (FoX, `json/MARL-0036.json`): a coarser relational formation count beats
  strictly-more-informative joint-observation counts for exploration, 5 seeds; an analogue of the
  COUNT-versus-RAW question in a different role.
- `DIRECT` — MARL-0062 (AIR): adaptive individual/collective exploration; no probe cost.
- `DIRECT` — B03 §8.3 costly communication (B03-CL006), a fixed-cost planning model.
- `CURATOR_OR_PROJECT_INFERENCE` — P11-CL006 (model disagreement as an active probe selector) and
  B01's value-of-information framing; neither is a source result.
- Gap: zero catalog hits for "active perception", "information gathering", or "value of
  information" as a paid action in either library; the two-stage competence-first paid-probe design
  has no local neighbour. `UNKNOWN` globally. `REVIEWER_INFERENCE`: single-agent active-sensing and
  POMDP information-gathering literature exists broadly, so the question is not novel per se; the
  novelty is the finite-budget competence-first protocol, and that protocol is what has failed four
  times.

---

## Cross-direction portfolio analysis

### Genuine overlap versus shared infrastructure

- **FRRIE / VNFC.** Shared: set-encoder shared policies across `N`, byte-paired strictly-containing
  comparators, the no-contact and hand-structured-action nulls. Different estimands (finite-budget
  package efficiency at fixed roster versus post-loss recovery). Do not merge; do share the
  containing-comparator methodology and the VNFC-B1 lesson that package gains must be attributed by
  component.
- **CBSC / UCOPE.** Shared: stipulated finite hosts with small margins, RAW-contains-STRUCT nulls,
  learners with competence gates. Different interventions (passive encoding versus paid action)
  and different learner families (online recurrent PPO versus offline fitted-Q). Do not merge; do
  share the competence-gate and budget-ladder discipline, and the warning that exact-oracle
  competence bars on small-margin hosts produce uninterpretable nulls.
- **SCDMP** shares nothing scientific with the other four. It shares the native UAV host and
  foundation PPO trainer, which is the only competent trained physical-simulator policy in the
  first wave and should be treated as portfolio infrastructure.
- **Adjacent ACTIVE directions.** RCLE (persistent-common versus containing FLEX churn recovery) is
  the nearest scientific neighbour to VNFC and should be reconciled with it before either runs a
  churn learner; EGRCR is correctly held as an FRRIE control; EOCIV-lite and ACVC are correctly
  separated from CBSC.

### Fusion, separation, recast, closure

- No fusion. The two natural pairs differ in estimand.
- Recast VNFC's law object and UCOPE's host margin as above.
- New object inside SCDMP: the learner run (`RUN-L1`) the direction is named for.
- No direction closure. Object closures: none beyond what is recorded.

### Ranking

By expected information gain per unit of engineering effort, and by proximity to a
decision-relevant learner result (the same order under both criteria):

1. **SCDMP** — zero engineering; one decision; prior descriptive positive; at most 30 min.
2. **CBSC** — small finish; one decision; 12 short runs; first recurrent-PPO curves.
3. **UCOPE** — trivial engineering (two constants); the prior on the acquisition question is low
   after four failures, but the exposure ladder can overturn the competence narrative in minutes
   and the whitening discriminator is already contracted; the cheapest falsifier in the portfolio.
4. **VNFC** — small engineering after the recast (runner exists); first return-bearing churn result
   against a competent fixed controller; 3 × 64 updates.
5. **FRRIE** — moderate engineering even when stripped; the contrast is an 18-parameter clipping
   box, so the expected information is lower than the direction's framing suggests; about 5 h
   serial.

### Reusable engineering components (no polarity transfer)

Fresh 4 GiB admission; create-once run roots; process-tree RSS/wall ledger (as a record, not a
gate); typed checkpoint save/load; worker-equivalence tests; immutable held-out tape loading; the
SCDMP native host and foundation trainer; the CBSC recurrent-PPO trainer as the template for any
GRU learner; the UCOPE fold and competence-gate code as the template for competence-first designs.

### Parallel plan (no capacity limit)

- Lane 1: SCDMP RUN-01-REPLACEMENT-01 now; on branch 5 or 8 register RUN-L1.
- Lane 2: CBSC finish E2E, flip the readiness constant, B1, conditional B1b.
- Lane 3: VNFC law recast doc, 50-row conformance test, R02 DEBUG, B1–B3.
- Lane 4: FRRIE B01-smoke, then B01 through a stripped chain (Slice B trainer plus a minimal
  evaluator only).
- Lane 5: UCOPE exposure ladder and the contracted whitening discriminator in parallel (minutes
  each), then the margin-scaled falsifier, the online-learner swap, or PARK.

### Root attention order (not a capacity limit)

1. SCDMP: sign the `A-R2` readiness (`REVIEW_REQUIRED` → launch) for RUN-01-REPLACEMENT-01 and
   downgrade telemetry from invalidator to record.
2. CBSC: approve B1 launch without consumer-recompute and capacity gates; approve the B1b ladder.
3. UCOPE: approve the exposure ladder as a named object next to the already-approved whitening
   discriminator; approve the margin-scaled recast (or PARK) conditionally on both.
4. VNFC: approve the canonical-sort recast and the unit-test-scale A0, then the R02 seeds.
5. FRRIE: approve the stripped chain (drop Slices C–E as gates) and the 1-seed smoke.

The packet's own restart order (UCOPE audit → VNFC A0 → SCDMP → CBSC → FRRIE) was
decision-latency driven; the order above is information driven. The main differences are SCDMP
first, because only a signature separates it from a learner result, and VNFC below UCOPE, because
VNFC's next step is a recast of code that has just been written while UCOPE's is a one-line budget
decision that could overturn a four-failure narrative in minutes.

### Scaffolding versus learners

Yes, the portfolio is over-spending on formal scaffolding. Concrete evidence: FRRIE's 916-row IUT
and lattice-uniform law, and a `b01/` package that is 1,500 lines of science inside 8,400 of
contract; VNFC's 304-row binary64 action law and hex-constant AdamW, now backed by about 5,600 lines of
exact-arithmetic code including a hand-written scalar autodiff, all written before any R02 learner
update has run; SCDMP's full-support KL/IUT
that turned 562/562 positive tapes into a nonpass and a telemetry rule that discarded a completed
run; CBSC's 15-table lossless publication with all derived fields null and a tamper-resistance HIGH
blocking a wired launch; UCOPE's sealed objects and hash chains around a 140-second run. Four of the
portfolio's quarantines this wave were telemetry or validator failures, none scientific.
Reallocation: adopt one two-page "B-run contract" (code SHA, config, seeds, admission receipt,
resource ledger, per-episode raw CSV, curves, competence flags, descriptive statistics) as the
default for every B/EXPLORE object; reserve exact, bitwise, and telemetry-invalidation machinery
for named C-FORMAL claims; treat a missing telemetry field as a recorded defect, never as grounds
to discard returns; and stop routing arithmetic (means, AUCs, competence Booleans) through
external decision nodes.

### Three uncertainties the current evidence cannot resolve

1. Whether the FRRIE, VNFC, and CBSC hosts are learnable by their frozen packages at their frozen
   budgets at all. UCOPE says no for its host at 320 updates, and the source audit suggests that
   budget is an order of magnitude short of what its own initialisation requires; the other three
   have never produced a curve, and their exposure laws deserve the same arithmetic before launch.
2. Whether any structured-package advantage that appears is relational or semantic rather than
   shrinkage or conditioning. Only reassociation and derangement controls run across a budget ladder
   can tell, and no such ladder exists yet.
3. Whether SCDMP's order value can be learned from public history by a policy, as opposed to
   exploited by an oracle scheduler. No object tests it.

## Portfolio action list

- `RUN_NOW`: SCDMP RUN-01-REPLACEMENT-01 (fresh master; `A-R2` projects 350 s); UCOPE exposure
  ladder and the already-contracted whitening discriminator; prepare the UCOPE margin-scaled
  falsifier in parallel and run it if the ladder fails.
- `REPAIR_THEN_RUN`: CBSC B1 (finish E2E, drop two gates, flip the constant); FRRIE B01 (Slice B
  trainer plus minimal evaluator, then 1-seed smoke, then 3 seeds); VNFC (law recast, 50-row
  conformance test, then R02 DEBUG and B1–B3).
- `PARK`: none now; UCOPE if the exposure ladder, the whitening discriminator, and the
  `0.25`-margin falsifier all fail for both learner families.
- `CLOSE`: no direction. Objects already closed stay closed.
- `RECAST`: VNFC R02 law/A0 (now implemented but unrun; recast before running); UCOPE budget rule,
  host margin, and competence criterion.

## Five-direction comparison table

| | FRRIE | VNFC | CBSC | SCDMP | UCOPE |
| --- | --- | --- | --- | --- | --- |
| Valid learner result on current object | none | none | none (LR01 offline, unresolved) | none (`.3` oracle-value, consumed) | yes, `0/3` all arms at 160/320 updates |
| Strongest prior signal | none | none (B1 lineage: hand-structure explains gains) | exact protocol value `5/8`; LR01 mixed | 562/562 tapes positive | none |
| Scientific / scaffolding lines (static) | ~5,300 / ~14,200 | ~3,000 / ~5,700 (+1,950 runner) | ~5,200 / ~17,500 | ~4,800 / ~4,060 | ~1,420 / ~3,200 (+1,900 runner) |
| Engineering to a run | moderate (no 512-loop; DLL unbuilt) | small after recast (A0 code exists, unrun) | one constant flip plus E2E finish | zero (`A-R2` signed off) | trivial (two constants) |
| Main null | no-contact / shrinkage | DIRECT contains; BCRH beats | RAW competent and equal; generic register | public state suffices | exposure too small; host margin too small |
| Disposition | `CONTINUE` | `RECAST` | `CONTINUE` | `CONTINUE` | `RECAST` |
| Next object | B01-smoke → B01 | law recast → A0-lite → R02 DEBUG → B1–B3 | B1 → B1b | RUN-01-REPLACEMENT-01 → RUN-L1 | exposure ladder ∥ whitening → margin falsifier → margin ladder |
| Wall estimate | ~5 h serial | minutes per seed | minutes per arm-seed | ~6 min projected, ≤ 30 min cap | 2–25 min per run |

## Addendum 2026-09-02 — calibration agreed with the owner after this review

This addendum was added the day after the review closed, following a discussion with the owner. It
records requirements the owner set after reading the review; it is not part of the independent
assessment above and does not change any disposition's polarity. The same calibration is now
normative in `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` §11.

The owner's position, in three sentences. MARL research in this project proceeds by taking an
inspiration from a simple setting (a bandit, a single-agent toy, a closed-form model) and then
proving it by experiment. Pre-registration, oracle-retuned comparators, held-out transfer splits,
and stated failure boundaries are paper-time obligations that support a C-BENCH claim; they must
not act as gates in early exploration. No direction needs to prove roster invariance,
duration-independent skill semantics, or semigroup consistency; empirically better performance on
the declared population is a sufficient claim, and the strongest theory a direction should aim for
is a suboptimality bound for the scheme as implemented.

What this changes in the five dispositions:

| Direction | Disposition (unchanged) | What the calibration removes | What the smallest next object becomes |
| --- | --- | --- | --- |
| SCDMP | `CONTINUE` | The theorem-or-witness dichotomy inherited from the renewal-indexed lineage and the semigroup-consistency obligation are optional analysis, not registration conditions. | `RUN-01-REPLACEMENT-01` runs under a two-page B contract; the duration menu (k ∈ {7, 13}) is a legitimate suboptimal scheme and the within-segment discount factor τ(1−γ)/(1−γ^τ) is its error bound. |
| CBSC | `CONTINUE` | `FORMAL_ANALYSIS_BOUND = False` and the consumer-recompute and capacity gates may not hold a B launch (§11.4). | The three-seed B1 with a budget ladder, launched without the gates. |
| UCOPE | `RECAST` | The exact-oracle competence criterion stops being a pass/fail gate on a B run and becomes a recorded observation; the exposure arithmetic becomes the one mandatory exposure line. | Exposure ladder first, whitening discriminator alongside; competence at training durations is a B observation, and the odd/even duration split is the later C-time obligation. |
| VNFC | `RECAST` | The 304-row binary64 finite-action law is demoted from conformance condition to optional analysis; canonical sort is an admissible suboptimal presentation scheme. | R02 DEBUG and three 64-update seeds under a unit-test-scale conformance check. The coverage loss (2K−N)/N and the delay cost ≈ k/2 × gap are the direction's bound, with k a fixed stated parameter. |
| FRRIE | `CONTINUE` | The exact no-projection-contact equality theorem is optional analysis; the ordered-28 / TV / parameter-distance panel is not a launch condition. | The stripped 512-update chain, one to three seeds, matched curves only. |

Two consequences for the review's own text. First, every `overformalization_audit` section above
now has a normative basis: the obligations it lists as "cannot change a B decision" are the
obligations §11.6 demotes. Second, the `smallest_next_object` sections were written against the
spec as it stood on 2026-09-01; where they mention frozen contracts or oracle comparators for a B
run, read those as C-time follow-ups, not as prerequisites.

One thing the calibration does not decide. The quarantine rule for incomplete attempts is
unchanged; whether an instrumentation failure should downgrade a run's evidence class rather than
annul it (recommendation R4 in the workflow review) remains an open owner decision.

## Materials consulted

Packet: `README.md`, `REVIEW_PROMPT.md`, `DIRECTIONS.md`, `SOURCE_MANIFEST.json`,
`literature/README.md`, `literature/DIRECTION_MAP.md`, `literature/selected_references.jsonl`.
Shared: `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`, `docs/research/portfolio/PORTFOLIO.md`,
`docs/research/portfolio/FIRST_INVESTMENT_WAVE_USAGE_SAFE_STOP_HANDOFF_20260901.md`, the three
2026-09-01 portfolio decisions. Every manifest-listed direction file was read in full, plus the
B01/R01/R02/B1 innovator intakes, CM contracts, clarifications, `VNFC_B1_SCIENTIFIC_INTAKE.md`,
`VNFC_B1_RESULT.json` (head), `UCOPE_STRUCTURAL_COMPETENCE_VALID_RESULT_INTAKE_20260831.md`,
`UCOPE_CONTEXTUAL_PAID_ACQUISITION_R01_BELIEF_RESULT_INTAKE_20260831.md`, `CODE_SCIENCE_INDEX.md`,
`docs/project/PROBLEM_CACHE.md` (no entry names any of the five), `docs/research/RESEARCH_MAP.md`,
and the RCLE and EGRCR direction files for overlap. Code was inspected statically only.

Read after the packet froze (2026-09-01 afternoon):
`SCDMP_B01_FRESH_NAMED_ATTEMPT_INNOVATOR_INTAKE_20260901.md`, the science-card diff, and
`temp/scdmp-b01/A-R2/{assessment,telemetry}.json`; the
`VNFC_BPCR_R02_FINITE_PHYSICAL_ACTION_LAW_A0_FREEZE_20260901.md` diff and the
`experiments/candidates/variable_n_fleet_churn_r02/` module inventory;
`UCOPE_INVERTIBLE_CONDITIONING_R01_CONVERGENCE_DECISION_INTAKE_20260901.md`, the first half of
`UCOPE_B_EXPLORE_FT_XF_BC_INVERTIBLE_CONDITIONING_DISCRIMINATOR_R01_PROSPECTIVE_CONTRACT_20260901.md`
plus a search of its budget and initialisation clauses, and
`experiments/candidates/ucope/competence_first_scout_r01/{model,training}.py` in full.
