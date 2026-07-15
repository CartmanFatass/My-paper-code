# Design-Review Package: R24-1 q_d Gate Disposition (2026-07-09)

Prepared by the Claude controller for the mandatory MARL design cross-validation
gate (marl-peer-reviewer, gpt-5.5 xhigh, read-only round).

## Decision under review

Three linked decisions, to be dispositioned together:

D1. ACCEPT the R24-1 gate verdict as FAIL: the team-conditioned behavior-window
    q_d hypothesis (individual skills z_i leave a team-conditioned behavioral
    signature recoverable from held-out windows above same-capacity nulls) is
    not supported. q_d and q_D rewards remain permanently blocked on this
    evidence line unless new mechanisms change the setting.

D2. Whether ONE pre-registered instrument-fix re-run is warranted before final
    archival: the frozen analyzer shows a consistent overfitting bias
    (loss_full/loss_prior 2.4-3.7x on held-out data across all runs;
    reduced-input variants beat full-input everywhere; fixed 300 steps, no
    early stopping). Proposed fix if approved: eval-based early stopping,
    identical for all variants, re-run all 4 analyses, pre-registered
    acceptance criterion = verdict unchanged unless real clears gates AND
    separates from nulls AND shows q_A-dependence. Purpose: make the negative
    result publication-solid, not rescue the gate.

D3. Pivot direction after acceptance: the pre-registered branch
    (IMPLEMENTATION_PLAN "Do Not Do Yet" + R23-next disposition) is the
    individual-skill/discoverer half — whether z_i skills are behaviorally
    differentiated AT ALL — rather than more q_D/q_d probe or target
    engineering. Supporting crumbs: the only variant ever crossing gate-level
    residual was behavior_only (+0.061, individual behavior without team
    context, on a collapsed no-q_A run); z_usage_entropy ~0.93-0.96 (moderate,
    not collapsed). A pending same-day experiment (matched arm0-vs-arm2
    deconfound, seed-1 pair completing tonight) addresses q_A's TASK effect —
    a separate question that does not block D1 but informs pivot priority.

## Evidence (all reward-off; full tables in the four gate_read files)

Four 320k cloud runs, 2 arms (qAon = q_A actionability reward on; qAoff_coef0 =
matched architecture, q_A off) x 2 seeds. Frozen analyzer: fresh probe per null
variant, identical capacity/budget (hidden 128, 300 steps, lr 3e-3), 80/20
per-env split, ~21k rows/run, 9 variants (real, shuffled, fake_marginal,
duration_matched, agent_matched, behavior_only, pre_only, action_only,
effect_only).

| Run | Policy health (final coverage) | real residual_gain | rank/9 | real-behavior_only | loss_full/loss_prior | analyzed on |
| --- | --- | --- | --- | --- | --- | --- |
| qAon/seed1 | 0.70 healthy | -0.0319 | 8 | -0.023 | 2.84x | CPU |
| qAon/seed2 | 0.0 collapsed | -0.0073 | 4 | -0.023 | 2.40x | CPU |
| qAoff/seed1 | 0.0 collapsed | negative | 8 | -0.074 | 3.66x | CPU |
| qAoff/seed2 | 0.0 collapsed | +0.0153 | 2 | +0.019 | 3.15x | GPU |

Pre-registered gates (all FAIL in all 4 runs): residual_gain >= 0.05,
positive_frac >= 0.60, acc gap >= 0.05, real >= 1.3x best label-null,
shuffled/fake ~0, between/within (from the separate forced audit: 0.308 vs
>1.2 required, at 1920-record power).

Facts vs interpretation:
- FACT: no run approaches any gate; the max real residual (+0.015) is in the
  no-mechanism arm; team-conditioning margin negative in 3/4.
- FACT: in-loop online probe read small POSITIVE (+0.010/+0.011) on qAon seeds;
  frozen held-out read is ~0/negative — the frozen instrument was built (GPT
  Rounds 3-4 requirement) precisely to check this, and it deflated the online
  signal.
- FACT: instrument artifacts exist: overfitting bias against full-input real;
  two exact-identity degenerate variants in qAon/seed2; the GPU-analyzed run is
  the outlier run (device nondeterminism plausible at this noise scale).
- INTERPRETATION (controller): mechanism-fail; instrument bias cannot explain a
  ~+0.08 gap to gates nor the absent q_A-dependence; D2 re-run is optional
  solidity, not gate-shopping.
- Related prior negatives: R21 Z near-inert (autopsy); R23 arm3 q_D target
  audit NULL; forced-audit between/within 0.308.
- Related positives that survive: q_A actionability Z->xi (residual_gain
  +0.222, forced-Z KL rising) — unaffected by this verdict; task-pace
  observation (qAon coverage 0.7-0.8 at 320k vs HMASD baseline reaching 0.7 at
  ~480k) — pending deconfound.

## Binding constraints

Mechanisms land default-off; reward paths open only after diagnostic gates
pass; env task reward stays external, never relabeled intrinsic; no intrinsic
reward from raw communication indicators; every new mechanism must retire or
supersede an existing one (mechanism budget rule); q_D must not read xi
directly; 160k/320k runs are mechanism gates, not performance verdicts.

## Exact review questions

1. Do you concur with accepting D1 (R24-1 FAIL, q_d/q_D reward blocked on this
   line)? If not, what specific analysis of the EXISTING data would change it?
2. Is D2's single early-stopping re-run worth running, with the stated
   pre-registered criterion? Or is the current evidence already sufficient /
   is the re-run risky (implicit garden-of-forking-paths) even as pre-registered?
3. For D3: given behavior_only was the only near-gate variant and z_usage
   entropy is moderate, is the individual-skill-differentiation pivot the right
   next mechanism question, and what is the minimal reward-off diagnostic you
   would design first for it?
4. Name the strongest objection to our overall reading that we have not stated.
5. Which of your own recommendations are evidence-backed vs judgment?

The reviewer is advisory and must not propose repository edits.
