# VSPC1 B03 normalization: technical acceptance

Engineering acceptance under [B03 CM specification](VSPC1_NATIVE_HOLD_VALUE_B03_CM_SPEC_20260908.md)
and [card §§2–5](VSPC1_NATIVE_HOLD_VALUE_B03_SCIENCE_CARD_20260908.md).
This assignment creates no native experiment, calibration, scientific model fit or
standalone runner fixture. Independent [review](VSPC1_NATIVE_HOLD_VALUE_B03_PRODUCTION_REVIEW_20260908.md)
inspects the numerical, credit, RNG and publication boundaries.

## Source and protected behavior

The designated checkout is `C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`,
branch `codex/direction-vsp_c1`, initially clean at
`b16d269d700401615f9adcdc191ac1114a9191c2`.
The minimal opt-in parameters preserve unnormalized collection/update defaults and
the existing shared entropy argument. B03 explicitly uses .01 entropy. A new scalar
`ValueMoments` stores per-arm CPU FP32 population moments outside autograd/optimizer
state. Collection decodes the old normalized critic into native value units. Update
forms native advantages first, merges exactly the two-episode native RTG rows once,
and reuses detached normalized targets for four epochs. There is no output/optimizer
rescaling, extra model forward, parameter or RNG stream.

The study records actual moments in rollouts, final checkpoints and summary, freezes
them through evaluation/H, and retains advanced moments even if a partial update
fails before Adam. The fixed8201 B03 runner selects the method and identity.
Explicit surface comparison against complete starting source
`e5cc7ce67cf9dfa4ebd95324bf5c67423bc9977a` is empty for B01/B02 runners, gated critic,
UCOPE policy and environment. Native code was not edited. PPO grouping, native reward,
held recurrence, common initialization, private RNGs, schedule, final-only endpoint,
H order and continuous deadlines are unchanged.

Scope-spec §4 additions: none. Production changes add127/remove13 lines, including
the35-line runner; within2000/600 limits. Test package marker `__init__.py` is the
minimal collection repair for two identically named test modules.

## Focused evidence

Exact command, with `PYTHONDONTWRITEBYTECODE=1`:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/native_hold_value_b03_normalization tests/experiments/candidates/vsp_c1/native_hold_value_b03 tests/experiments/candidates/vsp_c1/native_hold_value_b02/test_binding.py tests/experiments/candidates/vsp_c1/native_hold_value_b01/test_study.py::test_cli_fixed_configuration_without_running_fixture
```

Final exit0,17 passed in2.54s; process wall3.5546191s. First invocation failed only
at collection because B02/B03 had duplicate `test_binding` module names
(2.02s pytest,3.01197s process); adding the B03 package marker fixed that and the exact
command passed. Combined process wall6.5665891s is within300s. Existing unknown
`cache_dir` warning accompanies disabled cacheprovider. Retained result:
`temp/directions/vsp_c1/engineering/native_hold_value_b03/focused_result.json`.

Deterministic tiny generic modules/parameters check population merge/floor,
no moment gradients or optimizer parameters, old native decoded values across two
collections, native detached advantages shared across all four epochs, expected
normalized/native MSE and pre-clip critic gradients, .5 value and .01 entropy weights.
Full schedule uses fake scientific constructors/operations and real scalar moments;
its286720steps/2048Adam/96eval counters are stub metadata, not scientific exposure.
It checks fixed8201 rejection/propagation, all private RNG domains, one moment merge
per512 rows, separate arm state, frozen final evaluation/H, both checkpoint and
summary round-trips, and failure after a merge before Adam (n512,updates1,Adam0,
rollouts0 retained). Historical B02 binding and B01 no-run CLI checks pass unchanged.
No historical runner smoke was repeated. Inspected complete changed source and
`git diff --check` passes.

Only this invocation's resolved scratch directory under the designated checkout's
`temp/directions/vsp_c1/test/native_hold_value_b03_normalization` was cleaned after
retention, by native PowerShell leaf-file and empty-directory removal. Final
`Test-Path` was False. No other invocation/evidence root was removed.

## Cost and publication coverage

Per-arm projection reuses card §5: initialization +131072*c_env_actor
+256*c_moment_merge(512)+1024*c_update+8192*c_eval+publication. MLP also owns8192 H
steps and pair publication/readback/exit. Prior pair enclosing walls308.63s/304.52s
are planning references; scalar overhead remains unmeasured, with no new calibration
selected. The study is serial, so study critical path and sum of invocation wall
coincide for this single complete logical invocation; aggregate CPU is a separate
unmeasured quantity. Caps remain1800s per arm/3600s complete pair. These are planning
facts, not measured B03 performance or resource conformance.

Post-learner coverage exercises affected summary, moment/checkpoint publication and
readback through full stubs, plus partial-state preservation. Existing native path
coverage is reused; actual8201 training/evaluation/publication remains the sole
subsequent Root invocation. CPU FP32 portability is the existing accepted route.

## Exact Root command (staged, not submitted)

Accepted source commit `7a8ed3aa5d25ded71164aa338749d09318124dcf` was pushed immediately. Later
command/review documentation does not change the accepted source surface.
Configured node: `hmasd-wsl-node` (wsl_4070); CPU FP32, one process and numerical
thread, no device change. Exact detached cwd: `/home/wu/hmasd-worktrees/vspc1-native-hold-value-b03-8201-7a8ed3aa5d25`.

Local script: `temp/directions/vsp_c1/engineering/native_hold_value_b03/launch_8201_7a8ed3aa5d25.sh`.
Remote script: `/home/wu/hmasd-inputs/vspc1_hold_value_b03_8201_7a8ed3aa5d25.sh`. Exact bytes:655, UTF-8 without BOM,
8 literal LF and no CR. SHA256: `46a2ac327ddf65350c6af18282a7e87944c5be921c7008a0a5423cc0199e916e`.
Remote readback matches all bytes. Syntax-only check exited0 in0.4038779s;
scp readback exited0 in0.5733178s. No payload, resource admission, scientific state
or supervisor submission was executed. Binding evidence is retained in the same
local engineering directory's `launch_binding.json` and `remote_readback.sh`.

```bash
#!/usr/bin/env bash
# Accepted source: 7a8ed3aa5d25ded71164aa338749d09318124dcf
set -euo pipefail
exec /usr/bin/time -f 'whole_wall_seconds=%e,peak_rss_kib=%M' /bin/bash --noprofile --norc -c '
cd /home/wu/hmasd-worktrees/vspc1-native-hold-value-b03-8201-7a8ed3aa5d25 &&
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b03_8201_7a8ed3aa5d25_admission.json &&
/home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_native_hold_value_b03.py --seed 8201 --out /home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b03_8201_7a8ed3aa5d25
'
```

Root submits the already-staged script once after integrating and staging the exact
accepted source checkout:

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run vspc1_hold_value_b03_8201_7a8ed3aa5d25 /bin/bash /home/wu/hmasd-inputs/vspc1_hold_value_b03_8201_7a8ed3aa5d25.sh
```

Handle: `vspc1_hold_value_b03_8201_7a8ed3aa5d25`.
Output root: `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b03_8201_7a8ed3aa5d25`.
Fresh actual-node admission: `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b03_8201_7a8ed3aa5d25_admission.json`.
The literal syntax check was:

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /bin/bash -n /home/wu/hmasd-inputs/vspc1_hold_value_b03_8201_7a8ed3aa5d25.sh
```

**Root still owns source checkout staging.** This CM has staged only the shell input,
not claimed the named detached source cwd exists. Root uses its existing committed
source staging route and checks the actual cwd/source surface before submitting.
There is no native invocation or second normalized pair in this assignment.

The enclosing `/usr/bin/time` measures admission plus the scientific process through
exit, with peak RSS; it does not impose an earlier hard-KILL deadline. Existing
continuous1800s/arm and3600s/pair checks preserve partial results. At collection,
charge startup/common initialization to GATED and H/publication/readback/exit to MLP;
if the external/internal residual split is unknown, report it and use its entire
nonnegative amount in each conservative arm upper bound. An indivisible overrun
remains a breach, not a new allowance. Measured resource and wall conformance remain
pending the sole accepted handle. DM owns all-outcome scientific intake; this same
CM is available for collection on Root's continuation.

## Mechanical cwd correction after failed supervisor acceptance

This section supersedes the pending source-staging statement and original supervisor
name above. It preserves the original failure; no scientific retry was selected.
[Direct evidence](VSPC1_NATIVE_HOLD_VALUE_B03_CWD_CORRECTION_EVIDENCE_20260908.json)
contains terminal status, full log, actual supervisor wrapper, clean detached source
checks, absent admission/output paths and unchanged script digest.

Original handle `vspc1_hold_value_b03_8201_7a8ed3aa5d25` was accepted and failed with
exit1, PID3009140, inactive tmux. Its log records start/end
`2026-09-09T06:40:46+08:00`, missing exact cwd, displayed whole wall0.00s and peak
RSS3200KiB. This is wrapper-only evidence, not native resource conformance. The
failed `cd` is the first link in the shell's `&&` chain: neither admission nor the
scientific runner executed. Both admission and output paths were directly absent.
The original task directory/log/status/exit/runner files remain untouched remotely;
full log also retained locally as `failed_task.log` in the B03 engineering directory.

The remote `/usr/local/bin/agent-task` implementation permits reuse after tmux ends,
but removes/replaces exit/status/start/runner metadata and appends the same log.
To preserve the failed identity, the corrected submission uses only a new supervisor
name, `vspc1_hold_value_b03_8201_7a8ed3aa5d25_cwd1` (direct status: `not_found`).
Scientific source/master/output/admission/script and budgets remain identical.

The existing Git bundle route transferred already committed direction objects from
local `source_stage.bundle` to
`/home/wu/hmasd-inputs/vspc1_b03_7a8ed3aa5d25_source.bundle`, fetched into the configured
remote repository, and created the exact detached worktree:

```text
git -C /home/wu/projects/HMASD worktree add --detach /home/wu/hmasd-worktrees/vspc1-native-hold-value-b03-8201-7a8ed3aa5d25 7a8ed3aa5d25ded71164aa338749d09318124dcf
```

Actual HEAD equals the bound full SHA, `git status --porcelain` is empty and
`symbolic-ref -q HEAD` returns1 (detached). The admission script, fixed runner and
normalization module are present. No source byte was edited. The staged shell's
SHA256 remains `46a2ac327ddf65350c6af18282a7e87944c5be921c7008a0a5423cc0199e916e`;
prior syntax/readback evidence is reused. An initial remote `cat-file` read stalled
and its local SSH command was interrupted; the bundle route completed normally.
No tests, profiling, admission, scientific model, learner or evaluation ran during
this mechanical correction.

Ready exact Root submission (not executed by CM):

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run vspc1_hold_value_b03_8201_7a8ed3aa5d25_cwd1 /bin/bash /home/wu/hmasd-inputs/vspc1_hold_value_b03_8201_7a8ed3aa5d25.sh
```

Root owns this single scientific submission, fresh admission and terminal observation.
The source remains `7a8ed3aa5d25ded71164aa338749d09318124dcf`; this is a docs/evidence
correction only, with no replacement source, seed, script, output or allowance.
