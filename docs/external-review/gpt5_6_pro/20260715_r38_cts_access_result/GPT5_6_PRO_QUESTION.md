# GPT-5.6 Pro Review: R38 CTS Access Failure And The Single Post-R38 Route

Date: 2026-07-15

## Requested decision

Audit the implementation and raw result of `EXP-20260715-r38-cts-access`, then
make one explicit decision:

1. Is `FAIL_R38_CTS_ACCESS` a valid scientific failure of the registered
   benchmark-access gate, or is there a concrete M0 defect that changes the
   estimand?
2. If valid, what is the reusable causal conclusion from R35--R38, kept
   strictly separate from any claim about skills, asynchronous lifetime,
   hierarchy, intrinsic reward, HMASD, or S7?
3. Should the project now retire the custom sparse-toy access program itself?
4. Select exactly one post-R38 causal route and reject the alternatives. Give
   its lowest valid baseline level, exact causal edge, smallest evidence-bearing
   experiment, abandonment gate, and prohibited rescue changes.

Do not return parallel routes or a menu for later selection. The output must
commit to one route.

## Non-negotiable intrinsic-reward boundary

The user has explicitly forbidden environment-specific intrinsic reward.

Any future intrinsic mechanism must use one environment-agnostic mathematical
form and one input contract across benchmarks. It may not read, encode, or be
redesigned around task identities, objects, goals, contacts, phases, clocks
whose meaning is task-specific, distances to task entities, success predicates,
or external reward. Environment shaping is not intrinsic reward and cannot be
used as evidence for reconstructing HMASD's sparse-exploration loop.

Do not propose an R38-specific anchor/shuttle bonus, classifier, potential,
count, progress reward, curriculum, role hint, or privileged actor field.

## Registered R38 question

R38 was only a Level-1 environment-access gate:

```text
swap-equivariant simultaneous anchor/shuttle duties
-> ordinary constant-code recurrent MAPPO accesses both duties
-> reliable full sparse success
-> only then may one lifetime-controller gate be registered
```

The environment requires one agent to hold a public anchor continuously while
the other completes a left-right-left-right shuttle sequence during the same
unbroken attempt. Either agent may become holder; the transition and reward are
swap-equivariant. The actor receives only its position, teammate-relative
position, and relative public-zone geometry. It does not receive holder
identity, shuttle stage, anchor streak, contacts, role labels, success, or
reward. The centralized critic may see the task state.

The only reward is shared `+1` on full simultaneous success. Every partial
event gives zero. Intrinsic, process, progress, contact, potential, and partial
rewards are exactly zero.

The learner is functionally ordinary recurrent MAPPO: constant individual and
team code zero, no high-policy decision or update, no process update, and no
intrinsic path. It trained for 320,000 environment steps with 16 spawn
environments, rollout 200, 100 outer/low updates, seed 39031, and CUDA. Final
stochastic evaluation used 256 registered paired reset seeds. A uniform-random
policy used the same resets and an independent fixed action RNG.

## Exact retry2 result

The first completed training run was `INVALID_R38_IMPLEMENTATION` only because
the analyzer evidence path omitted explicit zero high-row metrics and computed
constant-label entropy as approximately `-1e-12`. The training algorithm and
scientific thresholds were unchanged. Those wiring defects were fixed, the
fix passed focused tests and independent review, and the entire frozen 320K
contract was rerun from a fresh neutral zero-step checkpoint.

Retry2 result:

```text
status                  FAIL_R38_CTS_ACCESS
implementation_valid    true
M0                       PASS
M1 access                FAIL
M2 repeatability         FAIL

constant-code MAPPO, 256 episodes
  short duty             0 / 256 = 0
  long duty              2 / 256 = 0.0078125
  full success           0 / 256 = 0
  mean external reward   0

uniform random, 256 episodes
  short duty             0 / 256 = 0
  long duty              0 / 256 = 0
  full success           0 / 256 = 0
  mean external reward   0

paired MAPPO-minus-random percentile intervals
  short                  [0, 0, 0]
  long                   [0, 0.0078125, 0.01953125]
  full                   [0, 0, 0]

full successes by contiguous 64-reset MAPPO block
  [0, 0, 0, 0]
```

M0 records 100 low/outer updates, zero high updates, zero process updates, zero
high/process rows, no nonzero intrinsic field, valid reward and terminal
semantics, and exact paired reset order.

The registered valid-FAIL branch says to retire CTS without shaping, intrinsic
reward, budget, seed, threshold, observation, learner, high-policy, process, or
skill rescue. A PASS was required before any shared-fixed-k versus per-agent
lifetime comparison.

## Cross-program evidence that constrains the next route

R29--R34 already retired small variations of:

- online actor-density-ratio reward;
- observational fixed-window effect information reward;
- direct individual interventional effect policy gradient;
- exact high-level roster-complementarity table fitting;
- balanced hindsight mode relabeling and recurrent distillation.

Those gates were implementation-valid. They showed some action sensitivity,
forced capacity, or small fitted movement, but no material codebook-wide causal
separation and natural transport. R30 lifetime mechanics and skill supply did
not collapse in the relevant gates.

R35--R38 then tested the substrate rather than another skill mechanism:

- R35: constant-code MAPPO and reward-pure R30 both had zero Alice--Bob access.
- R36: exact episodic joint-cell novelty expanded coverage `3.855204x` but still
  produced zero collection/cycle access; that novelty family is retired.
- R37: exposing current task identity caused 10/64 collection episodes versus
  zero in the matched control, but cycle mean `0.01953125` missed the registered
  `0.05` reliability floor; Alice--Bob was retired.
- R38: a new role-free two-timescale sparse task passed M0 but produced no short
  or full success under ordinary recurrent MAPPO; CTS is retired.

The project must avoid converting repeated substrate failure into benchmark
hopping or hiding it with a task-specific auxiliary signal.

## Mutually exclusive route classes to adjudicate

### A. Return to S7-S1

Use the standing original-HMASD S7-S1 reference as the positive access anchor.
It reached high service coverage around 0.8M steps and late mean `0.9639`.
Stop demanding that a custom toy first validate ordinary MAPPO. Register the
smallest matched causal gate that can resume the actual HMASD/HA-CTSE research
question, while respecting that historical exposure differences make the
existing run reference-only.

Risk: slower experiments and a harder separation between environment access
and algorithm effect.

### B. Adopt one established public cooperative benchmark

Choose one benchmark with a published, reproducible ordinary MARL positive
baseline. Preserve its native observations, rewards, termination, and task
distribution. First reproduce the positive baseline; then test only one
environment-agnostic temporal/credit mechanism. Do not create another local
toy or modify reward to manufacture access.

Risk: repository integration cost and possible distance from the HMASD/S7
target. If selecting this route, name the exact benchmark, scenario, reference
implementation, baseline evidence, and minimal reproduction gate.

### C. Return to the existing reward-off forced-capacity substrate

Use the R27 evidence that forced skills can induce persistent conditional
behavior through H40, without requiring sparse task success. Propose one
genuinely new causal mechanism edge that is structurally different from the
retired R29--R34 action/effect/composition/distillation families. Only after
that mechanism passes may task efficacy be reconsidered.

Risk: another diagnostic that never transports. A valid proposal must explain
why the prior negative evidence supports this new edge and exactly what result
permanently abandons it.

The controller's current preference is to retire custom sparse-toy construction
and choose A or B, because they bring an external positive learning anchor.
Override that preference only with concrete repository-grounded reasoning.

## Prohibited responses

Do not:

- rescue R38 or R35--R37;
- propose another custom sparse benchmark as the next action;
- lower thresholds or expand steps/seeds to turn a failed gate into a pass;
- relabel RND, ICM, count novelty, task progress, or reward prediction as a new
  route without distinguishing it causally from retired evidence;
- restore R29--R34 through a new coefficient, target, window, optimizer scope,
  classifier, codebook label, or reward/value wrapper;
- treat the rare two long-duty completions as access success;
- infer that asynchronous lifetime or intrinsic reward failed in R38;
- ask for several experiments in parallel.

## Repository files to inspect

Read these files before deciding:

- `AGENTS.md`
- `memory/CURRENT_WORK.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/IMPLEMENTATION_PLAN.md`
- `memory/ExpRecord.md`
- `memory/LTM/R35_R38_SPARSE_ACCESS_FAILURE_REVIEW_20260715.md`
- `memory/LTM/R35_R37_SPARSE_ACCESS_FAILURE_REVIEW_20260715.md`
- `memory/LTM/R29_R33_EFFECT_COMPOSITION_FAILURE_REVIEW_20260714.md`
- `docs/external-review/gpt5_6_pro/20260715_r37_actor_visible_identity_access_result/RESPONSE_RAW.md`
- `docs/external-review/gpt5_6_pro/20260715_r37_actor_visible_identity_access_result/DISPOSITION.md`
- `docs/superpowers/plans/2026-07-15-r38-cts-access-gate.md`
- `envs/pettingzoo/cooperative_two_timescale_sparse.py`
- `ha_ctse_process/config_r38_two_timescale_sparse.py`
- `ha_ctse_process/train.py`
- `ha_ctse_process/standalone_agent.py`
- `scripts/run_r38_cts_access_local.ps1`
- `scripts/analyze_r38_cts_access.py`
- `logs/r38_cts_access_320k_20260715_140641_retry2/result/r38_cts_access.json`

## Required answer format

1. `R38 validity verdict`
2. `Reusable causal conclusion`
3. `Retire or retain the custom sparse-toy access program`
4. `Exactly one selected route: A, B, C, or one superior replacement`
5. `Why the other routes are rejected`
6. `One falsifiable causal edge`
7. `Lowest valid comparator/baseline level`
8. `Smallest evidence-bearing implementation and experiment`
9. `Exact abandonment gate and prohibited rescue changes`
10. `Strongest objection to your selected route and whether it changes the decision`

Return one decisive research route. Do not provide a summary-only response.
