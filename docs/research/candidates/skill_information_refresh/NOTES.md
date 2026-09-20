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
