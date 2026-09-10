# CRTO B08 finite-zero movement repair evidence

Source correction technically accepted after focused checks and independent semantic review. This is the
bounded repair allocated in [repair intake §§1–3](CRTO_B08_ZERO_MOVEMENT_REPAIR_INTAKE_20260909.md),
responding to the special Pro review §2.10 paragraph at line133, original response commit
`e865e7b25beb16a7348070181161f18706fced4e`. No scientific run or family reopening is part of it.

Checkout `C:/Projects/HMASD-worktrees/codex-crto`, branch `codex/crto`, began clean at
`ced81c37f321bc64cf427e075821903d3423bce5`. Required inputs were already synced at31cf38b79.
No main/index edit, branch creation or runtime/model hot-reload claim was made. CM owns only
the B08 train_path source, matching test file and this result evidence; DM retains intake,
DIRECTION, audit and final annotation. No unrelated change was present or edited.

## Necessity, dependency and meaning

Read the current card §§6–7, evidence-spec §§11.4,11.8.5–7,11.10, the exact review paragraph,
and the scientific-tools skill's scientific-reading reference. Applied FOUNDATIONS §§4/6 and
04_EMPIRICAL sections “先分清在比较什么”, “随机性有层级”, “完整方法比较与机制归因” to distinguish
the optimizer process, endpoint parameters/policy, and native evaluation. The assumption used
here is narrow: the card asks to emit actual exposure and intact update execution, not to
require a positive endpoint norm. A finite zero norm therefore cannot prove absent optimization;
positive movement likewise cannot prove useful learning, competent native behavior or alignment.
This reasoning changes only the validity proxy. No external literature claim/search was needed.

Inspected read-only A01 helpers `_parameter_tensors`, `_parameter_scales`, `_movement`,
`_exposure_line` and the B08 train_path caller. Initial parameter clones are private to each
training path. `_movement` flattens initial and endpoint parameters in FP64 and measures their
net difference, normalized by initialization scales; it neither integrates path length nor
counts backward/Adam calls. Snapshot deep copies and exposure dictionaries are the downstream
consumers. They already support finite zero values without a serialization change.

The old final-update condition rejected any displacement value <=0. The repair retains only
the existing finite-value condition at every recorded endpoint. It still uses the same actual
movement computation, snapshots, exposure fields and last-batch loss. No synthetic positive
movement is substituted and no threshold is lowered in scientific scoring.

The only old indirect protection for an unrelated differentiable leaf loss was final movement:
`backward()` can succeed yet reach no model parameter; the previous nonfinite-gradient scan
skips None. Immediately after backward, train_path now rejects **all model parameter grads None**.
This detects that concrete broken graph directly, before clipping/Adam. A loss with no grad_fn
still fails through PyTorch backward. Finite zero gradients are accepted. There is no per-parameter
connectivity requirement or positive/nonzero gradient requirement. Nonfinite loss, present
gradients, post-step parameters and reported movement remain rejected by their original checks.

The objective, data/RNG, initialization, Adam arguments, clipping, update/cyclic order,
snapshot timing, exposure contents, endpoints and primary native score/reading are unchanged.
Older B04/B06/B07/A01 helpers were not repaired. Original B08 results remain bound to their
original source d9f643b76; all actual endpoint movements were positive, so this branch did not
invalidate or alter the completed B08. No historical result or claim is regenerated/reclassified.

ENGINEERING_SCOPE_SPEC §4 additions: **none**, as card §7 and this allocation require. The
runtime change adds4/deletes3 lines (net+1); no framework, telemetry or new launch machinery.
The direct missing-gradient check replaces the invalid movement proxy for the same training
integrity need. Runner unchanged. Current module316 + initializer1 + runner43 =360 runtime lines,
within2000/600; tests add90 lines including existing preservation-check adaptation.

## Focused synthetic acceptance

One local invocation:

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/commitment_residual_triggered_options/test/b08-zero-movement-20260909-a tests/experiments/candidates/commitment_residual_triggered_options/native_cost_b08/test_native_cost.py -k 'finite_zero or integrity_failures or loss_loop'
```

Result: **8 passed,13 deselected in5.41s**, command process wall7.016s. Total focused test wall
5.41s against300s. No repeat smoke or full historical suite was run. `git diff --check` passed.
The named invocation root was not created (no tmp_path fixture needed); `Test-Path` confirmed
absent, leaving no scratch to clean. No scientific evidence root was removed.

The connected stationary fixture patches only the production model constructor, RNG factory
and row collation with an eight-parameter synthetic module and two equal-cost rows. It calls
the actual B08 expected-cost loss/backward, real Adam/clipping, snapshot, movement and exposure
code. Both legal cost rows are constant zero, so connected gradients are finite zero. A wrapper
records two completed calls of the original Adam.step and their present zero gradient tensors.
Both snapshot update counts/examples (1/2 updates,2/4 examples) and both displacement ratios0
are emitted, with unchanged nonzero initial parameters and finite loss0. This fixture would
have failed at the old final movement condition after the two Adam calls.

Six injected failure cases verify: nonfinite loss before stepping; nonfinite gradient before
stepping; corrupted parameter after one step; nonfinite movement after one step; unrelated
requires-grad leaf with no model gradients before stepping; and detached loss rejected by
backward before stepping. Total synthetic Adam calls across this invocation:4 (stationary2,
parameter corruption1,movement corruption1); these are engineering fixture work, not scientific
optimizer exposure. The existing B04 update-body preservation comparison still passes after
normalizing only the explicit new missing-gradient check in addition to its prior known B08
loss/timer differences. Primary score/reading code is untouched, so no native evaluator test
or scientific packet/model/host was invoked.

## Review and closure

The original independent reviewer `rev_ah_crto_b08` inspected the exact diff against ced81c37f,
actual movement/exposure dependencies, current assignment/specification and scientific-reading
passages. Its final disposition: **no material finding**. It confirmed that zero_grad before
backward makes all-None a direct broken-graph check, finite connected zero gradients remain
valid, detached loss still fails, and movement/exposure emit finite zeros. It inspected the
stationary two-Adam-call fixture and six failure cases without rerunning them; it found no
unscoped machinery or changed scientific computation. Its explicit limit is that connectivity
is not useful optimization or native value. No reviewer files/index edits occurred. CM inspected
the complete source/test diff and accepts this correction; no separate verifier was needed.

Zero new scientific exposure:0 result-bearing invocations,0 environment/native/evaluator calls,
0 production model or seed-package constructions,0 scientific optimizer updates. No profile,
remote scientific staging, admission, retry/resume, new seed/arm/endpoint or Pro Send occurred.
The fixture imports the existing module definitions to reach train_path but substitutes the
production constructor/RNG/collation before execution; no production package is instantiated.

Remaining ceiling: this demonstrates the specified finite-zero and broken-graph behavior under
synthetic inputs. It does not demonstrate native learning or certify arbitrary missing individual
gradients. Root integrates the accepted source; DM records final annotation. The general PARK
and no-successor boundary remains after this specifically allocated repair.
