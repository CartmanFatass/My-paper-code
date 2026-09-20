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

## 2026-09-20 13:48 UTC — A01 execution begins after canonical registration

Root reports the owner's explicit authorization to register and continue worthwhile A/B/C
experiments without per-batch approval. I verified published `origin/main` and the actual
canonical checkout `/home/fires/hmasd-wsl` both at
`b254ed1ea86cf8c39d925d87ded4fee368c5e0a1`, with pause lifted and A's active lead exactly
`Codex DM`. The earlier missing-row dependency is resolved. A's loaded constitution,
scientific/engineering methods, compute and admission/launcher dependencies remain
byte-identical to the versions already adopted. The local node reports about 11 GiB
available memory; this is planning information, not the fresh native admission itself.

Root requested the latest reviewed direction source including the compatibility/reading
preparation. Therefore the previously proposed `0bc787070` launch source is superseded
before any accepted operation: use the published commit containing this execution entry,
whose full SHA will be bound in every native manifest. An executable/test-path diff against
reviewed `ec3f7ee0f` is empty. Only notebook entries have changed; there is no code/config,
arm, seed, horizon, alpha, evaluation-panel, endpoint or planned-cost revision. This is
not migration, rebind or retry of accepted work: there are no A01 handles yet.

Proceed with the fixed nine fits on local_linux, serial seed-major/arm order as declared.
DM retains direct launch/observation/collection responsibility. Native manifest links and
the eventual result reading will be appended below; technical exit alone will not end
the scientific work. No additional learning batch is selected by this activation entry.

## 2026-09-20 — A01 read: ordinary multi-step reuse works; longer Retrace traces add no clear gain

All nine declared fits were natively admitted on local_linux at source
`63b0ca73a212344d653ea8c3e5d0ae271ef10c29` and exited zero. DM directly retained and
reconciled every handle; no failure, retry or observer transfer occurred. Native manifests
and all runner outputs are in the following directories (each contains
`launch-manifest.json`, `process-exit.json`, `config.json`, `summary.json`, underlying
behavior/checkpoint arrays and full update/evaluation rows):

| Seed | one_step | qbeta | retrace |
| --- | --- | --- | --- |
| 91021 | [run](../../../../runs/termination_rule_experience_reuse/a01_one_step_91021_20260920/launch-manifest.json) | [run](../../../../runs/termination_rule_experience_reuse/a01_qbeta_91021_20260920/launch-manifest.json) | [run](../../../../runs/termination_rule_experience_reuse/a01_retrace_91021_20260920/launch-manifest.json) |
| 91022 | [run](../../../../runs/termination_rule_experience_reuse/a01_one_step_91022_20260920/launch-manifest.json) | [run](../../../../runs/termination_rule_experience_reuse/a01_qbeta_91022_20260920/launch-manifest.json) | [run](../../../../runs/termination_rule_experience_reuse/a01_retrace_91022_20260920/launch-manifest.json) |
| 91023 | [run](../../../../runs/termination_rule_experience_reuse/a01_one_step_91023_20260920/launch-manifest.json) | [run](../../../../runs/termination_rule_experience_reuse/a01_qbeta_91023_20260920/launch-manifest.json) | [run](../../../../runs/termination_rule_experience_reuse/a01_retrace_91023_20260920/launch-manifest.json) |

**Collection acceptance.** Independently read JSON/NPZ without importing the learner or
executing a trajectory. Reconciled each native runner identity/exit with its manifest,
source/config, every declared artifact SHA256, all counts and final finite Q/visit shapes.
Reconstructed service rewards from recorded old demand and next positions, behavior
probabilities from observed option changes, each of the 2,304 evaluation episode scores,
all curve means and the declared primary. Behavior arrays match exactly across arms within
each seed. All checks pass. Each fit has 49,152 training and 24,576 evaluation steps,
6,144 tabular update calls and 49,152 target rows/visits, with zero evaluation updates.
The three blocks visit 666, 640 and 656 of 800 table entries, identically across arms;
the unvisited entries do not become evidence about unsupported states.

**Observed native service J.** Primary is the prewritten equal mean of checkpoints
32/128/512; no checkpoint or execution-mode choice was made after observing results.

| Seed | one_step primary | Q(beta) primary | Retrace primary | Retrace − Q(beta) | Retrace − one_step |
| --- | ---: | ---: | ---: | ---: | ---: |
| 91021 | .71171332 | .72570530 | .72479926 | −.00090603 | +.01308594 |
| 91022 | .70009223 | .71195747 | .71357964 | +.00162218 | +.01348741 |
| 91023 | .70439453 | .71429579 | .71360677 | −.00068902 | +.00921224 |

Mean primary Retrace minus Q(beta) is **+.00000904**, with descriptive paired t interval
**[−.00347179, +.00348988]** (three independent blocks, df=2, approximate normal-difference
assumption). Its final differences are **−.00026042 / +.00667318 / −.00222982**, mean
**+.00139431**, corresponding interval **[−.01022270, +.01301133]**. These are mixed,
small exploratory estimates, not an equivalence result or evidence of stable superiority.

The ordinary one-step reference is a real learner: mean initial J is .57548828 and its
mean final J is .70976563; all three blocks improve. Q(beta) and Retrace final means are
.74343533 and .74482964. Retrace's final advantages over one_step are
**+.03704427 / +.04005534 / +.02809245**, mean **+.03506402**; its primary advantage is
**+.01192853**, descriptive interval [.00606366, .01779340]. Q(beta)'s primary/final
advantages are likewise positive in all three blocks. The curves retain the timing:
at 32/128 episodes the methods are close; the larger multistep advantage appears at 512.
This is finite-exposure exploratory learning evidence on this small host, with no claim
about tuned optimality, general superiority, current HMASD skills or UAV service.

**Intermediate prediction and changed judgment.** Retrace's discounted trace mass is
3.29344 / 3.30886 / 3.29157 versus Q(beta)'s 2.90108 / 2.93005 / 2.90295. It retains
2,997 / 3,010 / 3,069 actual renewal edges inside chunks; Q(beta) correctly retains none.
Thus the implemented extra reuse is active. Retrace also has larger mean squared return
increments (about 5.50–5.57 versus 5.13–5.18), not a measured reduction of estimator
variance or value error. Raw ratios reach 8 and are clipped as specified. Both state
support and actual learner movement are present; the missing clear Retrace advantage
cannot be explained by a dormant extra trace or a nonlearning one_step comparator.

The point-mean primary has the predicted positive sign by only .000009, while two of
three differences are negative. I do not credit that arithmetic sign as the anticipated
useful native consequence. The prediction of additional practical value from longer
Retrace propagation is weakened at this exposure. The result supports using established
multistep target-termination learning in the observed fixed-teammate reduction, and gives
no empirical reason to add a special team correction or attribute a gain to crossing
renewal boundaries. It leaves the *choice of behavior termination for collecting data*
untested: A01 used the same zeta=.125 in every arm. It also leaves simultaneous changes
to teammate laws, hidden commitments and learned skills untouched.

**Cost.** Nine started/completed fits; 442,368 executed training plus 221,184 evaluation
team steps and 55,296 tabular updates. Summed entry-to-summary wall is **11.851759 s**;
first native acceptance to last exit spans **234.149267 s**, including intervening serial
launch/staging waits. The first launch's preceding staging is outside that latter span.
Maximum observed single-process peak RSS is **41,028 KiB**, not a simultaneous sum.
Preserved output occupies about 28 MiB. Timing scopes and excluded final publication remain
as declared; no end-to-end speedup is inferred from these numbers. All outcomes stay kept.

**Next scientific action selected.** Retain ordinary Retrace as the standard implementation,
not as a discovered winner over Q(beta). Do not tune alpha, extend A01 or add an attribution
arm. The useful unresolved question is whether long behavior commitments actually help
target-policy learning compared with collecting under the target termination frequency.
That changes collection and state/option coverage, which A01 did not test, and can falsify
a central practical motivation for off-termination reuse without inventing an algorithm.

## 2026-09-20 — A02 prospective comparison: long behavior versus matched termination

One question: with **the same ordinary Retrace learner and fixed target beta=.5**, does
behavior zeta=.125 improve finite-interaction target J relative to **zeta=.5**? The latter
is the competent matched-termination reference. Its option choices are still uniform
during collection, so it is clock-matched, not on-policy with the learned greedy selector.
All skill dynamics, teammate law/countdown, information, table, gamma=.95, fixed-chunk
alpha=1.0, eight-row chunks, initial distribution and greedy target evaluation remain A01.

Arms `long_behavior` (zeta=.125) and `matched_termination` (zeta=.5), both using Retrace.
Three **fresh** blocks **91031, 91032, 91033**; **six planned fits**, each 512×96 training
ticks and four 64×96 evaluation panels at 0/32/128/512. Planned totals: **294,912 training
and 147,456 evaluation team steps; 36,864 tabular updates**. Fixed target evaluation worlds
are paired across arms/checkpoints within each fresh block. Behavior uses the same addressed
exogenous random draws in each pair, but different termination laws mean different observed
option/state trajectories; these must not be asserted identical. The joint initial/data
randomness varies independently across blocks. No A01 seed or selected checkpoint is reused.
Local_linux CPU, serial seed-major/arm order, same admission/collection rules. Six fits are
chosen for a two-law paired comparison across three new data blocks, not an allowance.

The primary is long-minus-matched mean J over the same three nonzero checkpoints; retain
all curves/final contrasts and block-level uncertainty. Expect longer behavior options to
produce more persistent primitive paths and more boundary/endpoint occupancy, potentially
helping delayed return propagation; this also risks worse coverage of alternative mid-path
choices. The **falsifiable native conjecture is a favorable primary across these blocks**,
not a guarantee from longer traces. Record actual termination/label-change counts, visited
state-option support, endpoint/interior occupancy, trace mass and native J from the existing
artifacts. These are descriptions of a collection-law package, not causal mediation or an
assumed larger trace-mass ordering. A01's mixed extra-trace result lowers confidence in a
simple "longer trace implies better J" explanation.

If long behavior loses or has no useful consistent gain, prefer matched-termination
collection when a fresh choice is available, while retaining off-termination learning for
already existing long data. That would weaken the claim that long commitments should be
chosen to save learning cost, not falsify their lawful reuse. If it helps, retain the
bounded collection-law observation and distinguish coverage/exploration from return
estimation. Neither outcome licenses a new gate, a joint-teammate-correction claim or a
UAV novelty claim. This is a new prospective collection-law question after A01 has been
read, not extension or renaming of its failed incremental-estimator prediction.

**L0 for one bounded behavior change.** Add A02's fixed `--arm/--seed` guarded runner
`scripts/run_termination_reuse_a02.py` and small study wrapper under
`experiments/candidates/termination_rule_experience_reuse/behavior_clock_a02/`. Reuse A01's
actual dynamics/learner and artifact producer. Add an optional per-call object identifier
to the shared experimental `run_study` if needed, preserving A01's default and frozen
source. Arm identity in artifacts must name long/matched while explicitly recording
learner `retrace`; do not overload the existing learner-arm field ambiguously. Either
separate run label from learner name through a minimal argument or make this explicit in
the A02 wrapper. No table/update/data/evaluation semantics change beyond the declared
collection zeta. Preserve actual conditional behavior probabilities (.9375/.0625 versus
.75/.25), ratio construction and isolated random streams.

Implementer owns only that executable wrapper/entry, the minimal shared experimental
producer interface change and matching correctness tests in its separate assigned checkout;
DM owns this notebook and accepts the diff. Tests must cover both fixed laws, artifact
identity and unchanged A01 default, action-kernel support, source guard and count contracts.
No scientific run, seed/horizon choice, notebook edit, shared index or child delegation by
Implementer. An independent Reviewer checks the result-identity and collector interface
change before DM acceptance and result execution. No outcome has been observed for A02.

## 2026-09-20 — A02 preparation: coverage prediction and reading limits

The A01 evidence and A02 prospective/L0 are published at `068985d0b`. All nine A01
directories include the underlying NPZ arrays and native logs despite the repository's
generic NPZ/log ignore rules. Rechecked canonical `origin/main@6ee15d7dd`: A remains active
under `Codex DM`, pause lifted; the constitution, loaded scientific/engineering methods,
compute configuration and launcher/admission/resource-preflight code are unchanged from
the versions already adopted. This is not a memory admission for A02. The Implementer has
the isolated checkout `fsd-a02-impl` / branch `codex/termination-reuse-a02-impl` and only the
one code task above; DM retains the notebook, scientific choice, review acceptance and runs.

**Simple-model bridge, no new fit.** Under uniform behavior reselection, the actual focal
label switches with probability p=zeta/2 per tick, so an untruncated label run has mean
length 1/p: 16 ticks for long_behavior and four for matched_termination. The ten-state
focal position/option marginal has stationary total endpoint mass 1/(1+3p), namely
.842105 and .571429. One direct balance derivation assigns mass C to each interior
oriented state, C/p to each endpoint after summing its orientations, and normalizes
6C+2C/p=1. This is an analytical statement about the fixed five-cell behavior walk,
not a simulated fit or a claim about finite 96-tick episodes. Uniform initial states
and resets cause a transient, and greedy target evaluation does not obey this uniform
behavior marginal. The reduction removes demand/teammate effects on action selection;
their joint reward and remaining-commitment coupling are still present in learned J.

As a descriptive check of already collected A01 data, its start-row endpoint fractions
are .82779948 / .83076986 / .82427979. Actual behavior renewals are 6,114 / 6,070 / 6,193,
and label changes 3,067 / 3,040 / 3,148. These were read from saved arrays, not reexecuted
trajectories. They make the predicted occupancy difference concrete; they do not show
that endpoint-heavy coverage is desirable for learning the beta=.5 target.

A02 reading will reuse the independent config/hash/count/reward/evaluation checks, with
the crucial change that paired behavior trajectories are expected to differ. Check that
initial states and the exogenous teammate/demand components agree within each pair, that
logged option probabilities match the arm's actual marginal law, and that the initial
target evaluation panels agree. Compute support and endpoint/interior occupancy on the
same training start rows; retain all curve contrasts rather than select the late panel.
Training reward is not the target-policy endpoint. Longer traces, more endpoint visits,
or larger Q movement cannot substitute for the prewritten primary J comparison.

The prospective preference for clock-matched collection if long behavior has no useful
consistent gain is an **operational default for this fixed implementation/exposure**, not
an equivalence or general superiority inference from a wide three-block interval. Neither
arm is tuned separately; this leaves algorithm-by-collection-law tuning interactions
untested. No arms, seeds, horizons, counts or primary endpoint are changed by this
clarification, and no A02 outcome has been observed.

The independent Critic read A01's nine summaries and this transition and found no material
design dissent. It independently checked the marginal occupancy calculation and emphasized
the same conditional choice limit. I adopt its additional wording correction: A02 can
weaken the expectation that **this uniform long-commitment collector at this exposure**
improves target J, not falsify a general motivation for off-termination reuse. Equal-step
J differences do not themselves measure saved wall time or the cost to reach a fixed J.
Mixed or imprecise results leave comparative ranking unresolved even if I choose a
provisional default for subsequent work. This advice supplies no independent empirical
replication and changes no batch input.

## 2026-09-20 — A02 engineering acceptance and fixed-batch execution decision

Accepted Implementer `d216577a997bedb987a8a57dd8296028b21f29cf`, integrated into the DM
branch as `c96df2756`; the owned executable/test diff between those revisions is empty.
The change is the fixed A02 wrapper/entry plus a small shared producer identity interface.
No dynamics, probability law implementation, TD/trace arithmetic, data addressing or
evaluation code changed. A01's default scientific semantics remain unchanged; new identity
fields in producer metadata are additive, and its completed results remain bound to `63b0ca73a`.

DM read the whole diff and ran the combined A01/A02 suite: **25 passed in .28 s**; the
control runner guard regression passed **two tests in .13 s**. Independent Reviewer read
`068985d0b..d216577a`, ran **25 tests in .25 s**, and found no material executable finding.
It also checked paired exogenous components, differing actual behavior trajectories and
identical initial target panels in non-learning in-memory fixtures. The reviewer did not
exercise native admission or the full horizon; those remain actual-run responsibilities.
No production A02 fit has started and these checks select no arm, seed or endpoint.

I accept this implementation for the already declared **six** local_linux fits. Publish
the commit containing this entry and bind that exact full SHA in every native manifest;
execute serial seed-major order 91031, 91032, 91033, with long_behavior then
matched_termination in each block. All dimensions and prospective reading remain fixed.
Use the configured native launcher/snapshot route and its fresh actual-node 4 GiB memory
floor. DM directly retains observation and collection; uncertainty must be reconciled on
the same operation, never by changing the tag. No additional owner/Root permission is
needed after the recorded active registration. The direction continues through collection
and interpretation rather than ending at accepted launch or a terminal process.

## 2026-09-20 — A02 read: persistent collection improves its own return, not target learning

All six declared fits were natively admitted and exited zero at exact source
`739344301e965134d44ba754e7a7363258731e81`, serially on local_linux. No failed attempt,
retry, observer transfer or scored input change occurred. The paired run roots contain
the full native handles, exit witnesses, logs, configs, summaries and underlying arrays:

| Seed | long_behavior | matched_termination |
| --- | --- | --- |
| 91031 | [run](../../../../runs/termination_rule_experience_reuse/a02_long_behavior_91031_20260920/launch-manifest.json) | [run](../../../../runs/termination_rule_experience_reuse/a02_matched_termination_91031_20260920/launch-manifest.json) |
| 91032 | [run](../../../../runs/termination_rule_experience_reuse/a02_long_behavior_91032_20260920/launch-manifest.json) | [run](../../../../runs/termination_rule_experience_reuse/a02_matched_termination_91032_20260920/launch-manifest.json) |
| 91033 | [run](../../../../runs/termination_rule_experience_reuse/a02_long_behavior_91033_20260920/launch-manifest.json) | [run](../../../../runs/termination_rule_experience_reuse/a02_matched_termination_91033_20260920/launch-manifest.json) |

**Independent collection/read acceptance.** No learner import or trajectory replay was used.
Reconciled manifest, runner/supervisor identities, OS exit witnesses, admitted command hash,
source and all object/arm/learner/seed metadata. Every declared artifact byte count/hash
matches. Each fit has 49,152 training steps/target rows/visits, 6,144 update calls, 256
evaluation episodes/24,576 evaluation steps, and zero evaluation updates. Independently
decoded recorded state transitions, closed-loop movements, rewards and teammate countdowns;
reconstructed visit tables and actual conditional option probabilities. Every recorded
label change has a real behavior renewal. Paired initial states/options and all exogenous
teammate/demand state components match; focal paths differ as expected. Initial evaluation
panels match exactly. Reconstructed each of the 1,536 evaluation episode scores, every
checkpoint/primary mean, and update-row sums from the underlying outputs. All checks pass;
final tables are finite and their reported movement matches the saved arrays.

**Prewritten target J contrast.** Primary is again the equal mean of checkpoints
32/128/512. These three fresh blocks are the independent units; A01's nine development
fits are not additional A02 replication or a confirmation batch.

| Seed | Long primary | Matched primary | Long − matched primary | Long final | Matched final |
| --- | ---: | ---: | ---: | ---: | ---: |
| 91031 | .70764974 | .71115994 | −.00351020 | .73331706 | .73924154 |
| 91032 | .71059028 | .71375326 | −.00316298 | .74752604 | .75704753 |
| 91033 | .70496962 | .72088759 | −.01591797 | .73994141 | .74086914 |

Mean long-minus-matched primary is **−.00753038**, with descriptive paired t95 interval
**[−.02557997, +.01051921]** (df=2, approximate normal block differences). Final differences
are **−.00592448 / −.00952148 / −.00092773**, mean **−.00545790**, interval
**[−.01617902, +.00526322]**. All six primary/final block contrasts are adverse, but there
are only three independent training blocks and wide intervals; this is not a population
inferiority, equivalence or practical-threshold verdict. At checkpoint 32, long is higher
in two blocks; at 128 and 512 it is lower in all three. Do not select the early panel to
rescue the fixed primary. Both are actual learners: the common mean initial J is .57329102,
and long/matched final means are .74026150/.74571940 with nonzero table movement in each fit.

**Intermediate prediction versus native consequence.** Long behavior has the predicted
larger endpoint start-state occupancy: **.826233 / .825297 / .829997**, versus matched
**.567566 / .563680 / .568929**. Renewals are 6,134/6,205/6,123 versus
24,342/24,615/24,459, with actual label changes 3,113/3,167/3,078 versus
12,134/12,306/12,232. These finite-episode fractions accord with the physical persistence
prediction, not an assumption that target learning must benefit from it.

Long trace mass is 3.28722/3.29156/3.31107 versus 2.47368/2.47138/2.49339. Raw ratios
reach 8 versus 2, and mean squared return increments are 5.56–5.67 versus 3.93–4.12.
The latter is not measured estimator variance. Long visits 655/651/648 table entries and
matched 666/668/665; merely counting entries does not identify whether useful target-state
coverage or correction/clipping dominates the result. In particular, the long collector's
own mean training rewards (.65492/.65706/.65647) exceed matched's
(.57781/.57831/.58144), while its target J is lower. Training reward, endpoint occupancy
and longer return propagation are therefore not sufficient proxies for this target-learning
benefit. None of these observational diagnostics identifies a causal mediator.

**Working judgment changed.** Drop the favorable A02 long-collector conjecture as a reason
to invest further in that collection choice at this exposure. Use matched termination as
a provisional default if making this same fresh-data choice; do not claim a general ranking.
The expected intermediate change occurred, while its predicted favorable native consequence
failed. This weakens the proposed persistence-to-useful-learning link in this fixed host,
not the legality or possible usefulness of reusing already existing long data. It supplies
no evidence for learning a gate, changing teammate laws or adding a bespoke team correction.

**Cost and continuation.** Six started/completed fits, 294,912 training and 147,456
evaluation team steps, 36,864 tabular updates. Summed entry-to-summary wall **6.841153 s**;
first native acceptance to last exit **173.390543 s**, including serial staging/observation
gaps but excluding preceding first-launch staging. Maximum individual process peak RSS is
**41,180 KiB**. The timing limitations stated before A01 still apply; no equal-work speed
or wall-to-threshold claim follows. Across A01/A02, 15 fits have been started/read, with
737,280 executed training and 368,640 evaluation steps; no fit entitlement was consumed.

The next action is a cumulative boundary reading, not another fit. In this fully observed,
fixed-teammate model, remaining commitments can be retained in the state and ordinary
off-policy learning already supplies the lawful route. A01 did not establish useful
extra value from Retrace over direct Q(beta); A02 did not support choosing this long
collector to improve target J. Neither observation provides a new reason for an automatic
beta/alpha sweep, longer training, extra seeds or a special multi-agent correction. DM is
checking the strongest contrary reading before deciding whether any concrete next
comparison is worth its cost. No A03 or confirmation batch is selected by this entry.

## 2026-09-20 — Cumulative boundary: keep the ordinary route; this prototype path is idle

The independent Critic read the six A02 configs/summaries and found no material dissent
from the above update or a concrete successor favored by the present evidence. I accept
two refinements. First, retain the early contrary panel explicitly: long-minus-matched
at 32 episodes is **+.00566406 / +.00901693 / −.00209961**, mean **+.00419379**. Thus this
is not "long is never useful at any stage"; the observed early advantage does not change
the prewritten primary or, by itself, justify a new collection curriculum. Second,
independent repetition is not inherently screening: it can test recurrence. Here there
is no present decision that needs a more precise ranking, so its information value does
not justify another batch. No need to exhaust all coverage/clipping explanations first.
Adviser agreement is not additional replication.

**DM decision.** Keep ordinary target-termination learning as the reference implementation;
keep the matched-termination collector as the provisional fresh-data default in this host.
Do not add a special termination learner, joint correction, new representation, beta/alpha
sweep, confirmatory claim or more seeds on the strength of A01/A02. The direction remains
`exploring`, but this prototype path is **idle with no selected successor or live producer**.
All 15 fits are collected and scientifically read, not merely terminal. This is an
investment decision, not completion of the direction, general falsification, or a claim
that the ordinary method is optimal.

What is strengthened: observed low-level skills with recorded teammate commitments permit
a lawful ordinary augmented-state learning route; in A01, established multi-step learning
beats its one-step reference at the declared exposure. What is weakened: useful extra
Retrace value over direct Q(beta) at that exposure, and the favorable target-J prediction
for the particular long uniform collector in A02. What remains untouched: effects on the
UAV host/current learned skills, hidden commitments, changing teammate laws, general
termination-rule populations, convergence and wall-time savings. The full-state fixed-law
reduction should not be sold as solving those omitted multi-agent couplings.

Re-entry needs a concrete new scientific reason and a distinguishable native prediction,
for example an identified fixed-skill collection/support condition under which the strong
ordinary reference may fail or a real use decision that requires recurrence/precision.
This is not a requirement for a positive pilot, proof or exhaustive bottleneck diagnosis.
The DM owns selecting such a question; none is selected now. There is **no external
dependency** and no waiting on Claude B08, Root permission, or a nonexistent producer.
Root owns only shared-index integration of this published standing; it is not being asked
to approve a batch or to invent the next idea. All evidence and negative constraints stay
available for a future reasoned continuation.

## 2026-09-20 — Owner-directed re-entry: test the scientific entry condition itself

Root relays the owner's instruction to reopen A: the direction must determine whether a
worthwhile termination-rule reuse condition exists, rather than stop after the present
fully observed host's package comparisons. The prior idle investment decision is therefore
superseded. A01/A02 results and their limits remain unchanged. Author checkout is still
`fsd-a`, branch `codex/termination-rule-experience-reuse`, clean at `961750ee5` before this
entry. The freshly checked canonical index still has pause lifted and A active under
`Codex DM`; loaded constitution, methods and compute inputs are unchanged. Cost remains
recorded without any fit allowance. There is no new gate-learning question or B08 dependency.

**Falsifiable scientific entry conditions, not new governance gates.** A concrete condition
qualifies for a further direct study if it passes all of the following tests:

1. Behavior and target terminations are fixed, explicit and causally distinct; changing
   the termination rule changes the relevant target value/control problem, not only a
   nominal label count. Skills are fixed, behaviorally different controllers, not copied
   aliases manufactured to disadvantage a label table.
2. The target quantity is identified by the legal observations and actual behavior support
   available to *both* arms. Teammate remaining commitments, option controller memory and
   any termination-event side effect must be represented or lawfully inferable. A missing
   post-interruption branch cannot be supplied by renaming an observed continuation.
3. There is a specific finite-data or finite-computation deficit of a **competent** ordinary
   reference, and a lawful structure capable of addressing it. The reference includes
   target-beta Bellman bootstrapping/Q(beta), appropriate augmented-state multistep learning,
   and action-compatible intra-option sharing where known controllers permit it. When
   a small same-data learned primitive model is practical, it is a serious simple rival;
   an oracle transition model is not a learned baseline. Ideal-state representability is
   not itself evidence that all finite learning is adequate.
4. An intermediate prediction distinguishes the proposed explanation, and a predeclared
   native consequence can change a use/research judgment at the declared exposure. Merely
   increasing trace mass, decreasing nominal label ratios, or recovering a known semantic
   correction does not pass this test. A matched-rule or equivalent-action comparison must
   expose if the alleged issue is generic slow TD or label duplication instead.

These conditions are a scientific selection question for this owner-requested re-entry,
not a universal prototype/proof prerequisite. A demonstrated lawful finite-exposure gap
can justify learning tests without an asymptotic novelty theorem. A negative analytic
bridge constrains its stated class, never every possible host or representation.

**First bounded bridge selected; no new fits yet.** Investigate one source-grounded case:
small target-label probability during a shared primitive-action prefix, with delayed value
propagation. Check whether termination mismatch creates a genuine deficit after admitting
ordinary action-compatible learning. Do not enumerate architectures or extend A02. The
bridge will also use an unsupported-divergence counterpart, so it can distinguish a
recoverable label-space mismatch from an unidentifiable real-action branch.

Primary-source check: the Q(beta) paper's section 8, p. 3180 (PDF p. 8), explicitly notes
that its target option-selector factor can suppress traces despite primitive-action
compatibility, and discusses action-level correction. Its section 4.4, Eqs. 15–16, separates
the two corrections. This is not a new idea or an established online-convergence result.
Sutton, Precup and Singh, *Between MDPs and Semi-MDPs* (1999), pp. 202–205,
[primary paper PDF](https://people.cs.umass.edu/~barto/courses/cs687/Sutton-Precup-Singh-AIJ99.pdf),
Eqs. 18–21 and Theorem 3, already supplies action-compatible intra-option model/TD learning
for deterministic Markov controllers under its visitation assumptions. I verified those
passages directly after the Scout's retrieval. Thus lack of sampled option labels alone
cannot establish a missing ordinary solution. Local catalog search found no matching
off-termination/intra-option source; adjacent asynchronous actor-critic titles were not
treated as evidence for this particular correction.

The Scout's proposed rare-label example blurred the behavior selector with target mu.
I do **not** adopt that identification: in Q(beta), `mu(o|s)` is the target selector;
small behavior selection probability by itself does not make the Q(beta) coefficient
small. The bridge must specify both distributions separately, keep their real action
support explicit, and test a strong action-compatible baseline rather than an intentionally
unshared label learner. The DM owns this correction and the eventual study/stop choice.

## 2026-09-20 — A Pro input: termination-reuse entry conditions and finite-data bridge

**Author and live decision.** This section is authored by A's DM for the owner's single
cross-direction Pro consultation. It is A's input, not B/C's proposal or a Portfolio
ranking. The preceding owner-directed re-entry remains active. No new result fit, code,
claim note or native launch was made for this analytical bridge. The question is whether
there is a concrete, worthwhile condition for studying termination-rule reuse beyond the
competent ordinary route, or whether to pause this direction's investment with an honest
scope. A later umbrella question will bind the independently authored B/C sections; this
section does not substitute for them.

### A standing, entry definition and contrary evidence

The four scientific entry conditions above are the object of criticism, not new permission
gates: (1) fixed, behaviorally different skills and a real value/control effect of changing
the fixed termination rule; (2) identification from the same legal observations and actual
support, including teammates' remaining commitments and relevant controller memory;
(3) a specific finite-data or finite-computation limitation of a competent ordinary
same-information reference, with lawful structure that could address it; and (4) an
intermediate prediction and native consequence that could change a research/use judgment.
No learned gate, counterfeit interrupted suffix, oracle model or deliberately unshared
label learner supplies that comparison. Direct Q(beta) is established prior work, not our
innovation. These conditions need not be proved before an exploratory test.

Cumulative evidence is in **A01 read** and **A02 read** above, with all 15 fits and raw
outputs committed at `961750ee58664022bbd3fad3365886e46fb3facc`. A01 compared one-step,
direct Q(beta) and ordinary augmented-state Retrace on the same behavior data, three
independent training blocks each. Both multistep arms beat one-step in all three primary
contrasts; Retrace-minus-Q(beta) primary was mixed, mean +.00000904. A02 compared the same
Retrace learner under long versus matched behavior termination on three fresh blocks:
primary differences were -.00351020 / -.00316298 / -.01591797, mean -.00753038 with a
wide paired t95 interval [-.02557997, +.01051921]. Longer behavior raised endpoint occupancy
and trace mass but not the declared target-J primary. Its early 32-episode contrast was
positive in two blocks, mean +.00419379; this contrary panel remains, not a replacement
endpoint. These are fixed fully observed two-agent-host findings, not equivalence,
population inferiority, a general impossibility result, or UAV evidence.

### A exact shared-prefix bridge: opportunity exists, this strong ordinary reference suffices

This is our constructed finite model and algebra, **not collected trajectories or a
measured learning result**. States x0 -> x1 -> x2 -> x3 -> terminal form a DAG, with at
most four primitive transitions. Gamma is 1; the derivation uses finite backward
induction, not an infinite-horizon contraction. The environment class here is deterministic
conditional on the actual action; the service transition is initially unknown. At x0 a
high-level decision chooses safe (immediate .75) or starts L. R may be initiated only at
x1/x2/x3. Both fixed feedback
skills issue ADVANCE at x0/x1/x2 where applicable; at x3 they issue genuinely different
L-service and R-service actions. Thus they are not copied aliases. All advance rewards
are zero. A teammate occupies the L station for an observed four-tick commitment with
recorded countdown. L-service adds no coverage; in this example R-service succeeds and
adds one unit of coverage. The reward rule can be known, while the service-success
transition is learned from observations. Teammate behavior is unchanged and exogenous;
endogenous co-learning and hidden commitments are absent.

After each advance there is a renewal opportunity. Both behavior and target renewal
selectors deterministically choose R; only their termination probabilities differ:
zeta=1/8 and beta=1/2. Once R is active, a renewal selects R again. The complete behavior
collector initially chooses safe/L with probability 1/2 each; the following Q_L is
conditional on choosing L, not a collector forced always to choose L. Therefore

`Q_L^beta(x0) = 1 - (1-beta)^3 = 7/8 > 3/4`, whereas
`Q_L^zeta(x0) = 1 - (1-zeta)^3 = 169/512 < 3/4`.

This positive control gives a real native decision distinction: revaluing the target rule
chooses L with value .875 rather than safe with value .75. It changes no termination gate.
At renewal states the target mu(L|x) is zero; it is not being confused with a rare behavior
selector. A matched-rule beta=zeta control correctly chooses safe.

Consider three constructed, positive-probability records from that one behavior collector:
`D_L` starts L, has no renewal on the three advances and observes terminal L reward 0;
`D_R` starts L, truly renews to R after the first advance, then observes R success/reward 1;
`D_safe` chooses safe and observes .75. These are nine primitive rows containing six
distinct state-action pairs. A same-data empirical primitive model reads those rows; it
is not supplied with an oracle transition table. Ordinary action-compatible intra-option
TD with replay may back up the same observed pairs in reverse order. Both use the known
controllers, target beta and renewal selector, and obtain:

| Backup location | L value | R value |
| --- | ---: | ---: |
| x3, actual distinct service observations | 0 | 1 |
| x2, common ADVANCE | .5 | 1 |
| x1, common ADVANCE | .75 | 1 |
| x0, initial allowed choices | .875 | not an allowed initial choice |

The recurrence is `Q_i(L)=(1-beta) Q_(i+1)(L)+beta Q_(i+1)(R)` and
`Q_i(R)=Q_(i+1)(R)`; the separate safe backup is .75. Eight relevant scalar Bellman
backups suffice after reading the nine rows, including the two distinct service values
and safe. This is a logical work count, not measured runtime or a speed claim. Shared
ADVANCE observations are reusable; **D_L's terminal reward is never assigned to R**.
For a deterministic common prefix with known beta_i, the same argument gives the L-end
weight `product_i(1-beta_i)` and complementary R-end weight, with linear backward work.
Consequently this selected shared-prefix/delayed-propagation condition is not evidence
that the strong ordinary reference is insufficient. This finite-work comparison, unlike
an ideal representability statement alone, directly absorbs the proposed local deficit.

Primary passages motivating the bridge are Q(beta), section 4.3 Eq.15 and section 8
[publisher PDF](https://ojs.aaai.org/index.php/AAAI/article/view/11740/11599), and
Sutton, Precup and Singh (1999), sections 5–6 Eqs.18–21
[primary PDF](https://people.cs.umass.edu/~barto/courses/cs687/Sutton-Precup-Singh-AIJ99.pdf).
They distinguish label-based correction from already established action-compatible
learning. The DAG, its work count and the following counterexample are our deductions,
not the papers' experiments or theorems. A primitive flat marginal alone is not a valid
replacement for the latent option/continuation law when beta is below one.

### A identification boundary and finite-resource uncertainty

Merely removing D_R from the displayed finite data does **not** remove population support
under zeta=1/8. It is finite missing coverage, potentially repairable by further genuine
observations. For a strict unsupported counterpart set behavior zeta=0 and prohibit an
initial or reset R: all behavior chooses safe or L and never executes R-service. Two
worlds can then share the known coverage reward rule, fixed controllers and the entire
behavior-data distribution, but differ in the unobserved R-service transition: success
probability 0 versus 1. Target beta=.5 gives Q_L of 0 versus 7/8, and different optimal
initial choices. No same-information learner identifies which world holds. Continuing the
observed L suffix cannot supply the missing R outcome. The pair changes an unknown
transition, not a reward rule the learner was already told.

A broader but carefully limited observation: with complete legal Markov state, recorded
or reconstructible joint primitive actions, fixed known collection/controller laws and
an unknown environmental kernel P, the data likelihood conditional on the initial state
factors as `C(D) product_t P(x_next,r | x,a_joint)`, where C(D) does not contain P.
Complete joint transition/reward counts are sufficient in a discrete tabular class.
Target beta changes a known controller law, not the environmental information in those
counts. Termination-event side effects must be represented as state/action variables if
they affect that kernel; hidden variables cannot be silently discarded. This is **not**
an efficiency theorem for plug-in values, compressed models, approximate state or planning.
Finite-sample estimation efficiency, sensitivity to beta and finite-computation advantages
are still logically possible even with the same sufficient data.

The independent Critic verified the DAG and raised the finite-coverage/structural-support,
conditional-start and known-reward distinctions above; I adopt them. It also explicitly
rejected upgrading the local comparison or sufficiency observation to a direction-wide
nonexistence claim. I agree. Adviser agreement adds no independent empirical evidence.
My present inclination is an **investment pause**, not a falsification: A01/A02 failed
their extra-benefit predictions, this source-grounded bridge is covered by a cheap
same-data ordinary route, and the unsupported version is not an estimable target. I have
not yet identified a concrete remaining finite-resource condition worth the next fit.
The owner's requested Pro consultation will challenge that inclination before I record
the next action. No external permission or missing canonical admission is the cause.

### A requested Pro discriminator

Criticize A's entry definition and the above implication. Give the strongest concrete
countercondition, if any, under fixed behaviorally explicit skills and fixed unequal
behavior/target termination: what legal data identify it, what real teammate commitment
or controller feature matters, why a competent ordinary augmented-state/Q(beta)/
action-compatible reference or practical same-data model may fail at a stated exposure,
and the smallest observation that could refute that story. Predict an intermediate
quantity **and** native value/decision effect; state the matched baseline's information,
learning/tuning rights, fit cost and dominant non-fit work. An existing-method comparison
can be worthwhile; neither novelty nor a positive toy test is mandatory. If the admission
premise itself wrongly excludes a worthwhile boundary question, explain with such a
concrete discriminator, not a general appeal to MARL complexity.

Alternatively explain why the presently supported conditions justify stopping investment,
and delimit precisely what has not been ruled out. Do not turn another package failure
into nonexistence, treat same sufficient information as optimal finite learning, invent
unobserved suffixes, learn a gate, revive residual-MC, or require an unbounded search before
either an ordinary study or a pause. A concrete new reason and prediction are sufficient
for re-entry; no prior proof or positive result is required. Additional cost for this
bridge is **zero fits**; previous cumulative cost remains 15 started/read local-CPU fits.
