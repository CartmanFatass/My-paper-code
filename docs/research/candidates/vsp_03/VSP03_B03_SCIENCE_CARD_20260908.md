Ordinary learned submission timing may improve native team utility over fixed readiness when a trained shared-service scheduler is executed greedily.
Binding structure: temporal abstraction / termination at fixed N=2; an irreversible eight-tick commitment can remove the partner's submission opportunities.

# VSP03 B03 — ordinary G for deterministic shared-service use

**B/EXPLORE, outcome-informed selection with a prospective new seed and primary.**
The complete [Convergence response](pro_packets/20260908_greedy_use_reentry_convergence/archive/RESPONSE.md)
at `861c5072160d624970875b7345c2f72e78183e53` selects one seed-5 G study under P54.
The [DM intake](VSP03_P54_GREEDY_USE_CONVERGENCE_INTAKE_20260908.md) applies it without
specification exception. This is a narrower study inside the existing shared-service
question, **not a second RECAST; recasts:1**. N1 and the B02 T-initialization/learned-T
family remain paused. Old cards, outcomes, sources, failed attempts and primaries remain.

## 1. Question, actual use and claim ceiling

Train ordinary G offline at the fixed budget, freeze it at update128, then use strict
`logit > 0` as the actual submission rule at every legal opportunity; otherwise continue,
including a tie. Does this deterministic learned scheduler improve native team utility
over fixed readiness R0? Primary is final greedy **G−R0**; fixed R and stochastic G
constrain the claim. There is no online adaptation or result-selected mode/checkpoint.

The independent training unit is **one G instance, seed5**. Controllers, episodes,
updates, worlds and modes are not additional training instances or a T/G pair. Seed4
is the outcome-informed discovery observation, not a second prospective confirmation
sample. This B can report one new controller's native comparison at this budget; it
cannot establish stable superiority/equivalence, optimality, initialization value,
an identified multi-agent/decentralized causal advantage, transfer/deployment/safety,
UAV entry or C promotion. No T model, additional seed, tuning, replay, diagnostic,
search, intermediate held-out checkpoint or result-dependent selection is authorized.

## 2. Frozen task, information and credit

Reuse the accepted B02 `Model`, `worlds`, `action_tapes`, `rollout`, `rule_actions`,
`return_to_go` and B01 `objective`, `vectors`, `scales`, publication helpers without
changing B01/B02 bytes. [B02 card](VSP03_B02_SCIENCE_CARD_20260907.md), Native host,
Public features and Learner sections, remains the precise inherited environment
and algorithm source; the selected differences here and the complete response §§4–6
control B03's arm, RNG identity, primary, counts and validation.

Two fixed controller/target identities each own one job and share one service slot.
There are no roster joins/leaves/rejoins, replacements, private partner observations
or changing partner policies at evaluation. Target occupancy return is not membership
change. Both target processes advance all40 primitive transitions. Occupied targets
leave with probability1/(d+4); absent targets return with probability1/2. A public fair
phase bit assigns fixed clocks0,4,...,32 versus2,6,...,30. Only pending and slot-free
controllers act on their own clock. Forced waits update latches without policy rows.

SUBMIT is irreversible, occupies the next8 target transitions, and earns success only
if the submitted target remains occupied through all8 samples. Failure does not release
early. Completion/reward/release precedes the next boundary's decision. CONTINUE reserves
nothing; a partner may submit two ticks later. All target evolution and waiting through
the common endpoint are retained, including missed final opportunities. The two jobs'
integer units are `200*success - 10*attempt - waiting_ticks`; native team return divides
their sum by400. Each valid action receives actual remaining team reward through t=40,
subtracting the already accrued team prefix. Primitive gamma1 and terminal bootstrap0
apply; there is no elapsed-opportunity shortcut or own-job-only credit.

Actor and critic receive the same14 public features: t/40; own(y,d/40,a,e,b);
partner(y,d/40,a,e,b); partner pending; own phase; partner next fixed clock/40, or1
if none. b is recomputed as a*y*(1−e), including the partner; latch/read/update order
is unchanged. The clock is calendar information, not future slot availability.
No future random tape, eventual service success or privileged critic state is visible.
Both controllers share and co-adapt G during training; both use its frozen parameters
at evaluation. Submission changes partner opportunity and native return, but this
fully public fixed-team task does not isolate a decentralized or MARL-specific cause.

## 3. Learner and exact RNG realization

Construct **one** shared G actor14→32→32→1 with tanh hidden layers and a trainable
own-b direct coefficient, and critic14→32→1:1570 actor/direct plus513 critic=2083
parameters. Torch initialization is40005. Output residual weight, output bias and
direct-b start at zero; other layers use the inherited initialization. Removing T
does not remove G's public event features or trainable direct-b parameter.

Run128 updates, each collecting128 complete joint episodes with parameters fixed
within the batch and one joint backward/Adam step. Adam lr0.001, betas(0.9,0.999),
eps1e−8, weight_decay0. Use the original actor log-probability times detached actual
team advantage summed over valid rows then divided by joint episodes; critic loss is
0.5 times mean squared error over valid rows. Entropy coefficient remains
`0.01*max(0,(64-u)/63)`. No clipping, advantage normalization, extra epoch or replay.
Random training and the resulting greedy mapping are different performance quantities;
neither parameter movement nor training return guarantees a greedy gain.

Use PCG64/SeedSequence target addresses `[302,5,split,episode,target]` and phase with
target2. Train split100, episodes0..16383; evaluation split200, worlds0..1023.
**G keeps arm identity1**, so action addresses are `[303,5,split,mode,1,episode]`,
mode0 training and mode1 final stochastic. Each tape has17 fixed-calendar-position
uniforms; blocked clocks do not shift them. Greedy/R0/R consume no action draws.
Deleting T must not renumber G to0. No old weights, optimizer state or streams load.

## 4. Evaluation, publication and reading rule

At update128 only, evaluate G greedy, G stochastic, R0 and R directly once each on
the **same1024** held-out worlds/phase. Use one1024-world batch per execution, preserving
the existing source's numerical/RNG semantics. Stochastic G has one action realization
per world, with no nested repetition. R0 submits iff own b=1 at a legal opportunity.
R adds only the existing yield condition: partner pending, has another clock, b=1,
and strictly older dwell age; ties submit. No extra deadline rule or rule tuning.

Primary: mean per-world `G_greedy.return - R0.return`. Report all four absolute means,
G greedy−R, and G stochastic−R0/R/own-greedy. For each contrast retain paired-world
sample SD(ddof1) and SE=SD/32; these are conditional evaluation variation, not training
population uncertainty. Record one training instance and keep seed4 discovery separately.

Retain four endpoint sets with world/phase, each job's integer utility, success, attempt,
failure, omission, waiting and submission time, plus existing fixed/pending/eligible/
blocked/final-clock counts. Preserve128 training curve rows, actual valid/gradient rows,
model/step/interaction/evaluation counts, initial/first/final parameter exposure, final
weights, launch SHA/node/command, wall/RSS and a readable summary. Read the necessary
persisted primary/count/weight output back inside the selected invocation. Missing
primary limits its dependent claim; trustworthy partial facts remain reportable.

**Reading rule:** G greedy above R0 and R supports this sampled ordinary deterministic
scheduler at this budget. A small positive stays small; it neither vanishes nor grants
an automatic next run. G above R0 but below R supports only the R0 comparison. A zero
or negative primary does not support replacing R0 here; retaining readiness is the
reasonable current control choice, without population equivalence or direction failure.
Stochastic losses restrict any gain to the declared greedy use; stochastic improvement
without greedy improvement does not answer the primary positively. Retain every sign
and seed, and never switch mode, threshold, checkpoint or primary after seeing output.

## 5. MEI, headroom, prediction and interpretation

MEI is0.02 absolute team-return units, eight total waiting ticks/400, inherited for the
same native utility. Absolute scale avoids ratios near zero. It is an interpretation
scale, not significance, equivalence, validity or a hard investment boundary. Tuned N2
headroom remains absent, not zero; R/R0 are fixed competing controllers, not uppers.
Reuse them because information/action/observation/native utility match; no tuned baseline
package or upper/curve pair exists to import. Computing one is not prerequisite work.

How the result will be interpreted: an above-MEI G−R0 with R also exceeded would support
retaining this scheme and considering a bounded independent-training follow-up; an
inside-MEI margin is a local signal or near-null at its actual size; opposite sign favors
readiness for this run. The complete result determines the next justified object
decision; no sign automatically selects another invocation. The old T=R0, small G gains,
stochastic losses, training uncertainty and N1 results remain alongside this result.

Prediction on record: **abs(final greedy G−R0)<=0.02, low confidence**. This came from
the P54 source intake before seed5 existed, not from a new observation. Owner prediction:
**not taken (unattended)** unless a relevant reply appears before intake.

## 6. Work, complete cap, exposure and execution

[Machine counts](VSP03_B03_COUNTS_20260908.json):1arm×1seed×128updates×128episodes×40ticks×2targets;
evaluation4executions×1024worlds×40ticks×2targets. Total **20480 joint episodes,
819200 team ticks,1638400 target transitions,128 backward and128 Adam steps**.
Training alone is16384 joint episodes and1310720 target transitions; G evaluation2048
episodes and fixed references2048. Policy batch rollout calls are at most2210, excluding
objective/critic/gradient work. Actual valid rows depend on actions; do not top them up.
Additional validation models/episodes/optimizer steps are **0/0/0**. No candidate,
joint-action, future-trajectory search or solver is used.

There is **one complete120-second wall cap**, covering adjacent node admission, imports,
initialization, training, all evaluation, necessary connection checks, output construction,
publication/readback and exit. The cost law is admission/import+G init+128C(128,40,2)
+E_Ggreedy(1024,40,2)+E_Gstochastic+E_R0+E_R+connection checks+output/readback/exit.
Do not restart the clock per stage or hide shared work outside it. Historical G-arm
1.470991699s excludes shared/cold-start costs. Historical complete T/G5.05s is only
a planning anchor for the smaller work count, not a new cost measurement or upper;
do not scale it proportionally. New complete wall and aggregate CPU remain unknown.
There is no separate timing/profiling/calibration invocation.

Exposure line: selected G has2083 parameters,128 real Adam steps at lr0.001 and16384
real training episodes. The same recipe's historical G had initial L2=5.8807516098 and
final displacement/initial L2=0.3774883786. This shows the recipe can move, not that
seed5 will improve. Record actual initial, first-step and final scale/displacement during
the normal learner. The linked machine line records zero new exposure at card creation.

Use configured remote-first **wsl_4070, CPU float32, one compute thread**, preserving
the existing float64 NumPy random worlds. Use exact committed/pushed source in a detached
worktree and the configured agent-task supervisor. Adjacent destination admission must
measure physical and effective available memory each>=4GiB before scientific construction.
No old receipt admits this invocation. P54 selects this configured route; any failed
remote route returns its concrete gap without silently choosing a local host.

Stop at the sole complete publication/exit,120s, or a concrete reward/information/
comparison/training/required-primary defect. Preserve partial records and trustworthy
counts without calling incomplete training a complete endpoint. No automatic retry,
seed replacement, extra evaluation, tuning, resume or cap expansion follows. Engineering
failure is not scientific polarity.

## 7. Scope, acceptance and observation

This object needs **none** of ENGINEERING_SCOPE_SPEC §4's optional machinery. Reuse
existing supervisor/admission/observation and simple publication. Limits remain2000
new non-test source lines,600 runner lines and5-minute research-directory test budget;
30% orchestration is a review signal. Do not add a monitor, registry, schema system,
recovery, pool, profiler, byte-manifest gate or extra execution layer.

CM owns a small B03 driver, thin matching runner, mirrored focused checks, technical
acceptance and result evidence in this existing shared checkout/branch. B02 run itself
is not called: it would construct T/G, execute the old eight-episode check, and report
the old T−R primary. Reuse its scientific functions and their accepted evidence.
Independent affected-path review focuses on the single G, arm1 RNG, new primary/unit,
counts and complete cap. Static/literal connection/output checks plus the selected
normal invocation's primary/count/weight readback protect those changes. Do not rerun
the old fixture, construct an extra model or simulate a pre-launch world.

Commit/push accepted source before the sole invocation. CM supplies node/handle/SHA/cwd/
log/results/admission and responsible identities to Root via collaboration; Root records
adoption before ACK and owns routine observation thereafter. CM retains collection and
technical acceptance, DM the complete scientific intake and next delegated decision.
No observation handoff relaunches a run. P54's conforming selected-object route covers
this card, CM work, one bounded execution and intake; ordinary continuation does not
need another Portfolio request or Pro round.

## 8. Freeze decision

Options: (a) freeze the exact conforming single-G design selected by the response;
(b) return a concrete scientific/specification conflict. Recommend and select(a), no
conflict found. **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
The direction selection is PRO_FINAL; this card wording/freeze is object-tier execution
of that choice. No additional exposure is spent to freeze it. The intake records the
owner scan, audit and P2 new-card item before implementation proceeds.
