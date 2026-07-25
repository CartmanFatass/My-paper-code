# Restart handoff

Updated: 2026-07-25. Branch `untied-k`.

Read `AGENTS.md`, then this file, then `docs/project/RESEARCH_GOAL.md`.

## Next action, exactly

**Wait on the D7.2B competence run, then audit its checkpoint.**

```text
run    logs/nonformal_d7_2b_toy_competence_20260725_0931948_pm1
audit  C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/audit_d7_2b_toy_positive_control.py \
         --checkpoint <run>/standalone_process_core_final.pt --out <run>/audit
```

1,000 updates, 3 epochs, lr 1e-3 — 3,000 high-level optimizer steps against the
200 the screen had. **Read condition A first.** If A passes, B and C are the
scientific readings and their thresholds are frozen. If A is still flat, the
policy has had a fair budget and the next candidate is credit, not budget — that
is a scientific direction question and belongs to a Pro round, not to another
tuning pass.

```text
docs/research/designs/D7_2B_TOY_POSITIVE_CONTROL_REALIZATION.md   the frozen realization
docs/research/designs/D7_R30_RENEWAL_DIAGNOSTIC.md               D7, and pass conditions A/B/C
docs/research/designs/D0_CARRIER_AND_ESTIMAND.md                 estimands, clocks, normalization
```

Pass conditions A/B/C **must not be renegotiated after seeing output**. Optimizer
budget is not a pass condition and may be raised; thresholds may not.

**Do not re-escalate the four unbundled gates.** They are ruled, in the design doc
and in `AGENTS.md`, *Implementing a ruling is not making one*. Do not re-pin
multi-epoch high PPO either — that pin was mine, it was measured to be blocking
competence rather than protecting credit, and the protection that matters is
structural: `block_return` requires `force_refresh_every_check`, where KEEP is not
a decision.

## What is settled, so it is not re-litigated

- **No-state-access control** — complete, `NO_ACCESS` by derivation. Team reward
  plateaued at `0.475`; reward is `0.5*(slow+fast)`, so the matches sum to `0.95`
  where A needs `1.5`.
- **Direct-state screen** — complete and flat, `0.443 -> 0.449` over 200 updates.
  The policy never left its initialization: at update 150 `keep_prob` was `0.599`
  against a `0.6` init and skill entropy `1.096` against a `ln 3 = 1.0986`
  maximum, with `high_grad_norm` between `0.26` and `0.48`. Nonzero gradient, no
  behaviour. Not a credit or information failure.
- **`B_H`** — measured before the audit, `B_30 = 10.0`, `B_5 = 1.875`. Must be
  averaged over windows starting at every check boundary; a step-0 window gives
  `B_5 = 0` exactly and divides condition B by zero.
- **State liveness** — verified in the skill logits. Do not probe it by comparing
  realized tokens: `keep_head.weight` is zero-initialized, so both agents
  deterministically KEEP at entry and tokens look identical either way.

## Where D7 stands

The 2026-07-25 ruling (`docs/external-review/rounds/20260725_d7_design_and_prior_art/21_PRO_OPEN_RAW.md`)
restructured D7 from one paired run into a staged diagnostic, and **its preflight
is already settled, negatively**:

- **No qualified R30 checkpoint exists** — 3 `.pt` files in this repo, all from an
  unrelated contract exercise; the external checkpoint `r31`–`r34` referenced is
  gone; the external `C:\project\HMASD` tree holds **zero** `.pt` files. The toy
  run cited in `ExpRecord.md` is not on disk either. Recorded results outlived
  their artifacts.
- So the evaluation-only route (D7.2A) is **closed**. The route is **D7.2B**, the
  toy positive control, which needs compute and a **new config** — the existing
  `config_r39_native_hmasd_toy.py` runs native-categorical edit, where KEEP is not
  a decision.

Pass conditions are fixed in the design and **must not be renegotiated after
seeing output**.

## What the ruling changed that is easy to get wrong

- **Two estimands, not one.** `U_opp` (does the source contain a valuable
  renewal — max over non-incumbent skills, **split-sample** or it is optimistic)
  versus `U_pi` (can the current SET policy exploit it). Collapsing them hides
  whether a null means "no heterogeneity" or "no competence".
- **`Δ` = one check interval**; `H` = one slow period (30 steps) on the toy.
- Later agents in the same check **must react** to the changed prefix. Holding
  them fixed estimates a direct effect the deployed policy never exhibits.
- **D8-frozen is dead**, D8-coadaptive lives. "Primitive skill policy unchanged"
  means unchanged architecture, **not frozen weights** — frozen weights is R44,
  which already collapsed to full-sync renewal with a live gradient path.
- **Same-label renewal is structurally impossible** under learned-keep; the
  incumbent is masked out of the SET distribution, so a reported zero is a
  tautology. Record `NOT_APPLICABLE_STRUCTURALLY_EXCLUDED`.
- **No best-fixed sweep in D7.** Deferred to whichever arm makes the paper claim.

## Traps found by reading, which will bite again

- Lifetime from **segment records is fragmented** by update cadence, not policy.
  Measure from `skill_age` at genuine SET. Latent, not active — `process_update`
  empties its list under R30 — so the R30 lane has no lifetime metric at all, and
  the obvious way to add one is the wrong way.
- Only **one of `act_sequence`'s branches is a renewal decision**. Under
  native-categorical, KEEP is a post-hoc label on a skill collision. Under
  `not active` there is no incumbent — and that fires on **every agent's first
  check of every episode**.
- **`skill_age` never advances during evaluation rollouts** (`record_environment_step`
  is never called there), so an age-conditioned hazard on the eval host would
  condition on a frozen number.
- `export_substrate_gate.py` is a **host, not a metric path** — wrong unit, and its
  role fields carry named relay/service semantics the ruling forbids as primary.

## Authorization

**Full and unattended.** Never return to the user for resource or compute
permission. Compute is authorized; only timing is gated:

```text
scripts/check_compute_free.ps1  ->  COMPUTE_FREE run | COMPUTE_BUSY wait 1h, recheck
```

The loop is a **backstop, not a scheduler** — if there is a next step and it is
yours, take it now. See `CLAUDE.md`, "The loop does not stop".

## Constraints that bite

- `aggressive` is not ours. Never push to it; excluded from discussion.
- **Children never run Git — at all**, not merely writes.
- Contract tests are pinned allow-lists; adding or removing an agent or skill
  needs the test edited in the same commit.
- Transport is `project_manager_direct`; `hmasd-review-monitor` only reports that
  generation stopped. **One tab per conversation** — if it wedges, *replace* it,
  closing the old one first.
- The flaky `test_process_update_injects_reward_into_matching_rollout_agent` is
  **repaired**, and the cause was not the missing seed. `process_reward_injection`
  defaults to `"none"`, so the process reward the test is named for never reached
  the rollout; the only thing making the assertion pass was a per-step
  skill-effect micro reward, clipped at zero, whose sign a randomly initialized
  predictor decided. `!= 0.0` was a coin flip per step. It now injects explicitly
  and asserts per-step routing. 6/6 deterministic.
- Everything is committed and pushed to `origin/untied-k`.
- The harness task list does **not** survive a session. The prior session's tasks
  #14 and #15 were gone on resume; the repository record is the only continuity.
