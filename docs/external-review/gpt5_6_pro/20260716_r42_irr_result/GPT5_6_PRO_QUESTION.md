# GPT-5.6 Pro Review Request: R42-IRR Valid Failure and the Next Native Temporal Edge

Date: 2026-07-16

## Requested review boundary

Audit the exact R42-IRR implementation and terminal evidence. Decide whether
`VALID_FAIL_R42_IRR_SERVICE` is valid, state the reusable causal conclusion,
and select exactly one structurally new next algorithm edge. R42 itself is
retired: do not rescue it through more seeds, steps, learning-rate changes,
threshold changes, residual capacity, reward shaping, or a renamed residual.

The controller's candidate next edge is a native renewal decision followed by
conditional autoregressive skill assignment, with probability and credit
factors matched to the actual retained/changed agents. Treat this only as a
candidate to accept, modify, or replace with one better single route.

## Background and innovation target

Standard HMASD samples a team code `Z` and then a MAT-style autoregressive
individual skill roster

```text
pi_H(Z, z | x) = pi_H(Z | x) product_i pi_H(z_i | Z, z_<i, x),
```

holds the joint assignment for a shared fixed period `k`, conditions each low
actor on its individual skill, and uses environment-agnostic `q_D/q_d`
mutual-information terms to drive team and individual skill semantics. The
sequential roster assignment and its complementary-team interpretation are
features that HA-CTSE must preserve.

OPT is retained only as a deterministic recognition/context substrate. A
sampled team intent was previously behaviorally near-inert and remains retired;
do not restore a decorative latent or add a new classifier/reward without first
establishing policy actionability.

The HA-CTSE innovation target is not a UAV-specific reward. It is a general
MARL controller in which different agents can maintain different natural skill
lifetimes while preserving HMASD-like skill discovery, differentiation,
cooperative composition, and sparse-task usefulness. A later open-roster axis
must also tolerate variable team membership, but join/leave transitions must
remain distinct from semantic skill renewal. Variable `N` is not authorized by
this review unless the fixed-`N` next edge first has a valid positive gate.

## Evidence chain that constrains the decision

1. R27 showed forced persistent skill-conditioned behavior, but natural use and
   cooperative credit remained unproved.
2. R29--R34 retired density-ratio, observational-effect, individual-effect,
   intervention-scored roster-composition, and fixed hindsight-mode routes.
3. R35--R40 retired several custom/public access substrates under their frozen
   contracts; these failures must not be repaired with environment-specific
   intrinsic rewards.
4. R41B freshly extracted the tracked original HMASD source and established a
   positive Alice--Bob source anchor. M0 passed with zero replay error and
   exactly 14,055 updates on each of the five optimizer paths. Exact-final
   deterministic win/key0/key1 were `0.89/0.97/0.92`, versus zero-step win `0`.
5. A proposed categorical `KEEP/SET(z)` reinterpretation was retired without
   training after source audit: when every agent still samples a skill label,
   mapping the incumbent label to KEEP leaves the final skill, policy inputs,
   likelihood, trajectory, and gradient distribution identical to full refresh.
6. R42-IRR therefore tested the smallest non-decorative native modification: a
   shared, task-blind residual on the original MAT individual-skill logits at
   the native `k0=50` check. It sees only incumbent/working roster, focal
   position, and active-agent mask. It adds no reward, duration action,
   independent KEEP head, new critic, team latent, age input, or low-policy
   change. The output was zero initialized, and the existing HMASD high
   advantage trained both the original head and residual.

## Exact R42 result

Both arms restored the same R41B checkpoint and ran concurrently on local CUDA:

```text
seed                         42041
arms                         fixed_refresh, incumbent_roster_residual
rollout environments         16 per arm, 32 concurrent
native check / episode       k0=50 / 100 steps
training                     200 outer updates, 320,000 env steps per arm
original optimizer paths     3,000 updates each per arm
final evaluation             100 deterministic paired resets per arm
bootstrap                    10,000 repetitions, seed 62042
```

M0 passed. The real-checkpoint preflight had zero action, log-probability,
value, entropy, replay, and base-gradient error; the direct residual gradient
norm was `0.2221746`; the module had exactly 548 parameters. The formal run had
the registered counts and valid replay/drift evidence.

M1 fixed anchor passed:

```text
fixed win/key0/key1 = 0.98 / 1.00 / 0.98
```

M2 service noninferiority failed:

```text
treatment win                         = 0.88
treatment-minus-fixed win mean        = -0.10
paired bootstrap 95% interval         = [-0.17, -0.03]
required strict lower margin          > -0.10
```

M3 temporal decoupling also failed:

```text
treatment discordant-agent SET rate   = 0.10      (required >= 0.20)
treatment-minus-fixed discordance CI  = [0.05, 0.16]
treatment full-synchronous SET rate   = 0.90      (required < 0.50)
agent SET rates                       = [1.00, 0.90]
minimum KEEP/SET marginal             = 0.00      (required >= 0.05)
actual SET-target entropy / log(4)     = 0.6514    (required > 0.80)
```

The PowerShell parent initially labeled the run failed because redirected
`Start-Process` objects exposed null `ExitCode` values. Both workers had already
written `state=completed` and complete seed results. The analyzer then ran once
on those unchanged results. This operational runner defect did not alter the
training, estimator, result JSON, or scientific branch; the runner now treats a
durable completed worker status as success only when no real nonzero exit code
exists.

## Controller interpretation to audit

R42 proves that a tiny incumbent-conditioned residual can receive a real policy
gradient and change the original joint distribution. It does not establish a
useful renewal mechanism. Under the unchanged full-refresh action grain and
existing joint high advantage, learning mostly retained synchronized full
replacement, collapsed one agent to always SET, narrowed actual SET targets,
and reduced task service.

The controller infers that merely biasing original skill logits is the wrong
action/credit factorization: retention is only the accidental event
`z_i^{new}=z_i^{old}`, while the sampled action is still a complete replacement
roster and receives the original joint-period credit. A structurally new route
would make renewal itself a real stored policy factor, apply MAT skill
assignment only to agents actually renewed, and give renewal/skill factors
returns whose time support matches their consequences. This inference must be
audited rather than accepted from outcome metrics alone.

## Candidate next edge for review

The candidate is provisionally named R43-NRC: Native Renewal and Conditional
Roster assignment.

At each fixed global inspection clock, use one canonical autoregressive
transaction:

```text
for agent i in MAT order:
    sample a true renewal decision b_i in {KEEP, RENEW}
    if KEEP: preserve incumbent z_i and open no new semantic segment
    if RENEW: sample z_i from the native skill head conditioned on Z and the
              tentative roster prefix, then commit it
```

The behavior likelihood must contain exactly the sampled renewal factors and
only the conditional skill factors actually sampled. Stored incumbents,
tentative prefixes, active masks, and executed decisions must be replayed
exactly. Later agents see earlier tentative KEEP/RENEW outcomes. The transaction
commits atomically after the canonical sequence; the low actor remains
`pi_l(a_i | o_i,z_i)`. Team `Z` lifecycle, event return, renewal credit, full
refresh escape, and warm-start initialization are unresolved design questions
for this review.

This route must not use lifetime bonuses, switch penalties, task identities,
contacts, goals, phases, distances, success predicates, external reward in an
intrinsic term, `q_d/q_D` as a renewal selector, or a duration-category action.
It must preserve the original environment-agnostic HMASD intrinsic objective
unless a general mathematical replacement is derived.

## Repository files to inspect

Read all of the following before answering:

- `AGENTS.md`
- `memory/CURRENT_WORK.md`
- `memory/ALGORITHM_PRINCIPLES.md` (especially Primary Benchmark Objective,
  Falsifiable Decoupled-K Hypothesis, and General MARL Objective Boundary)
- `memory/ExpRecord.md` (R41B and R42 entries)
- `memory/IMPLEMENTATION_PLAN.md` (R42 implementation boundary)
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/r42_irr_native_roster_residual.json`
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/fixed_refresh_seed_result.json`
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/incumbent_roster_residual_seed_result.json`
- `scripts/r42_native_roster_residual.py`
- `scripts/run_r42_native_roster_residual_arm.py`
- `scripts/analyze_r42_native_roster_residual.py`
- `scripts/run_r42_native_roster_residual_local.ps1`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/algorithms/mat/algorithm/ma_transformer.py`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/algorithms/mat/mat_trainer.py`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/runner/shared/base_runner.py`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/utils/h_shared_buffer.py`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/r41b_hmasd_alice_bob_full_source.json`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/seed1_result.json`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/FINAL_DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260715_open_roster_variable_team_review/DISPOSITION.md`

Primary HMASD paper:
`https://papers.nips.cc/paper_files/paper/2023/file/c276c3303c0723c83a43b95a44a1fcbf-Paper-Conference.pdf`

## Requested decision

Provide one integrated answer containing:

1. **R42 validity verdict.** Identify any concrete implementation, estimator,
   replay, comparator, evaluation, or analyzer defect that changes the valid
   result. Do not call a different hyperparameter or action space an
   invalidation.
2. **Reusable causal conclusion.** Separate what R42 establishes about
   residual actionability, existing HMASD credit, synchronized renewal, skill
   supply, and service from what remains only an inference.
3. **Route verdict.** Return exactly one of `ACCEPT R43-NRC`, `MODIFY R43-NRC`,
   or `RETIRE R43-NRC AND SELECT <one structurally different route>`. Do not
   return parallel alternatives.
4. **Exact policy contract.** If a renewal route is selected, give the joint
   probability factorization for team `Z`, true renewal decisions, and
   conditionally sampled skills; state the canonical autoregressive order,
   working-roster visibility, support, sampling/replay contract, and atomic
   commit semantics.
5. **Clock and segment contract.** Specify the lifetime of team `Z`, inspection
   clock, meaning of KEEP versus same-label RENEW, segment boundaries, episode
   reset/truncation, and whether any full-refresh escape is permitted without
   silently reinstating shared fixed lifetime.
6. **Credit and update contract.** Specify which return/advantage trains each
   renewal and conditional skill factor, its temporal support, detach and
   centralized-information boundary, and how it coexists with the unchanged
   low policy and environment-agnostic `q_D/q_d` objective. Explicitly address
   whether the original joint high advantage is reusable or is the failed edge.
7. **Warm-start boundary.** State exactly which R41B policy, optimizer,
   discriminator, ValueNorm, recurrent, and checkpoint states remain strict;
   how new renewal parameters initialize without changing the fixed path; and
   which parameter groups may update in the first gate.
8. **Minimum Alice--Bob abandonment gate.** Give the smallest local parallel
   paired run that distinguishes the selected mechanism from fixed refresh,
   including comparator, seed(s), environment steps, optimizer counts,
   evaluation episodes, exact M0/scientific metrics and thresholds, and
   mutually exclusive PASS/FAIL/INVALID branches. Do not weaken the service or
   temporal-mechanism claim after seeing R42.
9. **Variable-team compatibility.** State only the structural constraints the
   fixed-`N` design must preserve for a later masked open roster. Do not promote
   variable `N` before the fixed-`N` gate passes.
10. **Prohibitions and strongest objection.** List the retired R42 rescue
    variants and environment-specific intrinsic signals that remain closed.
    Give the strongest reason the selected route may still fail, and state
    whether it changes the verdict.

The answer must select one falsifiable next causal edge. It must not equate
label entropy, classifier accuracy, or a larger action space with useful skill
semantics or cooperation.
