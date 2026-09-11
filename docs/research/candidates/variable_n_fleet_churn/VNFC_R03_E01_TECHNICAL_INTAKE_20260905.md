# VNFC E01 technical intake and Root audit

Status: `E01_BLOCKED_WALL_CAP`. The bounded assessment completed; its full-work
cost projection fails the frozen continuation criterion. Stop this E01 investment
and return the cost gap to the existing Convergence node. This is not a scientific
negative, headroom result, direction PARK, or permission to run the full census.

## Source and execution

Source: `60d21ad7d2aab5dcb6e3bcaa1233ac763c8d2df0`.
Root compared all six changed source/test files against integrated main and found
identical Git blob bytes. Source acceptance and independent review are recorded in
`VNFC_R03_E01_SOURCE_ACCEPTANCE_20260905.md`; the fixture and stop rule remain in
`VNFC_R03_EXACT_BATCH_FEASIBILITY_E01_TECHNICAL_TASK_20260905.md`.

Node: `wsl_4070`. Exact detached worktree:
`/home/wu/hmasd-worktrees/vnfc-e01-60d21ad7d`.
Smoke task: `vnfc_e01_smoke_60d21ad7d_20260905_01`, recorded exit 0.
Formal task: `vnfc_e01_assessment_60d21ad7d_20260905_01`, exit 1.
Remote result root: `temp/directions/variable_n_fleet_churn/exp/e01_20260905_01`
under that worktree. Local collected evidence is in the corresponding
`e01_20260905_01_remote_fetch` directory. No new run was performed by this audit.

## Observed readings and interpretation

| Reading | Value |
| --- | --- |
| Preflight available physical/effective memory | 15,422,754,816 bytes each; both 4 GiB floors pass |
| Preflight timestamp | 2026-09-05T21:43:40.431454Z |
| Outer whole-invocation wall | 28.11 seconds |
| Outer user + system CPU | 37.51 + 0.42 = 37.93 seconds |
| Inner wall before summary | 28.087821977 seconds |
| Inner aggregate CPU before summary | 37.924671 seconds |
| Main / largest-child peak RSS | 326,508,544 / 292,691,968 bytes; separate peaks, not a concurrent sum |
| Full projected wall | 123,765.49970804117 seconds versus 2,700-second cap |
| Full projected CPU work | 414,878.862878936 seconds; no full-census CPU budget allocated |
| Projection status | BLOCKED_WALL_CAP |

The runner deliberately returns 1 when projected wall is not below 2700 seconds.
The output does not indicate timeout or native-crash failure. Actual assessment
wall/CPU pass 60/300; that does not make the full-work projection affordable.
Root independently recomputed 60 + 2 * sum(wall terms), and CPU fixed setup +
2 * sum(CPU terms), exactly matching the saved projection.

Reported coverage: 54 direct calls per implementation, 24 combined trajectory
calls, 24 prehistory decisions, 480 post-loss ticks, all full-record and four-map
comparisons equal, zero target worlds, RNG draws, training transitions, updates,
models and checkpoints. The saved records, trajectories, maps and summary exist.
Source comparisons execute before the successful coverage summary; these flags
are not evidence of testing every possible native input.

`distinct_native_deviation=false`: the predetermined alternative command did not
produce two distinct endpoint pairs. The pre-measurement fixture freeze explicitly
allows coincidence and requires reporting it. Do not claim distinct native
deviation coverage; synthetic selector/tie coverage is separate evidence.
Widths 2–7 have no formal timing: their projection uses the predeclared full-eight
empirical envelope. This is an engineering estimate, not measured full-census
elapsed time or a proven runtime lower bound. The full-census projected output is
219,341,201,129 bytes and was not created by the assessment.

## Next boundary

No repeat calibration, fixture/configuration/node change, full census or scientific
polarity follows. The frozen task requires returning this exact engineering gap.
Any successor selection is separate; this intake does not select one. Preserve
the prior results, source review and all collected artifacts.
