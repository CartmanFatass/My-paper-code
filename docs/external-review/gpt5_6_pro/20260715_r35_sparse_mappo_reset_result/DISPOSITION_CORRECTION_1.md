# Disposition: R35 Correction 1

- Source model: GPT-5.6 Pro / ChatGPT web `Pro`
- Date: 2026-07-15
- Related claim: R35 validity, no-access interpretation, and the single next
  non-skill causal edge
- Raw evidence: `RESPONSE_CORRECTION_1_RAW.md`
- Disposition: **ACCEPT VERDICT AND CAUSAL EDGE; MODIFY THE R36 CONTRACT**

## Accepted

1. `VALID_NO_ACCESS_R35_UNRESOLVED` is the correct R35 verdict. Zero task
   access precedes and blocks any MAPPO/R30 or hierarchy comparison.
2. The reusable result is limited to the tested initialization, single seed,
   320K budget, and final evaluation: neither trained arm entered a measurable
   task-access region.
3. R29--R34, OCSF, CBF, and TMPF remain closed. R35 is not rerun or expanded.
4. R36-AEM supplies one structurally new edge:

   ```text
   task-generic joint-position novelty
   -> broader reachable-state visitation
   -> first sparse collection access
   ```

5. The trained comparator is the same constant-code recurrent MAPPO substrate;
   R30 is diagnostic-only until access exists.

## Required modifications

The response leaves several experiment-defining quantities incomplete or
inconsistent. They are fixed before implementation rather than sent back for a
second algorithm menu:

1. **No hash:** use a direct arithmetic index into the fixed 625-cell joint
   position table. This respects the project-wide no-hash rule and has identical
   occupancy semantics.
2. **Exact novelty:** for environment `e`, before incrementing its per-episode
   cell count,

   ```text
   b_e,t = 1 / (80 * sqrt(N_e,t(c_e,t) + 1))
   r_train_e,t = r_env_e,t + b_e,t
   ```

   Counts reset only on that environment's episode boundary. The maximum
   possible novelty return is one when all 80 states are first visits. There is
   no coefficient sweep, learned predictor, potential function, or task field.
3. **Information/gradient boundary:** cell counts use only both agents'
   normalized positions. The count and bonus are detached collector scalars,
   are not actor/critic inputs, and are shared across the two agents exactly as
   the external reward is. They enter low GAE once. Only the existing
   constant-code actor and centralized critic update.
4. **Matched budget:** retain R35's actual topology instead of the response's
   unrelated `rollout=500`, `epochs=15`, and minibatch 32: seed `37031`, CUDA,
   16 envs per arm, rollout 80, 320,000 steps, 250 low updates, five low PPO
   epochs, recurrent sequence length 10/batch 64, and 64 paired stochastic
   80-step evaluation episodes.
5. **Causal gate:** absolute access is necessary but not sufficient. Require
   AEM to reach both the unchanged R35 access floor (cycle mean `>=0.05` and at
   least 10/64 collection episodes) and a paired collection-episode advantage
   of at least `0.10` with 95% bootstrap lower bound above zero. Require the
   proposed coverage carrier (`coverage_AEM / coverage_control >=1.50`, paired
   difference CI lower above zero). Zero-cycle `<0.90` is retained as a
   redundant readable safety check.
6. **Branches:** invalid implementation repairs only its concrete defect;
   `PASS_R36_AEM_ACCESS` authorizes one ordinary sparse-training comparison;
   `FAIL_M1_RETIRE_R36_AEM` retires this exact episodic joint-count bonus when
   access is absent or not causally better; `FAIL_M2_ACCESS_WITHOUT_CARRIER`
   records access without the registered visitation carrier and does not
   promote the mechanism; an operational crash retries only the failed path.

This modification preserves the Pro-selected algorithmic idea while removing
undefined scale, accidental budget expansion, a non-matched decision rule, and
the prohibited hash representation.
