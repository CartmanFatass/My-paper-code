# UCOPE root target-versus-fit R01 — cross-node numerical-locus plan

- Parent object: `UCOPE-A-RECON-THREE-WITNESS-ROOT-TARGET-VS-ROOT-FIT-AUDIT-R01`
- Parent evidence class and claim ceiling: unchanged **A/RECON**
- Record type: bounded engineering diagnostic inside the unresolved parent object
- Frozen: 2026-09-04, before diagnostic implementation or execution
- Scientific polarity: none under every diagnostic branch

## 1. Question and protected boundary

Attempt 02 reproduced eight solver-derived reconstruction values above the frozen absolute
`1e-12` tolerance, but its output does not identify whether the cross-node difference begins in
the reconstructed `design64`, the accepted FP32 root-target path, or `lstsq(rcond=None)`. Locate
that first differing boundary without rerunning, salvaging, or reinterpreting attempt 02.

The parent card remains unchanged: same retained summary, draw, offset, generator, canonical row
order, FP32 scorer arithmetic, `numpy.linalg.lstsq(..., rcond=None)`, absolute `1e-12` tolerance
with no relative tolerance, result branches, and claim ceiling. This diagnostic cannot make a
parent mechanism branch valid and cannot authorize a fresh parent attempt by itself.

## 2. Smallest diagnostic unit

Use only the lexicographically first observed failure block:

```text
seed=ucope-scout-r01-b1-fresh-00
fold=0
contexts=8
episodes_per_context=40960
offset=2000000
```

This block is chosen because attempt 02 records all three relevant failure families there: the
MSE-exact root plus both live-arm root distances. It is an engineering failure witness, not a
scientifically selected policy or a substitute for the parent card's all-six-policy rule.

Reconstruct and retain exactly four contiguous arrays per node:

1. the fold-0 `design64` array;
2. the FP32 MSE-reference root-target array;
3. the FP32 `DOSE-MATCHED-SINGLE` live root-target array; and
4. the FP32 `THREE-WITNESS` live root-target array.

Retain their dtype, shape and C-order bytes, plus the three corresponding
`lstsq(rcond=None)` root vectors, the retained reference/live root vectors and retained
`d_learned_root` scalars. Record Python, NumPy and linked BLAS/LAPACK configuration facts.

## 3. Pinned two-node procedure

The node is part of this technical estimand; the diagnostic is intentionally pinned to the
configured Windows control-plane node and `wsl_4070`. It is not a local fallback.

1. On `wsl_4070`, from a detached worktree at the exact pushed diagnostic SHA, run one
   source-external `agent-task` payload containing a fresh passing 4 GiB
   `admit-memory && emit-solve` invocation. Copy its ordinary array payload and JSON result to the
   direction runtime tree without rewriting them.
2. On Windows at that same pushed SHA, run one fresh passing 4 GiB
   `admit-memory && compare-solve` invocation. It reconstructs the same local block, compares the
   local arrays byte-for-byte with the staged remote arrays, and runs the same
   `lstsq(rcond=None)` locally on both the local and remote array sets.

No third invocation, retry loop, alternate node, tolerance sweep, driver sweep, scientific
parent runner, or automatic repair is authorized. If either invocation is not admitted or does
not publish its complete technical payload, stop with the partial facts and return to the DM.

## 4. Observables and first-match technical rule

For every array and root vector report byte equality, maximum absolute difference, first differing
element when one exists, dtype and shape. Apply this ordered rule:

1. `DESIGN_BYTES_DIVERGE` if the two reconstructed `design64` byte streams differ.
2. `FP32_TARGET_BYTES_DIVERGE` if design bytes agree but any corresponding target byte stream
   differs.
3. `SOLVER_DIFFERENCE_EXPLAINS_BOUNDARY` if all input bytes agree and the remote-versus-local
   solve of the remote payload differs by more than `1e-12` for any root vector.
4. `SOLVER_DIFFERENCE_SUBTOLERANCE` if all input bytes agree, solver outputs differ, but every
   maximum absolute difference is at most `1e-12`.
5. `RETAINED_REFERENCE_PATH_DIFFERS` if inputs and cross-node solves agree byte-for-byte, but the
   reproduced values still differ from the retained vector/scalar by more than `1e-12`.
6. `NO_DIFFERENCE_REPRODUCED` otherwise.

Every branch is technical evidence only. Mixed facts are listed as observations even though the
first-match label is singular. A later implementation repair must be separately reviewed; a fresh
parent attempt, if justified, must use a new SHA, new result root, new task ID and a fresh remote
admission.

## 5. Exposure, cost, predictions, and stop rule

Per node:

```text
replayed_environment_episodes=327680
replayed_environment_transitions=1638400
root_blocks_reconstructed=1
target_arrays=3
new_seed/draw/independent-sample identities=0/0/0
learner rows/optimizer constructions/steps/parameter updates=0/0/0/0
fresh sampled evaluation episodes=0
```

The remote stage performs three exact roots. The local stage performs the three local roots and
three roots over the staged remote bytes. From the accepted runner's own cost law, one seed costs
`61.827 s`; the projection and machine-time cap are therefore `61.827 s` **per node invocation**.
This is a fixed two-node diagnostic, not a sweep.

DM prediction: design and FP32 target bytes will agree, while the identical-byte root solve will
differ across NumPy/LAPACK environments at a magnitude sufficient to explain at least one frozen
predicate failure. Owner prediction: `not taken (unattended)`.

Stop on failed resource admission, retained-input mismatch, nonfinite output, missing array,
shape/dtype mismatch, wall above the per-node cap, or incomplete technical publication. Such a
stop has no scientific polarity and authorizes no blind resend.

## 6. Engineering scope and non-goals

This diagnostic adds one ordinary four-array payload per node because byte equality of the
`design64` and three target arrays is the quantity being measured. It records direct array
comparisons but adds no manifest, hash chain, authority/currentness guard, retry or lease
machinery, incident tree, registry, schema framework, compatibility shim, driver sweep, or
telemetry beyond wall time and peak RSS. No other engineering-scope §4 item is needed. New
research code remains below 2,000 lines, the runner below 600 lines, orchestration below 30
percent, and focused tests below five minutes.

Do not change the parent runner's scientific meaning, tolerance, solver, targets, RNG, counts or
branches; do not train, tune, select a passing row, rerun attempt 02, infer mechanism value,
declare headroom, treat an exact solve as a tuned baseline, unlock paid acquisition or COUNT/RAW,
or make a lifecycle, priority, fusion, safety, transfer or deployment claim.

## 7. Object-tier technical selection

Options:

- **(a) Run the pinned byte/solver locus diagnostic above.**
- **(b) Relax the frozen tolerance or select passing rows.** This would rewrite observed
  scientific meaning.
- **(c) Blindly repeat the parent runner on either node.** This would not locate the reproduced
  technical boundary.

Recommendation: **(a)**.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. This is a reversible engineering selection inside the unresolved parent
object; it is not a direction- or Portfolio-tier action.
