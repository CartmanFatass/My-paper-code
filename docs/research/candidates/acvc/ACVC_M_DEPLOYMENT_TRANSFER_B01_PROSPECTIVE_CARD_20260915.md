# ACVC M-deployment transfer B01 — prospective card (unfunded)

Class **B/EXPLORE**, host the retained five-UAV cluster (`make_cluster`, H256, native J = S/256),
prepared 2026-09-15 by the Claude Code research hub acting as ACVC's DM under the owner's
12:57 PDT scope instruction (derivation and innovation are the hub's; the convergence decision
is `em:acvc:convergence`'s). This is a proposal; it grants nothing and launches nothing. It makes
concrete the *best unlisted candidate* named in the node's 2026-09-15 decision
([response](pro_packets/20260915_post_block2_convergence/archive/RESPONSE.md), "a direct
M-based deployment test, not a certification sweep"), which that decision left unselected and
open to reconsideration before any further unchanged block.

## 1. Question and the choice it would change

The C/M family closed on the two-block claim that the fixed deployment transformation F
improves its own C proposer and its own-dwell control (F−C +.0475 / +.041 pooled J,
F−own-dwell +.0317 / +.022 pooled J) while F versus the untuned MAPPO-style proposer M is
unresolved and sign-unstable (+.0234 / −.0392 J). Every deployment increment measured so far
sits on the C proposer. The open question is **portability**: does the same transformation,
applied to the conventional private recurrent proposer M, produce a comparable increment?
The choice it changes is what to develop next if the direction reopens: M plus the fixed
transformation (a conventional trainer with a cheap deployment wrapper) versus the C package.
It does not ask whether C can be discarded; a direct F(C) versus F(M) replacement claim needs
its own comparison and is out of scope.

## 2. Object: one fresh M fit with three final panels

| Panel | Proposer | Per-tick law at the final snapshot | Counters |
| --- | --- | --- | --- |
| **M** | M actor, actor-only inference (`mappo.evaluate`) | send the bounded proposal `b = tanh(raw)` unchanged | none (as in blocks 1–2) |
| **F(M)** | same actor, same snapshot | `Binding.observe(obs, b)` flags link-loss opportunities; on a flagged agent send the retrace command `c`, else `b` | opportunities, retrace, distinguishable |
| **own-dwell(M)** | same actor, same snapshot | same mask; on a flagged agent send the zero command | opportunities, dwell, distinguishable |

The wrapper laws are the ones C's F and own-dwell panels use today
(`experiments/candidates/acvc/native_link_loss_b01/binding.py` `Binding`, and the substitution
in `native_link_loss_b01/learner.py` `collect`, lines 41–48): `Binding` consumes only the raw
observation and the proposed command and is proposer-agnostic; nothing in it references C's
skill, duration or coordinator structure. The executed command feeds back into the actor's
next observation (`last = sent`) exactly as M's evaluator already does (`mappo.py` line 196);
remaining hold stays 0 in every panel as it does for C, F, own-dwell and M today. M's
training recipe, adapter, buffer and optimizer law are byte-for-byte the block-2 recipe
(`cluster_mappo_comparison_b01/mappo.py`, upstream `de66d7a4b`); only the evaluation of two
additional panels is new. Each panel runs the same 64 common reset worlds and the same
per-episode actor noise stream (`100000·NS + 5000 + e`), so the three panels are matched
worlds that diverge only after the first substituted command.

Labels, chosen without inspecting realisations and disjoint from 28331/38331, 28431/38431
and 8961/8962: **MASTER 28531, evaluation namespace 38531** (training resets
`100000·28531 + 1000 + e`, e = 0..4095; panel resets `100000·38531 + 2000 + e`, e = 0..63;
environment constructor offsets 65 / 66 / 67 for M / F(M) / own-dwell(M)). Exactly **one**
original result-bearing invocation; retry, replacement, second fit, tuning, pilot, midpoint or
extra panels are zero. The fit is included regardless of its result.

## 3. Primary, MEI and reading rule

```text
Primary     T_F  = mean64[ J(F(M)) − J(M) ]          transfer increment of the retrace law
Supporting  T_D  = mean64[ J(own-dwell(M)) − J(M) ]  transfer increment of the hold law
            every absolute panel score and every matched-world difference
Descriptive T_F against the C-side increments on record: F−C +.0474962536 (block 2),
            block 1's F−C, pooled +.0411 J; reported side by side, never pooled
```

MEI **.01 J** absolute, the family's development-importance judgment, unchanged. Reading
applied to the unrounded primary: `T_F > .01` TRANSFERS (the fixed law adds an MEI-sized
increment on the conventional proposer in this instance); `−.01 ≤ T_F ≤ .01` WITHIN_MEI (a
small signed point observation, not equivalence and not non-transfer); `T_F < −.01` ADVERSE
(the law harms the conventional proposer in this instance). Conditional world SD/SE over the
64 matched differences are reported; one fit gives no training-population precision, so no
interval claims a population. What each outcome changes: TRANSFERS motivates a development
question "M plus the fixed transformation" and makes a later F(C) versus F(M) comparison
worth asking; WITHIN_MEI or ADVERSE bounds the portability hypothesis while preserving the
F(C) evidence. No outcome establishes stable superiority, that C can be discarded, tuned
headroom, equivalence or a mechanism.

Predictions (hub, on record; owner slot `not taken (unattended)`): T_F TRANSFERS .40,
WITHIN_MEI .30, ADVERSE .30; T_D UP .30, WITHIN .35, DOWN .35. Reason: the retrace law is
proposer-agnostic and addresses link loss the M proposer has no structure for, but M was
trained with feedback of its own commands and may respond worse than C to substituted ones.

## 4. Exposure and ordinary cost plan

One fit: 4,096 training episodes = 1,048,576 team ticks, 2,048 rollouts, 8,192 actor + 8,192
critic optimizer calls (16,384); three panels × 64 episodes = 192 evaluation episodes = 49,152
team ticks; **1,097,728 team ticks**, one snapshot, three final loads (the node's own
projection for this candidate, its table row "1 / 4,096 / 192 / 1,097,728 / 16,384 / 1 / 3").
Measured basis: block-2 M whole-command wall 2,427.41 s at peak RSS 585,504 KiB under heavy
node contention (block 1's M fit is the other measurement on record); the two extra panels are
actor-only inference over 32,768 ticks each, a small fraction of training. **Ordinary plan
about 2,600 s native wall, single thread, under 1 GiB RSS**; not a cap. Consultation exposure
of this card: zero.

## 5. Minimal L0 (hub implements directly; independent Opus review before launch)

- **Owned paths**: new `scripts/run_acvc_m_deployment_transfer_b01.py` (≤ 300 lines: binds the
  fresh labels the way `run_acvc_cluster_mappo_comparison_b02.py` `bind_block` does, delegates
  training to the unchanged M path, evaluates the three panels, publishes the summary and a
  `--mode reduce` readout with T_F, T_D, absolute scores, matched-world differences and the
  wrapper counters); new `experiments/candidates/acvc/m_deployment_transfer_b01/wrapped_eval.py`
  (an actor-only evaluation loop that reproduces `mappo.evaluate` tick for tick and inserts
  `Binding.observe` plus the F / own-dwell substitution; about 60–100 lines); focused tests
  under `tests/experiments/candidates/acvc/m_deployment_transfer_b01/`. **Read-only**:
  `native_link_loss_b01/binding.py`, `native_link_loss_b01/learner.py`,
  `cluster_mappo_comparison_b01/**`, the upstream `onpolicy` checkout, `hmasd/**`.
- **Facts fixed**: the F/own-dwell laws are not written against an abstract proposer; the
  coupling is the proposer call and `proposal_sample` in `collect` (`learner.py` line 32,
  `model.py` lines 79–83) and the arm-indexed RNG table in `model.py` `action_generators`,
  none of which the wrapped evaluator uses (it uses M's own `policy.act`, `tanh` adapter and
  per-episode generator, with `Binding` applied to the resulting proposal). Panel identity is
  checked by `protocol.panel` against the fresh namespace.
- **Protected**: M training bytes identical to block 2 (recipe, adapter, buffer, optimizer,
  ValueNorm handling); `Binding` unchanged; the M panel identical to `mappo.evaluate`
  (focused test: same actor, same seeds, identical 64 scores between `mappo.evaluate` and the
  wrapped evaluator with the substitution disabled); executed-command feedback in every panel;
  no critic or global input at evaluation; counters recorded per panel.
- **Acceptance**: focused tests green (identity of the unwrapped panel with `mappo.evaluate`
  on a synthetic adapter; substitution fires exactly on the `Binding` mask; RNG labels
  disjoint from every prior block; reduce label edges); reviewer findings resolved; per-fit cost
  projection recorded; frozen launch command with fresh `admit-memory` joined by `&&` on the
  WSL node; launch only through `hmasd-experiment-operator`.

## 6. Investment and authority

One fit outside the ended grant G; whether it fits the standing object-tier delegation or needs
a Portfolio investment question is for the node to say. Under every outcome: ACVC stays
ACTIVE/MEDIUM/recasts2 in its slot, the two-block claim and its label are unchanged, no C
promotion, no recast, no lifecycle, priority or peer change. Completion ends only this
allocation.
