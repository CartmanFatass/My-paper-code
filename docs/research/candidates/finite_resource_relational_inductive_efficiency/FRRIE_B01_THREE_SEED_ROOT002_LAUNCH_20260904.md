# FRRIE B01 three-seed root 002 launch — 2026-09-04

Status: `DETACHED_RUNNING / RESULT_UNOBSERVED`

Object: `FRRIE-B01-THREE-SEED-SECTION11-20260904`

This is the sole launch of ordered root `FRRIE-B01-FRESH-BLOCK-002` for the three-seed rung. The
science card is `FRRIE_B01_THREE_SEED_SECTION11_SCIENCE_CARD_20260904.md`. Root 001 was not
migrated, resumed, or repeated.

## Frozen execution placement

The card prospectively limits the ordered panel to “this fixed host.” Root 001 established that
host as the local Windows/MSVC/CPU execution surface. The active remote node is Ubuntu and builds
the native seam with a different C++ toolchain; technical source support for that node does not
make the already-started fixed-host scientific panel portable. Root 002 therefore uses the
REMOTE_FIRST policy's host-pinned local exception. Moving it after root-001 output would change
frozen scientific/numerical meaning.

- execution node: `local_windows`;
- route: `CARD_PINNED_LOCAL_FIXED_HOST`;
- launch SHA: `8fee334c01c7d14318134f2e3d4bd85fd445ad5c` (pushed);
- branch: `codex/frrie/dirty-intake-20260904`;
- runner: `scripts/run_frrie_b01_three_seed.py`;
- helper:
  `experiments/candidates/finite_resource_relational_inductive_efficiency/b01/three_seed.py`;
- root label: `FRRIE-B01-FRESH-BLOCK-002`;
- literal root hex:
  `4eb956af014e3c1e89b38e67e6bd46d53b7b9f41ac2698d3187cdee3b11c8e10`.

The declared implementation blobs at launch were helper
`5a2dcf2eee7b4ed81ab34c537807ea5d51121316`, runner
`dcc6db68cba72c6cb76cefee2ea9bc66de9108e4`, and focused test
`cecaa34123a815ffcf56c62f662cfd0af600e6d6`. The owned worktree and pushed upstream were both at
the launch SHA immediately before admission. No root-002 output root or duplicate process existed.

## Frozen input

The ignored five-root packet is the same prospective artifact used by root 001:

- path:
  `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_five_root_packet_20260904T032143.json`;
- size: `651` bytes;
- SHA-256: `3b661df5cacb15aebae8d2bcc0ee8b68d7c769da2ef478881cf8408481e62ce9`.

## Fresh resource admission

- receipt:
  `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root002_8fee334c_20260904T141201Z_admission.json`;
- receipt size / SHA-256: `511` bytes /
  `95411d5e878600be222fe2949c893c9aabcc9f1f76f189868e983ad4bb65c175`;
- assessed: `2026-09-04T14:12:01.766917Z`;
- measurement: `GlobalMemoryStatusEx`;
- physical available: `12,374,208,512` bytes;
- effective available: `12,374,208,512` bytes;
- required floor: `4,294,967,296` bytes;
- physical/effective/combined result: passed.

The admission completed immediately before the result-bearing process was created. This
invocation created no seed root, model, optimizer, checkpoint, or result root before admission.

## Detached invocation

- PID at acceptance: `20832`;
- process start: `2026-09-04T14:12:01.8060976Z`;
- output root:
  `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root002_8fee334c_20260904T141201Z`;
- stdout:
  `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root002_8fee334c_20260904T141201Z.stdout.log`;
- stderr:
  `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root002_8fee334c_20260904T141201Z.stderr.log`.

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_frrie_b01_three_seed.py --output-root C:/Projects/HMASD-worktrees/codex-frrie-dirty-intake-20260904/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root002_8fee334c_20260904T141201Z --seed-packet C:/Projects/HMASD-worktrees/codex-frrie-dirty-intake-20260904/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_five_root_packet_20260904T032143.json --admission-receipt C:/Projects/HMASD-worktrees/codex-frrie-dirty-intake-20260904/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root002_8fee334c_20260904T141201Z_admission.json --seed-label FRRIE-B01-FRESH-BLOCK-002
```

The process remained live on its first post-start observation; stdout and stderr were both empty.
The frozen direct projection remains about `4,092.42 s` per learned arm and `8,194.25 s` for the
invocation, within four attributed wall-hours per arm and eight wall-hours total. Process
acceptance and later exit are engineering facts only. They establish no projection contact,
comparator competence, return difference, reassociation effect, seed validity, or three-seed
branch.
