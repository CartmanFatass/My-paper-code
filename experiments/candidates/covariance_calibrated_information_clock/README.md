# CCIC-B1 revision-06 implementation

This directory is the self-contained engineering realization of
`CCIC-B1-SCIENCE-20260813-06`. It preserves the ideal-real packet model: one
mathematical real symbol plus 64 metadata bits per row. It makes no finite-word
Gaussian-channel claim. The deployed arms quotient immutable
`(origin_id,capture_tick)` lineage, use the same shared actor and legal action
support, and never call the centralized numerical reference.

The package is intentionally import-safe: imports perform no random draw,
training, evaluation, endpoint calculation, or filesystem mutation. The runner
first writes a machine-readable preactivity certificate into a fresh output
root. It stops before training unless every static, symbolic, numerical-reference,
resource, collision, stream, support, and forbidden-input check passes.

Production is not authorized by this README. When the Code Project Manager
later obtains production authority and the current exclusive CPU owner has
released the host, the exact command is:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.covariance_calibrated_information_clock.runner --output-root temp/results/ccic_b1_revision06 --max-workers 8
```

The output root must not already exist. The full command requires all 32 fixed
seed blocks and 256 episodes per evaluation cell; there is no quick-mode,
seed-substitution, adaptive-stop, or hyperparameter-search option. A failed or
missing seed is retained as a technical failure and cannot be replaced.

Static contract scaffolding lives under `tests/`. Those checks inspect source
and the frozen machine contract only; they must not be confused with the
preactivity numerical certificate, training, evaluation, or scientific
evidence.

`RI-STRONG-v2` is the functional, intentionally advantaged 83-scalar
comparator. Its shared `6 -> 9 -> 2` row MLP consumes
`(z,o,s,log M,t/30,k/5)`, applies `h=r+tanh(r)` in both training and execution,
and mean-pools in ascending unique-key order. The certificate blocks activity
unless observed symbolic replay agrees with the literal formulas
`W_CCIC=14N+392M+8`, `W_RI_v2=14N+357M+7`, `P_CCIC=22+6M`, and
`P_RI_v2=24+6M` in all 27 cells, with every ratio at most `1.10` and aggregate
`passed=true`.

The bounded implementation uses `O(N)` time and `O(N)` temporary state for
each agent's lineage quotient and fusion. The science-frozen complete
all-gather still creates `O(N^2)` system traffic. B1 fixes `N<=8`; this package
makes no scalable, arbitrary-`N`, or deployment claim. It performs no
hypothetical trajectory search or nested rollout/replanning. The prospective
resource ceiling is 90 wall minutes, 4 GiB peak RSS, eight CPU threads,
240,000 optimizer updates, and 60 million primitive ticks; the eight rollout
arms account for at most 53,084,160 evaluation ticks and the shared snapshot
bank for at most 294,912 one-tick draws.

Thread-library environment variables are bound explicitly to one before NumPy
loads. Each complete seed is retained atomically in fixed block order using a
temporary file, file `fsync`, atomic replacement, and directory `fsync`.
Partial blocks are not retained as complete seeds and never enter inference.
Retained JSON rejects NaN and infinity rather than emitting nonstandard JSON.
