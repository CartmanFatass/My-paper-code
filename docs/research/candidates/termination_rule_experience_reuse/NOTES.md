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

## Pro question 2026-09-20 abc-admission-conditions-and-minimal-discriminators

Conversation: new. Root operates the owner's requested **single Jev consultation**; no
separate Send is requested for the B/C input sections. A DM assembles this common question
and owns this target notebook. Each direction's scientific input is independently authored
by its own DM at the fixed source below. This is a cross-direction scientific critique,
not a Portfolio allocation/ranking, confirmation review or experiment-approval request.

**Question.** For each of A, B and C, does its proposed scientific entry condition expose
a worthwhile, legally observable learning/reuse question, or has the strongest ordinary
same-information reference already absorbed it? Criticize the condition itself, supply
its strongest lawful counterexample or hidden-information objection, and identify the
smallest decisive next observation if one is worthwhile. The answer should change each
DM's continue-versus-pause judgment without converting one package failure into absence
of opportunity, demanding novelty for its own sake, or requiring an endless search.

### Independently authored inputs and exact revision boundaries

Read the named section and its directly selected evidence/context, not an unbounded
history. The fixed sources are the scientific inputs; the latest writable target is used
only for preserving concurrent bytes when delivering the answer.

- **A — termination-rule experience reuse.** Source
  `250635b824cfe5ee175319f0c458f1034abfb814`, branch
  `codex/termination-rule-experience-reuse`, path
  `docs/research/candidates/termination_rule_experience_reuse/NOTES.md`, exact heading
  `## 2026-09-20 — A Pro input: termination-reuse entry conditions and finite-data bridge`.
  [Pinned A input](https://github.com/CartmanFatass/My-paper-code/blob/250635b824cfe5ee175319f0c458f1034abfb814/docs/research/candidates/termination_rule_experience_reuse/NOTES.md).
  Its four entry conditions, A01/A02 reads, finite DAG and strict-support counterexample
  are A's own input. Stage: 15 earlier fits read; the new bridge is algebra, **zero new
  fits**, and its proposed shared-prefix deficit is absorbed by a finite-work ordinary
  same-data reference. No direction-wide impossibility or final pause has been declared.
- **B — joint skill/teammate drift learning.** Source
  `7435fec3191926b61186ad7f97c39c182d10e932`, branch
  `codex/skill-teammate-drift-learning`, path
  `docs/research/candidates/skill_teammate_drift_learning/NOTES.md`, exact heading
  `## Pro consultation input — 2026-09-20 B03 joint-support admission`.
  [Pinned B input](https://github.com/CartmanFatass/My-paper-code/blob/7435fec3191926b61186ad7f97c39c182d10e932/docs/research/candidates/skill_teammate_drift_learning/NOTES.md).
  Read that DM's question and the directly cited B03 prospective/algebra and B02 adverse
  evidence. Stage: **B03 has not run** at this source; its 18 fits are prospective, not
  evidence of learning or admission. A does not rewrite B's scheme or scientific question.
- **C — skill information refresh.** Source
  `4ef39c08ae55c6dd623718b4072a7ddcc9b9e913`, branch
  `codex/skill-information-refresh`, path
  `docs/research/candidates/skill_information_refresh/NOTES.md`, exact heading
  `## Pro question 2026-09-20 C05 receiver-value bridge — Pro consultation input`.
  [Pinned C input](https://github.com/CartmanFatass/My-paper-code/blob/4ef39c08ae55c6dd623718b4072a7ddcc9b9e913/docs/research/candidates/skill_information_refresh/NOTES.md).
  Read that DM's question and directly cited C05 protocol/read/evidence and contrary
  C03/C04 evidence. Stage: **C05 already has a bounded positive timing-value result**;
  the single learned history matches the strong transparent VoI reference, not an extra
  learning gain. Preserve the DM's distinction between opportunity and learned-package
  value. A does not rewrite C's proposal or select its next experiment.

Within B's input and its nested Context, `source_sha` means B's full fixed SHA above;
within C's it means C's full fixed SHA above. Do **not** resolve their code/results against
A's question branch. Explicitly frozen execution or historical SHAs inside any input keep
their stated identity and meaning. A's historical 15-fit evidence remains at
`961750ee58664022bbd3fad3365886e46fb3facc`; the newer A bridge does not change those runs.

The B and C inputs each contain an empty Answer slot and conditional write instructions.
They are **read-only inputs for this consultation**, not writable destinations: no B/C
notebook has been lent to Pro. The only answer-only loan is the slot below this umbrella
question in A's notebook. Stop rather than write to a different question or file.

### Common current context and source precedence

The actual transport message supplies this umbrella question's full `source_sha` after
publication. Unless a different fixed revision is explicitly given above, read at that
source: `docs/project/OPERATING_CONSTITUTION.md` sections 1–5 and 7–8, and
`.agents/skills/hmasd-scientific-tools/SKILL.md` sections "Update the working explanation",
"Simple-model and literature bridges", "Comparators and MARL information", "Statistics"
and "Cost and exposure". Read research-engineering's "Checks and review" or "Execution
and admission" only if a consequential recommendation depends on executable feasibility.

For control state only, `docs/research/RESEARCH.md` at canonical main
`fd8402f592ac310cdccc4619137c041796df29b6` has owner pause lifted and all three directions
`exploring`, lead `Codex DM`. Its registration-era standing is not the latest scientific
reading; the independently authored pinned inputs above provide that. The current owner
explicitly reopened each entry-condition question and requested this consultation.
Ordinary direction work is already authorized: Pro neither resumes a pause nor grants a
batch. Constitution section 3 as amended 2026-09-20 has **no fit allowance**; stale
"allowance/up to six" text in skills or old notes is superseded. Fits record cost only.
Prospective arms, seeds and horizons, no scored-batch extension, preservation of failures,
matched-information baselines and a fixed 3–5-new-seed/arm confirmation rule still apply.

Read the pinned question and these Context sources before answering. Treat the stated
current owner instruction and constitution as governance, skills as applicable methods,
and historical/frozen files as their bounded evidence or contract. These replace
conflicting old chat instructions for this question; preserve named frozen meanings.
Do not substitute chat memory or a moving branch for inputs. Cite consequential sources
actually used and identify decision-critical sources you could not read. Unavailable
binary evidence is a stated limit, not permission to claim it was verified.

### Requested return and the sole write boundary

Return separate **A / B / C** judgments, preserving their different stages, and address
the following for each without prescribing a quota of new candidates:

1. Which entry conditions are established, falsified or still untested? Separate task
   opportunity, lawful representation/identification, finite learnability and package
   value; an ordinary-method reduction may be a useful answer rather than an innovation.
2. Has the strongest ordinary/transparent same-information reference already absorbed
   the proposed advantage? Name a missing *distinct* simple reference only if it changes
   the comparison; an algebraically identical renamed arm is not extra evidence.
3. Give the strongest legal counterexample or hidden leakage/unsupported-branch objection,
   with the exact assumption or observation it turns on. Do not posit free teammate state,
   context/request bits, new reward labels or model knowledge; do not silently change the
   gates/controllers that the respective direction holds fixed. B's declared joint drift
   remains its intervention, not a forbidden change or an inference about A/C.
4. If useful continuation exists, specify its **single smallest decisive observation or
   comparison**, what could falsify it, the strongest baseline and shared information/
   tuning rights, an intermediate prediction plus native consequence, fit cost and the
   dominant non-fit work. It can be an existing-method study; no prior proof, positive
   pilot, new architecture or automatic larger-host migration is required.
5. If no present continuation is worth its cost, explain the bounded investment-pause
   judgment, what remains unresolved, and a concrete re-entry reason. Distinguish this
   from universal nonexistence and from waiting for approval. State
   `MATERIAL_DISSENT: yes/no` for that direction and why. Advice is not replication.

Give advice within this question only: no experiments, new records, budget grants or new
approval requirements. Write the complete answer **only inside the empty `### Answer`
subsection immediately below this umbrella heading**, on branch
`codex/termination-rule-experience-reuse`, target
`docs/research/candidates/termination_rule_experience_reuse/NOTES.md` in
`CartmanFatass/My-paper-code`. Fetch the latest target file and use its actual blob SHA
for the write, while reasoning from the fixed sources. Preserve every other byte,
including the question and all B/C files; stop on overlapping edits. Report the actual
successful answer commit. If writing fails, return the **complete answer in chat**, not
only a receipt, SHA, status or link. Root reconciles uncertain Send/write state without
a duplicate consultation; each DM subsequently records its own adoption/rejection.

### Answer

*saved from chat* — Root reported Jev COMPLETE and NOT_DELIVERED. The complete collected answer is preserved verbatim below; on-disk SHA-256 `0b11d7216f66daea006f943a239aea6237d2a20f3fca4b2c6f21fb803df2a429` includes its final LF (the 11,144-character body without that LF has SHA-256 `35ace3a0d98a55c311a28f6eb56d212752c02467f80bb783b757bc2ac013b8b3`). Before insertion, remote question/empty Answer matched source `f3fe65778da4e58fb5eb0ca7a34f9c6896c9c945`, blob `9115bcb18a9a72eb86e82110ba5c39b0bf60f9f1`; no Send was repeated.

GitHub 读取成功，但本次未能写入。 当前连接提供的 GitHub 操作是只读的，没有可用的文件更新或提交操作；我没有修改任何仓库文件，也没有产生 Answer 提交。以下是针对附件中唯一 umbrella question 的完整答复，而不是写入成功回执。

来源、版本与证据边界

消息中没有另附 umbrella question 的完整 source_sha。我通过发布历史定位到 f3fe65778da4e58fb5eb0ca7a34f9c6896c9c945，并核对附件与该版本目标文件具有相同的 Git blob 哈希 9115bcb18a9a72eb86e82110ba5c39b0bf60f9f1。该版本的指定 ### Answer 为空。科学输入分别使用 A 的 250635b824cfe5ee175319f0c458f1034abfb814、B 的 7435fec3191926b61186ad7f97c39c182d10e932、C 的 4ef39c08ae55c6dd623718b4072a7ddcc9b9e913，没有用 A 分支替代 B/C 的代码或结果。

我已阅读全文，并读取所指定的科学输入、相关结果解释、共同规范、B03 科学模块和入口、C05 摘要与因果实现，以及相关原始论文段落。本次不是对全部底层实验制品的独立重审：没有重新验证 A/B 全部原始数组；C05 的 episodes.jsonl 读取未成功，接口报告文件可能过大或不受支持；updates.jsonl 只抽读了开头；没有独立读取、重建指定的二进制轨迹和检查点。因此，下文将原 DM 的全量 readback 视为已发表的结果报告，而不是本次新增验证。C05 的十八个条件动作、精确期望值和参数位移则已直接从摘要核对。

指定规范已经取消 fit allowance。下面的继续或暂停均为科学投资建议，不是实验批准、预算发放、恢复 owner pause 或修改方向状态；任何确认性结论仍须遵循原有固定确认规则。

总判断

“普通方法已吸收问题”必须区分两层含义：存在合法的普通学习路线，并不等于该路线在给定样本和计算下已解决实际决策问题。 前者不应阻止既有方法研究；后者才可能使进一步复杂化失去价值。

方向	当前材料支持的判断	建议
A：termination-rule reuse	存在真实的目标终止规则重估机会；所选共享前缀缺口已被有限工作量的普通方法吸收，A01/A02 未支持进一步复杂化的预测。	暂停当前增量算法／采集器路径的投资，保留普通方法；不宣称方向不存在机会。
B：joint drift	联合结果支持与情境特征支持不同的识别论证成立；普通联合条件回归就是候选方法，但其有限样本原生收益尚未检验。	保留既定 B03 有界比较，不增加新臂或另起筛选。
C：information refresh	C05 已建立合法时机价值机会，并有一个训练历史实现它；强透明 VoI 已吸收这个固定问题的学习增量。	结束这个已解小模型上的学习增益追逐；没有具体目标映射之前，不选择后继学习批次。

三者不是科研优先级排序，而是处于不同证据阶段所导出的不同选择。

hmasd-pro-question-abc-admissio…

A — Termination-rule experience reuse
1. 入场条件：机会成立，所选额外缺口不成立

A 的前两项条件是合理的：终止规则必须改变真实控制问题；目标必须由合法观察和实际支持识别。第三项则应解释为为额外方法复杂度寻找理由，不能强读成“除非普通方法失败，否则终止规则复用不值得研究”。发现普通方法已经足够，本身可以是方向的有效答案。A 的输入已经允许既有方法比较、不要求先验正结果；应保留这一解释。

共享前缀 DAG 确实建立了任务机会，而不只是标签变化：

Q
L
β
	​

(x
0
	​

)=1−(1−
2
1
	​

)
3
=
8
7
	​

>
4
3
	​

,
Q
L
ζ
	​

(x
0
	​

)=1−(1−
8
1
	​

)
3
=
512
169
	​

<
4
3
	​

.

因此，在同一组固定技能下，按目标终止规则重估会选择 L，而按行为规则评价会选择 safe。这里没有学习终止门；L/R 在最终服务动作上真实不同，队友占据 L 站点的四 tick 承诺具有行为内容，不能用“都是共享 ADVANCE”把整个例子归为重复标签。

合法识别则是有条件成立：必须保留实际队友承诺、有关控制器状态及影响转移的终止事件。A01 中队友项能在条件似然比里消去，是因为完整条件状态下其规律不变，不是因为两种目标下队友的边际轨迹必然相同。这个限制不能外推为已经解决隐藏承诺或共同学习的多智能体过程。

hmasd-pro-question-abc-admissio…

2. 强普通参考确实吸收了这一个共享前缀缺口

给定所构造的 D
L
	​

,D
R
	​

,D
safe
	​

，普通同数据原始动作模型，或允许动作兼容共享与逆序重放的 intra-option TD，都能使用九条真实 primitive rows 完成：

(Q
L
	​

,Q
R
	​

)
x
3
	​

	​

=(0,1),(Q
L
	​

,Q
R
	​

)
x
2
	​

	​

=(.5,1),(Q
L
	​

,Q
R
	​

)
x
1
	​

	​

=(.75,1),

再得到 Q
L
	​

(x
0
	​

)=.875 和 safe 的 .75。八次相关标量 Bellman 备份足够。最终 R 服务价值来自实际 R 服务观测，不来自把 L 的尾段重新命名。

这比“某个无限容量状态表示原则上能表示真值”强得多：它给出了同一批合法数据上的有限计算解法。不过，八次备份是已经取得这九行记录之后的工作量，不包括等待获得相关服务分支的采样成本；它既不是实测运行时间，也不是一般随机任务中的样本效率证明。

文献对应关系也准确。Q(beta) 原论文讨论了目标 option-selector 概率可能压低与原始动作兼容的轨迹权重；Sutton、Precup、Singh 的 intra-option 工作已经提供动作兼容学习路线。不能用故意不共享动作的标签表，制造一个普通方法原本没有的缺口。原 Q(beta) 论文还明确把在线收敛另列为待解决问题，其期望算子分析不能升级为本实验的在线收敛保证。
AAAI出版物
+2
麻省大学计算机与信息科学学院
+2

同样，Retrace 是一个既有多步离策略参考，而不是因加入队友状态就成为新的联合校正算法；它的理论性质不自动给出特定有限暴露下的原生收益排序。
NIPS论文集

3. A01/A02 应改变什么判断

我采用的是批评后修正的固定八行归一化、α=1 更新约定，而不是早期按随机访问次数取均值的版本；同时采用后续明确的“估计器完整实现比较”，不把差异单独归因于跨 renewal 边界。

hmasd-pro-question-abc-admissio…

A01 给出的积极事实是：三个训练块上，两种多步方法的 primary 均高于真实会学习的 one-step 参考。但 Retrace−Q(beta) 的三个 primary 差为负、正、负，均值仅 +.00000904，描述性配对区间为 [−.00347179,+.00348988]。额外 trace mass 和 renewal-edge 使用确实激活，却没有实现预期的清晰增量价值。这削弱“这套更长传播在此暴露下值得保留”的预测，不构成两种算法等价，也不识别是哪一个权重或边界因素造成结果。

A02 的 long−matched primary 为：

−.00351020,−.00316298,−.01591797,

均值 −.00753038，区间 [−.02557997,+.01051921]。更高端点占用、更长轨迹和更高采集期回报没有转化为目标 J 优势。仍须保留 32-episode 的相反证据：两个块为正，均值 +.00419379。因此不能说“长承诺在任何阶段都无用”，但也不能用这个早期面板替换预写 primary。

这支持把 matched termination 作为该实现下新采集选择的暂定默认；它不是总体劣势、等价或最优性结论，更不否定已经存在的长承诺数据值得合法复用。

4. 最强识别反例与没有排除的空间

严格无支持版本是决定性的反例：令行为 ζ=0，并禁止初始／重置时选择 R。两个世界可以有完全相同的行为数据分布、已知奖励规则和固定技能，却在从未观察的 R-service 成功转移上分别为 0 和 1；目标 Q
L
β
	​

 分别为 0 和 .875，最优初始动作相反。任何同信息方法都不能从这样的行为数据辨别两个世界。增加传播长度、重标标签或生成“中断后尾段”都不增加缺失的信息。

但正支持下的一批数据碰巧没有 D
R
	​

，不是上述结构性不可识别。有限覆盖、随机转移估计、近决策阈值的不确定性，以及有限规划计算，都没有被 A 的充分统计量论证排除。

一个具体的未排除边界是：未来实际任务中的 R 服务成功率为未知 p，其余 DAG 语义不变，则

Q
L
β
	​

(x
0
	​

)=
8
7
	​

p,L 优于 safe⟺p>
7
6
	​

.

这是对现有模型的条件性推导，不是新结果。若实际使用决策接近这个阈值，目标敏感度和估计误差就可能重要；但强参考必须包含同数据、同置信信息的普通模型决策，不能只比较未经校准的点估计。目前材料没有给出这种目标使用需求，也没有显示该普通参考不足，所以这个可能性不是立即再开一批的理由。

5. 下一步与分歧声明

建议暂停当前这条增量方法／长采集器路径的投资，新增 fits 为 0。 保留 A01/A02 的 15 个既有 fits、普通目标终止规则学习路线及 matched fresh-data 默认，不追加 alpha/beta 扫描、延长训练或归因臂。

可改变暂停判断的最小新理由，是一个真实使用决策：支持存在、信息合法，而在声明暴露或计算下，估计误差可能跨越明确决策阈值；或者一个实际决定确实需要重现性／更窄不确定性。届时只需围绕那个决定做同信息比较，不需要先证明新方法胜出。主要非 fit 工作是检查支持、控制器语义和必要备份，而不是继续枚举所有可能宿主。

MATERIAL_DISSENT: no。 我赞成当前有界暂停倾向；反对的是把“本地缺口被普通方法吸收”强读成方向不存在机会。现有输入没有做这种普遍化。

B — Joint skill/teammate drift learning
1. B03 的入场条件成立于识别层，尚未成立于学习收益层

B03 的关键不是“情境不重复”本身，而是：

历史情境特征缺少一个可识别方向，但同一合法历史中的实际联合结果仍覆盖了可迁移的条件结构。

固定三 tick 宏时钟下，两方控制器概率同时改变，正是 B 所声明的干预；不能把 A/C 的固定队友约束强加给 B。已读科学代码也把目标定义为终端单宏任务，没有把这个问题包装成共同训练队友、长程 bootstrap 或探索耦合的实验。

令

ϕ(u,v)=((1−u)(1−v),(1−u)v,u(1−v),uv),
n=(−.16,−.16,−.16,.84).

于是

ϕ(u,v)
⊤
n=uv−.16.

历史全部位于 uv=.16 时，这个方向不能由情境／宏奖励观测识别。两张合法条件奖励表

μ=(.05,.05,.05,.95),
μ
~
	​

=(.13,.13,.13,.53)

在所有源情境给出相同的 Bernoulli 宏奖励均值 .194，但在 (u,v)=(.87,.89) 给出 .74687 与 .43972，分别位于 safe=.60 的两侧。这个例子有效地反驳了“指纹函数类包含真值，所以历史已足以确定外推”的说法。

不过，整个合法数据集并非不可识别。实际 (X,Y,r) 被所有臂同样观察，四个联合结果有源支持，可以区分上述两张表。丢失识别方向的是仅使用情境／宏奖励关系的表示，不是原始联合历史。这里恰好存在普通条件化可以利用的结构。

2. 普通方法已经给出解法，但没有替代有限学习比较

joint_response 就是普通联合结果条件回归，再按已知当前联合完成规律积分：

Q
	​

coop
	​

(u,v)=
x,y
∑
	​

P
u,v
	​

(x,y)
E
[r∣coop,x,y].

这不是新型 replay correction。再增加一个使用相同五个可达 cell、相同伪计数、相同积分的“普通模型”臂，只会复制候选，不增加证据。B 的输入已经正确承认这种身份。

但它仍值得与直接 saturated fingerprint 比较，因为理论识别与有限暴露下的行动改进之间还有没有被观察的环节。按声明的源采集律，2048 个宏中，合作且 X=Y=1 的预期观测数为

2048×
2
1
	​

×.16=163.84.

这是由设计推导的期望计数，不是已收集数据。它说明联合 cell 估计有具体的样本基础；不能保证某个有限训练块的估计足够准确，更不能保证指纹方法收到目标标签后不会迅速追上。

在读取到的代码中，当前预测和精确评测发生在本宏结果进入更新之前；learner 接收的是当前合法参数及真实采样的 skill、outcome、reward，没有把 evaluator 的真奖励均值或本宏未来结果送入预测 API。这个静态检查支持所声明的信息边界，但不等于本次完成了独立工程验收或实际 admission。

3. 最强反对意见，以及唯一最重要的解释修正

最重要的修正是：不要把 B03 表述为“旧宏经验本身不可用”，而应表述为“对旧经验作情境无关平均或直接宏均值拟合，可能丢掉对新联合规律有用的条件结构”。

成功时，B03 证明的恰恰是旧数据仍然有用。它不是强普通方法之外的新解法，而是普通方法正确使用旧数据的一个有限样本存在见证。

最强的合法竞争解释是：fingerprint_recent、fingerprint_full 或 additive_response 即使价值误差较大，也可能在 primary 窗口内选出同样的原生最优动作。更准确的值预测不必带来更好的控制。 因而，MAE 改善而 native return 无改善，就不能通过完整入场条件。这不是给简单基线“宽松待遇”，而是坚持待解释对象是原生决策。

识别边界则明确落在两个假设上：当前联合完成规律确实已知；E[r∣skill,X,Y] 跨控制器情境保持平稳。如果新版本还改变了给定 X,Y 后的服务质量，或者两方完成有未知相关性，旧联合结果数据加已知边际 u,v 就不再自动识别目标。B03 通过明示假设排除了这些反例，没有解决这些反例。

原始文献也只能支持这个有界解释。Foerster 的条件分解有完整状态及相应联合规律的前提，部分观测下额外历史项不能消失；HIRO 的目标重标与轨迹重要性采样讨论不是 B03 的算法，其不利 IS 经验也不能直接预测这个终端条件回归的结果。
Proceedings of Machine Learning Research
+2
Proceedings of Machine Learning Research
+2

B02 的反面证据应原样保留：joint IS−较强 fingerprint 的三个 primary 为 −.055923、−.034057、−.047778，且相对 uniform 的残差预测也反向。不能因为 B03 可能成功，就把 B02 的原实现重新解释为已得到支持。B03 去除了原来的 bootstrap／全局归一化 IS 包，是新的结构化学习问题，不是原包的成功修复。

4. 单一最小判别：既定 first-64 prequential native 对比

保留 B03 既定比较即可；不需要第七个臂。 最小决定性观察是 first-64 target 窗口中，joint_response 相对预写 primary fingerprint_full 的配对原生收益，同时用已列入的 saturated recent fingerprint 和 additive response 判断该优势是否被更简单的适应或无交互模型吸收。

中间预测是：源联合 cell 的实际支持足以使条件化估计在目标初期降低两动作价值 MAE。原生预测是：这种改进能减少错误选择 safe 的次数，提高同一个预写窗口的 expected greedy return。不能用更晚窗口或 MAE 单独替换它。late-64 的 uniform-versus-recent 只回答旧混合分布平均是否造成后期适应损失，不是 first-64 条件迁移优势的替代终点。

使这条解释失败的观察很直接：联合结果模型没有获得足够支持；它虽更准确却没有减少原生决策损失；或近期指纹／加性模型已经吸收原生优势。出现部分支持时就报告部分结果，不把它计为完整入场通过，也不通过改 safe 奖励、窗口或种子救回构造。

所有臂继续拥有相同实际轨迹、奖励、当前控制器信息和逐步到达的目标标签；不得向候选单独提供条件奖励均值、未来情境或额外校准标签。保留既定先验与无调参协议，同时承认 additive 与 saturated 表示的先验几何并不相同，因此结果仍是实现包比较；单个臂差异不能单独量化“交互项”的纯因果效应。

成本保持既定 6 臂×3 个新块＝18 个 prospective fits：每 fit 2304 宏、6912 primitive ticks；合计 41,472 个宏／奖励标签／更新／精确评测面板和 124,416 ticks。独立训练单位是三个数据块，不是 18 个独立条件样本，也不是数万个评测面板。主要非 fit 工作是因果顺序、源支持、cell 统计及曲线读取；回归系统只有小型矩阵求解，精确评测不增加采样奖励。实际 wall/RSS 在该固定源处仍未测量，不能借用 B02 的秒数作保证。

5. 分歧声明与停止分支

MATERIAL_DISSENT: no。 B03 是合法且有判别价值的既有方法研究；目前没有发现需要改变科学设计的信息泄漏，或必须补充的、不同于候选本身的简单模型参考。

若完整 native 预测失败，应暂停这个构造的进一步投入，而不是继续找一个更有利阈值。若成功，应保留“已知联合规律、条件奖励平稳、终端单宏、三个探索块”这一范围，不升级为内生共同学习、一般 replay 校正或 HMASD/UAV 收益。在所指定固定源处，B03 尚未运行，以上全部是前瞻判断。

C — Skill information refresh
1. C05 已建立机会，不只是一个信息新鲜度代理

C05 的合法因果链清楚：接收方固定承诺和分支时刻不变；七字节任务上下文在 tick 0 发送、tick 1 到达；发送方的四字节快照只能在 tick 1 或 3 发送，延迟一 tick；所有臂每周期都支付 两包、十一字节，并有一次二元时序选择机会。发送方观察的是当前 X、已送达 w、校准风险 q，不是未来翻转。接收方按缓存位执行，不额外解码沉默。

因此：

Q
early
	​

=w+4(1−q),Q
late
	​

=w(1−X)+4,
Δ=Q
early
	​

−Q
late
	​

=wX−4q.

在 X=1,q=.5 时，w=1 应晚发，w=3 应早发；这些情况可以匹配 stage、age、cache change、clock 和 quota。改变的是接收方真实分支正确性的期望回报，而不是消息年龄的命名。

还可以直接核对其机会大小：以 PRE_LAST 的期望值 5 为基准，十八个等概率上下文中，早发的正增量为 .6、1.6、2.6、1，其余不选早发。因此

V
VoI
	​

=5+
18
.6+1.6+2.6+1
	​

=5.322222…

这是有限条件模型的代数计算，不是新增仿真或重复训练。

2. 四层判断不能合并

任务机会成立：这个宿主中，完整合法信息确实超过受限 stage/age/change 映射的能力。

合法表示成立于声明的信息制度：付费上下文及时到达，局部风险不是未来实现，固定接收器没有利用未声明状态。实际 SenderView 和 rollout 顺序与此一致。

有限可学习性有一个探索性训练历史的支持：C05 摘要记录 initial exact value 为 4，final learned value 为 5.322222222；十八个条件的最终贪心动作与 VoI 一致，严格条件错误数为零，参数确实移动，评测位移为零。结合

Regret=
18
1
	​

h
∑
	​

∣Δ(h)∣1{π
learned
	​

(h)

=π
VoI
	​

(h)},

这些摘要支持该有限上下文集合上的精确原生 regret 为零。它不是多 seed 稳定学习率、神经函数相等或一般分布外等价结论。

学习包的额外价值没有建立：在这个已知固定模型里，VoI 已直接比较两种合法动作的全部相关后果。学习器匹配它，是实现了机会，不是创造了超越强参考的机会。随机面板上即使出现偶然正差，也不能推翻其期望最优性；实际摘要中二者随机面板均值也相同。

3. 最强反例和必须保留的反面证据

C05 自己的 q=0 控制就是最干净的合法反例：不再有 obsolescence，AGE_CHANGE 与 VoI 的期望值同为 6，所称受限表示残差消失。因此，“固定技能＋有限消息机会”本身不充分；需要实际存在有价值的时机取舍。

更重要的信息边界是：付费 w、局部校准 q、固定接收器和不从沉默推断隐藏状态，都是模型条件。未经付费获得当前接收方意图，或者把未来 flip 当作风险输入，会改变信息问题；让接收方学习解码沉默，则改变了当前固定控制器问题。不能把这些变更作为原 C05 的“学习改进”。

整个 .322222 增益不能归给接收方上下文包。 在仍知道 q、但用 w 的已知平均值的规则之上，收到具体 w 的独立增量只有 1/18=.055555…。而所有比较臂已经支付七字节上下文，因此这不是“购买该包相对其他带宽用途的净收益”。

C03/C04 和 CADC 的反面证据也没有被 C05 推翻。C03 的 release-priority 修复减少了 stale-release waits，却使两个相关冻结策略分别少完成 9 和 5 个任务；C04 的较强 stage-only 参考吸收了此前小幅学习优势；CADC 的历史单训练配对仍是净服务 −.013354921301 的 adverse 观察，碰撞计数并不单独识别原因。它们分别约束旧解释，既不能推出刷新机会普遍不存在，也不能被新的无碰撞小模型“洗白”。

原论文边界同样重要：Soleymani 等的 VoI 最优性建立在特定控制模型、因果信息集及联合控制／触发选择上；SchedNet 同时训练编码、动作选择和调度，并明确考虑接入机制。它们不能提供固定技能下额外学习收益的现成证明，也不能授权免费的反馈或优先级通道。
KTH个人主页
+2
arXiv
+2

4. 现在不选择新学习批次；具体重入应围绕“未知但决策相关的量”

建议暂停这个已解固定宿主上的 learned-scheduler 增量投资，新增 fits 为 0。 不再增加 seed 以证明学习器能够持续匹配已知精确规则，也不因 toy 成功就自动迁移到 UAV。C05 一 fit、512 optimizer updates、255,480 总 team ticks 的既有成本和正面机会结果都保留。

能够改变这一选择的单一最小新观察，是一条具体目标宿主的信息—动作链，证实存在合法可估计、且影响两个固定接收方动作机会相对价值的未知量。不是再找一种 age 阈值，也不是先要求学习器已赢。

一个具体的重入形式可以是：目标仍有两个固定分支机会，已收费、带时间戳的任务请求在第一个机会前到达；发送方实际传感器只给局部 regime z，而非已经校准好的 q，q(z) 必须由双方同样可取得的既有合法历史估计。需要关心的中间量不是平均校准误差本身，而是估计是否把

q(z)放在wX/4

的错误一侧；原生后果是早／晚选择是否因此使真实分支任务损失增加。

这只是明确的重入条件示例，不是材料已经证明存在的目标映射。当前指定输入没有提供这样的目标接口、日志支持和反馈成本，所以我不据此选择新实验。

届时最强基线应是用相同历史学习 
q
^
	​

(z) 或条件转移、再执行预算感知 VoI 的透明 plug-in 规则。候选与基线必须共享校准样本、奖励获取权、延迟、包头／请求成本、接收器和调参机会；不能给候选额外的正确性标签或模拟器查询。若普通估计加 VoI 已吸收 native 差异，就应停在普通路线，而不是再弱化参考。

这一方向的最小非 fit 工作，是对现有目标信息链作定向读取：时间戳、请求到达时刻、可观测状态、合法反馈和真实 early/late 支持。两条事后看起来不同的轨迹，不足以识别两个反事实发送值；需要已有真实行动支持，或同数据可识别的条件模型，不能复制未观察分支。没有这类来源时，缺口就是目标映射尚未建立，而不是一个等待审批的问题。

5. 分歧声明

MATERIAL_DISSENT: no。 我认同 C05 的正面存在判断和零学习增量判断。我的投资建议更明确地停在这里：保留 VoI 为当前实现；目标映射未出现前，不继续这个 learned line。这个暂停不意味着信息刷新方向不存在机会，也不撤销 C05 的单历史可学习性观察。

结论对三个 DM 的实际含义

A：普通方法足够，已经是这个局部条件的实质答案。 不应再用同一个共享前缀故事为额外算法成本辩护；也不应把暂停写成一般不可能性。

B：普通方法就是候选，但其有限样本使用价值仍是未回答的问题。 既定 B03 足以作一次有界判别；不需要另造一个与候选相同的“强基线”，也不能把成功卖成普通方法之外的新校正。

C：机会存在且已被一个训练历史实现，但当前透明规则已经完成了全部决策计算。 下一项学习理由应来自合法、目标相关的未知量，而不是来自正 toy 的惯性。

这三项建议不要求更多顾问一致意见，不要求穷尽所有解释，也不新增实验批准条件。本次没有启动实验、改变任何预写科学参数或写入仓库；实际成功的 GitHub Answer 提交：无。

## 2026-09-20 — A post-Pro decision: retain ordinary reuse; pause direction investment

**Delivery and ownership.** The complete cross-direction answer was saved from chat in
`8904327f9598d4896cb9425550f84584deaa902a`. Before insertion the remote question and empty
Answer were byte-identical to `f3fe65778da4e58fb5eb0ca7a34f9c6896c9c945`; the answer body
compared byte-for-byte with Root's collected file. Its final LF explains the two recorded
hashes. Even its one trailing space and display-extracted formula/citation fragments were
preserved. Nothing was resent and no private conversation address was published. The
answer-only loan is reconciled and A's DM again owns this notebook. I read the complete
answer; the adoption below concerns A only. B/C's DMs own their respective decisions.

**Adopt, clarify and do not infer.** I adopt Pro's distinction between an available
ordinary route and a route that is adequate at a specified exposure. Entry condition 3
asks whether *additional complexity* has a useful discriminant; it does not forbid an
existing-method study or make prior ordinary-method failure a permission requirement.
An ordinary sufficient route can itself be a useful answer to a bounded research question.
I retain the A01/A02 reading unchanged, including the genuine multistep gain over one-step,
mixed Retrace-minus-Q(beta) primary, adverse long-minus-matched primary, contrary early
A02 panel, corrected fixed-denominator update and package-not-component interpretation.

I also adopt the qualification that the DAG's eight backups count work **after obtaining
the specified coverage**, not the cost of collecting it. Its nine primitive rows are
constructed legally realizable records, not a new collected dataset. The strict zeta=0
two-world counterexample is an identification result; positive support with a finite
missing branch is not that impossibility. For an unknown R-service success probability
theta in the DAG, `Q_L^beta=7 theta/8` crosses safe=.75 at `theta=6/7`, as Pro observes.
That is a possible decision-sensitive estimation problem, not a demonstrated current use
need or a newly selected fit. The ordinary rival must have the same observations and
uncertainty information. I do not adopt a claim that a sufficient statistic or a plug-in
model is automatically the most efficient finite-data estimator.

Source-use limits matter. Pro identified the intended umbrella source and its correct
blob, which our own pre-insertion check independently verified. It disclosed that it did
not redo all A/B raw-array checks. I rely on A's earlier actual readback for those facts,
not on Pro as additional replication or engineering verification. Its A arithmetic and
consequential Q(beta)/intra-option source boundaries agree with the independently checked
passages and algebra above. No extra consultation is needed merely to increase agreement.

### Additional read-only discrimination while transport was running

The notebook was not edited during its loan. I checked one specific finite-resource
countercondition rather than enumerating new hosts: marginalizing unobserved option paths
when different options share primitive actions. It supplies the following **positive
efficiency opportunity and ordinary reduction**, both analytical, not new runs.

First, this mechanism was absent in A01/A02. In
`experiments/candidates/termination_rule_experience_reuse/off_termination_a01/host.py`,
`closed_loop_move` maps L/R to stay/right at position 0, left/right at 1–3, and left/stay
at 4. Given position, the primitive move identifies the option. Thus those empirical
comparisons cannot refute a benefit from marginalizing ambiguous option labels; their
scope is not silently enlarged by this new question.

Second, there is a relevant stronger ordinary multistep precedent: Jain and Precup,
*Eligibility Traces for Options*, AAMAS 2018,
[primary PDF](https://www.ifaamas.org/Proceedings/aamas2018/pdfs/p1008.pdf), sections 2–3,
Eq.1/5/12 and the trace algorithms. I checked the primary derivations and their section 4
experimental conditions. They include action-compatible option-action learning and
option-path multistep corrections. This is not evidence that the paper already implements
complete action-history marginalization, nor that its function-approximation results
guarantee convergence or a MARL advantage. The narrow local catalog query had no match;
that miss is not a novelty conclusion.

Here is the ordinary reduction for fixed known Markov controllers on a common legal
state. Let H contain the primitive state/action/
reward history, initial option and all required observed teammate commitments, but not
the intermediate nominal option/renewal path being marginalized. For each law v in
{beta,zeta}, maintain its conditional option belief b^v. The observed-action likelihood,
posterior and next belief are

`ell_t^v = sum_o b_t^v(o) pi_o(a_t|x_t)`,
`bpost_t^v(o) = b_t^v(o) pi_o(a_t|x_t) / ell_t^v`,
`b_(t+1)^v = bpost_t^v K^v(x_(t+1))`.

The ratio `ell_t^beta/ell_t^zeta` is precisely ordinary history-policy importance
sampling. Under positive support and no omitted termination side effect, the unknown
environmental kernel cancels for the same physical state/action history. With
`K^v(o'|x,o)=(1-v_o(x)) 1[o'=o]+v_o(x) mu^v(o'|x)`, the filter arithmetic uses O(K)
per step given the evaluated controller probabilities: a diagonal term plus one weighted
renewal sum. This is O(TK) for **one fixed starting belief**, not a cost guarantee for
every start row/initial option in a learning batch. Controller evaluations, extra filters
or a justified shared computation must be counted for both methods. No full S-by-S
environment model is required by this ordinary reference. If controller memory depends
on a counterfactual initiation history, a belief over option labels alone is insufficient:
the joint option/memory state must be treated explicitly. The O(K) count does not price
that larger class for free; the present bridges use Markov controllers.

For an untruncated IS return G(H), `E_zeta[W_option | H]=W_action` implies that the
action-history estimator is a Rao–Blackwellization. In the earlier three-opportunity DAG,
conditional on initial L, the first transition to R occurs at steps 1/2/3 with behavior
probabilities `1/8, 7/64, 49/512` and option-path weights `4, 16/7, 64/49`. The return
estimate has mean 7/8 and second moment 134/49. Marginalizing the shared prefix gives
R probability 169/512, R weight 448/169 and second moment 392/169: a strict variance
reduction of `3438/8281`. This is a finite-efficiency difference despite identical
underlying information, but the same-data small branch model still covers this DAG.

The independent Critic also checked a random-loop analogue, removing dependence on an
acyclic example. Start safe (payoff .5) or L with positive collection probability. At a
common state both skills take the same action: with unknown environmental probability
p_exit it reaches a fork, otherwise it returns to the common state. Renew after each
such move with probability eta; the selector always picks R. At the fork, L/R execute
different terminal actions with true payoff 0/1, learned from actual outcome observations.
Both terminal actions have behavior support. This is a **single-agent bridge**, not the
old four-tick teammate model: its unbounded geometric waiting time cannot silently assume
that an old finite teammate commitment remains unexpired. Gamma=1 is justified here by
bounded terminal returns and almost-sure arrival for p_exit>0, not a discount contraction.

`P(T=t)=p_exit (1-p_exit)^(t-1)` and
`P_eta(R at fork)=eta/[p_exit+(1-p_exit) eta]`.

At true p_exit=.5, target beta=.5 gives value 2/3, behavior zeta=.125 gives 2/9, and safe
is .5: there is a genuine native decision opportunity. Given T=2 and the R terminal,
option-path weights are 4 or 16/7 with behavior conditional probabilities 8/15 and 7/15;
the action-history weight is always 16/5, eliminating conditional variance 128/175.
Nevertheless the ordinary history-policy reference uses the identical filter/weights.
This small loop also admits a practical empirical model using exit counts and real
terminal observations; its structure or replay cannot be denied to manufacture a gap.

I accept the Critic's two important limits: this variance argument does **not** directly
apply to clipped Retrace, an option-specific bootstrapped TD update or learned native J;
the value/readout transformation must also be valid. And the single-query filter work
does not price all-start-row training. The independent check is mathematical criticism,
not empirical replication. No scripts, new trajectories or fits were run for these bridges.

### Direction decision and actual re-entry condition

**Pause this direction's current investment; retain the ordinary reuse route.** There is
no selected next learner, collector comparison, confirmation claim or live operation.
This is a direction-level investment judgment under the owner's requested re-entry, not
a change to the owner's global pause and not a theorem that termination reuse is useless.
Root can record the paused investment in A's standing; A remains recoverable at its
published code/results. No evidence or worktree is being removed.

The reasons now go beyond one failed package: A01/A02 did not support their extra-benefit
predictions; a source-grounded shared-prefix opportunity has an explicit finite-work
ordinary solution; a random-loop finite-variance opportunity has an equally legal ordinary
history-policy implementation; and the genuinely unsupported alternative cannot identify
the new action branch. A hypothetical algorithm versus that exact same history estimator
would have identical trajectory targets and updates when read out identically, so a
learning batch between their two names would not answer a new question. A different
finite estimator could have different bias/variance/native decisions, but none is selected
by the present evidence merely because such differences are possible.

What is strengthened is the existence of lawful off-termination learning and concrete
ordinary solutions when fixed controller semantics, required teammate state and action
support are retained. What is weakened is a reason to add the tested trace/collector
complexity or to revive the shared-prefix story as an unaddressed special correction.
What remains unresolved includes real target uses near an estimation-sensitive decision
threshold, harder approximation/compute regimes, hidden-but-inferable commitments and
endogenous teammate changes. The current algebra and small-host fits do not establish
UAV value, general estimator optimality or a stable population ranking.

Re-entry needs a **concrete use/research question with a distinguishing prediction**, not
permission, a new algorithm, a prior proof or a positive pilot. For example, an actual
supported target decision could be sensitive to finite estimation error at declared
exposure; compare the distinct estimators with shared data/uncertainty rights, measuring
fixed-query bias/variance and full computation together with the learned target decision's
native return. A real recurrence/precision decision could also justify replication.
Neither need be known to favor a new method. No such current use is identified, and no
producer is being awaited to invent one. Do not automatically sweep beta/alpha, add seeds,
transfer to the UAV host, or read Claude B08 to fill that absence.

Incremental cost since A02 remains **zero fits and zero new simulator trajectories**;
cumulative actual cost remains the 15 started/read local-CPU fits reported above. Advice,
source reading and exact algebra are not additional training evidence or a wall-time
measurement. The Pro answer is fully collected and interpreted for A; Root's remaining
role is shared-index integration, not scientific approval or a launch dependency.

## 2026-09-20 — Final feasibility verdict: NOT_VIABLE_CLOSE

**Decision: close `termination_rule_experience_reuse` as an independent research
direction in its assigned fixed-skill, fixed-termination-rule scope.** This is the DM's
current binary feasibility judgment under the owner's narrowed direction space. It
supersedes the preceding idle, paused-investment and open-ended re-entry arrangements,
including the immediately preceding entry. No admission investigation, future comparison
or producer remains assigned to A. Root should remove A from active investment and record
the direction as closed/archived in the shared index; that integration is administrative,
not permission needed for this judgment. The owner's global pause is unchanged.

### Answer to the original question

Experience generated under one termination rule can lawfully improve learning for another
rule. A01 already supports the practical value of ordinary multistep reuse relative to its
one-step reference. The target rule changes a known controller transition law, however,
not an otherwise new environmental law. With the required physical/controller state,
teammate remaining commitments and actual action support retained, its identifiable
effects belong to ordinary target-rule Bellman learning, Q(beta), augmented-state/SMDP
learning, action-compatible intra-option learning, or model/history-belief off-policy
learning. Direct adaptation of those methods is a legitimate solution, not an independent
new correction merely because the experience has another termination label.

The DAG and history-filter reductions cover both a real target-decision change and a
strict finite-variance opportunity. In the latter, the proposed marginal correction is
exactly the ordinary same-information history-policy likelihood ratio. This is not only
an appeal to an unlimited state representation or asymptotic convergence. The DAG has a
small same-data branch model/action-compatible reverse update, and the marginal filter
has explicit finite arithmetic, with its all-start-row and controller-memory costs kept
visible. An added learned gate would change the assigned question and is excluded.

If the target requires an action branch with no behavior support and no independently
justified model knowledge, the two-environment construction gives identical legal data
but different target values and decisions. That branch is not identifiable here. The
observed suffix of continuing the old skill is not the outcome after earlier termination;
relabeling it cannot supply the missing data. Finite missing coverage despite positive
support is instead ordinary sampling uncertainty, not this impossibility result.

Thus, within this scope, lawful identifiable reuse is an ordinary learning problem,
whereas the unsupported alternative is not learnable from the admitted observations.
That classification does not say every ordinary estimator has the same finite-data
performance. It says there is no remaining independently specified termination-reuse
object, with a distinct legal target and practical discriminant, for this direction to
continue pursuing now.

### Evidence supporting closure, including contrary evidence

- A01: both multistep arms improved on one-step in all three independent training blocks.
  Retrace minus Q(beta) primary mean was +0.00000904, with mixed seed signs and a wide
  interval. This supports ordinary reuse, not stable extra value from the selected trace
  correction. It is not an equivalence result.
- A02: the long-behavior package increased endpoint occupancy and effective trace mass,
  as predicted, but long minus matched primary was negative in all three new blocks,
  mean -0.00753038. The interval remained wide and the early panel favored long behavior
  on average. The selected package did not earn continued investment; these observations
  neither isolate the causal component nor establish general long-collector inferiority.
- The shared-prefix DAG separates the target value 7/8 from behavior value 169/512 and
  safe value 3/4. Its nine constructed legal primitive rows support the ordinary solution
  in eight scalar backups after coverage. The count is not a collection-cost claim or
  an additional empirical result.
- Marginalizing option paths strictly reduces untruncated return-estimator variance in
  both the DAG and random-loop analogue, but an ordinary history-policy filter produces
  the identical weights. The latter bridge is single-agent, not evidence about persistent
  unobserved teammate commitments. Its variance statement does not prove a clipped-TD or
  native-return ranking. The zero-support example closes only the genuinely unsupported
  alternative.

The conclusion therefore does not rest on a failed package alone. It combines the
empirical extra-benefit failures with explicit ordinary reductions of the strongest
lawful counterconditions examined and an identification boundary for the unsupported
case. The fully observed fixed service host is the available collected-data/target
interface. The bridges are exact constructed examples, not an existing new target use.
No current legal host/data/target combination supplies a distinct next comparison that
survives the same-information ordinary references. Merely saying that finite samples,
approximation or computation might matter does not identify one, and is not retained as
a standing task or a reason to keep A active.

I read the complete Pro answer preserved in
`8904327f9598d4896cb9425550f84584deaa902a`. I retain its qualifications about coverage
cost, finite estimation, non-equivalence and ordinary reuse, and its recommendation not
to extend the current incremental learner/collector pathway. Adviser agreement is not
independent empirical evidence or an approval gate. The final closure, rather than the
previous pause, is my own direction judgment under the owner's current binary request.

### Closed scope and preserved result

The rejected proposition is a currently viable **independent termination-rule experience
reuse research direction** under these fixed skills/rules and admitted observations.
It is not that off-termination learning is useless, that all finite estimators are optimal,
or that arbitrary hidden-state, adaptive-teammate or UAV problems have been disproved.
Those different questions are not carried forward as A's open work. There is no final
confirmation claim and no queued fit, new toy, sweep, replication or consultation.

All 15 actual fits are collected and scientifically read. Incremental cost since A02 is
zero fits and zero new simulator trajectories. Published code, raw outputs, notebook
history and the verbatim Pro answer remain intact; no process is stopped and no evidence
is deleted. This entry closes A's scientific work and replaces its earlier open-ended
standing, leaving only Root's shared-index record of `NOT_VIABLE_CLOSE`.
