# ACVC matched-package comparison B01 — prospective card (for `em:acvc:convergence` to select and fix; Portfolio G3 envelope)

Class **B/EXPLORE**, host the retained five-UAV cluster (`make_cluster`, H256, native J = S/256),
prepared 2026-09-15 by the Claude Code research hub acting as ACVC's DM under the owner's
12:57 PDT scope instruction. `em:acvc:convergence` concluded the M-deployment transfer family
(A, [intake](pro_packets/20260915_m_deployment_transfer_b02_result_review/INTAKE.md)) and carried
"a fresh matched F(C) versus F(M) pair" to Portfolio as the strongest distinct alternative;
`portfolio:cross_direction` funded it (P1 with an inclusive ceiling, **G3**,
[decision](../../portfolio/decisions/2026-09-15-acvc-direction-investment-lifecycle.md)) and left
the object for the direction node to select and fix. This card is the DM's derivation of that
object inside the G3 envelope. It grants nothing and launches nothing; **the node fixes the
estimand, comparator specification, labels, pairing, panels and reading rule** (§7) before any
L0, review or launch.

## 1. Question and the choice it would change

Two complete proposer-packages exist on this host: the retained ACVC coordinator C deployed
through the fixed link-loss transformation F, **F(C)**, and the declared flat recurrent
MAPPO-style recipe M deployed through the same transformation, **F(M)**. The concluded C/M
blocks compared F(C) with unwrapped M (D1 +.02344 J, D2 −.03919 J: sign-unstable) while F(C)
beat its own C and own-dwell in both blocks; the concluded transfer instances compared F(M) with
unwrapped M on two fits (T_F +.018338 J TRANSFERS, +.002859 J WITHIN_MEI). Neither family
compared the two complete packages with each other on one matched block, and historical absolute
scores from different fits and panels cannot substitute (Portfolio, G3). The open question is
**replacement**: on one fresh prospectively paired training block, which complete package,
F(C) or F(M), attains the higher native return on the common final worlds, and by how much
relative to the .01 J importance scale? The choice it changes is **which package to develop
further** (the coordinator-side F(C), the conventional-proposer-side F(M), or neither with a
clear preference). It does not re-score or reopen the C/M blocks or the transfer instances,
does not test transfer, recurrence, opportunity-level mechanism or training through F, and does
not ask whether C or M is a competent tuned baseline. Structure class (spec §11.7): *systems /
information flow*.

## 2. Object: one fresh matched block, one C fit and one M fit, six sole-final panels

**One prospectively paired programme block, MASTER 28731 / evaluation namespace 38731**, with
exactly one fresh C fit and one fresh M fit of the unchanged recipes. The complete accepted C
recipe (reviewed DENSE64/GRU64 and 128×128 team critic, Monte-Carlo return / agent-compound PPO,
four ordered full-rollout replay epochs / chunk 32, shared joint Adam 3e-4 / ε 1e-8, entropy .01,
no ValueNorm, duration support (1, 4), renewal False, sampled velocity;
`cluster_mappo_comparison_b01/c_fit.py`) and the complete accepted M recipe and wrapper semantics
(private actor 108 / GRU 64, training-only critic 136, bounded tanh-action adapter, recurrent
buffer, γ .99 / GAE λ .95, four epochs / one minibatch / chunk 32, separate actor and critic Adam
at 3e-4 with ε 1e-5, ValueNorm; `cluster_mappo_comparison_b01/mappo.py`, pinned upstream
`de66d7a4b`) are retained byte for byte. CPU FP32 single thread; `Binding`'s existing
mixed-precision coordinate law (`native_link_loss_b01/binding.py`). Nothing is transferred from
any completed fit: no learned parameters, optimizer state, buffer or hidden state.

Each fit trains 4,096 complete native H256 episodes (two episodes per rollout, 2,048 rollouts,
8,192 PPO minibatches; C 8,192 joint optimizer calls, M 8,192 actor plus 8,192 critic calls) and
keeps one sole-final snapshot after the final prescribed update. Training episode e in both arms
resets at `100000·28731 + 1000 + e`, e = 0..4095. M initialisation / training-motion / shuffle
offsets +131 / +121 / +141 under the new master, as in every prior block.

| Panel (64 worlds each) | Proposer at the sole final snapshot | Per-tick law | Source |
| --- | --- | --- | --- |
| **C** | C actor, unwrapped | send C's proposal | C arm, existing panel law |
| **F(C)** | same C snapshot | `Binding.observe` on the panel's own history flags link-loss opportunities; on a flagged agent send the retrace command derived from observed displacement, else the proposal | C arm, existing panel law |
| **own-dwell(C)** | same C snapshot | same predicate on its own history; flagged agent sends the zero command | C arm, existing panel law |
| **M** | M actor, actor-only inference | send the bounded proposal unchanged | M arm (transfer runner) |
| **F(M)** | same M snapshot | the same `Binding` law as F(C), on this panel's own history | M arm (transfer runner) |
| **own-dwell(M)** | same M snapshot | the same dwell law as own-dwell(C) | M arm (transfer runner) |

All six panels use the **common reset addresses `100000·38731 + 2000 + e`, e = 0..63**, so
world e is the same exogenous world for every package (the matching); each panel owns separate
mutable episode state (environment, previous submitted command, hidden state, masks, actor or
action generator; a fresh `Binding` per episode for the wrapped panels); the actor generators of
the M-side panels sit at `100000·38731 + 5000 + e`; constructor offsets 62 / 63 / 64 (C arm) and
65 / 66 / 67 (M arm) are distinct. Equal reset and noise addresses couple exogenous inputs
without equating subsequent trajectories. The F law is one function applied to two proposers,
not a shared event schedule: neither wrapped panel borrows the other's opportunities, anchors,
displacement, commands or intervention counts. Labels are proposed without inspecting
realisations and are disjoint from 28331/38331, 28431/38431, 28531/38531, 28631/38631 and
8961/8962 (no repository-wide collision census or independence proof is claimed).

**Why six panels.** The two package panels F(C) and F(M) carry the primary. The four unwrapped
and dwell panels are produced by the accepted runners without any code change, cost 65,536
scored ticks inside the G3 ceiling, and supply the supporting decomposition on the same block
(F(C)−F(M) = (F(C)−C) + (C−M) − (F(M)−M), an arithmetic identity on matched rows, not an
attribution). Dropping them would require changing accepted evaluator code to save about 3 % of
the exposure; the DM recommends keeping all six. They do not turn this object into a third C/M
block: the C/M family is concluded, its primary F(C)−M is reported here only as a supporting
contrast on a new block and is never accumulated with D1/D2.

Exactly **two** original result-bearing invocations, one per arm. Retry, replacement, third fit,
tuning, pilot, native smoke, midpoint, changed checkpoint, extra panel or continuation until a
preferred sign are zero. Both originals are included regardless of the first result, subject
only to actual dependent integrity or resource limitations. No result-dependent successor.

## 3. Primary, MEI and reading rule

```text
Sole primary   P  = mean64[ J(F(C)) − J(F(M)) ]                 matched worlds e = 0..63
Supporting     C−M, F(C)−C, F(M)−M, F(C)−own-dwell(C), F(M)−own-dwell(M), own-dwell(C)−own-dwell(M)
               all six absolute panel means, every matched worldwise difference vector, sample SD,
               conditional SE, favorable / adverse / zero counts, extrema
```

MEI **.01 J** absolute, unchanged (2.56 episode-sum units of local development importance and
comparator continuity; not justified by a seed SD, a sign count or the runtime). Reading applied
to the unrounded primary: `P > +.01` **F_C_ABOVE_MEI** (the coordinator-side package attains an
MEI-sized advantage on this block; development advice favours F(C)); `−.01 ≤ P ≤ +.01`
**WITHIN_MEI** (no MEI-sized preference between the packages at this point scale; a small signed
observation, not equivalence; the cheaper or simpler package becomes the practical default
consideration); `P < −.01` **F_M_ABOVE_MEI** (the conventional-proposer package attains the
advantage; development advice favours F(M)); a missing or invalid operand **INCOMPLETE** (no
dependent contrast, no imputation; independently trustworthy panel facts remain reportable at
their own ceiling). Supporting contrasts are described at the same signed .01 scale; none is
co-primary and a favourable support never replaces the primary. A F_C_ABOVE_MEI with F(C)−C
inside the band, or a F_M_ABOVE_MEI with F(M)−M inside the band, says the winning package's
advantage comes from its proposer rather than from the transformation on that block; the primary
still decides the package question. No outcome establishes stable superiority, a
training-population mean, a discardable C or M, tuned headroom, equivalence, a K/N/retrace/memory
mechanism, C promotion, default change or safety claim.

**No pooling.** One block yields conditional-world precision for two attained fitted policies
and no empirical training-population precision. The result is read on its own and displayed
beside the concluded C/M blocks and transfer instances as labelled context only: no
accumulation with D1/D2 or T_F,1/T_F,2, no 128- or 192-world pooling, no best-instance or
majority rule, no aggregation chosen after the outcome.

Predictions (hub, on record before launch; owner slot `not taken (unattended)`): P
F_C_ABOVE_MEI .20, WITHIN_MEI .15, F_M_ABOVE_MEI .65. Reason: F(C) attained .3572 and .3550 J on
the two C/M blocks while the four fitted M instances attained .3338, .3942, .3786 and .4292 J
unwrapped and F(M) added +.018 and +.003 J on the two wrapped instances; three of the four M
instances already exceed F(C)'s observed level before wrapping, but one instance did not and the
between-fit spread of M is the largest source of uncertainty. Supporting C−M: UP .15, WITHIN .15,
DOWN .70; F(C)−C: UP .80, WITHIN .15, DOWN .05; F(M)−M: UP .40, WITHIN .45, DOWN .15.
Completeness forecast .90.

## 4. Exposure and ordinary cost plan (inside the G3 ceiling)

| New work | Amount |
| --- | ---: |
| Fresh training instances | 2 (one C, one M) |
| Training episodes / team ticks | 8,192 / 2,097,152 |
| Two-episode rollouts / PPO minibatches | 4,096 / 16,384 |
| Optimizer calls | 24,576 (C 8,192 joint; M 8,192 actor + 8,192 critic) |
| Sole-final panels / evaluation episodes / ticks | 6 / 384 / 98,304 |
| Total scored team ticks | **2,195,456** (= the G3 inclusive ceiling) |
| Final snapshots / loads | 2 / 6 |
| Environment constructions | C arm 2 + 3, M arm 2 + 3 |

Dominant work is the two full training-and-update programmes (each actor replays 20,971,520
agent rows). **Ordinary plans: C about 2,600 s, M about 1,200 s whole-native wall** on an
otherwise idle node (Portfolio's initial judgments; C measured 1,670.62 s beside one fit and
2,495.72 s beside four; M 985.12 / 989.80 s alone with three panels). Launching the two originals
concurrently, as in blocks 1–2, is allowed and lengthens both walls (about 2.3 versus 0.9 ms per
tick observed under contention); sequential C-then-M is the default if the node is otherwise
loaded. Plans are judgments, not caps or gates; revise them prospectively from node conditions.
No profiling pilot. Consultation exposure of this card: zero.

## 5. Minimal L0 (hub implements directly; independent review of changed behaviour before launch)

- **Reuse without redesign**: the accepted comparison runner
  `scripts/run_acvc_cluster_mappo_comparison_b01.py` (C arm: fit, snapshot, C / F / dwell panels)
  and the accepted transfer runner `scripts/run_acvc_m_deployment_transfer_b01.py` (M arm: fit,
  snapshot, M / F(M) / dwell(M) panels), their evaluators and focused tests; the protocol's
  `contrast`, `panel` and `fit_eligible` helpers.
- **Changed binding only**: one thin entry `scripts/run_acvc_matched_package_comparison_b01.py`
  with `--arm C|M` that binds MASTER 28731 / namespace 38731 / object / card into the protocol
  (C arm, as the block-2 wrapper did) or into the transfer runner's module globals (M arm, as the
  B02 thin entry did) **before any recipe import**, refuses any other `--seed`, and delegates to
  the unchanged code; plus `--mode reduce --c-summary --m-summary` computing the primary and the
  six supporting contrasts from the two summaries' `panels[*].scores_J` with the existing
  `contrast` helper, refusing mismatched identities and marking INCOMPLETE without imputation.
  Two launch scripts naming the thin entry and `--seed 28731`.
- **Focused checks**: identities reach initialisation, training resets, action streams, all six
  panels and the reducer before use (the transfer B01 review's material finding); early recipe
  import refused; reducer on synthetic summaries reproduces the primary and the identity
  `P = (F(C)−C) + (C−M) − (F(M)−M)` on matched rows; INCOMPLETE on a missing panel; launch scripts
  name the runner. Unchanged tests rerun only where the binding can affect them.
- **Protected**: C and M training bytes identical to blocks 1–2 and B01/B02; `Binding` unchanged;
  panel laws unchanged; direct matched reductions with strict/inclusive edges; real
  update/exposure accounting; two-snapshot / six-load verification.
- **Acceptance**: focused tests green locally and on the node; independent `hmasd-reviewer`
  review of the changed behaviour; per-arm cost projection recorded; two frozen launch commands,
  each with fresh `admit-memory` (≥ 4 GiB physical and effective) joined by `&&` on the WSL node
  at a detached exact-sha worktree (the M arm with the re-staged pinned on-policy root); launch
  only through `hmasd-experiment-operator`; no prelaunch native smoke.

## 6. Investment and authority

Funded by G3 (`PRO_FINAL / OWNER_DELEGATED`, 2026-09-15 23:31Z): at most one fresh C fit and one
fresh M fit, inclusive ceiling 2,195,456 scored team ticks with at most six 64-world panels,
zero automatic retries, replacements, third fits, additional panels or extensions; unused
allowance expires; completion ends the allocation, not ACVC. The node's conforming card needs no
second Portfolio permission or Root ratification. Under every outcome ACVC stays
ACTIVE/MEDIUM/recasts2 in its slot at the lowest sequencing priority; the two-block C/M claim,
both transfer instances, consumed C objects, failed alternatives and peer lifecycles are
unchanged; no C promotion, recast, lifecycle, priority or family change.

## 7. What the node is asked to fix (open points, DM recommendation first)

1. **Estimand and label**: P = mean64[J(F(C)) − J(F(M))] with the F_C_ABOVE_MEI / WITHIN_MEI /
   F_M_ABOVE_MEI / INCOMPLETE branches at unrounded ±.01 J (recommended), or another primary.
2. **Panel set**: all six panels from the unchanged runners (recommended; exactly the ceiling),
   or only the two package panels plus the two unwrapped panels (2,162,688 ticks; requires an
   evaluator change on the C side), or the two package panels alone (2,129,920 ticks; requires
   changes on both sides).
3. **Supporting contrasts and their reading**: the six listed in §3 at the same signed .01 scale,
   with the decomposition identity reported as arithmetic only (recommended), or a smaller set.
4. **Labels and pairing**: 28731/38731 with the reset, generator and offset scheme of §2
   (recommended), or corrected labels.
5. **Development-advice mapping of the three branches** (§3) and any correction to the DM's
   prediction reasoning.
6. **Launch order**: concurrent originals allowed with sequential C-then-M as the loaded-node
   default (recommended), or strictly sequential.
