# GPT-5.6 Pro Review — Literature-Informed Variable-N / Variable-Time Architecture

## Review purpose

Select one technically coherent, falsifiable post-R53 research program for
HMASD under both variable active-team size `N` and heterogeneous per-agent
skill/event duration `T_i`. This is an architecture and experiment-order
review, not authorization to implement or launch a new experiment.

The central problem is not merely scaling to many agents. The target system
must eventually support episode-internal join, leave and rejoin, survivor
hidden-state continuity, and different decision/event intervals for different
members, while preserving HMASD's skill semantics and on-policy probability
contract.

## Evidence boundary

- R53-RCMA-G0 is a small conventional anonymous variable-`N` queue-learning
  gate. Its formal run is in progress. Do not use intermediate metrics or
  assume PASS/FAIL; treat it only as a bounded baseline whose terminal result
  will be reviewed separately.
- The literature package contains eight paper/code analyses, a cross-paper
  synthesis, and an exact code/version index. Downloaded PDF binaries and
  third-party source trees remain local-only; the repository contains official
  paper/repository links and the inspected code anchors.
- Many-agent scalability, cross-episode generalization across fixed `N`, and
  episode-internal dynamic membership are distinct claims.
- Variable `T_i` must use real-time SMDP credit. A mechanism that only changes
  execution clocks without matching return, bootstrap, event ownership and
  PPO replay is not acceptable.
- Intrinsic reward must remain environment-independent. Do not introduce
  task labels, button/target/contact predicates, human roles, success signals,
  classifier shortcuts, or environment-specific reward shaping.
- Do not revive retired R29–R52 mechanisms by renaming, retuning, increasing
  budgets, or moving the same signal into a critic/reward.

## Repository files to inspect

Read all of these files before answering.

### Curated literature package

- `docs/research/literature/n_k_many_agent_deep_dive/README.md`
- `docs/research/literature/n_k_many_agent_deep_dive/SYNTHESIS.md`
- `docs/research/literature/n_k_many_agent_deep_dive/CODE_INDEX.md`
- `docs/research/literature/n_k_many_agent_deep_dive/PAPER_SELECTION.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P01_ACE.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P02_ACAC.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P03_InforMARL.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P04_Sable.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P05_ExpoComm.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P06_SafeM3UCRL.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P07_CTMARL.md`
- `docs/research/literature/n_k_many_agent_deep_dive/analysis/P08_IARO.md`

### Candidate and current HMASD boundary

- `docs/research/candidates/field_slot_coordination/README.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/CURRENT_WORK.md`
- `memory/IMPLEMENTATION_PLAN.md`
- `memory/ExpRecord.md`
- `ha_ctse_process/r30_fixed_clock.py`
- `ha_ctse_process/standalone_agent.py`
- `ha_ctse_process/r53_rcma.py`
- `scripts/run_r53_rcma_gate.py`

## Candidate synthesis to challenge

The current synthesis proposes four separable layers:

1. an active-roster/member-event shell with stable member keys and explicit
   join/leave/rejoin semantics;
2. an active-only variable-`N` representation built from an InforMARL-like
   sparse set/GNN reference, fixed-count population slots with mass and
   `log(1+N)`, plus a bounded exact residual for rare critical members;
3. an ACE-like per-agent event runtime shell, but with ACAC-style agent-owned
   histories and duration-correct `gamma^T_i` return/bootstrap/GAE;
4. the existing HMASD low-level skill policy and semantic mechanism, protected
   from environment-specific reward redesign.

The proposed order is to test representation sufficiency, learning transport,
dynamic membership, variable-time credit semantics, and only then the joint
`N + T_i` setting. Challenge this decomposition rather than accepting it by
default.

## Requested decision

Return one explicit verdict and one ordered route.

1. Audit the eight paper/code interpretations. Identify any material factual
   or implementation-reading error that would change the synthesis.
2. Give an `ABSORB NOW / CONDITIONAL / DIAGNOSTIC ONLY / DO NOT ABSORB` matrix
   for ACE, ACAC, InforMARL, Sable, ExpoComm, Safe-M3-UCRL, CT-MARL and IARO.
   Name the exact mechanism, not merely the paper.
3. Decide whether the four-layer decomposition above is technically coherent.
   If modifying it, give one replacement architecture only. Explicitly define
   its policy, time, information and credit contracts.
4. Resolve the MAT tension: explain what remains autoregressive, what becomes
   a deterministic permutation-safe representation, and which sampled values
   must be stored and teacher-forced for PPO. Do not call a deterministic slot
   transform a stochastic MAT action.
5. Select the single smallest post-R53 abandonment gate. It must isolate one
   causal edge, run on a toy environment, avoid a full training campaign, and
   include exact arms, data, model budget, metrics, numerical thresholds,
   PASS/FAIL/INVALID branches and prohibited rescues. If its launch depends on
   the terminal R53 branch, state one deterministic branch table while keeping
   one next action per branch.
6. State which components should be handled now and which must remain deferred
   until an earlier gate passes. In particular, do not activate learned timing
   and dynamic membership in the same first experiment.
7. Give the strongest objection to the selected route and say whether it
   changes the recommendation.

The response must not authorize UAV-scale training, multi-seed expansion,
environment-specific intrinsic reward, cold-start replacement of the low-level
actor, or implementation before this review is archived and dispositioned.
