# Restart handoff

Updated: 2026-07-25. Branch `untied-k`.

Read `AGENTS.md`, then this file, then `docs/project/RESEARCH_GOAL.md`.

## Next action, exactly

**Build D7.2B: a standalone-lane config, then the event ledger, then run it.**

The `keep_prob` capture is committed (`e23e48f`) and the three gates that made
D7.2B unrunnable are unbundled and committed. Nothing is blocking.

```text
docs/research/designs/D7_KEEP_PROB_CAPTURE_SPEC.md   frozen spec
docs/research/designs/D7_R30_RENEWAL_DIAGNOSTIC.md   what D7 is, and the pass conditions
tests/ha_ctse_process_d7_toy_executor_gate_test.py   what the unbundling may and may not do
```

The config does not exist yet. `config_r39_native_hmasd_toy.py` is the *other*
lane — `algorithm=hmasd_original`, `r39_native_toy_*` flags — and is not it. The
standalone lane is driven off a config module read by `ha_ctse_process/train.py`,
and D7.2B needs: `high_controller=r30_fixed_clock_ar_edit`,
`r39_native_categorical_edit=False` (learned keep is the carrier),
`r39_toy_fixed_skill_primitives=True` with `axis4_xy_v1`, `n_z=4`, 2D continuous
actions, `scenario=two_timescale_role_free_actions`, `skill_interval=r39_toy_k0=5`,
`device=cpu`.

Pass conditions A/B/C are fixed in the design and **must not be renegotiated after
seeing output**.

**Do not re-escalate the executor gate.** It is ruled, in the design doc and in
`AGENTS.md`, *Implementing a ruling is not making one*.

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
