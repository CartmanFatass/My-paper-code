# VSPC1 B05 — independent wider-critic source review

No material production finding was found by direct inspection and review of the
CM's focused check evidence. This is independent technical evidence, not
approval, permission, mechanism evidence, or a scientific disposition.

Contract: [B05 CM specification](VSPC1_NATIVE_HOLD_VALUE_B05_CM_SPEC_20260908.md)
and [B05 card sections 2–6 and P69 allocation section 8](VSPC1_NATIVE_HOLD_VALUE_B05_SCIENCE_CARD_20260908.md).
Checkout: `codex/direction-vsp_c1`, assignment input
`5bf2d063dbc3c98fbe9eef34da4cb64f83ce7571`, with complete scientific source
`d220ef01c717c3053c2b26528c6f984302ee4aee`.
The reviewer owns only this document and executed no tests, models, learner fit,
native invocation, fixture, staging, admission, submission, or commit.

## Architecture, initialization and optimizer

`WideCritic` copies the source network and widens its ordinary second/output
Linear layers to 133. The first layer, first 128 second-layer rows/biases and
first 128 output weights/scalar bias retain their copied values. No gate,
hold-column specialization, new input, layer or recurrent state enters this MLP.
Both hidden activations remain the source tanh operations; scalar output and
leading batch shapes remain those of the original critic.

The added rows are a contiguous CPU FP32 `5x128` uniform draw, followed by five
biases, from a private generator seeded 830100012. Bounds are exactly the selected
`+/-1/sqrt(128)`. Five appended output weights start at zero. Deep copies and
concatenated parameter tensors keep source/arm storage independent. Private draws,
zero allocation and copying do not advance global or actor/reset generators.
GATED construction and common actor/duration initialization remain unchanged.

Replacing the second/output tensors with `nn.Parameter` registers every widened
weight and bias as trainable. The unchanged optimizer collects parameters after
construction, so appended weights are included without an extra group or stale
pre-widening parameters. Their initial incoming gradient is zero because their
outgoing weights are zero; this is the declared initialization, not freezing.
No output-preservation or equality-of-updates claim is inferred beyond initial
function correspondence within the specified FP32 tolerance.

Read-only arithmetic gives 34,827 ordinary critic parameters, 650 added over the
old full MLP: 640 incoming weights, five hidden biases and five output weights.
This is ten more than unchanged GATED's 34,817. Width changes arithmetic inside
the existing forwards, not the number of scientific forwards or learner steps.

## Caller, state and publication boundaries

The existing `models` helper adds a direct optional second-MLP width and private
seed. Default 128 retains the historical route; only 133 selects the new ordinary
critic. GATED still selects its unchanged class. The B05 CLI fixes 8301, width 133,
normalization and B05 object/card; invalid key/fixture/width flags cannot enter
scientific state. No registry, general factory or global configuration mutation
is introduced.

On the B05 path, configuration/seeds retain the extra initialization seed and
second width. Per-arm summary metadata names the actual architecture and counts
constructed critic parameters. Final checkpoints carry those fields alongside
their object/seed/configuration, weights and existing independent moment state.
Readback checks the B05 architecture/count identities against both expected and
actual retained arm metadata, and compares the published summary fields. Thus
the retained `MLP-V` key is explicitly width 133 within a B05 result. Default 128
configuration/checkpoint fields receive no added architecture metadata.

The reviewer compared the full UCOPE package, normalization module, native
environment/adapter and B01–B04 runners against complete source `d220ef01`: no diff.
The native-value normalization order, .01 entropy, PPO reduction/clipping,
private arm streams, complete schedule, final-only sampling, H reuse, counts and
continuous deadline/publication paths remain the reviewed B03 method. No earlier
weights, optimizer, moments or outputs are loaded for 8301.

## Evidence and budget

The CM's original focused B05 command passed 16 checks in 13.65 pytest seconds;
directly affected B04 binding and B01 critic checks passed nine in 2.69 pytest
seconds (3.7350489 seconds enclosing process wall). Both exited zero. Exact
commands and retained evidence are linked in the
[technical acceptance](VSPC1_NATIVE_HOLD_VALUE_B05_TECHNICAL_ACCEPTANCE_20260908.md#focused-acceptance).
The reviewer inspected the current tests and retained `focused_result.json`;
no reviewer rerun was needed. The B05 enclosing process wall was not captured,
so 16.34 seconds is the sum of pytest durations, not measured aggregate CPU work
or complete enclosing-process wall. The existing cache configuration warning
does not indicate a test failure.

Tensor checks exercise actual model construction, exact copies and private draw
order, global/action RNG preservation, initial value tolerance, all 136 connected
inputs, counts/trainability, and nonzero incoming gradients after appended output
weights move. Direct source inspection establishes optimizer registration after
widening. Full-stub checks cover the fixed CLI, every stream domain, independent
normalization moments, final evaluation/H ordering, declared complete counts,
primary thresholds and missing-data branches, and summary/checkpoint architecture
identity/readback. The stub counts and returns are interface evidence; they do
not measure native execution or scientific validity.

The production delta is 95 added and nine removed lines: shared critic 7/2,
study 27/7, new critic 25, initializer 1 and runner 35. These satisfy the
2,000-source/600-runner limits.

Runtime-spec general requirements and scope-spec sections 4–5 identify no
prohibited addition without a card line. The direct optional arguments and
architecture/count publication implement this card's changed comparator identity;
they are not unnecessary orchestration. No worker, registry, resume/retry, source
guard, manifest or telemetry framework was added. Existing CPU FP32 single-process
and one-numerical-thread execution remains unchanged.

Width-specific native runtime and scientific performance remain unmeasured. The
inherited epsilon-based duration relative field remains undefined as a relative
displacement from zero; absolute movement is the meaningful quantity. Gate's
relative field remains null. This source-only P69 task creates no remote-ready
command or execution allowance; any later run must retain the declared complete
1,800s/arm and 3,600s/pair bounds and original partial-publication handling.
