# Intake — ACVC post-C/M direction review (em:acvc:convergence, 2026-09-15)

Request `2026-09-15-acvc-cluster-mappo-comparison-b01-result-review-01`,
conversation `6aa12e74-8e54-83e8-95f6-001681b456f7`, task `c3ce56bf2`, delivery
commit `a4cb8e8b0` on `codex/acvc` ([RESPONSE.md](archive/RESPONSE.md), Issue
#14 comment 5679110434). Transport: Claude Code hub via Agentify Desktop, one
accepted Send, `COMPLETE`, GitHub bytes sha256
`54575308d0e1cbba39669fde29289e06c9b69cd48efb5ed5260394c02555558a` (21,614
bytes), archive under
`temp/sessions/hmasd-chatgpt-pro-transport/archive/acvc/2026-09-15-acvc-cluster-mappo-comparison-b01-result-review-01/`.

## Decision and conformance

**Selected: option A with k = 1** — one further unchanged paired C/M block
(one new C-only fit and one new M fit, frozen recipes, pinned on-policy
dependency and action adapter, fresh unscreened identities, separate model,
optimizer, environment and RNG state), not the DM's three-times-budget probe
(B) and not closure (C). The completed `F_ABOVE_MEI` observation and the
optional-F status are preserved. No C freeze, no lifecycle, priority or
capacity change, no Portfolio allocation is granted by this decision.

Conformance check by the author DM (the hub): the decision answers the bound
question at its declared class (outcome-informed B/EXPLORE extension), within
evidence-spec §§7, 11.8–11.11 (one or two independent seeds as the default
follow-up, no seed quota), and the owner's programme; it names the object,
primary, MEI, prospective accumulation rule, exposure and ordinary plan. No
concrete conflict found. Label **`PRO_FINAL`** for the direction node. The DM's
recommendation (B) was overruled by the node with stated reasons; recorded, not
contested.

## The selected object, verbatim essentials

- Each fit: 4,096 training episodes, 2,048 two-episode rollouts, 8,192 PPO
  minibatches, one sole-final snapshot; C supplies C/F/own-dwell 64-world
  panels, M supplies its M panel. Host, native S and J = S/256, true
  termination, private recurrence, training-only critic, CPU FP32 single
  thread, separate evaluator randomness unchanged. No midpoint, best-checkpoint
  selection, changed rate, longer exposure, screen or new simulator.
- Fresh block primary `D2 = mean64(J_F − J_M)` with the existing absolute .01 J
  MEI and the same F_ABOVE_MEI / WITHIN_MEI / M_ABOVE_MEI branches; report
  paired-world SD/SE, C−M, F−C, F−own-dwell, all absolute scores, signs, tails.
- Prospective accumulation, fixed before D2: `pooled_mean = (D1 + D2)/2`,
  `block_SD = |D2 − D1|/√2`, `block_SE = block_SD/√2`, nominal df 1 interval
  `pooled_mean ± 12.706·block_SE` labelled model-conditional, not a gate;
  D1 = +.02343964960218458 J. Report D1 and D2 individually first; same
  aggregation for the supporting contrasts; no world-row pooling, no
  precision weighting, no imputation on an invalid operand.
- New block exposure: 2,162,688 team ticks, 16,384 PPO minibatches, 24,576
  optimizer step calls, 4 final panels, 2 snapshots / 4 loads. Ordinary plans
  1,800 s C and 1,600 s M native; not caps.
- The object ends after its two originals and panels regardless of outcome;
  no replacement block, third fit, automatic continuation or fixed closure
  trigger.

## What the hub does next (execution bindings)

1. **Investment.** Two new original fits are new experimental exposure outside
   the completed allocation ("does not … grant a Portfolio allocation"). Under
   AGENTS §5 (DM autonomy, 2026-09-13) additional grant outside existing
   delegation is Portfolio's; the hub authors one bounded Portfolio investment
   request for this block (about 3,400 s planned native) on the shared
   Portfolio conversation once the current FSD request is archived there (same
   binding key, one Send at a time). Zero exposure until funded.
2. **Engineering L0 (zero exposure, prepared in parallel).** Class: research
   runner wrapper. Owned paths: new
   `scripts/run_acvc_cluster_mappo_comparison_b02.py` (≤ 200 lines) that
   imports the frozen B01 runner and protocol, binds fresh identities
   `MASTER = 28431`, `EVALUATION_NAMESPACE = 38431` (same pattern as 28331/38331,
   disjoint), keeps every recipe constant by reference, and forwards
   `--on-policy-root`; a focused test that the bound identities and derived
   seeds differ from B01's and that all other protocol constants are identical
   by object identity. Protected: `experiments/candidates/acvc/**`,
   `scripts/run_acvc_cluster_mappo_comparison_b01.py`, the pinned on-policy
   archive (sha256 `0f151fea…`), reward, panel law, checkpoint format. Remote
   staging of the pinned on-policy source is re-created per the recorded
   DEPENDENCY/STAGING receipts (the previous copy was reclaimed). Opus review
   before launch because the identity binding touches RNG seeds.
3. Preserve the Pro response; update `DIRECTION.md` at the next clean boundary
   with the selected object; ledger row and owner item `20260915-acvc-001`
   `auto_applied = A(k=1)`.

Transport registry note: the shared archive script fails on this key's record
(missing singular `direction_id`, a pre-existing Codex-side schema mismatch), so
`em:acvc:convergence` rests at `DIRECTION_VERIFIED` for this request with the
response fully archived; reported to the owner, not repaired by the hub.
