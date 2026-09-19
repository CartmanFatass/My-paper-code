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
