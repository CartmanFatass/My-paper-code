# Open-roster direct MVP G5

Status: executable definition and formal evidence contract frozen after bounded
nonformal acceptance.

## Question and scope

Can one parameter-shape-`N`-independent direct recurrent policy learn an
absolutely usable task policy under within-episode membership change and
transfer to unseen active counts?

This is the first iteration of the user-authorized eight-round dynamic-agent
chain and will be reported as `docs/report/ITERATION_6.md`. Asynchronous skill
lifetime, skill selection, EHC, intrinsic reward and comparative advantage are
frozen out. The exact closed G0--G4 packages are neither rerun nor relabeled.

## Source family

Keep the 80-step Generic-SHORT task, primitive actions `IDLE/PERSIST/SHORT`,
terminal-only external utility, persistent duty and short-wave service. Each
episode contains four membership phases separated by temporary leave at step
20, rejoin plus genuine join at step 40 and terminal leave at step 60.

Training profiles are:

- `3 -> 2 -> 4 -> 3`;
- `4 -> 2 -> 6 -> 4`;
- `5 -> 3 -> 7 -> 5`.

Held-out profiles are:

- `6 -> 2 -> 8 -> 4`;
- `7 -> 4 -> 9 -> 6`.

Training uses operational capacity 10. Held-out evaluation uses capacity 12.
Capacity is padding/storage only and is not a model parameter or observation.
Wave demand remains `active_count - 1`; constructive utility must equal 1 for
every profile.

## Algorithm

Use a shared member encoder, a lifecycle-owned recurrent hidden state, active
embedding sum plus `log1p(N)` context, active-only autoregressive primitive
actions and a centralized active-set critic. Temporary absence freezes hidden
state, rejoin restores it, a genuine join starts at zero and terminal leave
destroys the active state. No persistent identity or slot embedding is read.

## Evidence semantics

The primary outcome is absolute held-out deterministic utility from one shared
checkpoint. Secondary outcomes are IID utility, stochastic utility, persistent
and short sub-scores, minimum replicate utility and final-minus-initial gain.
No comparator difference is an acceptance condition.

Operational validity requires exact source/profile counts, finite updates,
sample/replay parity `<=1e-6`, checkpoint/optimizer restoration, lifecycle
state ownership, parameter-shape independence from capacity and CPU one-thread
identity.

The prospective formal access conditions are:

- pooled IID deterministic utility CI95 lower bound `>=0.90`;
- pooled held-out deterministic utility CI95 lower bound `>=0.90`;
- every replicate held-out mean `>=0.85`;
- pooled held-out stochastic utility mean `>=0.80`;
- held-out deterministic final-minus-initial gain CI95 lower bound `>0`.

These are usability conditions, not claims of advantage.

## Frozen formal execution

```text
authorization_token=AUTHORIZE_OPEN_ROSTER_DIRECT_MVP_G5_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
replicates=3
updates_per_replicate=250
environments_per_update=8
horizon=80
ppo_passes=4
evaluation_episodes_per_cell=128
bootstrap_repetitions=10000
model_seed_base=551000
train_ledger_seed_base=651000
action_seed_base=751000
evaluation_seed_base=851000
bootstrap_seed=951005
```

The 20-update nonformal probe reached IID deterministic utility `0.68237` and
held-out deterministic utility `0.60549`, up from held-out zero-checkpoint
utility `0.35600`, with exact replay and lifecycle closure. This confirms a
learning slope but is not result evidence. The 250-update budget retains the
optimizer exposure of the earlier access-valid direct path while keeping each
replicate bounded.

## Admissible outcomes

First match after operational validity:

1. `NO_IID_ACCESS_OPEN_ROSTER_G5`;
2. `NO_HELDOUT_COUNT_ACCESS_OPEN_ROSTER_G5`;
3. `UNSTABLE_OPEN_ROSTER_DIRECT_G5`;
4. `USABLE_OPEN_ROSTER_DIRECT_G5`.

An invalid operational package consumes no iteration. A valid outcome consumes
iteration 6, preserves its observation and selects the smallest next dynamic-N
correction within the remaining seven-round grant.
