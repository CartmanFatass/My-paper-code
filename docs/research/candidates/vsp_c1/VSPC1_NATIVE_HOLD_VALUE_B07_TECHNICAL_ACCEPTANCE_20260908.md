# B07 P72 fixed-binding technical acceptance

The new 35-line runner is exactly B06 with B06 -> B07 and 8302 -> 8303 text
substitutions. Config defaults, whole-start clock, CPU/threads, normalization,
width133, publication and exit behavior remain unchanged. The existing master
law gives extra initialization 830300012. Shared scientific implementation and
historical runner/tests have no diff against accepted input
3e743b2cdd5913a1f506ab0e8d4a6ea11489fcb3.

Owned production path: scripts/run_vspc1_native_hold_value_b07.py. Pure-data/stub
tests: tests/experiments/candidates/vsp_c1/native_hold_value_b07/. Scope section 4
additions: none. Card sections 2,5 and intake section 3 request this fixed binding.
Production additions are 35 lines, under 2000-source/600-runner limits.

Focused invocation:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/b07_p72_binding tests/experiments/candidates/vsp_c1/native_hold_value_b07
```

PASS: 11 checks, 5.04s pytest /6.667623999994248s complete process, exit 0.
One existing unknown cache_dir warning accompanies disabled cacheprovider; no
test failure. Tests stub run_pair/thread setters and check pure generic
checkpoint metadata. They cover fixed B07/card/master/output/start, Config and
caps, normalization/width/extra seed, complete/limited/incomplete exit mapping,
early invalid key/fixture/width/method rejection, and both checkpoint identities
with actual architecture/count metadata. No model constructor, optimizer,
forward, native episode, evaluation or full pipeline was invoked.

The tests ran once. Results are retained at
temp/directions/vsp_c1/engineering/native_hold_value_b07_p72/focused_result.json.
The resolved exact invocation scratch was verified under this checkout's temp;
only its empty directories were deleted nonrecursively. Scratch existence is
false after cleanup. No other invocation was touched.

Accepted architecture/RNG/gradient/full-schedule/publication, normalization/PPO,
native/H/deadline checks and independent review are reused for unchanged source.
No repeated full schedule, model probe or smoke was warranted. P69's unmeasured
first enclosing-test-wall qualification is preserved. B07 used 6.67s of its
300s focused-check budget; source tests supply no native B07 outcome or timing.

Per-arm cost projection: card section 5 reuses identical work law and B06
conservative 208.5062/210.4093s complete-arm bounds, against 1800s per arm;
prior pair walls 315.20/407.33s inform the 3600s complete-pair plan. These are
planning references, not new measurements. Aggregate CPU and isolated overhead
remain unknown. Post-learner coverage reuses accepted B05/B06 complete native
publication and current pure identity checks. Actual B07 checkpoints, moments,
primary/H and terminal whole resources will be checked in allocated collection.

Return committed source for DM acceptance and exact execution binding within
P72's already allocated route. No B07 staging/admission/submission/scientific
exposure has occurred. DM owns card/intake/binding edits next; no intermediate
Root allocation is requested. All source/check/record text is strict UTF-8.
