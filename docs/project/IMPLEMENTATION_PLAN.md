# HA-CTSE Active Implementation Plan

Updated: 2026-07-20
Status: IMPLEMENTATION_COMPLETE_AWAITING_GIT
Work ID: `noncalendar-heterogeneous-tracking-g0-implementation-20260720-repair1`
Base/source commit: `48fdcfd51ac54d50b38746d385c07f3f0a431ca5`

## 1. Accepted evidence source and estimand

Implement only `NONCALENDAR_HETEROGENEOUS_TRACKING_G0`, the code-ready H/C/S/D
benchmark accepted by the full Convergent contract and its single field-5
repair. This assignment implements and focused-tests the source; it does not
launch training/evaluation, interpret evidence, change portfolio weights, or
select a successor.

The benchmark asks whether one anonymous dynamic-membership physical tracking
task is structurally reachable with independent primitive authority (`H`),
information-null to calendar/static recurrence (`C`), materially impaired by a
shared four-step renewal clock (`S`), and causally accessible to the matched
ordinary recurrent primitive controller (`D`). H/S are exact noncausal ceilings
with zero parameters and optimizer steps. C/D are byte-equal initializations of
the unchanged `DirectPrimitiveARPolicy` factorization and PPO algebra.

Per episode, tracking `A` is mean active-row quality, completion `B` is the
fraction of actually ended noncensored target segments completed with a two-step
target streak, and utility is `sqrt(A*B)`. Reward is zero at steps `0..78` and
equals `U` at step 79. A pass qualifies only a later separately reviewed
information-matched D-vs-R source; it proves no hierarchy or successor.

## 2. Frozen task, observation, and membership contract

- Horizon 80; lifecycle capacity 6; primitive actions `0/1/2` map to thrust
  `-1/0/+1`; local state is clipped to `{-2,-1,0,1,2}`.
- Target is `-2/+2`; per-step quality is `1-abs(x_next-g)/4`; segment completion
  requires a two-step target streak at its final active step.
- Training/IID duration blocks are permutations of `{5,9,13}`; held-out blocks
  use `{5,7,9}`. Each lifecycle has its own active-time stream and target flips.
- Adjacent sign mates share membership, duration, physical state, order, and
  action uniforms. Only all target signs invert.
- Training/IID membership events occur at `0/20/40/60`, with initial count
  `{3,4}`. Held-out uses `0/12/36/68`, with initial count `{2,5}`. Genuine JOIN
  zero-initializes, temporary absence freezes, REJOIN restores/increments epoch,
  terminal LEAVE censors/deletes, and survivors remain continuous.
- Every active row has the registered 15-field order. Field 5 is exactly
  `mean_{i in A_t}(abs(g_i-x_i)/4)` with range `[0,1]`.
- C zeros indices `3,4,5,6,9,10,11` before actor, critic, storage, and replay.
  D retains them. No causal network sees routing keys/ranks/epochs, parity,
  duration remaining, future ledger, reward history, identity, role, or H/S plan.

## 3. Files and replacement ledger

Only these paths may change:

- `docs/project/IMPLEMENTATION_PLAN.md` — this current executable design.
- `docs/research/designs/NONCALENDAR_HETEROGENEOUS_TRACKING_G0.md` — durable
  task, information, solver, exposure, checkpoint, result, and non-claim design.
- `ha_ctse_process/noncalendar_commitment_testbed.py` — paired ledgers,
  environment, mask, causal collection, exact H/S DP and brute force, audits,
  bootstrap, strict checkpoints, constants, and result branch selection.
- `scripts/run_noncalendar_commitment_benchmark_g0.py` — paired C/D trainer,
  registered evaluation, M0 assembly, strict resume, and one terminal output.
- `tests/ha_ctse_process_noncalendar_commitment_benchmark_g0_test.py` — one
  focused deterministic corruption check.

No file is deleted. Existing Direct PPO/event interfaces and all Generic-SHORT,
supplied-executor, opportunity-audit, old result, and checkpoint paths remain
read-only. The scientific replacement is the old predictable supplied-executor
substrate by this independent noncalendar benchmark, not a restart of that line.

## 4. Ledger, causal tensor, and PPO data flow

One immutable `NoncalendarLedger` is generated from explicit
`PCG64(SeedSequence([...]))` task and order streams. It owns only task-side
randomness. Future ledger contents are passed exclusively to H/S.

For C/D each step applies membership, constructs current active observations,
applies the C mask when registered, packs `[env,lifecycle,15]` with its active
mask and recorded order, and performs one batched direct-policy step. The real
primitive autoregressive token loop is retained. All primitive actions then
apply simultaneously. `DirectTrajectory` stores the same observation, mask,
order, action, token likelihood, value, hidden before/after, prefix, and reward
used by replay.

The existing 20-step recurrent packing, teacher-forced replay, GAE, clipped PPO,
entropy, and gradient clipping are reused unchanged. Collection for both arms on
the same 16 IDs finishes before either four-pass update. Environment, membership,
order, uniforms, masks, and reward are detached; only policy/value likelihood
and critic paths carry gradients.

Genuine JOIN hidden is zero; active hidden updates only at its actor token;
temporary absence freezes hidden; REJOIN resumes it; terminal state is zeroed
and never reused; survivor hidden remains continuous. The active mask is the
sole likelihood, entropy, and replay-row authority.

## 5. H/S solver, clocks, and performance structure

Per lifecycle, exact DP state is `(x, target streak, previous command)` and
labels are integer tracking quarter-units plus completed segments. H enumerates
all three actions for every active member at every step. S may change a focal
command only when `t mod 4 == 0` or that lifecycle genuine-JOINs/REJOINs;
otherwise it holds the previous command, including across temporary absence.
Neither solver mutates membership, targets, duration, order, or reward.

Labels Pareto-prune only within the same future-relevant state. Lifecycle
frontiers convolve with joint Pareto pruning, and the selected legal episode
trajectory maximizes `sqrt(A*B)` without splicing separate A/B optima. A tiny
unpruned H/S DP must exactly equal exhaustive brute force.

Simulator loops remain only for causal physical/lifecycle dependence. Policy
inference batches environments and padded lifecycle rows; the token loop remains
for real AR dependence. Trajectories pack once and reuse tensors for all four
PPO passes. H/S exploit finite-state lifecycle decomposition rather than joint
action enumeration. Evaluation batches all 256 episodes per registered cell;
wall time is reported for paired training and registered evaluation.

## 6. Model, exposure, RNG, evaluation, and checkpoint contract

C/D each retain the 14,980-parameter direct model: member encoder
`15->32->32`, active-set context `33->32`, GRU input/hidden `67/32`, AR head
`35->32->3`, and team critic `41->32->1`. PPO remains Adam `3e-4`, gamma
`0.99`, GAE lambda `0.95`, policy/value clips `0.20`, value coefficient `0.50`,
entropy coefficient `0.01`, gradient clip `0.50`, four passes, and BPTT 20.

Per arm: 16 environments, horizon 80, 250 updates, 320,000 transitions, 1,000
optimizer steps, and 4,000 training episodes. Seeds are model `58_058`, training
task/order/action `68_058/78_058/88_058`, IID task `98_058`, held-out task
`99_058`, evaluation order/action `79_058/89_058`, and bootstrap `108_058`.
Training IDs are `0..3999`; each evaluation profile uses `0..255`.

Each arm evaluates update 0 and 250 on IID and held-out, deterministically and
stochastically: eight cells and 2,048 episodes per arm. H/S solve the same 256
held-out ledgers once. One 10,000-resample table over 128 base clusters preserves
all sign, arm, checkpoint, and solver pairings. No best checkpoint is read.

Per-arm checkpoints are `update_000.pt`, `latest.pt` after every complete update,
and `update_250.pt`. Strict payloads contain arm, model/optimizer, completed
update, next episode ID, all seed/profile headers, Torch CPU/CUDA RNG, stream
ownership, mask schema, model shape/count, and BPTT. Resume requires paired
complete-update counters. Missing, extra, or mismatched data hard fails; final
model/optimizer reload error must be zero.

## 7. Validity, terminal branches, and focused evidence

M0 fails closed on any state/action/transition/reward, duration, membership,
sign-pair, mask, causal-information, solver-authority, DP equivalence,
heterogeneity, anonymous-relabeling, lifecycle-hidden, initialization, exposure,
active-row, replay, finiteness, parameter-drift, checkpoint, forbidden-module,
seed, evaluation, bootstrap, or successor-selection defect.

The only terminal result is
`result/noncalendar_heterogeneous_tracking_g0.json`. Its exact mutually exclusive
priority is:

1. `INVALID_BENCHMARK_IDENTIFIABILITY_G0`;
2. `REJECT_BENCHMARK_STRUCTURALLY_UNREACHABLE`;
3. `REJECT_BENCHMARK_CALENDAR_IDENTIFIABLE`;
4. `REJECT_BENCHMARK_NO_HETEROGENEOUS_LIFETIME_PRESSURE`;
5. `NO_ACCESS_BENCHMARK_ORDINARY_CONTROL`;
6. `PASS_BENCHMARK_IDENTIFIABILITY_AND_ORDINARY_ACCESS`.

All registered H/C/S/D floors, ceilings, and strict paired LCB margins are
encoded once in `THRESHOLDS`; missing, extra, or nonfinite terminal keys fail.
There is no `UNDERPOWERED` branch and no automatic successor.

The one focused CPU test covers exact field 5 and mask ordering, byte-equal C
sign-pair observations/order/actions/hidden and information-null ceilings,
JOIN/temporary-LEAVE/REJOIN/terminal hidden ownership, deterministic environment
snapshot continuation, tiny H/S DP against brute force, fail-closed result keys,
and registered counts. It does not train or run formal evaluation.

Accepted focused evidence is `1 passed in 4.78s`, including a direct runner
assertion that `_tiny_solver_valid()` returns `True`; the registered 250-update
paired training and 256-episode evaluation cells have not been launched.

## 8. Non-goals

No training or formal evaluation launch. No reward, shaping, budget, seed,
threshold, duration, membership, horizon, observation order, mask, authority,
model, optimizer, BPTT, bootstrap, checkpoint-selection, or result-branch change.
No hierarchy, high actor, skill, KEEP/SET, supplied executor, intrinsic reward,
posterior, graph, attention, communication extension, team latent, learned
hazard/duration, identity/role/progress input, new critic, compatibility path, or
fallback. No Git operation, scientific interpretation, external review,
integration, portfolio update, or successor route.
