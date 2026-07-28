# Remote compute handoff — D7.S event-aligned audit

Rewritten 2026-07-27. Branch `untied-k`. Read `AGENTS.md` first, then
`docs/project/CURRENT_WORK.md`, then this file.

> ## The R4 launch procedure here is LIVE again (2026-07-28)
>
> The void banner that stood here is lifted: its own condition — "rewritten once
> the repair lands and is re-reviewed" — is met. `--population r4` landed in
> `28d6933f` (D'), its two blocking defects were repaired in `0193de1a` (D''),
> and the Stage B review of D'' returned **APPROVE on conformance and
> semantics**, having driven the eight-shard route end to end.
>
> **`--population r4` is REQUIRED on every shard and is not decoration.** R4
> identity is DECLARED, not inferred. Without the flag a shard earns no R4
> contract/namespace fields, runs under the legacy R3 seed namespace, and pools
> into an artifact carrying no proof it is R4. The pooler now refuses such a
> pool outright rather than relabelling it.
>
> Two behaviours to expect that this file previously did not describe:
> a **whole-population single-process run** (including the bare no-flag
> invocation) is now put through `r4_freshness_sentinel` and refuses before
> writing anything if it fails; and the pooler prints
> `D7_S_EVENT_ALIGNED_BRANCH=` **only** for an R4-population artifact, printing
> an explicit `D7_S_EVENT_ALIGNED_NOT_CONCLUSION_BEARING:` line otherwise.
>
> Evidence:
> `docs/research/cdc/EVIDENCE_NOTES/20260728_D7_S_R4_THE_PLANNED_PRODUCTION_ROUTE_CANNOT_PROVE_IT_IS_R4.md`
> and `..._THE_REPAIR_OPENED_A_HOLE_THE_OLD_CODE_REFUSED.md`

**The previous version of this file described the ep64 persistence-margin job.
That job is retired as causal evidence** (its environment was built fresh per
arm and the construction-time worlds were never recorded, so the pairing cannot
be reconstructed). Do not run it and do not quote its numbers. The record of why
it died is `CURRENT_WORK.md` under `d7_s_ep64_*`.

## The job

```bash
python scripts/audit_d7_s_event_aligned.py \
  --population r4 \
  --topology-seeds <one seed of the frozen R4 population> \
  --workers 4 \
  --out <run-dir> > <run-dir>/stdout.json
```

The frozen R4 population is `20260734 20260735 20260736 20260737 20260738
20260739 20260740 20260741` — **not** R3's `20260726-20260733`, which are
measured, autopsied, used to motivate R4 itself, and which R4 forbids pooling
with. `--population r4` hard-refuses any seed outside the population, so a
matrix typo is a loud failure rather than a quiet one; it also refuses a
repeated seed, and refuses `--episodes-calibration`/`--episodes-audit` outright,
because a conclusion-bearing run does not take an episode-count argument.

Evaluation only. No training, no policy, no checkpoint, no GPU — `torch` and
`stable-baselines3` are imported nowhere on this path (both are guarded
`try/except` in `scenario_base.py` and never referenced). CPU, single-threaded.

Hard dependency set, and nothing more:

```text
numpy==1.26.3  scipy==1.15.2  matplotlib==3.10.0
gymnasium==1.0.0  pettingzoo==1.24.3  networkx==3.2.1
python 3.10
```

**Do not install `requirements_sb3.txt` on a remote runner.** It is a cu118 CUDA
lock exported from a different machine, and the recorded runtime pin is
`torch=2.7.0+cpu`, `backend=cpu`, "no CUDA fallback". It would pull CUDA wheels
this audit never uses.

## Sharding — one topology per job, and no finer

`--topology-seeds` is the only shard lever. `scripts/pool_d7_s_event_aligned_shards.py`
asserts that shards' seed sets are **disjoint** and that their union is a frozen
registered set, and its docstring is explicit that sharding is *by whole topology
seed, never splitting episodes within a topology*. So:

```text
max useful parallel width  8 seeds  -- the whole R4 population, and that is all
min work per job           one complete topology
```

**R4 has no expansion set.** Ledger `R4-002` registers expansion = NONE, and the
R3 expansion apparatus was deleted rather than left as a guard that never fires.
An earlier version of this line cited "16 under the expansion set"; there is no
such set to expand into.

`--episodes-calibration` / `--episodes-audit` are **refused outright on the R4
population** (R2 repair) — they are a development lever only. They were never a
way to fit a wall-clock budget, and now they are not a way to do anything to a
conclusion-bearing run: the registered volume is 8 calibration + 8 audit
episodes per topology per block, and the freshness sentinel re-checks from the
artifact that the volume actually ran.

Pool afterwards; never average normalized margins across shards.

## Wall clock, and the ceiling that binds

Measured on the local CPU box 2026-07-27 via
`scripts/d7_s_clone_conformance_check.py`: **0.0615 s/step** continuation rate.
Against `scripts/d7_s_prelaunch_cost_bound.py`:

| legal set | s/step | steps/topology | wall clock |
|---:|---:|---:|---:|
| 3 | 0.0615 | 119,704 | 2.29 h |
| 5 | 0.0615 | 163,800 | 3.05 h |
| 8 | 0.0615 | 229,944 | 4.18 h |
| 8 | 0.17 | 229,944 | 11.11 h |
| 8 | 0.30 | 229,944 | 19.41 h |

The recorded band is `3.58 h – 19.41 h`; the local machine sits below its
optimistic edge.

**A GitHub-hosted Actions job is killed at 6 hours and its shard is lost.** At the
local rate every legal-set size fits, worst case 4.18 h. The margin is
`6 / 4.18 = 1.43×` — so the audit survives only if the runner is **less than
1.43× slower than this box**, and a 4-vCPU shared runner plausibly is not. Since
a topology cannot be cut below one job, there is no supported way to rescue an
overrun.

**Therefore: measure the step rate on the target runner before launching the
audit.** `scripts/d7_s_clone_conformance_check.py` does exactly that in about two
minutes and simultaneously proves the instrument works there — it prints
`continuation s/step` and a `CLONE_CONFORMANCE_PASS` verdict over seven
conditions. The contract already permits one microbenchmark of at most 20
minutes, so this needs no new authorization.

## GitHub Actions specifics

`.github/workflows/d7s-audit.yml` is prepared in the working tree, with two
`workflow_dispatch` modes: `benchmark` (the conformance check) and `audit` (an
8-way topology matrix, `timeout-minutes: 350` so an overrun fails cleanly inside
the 6 h ceiling rather than being killed at it).

Both former gates were cleared by the user on 2026-07-27:

1. **`workflow` scope granted.** Token scopes are now
   `gist, read:org, repo, workflow`, so `.github/workflows/` is pushable.
2. **The repo was made PUBLIC.** Actions minutes on standard GitHub-hosted
   runners are therefore free and unmetered, which removes the quota question
   entirely. Note the consequence: this repository and its full history are now
   world-readable.

**The 6-hour job ceiling is the only remaining hard constraint, it is not
user-clearable, and the benchmark says it binds.**

## Measured verdict — GitHub-hosted runners are NOT viable for the formal audit

Run `30245735762`, tag `d7s-benchmark-1`, `ubuntu-latest`, 2026-07-27.
`CLONE_CONFORMANCE_PASS`, all conditions, zero reconstruction replays — the
instrument works correctly on Linux. The rate does not work:

```text
local   0.0615 s/step
runner  0.0864 s/step        ->  runner is 1.405x slower
```

| legal set | wall clock on runner | vs 6 h kill |
|---:|---:|---|
| 3 | 3.12 h | fits |
| 5 | 4.18 h | fits |
| 8 | **5.77 h** | **1.087x headroom — about 14 minutes** |

Fourteen minutes of headroom is not a margin. And `|Z|` is **data-determined**,
not a knob: the legal set size falls out of the certified event, so which shards
land at 8 cannot be predicted before launching. The realistic outcome is that
some shards complete and some are killed at 6 h, with **no way to recover a
killed one** — a topology cannot be split, so the shard is simply lost and must
be rerun whole.

Do not launch `d7s-audit-*` on `ubuntu-latest`. Two routes that work:

- **Self-hosted runner on a cloud VM.** No job ceiling at all. Costs
  provisioning; removes the constraint rather than dodging it. This is the
  recommended vehicle.
- **GitHub larger runners.** More vCPU, but the 6 h ceiling still applies and
  they are billed even on a public repo.

## Cross-machine reproducibility — task 14 is a prerequisite, not an extra

The benchmark ran pre-task-14 code and demonstrated the defect in the open. Same
`topology_seed=20260726`, same `episode_seed=1406135324`, two machines:

```text
local   t_e = 708 steps
runner  t_e = 921 steps
```

The topology is identical — `build_topology_template` binds a private
`RandomState(topology_seed)` before the two init calls, so it is a pure function
of the seed and reproduces across machines. What differs is the **user world**,
which without task 14 comes from construction-time OS entropy, lands in a
different BS quadrant, and therefore certifies a **different event**.

So a cloud shard and a local shard of the same seed are not comparable runs, and
rerunning a shard does not reproduce it. Land task 14 before any distributed
execution, or the shards being pooled were measured in worlds nobody recorded.

## Bringing results back

Each shard writes `<run-dir>/d7_s_event_aligned.json` plus its topology records;
the full lossless result JSON also goes to **stdout**, which is why the workflow
redirects it to a file rather than letting it flood the log. Upload the whole
`<run-dir>` as an artifact, then pool locally.

## What to read first in the result

`episode_world_provenance.all_seed_controlled` must be `true`. False means at
least one episode ran in a world that cannot be regenerated — the exact position
that retired ep64 — and those episodes are listed under
`episodes_not_seed_controlled`. Then `conformance.ok`, then the margins.
