# Continuous-roster history-proxy coherence G37 prelaunch evidence

```text
algorithm=CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37
source_id=CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_P0
source_commit=87f4dfbe56b36f31d34f134a3c350bd766fae8d7
run=logs/nonformal_continuous_roster_history_proxy_coherence_g37_cpu_20260726_87f4dfb_r1
formal=false
backend=cpu
torch=2.7.0+cpu
torch_threads=1
status=COMPLETE
operational_valid=true
operational_errors=[]
branch=NONFORMAL_CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_COMPLETE
formal_compute_started=false
```

## PM implementation acceptance

The accepted implementation reuses the byte-identical G36 donor bank and draws
four coordinate columns with independent snapshot-selection and row-permutation
streams. Actor fields 0:6, inactive zeros, critic, source, reward, lifecycle,
checkpoints and action streams remain unchanged. The exact formal G36 package is
validated and read, not rerun. Proof-sized evidence is seven focused G37 tests
and an 18-test G36/G37 aggregate, all passing on the registered CPU interpreter.

The first dispatch terminated before source reading because the executed command
omitted the source-commit argument and created no artifacts. A corrected
pre-repair exercise evaluated 4,608 transitions but was rejected because the
validator compared an eight-episode action-noise digest with the complete
128-episode G36 digest. The accepted repair recomputes the exact G35 action
stream over the current episode subset and retains stored G36 digest equality
for the formal 128-episode inventory. Neither discarded attempt is scientific
evidence or consumes an iteration.

## Bounded exercise

The registered Experiment Operator ran one complete foreground exercise from
the repaired source commit. It used one replicate, capacities 6/8/12, four
factorized cells per capacity, eight episodes per cell, 4,608 real transitions,
zero training transitions, zero optimizer steps and 250 bootstrap resamples.
`H=48`, `K_search=0`, hypothetical trajectories and transitions are zero, and
nested rollout and replanning are false.

```text
evaluation_wall_time_seconds=49.82453130000067
analysis_wall_time_seconds=67.61068489999889
nonformal_total_seconds=117.43521619999956
formal_projection_seconds=6370.006122999985
formal_wall_clock_cap_seconds=28800.0
formal_projection_executable=true
evaluation_manifest_sha256=bdc1df5512cf532c7a2ea39acac9627fbf3461c48a77dfb345d16e4d19572f5c
analysis_result_sha256=bdc3bb5198a1e197ab7bed39e4c7eb406fbdde3606408d5ef61dc2ec0a66dfd4
```

PM independently reran the artifact validator and obtained an empty error list.
PM regenerated the one-replicate whole-episode bootstrap plan, all absolute and
joint-minus-factorized quantities and the nonformal branch; the complete metrics
object matches the stored analysis exactly.

The preflight is not scientific evidence. Its observed primary
joint-minus-factorized interval is
`[0.0054416, 0.0065092, 0.0077670]`; all factorized access gates pass and the
largest observed conclusion-bearing UCB remains below the frozen 0.05 margin.
Those values only demonstrate executable code paths and cannot predict or
replace the required formal three-replicate result.

Formal execution remains blocked until the exact pushed implementation and
critical-point index receive `AUDIT_DISPOSITION=ALIGNED` from the single G37
code-science alignment audit. Any formal run must then bind this exact repaired
source commit, both preflight artifact digests and the dedicated G37 token.
