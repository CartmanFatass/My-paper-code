# R16.5 Guard-Mode Flag — FINAL Spec (for Codex)

Author: CC. Supersedes the Gemini guard-mode plan (v1, v2). Small change,
full spec anyway — the gap history of this week says condensation is where
correctness leaks. Where any prior document differs, this spec wins.
Date: 2026-07-04. Context: Condition 1 of the CC review of the R16.5 P1/P2
implementation (`cross_validation.md`), enforced by
`EXP-20260704-r16-5-coef01-entfloor`.

## Purpose

Let the entfloor comparison run execute under the SAME termination behavior
as the reference run (`run_20260704_142053`, which predates the ratio
guard), while still recording everything the guard would have done.

## Changes

### [MODIFY] ha_ctse_process/config.py

```text
reward_ratio_guard_mode = "kill"   # "kill" (default) | "warn"
```

### [MODIFY] ha_ctse_process/train.py

```text
CLI: --reward_ratio_guard_mode {kill,warn}
Manifest/start line: log reward_ratio_guard_mode explicitly.

Guard logic (both triggers: instant >1.0 post-warmup; sustained >0.5 for 5
consecutive post-warmup updates):
  mode == "kill": current behavior — write logs/CSV/TB for the update
    FIRST, then raise RuntimeError (unchanged).
  mode == "warn": log a strong console warning; DO NOT raise. Metrics
    continue identically to kill mode:
      proto_disc_reward_env_ratio_over05_count: keeps accumulating across
        the whole run — NEVER reset after a trigger (the read needs
        pathology DURATION, not just occurrence);
      proto_disc_reward_env_ratio_kill_triggered: CUMULATIVE count of
        would-have-killed updates (not a sticky 0/1);
      proto_disc_reward_env_ratio_guard_active: unchanged per-update.
```

### [MODIFY] scripts/run_r16_a2r_overnight_local_cuda.ps1  <- THE GAP

```text
The a2r_roster_coef01_entfloor arm MUST pass
  --reward_ratio_guard_mode warn
in its constructed command (hardcoded for this arm, or a runner parameter
defaulting to warn for this arm only). Without this, the pre-registered
launch command silently runs in kill mode — the exact second-variable
confound Condition 1 exists to prevent, failing invisibly unless the ratio
happens to spike. Echo the guard mode in the runner's per-arm banner.
(Mirror in scripts/run_r16_a2r_remote_32env.sh only if the entfloor arm
exists there.)
```

## Verification

```text
Automated:
  - default is "kill" in config;
  - warn mode: forced trigger -> run continues AND kill_triggered
    increments in CSV AND over05_count keeps accumulating afterwards;
  - kill mode: forced trigger -> RuntimeError raised AFTER the update's
    metrics are written.
Manual:
  - runner -DryRun for a2r_roster_coef01_entfloor prints
    --reward_ratio_guard_mode warn in the command AND banner;
  - tiny warn-mode smoke with forced trigger (as in Gemini v2).
Launch precondition: the -DryRun output showing the warn flag is pasted
into the ExpRecord entry before launch (cheap proof the confound guard is
actually wired).
```
