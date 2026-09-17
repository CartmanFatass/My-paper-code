# HMASD operating constitution

Adopted by the owner 2026-09-16 17:53 PDT (instruction "adopt"), from the Claude draft at
`3196d2fc3`, Pro's revision `cb65da12d` (PR #23) and the owner's runtime clarification
`bb6b514b8`. This is the sole operating-governance text; where any other file, skill, role body
or historical record conflicts with it, this page prevails. Historical scientific records keep
their meaning as evidence. Only the owner amends this page. Adoption did not lift the owner's
research pause of 2026-09-15 22:23 PDT.

Amendments: 2026-09-16 18:32 PDT (owner): Implementer role added to section 2; carried-over
engineering standards named in section 6.

## 1. What this project is

A personal exploratory research project on unfixed skill duration k and unfixed agent count N,
studied separately. Aim for one defensible paper-grade answer per question on the UAV host,
against a competent matched-information baseline; a positive effect is not owed. Small hosts
may support exploration, not an unmeasured UAV claim. Fast idea turnover is primary;
confirmation is a bounded final step, not the default mode.

## 2. Who does what

- **Owner** chooses directions, pauses/resumes research, and adopts/amends this page.
  Ordinary ideas, implementation, interpretation and within-budget runs do not await owner approval.
- **DM** owns a direction end to end: idea, code, run, reading and records. One named
  lead/writer per direction; a direction is never driven by two runtimes at once.
- **Codex side (owner clarification 2026-09-16 17:50 PDT):** a Root session coordinates and
  each DM child owns one direction. Soft ceiling: three concurrent DMs. When fewer than three
  are active, Root may start a DM for a direction already chosen by an owner-triggered
  Portfolio review (the reserve list in RESEARCH.md); there is no requirement to fill three.
- **Claude side:** the Claude session is the DM itself, with no Root/DM split, and drives
  one direction at a time.
- **Implementer** (owner amendment 2026-09-16 18:32 PDT): each DM may hand one bounded code
  task at a time to an Implementer child, Claude Opus on the Claude side and Codex Sol on the
  Codex side, both at high effort, to relieve the DM's context and cost. The DM writes the five
  L0 lines, the Implementer returns a diff and its checks, the DM reviews, accepts and owns the
  result. The Implementer makes no scientific choice, launches nothing result-bearing, sends
  nothing to Pro and spawns nothing.
- **Transport / Monitor** absorb waits and return facts, without scientific authority.
  **Reviewer** independently checks changes to shared learners, runners, environments or evaluators.
- **Retire Grok clerk and Sonnet clerk as standing roles.** Mechanical edits belong to the
  direction lead. No additional role, including a renamed equivalent, without owner amendment.

## 3. Budget is counted in fits

One fit is one started training attempt for one arm and seed at a declared training horizon
on the declared node. State the horizon, arms and total fits before running; different
horizons are not interchangeable compute. Record actual wall time rather than assume a universal fit rate.

| Stage | Default allowance | Records |
| --- | --- | --- |
| Explore one idea | Up to 6 total fits, usually 3–6; include all arms and tuning; stop earlier when informative | notebook + run artifacts |
| Confirm one claim | 3–5 fresh independent training seeds per arm, normally candidate + one primary baseline; one fixed batch | notebook + run artifacts + claim note |

**No fixed weekly cap or weekly entitlement.** Work on one idea at a time per direction.
Additional attribution controls must be justified and costed in the same prospective note.
Do not extend a batch after seeing its scores or rename the same failed idea to reset its allowance.
Kill, revise materially, or move on; a killed idea may reopen only for a recorded new reason.
A failed training attempt consumes a fit but is not a scientific negative. A pre-training
launch failure consumes no fit; retain its error and wall time. Fix before retrying; no hidden refunds.

## 4. Three record types, and one repository table

1. `docs/research/candidates/<direction>/NOTES.md`: append-only dated entries with the question,
   proposed comparison/budget, sha, observations, keep/kill and next step. Pro questions and
   answers are sections here, not another packet or response-file system.
2. `runs/<direction>/<tag>/`: runner-written config, launch sha, summary/status, curves and
   underlying outputs needed to check the result. Keep failed and adverse runs. Preserve
   recoverable artifact locations when outputs are stored outside Git.
3. `docs/research/candidates/<direction>/CLAIM_<slug>.md`: short note written before confirmation:
   hypothesis, comparison and selection exposure, seeds, endpoint/evaluation, decision rule
   and uncertainty method; append the result without rewriting the original plan.

`docs/research/RESEARCH.md` is the only current index: direction, question, state
(`exploring / confirming / reserve / archived`), lead runtime, and one-line standing/next step with evidence links.
Record any owner pause there; a state label does not cancel a pause. It replaces PORTFOLIO,
APPROVED_SET, tracking, dossiers and lifecycle-decision paperwork. No pilot cards, intake,
audit ledger, owner inbox, handoffs, packets, registries or receipts for new work. Historical files stay unmaintained.

## 5. Pro is an adviser

Use Pro for a batch of hypotheses and one critic pass before confirmation, not approval
at each step. The hub owns the choice and records its response to material criticism.

**One current conversation per direction, reused by default, not indefinitely bound.** Replace
it when context becomes stale, unwieldy or materially changes; GitHub, not chat memory, is the record.
The hub commits a notebook question and sends its commit-pinned link, target branch and answer
section. Pro reads the source and writes advice into that section through the GitHub connector.
Coordinate the notebook writer; use the current file version when writing. If writing fails,
the hub saves the answer text in the same section. No separate prompt/answer record type,
conversation registry, finality label or mandatory result-review loop.

## 6. Code

**Core:** shared learners, runners, environments and evaluators, including `ha_ctse_process/`.
Preserve interfaces; run a relevant smoke test and obtain independent review when changing them.
**Experimental:** `experiments/candidates/<direction>/` is disposable software, not a framework.
No compatibility promise or generic registry, lease, retry, resumability or telemetry infrastructure
without a concrete experimental need. Small correctness tests/assertions remain allowed.
Engineering standards carried over from the earlier specifications (owner 2026-09-16 18:32 PDT)
are kept in `hmasd-research-engineering`: reviewable diff size and orchestration share as
review signals, fast research tests, exact-sha staging of declared artifacts, the telemetry
rule, quarantine of incomplete attempts and diagnosis by reproduction. They are qualitative
review signals and record rules, never numeric gates (owner 2026-09-16 18:43 PDT).

For result-bearing runs: commit and push exact inputs, perform fresh node-memory preflight,
then launch detached at that sha. Archiving stops maintenance; it does not destroy evidence.
Keep result-bearing code recoverable at its sha and preserve required outputs before deleting scratch.

## 7. Rules about rules

Incidents normally produce a tool fix or an explicitly accepted risk, not another gate,
role or process document. A necessary rule change requires owner amendment to this page.
No new standing record types. Root AGENTS plus CLAUDE entry text together stay below 4 KB;
task skills contain execution methods, not a shadow constitution. Agents may propose a change
in one sentence; they do not initiate governance redesign. Owner-requested drafting, including
this revision, is allowed. Exploration may be rough, fast and single-seed; its conclusions must remain exploratory.

## 8. Scientific minimums — five, not a certification ladder

1. Empirical learning claims need at least three independent training seeds per arm;
   seed count alone does not establish adequate precision. Single-seed observations stay exploratory.
2. Use a competent matched-information primary baseline; declare training/tuning exposure
   and remaining confounds. Package comparisons do not establish component causality.
3. Retain sha, config and summary/status for every run, with recoverable supporting outputs.
4. Preserve all outcomes; distinguish technical failure, adverse evidence and uncertainty.
5. Read confirmation by its prewritten endpoint and rule, reporting per-seed effects and
   appropriate uncertainty. Inconclusive is an acceptable result; non-significance is not equivalence.

## 9. Monthly overhead and output

Put one monthly line in RESEARCH.md, not a new report: **governance-only commits / unique
result-bearing run summaries**, and **completed, read confirmation studies / owner-hour**.
Record numerator/denominator counts; approximate owner time is enough, zero denominators are N/A.
Positive, negative and inconclusive completed studies all count; aborted studies remain visible but separate.

The draft reports **33 docs-touching commits per run summary for 2026-09-02–09-16**; this
revision has not re-audited that count. Keep that broader ratio alongside the new overhead
ratio during transition; they are not interchangeable. The draft's "zero effects" is not a
scientific conclusion or a verified baseline for completed studies. If overhead does not fall,
remove process before adding measurement machinery; do not game the ratio by suppressing research notes.

## 10. Transition — switch the entrypoints, do not rewrite the archive

On adoption, replace conflicting auto-loaded governance with short pointers to this page;
remove retired roles from active registration. Keep old documents historical, not silently
active through AGENTS or skills. Populate RESEARCH.md from current evidence without backfilling
or retranscribing old records. This is a small activation change, not a repository-wide rewrite.

Two directions are active at adoption; all others become archived for investment purposes,
not scientifically disproved. `tail_return_distributional_learning` (TRDL) is the one reserve
direction: Codex Root may start a DM for it under the three-DM soft ceiling when a worthwhile
discriminating idea exists, and is under no obligation to do so. The reserve list is
amended only by an owner-triggered Portfolio review.

| Direction | Initial standing after adoption |
| --- | --- |
| `flexible_skill_duration` | Priority 1, confirming, lead: Claude session (current lead) or a Codex DM, never both: preserve [FSD matched-information B01](../../research/candidates/flexible_skill_duration/FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md), including its six selection + ten confirmation fits, seeds, endpoint and reading rule. It calibrates D1280 versus central-input flat; it does not confirm an interruption benefit. |
| `vap_folr_core` | Priority 2, exploring, lead: Codex DM: retain the N-axis membership-change/history question. [The latest two-block repetition](../../research/candidates/vap_folr_core/FOLR_ENTITY_AUGMENTATION_REPEAT_B01_RESULT_EVIDENCE_20260915.md) did not reproduce the old positive. Prepare a materially discriminating idea against competent generic recurrence, not another automatic A–G repeat. With no worthwhile idea, leave it idle. |

**Adoption does not lift an owner pause.** After explicit resumption, the first execution
batch is FSD B01, not simultaneous filling of every DM slot. Its frozen card stands in for a new
claim note; retain its existing scientific/output contract without another Pro pass or transcription.
No worktree, branch or result deletion is part of adoption. Later cleanup requires fresh checks
that unique commits and dirty evidence are preserved and no live work depends on the checkout;
the old worktree audit is not present-tense deletion authority.
