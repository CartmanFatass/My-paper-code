# Owner intervention workflow plan (2026-09-04)

Written by Claude Code (Fable 5.1) at the owner's request ("我们指定一个详细的计划，我们调整一下 codex 的
工作流"), after the owner's question on how to intervene while keeping the loop fully automatic.
The owner answered four alignment questions at 07:10 PDT; those answers are the decision record
`docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md` (`OWNER_DIRECT`).
This document is the plan behind that record: the principle, the owner's answers, every file
changed and why, the operating rhythm, what Codex does first, and what is still open. Companion:
`MARL_EXPLORATION_GUIDANCE_20260904.md` (the five principles).

## 0. Principle

Do not intervene in the loop's execution; intervene in its selection pressure and its output
format. Selection pressure is set once as numbers and applies to every direction at once. Output
format means the loop writes what the owner needs, in the owner's language, to append-only
surfaces, and reads the owner's replies at clean boundaries. Nothing waits on the owner.

## 1. The owner's answers

| Question | Answer |
| --- | --- |
| Owner brief scope and language | every valid result, Chinese |
| Entry triage for new cards | soft veto through the digest, launch never blocked |
| Prediction wait | none; one request per ladder, scored if filled, `not taken` otherwise |
| Policy parameters | initially MEI 5%/25% and recast budget one; **revised 07:35 PDT after Codex Root's review**: no repository-wide MEI (each card declares its own), headroom is a diagnostic and sequencing input only, recast budget one kept as lowest sequencing priority |
| Hard stops (asked 07:17 PDT) | none added; every surface is append-only and the loop never waits; the pre-existing owner ratification of Portfolio-tier actions is unchanged |

## 2. What changes, file by file

All edits below are made and committed under the decision record. They are excluded from the
unattended delegation (`AGENTS.md` §4.3) and were made with the owner present.

| File | Change | Why |
| --- | --- | --- |
| `AGENTS.md` §2 | new **Investment policy** paragraph: headroom floor, closure share, recast budget, "not a §11.4 gate" | policy numbers live in the runtime-neutral authority so every runtime applies them |
| `AGENTS.md` §4.4 | ledger row gains `kind` (`technical`/`selection`) and an owner flag (`none`, `close-call`, `critic-dissent`, `second-recast`, `portfolio`) | today's ledger has 30+ rows, most technical; the owner needs a filter, not more rows |
| `AGENTS.md` §4.5 | new **Owner surfaces** item: digest, prediction queue, briefs; loop reads replies at clean boundaries | the single asynchronous interface |
| evidence spec §11.7 | headroom floor, closure share, three readings on the card, baseline set location, binding-structure line; open ladders continue | the scientific reading rule for B results, written where DMs already read |
| `.codex/agents/hmasd-direction-manager.toml` | two new sections: card lines and investment policy; owner surfaces (ledger columns, digest rows, prediction row per ladder, Chinese brief per valid result, recast budget behaviour) | the DM is the agent that writes cards, intakes and ledger rows |
| `.codex/agents/hmasd-research-critic.toml` | ends every return with `MATERIAL_DISSENT: yes\|no` | gives the DM a machine-readable trigger for the `critic-dissent` flag |
| `.agents/skills/hmasd-portfolio-task/SKILL.md` | new **Investment policy** section: the three numbers as investment rules, usage-per-valid-result column, Portfolio proposals as digest rows | Root's comparisons use the same currency the owner sees |
| `docs/research/portfolio/owner/README.md` | owner's daily routine in Chinese; row schemas for digest, predictions, briefs; what the loop reads back | one place that both the owner and the agents read |
| `docs/research/portfolio/owner/PREDICTIONS.md` | empty queue with schema | first surface ready before the first ladder freezes |
| `docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md` | the decision record | provenance for all of the above |

Not changed: `PORTFOLIO.md` (Root fills the usage column at its next snapshot; this session did
not edit a file a running Codex Root owns), the prompt-author and transport skills (no packet
field changes), `CLAUDE.md`.

## 3. How a decision now flows

1. **A new card.** DM writes the claim sentence and binding-structure line, the headroom on record
   and the three readings, freezes the card, appends a `new-card` digest row and, if this is a
   ladder's first card, a `PREDICTIONS.md` row. Launch proceeds under §11.4 as before.
2. **An object-tier decision.** DM lists options, selects the recommendation, writes the ledger
   row with `kind` and a flag. Flagged rows are copied to the digest. Unflagged rows are not.
3. **A critic return.** `MATERIAL_DISSENT: yes` that the DM overrules becomes a `critic-dissent`
   row in both ledger and digest.
4. **A valid result.** DM writes the English intake, the Chinese brief, scores the prediction row,
   reports closure share against headroom, appends a `brief` digest row.
5. **A Convergence `RECAST`.** First one executes and records `recasts: 1`. Second one also
   executes, records `recasts: 2`, drops the direction to the lowest sequencing priority among
   ACTIVE directions, and writes a `second-recast` digest row. The owner may PARK it there.
6. **A Portfolio proposal.** Root records it and writes a `portfolio` digest row. Owner ratifies
   or refuses in the `owner` cell.
7. **Every clean boundary.** DM and Root read the ledger `owner` column and every digest and
   prediction `owner` cell. A filled cell is applied.

## 4. The owner's rhythm

| Cadence | Time | What |
| --- | --- | --- |
| daily | 15 min | open today's digest; fill `owner` cells only where you disagree; skim `new-card` rows and veto the ones with structure `none` or a claim you cannot restate |
| weekly | 1 h | read the briefs of the head directions; fill open prediction rows for ladders you care about; answer `portfolio` and `second-recast` rows |
| monthly | half day | read the usage-per-valid-result column; ratify the ACTIVE/PARK set; re-order the investment wave |

Expected owner load: two to three hours a week. Loop throughput unchanged.

## 5. What Codex does first (under the standing delegation)

1. Load the updated configuration in new tasks; running tasks finish under the old text.
2. From `2026-09-05` write ledger rows in the new column order.
3. For every ACTIVE direction whose next card is a new object family, check the headroom record
   on its host. Where none exists, the next object is the A/RECON headroom measurement
   (guidance draft action A1). ACVC R01 and SCDMP A01 already are that object.
4. Build the corridor and scenario-1 baseline sets (action A2) from E2's D0 sweep and E0's
   exposure probes, under `docs/research/baselines/` and `experiments/baselines/`.
5. Root adds the usage-per-valid-result column to `PORTFOLIO.md` at its next snapshot.
6. Root writes the first `portfolio` digest rows for the items still open in §6.

## 6. Still open for the owner

From the guidance draft, unchanged by this plan: the ACTIVE/PARK disposition of its §4 (five
ACTIVE, UCOPE HOLD, three conditional, rest PARK), the two fusion questions, and the UCOPE HOLD.
Root will surface them as `portfolio` rows in the first digest; the owner answers there.

## 7. Verification done in this session

- The two edited TOML files parse (`tomllib`).
- `tests/skills` run after the edits; result recorded in the commit message.
- No frozen object, live run, comparator, budget, RNG or claim meaning was touched.

## 8. Addendum 2026-09-04 07:35 PDT: revision after Codex Root's review

Codex Root reviewed the guidance draft and advised against approving it as one package. The owner
adopted its stance with two refinements from this session (headroom stays a mandatory proposal
field and a compute-sequencing tie-breaker; recast budget one stays as sequencing priority). The
committed authority text was revised accordingly: `AGENTS.md` §2 (investment fields, no numbers,
sequencing never a lifecycle disposition), evidence spec §11.7 (headroom record, declared MEI,
reading narrative, baseline set as reusable evidence, binding structure as classification with
`systems / information flow` excluding nothing), the DM definition, and the Portfolio skill (two
usage measures; share assets, do not fuse). The nine-point stance is recorded in the decision
record. §5 items 3 and 4 of this plan are read under that stance: the headroom census is
sequencing, not a precondition, and a baseline that must be trained is a declared B. §6 is
superseded: no batch PARK, no fusion now, UCOPE stays ACTIVE with competence-first ordering.
