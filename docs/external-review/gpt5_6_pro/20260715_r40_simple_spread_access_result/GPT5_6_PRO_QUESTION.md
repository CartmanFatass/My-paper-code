# GPT-5.6 Pro Review Request: R40 Valid Failure And The Single Post-Substrate Route

Date: 2026-07-15

## Requested review boundary

Audit the valid R40 result and decide whether the project should take the one
controller-proposed next route:

```text
exact HMASD-paper Alice--Bob environment
-> unchanged standard fixed-k HMASD positive reproduction
-> only after PASS, native categorical R30 per-agent KEEP/SET on the same task
```

Do not propose parallel routes. If this route is rejected, select exactly one
structurally different route and retire the others. Do not rescue a retired
gate through more steps/seeds, tuning, threshold changes, reward shaping, a new
toy, or another environment-specific intrinsic reward.

## Background and innovation target

Standard HMASD uses a team skill/code followed by autoregressive individual
skill assignments, a fixed shared skill period `k`, a low policy conditioned on
the individual skill, and environment-agnostic `q_D/q_d` mutual-information
pressure for team and individual skill semantics. Its sequential assignment is
the useful MAT-like coordination component that this project must preserve.

OPT is retained only as a deterministic continuous recognition/context
substrate. Earlier sampled team codes were behaviorally decorative and are
retired; do not restore a sampled team latent, `q_D` reward, or classifier until
its policy actionability is established.

R30 removes a discrete duration action. At a fixed global inspection clock
`k0`, every agent emits a native categorical `KEEP` or `SET(z)` token in an
autoregressive sequence. Later agents see the tentative earlier edits. Long
skills arise by repeated `KEEP`; different agents can acquire different natural
lifetimes without expanding a duration-action Cartesian product. There is no
positive lifetime reward, switch penalty, forced maximum lifetime, or
environment-specific shaping.

The later open-roster objective is variable team size plus variable per-agent
skill lifetime. Its intended controller is permutation-equivariant over active
members, masked to a bounded active roster, with join/leave transitions kept
separate from semantic skill renewal. That axis is deferred until a learned
fixed-`N` anchor exists.

## Evidence chain that must constrain the decision

1. R27 established forced persistent skill-conditioned behavior, but not
   natural use or learned cooperative credit.
2. R29--R34 retired actor-density ratios, observational effect identification,
   direct individual IFEPG, intervention-scored roster fitting, and related
   effect/codebook routes.
3. R35--R38 retired the repository's custom sparse Alice--Bob/CTS access
   program. Novelty increased coverage and task identity improved rare access,
   but ordinary policies never established reliable coordinated success.
4. R39 passed AR capacity, sampled reward alignment, exact stored-prefix replay,
   and native PPO mechanics, yet failed to learn the fixed-`N` roster mapping on
   `two_timescale_role_free_actions`.
5. R40 now validly fails on public PettingZoo `simple_spread_v3`: MAPPO mean
   return `-52.3922`, random `-52.5873`, paired difference `0.1950` with 95%
   interval `[-1.4484, 1.9034]`, and zero of four blocks above the `-35` floor.
   M0 passed with 500 updates, 2,500 low optimizer steps, replay error
   `2.384e-7`, and zero high updates.

The repository's custom Alice--Bob environments are not the HMASD paper's
original task and cannot inherit its published positive evidence.

## Controller interpretation

R40 is not evidence that recurrent MAPPO, HMASD, or `simple_spread` is generally
incapable. It retires only the frozen R40 contract. More importantly, the
combined R35--R40 record shows that searching for another convenient substrate
has become a research-detour loop.

The controller therefore proposes using the exact environment on which HMASD's
standard fixed-`k` skill/discriminator system already has positive published
evidence. This is not a new contribution. It is a positive compatibility anchor
for the actual algorithm family being extended. The original environment,
reward, observations, termination, skill semantics, fixed `k`, `q_D/q_d`
objective, and evaluation must be reproduced rather than redesigned.

If the unchanged fixed-`k` HMASD anchor passes, the only next causal change is
R30 temporal decoupling on the same checkpoint/task. If it fails validly, the
paper-task reproduction route must be retired rather than tuned until it passes.

## Repository files to inspect

Read all of the following before answering:

- `AGENTS.md`
- `memory/CURRENT_WORK.md`
- `memory/ALGORITHM_PRINCIPLES.md` (especially Research Causal Discipline)
- `docs/research/decisions/R35_R40_SUBSTRATE_FAILURE_REVIEW_20260715.md`
- `docs/research/decisions/R39_NATIVE_TOY_CREDIT_FAILURE_REVIEW_20260715.md`
- `docs/external-review/gpt5_6_pro/20260715_r40_simple_spread_access_result/r40_simple_spread_access.json`
- `ha_ctse_process/config_r40_simple_spread.py`
- `ha_ctse_process/standalone_agent.py` (`_update_low_recurrent` and recurrent likelihood)
- `ha_ctse_process/train.py` (constant-code/no-high update path)
- `scripts/analyze_r40_simple_spread_access.py`
- `scripts/run_r40_simple_spread_access_local.ps1`
- `hmasd/agent.py` (standard high/low/discriminator update and checkpoint paths)
- `hmasd/networks.py` (`SkillCoordinator` and stored-prefix evaluation)
- `config_r39_native_hmasd_toy.py`
- `train_multiproc_config_1.py` (native HMASD collector/update entry)
- `docs/research/designs/R30_FIXED_CLOCK_AR_EDIT_DESIGN_20260714.md`
- `docs/external-review/gpt5_6_pro/20260715_open_roster_variable_team_review/DISPOSITION.md`

Primary HMASD paper:
`https://papers.nips.cc/paper_files/paper/2023/file/c276c3303c0723c83a43b95a44a1fcbf-Paper-Conference.pdf`

## Requested decision

Provide one integrated answer containing:

1. **R40 validity verdict.** State whether a concrete implementation or
   estimator defect changes `VALID_FAIL_R40_ACCESS`. A mere alternative
   hyperparameter/budget/action choice is not an invalidation.
2. **Cross-round causal conclusion.** Separate verified mechanics,
   instrumentation failures, optimization/capacity uncertainty, and reusable
   negative scientific conclusions from R35--R40.
3. **Route verdict.** Return exactly one of `ACCEPT R41 HMASD-ALICE-BOB
   REPRODUCTION`, `MODIFY R41`, or `RETIRE R41 AND SELECT <one route>`.
4. **Exact reproduction boundary.** Identify the authoritative paper/code
   environment, native reward/observation/termination, fixed-`k` HMASD model,
   `q_D/q_d` objective, checkpoint initialization, optimizer/update exposure,
   and evaluation semantics that must be reproduced. Explicitly separate these
   from the repository's custom Alice--Bob variants.
5. **Minimum abandonment gate.** Give the smallest local/toy-first run that can
   establish a positive fixed-`k` anchor, with M0, scientific metrics and
   thresholds, comparator, seed(s), environment steps and optimizer counts,
   and mutually exclusive PASS/FAIL/INVALID branches. Prefer reduced compute
   only where it preserves the paper mechanism; do not silently weaken the
   claim.
6. **PASS-only R30 boundary.** Specify the single later causal comparison that
   would replace shared fixed `k` with per-agent `KEEP/SET`, including exact
   warm-start, probability, clock, gradient, reward, and checkpoint boundaries.
   Do not authorize that implementation before the reproduction PASS.
7. **Prohibitions.** State which substrate searches, intrinsic signals,
   retired effect objectives, variable-`N` mechanisms, and rescue variants
   remain closed.
8. **Strongest objection.** Give the strongest reason this route could still be
   another detour, and state whether it changes your verdict.

Do not use benchmark-specific intrinsic rewards. Any intrinsic term must retain
one environment-agnostic mathematical form and input contract and must not read
task identities, goals, contacts, phases, success predicates, distances, or
external reward.
