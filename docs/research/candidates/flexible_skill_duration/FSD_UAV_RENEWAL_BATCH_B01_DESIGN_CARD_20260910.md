Claim under test: individual internal renewal trained with a fixed larger coordinator batch can exceed authentic D0's final native UAV return at the same early environment exposure.
Binding MARL structure: (b) temporal abstraction or termination; asynchronous individual skill boundaries change the joint rows and valid credit heads presented to a shared coordinator update.

# FSD renewal batch B01 — source-grounded prospective design

**Allocated B/EXPLORE: one fresh I1280/D0 pair, training770703/evaluation780703.**
Portfolio option A in the 2026-09-11 five-chain refill now allocates the real pair:
D0 at most 900 seconds, I1280 at most 1800 seconds, support at most 300 seconds,
complete at most 3000 seconds. This prospectively supersedes the earlier
implementation-only spending boundary. The completed design and implementation
intakes retain their historical zero-real-exposure meaning. No successor is funded.
Technical acceptance and its limits are recorded in the
[implementation intake](FSD_UAV_RENEWAL_BATCH_B01_IMPLEMENTATION_INTAKE_20260910.md).
The one permitted fixture passed at source `0207d0b3c` in 4.8851396 seconds
including publication, cleanup and exit. Acceptance covers binding, traversal
and synthetic primary publication; it provides no new native performance fact.
The current execution assignment and exact commands are in
[the real-pair execution record](FSD_UAV_RENEWAL_BATCH_B01_EXECUTION_20260911.md).

## 1. Authority, question and bounded selection

The [fifth-vacancy decision](../../portfolio/decisions/2026-09-10-fifth-vacancy-selection.md)
and its [execution mapping](../../portfolio/pro_packets/20260910_fifth_vacancy_selection/EXECUTION_MAPPING.md)
allocate one FSD document return. Root assigned the existing `codex/fsd` checkout;
main input `867f5e3092b3279cab3b5fb668085dc3cd8f4481` was reconciled in
`48d315a61b081f0492ced1a7f30b871fa4a958cf`, the source inspected here.
The complete Portfolio response is immutable `f4fce9a4fd9603db66463ad8c81bb9464533e260`.

The subsequent [implementation mapping](../../portfolio/pro_packets/20260910_fifth_slot_implementation_selection/EXECUTION_MAPPING.md)
applies the conforming Portfolio option A from full response
`ade6a687d53b97b5f6cc2fe97da39daa2ad9bfa9`, integrated at
`75d4fa18e1a0a6dbda50b11f5b9f9a6467cc86ef`. Root assigns only that named
implementation return; merge `eec2ec260` brings these exact inputs into the
existing `codex/fsd` worktree. This prospectively supersedes only the earlier
zero-implementation/check allowance, without rewriting its completed design intake.

The one allocated question is: after five ordinary native training rollouts, does
**I1280**, the existing .25 individual-renewal package with coordinator batches
of 1280 joint rows, exceed a freshly trained intact **D0**, with its ordinary
128-row coordinator batches, by more than .01 native mean team reward?

This is an outcome-informed, object-level change within the P67 internal-renewal
mechanism. It changes the actual optimizer and minibatch-normalization arrangement.
It does not repeat P74's stopped unchanged recipe or its declined twenty-rollout
alternative. The original corridor stops, family boundaries, priority, recasts and
formal UAV-entry status remain as recorded. No new Pro question or Send is selected.

## 2. Exact operation already supported by source

`hmasd/agent.py:5896` reads `config.coordinator_batch_size`, defaulting to 128,
and passes it to `RolloutBuffer.get_d2_coordinator_sampler` in `hmasd/utils.py:1308`.
The sampler selects joint `(t, environment)` rows with at least one valid agent
or team segment, shuffles their indices once per PPO epoch, and visits every row
in chunks of the supplied size, including the last partial chunk. It does not
subsample rows or pad them into new data.

| Field | I1280 | Fresh authentic D0 |
| --- | --- | --- |
| `coordinator_batch_size` | **1280**, explicitly set before learner/evaluator construction | **128**, explicitly recording the existing effective default |
| Individual gap threshold `interruption_cost_c` | .25 | numeric positive infinity |
| Team threshold | numeric positive infinity | numeric positive infinity |
| `k`, individual cap, team cap | 10, 10, 10 | 10, 10, 10 |
| D2 mode, opportunity spacing, age feature | `d2`, 1 primitive step, `off` | same |
| PPO epochs, learning rates, clipping, networks, reward and segment credit | Existing settings | Existing settings |

The fixed 1280 choice is ten times the current 128-row chunk, tied to the
already recorded maximum tenfold expansion from clock-boundary joint rows to
all primitive joint rows on this k10 host. It is one specified setting, not a
search, dynamic row-matching policy, learning-rate rescaling or epoch reduction.
`high_level_batch_size` is a different derived field in `configs/config_1.py:767`;
changing that field would not change this D2 sampler.

Each yielded minibatch can cause one real coordinator optimizer step
(`hmasd/agent.py:6034`). Larger chunks also change the group over which the
existing valid-head advantage mean/variance is computed (`:5976`). Thus this is
not numerically equivalent batching and not a pure optimizer-count intervention.
Every selected segment still receives every PPO epoch; its own target formula
and the masked team/individual loss definitions stay intact. Realized rows,
gradients, normalizers and later trajectories can differ between arms.

The hypothesis is that grouping more asynchronous renewal rows before changing
the shared coordinator may produce a more useful later policy than the old
small-chunk renewal package. The source establishes the changed computation;
it establishes neither improved gradients nor return. Fewer updates may instead
undertrain the coordinator, and D0 may remain better.

## 3. Native decision, ownership and credit path

Reuse the [B01 card §§2–4](FSD_UAV_INDIVIDUAL_RENEWAL_B01_SCIENCE_CARD_20260908.md)
for the unchanged scenario1 host, actor/coordinator information and native reward.
Six UAV identities and fifty users remain fixed. Each actor receives its current
partial local observation and updates its own GRU on every primitive step; the
coordinator keeps the existing centralized state/observation/held-prefix inputs.
No input is withheld from D0, and no new information is supplied to I1280.

Own and partner motion changes observed service geometry. Before each primitive
action, the existing teacher-forced coordinator computes the held-skill logit
gap. Reset, invalid state or the common team age reaching 10 samples the team
and every individual. Otherwise an I1280 UAV may resample when its own gap is
at least .25 or its age reaches 10; D0 has only the cap. This is a logit gap,
not a reward advantage or a learned termination head (`agent.py:2330`).

The selected latent belongs to the same `(environment, UAV)` until its next
decision; resampling can retain the same token. A partner's individual renewal
does not reset this UAV's skill or recurrent memory. A team decision renews all
individual segments. Episode reset clears that lane's skills, ages and memory.
There is no join, leave, replacement, survivor-state transfer or identity reuse.

`agent.step` always sends the resulting skill and current observation to the
reactive actor (`:3042`, `:2897`). That actor produces a new native continuous
movement action even while its skill is held. Motion changes coverage, SINR
quality and altitude cost in `envs/pettingzoo/scenario1.py:80`; the unmodified
adapter reward remains native team reward divided by six.

Actual rewards accumulate in each open segment with primitive discount
`gamma**elapsed` (`agent.py:2114`). Own resampling, team resampling, episode end
or rollout flush closes the applicable segment; the terminal flag distinguishes
episode termination from a continuing rollout cut. `utils.py:968` computes one
GAE sequence per UAV and a separate team sequence over their valid rows, with
`gamma**duration` discounts and the existing lambda recursion. No duration
division, terminal-reward rewrite or new credit estimator is introduced.

Those rows enter the changed coordinator batches before the ordinary discoverer
and discriminator updates (`agent.py:6980`). Later collection uses that arm's
updated policy. The source-grounded question is about this complete learning
package and its native consequence, not a guarantee that a counter or predictive
statistic changes a competent action beneficially.

## 4. Comparator, evidence and interpretation limits

The strongest attained same-information comparator for this precise marginal
question is the existing authentic D0 learning recipe, freshly trained here.
Its observed P70/P72 policies beat I by .049670563167111874/.035312725297886094.
It retains recurrent primitive reaction, native action access and the original
128-row training regimen. It is not weakened by being forced to hold an action.

The [scenario1 baseline set](../../baselines/scenario_1/BASELINE_SET_RESULT_20260904.md)
is exposure/integrity evidence only. Its E0 returns cannot be ranked or reused
as performance controls; its training/evaluation budgets also differ. It supplies
no tuned same-information headroom, which remains absent. No baseline tuning,
MAPPO adapter, exact upper or positive pilot is requested before this question.

The two I losses and greater work are the strongest contradiction to benefit.
P70's coverage gain, P72's higher collection returns on rollouts 2–5, small
quality/altitude benefits and positive episode contrasts remain contrary
evidence at their original scope. The component signs differ. The old
54390/65761 training gap causes and 3345/3765 coordinator calls versus D0's
525 do not establish that the update count caused either loss. Zero extra
gap causes at both deterministic endpoints does not mean renewal was disabled
in training. Empty endpoint segment tables remain unmeasured duration.

A future positive I1280−D0 would support this whole package on one training pair.
It would not establish that I1280 improves over the historical I policies,
that larger batching alone is causal, that D0 at another batch size cannot
match it, or that renewal is necessary. These narrower claims require their
own later question; no extra I arm or retuned D0 is silently added here.

## 5. Exact prospective observation and all-sign reading

One matched pair, two arms, no historical checkpoint loads. Proposed new training
base **770703**, evaluation base **780703**, using the existing private lane
seed/reset laws. A bounded identifier search found no occurrence of either
base in the inspected FSD documents or `run_fsd*.py` sources; this does not
certify all historical RNG consumption. Each arm owns its initialization,
optimizer, data and recurrence; common seeds do not require identical trajectories.

Each arm: five rollouts, sixteen lanes, 500 primitive steps per lane, ordinary
updates after each rollout; then one separately constructed and synchronized
deterministic 32×500 endpoint. Preserve terminal storage followed by a fresh
observation **and** global state, evaluator RNG isolation, eval-mode normalizers
and zero evaluator updates. The retained B01/B02 collector already implements
these paths; the new binding must preserve them.

Primary: retain every unscaled adapter return U, report `J=6*U/500`, and read
the mean of the 32 ordered I1280−D0 differences. Report their sample SD and
conditional SE; the independent learning unit is **one matched training pair**,
not 32 episodes. No selected checkpoint, intermediate evaluation, pooling with
old pairs or training-curve replacement of this final endpoint.

MEI: **.01 absolute native mean team reward per primitive step**. Retaining this
native scale makes the new package's practical comparison readable beside the
old outcomes without changing their rules; a relative MEI is unsuitable as the
primary definition when baseline levels vary substantially across learning pairs.

| Future complete primary | Reading and proposed next recommendation |
| --- | --- |
| Greater than +.01 | One local package gain; preserve both old losses. Consider one separately selected independent repetition if its work is worthwhile. |
| Inclusive [−.01,+.01] | No resolved package advantage at this exposure; retain D0 and finish this comparison. This is not equivalence. |
| Less than −.01 | Opposite-sign result for I1280; retain D0 and recommend ending this exact batching variant. No broad FSD closure. |
| Incomplete or damaged dependent primary | Preserve trustworthy own-arm facts and the exact gap; no paired polarity, automatic retry or replacement seed. |

How the result will be interpreted: a gain motivates bounded reliability work,
an inside-MEI result leaves little observed reason to replace D0, and a loss
weakens this precise alternative. Every branch ends one intake and preserves
all signs, training rows and phase-specific treatment activity. No nonzero
endpoint-gap or all-seeds-positive condition is added.

DM prospective prediction: I1280−D0 below −.01, low confidence. The two prior
losses and the possibility of undertraining support caution; changed grouping
could nevertheless alter the outcome. This is not a prediction score or a
reason to reject a future trustworthy result. Owner prediction: not taken.

## 6. Work, complete limits and exposure by stage

Reuse the existing B02 count record for the unchanged two-arm environment
budget: 80000 training transitions, 160 training episodes, ten update stages,
32000 evaluation steps, 64 evaluation episodes, 112000 native environment
steps, 672000 agent-step observations, 6000 batched control calls, four model
constructions and two training starts. These are future counts, not work done.

Actual D2 work is row-dependent. For rollout r, let M_r be valid joint rows.
D0's recorded clock configuration has 800 per rollout; I has at most 8000.
Scheduled coordinator minibatches are `15*sum_r ceil(M_r/1280)` for I1280 and
`15*sum_r ceil(800/128)` for D0. Existing D0 executions recorded 525 calls.
Every row is still replayed for fifteen epochs with six-agent ordered decoding;
larger batches do not remove that dominant tensor work. Agent/team segment
construction and the held-gap pass remain. There are no nested candidate,
trajectory or policy searches and no extra validation evaluation panel.
The expressions are source-derived; no new count program or numerical probe
was run for the original design-only return. Actual executed learning calls remain a
future measurement, including any nonfinite-update failures.

Historical P70/P72 summed complete pair walls are 1693.38/1768.78 seconds,
3462.16 seconds together; aggregate CPU is 13739.12 seconds, distinct from
their 1817/1911-second study critical paths. These old rates are not a new
I1280 cost prediction. Larger batch memory, full new wall time, technical
support and authoring cost remain unmeasured. Fewer optimizer calls do not
prove lower total work or a faster completed result.

The 2026-09-11 Portfolio allocation now grants complete command caps D0 900 seconds
and I1280 1800 seconds, plus at most 300 seconds of shared technical support within
a 3000-second total envelope. These are spending ceilings, not timing
estimates. Command time includes adjacent admission,
imports, construction, collection, updates, the unique endpoint, readout and
closed-file publication. The support reserve includes focused verification,
staging/launch, Monitor queries and collection/readback; unknown support cannot
be counted as zero. No borrowing, grace, extra fit, retry or automatic extension.
Retain remote-first CPU four threads/FP32 and fresh destination memory admission
immediately before each arm. No cap borrowing, seed replacement or extension.

At the original design return, exposure was: **scientific invocations=0; models=0; checkpoint loads=0;
environments=0; training/native/synthetic steps=0; optimizer calls=0;
evaluations=0; tests/fixtures=0; replay/profiling/support search=0; Pro Sends=0;
parameter displacement=not applicable (no learner)**.
That reused the design allocation's zero-exposure definition; file/Git and
owner-console operations are document work. No claim is made that authoring is free.

At implementation intake, the [machine-generated fixture exposure](uav_renewal_batch_b01_implementation_20260910/synthetic_primary.json)
records one command, four configurations, one buffer/1281 valid rows, two sampler
traversals and four synthetic pair readouts. Models, checkpoint loads,
environments/steps, training starts, optimizer calls, real evaluations, replay,
explicit profiling, support search and scientific invocations remain zero.
The complete fixture wall was 4.8851396 seconds; at that implementation return,
all subsequent allowance was unallocated. The new real-pair allocation changes
that spending boundary prospectively; it does not fund another fixture.

## 7. Completed implementation boundary and L0 (historical allocation)

Deliverable: one explicit I1280/D0 entry, the matching strict primary readout,
and one complete technical acceptance return. The entry is
`scripts/run_fsd_uav_renewal_batch_b01.py`; it reuses the B01 runner's collection,
learning and final evaluation path. Its retained CLI/summary arm `I` denotes
I1280 only under new object ID `FSD_UAV_RENEWAL_BATCH_B01`, this card, and
training/evaluation bases 770703/780703. D0 keeps its identity. The entry binds
the proposed future per-arm caps 900/1800 seconds; these constants do not fund
an invocation, and the proposed shared 300-second support reserve is unallocated.

Owned paths/checkout: `scripts/run_fsd_uav_individual_renewal_b01.py`, the new
entry, `tests/experiments/candidates/flexible_skill_duration/uav_renewal_batch_b01/`,
this card and direction technical intake in
`C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd`. Root owns main
integration and Portfolio/tracking. Keep existing historical evidence intact.

Preserved semantics: §§2–5 control. A default-false `renewal_batch` argument
passes through learner and evaluator construction and the paired readout.
Only the new entry enables it. It sets 1280/128 before either model is built;
both snapshots record the field. The new readout requires those exact values
before removing that one additional comparison field. Every other configuration
field remains compared; the existing .25/infinity cost distinction remains exact.
B01/B02 retain their default arguments, object IDs, seeds and command behavior.
The summary's per-arm cap now supplies the existing deadline check, with B01/B02
retaining their original caps. No core algorithm, shared configuration default,
environment, reward, duration credit, RNG or recurrent-state path changes.

Acceptance: independent read-only high-risk review under Engineering Scope §7.3;
inspect changed/imported paths before the single fixture. Exercise the real D2
sampler and new reducer with visibly synthetic records, covering complete row
visitation/final chunk, declared new configuration difference, old defaults,
undeclared-difference rejection and missing primary. Static inspection and
accepted prior evidence cover unchanged full collection/evaluation behavior;
do not run a model, environment or old full-learner smoke for this assignment.

Budget/stop: at most **one** whole fixture command, **60 seconds** including
imports, publication, this invocation's scratch cleanup and exit; **four**
lightweight Config objects; **one** deterministic buffer with at most **1281**
valid joint rows; **two** real sampler traversals, once at 1280 and once at 128;
**four** synthetic pair readouts, each with 32 supplied scores per arm.
Models/encoders/critics, checkpoint loads, environments/steps, collection/training,
optimizer calls, real endpoint evaluations, replay, profiling, support search
and scientific invocations are **zero**. A pass establishes only binding,
traversal and synthetic primary publication. Full learner numerics, activation
memory, new complete cost and native benefit remain unmeasured. No second
numerical invocation follows a failure, correction or review. Report any gap
left by an invalidated check; finish one committed return, including an
incomplete return if necessary. No MGTAP fallback or automatic successor.

Engineering Scope §4 needs **none**. Existing 2000/600-line and cumulative
five-minute directory test limits remain. The fixture owns a unique directory
under this checkout's `temp/`; retain its useful report and remove only that
scratch. There is no result-bearing root or Monitor handle in this assignment.

## 8. Allocated real-pair L0 — 2026-09-11

Authority: conforming Portfolio option A, complete immutable response
`ed0c4e1c3cd28be353253e8533bc89a261f25357`; the
[exact FSD mapping](../../portfolio/pro_packets/20260911_five_chain_refill/EXECUTION_MAPPING.md#fsd--complete-one-fresh-i1280d0-b-pair)
and Root's named assignment. Required main `5bbae6d90` fast-forwarded the clean
shared `codex/fsd` checkout; the accepted learner/entry/readout source is unchanged.

Deliverable: one exact fresh pair through full collection, terminal publication,
technical/scientific intake and scoped closeout, or a bounded dependent failure.
Owned paths: this card, the execution record and its command/evidence directory,
result/intake/brief/audit/owner records under FSD. Existing source is reused;
no new learner implementation, tests or altered algorithms are selected.

Preserved semantics: §§2–5, including all score outcomes and contrary P70/P72
losses. Training770703/evaluation780703 is reconciled with local accepted records
and destination FSD supervisor/worktree listings before first acceptance; no
matching prior run was found. This is one declared fresh identity, not seed screening.

Execution: one detached exact-SHA remote checkout at
`/home/wu/hmasd-worktrees/fsd-uav-renewal-batch-b01-770703-20260911`, Linux node
`hmasd-wsl-node`, `/home/wu/.venvs/hmasd/bin/python`, CPU FP32/four Torch threads.
Private learner/evaluator RNG and lane laws are unchanged; Linux/CPU was the
predeclared portable route, with no CUDA use or precision substitution.
D0 runs first; after its terminal primary is collected, I1280 uses that same
fresh D0 summary. Separate `agent-task` handles and KILL timeouts include each
arm's destination admission, imports, initialization, learning, endpoint and exit.
The mandatory admission precedes creation of any scientific output/model/RNG.

Acceptance: reuse the unchanged reviewed fixture and collector/evaluator evidence;
read the actual new wrapper inputs and syntax-check the committed shell bytes
without running the payload. Inspect terminal exit, exact source, primary/counts,
configured batches, all outcomes and complete time receipts. Check evidence
against the frozen reading rule, with one independent training pair and conditional
episode uncertainty. No additional scientific validation or required positive sign.

Support accounting charges measured tool/command wall for preparation, review
execution, staging, publication/readback, Monitor observation, collection/reduction
and preservation/cleanup once; idle waiting and study elapsed remain separately
reported. Unknown overhead stays unknown, not zero. The execution record retains
charges and the remaining 300-second allowance. No added profiling or timing pilot.

Budget/stop: D0≤900s, I1280≤1800s, support≤300s, sum≤3000s; two fits/four models,
80000 training plus 32000 final evaluation steps, final32 episodes per arm.
Complete both preselected arms or stop at a bounded dependent failure; no third
arm, replacement, automatic retry, longer training, reduced endpoint or successor.
Monitor gets each accepted handle directly; DM stops routine polling and returns
pending collection to Root. Engineering Scope §4 needs **none**. Preserve unique
source/evidence before any scoped removal and leave the active authoring checkout.
