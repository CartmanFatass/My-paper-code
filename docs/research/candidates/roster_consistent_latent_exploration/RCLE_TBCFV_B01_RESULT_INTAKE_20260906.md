# RCLE-TBCFV-B01-PERSIST-VS-FLEX result intake — 2026-09-06

Card `RCLE_TBCFV_B01_PERSIST_VS_FLEX_SCIENCE_CARD_20260906.md` (B/EXPLORE, opened by the archived
first-B Innovator decision, `PRO_FINAL`, intake `RCLE_TBCFV_FIRST_B_INNOVATOR_INTAKE_20260906.md`);
CM record `RCLE_TBCFV_B01_CM_RECORD_20260906.md`; launch sha `4d40621e0a9abd26e783e8c8aeeaf2653e49cf6a`;
evidence `b01_tbcfv_20260906/` (arm and reference summaries, executability summary, receipts,
timings, launch scripts, task logs). Direction Manager: the Claude research hub. Predictions
scored in §4.

## 1. Execution facts (observation)

- Node `wsl_4070`, worktree `rcle-b01-4d40621`, single CPU thread, exact committed source. The
  POSIX native build branch (added by Grok Build inside platform conditionals; Windows build key
  verified unchanged by `hmasd-reviewer`) compiled with `g++-13` and the `/fp:strict`-equivalent
  flags; the Linux oracle tests (`test_native_host.py` exact structural equality against the
  Python oracle) plus the B01 tests: 23 passed in 3.84 s. Preparation chain
  (`agent-task rcle_b01_prep_20260906`): build 5.09 s, tests 3.84 s, executability `COMPLETE`
  (64 scripted episodes, 4,096 ticks, 0.057 s, preparation digests `59a32b3c…` / `466f5ff7…`
  as derived in the CM record); whole chain 11 s. A second native build into the default root is
  paid by the arms and validated by their own `native` block (disclosed in the CM record).
- Arm chain (`agent-task rcle_b01_arms_20260906`, 20:56:04Z, exit 0, 138 s): C1P1 `COMPLETE`
  62.0 s wall / 61.9 CPU-s / peak RSS 582 MB; FLEX `COMPLETE` 69.8 s / 69.7 CPU-s / 585 MB;
  INDEPENDENT-NEAREST reference `COMPLETE` 1.49 s. Each arm: 200 completed updates, 200 nonzero
  updates, zero-update incidence 0, `parameter_delta_norm` 0.0005 on every update, 2,048
  held-out scenarios (8 cells × 256), all eight cells evaluated; memory admission passed before
  every step (15.67 GB available). The FLEX arm validated the C1P1 summary before training
  (same object, seed 17, block digest `a67b0144…`, 200 updates, 256 episodes per cell).
- Block digest `a67b014451fa8d614c191e82f2e20ded2d8f77f21098dcb52d2744e64d596048` (seed 17), identical
  initial parameters in both arms (norm 21.186038495201018); final L2 displacement
  0.005124953442186519 (C1P1) and 0.005124967677931276 (FLEX).
- Cost against the card: 5,400 s pair budget, 2,700 s per arm (runner cap 2,600 s): used 11 s
  preparation + 62.0 + 69.8 + 1.5 s = **144.3 s**. No stop, no retry.

## 2. Frozen rule applied verbatim and the observed readout

Primary `Δτ_B01` = mean over the two ACTIVE_CONTINUATION paths of (FLEX − C1P1) τ; companions U and
40U on the same paths; τ, U, Y on all eight cells; reference row INDEPENDENT-NEAREST.

| Path (ACTIVE_CONTINUATION) | C1P1 τ mean | FLEX τ mean | FLEX − C1P1 | τ=40 fraction (both) | C1P1 U | FLEX U | ΔU | reference τ / U |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8→12 | 40.0 | 40.0 | 0.0 | 1.0 | 0.6929 | 0.6929 | 0.0 | 39.70 / 0.244 |
| 12→8 | 40.0 | 40.0 | 0.0 | 1.0 | 0.7181 | 0.7181 | 0.0 | 39.22 / 0.302 |
| **Δτ_B01** | | | **0.0** (SE 0.0) | | | | **0.0** | |

All eight held-out cells: τ = 40.0 in every one of the 2,048 episodes of each learned arm
(τ=40 fraction 1.0 everywhere); U 0.692–0.722, Y 0.281–0.310, F 0.247–0.335; **every per-cell
mean and every one of the 2,048 paired scenarios is identical across the two arms to all printed
digits.** The reference row: τ=40 fractions 0.95–1.0 (τ means 38.8–40.0), U 0.233–0.336, F
0.233–0.319, Y null (scripted package has no Y). Training curves (200 per arm, all kept):
episode Y mean 0.287 at update 1 and 0.289 at update 200 in both arms; per-cell τ mean 40.0
throughout; the curves are identical between arms.

## 3. Reading under the card's rule

- **Rule rows that apply.** Row 3 (inside τ ±4 and U ±0.05: no material difference claimed) and
  row 4 ("τ almost all 40": mixed/undecided; U and curves keep their own meaning). Both apply
  at their extreme: the difference is exactly zero and τ is 40 in every episode of both arms.
  Not inferred: equivalence, zero effect, the original C's no-material branch, closing RCLE,
  "persistent state has no value" at any N or budget.
- **Why the arms are identical (engineering fact, from a read-only code check, not a
  reproduction).** The FLEX pathway executed: it is wired into the actor's claim probabilities
  (`empirical_runner.py` `_draw_claims`) and only FLEX's forward graph reaches the two
  zero-initialized update heads; the two arms' parameter trajectories differ at the 1.4e-8
  level, so the treatment ran. But the registered update is a fixed-norm 0.0005 step per update
  (direction-normalized, independent of gradient magnitude), so 200 updates displaced the
  26,161-scalar policy by 0.0051 from norm 21.19 (path bound 0.1); the FLEX heads receive
  gradient only through the four ACTIVE_CONTINUATION training cells; and discrete claims are
  drawn by inverse-CDF sampling against uniforms whose hashed address does not include the arm
  (the card's "the arm name selects no RNG substream"), so a different claim requires the tiny
  probability perturbation to straddle the shared draw, which did not happen in any of the
  roughly 10^5–10^6 decisions. Identical τ/U/F/Y is therefore expected by construction at this
  budget; it is not a wiring failure and is not quarantined. The learned arms sit far above the
  scripted nearest-beacon reference in unserved demand (U 0.69–0.72 versus 0.23–0.34) and never
  reach the four-tick recovery condition: at 200 fixed-norm updates the policy remains a
  near-initialization six-way claim distribution, as the node's prospective judgement allowed
  ("both arms may barely learn at 200 fixed-norm updates").
- **What the result decides.** The persist-versus-flex question is undecided at this exposure
  and update law; it is not evidence for or against the persistent plan. The card's default
  follow-up (one independent paired seed at the same budget) would reproduce the same identity
  for the same mechanical reason and is **not** warranted: another seed changes the shared
  draws but not the fixed-norm step or the zero-initialized heads. A larger budget, a different
  step law (for example a plain learning rate without direction normalization) or a warm-started
  FLEX head is a new outcome-informed object with its own card, and the choice among them, or
  parking, is a direction-tier question.
- **Ceiling.** One paired training replicate; the identity is a property of this budget and
  update law on this host, not of the packages; the reference row shows the nearest-beacon
  heuristic recovers much more unserved demand than either learned arm at this exposure, which
  is a headroom fact for the learner, not a treatment fact.

## 4. Predictions scored

- DM primary: inside-MEI with τ=40 fractions above 0.5, because the fixed step and 200 updates
  move the policy little. **Confirmed at its extreme** (difference exactly zero, fractions 1.0).
- Competing prediction (`Δτ_B01 ≥ +4` on an active path): **wrong**.
- Node's prospective judgement (both arms may barely learn; saturated recovery a live
  explanation): **held**.
- Owner: not taken (unattended).

## 5. Decisions this intake produces

1. **Object tier, `OWNER_DELEGATED`**: accept the pair and the reference as a valid, complete
   B/EXPLORE result read under rows 3 and 4 (mixed/undecided at this exposure), not consumed as a
   treatment verdict. Options: (a) accept as above; (b) quarantine pending a reproduction of the
   identity; (c) launch the card's default second seed. Selected (a): the identity has a
   code-supported mechanism and the treatment demonstrably executed (trajectories differ);
   (b) adds a reproduction the claim does not depend on; (c) is uninformative for the stated
   reason. `Owner-delegated decision (unattended, 2026-09-03 instruction): (a)`.
2. **Direction tier**: the successor (a larger-budget or different-update-law B, a warm-started
   FLEX head, another TBCFV object, or park) goes to
   `em:roster_consistent_latent_exploration:innovator` as the post-B01 request with this intake,
   the summaries and the CM record as evidence. Nothing is launched meanwhile.
3. Records: ledger row, DIRECTION addendum, Portfolio row, owner brief
   `owner/briefs/roster_consistent_latent_exploration/2026-09-06_TBCFV-B01-result.md`, tracking row
   (already written at launch).
