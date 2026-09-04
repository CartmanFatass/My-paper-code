# FRRIE B01 owner-dirty Slice-B admission intake — 2026-09-04

Status: `NOT_ADMISSIBLE_AS_SUBMITTED / CARD_FROZEN / NO_RESULT`

## Purpose and ownership boundary

This intake audits, but does not adopt, the exact FRRIE bytes intentionally left dirty in
`C:/Projects/HMASD` by the owner. The audit ran from isolated worktree commit
`d39757b4b6c6111e90f8ec7025d409217b3596cb` on branch
`codex/frrie/dirty-intake-20260904`. Nothing in the main checkout was edited, staged, moved,
cleaned, copied, committed, or launched.

The audited source paths and SHA-256 values were:

| Main-checkout path | State | Lines | SHA-256 |
| --- | --- | ---: | --- |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/b01/checkpoint.py` | modified | 596 | `244af51ff9cd84d38212e9315d3c8784c52d3a0f92395e0079fd6d6cb641c50a` |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/b01/trainer.py` | modified | 2,073 | `1b1a87804d3ddf6dd0b73a16c7ccc1455304cfdd3a2dbccb4d3f98841f5edef3` |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/b01/b4_induction_pilot.py` | untracked | 1,268 | `31e0cc938d36318e139e583c570c43bbf56ecc1d80127b6deca63d57c4cef185` |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/b01/training_runner.py` | untracked | 619 | `0437ccf89ad301d612664e2eab6d10ba7c20ffc5492475d2fade3e82097f93e3` |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/b01/training_shards.py` | untracked | 904 | `46d3188909137ac04164a556aa788d674498a352c46b6fea53018d30a64580ea` |
| `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/b01/test_checkpoint.py` | modified | 523 | `060dd7be97cc8eaa75cdd1c82f16ff1f1a622ac6aea53244a46411e059835885` |
| `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/b01/test_b4_induction_pilot.py` | untracked | 417 | `077302e9a7cc6ee06f5a9e2f6bcd4de72347e3cd612b3943168b2d7922c190f7` |
| `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/b01/test_training_runner_contract.py` | untracked | 433 | `3319d3c98111614914eb497e2013a51710c7e0a3046602e43c920946fd8fb391` |
| `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/b01/test_training_shards.py` | untracked | 473 | `4365397c1b52767b8b1010f8357a47297d6ff074553861289eb8d338f925d4d7` |

The three modified code paths contain 453 added and two removed lines; the three untracked code
modules contain 2,791 physical lines. The audited code contribution is therefore at least 3,244
added physical lines excluding tests, above the 2,000-line research-attempt budget. The file named
`training_runner.py` is 619 lines, above the 600-line runner budget.

## What was checked

I compared the exact bytes with:

- `docs/research/candidates/finite_resource_relational_inductive_efficiency/DIRECTION.md`;
- the B01 Innovator decision and its action-TV and parameter-distance clarifications;
- `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`, especially §4, §5.2, and §11;
- `docs/project/ENGINEERING_SCOPE_SPEC.md` §3–§5;
- the owner-final Portfolio recast decision
  `docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`;
- `docs/research/portfolio/RESEARCH_HANDOFF_20260903.md`; and
- the actual clean and dirty Git surfaces.

The owner-final recast selects a one-seed 128-update real learner smoke, with `INTACT` evaluation at
`N={9,15}`, curves, contact, competence, wall/RSS, and the exposure line, before the unchanged
three-seed B01 rung. It explicitly demotes `launch_capable`, performance disposition, full-panel
validation, ordered-28, and full-chain telemetry from launch gates to recorded or optional fields.

## Direct observations over the dirty bytes

1. The dirty modules are a TEST/component implementation of the older full-512 Slice-B plan, not a
   128-consecutive-update result runner. `training_runner.py` describes pure exact-512 planning and
   repeatedly returns `launch_capable=false`, `result_bearing=false`, and
   `production_token=false`. `b4_induction_pilot.py` probes two transitions after selected checkpoint
   coordinate fixtures; it does not execute updates 1 through 128 as one learner history.
2. No audited file supplies an `argparse` result CLI, fixed production seed argument, launch sha,
   one `summary.json`, the R128 evaluation grid, or the R128 result rule. Therefore no command can be
   admitted as the selected B object without inventing a caller and scientific publication path.
3. The dirty trainer changes do expose a plausible per-update `update_with_direct_rows` transaction,
   cumulative work frontier, and continuation-state readback. This is component evidence only. It
   does not establish 128-update execution, evaluation, publication, or launch readiness.
4. The bundle builds multiple mechanisms prohibited by default in engineering-scope §4 without a
   current card line: multiprocessing and an active supervisor; checkpoint/resume/recovery
   orchestration; create-once writes and publication; rollback/quarantine trees; tamper matrices;
   extensive schema/receipt validation; and telemetry beyond wall time and peak RSS. The historical
   2026-09-01 engineering plan asked for much of this machinery, but evidence specification §11 and
   the 2026-09-02 owner decision supersede it as a B-launch prerequisite.
5. The direction had no §11 recast science card, prediction record, current exposure line,
   per-arm R128 cost projection, result branches, or §4 declaration before this intake. A dirty
   checkout also supplies no launch sha. These are card/implementation facts, not a negative
   scientific observation.

## Focused reproduction

Using the exact main-checkout bytes, Python
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, `PYTHONDONTWRITEBYTECODE=1`, no pytest cache,
and a `basetemp` under this isolated worktree, I ran the four changed/new focused test files while
deselecting the effectful actual B4 pilot:

```text
80 passed, 1 deselected, 1 warning in 8.77s
```

The warning is the repository's unknown pytest `cache_dir` option. An initial invocation produced
57 setup errors because pytest could not create a nested `basetemp` whose parent did not exist; the
same bytes passed after I created only that isolated parent directory. This reproduces and
classifies the first output as an audit-environment setup error, not a code failure. The main
checkout status and FRRIE source diff were unchanged afterward.

The passing tests support the local component contracts they exercise. They do not support a
claim that the actual B4 pilot, 128 consecutive updates, evaluation, or a scientific result ran.

## Bounded reading

The owner-dirty byte set is outcome-blind WIP with useful component evidence, but it is neither
meaning-complete for the owner-selected R128 rung nor technically launchable. This is not a
scientific negative, does not consume any object, and does not justify changing treatment,
comparator, seed law, budget, or direction lifecycle.

The smallest safe current contract is now frozen in
`FRRIE_B01_SECTION11_R128_SMOKE_SCIENCE_CARD_20260904.md`. It requires a fresh, small runner over
clean committed FRRIE APIs and explicitly excludes the owner-dirty paths. Reproducing the dirty
bundle in this worktree would assume ownership, retain superseded machinery, and exceed current
scope budgets, so no bytes were copied.

## Decisions this intake produces

### Decision 1 — disposition of the owner-dirty bundle (object tier)

Options:

1. adopt the nine paths wholesale and continue the old full-512 readiness chain;
2. treat the green component tests as launch authority and run a caller assembled around them; or
3. preserve the bundle as owner-owned WIP evidence, freeze the minimal §11 R128 card, and assign a
   fresh clean implementation that never touches those paths.

Recommendation: option 3. Options 1 and 2 violate the current evidence and engineering scope and
would erase the ownership boundary.

`Owner-delegated decision (unattended, 2026-09-03 instruction): (3)`

### Decision 2 — next rung (object tier)

Options:

1. send another Pro round;
2. launch a result immediately; or
3. have CM implement and technically accept the frozen R128 card, then return the exact clean
   launch sha and command to DM for fresh admission and a detached one-seed invocation.

Recommendation: option 3. The owner-final Portfolio decision and the existing B01 Innovator family
already decide the direction question; no Pro decision is missing. A result launch is not yet
admissible because there is no clean implementation or launch sha.

`Owner-delegated decision (unattended, 2026-09-03 instruction): (3)`

## Meaning-complete CM return contract

CM receives the science card verbatim. It owns only a new R128 runner, its focused mirrored test,
and at most one small object-local helper. It preserves the existing host, actor/critic, FP32
arithmetic, Adam/RNG laws, paired information/work, projection boxes, native endpoint, and external
side effects. It must not modify, copy, stage, or delete any of the nine owner-dirty paths.

Technical success is: one under-600-line `argparse` runner; one `summary.json`; one prospective
five-root packet with root 001 selected; exact nonzero count reconciliation; immediate
adaptation-free evaluations at `0,32,64,128`; the machine-generated exposure line; one toy
end-to-end smoke under 60 seconds; branch/count tests; no engineering-scope §4 machinery; a clean
commit and launch command. If clean existing APIs cannot supply this without a scientific or
numerical change, CM returns the exact missing API and stops.

Technical success cannot establish package value, competence, contact, equality, direction, or any
other scientific branch. DM interprets only a later valid result.

## Evidence paths and unresolved risks

- Science card: `FRRIE_B01_SECTION11_R128_SMOKE_SCIENCE_CARD_20260904.md`.
- Owner decision: `docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`.
- Handoff: `docs/research/portfolio/RESEARCH_HANDOFF_20260903.md`.
- Current direction: `docs/research/candidates/finite_resource_relational_inductive_efficiency/DIRECTION.md`.
- Component authority: B01 Innovator decision and clarifications in this directory.

Unresolved engineering risks are whether the clean committed collector/trainer APIs can run 128
consecutive updates without the dirty continuation additions, actual optimizer/evaluation wall
time, and native build availability at the future launch sha. These are CM/runtime facts. The
effectful B4 pilot was deliberately not run because it is not the selected R128 object and its
success would not close these gaps.

No `DIRECTION.md` update is warranted: no mechanism-level scientific result was observed.

