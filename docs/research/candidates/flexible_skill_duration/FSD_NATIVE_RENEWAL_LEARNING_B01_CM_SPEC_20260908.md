# FSD_NATIVE_RENEWAL_LEARNING_B01 — complete prospective CM task

## 1. Deliverable, checkout and source

Prepare one runnable research implementation of the
[science card](FSD_NATIVE_RENEWAL_LEARNING_B01_SCIENCE_CARD_20260908.md), with focused
synthetic boundary tests and independent source review. This specification is
the complete next implementation request under P30; it is **not yet a coding or
scientific execution allocation**. A later bounded CM assignment implements it
without constructing a real HMASD model, loading a checkpoint, collecting a
scientific host episode or sending a Pro request. P30 explicitly records the
three CM-comparison batches exhausted: no fourth comparison is enrolled.

Reuse `C:/Projects/HMASD-worktrees/codex-fsd`, `codex/fsd`, across DM/CM/reviewer.
Complete starting code: **ebce42e23e8a86b4e8d44f840441d166828fbe54**. This is the
merged P30 plus direction checkout, not main alone. Documentation publication
will be a descendant without source changes. Record actual starting status;
preserve unrelated work and serialize overlapping edits/index use. Do not create
an object/stage branch or edit the fixed Pro request or archived response.

Own only:

- `scripts/run_fsd_native_renewal_learning_b01.py` (new, <=600 lines).
- `tests/experiments/candidates/flexible_skill_duration/native_renewal_learning_b01/test_learning.py`
  (new focused suite).
- A concise `FSD_NATIVE_RENEWAL_LEARNING_B01_TECHNICAL_ACCEPTANCE_<date>.md` in this
  direction for source/check/review facts. Scientific card/intake edits remain DM-owned.

Do not modify `hmasd/`, `config_1.py`, `envs/relay_corridor/`, E0/E2/E3/A01 runners,
historical tests or their evidence. No persistent checkpoint is needed: each
learned-arm invocation trains and evaluates its endpoint in the same process.

## 2. Read these implementation entry points, not the old experiment contracts

All paths below bind to the starting source. Reuse suitable helpers directly;
small object-local code may avoid an irrelevant historical runner dependency.
Do not invoke an old runner's main/_execute or inherit its extra panels/guards.

| Entry point | Reuse or boundary needed here |
| --- | --- |
| `envs/relay_corridor/config.py` `proposal_config("large")` | The exact existing N6/K2/H400 large Bernoulli host. |
| `scripts/run_flexible_skill_duration_e3.py` `arm_parameters("large","d2")` | c/c_Z=.25, caps40/400, delta1, age off; same for both learners. |
| `envs/relay_corridor/hmasd_driver.py` `build_corridor_learner_config`, `run_rollout` | Real collection/storage/update ordering, action decode and existing config dimensions. Implement the two local changes below rather than editing this shared driver. |
| `hmasd/agent.py` `step`, `store_transition_batch`, `_d2_store_transition`, `update`, `reset_env_state`, `clear_buffers`, `get_d2_metrics` | Authentic sampled decision/credit path and the actual objects receiving each arm's native reward. Expand into direct callees only to resolve a concrete integrity question. |
| `scripts/run_flexible_skill_duration_e2.py` `_execute` learner/update section; `CorridorEvaluator.__init__`, `_sync`, `_reset_lanes` | Full learner and independent final active-module/ValueNorm synchronization. Avoid old enumeration, checkpoint publication, intermediate panels and diagnostic recorders. |
| `scripts/run_flexible_skill_duration_e0.py` `_preserve_rng`, `_StepCounter`, `_capture_theta0`, `_exposure_line` | Instance-bound actual optimizer-call counts and float64 relative initialization displacement; no new telemetry framework. |
| `scripts/run_fsd_native_renewal_control_a01.py` `apply_renew_mask`, `evaluate`, `summarize_panel` | Applied-mask and native measurement semantics only; do not inherit A01's checkpoint loading, fixture mode, limits or fixed artifact. |
| `envs/relay_corridor/references.py` `GreedyOnPublicState.reset`, `act` | Existing public G reference, as imported by A01. |

The implementation-relevant mechanism references are the P25 immutable response
sections 三–六 and this card sections 2–4. Prior ACAC/UTE literature distinctions
were already taken into P25: a supplied public rule is not learned termination,
and internal segment credit differs from a physical lease. No further retrieval
or new research interpretation is assigned to CM.

## 3. Exact setup and training seam

Use one plain argparse runner with policy C, H or G, output path and a recorded
launch SHA; H also accepts existing C/G summary paths for same-invocation paired
publication. Card constants bind seed/master 770203, evaluation master 770204,
five rollouts, 16 training lanes, H400 and 32 evaluation lanes. Do not add sweep,
resume, tuning, intermediate-evaluation or scientific fixture CLI modes.
The launch SHA is a provenance field, not a predicate that refuses a run.

For each C/H process, set CPU/four Torch threads before model construction;
seed Python/NumPy/Torch independently with 770203, then build a separate adapter,
config, learner, optimizers and normalizers. The base driver's constructor forces
one Torch thread, so use its builder and `HMASDAgent` directly or an equivalent
object-local setup that starts at four. Keep all bound defaults, including
n_Z6/n_z2/action2, gamma.99, GAE.95, PPO15/minibatches4 and ValueNorm on with
obs/state normalization off. The existing builder determines buffer dimensions;
these dimensions are not measured segment or optimizer counts.

Do not implement H by changing the learner's policy-interruption mode. Its
internal D2 remains identical to C's configuration. Collection must have this
concrete order in the new runner:

1. From this arm's current states/observations/env_steps/dones, call its real
   `agent.step(... deterministic=False, return_step_data=True, build_infos=False)`.
2. Keep the returned actions and complete original step_data. Copy the internal
   bool mask. Before host.step, read the **current** public
   `host.change_flag[:, host.region_of_agent]`. C applies the copied internal
   mask; H applies that mask at episode t=0 and the public flag at t>0.
   The applied mask is a separate array, never an alias written into step_data.
3. Call this adapter's `step(actions, renew_mask=applied)`. Native reward is
   `info["shared_reward"]` in float64, not a copied C value or a role target.
   Store the actual pre-state/observation, actual actions, actual reward, real
   terminal next-state/observation and actual done flags through
   `store_transition_batch`, with untouched sampled step_data and rollout index.
4. Only after terminal storage, advance this adapter's episode IDs, reset the
   adapter, and set **both** the next policy state from reset_info["state"] and
   next observation from reset_observations. Reset the lane's skill/RNN state
   with the existing `reset_env_state`, env_steps=0 and done bookkeeping.
   The current shared driver stores terminal next-state correctly but then
   assigns that old state alongside reset observations. Correct this next-input
   seam locally for both new arms; do not rewrite old results or the core driver.
5. After 400 steps, call the real `agent.update` with 400 buffered steps, terminal
   done values, coherent current state/observation and the existing zero terminal
   bootstrap values. Capture completed D2 metrics and raw segment-count summaries
   **after update, before clear_buffers**; then clear buffers and collect the
   next rollout with updated parameters. Do not call an extra flush that creates
   duplicate segments or updates. Preserve gamma-to-elapsed-duration credit.

No internal reset occurs at a public applied renew. H's own native trajectory is
what its authentic D2 reward accumulation sees. The two arms have paired initial
weights/exogenous keys but no later shared normalizer, optimizer, RNG object,
hidden state, endogenous state, action or reward tape. Record the five consumed
episode-ID blocks; do not report the post-reset next block as already trained.

Keep lightweight rollout aggregates rather than full replay: actual transitions,
completed episodes, native return, internal/applied renew totals, real update
stage count, per-network optimizer-call deltas/totals, coordinator inference
calls, `rows_M_agent`, `rows_M_team`, total rows and actual individual/team segment
counts and length summaries. Use the existing raw metric lengths before buffer
clear where necessary. A row count is labelled as its actual quantity, never
silently substituted for a coordinator optimizer step or legacy cost-law M.

Capture initial parameter norms and `_exposure_line` after every update for
coordinator, discoverer actor, discoverer critic and both active discriminators.
Count a bound optimizer's actual step calls, including zero when observed; do
not synthesize five updates per network. At least the first/final displacement
and all five count rows must be readable. A failed counter limits dependent
learning-exposure claims; never infer them from environment steps.

## 4. Final evaluator and public reference

After exactly the fifth real update, within `_preserve_rng`, construct one
independent 32-lane evaluator as in E2, sync the final active coordinator,
discoverer and discriminators plus arm-local enabled normalizers/ValueNorm.
`train(False)`, deterministic actions, no_grad, clear buffers and reset all lanes.
Construction and all subsequent evaluator work must preserve learner RNG, and
evaluation must not alter the learner's state/normalizers or make optimizer calls.
All evaluator model/optimizer construction costs count inside the learned arm;
there are two training starts and four total HMASDAgent constructions in the panel.

Use evaluation master770204 and IDs0–31 in every policy's own fresh adapter.
Implement the same C/H applied-mask seam during scoring but no transition storage
or learning. G constructs no learned agent and uses the existing public greedy
controller's own reset/act on its own host. Use exactly one H400 batch per policy,
no prior-checkpoint panel or final-policy replay.

Implement card §4 directly: float64 full/post returns, all 32 paired differences,
mean and sample SE, per-episode and pooled eligible/wrong counts, NA for no
eligible opportunities, reward-unit role loss, separate internal/applied renewal
counts. Return arrays remain ordered by actual episode ID. G's internal-mask
count is not applicable. H's role-loss-to-G-shortfall residual is a reported
number, not a guard or unique attribution. The primary source is the adapter's
actual `shared_reward`; do not infer reward from a diagnostic classifier.

## 5. Minimal outputs, complete caps and failure dependencies

Runtime artifacts live under `temp/directions/flexible_skill_duration/exp/` with
one ordinary object/run root and separate C/H/G outputs. A later launch assignment
names the concrete root and exact source SHA. Publish a small JSON summary for
each policy and the required H−C/G comparisons inside the final H invocation.
The intended later command list is G, C, H, one invocation each; it is no new
orchestrator. H reads existing C/G summaries as data and never executes them.
Keep a trustworthy pair result if G is unavailable and label only its reference
quantities incomplete. No complete learning pair is published if either learned
arm has not completed five updates and its endpoint. A companion arm can be
collected independently if a prior arm fails; this does not permit a retry.

Each JSON contains identity/card/launch SHA, actual policy/seed/keys/config and
device/thread/precision facts, model/training/evaluation/count exposure, the five
training rows (learned arms), 32 evaluation arrays, primary/secondary quantities,
completion/failure facts and available wall/peak-RSS evidence. Ordinary paths
and source fields suffice. Use built-in JSON; no internal schema validator,
byte manifest, checkpoint, full tape, version layer or provenance refusal.
Partially completed sums must have actual step/episode denominators or be named
partial sums; they may not masquerade as complete H400 means.

The complete future limits are **900 s for C, 900 s for H, 60 s for G; 1,860 s
summed invocation wall**. The authoritative external command timer starts before
the interpreter/imports and ends after publication. Start the runner's cooperative
clock before heavy imports; check it at ordinary collection/update/evaluation
and publication boundaries. Later execution uses the existing supervisor and a
fixed OS timeout for the complete command, without retry/restart machinery. A
long individual update cannot silently lift the complete cap. Publication and
H's paired arithmetic are inside H's cap, with no separate post-run computation
used to complete the scientific panel. External observed wall remains the final
cost fact even when a pre-publication timestamp is also written.

Preserve actual partial rows/counts at completed boundaries so an external cap
does not erase work facts. On deadline, nonfinite learner/primary values or a
defect threatening reward/information/storage/update/primary comparison, stop
the dependent work and leave the current log and partial output. Report the
observation and specific missing quantities; do not diagnose unseen root causes.
No shortened complete result, stitching, extension, alternate seed, cap increase
or automatic second launch is allowed. Required primary damage limits that
claim under evidence §11.8.7; valid negative results and missing optional resource
telemetry are retained. Do not impose all-network displacement positivity or
G dominance as success gates.

Prospective counts and per-arm historical cost anchors are in the card §6 and
[machine calculation](FSD_NATIVE_RENEWAL_LEARNING_B01_EXPOSURE_AND_COST_20260908.json).
New M-dependent update work is unknown; this implementation assignment adds no
cost probe or actual learner construction to estimate it. If code inspection
shows the selected task cannot fit its bounds, return the concrete fact to DM.

## 6. Focused acceptance and assignment stop

Use one focused pytest suite in the owned test file, bounded to 300 s of complete
test-process wall, with synthetic fake agents/adapters and hand-computed arrays.
Tests call the real new collector/evaluator/summary functions through monkeypatched
production bindings; do not add a fixture CLI or a reusable injection framework.
No HMASDAgent construction/load, scientific host episode, model update or
scientific result-bearing invocation occurs in this implementation assignment.
Imports/config inspection and fake boundary work are ordinary engineering checks.

Required meaningful changed-boundary coverage:

- A stateful fake supplies differing internal/public masks at reset and t>0.
  Run the actual collection seam and prove host applied masks follow C/H rules,
  actions/step_data remain authentic, native reward/actual terminal next-state
  reach storage, and public renewal never calls an internal reset.
- Give terminal and reset state/observation deliberately different sentinels.
  Check stored terminal values, next policy's coherent reset pair, per-lane
  reset/episode advancement and real collector update-before-clear ordering;
  capture metric/count results before clear and show next rollout uses updated
  fake policy state. This tests the production seam, not a second toy collector.
- Exercise actual evaluator construction/sync/reset boundaries with distinct
  fake module and ValueNorm states; check enabled statistics are copied from the
  correct learner, no shared mutable state or update occurs, and RNG is preserved
  across construction and scoring. Independent review follows the real E2/HMASD
  methods as source support, without creating a model for this test.
- Hand-calculated paired arrays check signs, full/post denominators, ddof1 SE,
  G gaps, opportunity-conditioned wrong counts/loss and zero-eligible NA. A
  truncated fake run must remain incomplete with true counts; no complete pair
  or branch arises from a missing learner or damaged primary output.
- A controllable clock exercises setup, collection/update, evaluation and
  publication deadline checks, plus nonfinite primary data. Check source placement
  of the clock before heavy imports and the later complete-command timeout
  requirement; no timed scientific calibration is part of this suite.

Obtain one independent source review of mask→actual storage/credit/update,
terminal/reset and evaluator/normalizer/RNG semantics, actual exposure counting,
primary publication and scope. Review the changed implementation and direct
bindings, not the old scientific history. Return focused corrections to the
same available CM and reviewer. Required review does not allocate a run.

Acceptance is runnable changed code, trustworthy focused check/review evidence,
readable true future exposure and correct claim/stop semantics. Test success is
engineering conformance; it is not a learning result or a scientific launch.
No new ENGINEERING_SCOPE_SPEC §4 machinery; <=600 runner lines and <=2,000 new
non-test research lines apply, with the 30% orchestration ratio only a review
signal. Commit by owned pathspec, with required attribution/scope trailers,
and push immediately. Return the full commit, paths, tests/review evidence,
exact remaining issue and future invocation syntax; do not launch it.

Controlling acceptance: card §§2–4,6–7; evidence spec §§4,5.2,11.4,11.7–11.9;
ENGINEERING_SCOPE_SPEC §§4–5; actual `.codex/hmasd-compute.toml` and resource
admission apply only to a later allocated invocation. This is one complete CM
assignment, with ordinary corrections retained in it and no fourth comparison.

## 7. Five-item handoff for the next bounded assignment

1. **Deliverable:** implement this one prospective B runner, focused synthetic
   suite and independent review/technical acceptance; no real model or scientific
   invocation. Follow the complete specification above and the linked card.
2. **Owned paths/source:** the two new code/test paths in §1 plus the technical
   acceptance document; shared FSD checkout `C:/Projects/HMASD-worktrees/codex-fsd`,
   branch `codex/fsd`, complete code base `ebce42e23e8a86b4e8d44f840441d166828fbe54`.
   Reconcile the published doc descendant before editing; preserve other work.
3. **Preserved semantics:** card §§2–3 and specification §§3–4: own fresh C/H
   trajectories and normalizers, authentic internal D2, H-only applied public
   renew, correct terminal/reset state, final independent deterministic evaluator,
   exact seed/keys/population/precision; no historical/core edits or extra arms.
4. **Acceptance:** specification §6's production-boundary synthetic checks and
   independent source review, card §4 quantities/§5 claim ceiling/§6 counts and
   complete caps, evidence §§4,5.2,11.4,11.7–11.9 and scope §§4–5. Publish actual
   checks/source facts; scientific validity awaits a separately allocated run.
5. **Budget/stop:** <=600-line runner, <=2,000 new non-test research lines, one
   <=300 s synthetic suite; no implementation-stage model/host/learner/Pro Send
   or fourth comparison. Future 900/900/60 s complete caps are implemented but
   unallocated. Stop at committed/pushed reviewed code or a concrete scoped gap;
   return to DM through Root with no launch or scientific follow-up selection.
