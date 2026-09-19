# FOLR research notebook

Direction: `vap_folr_core`. Current index: [RESEARCH.md](../../RESEARCH.md).
This notebook starts with the current work; historical evidence stays at its original paths.
Pro conversation: none selected for this study.

## 2026-09-19 — direct DM resumption and explanation update

Owner instruction in the current Codex session: continue this direction with the session
acting directly as DM and using bounded subagents, without a Root dispatch layer. FSD is
exclusively Claude Code's direction. This is the current session assignment, not a change to
other directions or a new standing role. The DM has read the PR26 methods at main
`fb3d225fb77e39301340e3ba9763c32470a1805b` and accepts their application to new work.
Authoring is isolated on `codex/folr-predictive-aux-a01`; the DM owns this notebook and index.
Leaves return facts and do not write the notebook. Historical completed operations remain
completed; this resumption neither retries nor reinterprets their frozen contracts.

### Evidence inherited and current judgment

- [Augmentation discovery](FOLR_ENTITY_HISTORY_AUGMENTATION_B01_RESULT_EVIDENCE_20260914.md):
  persistent A minus Generic G was +5.29640625 in one fresh comparison.
- [Persistence contrast](FOLR_ENTITY_PERSISTENCE_B01_RESULT_EVIDENCE_20260914.md):
  A minus current-only augmentation Z was -3.069453125; Z still retained Generic recurrence.
- [Current augmentation contrast](FOLR_ENTITY_CURRENT_INCREMENT_B01_RESULT_EVIDENCE_20260914.md):
  Z minus G was -4.44375 in a separate comparison.
- [Prospective repetition](FOLR_ENTITY_AUGMENTATION_REPEAT_B01_RESULT_EVIDENCE_20260915.md):
  A minus G was -5.830625 and -0.109921875; retain the original MIXED_BLOCK_PATTERN reading.

These observations weaken preference for the old augmented package. They do not establish
history redundancy, a stable Generic ranking, or which representation/optimization link failed.
The contrasts cannot be combined into an A/Z/G causal ranking across different fitted policies.
Generic already has local recurrence and truthful lifecycle cues; useful-history necessity is
not an established premise. The old package adds parameters, fusion and training burden.

Read-only artifact inspection of the latest repetition finds per-episode train/evaluation
returns and final checkpoints, not a retained independent per-transition event trajectory.
Its collection code computes lifecycle fields/counts that the runner discards. Therefore a
claim that the observed losses concentrate just after membership changes is currently unsupported.
Fresh event measurements must be prospectively declared, not manufactured from summary scores.

### Candidate question under design

Can observed short-window outcome supervision improve finite learning of the existing Generic
representation without adding an execution-time memory bank or input? This is the H-aux
question in the [PR26 proposal](../../designs/PREDICTIVE_INTERACTION_AUGMENTATION_PROPOSAL_20260919.md),
not a test of pretraining or proof that history is necessary.

The candidate uses factual mean native reward over three transitions, aligned with h_t before
action t; the existing TD objective instead bootstraps at t+1. Both arms train the same
separate predictor. The proposed intervention is whether its error updates the actor backbone;
an untrained predictor in the control would make prediction improvement uninformative.
Predictor gradients must not change native clipping or optimizer state in the detached control.
Future reward is a training label, never an actor input; incomplete windows are not zero-padded.

Two bounded Scouts have mapped prior evidence and interfaces. A focused ResearchCritic is
checking whether the proposed prediction diagnostic and comparison distinguish this question.
The DM will accept or modify the design and append its prospective executable scope before
implementation. No scientific fit or result evaluation has started in this resumption.

## 2026-09-19 — predictive auxiliary A01: selected exploratory comparison and L0

### Question, intervention and predictions

Select one new hypothesis: short-window factual-reward gradients into Generic recurrence may
improve finite-budget team control. This is a new auxiliary-gradient package screen, not a
diagnosed repair of the old entity-memory package and not a history-necessity claim.

Both arms use the unchanged GENERIC_RETAIN actor, FlexQMixer and complete-episode double-Q
learner: gamma .99, native RMSprop lr .0005/alpha .99/eps .00001, native gradient norm bound
10, original target update schedule, epsilon law and full-episode replay sampling. A separate
linear 64-to-1 predictor is initialized identically with an isolated constructor RNG stream
and trained in BOTH arms with its own RMSprop at those settings and separate norm bound 10.
It reads each active agent's h_t. Its label is (r_t+r_(t+1)+r_(t+2))/3 in native reward units.
Use t=0..17 in the fixed H20 host, active-at-t masks, and mean squared error averaged over
eligible agent-time entries. Retain windows containing later departures/replacements; no
future-survival mask. Incomplete windows and inactive-at-t agents provide no predictor label.
Native TD still uses all 20 transitions. All actor execution inputs and recurrent resets stay
unchanged, and the predictor never selects an action or supplies an actor input.

- DETACHED: train the predictor on h.detach(); native learner sees TD only.
- COUPLED: also send .1 times the prediction MSE gradient into the actor backbone, treating
  predictor weights as constants on this extra gradient path. Predictor parameter gradients
  and optimizer exposure remain the same rule as DETACHED. Clip actor/mixer gradients separately
  from predictor gradients so DETACHED is numerically the original native learner on a fixed batch.

The expected native direction is COUPLED minus DETACHED > 0, low confidence; an adverse result
is credible because rewards are already part of TD and added supervision can interfere with
control. Both predictors should acquire nonzero parameter updates; prediction/target moments,
errors and counts are descriptive diagnostics, not proof of a missing information mechanism.
The learning objective differs from TD by using two further observed rewards without a learned
bootstrap; this is a plausible finite-learning intervention, not an established cause of prior loss.

### Accepted focused criticism and reading

ResearchCritic returned MATERIAL_DISSENT=yes about using a common uniform-policy probe as a
decisive representation diagnostic. Accepted: factual future-reward labels depend on joint
behavior policy. A byte-identical uniform panel tests fixed-policy transfer error, not the
same conditional law as either arm's learned behavior. Its failure does not falsify H-aux,
and its improvement without native gain is predictive transfer only. Own-policy prediction
errors also remain conditional descriptions; neither error comparison identifies representation
quality independent of policy/head co-adaptation.

The primary is signed difference of mean native returns from the two sole-final greedy panels.
Report each complete panel, per-episode outcomes and actual fit counts. There is one training
instance per arm: no population claim, significance/equivalence verdict, MEI classification,
episode-based pseudo-replication or causal history attribution. Native gain with unchanged or
worse probe error remains a package observation. Native harm/non-improvement constrains this
target/coefficient/horizon realization, not history generally. Missing/nonfinite output is
technical incompleteness, not negative evidence. Retain all outcomes. No score-based continuation
or automatic larger-model follow-up is selected.

### Prospective exposure and resource scope

Exactly TWO fresh fits, DETACHED and COUPLED, each training seed 783101 (unscreened labels,
aligned initialization; no claim of episode pairing), 5000 H20 training episodes, 100000 native
training transitions and 4969 native/predictor optimizer steps. No tuning or auxiliary prefit.
One final checkpoint per arm, then 128 greedy episodes with evaluation seed 1783101 and zero
updates. After that, 128 fixed uniform-policy diagnostic episodes at probe seed 2783101, zero
updates, epsilon=1 using the existing selector and fixed-width terminal draws. Verify identical
probe observation/action/reward bytes before any cross-arm probe comparison; otherwise withhold
that comparison and report the mismatch. No extra seeds, interim native evaluation or selected
checkpoint. Two-arm totals: 10000 training episodes, 512 evaluation/diagnostic episodes,
210240 native transitions and 9938 native optimizer steps plus 9938 predictor steps.

Execution: configured local_linux CPU FP32, Torch threads/inter-op 1/1 per process, independent
per-arm environment, RNG, replay, optimizer and outputs. Separate from FSD's remote execution.
Up to two original arms may overlap if actual-node admission permits; no shared mutable state.
Historical Generic arms took roughly 35–38 minutes on a different CPU; local time remains
unmeasured. Initial planning estimate is 60 minutes per arm, not a scientific endpoint or kill
line. Observe progress and resource health; record actual runner wall, CPU and peak RSS including
preparation scope. Fresh launch admission, publication and handle reconciliation still apply.
This fixed two-fit screen consumes two of the default maximum six fits for an idea; unused
allowance is not an automatic extension or follow-up. Any new comparison needs its own declared
scientific purpose and includes this selection exposure.

### L0 implementation and ownership

Deliver one verifiable behavior: the selected separate-head auxiliary-gradient comparison with
the original native learner preserved in DETACHED and complete final/probe measurements.
Owned edit paths for Implementer: `experiments/candidates/vap_folr_core/predictive_aux_a01/`,
`scripts/run_folr_predictive_aux_a01.py`, and mirrored tests under
`tests/experiments/candidates/vap_folr_core/predictive_aux_a01/` only. Reuse existing actor,
environment, mixer and collection by import; do not modify historical experiment code or shared
launch/admission utilities. Read nearest AGENTS. DM owns NOTES and Git index/commits; Implementer
returns an unstaged diff and checks, does not launch scientific work, send Pro or spawn children.

Runner: admission before model/environment/output scientific effects; fixed arm/count/seed
bindings and launch SHA check. Publish config, incremental training progress, incomplete/error
status on exception, all train/final returns, final checkpoint including predictor optimizer,
parameter movement and real counts. Retain final and probe episode arrays including lifecycle,
rewards, inputs and predictions under `runs/vap_folr_core/<tag>/`; record source and panel hashes.
Preserve lifecycle counts; report whole-return and descriptive post-event reward windows (each
primitive tick counted once in the union of the first 3 action times after a noninitial event).
Those event strata differ by learned policy and are not a causal cross-arm recovery estimand.

Focused checks: exact detached native-update/optimizer/RNG parity on synthetic batches including
target synchronization; predictor learning in both arms; extra actor gradient only in COUPLED;
full-window alignment, active/inactive masking and future departure inclusion; separate gradient
clipping and checkpoint ownership; deterministic identical uniform probes; terminal and no-update
evaluation boundaries; runner refuses without admission. Synthetic tests use managed scratch,
no undeclared training/evaluation exposure. Independent Reviewer checks the executable change
before the DM accepts and publishes exact inputs. This note selects the study, not unreviewed code.

## 2026-09-19 — A01 implementation accepted before execution

The DM read and accepts the Implementer diff for the selected L0. The Generic actor is the
history-aware `entity_history_b01.model.Actor` constructed through
`entity_history_augmentation_b01.learner.Learner`, not the older simplified public-lifecycle
actor. Synthetic DETACHED parity covers exact actor/mixer/target parameters, native optimizer,
constructor/update RNG and target synchronization. Both heads learn through their own optimizer;
COUPLED alone adds the prescribed actor-backbone gradient. Full-window/activity masking,
future departure inclusion, post-event union, panel hashes, final-only counts, zero evaluation
updates and admission-before-effects have focused checks.

Independent Reviewer traced the collector through publication. Two failure-accounting findings
were repaired: completed optimizer counts are captured before diagnostic serialization, and
nonfinite diagnostics retain an incomplete/error summary with null values and explicit invalid
paths. The repaired runner has synthetic regressions for both failures. Reviewer concludes no
material finding remains; the DM accepts. Implementer reports 13 focused/admission tests passed;
Reviewer independently ran the original 9 candidate checks and the repaired 5 runner checks.
No native fit or result-bearing smoke was used as a test. Runtime resource use and identical
cross-arm probe inputs remain observations to verify from the selected runs.

Publish these exact accepted inputs, then admit the two original arms through the configured
local_linux kernel with source snapshots. No change to the scientific scope or two-fit exposure.
FSD's new main notebook commit `ff0725db5` acknowledges the shared host and separate direction
writers; its work stays with Claude. Run identities will be linked here from native manifests.

## 2026-09-19 — A01 two original arms admitted

Both selected original invocations were accepted by the configured actual-node kernel after
fresh publication/policy/memory checks. Native manifests preserve operation refs, source
snapshots, command identities and process witnesses:

- [DETACHED launch](../../../../runs/vap_folr_core/predictive_aux_a01_detached_783101/launch-manifest.json)
- [COUPLED launch](../../../../runs/vap_folr_core/predictive_aux_a01_coupled_783101/launch-manifest.json)

The published accepted implementation is `356bb3cc53479946bc031a24ada1ea979769fddf`.
Both runners entered training: two fits started of the two selected; no repeat or additional
fit is selected. A bounded Monitor is assigned these exact operations; the DM retains acceptance
and collection/read responsibility. These retained snapshots remain immutable while notebook
work continues. Final scientific reading awaits complete outputs and cross-arm probe identity.

## 2026-09-19 — A01 complete: adverse native observation, slightly better predictive transfer

Both original accepted operations have matching terminal witnesses, exit zero and complete
runner summaries. Monitor returned an empty active set; its terminal notice also used the
owner-authorized relay task. The DM reconciled the same handles, with no retry or new fit.

| Reading | DETACHED | COUPLED |
| --- | ---: | ---: |
| Sole-final native mean, 128 greedy episodes | 2.69046875 | -3.8690625000000014 |
| Negative-return final episodes (descriptive) | 51 / 128 | 95 / 128 |
| Own-policy prediction MSE (different induced data/laws) | 1.2180755787628395 | 1.2475613021859853 |
| Common uniform-policy transfer MSE | 1.91582951272241 | 1.803888307163275 |
| Eligible common-probe agent-time entries | 6173 | 6173 |
| Runner wall seconds, single process including imports/preparation | 1785.3945803509996 | 1844.1139315610053 |
| Single-process CPU seconds | 1785.940704938 | 1844.257223117 |
| Single-process peak RSS, KiB | 671212 | 681528 |

Primary signed observation COUPLED minus DETACHED = **-6.559531250000001**.
Both have 5000 training episodes, 100000 training transitions, 4969 native and 4969 predictor
optimizer steps, one final checkpoint, 128 final plus 128 probe episodes, zero evaluation
updates. Total consumed is exactly the two selected fits; no failed or hidden training attempt.
Both actors and predictors moved from initialization. The first/last 200 update-row mean
prediction MSE changed from 2.4397651 to 1.4403850 in DETACHED and 2.0597891 to 1.2190964 in
COUPLED. These are changing replay distributions, not held-out learning curves or evidence
that prediction progress caused the native difference.

### Verification and retained evidence

- [DETACHED summary](../../../../runs/vap_folr_core/predictive_aux_a01_detached_783101/summary.json)
- [COUPLED summary](../../../../runs/vap_folr_core/predictive_aux_a01_coupled_783101/summary.json)

The DM independently reconstructed complete counts, label alignment/activity masks and panel
MSE from retained arrays, checked finite checkpoint tensors, checkpoint/update/panel SHA256s,
and the recorded source hashes against each immutable launch snapshot. Recomputed sums of
FP32 reward storage differ from native accumulated returns by at most 0.000001038; the primary
uses original native returns. Common-probe semantic input digest is identical in both arms:
`f34109d178270b3c4ae4b123e8c8910cba8850fe87567d1329b2d0f55fd57435`.
Thus the reported transfer-error contrast has the required common-input support. No additional
policy evaluation or training was run for verification.

Text summaries, full per-update JSONL, admission/preflight and terminal manifests are published
with this entry. Binary checkpoints/panels and stdout/stderr remain at their original durable
local output paths under
`/home/fires/.codex/worktrees/folr-predictive-aux/hmasd-wsl/runs/vap_folr_core/`, in the two linked
tag directories; their exact names and SHA256s are in the summaries. They are not in Git and
must be preserved before any worktree cleanup. Source and native operation claims/snapshots
also remain in place; there is no cleanup in this task.

### Explanation update and next choice

The expected positive native sign failed in this single fitted comparison. This weakens the
case for using the exact short-window/.1 coupled auxiliary package and provides no reason to
advance it to confirmation or pretraining. A modest reduction of common-policy prediction
error coexists with worse native return, reinforcing the distinction between predictive
transfer and usefulness for control. It does not establish a stable adverse effect across
training instances, a causal representation defect, or a general failure of auxiliary learning.
The two policies induce different data, targets and optimization trajectories; optimization
interference, policy/head co-adaptation and training-instance variation remain undistinguished.
History necessity (H-need), pretraining increment (H-pre), and UAV deployment value are untouched.

End this exact two-fit batch without seed extension or coefficient/horizon search. Keep the
broader auxiliary idea unresolved, and deprioritize this implementation given its adverse
native observation. The next useful work is reasoning-only: specify a small membership-change
prototype with a controllable difference between current cues and legitimate history, so an
opportunity claim can be separated from finite-learning failure before another architecture is
chosen. Such a prototype must state the MARL coupling it omits and cannot establish a native
Traffic-Junction/UAV effect. No new prototype implementation or fit is selected by this entry.

## 2026-09-19 — continued: analytic history opportunity and retained-panel inspection scope

Owner approved continuation after A01 closeout. Keep its two-fit result and fixed batch ended.
The next work is a source-derived finite conditional counterexample, not an implemented toy or
new fit. Scout maps actual host information/dynamics; ResearchCritic independently checks the
analytic construction. No additional role or Root layer is introduced.

Before reading new descriptive counts, select one fixed post-hoc inspection of the already
retained A01 panels: DETACHED final, COUPLED final, and the shared uniform probe (once, since
its input digest matches). Across all 128 episodes and action times 0..19, count active observer
ticks and the subset having at least one active, previously seen, currently hidden subject in
the same row/column exactly two cells away (Manhattan distance 2, Chebyshev distance 2).
Use integer positions recovered from the stored native coordinates times dimension 7; verify
rounding error. This geometric condition permits a shared reachable next cell on the native
cross road. Count each observer tick once, not once per hidden subject. Also report how many
such ticks overlap the already declared union of first three action times following noninitial
public lifecycle events, plus episode counts. No favorable subset/lag search is selected.

Hidden current positions are privileged only for this retrospective geometric description,
never an actor input. Presence of this condition does not establish that lawful history locates
the hidden subject, that a collision was avoidable, that action ranking changed, or that the
conditional counterexample's teammate law occurs. This is direct reading of existing artifacts:
zero new transitions, fits, optimizer steps, model inference or counterfactual environment calls.
The purpose is to distinguish a potentially relevant geometric stratum from a source-only
existence argument; it cannot estimate a memory effect or new-policy performance.
