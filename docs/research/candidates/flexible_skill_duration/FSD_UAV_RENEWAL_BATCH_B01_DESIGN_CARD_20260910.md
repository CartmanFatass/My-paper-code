Claim under test: individual internal renewal trained with a fixed larger coordinator batch can exceed authentic D0's final native UAV return at the same early environment exposure.
Binding MARL structure: (b) temporal abstraction or termination; asynchronous individual skill boundaries change the joint rows and valid credit heads presented to a shared coordinator update.

# FSD renewal batch B01 — source-grounded prospective design

**DESIGN ONLY; proposed B/EXPLORE; zero implementation and zero numerical allowance.**
One existing configuration consumer supports the proposed operation. This is ready
as a source/design return, not as an accepted executable or a launch assignment.

## 1. Authority, question and bounded selection

The [fifth-vacancy decision](../../portfolio/decisions/2026-09-10-fifth-vacancy-selection.md)
and its [execution mapping](../../portfolio/pro_packets/20260910_fifth_vacancy_selection/EXECUTION_MAPPING.md)
allocate one FSD document return. Root assigned the existing `codex/fsd` checkout;
main input `867f5e3092b3279cab3b5fb668085dc3cd8f4481` was reconciled in
`48d315a61b081f0492ced1a7f30b871fa4a958cf`, the source inspected here.
The complete Portfolio response is immutable `f4fce9a4fd9603db66463ad8c81bb9464533e260`.

The one proposed question is: after five ordinary native training rollouts, does
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

## 6. Work, proposed limits and current zero exposure

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
was run for this zero-numerical assignment. Actual executed calls remain a
future measurement, including any nonfinite-update failures.

Historical P70/P72 summed complete pair walls are 1693.38/1768.78 seconds,
3462.16 seconds together; aggregate CPU is 13739.12 seconds, distinct from
their 1817/1911-second study critical paths. These old rates are not a new
I1280 cost prediction. Larger batch memory, full new wall time, technical
support and authoring cost remain unmeasured. Fewer optimizer calls do not
prove lower total work or a faster completed result.

For a later allocation, **request** complete command caps D0 900 seconds and
I1280 1800 seconds, plus at most 300 seconds of shared technical support within
a 3000-second total envelope. These are proposed spending ceilings, not timing
estimates or currently granted budget. Command time includes adjacent admission,
imports, construction, collection, updates, the unique endpoint, readout and
closed-file publication. The support reserve includes focused verification,
staging/launch, Monitor queries and collection/readback; unknown support cannot
be counted as zero. No borrowing, grace, extra fit, retry or automatic extension.
If separately allocated, retain remote-first CPU four threads/FP32 and fresh
destination memory admission; no admission or launch occurs in this return.

Current exposure: **scientific invocations=0; models=0; checkpoint loads=0;
environments=0; training/native/synthetic steps=0; optimizer calls=0;
evaluations=0; tests/fixtures=0; replay/profiling/support search=0; Pro Sends=0;
parameter displacement=not applicable (no learner)**.
This reuses the accepted allocation's zero-exposure definition; file/Git and
owner-console operations are document work. No claim is made that authoring is free.

## 7. Remaining engineering boundary

The existing algorithm/configuration consumer is real, but the old fixed runner
is **not** already a runnable I1280 object. `make_config` sets only the old arm
cost; `main` has no batching argument; `assemble_pair` requires all configuration
fields except the old cost to match. Running it unchanged would not implement
this design. No monkeypatch, permissive pair validator or old-card rewrite is
selected as a substitute.

A later bounded binding would explicitly pass the coordinator batch value to
both learner and evaluator, preserve B01/B02 defaults, name the new object/seeds,
and permit exactly the declared 1280/128 distinction in its own pair readout.
The core `agent.py`, `utils.py`, config defaults, native environment and credit
formulas need no algorithm change for this operation. Existing snapshots already
include the field when present. Focused future checks need to falsify that actual
D2 batching consumer and the new primary/configuration readout; none was run here.

Engineering Scope §4 needs **none** for this document return or the proposed
ordinary binding; no new execution/retry/telemetry/registry machinery is requested.
The current five-fact L0 is Root's one-return assignment: owned direction docs
and audit/item records in `codex/fsd`; unchanged source and historical semantics;
acceptance by these inspected consumers and explicit remaining gaps; zero
implementation/numerical budget; stop after this complete committed return.
Any later implementation, focused checks, source acceptance or execution must
have its own actual allocation. This document creates none.
