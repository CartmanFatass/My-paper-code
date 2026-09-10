# B08 P73 fixed-768 source technical acceptance

The new 35-line B08 runner changes only B07 object/card/master labels and fixes
Config(seed=args.seed, train_episodes=768). It preserves common start, CPU/threads,
normalization, width133, extra-init master law (840100012), other defaults and
exit behavior. Shared study.py changes only the three cost-projection strings:
train*horizon, (train//2)*4 Adam, eval*horizon (twice for MLP+H), train//2 merges
of 2*horizon rows. The default512 strings remain exactly unchanged. Actual loops,
Config defaults, optimizers, RNG, environment, architecture and value moments are
untouched. No shared exposure/scheduling implementation gap was found or changed.

Owned code is scripts/run_vspc1_native_hold_value_b08.py and the three reporting
lines in experiments/candidates/vsp_c1/native_hold_value_b01/study.py. Tests are
under tests/experiments/candidates/vsp_c1/native_hold_value_b08/. Scope section 4
additions: none, as card sections 2,5 and intake section 3 request. Production
additions are 38 lines /3 removed, including the 35-line runner; within 2000/600
limits. Protected scientific and historical runner/test paths have no diff against
dd27e6fed955385da55637290895d27992ecf34e. CM inspected the complete production diff.

## Focused checks

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/b08_p73_binding tests/experiments/candidates/vsp_c1/native_hold_value_b08
```

PASS: 15 tests, 3.22s pytest /4.3296453999355435s complete process, exit 0.
One existing unknown cache_dir warning accompanies disabled cacheprovider; no
failure. The suite ran once, within the 300s budget. Retained process evidence:
temp/directions/vsp_c1/engineering/native_hold_value_b08_p73/focused_result.json.
The exact resolved owned scratch was checked under this checkout's temp; its
24 entries were removed using file and empty-directory operations. Scratch
existence is false; no other invocation was touched.

Twelve thin binding/metadata cases verify fixed8401/B08/card/768 Config and caps,
normalization/width/extra seed, exit mapping, early invalid-key/fixture/method/
width/budget-option rejection and both generic checkpoint identities. One full
768 pure-stub schedule verifies 768 training episodes per arm, 384 rollouts/
moment merges and 1536 Adam each, 96 final evaluations, 417792 total steps,
393216 train/24576 eval, 1632 rows, two constructors and final-only global order.
It verifies exact reset/action-generator domains and private RNG object pairing,
fresh independent moments, 196608 targets per arm, normalized loss labels,
frozen final/evaluation/H state, architecture/count/source metadata and actual
summary/checkpoint readback. Every model, environment, optimizer and update is
fake; pure tensor returns/moment calculations are used without any real model
construction/forward, learner/native episode or evaluation.

The full stub also checks exact768 cost strings. Two default-cost cases stop
intentionally at the templates boundary before scientific state and verify
actual default512 report strings byte-for-byte, with and without normalization.
These are deliberate test-only incomplete summaries with zero steps/Adam, not
failed scientific attempts. Accepted architecture/RNG/gradient/PPO/native/H/
normalization/deadline review remains applicable; no shared scientific schedule
change occurred requiring a new independent review. P69's historical first
unmeasured enclosing-test-wall qualification remains unchanged.

## Cost, publication and next boundary

Per-arm cost projection reuses card section 5 and its preparation JSON: uniform
1.5x scaling of prior largest complete wall gives610.995s; conservative complete
arm proxies312.7592679495/315.6140233080s are below1800s, whole below3600s. Actual
768 runtime, aggregate CPU and isolated component overhead are unmeasured.
These proxies inform planning and grant no extra run. Post-learner coverage now
includes the full768 stub's final-only publication/moments/readback; unchanged
native B05-B07 publication evidence remains reusable. Later actual B08 collection
must establish its native primary/H/adverse/count/checkpoint/resource facts.

Return pushed source to DM for acceptance and exact execution binding within
P73's already allocated route. No B08 scientific staging, admission, submission
or exposure has occurred. DM owns the card/intake/binding edits next. No
intermediate Root allocation is requested. All new text is strict UTF-8.
