# RCLE-TBCFV-B02-NORM-0p02 result intake — 2026-09-06

Card `RCLE_TBCFV_B02_NORM_0P02_SCIENCE_CARD_20260906.md` (B/EXPLORE, outcome-informed, opened by
the archived post-B01 Innovator decision, `PRO_FINAL`, intake
`RCLE_TBCFV_POST_B01_INNOVATOR_INTAKE_20260906.md`); CM record
`RCLE_TBCFV_B02_NORM_0P02_CM_RECORD_20260906.md`; launch sha
`8ad01cb9ea69b77a2e907947bef59bf716a8b45a`; evidence `b02_tbcfv_norm0p02_20260906/` (arm,
initialization-panel and reference summaries, final parameters, receipts, timings, launch
script, task log). Direction Manager: the Claude research hub. Predictions scored in §4.

## 1. Execution facts (observation)

- Node `wsl_4070`, worktree `rcle-b02-8ad01cb`, one detached chain (`agent-task
  rcle_b02_chain_20260906`, 22:23:39Z, exit 0, **chain wall 152.6 s** of the 1,500 s object
  cap). Memory admission passed before every step (≈14.2 GiB available). Native build into the
  request root 3.04 s; focused check (Linux oracle + B02 tests) `23 passed` in 4.05 s;
  preparation 7.17 s.
- **C1P1**: `COMPLETE`, 200 updates, 200 nonzero, 0 zero-gradient; `/usr/bin/time` 1:11.47
  (71.5 s including the 2,048-episode initialization panel), study wall 70.24 s, CPU 70.2 s,
  peak RSS 575 MB; **FLEX**: `COMPLETE`, 200/200/0, 1:11.23, 70.04 s, 69.9 s, 581 MB; reference
  1.53 s. Charge: 7.2 + 71.5 + 71.2 + 2.6 = **152.5 s**; each arm well inside 600 s.
- Seed law: root key `fd3cd5cf…`, block digest `82593ad7…` in both arms and the reference (the
  derived values of the card); identical initial tensors (norm `21.205717682888885`; B01's seed-17
  norm was 21.186); five package models allocated, two training instances (recorded).
- The learning-law change ran as specified: every one of the 400 updates records
  `parameter_delta_norm = 0.02` and `measured_parameter_delta_norm = 0.02` (the measured L2 of the
  applied delta); final displacement **0.4729 (C1P1) and 0.4729 (FLEX)** against the path bound 4.
- Acceptance: the FLEX arm validated the C1P1 summary (object, seed 18, block digest, 200 updates,
  256 episodes per cell, initialization panel present); paired publication joined the three
  panels by scenario; no exception; both `.stderr` empty. Valid, complete B/EXPLORE result.

## 2. Frozen rule applied verbatim and the observed readout

Primary `ΔU` = mean over `8→12` and `12→8` (ACTIVE_CONTINUATION) of `(U_FLEX − U_C1P1)`;
companion `G_U` per arm = mean over the same paths of `(U_init − U_final)`; MEI U 0.05, τ 4 ticks.

| Path | `U_init` | `U_C1P1` | `U_FLEX` | `ΔU` (FLEX − C1P1) | `G_U` C1P1 | `G_U` FLEX | τ=40 fraction (init / C1P1 / FLEX) | reference U / τ=40 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8→12 | 0.6967 | 0.6953 | 0.6953 | +0.000033 (SE 0.000033) | +0.0014 | +0.0014 | 1.0 / 1.0 / 1.0 | 0.2456 / 1.0 |
| 12→8 | 0.7212 | 0.7187 | 0.7187 | −0.000037 (SE 0.000037) | +0.0025 | +0.0026 | 1.0 / 1.0 / 1.0 | 0.3187 / 0.973 |
| **mean** | | | | **`ΔU_B02` = −0.000002 (SE 0.000025)** | **+0.0020** | **+0.0020** | | |

`Δτ_B02 = 0.0` (τ = 40 in every one of the 2,048 held-out episodes of the initialization panel
and of each arm; the reference has τ < 40 in 2–11 episodes per cell). Eight-cell means: U 0.7072
(initialization), 0.7058 (C1P1), 0.7057 (FLEX); Y 0.2951 / 0.2962 / 0.2963; every cell moved by
less than 0.003 in U. **The two arms are no longer bit-identical**: 14 of the 2,048 paired
scenarios differ in U between C1P1 and FLEX (by at most a few 10⁻³), and the initialization panel
differs from the C1P1 final in 1,874 scenarios; every per-cell mean agrees to three decimals.
Training curves: per-update Y mean 0.2869 over the first 50 updates and 0.2871 over the last 50 in
both arms (the two curves coincide to 10⁻⁴ until the last updates); the raw gradient norm fell
from 0.68 / 0.80 / 0.58 (updates 0–2) to 0.06 / 0.04 / 0.03 (updates 197–199) in both arms while
the applied step stayed 0.02.

**Reading: card row 4.** `ΔU` is inside the MEI (by three orders of magnitude), neither arm's
`G_U` approaches 0.05 (+0.002 each), and τ stays saturated at 40 in every learned episode:
**this 0.02 / 200 movement attempt gave no useful learning signal.** The card's row-4
instruction applies: end this spend and return to the next object selection with the complete
counterexample; no automatic 4,000 updates, step sweep or warm-started heads; this does not
prove the normalisation principle wrong or the host unlearnable. Also present, as facts: the
learned arms leave about 0.70 mean normalised unserved demand on the active paths against the
scripted nearest-beacon reference's 0.25 / 0.32 on the same seed-18 panel (the same headroom
description as B01's seed-17 panel); the parameter vector moved 0.47 (23 × B01's 0.0051) with no
service change; the gradient norm decayed twenty-fold under a constant-norm step.

Not inferred: package equivalence; that the learner cannot learn; that the persistent state has
no value; that a larger step, an un-normalised step, more updates, warm-started heads, or a
different objective would or would not move service; any cause for the flat Y under a large
parameter displacement (the gradient-norm decay is recorded, not explained). One seed, one step
size, this toy, these cells.

## 3. What the observation adds to the direction's record

- Second training instance (seed 18) and second update law (0.02) on TBCFV: both learned packages
  end within 0.003 of their own initialization's U on every held-out cell, with τ saturated; the
  first instance (seed 17, 0.0005) was identical by construction, this one is not identical but
  indistinguishable in service.
- The shared initialization panel and the same-panel reference establish that the learner's
  service level is that of its Xavier / zero-bias initialization and roughly three times the
  unserved demand of the scripted nearest-beacon policy, on this seed too.
- The `parameter_delta_norm` publication now reports the prescribed and the measured step; the
  B01 constant-only publication is superseded for new objects.

## 4. Predictions scored

- **Node (Pro)**: "may lower at least one package's U by about 0.05 relative to its initialization"
  did not happen (+0.002); the stated strongest competing prediction (both arms still barely
  improve) held.
- **DM primary** (`G_U` ≥ +0.05 for at least one arm; `ΔU` inside ±0.05; τ still all 40): the
  first part failed, the second and third held. Partly wrong. **DM competing** (FLEX below C1P1 by
  ≥ 0.05): wrong.
- **Owner**: not taken (unattended).

## 5. Decisions this intake produces (object tier, delegated)

Options: (a) accept the pair, the initialization panel and the reference as a valid complete
B/EXPLORE result read under card row 4, and put the next object selection to
`em:roster_consistent_latent_exploration:innovator` with the complete counterexample; (b) buy a
further step size or a longer run now (excluded by row 4); (c) quarantine (no defect: the law ran
as specified, counts and outputs complete). Recommendation: (a).
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**

Successor question for the node (direction tier): after B01 (0.0005, identical arms) and B02
(0.02, 23 × more displacement, flat service, decaying gradient norm), what is the next object:
a learner-side change that is not a step-size change (for example an un-normalised or adaptive
step, a different manager / actor objective, or a longer exposure with intermediate panels), a
diagnostic A on why the gradient norm decays while service does not move, a return to a
different TBCFV object, or park. Packet `pro_packets/20260906_post_b02_innovator/`.

Records: brief `owner/briefs/roster_consistent_latent_exploration/2026-09-06_TBCFV-B02-result.md`;
ledger rows; DIRECTION addendum; Portfolio row.
