# VSPC1 B04 binding: technical acceptance

The [B04 CM specification](VSPC1_NATIVE_HOLD_VALUE_B04_CM_SPEC_20260908.md) and
[card §§2–5](VSPC1_NATIVE_HOLD_VALUE_B04_SCIENCE_CARD_20260908.md) define this
engineering delivery. Designated checkout:
`C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`, branch
`codex/direction-vsp_c1`, initially clean at
`0a60f57514709a0eb390253576dc8df8f7d47c21`.

## Changed boundary and checks

The new 35-line `scripts/run_vspc1_native_hold_value_b04.py` copies the accepted
B03 caller with only the object/card labels and fixed seed changed to B04/8202.
It still supplies `normalize_value=True`. Core learner, moments, actors, critics,
PPO, .01 entropy, native credit/reward/hold law, sampled endpoint and deadlines
remain byte-identical to accepted source
`7a8ed3aa5d25ded71164aa338749d09318124dcf` on the declared scientific surface.
The existing B03 runner/tests were not edited. Scope-spec §4 additions: none;
35 new non-test lines, runner35, within2000/600.

Exact original focused command, with `PYTHONDONTWRITEBYTECODE=1`:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/native_hold_value_b04_binding tests/experiments/candidates/vsp_c1/native_hold_value_b04
```

One invocation, exit0;7 passed in3.79s, process wall5.3719231s, within300s.
The existing unknown `cache_dir` warning accompanies disabled cacheprovider.
Result retained at `temp/directions/vsp_c1/engineering/native_hold_value_b04/focused_result.json`.
Tests verify8202 propagation, rejection of8101/8102/8201/9001/fixture before
scientific state, normalized configuration, all private820200000-based RNG domains,
full stubbed schedule and B04 summary/both checkpoint identities. Stub moments are
fresh per arm and frozen through evaluation/H. No scientific model or environment
was constructed; stub schedule counts are metadata, not executed native exposure.
Accepted B03 arithmetic and partial-update checks were reused without rerunning.
Only the verified invocation scratch was removed after result retention using
PowerShell leaf-file and empty-directory removal; final `Test-Path` was False.

[Independent review](VSPC1_NATIVE_HOLD_VALUE_B04_PRODUCTION_REVIEW_20260908.md)
covers the changed key/object/RNG/publication boundary and later actual staging.

## Cost and publication coverage

Per-arm planning reuses card §5: initialization +131072*c_env_actor
+256*c_moment_merge(512)+1024*c_update+8192*c_eval+publication. MLP additionally
owns8192 H steps and pair publication/readback/exit. B03 enclosing310.79s is the
complete-path reference, not a B04 performance guarantee. Normalization-specific
overhead and B04 aggregate CPU remain unmeasured; no calibration was selected.
Serial execution makes study critical path and summed invocation wall coincide
for the sole complete logical invocation. Caps remain1800s/arm and3600s/pair.

Post-learner B04 identities and moment/checkpoint/summary publication/readback are
covered by full-schedule stubs. Native publication and normalization evidence reuse
accepted B03 collection. The main integration gap concerning existing UCOPE
`environment.py` and `__init__.py` does not alter this complete direction source;
Root retains integration responsibility.

## Exact source staging and Root command

Source accepted and remote staging verified below. This CM
executes no admission, scientific payload, native smoke or standalone fixture.
The owner's safe pause allows only current P66 through its sole8202 run and intake,
then a clean pushed stop; no successor or additional scientific invocation follows.

Reporting disposition: unchanged source retains the historical epsilon-denominator
duration relative-displacement field when its initial norm is zero. At collection,
retain the raw field but treat that ratio as undefined and report absolute movement;
it is not evidence of relative exposure. Gate relative movement is already null.
This reconciles card §5's reporting requirement without changing the accepted source.


Accepted scientific source: `a33a3820fe9d4a46a3231bcf267afc956554b6c5`, pushed immediately.
Remote node `hmasd-wsl-node` uses the configured interpreter and CPU FP32 route.
The existing bundle/fetch route created actual detached cwd `/home/wu/hmasd-worktrees/vspc1-native-hold-value-b04-8202-a33a3820fe9d`.
Direct `rev-parse HEAD` equals the accepted full SHA, `status --porcelain` is empty,
and `symbolic-ref -q HEAD` exits1 (detached). Twelve required source paths exist
and their remote SHA256 digests match exact committed blobs, including UCOPE
`environment.py` and `__init__.py`, learner/policy/study, B01 study/critic,
normalization module, native environment/adapter and runner/preflight.
[Staging evidence](VSPC1_NATIVE_HOLD_VALUE_B04_STAGING_EVIDENCE_20260908.json)
records the actual commands and outputs. No source rewrite or import smoke occurred.

The script is staged at `/home/wu/hmasd-inputs/vspc1_hold_value_b04_8202_a33a3820fe9d.sh`;
local bytes are retained at `temp/directions/vsp_c1/engineering/native_hold_value_b04/launch_8202_a33a3820fe9d.sh`.
It has655 UTF-8 bytes,8 LF and zero CR; remote readback is identical. SHA256:
`a3f46d2ce69d4f2e818dd9008f4ac978a9dddd0c815dbb41d0ec123f5ecb1228`. `bash -n` exits0; staging/syntax/readback command process
wall was1.521803s. No scientific payload or admission was executed.

```bash
#!/usr/bin/env bash
# Accepted source: a33a3820fe9d4a46a3231bcf267afc956554b6c5
set -euo pipefail
exec /usr/bin/time -f 'whole_wall_seconds=%e,peak_rss_kib=%M' /bin/bash --noprofile --norc -c '
cd /home/wu/hmasd-worktrees/vspc1-native-hold-value-b04-8202-a33a3820fe9d &&
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b04_8202_a33a3820fe9d_admission.json &&
/home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_native_hold_value_b04.py --seed 8202 --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b04_8202_a33a3820fe9d
'
```

Ready exact Root submission, after DM binding/integration:

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run vspc1_hold_value_b04_8202_a33a3820fe9d /bin/bash /home/wu/hmasd-inputs/vspc1_hold_value_b04_8202_a33a3820fe9d.sh
```

Requested handle `vspc1_hold_value_b04_8202_a33a3820fe9d` returns `not_found` before submission.
Output `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b04_8202_a33a3820fe9d` and adjacent admission `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b04_8202_a33a3820fe9d_admission.json`
are directly absent. Both historical B03 supervisor identities and output remain
untouched. The existing whole-process timer includes admission and process exit;
cooperative1800s/arm and3600s/pair checks retain partial-publication behavior.
At collection report enclosing/internal wall and charge any unpartitioned
nonnegative residual conservatively to both arm upper bounds. No hard-KILL,
retry, new budget or clock reset is added. Final runtime conformance remains
unmeasured until Root's sole accepted handle terminates.
