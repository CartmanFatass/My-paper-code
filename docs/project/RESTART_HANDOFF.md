# Restart handoff

Updated: 2026-07-25. Branch `untied-k`.

Read `AGENTS.md`, then this file, then `docs/project/RESEARCH_GOAL.md`.

## Next action, exactly

**Finish and commit the `keep_prob` capture, then build D7.2B.**

There is **uncommitted work in the tree** — the `keep_prob` diff. It is audited
(`semantics=APPROVE`) and an implementer is closing three test gaps. Do not
commit until those land and you have re-run the checks yourself.

```text
docs/research/designs/D7_KEEP_PROB_CAPTURE_SPEC.md   frozen spec
docs/research/designs/D7_R30_RENEWAL_DIAGNOSTIC.md   what D7 is now
```

Then D7.2B, the toy positive control — task #14, which carries the binding
constraints and the pass conditions.

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
- `tests/ha_ctse_process_standalone_test.py::test_process_update_injects_reward_into_matching_rollout_agent`
  is **flaky** (~2 failures in 3, at HEAD too). It briefly read as a regression
  from the D7 diff. Task #15.
- Everything except the `keep_prob` diff is committed and pushed to
  `origin/untied-k`.
