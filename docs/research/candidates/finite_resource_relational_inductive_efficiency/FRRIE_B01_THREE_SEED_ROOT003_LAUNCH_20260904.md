# FRRIE B01 three-seed root 003 launch — 2026-09-04

Status: `DETACHED_RUNNING / RESULT_UNOBSERVED`

Object: `FRRIE-B01-THREE-SEED-SECTION11-20260904`

This is the sole launch of ordered root `FRRIE-B01-FRESH-BLOCK-003` for the three-seed rung. The
science card is `FRRIE_B01_THREE_SEED_SECTION11_SCIENCE_CARD_20260904.md`. Roots 001 and 002 were
not migrated, resumed, or repeated.

## Frozen execution placement

The card prospectively limits the ordered panel to “this fixed host.” Roots 001 and 002 established
that host as the local Windows/MSVC/CPU execution surface. The active remote node is Ubuntu and
builds the native seam with a different C++ toolchain; technical source support for that node does
not make the already-started fixed-host scientific panel portable. Root 003 therefore uses the
REMOTE_FIRST policy's host-pinned local exception. Moving it after earlier output would change
frozen scientific/numerical meaning.

- execution node: `local_windows`;
- route: `CARD_PINNED_LOCAL_FIXED_HOST`;
- launch SHA: `5d0255dcd2aa221378d457c9519312996b0a3f45` (pushed);
- branch: `codex/frrie/dirty-intake-20260904`;
- runner: `scripts/run_frrie_b01_three_seed.py`;
- helper:
  `experiments/candidates/finite_resource_relational_inductive_efficiency/b01/three_seed.py`;
- root label: `FRRIE-B01-FRESH-BLOCK-003`;
- literal root hex:
  `5aca87f3fd99d00191e73330d611092a30cbc4ba73ca0a032c12be990f00d428`.

The declared implementation blobs at launch were helper
`5a2dcf2eee7b4ed81ab34c537807ea5d51121316`, runner
`dcc6db68cba72c6cb76cefee2ea9bc66de9108e4`, and focused test
`cecaa34123a815ffcf56c62f662cfd0af600e6d6`. The owned worktree and pushed upstream were both at
the launch SHA immediately before admission. No root-003 output root or duplicate process existed.

## Frozen input

The ignored five-root packet is the same prospective artifact used by roots 001 and 002:

- path:
  `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_five_root_packet_20260904T032143.json`;
- size: `651` bytes;
- SHA-256: `3b661df5cacb15aebae8d2bcc0ee8b68d7c769da2ef478881cf8408481e62ce9`.

## Fresh resource admission

- receipt:
  `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root003_5d0255dc_20260904T162246Z_admission.json`;
- receipt size / SHA-256: `511` bytes /
  `25a8af2523985d41bb8669f5439139c0bbb76fe3b75a8f357e632e35e262c2a4`;
- assessed: `2026-09-04T16:22:46.285388Z`;
- measurement: `GlobalMemoryStatusEx`;
- physical available: `15,509,004,288` bytes;
- effective available: `15,509,004,288` bytes;
- required floor: `4,294,967,296` bytes;
- physical/effective/combined result: passed.

The admission completed immediately before the result-bearing process was created. This
invocation created no seed root, model, optimizer, checkpoint, or result root before admission.

## Detached invocation

- PID at acceptance: `25984`;
- process start: `2026-09-04T16:22:46.3392282Z`;
- output root:
  `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root003_5d0255dc_20260904T162246Z`;
- stdout:
  `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root003_5d0255dc_20260904T162246Z.stdout.log`;
- stderr:
  `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root003_5d0255dc_20260904T162246Z.stderr.log`.

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_frrie_b01_three_seed.py --output-root C:/Projects/HMASD-worktrees/codex-frrie-dirty-intake-20260904/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root003_5d0255dc_20260904T162246Z --seed-packet C:/Projects/HMASD-worktrees/codex-frrie-dirty-intake-20260904/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_five_root_packet_20260904T032143.json --admission-receipt C:/Projects/HMASD-worktrees/codex-frrie-dirty-intake-20260904/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root003_5d0255dc_20260904T162246Z_admission.json --seed-label FRRIE-B01-FRESH-BLOCK-003
```

The process remained live on its first post-start observation; stdout and stderr were both empty.
The frozen direct projection remains about `4,092.42 s` per learned arm and `8,194.25 s` for the
invocation, within four attributed wall-hours per arm and eight wall-hours total. Process
acceptance and later exit are engineering facts only. They establish no projection contact,
comparator competence, return difference, reassociation effect, seed validity, or three-seed
branch.
