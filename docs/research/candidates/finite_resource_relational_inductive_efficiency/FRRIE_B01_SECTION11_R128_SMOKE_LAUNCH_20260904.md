# FRRIE B01 section-11 R128 smoke launch record — 2026-09-04

Status: `RUNNING / DETACHED / SOLE RESULT-BEARING INVOCATION`

Object: `FRRIE-B01-SECTION11-R128-SMOKE-20260904`

Science card:
`FRRIE_B01_SECTION11_R128_SMOKE_SCIENCE_CARD_20260904.md`

## Direct launch facts

- launch SHA: `85b96dc80bb0b75ab605fa0cf606bcbb37649152`;
- branch: `codex/frrie/dirty-intake-20260904`;
- process start: `2026-09-04T10:22:34.6349922Z`;
- detached Windows PID at dispatch: `15512`;
- run root:
  `C:\Projects\HMASD-worktrees\codex-frrie-dirty-intake-20260904\temp\directions\finite_resource_relational_inductive_efficiency\exp\frrie_b01_r128_root001_85b96dc8_20260904T032143`;
- seed packet:
  `C:\Projects\HMASD-worktrees\codex-frrie-dirty-intake-20260904\temp\directions\finite_resource_relational_inductive_efficiency\exp\frrie_b01_five_root_packet_20260904T032143.json`;
- stdout and stderr are sibling files with suffixes `_stdout.log` and `_stderr.log` on the
  run-root tag.

The runner created the output root only after it had read the launch SHA, so this later launch-
record commit does not alter the recorded execution revision.

## Resource admission

The exact `admit-memory` invocation completed immediately before process creation. Its receipt is
the sibling file
`frrie_b01_r128_root001_85b96dc8_20260904T032143_admission.json`.

- assessed: `2026-09-04T10:22:34.542675Z`;
- measurement source: `GlobalMemoryStatusEx`;
- available physical bytes: `5,235,474,432`;
- effective available bytes: `5,235,474,432`;
- required floor: `4,294,967,296` bytes;
- physical/effective/pass fields: `true / true / true`.

The seed packet did not exist before admission and was created by this invocation after admission.

## Exact invocation

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
scripts/run_frrie_b01_r128_smoke.py
--output-root C:/Projects/HMASD-worktrees/codex-frrie-dirty-intake-20260904/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_r128_root001_85b96dc8_20260904T032143
--seed-packet C:/Projects/HMASD-worktrees/codex-frrie-dirty-intake-20260904/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_five_root_packet_20260904T032143.json
--admission-receipt C:/Projects/HMASD-worktrees/codex-frrie-dirty-intake-20260904/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_r128_root001_85b96dc8_20260904T032143_admission.json
--seed-label FRRIE-B01-FRESH-BLOCK-001
```

The process was started with a hidden window and stdout/stderr redirection. It was observed alive
after dispatch with an empty stderr log. No second result-bearing invocation has been started.

## Declared execution surface and cost

The new execution surface at the launch SHA is exactly:

- `experiments/candidates/finite_resource_relational_inductive_efficiency/b01/r128_smoke.py`;
- `scripts/run_frrie_b01_r128_smoke.py`;
- `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/b01/test_r128_smoke.py`.

The frozen projection is `655,360` environment slots per learned arm, about 12.9 minutes of
native-slot work per arm at the retained collector rate, plus one shared `6,144`-slot uniform
reference. The cap remains four wall-hours per learned arm and eight wall-hours for the invocation.

This record establishes only admission and launch identity. It contains no outcome and creates no
scientific branch. The owner-dirty main-checkout supervisor/checkpoint bundle is outside this
launch surface and remains untouched.
