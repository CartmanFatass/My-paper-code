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
