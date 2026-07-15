# R35--R38 Sparse-Access Failure Review

Date: 2026-07-15

## Decision

R38 is a valid `FAIL_R38_CTS_ACCESS`. Retire
`cooperative_two_timescale_sparse` as an algorithm-comparison benchmark under
the registered seed, 320K-step ordinary recurrent MAPPO budget, observation,
dynamics, sparse reward, and access thresholds. Do not rescue it with shaping,
intrinsic reward, task hints, learner changes, more steps or seeds, or lower
thresholds.

The result does not test R30, skill discovery, asynchronous lifetime, or an
intrinsic mechanism. It establishes only that the new CTS substrate failed its
ordinary-policy access prerequisite. The PASS-only shared-fixed-k versus
per-agent-lifetime gate is therefore blocked.

R35--R38 also closes the current custom sparse-toy access program. A third
locally invented sparse benchmark would repeat benchmark construction without
positive evidence that this is the missing algorithmic edge. The next route
must instead be anchored either to a benchmark with existing positive learning
evidence or to a causal mechanism gate that does not require sparse success.

## Cross-Round Evidence

| Gate | Valid mechanism evidence | Access evidence | Reusable decision |
| --- | --- | --- | --- |
| R35 constant-code MAPPO vs reward-pure R30 | Both arms completed 320K steps and 250 low updates from one neutral initialization | Both had zero collection episodes and zero cycle success | No hierarchy comparison was interpretable on the original Alice--Bob substrate |
| R36 exact episodic joint-cell novelty vs constant control | The isolated novelty path expanded 625-cell coverage `3.855204x` | Both arms still had zero collections and zero cycle success | Undirected coarse state breadth is not a sufficient sparse-access carrier; this novelty family is retired |
| R37 actor-visible vs identity-masked task state | Capacity, initialization, critic, reward, and update exposure matched; actor-slot audit was exact | Visible identity produced 10/64 collection episodes and cycle mean `0.01953125`; masked produced zero, but the registered `0.05` cycle floor failed | Hidden task identity was a real bottleneck, but repairing it did not make Alice--Bob a reliable comparison gate |
| R38 ordinary constant-code recurrent MAPPO vs paired uniform random | M0 passed: 100 low updates, zero high/process updates, intrinsic fields all zero, 256 paired resets per policy, valid reward/terminal semantics | MAPPO short `0/256`, long `2/256`, full `0/256`; random was zero on all three; all four 64-reset MAPPO blocks had zero full success | The new swap-equivariant anchor/shuttle substrate is not an accessible ordinary-policy benchmark under its frozen contract |

## R38 Failure Classification

- Instrumentation and data quality: no identified defect. M0 passed and the
  retry used the exact registered contract after repairing only invalid
  evidence wiring from the first run.
- Optimization and capacity: unresolved at the general level. This one
  recurrent MAPPO contract did not access the task, but a single valid access
  gate cannot prove the task unlearnable or recurrent MAPPO generally
  incapable.
- Scientific failure: the registered implication failed:

  ```text
  simultaneous role-free anchor/shuttle duties
  -> ordinary recurrent MAPPO short and long access
  -/-> reliable full sparse success
  ```

- Claim boundary: no conclusion about skills, lifetime, hierarchy, HMASD,
  intrinsic reward, or S7 follows from R38.

## Baseline Matrix For The Post-R38 Decision

| Candidate substrate | Positive evidence already available | Blocking issue / constraint |
| --- | --- | --- |
| Retired 80-step Alice--Bob | R37 proved a positive identity-information effect and 10/64 collections | Registered access floor failed; no horizon, geometry, budget, reward, or learner rescue |
| Retired R38 CTS | Mechanics and measurement are valid; 2/256 long-duty completions show the state machine was reachable in rare cases | Zero short/full success and no repeatable access; no shaping, intrinsic, hint, budget, seed, threshold, or learner rescue |
| S7-S1 | Standing original-HMASD reference reaches high service coverage around 0.8M steps and late mean `0.9639` | Slower and not an ordinary-MAPPO access proof; any use must respect matched exposure and existing reference-only limits |
| Established public cooperative benchmark | Published ordinary-policy success can provide an external positive access anchor without another custom environment | No single benchmark and repository integration are yet selected; native observation/reward/termination must remain unchanged |
| Existing R27 forced-capacity substrate | Forced skills already show persistent conditional behavior through the registered H40 intervention | It is a reward-off causal mechanism substrate, not sparse-task efficacy; R29--R34 already retire action-ratio, observational-effect, direct IFEPG, roster fitting, and hindsight-distillation variants |
| A third custom sparse toy | None | Repeats the failed access-first construction loop and is not authorized |

## Reusable Negative Conclusions

1. Random or coarse state visitation can grow substantially without reaching a
   coordinated sparse event.
2. Making task identity observable can causally improve access without making
   the benchmark reliable enough for algorithm comparison.
3. A structurally elegant two-timescale task is not a usable research substrate
   until a non-hierarchical learner clears a predeclared access floor.
4. An access failure must not be hidden by an intrinsic reward, especially one
   reading benchmark targets, contacts, stages, distances, success predicates,
   or external reward.
5. R29--R34 and R35--R38 jointly rule out returning to small variations of the
   same effect-reward, codebook-fitting, novelty, or custom-toy routes.

## Open Decision

The next decision is not another implementation. External review must select
one and only one upstream route:

1. return to S7-S1 using the existing positive HMASD reference as the access
   anchor;
2. adopt one established public cooperative benchmark with a reproducible
   ordinary-policy positive baseline and native reward contract;
3. use the existing reward-off forced-capacity substrate for one genuinely new
   environment-agnostic causal mechanism edge that is structurally distinct
   from R29--R34.

The review must reject the other routes, define the lowest valid baseline
level, and give one minimum abandonment gate. Any proposed intrinsic signal
must have one benchmark-independent mathematical form and input contract and
must not consume task identities, objects, goals, contacts, phases, distances,
success predicates, or external reward.
