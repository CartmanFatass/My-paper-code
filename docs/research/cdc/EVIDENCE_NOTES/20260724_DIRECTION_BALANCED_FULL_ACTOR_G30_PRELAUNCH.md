# Direction-balanced full actor G30 prelaunch

```text
status=FORMAL_PRELAUNCH_READY
formal=false
iteration_consumed=false
source_commit=ef8c106ce64dec19fc0b3e03e89e830c04bc3b85
exercise_branch=NONFORMAL_DIRECTION_BALANCED_FORMAL_PATH_EXERCISE_COMPLETE
formal_required_rejection=true
next_boundary=DIRECTION_BALANCED_FULL_ACTOR_G30_FORMAL_ITERATION_20
```

The registered CPU one-thread formal-path exercise completed
`train -> evaluate -> analyze` from a fresh run root. It produced both zero and
final checkpoints for G17 and G18, two training rows and the exact seven-cell
evaluation inventory. Runtime, source, seed, phase-count and checkpoint
identities close exactly.

Both source rows are finite, lifecycle-valid and ownership-valid. Replay and
composition identity errors are exact zero; minimum immediate-direction dots
are `0.23256` and `0.03779`; actor optimizer steps advance exactly once; the
residual remains exact zero. The analyzer reports no operational errors and the
formal-required path rejects these nonformal artifacts.

This exercise is operational evidence only. It does not estimate G17/G18
utility, consume iteration 20 or support a UAV claim. The already-frozen formal
token, counts, fresh seeds, thresholds and first-match branches may now be used
unchanged for the one authorized formal run.
