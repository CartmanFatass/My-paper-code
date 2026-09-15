# FSD baseline × interruption B01 — prospective card (unfunded)

Class **B/EXPLORE**, host Scenario 1 (`envs.pettingzoo.scenario1.UAVBaseStationEnv`,
six UAVs, fifty users, H500, J = 6U/500), prepared 2026-09-15 by the Claude Code
research hub acting as FSD's DM after the owner's 2026-09-15 resume. This is a
proposal for `portfolio:cross_direction`; it grants nothing and launches nothing.
It merges the two open FSD preparations: the same-host baseline card the
2026-09-14 Portfolio decision said "continues independently", and the follow-up
to the completed interruption × batch factorial
([E0](FSD_INTERRUPTION_BATCH_B01_RESULT_EVIDENCE_20260915.md),
[intake](FSD_INTERRUPTION_BATCH_B01_INTAKE_20260915.md)).

## 1. Decision and source of the question

The completed factorial reads the high-batch renewal primary SI1280 at
−.02644030 / +.08464985 J by block (mean +.02910478, training SD .07855260,
df = 1 interval [−.6767, +.7349]); MB −.00280123, INT −.03983204, PKG +.04621956.
Two blocks cannot separate a +.03 J mean from the block-to-block variation, and
FSD still has no same-host baseline: the direction cannot say whether D2-D0 or
I1280 sits above or below a flat comparator at all. The hub's cross-direction
review ([FOUR_DIRECTION_PROGRESS_REVIEW_20260915.md](../../../Claude_docs/reviews/FOUR_DIRECTION_PROGRESS_REVIEW_20260915.md))
names both as the direction's binding uncertainties and finds that pooling the
seven package observations on record gives a mean of about +.06 J with a 95 %
interval that still touches zero.

The question for Portfolio: fund one combined study that (i) adds the missing
same-host flat baseline arm, (ii) replaces the 5-rollout early endpoint with a
15-rollout endpoint while keeping the 5-rollout panel as a replication datum,
and (iii) buys enough independent training blocks (six) for a descriptive
interval that can distinguish a .05 J effect from block noise at the scale
observed so far, or fund a smaller version, or decline and leave FSD ACTIVE-idle.

## 2. Arms and implemented factors

| Arm | What it is | Coordinator | Individual gap | Joint-row batch |
| --- | --- | --- | --- | --- |
| **FLAT** | private-actor flat reduction of the same HMASD stack: single constant skill (`n_Z = n_z = 1`, `k = 10` as in the D arms, see §8), coordinator and both discriminators **never updated** (the coordinator is still forward-called every ten steps to assign the single skill), discriminator rewards off, only the `SkillDiscoverer` actor + critic receive PPO updates | never updated | n/a | n/a |
| **D1280** | D2-D0 as in the completed factorial | on | +∞ | 1280 |
| **I1280** | interruption recipe as in the completed factorial | on | .25 | 1280 |

FLAT is selected by `hmasd.baselines.apply_algorithm_config(config, "mappo")`
(`hmasd/baselines.py:126-148`), which mutates the ordinary config and routes to
the plain `HMASDAgent`; under it `store_transition_batch` skips coordinator
experience (`hmasd/agent.py:3850`), `update()` skips `update_coordinator` and
`update_discriminators` (`hmasd/agent.py:6974-6998`) and runs only
`update_discoverer_from_rollout` (`hmasd/agent.py:6986-6988`). The actor
consumes the private observation, the constant skill and its private recurrent
state (`hmasd/networks.py:1687`); the critic consumes the global state
(`hmasd/networks.py:1695`). Shared with D1280/I1280: environment construction
and lane seeds, reward and J, optimizer law, observation/state/value
normalizers, evaluator and 32-world panel, checks and summary format.

Labelling: FLAT is the **private-actor flat reduction** the 2026-09-14
preparation intake lists as its second candidate ("two implemented information
architectures"). It is MAPPO-style (recurrent private actor, central-state
critic, PPO) but it is not the pinned upstream R-MAPPO used by ACVC, and it is
not information-matched to the HMASD coordinator, whose skill path carries
global state and joint observations into action selection. The read-only map
of the alternative (porting ACVC's on-policy adapter) found hard-coded
five-agent / 116-dimensional feature slices, a per-run external staging of the
pinned upstream source, a 256 versus 500 horizon and a reward law without the
Scenario 1 altitude penalty; that port is a different, larger object and is not
proposed. The central-input flat variant (first candidate in the preparation
intake) is deferred to a later ablation because its input adapter is new code
on the actor surface and its value depends on the answer this study gives: if
D1280 does not beat the private-actor flat reduction, an information-matched
comparator cannot rescue a headroom claim.

Unchanged for all arms: D2 mode where applicable, primitive-reactive actor/GRU,
k/individual/team caps 10, team gap ∞, age off, causal information, native
reward, primitive-duration credit, CPU FP32 four threads, exact committed
source, remote-first WSL node.

## 3. Endpoint, panels and independent units

Each fit runs **15 training rollouts** of 16 lanes × H500 (120,000 team steps;
the completed factorial used 5 rollouts = 40,000). The **same 32-world H500
deterministic panel** (evaluation base seed of the block, lanes base + rank) is
evaluated after rollouts 5, 10 and 15 from one evaluator object whose weights
and evaluation-mode normalizers are synced from the learner at each panel;
each panel runs inside the existing `_preserve_rng()` wrapper, so training draws
continue bit-for-bit as if no panel had run (the collector and evaluator share
the process-global RNG; the wrapper snapshots and restores it,
`run_flexible_skill_duration_e0.py:122-133`, used by
`run_fsd_uav_individual_renewal_b01.py:264-323`). The rollout-15 panel is the
endpoint; rollouts 5 and 10 are declared interim panels.

Independent units are **training blocks**: six fresh blocks with training
bases 772203, 772303, 772403, 772503, 772603, 772703 and evaluation bases
782203 … 782703 (continuing the completed factorial's pattern; lane seeds are
base + rank, ranges disjoint). Within a block the three arms share initial
lane schedules as the completed factorial did; models, optimizers, buffers and
evaluator state are arm-local; nothing is transferred across blocks. 32 panel
worlds are nested endpoint conditions, never training replicates. No historical
model, buffer or checkpoint is reused.

## 4. Primary, auxiliaries, MEI and reading rule

```text
Primary   SI1280_15 = J15(I1280) − J15(D1280)          six blocks, equal weight
Headroom  H_15      = J15(D1280) − J15(FLAT)            six blocks
          HI_15     = J15(I1280) − J15(FLAT)            six blocks
Curve     SI1280_r, H_r for r = 5, 10                    six blocks each
Replicate SI1280_5 pooled: six new blocks + the two completed factorial blocks
```

**Primary MEI: .05 J absolute** (about 13 % of the arm level ≈ .37 J seen so
far). Reason: I1280 costs about 2.2 × the wall of D1280 per fit (1075–1319 s
versus 488–595 s at 5 rollouts) and adds coordinator work per renewal; a
renewal benefit smaller than the block-to-block variation of an arm level
(.06–.09 J across the two completed blocks) would not change the authentic-D0
default, so the smallest effect worth developing is one of that order. The
completed factorial's .01 J was a task-justified reading threshold for a
two-block sign observation; it is not rewritten there.

Reading of the primary (six blocks, sample SD, SE, Student-t df = 5 95 %
interval under the iid-normal block-contrast working model, coverage not
empirically established): mean > +.05 with the interval excluding 0 supports
developing the renewal recipe at this budget; interval inside (−.05, +.05)
reads as no MEI-sized renewal effect at 15 rollouts on this host (not
equivalence); mean < −.05 is adverse; anything else is unresolved and is
recorded as such. **No automatic extension**: a further tranche of blocks is a
new Portfolio question with the six-block numbers on record.

Headroom H_15 and HI_15 carry no MEI; they are the direction's headroom record
under evidence-spec §11.7 (diagnostic and sequencing input). Their sign and
interval are reported with the same working model. A negative H_15 with an
interval excluding 0 is a real result: the D2-D0 package under this recipe sits
below a private-actor flat reduction at equal exposure, which bounds every
package claim the direction has made at this budget.

The curve panels answer whether the contrasts move with training; they are
reported per rollout, never selected among. The pooled SI1280_5 (eight blocks,
df = 7) is prospectively declared here as a replication of the completed
factorial's primary; the six new blocks are also reported alone.

Predictions (hub, on record; the owner's slot is `not taken (unattended)`):
H_15 mean in [−.05, +.05] (P .55), below −.05 (P .30), above +.05 (P .15);
SI1280_15 mean in [−.05, +.05] (P .60), above +.05 (P .30), below (P .10).

## 5. Exposure and ordinary runtime plan

| Quantity | Per fit | F: 3 arms × 6 blocks = 18 fits | S: 3 arms × 4 blocks = 12 fits |
| --- | ---: | ---: | ---: |
| training team steps | 120,000 | 2,160,000 | 1,440,000 |
| training episodes | 240 | 4,320 | 2,880 |
| evaluation team steps (3 panels) | 48,000 | 864,000 | 576,000 |
| evaluation episodes | 96 | 1,728 | 1,152 |
| update stages | 15 | 270 | 180 |
| model constructions | 2 | 36 | 24 |
| batched control calls (training + panels) | 9,000 | 162,000 | 108,000 |
| agent-step observations | 1,008,000 | 18,144,000 | 12,096,000 |

Coordinator law unchanged, `15 × Σ_r ceil(M_r / batch)`: D1280 schedules 15
calls per rollout (225 per fit); I1280 at most 105 per rollout (≤ 1,575 per
fit, 330–360 per 5-rollout fit observed); FLAT 0. Actor/critic steps 11,250 per
5-rollout fit in the completed factorial, so about 33,750 per fit here.

Ordinary planning walls per fit, scaled from the completed factorial's measured
whole-command walls at 5 rollouts (D1280 487.60/594.97 s, I1280
1075.13/1319.23 s, D128 463.64/515.18 s) with training and panel parts each
tripled: D1280 ≈ 1,500–1,800 s, I1280 ≈ 3,300–4,000 s, FLAT ≈ 1,200–1,600 s
(no coordinator or discriminator work; unmeasured). Per block ≈ 6,000–7,400 s;
**F ≈ 36,000–44,000 s native wall sum** (about 10–12 h if the node runs fits
one after another, as the completed factorial's span suggests), **S ≈
24,000–30,000 s**. CPU ≈ 4 × wall. These are plans, not caps; complete
support/provider cost is unknown. Exposure counts are card-fixed.

## 6. Minimal L0 (implementation the hub will perform directly)

Under OWNER_DIRECT 2026-09-12 the hub implements; `hmasd-reviewer` (Opus)
reviews before launch because the change touches the evaluation path and a
new algorithm-mode configuration.

- **Owned paths**: new `scripts/run_fsd_baseline_interruption_b01.py` (≤ 600
  lines), new `tests/scripts/fsd_baseline_interruption_b01_test.py`, new
  `experiments/candidates/flexible_skill_duration/baseline_interruption_b01/`
  only if a module is needed. **Read-only**: `hmasd/**`,
  `scripts/run_fsd_uav_individual_renewal_b01.py`,
  `scripts/run_fsd_interruption_batch_b01.py`,
  `scripts/run_flexible_skill_duration_e0.py`.
- **Facts fixed**: `ROLLOUTS = 5` is a bare module constant read by name inside
  `collect_training` and validated by `assemble_pair`
  (`run_fsd_uav_individual_renewal_b01.py:30,176,338-340`); the new runner sets
  its own rollout count of 15 explicitly, records it in the summary, and does
  its own assembly/validation for three panels (the existing `assemble_pair`
  asserts exactly one evaluation and `model_constructions == 2`). FLAT is
  built from `shared.make_config` + `apply_algorithm_config(config, "mappo")`
  before `HMASDAgent` construction, through the new runner's own builder and an
  additive `Evaluator` subclass (no injection seam exists inside
  `build_learner`/`Evaluator.__init__`). One evaluator per fit; three panels;
  `_preserve_rng()` around each.
- **Protected**: no edit to `hmasd/**`; no change to reward, information,
  action space, normalizers, optimizer law, RNG seeding law, panel law, D1280
  and I1280 recipes (byte-identical config to the completed factorial except
  the rollout count); training trajectory with interim panels identical to the
  trajectory without them (focused test on a synthetic tiny config); FLAT
  coordinator/discriminator optimizer call counts 0 and finite actor/critic
  parameter motion recorded.
- **Acceptance**: focused tests green; reviewer finding list resolved; per-arm
  cost projection recorded; frozen launch commands per fit with fresh
  `admit-memory` joined by `&&` on the WSL node; launches only through
  `hmasd-experiment-operator`; collection through `hmasd-experiment-tracker`.
- **Exposure until funded**: zero models, fits, environment steps beyond the
  synthetic focused tests.

## 7. Investment options for Portfolio

- **F (recommended)**: three arms × six blocks, 18 fits, all three panels,
  everything in §§2–6.
- **S**: three arms × four blocks, 12 fits, same design; df = 3 interval,
  weaker but still the first headroom record.
- **P**: F plus a fourth arm, direct fixed-k10 HMASD (the ordinary route with
  the coordinator on, no D2 reactivity), 24 fits, for a method-level headroom
  record in addition to the package-level one; not recommended now because it
  adds a third of the cost to answer a question the D1280 result may make moot.
- **N**: no experimental allocation; FSD stays ACTIVE/HIGH and ACTIVE-idle with
  this card on record.

Why F over S: the whole point is a block count that can say something about a
.05 J effect; four blocks give a df = 3 interval whose half-width at the
observed SD (~.08 J) is about .13 J, six blocks about .08 J. Neither resolves a
.03 J effect; six is the smallest count at which a .05 J effect with the
observed SD has a fair chance of an interval excluding zero, and at which a
zero-centred interval narrower than ±.10 J is possible. Why FLAT is the
private-actor reduction and not a ported R-MAPPO: identical collector,
evaluator, reward and panel make H_15 a clean architecture contrast at equal
exposure; a ported trainer would confound optimizer, normalizer and buffer law
with architecture, and costs a separate object.

Under all options: authentic D0 remains default, limited optional I1280 keeps
its accepted scope, no lifecycle, priority or peer change, no C promotion, no
recast, no specification exception. Completion ends only this allocation.

## 8. Portfolio decision applied (2026-09-15, `PRO_FINAL / OWNER_DELEGATED`)

`portfolio:cross_direction` selected **S with corrections**
([RESPONSE.md](../../portfolio/pro_packets/20260915_fsd_baseline_interruption_investment/archive/RESPONSE.md),
request `2026-09-15-fsd-baseline-interruption-investment-01`, delivery commit
`5c6053f4a`). The frozen object is therefore:

- **Four** fresh training blocks, bases 772203/772303/772403/772503 and
  782203/782303/782403/782503; twelve original fits; blocks 772603/772703 are
  unpurchased. Fifteen rollouts and all three panels are retained.
- **FLAT is built from the ordinary `off` configuration** and then the
  `apply_algorithm_config(config, "mappo")` switch, not from a D2 configuration.
  It keeps constant single skills, zero coordinator/discriminator updates and a
  learning private recurrent actor with a central-state critic.
  *DM deviation from the decision's "switch-selected long k", returned to the
  node:* the switch's `k = rollout_length + 1` does run (the discoverer sampler
  falls back to one full-rollout chunk, `hmasd/utils.py` `get_discoverer_sampler`;
  the reviewer ran it on the tiny real host), but `config.k` is also the
  truncated-BPTT chunk length of the recurrent actor and critic
  (`hmasd/agent.py:6125`), so the long k would train FLAT through 500-step
  chunks against the D arms' 10-step chunks, confounding the architecture
  contrast with the gradient-truncation law and adding a 500-step BPTT
  memory/wall risk. The runner therefore sets `k = 10`, identical to the D arms:
  the optimizer law is the same in every arm and the only differences are the
  single constant skill and the absent coordinator/discriminator learning. The
  switch's high-level buffer fields stay as computed at its own k; they are inert
  and listed as planned differences. Independent Opus review (2026-09-15)
  judged k = 10 the better control and required this reason to be recorded and
  returned to `portfolio:cross_direction` as a correction note; the FLAT arm is
  dependent work under AGENTS §3 and waits for that return, while D1280/I1280
  launch as independent authorized work.
  **Returned and confirmed** (`PRO_FINAL / OWNER_DELEGATED`, 2026-09-15 12:55Z,
  [decision](../../portfolio/decisions/2026-09-15-fsd-flat-k-correction.md)): option 1,
  FLAT stays at k = 10; the FLAT arm is independent work from that time.
- **Labels:** `H_r`/`HI_r` are renamed `GAP_D`/`GAP_I`, *untuned
  cross-information package gaps* D1280 − FLAT and I1280 − FLAT; they are not
  §11.7 headroom and supply no tuned same-information reference.
- **MEI .05 J** stays as a cost-sensitive development target; the claim that an
  effect must exceed arm variability to matter is withdrawn. Reading is split:
  importance (mean above +.05 locally substantial positive; below −.05 adverse;
  inclusive ±.05 small signed) and uncertainty (df = 3 working-model interval
  reported alongside; zero exclusion strengthens but is not required; an
  interval inside ±.05 is a model-conditional small-magnitude reading, never
  equivalence).
- **Rollout-5 accumulation:** four new plus two historical blocks (six, df = 5),
  new and historical groups reported separately first; the combined summary is
  explicitly outcome-informed descriptive accumulation, permitted because the
  five-rollout prefix, evaluation and seed semantics are inherited unchanged
  (collector equivalence test; entropy annealing is off in this recipe so the
  inherited `total_timesteps` is inert).
- **Exposure (S):** 1,440,000 training + 576,000 evaluation team steps, 2,880 +
  1,152 episodes, 180 update stages, 24 model constructions, 108,000 batched
  control calls, 12,096,000 agent-step observations. Ordinary plan 24,000–30,000 s
  summed native wall; not a cap.
- Implementation: `scripts/run_fsd_baseline_interruption_b01.py` (488 lines) and
  its two focused test files, committed on `codex/fsd` at `db0b11bd8`; 15
  synthetic and 2 real tiny-host tests green; Opus independent review requested
  before launch. `hmasd/**` and the existing runners untouched.
