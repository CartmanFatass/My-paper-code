# G31 return-to-go direction-balanced formal result

```text
status=COMPLETE_OPERATIONALLY_VALID
formal=true
iteration=21
iteration_consumed=true
source_commit=03bedada8b4aaa83d39d5b25e80d14505fa01b22
run=logs/formal_return_to_go_g31_cpu_20260724_03bedad_r1
branch=USABLE_RETURN_TO_GO_DIRECTION_BALANCED_G31
iterations_remaining=6
```

## Evidence closure

The registered CPU one-thread train/evaluate/analyze pipeline completed with
six source/replicate rows, twelve zero/final checkpoints and twenty-one exact
evaluation cells. Source, formal identity, token, phase exposure, fresh seeds,
configuration and runtime all close. Replay, direction composition and
terminal return-to-go errors are zero; the maximum finite RTG target is
`34.441227`. Lifecycle, ownership, inactive rows, exact-zero residual and
single-step Adam invariants pass. PM re-ran the frozen artifact validator with
no errors and independently obtained the same first-match branch from
`select_result_branch`.

## Registered result

- G17 IID utility CI95: `[0.957394, 0.960560, 0.965295]`.
- G17 held-out utility CI95: `[0.951364, 0.956601, 0.961905]`.
- G17 gain CI95: `[0.380301, 0.488652, 0.604038]`; minimum episode
  `0.925097`; minimum effort/mix correlations `0.985297/0.994716`; maximum
  MAEs `0.019032/0.011788`.
- G18 utility CI95: `[0.977762, 0.983669, 0.986834]`.
- G18 gain CI95: `[0.161437, 0.237388, 0.276850]`.
- G18 spike utility CI95: `[0.959689, 0.968430, 0.985076]`.
- G18 rotating effort share CI95: `[0.962239, 0.970913, 0.986846]`; minimum
  replicate utility `0.977605`.

All first-match gates pass, so the result is
`USABLE_RETURN_TO_GO_DIRECTION_BALANCED_G31`.

## Scientific disposition

For the registered paired toy family, detached realized future-tail credit plus
G30's equal global unit-gradient directions is a usable unified algorithm for
runtime-variable membership with both immediate and policy-dependent delayed
service consequences. The fresh-seed result rejects the narrower explanation
that the bounded G31 spike access was a single-seed accident and shows that
G30's remaining failure was separable through target estimation without an
environment-specific event flag.

This does not establish individual causal attribution of later team reward,
arbitrary stochastic-horizon robustness, UAV physical transport or superiority
on every dynamic-agent task. G31 is now eligible for exactly one proof-sized
UAV promotion package; no toy rerun, threshold change or further G31 rescue is
admissible.
