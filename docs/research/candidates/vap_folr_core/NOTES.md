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

## 2026-09-19 — native analytic counterexample and completed artifact reading

### Accepted reasoning and rejected shortcuts

The abstract binary-choice model clarifies the disputed link without a simulation. Let
b=P(Z=1|I), reward R=1{a=Z}, and let a fixed behavior choose a=1 with probability u,
independently of Z conditional on predictor information I. Then
E[R|I]=(1-u)+(2u-1)b, while Q(1|I)-Q(0|I)=2b-1. At u=1/2 the reward mean is constant even
when extra lawful history changes the optimal action. This is a counterexample to treating
factual-reward mean prediction as a universally informative control target, not an A01 diagnosis.
A binary-cue prototype also shows that lower posterior squared error need not change the
optimal action when a more reliable current cue already determines its sign. No toy training
is needed to establish these conditional identities.

Scout's first source map required correction, accepted before using it: masking a currently
hidden subject does NOT stop the Generic GRU from retaining earlier visible observations.
Also native `wait` increments for all slots on every tick, resets on removal but not movement
or birth, and includes inactive elapsed time. It is not a blocked-step counter. At a fixed
state the immediate time penalty is computed before arrival/collision removal and is common
to the alternative actions. Predicting it better need not improve one-step action choice;
longer-term duration effects would require their own argument. No frozen environment is changed.

### A conditional case in the actual native host

Use easy mode's 7x7 cross road, vision 1, two active cars A and B, and no unrelated births.
Targets are A=(3,6), B=(0,3); these are legitimate visible entity fields, not hidden types.
Construct the following positive-support prefix from a legal reset/birth. Time labels below
are transition indices, so the state after transition 6 is observation boundary 7.

| Boundary/action | A position after action | B position after action, left / right branch |
| --- | --- | --- |
| reset | (3,0) | absent |
| transition 0 | (3,1) | birth at (6,3) |
| transition 1 | (3,1) | (5,3) |
| transition 2 | (3,1) | (4,3) |
| transition 3 | (3,2) | (3,3) |
| transition 4 | (3,3) | (3,2) / (3,4) |
| transition 5 | (3,3) | (3,1) / (3,5) |
| transition 6 | (3,3) | (3,1) / (3,5) |

The transition-4 swap in the left branch is legal under this native implementation: collision
checks compare final positions, not edge crossings. Neither target has been reached.
At boundary 7 both branches have the same CURRENT permitted inputs for A: its target/position,
previous stay action, public active/birth/departure/continuation/event table, and local seen/age.
B is hidden with seen=true and age=2 in both. Global raw entity rows differ; they are masked
before actor learned processing. Earlier lawful visible histories differ in B's branch.

The conditional two-case population gives the branches equal prior weight and specifies a
known B phase law: outward at transition 5, stay at 6, then move one horizontal cell toward
column 3 at the candidate transition 7. History observes the branch; the known law supplies
the intervening hidden moves. Those hidden actions are NOT claimed observable to A. This
specified support/law is essential, and is not asserted to describe the learned teammates.
A current-only oracle knows the same law and prior but lacks the earlier branch observation.

Native immediate TEAM rewards, before the common time penalty, are:

| B case / A action | stay | right | left | up | down |
| --- | ---: | ---: | ---: | ---: | ---: |
| B left: (3,1) -> (3,2) | 1 | 2 | -10 | 0 | 0 |
| B right: (3,5) -> (3,4) | 1 | -8 | 0 | 0 | 0 |

B contributes +1 progress in each case; A contributes 0,+1,-1,-1,-1. A collision subtracts
10 once from total reward. Both native wait counters are 7 before the candidate step and
become 8, so subtract .16 from every displayed entry. Consequences:

- Uniform focal-A action averaging yields **-1.56 in both cases**.
- Under the equal-case prior, the best current-only action is stay, expected reward **.84**.
- History identifies the case and chooses right in the left branch, stay in the right branch:
  expected reward **1.34**, a conditional one-step value difference **+.5**.

Thus lawful history can change native action preference while the squared-error-optimal
behavior-averaged reward mean hides that distinction. The full reward distributions do differ.
Uniform focal A with this structured B law is NOT A01's fully uniform team probe, and the
one-step calculation is NOT its three-step target or H20 endpoint. This establishes conditional
opportunity only: no prevalence, trained-Generic shortfall, learned-policy improvement or UAV
claim. Generic has legitimate access to the distinguishing history and could represent it.
Birth/lifecycle validity is preserved, but no incremental benefit specific to N-change is proved.

Source anchors: [movement/reward/removal](../../../../experiments/candidates/vap_folr_core/public_lifecycle_b01/native_env.py),
[public lifecycle](../../../../experiments/candidates/vap_folr_core/public_lifecycle_b01/environment.py),
[local seen/age](../../../../experiments/candidates/vap_folr_core/entity_history_b01/environment.py),
[actor masking and recurrence](../../../../experiments/candidates/vap_folr_core/entity_history_b01/model.py).
Scout and ResearchCritic independently checked the actual source and arithmetic. Critic's
material qualifications (known hidden-motion law, reward mean versus distribution, structured
B versus fully random team) are accepted above; final MATERIAL_DISSENT=no. No simulator or
model was instantiated, and no learned or empirical result is claimed for this construction.

### Selected retained-panel counts

Artifact SHA256s were checked against the existing summaries. Multiplying stored positions by
7 reconstructed integer coordinates with zero observed rounding error. The fixed geometric
predicate from the preceding scope entry gives:

| Existing panel | Qualifying / active observer ticks | Fraction | Episodes containing at least one / 128 | Qualifying ticks in post-event window / all active observer ticks in that window |
| --- | ---: | ---: | ---: | ---: |
| DETACHED final | 718 / 7281 | 9.8613% | 88 / 128 | 363 / 4264 |
| COUPLED final | 180 / 7591 | 2.3712% | 44 / 128 | 102 / 4049 |
| Common uniform probe | 297 / 7072 | 4.1997% | 54 / 128 | 134 / 3944 |

The calculation is reproducible directly from each retained `*-panel.npz`: restrict time to
0..19, recover positions with round(7*entities[...,2:4]), form observer-subject absolute position
differences, select Manhattan==2 AND Chebyshev==2 AND both active AND seen AND NOT visible,
then reduce `any` over subjects. Divide by all active observer ticks. Public event windows are
the union [t,t+3) clipped to 20 for events at t>0, counted once per primitive time. No subject,
episode, action or lag was selected by reward; full panels are retained unchanged.

These are descriptive counts on existing policy-induced data, not independent training units.
The geometric stratum occurs in all three panels, including around lifecycle events; this
makes it more concrete than a source-only possible configuration. It remains an upper-scope
candidate stratum, not a count of identifiable or avoidable collisions. COUPLED's smaller
fraction does not explain its lower score or show better avoidance: policy-induced survival,
positions, visibility and histories differ. The records do not supply conditional counterfactual
action rankings or prove that old observations predict the currently hidden positions.

### Judgment and next scientific choice

H-need is now supported as a conditional possibility inside the existing native dynamics;
its materiality under learned teams remains unresolved. The old conjecture that history might
help because of persistent hidden velocity/type is not used. Scalar factual-reward prediction
is a weaker proxy for useful information than an action contrast in this example. This does
not attribute A01's loss to that limitation, and no auxiliary coefficient/seed rescue is selected.

Next discriminating question: under a specified actual frozen teammate continuation, does a
lawful history feature predict collision-relevant action differences beyond current cues, and
does Generic already preserve that feature? A bounded action-contrast or hidden-state forecast
measurement could answer parts of this question, but needs its own declared information rights,
policy/target law and compute scope before implementation. A target based on privileged state
must remain a training/diagnostic label, never silently enter actor inputs. Do not start another
reward-head fit merely because this counterexample exists. This continuation used zero new
fits, optimizer steps, model calls or environment transitions; A01 remains 2/2 fits completed.

## 2026-09-19 — continuous DM work: selected frozen-action diagnostic A01 and L0

Owner requests a continuous research loop, not a permission stop at each routine step. Within
this direction the DM proceeds through design, checks, execution and reading at scientific
boundaries. This does not change fit allowances or FSD ownership. The completed predictive
auxiliary A01 stays ended; the following is a new zero-fit diagnostic of its frozen outputs.

Question: on the prespecified seen/hidden axis-distance-two stratum in each retained final
panel, does carrying the trained Generic recurrence change the selected action's immediate
team-reward consequence, conditional on the recorded teammates' greedy actions? The contrast
is full frozen recurrence versus setting the same actor's hidden state to zero at each
observation; all current legal inputs INCLUDING seen/age/public lifecycle metadata remain.
The latter is an out-of-distribution state-reset intervention, not a trained memoryless
baseline or a measure of what the representation could learn/linearly decode. Expect the
DETACHED actor's carried state to reduce conditional immediate regret, low confidence.
Intermediate prediction: reset changes some actions in the selected stratum. Read a null or
adverse contrast narrowly; neither proves history redundancy or a defect worth training away.

Inputs: the two A01 sole-final panels/checkpoints, fixed before this diagnostic:

| Input | SHA256 |
| --- | --- |
| DETACHED final.pt | 6c59f47535e6887c58c5bd4484044077e6acf1cde7b60181baf8334a136aed6e |
| DETACHED final-panel.npz | 6e140a6c23feb25481d3fb5705a26bed1acbbd5de85428408759b15f48cc7e7d |
| COUPLED final.pt | b8ccb717c22ce11254436d8873e26be25d14882b9a0f82c4179ab47dce28c7b0 |
| COUPLED final-panel.npz | 8a5f7b110fc027a86feef17810846d43d590909883be924ccc44d07556fd683f |

Their known tags are predictive_aux_a01_detached_783101 and
predictive_aux_a01_coupled_783101 under the durable author-checkout runs/vap_folr_core root.
Use native NumPy seed 1783101 at the start of EACH panel replay, then all 128 episode resets
and recorded joint actions in original order. Reconstruct each native observation, lifecycle,
reward and final boundary and check against stored arrays before reading the dependent result.
Native float64 replay returns are checked against summaries; FP32 reward casts against panels.

At each of the selected 718 DETACHED and 180 COUPLED observer ticks, hold every other slot's
recorded action fixed and evaluate each of the four non-factual focal actions through a deep
copy of the real native environment. Save/restore GLOBAL NumPy state around every branch;
branch births and removals never alter the factual continuation. Reuse the verified factual
reward for the fifth action. This is exactly 3592 counterfactual single steps plus 5120 factual
replay steps = 8712 native transition calls, not 5-to-the-number-of-agents joint search. Each
branch stops after one step; no new policy rollout or fitted model. No measured geometric row
is selected by its reward or by whether reset changes an action.

Replay the frozen actor serially at all 21 observation boundaries, as the original collector
did, with full hidden state and independently with zero incoming hidden state. Confirm full
active greedy actions equal stored actions before accepting a panel; do not switch to a batch
path whose numerical ties could change actions. This is 10752 actor calls across both panels,
no predictor/mixer forward needed, zero optimizer steps and zero parameter movement. CPU FP32,
Torch threads 1/1, configured local_linux. Initial wall estimate five minutes, adjustable for
engineering health but not a scientific stopping endpoint. No search, sweep or new fit.

Retain each selected row's episode/time/agent, five native reward values, full/reset actions,
full/reset conditional regret, action-change flag and public-event stratum. Summarize each
panel separately: counts, changed-action fraction, mean full/reset regret and signed
full-minus-reset immediate reward, and per-episode sums/counts. The oracle here has privileged
state and frozen other actions: its gap is not achievable actor headroom or H20 policy value.
Do not compare the two panels as a causal arm effect. One-step regret may disagree with good
long-horizon behavior; it is an operational local diagnostic of these actual frozen actions.
Invalid replay/action identity means technical incompleteness, never a negative scientific
finding. Preserve invalid counts/errors and all outcomes; no outcome-selected extension.

L0: Implementer owns only experiments/candidates/vap_folr_core/action_contrast_a01/,
scripts/run_folr_action_contrast_a01.py and mirrored tests. Reuse native env and Generic Actor
by import; no historical/core source edit. DM owns this notebook and index/Git. Entry requires
admission before loading scientific inputs, construction or output effects, with --launch-sha
matching admission and --input-root resolving the declared external files at their digests.
Output summary.json has complete/incomplete, input/source hashes, zero fits/updates and actual
forward/factual/counterfactual counts, runtime/RSS, rows and per-episode readings. Verify input
checkpoint hashes unchanged after execution. Use a runner-written JSONL for selected rows.
No generic evaluator framework. Check native branch isolation/global RNG, masks and selected
predicate, analytic two-case reward vectors, full serial action agreement, parameter immutability,
zero optimizer use, mismatch/error publication and admission refusal using managed pytest
scratch. Independent engineering Reviewer before DM acceptance/commit/push/admitted execution.

### A01 diagnostic scope clarification before implementation acceptance

Accept ResearchCritic's two material qualifications. Full carry outperforming zero carry does
not establish adequate memory capacity or informative history: a trained GRU can prefer its
usual operating state even when the carried content is uninformative. This diagnostic will
not infer a representation deficit or sufficiency from reset effects. Also multiple focal
deviations can concern the same collision and retain factual later states. Per-episode sums
are explicitly nonadditive overlapping local deviations, not a recoverable episode return.
Counterfactual reward/regret is evaluated only for the 898 selected observer ticks; other
active ticks receive no fabricated zero regret. Full-action identity checks still cover all
active ticks. Report per-row five-action reward range and aggregate nonflat-contrast count
(tolerance 1e-12), full/reset positive-regret counts and per-episode means/counts, derived from
the same selected rows with no extra native calls. These reveal whether the selected immediate
action contrast actually varies; they do not establish learnable history-specific headroom.
The DM will use the reading to decide the next question, with no automatic decoder fit,
second diagnostic, or extension. No additional empirical exposure is introduced by this note.

The DM accepts the Critic's final refinement before executable acceptance: selected actual
one-step action consequences/factual regret are PRIMARY; carry reset is secondary sensitivity.
For the same five branches also retain changes in native `collision_times` from the common
pre-state. The factual delta reuses the actual factual step. A row is collision-sensitive
when these five deltas differ; report its count and the same regret readings separately,
with null for an empty subset. This is a fixed descriptive partition of all selected rows,
not a reward-selected extension. Collision counts include the rest of the native team;
variation under focal action establishes that local intervention changes a collision outcome,
not that history could predict or prevent it. No new environment calls. Small collision-related
variation weakens this stratum as a target; little factual regret despite variation weakens
its immediate improvement rationale. Substantial regret leaves prediction, learnability and
H20 consequences unresolved. This smaller measurement does not claim to answer the stronger
question of history's incremental predictability, and is not a prerequisite for a learning test.

### Method choice after the owner's question about stepwise replay

The owner questioned whether this is a usual RL research choice. Distinguish experience replay
(training from stored samples; [DeepMind's DQN explanation](https://research.google/blog/from-pixels-to-actions-human-level-control-through-deep-reinforcement-learning/))
from this custom environment reconstruction/one-step branch diagnostic. A relevant conceptual
precedent is [COMA](https://arxiv.org/abs/1705.08926), whose centralized critic marginalizes one
agent's action while fixing others, efficiently in one forward pass. That is not a precedent
requiring real simulator branch replay, and this diagnostic is not COMA or an RL standard.
Primary passages were checked; their empirical results provide no evidence for this project.

DM judgment: the construction is proportionate only as this closed, small-host census, with
implementation already at its focused check boundary. It answers a limited local consequence
question, not learning efficacy. Finish this bounded reading, then choose a real learning
intervention or retire the subidea based on remaining scientific reason. No routine replay
stage, expandable forensic framework or additional diagnosis chain is adopted. A direct
learning comparison can be preferable even when the causal explanation is incomplete.

## 2026-09-19 — DM scope correction before any diagnostic launch

After the owner's questions about unusual scopes, the DM deselects the frozen-action diagnostic
from the current execution plan. Its implementation and independent engineering review found
no material defect, but that is not a scientific reason to run it: its possible readings do
not yet justify their cost relative to a direct learning comparison, and neither sign identifies
a history-representation deficit. No diagnostic operation, actual-checkpoint replay or new fit
was launched. Preserve the untracked implementation; do not delete or silently promote it.
The prior analytical example and A01's adverse result remain valid within their stated scope.
This is DM prioritization, not an owner research pause. Current methods already allow direct
learning tests without toy/proof prerequisites; they did not require this diagnostic chain.
Do not turn a bounded engineering assignment into the unit of scientific progress or a reason
to return control after each step. Reassess the next learning comparison by the direction-level
question and the decision its result could change; no extra governance gate is introduced.

## 2026-09-19 — owner-requested transfer to a new independent Astra/max DM task

The owner enabled memory for new sessions and requests a new independent Codex task with
Astra at max effort to continue FOLR directly as DM, without a Root dispatch layer. This old
task (01a0b9c5-7303-70d2-a6b7-12dc66d4ea79) relinquishes direction writing/launching when the
new task is created; it does not remain a coordinating Root. FSD stays exclusively with Claude.
The new task receives the current branch, notebook, completed evidence and local artifact
locations. There are no live FOLR scientific operations to transfer. Memory availability itself
is an application setting, not established by this repository entry.

Preserve the previously untracked action_contrast_a01 implementation and tests in this same
commit for recoverability. Focused/admission checks passed 10 tests; independent Reviewer ran
8 focused tests and found no material engineering defect. The diagnostic remains DESELECTED,
unexecuted and scientifically unaccepted as a next investment; publication grants no launch.
Do not spend another review/run merely to finish the discarded plan. The prior entry's
"untracked" status is superseded only as a storage fact, not as a scientific decision.

Continue by choosing a direction-level research question and a result that could change its
judgment. Compare worthwhile learning options against simple baselines, inherited adverse
evidence and actual cost. A prototype, formal explanation or diagnostic is not a required
pre-stage. The owner explicitly wants a continuous research loop: use bounded subagents where
useful, retain DM decisions, and do not return for permission at each ordinary step. Internal
reports and engineering scopes are not separate scientific milestones. No governance rewrite
or new rulebook is authorized by this handover.


## 2026-09-19 — new direct DM: last-sighting cache learning comparison A01

This independent task accepts direction ownership from the relinquished task, with no Root
or second DM. It read the constitution, current RESEARCH, complete current notebook and the
scientific/engineering methods including `f3402661876781536afd23226aa212c21623e5fb`.
Author checkout is `/home/fires/.codex/worktrees/1275/hmasd-wsl`, branch
`codex/folr-direct-dm`; merge `99d0a65e3` retains main `22f998ae2` and the inherited direction
commits, preserving main's newer FSD row. FSD remains exclusively with Claude; there is no
live FOLR operation to recover. The previous checkout and its untracked binary evidence stay
in place. Available memory had no relevant project entry; Git and this notebook supplied the
continuity. No memory write or governance change was made.

### Direction question and choice

Question: on the existing small host with changing membership, can an explicit lifetime-scoped
cache of lawful last observations improve learned team control over the competent Generic64
recurrent baseline? A consistent useful result would support taking this simple representation
forward; an adverse or unresolved batch would leave no reason to promote it, and would lower
the priority of further small-host history packaging without a materially new reason. Neither
outcome establishes the benefit specifically caused by N changes, arbitrary-N generalization,
UAV performance, memory necessity or optimality.

This follows the adverse auxiliary reading and the scope correction above. The old persistent
augmentation added a learned pair-GRU stream and fusion, and its initial positive was not
reproduced. A01's coupled reward predictor also had an adverse native observation. Those facts
weaken those packages, not every use of lawful history. Selected here is a different hypothesis:
a deterministic last-sighting cache can make useful past measurements accessible without
asking a second learned memory system or proxy loss to discover what to store. It does not
reopen either closed study or claim to diagnose their failure.

Alternatives considered: further auxiliary coefficients/seeds would rescue an already adverse
package without a new discriminating reason; scaling Generic capacity/horizon would study an
optimization budget choice but not directly answer whether simple history organization earns
its cost; repeating old augmentation lacks new information beyond its failed repetition.
Idling remains a legitimate alternative, but a same-parameter, direct native comparison can now
resolve the use choice more directly than further geometry, reconstruction or hidden-state
intervention diagnostics. This is a package screen, not a mechanism-identification experiment.

### Fixed comparison and reading

- GENERIC_RETAIN: unchanged `entity_history_b01.model.Actor` with GRU64 and all existing legal
  visibility/seen/age and truthful public lifecycle metadata.
- LAST_SIGHTING: the exact same trainable modules, parameter shapes, constructor RNG and
  Generic GRU64, but the attention token for an active previously seen subject carries that
  observer's last visibly observed nine physical/previous-action values. Both observer and
  subject continuation are required to retain a cache cell. Clear on either lifetime break;
  overwrite only on current visibility. Attend over active seen subjects. The existing
  current visibility, seen and age metadata stay current, so old values are not labelled fresh.
  Never cache hidden current values, another observer's sightings, privileged motion or future
  labels. No new learned parameter, auxiliary target, predictor, trainable branch or loss.

Both arms retain the unchanged entity-history environment, local actor information rights,
central FlexQMixer information, gamma .99 double-Q loss, RMSprop .0005/.99/.00001, norm 10,
200-episode target schedule, full-episode replay and epsilon law. Capacity in trainable
parameters and training exposure are matched; deterministic storage, available attention
tokens and read bandwidth intentionally differ. The cache is a last-observation heuristic,
not a Bayesian belief or a forecast. It can hurt through stale tokens and attention dilution.
Expected native sign is LAST_SIGHTING minus GENERIC_RETAIN positive, with low confidence.

Exactly SIX fresh fits: both arms at unscreened training seeds 784101, 784201, 784301.
Each runs 5000 H20 training episodes / 100000 transitions / 4969 optimizer updates, then
one final checkpoint and 128 greedy evaluation episodes with evaluation seed 1784101.
No tuning, prefit, interim evaluation, selected checkpoint, probe panel, diagnostic replay,
additional seed or outcome-based extension. Totals: 30000 training episodes, 600000 training
transitions, 29814 optimizer updates, 768 final episodes / 15360 final transitions, six final
checkpoints. This new idea consumes all six of its default fits; every started attempt counts.
The six are selected prospectively together; partial scores do not select which fits finish.

Primary reading is each sole-final mean native episode return, all three signed within-label
contrasts and their descriptive mean/range. Independent training instances, not episodes, are
the replication units. Common initialization/seed labels do not supply paired counterfactual
worlds; evaluation remains conditional on one common nominal evaluation schedule. Report all
scores and curves without a significance, equivalence or frozen-confirmation verdict. Native
benefit across instances supports this complete cache package for further consideration;
mixed/adverse outcomes constrain it and do not become a memory-capacity verdict. No amount of
cache activation substitutes for native gain. No population precision is promised from three
instances. Lifecycle counts and retained final trajectories are descriptive/recoverability
outputs, not another scientific selection stage.

Execution is local_linux CPU FP32, one Torch intra/inter-op thread per fit, independent RNG,
replay, learner and output. Up to six original fits may overlap subject to actual admission;
FSD's remote compute is untouched. Current host reports 16 logical CPUs and about 11 GiB
available; that observation does not substitute for fresh launch memory checks. A01 used about
30 minutes and 0.7 GiB RSS per fit locally; cache/runtime cost is not yet measured. Planning
estimate is 45–75 minutes for the concurrent batch, not an endpoint or kill line. Retain wall,
CPU and single-process peak RSS and the actual batch span.

### L0: cache actor and fixed six-fit runner

Implementer owns only `experiments/candidates/vap_folr_core/last_sighting_a01/`,
`scripts/run_folr_last_sighting_a01.py` and mirrored tests under
`tests/experiments/candidates/vap_folr_core/last_sighting_a01/`. Reuse environment, collection,
native learner update and mixer by import; do not edit historical code or control tools.
DM alone owns NOTES and Git index/commits. Return unstaged diff, focused checks and limitations;
no result-bearing run, other source edit, Pro send or children.

Actor may pack GRU64 plus the 5x9 raw cache per observer for online collection, while replay
reconstructs the same causal cache from complete observation sequences. Learner constructor
selects the actor, then uses the existing native update/save contract unchanged. Bind arms,
training seeds, single evaluation seed and counts in the new entry. Admission and exact launch
SHA precede model/environment/output effects. Publish source/config, actual counts, incremental
returns and update loss JSONL, parameter movement, final checkpoint, full final arrays and their
digests, lifecycle counts, incomplete/error status and resource scope. Final evaluation has
zero new updates. Do not import the auxiliary learner or invoke the deselected diagnostic.

Focused checks cover identical initial trainable state and RNG; exact unchanged Generic native
update/target synchronization; cache contents against hand-computed lawful sequences; no hidden
current/other-observer leakage; observer/subject departure, birth and slot reuse; online versus
whole-sequence Q/state equivalence; no stale cache after lifetime breaks; same Q/GRU as Generic
when all subjects are always visible; real loss updates for candidate on synthetic complete
batches; fixed-runner counts, admission-before-effects, terminal/no-update evaluation and
failure retention. Tests use managed scratch and synthetic inputs, with no undeclared native
fit/evaluation. Independent Reviewer checks this executable change before acceptance/launch.
A focused Critic is assessing scientific value and the distinction from old augmentation;
the DM will record any material change before publishing executable inputs.


### Independent scientific criticism before execution

ResearchCritic checked the actual old actors/learner and A01 summaries and returned
MATERIAL_DISSENT=no. Accepted: the smallest useful discriminator is this learning comparison,
not a prerequisite diagnosis. Equal trainable shape does not equal storage or computation;
cache success cannot identify N-change causality or defeat every tuned Generic alternative.
Stale-token interference can cause failure without proving history redundancy. The negative
history/auxiliary observations remain constraints on expectations. No extra arm, diagnostic or
design change is selected. The six-fit scope and all outcome branches above remain in force.


### Cache A01 implementation accepted before the six original launches

The direct owner is Codex task `01a0bbd6-6cfa-74e3-82d3-b2afe7fa9426`. The DM read the complete
actor, learner, artifact, publication and runner diff and accepts the declared L0. Independent
Reviewer traced the full path and reports no material finding; it ran 34 focused new/inherited
checks. Implementer separately reports 16 new and 12 inherited entity-history checks. The DM's
source/CLI admission regression passed 2 tests. These are synthetic/source checks, with no native
training or policy evaluation. Scratch was managed and cleaned by pytest.

Both actor/mixer initial trainable states and constructor RNG match exactly. The Generic
wrapper retains exact inherited update, optimizer and target synchronization on the checked
batch. The cache actor's online and whole-sequence Q/state replay are exact in its focused
check. With all subjects visible, its per-step attention versus Generic's batched-time
attention differs by ordinary FP32 rounding (observed max Q difference 2.24e-8); this is not
claimed bit-identical or a universal error bound. The intervention includes its deterministic
state/read path and numerical execution organization. No changed reward, actor privilege,
training exposure or source-native evaluator is introduced.

Publish the accepted exact source, then admit the six already selected original fits. This
acceptance adds no scientific fit, arm, parameter search or diagnostic. Each native operation
will be linked below; original accepted handles must be reconciled, never blindly repeated.


### Six original A01 operations admitted

All six selected original requests returned accepted at published source
`e7ba09858760a29903e5d23e91b274a333d8feb6` after fresh canonical policy/publication and
actual local_linux memory checks. There are six selected attempts and no replacement/retry.
Snapshots preserve input code while authoring continues. Native operation identities, process
witnesses and commands are retained in the following runner-owned manifests:

- [generic 784101](../../../../runs/vap_folr_core/last_sighting_a01_generic_784101/launch-manifest.json)
- [cached 784101](../../../../runs/vap_folr_core/last_sighting_a01_cached_784101/launch-manifest.json)
- [generic 784201](../../../../runs/vap_folr_core/last_sighting_a01_generic_784201/launch-manifest.json)
- [cached 784201](../../../../runs/vap_folr_core/last_sighting_a01_cached_784201/launch-manifest.json)
- [generic 784301](../../../../runs/vap_folr_core/last_sighting_a01_generic_784301/launch-manifest.json)
- [cached 784301](../../../../runs/vap_folr_core/last_sighting_a01_cached_784301/launch-manifest.json)

The bounded Monitor has these exact original handles; DM retains scientific reading and
collection responsibility. The first sampled progress shows 200 episodes / 169 updates for
the earliest three launches; later starts have not yet emitted their first 200-episode summary.
No early score is used for selection. Terminal witnesses, final artifacts and scientific
interpretation are pending. This is an active producer, not a new authorization request.


## 2026-09-19 — last-sighting A01 complete: three adverse native contrasts

All six original operations have matching native terminal witnesses, exit zero and complete
runner summaries. Monitor reconciled the original identities and returned an empty active set;
DM collected and read every selected outcome. There was no failed fit, replacement, added seed,
selected checkpoint or new scientific execution during readback. This exact exploratory study
ends at its six selected fits, with all six charged to the idea.

| Training seed | Generic sole-final mean | Last-sighting sole-final mean | Cache minus Generic |
| --- | ---: | ---: | ---: |
| 784101 | -0.195781250 | -0.429843750 | -0.234062500 |
| 784201 | 3.774531250 | 0.935390625 | -2.839140625 |
| 784301 | 1.964140625 | -1.224453125 | -3.188593750 |

Descriptive mean difference is **-2.087265625**, range [-3.18859375, -0.2340625]. Generic's
three-fit mean is 1.8476302083 and cache's is -0.2396354167. All three signs oppose the
prospective positive expectation; the first contrast is small relative to its conditional
panel variation. These are three fresh instances per arm in an exploratory package screen,
not a new confirmation, a significance/equivalence verdict or episode-level replication.
The common evaluation label does not create paired counterfactual worlds. Episode standard
errors in each summary are conditional panel descriptions, not uncertainty on a learning effect.

### Complete exposure, validation and recoverability

Each fit has exactly 5000 H20 training episodes, 100000 native training transitions and 4969
native actor/mixer optimizer updates, one final checkpoint, then 128 greedy episodes / 2560
transitions and zero evaluation updates. Totals: six fits, 30000 training episodes, 600000
training transitions, 29814 updates, six final checkpoints and 768 final episodes / 15360
transitions. Both arms have 103173 actor parameters; all actors and mixers moved from their
initial values. First-500 train means were between -12.1862 and -11.05586; last-500 means
between -2.30656 and +1.26492. This documents learning under the fixed recipe, not convergence
or optimality; exploratory behavior and policy-induced data differ over training.

DM independently checked the admitted and summary SHA against
`e7ba09858760a29903e5d23e91b274a333d8feb6`; all recorded source hashes; every checkpoint,
progress file and panel container/content digest; finite checkpoint/optimizer tensors and
nonempty optimizer state; all 5000 progress rows with exact cumulative update counts and
4969 finite losses; 128x20 final reward arrays and finite retained inputs; and all terminal
exit-zero witnesses. Checkpoints retain actor, mixer, targets and optimizer. Recomputing final
returns from FP32 reward arrays differs from native float64 sums by at most 9.211153e-7;
primary values use the original native sums. The committed six-endpoint `study_result` reader
and independent arithmetic agree. No new model call, environment step or fit was used to
verify these outputs.

The source review's 34-check invocation covered
`tests/experiments/candidates/vap_folr_core/last_sighting_a01` and
`tests/experiments/candidates/vap_folr_core/entity_history_b01`, with the configured scientific
interpreter; the separate admission/source regression passed two checks. No source changed
after acceptance or during execution.

All six summary/progress/exit files are published together with this reading:

- [generic 784101 summary](../../../../runs/vap_folr_core/last_sighting_a01_generic_784101/summary.json)
- [cached 784101 summary](../../../../runs/vap_folr_core/last_sighting_a01_cached_784101/summary.json)
- [generic 784201 summary](../../../../runs/vap_folr_core/last_sighting_a01_generic_784201/summary.json)
- [cached 784201 summary](../../../../runs/vap_folr_core/last_sighting_a01_cached_784201/summary.json)
- [generic 784301 summary](../../../../runs/vap_folr_core/last_sighting_a01_generic_784301/summary.json)
- [cached 784301 summary](../../../../runs/vap_folr_core/last_sighting_a01_cached_784301/summary.json)

The final.pt, final-panel.npz and stdout/stderr for each tag remain at their original durable
local output paths under `/home/fires/.codex/worktrees/1275/hmasd-wsl/runs/vap_folr_core/`.
These binaries total 28421192 bytes and are ignored by Git; exact paths and hashes are in the
summaries. Preserve this checkout and these outputs before any later cleanup. The old author
checkout and its A01 binaries were not modified or removed. All snapshots and native claims
also remain available; no cleanup is part of this study.

| Fit | Runner wall seconds | Process CPU seconds | Process peak RSS KiB |
| --- | ---: | ---: | ---: |
| generic 784101 | 2236.081 | 2236.435 | 571816 |
| cached 784101 | 2411.219 | 2411.447 | 525360 |
| generic 784201 | 2275.363 | 2275.779 | 575692 |
| cached 784201 | 2426.246 | 2426.342 | 524996 |
| generic 784301 | 2254.167 | 2254.532 | 576612 |
| cached 784301 | 2425.922 | 2425.816 | 523636 |

First native acceptance to last OS exit was 2526.038 seconds (42.10 minutes); runner walls
sum to 14028.998 seconds and single-process CPU seconds to 14030.350. These fits overlapped;
the sum is not elapsed batch time. Maximum individual process peak RSS was 576612 KiB, not
a simultaneous six-process memory peak. Runner walls include imports/preparation from the
runner clock; code development, source publication and launch preparation before acceptance
are outside the batch span. No controlled speed/efficiency claim is made.

### Working explanation and scientific decision

Observed: the expected positive native sign failed in all three instances, with two sizable
adverse point contrasts. This strengthens the practical reason to prefer the unchanged Generic
recipe over this cache package for the measured use. It weakens the conjecture that making raw
last sightings explicit, while removing the old extra learned memory/fusion or auxiliary
objective, is by itself enough to improve finite-budget control here. A stable population
ranking is not established, and the small first contrast does not establish equivalence.

Representation opportunity remains conditional: lawful history can distinguish some actions,
but that source-derived possibility never predicted an automatic learned benefit. Cached input
can be stale, attention access is changed, and learning/team co-adaptation differs. These
remain possible explanations, not diagnosed causes of the observed loss. The result does not
measure a Generic capacity deficit, a causal N-change increment, arbitrary-N transfer or UAV
value. Equal learned parameter count does not make storage, read bandwidth or computation equal.

Decision: end this raw last-sighting idea without extension, age-gating/size tuning, confirmation
or UAV promotion. Retain the old augmentation and auxiliary adverse evidence alongside this
new three-instance result. No currently specified next intervention has enough independent
scientific reason to justify another small-host packaging or diagnostic chain. FOLR therefore
remains an owner-chosen **exploring direction, currently idle**, with no running producer or
outstanding user-approval request. This is an investment judgment about the available next
steps, not archiving, an owner pause, or falsification of useful history generally.

A concrete re-entry reason would be independently grounded evidence of a modifiable learning
or target-host membership mechanism that predicts a different native outcome, or a better
justified direction-level comparison. Mere completion, a new name, another auxiliary
coefficient, a raw-cache attention tweak or a hidden-state intervention is not such evidence.
No additional result invocation is selected by this entry. The task has progressed from its
inherited unresolved choice through an entire reviewed learning comparison to this readable
scientific boundary, rather than returning after an internal engineering step.


Independent ResearchCritic read all six summaries and returned MATERIAL_DISSENT=no on this
update and idle decision. Accepted wording: removing the extra learned stream/proxy loss
through this raw-cache design did not produce the predicted benefit; it does not identify
whether optimization burden caused older failures, since content and attention also changed.
Improving exploratory training returns do not establish convergence or horizon adequacy.
The idle judgment is "no worthwhile next intervention presently identified", not a permanent
prohibition on future exploration. No additional comparison is selected or needed for the
present decision not to promote this package.


## Pro question 2026-09-19 folr-n-axis-cumulative-synthesis

Conversation: new via Jev; the private account conversation address stays only in the local
transport operation, never in this notebook or Git. The question key will identify delivery.

Question type: direction-level evidence synthesis and next-useful-comparison advice, not
Portfolio, confirmation approval, a compulsory post-result review, or an execution request.

**核心问题：在成员变化后的合法历史组织这一 N 轴问题内，累计证据究竟改变了什么判断，
现在是否存在一项比暂时空闲更值得投入的比较？如有，为什么它能改变一个有价值的选择；
如无，哪些具体证据会使这个判断值得重看？** 请审视目前 DM 的空闲判断，不必赞同它，
也不必为了继续而发明新架构。最后推荐一个下一步（可以是 idle）及其最强替代选项。

### Owner instruction, current status and allowance

Owner now asks: “可以 做好证据综合发送Pro即可 使用Jev”. The scope of this request is the
synthesis and Pro consultation; no new fit is selected. The existing owner instruction keeps
this Codex task itself as FOLR DM, with no Root layer/additional DM and with bounded advisers
returning facts. FSD remains exclusively Claude-owned; do not take over FSD, start TRDL or make
Portfolio decisions about other directions. General research pause is lifted in RESEARCH;
FOLR is exploring but currently idle after the completed cache batch. No live FOLR experiment
or uncertain launch exists. Advice itself grants neither a fit nor a direction change.

The old auxiliary batch ended at its selected 2/2 fits; unused default allowance is not an
extension. The cache idea used all selected 6/6 fits and ended. A genuinely prospective idea
inside the already chosen direction can use the constitution's default up to six fits after
its own question/design/exposure is recorded; this is not a per-idea owner-approval gate.
Do not rename the same tuning or extend a closed batch after scores. A claim confirmation
would need a new prospective claim, its own fresh seeds and fixed rule. Nothing here selects it.

Current evidence and methods are published on `codex/folr-direct-dm`. Main at
`22f998ae22be147ec000edfeef630f7008fad47d` still has the earlier FOLR standing; accepted direction
commits through `b8167ff68e49f1f3aaff1ef8a99154c401c8e853` have not been integrated there.
Use the pinned source of THIS question, not moving main. The main integration is a shared-write
follow-up, not scientific evidence or a prerequisite to this advice. Preserve FSD's current row.

### Direction question and actual comparison setting

The research goal is a defensible answer about organizing a continuing agent's legitimately
available history after physical membership changes, against competent generic recurrence,
ultimately relevant to the UAV host. The present native results are on easy Traffic Junction:
7x7 cross road, H20, five padded slots/five actions, vision 1, actual arrival/departure/slot
replacement and a native team reward. `collect` resets without a curriculum `t_env`, so the
arrival law stays at its initial setting. This is not a held-out agent-count transfer experiment,
open ad hoc teamwork with unknown partner policies, or a measured UAV result. Current actor
labels/metadata and FlexQMixer are fixed to five slots; changing max N is not a neutral config edit.

The lawful interface supplies truthful public lifecycle information; each observer sees only
allowed current physical/previous-action values. Modern Generic additionally receives its own
subject-wise visible/seen/age metadata and has a 64-dimensional recurrent state, reset only on
its own lifetime break. It can already retain lawful history through other agents' departures.
The current-only augmentation Z still has this Generic recurrence. Neither G nor Z is a
memoryless baseline. Central training mixer information does not become actor information.
All joint team policies co-adapt during training; changing one learning package changes data,
partner continuation and future visibility as well as fitted weights.

The recent native recipe is complete-episode replay/double-Q FlexQMixer, gamma .99, RMSprop
lr .0005/alpha .99/eps .00001, norm 10, target update every 200 episodes, fixed epsilon law.
A full fresh fit is 5000 H20 episodes / 100000 transitions / 4969 optimizer updates, one final
checkpoint, then 128 greedy episodes with zero updates. The earlier public-lifecycle B01-B03
used only 32 final episodes and a simpler public-input actor without the later seen/age table.
Training-instance effects and conditional evaluation noise must remain distinct. Shared seed
labels do not certify paired counterfactual worlds. No pooled leaderboard, cross-study causal
A/Z/G ranking, or trained-population significance/equivalence is licensed by these tables.
No tuned same-information headroom or converged Generic optimum has been established.

### Cumulative evidence: preserve positive, adverse and incomplete observations

The following is a bounded synthesis of the scientific families relevant to this decision,
not a claim that all direction-lifetime fits, failed attempts and support costs were enumerated.
Paths in this section are relative to `docs/research/candidates/vap_folr_core/` unless otherwise
stated. Historical file vocabulary and decision rules remain evidence, not current governance.

| Earlier family | Observations and comparison unit | What this changes / leaves unresolved |
| --- | --- | --- |
| N3 routing B04 on the separate B3 three-transition host | Three seeds; TYPED minus GENERIC stale-load AUC +0.0026041667, within original .05 MEI; both learned final returns .98828125, RESET .5065104167, simple LATCH .9986979167. Writer/routing horizons differ entirely from H20 Traffic Junction. | Lawful carried information can be useful in that constructed task, while a typed route did not establish an increment over learned Generic. Not a Traffic Junction or UAV result; within-MEI is not equivalence. Source: [B04](N3_FOLR_ROUTING_B04_RESULT_EVIDENCE_20260904.md). |
| Public-lifecycle RETAIN vs event RESET B01-B03 | Three successive fresh pairs, 32 final episodes per fit: RETAIN minus RESET -2.0021875, -1.9228125, +2.559375. | Two reset-favoring observations followed by reversal; both sides must survive. These are separately trained reset policies, not post-training hidden-state erasure. Sources: [B01](FOLR_PUBLIC_LIFECYCLE_B01_RESULT_EVIDENCE_20260909.md), [B02](FOLR_PUBLIC_LIFECYCLE_B02_RESULT_EVIDENCE_20260909.md), [B03](FOLR_PUBLIC_LIFECYCLE_B03_RESULT_EVIDENCE_20260909.md). |
| Event timing B01-B03 | At 128 final episodes: EVENT minus RETAIN +2.804765625, -.590703125, -5.44609375. In B01 EVENT minus RANDOM +1.363671875; B02 RANDOM minus RETAIN -.140859375. B03 was a RETAIN/EVENT pair. RANDOM uses p=.1 per eligible survivor and is not reset-dose matched. | Initial apparent timing benefit did not persist across the later realizations. No event-timing causality or universal retention/reset ranking. Sources: [timing B01](FOLR_PUBLIC_LIFECYCLE_TIMING_B01_RESULT_EVIDENCE_20260909.md), [B02](FOLR_PUBLIC_LIFECYCLE_TIMING_B02_RESULT_EVIDENCE_20260910.md), [B03](FOLR_PUBLIC_LIFECYCLE_TIMING_B03_RESULT_EVIDENCE_20260910.md). |
| Fixed-half and learned scalar retention | HALF minus RETAIN +1.56546875 then -4.293046875; LEARNED minus RETAIN +1.763359375, -1.76953125, -1.215546875. Each is a fresh selected pair at 5000/4969/128. The learned gate adds 129 coefficients. | More gradual/trainable retention did not establish a stable package gain. Does not identify useful-memory selection or prove gates inherently harmful. Sources: [HALF B01](FOLR_PUBLIC_LIFECYCLE_HALF_B01_RESULT_EVIDENCE_20260910.md), [B02](FOLR_PUBLIC_LIFECYCLE_HALF_B02_RESULT_EVIDENCE_20260910.md); [LEARNED B01](FOLR_LEARNED_RETENTION_B01_RESULT_EVIDENCE_20260911.md), [B02](FOLR_LEARNED_RETENTION_B02_RESULT_EVIDENCE_20260911.md), [B03](FOLR_LEARNED_RETENTION_B03_RESULT_EVIDENCE_20260911.md). |
| Entity-history replacement BANK | B01 Generic stopped at 4253/5000 episodes with no final endpoint, so no pair polarity. A later reference-use comparison used one new Generic fit against the fixed old BANK and observed -5.932421875; zero new BANK fits. Fresh/fresh B02/B03 then gave BANK minus Generic -4.830859375 and -6.63671875. | Technical incompleteness and retained-policy evaluation are not extra learning replications. The two fresh negatives constrain the replacement GRU16 entity-bank package, which differs in architecture/capacity from Generic64. Sources: [incomplete B01](FOLR_ENTITY_HISTORY_B01_RESULT_EVIDENCE_20260912.md), [reference-use](FOLR_RETAINED_REFERENCE_USE_B01_RESULT_EVIDENCE_20260913.md), [B02](FOLR_ENTITY_HISTORY_B02_RESULT_EVIDENCE_20260914.md), [B03](FOLR_ENTITY_HISTORY_B03_RESULT_EVIDENCE_20260914.md). |

The historical public families and newer entity-history families differ in actor interface and
intervention; do not pool them to infer a single memory effect. The B3 writer/routing phases
and native H20 fits also have different exposure units. Original MEI/category readings remain
unchanged; this consultation does not reclassify frozen results under a new rule.

| Recent family | Complete observed native evidence | Design and interpretation |
| --- | --- | --- |
| Learned persistent augmentation A vs Generic G | Discovery A-G +5.29640625 (one fresh fit per arm); prospective later repetition -5.830625 and -.109921875 (two fresh fits per arm), original MIXED_BLOCK_PATTERN retained. | A keeps Generic64 and adds learned pair-GRU16 plus attention/fusion; actor params G103173/A192741. The positive discovery is preserved, but it did not reproduce in the two later blocks. Package evidence, not isolated persistence. Sources: [discovery](FOLR_ENTITY_HISTORY_AUGMENTATION_B01_RESULT_EVIDENCE_20260914.md), [repeat](FOLR_ENTITY_AUGMENTATION_REPEAT_B01_RESULT_EVIDENCE_20260915.md). |
| Persistence/current-augmentation decomposition | Separate fresh comparisons: A-Z -3.069453125; Z-G -4.44375. One fit per arm in each different study. | Z retains Generic recurrence; A/Z have the same augmented modules, G fewer parameters. These outcomes cannot be algebraically chained into a cross-study causal ranking. Sources: [A-Z](FOLR_ENTITY_PERSISTENCE_B01_RESULT_EVIDENCE_20260914.md), [Z-G](FOLR_ENTITY_CURRENT_INCREMENT_B01_RESULT_EVIDENCE_20260914.md). |
| Predictive auxiliary A01 | DETACHED 2.69046875, COUPLED -3.8690625; difference -6.55953125. One fresh fit per arm, complete. Common uniform-policy prediction MSE 1.9158295 vs 1.8038883 on identical semantic panel bytes. | Both train a separate linear head predicting next-three-step mean team reward; only COUPLED sends .1-weight head-loss gradient into Generic actor. Slightly better probe prediction with worse native control weakens this package; probe law differs from trained behavior. It diagnoses neither history redundancy nor a causal representation failure. Source: earlier A01 prospective/result entries in this NOTES; implementation `356bb3cc53479946bc031a24ada1ea979769fddf`. |
| Deterministic last-sighting cache A01 | Six fresh fits, three per arm. Ordered cache-G differences -.2340625, -2.839140625, -3.18859375; descriptive mean -2.087265625. | Same learned Generic64 modules/103173 actor parameters and constructor RNG, unchanged native learner; own last-visible 5x9 measurements cached and cleared on either observer/subject lifetime break, attend over active seen subjects. No learned bank/fusion or auxiliary loss. Storage/read bandwidth and numerical execution organization differ. All three point signs adverse; not a confirmation, universal population harm or equivalence of the smallest contrast. Source: prospective/result entries in this NOTES; implementation `e7ba09858760a29903e5d23e91b274a333d8feb6`. |

Cache sole-final values (all 128 episodes, common evaluation seed 1784101):

| Training seed | Generic | Cache | Cache minus Generic |
| --- | ---: | ---: | ---: |
| 784101 | -.19578125 | -.42984375 | -.2340625 |
| 784201 | 3.77453125 | .935390625 | -2.839140625 |
| 784301 | 1.964140625 | -1.224453125 | -3.18859375 |

These recent tables together contain 18 selected fresh fits across different questions; that
is not the lifetime total, not 18 repetitions of one hypothesis and not a pooled inference unit.
All new A01 outputs retain native summaries/progress/terminal witnesses, actual counts and
parameter movement. The DM verified finite populated checkpoints and artifact/source hashes;
Pro must distinguish that reported local verification from what it can itself inspect remotely.
Binary checkpoints/panels are local only at the recoverable paths in the preceding NOTES entries.
They are not available through GitHub. Per-episode train/final returns and per-update progress
for the new studies are in Git. Improving exploratory train returns do not prove convergence.

Recent supporting output roots, all at source_sha:
- `runs/vap_folr_core/predictive_aux_a01_detached_783101/` and
  `runs/vap_folr_core/predictive_aux_a01_coupled_783101/`: `summary.json`, update JSONL and exits.
- `runs/vap_folr_core/last_sighting_a01_generic_784101/`, `last_sighting_a01_cached_784101/`,
  `last_sighting_a01_generic_784201/`, `last_sighting_a01_cached_784201/`,
  `last_sighting_a01_generic_784301/`, `last_sighting_a01_cached_784301/`, all under
  `runs/vap_folr_core/`: `summary.json`, `training-progress.jsonl`, `process-exit.json`.

### What the analytical and diagnostic work does NOT add

The source-derived 7x7 counterexample in this NOTES establishes conditional one-step opportunity:
with a specified known teammate motion law, the same lawful current cues but different earlier
sightings permit different preferred actions, while uniform focal-action-averaged reward means
can coincide. It is not the actual learned teammate law, the fully uniform team probe, the
three-step target, H20 gain, a Generic representational shortfall, or an N-change-specific increment.
Post-hoc retained-panel geometry counted 718/7281 (DETACHED final), 180/7591 (COUPLED final) and
297/7072 (common probe) active observer ticks. These are policy-induced geometric strata, not
avoidable collisions, causal effects or realizable headroom. One-step local gains cannot be
summed into episode benefit. Erasing trained hidden state would be a distribution-shifting
intervention and would not identify insufficient/sufficient memory capacity.

The implemented `action_contrast_a01` environment-reconstruction/counterfactual diagnostic was
DESELECTED before launch. It has zero actual-checkpoint replay and zero new fits; code review
success supplies no scientific reason to execute it. Do not revive it merely because it exists.
The owner corrected an earlier chain of narrow toy/geometry/replay questions that could be
answered rigorously but did not justify their cost or reliably identify long-run learning
bottlenecks. Direct learning comparisons are permitted without toy success, history-necessity
proof, a perfect mechanistic account or exhaustive headroom/diagnostic preliminaries.

### Working explanation to challenge, and the live decision

Observed package failures lower the practical case for the tested ways of organizing history.
They do not by themselves separate (i) decision-relevant opportunity under the actual joint
policy, (ii) what a generic recurrent representation can hold, (iii) what it learns at this
exposure, and (iv) whether the total candidate earns its extra costs. The source counterexample
supports a possibility in (i), not its materiality; the learning screens mostly address (iv).
The older positive observations prevent rewriting the history as uniformly negative.

DM's present judgment: do not promote the failed cache/auxiliary/old augmentation packages.
With no specifically justified successor currently selected, leave FOLR idle for investment
reasons. This is open to challenge and is not a claim that the N-axis question is exhausted.
In particular, a list of negative packages is not already a paper-grade negative answer about
legal history or membership changes. A generic capacity/horizon issue, task/distribution issue,
attention/credit issue or new useful representation is not established just by naming it.

Compare a small number of actually plausible choices, not an obligation to fill a candidate
list: a direct finite-learning comparison on this host when a concrete alternative supports it;
a materially justified focus on a membership mechanism/target-host question within FOLR;
a specifically useful existing-evidence or primary-source bridge; and remaining idle. A change
of task/population/question must be named, not presented as replication or a budget reset. Do
not assume the UAV adapter/baseline already exists for the proposed question. Broader direction
activation/archive/reprioritization can only be advice for an owner-triggered Portfolio later.

If you recommend a next comparison, explain the resulting defensible claim or use decision,
its strongest simpler explanation, the competent matched-information baseline and any relevant
training/tuning exposure, the predictions that differ, and what each outcome would change.
For a targeted repair give intermediate AND native predictions; for a package screen explicitly
forgo attribution where appropriate. Propose the smallest informative exposure, count every arm,
seed and tuning/auxiliary fit, and account for dominant non-fit work. Unchanged replication can
be valid when repeatability really changes a decision; a new architecture is not required.
Do not automatically tune one of the closed packages or propose a long diagnostic prerequisite
chain. If idle remains best, state why compared with the strongest feasible continuation and
what would make a return worthwhile; exhaustive falsification is not required.

Known cost context: cache A01's six overlapping local CPU FP32 fits took 42.10 minutes from
first acceptance to last OS exit; summed runner wall 14028.998 s, max individual RSS 576612 KiB.
Each cache fit was about 40 minutes, each Generic about 37–38 in that concurrent batch. Auxiliary
A01 took 1785.395 and 1844.114 s per process. These are recorded implementation facts, not a
universal fit rate or total research cost. Full lifetime engineering/provider/support cost is
unknown. Larger models, supervised preparation, simulation branching and nested search are real
work even if they are called zero RL fits. No universal benchmark sweep or prototype is required.

### Context and source precedence

All repository paths here resolve at **source_sha**, the full immutable question commit supplied
in the actual send message, unless an explicit older execution revision is named. The older
execution SHAs identify the original experimental semantics; current methods do not rewrite them.
Read the question and the decision-relevant sources before answering; use the synthesis as a map,
not a substitute for consequential source checks. No recursive historical-governance preload.

Current governance / method:
- `docs/project/OPERATING_CONSTITUTION.md`, sections 1–5 and 7–8: project objective, current
  responsibility, fits, records, advisory Pro and scientific minima. The newer direct-DM owner
  assignment and consultation-only scope above apply to this task.
- `docs/research/RESEARCH.md`, owner pause and FOLR row: branch's current direction standing;
  other directions are context only.
- `.agents/skills/hmasd-scientific-tools/SKILL.md`, Explore an idea / Update the working
  explanation / Simple-model and literature bridges / Comparators / Statistics / Cost and
  exposure: cumulative judgments, direct comparisons, no required toy gate, information and cost.
- `.agents/skills/hmasd-research-engineering/SKILL.md`, Core versus experimental / Checks and
  review / Execution and admission: only when a proposed next step depends on implementation
  or feasibility. It adds no scientific authority or mandatory pre-research approval.

Core evidence and mechanism checks:
- This `NOTES.md`: inherited evidence; predictive auxiliary A01 prospective and complete result;
  native counterexample and qualifications; scope correction before diagnostic launch; cache
  A01 prospective entry and complete six-fit reading. Older family result files are linked above;
  follow the ones that bear on your consequential conclusions, preserving their bound meanings.
- `experiments/candidates/vap_folr_core/public_lifecycle_b01/native_env.py`, `environment.py`,
  `collection.py`, `learner.py`, `flex_qmix.py`: actual reward/dynamics, lifetime and training path.
- `experiments/candidates/vap_folr_core/entity_history_b01/environment.py`, `model.py` and
  `entity_history_augmentation_b01/model.py`: lawful own-observer information, Generic, BANK and A/Z.
- `experiments/candidates/vap_folr_core/predictive_aux_a01/learner.py` and
  `last_sighting_a01/model.py`: actual two recent interventions. Their runners are
  `scripts/run_folr_predictive_aux_a01.py` and `scripts/run_folr_last_sighting_a01.py`.
- New run summaries/progress listed above; read the fields/output needed to substantiate your
  conclusion. Do not claim to have read unavailable local binaries or to reproduce a local check.
- `docs/research/designs/PREDICTIVE_INTERACTION_AUGMENTATION_PROPOSAL_20260919.md`, sections 1–2
  and 4–6, is the original optional proposal, not an adopted experiment roadmap. H-aux has now
  one adverse realization; H-pre is untested. A larger pretrained model is not the default rescue.
- If recommending a concrete UAV path, inspect relevant actual source such as
  `envs/uav_service_restoration/README.md`, `env.py`, `observations.py`, `events.py`, `baselines.py`
  and `adapter.py` as needed. Name any missing membership/history/comparator implementation;
  no UAV outcome or feasibility claim follows from this list or FSD's unrelated K-axis results.

For literature-based recommendations, verify primary passages and state the mapping, assumptions
and MARL coupling they omit. Literature and adviser agreement do not supply empirical replication
here. State any decision-critical source you could not read and narrow dependent conclusions.
Historical DIRECTION/Portfolio/packet rules and old chat instructions do not govern this question.

### Return and answer-only write boundary

Please answer in Chinese with a connected research argument, an explicit recommendation and
its strongest competing option. Distinguish observed facts, strengthened/weakened/untouched
judgments and fresh conjectures. Make the next observation's decision value concrete; no new
insight, positive result, prototype, fixed candidate count or new architecture is owed. Address
whether the DM's idle decision is justified and what a defensible eventual contribution would
actually require. Return MATERIAL_DISSENT yes/no for material disagreement with the current
interpretation/decision, and explain the disagreement if present. Do not create workflow rules.

Repository: `CartmanFatass/My-paper-code`.
Target branch: `codex/folr-direct-dm`.
Target path: `docs/research/candidates/vap_folr_core/NOTES.md`.
Question heading: `## Pro question 2026-09-19 folr-n-axis-cumulative-synthesis`.
Answer heading: `### Answer` immediately below, inside THIS question only.

Read the immutable question/source for reasoning, then fetch the latest target file and actual
blob SHA for writing. Write only the currently empty answer subsection. Preserve the question,
all preceding notebook bytes, all other files and all other answer sections; stop on overlap.
Do not add a top-level `## ` heading inside the answer (use `####` or prose) or it would end this
question's subsection. No training, model execution, new budget, governance edit, FSD/Portfolio
change or main integration is requested from Pro. Do not include private account identifiers
or the Jev conversation address in a repository write. On success report the actual answer
commit. If GitHub writing fails, return the full answer in chat so the author can preserve it
in this same subsection, not merely a receipt, link or invented commit. DM will read and record
adoption/modification/rejection separately; advice is not acceptance or execution authorization.

### Answer

Saved from chat by the DM on 2026-09-19, verbatim captured answer below. Jev confirmed
`send_effect=sent`, `completion=COMPLETE`; repository readback found no answer commit and the
assigned subsection was still empty. Pro reported that its GitHub connection exposed no write
operation. The returned `d3ead403aff96778852406441a5164f7dd3984ff` is the verified source file
blob, not an answer commit. The other returned SHA is the question commit.

Question key: `hmasd:c59e155bde8f0dab63843be1f93037522fe1ac808afe6d45e55d6035dbe1d53c`.
Question source: `ee648d5315febfac86d9c938398e36fb83009757`.
Captured answer text SHA-256 (before the transport's final newline):
`87055587d3002ef86abc27fe6e810d1df1409b82b435ce75e87dc0a86dbede79`.
The attachment-citation labels below are preserved as captured in chat; no unavailable link
or source verification is reconstructed from them. Private account facts remain local.

未能写回 GitHub，因此没有答案提交。 本会话的 GitHub 连接未提供写入操作。最后读取的目标文件 blob 为 d3ead403aff96778852406441a5164f7dd3984ff，与固定 source_sha 下的文件相同；题目未变，指定的 ### Answer 仍为空。以下是供保存到该小节的完整中文答案。

Answer

MATERIAL_DISSENT: no。

建议下一步保持 FOLR exploring、当前 idle，不追加拟合，也不推广已经结束的 cache、auxiliary 或旧 augmentation 包。 我同意这个当前投入判断，但同意的理由不是“历史已经被证明无用”，也不是“连续负结果足以关闭 N 轴”。累计证据改变得最明显的是：在目前这个宿主、合法信息接口和有限学习配方下，已测试的几种专门历史组织方式，越来越缺少值得继续投入的实际理由；它对“实际联合策略下还有多少历史机会”“Generic 能表示什么”“更长或不同训练会学会什么”的回答仍然很有限。

我认为最强的可行替代不是再制造一种记忆架构，而是对同信息 Generic 做一次有明确用途的训练曝光校准：检验更长训练是否值得其额外成本。下面给出这一备选的具体、较省曝光的形式，并解释为什么它目前仍不优于 idle。这是备选价值分析，不是选中一个实验，也不增加审批要求。

一、首先明确：当前比较不是“有历史”对“无历史”

本题真正关心的是：成员变化之后，一个继续在场的智能体，怎样组织自己合法获得的历史，才能在有能力的通用循环参照之外获得值得成本的收益？

Modern Generic 已经有自己的 GRU64，接收真实公共生命周期信息，以及该观察者自己的 visible、seen、age 元数据；别人的离开不会清空它自己的循环状态。Z 的“current-only”只针对新增实体流，并没有去掉 Generic 循环。因此，G、Z 都不是无记忆基线；“显式存下更多历史”也不是给一个完全没有历史的参照补上缺失能力。与此同时，Generic 有相应输入和循环状态，不等于它已经学会充分利用这些输入，更不等于证明了它在当前曝光下最优。

实际结果所在的宿主是 easy Traffic Junction：7×7、H20、五个填充槽位、五个动作、vision 1，确有出生、离开及槽位复用。但 collect 明确调用不带 t_env 的 reset()，普通加车分支的 add_rate 保持初值，而不是随累计训练进入更拥挤的 curriculum。当前演员标签、元数据形状和 FlexQMixer 也绑定五槽位。故这些结果回答的是这个固定实现中变化成员下的有限学习问题，不是未见 N 迁移、未知队友策略下的开放协作，也不是 UAV 实测结果。

这里还必须保留 MARL 的整体性：换掉一个学习包，不只改变最后的权重，还改变共同适应的队友、训练数据、离开与后续可见性的分布。相同种子标签不是动作之后仍相同的反事实交通世界。因而，当前最可靠的解释单位是完整学习程序在声明曝光下产生的结果，不能把团队回报差值直接命名为“记忆本身的因果效果”。

二、累计证据不是一串负号，而是对几种不同希望的逐步收缩

较早证据保留了“历史有用”与“专门组织未必有增量”同时成立的实例。 N3 routing B04 的独立 B3 三转移宿主中，TYPED 与 GENERIC 的最终 stale-load 回报均为 0.98828125，RESET 为 0.5065104167，简单 LATCH 为 0.9986979167；TYPED−GENERIC 的 AUC 差只有 +0.0026041667，保持原来的 B04_WITHIN_MEI。它支持那个构造任务中合法携带信息的价值，却没有建立 typed routing 相对已学习 Generic 的实质增量。不能把它当成 Traffic Junction 的学习重复，也不能把 within-MEI 改称等效。

公共生命周期系列削弱了简单的“遇到事件就应该保留／清空／部分保留”通则。 RETAIN−RESET 的三次观察为 −2.0021875、−1.9228125、+2.559375；EVENT−RETAIN 为 +2.804765625、−0.590703125、−5.44609375；HALF−RETAIN 为 +1.56546875、−4.293046875；LEARNED−RETAIN 为 +1.763359375、−1.76953125、−1.215546875。早期有利观察和后来的反转都应保留。这里不是四组可汇总投票的同一干预：原始 public 对只有 32 个最终评价回合，后续系列多为 128；接口和干预不同，RANDOM 也没有做 reset-dose 匹配。它们约束的是这些已训练方案的可靠收益，不是训练后擦除 hidden state 的效果，更不是对所有 retention gate 的否定。

hmasd-pro-question-folr-n-axis-…

BANK 系列需要把缺测、固定策略使用和新学习比较分开。 B01 的 Generic 停在 4253/5000 回合，没有最终终点，所以没有配对结果的正负方向；后来 −5.932421875 的 reference-use 比较只有一个新 Generic fit，BANK 是旧的固定策略，新增 BANK fit 为零。真正 fresh/fresh 的 B02、B03 差值为 −4.830859375、−6.63671875。这两个负结果实质性削弱了该 replacement BANK 包，却不能被写成“四次独立 BANK 学习失败”。

BANK 的含义也不只是“记忆更细了但没用”。源码中它用按观察者—实体组织的 GRU16 替代 Generic64 的整体循环路径，更新与可见性绑定，融合后没有原来的 Generic 跨步循环状态。因此，容量、更新方式和跨实体历史组织一起改变了。即使总存储较多，也不代表包含了 Generic 的全部可学习历史功能。这是比较范围的解释，不是已经查明 BANK 失败的原因。

保留 Generic 的 augmentation 曾给出真正值得重视的正观察，但后续没有兑现其可重复收益。 Discovery 的 A−G 为 +5.29640625；之后前瞻选定的两个重复块为 −5.830625、−0.109921875。原来的 MIXED_BLOCK_PATTERN 必须保留：mixed 指阈值类别不同，不是两个符号相反，也不能事后改成 BOTH_G_ABOVE_MEI。正发现没有消失，但现在不足以支撑继续推广原 A 包。

A−Z 的 −3.069453125 与 Z−G 的 −4.44375 则来自不同的新学习比较。它们可以共同降低对这些增强方式的实践期待，不能相加成跨研究的 A−G 因果估计，也不能构造一条已经识别的 A、Z、G 排名链。

以上累计变化并非“从未成功”，而是：最初足以支持一次探索或重复的希望，在真正付出后续曝光后，没有发展成现在值得使用的稳定理由。 这比删去阳性、只数失败更能解释为什么目前应该停下。

三、最近两个 A01 更新了什么，又没有更新什么

Predictive auxiliary A01 削弱的是这一个预测训练包连接到控制收益的希望。 DETACHED 为 2.69046875，COUPLED 为 −3.8690625，差值 −6.55953125。源码确认，两边都有单独训练的线性预测头；只有 COUPLED 把权重 0.1 的预测损失梯度送入 Generic actor。目标是事实轨迹接下来三步的平均团队奖励，不是未执行动作之间的价值差。

两份摘要记录了相同的共同 probe 输入摘要，uniform-policy probe MSE 从 1.9158295 降到 1.8038883，而 native control 变差。正确更新是：这个标量目标上的小幅预测改善，没有在这次学习实现中转化为控制收益。 它既没有识别 Generic 缺少哪种表示，也没有证明历史冗余；probe 的策略律不是最终共同学习策略的行为律。H-pre 仍未被这一比较测试，不能因 H-aux 的不利实现就默认转向更大的预训练模型。原提案本身也把这些判断列为可分开的备选，而非自动续跑路线。

Cache A01 是目前更直接的实践约束。 六个新 fit 的三个比较为：

训练标签	Generic	Last-sighting cache	Cache−Generic
784101	−0.19578125	−0.42984375	−0.23406250
784201	3.77453125	0.935390625	−2.839140625
784301	1.964140625	−1.224453125	−3.188593750

三个点符号均不利，描述性平均差 −2.087265625。这不是确认性总体伤害结论；第一个小差值也不是等效结论。但对“现在是否采用这个 cache 包”的选择而言，它已经提供了足够明确的不推广理由，不必再花钱把这个有限使用决定升级成普遍定理。

这次比较的价值在于：它保留 Generic64、相同的 103173 个可学习 actor 参数与原生 learner，没有新增 learned bank/fusion，也没有辅助损失。因而，它削弱了一个较具体的实践希望——只要拿掉额外学习流和代理损失，把合法 last sightings 直接显式提供出来，就足以改善这里的有限预算控制。 但它没有识别“旧包就是被额外优化负担拖坏的”，因为它同时换了内容、读取方式和注意力集合。

源码还允许更精确地说明一个未验证的解释：cache 的注意力读取集合从当前 visible 扩展到 active 且 seen；缓存 token 的注意力打分没有显式接入 age，相关元数据在注意力汇聚后才进入 fc2。所以“陈旧 token 与当前 token 竞争读取”是一个具体、可理解的可能性，而不是一句泛泛的“优化困难”。然而，下游网络可能补偿这种差异；目前没有证据说明这一差异解释了三个负终点，更没有证据保证 age-aware 修改能改善 native return。它是源码支持的候选解释，不是已经找到的修复点，也不足以自动重开 cache 调参。

因此，最近证据对四层判断的影响应这样分开：

判断层	当前更新
实际联合策略下是否有重要的历史机会	仍未充分测量。构造任务与条件反例支持可能性，不给出当前策略下可实现收益的大小。
Generic 的表示能力是否足够	未识别。它有合法历史通道，但没有充分性或容量不足的证明。
当前曝光下是否学会了有用组织	多个专门组织包没有兑现原生收益；并未由此识别统一的学习瓶颈。
已测试完整包是否值得其成本	明显向不推广收缩，这是累计证据最有力的实际结论。

近期 18 个 selected fresh fits 属于不同问题，不是一个假设的 18 次重复，更不是方向全生命周期总数。训练实例层面的变化与给定策略下评价回合的噪声也仍须分开；不能靠汇总 episode 或引用某个历史 Generic 高分，制造总体排序或已知 headroom。

hmasd-pro-question-folr-n-axis-…

四、分析性工作保留了机会，但没有给下一次投入开出支票

NOTES 的 7×7 反例值得保留：在指定且已知的队友运动律下，相同合法当前线索、不同较早 sightings，可以对应不同的较优动作；均匀平均焦点动作后的即时奖励均值却可能相同。它说明，一个标量平均奖励预测任务可能丢掉行动区分所需的信息。这是对“预测误差足以裁决历史价值”这一推理的反例，不是对 COUPLED 失败的实证诊断。它没有使用实际学习到的队友律，也不是完全均匀团队 probe、三步目标或 H20 整回合收益。

同样，已保留轨迹中的几何分层计数描述的是策略诱导的观察者时刻，不是可避免碰撞率，不是因果效果，更不是可以逐步相加的 episode headroom。对训练后的 hidden state 做擦除会改变输入状态分布；它不能代替一个从头训练的较少记忆程序，也不能单独判断 Generic 容量是否充足。action_contrast_a01 在启动前已被撤选，实际 checkpoint replay 和新 fits 都为零，代码存在或审查通过不是执行它的科学理由。

由此得到的不是“必须先做好更强诊断”，而是相反：不能让一个能被严谨回答、却不改变有价值选择的小问题，自动排在直接学习比较之前。 有具体理由的完整包比较可以直接做，不欠一个 toy 成功、历史必要性证明或完美机制解释。

五、最强替代：Generic 训练曝光校准；为什么现在仍不选

对 idle 最有力的质疑是：Generic 尚未证明收敛，探索期训练回报有改善，拟合的已记录机器成本也并非不可承受。也许应先判断“继续投入通用学习”是否比“继续设计专门历史模块”更有效，而不是把 5000 回合配方无意中当成不可改变的科学常数。

这个质疑成立为一个备选问题。我认为其最清楚的版本是：

在完全相同的 lawful interface、Generic64、H20、原生学习法和初始到达律下，把一条新训练轨迹从 5000 延长到 10000 回合，是否带来值得额外成本的最终 native return 改善？

它问的是训练投入的使用价值，不是 Generic 的表达能力定理，也不是“历史组织无效”的验证。更长训练同时增加数据、更新和团队共同适应，不能把收益归为一个已隔离的优化原因。

为了不重复支付相同训练前缀，一个较小而有实际判别力的探索版本可以是：两条从头开始、使用两个新且不筛选训练标签的 10000 回合 Generic 轨迹；每条预先固定 5000、10000 两个检查点，训练中不做评价，完成后在隔离的评价进程读取这两个预定检查点。 每个检查点评价 128 个 greedy 回合，评价标签事先固定，不根据结果增加面板或挑选检查点。

按现有“第 32 回合起每回合一次更新”的规律，这个备选实际计数为：

项目	前瞻备选曝光
学习包／曝光条件	一个 Generic 包，5000 与 10000 两个预定时点
新训练轨迹、训练标签、fresh fits	各 2
总训练回合／转移	20000／400000
总优化器更新	2×9969＝19938
检查点／最终评价面板	各 4
总评价回合／转移	512／10240
评价更新、调参 fit、辅助或预训练 fit	均为 0

5000 时点包含在各自 10000 回合轨迹里，不能再加算一次训练，也不能把四个检查点叫作四个独立训练重复。可以比较的是两条训练轨迹各自的预定时间差；相同评价标签仍不构成逐 episode 的反事实世界配对。以上只是一个低精度探索比较，不许诺总体显著性或等效性。计数和复用方式依据现有 collector、完整回合 replay 与 runner 更新路径推导。

这会是新定义的曝光研究，不是延长已经结束的某个 fit，也不是旧单最终检查点实验的原样复现。现有 runner 锁定 A01 的种子和计数，不能当成已有的通用 10000 配置开关。还需为这个新问题处理预定中间保存、评价隔离、正确计数和输出；完整 replay 随回合数增长，额外内存与抽样、保存和评价成本也要算入。不能把这些非拟合工作记为零，也不能由旧 cache 批次的 42.10 分钟推算新的保证完成时间。

它的不同结果有清楚但有限的用途：

**若两个预定时间差都出现有实际意义的 native 改善，**会增强“为这个宿主继续购买 Generic 训练曝光值得考虑”的判断，并影响未来在较大训练预算下选择什么参照。它不会复活 cache，也不证明 augmentation 在更长训练下会改善。

**若没有相称的 native 改善，或结果混杂、不利，**则不支持目前为这一曝光增量付费；仍不能说 Generic 已收敛，或更好的历史组织不可能有效。仅训练回报改善而最终 native 不改善，不算这个使用问题的成功。结果也不会自动生成 20000 回合的下一轮。

我现在仍不选择它，原因是缺少足够直接的决策需求。 目前既没有准备采用的历史候选，需要判断应该给它匹配多少 Generic 训练；也没有必须在两个 Generic 训练成本之间做出的实际使用选择。即使这个备选得到一个清楚的正结果，最直接改变的仍是训练投入，而不是成员变化后应采用哪种历史组织。若结果混杂，我们很可能只是增加了一个“仍未收敛或未区分”的记录。因此，它是比再次包装 cache、更大预测模型或撤选诊断更强的延续选项，却还没有强到值得现在执行。

这个结论不是说“基线未知便永远不值得研究”，也不是要求未来先通过 headroom 检查。一旦出现具体用途或有独立理由的新候选，完全可以把相称的 Generic 曝光直接放进那次学习比较，不必先单独买这一轮。

成本也支持慎重而不是机械拒绝：cache 六 fit 的实际并行批次跨度为 42.10 分钟，但 runner wall 合计 14028.998 秒；单进程最大 RSS 576612 KiB 不是六进程同时峰值，工程、支持和全生命周期成本仍未知。机器时间可承受，不等于任何可回答的小问题都有正的投入价值。

六、为什么“直接转 UAV”或“再做一轮桥接”目前也不是更强选择

本次对目标宿主源代码的检查揭示了一个实质性差别，而不是一个待跑分数：events.py 的事件改变地面站能力；env.py 按配置的 n_uavs 建立 agent 集合，reset 将整个集合置为活动，step 对这个配置集合处理动作，直到窗口结束才清空 agents。reactive_launch 的主路径是待命期间把速度请求置零，并不是本题 Traffic Junction 中的物理成员出生、离开与槽位复用。不能把“有故障、有恢复、有 UAV”直接当成已经实现了同一个 N 轴问题。

这里确实有通用的 Parallel/array adapter，不能说“UAV 没有适配器”。但所读适配器只是通用数组接口及诊断透传；baselines.py 提供的是读取允许集中遥测的非学习诊断控制器，不是本题所需的匹配循环学习参照。这些入口本身没有交付“物理 UAV 成员变化—继续在场观察者的合法历史—对应训练基线”的完整比较。我没有据此声称整个仓库其他路径均无可复用实现，也没有把 FSD 的结果借作 FOLR 的实现或功效证据。

所以，目标宿主路线可能有更高的最终价值，但现在不能诚实地把它报成一个现成、廉价、只是换配置的后续。需要明确的是实际要研究哪一种物理成员变化、何种生命周期和信息权利，以及为什么该问题具有用途；不能仅因为 easy Traffic Junction 的包失败了，就改变任务并称为复制或预算重置。

同理，本次综合已经完成了有明确用途的一段现有证据与源码桥接。再泛读一批文献、再制作一个 toy 或再统计一个几何分层，目前没有已说明的使用决定可供改变。“零 RL fits”不是免费，也不是自动比 idle 更有价值。

七、哪些具体信息会使 idle 值得重看

我不会要求穷尽所有替代解释才允许回来。下面是几类真正能改变选择的信息，它们是重新评估的理由，不是必须依次通过的门槛。

第一类是出现一个具体的目标宿主成员机制与用途。 例如，后续确实需要比较一种明确的飞行器离开、补入或身份复用规则，并且能说明：继续在场者此前合法知道什么，变化后仍可使用什么，这会影响哪一项原生服务选择。那时，值得问的是“针对这个机制的合法历史组织，是否优于同信息通用循环学习”，而不是笼统地“把记忆搬到 UAV”。若实际需要只是地面站能力变化，则应明确它与本题物理成员变化的区别，不能默认两者相同。

第二类是出现具有独立理由、能改变采用选择的直接学习候选或复现需求。 不要求新架构，也不要求先做 toy。关键是能具体说明为什么这个候选对当前暴露的弱点有不同预测，或为什么重复某个原方案的可重复性现在会决定一个真实使用选择。若是针对性修复，应同时预期相关中间变化和整回合 native 改善；中间现象改善而 native 不改善，不支持修复具有使用价值。若只做完整包筛查，则可以主动放弃归因，以 native 收益和成本决定是否继续。仅把“陈旧 token 干扰”改写成“加一个 age gate”，没有增加这类理由。

第三类是 Generic 的训练投入真正成为待决定事项。 当下一项同宿主用途要在 5000 与更长训练之间选择，或新候选的宣称依赖于这一区别时，上述曝光比较就有直接价值。届时无需先证明“当前肯定欠训练”；但应承认其回答的是有限训练投入，不是记忆容量。

新的证据也可能直接推翻当前某个记录。例如，若终点、生命周期处理、信息权限或执行完整性被实质性更正，则依赖它的判断应随之重看。相反，更多总体训练回报、另一个探针 MSE、同一批轨迹中的更多几何比例，若仍不连接采用选择，就不会因为数量增加而自动成为重新投入的理由。

八、一个最终可辩护的贡献需要什么

目前已经可以准确报告一个有边界的事实：在声明的 easy Traffic Junction、合法信息接口与有限训练配方下，多种特定历史组织包没有建立可靠的使用增量，且若干前瞻重复明显削弱了早期希望。 这是有内容的探索结果，但尚不是“成员变化后的合法历史不值得组织”的论文级否定答案。

最终贡献至少应与所作主张对齐。

**若主张是有限预算下某个方法包值得使用，**重点是它对有能力、同信息参照的可重复 native 收益与实际成本，而不是先证明历史在信息论上必要。训练和调参权限要可解释，独立训练实例与评价噪声要分开，正常阶段损失不能被有利的事件后窗口掩盖。可以把主张严格限定在一套 Generic 配方；但不能同时把措辞扩大成已经胜过充分调优的通用循环方法。

**若主张增量来自 N 变化后的历史组织，**则需要能区分成员机制与一般部分可观测性、额外资源或共同适应收益的证据。可以使用与问题相称的前瞻机制对照，但不能只筛选各自策略诱导的 event 时刻，把“事件后看起来更好”直接当成 N 因果效果。若主张未见 N 迁移或 UAV 价值，还需要对应的真正实现、分布和结果；现有五槽位 H20 表格不能承担这些外推。

**若主张是一项负结果或作用边界，**应明确否定的是哪些方法、哪些训练资源和哪些任务条件，并有与“没有有价值增量”这种措辞相称的精度。当前“未建立增量”“不值得继续投入”可以成立；“已经证明没有增量”则强得多。旧的 MEI 类别不因本次综合变成显著性或等效结论；探索结果也不追溯改写为确认样本。

hmasd-pro-question-folr-n-axis-… +2

因此，我不会要求为了“凑一篇完整否定论文”继续扫架构、任务或预算。当前材料最重要的科研价值，是把原先混在一起的判断拆开，并让已失败的实践希望真正失去优先级，而不是用新的机制名称无限保护它们。

九、本次证据可读性与核验边界

上述推理以 ee648d5315febfac86d9c938398e36fb83009757 的题目、当前治理与方法、NOTES、相关原始结果报告、实际模型／环境／学习／runner 路径及运行摘要为依据；没有使用移动 main 替代这些推理输入。对两个近期干预，还核对了所读 cache actor、auxiliary learner 与各自明确执行 revision 的 blob 一致。

需要明确保留的缺口是：本次没有读取本地 final.pt、final-panel.npz、probe-panel.npz，所以没有重新验证张量有限性、optimizer 填充、完整 panel 字节或从 reward 数组重算回报。那些是 NOTES 中 DM 报告的本地验证，不是本次远端重复完成的验证。本次核对了六个 cache 摘要的终点、曝光及参数移动等字段，并读取了一个 cache progress 文件的末尾实际记录；没有逐行复核全部日志。

此外，predictive_aux_a01_coupled_783101/training-updates.jsonl 的范围读取没有返回内容，随后 raw-file 读取也报不可读取，因此该逐更新文件未被本次核验。不能把工具返回空内容解释成仓库文件为空或实验没有更新。 这里对辅助实验的判断依赖已读取的实现、完整结果记录及摘要字段；不作逐更新完整性已经由我独立验证的声明。UAV 检查也仅支持上述入口与机制范围判断，不是整个 UAV 训练系统的完整集成审计。

最终选择仍是 idle；最强替代是有明确用途的 Generic 训练曝光校准，但当前不选。 这保留了 N 轴的开放性，同时不把“仍有未知”误当成继续投入的充分理由。下一次值得购买的证据，应能改变一个明确而有价值的选择；它不必先带来新架构、正结果或完美机制解释。


## DM response 2026-09-19 folr-n-axis-cumulative-synthesis

已通读上节完整答复。Pro 返回 `MATERIAL_DISSENT: no`；其 GitHub 连接没有可用写操作，
因此没有 Pro 答案提交。Jev 确认同一请求已发送并完成；远端分支核对确认答案仍为空、
题目未变后，DM 将完整聊天原文保存于指定 Answer 小节，提交
`0fbccd88f9e7677f705fb071aae8baaebc15bc71`。原文中的文件引用显示标签照录，没有补造链接。
这次交付已通过聊天回收完成，不需要重发问题；私有会话地址留在本地 transport 状态中。

采纳累计解释与当前 idle 建议。早期正观察、后续反转、BANK 未完成运行及固定策略使用的
区别继续保留，旧 MIXED_BLOCK_PATTERN 等冻结类别不改。增强的判断是：在已声明的小宿主、
合法信息与学习曝光下，被测试包缺少继续推广的实际理由。实际联合策略下历史机会的量级、
Generic 表示是否充分、当前曝光是否足够仍未识别；不得把失败包的集合写成 N 轴历史无用、
Generic 已最优或 UAV 已验证的结论。Pro 的同意增加了论证检查，不增加独立训练实例或
确认性证据。既有两个 A01 批次保持结束。

把“Generic 训练曝光校准”保留为本次所讨论选项中的较强备选，但不选中执行。建议中的
两条新 10000 回合轨迹、各自预定 5000/10000 检查点，是 2 个新 fits、20000 总训练回合、
400000 转移、按现有更新规律推导的 19938 次更新，以及 4 个评价面板；检查点不是额外
独立重复，也不是延长旧 fit 的授权。它改变的是是否值得购买更多 Generic 训练的选择，
不能直接裁决 N 变化后的历史组织。现在缺少足够明确的新增信息用途来支付实现、保存、
隔离评价与长训练成本，故不把这个有边界的设计自动转换为下一轮工作。
这里的用途包括科学理解与投入选择；不采纳任何“必须先有待部署方案或正候选才可探索”
的扩大解释，也不把基线曝光校准变成未来学习比较的必经前置门槛。

对答复新增的源码解释作了本地核对，结论保持以下边界：

- `last_sighting_a01/model.py` 的缓存 token 经 `fc1` 和 attention 后，才与含 age 的
  metadata 一起进入 `fc2`；读取掩码从 visible 扩到 active-and-seen。接受这条输入路径
  描述，但“陈旧 token 竞争导致回报下降”仍是结果后提出的猜想，没有中间或 native
  证据把它识别为原因，不据此重开 age gate 调参。
- `envs/uav_service_restoration/events.py` 处理地面站能力；所读 `env.py` 主路径使用配置的
  UAV 集合，reset 后全体入列，reactive launch 在待命期把请求速度置零，窗口结束后才
  清空 agents。`adapter.py` 确有可复用的数组适配器，`baselines.py` 是集中遥测下的非学习
  诊断控制器。这些入口尚不等于 FOLR 所需的物理成员进出、合法历史与匹配循环学习比较。
  接受该范围限定，不把这次入口核对扩大成整个 UAV 训练系统没有可复用实现的断言。

Pro 清楚区分了已读摘要、有限进度读取和无法读取的本地二进制。它未能读取的 coupled
`training-updates.jsonl` 在固定问题提交中确实存在（blob
`d34f683606b77063a21a44421f93dc64fccaf7e4`，1633711 字节）；远端读取失败不是零更新或
缺失实验的证据。既有 DM 本地完整性检查仍是既有检查，不包装成本次 Pro 独立重复验证。
新源码解释已核对，其余源使用限制保留在答复中，不另建核验或诊断任务。

当前选择仍为 FOLR exploring、idle。重新投入可以由具体目标宿主成员机制及用途、有独立
理由且能改变判断的直接学习比较/复现需求、或真正待决定的 Generic 训练投入来支持；
这是本次投入判断可被改变的条件，不是依次过关的流程。一般 within-direction 探索权限
和默认 fit 规则没有改变。本轮按 owner 要求完成证据综合、一次 Jev 发送、完整答复收取
和 DM 读取；没有选定或启动新 fit、确认或迁移研究。
