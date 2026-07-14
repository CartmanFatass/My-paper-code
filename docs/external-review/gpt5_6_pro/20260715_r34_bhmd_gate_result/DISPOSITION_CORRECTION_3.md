# Controller disposition: accept the reset, modify the comparator

Date: 2026-07-15

Source model: GPT-5.6 Pro. The raw response is
`RESPONSE_CORRECTION_3_RAW.md`.

## Decision

- R35-TMPF invalidity and retirement: **ACCEPT**.
- Closing the current R29--R35 intrinsic skill-formation program: **ACCEPT**.
- A sparse-reward recurrent MAPPO reset as a baseline question rather than a
  paper contribution: **ACCEPT**.
- The proposed trained-MAPPO versus frozen-R30 gate: **REJECT AS WRITTEN;
  MODIFY ONCE**.

## Why the proposed gate is not causal

The response gives Arm A 40 PPO updates while Arm B is frozen, then requires
equal PPO and optimizer exposure. That comparison measures continued training
against no training, not the value of a skill abstraction. A pure
`MLP -> RNN -> action` actor also cannot be initialized as the same function
from a trained R30 checkpoint containing skill FiLM, a high editor, and a
bridge. Partial loading or deleting FiLM would confound the starting policy.

The relative reward and completion gates are also undefined when the sparse
Alice--Bob arms both obtain zero collections. The previous 64K pair did exactly
that, so a positive-access condition is required before noninferiority can be
claimed.

## Accepted reset gate

Both trained arms start from one shared, untrained zero-step checkpoint:

- `constant_code_mappo`: the existing recurrent low MLP/FiLM/RNN/action head
  and centralized recurrent critic remain shape-identical, but every agent and
  time step receives dummy skill `0` and team code `0`; the high editor never
  executes or updates. With constant conditioning, the behavior policy is a
  function only of observation and recurrent history.
- `reward_pure_r30`: the same low stack plus the active R30 KEEP/SET editor;
  both low and high policies train from sparse external reward only.

Each arm receives 320,000 on-policy steps with 16 environments, rollout 80,
five recurrent PPO epochs, sequence length 10, sequence batch 64, and 64
paired-reset stochastic evaluation episodes. Low actor/critic exposure is
matched. R30's additional high update is the treatment and is reported
separately, not falsely counted as matched optimizer exposure.

The trained comparison uses absolute paired noninferiority margins for
normalized cycle success, normalized 625-cell joint-position coverage, and the
zero-cycle episode fraction. It cannot pass unless at least one arm reaches a
predeclared positive sparse-task access floor. The old trained R30 checkpoint
may remain a reference-only evaluation source, but it is not part of this
causal difference.

## Supported boundary

A PASS can establish only that, for one 320K Alice--Bob seed with matched low
optimization, observation-only recurrent MAPPO is a noninferior optimization
baseline to reward-pure R30. A clear R30 advantage establishes only a benefit
of the temporal-skill machinery in this toy setting and budget. Neither branch
proves that hierarchy is generally useful or useless, changes the valid
R29--R35 retirements, establishes HMASD/S7 parity, or constitutes the paper's
algorithmic contribution.
