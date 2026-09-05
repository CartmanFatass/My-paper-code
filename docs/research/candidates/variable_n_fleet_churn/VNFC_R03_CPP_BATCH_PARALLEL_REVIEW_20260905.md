# VNFC R03 — owner question on C++ and parallel feasibility

2026-09-05. Owner asks: “这类实测投影为何远超合理时间 是否符合cpp加速和批处理并行的要求”.
This source inspection adds engineering facts to the pending cost-return Convergence question.
No new timing, calibration, target-world computation, source repair or launch occurred.

## What the measured path actually does

`experiments/candidates/variable_n_fleet_churn_causal_headroom/native_backend.py`
builds a shared C++20 library with `-O2 -fno-fast-math -ffp-contract=off`.
`calibrate_native` makes one ctypes call to `vnfc_causal_calibrate` for the entire native
calibration. The six epoch calls and tick/prehistory loops execute in native C++, not through
one Python crossing per candidate. This establishes coarse native-call batching only.

`native/calibration.cpp::calibrate` executes six serial `grun_bcrh` calls on synthetic
maximum-support seven-agent inputs. Each full call contains1,961 candidate rows and checks
scorer/checker, independent enumeration and every candidate record. The max observed call
was0.449180563s; the projection uses its per-row0.00022905689087200407s at all upper rows.

`experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_general.hpp::grun_bcrh`
enumerates/sorts scorer commands, independently enumerates checker commands, computes common
weights once per call, loops serially over candidate scores, selects the best, executes the
independent checker, then compares and copies every candidate record. Existing per-call common
weight reuse is real. No parallel candidate dispatch is present in the inspected wrapper/body.
This inspection does not establish thread safety, SIMD utilization or a measured optimal kernel.

## Why the projection is large

The corrected full-terminal upper count is94,128 world/epoch/action continuations,376,688
later/baseline/selected BCRH calls, and738,685,168 internal scored candidate rows. The
factor2 planning multiplier yields338,401.855830688s for complete BCRH work, about97.3% of
the347,623.18427552027s total. Exact solver extrapolation adds9,152.017350242992s.
Native transitions outside BCRH contribute only0.5022888615s. Thus moving the wrapper into C++
alone does not remove the dominant nested full-comparator work, which is already C++.

This combines maximum synthetic unit cost and worst support/count bounds. It is neither an
observed96-hour target run nor a lower bound on every semantics-preserving implementation.
Actual state-dependent support, reusable computations, candidate-level work and full-pipeline
costs have not been measured on a complete implementation. No claimed speedup is established.

## Parallel/batch conformance and decision relevance

The original science card section10 explicitly requires one process and one computational
thread. The accepted calibration conforms to that original execution restriction, but it does
not establish compliance with a broader goal of exploiting available batch/parallel execution.
Repository permission for multiple experiment invocations is distinct from a parallel kernel
inside this frozen invocation. Full census implementation and publication remain absent.

Potential review questions are whether equivalent repeated states/work can be reused, whether
independent candidate/continuation work can be batched with deterministic indexed outputs, and
whether native parallel evaluation can preserve all exact comparator/checker and tie semantics.
These are unverified engineering possibilities, not selected implementations or promised gains.
Do not remove required independent checks, truncate actions/worlds or shorten native terminal
continuations to report a faster implementation of the unchanged object.

The next node should address the owner's performance question before treating current cost as
sufficient reason to abandon the scientific family. If it selects a bounded feasibility or
optimization step, state the actual remaining implementation/probe and execution-policy change,
keep every scientific observation, and distinguish elapsed wall time from aggregate work/CPU
time. Dividing the serial projection by a nominal core count is not an admission measurement.
Any proposed change to the original2,700s cap must be explicit; no change is applied here.
