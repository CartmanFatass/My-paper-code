# Owner intervention surfaces and investment policy

Date: 2026-09-04 (07:06–07:20 PDT)

Provenance: `OWNER_DIRECT`

## Decision

The owner keeps the fully automatic research loop and intervenes only through append-only
surfaces the loop writes and reads, never through a wait. Four choices were taken with the owner
present, in reply to the alignment draft
`docs/Claude_docs/plans/MARL_EXPLORATION_GUIDANCE_20260904.md` and the plan
`docs/Claude_docs/plans/OWNER_INTERVENTION_WORKFLOW_PLAN_20260904.md`:

1. **Owner brief.** Every valid result gets a one-page brief in Chinese, written by the DM at
   intake next to the English intake document, at
   `docs/research/portfolio/owner/briefs/<direction>/<YYYY-MM-DD>_<object>.md`.
2. **Entry triage is a soft veto.** New science cards launch without waiting. Each card's first two
   lines (one-sentence claim, binding MARL structure) are copied into the daily digest
   `docs/research/portfolio/owner/digest/<YYYY-MM-DD>.md`; the owner vetoes asynchronously by
   filling the row's `owner` cell, and the loop applies it at the next clean boundary.
3. **Predictions never block.** One prediction request per ladder (not per invocation) is appended
   to `docs/research/portfolio/owner/PREDICTIONS.md` when the ladder's first card is frozen.
   Launch never waits for it. At intake the DM scores whatever the owner cell holds and records
   `not taken` otherwise.
4. **Policy parameters.** Minimum effect of interest: headroom floor 5% of the tuned baseline
   return on the host before a mechanism B family is opened; closure share 25% of the recorded
   headroom for a positive B signal. Recast budget: one per direction; a second Convergence
   `RECAST` still executes but drops the direction to the lowest sequencing priority among ACTIVE
   directions and is flagged `second-recast` in the digest, where the owner may PARK it.
5. **No hard stops were added** (owner, 07:17 PDT: "我希望保持软介入的方式，硬门限可能会导致无人值守长期
   停摆"). Every surface above is append-only and the loop never waits on it. The only
   pre-existing wait, owner ratification of Portfolio-tier actions, is unchanged.

Supporting changes: the audit ledger row gains `kind` (`technical` / `selection`) and an owner
flag (`none`, `close-call`, `critic-dissent`, `second-recast`, `portfolio`); the critic ends every
return with `MATERIAL_DISSENT: yes|no`; the Portfolio skill records usage per valid result as a
column and treats the two MEI numbers and the recast budget as investment policy.

## Revision after Codex Root's review (07:22–07:35 PDT, `OWNER_DIRECT`)

Codex Root reviewed the guidance draft and recommended not approving it as one package, because
it mixed diagnostic method with Portfolio policy that would narrow the research scope. The owner
adopted the following stance, and item 4 above is superseded by it:

1. Headroom is a diagnostic and a sequencing input, never an investment threshold. Computing it
   from existing results is A/RECON; training or tuning a baseline for it is a declared B.
2. No repository-wide MEI. Each card declares its own (absolute, relative, or both) with the DM's
   reason; it informs Portfolio comparison and never rewrites a card's result branches.
3. All ACTIVE directions continue in parallel; there is no batch PARK and sequencing never becomes
   a lifecycle disposition. The owner does not limit the direction count on the Codex loop.
4. No fusion now; directions on one host share baseline sets and evidence interfaces.
5. UCOPE stays `ACTIVE` with the object order competent baseline, then headroom, then mechanism.
6. FSD and VNFC prepare a direction-level multi-UAV proposal after E3 / R02; no B is
   pre-authorized.
7. Usage per valid result is recorded in two measures (the valid result's own compute; total
   accepted-attempt compute divided by valid results), with node, device and missing values kept.
8. Card fields are descriptive: binding MARL structure (or `systems / information flow`, which
   excludes nothing) and a reading narrative; no numeric gate.
9. Recast budget one remains, as lowest sequencing priority only.

Codex Root will form the persistent `portfolio:cross_direction` Pro packet from this stance and
return a formal Portfolio proposal for the owner's ratification; `PORTFOLIO.md` is not changed by
this record.

## Files changed under this decision

`AGENTS.md` §2 and §4; `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` §11.7;
`.codex/agents/hmasd-direction-manager.toml`; `.codex/agents/hmasd-research-critic.toml`;
`.agents/skills/hmasd-portfolio-task/SKILL.md`; new `docs/research/portfolio/owner/`
(`README.md`, `PREDICTIONS.md`). These edits are excluded from the unattended delegation
(`AGENTS.md` §4.3) and were made with the owner present at the owner's instruction.

## Not decided here

The ACTIVE/PARK disposition of §4 of the guidance draft, the two fusion questions
(roster_consistent_latent_exploration into VNFC; vsp_03 into FSD E4), and the UCOPE HOLD remain
open Portfolio items awaiting the owner. Ladders already open on 2026-09-04 continue unchanged.

## Rollout

New Codex tasks load the updated project configuration; running tasks finish under the old text.
The ledger format applies from the next daily file (`2026-09-05.md`); today's file keeps its
columns. The first digest file is created by whichever agent writes the first row.
