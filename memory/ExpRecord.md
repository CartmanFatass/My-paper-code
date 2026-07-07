# HA-CTSE Experiment Dashboard

Updated: 2026-07-07

Purpose: factual current experiment state. ExpManager records experiment
content, running state, commands, package paths, and result facts here.
LongTimeMemoryManager decides how these facts affect current memory and LTM
archives.

## Protocol

Before launching or recommending an experiment, keep one dashboard row here and
record enough factual detail for LongTimeMemoryManager to decide any archive or
project-memory update.

Required dashboard columns:

```text
ID | Status | Stage | Location | Owner Agent | Next Read | Key Logs / Package | Decision
```

Status vocabulary:
`planned`, `launch-ready`, `running`, `completed`, `stopped`, `failed`,
`invalid`, `superseded`, `blocked`.

## Current Dashboard

| ID | Status | Stage | Location | Owner Agent | Next Read | Key Logs / Package | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXP-20260707-r24-assignment-to-behavior-bridge | launch-ready | R24 | local 16env diagnostic launcher under `scripts/run_r24_qd_probe_local_cuda.ps1`; cloud 64env package optional | ExpManager | R24-0 forced-xi / forced-z behavior audit (offline / checkpoint-based), then R24-1 team-conditioned q_d reward-off probe | `scripts/r24_forced_behavior_audit.py`; `scripts/run_r24_behavior_audit_local_cuda.ps1`; `scripts/run_r24_qd_probe_local_cuda.ps1`; input checkpoint from q_A reward arm in `logs_r23_next_mechanism_matrix_local` | External Round 1 sequencing: R23 q_A is high-level `Z->xi` validation only. First prove xi/z_i causes persistent behavior separation at H={10,20,50}; then q_d_full-vs-prior probe. R24-1 is reward-off and logs `r24_qd_*`. Reward-on low-only q_d remains blocked until behavior audit and q_d residual both pass. q_D reward and 960k scale runs deferred. |
| EXP-20260707-r23-next-mechanism-matrix | completed / mixed (local 16env, single seed) | R23-next | local CUDA; cloud candidate | ExpManager | optional cloud 64env rerun for a matched-env task read + q_D-probe upgrade | `logs_r23_next_mechanism_matrix_local`, `scripts/run_r23_next_mechanism_matrix_local_cuda.ps1`, `scripts/run_r23_next_mechanism_matrix_cloud_64env.sh` | q_A actionability VALIDATED (Z->xi learnable: arm2 residual_gain +0.222, forced-Z KL 0.059->0.070). q_D target audit NULL across all targets/H (underpowered caveat) -> xi->recoverable-joint-effect still unestablished. Task encouraging @160k (cov 0.303 ~3x control) but confounded. Next lever = individual-skill/discoverer half + stronger q_D probe, NOT more q_D targets. Local 32env OOMs (31.6GB box); use 16env locally or 64env cloud. |
| EXP-20260706-r23-actionable-team-intent | completed / mixed | R23 | cloud CUDA seed1 | ExpManager | none unless comparing to R23-next | `dist/logs_cloud_r23_actionable_team_intent_64env` | Architecture capacity passed; g-info objective and q_D target failed/null. This motivates q_A residual and q_D target audit. |
| EXP-20260705-r21-team-intent | completed / negative | R21 | cloud CUDA seed1 | ExpManager | none | `dist/logs_cloud_r21_team_intent_64env`, `memory/R21_AUTOPSY_REPORT.md` | Z was near-inert; sampled team code did not create recoverable team effect. No seed2 or sweep on this design. |

## Active Experiment Detail

### EXP-20260707-r24-assignment-to-behavior-bridge

Launch-ready from External Review Round 1 memory disposition. This is not a
launched run yet; it is the next mechanism gate sequence.

- Forced-xi / forced-z audits first: load the q_A reward checkpoint, force
  alternative Z/xi/z_i choices on matched states, roll out H={10,20,50}, and
  measure action KL plus behavior/effect separation and persistence.
- Team-conditioned q_d probe second: compare
  `q_d_full(z_i | local_effect_i, Z, xi, c,omega)` against
  `q_d_prior(z_i | Z, xi, c,omega)` with duration/reward/phase/agent shortcuts.
- Reward sequence: no q_D reward; no q_D coefficient sweep; no 960k scale run.
  Only after positive forced-z/q_d evidence should a small clipped low-only q_d
  reward arm be considered. q_D returns only as a reward-off re-probe after
  behavior separation exists.

Implementation handoff:
- R24-0 behavior audit is offline/checkpoint-based and writes `r24_behavior_audit.csv`.
- R24-1 q_d probe is reward-off and logs `r24_qd_*`.
- Reward-on low-only q_d remains blocked until behavior audit and q_d residual both pass.

Script references:
- `scripts/r24_forced_behavior_audit.py`
- `scripts/run_r24_behavior_audit_local_cuda.ps1`
- `scripts/run_r24_qd_probe_local_cuda.ps1`

### EXP-20260707-r23-next-mechanism-matrix

Current read:

- Arm1 q_A probe: positive residual-gain trend, but stopped before full 320k.
- Arm2 q_A reward: completed 40 updates at 16 env; q_A residual gain reached a
  strong mechanism-positive signal. Task read is encouraging but caveated by
  env-count mismatch and single seed.
- Arm3 q_D target/timescale audit: COMPLETED-effectively (38/40 converged, 16env).
  NULL result — every target x horizon collapses to the marginal baseline by u38
  (acc ~0.243, residual_gain ~0.000 for s_next / joint_action / joint_effect /
  delta_omega at H{10,20,50}). No effect space recovers Z above marginal; consistent
  with team_disc-at-chance. CAVEAT: underpowered probe (~1 grad step/update over
  high-dim targets; q_A succeeded on the same budget only because xi is low-dim/direct;
  baseline is context-free marginal, not context-conditioned) -> read as "no signal
  found", NOT "proven absent". Earlier u20 gains (+0.06..0.13) were a transient
  baseline-lag artifact, now gone. Keep q_D reward disabled.

Verdict (R23-next matrix): the g-info -> q_A pivot is VALIDATED. Z->xi actionability
is now learnable (arm1 probe gain 0->+0.097; arm2 reward gain ->+0.222 with forced-Z
KL rising 0.059->0.070, Z-usage healthy) -- decisively fixing the g-info failure
(T2 audit: g-info grad <2% of PPO, self-stalling). The remaining blocker is xi ->
recoverable joint effect: arm3 finds no q_D target/timescale above marginal (underpowered
caveat). Next lever is the individual-skill/discoverer half (does z_i differentiate
low-level behavior -- "Reason B") and/or a stronger q_D probe (more head epochs/update +
context-conditioned baseline), NOT more q_D target engineering. Task: NOISE-DOMINATED at
this depth/seed. cov@160k across arms = arm1 0.063 / arm0 0.10 / arm3 0.192 / arm2 0.303,
and arm3 declined 0.192->0.082 by 320k despite reward-off/probe arms sharing ~identical
policies -> RNG-desync variance. arm2's "3x coverage" is most likely favorable variance,
NOT a real q_A-reward task gain; downgrade it. No reliable task signal without a
matched-env, multi-seed run. The q_A mechanism result (per-arm-internal residual_gain
trend) is independent of this and stands. Firm-up: cloud 64env matched rerun (both seeds).

Operational note:

- Local 32env subproc runs can exceed available RAM. Prefer 16 env locally or a
  cloud 64env package/run.

## Archive Pointers

- Full pre-compaction experiment record:
  `memory/LTM/EXPERIMENT_RECORD_20260707_full_import.md`
- LongTimeMemoryManager-owned detailed experiment archive:
  `memory/LTM/EXPERIMENT_ARCHIVE.md`
