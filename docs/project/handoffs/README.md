# Public Semantic Handoffs

This tracked file defines the stable collaboration interface between Independent
Research Explorer and Code Project Manager. Live exchange files are ignored
temporary files under `temp/handoffs/`, so ordinary handoffs require no Git.

## Ownership

- `temp/handoffs/explorer_to_code_manager/`: Explorer alone creates, edits and
  deletes its outbound files. Code Manager reads them.
- `temp/handoffs/code_manager_to_explorer/`: Code Manager alone creates, edits
  and deletes its outbound files. Explorer reads them.
- Workflow Design Manager owns this interface contract but never authors,
  interprets or cleans live handoff content.

Same-file concurrent writes are forbidden. The sender deletes the exchange copy
after intake; live files never enter Git. Canonical records stay with their
owners, with no handoff history tree.

## Scientific-only intake boundary

Scientific intake is defined once in
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`. This handoff contract
owns only the exchange-file boundary and does not duplicate scientific decisions
or CPM's technical packet validation.

## Semantic briefs

Markdown, JSON and receiver-readable attachments are allowed. A useful brief
normally makes the target, candidate and version, intended outcome, concrete
inputs, evidence and uncertainty, allowed and excluded effects, authority
boundary, completion evidence and return task understandable. These are writing
cues, not mandatory headings or machine-admission fields. Explorer-origin
treatment, requested-work and External-Pro acceptance rules are defined only by
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`.

The receiver uses judgment and bounded safe read-only reconnaissance. It stops
only for a materially missing authority, scientific choice or concrete input
object. A missing schema, `document_kind`, validator receipt, hash, byte count
or fingerprint is never a blocker.

The strong action-bearing semantic minimum for every Explorer brief, CPM result
and Codex-native fallback is defined once in
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`. The prose must carry
current evidence and exact locators, frozen and unfrozen facts/choices, why each
owner is or is not needed now, the permitted owner/action, completion evidence,
and the return/intake boundary; status-only labels are insufficient. This file
defines only the exchange-file ownership and temporary-copy boundary.

Direction-specific briefs and reverse results follow the direction-local
context binding in
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`. Explorer selects one
primary direction and supplies only its smallest set of canonical
decision/source context, adding the smallest set of parent, child or
cross-direction edges only when material. An explicitly multi-direction brief
may name several directions; sibling directions are not preloaded or
generalized unless explicitly named. The result begins with a conclusion and
mirrors the same primary direction or explicitly named direction set,
candidate/proposition, stage,
source/evidence revision boundary and material relationships before technical
evidence. A Codex-native message fallback carries the same binding. If the
binding is missing or contradictory, preserve the original brief/artifact and
ask exactly one concrete semantic clarification while continuing unrelated
work; do not guess, merge directions, rewrite the artifact or create a
`BLOCKED` state.

An optional manifest may list temporary brief paths in their intended order. It is
not a queue, registry, lease or state machine. Capacity-admitted work may be
concurrent, but every entry remains direction/treatment-specific and uses
distinct sender files; manifest order is not runtime admission, scientific
priority or a cross-direction barrier. A result begins with its natural-language
conclusion and then appends the necessary exact evidence; a mechanical envelope
alone is insufficient.
For two or more already selected and frozen independent treatments with closed
direction-local predecessor/intake barriers, this interface follows the
parallel-first normal path within available capacity. A global serial fallback
requires named dependency or actual resource evidence; attribution, generic
caution, completion order and convenience are not sufficient. The handoff
interface does not fill capacity, reprioritize or reactivate directions.
Explorer progress is event-driven or user-resumed; CPM treatment dispatch is
constrained only by an exact scientific/dependency predecessor, capacity/admission,
a formal or actually observed resource conflict, or a same mutable-path/object
conflict. Read-only Explorer science lanes remain independent of CPM
pool/admission by default; only an exact question depending on an unreturned CPM
result creates a direction-local science barrier.
