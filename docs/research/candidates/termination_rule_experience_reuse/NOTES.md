# Termination-rule experience reuse

## 2026-09-20 — A01: fixed-skill off-termination learning in an asynchronous service team

**State and authority.** Owner-selected direction A, lead Codex DM
`/root/dm_termination_reuse`, author checkout `/home/fires/.codex/worktrees/fsd-a/hmasd-wsl`,
branch `codex/termination-rule-experience-reuse`, initial source `45945dd7f`.
The owner pause is lifted. I have read and adopted constitution section 3 as amended on
2026-09-20: fits record cost, with no allowance, balance, refund or reset. Old allowance
wording in loaded role/scientific/engineering methods is superseded. Arms, horizons and
seeds remain prospective; a technical failure is not a scientific negative and a retry
is a new recorded decision. This branch's active/lead row is not yet canonical main;
Root owns that integration dependency. No result-bearing execution until it is canonical
and native admission passes. Reading, design, isolated implementation and correctness
tests proceed. No shared RESEARCH, Claude B08 or team-termination checkout edits.

### Evidence, source bridge and present explanation

The owner proposal asks whether observations under one termination rule can teach values
for another. Low-level skills and the teammate policy will be fixed. The learned object
is the focal agent's high-level skill value/choice, not a learned termination gate.
Changing both teammates' policies/termination laws is outside this first comparison.

Primary literature checked: Harutyunyan et al., *Learning with Options that Terminate
Off-Policy*, AAAI 2018, DOI 10.1609/aaai.v32i1.11740,
[publisher PDF](https://ojs.aaai.org/index.php/AAAI/article/view/11740/11599), sections
4.3–4.4, Algorithm 1, sections 5–6 and Discussion. The target TD bootstrap mixes continued
option value and reselection value using target beta. Its trace uses that option's target
continuation probability, stopping at a sampled behavior termination. Distinct option
action distributions require an additional correction; section 4.4 does not solve that
combined problem. The paper proves properties of an expected operator, explicitly leaves
online convergence open, and reports that a plain off-policy comparator performs comparably
in Pinball. Thus this is an established starting point, not our algorithm or a promise of
MARL performance. Local Inst-sci catalog title/Retrace search returned no match; this says
nothing about the complete library or novelty. The verified publisher copy supplies the
needed source.

Ordinary comparator source: Munos et al., *Safe and Efficient Off-Policy Reinforcement
Learning*, NIPS 2016,
[paper](https://papers.nips.cc/paper/2016/file/c3992e9a68c5ae12bd18488bc579b30d-Paper.pdf),
general return operator and Retrace coefficients. We use bounded per-transition ratios in
the actual option-transition kernel. This is a standard augmented-state application, not
a novel joint-policy correction.

Closest local evidence read:

- SCDMP [B01 result](../semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_RESULT_EVIDENCE_20260909.md)
  and [B02 interpretation](../semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B02_INTAKE_20260910.md):
  residual-MC minus intact MC was +.006737 and +.003658 in two fitted pairs, each read
  WITHIN by its original rule. Nonempty loss exposure and learner movement did not establish
  useful package improvement. Those were opening-held, MC-anchored regularization tests,
  not cross-termination data reuse. We retain their native/proxy and small-n limits without
  reviving their coefficient or batch.
- Read-only team-termination notebook at `1d3091830`, final two sections (12:05 and 12:50
  UTC): held labels need behavioral content; optional END differs from a fresh label draw
  or actual behavior change. That work owns learned J/I gates on an accepted FSD foundation.
  A uses an explicit independent skill library and does not wait for B08 or establish any
  property of current HMASD learned labels. Its obsolete fit-balance language was explicitly
  superseded in its second section and is not inherited here.

**Working judgment.** There is a well-defined learning problem when the teammate's current
commitment is part of the Markov state and the teammate law is unchanged. That reduction
already permits ordinary multistep off-policy learning; a special team correction has not
earned its complexity. We first compare the two principled existing routes directly.
Task opportunity, learning improvement, and UAV/package value remain unmeasured. No score,
learnability prerequisite, theorem proof or headroom claim is asserted by this design.

### Direct comparison and information rights

Use an independent, fully observed **two-agent service line**, not Scenario1. Five positions
0–4 have service sites at 0 and 4. Each skill is an immutable closed-loop controller:
move one cell toward its named site from the current position, then stay. Skill labels
therefore specify feedback behavior, not a copied command. Shared reward after both moves
is .7 for coverage of the currently high-demand site and .3 for the other site; duplicate
coverage gives no extra reward. Demand flips with probability .12 per tick. There is no
switch charge or reward for preserving a skill.

The teammate renews every four ticks, choosing the current high-demand site with probability
.85 and the other with .15. Its physical motion, choice law and clock are identical in
collection and target evaluation. At initialization its remaining commitment is uniform
1–4; positions, demand and held teammate skill are sampled independently. The focal agent's
behavior termination probability is zeta=.125 after every transition, with uniform skill
reselection; the target beta=.5 is fixed. Both choices have positive behavior support.

The legal common state is `(focal_position, teammate_position, demand, teammate_skill,
teammate_remaining)`: 400 states and 2 focal skill values per state. A learner sees no
future demand, termination draw, teammate draw or evaluation outcome. A transition moves
under both current skills, computes reward under current demand, then updates demand and
the teammate countdown/renewal. Focal termination/reselection follows that transition.
The full teammate state is retained even at an unexpired commitment. Its unchanged
conditional transition law cancels in the focal off-policy ratio; omitting it is not a
claim to have corrected the joint process.

All arms learn the same 800-entry float64 Q table from identical, independently seeded
behavior episodes, with greedy target skill selection and uniform tie-breaking:

| Arm | Update | Role |
| --- | --- | --- |
| `one_step` | One-step expected intra-option TD with the target beta bootstrap | Simple same-information reference; no deliberately incorrect SMDP discount |
| `qbeta` | Truncated forward Q(beta) return, stopped at actual behavior terminations including same-label redraw | Direct established off-termination method |
| `retrace` | Generic Retrace over the augmented option-transition MDP, allowed across actual reselections | Strong ordinary multistep primary comparator |

For all arms, `V_beta(x', o) = (1-beta) Q(x', o) + beta max_v Q(x', v)` and
`delta_t = r_t + gamma V_beta(x_next, o_t) - Q(x_t, o_t)`.
Let `K_target(v|x,o) = (1-beta) 1[v=o] + beta mu_Q(v|x)` and
`K_behavior(v|o) = (1-zeta) 1[v=o] + zeta/2`. Retrace uses
`c_t = min(1, K_target(o_t|x_t,o_previous)/K_behavior(o_t|o_previous))` with lambda=1.
Q(beta) uses `c_t = 1-beta + beta mu_Q(o_previous|x_t)` if no actual behavior renewal
occurred, otherwise zero. Coefficients multiply only later TD residuals; neither method
appends observed continued rewards as an uncorrected post-termination counterfactual.
The same-label renewal flag is recorded separately from skill identity.

Use gamma=.95, alpha=.15, maximum eight-step chunks, frozen Q inside each chunk, and one
mean update per visited state/skill in that chunk. Every arm processes the same start rows,
chronological chunk partition and one pass. A 96-tick episode is a collection truncation,
not an absorbing task terminal: its last transition bootstraps and its trace then stops.
This is a continuing-value learner evaluated on a fixed 96-tick service panel, not an
exact finite-horizon optimal controller. There are no learned recurrent states, normalizers,
neural skill weights, privileged critic inputs or cross-arm checkpoint selection.

**Predictions and losing outcomes.** At a common Q, Retrace retains at least as much trace
weight on a behavior-continuation suffix as Q(beta), and can use supported transitions
across reselection. This predicts greater effective trace mass and faster useful learning,
not merely more generated labels. The primary exploratory native reading is the mean
service J at fixed training checkpoints 32, 128 and 512, Retrace minus Q(beta); final J
and each checkpoint remain separately visible. Expect a positive primary and no consistent
final loss; compare each learner's movement from zero and initial J, and retain one_step
even if it wins. A trace-mass increase without native benefit weakens practical value of
longer reuse at this exposure. A one_step advantage favors the simple route here; it is
not repaired by silently raising a horizon. A Q(beta) advantage would weaken our presumed
utility of crossing renewal boundaries, without disproving the generic estimator. Three
seeds still need an uncertainty-aware reading and do not establish equivalence from a
small mean. No special MARL correction or UAV claim follows from either ordering.

The reduction preserves nonadditive team coverage and asynchronous held teammate behavior.
It removes learned teammates, changing skill policies, partial observability, communication,
interference and arbitrary changes to both agents' termination laws. A positive result
can justify a subsequent new question on those couplings; it cannot stand in for it.

### Prospective cost and outputs

One batch, three arms times training seeds **91021, 91022, 91023 = nine planned fits**.
Each fit processes 512 behavior episodes × 96 ticks = 49,152 training team transitions,
6,144 chunk update calls and 49,152 target start rows. All Q tables initialize at zero.
These seed blocks pair the exact behavior data and address evaluation randomness by
episode/tick, while blocks are independent. Four panels at 0, 32, 128, 512 episodes each
use 64 fresh evaluation worlds × 96 ticks. Totals: 442,368 training and 221,184 evaluation
team transitions; 55,296 chunk update calls; nine fits. Evaluation makes zero updates.
The cost is chosen to expose early and later learning in a small tabular state space across
three independent blocks, with a real one-step alternative; it is not an allowance.
No tuning, selected checkpoint, automatic retry or additional seed is included.

Use configured **local_linux CPU**, serial fits, one numerical thread; this small NumPy
host needs no GPU and does not occupy the shared wsl_4070. Peak memory and full fit wall
are not yet measured; expected storage is only a few MB per fit, with no claim of a measured
speedup. Fresh actual-node admission still applies. Each fit writes config/source/admission,
status and summary JSON, all evaluation rows/curve, the behavior transitions with renewal
flags and teammate state, final Q/visits, update/trace/support diagnostics, and measured
wall/CPU/RSS scope. Runner failure preserves partial output and a failed status. Unit
tests below are correctness fixtures, not this learning batch or result evidence.

### L0 — implementation and checks

Deliver `experiments/candidates/termination_rule_experience_reuse/off_termination_a01/`
with the immutable service dynamics, addressed data/evaluation streams, three tabular
updates and artifact-producing study; entry `scripts/run_termination_reuse_a01.py`.
Own matching tests under `tests/experiments/candidates/termination_rule_experience_reuse/`.
No shared learner/environment/launcher changes. The entry calls native `require_admission`
before training, evaluation, creating output or constructing a scientific environment.
Source SHA must match admission. Artifact roots are fresh and refuse overwrites.

Protect: actual remaining teammate commitment; separation of renewal/changed label;
target versus behavior kernel; exact supported-ratio denominators; no fictitious suffix;
trace indexing; chunk-frozen Q; correct truncation bootstrap; isolated train/eval randomness;
same data and update start rows across arms; output counts and parameter movement.
Focused hand-computed tests cover these semantics, an independent forward-return
calculation, and the guarded CLI/summary schema using fixture work under pytest temp/.
Independent Reviewer is required because learner targets and result identity have
scientific meaning. DM implements and accepts locally; any delegated review is read-only,
has no index ownership, launches no result and spawns no child. Stop only the dependent
action for a concrete conflict. Launch preparation does not bypass the canonical-index
dependency recorded above.

## 2026-09-20 — A01 pre-execution scientific criticism and adopted correction

The independent ResearchCritic `/root/dm_termination_reuse/a01_science_critic` verified
the primary Q(beta)/Retrace passages and returned **MATERIAL_DISSENT: yes** on a precise
aggregation defect in the first L0. I accept the finding before any result or score.
The earlier per-state/skill mean divided by that entry's realized chunk visit count;
that denominator depends on future transitions. A two-step hand example at the true
one-step value has nonzero expected update under this rule. This would have changed the
ordinary estimator we intended to compare.

**Superseding update convention:** fixed eight-row chunk, frozen Q, sum return increments
for each state/skill and divide by the fixed chunk length, **alpha=1.0** for all arms.
Thus each start row has weight 1/8, and an entry repeated in every row has aggregate
weight at most 1. This replaces alpha=.15 and the random per-entry denominator in the
original entry. It is an outcome-blind definition of a conventional batch mean, not a
score-driven learning-rate selection; all exposure, seeds, arms and endpoints are unchanged.
The hand counterexample and an independent forward-sum computation are correctness tests.

The critic also identified over-attribution in the proposed losing-outcome paragraph.
Retrace changes both continuation weights and renewal-boundary crossing. A Q(beta)
advantage would therefore weaken the practical value of this whole Retrace implementation
at the declared exposure, not identify boundary crossing as the cause. Likewise a Retrace
advantage may reflect ordinary return propagation or effective update magnitude. Common-Q
trace-mass dominance is algebraic; actual arm-specific trace masses need not remain ordered
after Q tables diverge. We retain the direct estimator-package comparison and no extra
attribution arm. A renewal-cut Retrace control would be a later prospective question only
if that attribution becomes useful.

The exact state reduction is now explicit: augmented state `(x, previous_option)`, action
`executed_option`; after that action the previous option has no physical effect, so sharing
`Q(x, executed_option)` across previous-option copies is exact for these memoryless skills.
The teammate law cancels conditionally, not because its marginal trajectory is unchanged.
These checks clarify the representation; there is still no empirical learning observation,
no resolved native ordering and no new claim of online convergence.

## 2026-09-20 — A01 implementation prepared; result execution still pending

DM implemented the declared small host, tabular return schemes, guarded entry and output
contract directly in this isolated checkout. Focused scientific-interpreter checks passed:
`python -m pytest -q tests/experiments/candidates/termination_rule_experience_reuse/off_termination_a01/test_a01.py`
— **16 passed in .25 s**. The cases include the critic's fixed-point counterexample,
independently expanded forward returns, renewal-versus-label identity, supported marginal
ratios, changed-option residual indexing, actual teammate countdown, truncation bootstrap,
evaluation/RNG isolation, output hashes/counts/failure preservation, and refusal before
scientific output when native admission is absent. `git diff --check` passed. Tiny
pytest fixtures produced no A01 scientific result or performance selection and were
automatically cleaned by the repository scratch lifecycle.

The implementation is prepared, not yet independently engineering-reviewed or scientifically
executed. Review will inspect the accepted estimator correction and result identity/guard.
Root still owns canonical active/lead integration; no result launch or run handle exists.
The current judgment is unchanged: ordinary off-policy methods may already suffice under
the declared fixed teammate reduction; the proposed native ordering remains unmeasured.

## 2026-09-20 — A01 independent engineering review accepted; canonical-index dependency

Published inputs: `ec3f7ee0fbbce7dcfe7d0bef620d5722feb2d3d7` on
`origin/codex/termination-rule-experience-reuse`. Independent Reviewer
`/root/dm_termination_reuse/a01_engineering_review` read the committed diff and contract,
traced CLI/admission/source binding, collector, return/update, evaluator and artifacts,
and independently ran the focused suite: **16 passed in .16 s**. It found no material
executable defect and requested one prospective wording clarification. I accept the
implementation and its checks; the Reviewer does not own the scientific decision.

**Evaluation-panel clarification, before any result:** each block has **64 worlds fresh
relative to training**, reused at all four checkpoints and across all three arms in that
block. The word "fresh" in the original entry did not mean 64 new worlds per checkpoint.
This common panel is exactly the addressed RNG scheme and existing test; no code, seed,
world, endpoint or selection rule has changed. There are 192 distinct evaluation worlds
across the three independent blocks, executed 12 times each (four checkpoints times three
arms), for the declared 221,184 evaluation team steps. Checkpoints/episodes are nested
within three independent training blocks, not extra training samples.

Similarly, each block's 512 behavior episodes is identical across its three arms. There
are 147,456 unique seeded behavior transitions across the three blocks, generated and
processed three times for the declared 442,368 executed training team transitions. Data
reuse across comparison arms matches the sample exposure; repeated generation remains
part of measured work and is not an efficiency claim. Different arms' target arithmetic
and resulting update magnitudes remain package differences.

No A01 result-bearing fit, evaluation, accepted operation or live observer exists. The
tiny correctness fixtures establish implementation behavior only. Current state is
exploring, implementation accepted, native learning comparison unread/unrun. The sole
current execution dependency is Root's confirmed integration of the A active/lead row
into canonical main and the live canonical checkout, followed by native admission on
local_linux. Re-entry is that integration notification; no recurring check or extra
approval of ordinary science is requested. Keep the batch fixed and preserve any eventual
admitted handle. Nothing here grants a result claim or changes another direction.

## 2026-09-20 — A01 compatibility, launch-interface checks and result-reading preparation

Direction remains **exploring**, with the fixed A01 comparison as the next scientific
action. Root integrated the accepted code and review note at
`origin/codex/fsd-parallel-root@2640d7fcaa0cee30077d597b8d243ef2b035726b`. A path-limited
diff verifies byte identity with A's `0bc787070` on all seven owned files. Published main
has advanced to `eaa1401c97d5fd068f94d862656b08a640555e03`; relative to A's base, it
changes none of A's governing constitution/methods, compute configuration, launcher,
admission/resource code or test scratch contract. No compatibility repair or source
rebase is needed for this independent NumPy host. No B08 result was consulted.

Both CLIs parse their documented `--help` interface. A read-only call to the launcher's
runner/output resolver and guard-contract checker accepts the actual A01 entry, direction,
source SHA argument and first declared output path, which does not exist. This is an
interface check, not a launch, fresh-memory admission or accepted operation. Additional
existing control-plane regressions passed under the configured science-tools interpreter:
**11 passed, 42 deselected in 2.45 s**, selecting new-runner guarding, direct refusal,
snapshot isolation/output placement, successful detached fixture admission, stable claim
identity, duplicate rejection and missing/expired/mismatched admission. Their repositories,
detached children and outputs were test fixtures under pytest-owned scratch; they do not
create an A01 process or scientific result. No production memory check was substituted by
the fixture's memory data.

The concrete current dependency was checked using the native **read-only local policy
function**, against `/home/fires/hmasd-wsl` and expected lead `Codex DM`. It returned:
`LaunchRefusal: direction 'termination_rule_experience_reuse' must appear exactly once in the Active table`.
Fresh `git ls-remote` confirms the canonical published main above and the published A
source `0bc7870700e7d9ce0cd5846b0bd2987150df1ea9`. Root owns integration of the A row into
published `origin/main` and coordination of the actual canonical checkout's matching
RESEARCH content. The pause must remain lifted and the lead cell must remain `Codex DM`;
a changed assignment is a conflict to reconcile, not a string to silently substitute.
After Root supplies that integration fact, DM performs actual-node admission and executes.

The selected result source remains the already published, reviewed
`0bc7870700e7d9ce0cd5846b0bd2987150df1ea9`; this continuation entry changes no executable
input, cost or endpoint. Planned tags are `a01_<arm>_<seed>_20260920`, for arms
`one_step`, `qbeta`, `retrace` and seeds `91021`, `91022`, `91023`. Execute serially in
seed-major order, with that arm order inside each seed. Preserve each returned manifest
and terminal witness before proceeding. The first command, **prepared and not executed**, is:

```sh
/home/fires/.venvs/hmasd-linux-science-tools/bin/python scripts/hmasd_launch.py launch \
  --node local_linux \
  --source-root /home/fires/.codex/worktrees/fsd-a/hmasd-wsl --snapshot \
  --direction termination_rule_experience_reuse --lead 'Codex DM' \
  --sha 0bc7870700e7d9ce0cd5846b0bd2987150df1ea9 \
  --output runs/termination_rule_experience_reuse/a01_one_step_91021_20260920 \
  -- scripts/run_termination_reuse_a01.py --arm one_step --seed 91021 \
  --out runs/termination_rule_experience_reuse/a01_one_step_91021_20260920 \
  --launch-sha 0bc7870700e7d9ce0cd5846b0bd2987150df1ea9
```

The configured child is `/home/fires/.venvs/hmasd-linux-cpu/bin/python`. Actual local
physical/effective available memory must meet the unchanged 4 GiB native floor immediately
before release. The check is intentionally left to the actual launch; an earlier snapshot
would not admit it. Local CPU resources remain shared even though this batch uses no GPU.
On uncertain acceptance, reconcile the same native manifest/operation; do not change the
tag or relaunch. No accepted handle currently exists.

**Collection and reading are ready, not performed.** Snapshot output stays under this
author checkout's `runs/termination_rule_experience_reuse/<tag>/`, not the snapshot tree.
No remote copy is needed. Read in this order:

1. Reconcile native manifest, launch status and `process-exit.json`, then runner status.
   A missing/contradictory exit remains unknown. Preserve each failure and any partial files.
2. Validate the recorded source/config and all artifact hashes. Per completed fit require
   512 training episodes, 49,152 training team steps, 6,144 tabular update calls, 49,152
   target start rows and visit-count sum, 256 evaluation episodes, 24,576 evaluation team
   steps and zero evaluation updates. Read Q movement and actual support/renewal records.
   Different numbers of unique table entries written are not extra start-row exposure.
3. Reconstruct checkpoint J from all `evaluation.jsonl` reward sums divided by 96, and
   primary from the fixed 32/128/512 checkpoint means. Compare within-block behavior
   arrays exactly across arms, independently of archive-container hashes. Read all
   checkpoints, final Q/visits and per-update trace/ratio diagnostics; do not reexecute a
   model, environment or trajectory merely to collect this evidence.
4. Report each of the three paired Retrace-minus-Q(beta) primary differences, their
   mean/range, each final difference, both comparisons with one_step and training-relative
   changes from the untrained panel. A descriptive paired Student-t interval, if shown,
   uses the three block differences (df=2, approximate normal block-difference assumption),
   never the evaluation episodes as n. With only three exploratory blocks it is fragile;
   neither interval crossing zero nor a small mean establishes equivalence. An incomplete
   pair is absent, not zero, and is not silently replaced.
5. Compare the intermediate trace-mass/support prediction with native J while retaining
   the package-attribution limitation adopted above. Lower Q error is not measured here;
   TD residual magnitude is not relabelled as value error. Interpret task opportunity,
   finite learning, and additional useful complexity separately. In particular, success
   of ordinary Retrace can favor using the simple existing route without creating an
   algorithm-novelty or current-HMASD skill claim.

Per-fit recorded wall is entry-to-summary-assembly, with whole-process CPU/RSS at that
point; interpreter startup and final summary/status publication are outside that wall
field. Native acceptance/exit timestamps supply their own scope, not exact compute time.
There is no complete-path speed claim. Preserve this timing limit when reporting summed
fit walls versus batch elapsed time. All fits stay fixed while the batch is being read;
any next learning batch requires a new prospective scientific reason. If only estimator
ordering is resolved, choose the next action for the remaining question rather than add
an automatic control, new architecture or seed. Current scientific judgments remain
unresolved because no A01 score exists; direction ownership and continuation stay with DM.
