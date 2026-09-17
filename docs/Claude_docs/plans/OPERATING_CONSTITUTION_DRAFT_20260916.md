# HMASD operating constitution — DRAFT for owner revision

Status: draft by the Claude hub, 2026-09-16, at the owner's request (17:13 PDT). Nothing here
is in force until the owner adopts it. Items marked `[ASK]` need the owner's choice. Once
adopted, this page is the one governance text; it replaces nothing by rewriting, it makes the
old apparatus unused.

## 1. What this project is

A personal exploratory research project on untied K in HMASD: unfixed skill duration k
(FSD) and unfixed agent count N, studied as two parallel questions. The deliverable is one
paper-grade claim per question, on the UAV host, against a matched-information baseline.
Fast iteration on ideas is the primary value; confirmation is a final, bounded step.

## 2. Who does what

- **Owner**: chooses which directions exist, triggers Portfolio review, resumes or pauses
  research, adopts or edits this page. Nothing waits for the owner unless it is one of these.
- **Hub session** (Codex root or the Claude hub): one session owns a direction end to end,
  from idea through code, run, reading and record. It is Root and DM at once. Two
  directions at most per runtime.
- **Codex DM children**: allowed, because Codex needs them for cost and parallelism. A DM
  child owns one direction with the same end-to-end scope; it reports facts to the root.
- **Transport** (Pro send/wait/collect) and **Monitor** (run wait/collect): exist only to
  absorb long waits. They return facts and make no judgment.
- **Reviewer**: only for a change to the core learner or a shared runner.
- No other role. No new role, agent, or "equivalent under another name" without the owner
  writing it into this page. `[ASK]` Keep Grok clerk mode and the Sonnet clerk for mechanical
  edits, or retire both? (Under the three-record rule there is little mechanical work left.)

## 3. Budget is counted in fits

One fit is one training run of one seed on the declared node. The node does about 80 idle
fits per day when serialised; contended fits take roughly 2.5 times longer.

| Stage | Allowance | Records |
| --- | --- | --- |
| Explore an idea | 3 to 6 single-seed fits, any host | notebook entry + runs folder |
| Confirm a claim | 3 to 5 seeds per arm, one baseline arm, once | notebook entry + runs folder + claim note |

An idea that does not show anything after its exploration allowance is written down as
killed and not rerun. A failed run is a bug to fix, not a spent or refunded allowance.
`[ASK]` Standing weekly cap per direction, or none beyond the per-idea numbers?

## 4. The three records per direction, and nothing else

1. `docs/research/candidates/<direction>/NOTES.md`: append-only lab notebook. One dated
   entry per idea or run batch: what was tried, sha, what was seen, keep/kill, next step.
2. `runs/<direction>/<tag>/`: written by the runner, never by hand. `config.json`, launch
   sha, `summary.json`, curves. Bad runs stay.
3. `docs/research/candidates/<direction>/CLAIM_<slug>.md`: half a page, written before the
   confirmation fits start: hypothesis, baseline, seeds, evaluation protocol, decision rule,
   and after the fits the result read by that rule.

One repository-level `docs/research/RESEARCH.md` holds a table of directions: name, question,
state (exploring / confirming / archived), one line of current standing. That table replaces
PORTFOLIO, APPROVED_SET, EXPERIMENT_TRACKING, dossiers and lifecycle decisions as the current
view. Retired as of adoption: cards for pilots, intake documents, audit ledger, owner inbox
items and briefs, per-session handoffs, packet/registry/binding files, decision records for
object-tier choices. Historical files stay where they are, unmaintained.

## 5. Pro

Pro is used for two things: generating and converging a batch of hypotheses per direction
before experiments start, and one critic pass on a claim note before its confirmation fits.
It is not a decision node; its answers are advice the hub reads and the notebook records.

Mechanics: the hub commits the question as one markdown file and pushes; the hub (or its
Transport) opens the direction's Pro conversation in the browser, sends one line with the
GitHub link, waits, and Pro writes its answer into the repository through the ChatGPT GitHub
connector; the hub reads the committed file. No packet renderer, registry, conversation
binding records, finality labels or receipts. If the connector fails, the page text is saved
as the answer. `[ASK]` One Pro conversation per direction, reused indefinitely?

## 6. Code

- **Core** (`ha_ctse_process/`, the shared learner, runners, envs): keep compatible, one
  smoke test, Reviewer on change.
- **Experimental** (`experiments/candidates/<direction>/`): disposable. No compatibility,
  no schema validators, no provenance guards, no registries, no resumable execution, no
  retry or lease machinery, no telemetry beyond wall time and peak RSS. Delete when the
  direction is archived.
- Every result-bearing run: commit first, memory preflight, launch detached on the declared
  node at the committed sha. This is the entire launch procedure.

## 7. Rules about rules

1. An incident becomes a tool fix or an accepted risk. It never becomes a new rule,
   OWNER_DIRECT block, guard or label.
2. No new process document without deleting one. No new record type at all.
3. Always-loaded text (root AGENTS plus CLAUDE) stays under 4 KB. Anything longer moves
   into a task skill or is cut.
4. Only the owner edits this page. Agents may propose a change in one sentence in their
   final report; they do not draft governance.
5. Codex and Claude are asked for code, runs, readings and reviews. They are not asked to
   design process, and a request phrased as "make the workflow more rigorous" is answered
   with a proposal, not an implementation.
6. Rigor scales with the claim. Exploration is allowed to be sloppy, fast and single-seed.
   Confirmation is not, and is rare.

## 8. Scientific minimums (the only ones)

Seeds before belief (three or more independent training seeds behind any claim); one
matched-information baseline per claim; sha, config and summary per run; keep the bad runs;
read a confirmation by the rule written in its claim note. Nothing else is mandatory.

## 9. How to measure whether this is working

Once a month: valid results (claim notes with a read result) per owner-hour, and commits
touching `docs/` per run summary. The 2026-09-02 to 09-16 baseline is 33 documentation
commits per run summary and zero effects on record. If the ratio is not falling, the
process is still too heavy.

## 10. Transition (no rewrite)

1. Owner adopts this page; the old AGENTS, skills and role files stay as they are and go
   unused except where this page names them.
2. Research resumes with FSD B01 as the only active object, under the three records.
3. Directions outside the two or three the owner names go to `archived` in RESEARCH.md;
   their worktrees are removed after the branch is confirmed on the remote (audit of
   2026-09-16: every direction branch is on a remote; dirty files exist only in
   `codex-portfolio`, `dm-rcle-a02-20260906` and the ten `temp/cm-model-comparison`
   checkouts; two `~/.codex/worktrees` detached checkouts hold one unpushed commit each).
   `[ASK]` Which directions stay active?
4. Old documents are deleted later, in one commit, once nothing current references them.
