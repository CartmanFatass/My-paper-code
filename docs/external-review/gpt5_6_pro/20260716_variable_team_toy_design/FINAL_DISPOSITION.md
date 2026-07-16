# GPT-5.6 Pro R51-AMDT Launch-Exact Disposition

Date: 2026-07-16

Source model: GPT-5.6 Pro (`Pro` web conversation)

Raw evidence:

- `GPT5_6_PRO_RESPONSE_RAW.md`
- `GPT5_6_PRO_LAUNCH_CLARIFICATION_RESPONSE_RAW.md`

## Decision

Accept `CONFIRM_R51_AMDT_625_STEP_CONTRACT`. R51-AMDT-G0 is launch-exact.

The only correction to the original response is:

```text
125 balanced cycles
5 N-specific rollout/update units per cycle
625 shared optimizer steps
125 optimizer steps per specialist
625 aggregate specialist optimizer steps
320,000 transitions per arm
64,000 transitions per N per arm
PPO epochs = 1
no collected-batch reuse
```

The Anonymous Maintenance--Dispatch Task, `N={2,3,4,5,6}`, 32-step horizon,
persistent stations, short dispatch jobs, sparse terminal reward, anonymous
set-pointer recurrent actor-critic, fixed-N specialist family, seeds,
evaluation, M0--M2 thresholds, outcome branches, no-rescue clauses, and all
claim boundaries remain unchanged.

## Authorized action

Implement the isolated AMDT environment, shared policy, specialists, paired
probability ledger, analyzer, and local runner. Run one focused engineering
smoke, freeze a prelaunch Git boundary, then run the single registered local
CUDA experiment. A smoke is wiring evidence only and may not change the
contract.
