# FSD matched-information baseline B01 — frozen card (CONFIRM lane)

Class **B** under evidence spec section 11, lane **CONFIRM** (approved set v1, priority 1), host
Scenario 1 (`envs.pettingzoo.scenario1.UAVBaseStationEnv`, six UAVs, fifty users, H500,
J = 6U/500). **Fixed by `em:flexible_skill_duration:convergence` on 2026-09-16 05:19Z** (request
`2026-09-16-fsd-host-headroom-card-convergence-01`, option **C**, PRO_FINAL; response commit
`1462d3954`, [archive](pro_packets/20260916_host_headroom_card_convergence/archive/RESPONSE.md),
38,865 B, sha256 0e9f6ca308ef8bd70d68836708a1db71faeae26a1f378f3eff60b1f42ac7fc66). It replaces the
rejected [host headroom card](FSD_HOST_HEADROOM_B01_PROSPECTIVE_CARD_20260916.md) as the direction's
first CONFIRM object. This card transcribes the node's object definition; the DM's own additions
are marked "DM:". This is the object's one Pro round; the result is read by section 6 without a
result review unless an event the rule does not cover changes the comparison's meaning.

`headroom_record: not established`. The object measures a bounded method difference between two
complete learning methods under the same exogenous information and the same central-refresh
timing; it is not an upper reference minus a baseline and it does not promise a strict section
11.7 headroom record.

## 1. Question, treatment and comparator

**Question.** At a fixed 360,000 training team steps, does the standing D1280 recipe show a
development-scale native-performance increment over a central-input flat (CF) whose learning
rate was selected by the limited procedure of section 3? It compares two complete learning
methods; it does not show that the hierarchy is necessary and it does not measure the
interruption increment.

| Item | D1280 | CF: central-input flat |
| --- | --- | --- |
| Construction | the accepted D2 fixed-clock path; individual and team gaps numeric +infinity | ordinary `off` route then the `mappo` switch (`hmasd.baselines.apply_algorithm_config`): one constant team/individual skill; then explicit `k = 10` |
| High-level learning | standing coordinator batch 1280; original discriminator and credit semantics | coordinator and both discriminators never optimized; discriminator intrinsic rewards off |
| Holding and reaction | k 10, caps 10/10, age off; private recurrent primitive actor reacts every step | constant skill; reacts every step; each UAV holds its own GRU state |
| Flat-only design | this arm's inputs and recipe are unchanged | the legal central snapshot and ego identity below are wired into the actor; only the actor's input projection changes as needed |
| Tuning right | none; standing recipe | stage-0 three-point learning-rate multiplier only |
| Common conditions | Scenario 1, six fixed UAVs, fifty users, H500, native reward and termination, J = 6U/500, CPU FP32, four threads, 16 training lanes, the existing PPO and an independent evaluator | same, except the declared flat input and tuning differences |

**CF information interface (exact).** At the initial decision step after a lane reset and at
every k = 10 team-decision step the D arms use, the arm reads its own legal current global state
and the six joint observations ordered by fixed UAV identity and forms a central snapshot. The
snapshot is refreshed only at those steps; for the nine intervening steps the latest snapshot is
held and no new central variable is read. Each step's actor input is the UAV's latest private
observation, the latest central snapshot, a fixed six-dimensional ego one-hot, the constant
skill, and the UAV's own GRU state. Reset clears the lane's old snapshot and recurrent state and
rebuilds the snapshot from the new episode's initial information. Forbidden: future states,
future rewards, optimal actions, other arms' trajectories, or new environment internals.

The refresh limit is a prospective choice: the flat is not given a new central observation
every step, and the comparator's central coordination input is limited to the k = 10 cadence;
the central critic's input is not mistaken for an execution right. Both arms have the same
exogenous information source and the same central refresh opportunities, but D1280 encodes them
as discrete skills and CF as raw snapshot input, so representation, bandwidth use and learning
differ. This is a comparison of information organization and complete methods, not an isolation
of the hierarchy's causal effect. CF is named "central-input flat", never "private-actor MAPPO".

Kept unchanged: the actor's hidden width, continuous action head, critic input, PPO loss, and
primitive-time discount / GAE / termination semantics; no new encoder search, attention,
termination head or separate trainer beyond the projection the wider input needs. Continuous
quantities in the snapshot reuse the corresponding observation/state normalization semantics;
the ego identity has no running statistics. CF evaluates with its own final normalization state,
never copied from D1280 or another seed. The native reward is not rescaled for training.

**I1280 is not in this object.** SI45, HI45 and any "this card also confirms interruption" claim
are given up; they are not filled from old SI values. D1280 is this experiment's high-batch
fixed-clock reference; the historical U batch-128 default comparison is not replaced by the
words "authentic default".

## 2. Budget, endpoint, panels, units

- Every fit: 45 rollouts × 16 lanes × 500 steps = 360,000 training team steps, 720 training
  episodes, 45 update stages. One learning model and one independent evaluator per fit.
- Panels after updates 5, 10, 15, 20, 25, 30, 35, 40 and 45: the block's same 32 fixed world
  addresses, H500 deterministic, one panel each. Rollout 45 is the only primary endpoint; the
  other eight are curves. Each panel syncs the arm's weights and evaluation-mode normalizers,
  resets the evaluation environments, skill/timer/snapshot/RNN state, saves and restores the
  training RNG, and changes no training normalizer, buffer or other learning state. The RNG
  wrapper alone is not proof of that isolation.
- Common random numbers mean the design's initial exogenous world arrangement, not "same seed
  number gives the same trajectory". Different input shapes forbid claiming element-wise
  identical initialization; the shared random consumers that can be matched are declared, other
  consumption stays arm-local. Each evaluation pair shares world addresses; actions and native
  trajectories may differ. Seed numbers are prospective identities.
- No early stop on apparent convergence, no extension to a flat curve, no best-checkpoint
  selection, no sixth block, no tenth panel. 45 rollouts is a fixed resource condition, not a
  convergence proof.

## 3. Stage 0: the complete limited selection procedure

- Grid **λ ∈ {0.5, 1, 2}**, two independent training blocks per point, 45 rollouts each. For every
  parameter group of the CF actor and critic optimizers that actually train, the learning rate
  equals the standing rate × λ; an existing schedule, if any, is multiplied once on its output.
  Nothing else is tuned (optimizer attributes, entropy, widths, k, loss weights). Coordinator and
  discriminator fields are not tuning factors.
- Tuning training bases **772603, 772703**; evaluation bases **782603, 782703**. Each λ/seed fit
  constructs its own model, optimizer, normalizers, buffer, RNG and evaluator. Every candidate runs
  the same 45 rollouts and nine panels; selection uses only the mean of the candidate's two J45.
- **Selection rule.** The λ with the highest mean J45. If several share exactly the highest value,
  the first in the fixed order **1, 0.5, 2** among that maximal set wins (so a tie between 0.5
  and 2 above 1 selects 0.5). No post-hoc near-tie tolerance, no best-world/seed/interim-panel
  selection, no reruns. All six candidate results and the selection exposure are retained; the
  selected candidate's tuning score is not a final reference level.
- If any of the six planned fits is missing, non-finite, or has an integrity problem affecting
  the selection quantity, stage 0 is **`SELECTION_INCOMPLETE`**: no silent selection among the
  rest, no automatic fallback to 1×, no stage 1. Credible existing facts are kept; no automatic
  retry, replacement or reseeding. After all six complete, the unique λ and its basis are fixed in
  the stage-0 record **before any stage-1 fit or panel is read**.

## 4. Stage 1: five fresh independent confirmation blocks

Training bases **772803, 772903, 773003, 773103, 773203**; evaluation bases **782803, 782903,
783003, 783103, 783203**. Per block one D1280 and one CF instance trained from scratch at the
selected λ (CF) and the standing recipe (D1280). All confirmation fits run as planned regardless
of earlier scores; only real integrity, resource or platform limits change executability.

## 5. Quantities

```text
G_b = J45(D1280, b) − J45(CF_λ*, b)        b over the five confirmation blocks; J45 = mean of the 32 final world scores
Primary   mean(G) over five blocks (equal weight)
Report    the five G_b; the ten J45; each block's 32 ordered world differences with conditional SD/SE;
          s_G = sample SD of G_b, SE_G = s_G / sqrt(5), mean(G) ± t(.975, 4) × SE_G
Curves    G_r for r = 5 … 40, reported per rollout, never selected among, never pooled with older objects
Levels    per-arm J45 mean and SD (descriptive; never a substitute for the paired-difference SD)
Counts    positive, negative and zero blocks, listed, never used as a pass gate
```

The df = 4 interval uses the declared iid-normal paired-block working model; coverage is not
validated by five blocks; it is conditional on the stage-0 λ and excludes the variation of
rerunning the tuning. No three-arm pooled s, no df = 12, no 2s / 1s rule, no 4-of-5 gate. Two-arm
level SDs are descriptive only.

## 6. MEI and the pre-registered reading rule (complete; no result review for covered outcomes)

**MEI = .05 J absolute**, fixed by the node as the prospective development scale for this longer,
costly method choice: only a mean per-step weighted native-return increment of that size is
called a difference worth developing. It follows the host's cost-sensitive development scale
used before; it is not derived from an old SD, it is not a project-wide threshold, and it does not
re-judge the old .01 or other objects' .05 results. J includes coverage, quality and altitude;
.05 J is not "five coverage points". A newly measured SD changes only the precision report.

| Importance label | Sole numeric condition | Reading and fixed consequence |
| --- | --- | --- |
| **D_REFERENCE_ABOVE** | mean(G) > +.05 | the fixed D1280 recipe has a development-scale positive point difference on these five blocks; D1280 is retained as a locally supported comparison reference; a record for later use, no automatic interruption object and no default change |
| **SMALL_SIGNED** | −.05 ≤ mean(G) ≤ +.05 | the point difference is inside the interest interval, sign retained; no equivalence, no "the host needs no skills", no "no room to improve"; the object completes, no automatic extra training |
| **CF_REFERENCE_ABOVE** | mean(G) < −.05 | the selected CF shows a development-scale advantage over standing D1280 on these five blocks; weakens the case for this D1280 recipe at this budget; a bounded method-comparison record; no code-defect diagnosis, no withdrawal of historical FSD results |

Each row carries an **independent uncertainty label**: interval lower end > 0 → `INTERVAL_POSITIVE`;
upper end < 0 → `INTERVAL_NEGATIVE`; otherwise `INTERVAL_INCLUDES_ZERO` (an endpoint exactly zero
includes zero). Also recorded: whether the closed interval lies entirely inside [−.05, +.05]; if
so it is a small-magnitude reading under the working model, not equivalence.
`SMALL_SIGNED + INTERVAL_INCLUDES_ZERO + not inside MEI` is written as "small point estimate, true
magnitude and direction unresolved", never as "indistinguishable". A large point difference with a
wide interval is a large but imprecise difference, never "no effect". If s_G = 0 the degenerate
computation is reported as such.

**Incomplete or invalid branches are registered too.** `SELECTION_INCOMPLETE` (section 3) ends
the object's dependency chain. Fewer than five complete, comparable, finite stage-1 pairs, or a
defect touching reward, information, training/evaluation isolation, identity or the primary,
reads `PRIMARY_INCOMPLETE_OR_INVALID`: no filling of missing arms, no zero-difference imputation,
no dropping of negative blocks, no curve in place of J45; every credible completed arm, pair and
actual exposure is kept with its available n; n = 1 has no sample SD/SE. This branch is not a
negative result and authorizes no retry, seed replacement, extra panel or budget.

**When a result review is still needed.** The rule above reads every complete finite result,
mixed block signs, wide intervals, unflattened curves and the defined incomplete cases; the node
does not want to see every ordinary result. Only an event the rule does not cover that changes
the comparison's meaning, or a substantive DM objection to applying the rule, uses the lanes'
exception path. Disliking the sign, a wide interval, a boundary value or "not reaching .67" is
not "outside the rule".

**All branches end this object and keep the result.** Direction CLOSE, a hazard host, use of the
next window's budget or a default change can only be recommendations with evidence attached,
read at an owner-triggered review; no label executes them and no Portfolio question is sent.
The approved set's "headroom plus follow-up" exit wording is not rewritten by this card and does
not pre-authorize a second fit object.

## 7. Exposure and cost plan (plans, not caps)

| Quantity | Stage 0 (3 settings × 2 blocks, CF) | Stage 1 (2 arms × 5 blocks) | Total |
| --- | ---: | ---: | ---: |
| fits from scratch | 6 | 10 | 16 |
| training team steps | 2,160,000 | 3,600,000 | 5,760,000 |
| evaluation team steps | 864,000 | 1,440,000 | 2,304,000 |
| evaluation panels | 54 | 90 | 144 |
| update stages | 270 | 450 | 720 |
| learner/evaluator constructions | 12 | 20 | 32 |

D1280 coordinator work by the standing law: 15 calls per rollout, 675 per fit; CF 0. Actor and
critic optimizer calls about 101,250 per fit (linear from 33,750 at fifteen rollouts) are planned
values; acceptance uses the real counts. A wider input projection does not add steps but may add
per-step cost; equal update stages are not matched compute.

Cost law: `11 × whole_wall(CF45) + 5 × whole_wall(D1280_45) + necessary support`. Ordinary plan
(node's choice, prospective, not a measurement): CF about 12,000 s per fit (the private-FLAT
extrapolation with margin for the new input path), D1280 about 10,300 s; native sum about
183,500 s. Support, checks, publication, intake and provider cost stay UNKNOWN. The DM may
revise the ordinary plan from real code size, contention and completion records without a
profiling experiment; a plan change never changes a started 45-rollout endpoint. Stage 0 precedes
stage 1, per-arm RSS, scheduling gaps and admission bound the makespan; "sum divided by four" is
not a promise. CF's RSS and wall are unmeasured. This is **one** two-stage CONFIRM object inside
the direction's seven-day standing budget; no new Portfolio budget; a real shortfall is recorded
and handled under the owner's control, never hidden.

## 8. Implementation acceptance boundary (DM: L0)

The rejected card's "thin entry, no independent review" does not carry over. The CF input surface
must run through the real collector, stored/recurrent replay and the evaluator; cache identity,
refresh timing, normalization and reset must be consistent; a thin file's `ROLLOUTS = 45` proves
nothing unless the imported loop, panel schedule, summary and reducer actually read it.

- DM: runner `scripts/run_fsd_matched_information_baseline_b01.py` (thin entry over the B01
  runner for the loop, panel law and fit validation; arms `D1280` and `CF`; stage/λ arguments;
  `select-stage0` and `reduce` implementing sections 3 and 6 verbatim), the CF adapter gated by a
  config flag that is off for every other arm and object, launch script, tests.
- Tests kept local to the changed contract: central snapshot fields and refresh steps and lane
  reset; identical inputs in collection, replay and evaluator; CF optimizer multiplier applied to
  the active groups only and D1280 unchanged; every stage-0 tie case; 45/nine-panel binding;
  primary and uncertainty boundaries, zero variance, missing pairs and invalid selection. No full
  S rerun and no result-bearing smoke.
- Independent `hmasd-reviewer` review for the diff touching the actor input, numerics, RNG or
  result identity (lanes section 6); record-only or truly semantics-free thin-entry parts do not.
- Every fit: exact committed source, CPU FP32 four threads, remote-first WSL, fresh admission with
  physical and effective available memory ≥ 4 GiB, detached supervision, independent evaluator.
  No resource failure or incomplete output becomes a negative branch.

## 9. Not claimed

Hierarchy necessity; an upper reference; strict section 11.7 headroom; SI45/HI45 or any
interruption result; equivalence; code-defect diagnosis from CF_REFERENCE_ABOVE; anything about
.67 J (removed from this object's quantities, thresholds and curves); generalization beyond five
blocks; C-BENCH promotion; changes to the D0 default; lifecycle.

## 10. Predictions (DM, on record before any scientific output; owner slot open)

mean(G): D_REFERENCE_ABOVE .25, SMALL_SIGNED .50, CF_REFERENCE_ABOVE .25; INTERVAL_INCLUDES_ZERO
.80. The rejected card's predictions stay bound to its 2s rule and are not scored under this one.
