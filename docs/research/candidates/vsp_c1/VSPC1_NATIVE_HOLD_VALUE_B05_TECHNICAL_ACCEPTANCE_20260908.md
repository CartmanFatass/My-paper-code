# VSPC1 B05 source technical acceptance

P69 selects the source engineering task in the
[B05 CM specification](VSPC1_NATIVE_HOLD_VALUE_B05_CM_SPEC_20260908.md), under
[card §§2–6,8](VSPC1_NATIVE_HOLD_VALUE_B05_SCIENCE_CARD_20260908.md).
This delivery ends at accepted source. It includes no remote staging, resource
admission, scientific invocation, native constructor/episode, or standalone learner
fixture. Native performance and the proposed comparison remain unmeasured.

## Source change

Checkout `C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`, branch
`codex/direction-vsp_c1`, was clean at
`5bf2d063dbc3c98fbe9eef34da4cb64f83ce7571`; complete starting production surface
`d220ef01c717c3053c2b26528c6f984302ee4aee` is retained.

The new25-line `native_hold_value_b05/critic.py::WideCritic` deep-copies the common
ordinary network. It retains the complete136→128 first layer, existing128 second
rows/biases and output weights/bias; a private CPU FP32 generator seeded b+12 draws
5×128 appended weights followed by5 biases, uniform ±1/sqrt128. Five appended
output weights start zero. The result is an ordinary fully connected
136→128→133→1 tanh MLP with34,827 trainable critic parameters; GATED retains34,817.
No layer initializer consumes the global RNG and no weight is frozen. Replacement
parameters are registered before the existing optimizer is constructed.

`native_hold_value_b01/critic.py::models` gains direct optional width128 and
extra-seed arguments; only the width133 ordinary path constructs WideCritic.
The shared study passes those options only for B05, records its extra seed,
per-arm architecture and actual parameter count, saves them with both final
checkpoints and checks them in existing readback. Width128 keeps its former
configuration/checkpoint fields. The new35-line runner accepts only8301 and passes
width133, extra seed830100012, normalization=True and B05 object/card.

Default actor/gate and common initialization, independent arm copies/optimizers/
RNG streams/moments, normalized native credit, .01 entropy, compound PPO, H order,
complete counts/deadlines and primary keys/thresholds remain unchanged. Protected
UCOPE, normalization, native environment and historical runner diff against the
starting source is empty. No old weights/state/results are loaded.

Complete production delta95 added/9 removed lines: shared critic7/2, study27/7,
new critic25, marker1, runner35. Scope-spec §4 additions:none; within2000-source/
600-runner limits. This is the card's scientific architecture change, not machinery.
CM inspected the complete diff and `git diff --check` passes.

## Focused acceptance

Original command, with `PYTHONDONTWRITEBYTECODE=1`:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/native_hold_value_b05 tests/experiments/candidates/vsp_c1/native_hold_value_b05
```

Exit0;16 passed in13.65s. The exec yielded while running, so full enclosing process
wall was not separately retained. Directly affected existing checks:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/native_hold_value_b05_defaults tests/experiments/candidates/vsp_c1/native_hold_value_b04 tests/experiments/candidates/vsp_c1/native_hold_value_b01/test_critic.py
```

Exit0;9 passed in2.69s, stopwatch process wall3.7350489s. Both invocations passed
first try; total pytest wall16.34s, within the300s focused budget. Existing unknown
`cache_dir` warning accompanies disabled cacheprovider. Retained result:
`temp/directions/vsp_c1/engineering/native_hold_value_b05/focused_result.json`.
After retaining evidence, only both verified invocation scratch paths were removed
using native PowerShell leaf/empty-directory removal; both final Test-Path values
were False. No scientific evidence or other invocation was removed.

Tests substantiate exact copied tensors, draw order, private-generator isolation,
unchanged global/action RNG states and matched independent actors/duration heads,
all136 connected inputs, trainable34,827/34,817 counts, initial value agreement
at rtol1e-5/atol1e-6, and the declared two-stage gradient behavior: appended outputs
receive first-pass gradients; incoming rows/biases start with zero gradients and
learn after the outputs move. These are bounded deterministic tensor operations,
not a native/PPO fit or scientific performance measurement.

Full stubbed plumbing checks verify8301/width133/normalization/extra-seed propagation,
invalid old seeds/fixture/width flags rejected before scientific state, every
private830100000-based action/reset domain, fresh independent moments, final-only
286720/2048/96 counts and H order, normalized units, frozen moments and B05
architecture/count identity in summary and both checkpoints. Stub counts/returns
are metadata only. Five primary-region cases include both inclusive±.01 endpoints
and missing-primary/H behavior with unchanged contrast keys. Existing B04 full-stub
binding and B01 critic tests confirm the shared defaults; broader historical/native
normalization/PPO/deadline coverage is reused without replay.

## Review, coverage and next owner

[Independent review](VSPC1_NATIVE_HOLD_VALUE_B05_PRODUCTION_REVIEW_20260908.md)
checks architecture, initialization/RNG, optimizer registration, normalized caller
and publication meaning. CM dispositions are recorded there; source test success
establishes conformance, not a gated-capacity mechanism result.

Changed post-learner architecture/count identity and readback are covered by stubs;
unchanged native publication and moments reuse accepted B03/P67 evidence. No fresh
native assessment is selected. A later result-bearing plan retains card §6's own
per-arm law and costs; width133 native wall remains unmeasured by this source task.

After this source acceptance, DM supplies the exact prospective execution binding
to Root under P69. No remote staging/admission/submission is part of this return.
The completed three CM-comparison batches are unchanged; no fourth is enrolled.
