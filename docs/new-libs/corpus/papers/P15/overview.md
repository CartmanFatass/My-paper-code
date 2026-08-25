# P15 — Learning Efficient Multi-agent Communication: An Information Bottleneck Approach

## Identity and scope

- An ICML 2020 empirical MARL communication paper proposing IMAC, which jointly learns compact messages and a weight-based scheduler under simulated bandwidth constraints (PDF pp. 1–9).

## Problem formulation

- Agents act under CTDE with learned messages and a scheduler deciding who communicates what to whom; a limited noiseless channel motivates an entropy budget (PDF pp. 2–5).

## Actual contribution

- The paper connects channel bandwidth to a message-entropy upper bound, applies a variational information bottleneck to message generation, and unifies protocol/scheduler training end to end (PDF pp. 3–6).

## Core objects and equations

- Core objects are message M_i, bandwidth B, differential/discretized entropy, mutual-information bottleneck terms, prior z(M_i), and scheduler weights (PDF pp. 3–6).

## Algorithms or mechanism primitives

- Algorithm 1 trains actor, protocol, centralized critic, and scheduler from replay; customized normalization regulates message entropy to emulate a bandwidth limit (PDF pp. 5–6).

## Assumptions and information structure

- The entropy propositions assume noiseless communication and quantization/rate definitions; learning assumes centralized training, differentiable messages, replay, and task-specific communication neighborhoods (PDF pp. 3–6).

## Theorems and guarantees

- Propositions 1–2 derive bandwidth-dependent entropy upper bounds for scalar/vector messages; they do not prove improved MARL return or optimal scheduling (PDF p. 4).

## Experiments and evaluation protocol

- Experiments cover cooperative navigation, predator-prey, and SMAC 3m/8m with bandwidth sweeps, ablations, and TarMAC/GACML/SchedNet plus communication baselines; predator-prey uses 4 predators, 2 prey, 2 landmarks, 100,000 training episodes, and 1,000 evaluation rounds (PDF pp. 6–9).

## Failure boundaries and non-claims

- Experiments with different agent counts/bandwidths are not a frozen-policy held-out-N study; entropy control is a communication mechanism, not proof of semantic sufficiency in every task (PDF pp. 6–9).

## HMASD prospective connections

- IMAC suggests a bandwidth-aware message bottleneck and learned sender scheduler for UAV teams; HMASD would need safety-critical content tests, link failures, and roster-generalization evaluation (PDF pp. 3–9).

## Recommended reading route

- Read the bandwidth propositions on pp. 3–4, the bottleneck/scheduler on pp. 5–6, then protocol details and task-specific evaluation on pp. 6–9.

## Source-page anchors

- Communication model (PDF pp. 2–3); entropy propositions (pp. 3–4); IMAC objective/scheduler (pp. 5–6); experiments and ablations (pp. 6–9).
