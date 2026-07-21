# Handoff — Formal Training Launched

Written 2026-07-22 00:48, immediately after launch. This is a cycle boundary:
implementation is complete and the experiment is running.

## What is running

```
run root : logs/event_held_commitment_link_g0_20260722_004657/
command  : scripts/run_noncalendar_commitment_benchmark_g0.py --mode train
           --device cuda
           --authorize-formal AUTHORIZE_EVENT_HELD_COMMITMENT_LINK_G0_FORMAL
stdout   : <run root>/train_stdout.log
```

Three arms, five replicates, 250 updates each, 320,000 transitions per arm.
Expected wall clock about **7 hours** on the RTX 4070, serial. Confirmed live at
launch: GPU 21% against a 1% idle baseline, 1434 MiB, one process.

Checkpoints land under `<run root>/train/replicate_<r>/<arm>/`. Formal evaluation
accepts only `update_250.pt`.

## Read this before interpreting results

**The `A_KEEP` and `A_RENEW` gates will not be readable from this run.** The fork
engine runs deterministically, while Replacement C is defined on held-out
stochastic trajectories. Under determinism a primitive action is an argmax and
the commitment bias cannot move one, which is why `A_KEEP` measured exactly zero
on every initialized natural-KEEP coordinate — an artifact of the apparatus, not
a property of the benchmark. See `PROBLEM_CACHE.md` P1.

The runner feeds absent fork evidence to the analyzer, so an unwired analyzer
resolves to `BENCHMARK_NON_IDENTIFIABLE` and can never reach
`COMMITMENT_SUPPORTED`. That is deliberate fail-closed behaviour, not a result.

**What this run does answer:** the primary `G = U_EHC − U_DUM`, the secondary
`V = U_EHC − U_OR`, the access floor, the `K`-bin lifetime conditions, and the
action-distribution TV intervention.

## Why CUDA and not CPU

CPU measured 3.26x faster end to end on a full three-arm update and scales to
5.94x across 15 workers where one CUDA card saturates at 2.0x — roughly 22
minutes against 7 hours. It is unusable anyway: the fork engine succeeds 6 of 6
eligible coordinates on CUDA and fails 6 of 6 on CPU, because the branch packs
one fewer request row at the forked step and CPU linear layers are batch-size
dependent for these shapes where CUDA is not. A CPU checkpoint also cannot be
loaded under CUDA by design. See `PROBLEM_CACHE.md` P1b.

## Contract, frozen into every checkpoint

```
execution   backend cuda, torch_threads 1
budget      16 envs, horizon 80, 250 updates, 5 replicates, 320,000 per arm
gates       access 0.78, gain 0.10, support_floor 128, k_bin 0.10,
            intervention 0.10, a_keep_lcb 0.0, a_renew_lcb 0.0,
            a_keep_mean_floor 0.02, a_renew_mean_floor 0.02
fork quota  32 KEEP + 32 RENEW per replicate, 320 pairs, no pooling
```

`registered_contract()` serializes to 6188 bytes and `load_checkpoint` rejects on
any inequality, so a checkpoint from this run cannot be mixed with one produced
under a different backend, thread count or threshold set.

## Commit chain this session

```
ce0d0ec  three-arm OR/DUM/EHC implementation
7ba056e  battery revision A/B/D
473b9da  Replacement C stage 1, candidate mark retention
1dcee48  stage 1 hardening, four guards
bcdff53  sequential counterfactual fork engine
def063c  per-factor replay tolerance classes
f6c6204  execution backend and Replacement C gates
8d2e10e  untrack a literature script committed by accident
```

38 focused tests pass on the CUDA backend.

## When the run finishes

1. Check `<run root>/train_manifest.json` exists and every cell reached update
   250. The manifest embeds the contract; a mismatch means something changed
   underneath the run.
2. Do **not** run `--mode evaluate` expecting C evidence until stochastic forking
   exists. Evaluation of `G`, access, `K`-bins and TV is valid now.
3. `--mode analyze` will return `BENCHMARK_NON_IDENTIFIABLE` while fork evidence
   is absent. That is the guard working.

## Highest-value next work

1. **Stochastic forking** (`PROBLEM_CACHE.md` P1) — retain realized per-step
   variates during held-out evaluation and script the four fork streams from
   them. Contract-neutral: trajectories are not checkpointed and their fields are
   not in the contract, so this needs no new boundary. Required before the C
   gates mean anything.
2. **Same-size request packing** (P1b) — would unblock CPU and remove a hidden
   shape-identity dependence. Needs its own boundary because `collect_trajectory`
   is frozen.
3. **float64 likelihood accumulation** (P2) — would likely retire the
   compositional joint bound, the width coupling and much of the device
   sensitivity. Three of the last five repairs would not have existed. Ask the
   external reviewer first; it is protected probability semantics.

## Environment gotchas

- Always `C:/Users/wu/.conda/envs/SB3/python.exe` directly. The default `python`
  is CPU-only torch. `conda run -n SB3` raises `UnicodeDecodeError`.
- `.gitignore` ignores `*.md` globally with per-directory negations. If a
  markdown file will not stage, add a negation rather than `git add -f`.
- Never `git add <directory>` here — it swept an untracked user script into a
  commit this session. Stage explicit paths and check `git status` afterwards.

## Decisions taken under delegated permission

1. Substituted mutation testing for a third review on the replay-tolerance
   repair. The mutation was decisive: neutering only the support-leak
   computation, with the field still registered, let the corruption through.
2. Registered CUDA rather than CPU as the execution backend, after measuring
   that CPU cannot produce the fork evidence at all. Speed lost to validity.
3. Merged the CPU execution contract and the result-gate constants into one
   change rather than two, so checkpoints are invalidated once rather than twice.
