# Skill information refresh

## 2026-09-20 — C01 question, evidence and prospective comparison

Owner-selected direction `skill_information_refresh`; Codex DM `/root/dm_info_refresh`,
author checkout `/home/fires/.codex/worktrees/fsd-c/hmasd-wsl`, branch
`codex/skill-information-refresh`, initial source `45945dd7f3fadda6812a311e4e462c21503132c5`.
The owner pause is lifted. A/B/C are present only on the coordinating Root's branch at this
entry: result execution waits for canonical main/lead integration and native admission.
Reading, design and isolated implementation are assigned now. Constitution section 3 as amended
2026-09-20 is loaded and adopted: **no fit allowance**. The stale scientific skill's “up to six”
does not apply. Fits, horizon, wall time and node record cost; they are not an entitlement.

### Working explanation and inherited contrary evidence

The question is when limited teammate information should arrive while behaviourally explicit
skills continue. Fix the skill library, skill-selection rule, termination clock, packet payload,
transport delay and channel access. A received packet may alter a fixed skill's feedback action
without ending its commitment. We do not learn a termination rule, skill content or radio access.

[SchedNet, ICLR 2019](https://arxiv.org/abs/1902.01554) was checked in the
[primary full text](https://arxiv.org/html/1902.01554v1), sections 3.1–3.3, 4 and appendix D.
Its local observation generates a message and priority; a weight-based Top(k)/Softmax(k)
scheduler selects senders, then actors consume scheduled messages. A global critic is used
only in training. Encoding, action selection and scheduling are jointly trained. Its RR and
full-communication comparisons support that package in predator-prey/navigation; they do not
test fixed-skill refresh timing against a decision-aware rule. Appendix D describes CSMA
approximations using backoff/holding times. This is an analogy for legal local scheduling,
not evidence that a priority/request channel is free or that our timing problem is novel.

The closest local contrary result is archived
[CADC B01](../contention_aware_decentralized_communication/CADC_B01_RESULT.md), source
`22e009c9387f2507aab6ebab4555d92e27f5070e`. Its one trained LEARNED/RR pair completed
512 training and 32 final episodes per arm. LEARNED minus RR was -0.013354921301 net service
and -0.012099183996 physical service; 10 of 32 final worlds were positive. LEARNED had 16,744
collided attempts, RR zero. These are endogenous package facts, not a collision diagnosis;
one pair does not establish stable inferiority or unlearnability. The archived channel/model/
study were read: local seven-number payloads, delayed shared collision channel, a learned send
head and motion learner versus fixed RR with learned motion. We carry forward its adverse
evidence and avoid inferring that another send head should help.

Current judgments: useful freshness is plausible **opportunity**, not demonstrated value;
legal local observations plus public commitments may **represent** urgency, but this remains
to be checked; finite **learnability** and complete-package value over an informed simple rule
are unresolved. The main simple explanation is that observable state changes, age and known
action times already tell us enough. A new collision-free communication object cannot repair
or relabel the old CADC result. No current HMASD learned-skill or UAV claim is made.

### C01: fixed crossing skills, fixed channel, learned packet timing

Use an independent, small two-robot service host. Each robot repeatedly executes a fixed
closed-loop “deliver through the shared crossing” skill. Agent 0 has a 12-tick commitment,
agent 1 a 16-tick commitment; both start at time 0. At each fixed boundary a new job starts
at an independently sampled approach distance 1–7. Every approach tick independently advances
with probability .75; the realized delay is local. The immutable feedback controller approaches,
then waits or enters using its own state and its cached peer packet. Crossing takes two ticks.
The lower-priority robot yields to a predicted near peer; either robot yields to predicted peer
occupancy. Simultaneous physical occupancy fails both jobs. A job still unfinished at its fixed
boundary expires. A successful crossing completes one job. These are task dynamics, not radio
collisions. H=96 ends on both commitment boundaries, so no extra final partial job is started.

The packet contains four uint8 fields: sender stage, approach distance, remaining crossing
ticks and remaining commitment. Timestamp (uint16) and sender (uint8) make seven bytes total.
Packets are copied at send time and delivered at the next tick before control; receiver uses
the most recent delivered packet only. A fixed projection subtracts floor(.75 * age) from
cached approach distance; it expires a packet at the sender's next known skill boundary and
projects a completed crossing as done. Missing/expired peer information is explicitly unknown,
not an invented current peer state. Fixed controllers never infer private values from silence.

Access is fixed TDMA: at tick t only sender t mod 2 may send. Each sender must use exactly one
packet in each 8-tick communication frame; if unused it sends in its final eligible slot.
Thus there are 24 packets/168 payload-and-header bytes per episode in every arm. The visible
send/idle outcome is itself a bounded timing channel: 96 one-bit slot outcomes per episode,
equal available opportunities across arms. No request or priority message exists. Sender
scheduling may read its own current state, its own previously sent snapshot and age, the last
delivered peer snapshot, and public clock/budget/identity. It cannot read the current hidden
peer state. The controller consumes payload and age, never a side-channel interpretation of
send/idle. Training reward is the shared job outcome and is not an execution observation.

The direct comparison is one shared local PPO scheduling policy (`LEARNED`) versus a selected
age/observable-change rule (`AGE_CHANGE`, primary), plus `PRE_DECISION` and `POLL` references.
Everything except packet timing is identical. No learned physical policy or message encoder.

- `AGE_CHANGE`: send on an observable change when either the sender or its cached peer is near
  the crossing, on the last eligible slot before the peer's skill decision, or at an age limit.
  Select one pair from distance-change thresholds {1,2,4} and age limits {2,4,6} using 256
  development episodes, before final evaluation; fixed lexical tie-breaking. Unknown peer
  status counts as possibly actionable. This includes both immediate event and freshness
  rules; the primary is selected by service, not by final scores.
- `PRE_DECISION`: in each frame send in the latest eligible slot strictly before a peer skill
  decision within that frame/delivery boundary; otherwise use the frame's last eligible slot.
  Delayed arrival, rather than send time alone, determines whether a refresh precedes a decision.
- `POLL`: first eligible slot in every frame. This is descriptive, not the primary null.
- `LEARNED`: a small feed-forward shared actor/value model; actor and critic receive the same
  legal local features. Forced or budget-masked actions have no policy-gradient/entropy term.
  Shared reward trains scheduling only. Final policy uses p(send) >= .5, with the identical
  forced-last-slot rule. No recurrent hidden state or centralized execution input.

Prediction: LEARNED should allocate more transmissions near a peer's *actionable crossing*
within a commitment, conditional on local change/age, rather than only near skill boundaries.
Its intermediate consequence should be fewer cached-state gate decisions disagreeing with the
same fixed controller given the actual peer snapshot at that same encountered state, and fewer
physical conflicts/wasted waits. The full-state comparison is an offline one-step diagnostic,
never an actor feature, reward, extra training target or a counterfactual trajectory. Its native
consequence should be higher completed-job fraction at the identical packet count than selected
AGE_CHANGE. Mean freshness alone is not success. Completion and conflict readings stay beside
the diagnostic; a disagreement reduction alone does not establish practical value.

If AGE_CHANGE matches/exceeds the trained policy, the finite learned timing package loses value
in this host; it need not show that timely information is useless. If the learned policy merely
reproduces PRE_DECISION, the proposed within-skill allocation increment is unsupported. If it
changes timing without reducing action disagreement or improving service, the urgency explanation
weakens. A native gain without the predicted intermediate change is a package result with an
unresolved explanation. Technical failure or no learner movement is not a scientific negative.

This small model retains mutually coupled physical outcomes, decentralized hidden progress,
stale peer state, asynchronous commitments and delayed packets. It omits learned skills,
teammate policy drift, N variation, realistic UAV dynamics/radio contention and learned motion.
It is the first direct experiment for this new question, not a compulsory toy-pass gate or a
SchedNet reproduction. A favorable result would justify considering a harder host, not prove
native UAV or current HMASD benefit. Literature novelty remains unreviewed.

### Prospective exposure, outputs and L0

Exploration only, no confirmation claim. Master seed 73141; one started fit for LEARNED at
4,096 training episodes x 96 ticks (393,216 team transitions), CPU float32, one native thread,
32 independent environments per rollout, four PPO epochs per 3,072-transition rollout,
512 optimizer calls. PPO uses gamma .99, GAE .95, clipping .2, entropy .01, value weight .5,
Adam 3e-4, gradient norm .5; hidden layers 32/32. No training, horizon or hyperparameter search
after scores. Final checkpoint only. Initial policy has a separate 64-episode development
evaluation, zero updates. Heuristic selection is nine x 256 x 96 = 221,184 team transitions,
zero fits/updates, development worlds. Four final arms x 256 x 96 = 98,304 transitions on a
disjoint common exogenous panel (movement uniforms indexed by world/tick/agent regardless of
actions). Those 256 episodes are conditional evaluation worlds, not training replicates.
Total planned work is 718,848 team transitions, one fit, 512 optimizer calls. Actual choice
counts may differ by policy; report them. Node planned: local_linux CPU, appropriate for this
small independent host; Root coordinates actual admission. No GPU or wsl_4070 slot requested.
Wall/RSS remain unmeasured before execution; no inherited CADC/UCOPE deadline or allowance.

Primary endpoint: final completed jobs / jobs started per episode, LEARNED minus the
development-selected AGE_CHANGE, all 256 per-world differences retained. No significance,
equivalence, stable ranking or learning effect claim from n=1. Report PRE_DECISION/POLL,
physical conflicts, waits, missing/expired packets, message age, timing histograms, gate
disagreement and actual packets/bytes. Train/eval RNG streams are disjoint. Retain config,
launch SHA, admission/exit evidence, per-episode and per-update streams, initial/final model,
learner displacement, all counts and summary/status; incomplete/failed outputs remain.

L0 deliverable: a disposable C01 host, fixed skills/channel, scheduler learner/comparators and
admitted CLI with focused tests. Owned edits: `experiments/candidates/skill_information_refresh/`,
mirrored `tests/experiments/candidates/skill_information_refresh/`, this notebook and
`scripts/run_sir_c01.py`. Root and other DMs are simultaneous writers in their own checkouts;
no writes to their indexes, notebooks or scientific code. Preserve the information boundary,
copy-at-send/next-tick-delivery order, fixed clocks, exact communication count, masks, paired
exogenous world law and no-score-before-admission. Test these invariants and the PPO masking/
movement/output path using small fixture inputs under pytest-owned `temp/`; obtain independent
read-only review because host/learner/evaluation semantics are consequential. DM implements
and accepts. Stop dependent actions for a real semantics/resource/writer conflict; no result
launch until Root reports canonical integration and the native guard passes.

## 2026-09-20 — prospective comparator correction before implementation/results

Independent ResearchCritic `/root/dm_info_refresh/c01_design_critic` identified a concrete flaw
in the proposed age limits: with one packet per 8-tick frame, an unconditional maximum age
of 2/4/6 ticks drives every variant toward its first eligible slot after a first-slot send.
That would make the nominal event/decision-aware primary largely POLL. I adopt the objection.
Replace age limits by **{8,12,disabled}**, crossed with the same distance deltas {1,2,4}; there
are still nine development variants and no changed fit/transition count. Age means ticks since
the sender's last transmitted snapshot. With no prior transmission, finite age limits fire;
the disabled limit does not. A local stage change or sufficient distance change triggers only
when the sender or cached peer is near/possibly actionable; the decision and forced-last-slot
rules remain. A focused lawful-history test must show a nonpolling variant can preserve its
token past the first slot. No score was inspected or training started before this correction.

The Critic's remaining alternative is retained: the commensurate 8/12/16 public clocks permit
a phase-specific periodic schedule to improve both service and gate-disagreement without
using realized private progress. The present first comparison is therefore a **conditional
timing-package comparison**, not component attribution to receiver actionability. I keep the
one-fit exploration because it can change whether this finite package is useful beyond the
informed rule; I do not add a clock-only learner now. Final legal-feature/request/send traces
and agent/public-clock timing counts are retained for reading that alternative. A favorable
package score alone will not establish dependence on private change, and the full-snapshot
one-step diagnostic is neither a return upper bound nor a causal mediation estimate. The
Critic reported `MATERIAL_DISSENT: yes` for the original, now corrected baseline defect;
no further material design objection to this limited exploration. DM accepts the correction
and the narrower interpretation. This is advisory reasoning, not empirical evidence.

## 2026-09-20 — C01 implementation and pre-result checks

DM directly implemented `experiments/candidates/skill_information_refresh/c01/{host,learner,study}.py`
and `scripts/run_sir_c01.py` under the L0 above. The CLI validates arguments, consumes native
admission and checks launch SHA before loading the scientific code or creating outputs.
No shared core, CADC, Claude FSD or team-termination code was edited.

Focused check command: `/home/fires/.venvs/hmasd-linux-cpu/bin/python -m pytest -q
tests/experiments/candidates/skill_information_refresh/c01`; **14 passed in 2.46 s**.
It covers legal-observation invariance to unsent peer state, copy-at-send/next-tick delivery,
exact packet accounting, fixed skill clocks, physical crossing/priority, packet expiry,
recipient-clock refresh timing, the corrected nonpolling heuristic, action-independent world
RNG, terminal GAE, masked actor/value separation, actual optimizer movement, complete artifact
counts/readback, direct-CLI admission refusal and preservation of a partial optimizer failure.
Tests own temporary outputs under pytest `temp/` and report no scientific comparison scores.
The small fixture optimizer updates are engineering checks, not execution of the prospective
4,096-episode C01 study. An initial pytest collection error used its reserved parameter name
`request`; renamed to `should_send`, then the suite passed. No result attempt or retry occurred.

The implementation keeps final legal-feature/request/send arrays as well as per-world and
per-update streams; these allow the public-clock alternative to be read without inventing
missing observations later. Actual private peer state is used only by physics and the declared
offline one-step disagreement/timing diagnostics. Technical completion is not a scientific
result: the hypothesis, representation and finite learnability judgments remain unresolved.
Independent engineering review is next; result launch still waits for canonical active/lead
integration plus native admission, owned by Root for the shared-index coordination.

## 2026-09-20 — pre-run repair: a real fixed skill decision at the boundary

Engineering Reviewer `/root/dm_info_refresh/c01_engineering_review` independently inspected
`45945dd7f..a3c4f32b3`, reran 14 focused checks (2.33 s), and returned no material engineering
finding. Two existing admission-contract checks also passed (0.13 s). I accept that engineering
reading, but caught a scientific scope gap during the final review: the original boundary only
started a new exogenous job. No message-conditioned skill choice occurred there, so its
`PRE_DECISION` was only a pre-job-boundary clock rule. The Critic verified that fact in the
actual reset/gate code. The owner's requirement includes a skill-decision refresh reference;
disclosure alone would not make that contrast meaningful.

Before any result execution, retain the C01 question, arms, seeds, horizon and cost, and make
one targeted host repair. There are now **two immutable closed-loop route skills**: SHARED,
the existing two-tick shared crossing, and BYPASS, a four-tick independent detour after the
same local approach. Only SHARED occupancy can conflict. Skills are selected solely at the
existing 12/16 boundaries and cannot switch mid-commitment. A fixed, untrained selector chooses
BYPASS when the last legally delivered, still-valid peer packet predicts a SHARED crossing
within three ticks of our expected arrival, and expected approach plus detour fits the
remaining commitment with one tick of slack; otherwise SHARED. Arrival prediction is distance
divided by .75 (zero for a crossing peer); a predicted peer commitment ending first does not
establish a current conflict. Invalid/expired peer packets select SHARED. The selector uses
the new local job distance and cached peer only, not the peer's unsent new job or skill.

Add the sender's committed route as one uint8 in the fixed payload for **all** arms: five
uint8 fields plus timestamp/sender header = eight bytes, hence 192 bytes per 96-tick episode.
Actor features grow from 22 to 24 by own route and valid cached-peer route; remaining crossing
ticks are scaled by four. Packet access, latency, 24-packet quota, timing-bit accounting and
all learner/evaluator exposure stay unchanged. Gate feedback respects the committed route;
a BYPASS robot does not block or yield for the shared crossing. Count chosen routes and
skill choices using valid peer information. This creates a meaningful decision-before-refresh
reference while retaining the within-skill timing question; it does not learn or adapt
termination, message coding, physical control or channel access.

The pre-result prediction now has two possible information-use sites: the fixed route choice
at a boundary and gate feedback within the selected SHARED skill. Primary service remains
completed-job fraction versus selected AGE_CHANGE; PRE_DECISION now serves actual route
choices. A service difference may involve both sites, so gate-disagreement alone cannot
attribute it to the latter. Keep route counts, clock-conditioned sends and legal traces.
All claims remain conditional small-host package readings. This repairs an unrun design,
not a score-driven extension, renamed failed idea or retroactive change to accepted results.
The changed host/features will receive focused checks and an independent review of the delta.

The Critic's focused follow-up agrees that this repair is required by the owner's exact
skill-decision reference wording and is a small, scope-respecting change; `MATERIAL_DISSENT:
yes` records the original semantic mismatch. Two controlled traces now exercise a packet
arriving before and changing the boundary route choice, and a later packet changing within-
skill feedback with the route unchanged. Final traces also retain the factual two-agent
state and delivered caches/timestamps for offline auditing of both decision sites. Those
diagnostic arrays never enter either network; scheduler observations remain legal and local.
After the repair, the same focused pytest command reports **19 passed in 2.48 s** and
`git diff --check` passes. No C01 result batch has started and no selection/final scores have
been inspected; the original engineering review does not substitute for review of this delta.

## 2026-09-20 — final C01 review and execution preparation

The Reviewer read `a3c4f32b3..ef52fd155`, confirmed the new skill/packet/feature law, and ran
19 checks (2.76 s). It found one P2 diagnostic issue: the old `send_peer_actionable` counter
also counted receivers already executing BYPASS, which ignores within-skill peer feedback.
I accept and repair it before running. The old route-agnostic quantity is now honestly named
`send_peer_near_crossing`; an additional `send_peer_shared_near_gate` counts only a SHARED
receiver approaching at distance <=1 with at least two commitment ticks left. Both are
encountered-state proximity counts, not proof of causal actionability. The bypass fixture now
sends at tick 2 and checks that only the route-agnostic count increments. No scheduling,
physics, learner or primary endpoint is changed by this repair.

Root reports owner-authorized registration on canonical main `b254ed1ea` and synchronization
of the actual control checkout: pause lifted, `skill_information_refresh` lead `Codex DM`.
This removes the shared-index dependency. After accepting the repaired review, publish the
exact inputs and execute the already specified C01 batch via the local_linux native launcher;
fresh admission and memory checks still apply. No extra approval, score-driven extension,
fit allowance, or inherited deadline is introduced.
The requested repair passes **19 checks in 3.12 s** and the whitespace check. I read both
engineering reviews and the scientific criticism in full, accept the implementation with
this verified diagnostic repair, and select the declared single-fit C01 execution. Source
identity, native process and output location will be retained by its launch manifest; test
success is not scientific support for the timing hypothesis.

## 2026-09-20 — C01 accepted execution

Native admission accepted the frozen C01 request at 13:50:52 UTC after checking current
canonical direction/lead and fresh local-node memory. Its
[launch manifest](../../../../runs/skill_information_refresh/c01_s73141_20260920/launch-manifest.json)
retains source, invocation, process identity and output paths; the sibling admission-preflight
and later process-exit records retain the native checks. DM observes this same operation
directly; no observer transfer, duplicate invocation or expanded batch. Training and collection
are in progress at this entry. Acceptance is technical, not a read scientific result.

## 2026-09-20 — C01 read: trained execution recovers the simple clock

The accepted operation exited zero. I read the runner
[summary](../../../../runs/skill_information_refresh/c01_s73141_20260920/summary.json), complete
episode/update streams, selected baseline and final traces. All declared exposure completed:
4,096 training episodes/393,216 transitions, 512 optimizer steps, 64 initial episodes,
2,304 rule-selection episodes and 1,024 final episodes; 718,848 total team transitions.
Every final arm has all 256 world IDs, 96 ticks, 14 jobs and exactly 24 packets/192 bytes per
world. Evaluation updates are zero. Actor displacement is 2.38828349, critic 4.15770912,
all 3,778 parameters finite. This is a real learning attempt, not nonactivation. Cost: one
started fit, local_linux; runner wall 19.738879 s (training 12.728538 s), approximately 21.49 s
from native acceptance to child exit including scientific import/start overhead. Peak RSS
306,756 KiB is the single scientific child; user/system CPU 19.735485/1.762812 s. Queue/control
publication time is not included in that process wall. No GPU usage or speed claim.

| Final 256-world mean | LEARNED | Selected AGE_CHANGE | PRE_DECISION | POLL |
| --- | ---: | ---: | ---: | ---: |
| Completed-job fraction | .944196429 | .944196429 | .899553571 | .944196429 |
| Physical conflicts/episode | .1484375 | .1484375 | .43359375 | .1484375 |
| Wait ticks/episode | 6.80859375 | 6.80859375 | 1.82421875 | 6.80859375 |
| Gate disagreement/opportunity | .255621757 | .255621757 | .136212625 | .255621757 |
| BYPASS choices/episode | 2.21875 | 2.21875 | 2.453125 | 2.21875 |

The development winner was `delta1_age8` (.950613839); every age-8 variant tied it.
`delta1_age12` and `delta1_ageoff` scored .949776786; other variants ranged .938616071–.944754464.
Thus nonpolling variants were actually evaluated, not silently omitted. Final LEARNED sends
in the first eligible slot of every frame, just as the selected rule and POLL do. Direct
array comparison finds **all final sent masks, choice masks, legal features, physical states,
delivered caches/timestamps and world IDs identical** across those three arms. All 256 primary
LEARNED-minus-AGE_CHANGE differences are exactly zero. This is observed execution identity on
this panel, not statistical equivalence or a population zero effect. The trained greedy policy
has no executed state-sensitive timing increment here.

Relative to PRE_DECISION the conditional mean difference is +.044642857, with 89 positive,
13 negative and 154 tied worlds. That contrast is shared equally by the no-learning POLL rule;
it is not a learned communication advantage. Its larger gate disagreement and extra waiting
alongside fewer conflicts/higher service contradict a monotone “closer to full-snapshot gate
decisions means better return” reading. The diagnostic compares different encountered states
and is not an upper bound or mediator; I will not optimize that proxy as if it were the task.
The training curve rises descriptively (successive 512-episode means .896066, .909877, .918945,
.925502, .929269, .928571, .935965, .924386), but final-world gains cannot be inferred from
the initial .869420 mean on a different 64-world panel.

Working update: **complete-package incremental value is weakened**—the trained policy pays
training cost to reproduce a no-learning rule. The predicted state-sensitive redistribution
and improvement over the informed primary did not occur. **Task opportunity** for timing
matters conditionally (clock policies differ), but useful private-context opportunity beyond
POLL remains unresolved. **Representation** has a verified lawful action path; that does not
show the policy used it beyond a public clock. **Finite learning** is active but its final
readout learns a simple schedule; one initialization does not establish inevitable collapse.
The pre-recorded public-clock alternative is strengthened. CADC's adverse result remains an
independent constraint on its different package, unchanged by these numbers. No UAV, current
HMASD skill-content, adaptive-termination, novelty or population claim follows.

## 2026-09-20 — C02 prospective recurrence check, same idea and unchanged code

Select a small independent repetition to change the unresolved *recurrence* judgment, not to
rescue the mean or search a new architecture. C01's greedy execution exactly matching POLL is
stronger than an ordinary small score difference; whether another initialization/world history
does the same changes whether another learned refinement in this host is worth considering.
The measured complete path is about 22 s per attempt, making two independent histories a
proportionate direct observation. C01 remains fully read with its zero primary; this is a new
prospective batch, not an extension of its 256-world panel or a renamed failed idea.

Run the unchanged accepted C01 program at master seeds **73142 and 73143**, sequentially on
local_linux. Two new started fits planned. Each retains 4,096 x 96 training transitions,
512 optimizer calls, 64 initial, nine x 256 development-rule and four x 256 final episodes,
the same final greedy extraction, route/channel law and primary LEARNED-minus-selected-AGE_CHANGE.
Total new exposure: 1,437,696 team transitions and 1,024 optimizer calls; no tuning changes,
new arms, checkpoint selection, stochastic-policy rescue evaluation or further seeds selected
after scores. Approximate process occupancy 45 s follows C01, not a hard deadline or entitlement.
Each seed gets fresh model/action/environment streams and its own disjoint development/final
panels. Within a seed all final arms share the declared exogenous world addresses; across seeds
there are independent training histories. Fixed rules still have zero learning updates.

Prediction being checked: the finite learner again executes the simple first-slot clock and
therefore offers no increment over a competent selected rule. Read each seed's actual sends,
state/return differences and learner movement, then report all three exploratory histories
including C01; do not pool their evaluation worlds as extra training n. If a new history
executes context-sensitive timing with useful return, the recurrence explanation weakens and
the saved lawful traces can discriminate it from a different fixed periodic schedule. If the
same simple solution recurs, retain the simple rule and stop spending fits on this unchanged
learned package; a successor would need a different, explicit information-value question,
not merely more training or a new initialization. These are exploratory readings, not a
confirmation batch or a prewritten population-equivalence test.

## 2026-09-20 — C02 accepted, collected and read: contextual timing, negligible observed net gain

The two prospectively fixed C02 histories ran sequentially at published source
`118d8bc391c0e9acafc054ed16a8899ccd795de9`. Native local_linux admission checked canonical
main `b254ed1ea86cf8c39d925d87ded4fee368c5e0a1`, the current lead/pause and actual-node memory.
The [73142 manifest](../../../../runs/skill_information_refresh/c02_s73142_20260920/launch-manifest.json)
records acceptance at 13:58:12.359732 UTC, runner 2283929 and supervisor 2283928; the
[73143 manifest](../../../../runs/skill_information_refresh/c02_s73143_20260920/launch-manifest.json)
records acceptance at 13:59:09.109857 UTC, runner 2285644 and supervisor 2285643. Both original
operations exited zero with valid process-exit witnesses and consistent native records.
The DM retained observation of those handles; neither operation was duplicated or rebound.
Both terminal states preceded this whole-batch outcome reading.

I read both summaries, complete episode/update streams, rule selection and saved final traces.
Each completed the declared 4,096 training episodes/393,216 team transitions, 512 optimizer
calls, 64 initial episodes, 2,304 selection episodes and 1,024 final episodes: 718,848 total
team transitions per history. Each has 7,488 episode rows and 512 finite update rows, with
zero evaluation updates. All final arms retain 256 unique matched world IDs, 96 ticks,
14 job opportunities and exactly one eight-byte packet per sender per eight-tick frame:
24 packets/192 bytes each world. All four trace sets are finite. The initial/final checkpoints
agree on source/seed and all 3,778 final parameters are finite. Actor displacements are
2.00846004/1.72397602; critic displacements 3.86843610/3.92253280.

Cost is **two new started fits**, not a quota allocation. Runner wall is 15.015690/14.676739 s
(training 9.456738/9.354606 s); acceptance-to-child-exit 16.418754/16.108145 s. Peak RSS is
306,344/306,580 KiB per scientific child, not aggregate node occupancy. User/system CPU is
15.207562/1.679928 and 15.151713/1.444166 s. These exclude the earlier queue/control/publication
path; the two child processes were sequential and used no GPU. C01 plus C02 now represent
**three exploratory training histories**, 12,288 training episodes/1,179,648 training team
transitions and 2,156,544 total team transitions. The 768 final worlds are not training n=768.

| Final mean / contrast | 73142 | 73143 |
| --- | ---: | ---: |
| LEARNED completed-job fraction | .949776786 | .946986607 |
| Selected AGE_CHANGE = POLL | .949218750 | .946707589 |
| PRE_DECISION | .908482143 | .907087054 |
| Primary LEARNED minus selected AGE_CHANGE | +.000558036 | +.000279018 |
| Positive / negative / tied final worlds | 6 / 10 / 240 | 8 / 13 / 235 |
| Net additional completed jobs / 3,584 opportunities | +2 | +1 |
| LEARNED versus POLL total conflict difference | -6 | -8 |
| LEARNED versus POLL total wait-tick difference | +320 | +489 |
| LEARNED versus POLL total BYPASS-choice difference | +154 | +181 |

The independent development panels both selected `delta1_age8`, with selection means
.950055804/.948939732. All age-8 variants tied; the six nonpolling variants were actually
evaluated and ranged .933314732–.946149554 and .934430804–.946986607 respectively. On each
final panel the selected AGE_CHANGE and POLL have identical executed sends, choice masks,
legal features, physical state, delivered caches/timestamps and world IDs. Their raw
requests sometimes differ after a frame's packet has already been spent; those requests
have no effect. Execution identity is not identity of unused network/rule outputs.

**The recurrence prediction failed.** Both new learned policies execute a different send
schedule from POLL in every final world. There are 245/235 distinct full schedules and
31/37 absolute time slots at which some worlds send and others do not, although clocks,
identity and remaining horizon agree. This cannot be described as merely another fixed
periodic clock. At tick 8, for example, all 256 worlds still have the same prior first-frame
schedule and a legal choice. Seed 73142 sends for all 58 APPROACH and 33 CROSSING senders but
for none of the 165 DONE senders; seed 73143 sends for all 73 APPROACH senders and none of
the 14 CROSSING or 169 DONE senders. This is observed lawful contextual execution, not proof
that a particular feature is individually causal or that receiver actionability was learned.
Packet counts, payload, skill selector/controller, terminal law and latency remain fixed.

The small aggregate primary masks opposing native outcomes, not a broad per-world advantage.
For 73142, six worlds have one fewer physical conflict and two additional completed jobs
each; the other 250 worlds contribute ten fewer completed jobs in total. For 73143, eight
worlds have one fewer conflict and 15 additional completions in total; the other 248 worlds
contribute 14 fewer completions. All worlds with fewer completions have unchanged conflict
count and extra waiting. These are paired factual outcome associations after policies change
their histories, not an identified decomposition into conflict, route and waiting mediators.
In particular, more BYPASS decisions or better conflict counts cannot be credited as net
learned value while omitting the completion losses. Higher gate disagreement accompanies
these learned policies too; the diagnostic remains unsuitable as a monotone native target.

I read the Critic's complete post-C01 answer and accept two interpretation corrections:
C02 changes initialization, action samples and environments together, so it tests independent
*training histories*, not initialization in isolation; execution recurrence against POLL
and the primary against independently selected AGE_CHANGE must be read separately. Here the
two simple arms happen to execute identically, but that was not guaranteed by the protocol.
The Critic also verifies that initial negative actor logits are guaranteed by bounded tanh,
final-row norm .01 and bias -1.1 (maximum logit <= -1.1 + .01 sqrt(32) < 0). All 64 initial
episodes per history indeed send only through the 24 forced slots. The learned behavioral
change is real. Different initial evaluation worlds still preclude claiming a same-panel
return gain from their means. No adviser agreement is independent empirical evidence.

Working update: retract the simple-clock-collapse account as a general explanation for this
finite learner. **Representation and finite learning** can produce legal context-dependent
timing on this host, although C01 used only the simple clock. **Task opportunity** beyond a
public clock is not established merely by variable schedules; useful conditional information
must ultimately improve native completions. **Complete-package value** remains unsupported:
observed increments are 0, +2 and +1 completions over three separate 3,584-opportunity panels,
with training cost and opposing losses. This is neither population equivalence nor a proof
of no worthwhile timing policy. The CADC adverse evidence, simple-baseline requirement and
small fixed-skill host ceiling remain in force; nothing here establishes current HMASD
learned-skill effectiveness, repaired CADC, UAV performance or novelty.

## 2026-09-20 — C02 saved-trace critic: delayed release, not demonstrated useful freshness

The Critic independently read the C02 saved arrays and classified the first native decision
difference while paired physical histories still match. For 73142/73143 it finds 177/177
within-skill gate-first worlds, 48/60 boundary-route-first worlds, and 31/19 worlds with no
recorded physical difference. All 354 gate-first cases have robot 0 actually DONE, a still-
valid LEARNED cache projected as SHARED APPROACH at distance zero, and POLL's cache correctly
DONE. Robot 1 waits under LEARNED but enters under POLL and under the factual full-snapshot
gate. The result is a read of saved states through the unchanged `project`/`gate` functions,
not a new simulated trajectory or fit. It locates a real information-to-action entry site;
it does not isolate the native return effect of that wait from subsequent coupled histories.
The Critic also finds 17/23 absolute slots with both requested actions among genuinely free
choices, so the context-dependence reading survives excluding forced and budget-masked actions.

I read and accept the full critique (`MATERIAL_DISSENT: no`). It contradicts the original
intermediate story of reducing stale gate errors: the common initial effect instead prolongs
a stale block by withholding a release update. It leaves two materially different explanations:
needless waiting cancels conflict benefits, or the stale block itself supplies useful
conservative pacing. Both can produce the observed aggregate counts. No extra training is
selected to resolve them. The next useful decision is whether a prospectively specified
frozen-policy release intervention, available equally to the simple reference, can separate
those explanations at the same packet quota. C02 is technically complete and scientifically
read; such an intervention would be a new diagnostic comparison, not more C02 seeds or a
confirmation/promotion of its tiny positive means.

## 2026-09-20 — C03 prospective frozen-policy release-priority comparison and L0

The Critic's outcome cross-tab makes the next question concrete. Across the two C02 panels,
the 354 gate-first worlds jointly have ten fewer conflicts but zero additional completions;
the other first-difference groups contribute the aggregate +3 jobs. This grouping is factual,
not a decomposition of the first event's causal effect. I accept the Critic's further limit:
an earlier release consumes the packet otherwise available for a later snapshot. A release
intervention therefore identifies the package value of **release priority**, not uniquely the
value of removing conservative waiting. The cross-tab cannot answer that counterfactual.

Select a zero-new-fit diagnostic on all three existing final checkpoints, with no checkpoint
selection, retraining or calibration. A local `release_due` predicate is true when the sender
is currently DONE and projecting its own last transmitted packet under the unchanged public
projection law still yields a valid SHARED APPROACH at distance <=1. Its inputs are exclusively
the sender's current state, own last-sent payload/time and public time. It never inspects
untransmitted receiver state, reward, privileged diagnostics or a scheduler request channel.
For each release-priority arm, request send when either its ordinary scheduler requests or
`release_due` is true. Existing availability/forced-slot logic still enforces exactly one
packet per sender per frame. The guard neither creates a packet nor changes payload content,
latency, routes, controllers or termination. The same predicate is supplied to simple rules.

The primary targeted prediction is **fewer stale-release blocked gate decisions and more
completed jobs** for the guarded contextual policies versus their own unguarded frozen version.
That prediction would support trying a release-aware timing rule, not prove that fresher
messages are generally better. Reduced blocking with flat/worse service would weaken this
repair and emphasize scarce-token/future-snapshot tradeoffs or useful conservative pacing.
No reduction in blocking would mean the intended intermediate link was not reached by this
legal guard. If a guarded learner improves, compare it with the same-information simple
release rule before crediting learning. Do not optimize disagreement or collision counts
while ignoring native completed jobs.

Exposure is fixed now: master world seed **73150**, development phase 4 and final phase 5,
256 independent 96-tick worlds each, batch 32. The world addresses are disjoint from C01/C02.
Evaluate the existing nine AGE_CHANGE variants, and the identical nine with release priority,
on the same development worlds: 18 x 256 episodes. Select the best within each family by
completed-job fraction then the existing lexical tie rule, and separately record the best
development-selected simple family (lexical family tie: ordinary AGE_CHANGE first). This
selection uses no final worlds or policy fitting. The strongest selected simple reference
therefore has all legal release information supplied to the candidate.

Final arms are the six frozen-checkpoint variants (`L73141`, `L73141_RELEASE`, `L73142`,
`L73142_RELEASE`, `L73143`, `L73143_RELEASE`) plus selected `AGE_CHANGE`, selected `AGE_RELEASE`,
`PRE_DECISION` and `POLL`: ten x 256 episodes on one common exogenous panel. Report every arm,
within-checkpoint guarded-minus-original per-world differences, and each learned arm minus
the development-selected simple reference. Sharing this evaluation panel does not create
new independent training histories. **Zero new fits, zero training transitions and zero
optimizer calls**; total work is 4,608 development + 2,560 final episodes = 688,128 team
transitions. The existing measurements suggest roughly 15–30 s of single-child CPU work,
not a hard runtime endpoint. No post-score variants, thresholds, seeds or extra panels.

Frozen model inputs are the published `final.pt` files from C01 seed 73141 and C02 seeds
73142/73143. Their SHA-256 digests, respectively, are
`461db24607e23cc3c92c9e636850c61e1a9e29b703ed3b9a09d4e4a4f6b5b10e`,
`2d7d1a3d6db1f16b0f6fe4ad1041ea0dfc3afce0746748adf7fe936ae8ce43f7`, and
`522011e9b8dc0ce6e4d16f91b856e3278dda6bf3e575bddcb97bd16965048e55`.
Record their original source SHA/seed, reject digest or metadata mismatch before evaluation,
and verify exactly zero parameter movement relative to those loaded bytes. This is evaluation
of previously learned schedules, never new learning or a confirmation batch.

L0: implement this one intervention/evaluator under
`experiments/candidates/skill_information_refresh/c03/`, entry `scripts/run_sir_c03.py`, with
mirrored tests; DM owns the edits and accepts the review. Import unchanged C01 host/model/rule
functions rather than modifying accepted C01 semantics. Retain per-episode counts, complete
selection results, paired differences, legal/raw/guarded requests, executed sends and factual
state/cache traces; privileged stale-release waiting counts are offline diagnostics only.
Runner artifacts stay under this direction's new C03 run root. Check legal-info isolation,
guard truth cases and forced/budget behavior, unguarded collector replay against C01,
checkpoint digest/identity and immutability, exact counts/primary arithmetic and CLI admission
refusal. High-risk evaluator/checkpoint behavior gets independent review before DM acceptance.
Publish exact inputs, then use the existing local_linux native-admission path. No new shared
core, main/RESEARCH write, external dependency or GPU work. Stop on an unresolved technical
failure and retain the original operation; costs remain recorded without fit allowances.

C03 is implemented without editing C01. The focused suite reports **12 passed in 2.37 s**:
legal guard truth cases, peer-information independence, all four unguarded collector replay
paths, exact frame quotas/masks, one-tick release delivery and unavailable-budget refusal,
checkpoint digest/metadata validation, parameter immutability, complete synthetic output
arithmetic/selection, technical-failure labeling and the actual CLI's missing-admission
refusal. Author review caught an initially ineffective CLI test path and repaired it to
assert the specific admission rejection before this result. `git diff --check` passes.
These are synthetic correctness checks, not extra scientific evaluations. The independent
Reviewer now receives this C03-only evaluator/identity delta before execution.

The independent Reviewer read `d6d588450..052763ff6`, ran 12 tests (2.33 s), loaded and checked
all three actual frozen inputs against their declared digests/metadata, and returned no
material engineering finding. I read and accept that review. An additional author check of
combined C01/C03 collection exposed pytest's duplicate bare module name `test_contract`;
rename only the new C03 test to `test_release_contract.py`, preserving C01 and scientific
code. The combined direction suite now reports **31 passed in 3.47 s**, with whitespace
checks clean. This fixes test discovery, not the experiment or its exposure. Reviewer facts
do not establish scientific value. DM accepts C03 for the already specified native launch
after publication of this final input revision.

## 2026-09-20 — C03 read: release-priority repair reaches its proxy but loses native value

The [C03 manifest](../../../../runs/skill_information_refresh/c03_release_s73150_20260920/launch-manifest.json)
records native acceptance of the exact published inputs; its same operation exited zero with
a consistent process-exit witness. The DM retained observation throughout. Canonical control
had advanced to `6ee15d7d`; comparison against the earlier admitted control shows no change
to AGENTS, constitution, RESEARCH, skills or compute configuration, so no adopted governance
method or bound input was silently replaced. No duplicate, rebind or score-driven extension.

I read the [summary](../../../../runs/skill_information_refresh/c03_release_s73150_20260920/summary.json),
all 7,168 episode rows, the 18 development readings and ten final trace sets. Actual exposure
is exactly 4,608 development and 2,560 final episodes/688,128 team transitions, **zero fits,
training transitions and optimizer updates**; `updates.jsonl` is empty. Each loaded policy
has 3,778 finite parameters and exactly zero movement from its recorded input. All final
arms have the complete common 256-world panel, 14 jobs/96 ticks, 24 packets/192 bytes and
one packet per sender per frame. Trace values are finite. Runner wall is 12.206326 s
(selection 6.870426, final evaluation 5.311254), acceptance-to-child-exit 13.541678 s;
peak single-child RSS 241,596 KiB, user/system CPU 13.082793/1.029478 s. No GPU, training
replication, full-path speed claim or aggregate-node memory claim.

Both simple families independently selected `delta1_age8` on development (.938895089);
the predeclared family tie rule selected ordinary AGE_CHANGE. The selected AGE_CHANGE,
AGE_RELEASE, POLL, L73141 and L73141_RELEASE all have identical executed sends, legal
features, choice masks, physical states and caches on this fresh final panel. Guarded
nonpolling development variants did receive interventions (means 1.3125–1.48828125 per
episode), so the guard was not globally dormant. Final PRE_DECISION service is .898437500.

| Frozen checkpoint | Original service | Release-priority service | Guard minus original | Native jobs gained/lost | Stale-release waits removed | Conflicts added |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 73141 | .931361607 | .931361607 | 0 | 0 | 0 | 0 |
| 73142 | .934430804 | .931919643 | -.002511161 | -9 | 561 | 9 |
| 73143 | .933314732 | .931919643 | -.001395089 | -5 | 593 | 10 |

For 73142/73143 the guard actually overrides 1,173/1,454 free requests across all 256 worlds;
the first checkpoint has no override. Total ordinary waiting falls 472/495 ticks and BYPASS
choices fall 126/136. Guarded-minus-original positive/negative/tied worlds are 8/9/239 and
12/10/234. Thus the intervention is active and reaches its intermediate prediction, while
the predicted native improvement fails with the opposite sign. **Kill this release-priority
repair for the current package.** Better agreement with a fresh DONE state is not enough:
the intervention changes passage timing, routing and which later snapshot can use the quota.
The result identifies this legal guard's package effect, not a unique mediation effect of
waiting and not proof that intentional misinformation or delay is generally beneficial.

On the same fresh panel, original L73141/L73142/L73143 minus the selected simple reference
are 0/+.003069196/+.001953125: exactly 0/+11/+7 completed jobs among 3,584 opportunities.
The corresponding guarded increments are 0/+2/+2 jobs. The conditional original-policy
advantages are real readings and should not be erased by the failed repair. They are not
three newly trained replicas or a stable population/importance claim. Together with C02,
they strengthen the possibility that lawful contextual timing changes native pacing, while
weakening “remove stale blocks” as the useful-learning mechanism. The simple-clock explanation
does not cover the two contextual policies; a more plausible *simple* explanation is to
defer packets reporting a non-APPROACH/DONE stage, which the current freshness-oriented rules
do not directly express. Learning's increment over that transparent rule remains untested.

## 2026-09-20 — C04 prospective stage-only null comparison and L0

Select one final zero-new-fit comparator check to address the newly concrete simpler
explanation, not to optimize another learned architecture. Two untuned rules are fixed now:
`ACTIVE_FIRST` requests at any available slot if own stage is APPROACH or CROSSING, otherwise
waits for the ordinary forced slot; `APPROACH_FIRST` requests only if own stage is APPROACH,
otherwise waits for that same forced slot. They read only the sender's observed stage, not
distance, unsent teammate state, reward or a newly free priority channel. No threshold fitting,
learning, payload, access, delay, skill/route/controller or termination changes. C02's stage
slice motivates these two rules explicitly after observing outcomes; this is new exploration,
not a retrospectively prespecified C01 baseline or fresh confirmation.

Keep all three frozen checkpoint inputs/digests from C03, original greedy extraction only;
the failed release guard is not retained as a candidate. World master seed **73151**, disjoint
development phase 6 and final phase 7, each 256 x 96 ticks, batch 32. Develop the same nine
AGE_CHANGE variants plus ACTIVE_FIRST, APPROACH_FIRST and PRE_DECISION: twelve x 256 episodes.
Select the best AGE_CHANGE variant by its existing lexical rule, then the strongest simple
arm among that winner and the three fixed rules by development service and lexical arm name.
Final arms are original L73141/L73142/L73143, selected AGE_CHANGE, ACTIVE_FIRST, APPROACH_FIRST,
PRE_DECISION and POLL: eight x 256 episodes on one common exogenous panel. POLL is already
represented by the age-8 development variants, so no duplicate development execution is needed.
Report all arms and each frozen learner minus the development-selected simple reference.
Total 3,072 development + 2,048 final episodes = **491,520 team transitions, zero new fits,
zero training and zero updates**. Rough occupancy expectation 10–20 s from C03, not a deadline.
No outcome-selected further rule, panel, seed, horizon or network; the three training units
remain the original exploratory histories regardless of final episode count.

Prediction: at least one transparent stage-only rule produces the characteristic extra
stale-release waiting and much of the conditional native advantage, leaving little learned
increment against the development-selected reference. Check both executed schedules/initial
decision sites and completed jobs rather than claiming the rule matches a neural policy
from mean return alone. If the rule is stronger, prefer it and stop this unchanged learned
package; if a learned remainder survives, report the residual conditional gap honestly rather
than seeking confirmation in this bespoke host merely because its sign is positive. In either
case this closes the current small-host comparator/repair cycle. A further training study
would need a distinct target-relevant information-value question, not another initialization
or an ad hoc fourth stage rule.

L0: add only `experiments/candidates/skill_information_refresh/c04/`, the explicit admitted
entry `scripts/run_sir_c04.py` and mirrored uniquely named tests. Reuse C03's reviewed frozen
loader, collector, mean readings and paired arithmetic without changing C01/C03 code. The
two fixed stage predicates can use a parameter-free policy adapter to that collector; their
names/counts must remain unambiguously nonlearning. Preserve checkpoint digest/metadata,
zero movement/update verification, full twelve-variant selection and all eight final traces.
Check stage truth tables and irrelevance of other features, quotas, development-only selection,
full output arithmetic/identity, and CLI admission. Independent review covers the new selection
and fixed-rule adapter before acceptance. Publish exact input SHA and use local_linux's native
admission; keep the original handle and report any technical failure without rerunning blindly.

C04 implementation reuses C03 code byte-for-byte. The parameter-free adapter is explicitly
reported as a fixed rule; its use of the collector's policy-call interface is not called
learning. Six new checks verify exact stage truth tables, independence from all other legal
features, equality to an independently implemented direct stage predicate, channel quotas,
complete synthetic selection/output arithmetic and admission refusal. The full C01/C03/C04
direction suite reports **37 passed in 4.36 s**, and whitespace checks pass. The new C04
selection/adapter/entry delta goes to the independent Reviewer before any scientific run.

The Reviewer read `a9bbf9dbf..96a8d9dee`, independently verified the declared stage-only
information and phase-6/phase-7 selection separation, and ran six focused checks (1.75 s).
It returned no material finding or requested repair; unchanged C01/C03 code retains its
accepted checks. I read the full review and accept C04 for its frozen native-admission run.
This acceptance establishes implementation consistency only, not a scientific result.

## 2026-09-20 — C04 read: a stage-only rule captures the native advantage

The [C04 native manifest](../../../../runs/skill_information_refresh/c04_stage_s73151_20260920/launch-manifest.json)
binds the published source and accepted request. Its same operation exited zero with a valid
process-exit witness and consistent native records; DM retained observation, with no duplicate
or rebind. I read the [summary](../../../../runs/skill_information_refresh/c04_stage_s73151_20260920/summary.json),
all 5,120 episode rows, the twelve development variants and all eight final trace sets.
Actual exposure is 3,072 development/294,912 transitions and 2,048 final/196,608 transitions:
**491,520 team transitions, zero fits, training transitions and optimizer updates**. The update
stream is empty; all three checkpoint parameter movements are exactly zero and all parameters
are finite. All eight arms retain every common final world, 96 ticks/14 jobs and exactly
24 eight-byte packets, one per sender per frame. All trace values are finite.

Runner wall is 8.291329 s (selection 4.349858, evaluation 3.918602), acceptance-to-child-exit
9.408551 s. Peak RSS 241,884 KiB is the single child, user/system CPU 9.058556/1.144322 s;
the native memory admission passed on the actual local node. This is not full authoring,
queue or publication time and no speed claim follows. Across C01–C04 the cost remains **three
started training fits**, 1,179,648 training team transitions/1,536 optimizer calls, plus the
recorded initial/development/frozen evaluations: 3,336,192 total team transitions. Reusing
three trained checkpoints on more world panels never increases independent training n.

Development selected `ACTIVE_FIRST` (.948381696), ahead of selected AGE_CHANGE `delta1_age8`
(.947823661), APPROACH_FIRST (.946707589) and PRE_DECISION (.890066964). Selection occurred
before the final panel. The final comparison is:

| Final arm | Completed-job fraction | Physical conflicts/episode | Stale-release waits/episode |
| --- | ---: | ---: | ---: |
| ACTIVE_FIRST (selected simple) | .944475446 | .16015625 | 6.56640625 |
| APPROACH_FIRST | .944196429 | .16015625 | 6.734375 |
| L73141 | .941127232 | .19921875 | 4.8046875 |
| L73142 | .944196429 | .16015625 | 6.59375 |
| L73143 | .944196429 | .16015625 | 6.734375 |
| Selected AGE_CHANGE = POLL | .941127232 | .19921875 | 4.8046875 |
| PRE_DECISION | .907924107 | .40234375 | 1.4296875 |

L73141/L73142/L73143 minus the development-selected reference are -.003348214/-.000279018/
-.000279018: **12/1/1 fewer completed jobs** on the 3,584-opportunity panel. Positive/negative/
tied worlds are 8/10/238, 0/1/255 and 0/1/255. The two contextual models and APPROACH_FIRST
have identical per-world completion counts, not merely the same mean, and all three lose
the same single job versus ACTIVE_FIRST in world 126. ACTIVE_FIRST versus POLL has 12 more
completions, ten fewer conflicts, 367 extra ordinary waiting ticks, 451 extra stale-release
waiting ticks and 159 extra BYPASS choices. Thus a parameter-free own-stage rule can produce
the native pacing pattern and the conditional benefit attributed to contextual timing.

Do not turn those counts into policy equivalence. L73142 matches ACTIVE_FIRST's full send
schedule in only 37/256 worlds (832 different send bits), but physical state histories in
249/256. L73143 matches ACTIVE_FIRST's schedule in 10 worlds and physical histories in 209;
against APPROACH_FIRST its schedule matches in 143 worlds and physical histories in 254.
Messages may move without affecting a later physical choice. By contrast, L73141, selected
AGE_CHANGE and POLL are actually identical in the saved executed sends, legal features,
choice masks, physical states and caches on this panel. No equality outside the observed
panels, statistical equivalence, global optimality or stable learned-versus-rule ranking
is claimed.

**Decision: prefer the transparent stage rule on this host and stop the unchanged learned
package/repair cycle.** The stronger simple explanation predicted additional stale-release
waiting together with comparable native benefit, and that is observed. Legal representation
and finite learnability are supported: two genuine trained policies do execute contextually.
Complete-package learning value is not established once the outcome-informed but independently
selected stage-only comparator is included. The discarded release-priority repair is an
especially useful negative constraint: reaching a freshness-related proxy can hurt service.
These effects are contingent on this host's fixed projection, yielding and route-selection
laws; they are not evidence that outdated data is desirable in general or that current HMASD
learned skills, UAV communication or archived CADC have been validated.

The direction is now **idle at a scientific boundary**, not waiting for an owner ACK, a fit
allowance, a process, an uncollected result or an adviser. No further training, rule variant,
panel expansion or confirmation is selected for this small host. A concrete re-entry would
be a distinct target-relevant timing question with a recorded information/receiver law and
a prediction separating learned scheduling from the now-carried-forward stage-only null;
it need not use a new architecture or earn a toy pass. Merely adding seeds, training longer,
or omitting the stronger simple rule is not that new reason. Root remains the shared
main/RESEARCH integrator; the direction's evidence and code are published on its own branch.

### Final saved-trace criticism and factual correction

I read the Critic's full final answer and adopt its limited closure (`MATERIAL_DISSENT: no`),
not as another empirical replicate. Against POLL, first gate/route/no-native-difference counts
are ACTIVE_FIRST 166/52/38, APPROACH_FIRST 174/57/25, L73142 168/48/40 and L73143 174/56/26.
All C04 gate-first cases prolong robot 1's wait on a valid projected APPROACH-at-zero while
the actual peer is DONE; POLL and the factual full-snapshot gate enter. ACTIVE_FIRST matches
L73142's first-decision signature in 252/256 worlds, including 38 common no-event worlds;
APPROACH_FIRST matches L73143 in 254/256, including 25 common no-event worlds. Their first-send
signatures match only 221/256 and 255/256 respectively. This independent saved-trace read
supports reproduction of the initial behavioral pattern, not identity of whole policies or
a decomposition of return into waiting effects. C03's packet-allocation tradeoff still limits
the causal interpretation. Preferring simplicity is not a statistical superiority/equivalence
claim, and earlier conditional gains over POLL remain valid evidence.

Correction to the earlier C02 critic entry: its phrase “all 354 ... at distance zero” was too
specific. The direct audit finds 352 projected distance-zero cases and two distance-one cases
(both from seed 73143). All 354 satisfy the same <=1 yielding condition; the gate-first counts,
outcome cross-tabs and delayed-release interpretation are unchanged. This correction is
appended without rewriting the historical reading.

## 2026-09-20 — Owner re-entry: a falsifiable receiver-value condition

The owner explicitly reopens C to answer its recorded admission question, not to repeat C04
or infer that timing value cannot exist. I verified the clean direction checkout at
`43d271914c20b1b3c496153a902d41a2e42ceef2`, current canonical owner pause lifted, C exploring
and assigned to Codex DM. I reread the current constitution and both scientific/engineering
methods. Fits remain measured cost, **not an allowance**; the methods' stale allowance prose
does not apply. The previous idle boundary is superseded by this owner-directed question.

The discriminating condition is: **two legal sender histories matched on stage, cache age,
cache change, public clock and remaining quota have opposite rankings of the native values
of sending now and later, because of received task context or locally observable uncertainty.**
Merely correlating a neural score with age, or assuming that the receiver wants a packet,
does not satisfy it. A receiver request/priority is information and must arrive through a
declared, charged channel. "Not captured by stage/age/change" is a restricted representation
statement, not an assertion that no transparent rule can encode the answer. A model-aware,
budget-aware value rule is the strongest same-information simple comparator if available.

I verified the primary author PDF of Soleymani, Baras, Hirche and Johansson,
[Value of Information in Feedback Control: Global Optimality, IEEE TAC 2023](https://people.kth.se/~kallej/papers/Value_TAC2023_Soleymani.pdf)
(DOI 10.1109/TAC.2022.3194125), especially sections II–III and equations 10–12. Its trigger
uses a specified causal information set, a costly channel with one-step delay, and a value
difference containing both current estimation error and future continuation value. Its
optimality result assumes its Gauss–Markov/quadratic-control model and jointly chosen
controller/trigger; it does not establish a fixed-skill MARL result. In particular, its
trigger's access to past controls is not free feedback that our host may import. The useful
bridge is the opportunity cost of consuming a finite communication opportunity, not the
paper's optimality claim. The SchedNet full-text reading and adverse CADC result above remain
binding contrary evidence: removing collisions or using fixed skills cannot redeem CADC.

The independent Critic returned a two-decision counterexample in which a fixed, paid
receiver-mode packet indicates which private observation is unreliable. It correctly notes
that comparing the two Bayesian gains solves that toy exactly, and that timing after seeing
the condition could itself signal it. I accept these constraints. C05 below uses a related
explicit cache-refresh law with a task weight and sensor-observed obsolescence risk. Its
receiver decoder is fixed and does not infer hidden state from silence; the visible timing
choice is nevertheless recorded as an information-bearing channel. No adviser opinion is
counted as another experiment.

### C05 minimal host, causal information and analytical admission

One six-tick cycle has two agents, a sender S and receiver R. R executes fixed commitments
`[0,3)` and `[3,6)` with immutable feedback branches at ticks 2 and 4. At either branch it
uses its last delivered binary cache value; a correct branch completes a job worth `w` and
4 task-service units respectively. Skills, endpoints, branch law, packet content and access
are identical across arms. The initial cache is 0 and the initial true condition X is an
independent fair bit, so that default is not worse than another fixed prior guess.

R privately observes the first job weight `w in {1,2,3}`. At tick 0 it always sends the fixed
context payload `(w, 4, 2, 4)`: four uint8 payload fields, a uint16 timestamp and uint8 sender
header, **seven bytes**. This reaches S at tick 1. Treat it as a charged priority/context
request, not a free scheduler feature. S at tick 1 locally observes X and a calibrated
sensor regime `q in {.1,.5,.9}`. At tick 3 the condition flips with probability q, independently
of the packet choice. q is an observed probability, **not the future flip realization**.
The three weights, three risk regimes and two initial conditions are independent/uniform.

Fixed TDMA permits R only at 0 and S at 1 or 3. S has one data token: send at 1, or save it
and obligatorily send at 3. The payload is always the currently observed condition, one
uint8 plus the same three-byte timestamp/sender header. Delay is exactly one tick, before
the branch at 2 or 4. Thus every arm spends **two packets / eleven bytes per cycle**, including
the context request; there are two visible S access slots and one binary timing choice.
Neither requests, priority ordering nor fresh global states are otherwise accessible. All
policies receive the same lawful `(X, delivered w, q)` view. The evaluator can log future
state but cannot supply it to the scheduler. R uses the received bit, not timing inference,
q, oracle state, or an arm-specific decoder. These are explicit fixed-host limits.

Conditional native values are `Q_early = w + 4(1-q)` and
`Q_late = w(1-X) + 4`, so **Delta = w*X - 4*q**. With X=1 and q=.5, w=1 prefers late
and w=3 prefers early even though sender stage/age/change/clock/quota match. With X=1 and
w=2, q=.1 prefers early and q=.9 prefers late. The full same-information transparent
`VOI` rule sends early iff Delta>0 (ties late); it is exactly optimal for this fixed decoder
and these two timing choices. There is no prediction that a learner beats it.

The complete deterministic stage/age/change family here consists of the four Boolean
mappings from X to early/late; all other family inputs are constant. `PRE_FIRST` always
sends before the first action (also first-slot polling/active-first), `PRE_LAST` always
saves for the next commitment's action, `AGE_CHANGE` sends early iff X differs from cache0,
and `INVERSE_CHANGE` supplies the fourth mapping. A randomized mixture cannot improve on
their maximum expected value. Their analytical maximum is 5 task units/cycle. VOI is
`5 + 5.8/18 = 5.322222...`; the extra .322222 is the specified representation opportunity,
not an observed learning gain. Setting q=0 removes obsolescence: AGE_CHANGE and VOI then
coincide in value at 6, and the claimed context-dependent residual is zero. Giving the
scheduler an uncharged w or realized future flip would invalidate the admission, not rescue it.
The charged context itself adds only .055555... over a rule that knows q but averages unknown
w; most of the restricted-family gap involves local predictive risk. We will not attribute
the whole gap to the receiver packet or assume it is worth adding in a different system.

### C05 prospective direct comparison, cost and L0

Proceed once with this bounded bridge, without transferring the old crossing host's rewards
or checkpoint. **One exploratory fit, training seed 73160, 16,384 six-tick cycles**, 128/call,
four full-batch PPO epochs per call = 512 optimizer calls and 98,304 training team ticks.
The sender policy and value functions each use the three normalized legal inputs, a 16-unit
tanh hidden layer and scalar head; float32 CPU. Adam lr .003, PPO clip .2, entropy .01,
value coefficient .5 on squared-error/2, gradient norm .5. Native reward is divided by the
fixed upper bound seven for training only. Each episode has one learnable Bernoulli timing
choice and terminal reward; there is no bootstrapped future target or analytic-VoI label.
Final greedy send iff probability >=.5. Random initialization and action draws use the seed;
world generation uses separate phase-keyed generators. No development tuning/selection.

Final six arms are LEARNED, VOI, PRE_FIRST, PRE_LAST, AGE_CHANGE and INVERSE_CHANGE on 4,096
common new cycles. Read final LEARNED minus **VOI** as the primary learned-increment comparison,
and separately report the best of the exhaustive restricted family; never substitute the
weaker family as the strongest primary. A finite exact panel enumerates all 18 contexts and
ten equiprobable flip outcomes: 180 cycles for initial LEARNED, and 180 for each final arm.
A prespecified q=0 control enumerates six contexts and the same ten outcomes: 60/arm, no
retraining. Exact panels are model enumeration, not independent training seeds or real-world
replicas. Total exposure is 42,580 cycles / **255,480 team ticks**, one started fit, 512
optimizer calls; no other fits, seed extensions, hyperparameter variants or confirmation.

Intermediate prediction: the exact-value comparator reverses its send choice within matched
change strata as legal w/q vary, whereas each restricted rule cannot. Those choices must
change the receiver's actual branch correctness, not merely an information-age proxy.
Native prediction: VOI's enumerated .322222 advantage over the strongest restricted rule
is recovered, and disappears at q=0. For the learner, parameter movement alone is insufficient:
read greedy conditional choices, exact native regret to VOI and initial-to-final movement.
Learning may recover some/all of the opportunity but cannot establish extra package value
over the rule. A wrong exact identity, context arriving too late, or leaked future bit is
a technical failure; the disappearance of the legal value reversal would instead defeat
this scientific condition. An unsuccessful fit would weaken finite learnability for this
declared procedure, not the algebraic existence claim.

L0: add only `experiments/candidates/skill_information_refresh/c05/`, admitted
`scripts/run_sir_c05.py`, and uniquely named mirrored tests. Do not change C01–C04, shared
learners, canonical control or RESEARCH. Implement explicit packet bytes, one-tick delivery,
the frozen receiver branches and a view isolated from future state; preserve raw traces,
updates, checkpoint, phase counts and exact context tables. Test packet/causal boundaries,
all finite contexts and the q=0 falsifier, sampling/phase separation, real parameter updates,
complete output arithmetic and admission refusal using managed pytest scratch. Independent
engineering review precedes acceptance, publication and native local_linux admission.
This is an existence/representation and finite-learnability bridge under fixed scripted
commitments, not evidence for current HMASD learned skills, endogenous coordination or UAVs.

C05's focused synthetic checks initially passed (8 tests, 1.66 s). They verify the exact
counterfactual value identity and q=0 boundary as implementation checks, not a completed
scientific fit. The implementation also retains all sampled training-cycle traces, rather
than relying only on update-mean rewards to recover actual exposure. Final review/tests
follow before any result-bearing execution.

The independent Reviewer read `43d271914..7dd0673e4` and ran the eight focused tests
(1.68 s). Its sole material finding was P2 failure instrumentation: completed training
rollouts were counted only after all optimizer epochs, and raw training traces were saved
only after all batches. I accepted the finding and moved exposure counting immediately
after rollout, retained accumulated traces on handled failures, and recorded available
parameter movement in the finalizer. A new managed-scratch second-optimizer-step failure
regression requires one completed batch, exactly one successful update, partial raw traces
and TECHNICAL_FAILURE, without a final checkpoint. This is an engineering repair before
the first C05 scientific run, not a failed scientific seed or a renamed retry.

The complete direction suite passes **46 tests in 4.45 s**. The Reviewer independently
accepted the repair at `91a0127c2`, running the new failure regression (1 passed, 1.67 s)
and finding no remaining material issue. I read the full review and accept the C05 delta.
The Critic also checked the concrete information view and value algebra, with no material
dissent. I adopt its sharper learning read: exact native regret is
`sum_context |Delta| * I[learned_choice != VOI_choice] / 18`; ties contribute zero, and an
accidental advantage on 4,096 random cycles cannot beat VOI in expectation. Calibrated local
q and the fixed, non-inferential receiver are essential limits; the paid w contributes
only 1/18 task unit independently, not the entire restricted-rule gap. This single fit ends
the bridge's finite-learnability question at its exact regret, with no seed extension or
superiority confirmation. A later target-host question requires its own lawful mapping and
strong simple reference; neither sign of this toy automatically decides that question.
These reviews establish consistency and interpretation constraints, not an empirical result.

## 2026-09-20 — C05 read: the legal value condition exists; learning implements the rule

The [C05 manifest](../../../../runs/skill_information_refresh/c05_value_s73160_20260920/launch-manifest.json)
binds published source `d8680026026b06f0861601839444392c452e8c20` and the original native
operation `6a2824b43e43a0c99ffad472a87efa178ec3774c19507dda0f2a825c1308edd5`. Admission
observed canonical `fd8402f592ac310cdccc4619137c041796df29b6`, accepted at 22:56:32.065558 UTC,
and passed fresh actual-node memory (11,771,940,864 available bytes, four-GiB floor).
The same handle exited zero with a valid OS process-exit witness and consistent native records.
No duplicate, retry or observer rebind occurred. At this boundary I compared the changed
canonical revision's AGENTS, constitution and three used methods with the accepted source:
no relevant content changed; the loaded no-allowance rule remains adopted.

I read the complete [summary](../../../../runs/skill_information_refresh/c05_value_s73160_20260920/summary.json),
26,196 evaluation rows, 512 update rows and all twenty saved trace arrays, including every
sampled training cycle. Actual cost matches the prospectus: **one fit, 16,384 training cycles,
98,304 training ticks, 512 updates; 42,580 total cycles / 255,480 total ticks**. Every recorded
cycle uses two packets/eleven bytes, with context arrival at 1 and data arrival at 2 or 4.
All numeric arrays and parameters are finite. Independent reconstruction from raw conditions,
actions, weights and flip draws matches every native reward; phase row counts and summary
counts agree. Checkpoint displacement is 4.983677387 for 162 parameters; evaluation movement
is zero. Runner wall is .787012 s (training .594916, evaluation .186245); acceptance-to-exit
2.726698 s. Peak child RSS is 301,052 KiB and user/system CPU 2.179584/1.133703 s, not total
node occupancy or complete research cost. Across C01–C05: four started fits, 1,277,952 training
ticks, 2,048 updates and 3,591,672 total team ticks across the different declared hosts.

| Arm | Exact expected task units | Fresh 4,096-cycle mean | q=0 exact control |
| --- | ---: | ---: | ---: |
| LEARNED | 5.322222222 | 5.313964844 | 6.0 |
| VOI (primary) | 5.322222222 | 5.313964844 | 6.0 |
| PRE_FIRST / first-slot polling | 4.0 | 3.957031250 | 6.0 |
| PRE_LAST | 5.0 | 5.001220703 | 5.0 |
| AGE_CHANGE | 5.0 | 4.990234375 | 6.0 |
| INVERSE_CHANGE | 4.0 | 3.968017578 | 5.0 |

The claimed intermediate reversal occurs. At X=1,q=.5, learned early probabilities for
w=1/2/3 are .268483/.459387/.664715: greedy late/late/early, agreeing with the exact
negative/tied/positive value differences. The initial greedy policy was early everywhere
(exact value 4.0). Final greedy choices match VOI on all eighteen contexts, including the
tie; strict errors and the independently reconstructed **exact native regret are both zero**.
Across final exact, random and q=0 panels, every saved native trace field matches VOI,
not only the mean return (the neural probabilities differ from a deterministic rule).
This is finite-support executed-greedy equality for this one training history, not equality
of neural functions, stochastic training policies or out-of-support policies.

The native prediction also holds: the exhaustive restricted family's expected maximum is
5.0 and VOI/LEARNED are higher by .322222222. The fresh panel difference from its best
restricted rule is .312744141, or 1,281 weighted task units. That final-panel maximum is
descriptive, not a development-selected baseline; the primary VOI was fixed beforehand.
At q=0 the expected gap vanishes exactly, as predicted. The learned control-panel match is
an observation at the specified out-of-training-support q=0, not broad distribution-shift
evidence. Adding the receiver context has not been shown to be net worthwhile relative to
spending its seven bytes on something else; its independent value in the fixed comparison
is only 1/18 task unit, and all compared arms already pay those bytes.

**Judgment changed:** a legal, task-relevant refresh-value condition beyond a restricted
stage/age/change mapping now has an explicit constructive answer, and one actual fit learns
it. C01–C04's failure to beat ACTIVE_FIRST therefore does not justify an absence judgment
for the direction. **Judgment not changed:** learning has no incremental value over the
strong transparent comparator here; the exact VOI rule is the preferred implementation.
The calibrated q, predetermined two-decision law and fixed non-inferential receiver make
this a small information-decision bridge, not general MARL, learned-skill, UAV or CADC evidence.
The old CADC adverse result and C03's failed freshness repair remain unchanged.

The prespecified C05 bridge is complete and read; no extra seed, longer fit, architecture,
rule sweep or confirmation follows from zero regret. C remains exploring at the positive
existence boundary, with the owner's now-requested C-specific Pro consultation as the next
action. The live question is a target-relevant lawful mapping that would make estimation/
learning useful beyond a matched value rule, not whether an extra rule can be found to win
this solved toy. I do not mark the entire direction absent or paused from this result.

## Pro question 2026-09-20 C05 receiver-value bridge — Pro consultation input

Conversation: new / actual conversation and dispatch are coordinated by Root. This is C's
independently authored input only, not an A/B synthesis or a request for an independent Send.
The owner explicitly requested this consultation section after reopening C's admission
question. Root will supply the full question `source_sha` after publication. C DM owns the
whole notebook until an explicit answer-only loan is dispatched; no adviser currently owns
or may edit this file merely because the empty answer slot below exists.

Question: **Does C05 establish a useful admission condition for continuing information-refresh
research, and what single smallest target-grounded observation/comparison would justify a
learning test beyond a strong same-information value rule—or justify suspending the learned
line without claiming that refresh value is absent?** This is a source/target bridge and
scientific choice, not a request to approve C05, invent a menu of schedulers or recommend
more seeds because the toy is positive.

Standing: C05 constructs the condition that legally available task context reverses timing
value at matched stage/age/cache-change/clock/quota. A receiver with fixed two commitments
and cache-feedback branches at ticks 2/4 privately sees job weight w=1/2/3 and sends its
fixed seven-byte context at tick0, arriving at tick1. The sender locally sees fair bit X
and calibrated flip probability q=.1/.5/.9, never the future flip. Its one fixed four-byte
snapshot must be sent at1 or3 and arrives one tick later; every arm pays two packets/eleven
bytes. The receiver does not learn, change termination or decode silence. Native rewards
are weighted correct branches w and4. `Delta=wX−4q` flips sign with paid w or local q;
transparent VOI sends iff Delta>0 and explicitly includes the saved-token opportunity cost.
This same-information rule is the strongest primary, not a myopic freshness or polling null.
All four deterministic change-only mappings are reported, including refresh before the
first decision and before the later commitment decision. Their exact best is 5; VOI is
5.322222222. One declared 16,384-cycle PPO fit matches VOI on every one of eighteen contexts
and every native trace in the final random/exact panels: exact regret 0, no incremental
learning value. The q=0 falsifier removes the restricted-rule gap. The whole .322222 gap
must not be credited to recipient context: paid w independently adds only 1/18 over using
the known average w. We have not tested whether that context packet is worth buying.

Strongest alternatives/contrary evidence: (1) C05 may be a valid but too specially solved
fixed-decoder example: perfectly calibrated q and a known law eliminate the need for a
learned scheduler. (2) C04's own-stage ACTIVE_FIRST beats three frozen policies by12/1/1 jobs;
learning's earlier tiny advantage over age/poll rules disappeared with a stronger simple
reference. C03 reduced stale-release waits but lost native completions, so freshness is not
itself the objective. (3) archived CADC's one learned/RR pair was adverse, net service
-.013354921301 and physical-.012099183996, with16,744 versus0 collided attempts; this is not
a causal collision diagnosis and this collision-free fixed host does not redeem it.
(4) If a proposed target needs current receiver intent/uncertainty without a timestamped
packet, or learns a priority/backoff/request channel without charging it, it changes the
information problem. Timing itself can signal X; C05 holds the receiver's no-silence decoder
fixed and records the binary timing opportunity, not a proof for jointly optimized signaling.

Context (repository-relative paths resolve at the full `source_sha` Root supplies, except
the explicitly frozen C05 execution source and external primary URLs):

- Governance: `docs/project/OPERATING_CONSTITUTION.md` sections1–8, especially3 (fits are cost,
  no allowance),4 (existing records),5 (Pro advisory),8 (matched information and baselines).
  `docs/research/RESEARCH.md`: owner pause and only the skill_information_refresh row; current
  owner instruction is the re-entry/consultation described here, not a portfolio review.
- Methods: `.agents/skills/hmasd-scientific-tools/SKILL.md`, "Update the working explanation",
  "Simple-model and literature bridges", "Comparators and MARL information", "Statistics"
  and "Cost and exposure". Its stale allowance wording is superseded by constitution section3.
  Engineering "Checks and review" / "Execution and admission" only if feasibility is contested.
- Current question/interpretation: this notebook's "Owner re-entry" and "C05 read" sections;
  the immediately preceding exact protocol is frozen at execution source
  `d8680026026b06f0861601839444392c452e8c20` and must not be retrospectively changed.
- Actual C05 evidence: `runs/skill_information_refresh/c05_value_s73160_20260920/summary.json`,
  `episodes.jsonl`, `updates.jsonl`, `final_exact_LEARNED.npz`, `final_exact_VOI.npz` and
  `zero_risk_exact_AGE_CHANGE.npz`; causal implementation in
  `experiments/candidates/skill_information_refresh/c05/host.py` and `study.py`.
  Binary traces may be unavailable to Pro; state that gap rather than claim to have read them.
  Summary contains all eighteen conditional actions/probabilities and exact expected values.
- Contrary evidence: this notebook's C03/C04 reads and
  `runs/skill_information_refresh/c04_stage_s73151_20260920/summary.json`; archived
  `docs/research/candidates/contention_aware_decentralized_communication/CADC_B01_RESULT.md`
  (its source `22e009c9387f2507aab6ebab4555d92e27f5070e` remains the historical contract).
- Primary bridges: SchedNet <https://arxiv.org/html/1902.01554v1>, sections3.1–3.3/4/appendixD,
  and Soleymani et al. <https://people.kth.se/~kallej/papers/Value_TAC2023_Soleymani.pdf>,
  sectionsII–III/equations10–12. Use their actual information/controller assumptions, not
  a remembered slogan or a claim that either establishes this fixed-skill learning advantage.

Cost, not allowance: four cumulative exploratory training fits in C, one being C05; C05
alone cost 255,480 team ticks (42,580 six-tick cycles) and 512 optimizer updates. There is no
numerical fit allowance or extra approval gate. No successor fit is prospectively selected
yet. The adviser cannot grant a budget, launch runs or resume a pause. Any chosen next batch
will declare arms, seeds, horizon, fit/non-fit cost and intermediate/native predictions;
a confirmation claim, if ever justified, needs 3–5 fresh independent training seeds/arm.

Return: give a focused judgment and strongest objection, preserving separate claims about
opportunity, representation, one-history learnability and package value. If continuation is
worthwhile, identify **one** concrete lawful receiver-commitment/action-opportunity/uncertainty
mapping; explain how the sender obtains it with delay and full bit/packet cost; name the
strongest transparent same-information comparator (including calibrated/plug-in VoI if
appropriate), what remains unknown to both, and a discriminating intermediate/native
prediction with fit and dominant non-fit work. Do not create a richer learned arm by giving
it feedback, request bits, simulator queries, calibration data or model knowledge denied to
the comparator. A specific observation showing this mapping exists and changes the relative
timing value would justify a new prospective comparison. An argument that all proposed
benefit is from an unpaid context channel, a changed receiver, or an already solved rule
would instead justify suspending this learned line while retaining C05's bounded existence
result. "Try a bigger network" or "the toy passed, so test UAVs" would not change the next
action. It is legitimate to recommend no useful next learning experiment; do not infer a
general absence theorem or require an endless baseline/rule search. State consequential
source-use gaps and `MATERIAL_DISSENT: yes/no`.

Constraints for any later answer-only dispatch: no training and no edits outside this
question's empty `### Answer` subsection on branch `codex/skill-information-refresh`, target
`docs/research/candidates/skill_information_refresh/NOTES.md`. Read reasoning inputs at the
pinned question/source SHA, fetch the latest target blob before writing, preserve every
other byte, and stop on overlap. Report the actual answer commit; on write failure return
the complete answer in chat, not only a SHA/status/link. Root coordinates the actual Send;
C DM will verify the complete answer and append its own adoption/rejection judgment.

### Answer

## 2026-09-20 — Post-C05 narrowing: prefer transparent value prediction; no successor fit

Root explicitly asked C to continue its own judgment while the owner-requested Pro
consultation proceeds, without editing A's answer. I rechecked the clean C checkout at
`4ef39c08ae55c6dd623718b4072a7ddcc9b9e913`, current canonical pause lifted/Codex DM assignment,
and the constitution and scientific/engineering methods. The no-allowance cost regime is
still adopted. This entry is only in C's owned notebook; it neither changes the pinned Pro
input nor writes in its empty answer subsection. Pro is not permission for the next action.

The current explanation is stronger and narrower than the earlier C04 idle judgment:
lawful task-sensitive timing value demonstrably exists, and one trained history realizes
it, but the complete C05 policy is a transparent value rule. The next useful question must
change that decision/use, not merely make the toy larger. I examined two concrete proposed
extensions before selecting any implementation or experiment.

**Unknown q alone is not a new scheduling-learning question.** Let H be the same lawful,
passively observed sender history available to both arms. Under the unchanged fixed
two-action receiver and exogenous transition law,
`E[Delta | H,X,w] = wX - 4 * Pr(next flip | H,X,w)`.
Thus a model-consistent posterior-predictive probability plugged into the same transparent
threshold is sufficient for this decision. For a persistent Bernoulli risk with n locally
observed flips and k successes, for example, a declared discrete prior has
`Pr(q | H) proportional to Pr(q) q^k (1-q)^(n-k)`; use its predictive mean, with identical
history/model/prior rights for a learned arm. A frequency or calibrated predictor is a
necessary practical comparator when the prior/model is estimated, not an extra privilege
reserved for the rule. This is a conditional derivation, not a new training result or a
claim that known-model Bayes performance describes every empirical estimator.

There is a sharper point for the *actual C05* law: q is independently redrawn each cycle.
If its local calibration observation is simply hidden, earlier cycles do not identify the
current draw; under the known uniform prior the predictive flip probability remains .5.
The optimal same-information rule becomes early only when X=1,w=3 (ties late), with
analytical expected value `31/6 = 5.166666...`, not the full-information `479/90`.
Giving a new neural arm the true current q while this comparator only gets history would
manufacture an information advantage. Making q persist, making observations depend on the
schedule, or adding informative local covariates could be legitimate new hypotheses, but
they change the scientific condition and need an actual target reason. Neither "unknown q"
nor a larger recurrent network by itself supplies one here. The single predictive probability
is sufficient for this law; I do **not** claim that a scalar is sufficient for an arbitrary
feedback problem or that a full Bayesian posterior is generally inadequate.

**The paid-context construction is not a demonstrated best communication allocation.**
If the per-sender R1/S1 quota is relaxed while retaining the two available S slots and a
total two-packet/eleven-byte ceiling, omit the seven-byte R context and send two four-byte
S snapshots at ticks1 and3. They arrive before both fixed receiver decisions, so each branch
is correct and expected native value is `E[w]+4 = 6` using only eight bytes. This exceeds
C05's 5.322222... without learning. It is a useful resource-design dominance example, not
a legal new primary under C05: it changes sender quota/allocation and the information
received, whereas C05 explicitly fixes one mandatory R packet and one S token. It therefore
limits the claim that buying C05 context is a useful overall communication design; it does
not invalidate the legal timing-value reversal within that bound contract. No new arm was
silently added to C05 and no run was relabelled. The already-read independent w value of
only1/18 task unit remains a warning against crediting the entire .322222 gap to context.

The nearest coupled-host mapping is also not automatic. In C01's actual `Worlds.make`,
local progress probability is the constant .75; `LocalView` contains own/last-sent state,
the delivered projected peer cache and public12/16 commitment clocks. Native jobs have
equal weight. It has no C05-style variable calibrated q or recipient-private w. Packets do
affect the fixed gate/route choice and hence later physical states, so endogenous coupling
is not missing from that host. But C02–C04 already show that a stage-only rule reproduces
the observed native pattern and removes the learned increment; C03's targeted freshness
repair attained its intermediate effect while harming native service. Merely citing this
known coupling again does not distinguish a new explanation from the carried-forward
ACTIVE_FIRST null. These facts do not prove that no better crossing scheduler exists.

The independent Critic checked this proposed narrowing and returned no material dissent.
I adopt its two qualifications: the eight-byte schedule changes quota, and the statement
about posterior sufficiency concerns C05's *one predictive probability*, not complete
belief-state reasoning in general. Its conclusion is advice, not another empirical unit.

**Decision: retain transparent VOI for the solved C05 object, and suspend additional fits
on the current learned-scheduler line; no C06 or larger-host experiment is selected now.**
This is a scientific narrowing/prepared pause, not an owner pause, an allowance limit,
a failed seed count, or a claim that information refresh has no value. C remains indexed
`exploring`; Root owns any standing update. In particular, no result or theory here validates
HMASD learned skills, UAV benefit, or the archived CADC package. Pro consultation can still
change this choice when its concrete argument is read, but its pending answer is not the
reason to stop these uninformative extensions and does not block independent reasoning.

A concrete re-entry would identify, in a specified target, how a lawful refresh changes
receiver feedback and future opportunities so that the C05 single exogenous value difference
does not settle the useful choice, and give a new native prediction against the carried-
forward stage rule and a competent same-information predictive/value comparator. Legal
context must have a timestamp, delay and full request/packet cost; any estimation or
amortized-computation benefit must compare the same data/model access and full work. For
the already-studied crossing host, this needs a discriminating reason beyond its previously
known gate/route coupling. These are examples of information that would change the present
judgment, **not** a new approval requirement, an exact-headroom proof or a toy-pass prerequisite.
A sufficiently concrete new hypothesis may be tested prospectively without waiting for Pro
or the owner to approve an ordinary within-direction idea. At present I have selected none;
there is no fabricated external blocker or recurring check.

This continuation used source reading, analytic counterexamples and criticism only:
**zero new fits, optimizer updates, simulations or result-bearing launches**. C's cumulative
cost remains four fits and the counts already recorded in the C05 read. The notebook and
the complete C01–C05 evidence remain available; no code, result, claim, A/B record or shared
index was altered. On receipt of the actual Pro answer I will read it and append the
specific adoption/rejection and any changed experiment decision here.

## 2026-09-20 — Pro answer adoption and formal direction-investment suspension

I read the complete 474-line ABC Pro answer, including its source/readability limitations,
then checked its C recommendations. The actual delivered answer is preserved in A's
[notebook at answer commit 8904327f9598d4896cb9425550f84584deaa902a](https://github.com/CartmanFatass/My-paper-code/blob/8904327f9598d4896cb9425550f84584deaa902a/docs/research/candidates/termination_rule_experience_reuse/NOTES.md#pro-question-2026-09-20-abc-admission-conditions-and-minimal-discriminators),
under the umbrella question's `### Answer`, marked saved from chat. I fetched that exact
commit: its parent is the pinned question source `f3fe65778da4e58fb5eb0ca7a34f9c6896c9c945`,
and its only changed file is A NOTES. The extracted complete answer hashes to
`0b11d7216f66daea006f943a239aea6237d2a20f3fca4b2c6f21fb803df2a429`, matching the transport
file I read. Removing only its final LF gives the driver's reported
`35ace3a0d98a55c311a28f6eb56d212752c02467f80bb783b757bc2ac013b8b3`; the apparent hash
discrepancy is reconciled, not a changed answer. Root reported native `DELIVERED`, originally
empty Answer, unchanged question/rest and no repeated Send. I made no A-file edit and do not
duplicate the umbrella answer in C's unused answer slot.

Pro used C's pinned `4ef39c08ae55c6dd623718b4072a7ddcc9b9e913`, so it read C05's result and
consultation input but not my subsequent `176a5cbc7` narrowing. It explicitly could not read
C05 episodes.jsonl, only sampled the update log, and did not independently inspect binary
traces/checkpoints. I accept that disclosure: the answer is scientific advice and a direct
summary/code reading, **not another raw-data audit, fit or empirical replicate**. My prior
full C05 read remains the source of those raw checks. I rechecked the cited C05 summary
values, eighteen conditional actions and causal view, and matched the C03/C04/CADC numbers
to their published local records; no factual C discrepancy was found.

The two consequential primary-source boundaries also check out on rereading. SchedNet
jointly trains message encoding, action selection and scheduling weights and specifies
medium-access rules; it is not a fixed-skill timing-only comparison or a free priority
channel. See [sections 3.1–3.3 and appendix D](https://arxiv.org/html/1902.01554v1).
Soleymani et al.'s result uses its Gauss–Markov/quadratic-control setup, causal information
sets and a one-step channel, with jointly optimized triggering/control; its continuation
value does not imply extra learned value for our frozen receiver. See
[sections II–III, equations 10–12 and Theorem 1](https://people.kth.se/~kallej/papers/Value_TAC2023_Soleymani.pdf).

### C-specific response to the advice

1. **Adopt the four-way separation.** C05 is a constructive timing-value opportunity with
   legal representation and one exploratory training history realizing it. Initial value4
   becomes5.322222222, and exact greedy regret to the transparent rule is0 on the finite
   context support. This neither establishes multi-seed reliability nor incremental
   learned-package value. The strong VOI rule, not the restricted age/change family, stays
   the implementation choice. The existence answer is not withdrawn by the pause.

2. **Adopt the adverse evidence and information limits unchanged.** The q=0 control removes
   the restricted-rule residual; the paid w contributes only1/18 task unit independently
   when q is known. Context was already paid by every C05 arm, so no package-purchase value
   follows. C03's successful proxy repair lost9/5 jobs, C04's stage rule removed the learned
   remainder, and CADC's adverse single pair remains adverse. Silence decoding, unpaid
   receiver intent or future flip input would change the tested problem. Pro did not read
   the later eight-byte allocation example; that remains my bounded cross-quota analytical
   comparison, not adviser-verified evidence and not a new C05 primary.

3. **Modify the post-C05 narrowing's possible over-strong reading.** A transparent posterior/
   plug-in value route *exists* does not mean finite data and computation have already
   solved a new target decision. The previous unknown-q derivation is conditional on its
   declared information and model; it is not a reason to dismiss ordinary learned risk
   estimation or another competent existing method. Re-entry need not break the algebraic
   `wX-4q` form, require endogenous multi-agent coupling, invent a new algorithm, or first
   prove a positive headroom gap. A target-sensitive finite-estimation question can itself
   justify an ordinary-method comparison. This is the substantive clarification I adopt
   from Pro; it does not create an empirical gain missing from the current data.

4. **Retain the suggested q(z) condition, but do not adopt it as a ready experiment.**
   Pro proposes a locally observed regime z with unknown q(z), estimated from common lawful
   history, and a charged timestamped request arriving before fixed receiver decisions.
   The useful intermediate error is placing q(z) on the wrong side of wX/4; the native
   prediction is avoidable loss from choosing the wrong transmission time, not merely lower
   calibration MSE. This remains inside a transparent learned-predictor-plus-VOI baseline.
   Pro explicitly supplies no actual target interface, existing feedback source/cost or
   action-support evidence. C01 has constant .75 progress and uniform job weights; C05 gives
   calibrated q and redraws it independently each cycle. Neither currently supplies the
   proposed new finite-estimation problem. I therefore reject an immediate successor fit
   from this example alone, **not** the possibility or legitimacy of such future research.

5. **Adopt the support and comparator requirements as scientific design, not new gates.**
   A later target can use genuine early/late action support or an identified conditional
   model from common data; two different historical paths are not observed counterfactuals.
   A candidate and the transparent predictive/value reference must share calibration data,
   feedback/reward rights, model access, delay, full request/header cost and tuning exposure.
   A worthwhile new question need not demonstrate victory in advance. No duplicate
   comparator identical to the candidate, exhaustive rule search, additional Pro approval
   or mandatory architecture change is needed.

### Final boundary

**Formal scientific decision: suspend further experimental investment in
`skill_information_refresh` at the present boundary.** This replaces the earlier wording
"prepared pause" or "idle": no successor training, simulation, rule sweep, confirmation
or repeated adviser request is selected. Retain the transparent stage rule for the original
crossing comparison and transparent VOI for C05, with all positive and adverse evidence.
The reason is that C05's actual decision calculation is solved and the proposed new
finite-estimation target mapping is not established—not that every ordinary route always
solves every task, that lawful refresh value is absent, or that Pro permission is missing.

The specific re-entry is a target-grounded legal observation/feedback chain in which an
unknown, estimable quantity affects the relative native value of the fixed action
opportunities, plus a bounded comparison against the strongest same-information predictive/
value rule at declared data and compute. The q(z) threshold example is one possible form;
it is not a new toy to manufacture solely to keep this direction running. A concrete new
question may change the investment judgment without first proving a gain. Until then there
is no unresolved producer, observation task or approval dependency to wait on.

This is a direction-investment suspension, **not an owner-wide pause, new RESEARCH state or
archival decision**. Root owns the shared index and can record `exploring` with experimental
investment paused and this re-entry condition. Pro's `MATERIAL_DISSENT: no` is consistent
with this decision but is not the evidence that establishes it. This adoption adds zero
fits, updates, simulations or launches; C remains at four exploratory fits, 1,277,952
training ticks, 2,048 updates and 3,591,672 total team ticks across the recorded hosts.
No code, results, A/B answer or shared-control file was changed.

## 2026-09-20 — Final feasibility verdict: NOT_VIABLE_CLOSE

### Decision on the current direction

**NOT_VIABLE_CLOSE. Recommend closing `skill_information_refresh` and removing it from
the active direction set.** This is the DM's current-scope scientific investment verdict,
not a request to retain an active direction while waiting for a new target. It supersedes
the idle/prepared-pause language in `176a5cbc74c16a7343e7856068594326e1a29163` and the
direction-investment suspension plus open-ended re-entry task in
`491504442972ee0d37c0055767c4ae5831ee04ca`. Those entries remain as historical reasoning;
their proposed standing is no longer the decision. Root owns the shared RESEARCH index
and should record this closure using the existing archived-direction vocabulary.

The original question was whether learning **when** to refresh has independent practical
value with skills, termination, message content and communication access fixed. The
available evidence establishes a lawful timing-value opportunity, but does not establish
an independent learned-scheduling problem worth further investment in the current scope.
On the constructed host that isolates receiver-relevant value, a transparent VoI rule
already solves the timing decision. On the original coupled crossing host, the tested
learned policies do not improve on the strongest observed same-information stage rule.
There is no selected next comparison using an already available legal target interface
and feedback stream that changes this judgment.

### Evidence that determines the verdict

- **C01–C04: no residual practical learned advantage.** The three independent training
  histories either reproduced polling or produced small conditional improvements over
  AGE_CHANGE/POLL. On C04's common evaluation panel, ACTIVE_FIRST exceeded the frozen
  learned policies by 12, 1 and 1 completed jobs respectively. This is an empirical
  comparator result, not a proof that ACTIVE_FIRST is globally optimal. C03's targeted
  stale-release repair reduced its intended stale-wait intermediate but lost 9 and 5
  jobs in the two affected learned policies. Thus fresher information or fewer stale
  waits cannot stand in for native usefulness. The complete readings remain in
  `43d271914c20b1b3c496153a902d41a2e42ceef2` and the bound C01–C04 run directories.
- **C05: the lawful opportunity is absorbed by transparent VoI.** With the mandatory
  paid receiver context, fixed decoder, one data send, fixed delay and two available
  send opportunities, the native advantage of early over late is exactly
  `Delta = w * X - 4 * q`. Sending early iff `Delta > 0` (late on ties) optimizes this
  declared decision. One exploratory learned history attained the same greedy choices
  on all 18 contexts and exact mean reward 5.322222222, compared with 5 for the best
  restricted stage/age/change rule. It did not exceed VOI. The positive existence and
  narrow learnability result stand; multi-seed learning reliability, extra practical
  value of learning, or the value of purchasing context were not established. Source
  `d8680026026b06f0861601839444392c452e8c20`, collected/read results
  `4ef39c08ae55c6dd623718b4072a7ddcc9b9e913`.
- **The adverse predecessor is not redeemed.** Archived CADC's learned communication
  package remained worse than polling in its recorded comparison (net difference
  -0.013354921301). C's collision-free access and fixed behavior are a different
  object. Neither C05's positive timing result nor its trained imitation of VOI
  overturns that package-level contrary evidence.
- **Pro supplies no presently executable exception.** The complete delivered answer at
  `8904327f9598d4896cb9425550f84584deaa902a` (parent equals the committed question source;
  only the assigned A answer subsection changed) has been read and adopted with the
  qualifications in the preceding entry. It supports no successor fit on solved C05.
  Its unknown `q(z)` example did not supply an existing target observation/history/
  feedback mapping with an unresolved, practically relevant comparison against the
  strongest same-information posterior-plus-VoI reference. Advice is not a new replicate
  or independent empirical evidence.

### Why this closes the current question rather than postponing it

Hiding `q` in actual C05 does not expose a justified new learning opportunity: `q` is
independent across cycles, so previous cycles do not identify the current hidden value.
Under the unchanged two-action contract the strongest transparent decision uses the
conditional flip probability in the same VoI expression. Giving the learner current
`q`, a request, a priority or a receiver state unavailable to that comparator changes
the information problem; such signals are not free. Replacing the host with a new
unknown-regime or new target-feedback construction solely to maintain an active
direction is not the original current-scope comparison. No such successor is selected,
and none is left as an open admission, investigation or re-entry task.

This closure does **not** assert that all learned communication scheduling is impossible,
or erase lawful refresh value. It preserves the narrower result: recipient commitment,
next action opportunity and uncertainty can matter, but in the available isolating host
their value is captured by the transparent rule; the coupled host supplies no observed
learned increment over its strong simple reference. These fixed scripted-host findings
also do not establish benefits for current HMASD learned skills or a UAV deployment.
Those scope limits are limits on the claim, not a reason to keep this direction active.

No additional fit, seed, threshold search, architecture change, simulation or Pro request
is authorized by this conclusion or planned by the DM. All accepted runs are collected
and read; there is no pending scientific producer, launch, approval or adviser dependency.
Cost is unchanged: four exploratory fits, 1,277,952 training team ticks, 2,048 optimizer
updates and 3,591,672 total team ticks across the declared hosts. This entry adds zero
result execution. Preserve the notebook, code and run evidence; perform no destructive
cleanup. The only remaining coordination action is Root's shared-index closure update,
not further direction research.

## 2026-09-21 — Independent direct DM initialization and selected multi-step question

The owner's explicit new-task instruction activates C alongside B and VSP-03 and
supersedes the prior current-scope archival/investment decision, without changing any
old result. Direct DM task `01a0c348-428c-7f01-bd8b-121d69543032`, host `local`, works
in `/home/fires/.codex/worktrees/f987/hmasd-wsl` on `codex/c-multistep-send-value`.
There is no new Root or intermediate DM, no reporting relationship to another task,
and no App message/acknowledgment/forwarding loop. This DM publishes its own scoped
standing and evidence. The one-time owner activation is being published separately;
until canonical control contains it, only reading, design and engineering proceed.

Loaded and adopted the current AGENTS, constitution, direction-manager responsibility
body, scientific-tools and research-engineering methods. Fits are measured cost with
no allowance or runtime window. Prospective arms/seeds/horizon and no score-driven
extension remain. Confirmation would need its actual claim and 3–5 fresh independent
seeds per learned arm. Jev Pro and bounded internal helpers remain available.

Inherited this complete notebook verbatim through the previous final entry from
`089e21f36fd51716bf15efde1abb3e4aca0100c5`, plus its C01–C05 code and correctness tests;
no prior experiment is restarted. All historical governance/routing prose above is
historical, not a second rulebook. Read the complete Portfolio Answer and Decision at
`b6093d211fa33a81d05d490ffa5bc920f43605eb:docs/research/RESEARCH.md`, including its
C-specific multi-step proposal and CADC correction. The Pro Answer evaluated a different
CADC proposal; it is not specific advice on the comparison proposed below.

Current explanation: C03's freshness repair reduced stale waits while losing 9/5 jobs;
C04 ACTIVE_FIRST beat the three frozen learners by 12/1/1 jobs on its panel. Those are
strong constraints on the old package, not stage-rule global optimality. C05 solved its
known two-action law with Delta=wX−4q and one learner matched all 18 actions and exact
479/90; no attempt to exceed that optimum is selected. Hiding its iid q is not an
identifiable history-learning problem. C's cumulative old work remains four fits.

The first concrete next step is to construct a lawful belief over hidden peer progress
in the original CrossingHost, then compare send-now versus retain-quota using task
completions across future sending opportunities and a receiving skill boundary. Preserve
12/16 periods, fixed gate/project/choose_route, H96, uniform distance law, .75 movement,
one eight-byte packet per sender per eight-tick frame, alternating slots, one-tick
delivery and mandatory last-slot send. No receiver decoder, reward, communication charge
or task population change. Complete jobs are primary; conflicts, waiting and bypass
choices expose tradeoffs. No current hidden peer state, diagnostic oracle or future
exogenous values may enter policy inputs or synthetic rollouts.

Selected work mode is ordinary transparent model-based prediction; a neural scheduler
is not required. Both predictive comparators receive the same known transition model,
lawful history and belief approximation. Model access is explicitly a shared resource,
not an inferred real-world learned model. The strongest simple reference must include
reasonable development-only calibration and ACTIVE_FIRST. Full belief/rollout work is
cost even with zero fits. The forthcoming focused Pro consultation can change the
nearest-decision comparator and finite rollout design; it is advice, not approval.

L0 for initial independent engineering: owned paths are new
`experiments/candidates/skill_information_refresh/c06/`, mirrored tests and eventually
`scripts/run_sir_c06.py`; frozen C01–C05 code stays byte-identical. First deliverable is
an immutable local record with raw delivered packet/time, own current state, own send
history and public clocks, plus a tested small finite-state physical filter. All arms
may retain own observations each tick (a declared common richer local-history cadence);
this adds no communication or receiver information. Test invariance to unobserved peer
state/future world randomness, delivery order, boundary resets, collision conditioning,
quota reconstruction and synthetic-rollout independence. High-risk filter/evaluator
semantics receive independent review. No result-bearing execution before prospective
comparison, published exact source and native admission.

## Pro question 2026-09-21 C06 multi-step send value and nearest-decision comparator

Conversation: Jev account route; local operation key only in shared records. This is a
new C-specific consultation, not a resend of the old umbrella or unused C05 question.

Question: **What is the smallest scientifically defensible comparison of lawful
multi-step send-now value versus a competent nearest-receiver-decision VoI rule in
the unchanged CrossingHost?** This decides the exact comparator/continuation target,
not whether the owner may activate C. The owner already authorized actual research and
selected this route. Ordinary planning can be the final method; novelty, a neural win,
positive headroom and an already implemented batch are not requirements.

Standing/evidence: use the independent-DM initialization immediately above and C03/C04/C05
readings in this notebook. In particular, proxy freshness can cost completed jobs. The
complete Portfolio review at `b6093d211fa33a81d05d490ffa5bc920f43605eb` supports this owner
choice, but its Pro Answer assessed CADC fixed RR, not this new crossing comparison.
No new scientific run, fit or policy evaluation has been performed for this question.

Concrete model and lawful interface: read ALL of
`experiments/candidates/skill_information_refresh/c01/host.py` at source_sha. Both agents
observe own state each tick, their own sent payload/time history, raw *delivered* peer
payload/time, own quota and public clock/identity. Raw cache is already delivered content,
not a new message. A receiver's cache of this sender is reconstructible from own send
history because delay=1 and no loss; the receiver's actual progress is hidden. At a
sender's slot, a peer send at t−1 has already arrived; a peer token spent in this frame
can then be inferred from its latest delivered timestamp. Preserve all opportunities,
payloads, dynamics, gate, route choice, forced send and H96. Task completions, not oracle
gate agreement, are the reward. No online access to host.worlds, current peer state or
future random values. Shared known laws (.75 independent advances, uniform job distances)
are a declared modelling resource for BOTH value rules, not free only for the candidate.

Proposed estimator and intervention: maintain a finite distribution over hidden peer
(stage,distance,cross_left,route) from delivered packets and own observed physical history.
A practical first filter may condition packet contents and own physical transitions but
ignore the likelihood of state-dependent send timing/silence. If used, call it an
approximate physical belief, not an exact Bayesian posterior; share it between rules and
retain contradiction/fallback counts. At each unforced available slot sample latent peer
states from that distribution, construct an independent model state with own state and
legally reconstructible caches/quotas, and compare root SEND versus HOLD using paired
synthetic future random streams unrelated to evaluation worlds. After the root action,
both branches use the same fixed ACTIVE_FIRST continuation for both agents, with the
normal quota rules. Deploy the selected rule receding over its own resulting trajectories.
This is finite rollout policy improvement over a specified continuation, not exact
optimal control or a claim that the continuation equals the deployed policy.

Provisional candidate: team completed-job sum through min(t+32,H96), enough to pass the
next peer skill boundary and intervening send opportunities except true episode end;
no terminal value beyond that truncation. Value difference uses 32 paired synthetic
trajectories per decision, common sampling budget with the short rule. A positive result
would be a conditional known-model, finite-computation package result; it need not identify
horizon alone because deployment changes histories. Save per-decision values/SE/actions
and native trajectory/packet accounting so lack of separation is readable.

Comparator decision still to settle: a naive one-tick gate-agreement score is disqualified
by C03. The strongest simple *nearest decision* rule should price the native consequence
of the first receiver gate/route decision changed by the arriving packet, while using a
development-fitted shadow price for consuming the quota. A concrete implementable default
is paired root SEND/HOLD rollouts through the end of the receiver's first affected
commitment: if arrival t+1 is a peer boundary, include the newly starting job; otherwise
include the current job. Score complete TEAM jobs over that short interval, with the
same ACTIVE_FIRST continuation and belief. This is honestly a nearest-commitment VoI
approximation, not exact one-step VoI. Please challenge whether that is already too
multi-step, or is a stronger and clearer simple primary than a literal first-decision
rule whose value needs an arbitrary surrogate. No weak baseline is owed to make the
long horizon win. ACTIVE_FIRST remains an untuned zero-model reference.

Provisional exploratory cost, to finalize after advice before implementation acceptance:
zero training fits/optimizer updates for shared known-model planning. Equal development
selection rights for each predictive arm: four declared additive send thresholds
{-0.05,0,0.05,0.10} completed-job units on 64 common development worlds, then only the
selected short/long rules plus ACTIVE_FIRST on 256 fresh common worlds, H96. This is
8*64+3*256=1,280 real modelled episodes / 122,880 actual host ticks, plus intrinsic nested
rollouts. Conservative upper bound: at most 72 optional calls/world, 32 particles, two
root branches, 32 synthetic ticks/call for long and <=17 for short; count actual branch
transitions and full wall/RSS, not just zero fits. Rule threshold selection is explicit
outcome exposure; it is not parameter learning or free optimization. Seeds/streams and
a finite action tie rule will be frozen prospectively. These are costed options for one
exploration, not confirmation or a frozen launch yet.

Predictions: the long rule sometimes retains a token that short value would spend,
causing a later packet to alter receiver routing/passage; if those tradeoffs matter,
complete task counts improve without hiding extra conflicts or expiring jobs. ACTIVE_FIRST
may already be sufficient; shared belief error or Monte Carlo noise may erase the planned
value differences. Distinguish these explanations where the saved values and behavior
actually do so. Do not assume exact-model planning must improve when deployed receding,
or treat a handful of counterfactual local deltas as a policy-level gain.

Context (paths inherit source_sha unless explicitly pinned): constitution sections 1–6
and 8; scientific-tools sections Explore, Update the working explanation, Comparators,
Statistics, Cost and exposure, and Pro; research-engineering Checks and review and
Execution and admission. Current owner task authorization and constitution supersede
historical archive/Root/allowance wording, with old scientific contracts unchanged.
The current branch may not yet include the separate activation publication; no result
runs occur until native canonical controls agree. Use the actual code and supplied
notebook; no recursive audit of unrelated directions is requested.

Return: a focused critique with MATERIAL_DISSENT yes/no, consequential sources actually
read and gaps, the cleanest comparator definition and belief/continuation caveats, a
bounded useful first observation, and any material cost/design correction. Explain what
would strengthen/weaken the multi-step-value account and which outcomes justify adopting
a transparent rule. A failed finite planner does not prove no lawful timing value.

Constraints: no experiments and no edits outside this question's empty `### Answer`
subsection at `docs/research/candidates/skill_information_refresh/NOTES.md` on branch
`codex/c-multistep-send-value`. Read reasoning at the supplied immutable source_sha;
fetch the latest writable target blob and its actual SHA, preserve all other bytes,
and stop on overlapping edits. Report the actual answer commit; if GitHub writeback
fails return the complete answer in chat, not just a receipt, SHA or link. This DM
reads the full answer and chooses; Pro introduces no permission layer.

### Answer

Saved from chat (complete fallback answer; no GitHub answer commit):

GitHub 读取正常，但本会话没有可调用的文件更新或提交接口，因此未写入，也未产生 Answer commit。 我检查了指定分支上的目标小节：本次读取时 C06 的 ### Answer 仍为空，目标文件的实际 blob SHA 为 66cb074a1faeb5c869600a06f64b8842542416e2。这是文件对象 SHA，不是答复提交。以下按附件指定的备用方式给出完整答复；仓库内容没有被修改。 

hmasd-pro-question-c06-multiste…

Answer
一、判断与实质分歧

建议保留这项已获 owner 授权的研究，采用三个臂：LONG32、修正后的 NEAR_COMMIT 和不调参的 ACTIVE_FIRST。两个预测臂共享合法物理信念、已知模型、32 对合成轨迹及 ACTIVE_FIRST continuation；只在开发集选择各自的发送阈值。普通透明规划可以直接成为最终方法，不需要再附加神经网络。

MATERIAL_DISSENT: yes，范围有限。 我支持研究路线，也支持用承诺期内的完整任务后果代替一步 gate-agreement；实质异议是：“到达不是边界就截到当前接收者任务结束”不总是一个合格的最近决策参照。它可能在最近一次可受影响的接收者决策发生前就停止。 修正这个问题后，短规则有时也需要接近 32 ticks，原来的短规则 ≤17 成本界不再适用。这是比较器与计费修正，不是重新审批 C 的激活。

历史证据给出的约束保持不变：C03 去掉了大量 stale-release waits，却少完成 9/5 个任务；C04 的 ACTIVE_FIRST 在其面板上分别比三个冻结学习策略多完成 12/1/1 个任务；C05 的一个学习历史匹配透明 VOI 的全部 18 个条件动作与精确值 479/90。因此，不能把 freshness 当目标，也不能把击败弱规则当作额外方法价值；但这些结果都没有证明 ACTIVE_FIRST 在 CrossingHost 全局最优。

我也区分了 Portfolio 的两个层次：其完整 Pro Answer 评估的是 CADC 固定 RR 下的 send/skip 提案；后续 Decision 才明确发展原 CrossingHost 的多步配额取舍。前者不是已经覆盖 C06 的专门建议。

二、最干净的主比较：最近可受缓存影响的机会，随后计完整承诺期结果

为什么当前默认切点需要修改。 在代码中，接收者处于 DONE、已经 CROSSING，或者当前执行 BYPASS 时，新缓存未必还能影响当前任务的物理动作。BYPASS 的 gate 不受 peer cache 阻挡；DONE 和 CROSSING 不再通过 gate 选择是否进入当前 crossing。这时最近有意义的接收者选择可能是下一个技能边界的 choose_route，而不是当前任务内的某次 gate 调用。

一个由代码允许、但不是本次实验观察的具体情形是：在 t=10，sender 0 和 receiver 1 都已 DONE，本帧 sender 0 的 token 尚未使用。SEND 会发送旧任务快照，它在 sender 的 t=12 边界过期，同时耗掉本帧 token；HOLD 后采用 ACTIVE_FIRST，则可在 t=12 新任务开始时发送新快照，t=13 到达，并可能改变 receiver 在 t=16 的选路。原短规则截到 16，恰好把这次最近可改变的选路排除。短评分为零不能解释为“最近决策无价值”，更不能直接把长规则的差异解释为更远期的多决策收益。这一例子只指出截断缺陷，不声称哪个选路最终更好。

我建议如下定义 NEAR_COMMIT：最近可受缓存影响的机会所对应承诺期的 rollout。

令当前 sender 为 i，receiver 为 j，其固定周期为 P
j
	​

∈{12,16}，到达时刻为 a=t+1。对每对合成样本，从共同的合法根状态出发，寻找 a 之后的第一个机会 τ：

接收者的技能边界，即一次 choose_route；或者

接收者处于 SHARED、APPROACH、distance 为零且剩余时间至少两 tick 的 gate opportunity。是否实际被挡住不影响它作为机会的资格。

这不是寻找“第一次恰好出现有利收益”，也不是无限追踪到两个动作终于不同。它是预先固定的、可能受缓存影响的机会定义。若到达恰好在边界，那个新任务的 route choice 就是该机会；若当前任务已经没有这样的 gate，就等到下一边界。

在本题固定 ACTIVE_FIRST continuation 下，根发送首先只改变接收者缓存及发送配额；在第一个上述接收者机会之前，两分支的物理前缀相同。因此可以给这一对样本使用同一个 τ 和同一个终点，而不是给 SEND/HOLD 各挑一个更有利的停止时刻。实现时应检查这一性质，不把它扩展到读取缓存的任意 continuation。

短终点定义为

T
S
	​

=min(96,P
j
	​

(⌊τ/P
j
	​

⌋+1)).

若 episode 结束前没有上述机会，则取 T
S
	​

=96。两分支均计 [t,T
S
	​

) 内的完整 TEAM completed jobs。这样，边界处开始的新任务包括在内；截止时刻的新任务不再贡献区间内奖励。它仍不是精确的一步 VoI，而是对最近一个决策相关承诺期的任务后果估值。

长规则保留

T
L
	​

=min(t+32,96),

同样无额外 terminal value、无折扣、无人工 freshness 奖励。

这个修正不需要扩大 LONG32。 最近的 route 边界一定会出现，所以短窗口最多到下一接收者任务结束，满足

T
S
	​

−t≤2P
j
	​

≤32.

某些根上 T
S
	​

=T
L
	​

，两个评分自然相同；这应作为“此处没有额外视野差异”报告，而不是再缩弱短规则或延长长规则来制造分离。上述定义和边界推导依据冻结的 gate、choose_route、固定周期及 tick 顺序。

因此，本研究最准确的问题是：

超出最近可受缓存影响的机会所对应承诺期后，额外的任务价值预测，是否在声明的有限计算量下改善完整部署表现？

它不是“多步方法击败真正一步方法”，更不是“规划击败所有 VoI”。

三、合法信念与状态重建：最重要的是时间对齐，而非滤波器名称

首先固定根状态所在的执行相位。 CrossingHost 每 tick 先交付 pending 包，再重置本帧配额，再做边界任务初始化和选路，之后才提供 scheduler view。发送复制的是这个相位的快照；随后才执行 gate、approach movement、碰撞和完成更新。因此，当前根上的 route 已经选完，本次发送不能倒过来改变它。

raw packet 必须按发送时间而非到达时间同化。 在 s+1 收到的包描述的是 s 的发送前物理状态，不是 s+1 的当前 peer 状态。正确做法是对 s 的状态施加包内容约束，再传播 s 的物理转移，并处理 s+1 的可能边界重置。把收到的 payload 直接钉成当前状态，会错过一次移动、碰撞、穿越倒计时或新任务重抽。固定 project() 是接收控制器的缓存投影，不是真实 peer 转移模型；规划信念不能把它当成无误差状态预测。

缓存和配额可以合法重建，但需要明确来源。 receiver 持有的本 sender 缓存来自自己的已发送历史，且只包括已经到达的发送。当前 sender slot 上，peer 在 t−1 的发送已经交付，因此 peer 本帧 spent 可由最新已交付时间戳是否落在当前帧判断；不能把上一帧末尾、刚到达的包误算成新帧 token 已花掉。缺包、过期和未发送状态都应显式表示，不能填入真实 peer 值。当前题目允许双方每 tick 保留自己的观察，这是一项共同的局部历史接口扩展，不是新增接收信息，也不改变固定接收控制器。

对自身物理转移的条件化不能偷用原因标签。 例如，自身进入 DONE 可能来自正常完成，也可能来自碰撞；某些前态可以区分，另一些不能。滤波器必须对所有与合法自身观察相容的隐藏转移求和，不能读取 evaluator 的 conflicts、team reward 或真实 peer trajectory 来选择隐藏原因。

采用题目提出的“忽略状态依赖发送时机/沉默似然”的版本是可接受的第一近似，但必须称为 approximate physical belief。它不等于真实部署策略下的精确 Bayesian posterior。另一方面，忽略这类似然不意味着可以忽略已经交付的包、确定的配额事实或自身物理转移。两个预测臂共用同一近似与 fallback 规则，但因为部署轨迹不同，它们后来收到的历史和形成的信念当然可能不同。

首版可以保留这个小有限物理状态空间的完整支持；32 个 rollout 样本不要求同时把滤波器也压成 32 粒子。 应记录零归一化质量、矛盾及 fallback 次数。若未裁剪的物理支持出现硬矛盾，不应直接用“忽略沉默，所以正常”解释；优先检查时间对齐、边界和碰撞语义。fallback 不能使用真实 peer 修复信念，且其执行轨迹与代价必须留在结果中。

合成模型只能从这些合法重建量和抽样 latent state 初始化，不能复制真实 host 后仅覆盖几个明显隐藏字段。另一个具体工程陷阱是：冻结的 Worlds.make 要求 horizon 为 48 的倍数；17/32 是 H96 内的 rollout 截断长度，不是修改冻结宿主 horizon 的理由。t=96 不再执行 _prepare_tick，最后一个强制包可能仍 pending，不能补交付或启动额外任务。

四、发送价值、阈值与 continuation 应怎样解释

每个 unforced available 根使用 32 个独立的“latent peer 样本＋合成未来”对。每对 SEND/HOLD 共用 latent state、未来 movement draws 和任务距离 draws，且这些随机流与真实开发/最终世界的生成流分离。两个 horizon 在共同前缀上也使用相同样本。

对 K∈{S,L}，记

d
k
K
	​

=G
k
K
	​

(SEND)−G
k
K
	​

(HOLD),
Δ
K
	​

=
32
1
	​

k=1
∑
32
	​

d
k
K
	​

.

这里 G 是规定窗口内 completed TEAM jobs。误差条使用配对差值：

SE
(
Δ
K
	​

)=
32
s
2
(d
K
)
	​

	​

,

不能把两分支当成独立样本后相加标准误。这个 SE 只描述给定近似信念和 continuation 的有限 Monte Carlo 误差，不覆盖信念偏差、截断误差或部署时的 continuation mismatch。32 次全为零也不证明真实差值为零。

保留四个开发阈值

λ∈{−0.05,0,0.05,0.10},

发送条件明确为 
Δ
K
	​

>λ，相等时 HOLD；无 quota 时不查询规划器，forced slot 按原规则发送。开发配置之间的平局规则也应预先固定。

这些 λ 应称为加性决策校准，而不是全部称为 token 的真实影子价格。 HOLD 分支已经通过未来 ACTIVE_FIRST 发送，计入了窗口内保留 quota 的部分机会价值；再扣一遍“完整未来 token 价格”会重复计费。负阈值也不是物理通信成本。它们可以补偿截断或有限估计误差，但不能因此改变任务奖励。所有臂仍必须是每 episode 24 包、192 字节、原有 96 个可见 slot outcomes；不能另加请求信道。

在这里，单轨迹 completed jobs 是整数，所以等权 32 样本的均值差以 1/32=0.03125 任务单位变化。阈值网格和零附近决策的分辨率应如实解释，不把小数点后的多位输出当作高精度估值。

最后，两分支在根后都使用 ACTIVE_FIRST，实际部署却由双方不断重新规划。这是相对于固定 continuation 的有限 rollout 改进尝试，不是求出了实际部署策略的精确 Q。补充核对的 Bhattacharya 等人 POMDP rollout 正文明确区分基策略价值、截断与 terminal approximation，其理论表述还要求能恢复真实 belief 的充分统计量。C06 的近似物理信念、零终值截断和双方重规划不能直接继承“不劣于基策略”的保证。
arXiv

五、一个有界且有用的首次观察：检查远期增量是否真的改变选择

我不建议另加一个必须“先通过”的 pilot。在已计划的开发执行中，利用 λ=0 的 LONG32 轨迹，按预先固定、与评分无关的抽样方式保留最多 64 个 optional 根。 例如，对所有遇到的根按固定的 (world,t) 哈希取样。这个样本描述的是该开发策略实际遇到的历史，不是所有合法状态的无偏普查。

对这些根，从同一套 LONG32 轨迹中读取短窗口累计值，无须另加 rollout，保存：

Δ
S
	​

,
Δ
L
	​

,
Δ
tail
	​

=
Δ
L
	​

−
Δ
S
	​

,

以及配对差值、SE、机会类型、短终点、quota、根动作和后续包时刻。这里的 tail 是超过最近机会承诺期后的模型内收益差，不是已识别的配额因果贡献。

最有辨别力的读数不是“长规则发得更晚”，而是：在相同合法根、相同信念和样本上，远期项是否使发送排序翻转；预测中被保存的 token 是否确实用于不同的后续快照；它是否改变 gate/route，以及完整任务数。先把这些局部模型预测与最终真实部署轨迹的包、物理决策及任务结果并置，再判断解释得到多少支持。

已有 32 对样本可以按预写的前 16/后 16 做粗略方向一致性检查，不增加采样量、不据此事后扩展 batch。若大部分翻转都集中在零附近且半样本符号不一致，现有读数只能说明有限 MC 决策不稳，不能支持精细的远期机会分配解释。若需要区分信念误差，评估器可保留策略不可读取的真实状态支持/校准诊断；没有这类证据时，就不要把所有负差值归咎于 belief error。

这些局部反事实依然只是声明模型和 continuation 下的诊断。最终收益必须来自各臂按自身历史完整部署得到的原生完成任务数，不能由几个正的根差值代替。

六、成本、开发选择与统计范围

原外层计数正确：

8×64+3×256=1,280 episodes,1,280×96=122,880 host ticks.

每个预测臂有 4×64+256=512 个 episode。每帧两 sender 各最多三个非强制机会，12 帧给出每世界最多 72 个 optional planning calls。按题目给定的 32 样本、两个根分支计算，内部工作上界如下；这是前瞻整数核算，不是实测执行量。

内部 rollout 工作	保守 synthetic tick 上界
LONG32	75,497,472
原默认短规则，按 17 ticks 计	40,108,032
原两预测臂合计	115,605,504
修正后的 NEAR_COMMIT，按最多 32 ticks 计	75,497,472
修正后两预测臂合计	150,994,944

所以修正后的内部转移上界约为外层 host ticks 的 1,229 倍。实际工作会因提前用完 token、较早短终点及 episode 截断而减少，但不能以“零拟合、只有 1,280 episodes”描述它的主成本。滤波传播、随机数生成、状态复制、记录、初始化及读取开销还未包括在该转移上界中。wall/RSS 尚未知，不能从 C04 的几秒钟外推。科学方法明确要求计入这种算法内生的嵌套搜索。

保留一次有界探索即可。两个预测臂分别在同一 64 个开发世界上按实际完整 completed jobs选择一个阈值，随后冻结，在 256 个新的共同世界上比较选定的 LONG32、NEAR_COMMIT 和 ACTIVE_FIRST。主比较是 LONG32−NEAR_COMMIT，同时完整报告各自相对 ACTIVE_FIRST 的结果；不能最后发现另一对更好就改换主比较。阈值单位是任务数，不是除以 14 后的 service fraction。

共同的 32 样本预算是抽样权利匹配，不是计算量匹配。应报告实际 planning calls、各臂 branch transitions、过滤工作、完整 wall、CPU 与明确作用域的 RSS。参数更新为零，但阈值选择是有 outcome exposure 的优化工作，不能隐藏。高风险滤波/评估实现采用已有的独立工程审阅要求；不新增 Pro 批准或强制 profiling 实验。

统计上，这里没有新训练历史。最终 256 个世界可以在明确的独立外生世界和规划随机流设计下，用于描述已选定规划程序在该世界律下的配对均值与不确定性；不能把根、粒子或 ticks 当成独立重复。它也不衡量重新开发选择的稳定性。反过来，不能机械要求一个零拟合规划比较制造三个“训练种子”才能开始探索；确认规则中的学习种子要求应适用于其实际学习主张。无论区间如何，当前比较都不能声称统计等价、全局最优或 UAV 效果。

七、哪些结果改变解释，哪些结果支持采用透明规则

LONG32 高于 NEAR_COMMIT，也高于 ACTIVE_FIRST，并出现预期的远期排序翻转和后续任务取舍： 这会加强“超过最近接收者机会的价值预测在此处有用”的解释。可考虑采用 LONG32，但结论限于共同已知模型、该近似信念、有限采样、固定 continuation 与实测计算代价。它不是神经学习收益，也不自动是纯 horizon 的因果效应。

NEAR_COMMIT 吸收了 LONG32 的收益，并相对 ACTIVE_FIRST 有值得保留的表现： 采用 NEAR_COMMIT 是成功的研究答案，说明最近机会的任务后果估值已足够支持当前用途。若短规则在多数实际根上也需要 32 ticks，则不能未经计量称它更便宜。

LONG32 只赢 NEAR_COMMIT，却不赢 ACTIVE_FIRST： 可以保留局部估值差异的科学观察，但没有建立新增规划包的实际使用价值。ACTIVE_FIRST 仍应是当前实现选择，而不是因“主比较正了”就采用更复杂的规则。

两预测规则与 ACTIVE_FIRST 接近或更差： 结合日志区分没有动作分离、MC 不稳、近似信念问题、局部预测未转化为完整部署收益，以及明确技术错误。技术错误不算科学负结果；其余结果可以支持结束本次有限规划包，而不证明合法刷新价值不存在。C05 的有界存在结果仍保留。

尤其应把冲突、等待、BYPASS 和过期任务留在完成任务数旁边。等待增加不自动有害，freshness 改善不自动有益；C03/C04 已经使这个区别成为本题的实质约束。

八、实际来源与信息缺口

推理使用附件指定的不可变来源 eeabf6b11585ccdd4420a83d379a415fdd90b7b5：已读取 C06 完整问题、紧邻初始化说明、C03/C04/C05 指定读数与解释；完整读取 C01 host.py；读取 constitution 第 1–6、8 节，以及指定 scientific-tools 和 research-engineering 方法。治理上采用当前 owner 任务与 no-fit-allowance 规则，不把历史归档、Root 路由或 allowance 文字恢复成当前约束。

另已读取 b6093d211fa33a81d05d490ffa5bc920f43605eb 的完整 Portfolio Answer 与 Decision，但没有递归重审其中无关方向。补充方法核对使用了 Bhattacharya 等人论文第 II–III 节的实际正文，只用于限定 rollout 理论类比，不作为 C06 的经验支持。 
arXiv

指定的决策关键正文没有读取失败。 但本答复不是历史底层制品审计：C03/C04/C05 的结果数值来自已读 NOTES 的作者读数，没有重新读取并重算全部 episodes、NPZ、checkpoint 或 optimizer logs。没有 C06 实测结果、滤波校准、MC 稳定性或 wall/RSS 可以报告；没有单独验证当前 canonical activation 是否已发布，因而不声称现已满足启动条件。

本次没有执行训练、环境评估或结果性仿真。建议是：修正最近机会比较器及其成本界后，保留一次声明清楚的透明规划探索；由完整任务结果决定采用 LONG32、NEAR_COMMIT 还是 ACTIVE_FIRST，而不是预先要求长视野获胜。


## 2026-09-21 — C06 Pro reading, adoption and corrected-target L0

The complete answer above was saved from chat after one accepted Jev send, operation
key `hmasd:f781f5dfd6bea99f99983b9c7dfcc538ac9f68ad5f1d12963bad8321272d05c5`.
The transport completed and closed its owned tab. GitHub writeback was unavailable;
there is no Pro answer commit. The SHA `66cb074a1faeb5c869600a06f64b8842542416e2`
mentioned in chat is the fetched NOTES blob, not an answer commit. The complete chat
answer content SHA-256, excluding its transport final newline, is
`c47ae11c3a88734f189859e2b0f3056dd0e942072f34426b4ba58d5e0c1b28e8`.
No resend is needed. DM read the full answer and retains its material dissent.

Adopt the nearest-opportunity correction. For each paired synthetic sample, find the
first receiver cache-sensitive opportunity tau >= root t+1: a receiver job boundary
(route choice), or SHARED APPROACH at distance zero with at least two remaining ticks
(a gate opportunity, including a blocked attempt). Before that opportunity the paired
physical prefixes must agree under the common ACTIVE_FIRST continuation. Detect a
boundary before checking prefix equality because native pre-step preparation has
already chosen routes. End the near return at min(H, P_receiver*(floor(tau/P_receiver)+1));
if no opportunity precedes H, end at H. Each pair shares an endpoint regardless of
whether either action actually changes. Never search for the first favorable difference.
Name this arm NEAR_COMMIT. LONG retains min(t+32,H) with zero terminal value. In this
host NEAR_COMMIT's end is no later than LONG's; equality is an observation, not a reason
to weaken NEAR_COMMIT or lengthen LONG. The former SHORT implementation was provisional
engineering only and has produced no scientific result.

Adopt common approximate physical belief, known model, 32 paired samples, fixed
ACTIVE_FIRST continuation and development-only additive thresholds {-0.05,0,0.05,0.10}.
They are calibration offsets, not identified token prices: HOLD already contains later
opportunity cost. Retain the implemented ACTIVE_FIRST choice on exact value/threshold
ties instead of Pro's suggested HOLD tie. This preserves the simple reference where
finite MC supplies no preference, applies identically to both predictive arms, and is
fixed before results. P32 gives mean integer-return resolution 1/32; SE covers only
synthetic paired-sampling uncertainty.

Adopt a bounded diagnostic from development LONG at threshold zero: keep at most 64
optional roots by smallest SHA-256 rank of the fixed string
`C06-root-v1:<world_id>:<tick>`, independent of outcomes. Keep paired short/long returns,
near endpoints and opportunity kinds, root local record/quota, actions and future model
packet/state/wait/bypass traces. Reuse the same LONG rollouts, with no extra synthetic
trajectories or tuning. Record first-16/last-16 delta signs and paired SE; read horizon
tail reversals beside full-trajectory native rewards. These are model-based local
predictions, not causal token-price estimates or policy-level gains.

The corrected conservative upper bound for both predictive arms is 150,994,944 model
branch transitions, plus filtering, model initialization, random draws, copying and
logging. Outer scope remains 1,280 episodes / 122,880 actual host ticks, zero fits and
zero optimizer updates. Retain exact counts, wall, CPU and child peak RSS. No scientific
run has started. Paired evaluation worlds are the uncertainty unit; particles, roots
and ticks are not independent replicates.

DM checked the primary text of Bhattacharya et al., sections II–III,
https://arxiv.org/html/2002.04175v1 . Its feature state determines the exact belief, and
its rollout bound depends on terminal-cost approximation. C06's approximate belief,
finite samples and zero terminal value provide no inherited non-worsening guarantee.
This is a method analogy, not empirical evidence for C06.

L0 for one bounded correction: Implementer owns c06/planning.py and mirrored
 test_planning.py only. Replace SHORT by NEAR_COMMIT; implement per-particle first
opportunity/endpoint, pre-opportunity physical equality checking and same-sample near
prefix extraction during LONG. Return near_hold_samples, near_send_samples,
long_hold_samples, long_send_samples, near_end, opportunity_tick, opportunity_kind
as B x particles arrays (long sample keys only for LONG). Preserve selected-arm
hold/send/delta/se and complete incremental counters, counting padded batch transitions.
Optional diagnostics=True returns a diagnostics dict of native model sent/payloads/
wait/bypass step traces, each B x 2(hold,send) x particles x time [...]; no extra rollouts.
Kinds: 0=no opportunity before terminal, 1=route boundary, 2=gate. Add meaningful fixtures
for arrival during DONE whose first affected opportunity is next route, gate-first,
terminal absence, unequal per-particle endpoints, and identical near-prefix extraction
from LONG samples. DM independently owns study.py and mirrored study tests, including
blind reservoir retention and naming. No host/model law change, no result execution,
no git-index operations by helper. Independent reviewer checks this delta before DM
acceptance, prospective freeze/publication and native launch.


## 2026-09-21 — Prospective C06 exploration declaration

This fixes the first result batch before any new scientific execution. It is an
exploration of known-model transparent planning, not confirmation or a learned method.
Inputs are this declared source commit and its immutable native-launch snapshot. Use
local_linux and the configured Python/supervisor; canonical pause/lead, publication,
actual-node free memory and duplicate claims must pass native admission. Planned fresh
output: `runs/skill_information_refresh/c06_multistep_s73170_20260921/`.
Expected lead is exactly `Codex DM (independent session)`.

Object: byte-identical original C01 CrossingHost. Horizon 96 team ticks, periods 12/16,
frame 8, alternating sender, delay 1, one eight-byte packet per sender/frame with forced
last slot. Fourteen started jobs, 24 packets and 192 bytes per episode. Dynamics,
receiver decoder, gate/route policy and native completion reward do not change. Both
planning arms use the same copied lawful each-tick local history, full 22-state
approximate physical belief and known law. No hidden actual peer state or future-world
randomness enters the policy. Raw actual hidden state saved after request fixation is
for offline diagnosis only. State-dependent silence likelihood is deliberately omitted;
zero compatible physical support is a technical failure, not a true-state fallback.

Arms: NEAR_COMMIT as corrected/adopted above, LONG with min(t+32,96), and untuned
ACTIVE_FIRST. Both root interventions use HOLD/SEND, 32 common latent/noise samples and
ACTIVE_FIRST continuation on both agents, with identical quota/delivery rules and zero
terminal value. Deploy receding planning on each arm's resulting local histories.
At each optional slot request SEND iff sampled delta > threshold, HOLD iff less, and
ACTIVE_FIRST on equality. Forced and spent slots use the frozen host. Threshold offsets
are not fitted physical communication prices. Equal model access/sampling/selection
rights make a fair package comparison, not isolated identification of horizon.

True-world master seed 73170; independent planner master 973170. Development phase 20,
world IDs 0..63, for each of two planning arms at four thresholds in declared order
(-0.05,0,0.05,0.10). Choose each arm's threshold by largest mean completed jobs, ties by
smallest absolute threshold then numeric threshold. Final phase 21, fresh world IDs
0..255, evaluates only those two selected rules and ACTIVE_FIRST. Development and final
world/advance/job streams use the original SeedSequence addressing; synthetic streams
use (model_seed, phase, world_id, root_tick, 606), shared between planning arms and
thresholds but independent of actual world arrays. Batch size 16. No result-driven
change of seeds, particles, horizon, thresholds, continuation, sample size or arms.

Primary contrast: LONG minus NEAR_COMMIT completed jobs per final world. Both contrasts
against ACTIVE_FIRST are required for practical interpretation. Also read all conflicts,
waits, gate opportunities, bypass/jobs started and completion/service accounting. Save
all final world/tick local observations, beliefs, values/paired SE, requests/sends,
near endpoint statistics, native rewards and diagnostic actual state. Read all 256
paired world differences, positive/negative/tied counts and conditional-world SE;
any reported normal mean interval is descriptive for this fixed selected program and
world law. It is not re-development uncertainty, training replication, global
optimality, equivalence or UAV/MARL evidence. No optimizer updates occur during selection
or evaluation. Parameter-learning seed confirmation requirements are not invoked.

Read the predeclared at-most-64 hashed development LONG threshold-zero roots using
already-computed paired trajectories: near/long/tail values, paired sampling SE,
first-16 versus last-16 stability, opportunity kinds/endpoints, quota and future packets,
physical states, waits and bypasses. Retain only the fixed hash sample, never preferred
stories. No added rollouts. Long/near endpoint equality and absent/unstable ranking
separation are substantive possible observations. Do not attribute model-tail value
causally to quota or substitute it for actual deployment gain.

Cost: zero new fits, zero training episodes/ticks, zero optimizer updates. Eight
64-world development panels (512 episodes) plus three 256-world final panels (768)
give 1,280 outer episodes and 122,880 actual team ticks. Both planning arms together
are 1,024 episodes, at most 72 optional roots per episode, 32 particles, two branches
and at most 32 model ticks each: upper bound 150,994,944 branch transitions. Actual
padding to the largest near endpoint counts as work. Record exact initializations,
synthetic draws, belief calls/rows/packet constraints/contradictions, per-panel work and
wall time, total wall/CPU and the scientific child Linux peak RSS. Historical C cost
remains four fits; zero new fits does not mean zero computational cost.

Predictions and decisions: a useful longer-horizon package should beat both competent
NEAR_COMMIT and ACTIVE_FIRST on completed jobs while showing readable tradeoffs beyond
the near opportunity. A capable NEAR_COMMIT that absorbs LONG supports adopting the
simpler target. A win only over NEAR_COMMIT does not displace ACTIVE_FIRST. Close or
adverse results require separating lack of action separation, finite-MC instability,
belief mismatch and local-to-deployed value failure using the retained evidence before
choosing the next useful observation. A finite negative result does not disprove lawful
refresh value or reopen solved C05. Technical exceptions retain all accepted handles,
partial work and evidence; reconcile the same request, never blindly relaunch. Scientific
continuation must answer a new explicit question, not expand this panel after its scores.


### C06 implementation acceptance before first launch

DM accepted the lawful filter/model hydration and complete evaluator/output work from
93684c673, df10a0baf and 2dad09256, then read and accepted the corrected planner and
bounded diagnostic delta above. Frozen C01 host remains byte-identical to 089e21f36.
The independent Reviewer reported no material finding on the physical-belief/planning
base, evaluator (after repairing native atomic-manifest temporary-file coexistence),
blind diagnostic retention, or corrected opportunity-based planner. Latest integration
checks: 29 C06 tests pass; planner plus original C01 contract 32 pass; independent
planner/study pass 21. These are engineering fixtures, not experiment outcomes. Meaningful
checks cover packet t-1 alignment, original host hydration, root RNG independence,
first gate/boundary and terminal absence, per-particle common endpoints, padded compute,
same near samples inside LONG, native admission refusal, exact tie behavior and retained
partial outputs. No open material review item remains. The declared full protocol has
not yet executed; runtime, belief approximation and scientific usefulness remain to be
measured. Publish this exact source and launch once through native admission.


### C06 accepted native operation

The first launch was accepted at 2026-09-21 10:17:21 UTC on local_linux from published
source `45a1f534539032c021f5d44a7d78f4b503b0ba51`. Complete native identity, immutable
snapshot, child/supervisor handles, current canonical-control observation and actual-node
memory evidence are in [launch-manifest.json](../../../../runs/skill_information_refresh/c06_multistep_s73170_20260921/launch-manifest.json)
and its referenced admission preflight. The same manifest is the read-only status handle;
no second launch is planned. A bounded Monitor returns native facts while the DM prepares
the complete reading. Acceptance is not scientific completion or a result claim.
