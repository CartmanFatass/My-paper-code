# UCOPE R03 S2 engineering request

Decision owner: EM-ucope

```text
document_kind=DIRECTION_ENGINEERING_REQUEST
document_revision=S2-R01
direction_id=ucope
logical_identity=EM-ucope
generation=1
exact_object_revision=UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-03
science_revision=UNCHANGED
engineering_stage=S2_CONSTRUCTION_ONLY
s1_disposition=S1_TECHNICALLY_ACCEPTED
registered_panel_execution=false
result_bearing_command_authority=false
reviewer_release=false
sancheck_release=false
empirical_authority=false
effect_refs=EMPTY_AT_HANDOFF
```

## Idempotent intake and frozen authority

The Portfolio-to-EM Work Packet is intaken idempotently as work id
`e4171414a057bb22e8c62c0ebb2c1f20c1e660a361755b642babb295e19f87f2`.
Its packet SHA-256 is
`b3ad54090add9d6a46ea18a3de71aced8aea2b4bd0ce8cad5199f60fd650bbf0`.
Before this create-once artifact was written, the packet schema, work id,
scope, every authority ref, repository-relative containment, non-reparse path
identity, expected research revision, and empty Effect set matched current
facts. This decision is derived from those durable authorities, not from a
conversation summary.

The exact frozen authority boundary is:

| Reference | Frozen identity |
| --- | --- |
| `.codex/runtime/work/ready/e4171414a057bb22e8c62c0ebb2c1f20c1e660a361755b642babb295e19f87f2/packet.json` | SHA-256 `b3ad54090add9d6a46ea18a3de71aced8aea2b4bd0ce8cad5199f60fd650bbf0` |
| `.codex/runtime/work/ready/4d81a653ab636b29019b83f183c0c87e6716c00f9622a944e12fb9c16e7e42e4/packet.json` | SHA-256 `5725d75ce425472bec13d61ef1d81e340e526b947fd34d326afe2d4efc1aa3fb` |
| `.codex/runtime/work/ready/6b6faffe28569ee91047172c7ec03589cbda6818b84bf808fe9464c931ab2d54/packet.json` | SHA-256 `50df832a3543550a8eb6473dcec3420d1fa0815a6ecc5f445198a8bc9e9038ae` |
| `.codex/runtime/work/ready/dfbff7ba40fe074fe06cc18f622bb7a3c318f4ed355ed63642f23ca8f17f47aa/packet.json` | SHA-256 `af931caf282d183dd94123b2b9b442984d0e9b4eba681234148c9ee3736d5a0e` |
| `docs/research/portfolio/PORTFOLIO.md` | SHA-256 `37248491759e616b772dac89076dd6ba3d7457bfa8f4cb61dc01f5560ce43dc9` |
| `docs/research/portfolio/workflow/registry.json` | revision `9`, SHA-256 `95e3dd2aaf0c54b589b6f29ed51aadd0871300ba6ec528f64e12509550e03941` |
| `docs/research/candidates/ucope/DIRECTION.md` | SHA-256 `ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d` |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_SCIENCE_CARD_20260823.md` | SHA-256 `94fa0ddb4ef4c686a60a1d9386f8b1b6184184f75df6c51a6fb61cedd8185e1c` |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_CHATGPT_PRO_CLOSED_INTAKE_20260823.md` | SHA-256 `0e7908ad5001085b8861470286233fd2008f657545d260fd92877ecf14acec19` |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_STATIC_FEASIBILITY_PORTFOLIO_EM_VALUE_INTAKE_20260823.md` | SHA-256 `7586f4624111974dc993c328c7ae47b21adcd7801b38fd7a31e1b6c380112554` |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_FINITE_STAGED_CONSTRUCTION_PORTFOLIO_SELECTION_20260823.md` | SHA-256 `7818c4b353037243993590a5d4968d429a92433b38ffbea99271789febc18aec` |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_S0_CM_TECHNICAL_ACCEPTANCE_PORTFOLIO_EM_INTAKE_20260824.md` | SHA-256 `f7d5522506c3bd96d84c222dc6474cc40b6f4dfbb0aed12b7be68c1bda63b7ae` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_ENGINEERING_REQUEST_R03_20260825.md` | SHA-256 `1c78a75d418181c949c142220c27326958baaae914c54666d6e040f5f8b02f08` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_ENGINEERING_REQUEST_R04_20260825.md` | SHA-256 `874bee1e49837182b45a2fe3fa62c2ba0c12f1443386bd15130b296e5cad9fda` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_ENGINEERING_REQUEST_R05_20260826.md` | SHA-256 `653d2caf0f9d0c1388568cbdfdae9945e3d0b7ea0cb38002eaa458a2f57a484d` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_ENGINEERING_REQUEST_R06_20260826.md` | SHA-256 `e20e3409567ab00abe193c103cea1ed415d321a2df3a0a202f8114161ed0a381` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_TECHNICAL_ACCEPTANCE_R06_20260826.md` | SHA-256 `86e6e08bf8269a3da1fa6aadd0eacdbf20a3c437c24be51a2184222c33d5ce81` |
| `docs/research/candidates/ucope/workflow/research/state.json` | revision `10`, SHA-256 `95419a6dccc96a875e326853833bbf4b632bccdb641a65895ceaf2f62bfa076a` |
| `docs/research/candidates/ucope/workflow/engineering/state.json` | revision `7`, SHA-256 `c48cd254cae5d913e44c45e22780c8cc0ccbb93cfcbf7732416706170a691437` |
| `temp/directions/ucope/test/s1/r6/R06_S1_TECHNICAL_ACCEPTANCE.json` | SHA-256 `eb346b006c271892b4419c3f9a24290474107299d589d23c6062104fde89c4fb` |
| `temp/runtime/receipts/wt-ucope-engineering-s1r6.json` | SHA-256 `3e6f5a3e9f02e8dd06b098c32dd92777d42b37d31df30699185425e673ba231a` |
| `temp/directions/ucope/test/s1/S1_R03_RESULT_RUN_ENVIRONMENT_INCOMPATIBILITY.json` | SHA-256 `f3dea1165b939174f0cbb0301dfd40465a29ebfa533687450390d2248dc6f36f` |
| `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260825-02/S1_R04_BASETEMP_PARENT_INCOMPATIBILITY.json` | SHA-256 `e754208383220b66e30fddcae0a8e8603e2ffff212236132f698cecfae502023` |
| `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260826-03/S1_R05_WINDOWS_PENDING_PATH_LENGTH_INCOMPATIBILITY.json` | SHA-256 `124861fa6d05e2937b14d01fdea09fa8752484de6fe8e0dee62fdb2fa1ee2df8` |
| `scripts/hmasd_run.py` | SHA-256 `a072f8a50c825a19d91189b2330b19dc9c4198810d8453a5ae8c9057e77453d4` |
| `scripts/hmasd_state.py` | SHA-256 `8e7b6c43d8d70ae3e5769084c7e2fec19e8626404d154c68639a2f83632bd653` |
| `scripts/hmasd_work_packet.py` | SHA-256 `a3a7f7b7a62b74fba3ac335e8ffc1897cd9435bcbc41a4549fad1571d3b4d9fb` |

Runs 01 through 03 and the accepted R06 run, their claims, Operators,
manifests, logs, evidence, and worktrees remain immutable. The accepted R06
facts remain technical only: `42` focused tests passed, all thirteen
result-blind gates are true, the worst pending path is `186 <= 240`, and the
complete counts-only projection is `380.2810449061144` seconds,
`0.10563362358503178` CPU-hours, `515145728` peak-RSS bytes, and
`2312507074` aggregate-I/O bytes. No complete R03 package, partial value,
question-relevant output, registered seed, S2 access, candidate, source/test
diff, scientific result, or Effect exists.

## Frozen R03 and S1 boundary

The sole scientific object remains revision
`UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-03`.
This request changes no host, horizon, panel, arm, coordinate, `K_train`,
`K_test`, seed, episode count, reward, comparator, optimizer, RNG namespace or
sharing law, FP32 rule, checkpoint law, threshold, diagnostic, attribution
branch, activity boundary, strongest alternative, claim ceiling, or successor
condition. Pro closure, the S0 intake, R03 through R06 engineering provenance,
and the R06 S1 technical acceptance remain intact.

S1 is accepted only as a native, result-blind semantic substrate. It supplies
no observed S2 speedup. The R06 projection is a counts-only planning proxy with
no unmeasured worker or cross-phase speedup and is not a result-command
estimate, empirical observation, or S2 conclusion.

The only remaining construction allocation is `6` managed / `6` hard S2
engineer-days. The total `15` managed / `18` hard engineer-day envelope is
non-replenishable. S2 construction keeps cumulative result-blind TEST at `6`
managed / `12` hard CPU-hours and the largest S2 TEST command at `30` managed /
`60` hard minutes. No unused S0 or S1 budget transfers into S2.

## Engineering request — S2 construction only

Canonical `CM-ucope` may coordinate one bounded construction tranche for a
coherent S2 candidate after Root delivers this immutable request. The tranche
may extend only the existing direction-local R03 package and one focused S2
test file, using nonregistered, result-blind fixtures. It must stop and return
before Reviewer, SANCheck, registered-panel execution, or any result-bearing
command. This artifact and its follow-on packet do not create or dispatch CM,
an Implementer, a worktree, a Reviewer, SANCheck, an Operator, or a run.

One coherent source ownership scope remains assigned to at most the already
authorized single Sol-high `hmasd-implementer`; it is not split across parallel
Implementers or replaced with a second Implementer. Root owns any later fresh
native Windows assignment. A suitable short assignment identity is `s2c1`,
with branch `omp/ucope/engineering/s2c1` and canonical cwd
`C:/Projects/HMASD-worktrees/ucope-engineering-s2c1`; provisioning and its
runtime receipt are prerequisites, not effects of this request.

### Complete finite evaluator and diagnostics

The construction candidate is coherent only if it implements the following
closed evaluator contract without changing the R03 science card:

1. **Input closure.** The production evaluator accepts exactly the final
   batch-320 checkpoint inventory for `3` learned arms x `3` panels x `10`
   master seeds (`90` distinct slots), the exact R03 object digest, and no
   alternative checkpoint. It rejects a missing, duplicate, extra, malformed,
   non-final, cross-object, or digest-mismatched slot before publication. S2
   construction fixtures use a separate nonregistered namespace; they may test
   all shapes and branches but may not load a registered checkpoint or execute
   the registered population.
2. **Primary finite enumeration.** For every final seed/panel/learned-arm
   checkpoint, conclusion-bearing `K_test={2,4,6,8}` evaluation enumerates both
   probe regimes, every tail regime permitted by the panel, all `2^6` actual
   histories, all `2^6` displayed yoked histories under SEVERED, every legal
   candidate period, and analytic terminal-service expectation. Frozen model
   probabilities are FP32 weights; normalization error above `1e-5` is a
   technical invariant failure. There is no Monte Carlo evaluation.
3. **Mandatory comparator and attribution populations.** The evaluator includes
   ordinary-FP32 `BELIEF-DP`, `IMMEDIATE-DP`, and
   `FORCED-PROBE-BLIND-DP` finite enumeration with frozen `1e-6` comparison
   tolerance and tie order. It evaluates unchanged final checkpoints over the
   complete `K_train={1,3,5,7,9}` population. For forced-PROBE PERSISTENT
   `K_test`, RAW-PERMAVG averages final RAW tail logits over every distinct
   permutation of each six-bit history, then applies the frozen greedy tie rule
   without retraining or recomputing RAW's root action.
4. **Values and decomposition.** For every required seed, panel, and arm, retain
   expected total `J`, every utility component, root action, and tail action.
   Compute `A` for forced PROBE, `A_0` for FORCED-PROBE-BLIND-DP, `B` for
   IMMEDIATE-DP, `I=A-A_0`, `D=A_0-B`, `Gamma=A-B=I+D`, and `G=J-B`.
   `Gamma=I+D` must hold within `1e-5`; failure is a preactivity analysis
   defect, never a scientific result.
5. **Headroom diagnostics.** Before learned interpretation, report and require:
   a prior-optimal IMMEDIATE-DP `K_test` period unique by at least `0.02`;
   different regime-conditional optima;
   `I_BELIEF-DP,PERSISTENT >= 0.04`;
   `Gamma_BELIEF-DP,PERSISTENT >= 0.03`;
   `D_PERSISTENT` in `[-0.021,-0.019]`;
   `abs(I_BELIEF-DP)<=1e-5` in REDRAW and SEVERED with immediate commitment
   preferred over PROBE by at least `0.019`; and every q-value and expected
   action value finite and more than `1e-6` from an unintended FP32 tie.
6. **Support diagnostics.** For every seed/panel/learned arm, report at least
   `2048` visits for every root action and, conditional on PROBE, every tail
   period; exact balanced totals (`40960` per PERSISTENT regime and `20480` per
   ordered REDRAW or SEVERED regime pair); and at least `256` occurrences of
   each displayed count `N in {0,...,6}` in the treatment channel.
7. **Competence diagnostics.** Compute
   `R_comp(s,p)=J_BELIEF-DP,p-J_BELIEF-FEATURE,s,p` on complete held-out
   `K_test`, and forced-PROBE tail agreement `T_comp(s,p)` over the complete
   panel. For every panel, at least `9/10` seeds must match the BELIEF-DP greedy
   root action, satisfy `R_comp<=0.02`, and satisfy `T_comp>=0.95`.
8. **Three paired contrasts.** Per seed compute
   `Delta_test=J_COUNT,PERSISTENT,K_test-J_RAW,PERSISTENT,K_test`,
   `Delta_train=J_COUNT,PERSISTENT,K_train-J_RAW,PERSISTENT,K_train`, and
   `Delta_perm=A_COUNT,PERSISTENT,K_test-A_RAW-PERMAVG,PERSISTENT,K_test`.
   Apply the same two-sided 95% Student-t interval over the ten paired seeds:
   `COUNT_ADVANTAGE` iff the lower bound is above `+0.03`; `EQUIVALENT` iff the
   entire interval is in `[-0.03,+0.03]`; `RAW_SUPERIOR` iff the upper bound is
   below `-0.03`; otherwise `UNRESOLVED`. For the permutation contrast,
   EQUIVALENT or RAW_SUPERIOR maps to `PERMUTATION_CONTAINS`, and only
   COUNT_ADVANTAGE maps to `RESIDUAL_AFTER_PERMUTATION`.
9. **Descriptive permutation diagnostics.** Per seed report the complete-
   population forced-PROBE agreement values `T_perm_count` and
   `T_perm_belief`. They have no threshold, containment, successor, or claim
   authority.
10. **Acquisition and exhaustive attribution.** Per seed compute the frozen
    worst signed margin
    `M=min(Gamma_COUNT,PERSISTENT-0.03, I_COUNT,PERSISTENT-0.03,
    0.02-abs(I_COUNT,REDRAW), 0.02-abs(I_COUNT,SEVERED),
    0.05-(J_BELIEF-DP,PERSISTENT-J_COUNT,PERSISTENT))`. Acquisition support
    requires a one-sided 95% Student-t lower bound on mean `M` above zero,
    every persistent COUNT seed choosing PROBE, every REDRAW/SEVERED COUNT seed
    choosing immediate commitment, and all support and competence gates. After
    that gate, implement the exact ordered seven-branch cross-product map from
    the R03 science card. Successor eligibility is true if and only if
    acquisition is supported and all of `Delta_test`, `Delta_train`, and
    `Delta_perm` are COUNT_ADVANTAGE. Every other cross-product denies
    successor eligibility and retains every applicable attribution label.
11. **Mandatory retained diagnostics.** Retain all seed-level values and
    contrasts, intervals and classes, components/actions, support, competence,
    headroom, normalization and decomposition facts, both descriptive
    agreement values, the exhaustive attribution labels, and the exact
    result-to-action terminal class. No outlier removal, episode-row pooling,
    added seed, checkpoint selection, tuning, retraining, or rescue path exists.

### Complete-only output and activity firewall

The candidate must implement a fail-closed, atomic complete-output protocol:

1. Before completion, evaluator cells, values, components, contrasts,
   diagnostics, interval classes, attribution labels, and successor eligibility
   remain private pending material. They are not emitted to stdout/stderr,
   progress logs, benchmark JSON, engineering state, task messages, dashboards,
   or any user/agent-readable result surface. Only result-blind counts, schema
   booleans, resource measurements, hashes, and synthetic fixture assertions may
   cross the construction boundary.
2. A final package is publishable only after the exact `90`-slot inventory,
   every required `K_test`, `K_train`, DP, RAW-PERMAVG, value/component/action,
   support, competence, headroom, normalization, decomposition, seed-contrast,
   interval, agreement, acquisition, attribution, and terminal-action field is
   present, finite where required, internally consistent, and bound to the
   exact R03 object and checkpoint digests.
3. Publication uses a private sibling pending path and same-filesystem atomic
   replacement. A completion manifest containing schema revision, exact object
   digest, checkpoint inventory digests, required-field inventory, completeness
   digest, and `complete_r03_package=true` is committed last. No partial path,
   per-seed file, checkpoint log, or uncommitted manifest is a result.
4. Missing, duplicate, invalid, nonfinite, or inconsistent mandatory output;
   a normalization/decomposition failure; process interruption; or absence of
   the final atomic completion manifest produces no final package. The exact
   terminal status is a scoped preactivity technical non-completion, never an
   empty, zero, negative, unresolved, partial, or scientific result. Pending
   bytes remain inaccessible and may not be manually assembled or inspected.
5. Question-relevant scientific activity begins only when one complete package
   has atomically emitted every mandatory fact. Once that future package is
   technically valid, every R03 branch is terminal: complete support failure,
   complete competence failure, acquisition/specificity failure, or any of the
   seven attribution branches permits no rerun, seed change, extra episode,
   new panel, checkpoint change, or tuning. Only the science-card preactivity
   classes 1--2 permit a separately authorized unchanged-checkpoint technical
   completion; S2 construction itself grants no such future execution.
6. Malformed input, path traversal, object/checkpoint mismatch, duplicate slot,
   incomplete inventory, and attempted registered materialization in TEST must
   refuse before publication and must leave the result firewall intact.

### Coherent-candidate review and SANCheck fence

A coherent S2 candidate exists only after one assignment-local source/test
change set implements every evaluator and firewall predicate above, all
result-blind construction evidence is current-byte and within caps, the
registered boundary remains unaccessed, and CM can bind the exact changed-path
set and candidate bytes without a known material ambiguity. Until that point:

- Reviewer is prohibited;
- `HMASD-MARL-SANCHECK-V1` is prohibited;
- Verifier and a second routine review are prohibited; and
- no review or SANCheck absence may be treated as a construction defect.

The initial follow-on CM packet ends at either
`S2_COHERENT_CANDIDATE_READY_FOR_REVIEW` or one exact scoped incompatibility.
It does not release Reviewer or SANCheck. A later authority may, only after the
coherent candidate is frozen, release exactly one independent Reviewer for the
single risk cluster of native panel/channel intervention, counter sharing and
private addresses, FP32 reduction, checkpoint resume, evaluator completeness,
and the activity-boundary firewall. Review is advisory and CM retains technical
acceptance. A later current-byte SANCheck must reach `PASS`; one initial check
and at most one bounded CM-directed repair and rerun remain inside the same S2
hard caps. No current packet grants either later step.

### Proxy-only command and resource boundary

S2 construction may use only nonregistered, result-blind compile/static checks,
focused unit tests, and source-bound toy/proxy benchmarks. Before each such
command, CM must record exact argv, cwd, input byte digests, fixture namespace,
estimated wall/core/RSS/scratch/durable/I/O, and the predicate
`registered_master_seeds=false|complete_registered_panel=false|question_relevant_output=false`.
The only writable TEST root is `temp/directions/ucope/test/s2/c1`; no
`temp/directions/ucope/exp/` root, run claim, Operator, or official result
manifest is authorized.

The allowed focused-test surface is the unchanged S0/S1 tests plus exactly
`tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s2.py`.
Any toy/proxy benchmark must use a distinct synthetic namespace, exercise
structural cardinalities and every diagnostic/firewall branch without the
declared master-seed values or registered checkpoint contents, and emit only
technical booleans, counts, timings, resource measurements, and hashes. It may
not emit `J`, `A`, `I`, `D`, `Gamma`, `G`, `M`, a scientific interval/class,
an attribution label, successor eligibility, or any proxy for their registered
values.

Resource accounting is auditable as follows:

- TEST CPU-hours are the sum of user plus kernel CPU seconds for each command
  process tree divided by `3600`; the cumulative total, including the accepted
  pre-S2 upper bound `0.34804809333333336` CPU-hours, must remain at or below
  `6` managed / `12` hard CPU-hours.
- Per-command wall is elapsed monotonic parent time and remains at or below
  `1800` managed / `3600` hard seconds.
- Concurrent process-tree width is at most `16` CPU cores; aggregate live
  process-tree RSS is at most `8 GiB`; maximum live scratch under the TEST root
  is at most `2 GiB`; retained durable TEST evidence is at most `0.75 GiB`;
  and summed process-tree read plus write bytes are at most `8 GiB`.
- GPU and accelerators are forbidden. An unsafe memory plan is reduced,
  batched, or sharded; it is never offered for approval.
- The complete-transaction proxy remains phase-stratified, counts-only, and
  conservative. It may scale measured source-bound toy work only by frozen
  workload counts and directly measured width. It applies no unmeasured worker,
  cross-phase, device, cache, or algorithmic speedup. The current planning
  reference remains `380.2810449061144` seconds,
  `0.10563362358503178` CPU-hours, `515145728` RSS bytes, and
  `2312507074` I/O bytes; none is an S2 observation.
- A current-byte construction return must still project a future complete
  transaction at no more than `1800` seconds, `24` CPU cores, `12` CPU-hours,
  `10 GiB` peak RSS, and `6 GiB` aggregate I/O, with cold compile/load at no
  more than `360` seconds. These are admission gates, not execution authority.
- Any later exact result command estimated above `7200` seconds remains subject
  to one performance-reasonableness review attempt and explicit user approval
  bound to that frozen command and evidence. No exact result command exists or
  is authorized here, so no approval is requested.

### Acceptance criteria

The bounded CM construction tranche is accepted as a coherent-candidate return
only when every item below is true:

1. Every authority ref matches current bytes before work; Root's future short
   assignment is clean at the frozen base; writes stay within the exact
   downstream owned paths; and engineering state keeps its validator-compatible
   scope bound to exact `DIRECTION.md` SHA-256
   `ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d`.
2. One coherent Implementer scope produces the complete finite evaluator,
   mandatory diagnostics, malformed-input refusal, exhaustive attribution map,
   and atomic complete-only package defined above without changing R03 or S1.
3. Current-byte, nonregistered result-blind fixtures cover every evaluator
   cardinality, comparator, diagnostic threshold edge, terminal branch,
   missing-output case, malformed input, atomic publication state, and firewall
   refusal. No registered identity/checkpoint/population or scientific value is
   used or emitted.
4. Every construction command and the current conservative projection satisfy
   the exact command, labor, CPU/wall/core/RSS/scratch/durable/I/O/GPU, memory-
   safety, and no-unmeasured-speedup predicates above.
5. The complete-only firewall proves that no partial package or mandatory
   diagnostic can cross the activity boundary and that only an atomically
   complete, internally consistent future package can become question-relevant.
6. The exact changed-path set and candidate bytes are coherent and current;
   source/test diff outside the owned set is empty; no shared-core change,
   registered access, result command, Operator, Reviewer, SANCheck, provider,
   deployment, flight, push, or integration occurs.
7. Engineering state advances from revision `7` only through expected-revision
   CAS with writer `CM-ucope`, retains `scope_ref` on exact `DIRECTION.md`, and
   records actual S2 engineer-days, cumulative TEST CPU/wall/RSS/scratch/
   durable/I/O, exact changed/test/proxy refs, proxy formula, remaining unknowns,
   and either `S2_COHERENT_CANDIDATE_READY_FOR_REVIEW` or one exact scoped
   incompatibility. Candidate and integrated SHAs remain null unless a later
   packet expressly authorizes a candidate commit.
8. CM returns to EM/Root before Reviewer or SANCheck. Successful construction
   is a technical-admission candidate only, not S2 acceptance, empirical
   authority, a complete R03 package, scientific output, or result release.

### Scoped returns and exact resume conditions

| Return code | Exact scope and evidence | Resume condition |
| --- | --- | --- |
| `S2_AUTHORITY_OR_CAS_CONFLICT` | A frozen path/SHA/revision differs, the create-once artifact was pre-existing, or research/engineering CAS loses its expected revision. | Root publishes a new immutable packet binding the observed current authority and exact expected revision; no old packet is replayed and no artifact is overwritten. |
| `S2_OBJECT_CONTRACT_INCOMPATIBLE` | A conforming evaluator would change a frozen R03/S1 semantic, diagnostic, threshold, comparator, FP32, RNG, checkpoint, attribution, activity-boundary, or claim rule. | EM-ucope receives a new owner-authorized coherence packet after Portfolio records any required science/allocation decision; CM does not substitute an object. |
| `S2_COMPLETE_OUTPUT_FIREWALL_INCOMPATIBLE` | Partial/missing/invalid output cannot be kept inaccessible or atomic completeness cannot be proven on result-blind current bytes. | CM returns exact changed paths, failing fixture/transition, and observed leak surface; EM freezes a new immutable firewall correction before any retry. No partial value is inspected or adopted. |
| `S2_REGISTERED_BOUNDARY_ATTEMPTED` | Any command or code path requests a registered master seed, checkpoint, complete panel, question-relevant field, result root, claim, or Operator. | Stop before launch when possible; otherwise Root invokes Effect-scoped recovery from exact observed facts. A new packet must bind the reconciled state and a distinct command if one is ever authorized; no replay occurs. |
| `S2_RESOURCE_ENVELOPE_INCOMPATIBLE` | S2 exceeds 6 hard engineer-days, cumulative TEST exceeds 12 CPU-hours, any TEST exceeds 60 minutes, or a core/RSS/scratch/durable/I/O/GPU/1800-second projection gate fails. | CM returns actual measurements and the minimal safe reduction/batch/shard alternative. Portfolio must explicitly revise authority to enlarge any envelope; this request never does so. |
| `S2_COHERENT_CANDIDATE_NOT_REACHED` | The bounded construction ends with an implementation/test ambiguity or source-local defect but no registered/result activity. | CM returns exact source/test refs, actual cost, unresolved predicate, and smallest same-object repair. Root may reconcile only a new packet whose scope and remaining caps cover that repair. |

None of these returns is a negative R03 result or a direction-wide bare
`BLOCKED` disposition.

## Explicit non-scope

This request and its initial follow-on CM packet do not authorize:

- registered master seeds, registered checkpoints, the complete registered
  training/evaluation panel, empirical identity or coordinate materialization,
  question-relevant output, partial values, a complete R03 package, scientific
  interpretation, or any result-bearing command;
- `scripts/hmasd_run.py` prepare/execute, an Experiment Operator, run claim,
  `temp/directions/ucope/exp/` output, result manifest, provider operation, or
  external Effect;
- Reviewer, Verifier, `HMASD-MARL-SANCHECK-V1`, technical acceptance, empirical
  release, result intake, deployment, or flight before a coherent candidate;
- retraining, tuning, added/dropped seeds, changed checkpoints, new panels,
  changed periods, changed thresholds, changed diagnostics, rescue runs, or a
  second scientific transaction;
- modification of `DIRECTION.md`, Portfolio, registry, research authority other
  than the expected-revision state CAS, R03 through R06 artifacts, S1 acceptance,
  terminal runs/evidence/worktrees, external-review authority, scripts, shared
  core, or any UCOPE source/test path outside the downstream owned set;
- a second Implementer, split implementation ownership, candidate push,
  integration, shared-core Git change, manager-task creation, or direct task
  dispatch by EM; or
- treating S1 metrics, a toy fixture, proxy counts, a timing, a resource
  projection, missing output, or construction failure as an S2 speedup,
  scientific answer, partial result, or successor decision.

This artifact creates no task, worktree, Implementer, Reviewer, SANCheck,
Operator, command, claim, run, source/test change, Git action, provider action,
deployment, flight, scientific result, or Effect. Its follow-on CM packet has
`effect_refs=[]`. Root owns canonical task/worktree orchestration; CM owns only
the later bounded construction; EM retains scientific acceptance authority;
Portfolio retains any later empirical-investment decision.
