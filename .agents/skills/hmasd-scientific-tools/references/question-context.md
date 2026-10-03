# Question context and evidence navigation

Use this method when entering, resuming or handing over a scientific question, or when a
material decision needs its earlier evidence. It implements the owner's 2026-10-03 request
to borrow source navigation from OpenResearch. The view is disposable and rebuildable;
RESEARCH, direction NOTES/claims and run outputs retain their existing roles.

## Orient from current sources

A short entry view should locate:

- The current question and working judgment, including its scope.
- The consequential supporting and contrary evidence, with original source locations.
- Accepted work, unfinished reading and still-open questions, keeping these states separate.
- The contract, relevant interpretation and original measurements that must be read next.

Use this in the existing assignment or working context; do not maintain a second summary file
or ask a DM to restate its notebook. Begin with the current RESEARCH entry and follow the
relevant links. Read the load-bearing original passages and outputs before a scientific choice.
An earlier summary can locate them, but a chain of summaries is not a substitute. Reuse still
applicable reading within a study; there is no per-cell context rebuild or full-history preload.
This is the Root/DM entry view. The independent Scientific Reviewer still reconstructs original
evidence before reading proponents' interpretations under constitution section 2.

The local adaptation at `/home/fires/projects/OpenResearch-HMASD` already derives direction
views from these sources. Its [workspace contract](/home/fires/projects/OpenResearch-HMASD/docs/hmasd-workspace.md)
describes the API and limits; its [README](/home/fires/projects/OpenResearch-HMASD/README.md)
describes the actual dev-slot URL. When available, use `/hmasd`, its copy-context action, or
read-only `GET /api/hmasd/overview`, `GET /api/hmasd/directions/{id}` and
`GET /api/hmasd/source?path=...&line=...&limit=...&anchor=...` to locate originals.
Use the slot's actual API address, not an assumed port. If it is unavailable, read the same
repository sources directly; orientation does not depend on starting a service.

Carry retrieval time, revision/file identity, source location and any truncation or warnings
with copied excerpts. The current adapter exposes recent NOTES sections and a bounded set of
compact run records, not a complete synthesis. Missing or out-of-window evidence stays unknown;
absence from this view is not absence from the project. A working-tree excerpt may differ from
published main or an accepted source SHA. Read the appropriate original version for the choice.
Recorded direction, worker and reader statuses do not establish scientific completion or live
process state. A wake event likewise calls for reading the existing operation's actual status;
it does not authorize a replacement launch or another Send.

## Explain the relationship in the existing notebook

At a material explanation or investment change, make the relevant relationship explicit in
ordinary NOTES prose with a direct Markdown link. Useful distinctions are:

| Relationship | What the source-backed explanation should say |
| --- | --- |
| Inherit a capability | What demonstrated ability or useful ordinary comparator is retained, and under which conditions? |
| Explain a counterexample | Which adverse observation changes the earlier explanation or limits its scope? |
| Repair a technical condition | Does the repair restore executability or data validity, and which scientific effect remains untested? |
| Test a new prediction | Which observation would distinguish explanations that remain compatible with the earlier evidence? |

These are reasoning aids, not four fields owed by every run or a fixed experiment tree.
A study may have several relevant predecessors. Code ancestry and a Markdown link alone do
not establish any scientific relationship. The adapter currently extracts `references` only;
typed relationships require the author's source-grounded explanation, preserving uncertainty
and disagreement. A new success can narrow an earlier negative result without rewriting it.

## Make a reported result easy to inspect

Link a conclusion to its published interpretation and limits, prospective comparison/arms,
accepted source identity, complete paired measurements and relevant adverse or failed cases.
Use ordinary Markdown links to exact run files and notebook anchors so both agents and the
workspace can follow them. A code link establishes code provenance; it does not establish a
measured effect. A worker or reader completion label is likewise not the result's interpretation.

Generate repeated numeric tables and source links from the existing saved outputs or reader
when useful, with the source revision/hash and declared comparison scope. Preserve paired
identities, the full outcome population, missingness and adverse cases; show any filter,
rounding or truncation. Do not manually maintain a second set of numbers or silently mix
revisions. Check the generated view against its sources at publication; it remains navigation,
not replacement evidence. View refresh reads existing records and does not run a new model,
evaluation or fit. No retrospective rewrite of frozen outputs is needed.
