# DISH B07 complete CM implementation handoff — 2026-09-08

This is the full code specification and original acceptance for the selected B07 card.
It is delivered to Root before coding. The present DM task authors these files only;
no CM has been dispatched and no implementation or scientific invocation has started.

## 1. Deliverable and goal

Implement a runnable **single seed127 paired B07 study**, OWN_COMMAND_MEAN versus newly
trained DIRECT_MEAN, with coherent live/replay likelihood and the complete primary/native
companions in `DISH_OWN_COMMAND_MEAN_B07_SCIENCE_CARD_20260908.md` §§2–6. Deliver the code,
one focused synthetic check, and a CM implementation record with its measured check
charge and remaining scientific allowance. The engineering assignment stops at a reviewed,
inspectable implementation; no real initializer, native episode, learner or result-bearing
run is purchased by it. The later real pair has the card's one scientific allowance.

Use one thin `argparse` runner and one B07 study module, retaining existing numerical,
training and native paths. Runtime output later is one run's `summary.json`, its existing
checkpoints/resets and logs/partial output, under
`temp/directions/degraded_incumbent_shadow_handover/exp/own_command_mean_b07_<run>/`.
Do not build another framework, scheduler, schema validator, provenance gate, checkpoint
manager, native source fork or generic policy factory.

## 2. Starting code, owned paths and direct entry points

Designated checkout: `C:/Projects/HMASD-worktrees/dm-dish-b06-scientific-intake-20260907`.
Branch: `codex/pro-dish-post-b06-20260907`. **Complete starting source:**
`5b9390ba2da7c2002a512505c2a13f3045a57ab1`; this authoring task began clean there.
The relevant B02/B03/B04/B06/first-trigger/r06 source content is unchanged from accepted
B06 launch `373d187200a91942385e9380770dcf9f8098aada`. The delivery commit adds documents
only. Root supplies the complete committed delivery/card/spec and this source, preserving
unrelated work and reconciling current instruction inputs before dispatch. Do not copy
uncommitted code into a remote execution checkout.

CM owns only these code/test surfaces and its implementation record:

| Owned path | Required change or permitted bounded plumbing |
| --- | --- |
| `experiments/candidates/degraded_incumbent_shadow_handover/own_command_mean_b07/study.py` and minimal package `__init__.py` | New B07 composition, explicit arm labels/mode, own references, fixed training/evaluation and primary reduction; reuse existing primitives. |
| `scripts/run_dish_own_command_mean_b07.py` | One seeded runner, fixed caps, existing timing/error/partial-output pattern and readable summary. |
| `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_training_engine.py` | The shared mean law used by `_policy_log_prob`, physical-role selection where needed, and `run_full_4096_dry_update`'s replay/repeated motion term. |
| `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_recurrent_trainer.py` | `BatchedRecurrentPolicy` construction/`step_rows`, `NativePersistentTrainingFlow` construction and post-update policy reconstruction carry the selected mode/raw input. |
| `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_training.py` | `PersistentTrainer` construction/`run_update` forwards the same mode into the real update engine. |
| `experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/study.py` | Only needed argument propagation/reuse seams for B07 in `configuration`/`prepare_shared`/`run_arm`; preserve existing DIRECT and LR defaults. No B04/B05 result or algorithm revision. |
| `tests/experiments/candidates/degraded_incumbent_shadow_handover/own_command_mean_b07/test_own_command_mean.py` | The one focused changed-behavior and primary-output module described in §4. |
| `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_OWN_COMMAND_MEAN_B07_CM_RECORD_20260908.md` | Delivered diff, focused evidence and check charge, independent review outcome, remaining issue/next route. |

Read-only implementation inputs, not owned native edits:

- `forecast_package_b02/study.py:12–19,35–44,48–88,106–160`: accepted A03 host imports,
  progress/measurement, `terminal_facts` and `evaluate_episode(..., record_first_transfer=True)`.
- `control_low_lr_b04/study.py:36–85,89–209`: master/coordinates/resets, LR payload and
  readback, common initializer, real flow/update16 evaluation. The unchanged `prepare_shared`
  currently evaluates **four DIRECT initial rows**, not a common reference for both modes.
- `r06/production_recurrent_trainer.py:287–374,387–413,467–542`: live raw input,
  old likelihood, fragments and mode propagation through updates. Here `r06/` abbreviates
  `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/`.
- `r06/production_training_engine.py:345–383,428–459,496–643` and
  `r06/production_training.py:62–93`: physical-copy selection, Gaussian/Bernoulli density,
  real replay/update and persistent caller. No full 1024-update path is selected.
- `first_trigger_source_scout_b01/native_a03.py` and
  `r06/native/rbhr_r06_production_backend.cpp:261–264,304–317,433–497,731–746`:
  unchanged host/actor/projection/application/reward/private-label semantics. P53 intake
  §2 supplies the implementation-relevant source map; the historical citation tree is unnecessary.

The non-r06 study and native_a03 paths above are under
`experiments/candidates/degraded_incumbent_shadow_handover/`. Existing shared sources
remain in place. CM is not alone in the repository: preserve other edits and serialize
overlapping edits/checks/commits in this same checkout; do not create another authoring branch.

## 3. Required behavior and preserved semantics

The frozen definitions are card §§2–4; do not ask CM to choose new scientific semantics.
The necessary code change is an explicit DIRECT/OWN mean mode with DIRECT as the existing
default, carried through collection, persistent updates, policy reconstruction and initial/
final evaluation. Both retain native/training arm **STRUCTURED** and LR3e-5. Mode is an
ordinary study argument/field, not a new native arm, RNG namespace, model parameter or
checkpoint-version system. Record the mode actually used, rather than only its desired label.

Implement one coherent mean calculation for the specified own raw input. At all live and
replay consumers preserve physical vehicle0 x,y then vehicle1 x,y and the card's owner/copy
table. Live raw actor is shape `[width,4,54]`; replay raw actor and owner follow recorded
fragment dimensions. Do not substitute normalized observations or current simulator state.
Preserve old behavior likelihood and raw Gaussian density; the engine's repeated motion
term uses the same mean, with gradient through motion/tanh. Keep log_std clamp, Bernoulli
law/masks, entropy, labels/losses, optimizer, Welford and recurrent/promotion semantics.
Changing only evaluator output or only generated actions fails this deliverable.

Reuse the common initializer and accepted LR/reset/training/evaluation primitives. B07
needs two real LOW_LR flows after one common initialization and **eight initial rows across
the two parameterizations**, followed by each arm's four update16 rows. If reusing B04's
four initial DIRECT rows, count them as DIRECT's own initial rows and do not repeat them.
OWN requires its separate four with the same initial weights/count0 Welford. DIRECT initial
episode time belongs to DIRECT, even if an existing helper currently calls it "shared".
Use B04's existing update16 checkpoint access; retain r06's 1024-update constants and
sole-checkpoint contracts, which this B07 path does not invoke.
Do not invoke B04/B05/B06 as additional studies, reuse their checkpoints/resets, or perform
any extra native/learner smoke to qualify B07.

The runner interface for the later single paired invocation is:

```text
python scripts/run_dish_own_command_mean_b07.py --seed 127 --output <run-root> --launch-sha <accepted-sha> --prior-shared-seconds <actual-required-check-charge>
```

The runner fixes the two arm modes and card caps (1800s/arm, 3600s/pair). The prior shared
charge is already spent necessary checking, not extra allowance; add it once to actual
in-run shared work and split total shared S/2. Execute the fixed arm list in order DIRECT
then OWN; order is operational, not selection. Each arm's full cost includes its initial
and final evaluation. Keep final reduction/publication inside the same pair/arm charges.
No generic queue, resume or retry logic follows. The future named launch supplies fresh
same-node admission and existing detached supervision outside this runner.

`summary.json` must expose the numbers the card reads: object/seed/actual master/mean mode,
launch SHA and node/device/dtypes; four retained resets; separate arm configuration,
actual update/transition/optimizer and existing learning summaries; all 16 labeled
`arm × initial/final × condition` episode rows; four final differences, both initial/final
means, Delta_mean, D_OWN and D_DIRECT; native companions in card §4; complete charged
shared/arm/pair wall and peak RSS if available. Model reconstructions are not extra learners.
Report missing H or optional resources honestly, with the existing bound/label.

A full paired primary requires the two actual completed learners and complete fixed final
rows. Missing initial rows limit the initial-relative/full-card claims and must remain
explicit; do not fabricate them or suppress independently trustworthy final observations.
Preserve partial output and actual failure/counts. An output marked complete must contain
the card's whole 16-row deliverable; missing optional resource telemetry alone does not
make the native service result invalid. Native terminal rows are complete under the
fixed-horizon zero-remainder convention.

## 4. Original acceptance and focused checks

Accept implementation by the actual changed paths, synthetic outputs and existing
independent review, under card §§2–6 and evidence-spec §§4,5.2,11.4,11.8.6–11.8.7.
The one new focused module covers these direct dependencies, with small inputs and no
scientific initializer/native episode/training invocation:

1. Owner0/1 select the card's physical copies for live and replay ranks. Use distinct
   nonzero own accelerations, zero acceleration, and a few nonrenewal/reset/role-change
   inputs. OWN follows the exact formula, DIRECT follows its unchanged formula, and zero
   own input makes their means agree. Raw versus normalized inputs are distinguishable.
2. For identical synthetic state/parameters/raw action, generation's mean, online behavior
   density, replay density and the engine's repeated motion term agree. Include nonrenewal
   and preserved Bernoulli/mask behavior. A small tensor/model gradient check reaches motion
   parameters; do not detach the complete mean or add a projection/squash-density correction.
3. Mode reaches initial/final policy, both real-flow constructors, PersistentTrainer, the
   update engine and reconstructed policy after update. Check the actual master family is
   passed to initialization/train reset/semantic streams/evaluation reset; use intercepted
   consumers for this engineering check, not a new scientific seed or real learner run.
   DIRECT default callers retain their old behavior. No full synthetic 4096-update run is
   needed solely to test argument propagation; normal method seams may be intercepted.
4. A few artificial complete/incomplete result rows verify four-condition final reduction,
   separate own initial references, D_OWN/D_DIRECT, ±24/open-band and own-initial-loss
   predicates. Verify adverse rows remain, native terminal remainder is zero, first transfer
   is the native post-step tick/null, and training/evaluation counts stay separate. The
   subjective native-tradeoff decision stays with DM, not a new automated polarity gate.
5. Exercise `summary.json` publication/readback using those synthetic rows, including an
   incomplete path, and shared versus per-arm cost allocation with checks counted once.
   Fake clocks/tiny inputs suffice; no timing/cost experiment, native replay or new fixture
   platform is required. Use FP32-appropriate action/probability tolerances and explain
   them; no cross-platform or full-trajectory bit equality is requested.

Original focused acceptance command, from the checkout with its configured interpreter:

```text
python -m pytest -q -p no:cacheprovider --basetemp temp/directions/degraded_incumbent_shadow_handover/test/b07-own-command-<run-tag> tests/experiments/candidates/degraded_incumbent_shadow_handover/own_command_mean_b07/test_own_command_mean.py
```

Use one invocation-owned run tag; retain the needed log/result then clean only that
resolved scratch directory under this checkout's `temp/`, on success or failure, as
current `tests/AGENTS.md` requires. One final whitespace/changed-source inspection is
sufficient. Existing B06 CM record's focused accepted checks cover unchanged master seams,
renewal, modal behavior, checkpoint/state ownership, native promotion, first transfer/null
and terminal publication. Reuse them where unchanged; do not rerun the historical suite
merely because this card is new. A concrete failure or newly affected boundary warrants
the focused correction, whose time is still charged.

The changed action-distribution and learning semantics require the existing independent
CM review. Reviewer inspects the final affected boundary and this acceptance evidence;
test exit or certificate production alone does not establish scientific value. No new
critic round, approval layer, performance-sign check or Pro launch condition is added.

## 5. Budget, stop and exact CM return

Engineering scope §4: **none newly needed**. Retain <=2000 new non-test lines, <=600 runner
lines and <=5min total focused research-directory test wall; 30% orchestration is only a
review signal. No arbitrary new engineering time allowance is drawn from prior objects.
Required computational checks/builds are charged once to shared S under card §6, including
failed relevant checks; report their actual time and remaining per-arm/pair allowance.
Ordinary editing, source reads and this documentation preparation are not training exposure.

Short synthetic checks may stay local. Long portable checks follow the configured remote
route once source is committed/pushed. Actual scientific execution remains remote_first
`wsl_4070` CPU, native float64/policy FP32, one Torch/BLAS thread, exact committed bytes,
detached `agent-task` supervision and fresh same-node physical/effective memory >=4GiB.
No implementation check is permission for a result-bearing run. Do not construct a model,
native state or experimental master during the current DM authoring task.

Stop engineering at implementation plus focused acceptance/independent review, or return
a concrete unresolved correctness/scope/budget conflict with the delivered portion. Do not
weaken the card or add machinery to force completion. For a later result-bearing invocation,
the card's complete cap/nonfinite/measurement stop applies; no retry or extra seed follows.

CM returns the exact changed paths/commit and push, original focused command/result and
wall charge (including failures), independent review outcome, actual source-budget facts,
the runnable argv above and any remaining gap. It retains technical acceptance; DM checks
scientific conformance and Root integrates the named accepted commit in the existing route.
If later launched, CM collects the real pair and hands the accepted handle to Root under
`docs/project/EXPERIMENT_MONITOR.md`; no handle exists in this implementation return.

Root has the complete identical source/task/spec/acceptance before any coding dispatch.
The current main comparison record at `27c0a4ed3efe4f4a3118af922d2260b07273ab0f` shows
all three prospective CM comparison batches completed; this preparation enrolls none and
does not restart that test. Preserve the original full handoff if Root must reconcile
dispatch facts. This is a real next B07 deliverable, not historical or duplicate scientific work.
