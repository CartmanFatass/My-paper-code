# VSP-C1 K4 B01 technical record

## Prospective engineering contract

CM owns the implementation and observed execution of the scientifically selected [B01 card](VSPC1_K4_FACTOR_VALUE_B01_SCIENCE_CARD_20260905.md), with science and successor decisions retained by DM. Starting main: `582a2e4de0e67e47c33bd1b5a8cabb496450a7bf`, clean when inspected. Worktree: `C:/Projects/HMASD-worktrees/cm-vspc1-b01-20260905`; branch `codex/cm-vspc1-b01-20260905`. Concurrent work remains outside the owned paths.

Acceptance is a real seed-0 FACTOR/GENERIC comparison on the eight full-support contexts: correct six-step partner-dependent rewards, legal held actions, CPU FP32 networks of 188/191 parameters, exactly 128 unfrozen Adam steps, 8192 renewal transitions, episode-weighted loss, detached pre-update bootstrap and fixed nine-checkpoint evaluation. Each arm executes 25008 joint primitive steps. Actual action/context counts, parameter norms/displacement, all context returns, final J and normalized trapezoidal AUC must be readable. Final comparison and competing parameterization/optimization predictions belong to the DM; code conformance alone establishes no scientific advantage.

Owned source is `experiments/candidates/vsp_c1/k4_factor_value_b01/`, thin `scripts/run_vspc1_k4_factor_value_b01.py`, mirrored tests under `tests/experiments/candidates/vsp_c1/k4_factor_value_b01/`, and this record. Runtime evidence lives under ignored `temp/directions/vsp_c1/exp/`. Old audit/code/results, core, scientific card/intake, DIRECTION, shared Portfolio/audit/owner and workflow specifications are non-goals. No reference controller, forced-action evaluation, prerequisite A, extra seed, hyperparameter search or optional framework is selected.

Engineering scope section 4 additions: **none**. Ordinary in-process batch32 and existing supervisor/admission/timeout tools suffice. No queue beyond two serial commands, registry, resume, compatibility layer, provenance guard, profiler service or additional smoke is added. Source limit 2000, runner 600, research checks 5 minutes; orchestration ratio is a review signal only.

## State and protected dependency map

Each arm owns its network, Adam state and actual action trajectories. One batch contains 32 episode states `(p,tau,c,t,held_action)`. Time advances causally through six primitive steps. Period/partner/channel contexts are balanced; context ordering and exploration draws are shared by named seed streams, addressed independently of each arm's outcomes. Model initialization uses separate named streams because shapes differ. Greedy evaluation consumes no training randomness.

Boundary state is four FP32 features, action code is two entries, period code is two entries. FACTOR maps six inputs through 16 tanh units to four coordinates and dots the two-by-four embedding; GENERIC maps eight inputs through 19 tanh units to scalar Q. Renewal rows last only for a rollout/update cycle: 48 short-period plus 16 long-period rows. Targets are computed before the sole update and detached. Loss weight per row is `1/(32*(6/p))`; each period contributes one half. No replay, recurrence or checkpoint/resume serialization exists. Fixed evaluation and compact JSON are the sole primary consumers.

Preserve action timing, reward and normalization, public information, population, ordering/pairing, dtype, CPU/thread topology, all RNG stream assignments, optimizer parameters, bootstrap terminal semantics, all checkpoints and adverse outcomes. No cross-host bit-identity promise or frozen checkpoint format exists.

## Cost, placement and stop

Per arm cost law: imports/initialization + 24576 training joint steps / 8192 renewals + 128 updates over 64 rows + 432 evaluation joint steps / 144 decisions + actual semantic checks and publication. Unit times are unknown before the real invocation, not zero. The selected tiny dense tensor path needs no independent calibration or reference search; no measured speedup is asserted.

Two arm invocations run serially on configured `wsl_4070`, CPU FP32, one scientific process and one compute thread, in-process batch32. Each complete runner invocation has a 2700-second external timeout, including import/init/train/evaluation/checks/write/read. Sum of caps is 5400 seconds; study critical path, summed actual wall and aggregate CPU are reported distinctly. External Git/SSH/checkout/preparation is not scientific invocation time and is reported separately without invented timings.

Only committed and pushed source enters an exact-SHA detached remote worktree. Fresh actual-node `admit-memory` immediately precedes each runner, joined with `&&` inside its existing `agent-task` command. Both physical and effective available memory must be at least 4 GiB. No remote process or admission exists at this record's initial boundary. A cap or technical failure preserves outputs, supplies no mechanism polarity, and does not authorize extra seeds/arms or duplicate launches.

## Verification plan

Read-only source inspection plus focused pure/serialization tests check the changed dependencies without extra model/learner/environment exposure. Independent reviewer inspects actual source; formal budgeted trajectories provide held-action, partner/reward, count and loss-weight observations. Primary JSON is written and read within each invocation and read independently after completion. No separate environment or learner smoke and no historical publication replay is selected. This uses current evidence-spec sections 11.8/11.9 over older directory smoke defaults.

Scientific-tools skill and only its relevant adapters reference were read. The selected small Q host needs no PPO rewrite, PettingZoo interface migration or new dependency. Existing Torch native tensor operations implement the specified networks; current node declares Torch 2.7.0 and Python 3.10.21. No global interpreter upgrade follows.

## Implementation, review and execution

Pending; no result is asserted by the prospective contract above.
