# ACVC M-deployment transfer B02 — prospective card (selected by `em:acvc:convergence`, 2026-09-15 result review; Portfolio investment pending)

Class **B/EXPLORE**, host the retained five-UAV cluster (`make_cluster`, H256, native J = S/256),
prepared 2026-09-15 by the Claude Code research hub acting as ACVC's DM under the owner's
12:57 PDT scope instruction. The object is the successor `em:acvc:convergence` fixed in its
result review of B01 ([response](pro_packets/20260915_m_deployment_transfer_result_review/archive/RESPONSE.md),
[intake](pro_packets/20260915_m_deployment_transfer_result_review/INTAKE.md), `PRO_FINAL`,
option B): **one unchanged repetition of the M-deployment transfer object on a new
independently initialised M fit.** This card grants nothing and launches nothing; the one fit
goes through a bounded Portfolio investment question before launch (§6).

## 1. Question and the choice it would change

B01 ([E0](ACVC_M_DEPLOYMENT_TRANSFER_B01_RESULT_EVIDENCE_20260915.md)) observed on one fresh
conventional proposer M that the complete fixed deployment transformation F adds an MEI-sized
mean increment, T_F = +.018338 J (53/64 worlds favorable, conditional SE .0055), while the
simpler own-dwell package adds +.00907 J and the paired F-over-dwell difference U = +.00927 J
stays inside the ±.01 J band. The open question is **recurrence**: does an observed useful
whole-package increment F(M)−M recur on another unscreened trained proposer, with the cheaper
dwell alternative retained in the same panels? The choice it changes is which deployment
package deserves further M-side development (F, dwell, or neither) and whether further
unchanged spending on this family is warranted. It does not ask whether C can be discarded,
does not compare F(C) with F(M), and does not resume or re-score the concluded two-block C/M
claim; it is not a third C/M block, a C-promotion object or training through an intervention.
Structure class (spec §11.7): *systems / information flow*.

## 2. Object: one new independently initialised M fit with three final panels

The complete accepted M recipe and wrapper semantics are retained byte for byte, not only by
name: clustered five-UAV/fifty-user host, true H256 termination, native S and J = S/256,
private actor 108 / GRU 64 and training-only critic 136, bounded tanh-action adapter,
recurrent buffer, γ .99 / GAE λ .95, four epochs / one minibatch / chunk 32, separate actor
and critic Adam at 3e-4 with ε 1e-5, ValueNorm and the recorded remaining loss/normalisation
settings (`cluster_mappo_comparison_b01/mappo.py`, pinned upstream `de66d7a4b`); CPU FP32
single-thread execution; `Binding`'s existing mixed-precision coordinate law
(`native_link_loss_b01/binding.py`). Nothing is transferred from the completed B01 fit: no
learned parameters, optimizer state, buffer or hidden state.

| Panel | Proposer | Per-tick law at the sole final snapshot | Counters |
| --- | --- | --- | --- |
| **M** | M_2 actor, actor-only inference (`mappo.evaluate`) | send the bounded proposal unchanged | none |
| **F(M)** | same actor, same snapshot | `Binding.observe` on the panel's own history flags link-loss opportunities; on a flagged agent send the retrace command derived from observed displacement, else the proposal | opportunities, substitutions, distinguishable |
| **own-dwell(M)** | same actor, same snapshot | same predicate on its own history; on a flagged agent send the zero command | opportunities, substitutions, distinguishable |

All three panels load the one sole-final snapshot after the final prescribed optimizer update
and own separate mutable episode state: environment, previous submitted command, hidden
state, masks, actor generator and, for the wrapped panels, a fresh `Binding` per episode. One
observe-and-draw per primitive tick even when substituting; the submitted command feeds the
next actor input; retracing derives from observed displacement, never from a negated proposal;
hold stays zero. No borrowed intervention schedule, no common mutable RNG, no extra M panel.
Equal reset and noise addresses couple exogenous inputs without equating subsequent
trajectories.

**Labels**, proposed without inspecting realisations and disjoint from 28331/38331,
28431/38431 and 28531/38531 (no repository-wide collision census or independence proof is
claimed): **MASTER 28631, evaluation namespace 38631**. Training resets
`100000·28631 + 1000 + e`, e = 0..4095; common within-instance panel resets
`100000·38631 + 2000 + e`, e = 0..63; a separate equal-seeded actor generator per panel and
episode at `100000·38631 + 5000 + e`; initialisation / training-motion / shuffle offsets
+131 / +121 / +141 under the new master; panel constructor offsets 65 / 66 / 67. Every consumer
is bound before model/configuration construction and again before reduction. Exactly **one**
original result-bearing invocation: retry, replacement, second new fit, tuning, pilot,
midpoint, changed checkpoint, extra evaluation or continuation-until-positive are zero. The
fit is included regardless of its sign, subject only to actual dependent integrity or
resource limitations.

## 3. Primary, MEI and reading rule

```text
Sole primary  T_F,2 = mean64[ J(F(M_2)) − J(M_2) ]
Supporting    T_D,2 = mean64[ J(own-dwell(M_2)) − J(M_2) ]
              U_2   = mean64[ J(F(M_2)) − J(own-dwell(M_2)) ]   direct worldwise vector, own SD/SE
              all three absolute panel means, every matched difference, SD, conditional SE,
              positive / negative / zero counts, extrema
```

MEI **.01 J** absolute, unchanged (2.56 episode-sum units of local development importance and
comparator continuity; not justified by a seed SD, a sign count or the new runtime). Reading
applied to the unrounded primary: `T_F,2 > +.01` **TRANSFERS** (recurrence of an MEI-sized
observed package increment; strengthens the case for further M-package development);
`−.01 ≤ T_F,2 ≤ +.01` **WITHIN_MEI** (useful-size recurrence not observed at this point scale;
preserve sign and uncertainty; reconsider further unchanged spending); `T_F,2 < −.01`
**ADVERSE** (a direct adverse instance; weakens unqualified M-wrapper use and favours the
unmodified M for that observed comparison); missing or invalid operand **INCOMPLETE** (no
dependent contrast, no imputation; independently trustworthy facts kept without replacement
authority). T_D,2 and U_2 are described at the same signed .01 scale; neither is co-primary. A
fresh TRANSFERS with U_2 inside the band still leaves dwell as a practical alternative; a
useful positive U_2 would strengthen the local preference for F over dwell while remaining a
package contrast; an adverse T_F,2 with useful T_D,2 favours the simpler intervention in that
instance. No outcome supplies a pure mechanism, equivalence, default or safety promotion,
tuned headroom or permission to discard C.

**No pooled performance verdict.** Read the fresh result on its own first, then display the
two M-transfer instances (B01 and B02) side by side with their T_F / T_D / U values and their
own conditional uncertainties. Neither is appended to the old C/M accumulation; the 128 worlds
are not pooled as training replicates; no best-instance or majority-vote rule; no aggregation
method chosen after seeing the second result. This deliberately limited repetition claims
recurrence or discrepancy of observed outcomes, not a precise training-population mean; two
fits leave population uncertainty unresolved, and no interval, bootstrap or sample-size
promise is added. Even two favourable observations would not entitle the family to more
compute; a negative observation would not erase the first.

Predictions (hub, on record before launch; owner slot `not taken (unattended)`): T_F,2
TRANSFERS .45, WITHIN_MEI .35, ADVERSE .20; T_D,2 UP .35, WITHIN .45, DOWN .20. Reason: one
favourable instance raises the hub's belief that the fixed rule helps a proposer that lacks
it, but B01's world-level spread (T_F from −.161 to +.170 J) and the sign reversal of F−M
across the two C/M blocks keep a within-band or adverse second instance plausible; dwell's
increment was inside the band once and is expected to stay small. B01's forecasts are not
revised.

## 4. Exposure and ordinary cost plan

| New B02 work | Amount |
| --- | ---: |
| Fresh training instances | 1 |
| Training episodes / team ticks | 4,096 / 1,048,576 |
| Two-episode rollouts / PPO minibatches | 2,048 / 8,192 |
| Actor / critic optimizer calls | 8,192 / 8,192 (16,384) |
| Sole-final panels / evaluation episodes / ticks | 3 / 192 / 49,152 |
| Total team ticks | 1,097,728 |
| Final snapshots / loads | 1 / 3 |
| Environment constructions (two training lanes + one per panel) | 5 |

The unchanged replay law entails 20,971,520 actor-agent rows and 20,971,520 repeated-agent
critic rows; the dominant work is the full training-and-update programme. **Ordinary plan
about 1,200 s whole-native wall** under scheduling comparable to B01's otherwise-idle
execution (measured 985.12 s wall, 983.51 s CPU, peak RSS 585,028 KiB; the panel phase timings
of about 12–14 s each are inside that total), rounded above the measurement; a planning
judgment, not a cap or guarantee. The older M walls (1,521.04 s and 2,427.41 s with one panel
under different contention) are resource context, not a prediction interval. Revise the plan
prospectively when actual node conditions differ; no profiling pilot, runtime gate or shortened
endpoint. Consultation exposure of this card: zero.

## 5. Minimal L0 (hub implements directly; independent review of changed behaviour before launch)

- **Reuse**: the accepted B01 runner `scripts/run_acvc_m_deployment_transfer_b01.py`, wrapped
  evaluator `experiments/candidates/acvc/m_deployment_transfer_b01/wrapped_eval.py`, reducer
  and the eleven focused tests under `tests/experiments/candidates/acvc/m_deployment_transfer_b01/`
  (launch source `a741758a1`), without redesigning training.
- **Changed binding only**: the new object / identity / destination binding for MASTER 28631 /
  namespace 38631 and the B02 evidence root (a thin B02 entry that binds the identities before
  any recipe import and delegates to the unchanged B01 code, or the equivalent parameterisation
  that leaves B01's recorded bytes untouched). **Focused check**: the new master / namespace /
  object identity reaches initialisation, training resets, action streams, the final panels and
  the reducer before use (the B01 review's material finding, reduce mode binding the identities
  too late, is the concrete risk). Reuse the no-op identity, actual-command feedback,
  private-history, panel-order and terminal checks for unchanged code; rerun or extend only the
  checks the change can affect.
- **Protected**: M training bytes identical to blocks 1–2 and B01; `Binding` unchanged; the M
  panel produced once by the unchanged evaluator; direct d_F / d_D / u reduction with
  strict/inclusive edges and incomplete-operand handling; real update / exposure accounting;
  one-checkpoint / three-load verification.
- **Acceptance**: focused binding test green; unchanged tests still green where rerun;
  independent review of the material changed behaviour (not a full source census); per-fit cost
  projection recorded; frozen launch command with fresh `admit-memory` (≥ 4 GiB physical and
  effective) joined by `&&` on the WSL node at a detached exact-sha worktree; launch only
  through `hmasd-experiment-operator`; no prelaunch native panel or model-selection smoke.

## 6. Investment and authority

The B01 one-fit grant is complete with no automatic second-fit or extension allowance. Per the
node, this one-fit B02 goes through the bounded Portfolio investment question
(`portfolio:cross_direction`) before launch; that does not make every future fit a separate
approval (spec §8.1 preserves ordinary in-scope work within a real standing delegation), but
no applicable allocation is shown and the review creates none. Under every outcome ACVC stays
ACTIVE/MEDIUM/recasts2 in its slot at the lowest sequencing priority; the two-block C/M claim,
both consumed C objects, failed alternatives and peer lifecycles are unchanged; no C
promotion, recast, lifecycle, priority or family change; completion ends only this allocation.

## 7. Node specification (`em:acvc:convergence`, 2026-09-15 result review, B, `PRO_FINAL`)

Fixed by the node and carried above: one new independently initialised M fit; the complete
recipe and wrapper semantics retained; labels 28631/38631 with the reset, generator and offset
scheme of §2; three sole-final panels with separate mutable state; sole primary T_F,2 with the
unchanged unrounded branches and INCOMPLETE; T_D,2 and direct paired U_2 supporting; per-instance
display beside B01 with no pooled verdict, no accumulation and no post-hoc aggregation; end
after the one original regardless of sign; exposure table of §4; ordinary plan about 1,200 s;
L0 reuse with the focused binding check; remote-first execution with fresh admission; the
Portfolio investment question before launch. Corrections the same review applied to B01's
records (U as a complete package contrast, T_F variability not inherited from the C-side
block dispersion, the M score ordering as description only) are in B01's E0 and in
`DIRECTION.md`.
