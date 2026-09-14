Claim: one fresh real-learning pair will measure whether learned public-event retention changes final native return against competent event-aware RETAIN on easy Traffic Junction.
Binding MARL structure: agent-count scaling or roster change; physical-trip turnover under partial observation makes the useful lifetime of a survivor's local history uncertain.

# FOLR-LEARNED-RETENTION-B01 — B / EXPLORE

## Authority, question and scope

Portfolio PRO_FINAL / OWNER_DELEGATED at `6c32ade3216c374ecf2f5179b15d559729cd45c9`,
[response §§1,3,9](../../portfolio/pro_packets/20260911_open_directions_program/archive/RESPONSE.md),
selects this fresh implementation and one pair. The [accepted opening](FOLR_LEARNED_RETENTION_CONVERGENCE_INTAKE_20260911.md)
and [candidate](FOLR_LEARNED_RETENTION_CANDIDATE_20260911.md) fix the in-family operation.
This allocation prospectively supersedes the candidate's former zero-runtime allowance;
it neither changes historical results nor reopens the paused exact fixed-half recipe.
No recast, C, UAV entry, lifecycle or priority change is selected.

Question: after 5,000 complete native training episodes per arm, what is the final
128-episode native-return difference of LEARNED_EVENT minus fresh RETAIN? One matched
initialization/training-seed pair is the independent experimental unit. Retain every
outcome; neither a favorable fit nor a mechanism explanation is required for B.

## Operation, comparator and lifetime

The shared scalar is `g = sigmoid(w_x*x + w_h*h_bar + b)`, with 64-wide existing
local recurrent input x and 64-wide lifetime-masked incoming h_bar: 128 weights and
one bias. Initialize weights exactly zero and bias `log(99)`, giving 0.99 at events,
not exact RETAIN. For a true survivor at a completed public birth/departure event,
feed g*h_bar to the ordinary GRU. Otherwise feed h_bar unchanged. No coefficient,
initialization, architecture or seed search is selected.

Physical new trips, including same-step recycled slots, receive zero old hidden
state and zero previous action; inactive/departed slots carry no state. Use the
existing completed-transition continuation/event/own-birth fields. x is the existing
locally masked attention -> fc2 ReLU input, with public event and own birth included.
The actor receives no future event, global critic-only state or additional sensor.
All five slots are storage; a continuing physical trip owns its history.

RETAIN is the existing competent local attention/GRU actor and FlexQMixer learner.
Its GRU already conditions on the same current input/history and public lifecycle
cues. The extra scalar is a same-information inductive bias with 129 extra trainable
coefficients, not a new-information effect or a capacity-matched causal experiment.
Keep environment, native rewards, action selection and partner co-adaptation intact.
CAMA-derived components and this public-event wrapper do not constitute original CAMA.

Acting and complete-episode online/target replay apply the same law with each
network's own parameters and reconstructed hidden states; never store an acting gate
as a replay constant. Preserve all common actor/mixer constructor draws by isolating
the new Linear constructor's RNG. Include the gate in RMSprop, target state copying,
checkpoint save and same-arm load. Preserve episode/minibatch selection, optimizer
settings, target cadence, double Q targets and native final-publication path.

## Prospective identities, learner and endpoints

Fresh unscreened training seed **7809**, evaluation seed **107809**, chosen by advancing
the prior 7808/107808 identities once without sampling results. Both arms use these
bindings with Python/global NumPy/Torch seeded before construction. Native traffic
and replay share global NumPy; epsilon selection consumes Torch draws at greedy and
terminal calls too. Both streams are reset to 107809 before the fixed final panel.
No historical model, partial state, handle or RNG namespace is reused.

Per arm: 5,000 ×20 native training ticks, 4,969 RMSprop steps beginning at episode32;
32 complete episodes per replay sample, one online and one target 21-observation
unroll; target copy every200 episodes, lr0.0005/alpha0.99/eps0.00001, gamma0.99,
gradient clip10. The final checkpoint follows training and precedes exactly128
20-tick greedy final episodes. Five storage slots and the terminal controller pass
remain. Retain training-return sum/mean as changing-policy context, not the primary.

Exposure line (prospective, computed from fixed loops): 2 real learners; 10,000
training episodes; 200,000 training team ticks; 9,938 optimizer calls; 256 final
episodes; 5,120 final ticks; 205,120 total team ticks. Base recurrent work is
2 arms ×4,969 updates ×32 episodes ×21 observations ×5 slots ×2 networks =
66,783,360 replay GRU rows; 2 ×5,128 ×21 ×5 =1,076,880 acting rows. The learned arm
adds a 128-input scalar gate on 33,930,120 forward rows, with online gradients,
plus optimizer work. Mixer, data movement and publication remain actual work.
There are no nested candidates, extra trajectories, pilots or initial-policy panels.

## Primary, MEI, prediction and interpretation

Primary: d_LR = mean(all128 LEARNED_EVENT native returns) − mean(all128 RETAIN
native returns), in unnormalized native episode-return units. Preserve complete
ordered arrays and per-arm conditional SDs. Same evaluation row labels do not make
post-action worlds paired: actions affect traffic/RNG consumption. No episode-wise
paired-world inference or across-training-seed standard error is available from one pair.

**Reading rule, applied verbatim:** `d_LR >= 1: LEARNED_EVENT_ABOVE_MEI; d_LR <= -1:
RETAIN_ABOVE_MEI; otherwise: WITHIN_MEI. An incomplete or untrustworthy primary has
no paired performance polarity; preserve independently trustworthy facts.`

MEI is absolute1 native return, adopted prospectively as a practical scale equal
to one tenth of the native10-unit collision penalty. This is a provisional decision
scale for this host, not a repository threshold or a powered statistical test.
A gap above it would support a bounded package-level gain and discussion of a later
independently selected replication. Inside it, report the signed small difference
and keep RETAIN the economical generic option; it is not equivalence. Opposite sign
would favor RETAIN on this instance, not close all learned-memory mechanisms.
No result branch authorizes an automatic extension, retry or successor.

DM prediction: WITHIN_MEI, low confidence, because the null already has adaptive GRU
gates and the added rule starts near retention; finite optimization may still change
substantially. This is a forecast, not evidence. Owner prediction: not taken
(unattended; no reply at card preparation). Score only against a valid primary.

Headroom: no tuned same-information headroom record on this host. Fresh RETAIN is
the B comparator, not a separately tuned baseline or an upper reference. The two
fixed-half pairs (+1.56546875 and −4.293046875) are different-law historical evidence,
not observations of this gate. They caution against stable or causal memory claims.

## L0 implementation, acceptance and complete budget

Deliverable: smallest implementation of the above law plus this pair and full intake.
Owned checkout `C:/Projects/HMASD-worktrees/codex-vap-folr`, branch `codex/vap-folr`;
starting clean HEAD `fe105b8f653cf890c02b27217b82d34005be4617`. Owned changes are model,
existing transition counter and primary helper under
`experiments/candidates/vap_folr_core/public_lifecycle_b01/`, existing runner
`scripts/run_folr_public_lifecycle_b01.py`, mirrored boundary tests, and FOLR records.
Unchanged learner/environment/attention/mixer/native source are reviewed dependencies.
No shared core or governance write is commissioned; existing directories stay in place.

Acceptance: Evidence Spec §§4,11.3–11.4,11.8 and Engineering Scope §7. Check the changed
recurrence/lifetime and gradients, common constructor RNG and mixer tensors, stepwise
acting versus replay, independent target recomputation/copying, optimizer/checkpoint
inclusion and the dependent primary/publication/identity path. Reuse unchanged accepted
checks. Independent Astra/high read-only review is required for these changed risks.
Focused synthetic checks are engineering exposure, not a native learning pilot. Existing
public_lifecycle test-directory known prior wall is32.4911638s; cumulative limit300s.

Execution is remote-first on wsl_4070, exact committed source in a detached worktree,
CPU FP32, Torch compute/inter-op threads1/1, `/home/wu/.venvs/hmasd/bin/python`.
Linux `resource` publication is required; no local Windows result fallback is declared.
Use the existing agent-task supervisor and a fresh destination memory admission
immediately joined to each runner before its scientific root/model/RNG construction.
Publish exact source and commands before launch; this card does not itself assert
runtime acceptance. Each arm is preselected regardless of the other's valid score.

Fresh ceilings: each complete arm1800s, native sum3600s, all additional invoked
support300s, complete3900s. Native includes admission/startup/imports, initialization,
all learning/replay/final evaluation/checkpoint/publication/exit under one outer clock.
Support includes preparation/check commands, independent review commands, staging,
Monitor observations, collection/reduction/readback, publication/integration and scoped
preservation/cleanup, counted once per invoked command. Unknown terms remain unknown;
a sum of invoked clocks is not elapsed study time. No borrowing between caps.
Historical native1513–1517s is a planning anchor only; gate wall/memory and support
remain unmeasured. No timing pilot or profiler is commissioned. Return a concrete
implementation/cost gap rather than shorten training or final evaluation. Failure or
cap exhaustion preserves actual exposure and stops without retry/replacement.

Engineering Scope Spec §4: this object needs none; no new machinery is added.
DM owns acceptance, exact inputs, launch, collection and intake; Root integrates.
After each accepted handle, direct MONITOR_ADD goes to the live primary configuration's
app thread `01a087e5-2044-7301-abb6-7a1709a98197`, as corrected by Root;
observation dispatch and MONITOR_ADOPTED receipt are distinct.
DM then stops routine polling and returns pending collection. Monitor reports
terminal facts to Root, which resumes this DM. End after one full intake/closeout or
bounded failure; clean owned test scratch and preserve unique evidence before cleanup.

## Scientific grounding

Reuse the source-grounded candidate and accepted opening: current FOUNDATIONS §§2–4,6
and empirical topic distinguish own-history information, finite optimization and the
independent training fit. The verified local CAMA passages (MARL-0409 pp2–3,16–17;
SHA256 `ee9d7b6adc209780a1bb0ad95d73332e9fe4456bfe7ed738926510f70448b20b`) support
recurrent local history and the host's reward scale. They validate neither the public
event extension nor a useful gate. The same-information null and unknown finite
learnability remain explicit. No new literature search or novelty verdict is needed
for implementing this already selected operation.
