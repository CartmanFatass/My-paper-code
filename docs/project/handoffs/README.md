# Public Semantic Handoffs

This tracked file defines the stable collaboration interface between Independent
Research Explorer and Code Project Manager. Live exchange files are ignored
temporary files under `temp/handoffs/`, so ordinary handoffs require no Git.

## Ownership

- `temp/handoffs/explorer_to_code_manager/`: Explorer alone creates, edits and
  deletes its outbound files. Code Manager reads them.
- `temp/handoffs/code_manager_to_explorer/`: Code Manager alone creates, edits
  and deletes its outbound files. For a treatment assignment, the assignment
  names one exact descendant under this root; Explorer reads only that file.
- Workflow Design Manager owns this interface contract but never authors,
  interprets or cleans live handoff content.

Scheduler creates the handoff's same-level user-owned Desktop Explorer owner
task. Each assignment declares `owner_mode=direction` for one named direction
or `owner_mode=portfolio` for an explicitly named direction set, with a
self-contained natural-language brief, exact canonical inputs, write paths and
result destination. Direction mode excludes sibling preload; portfolio mode
does not infer unnamed directions. The terminal owner task returns a
conclusion-first canonical capsule and is archived. Existing registered child
profiles and authority are unchanged.

Same-file concurrent writes are forbidden. The sender deletes the exchange copy
after intake; live files never enter Git. Canonical records stay with their
owners, with no handoff history tree.

## CPM treatment reverse-handoff scope

The CPM `owner_mode=treatment` assignment has exactly two physical write scopes:
ticket-local paths inside one registered ticket/worktree and one exact
strict-descendant main-checkout transport path under
`temp/handoffs/code_manager_to_explorer/`. Treatment Git and shell mutation
remain ticket-worktree-scoped. The one main-checkout handoff file is written
with `apply_patch` only and has no Git authority; it is conclusion-first,
disposable transport that points to the exact assignment-named treatment
artifact/evidence/technical-acceptance locators. It is not the canonical
technical artifact, acceptance record, result ledger, queue, Scheduler semantic
relay or Git object. Explorer reads only the exact named handoff/technical
locators and performs exactly one scientific intake, then existing sender and
receiver cleanup applies. Scheduler routes/checks locators mechanically and does
not interpret the result. `owner_mode=integration` keeps the existing
shared-mainline integration semantics and does not repeat treatment runtime or
treatment acceptance.

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
not a queue, registry, lease or state machine. Scheduler observes resource
vectors and conflict sets; independent entries may be concurrent when their
writers and vectors are disjoint. Manifest order is not runtime admission,
scientific priority or a cross-direction barrier. A result begins with its
natural-language conclusion and then appends the necessary exact evidence; a
mechanical envelope alone is insufficient.
For two or more already selected and frozen independent treatments with closed
direction-local predecessor/intake barriers, this interface follows the
parallel-first normal path when observed vectors and writers are disjoint. A
global serial fallback requires a named dependency, same writer/mutable
path/object or observed resource conflict; attribution, generic caution,
completion order and convenience are not sufficient. A design explicitly
marked formal local result-bearing runtime may exclude only conflicting local
experiment runtime. Owner-task lifecycle replaces polling-loop scheduling and a
resource wait never blocks non-runtime work or changes scientific priority.
