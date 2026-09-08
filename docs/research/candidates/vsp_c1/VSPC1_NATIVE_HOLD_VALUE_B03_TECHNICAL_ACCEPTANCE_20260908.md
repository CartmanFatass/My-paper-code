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

## Exact Root command

Pending source commit binding and staged LF shell verification; no supervisor
submission or result-bearing payload is executed by this engineering assignment.
