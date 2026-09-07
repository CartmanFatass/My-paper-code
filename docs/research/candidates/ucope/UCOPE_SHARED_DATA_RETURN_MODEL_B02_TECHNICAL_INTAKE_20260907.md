# UCOPE shared-data return model B02 — CM technical return

**Implementation technically accepted; no real-host invocation performed.** Root dispatched
Portfolio command `P07-UCOPE-IMPLEMENT-01` against frozen main `c4687f6f2`. This return and its
source/tests are delivered together on `codex/cm-ucope-shared-data-return-b02-20260907`; the exact
delivery commit is returned to Root. Scientific contract: [card §§2–6](UCOPE_SHARED_DATA_RETURN_MODEL_B02_SCIENCE_CARD_20260907.md).
This is engineering acceptance, not scientific intake or permission for a future launch.

## Delivered path and preserved behavior

- `experiments/candidates/ucope/shared_data_return_model_b02/model.py` owns zero-initialized
  binary64 values/integer counts, one private behavior stream, streamed collection, observed-action
  incremental means, final FULL/BLIND policies and actual scalar-update/movement exposure.
- `evaluation.py` owns deterministic FULL/BLIND/IMMEDIATE-4 host calls on paired addresses,
  `math.fsum` means and sample variances, conditional Monte Carlo SE and the frozen RM rule.
- `scripts/run_ucope_shared_data_return_model_b02.py` is the fixed seed-6401 CLI and compact
  complete/partial `summary.json` publisher. The summary includes final learned values/counts,
  histogram, final actions, context/overall returns and differences, probe/paid components,
  actual event/time/update counts and movement. There is no checkpoint selection or resume path.
- `tests/experiments/candidates/ucope/shared_data_return_model_b02/test_shared_return.py` contains
  the focused synthetic changed-path/publication case and twelve branch-boundary cases.

Collection holds one model state containing both fits and a shared immediate table; it retains
no episode dataset. Each batch traverses the eight contexts then 32 local rows. The private
`random.Random(2006401)` supplies exactly one uniform per row, with immediate draws discarded.
Probe duration is chosen by the count-only callback, ignoring its count during collection.
Only completed `Execution.external_return` enters the learner: immediate updates the shared
table once; probe updates full, then blind, then histogram. Each value update increments its
integer count and performs `q + (R-q)/N` with Python binary64 scalars in the prescribed row order.

Final full-cell fallback uses the corresponding blind value only when the full count is zero.
FULL uses the empirical display histogram with `math.fsum`; without any observed probe it stays
immediate. Root ties stay immediate and tail ties choose the first legal period. Final evaluation
freezes these learned plans; FULL sees the current displayed count only inside its callback,
BLIND ignores it, and all three policies share each context/index/eval ancestry. Evaluation stores
only one context's episode arrays to calculate the prescribed paired moments, then retains its
compact measurements. Interrupted evaluation retains actual counts and completed-context facts.

The four bound historical host/contract/RNG/oracle modules are unchanged: Git comparison against
`a0b00f561159ddeedf66b65711cf3f7d2ec93b04` is empty. No B01 learner, retained policy, posterior label,
oracle action target or other historical training path is reused. The implementation is standard
library only: one process/compute thread, no Torch optimizer, GPU or parallel reduction.

## Focused acceptance evidence

Executed once from `C:/Projects/HMASD-worktrees/cm-ucope-shared-data-return-b02-20260907`:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider tests/experiments/candidates/ucope/shared_data_return_model_b02 --basetemp temp/directions/ucope/test/shared-return-b02-synthetic-01
```

**13 passed in 0.36 s**, within the five-minute directory allowance. The existing pytest
`cache_dir` warning with cacheprovider disabled is unrelated to the tested behavior. Every host
call in this check is replaced by a synthetic fixture; none calls the real environment or its RNG.
The main fixture traverses the real runner/collector/evaluator/publisher with 256 mock training
rows, 384 scalar updates and 96 mock evaluation executions, then reads the emitted JSON. Independent
reference calculations verify the observed-action tables/counts, same-label sharing, stream/order,
all paired differences, `ddof=1` variances and overall SE. Additional in-case fixtures pin unseen
cells, observed-zero cells, no-probe FULL behavior and root/tail ties. A synthetic interruption
after one mock immediate observation confirms `INCOMPLETE` publication with its actual value/count.
The twelve rule cases include both MEI boundaries, RM-D, incomplete primaries and positive native
gain without FULL acquisition. No bit-identity or historical replay claim is made.

Synthetic complete/partial JSON artifacts are under
`temp/directions/ucope/test/shared-return-b02-synthetic-01/test_synthetic_changed_path_an0/`
in that local worktree. They are test fixtures, not B02 result evidence.

Independent affected-path Reviewer `review_ah_ucope_b01` inspected this B02 source/card and found
**no material defect**. Its separate synthetic reference covered two batch boundaries (512 mock
training rows, 768 scalar updates) and 24 three-policy evaluation indices. It verified stream/order,
binary64 updates, the shared immediate fit, fallback/ties, information timing, paired means/SE and
RM integrity handling. Its interrupted-evaluation fixture retained policy counts `[4,3,3]`,
completed first-context measurements and serializable partial output without overall primary.
The review performed zero real-host calls, admissions or scientific invocations. CM's on-disk
complete/partial checks supply the publication boundary the reviewer initially left unverified.

## Scope, exposure, cost and remaining boundary

New non-test source is **285 lines**: model 125, evaluation 80, initializer 1, runner **79**.
Tests are 179 lines. `git diff --check` passes. ENGINEERING_SCOPE_SPEC §4 additions: **none**,
as card §5 requires. Final-value serialization is a compact learner result, not resume machinery.
No source guard, schema validator, worker pool, registry, provider transport or extra telemetry
was introduced. The fixed scientific workload and all comparisons remain intact.

**Actual scientific exposure in this assignment: 0 real episodes, 0 real-data scalar updates,
0 real evaluations, 0 admissions, 0 provider Sends.** Synthetic rows above do not increase the
independent-dataset count and establish no acquisition value. Future selected work remains one
shared seed-6401 dataset: 262,144 training episodes, 393,216 scalar value updates and 98,304
evaluation episodes, with one complete 600 s cap covering both fits and all three evaluations.

Cost law is `T_init + 1024*T_batch256_shared_fit + 32768*T_three_policy_eval + T_publish`.
Its real-host unit coefficients remain unmeasured. Synthetic test wall is not a B02 cost estimate;
no real-host pilot or inherited B01 timing is substituted. There is no measured cap conflict.
The runner checks elapsed wall and publishes partial state on ordinary errors/interrupts; future
whole-process timeout, adjacent destination admission and peak-RSS measurement use the existing
configured remote route when separately assigned. Internal wall includes first summary publication
but excludes the final measurement-refresh write; external whole-process timing must cover that
write and interpreter startup/exit. Aggregate CPU and formal study elapsed are unmeasured.

No implementation gap remains. Root integrates the explicit owned paths and returns the technical
delivery to DM/Portfolio. A future real-host run and scientific interpretation remain separately
assigned work; this implementation delivery starts neither.
