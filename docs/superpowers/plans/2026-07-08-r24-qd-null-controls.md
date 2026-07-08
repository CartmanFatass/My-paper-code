# R24 q_d Null-Control Diagnostics Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for implementation. This is core q_d diagnostic code; keep implementation controller-owned unless a bounded parallel task with disjoint files is created.

**Goal:** Strengthen the R24 reward-off `q_d` probe so the next run can distinguish real behavior-window skill information from context, label, duration, and pre-assignment shortcuts before any intrinsic reward path is considered.

**Architecture:** Keep the existing dual-stream current-window probe:

```text
q_full(z_i | action_window_i, effect_window_i, Z, xi_context_i, c, omega)
q_prior(z_i | Z, xi_context_i, c, omega)
```

Add diagnostic controls:

```text
q_behavior(z_i | action_window_i, effect_window_i)
q_pre(z_i | pre_assignment_action_window_i, pre_assignment_effect_window_i, Z, xi_context_i, c, omega)
shuffle/fake-label residual reads from trained logits
label-distribution baseline diagnostics
```

The controls are reward-off and default-off with the existing `--enable_team_conditioned_qd_probe` switch.

**Tech Stack:** Python 3.10, PyTorch, NumPy, pytest, existing HA-CTSE segment manager.

## Constraints

- Do not add q_d reward, q_D reward, low-only intrinsic reward, or new PPO reward plumbing.
- Do not change default training behavior when `enable_team_conditioned_qd_probe=False`.
- Do not include the focal executed `z_i` in `xi_context_i`.
- Pre-assignment windows must read only behavior/effect before the current skill assignment. If no previous segment exists, report zero/empty pre-control metrics rather than inventing data.
- Keep communication/backhaul fields out of intrinsic/probe targets. They remain evaluation diagnostics only.
- Preserve existing R24 runner behavior; this plan only increases logged diagnostics.

## Task 1: Add q_d Diagnostic Heads And Metrics

**Files:**
- `ha_ctse_process/team_conditioned_qd.py`
- `tests/r24_team_conditioned_qd_test.py`

**Steps:**

- [ ] Extend `TEAM_CONDITIONED_QD_METRIC_FIELDS` with behavior-only, pre-assignment, shuffled-label, fake-label, and label-baseline metrics.
- [ ] Add a `q_behavior` head over encoded current action/effect streams.
- [ ] Add a `q_pre` head over encoded pre-assignment action/effect streams plus condition.
- [ ] Keep all inputs detached.
- [ ] Return `loss = loss_full + loss_prior + loss_behavior + loss_pre_when_available`.
- [ ] Compute shuffled-label and fake-label residual reads from current trained logits without optimizing on fake labels.
- [ ] Add tests proving:
  - behavior-only can recover labels when action/effect carries skill information;
  - pre-control metrics exist and are bounded;
  - fake/shuffle metrics exist;
  - all empty metrics match the field list.

## Task 2: Store And Feed Pre-Assignment Behavior Windows

**Files:**
- `ha_ctse_process/standalone_agent.py`
- `tests/r24_team_conditioned_qd_test.py`

**Steps:**

- [ ] Add bounded pre-assignment raw-window fields to `Segment`.
- [ ] When `SegmentManager.renew()` closes an old segment and opens a new one for the same agent, copy the last pre-assignment action/obs window into the new segment.
- [ ] Refactor current action/effect stream helpers so the same summarizer can build current and pre-assignment streams.
- [ ] Update `_r24_qd_segment_tensors()` to return current action/effect, condition, labels, pre-action, pre-effect, and a pre-valid mask.
- [ ] Update `_team_conditioned_qd_update()` to pass the pre tensors/mask and log the new metrics.

## Task 3: Logging And Plotting

**Files:**
- `ha_ctse_process/plotting.py`
- `ha_ctse_process/train.py` if needed

**Steps:**

- [ ] Confirm `TEAM_CONDITIONED_QD_METRIC_FIELDS` still feeds TensorBoard and `metrics/train_updates.csv`.
- [ ] Add the most important new fields to the R24 plotting key list:
  - `r24_qd_acc_behavior`
  - `r24_qd_acc_pre`
  - `r24_qd_full_minus_behavior_acc`
  - `r24_qd_full_minus_pre_acc`
  - `r24_qd_shuffle_acc_gap`
  - `r24_qd_fake_acc_gap`

## Task 4: Verification

**Commands:**

```powershell
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_team_conditioned_qd_test.py -q
& "C:\Users\wu\.conda\envs\SB3\python.exe" -m py_compile ha_ctse_process\team_conditioned_qd.py ha_ctse_process\standalone_agent.py ha_ctse_process\train.py ha_ctse_process\plotting.py
```

**Acceptance:**

- Existing q_d probe tests still pass.
- New diagnostic metrics are non-empty and prefixed `r24_qd_`.
- No reward path is touched.
- Probe-disabled behavior remains empty metrics only.

