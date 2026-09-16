# FSD host headroom B01 — prospective card (CONFIRM lane, unfrozen until the convergence round)

Class **B** under evidence spec section 11, lane **CONFIRM** (approved set v1, priority 1,
`docs/research/portfolio/APPROVED_SET.md`), host Scenario 1
(`envs.pettingzoo.scenario1.UAVBaseStationEnv`, six UAVs, fifty users, H500, J = 6U/500),
prepared 2026-09-16 by the Claude hub as FSD's DM. This card is the direction's first object under
the workflow lanes: it gets **one** Pro round, at freeze, with `em:flexible_skill_duration:convergence`;
its result is read by the rule in section 5 and needs no result review unless the outcome falls
outside that rule. It launches nothing until frozen and admitted.

## 1. Why this object, and what it would change

The direction has never measured headroom in the sense of evidence spec section 11.7: the gap
between an upper reference and a *tuned* same-information baseline on its host. Every FSD result
sits at 0.40 to 0.45 J against an achievable reference of about 0.67 J (foundations review
2026-09-14, section 3), and the only flat comparison on record (baseline × interruption B01,
2026-09-15) is an untuned private-actor reduction that nevertheless scored .04 J above both
hierarchy arms at rollout 15 with intervals including zero. The convergence node closed that
stage (20:27Z, option A) and named as a reopening fact "a same-information comparison with a
defined legal execution interface, method definition and ordinary cost". This card supplies it.

The choice it changes: whether FSD keeps studying interruption timing on this host at all.
Foundations review R1 states the three outcomes and this card pre-registers them (section 5):
the hierarchy beats a tuned flat by more than the seed noise (keep the host, confirm interruption
next); they are indistinguishable (the host does not reward skills at this budget; FSD moves to
CLOSE with the hazard-host recommendation of R2 queued for the owner's review); the flat wins
(implementation or tuning of the base is suspect; CLOSE with an engineering finding that bounds
every package claim the direction has made).

## 2. Arms (all implemented; no new learner code)

| Arm | Definition (unchanged from B01 card section 2) | Recipe |
| --- | --- | --- |
| **FLAT** | private-actor flat reduction of the same HMASD stack via `hmasd.baselines.apply_algorithm_config(config, "mappo")`: single constant skill, coordinator and discriminators never updated, `k = 10` chunking as the D arms (`run_fsd_baseline_interruption_b01.py`) | **tuned in stage 0** (section 3) |
| **D1280** | the direction's authentic D0 default at joint-row batch 1280, no interruption | standing recipe, untouched |
| **I1280** | the interruption recipe at joint-row batch 1280 (individual gap .25) | standing recipe, untouched |

The hierarchy arms are the studied object and keep their standing recipe; tuning them would
change the object. The flat arm is the baseline and is tuned, because section 11.7 headroom is
defined against a tuned baseline. Information matching (a central-input flat that receives the
global state the coordinator sees) is a different architecture question, recorded in the
2026-09-14 restart-preparation intake as an option; it is not part of this card. The
private-actor reduction is the natural "drop the hierarchy" comparator of R1(b): the same
stack minus skills, with the same actor, critic, optimizer, chunking and exposure.

## 3. Budget, endpoint, panels, units

- **Training length: 45 rollouts of 16 lanes × H500 = 360,000 team steps per fit**, three times
  the longest FSD run on record (B01: 15 rollouts) and nine times the completed factorial. The
  main-branch reference of 5 × 10^6 steps (`experiments/launchers/main.py` default) is not
  affordable on the CPU node (an I1280 fit would take about 74 hours); the card measures the gap
  at 360,000 steps and reports every arm's absolute level against the 0.67 J reference as context.
- **Panels: the same 32-world H500 deterministic panel after every 5 rollouts** (nine panels,
  rollouts 5 to 45) from one evaluator synced from the learner, inside the RNG-preserving
  wrapper exactly as in B01. Rollout 45 is the endpoint; the other eight panels are declared
  learning-curve points and are never selected among.
- **Independent units: training seeds (blocks).** Within a block the three arms share initial
  lane schedules as before; nothing is shared across blocks. Panel worlds are nested endpoint
  conditions, never replicates.
- **Stage 0 (flat tuning, EXPLORE-style inside this card):** FLAT at three learning-rate
  multipliers {0.5×, 1×, 2×} of the standing recipe, two seeds each (blocks 772603, 772703;
  evaluation bases 782603, 782703), 45 rollouts. Selection rule, fixed now: the multiplier with
  the highest mean J45 over the two seeds; ties go to 1×. Nothing else is tuned. The two tuning
  seeds are excluded from stage 1.
- **Stage 1 (confirmatory):** FLAT at the selected multiplier, D1280 and I1280, **five fresh
  seeds each** (blocks 772803, 772903, 773003, 773103, 773203; evaluation bases 782803 …
  783203). Fifteen fits.

## 4. Quantities

```text
Headroom   H_45  = J45(D1280) − J45(FLAT_tuned)     per seed, five seeds, mean, SD, t-interval df = 4
           HI_45 = J45(I1280) − J45(FLAT_tuned)     same
Interrupt  SI_45 = J45(I1280) − J45(D1280)          same
Curves     H_r, HI_r, SI_r for r = 5 … 40            reported per rollout
Levels     J45 per arm, mean and SD, against 0.67 J  context only
Noise      s = pooled across-seed SD of J45 over the three stage-1 arms (df = 12)
```

Contrasts are paired by seed because arms share lane schedules within a block.

## 5. Minimum effect and pre-registered reading rule

**MEI: .08 J absolute**, the recorded block-to-block SD of an arm level on this host (B01: .079 J
at rollout 15), as the workflow lanes require for CONFIRM. The reading rule uses the SD measured
in this study, which supersedes the prior value once observed:

| Reading of H_45 (primary) | Condition | Consequence (pre-registered; no result review) |
| --- | --- | --- |
| **HIERARCHY_ABOVE** | mean H_45 > +2s and H_45 > 0 in at least 4 of 5 seeds | the host rewards the hierarchy at this budget; FSD stays in CONFIRM and its next card is interruption timing at this budget with SI as primary |
| **INDISTINGUISHABLE** | mean H_45 inside ±1s | the host does not reward skills at this budget; FSD moves to lane CLOSE with a closing memo recommending the hazard host of foundations review R2, queued for the owner's review |
| **FLAT_ABOVE** | mean H_45 < −2s and H_45 < 0 in at least 4 of 5 seeds | base tuning or implementation of the hierarchy is suspect; CLOSE with an engineering finding; every FSD package claim on record is bounded by it |
| **UNRESOLVED** | anything else | recorded as such; a further seed tranche is not automatic and goes to the owner's review |

SI_45 is read with the same 2s / 1s rule and reported beside H_45; a positive SI_45 signal with
HIERARCHY_ABOVE is the direction's first confirmatory interruption result. HI_45 is context. No
pooling with B01 or the factorial; the B01 rollout-15 values are displayed beside the rollout-15
panel of this study as a replication datum only.

Predictions (hub, on record; the owner may add a prediction before freeze): H_45 INDISTINGUISHABLE
.45, FLAT_ABOVE .25, HIERARCHY_ABOVE .15, UNRESOLVED .15; SI_45 signal-positive .20.

## 6. Exposure and cost projection (plans, not caps)

| Quantity | Stage 0 (6 fits) | Stage 1 (15 fits) | Total |
| --- | ---: | ---: | ---: |
| training team steps | 2,160,000 | 5,400,000 | 7,560,000 |
| evaluation team steps (9 panels × 32 worlds × 500) | 864,000 | 2,160,000 | 3,024,000 |
| model constructions | 12 | 30 | 42 |

Walls scale linearly from B01's measured whole-command walls at 15 rollouts (FLAT 2,020–2,590 s,
D1280 2,620–3,430 s, I1280 5,050–6,550 s; peak RSS 1.25 / 2.8 / 3.8 GiB): per fit FLAT ≈
6,100–7,800 s, D1280 ≈ 7,900–10,300 s, I1280 ≈ 15,100–19,700 s. Native wall sum ≈ 40,000–47,000 s
(stage 0) plus 145,000–190,000 s (stage 1); with four fits concurrent on the 20-core node
(memory allows one I1280 beside three others) the makespan is about 3–4 h plus 12–16 h. CPU
≈ 4 × wall. This is one CONFIRM object inside the direction's seven-day standing budget.

## 7. Minimal L0 (hub implements directly; self-review plus tests, section 7.3 review not needed)

1. Thin entry `scripts/run_fsd_host_headroom_b01.py` importing `run_fsd_baseline_interruption_b01`
   and rebinding `ROLLOUTS = 45`, `PANEL_ROLLOUTS = (5, 10, …, 45)`, the seven new blocks, a
   `--lr-multiplier` argument applied only to the FLAT arm's optimizer learning rates, and an
   output identity naming stage, arm, block and multiplier. No learner, environment, RNG or
   evaluation code is touched.
2. `--mode reduce` over stage-1 summaries: paired contrasts, pooled s, the section 5 labels, the
   curve table, and the stage-0 selection record (which multiplier, both seed means).
3. Tests under `tests/experiments/candidates/flexible_skill_duration/`: binding (45 rollouts, nine
   panels, block identities, multiplier applied only to FLAT), reduce rule (label boundaries at
   exactly 2s and 1s with zero-based fixtures, the 4-of-5 sign count), and a stage-0 selection
   tie case.
4. Launch: two `agent-task` waves through `hmasd-experiment-operator` with admission before each
   fit; stage 0 first; the selected multiplier written into `stage0/SELECTION.json` before any
   stage-1 FLAT launch.
5. Records at completion: E0 (rule applied verbatim, counts, walls), `summary.json`, intake with
   the section 5 branch applied, brief, ledger row (selection, real alternative). Retained
   originals preserved locally before remote reclamation, as for B01.

## 8. Not claimed

Population means beyond five seeds; equivalence; tuned headroom against the 5 × 10^6-step
reference; anything about information-matched flats; any interruption result unless SI_45 meets
the rule; C-BENCH promotion; changes to the authentic D0 default.

## 9. Freeze record

**Rejected 2026-09-16 05:19Z by `em:flexible_skill_duration:convergence` (option C, PRO_FINAL; response `1462d3954`,
sha256 0e9f6ca308ef8bd70d68836708a1db71faeae26a1f378f3eff60b1f42ac7fc66).** Superseded by
[FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md](FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md): the private-actor FLAT is not a same-information baseline, the 2s / 1s rule and the
.67 J reference are withdrawn, I1280 is dropped. This card is kept as the rejected draft; its predictions are not scored.

Original text of this section: To be filled by the convergence round (packet
`pro_packets/20260916_host_headroom_card_convergence/`): the node may correct arms, the
tuning grid, the seed count, the rule constants or the branch consequences; corrections are
applied with dated markers before freeze.
