# DISH-RENEWAL-BOUNDARY-A02-CORRECTION — result intake (2026-09-06)

Object: `DISH-RENEWAL-BOUNDARY-A02-CORRECTION` (A/RECON), card
`DISH_RENEWAL_BOUNDARY_A02_CORRECTION_SCIENCE_CARD_20260906.md`, CM record
`DISH_RENEWAL_BOUNDARY_A02_CORRECTION_CM_RECORD_20260906.md`. Direction Manager: the Claude
research hub. Implementation: Grok Build (`3f4d447f6`, reviewed by `hmasd-reviewer` and the
hub). Evidence root: `a02_renewal_boundary_20260906/{check,formal}/` (summary, rows, run log,
admission receipt, supervisor files; byte-verified copies from the node).

## 1. Provenance and technical facts (observation)

- **Launch.** Node `wsl_4070`, detached worktree `/home/wu/hmasd-worktrees/dish_a02_3f4d447f6`
  at `3f4d447f662db638dbdf0c75d49dfa8b230dc002` (clean), interpreter
  `/home/wu/.venvs/hmasd/bin/python`, single thread, `agent-task` supervisor, fresh
  `admit-memory` joined by `&&` before each invocation (available physical 15.67 GiB / 15.68 GiB,
  floor 4 GiB, both passes). Tasks `dish_a02_check_3f4d447f6_20260906_01` (PID 1949645, start
  epoch 1788707117) then `dish_a02_formal_3f4d447f6_20260906_01` (PID 1949932, start epoch
  1788707203); formal launched only after check reported COMPLETE / exit 0. Each launched once.
- **Frozen input.** `checkpoint_update16.pt`, 2,368,467 bytes, sha256
  `504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66`, verified by the operator
  before launch and by the runner (`expected_checkpoint_sha256 == checkpoint_sha256`).
  Configuration: arm STRUCTURED, forecast_package true, host
  `GROUND-TERMINAL-LINEAR-CLEARANCE-A03`, B02 master `ef9ec35c…`, FP32 policy, float64 native,
  `torch_threads` 1. Exposure block: 0 training transitions, 0 optimizer steps, 0 new models,
  consultation exposure 0. Parameter norm before and after each window 39.1492 (unchanged).
- **Completion.** Both profiles `status: COMPLETE`, exit code 0. Formal: 64 live ticks (32 + 32),
  no early terminal, phases match expected (4 and 2), runner wall 0.092 s, peak RSS 363 MB,
  `scratch_unmeasured` true (telemetry rule: valid). Check: 4 ticks of window 1, wall 0.064 s,
  peak RSS 361 MB. Complete compute limit 120 s per invocation: inside.
- **Dependency.** The hub ran the a02 and a01 focused tests (11 passed) and the r06 suite
  (64 passed) on the accepted bytes before the cherry-pick; the reviewer's four findings on the
  first diff were fixed or recorded before acceptance.

## 2. Measurements (formal, verbatim from `summary.json` and `rows.json`)

| count | window 1 (K8) | window 2 (K4_TO_K12) | overall |
| --- | ---: | ---: | ---: |
| live ticks | 32 | 32 | 64 |
| `native_out_renew_equals_policy_renew` (primary) | 32 | 32 | **64** |
| `native_out_true_policy_false` | 0 | 0 | **0** |
| `policy_true_native_out_false` | 0 | 0 | **0** |
| matched renewals (secondary, countdown-based) | 4 | 8 | **12** |
| matched non-renewals | 28 | 24 | **52** |
| countdown disagreements (either kind) | 0 | 0 | **0** |
| admissions | 4 (t = 4, 12, 20, 28) | 8 (t = 2, 6, …, 30) | 12 |
| `admissions_held_equals_projected` | 4 | 8 | **12** |
| `admissions_emitted_equals_held` | 0 | 0 | **0** |
| `held_changed_ticks` | 4 | 8 | 12 |
| nonzero emitted command on admission ticks | 4 | 8 | 12 |
| service ticks | 30 | 30 | 60 of 64 |
| energy increments (sum) | 4584.32 | 4636.65 | 9220.97 |
| `cas_applied` | 0 | 0 | 0 |
| hard events (all seven kinds, final) | 0 | 0 | 0 |

- **Clock.** The policy's consumed flag `policy_renew`, the raw completed-transition flag
  `renew_completed` and native admission are true on exactly the same ticks in both windows
  (window 1: 4, 12, 20, 28; window 2: 2, 6, 10, 14, 18, 22, 26, 30), the ticks A01 recorded as
  native admissions with a consumed zero. Tick 0 in both windows: `renew = 0`, countdown 4 and
  2, no admission (unchanged from A01).
- **Incorporation.** At each of the 12 admissions the held vector after the step equals the
  independent float64 projection of that tick's emitted command from the previous held vector
  (`incorporated_as_projected` true, checked row by row to 1e-9); away from admissions the held
  vector is unchanged. Example, window 1 t = 4: emitted `[-1.1996, 1.5664, 1.0252, -0.4977]`,
  held after `[-0.9120, 1.1909, 1.0252, -0.4977]` (change clipped at 1.5 per component, then
  the magnitude rule); t = 12: held moves from that vector to `[-0.9821, 2.0851, -0.1753,
  -1.3971]`. Largest emitted component 2.83, largest held component 2.64 (≤ 3).
- **Proposals.** Prepare proposals now sample on admission ticks (window 1: all four; window 2:
  five of eight), commit proposals on admission ticks (window 1: first two; window 2: all
  eight). `cas_applied` stayed 0, owner 0 throughout; no legal transfer occurred.
- **Behaviour context (not acceptance conditions).** Service ticks 60 of 64, the same count as
  A01's unmodified path; energy increments sum 9220.97 versus 8563.59 in A01 (higher with fresh
  commands incorporated). No early terminal, no hard event.

## 3. Rule applied (card section 4, first row, verbatim)

> Zero same-tick permission disagreements; at every admission the held vector equals native's
> projection of that tick's emitted command (float64 scale); no held change away from admission;
> value-distinguishing commands incorporated → Local ordinary-renewal/command-delivery correction
> accepted on the observed windows → Complete the correction intake and the qualified B01/B02
> reinterpretation intake; no return gain, calibration, competence or source value claimed; a
> later learning comparison is separately selected.

**Reading: row 1 on both windows.** Every clause is met: 0 disagreements of either kind, 12 of
12 admissions incorporated as projected, 0 held changes outside admissions, 12 of 12 admission
commands nonzero and different from the held vector (not the value-equal row 2). Row 4 (adverse
behaviour) does not apply: both windows ran their full 32 ticks with no terminal or hard event;
the higher energy sum is recorded as context. The correction is accepted on the observed
windows at A/RECON. It says nothing about service value, calibration, source value or learning.

## 4. Predictions scored

- **Pro** (expected counts 12/52/0 as expectations; commands may be poor; delivery may reduce
  service or increase energy): counts matched exactly; service unchanged at 60/64; energy sum
  higher. Matched.
- **DM (hub)**: row 1; 12/52/0; held vector changes at each of the 12 admissions and equals the
  projected command; both windows live for 32 ticks; service ticks differ from 60 (direction not
  predicted); prepare/commit sample on admission ticks; CAS 0. All matched except the service
  sub-prediction: service stayed at exactly 60 (wrong on that clause).
- **Owner:** not taken (unattended).

## 5. Decisions this intake produces

- Object tier, `OWNER_DELEGATED`: row 1 executed. The correction is accepted on the observed
  windows and the corrected boundary (`3f4d447f6`) is the ordinary path for any later DISH
  learning object. Options considered: (a) accept per row 1 and write the reinterpretation
  intake (recommended, selected); (b) extend to longer windows or the training-collection path
  first (rejected: the card forbids widening; the reinterpretation intake needs no
  training-collection measurement per the Pro decision). Not a close call.
- The qualified B01/B02 reinterpretation intake is
  `DISH_B01_B02_QUALIFIED_REINTERPRETATION_INTAKE_20260906.md`, written at this boundary.
- No next experiment object is selected here; the next selection (a learning comparison on the
  corrected interface, or otherwise) is a direction-tier question for `em:dish:convergence` with
  this result and the reinterpretation as evidence.

Owner brief (Chinese): `docs/research/portfolio/owner/briefs/degraded_incumbent_shadow_handover/2026-09-06_A02-renewal-boundary-result.md`.

scope: none
