# VSPC1 B02 native collection: technical acceptance

Technical collection checks PASS for the one completed P55 handle
`vspc1_hold_value_b02_8102_0ec208899f5e`. No rerun, extra arm, H completion,
model construction or scientific replay was performed during collection. The same
VSPC1 DM owns scientific intake and the P55 all-outcome stop.

The [evidence JSON](VSPC1_NATIVE_HOLD_VALUE_B02_COLLECTION_EVIDENCE_20260908.json)
retains the entire unchanged native summary, calculated collection checks, exact
supervisor runner/log and executed launch script. Contract:
[B02 card sections 2-5](VSPC1_NATIVE_HOLD_VALUE_B02_SCIENCE_CARD_20260908.md),
[B02 CM spec](VSPC1_NATIVE_HOLD_VALUE_B02_CM_SPEC_20260908.md),
[accepted implementation/command](VSPC1_NATIVE_HOLD_VALUE_B02_TECHNICAL_ACCEPTANCE_20260908.md).

## Source, handle and retained artifacts

- Node: `hmasd-wsl-node`; source SHA
  `0ec208899f5e8b4c190ab7bd9806be2cc30b6fda`.
- Detached cwd:
  `/home/wu/hmasd-worktrees/vspc1-native-hold-value-b02-8102-0ec208899f5e`.
  Read-only remote Git inspection confirmed exact HEAD and clean status.
- Native output:
  `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b02_8102_0ec208899f5e`.
- Admission: same parent, `native_hold_value_b02_8102_0ec208899f5e_admission.json`.
- Supervisor:
  `/home/wu/.agent-tasks/vspc1_hold_value_b02_8102_0ec208899f5e/`.
- Invoked script:
  `/home/wu/hmasd-inputs/vspc1_hold_value_b02_8102_0ec208899f5e.sh`.
  Collected bytes equal the reviewed 655-byte LF source artifact. It has no hard-KILL
  timeout; unchanged cooperative source deadlines and complete external wall remain.
- Local scp collection beneath the designated direction checkout:
  `temp/directions/vsp_c1/collection/native_hold_value_b02_8102_0ec208899f5e/`.
  It retains `output/` with both final checkpoints and every JSONL row, `supervisor/`,
  `admission.json`, `launch.sh`, `check_collection.py` and `collection_checks.json`.

Read-only supervisor status confirms finished, exit 0, PID 2784739, tmux inactive.
Terminal log duration is 305s (status uptime is not finished-run wall). The exact
supervisor invoked the supplied shell, which performs fresh admission and then:

```text
/home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_native_hold_value_b02.py --seed 8102 --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b02_8102_0ec208899f5e
```

## Checks over collected bytes

Executed once with the existing local scientific interpreter, without constructing
any policy/environment or calling a learner:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' temp/directions/vsp_c1/collection/native_hold_value_b02_8102_0ec208899f5e/check_collection.py
```

Exit 0; combined remote Git/log inspection and local check took 2.873s. The ordinary
readback script reuses B01's bounded collection checks with B02 identity/key, and
recomputes the declared MEI rule without assuming a positive outcome. No scientific
result was changed to pass a check. A separate byte-readback of the executed launch
script matched its previously reviewed source, exit 0, observed wall 0.850s.

- Summary object/card/seed, fixed full configuration, launch SHA and all 810200000-based
  seed domains match B02. Both fits and final endpoints complete; status COMPLETE,
  publication_readback complete, empty limits, no cap breach or partial steps.
- 1120 complete 256-step rows: 512 training per learner and 32 final evaluations per
  GATED-V/MLP-V/H. Episode/reset identities exactly match the declared domains.
  Native J equals reward_sum/256 and prefix+suffix equals total within ordinary
  floating-point rounding. Per-row decisions reconcile with summary and phase counts.
- 512 rollout records, 256 per learner, each with four epoch records and four Adam
  calls: 2048 actual optimizer calls. Counts reconcile to 286720 native team steps,
  262144 train + 24576 eval, 96 evaluations, 1120 explicit resets and two constructors.
- All recorded numeric losses, rewards, endpoints and checkpoint tensors are finite.
  Both final checkpoint object/arm/seed/configuration/SHA identities match the run;
  both actors retain duration parameters. Tensors are FP32; actor parameter count
  32264 and critic counts 34817/34177 match. Final total norms agree with summary.
- All three 32-endpoint J lists and all three 32-difference lists, means and conditional
  SEs recompute from episode/reset joins and equal saved primary fields. Dependence
  identity is retained. No evaluation episode is counted as another training pair.
- Gate tensor shape is 128-by-5; its norm/displacement agrees with the recorded
  2.601895809173584. Initial norm is zero and relative displacement remains null.
  Source duration exposure is preserved; its epsilon-based relative value is not
  interpreted as a meaningful ratio to a zero initial norm.

## Direct observations for DM intake

| Quantity | Recorded value |
| --- | ---: |
| GATED-V mean J | 0.1889430171129279 |
| MLP-V mean J | 0.07321588661930342 |
| H mean J | 0.16244093193733047 |
| GATED-V minus MLP-V; conditional SE | +0.11572713049362449; 0.009472055753507819 |
| GATED-V minus H; conditional SE | +0.026502085175597434; 0.009388482227809858 |
| MLP-V minus H; conditional SE | -0.08922504531802705; 0.010765618591322513 |
| Saved rule region | UP |
| GATED-V / MLP-V total relative displacement | 0.5389322229365768 / 0.46125991503565106 |
| Nonzero-hold rows: train GATED-V / MLP-V | 1473 / 1482 |
| Nonzero-hold rows: eval GATED-V / MLP-V | 90 / 90 |

This record preserves all outcomes from this one new matched training pair, including
MLP-V below H. It performs no cross-pair pooling, training-population inference,
mechanism attribution, direction disposition or formal UAV-validation declaration.

## Complete cap and resource observations

Fresh admission at 2026-09-08T20:21:01.013301Z passed: physical and effective available
memory 15642329088 bytes, above the 4294967296-byte floor. Cgroup max/headroom are
null, not zero. The enclosing command's peak RSS is 555072 KiB (542.0625 MiB).
Aggregate CPU, actual numerical thread census and device utilization were not measured;
one-process/one-numerical-thread CPU FP32 remains the fixed configuration. The raw
summary's resources_unmeasured label is preserved alongside these external facts.

Enclosing admission+scientific process wall is 304.52s; supervisor duration 305s.
Internal pair wall is 303.9593814199907s and MLP start offset 157.64559505297802s.
The nonnegative 0.5606185800093044s residual has an unobserved admission/startup/exit
split. Adding the whole residual to each internal arm interval conservatively gives:

| Complete interval bound | Seconds | Unchanged cap |
| --- | ---: | ---: |
| GATED-V conservative upper bound | 158.20621363298733 | 1800 |
| MLP-V conservative upper bound | 146.87440494702196 | 1800 |
| Whole scientific process, enclosing-command upper bound | 304.52 | 3600 |

The complete caps therefore conform. The enclosing wall includes admission and is
not an exact learner-only duration; the residual is not assigned wholly to MLP.
Startup stays GATED-owned and H/publication/readback/exit MLP-owned. External terminal
evidence resolves the raw summary's explicitly unmeasured exit-cap boundary without
rewriting the summary, resetting a clock or borrowing budget. No source failure,
missing endpoint, incomplete H or publication gap remains for this collection.

## Delivery

The designated authoring checkout was clean at
`68d08e210cb88e2c101105f0f2d442513755dd61` on `codex/direction-vsp_c1`.
Only this CM collection record and its evidence JSON are changed; scientific source,
card, intake, audit and B01 artifacts are unchanged. Scope-spec section 4 additions:
none. Collection added zero native, model, training or evaluation exposure.

Root integrates this collection commit; `/root/dm_vspc1_p49_value_question` owns
scientific intake and the P55 all-outcome stop. No third pair or other follow-on call
is authorized by technical collection acceptance.
