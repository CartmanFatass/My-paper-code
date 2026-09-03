# VNFC — section 11 recast intake (2026-09-03)

- Direction: `variable_n_fleet_churn`
- Live B object: `VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02` (`B/EXPLORE`)
- Demoted object: `VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0` (`A/RECON`, `result_bearing=false`)
- Controlling law: `VNFC-R02-ORC-B64-Q52-U64-V1` (freeze body unchanged; a dated addendum records the
  demotion)
- Governing method: `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`, §11 controlling

This is the §11.6 record of the demotion ("Direction owners SHOULD record the demotion in the
direction's next intake rather than rewrite historical documents"). It changes no scientific factor
of the R02 return question, and by itself produces no return, recovery or comparator observation.

## 1. Provenance of the decisions implemented here

- `docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md`, Part A.4, decisions 4, 6
  and 7; the VNFC audit with `file:line` for every gate is Part B section 2 of the same file.
- `docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`.
- Upstream: `docs/Claude_docs/reviews/FIRST_WAVE_INDEPENDENT_REVIEW_20260901.md`, VNFC section
  (disposition `RECAST`), and its 2026-09-02 addendum.

Decision 4, verbatim from A.4:

> Recast per §11: the 304-row A0 law is demoted to optional analysis and replaced as an integrity
> item by a ~50-row unit-test-scale presentation check; R02 DEBUG (8 updates) and three 64-update
> seeds run on the R01 runner; byte manifests are recorded if produced, never required

Decision 6, verbatim from A.4:

> Order | SCDMP → UCOPE → CBSC → VNFC → FRRIE, one Opus session each, sharing the two-concurrent
> budget with E1 (E1 still launches on its own trigger after P3)

Decision 7, verbatim from A.4:

> Downgrade, not annul: a run whose resource telemetry (peak RSS, scratch, wall) is missing stays
> valid and is marked "resources unmeasured"; annulment only when the claim itself is a resource
> claim. Learner-side instrumentation failure (missing logs or checkpoints) still quarantines under
> §6.2

The independent review's disposition for this direction, verbatim
(`FIRST_WAVE_INDEPENDENT_REVIEW_20260901.md`:1048):

> The 304-row binary64 finite-action law is demoted from conformance condition to optional analysis;
> canonical sort is an admissible suboptimal presentation scheme.

## 2. What §11 demotes in this direction

Each row is quoted from the compliance note's VNFC audit (Part B section 2) with the `file:line`
that note gives. "DIRECTION.md", "A0 freeze" and "A0 EM intake" are the working-tree revisions
committed unchanged in `Record VNFC working-tree state before the section 11 recast`
(`55a46c206`).

| # | Demoted condition (quoted) | file:line | Now |
| --- | --- | --- | --- |
| 1 | "No R02 result-bearing DEBUG is permitted until the one-law A0 object is complete and passing under its finite claim ceiling." | `DIRECTION.md:181-182` | **superseded.** A0 is optional analysis; it holds nothing. R02 DEBUG launches under §11.4's admitted conditions (§3 below). A0 may be finished later as an A object on its own merit |
| 2 | "Before any R02 DEBUG, exactly one finite physical-action law must prospectively fix: …7. an address-resolved conformance gate for structural predicates, deterministic commands, physically aligned probabilities, and RNG-coupled physical actions." | `DIRECTION.md:96,105-106` | the *seven definition obligations stay as the law's definition*; obligation 7's **address-resolved conformance gate** is replaced as a §4 integrity item by the 52-row unit-test-scale presentation-conformance check in §4 below. The check covers exactly the four families obligation 7 names |
| 3 | "Its frozen panel contains 304 address rows… Every physical CDF boundary, adjacent representable value and adjacent production word is enumerated" | `DIRECTION.md:122-126` | optional analysis. Not produced, not required, and its absence carries no polarity |
| 4 | "`PASS_CONFORMANT` requires every top-level row, every token, every CDF probe, every training replay, every containment check, and every independent predicate to pass exactly." | `A0 freeze:880-881` | recorded as A0's own decision rule for A0. It is **not** a launch condition for R02. No `PASS_CONFORMANT` exists and none is required |
| 5 | "binds exactly 942 loaded Python dependency sources plus the content-bound real `scripts/run_vnfc_bpcr_r02_a0.py` `__main__`, 31 opened distribution resources, and 81 compiled modules" | `DIRECTION.md:41-44`; `A0 EM intake:36-39` | **recorded if the tooling produces it, never required.** The R02 runner records what it can observe (source inventory, native artifact identity) as fields with `gating: false` |
| 6 | "the source-keyed `bpcr_backend.dll` at literal build key `7222d990…`, forbids compilation, helper subprocesses, fallback, or cache mutation, and changes the compiled inventory from the frozen 81-row pre-load root to exactly the frozen 82-row post-load root" | `DIRECTION.md:47-51`; `A0 EM intake:52-58` | **recorded, not required.** Compilation of the native backend from unchanged source is permitted; the observed build key and the observed artifact sha256/size are recorded. A DLL rebuilt from unchanged source with a different build key (or the same key and a different artifact digest) is recorded as such and holds nothing |
| 7 | "Framework autograd or a different algebraic derivative association is not an implementation of this law." (memoised scalar reverse DAG) | `DIRECTION.md:174-176` | recorded as **the law's own statement about itself**, not as a launch condition for R02. R02 trains with framework autograd; §11.2 removes bit identity as an admission condition |
| 8 | "`FAIL_LAW` … returns this law for revision, has no algorithm polarity, and forbids R02 DEBUG." | `A0 freeze:883-886` | the "forbids R02 DEBUG" clause is superseded. `FAIL_LAW` remains A0's own disposition if A0 is ever executed, with no algorithm polarity, as it always had |
| 9 | "Forbidden now: … any result-bearing R02 DEBUG, PRIMARY, OPTIONAL, return endpoint, learner training, or B claim" | `A0 freeze:903,908` | superseded for R02 DEBUG/PRIMARY under this recast. The other clauses of that list — no R01 rerun/resume/repair/read, no alternate or runtime-selectable law menu, no opaque rank as a learned feature, no latent presentation/row/memory/hash/lane/batch-neighbour identity, no performance or lifecycle claim from A0 — are unchanged and still binding |
| 10 | "fresh 4-GiB admission, complete telemetry, create-once quarantine, and B/EXPLORE claim semantics" transfer to R02 | `DIRECTION.md:94` | split. The admission, create-once quarantine and B/EXPLORE claim semantics remain launch conditions (§11.4 allows all three). "Complete telemetry" becomes a recorded field under decision 7: missing resource telemetry sets `resources_unmeasured: true` with reasons and does not annul |
| 11 | "`INCOMPLETE` is missing/invalid source identity, dependency drift, nonfinite value, absent address, artifact/telemetry failure…" | `A0 freeze:888-890` | the audit classed this `UNCLEAR` because §11.4's last sentence left the downgrade-versus-annul question open. Decision 7 closes it: **resource**-telemetry failure downgrades; **learner-side** instrumentation failure (missing checkpoints, missing result body, nonfinite values, absent addresses, source drift) still quarantines under §6.2 |

Row 1 is the operative block the compliance note names ("the VNFC block is documentary
(DIRECTION.md:181-182)"), and A0 has no implementation to grep. Rows 5, 6 and 7 are the
2026-09-02 edits that the compliance note records as movement *away* from §11; they are recorded
here as demoted rather than rewritten out of their documents.

## 3. What remains a launch condition for R02

Unchanged and still binding:

- the §4 common integrity requirements, in full;
- the §5.2 requirement that the real environment, policy, learner, trainer and evaluator run and
  report **nonzero** transition, optimizer-update and evaluation counts. For R02 these are the
  frozen counts of the R01 innovator intake
  (`VNFC_BPCR_BEXP_PRESENTATION_SAFE_RETURN_R01_INNOVATOR_INTAKE_20260901.md`:83-90): DEBUG 8
  updates = 256 episodes / 1,536 joint transitions / 256 optimizer steps / 112 evaluation rollouts
  per arm-pair; each PRIMARY seed 64 updates = 1,024 episodes / 6,144 transitions / 1,024 optimizer
  steps per arm and 208 evaluation rollouts;
- the mandatory resource admission: `python scripts/hmasd_resource_preflight.py admit-memory --out
  <run_dir>/preflight.json`, at least 4 GiB physical **and** effective available memory, run
  immediately before each invocation and re-validated inside the runner
  (`_implementation_hard_fence`, freshness window 300 s);
- **one exposure line.** R02 records, per arm per update, the relative parameter displacement
  `||θ − θ0|| / ||θ0||` against the arm's own initialisation, alongside the per-step pre-clip
  gradient norm the R01 runner already records. This is §11.4's exposure clause and is a launch
  condition;
- the §4 integrity items this direction already defines and which are **not** demoted:
  - the **52-row presentation-conformance check** of §4 below (the replacement integrity item for
    the address-resolved conformance gate);
  - **equal exposure between arms**: matched interaction and optimizer exposure for MAPR-4 and
    DIRECT-SET-AR (R01 intake:34-35), enforced by the runner's per-update forward/backward exposure
    reconciliation (12 action forwards, 384 optimizer forwards, 16 backwards, 16 optimizer steps
    per arm per update);
  - **leakage**: the held-out `N=7` namespace is disjoint from training, the freeze token binds
    training counts, checkpoint digests and the gate before any `N=7` endpoint is opened, and the
    four forbidden `N=7` control surfaces (`n7_tuning_callback`, `checkpoint_selector`,
    `seed_selector`, `heldout_adaptation_callback`) remain absent;
  - **DIRECT strictly contains MAPR** at initialisation with an exactly zero residual output, and
    the DIRECT residual-activity flag is observed at evaluation;
  - **comparator competence**: the eight-corner high-demand BCRH precheck, with scorer/checker and
    independent-enumerator agreement and no hard-validity failure. Its failure invalidates only the
    BCRH comparison (`NONIDENTIFIED`), not the run;
- create-once publication and the §6.2 quarantine of an incomplete attempt;
- the RNG ancestry law: one master per seed, `SHA-256(label || uint64_be(seed))`, no external-master
  seam, and every draw taken at a declared address.

### Frozen factors, unchanged

Host, observations, legality masks and the four-token physical action grammar; training support
`N = {3, 5}` and held-out `N = 7`; unshaped `J_ext = 0.5·R_fail_60 + 0.5·U_total` with `R_fail_60`
primary; the abstract MAPR-4 and DIRECT-SET-AR topology with DIRECT strictly containing MAPR;
`BCRH-PERSIST`; the exploratory budget structure; 16 balanced episodes, 96 joint decisions, four
PPO epochs × four minibatches and 16 optimizer steps per update per arm; evaluation of update 0 and
update 64 for both learned arms on eight common fresh worlds in all six `(N, failed-zone)` cells,
then BCRH once on the same sixteen `N = 7` worlds (208 evaluation rollouts per seed).

### Seeds fixed here, before launch

R02 requires fresh seed identity (`DIRECTION.md:111-113`), and no VNFC document fixes R02 seeds.
They are fixed now, outcome-blind, before any launch:

| Stage | Seed(s) | Updates |
| --- | --- | ---: |
| `B0-DEBUG` | `2026090301` | 8 |
| `B1-B3-PRIMARY` | `2026090311`, `2026090321`, `2026090331` | 64 each |

No optional seed is opened by this intake.

## 4. The 52-row presentation-conformance check (the replacement integrity item)

Object id: `VNFC-R02-PRESENTATION-CONFORMANCE-52`. Unit-test scale, seconds to run, no native host,
no learner run, no result polarity. It is a pass/fail launch condition for R02 and replaces the
address-resolved conformance gate of `DIRECTION.md:105-106`.

**What it tests.** The canonical computational representative: the physical candidate rows are
sorted by ascending opaque rank before the first tensor operation, the null candidate stays last,
and the deterministic command, the physically aligned probability vector and the RNG-coupled
sampled command are therefore functions of physical state alone. A *presentation* is a permutation
of the agent rows with masks, fixed-occupant indices and opaque ranks co-permuted; the four
presentations are `canonical`, `reverse`, `cyclic` and `seed_fixed_random`. Physical rank is
carried by the opaque rank, so the inverse-mapped physical command is compared across
presentations, never the row index.

**The row list, frozen before the check is run.**

| Row | Id | Asserts |
| --- | --- | --- |
| A01 | `SORT_ASCENDING_N3` | canonical row order equals ascending opaque rank at `N=3` |
| A02 | `SORT_ASCENDING_N5` | same at `N=5` |
| A03 | `SORT_ASCENDING_N7` | same at `N=7` |
| A04 | `SORT_NULL_LAST` | the null candidate keeps index `N` under every presentation and is never reordered among agent rows |
| A05 | `TIE_EXACT_LOGIT_SMALLEST_OPAQUE` | on an exact logit tie between two agents the deterministic decoder takes the smaller opaque rank, under all four presentations |
| A06 | `TIE_AGENT_BEATS_NULL` | on an exact agent/null logit tie the agent wins (null tie rank `2**30`), under all four presentations |
| B01 | `AGENT_ROWS_COPERMUTED` | agent rows keyed by physical rank are equal across presentations |
| B02 | `LEGAL_MASKS_COPERMUTED` | legality masks keyed by physical rank are equal across presentations |
| B03 | `FIXED_OCCUPANTS_COPERMUTED` | fixed-occupant indices resolve to the same physical ranks across presentations |
| B04 | `OPAQUE_RANKS_COPERMUTED` | opaque ranks travel with their agent row |
| B05 | `PHYSICAL_SUPPORT_EQUAL` | the legal physical-candidate support per token is equal across presentations |
| B06 | `OPAQUE_DETERMINISTIC_TIE_RANKS_COMPLETE` | opaque ranks are a complete unique total order `1..N` in every presentation |
| C01 | `DET_MAPR_CANONICAL` | deterministic inverse-mapped physical command, MAPR, canonical |
| C02 | `DET_MAPR_REVERSE` | same under `reverse`, and bitwise-equal logits and probabilities |
| C03 | `DET_MAPR_CYCLIC` | same under `cyclic` |
| C04 | `DET_MAPR_SEED_FIXED_RANDOM` | same under `seed_fixed_random` |
| C05 | `DET_DIRECT_CANONICAL` | deterministic inverse-mapped physical command, zero-residual DIRECT, canonical |
| C06 | `DET_DIRECT_REVERSE` | same under `reverse`, and bitwise-equal logits and probabilities |
| C07 | `DET_DIRECT_CYCLIC` | same under `cyclic` |
| C08 | `DET_DIRECT_SEED_FIXED_RANDOM` | same under `seed_fixed_random` |
| D01 | `CDF_BOUNDARY_0_BELOW` | uniform immediately below cumulative boundary 0 selects the same physical candidate in all four presentations |
| D02 | `CDF_BOUNDARY_0_AT` | uniform exactly at cumulative boundary 0 |
| D03 | `CDF_BOUNDARY_1_BELOW` | immediately below cumulative boundary 1 |
| D04 | `CDF_BOUNDARY_1_AT` | exactly at cumulative boundary 1 |
| D05 | `CDF_BOUNDARY_2_BELOW` | immediately below cumulative boundary 2 |
| D06 | `CDF_BOUNDARY_2_AT` | exactly at cumulative boundary 2 |
| D07 | `CDF_FIRST_HALF_OPEN` | the smallest representable uniform above 0 |
| D08 | `CDF_LAST_HALF_OPEN` | the largest representable uniform below 1 |
| E01 | `RNG_MAPR_CANONICAL` | RNG-coupled sampled physical action, MAPR, canonical, four token uniforms drawn at declared addresses |
| E02 | `RNG_MAPR_REVERSE` | same physical action under `reverse` for the same uniforms |
| E03 | `RNG_MAPR_CYCLIC` | same under `cyclic` |
| E04 | `RNG_MAPR_SEED_FIXED_RANDOM` | same under `seed_fixed_random` |
| E05 | `RNG_DIRECT_CANONICAL` | RNG-coupled sampled physical action, zero-residual DIRECT, canonical |
| E06 | `RNG_DIRECT_REVERSE` | same under `reverse` |
| E07 | `RNG_DIRECT_CYCLIC` | same under `cyclic` |
| E08 | `RNG_DIRECT_SEED_FIXED_RANDOM` | same under `seed_fixed_random` |
| F01–F12 | `RANDOM_STATE_01` … `RANDOM_STATE_12` | twelve fixed-seed random draws over `N ∈ {3,5,7}` × `zone ∈ {1,2}` × state kind ∈ {`t0`, `later_fixed_or_acquiring`, `diagnostic_null_tie`}, arms alternating MAPR / zero-residual DIRECT, each tested under all four presentations for bitwise-equal candidate logits, bitwise-equal probabilities, equal deterministic physical command, and equal sampled physical command under a common uniform |
| G01 | `NEAR_TIE_N5_REVERSE_SURROGATE` | a constructed `N=5` near-tie (two candidate logits within one ULP) selects the same physical agent under `reverse` as under `canonical` |
| G02 | `DUPLICATE_TIE` | two byte-identical agent rows with different opaque ranks: the deterministic choice takes the smaller opaque rank under every presentation |
| G03 | `FIXED_PREFIX_NULL` | a fixed occupant on one token together with a null-legal token: support and command are presentation-independent |
| G04 | `ONE_STEP_GRADIENT_PARAMETER_EQUALITY` | one forced-command PPO backward under `canonical` and under `reverse` gives bitwise-equal gradients and bitwise-equal post-step parameters |

Row count: 6 (A) + 6 (B) + 8 (C) + 8 (D) + 8 (E) + 12 (F) + 4 (G) = **52**.

**Declared boundary of the check.** It is a finite conformance observation on the states it
enumerates. It supports no learnability, return, recovery, superiority, arbitrary-`N` or general
permutation-invariance claim. Row `G01` is a *surrogate* for the registered `N=5/reverse` witness:
the frozen witness parameterisation lives in the untracked A0 package
`experiments/candidates/variable_n_fleet_churn_r02/fixtures.py`
(`source_bound_witness_parameter_fixture`), which this recast does not commit or import, so the
check constructs its own near-tie exhibiting the same mechanism. This is recorded as a deviation,
not as a reproduction of the witness.

## 5. The R02 object, restated in one page

**Question.** On the exact two-zone, one-unannounced-executor-loss simulator, does a
presentation-safe shared `MAPR-4` policy learn post-loss recovery from unshaped external return at
training rosters `N = {3, 5}` under 64 updates, and show preliminary failed-zone recovery direction
on untouched `N = 7` worlds, separately against (1) the strictly containing same-information
`DIRECT-SET-AR` learner under matched interaction and optimizer exposure and (2) the competent
fixed `BCRH-PERSIST` controller on common evaluation worlds?

**Claim ceiling: `B/EXPLORE`.** Preliminary learnability, direction, instability and finite-budget
held-out `N = 7` external-return/recovery evidence for the exact simulator support and the named
implementations. No stable superiority, confirmatory C result, arbitrary-`N`, repeated churn,
general MARL, permutation-invariance theorem, unique mechanism, UAV/hardware transfer, safety,
flight or deployment claim.

**Arms.**

| Arm | What it is | Mechanism it carries |
| --- | --- | --- |
| `MAPR-4` | shared four-token autoregressive set policy, roster-size-agnostic order-independent pooling, `O(4N)` | factorised reassignment: the same parameters express "reassign the lost executor's role" at any `N` |
| `DIRECT-SET-AR` | strictly containing same-information learner (MAPR base plus a prefix-conditioned residual initialised to exactly zero), matched interaction and optimizer exposure | the same information without the factorisation constraint |
| `BCRH-PERSIST` | competent fixed bounded receding-horizon controller, up to 1,961 legal commands at `N = 7`, no learning | hand-structured rule sufficiency |

**The two mechanisms the arms separate.** `MAPR` versus `DIRECT` separates *finite-budget inductive
bias* (factorisation / optimisation / regularisation) from *representational capacity*: because
DIRECT strictly contains MAPR, any MAPR edge can only be a finite-budget effect, never
representational superiority or information necessity, and it reads as a factorisation effect only
if DIRECT shows residual distribution or command activity. `MAPR` versus `BCRH` separates *learned
recovery* from *bounded heuristic sufficiency*: if the fixed controller matches or beats the
learner, the host is solved by a rule and the learning question is not yet posed.

**The differentiating measurement.** Per seed, for both learned arms at checkpoints `update 0` and
`update 64`: `R_fail_60` (primary) and `U_total` at `N ∈ {3, 5, 7}`; MAPR final-minus-initial at
`N = {3, 5}`; paired MAPR−DIRECT and MAPR−BCRH `R_fail_60` at `N = 7` on common worlds; plus
`U_intact`, failed-zone first-service seconds, executor reacquisition seconds, zero-service seconds
0–60, zone strata, individual worlds, the DIRECT residual-activity flag (total variation and
physical-command change under residual ablation), the relabel-mismatch counts and the exposure line.

**The reading rule, written before the data.** Transferred verbatim from the R01 innovator intake
(`VNFC_BPCR_BEXP_PRESENTATION_SAFE_RETURN_R01_INNOVATOR_INTAKE_20260901.md`:99-114):

> Preliminary support requires at least two of the first three valid seeds to show positive MAPR
> final-minus-initial recovery at both training sizes and positive paired `N=7 R_fail_60` directions
> against each comparator, with active/competent comparators, no persistent zone reversal, and no
> repeated adverse `U_total` or `U_intact` direction. This remains hypothesis-generating.
>
> The exact 64-update proposition is falsified only when common validity, PS-B0, action sensitivity,
> and comparator competence hold and either:
>
> - MAPR has nonpositive final-minus-initial recovery at one or both training sizes in every seed; or
> - MAPR learns at both training sizes but has nonpositive paired `N=7` recovery versus both DIRECT
>   and BCRH in every seed.
>
> Mixed seed signs or zone reversal mean `INSTABILITY/HETEROGENEITY`. Relabel, telemetry, resource,
> native-host, hard-validity, or comparator-competence failure means `INCOMPLETE` or comparator-
> specific `NONIDENTIFIED`, never a scientific null. A valid Class B null does not close the
> direction.

Two clarifications this recast makes to that rule, both consistent with decision 7 and with §11:

1. "PS-B0" in the falsifier clause is read as the presentation-safety condition, now discharged by
   the 52-row check of §4 plus the per-decision fresh-relabel mismatch counts the runner records.
2. "telemetry … failure means `INCOMPLETE`" is read as **resource** telemetry downgrading to
   `resources_unmeasured: true` and **learner-side** instrumentation failure still quarantining.

**Budget.** One DEBUG invocation at 8 updates, then three PRIMARY invocations at 64 updates each,
one process at a time, at most four torch threads, a fresh admission receipt immediately before
each invocation. Outputs under `temp/directions/variable_n_fleet_churn/exp/R02_20260903/`
(gitignored).

**The R02 presentation change.** Exactly one, as the direction's documents define it: the canonical
opaque-rank sort is swapped into the existing R01 runner, so that the physical candidate set is
serialised in ascending opaque rank before the first tensor operation and the null candidate stays
last. No other treatment, observation, action grammar, host or comparator change is made. Under
§11.3 canonical-sort presentation is an admissible suboptimal scheme and needs no invariance proof.

## 6. Relation to `flexible_skill_duration`

Spec §11.5, verbatim:

> Untying the skill duration k and untying the agent count N are **two separate directions**, not one
> joint algorithm. Each holds the other quantity fixed as a stated parameter of its objects and
> reports sensitivity to it where the bound in §11.2 depends on it. No joint variable-k-plus-variable-N
> object exists unless the owner opens one.

`variable_n_fleet_churn` is the untied-`N` direction: `N` varies (training `{3, 5}`, held-out `7`,
and one unannounced within-episode loss), and the skill/commitment duration is not a free quantity
of any R02 object. `flexible_skill_duration` is the untied-`k` direction and holds `N` fixed. This
intake opens no joint variable-`k`-plus-variable-`N` object and none exists. VNFC's §11.2 preferred
theoretical product remains the direction-level pair the review names: the coverage loss `(2K−N)/N`
and the delay cost `≈ k/2 × gap`, with `k` a fixed stated parameter here.

## 7. What this intake does not do

It records no return, recovery, learnability or comparator observation, changes no host,
observation, action grammar, objective, arm, roster law, budget, evaluation plan or reading rule,
and consumes no scientific object. It does not resume, salvage, reopen or reinterpret the
quarantined R01 DEBUG attempt, whose endpoints, checkpoints, optimizer tensors, RNG masters and
polarity remain unavailable. Revision-09 remains consumed and invalid for value attribution. A0 is
neither executed nor abandoned: it becomes optional analysis with no polarity, and its
implementation stays in the working tree at `experiments/candidates/variable_n_fleet_churn_r02/`,
uncommitted.

## 8. Result

See §9 (added after the run).
