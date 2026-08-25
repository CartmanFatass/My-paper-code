# NONCALENDAR_HETEROGENEOUS_TRACKING_G0

## Purpose and estimand

This benchmark asks whether one independent, noncalendar physical tracking
task simultaneously establishes four facts under anonymous dynamic membership:

1. `H`: the task is structurally reachable with per-member primitive authority;
2. `C`: calendar, membership phase, recurrent memory, and static pre-positioning
   are information-null when current demand/error fields are removed;
3. `S`: a shared four-step renewal clock is materially weaker than independent
   primitive command changes; and
4. `D`: the matched ordinary recurrent primitive controller can learn causal
   access from current online demand.

`H` and `S` are noncausal exact ceilings. `C` and `D` are separate byte-equal
initializations of the existing `DirectPrimitiveARPolicy`. A pass qualifies a
later, separately reviewed information-matched D-vs-R source only. It does not
establish hierarchy, learned skills, cooperation, temporal abstraction value,
UAV transfer, or successor authority.

## Finite-state task

- Horizon: 80 physical steps; lifecycle capacity: 6.
- Primitive actions `0/1/2` mean thrust `-1/0/+1`.
- Local state `x` is clipped to `{-2,-1,0,1,2}`.
- Current target `g` is `-2` or `+2`.
- Per-step tracking quarter-units are `4 - abs(x_next - g)`, hence
  `q = 1 - abs(x_next-g)/4`.
- A target segment completes only when its final active step ends with a
  two-step streak at the target.
- Training/IID durations are permutations of `{5,9,13}` in independent
  three-segment blocks. Held-out durations use `{5,7,9}`.
- Targets flip at each segment boundary. Duration remaining and future target,
  membership, order, and action randomness never enter a causal network.
- Tracking `A` is mean `q` over active rows. Completion `B` is the fraction of
  actually ended, noncensored segments completed with the registered streak.
  Utility is `sqrt(A*B)`.
- Rewards are exactly zero at steps `0..78`; step 79 pays `U`.

Each sign pair shares its complete ledger, initial physical state, order, and
action uniforms. Only every target sign is inverted. Episode `e` has
`base_id=floor(e/2)` and `sign_parity=e mod 2`.

## Membership and lifecycle ownership

Each base ledger draws a permutation of six opaque routing keys. Keys, ranks,
epochs, parity, identities, and roles never enter model inputs.

Training/IID membership events are at `0/20/40/60`: initial genuine JOIN of
`N0 in {3,4}`, one initial temporary LEAVE, its REJOIN plus one genuine JOIN,
then one active terminal LEAVE. Held-out uses `0/12/36/68` and
`N0 in {2,5}`. This yields registered roster traces `3->2->4->3`,
`4->3->5->4`, `2->1->3->2`, or `5->4->6->5`.

Genuine JOIN initializes physical state and recurrent hidden state to zero.
Temporary absence freezes physical state, demand active-time, command, and
hidden state. REJOIN restores them and increments the membership epoch.
Terminal LEAVE censors the open segment and deletes its state after boundary
finalization. Unrelated survivors remain continuous. Every held-out base ledger
is deterministically rejection-materialized until it has at least 20 physical
steps with two active remaining durations differing by at least two and at
least three lifecycle instances with a completed target transition.

## Observation and information boundary

Every active row is width 15. Common fields `0..7` are:

1. `t/80`;
2. `log(1+N)/log(7)`;
3. active mean `x/2`;
4. active mean `g/2`;
5. active mean `(g-x)/4`;
6. `mean_{i in A_t}(abs(g_i-x_i)/4)`, range `[0,1]`;
7. active fraction with `target_changed=1`;
8. active fraction currently JOINing or REJOINing.

Local fields `8..14` are `x/2`, `g/2`, `(g-x)/4`, `target_changed`, event code
(`JOIN=+1`, `REJOIN=-1`, ordinary `0`), previous thrust, and capped action-run
length divided by 16.

`D` retains all fields. `C` zeros indices `3,4,5,6,9,10,11` before actor,
critic, rollout storage, and replay. It retains time, roster size, physical
state, membership events, previous command/run, recurrent state, active-set
sum communication, and primitive AR prefix. Consequently both sign mates have
exactly equal C observations, order, action uniforms, action tapes, and hidden
states. Their pair mean tracking is exactly 0.5; completion and utility pair
means are at most 0.5.

## Causal model and PPO

Both causal arms use the existing probability factorization unchanged:

- member encoder `15 -> 32 -> 32`, Tanh/Tanh;
- active-set context from embedding sum and `log(1+N)`, `33 -> 32`, Tanh;
- per-lifecycle GRU input width 67 and hidden width 32;
- primitive AR action head `35 -> 32 -> 3`, Tanh;
- centralized team critic from set sum/count and eight common fields,
  `41 -> 32 -> 1`, Tanh;
- exactly 14,980 parameters per arm.

The PPO contract is Adam `3e-4`, gamma `0.99`, GAE lambda `0.95`, policy and
value clip `0.20`, value coefficient `0.50`, entropy coefficient `0.01`,
gradient clip `0.50`, four passes per update, BPTT chunks of 20, and all
16 environments times four chunks per minibatch. Order changes only the
autoregressive factorization; actions are applied simultaneously. Collection
for both arms completes on the same 16 episode IDs before either update.

Per arm: 16 environments, horizon 80, 250 updates, 320,000 transitions,
1,000 optimizer steps, and 4,000 training episodes. Total causal exposure is
640,000 transitions and 2,000 optimizer steps.

## Exact H and S solvers

The task decomposes by lifecycle because demand and membership are ledgered and
there is no joint resource constraint. Per lifecycle, exact DP state is local
`x`, target streak, and previous command (needed for S). Labels are integer
tracking quarter-units and completed segments. Each step Pareto-prunes labels
only inside the same future-relevant state. Lifecycle frontiers are convolved
and Pareto-pruned jointly; the selected episode trajectory maximizes
`sqrt(A*B)` and never splices independently optimal A and B paths.

`H` may choose any legal primitive action for every active member each step.
`S` may change a focal command only at `t mod 4 == 0` or that member's genuine
JOIN/REJOIN; otherwise it holds the previous command. Absence freezes command.
Neither solver mutates membership, targets, durations, order, or rewards.
A tiny unpruned DP is compared with brute-force enumeration for both arms.

## RNG, evaluation, and confidence contract

All non-Torch task streams use `numpy.random.PCG64(SeedSequence([...]))`.
Seeds are: model 58,058; training task/order/action 68,058/78,058/88,058;
IID task 98,058; held-out task 99,058; evaluation order/action 79,058/89,058;
bootstrap 108,058. Training IDs are `0..3999`. Every evaluation profile uses
IDs `0..255`.

For each causal arm, update 0 and update 250 are evaluated on IID and held-out,
deterministically and stochastically: eight cells and 2,048 episodes per arm.
H and S each solve the held-out 256 ledgers once. There is no best-checkpoint
selection. Paired margins use the same 10,000 bootstrap resamples over 128
base-ID clusters; each resample retains both sign mates and every H/C/S/D and
zero/final pairing.

## Checkpoint and result integrity

Each arm stores `update_000.pt`, `latest.pt` after every complete outer update,
and `update_250.pt`. A strict checkpoint contains arm mode, model and optimizer,
completed update, next episode ID, all seed/profile headers, Torch CPU/CUDA RNG,
task/order/action ownership, observation-mask schema, model shape, and parameter
count. Resume is accepted only at a complete update boundary. Missing, extra,
or mismatched fields hard fail. Final reload must reproduce model and optimizer
tensors exactly.

M0 fails closed on any environment, ledger, mask, replay, lifecycle, solver,
count, finiteness, drift, checkpoint, seed, evaluation, or forbidden-module
defect. The mutually exclusive priority result is:

1. `INVALID_BENCHMARK_IDENTIFIABILITY_G0`;
2. `REJECT_BENCHMARK_STRUCTURALLY_UNREACHABLE`;
3. `REJECT_BENCHMARK_CALENDAR_IDENTIFIABLE`;
4. `REJECT_BENCHMARK_NO_HETEROGENEOUS_LIFETIME_PRESSURE`;
5. `NO_ACCESS_BENCHMARK_ORDINARY_CONTROL`;
6. `PASS_BENCHMARK_IDENTIFIABILITY_AND_ORDINARY_ACCESS`.

There is no `UNDERPOWERED` branch and no automatic successor. Numeric floors,
strict margins, and absolute ceilings are encoded once in the benchmark module
and emitted unchanged in the sole terminal result
`result/noncalendar_heterogeneous_tracking_g0.json`.

## Replacement and non-goals

This source replaces Generic-SHORT supplied-executor evidence as the active
benchmark substrate; it does not modify or restart that stopped line. No
existing file is deleted. The task adds no high actor, skill label, KEEP/SET,
supplied executor, intrinsic reward, shaping, posterior, graph, attention,
communication extension, new critic, learned duration, hazard, identity, role,
or compatibility path.
