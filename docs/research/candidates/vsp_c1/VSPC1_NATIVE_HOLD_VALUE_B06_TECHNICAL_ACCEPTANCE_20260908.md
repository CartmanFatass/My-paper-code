# B06 P71 fixed-binding source acceptance evidence

The new 35-line runner is exactly B05 with B05 -> B06 and 8301 -> 8302 text
substitutions. It preserves Config defaults, common start/exit semantics,
CPU/one-thread settings, normalization and width133; extra initialization is
830200012 from the existing master law. Object/card labels are B06. Shared
scientific implementation and historical runners/tests have no diff against
accepted input 4fa2829a347032ec80f375f95ca8ebec4ad723dd.

Owned production path: scripts/run_vspc1_native_hold_value_b06.py. Tests:
tests/experiments/candidates/vsp_c1/native_hold_value_b06/{__init__,test_binding}.py.
Scope section 4 additions: none. The card sections 2,5 and intake section 3 ask
for this minimal fixed object/key binding. Production additions are 35 lines,
under both 2000-source and 600-runner limits. No extra scientific mechanism,
telemetry, framework or guard was introduced.

Focused check command:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/b06_p71_binding tests/experiments/candidates/vsp_c1/native_hold_value_b06
```

PASS: 11 tests, 2.29s pytest wall; complete enclosing process 3.39652800001204s,
exit 0. One existing pytest configuration warning reports unknown cache_dir
while cacheprovider is disabled; no test failed. Tests stub run_pair and thread
setters, and inspect pure checkpoint identity data. They verify the exact
Config/master/output/start/object/card/normalization/width/extra-seed binding,
COMPLETE/PRIMARY_COMPLETE_WITH_LIMITS/incomplete exit mapping, rejection of
invalid keys and fixture/width/method options before the scientific boundary,
and both arms' generic checkpoint source/object/configuration/architecture/count
identity. No model constructor, optimizer, forward, native episode or evaluation
was executed by these checks. Actual native performance/publication remains
unobserved for B06.

The original combined test/recursive-cleanup command was rejected before
execution. The focused tests then ran once. Results were retained at
temp/directions/vsp_c1/engineering/native_hold_value_b06_p71/focused_result.json.
The exact resolved invocation scratch path was checked under this checkout's
temp tree; only its empty directories were removed without recursive deletion.
Post-cleanup existence is false. No other scratch was touched.

Reuse B05's accepted architecture/RNG/gradient/full-schedule/publication review
and normalization/PPO/native/H/deadline checks: those source boundaries are
unchanged. No repeat suite, review or native smoke was warranted by this binding.
P69's unmeasured first enclosing-test-wall qualification remains unchanged.
This new focused process used 3.40s of the B06 300s check budget.

Per-arm cost projection: card section 5 reuses same-method B05 conservative
167.9571218310/155.6930584460s complete-arm bounds and 315.20s pair wall against
1800s per arm/3600s whole pair. The same runner work law applies; this is planning
evidence, not a B06 measurement. Aggregate CPU and isolated width/normalization
cost remain unknown. Post-learner coverage reuses the accepted B05 stub checks
and complete native P70 publication/collection; actual B06 checkpoint, primary,
H, resources and terminal receipts will be checked in the allocated collection.

Return this committed source for DM acceptance and exact execution binding.
No B06 staging, admission, accepted submission or scientific exposure has yet
occurred. The one-pair route remains allocated within P71, pending the requested
DM source-acceptance boundary. DM owns the binding/card/intake edits next.
