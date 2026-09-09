Claim: individual internal skill decisions between a fixed team's ten-step boundaries may improve early native UAV performance beyond a fixed-clock learner whose recurrent actor already reacts every step.
Binding MARL structure: (b) temporal abstraction or termination; the question arises from partial actor observations and service geometry changed by jointly adapting UAVs.

# FSD UAV individual-renewal B01 — prospective science card

## 1. Class, authority and state

**B/EXPLORE; one new matched training pair; prospective and unlaunched.**
The complete [P67 Convergence response](pro_packets/20260908_p67_uav_internal_renewal/archive/RESPONSE.md)
at `48b000c08d2a82192de733740230545c97b2a7ab` selects only this scenario1
internal-individual-renewal object family and one I/authentic-D0 comparison.
Its [conformity intake](pro_packets/20260908_p67_uav_internal_renewal/CONVERGENCE_INTAKE.md)
applies A as PRO_FINAL / OWNER_DELEGATED. This is not a recast: P52's ended
supplied-public-mask extension and the ordinary public-cue N6/K2 corridor
family pause remain intact. No Portfolio lifecycle, priority or capacity changes.

Root's response-intake assignment authorizes this exact card and bounded CM
specification. It allocates **no experiment launch**. The code is not yet
implemented or technically accepted, and this preparation does not claim an
accepted UAV execution or register formal UAV entry. The later explicit
allocation is a task-scope boundary, not another scientific gate or owner vote.

Designated authoring checkout/branch:
`C:/Projects/HMASD-worktrees/codex-fsd` / `codex/fsd`.
Starting source is `335425e92cda16677fd1f4181e2c31730887e911`; the relevant
learner/config/environment/E0 source is byte-identical to the fixed Pro input
`de9af8f93d311426f2af069b1a0039765cdeef93`. Bind the eventual accepted code SHA
when implementation returns; do not substitute this doc-only revision for runnable
code. Reuse this checkout and preserve other writers' work.

## 2. Host, intervention and comparator

Use the existing `envs.pettingzoo.scenario1.UAVBaseStationEnv` through
`ParallelToArrayAdapter`, with six fixed UAVs, fifty users, H500, uniform user
reset distribution and free-space channel. All other host defaults, movement,
connection assignment, observation construction and reward remain unchanged.
UAV/user entity sets are fixed within an episode; no join/leave/replacement or
identity reuse. Observation slots may change their visible neighbors without
changing entity membership. Each actor observes the same existing partial local
position/SINR vector at every primitive step. Each coordinator has the same
existing centralized state/observation/held-prefix information permissions.

| Field | I | authentic D0 |
| --- | --- | --- |
| Learner | Ordinary HMASD coordinator, recurrent actor/critic and discriminators | Same learning stack |
| `policy_interruption_mode` | `d2` | `d2` |
| `interruption_cost_c` | .25 | numeric positive infinity |
| `interruption_cost_c_Z` | numeric positive infinity | numeric positive infinity |
| `skill_cap_k_max`, `team_cap_k_Z`, `k` | 10,10,10 | 10,10,10 |
| `interruption_delta`, `age_feature` | 1,`off` | 1,`off` |
| `n_Z`, `n_z` | 6,6 | 6,6 |
| Primitive actor | Current observation, current skill, own persistent GRU memory every step | Same reactive capability |

Preserve ordinary network/loss/normalizer settings, gamma.99, GAE lambda.95,
PPO epochs15, and actual optimizer schedules. A common team **decision time**
does not make the arms' sampled team token equal. Only I can add individual gap
decisions between those common boundaries. A resampling decision may retain the
same token; sampled-decision count and token-switch count are distinct.
Do not force a gap, a token switch or a minimum treatment activity. Zero extra
gaps is a valid activity fact, not a failed experiment.

Concrete hypothesis: own/partner motion changes service geometry → a fixed
UAV owns its held skill and movement → the same current coordinator information
may produce an individual held-logit gap → I can update that skill before the
common team boundary → the same recurrent actor's movement distribution changes
→ native service/quality/altitude reward and own subsequent learning data may
change. The gap is not a measured reward advantage or an established event
detector. D0's reactive actor may already compensate, and interruptions may harm.

No public event bit, corridor lease-renewal actuator, new termination head,
communication, observation-arrival clock or credit algorithm is added. The
existing D2 partial assignment and authentic decision metadata reach the actual
actor and storage. Keep native variable-segment discount/credit and terminal
semantics; differing data, normalizers, segments and optimizer work belong to
the package estimand. Skill renewal does not clear actor memory.

D0 is the directly available same-learning-stack, same-information fixed-clock
null for this marginal question, not a tuned optimum or the strongest possible
UAV algorithm. The [scenario1 baseline record](../../baselines/scenario_1/BASELINE_SET_RESULT_20260904.md)
supplies E0 exposure/integrity and cost facts only. Its frozen returns cannot be
ranked or reused as this comparator. Tuned same-information generic headroom is
**absent**; neither a MAPPO adapter nor a baseline/tuning sweep is a prerequisite.

## 3. Training, RNG, terminal state and endpoint

Prospectively selected **training seed/lane base770503** and
**evaluation seed/lane base780503**. The
[machine preparation record](FSD_UAV_INDIVIDUAL_RENEWAL_B01_PREPARATION_FACTS_20260908.json)
records the zero-occurrence identifier search and exact lists. Each separate
arm process starts Python/NumPy/Torch CPU learning RNG from770503; private
training environment lane j uses770503+j for j0–15. Pair initialization and
exogenous reset schedules, not endogenous action trajectories or RNG consumption.
Every arm owns its model, optimizer, normalizers, recurrence and data.

Run exactly five16×500 learning rollouts per arm:40000 transitions,80 episodes
and five update stages. Each later rollout uses that arm's earlier updates.
Store the actual terminal transition before resetting. On completion, both
the next policy observation **and global state** must come from that lane's
fresh reset; reset only that lane's hidden/skill/timer state. The old E0 loop's
terminal-global-state/fresh-observation pairing is not inherited. With H500,
all lanes terminate at each rollout edge; preserve done-masked bootstrap/credit
semantics without an extra action or skill-sampling call at that edge.

After update five, construct/synchronize only that arm's separate32-lane
evaluator and evaluate once. Evaluation lane e uses780503+e, e0–31, disjoint
from the training seed range. Preserve the training Python/NumPy/Torch CPU RNG
around evaluator construction, synchronization, resets and scoring; within that
scope start evaluation RNG from780503. The evaluator uses the arm's same real
costs/caps/architecture and final active modules, enabled normalizers and eval
mode. Its seed/lane dimensions may differ as specified here. Clear evaluation
buffers and reset its lanes. Evaluation performs no update or normalizer learning
and never mutates the training agent. Use the existing deterministic policy path.

There are two fresh learners and two fresh evaluators, zero old checkpoint loads,
no intermediate evaluation, checkpoint/seed selection, tuning or continuation.
Do not load a corridor learner, replace actual sampled metadata, mix arms'
weights/normalizers or force their endogenous state to agree.

## 4. Primary observable and reporting

For arm p and endpoint e, retain the unmodified adapter episode return U[p,e].
The native team score is `J[p,e] = 6*U[p,e]/500`; each original scalar reward is
native team reward/6. This is reporting arithmetic only: do not scale training
reward, value targets or losses. Native team reward remains
`.7*coverage + .3*quality - altitude_penalty`.

The primary is the32 paired `d[e]=J[I,e]-J[D0,e]`, their mean, sample SD(ddof1)
and conditional SE=sample_SD/sqrt(32). Keep all32 U/J values per arm and all
paired differences. The independent training unit is one matched pair; episode
spread does not estimate uncertainty over training seeds. No resampling service,
confidence threshold or larger endpoint panel is needed for this B reading.

Publish all five training rows with actual transition/episode/update counts,
unscaled native-scalar collection returns, losses, optimizer.step counts for
each existing network, initial parameter norms and initialization-relative
exposure after update one and five. Zero/unused groups or missing instrumentation
are explicit; parameter displacement is not a competence threshold.

Keep actual individual/team sampled decisions, causes, token switches and
segment/optimizer exposure through the existing D2 metrics/tables before buffers
are cleared. Retain counters for training and the endpoint separately; do not
confuse cumulative totals, per-rollout deltas or team timing with token equality.
Report native endpoint coverage, quality and altitude components available from
the existing reward info; they explain the objective, not alternative primary
metrics or permission to select the best component. No full trajectory census.

One complete arm publishes its own scalar/component/count/exposure facts even
if its companion is absent. A complete paired primary requires both original
arms, the specified endpoint IDs/seed law and readable comparison semantics.
Assemble the pair during I's complete invocation after D0; do not move primary
calculation or publication beyond the relevant cap. Missing/damaged companion
output leaves the pair incomplete, without assigning an I−D0 sign.

## 5. MEI, predictions and immutable reading rule

**MEI=.01 absolute native mean team reward per primitive step.** This is one
percentage point on the same weighted native scale including altitude cost;
it is5 team-reward points or5/6 adapter-return points per H500 episode, not one
percentage point of coverage alone or a weak-baseline-relative threshold.

| Complete trustworthy mean I−D0 | Reading and recommendation |
| --- | --- |
| >+.01 | One local early native-UAV package gain; retain as a possible basis for a later separately selected question. No automatic extra seed or successor. |
| inclusive[−.01,+.01] | Small/resolution-limited at this budget; finish the observation without extending it to obtain a clearer sign. Not equivalence or universal no value. |
| <−.01 | Opposite native performance on this pair; it weakens this exact .25 individual-gap configuration at this budget. It does not close every threshold or FSD. |
| Incomplete/damaged primary | Report trustworthy narrower facts and the exact dependency gap; no paired polarity, replacement seed or automatic retry. |

How this will be interpreted: a gain above MEI would make internal individual
renewal worth considering on a host where the actor already reacts; an observation
inside MEI leaves little large marginal signal at this budget; an opposite sign
supports retaining D0 for this comparison. All retain data/credit/optimizer
differences and conditional uncertainty. Any result ends one intake. This is not
stable superiority, timing causality, matched-compute superiority, learned
termination, an optimal clock, H transfer or real-world UAV performance.

**DM prediction on record, before any construction or outcome:** the mean I−D0
will fall inside inclusive±.01; confidence low. The reactive null and earlier
competent-control losses motivate that modest forecast despite the new question's
information value. No calibrated probability or magnitude forecast is claimed.
Owner prediction: **not taken (unattended)**. P67's agreement with the DM's
direction recommendation is not verification of an empirical forecast.

## 6. Work, caps, failure and engineering scope

The machine record preserves zero current scientific exposure and computes
the selected future counts:80000 train transitions/160 train episodes/10 updates;
32000 evaluation steps/64 endpoints;112000 environment steps/672000 agent-step
observations; four model constructions/two training starts/zero checkpoint
loads/6000 learner-evaluator batch control calls. None of these row counts is
an extra independent training seed or an optimizer.step count.

D0 has M=16×500/10=800 joint boundary rows per rollout and4800 individual rows.
I retains800 team rows but can reach8000 joint/48000 individual decision rows.
Actual segment/minibatch/optimizer work is data-dependent. No nested candidate,
trajectory or solver search and no added scientific validation panel.

Complete per-arm caps: **D0 3600s; I 18000s; sum21600s.** The clock covers fresh
admission, interpreter/imports, config/model/optimizer creation, all training,
evaluator construction/sync/score, primary readout and closed-file publication.
No time outside that chain, grace extension, splitting, restart, resume,
borrowing from another arm or spent P47/P52 budget. Future arm order is D0 then I,
each once if explicitly allocated. An adverse or weak valid D0 is still the
comparator; a concrete shared integrity error stops affected dependent work.

The accepted cost scenarios are1617.82s D0 and16178.2s I from old local E0 work
and a deliberately loose tenfold row stress factor. They are not current remote
measurements, verified upper bounds or proof of admission. The machine record
retains the exact formula and mixed140.4s old non-rollout remainder. Missing
current cost stays unknown; no additional timing run, profile or preceding A
is selected. A concrete over-cap implementation projection returns the exact
cost gap without changing the scientific arm, steps or cap.

Future portable execution uses the configured remote-first CPU/four-thread,
FP32 learner and existing environment/return precision; hardware is not an
estimand. Fresh per-invocation memory admission and detached exact committed
source follow AGENTS§§5–7 and the current compute configuration. CM owns the
complete technical invocation/observation/collection under its later assignment;
Root owns integration and any explicit observation adoption.

Stop at completed publication, the complete cap, nonfinite actual action/loss/
parameter/native primary, or a concrete error threatening reward, information,
real updates or primary comparison. Preserve partial output. Intentional numeric
infinite **configuration costs** are not corrupted scientific values. Missing
resource telemetry is `resources_unmeasured`; missing learner instrumentation
limits only its dependent claim under§11.8.7. Weak learning or no extra gap does
not itself justify quarantine. B has no consumption state.

Engineering-scope§4: **none requested**. Reuse existing learners, environment,
metrics and ordinary output; add no guards, schemas, registries, retry/resume
service, new profiler or orchestration layer. Ordinary§5 budgets and focused
verification remain. The complete bounded [CM assignment](FSD_UAV_INDIVIDUAL_RENEWAL_B01_CM_SPEC_20260908.md)
names the affected code and exact original acceptance checks.

## 7. P69 source implementation allocation — 2026-09-08

After the conforming P67 intake/card/spec return at
`b317b1edde00d05a075b5f5ec5a8bb8e18d9cdba`, Root explicitly allocates P69:
implement the exact existing CM specification, run its focused fake-only checks,
obtain independent high-impact review and return accepted source/readiness or
one concrete gap. Reuse the same direction CM and checkout. The source baseline
remains `335425e92cda16677fd1f4181e2c31730887e911`; this allocation changes no
arm, key, comparator, learner/evaluator, primary, resource cap or reading rule.

This is a new **source engineering** allocation only. No scientific staging,
admission, model construction, environment rollout, real-learner smoke, profile,
invocation or retry is allocated. The accepted-source SHA and exact future per-arm
argv will be recorded after technical acceptance. The earlier P67 preparation
and zero-exposure record retain their historical state. Root-action completion
uses the configured wake relay; nested CM/reviewer acceptance remains native.

## 8. P69 source accepted — 2026-09-08

DM accepts implementation `ca36e2f941d6c4d4e996a9bd919378af44ea0e93` after
reading its actual changed source, focused fake checks and independent review.
The [P69 source intake](FSD_UAV_INDIVIDUAL_RENEWAL_B01_P69_SOURCE_INTAKE_20260908.md)
records the applied rule, three owned paths, 33 passing cases plus the corrected
pairing regression, 424-line runner, 19.6496163-second observed check total,
source/counter readback, preserved semantics and exact future per-arm argv.
The read-only baseline source remains unchanged; no scientific fields in this
card are revised. The reviewer-found SHA pairing gate was removed before source
acceptance. Ignored test scratch remains after automatic cleanup rejection,
without affecting the source or future scientific output roots.

This completes P69 source/check/review/readiness only. Real scientific exposure
remains zero, the forecast remains unscored, and no formal UAV-entry registration
is made. Staging, admission and the complete D0/I technical execution still
require their later explicit allocation. Old complete caps, first/final exposure,
unique endpoint, all-outcome reading and no-retry/no-successor boundaries remain.

## 9. P70 full pair execution allocation — 2026-09-08

Root now explicitly allocates **one full D0-then-I technical execution,
observation and collection batch**, after accepting P69 readiness
`8215fd50869cb5306466005cb2853f6da41c03ed`. The exact scientific source is
`ca36e2f941d6c4d4e996a9bd919378af44ea0e93`; the seed/lane laws, CPU4/FP32,
I/authentic-D0 configurations, five rollouts, unique final endpoint, native
primary and all reading branches in §§2–6 remain unchanged. The exact runner
argv and output roots remain those in the P69 source intake §5.

This is a new allocation, not a replay of P69 or an old P47/P52 balance.
Allow **at most one accepted supervisor submission per arm**, D0 first then I
with the named D0 summary. Each arm has its own fresh physical/effective-memory
admission at least 4 GiB before scientific roots or model/learner state. Full
outer caps remain D0 3600s / I 18000s / summed 21600s, including admission,
imports, models, training, unique evaluation and closed-file publication. No
grace, borrowing, retry/resume, extra arm/evaluation, pilot or source fixture.

The same CM remains sole observer and collector through both terminal facts;
accepted-handle notifications do not transfer polling to Root. An adverse/weak
but valid D0 is the actual comparator. Stop affected dependent work for a
concrete shared integrity error; preserve trustworthy own-arm facts and the
incomplete-pair branch if the companion is missing. Do not invent rescue work.
DM owns the all-outcome scientific intake, unchanged prediction, brief and audit.
The [P70 handoff](FSD_UAV_INDIVIDUAL_RENEWAL_B01_P70_EXECUTION_HANDOFF_20260908.md)
records the complete technical batch and source/observation boundaries.

At allocation there is no accepted handle and scientific exposure remains zero.
No owner prediction reply or FSD audit override is present at the clean boundary;
existing empirical forecasts and P67 direction scope remain. No formal UAV-entry
registration or Portfolio lifecycle/priority change is made by this allocation.
