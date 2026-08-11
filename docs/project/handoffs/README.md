# Public Semantic Handoffs

This tracked file defines the stable Root-routed collaboration interface for
one direction-scoped Independent Research Explorer (EM) and one Code Project
Manager (CM) slice. Live exchange files are ignored temporary files under
`temp/handoffs/`, so ordinary handoffs require no Git.

## Ownership

- `temp/handoffs/explorer_to_code_manager/`: direction EM semantically authors
  and approves the handoff; its assigned Writer physically writes the exact
  outbound temporary file and may remove it only after Root confirms CM
  intake. Root receives and routes it to the exact `CM direction:<id>` slice.
- `temp/handoffs/code_manager_to_explorer/`: CM returns its technical result
  to Root; Root writes and routes the exact reverse temporary copy to the same
  EM direction and may remove that copy only after Root confirms EM intake.
- A shared component request is a separate Root-assigned `CM shared:<component>`
  slice and returns through Root; there is no `shared:all` route.
- Workflow Design Manager owns this interface contract but never authors,
  interprets or cleans live handoff content. Root owns user communication,
  macro/portfolio advisory science, cross-owner relay, lifecycle, mechanical
  integration and accepted physical writes. Root owns cross-direction compare,
  ranking, pause/continue, dependency and complete-map/relation acceptance;
  Root does not execute direction research or own CM technical acceptance.

Same-file concurrent writes are forbidden. After Root confirms CM intake, EM may
assign its Writer to remove the exact EM outbound copy. After Root confirms EM
intake of a Root-written reverse copy, Root may remove exactly that copy. Live
files never enter Git. Owner records stay with their owners, with no handoff
history tree. EM and CM do not contact each other directly.

## Scientific-only intake boundary

Scientific intake is defined once in
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`. This handoff contract
owns only the exchange-file boundary and does not duplicate scientific decisions
or CM's technical packet validation.
The complete Direction Action Map and cross-direction relations never travel
through a handoff message; reverse intake uses the exact direction-local
temporary patch and Root-owned complete-map candidate described by that source.

## Semantic briefs

Markdown, JSON and receiver-readable attachments are allowed. A useful brief
normally makes the target, candidate and version, intended outcome, concrete
inputs, evidence and uncertainty, allowed and excluded effects, authority
boundary, completion evidence and return task understandable. These are writing
cues, not mandatory headings or machine-admission fields. EM-origin direction
treatment, requested-work and External-Pro acceptance rules are defined only by
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`.

The receiver uses judgment and bounded safe read-only reconnaissance. It stops
only for a materially missing authority, scientific choice or concrete input
object. A missing schema, `document_kind`, validator receipt, hash, byte count
or fingerprint is never a blocker.

The strong action-bearing semantic minimum for every EM brief, CM result
and Codex-native fallback is defined once in
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`. The prose must carry
current evidence and exact locators, frozen and unfrozen facts/choices, why each
owner is or is not needed now, the permitted owner/action, completion evidence,
and the return/intake boundary; status-only labels are insufficient. This file
defines only the exchange-file ownership and temporary-copy boundary.

Direction-specific briefs and Root-routed reverse results follow the
direction-local context binding in
`docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`. EM selects exactly one
`direction:<id>` and supplies only its smallest set of canonical decision/source
context, adding the smallest set of parent or child edges only when material.
The portfolio and sibling directions are never preloaded into EM or CM. The
result begins with a conclusion and mirrors the same direction,
candidate/proposition, stage,
source/evidence revision boundary and material relationships before technical
evidence. A Codex-native message fallback carries the same binding. If the
binding is missing or contradictory, preserve the original brief/artifact and
ask exactly one concrete semantic clarification while continuing unrelated
work; do not guess, merge directions, rewrite the artifact or create a
`BLOCKED` state.

An optional manifest may list temporary brief paths in their intended order. It is
not a queue, registry, lease or state machine. Root splits the entries into
separate CM assignments, each covering exactly one `direction:<id>` or one named
`shared:<component>` and never a direction set, multi-direction result or
`shared:all`. Every entry remains direction/treatment-specific and uses distinct
sender files; manifest order is organization, not scientific priority or a
cross-direction barrier. A result begins with its natural-language conclusion
and then appends the necessary exact evidence; a mechanical envelope alone is
insufficient. Root union Tests/Static checks remain mechanical evidence only and
never become CM technical acceptance or External Pro/user scientific
acceptance.

Independent exact assignments may run concurrently only when each has a closed
scientific/dependency predecessor and no same mutable path or concrete
resource conflict. A fresh observed process/CPU/memory or other concrete
resource check may inform Root's mechanical scheduling decision; it does not
create a runtime pool, reservation, ledger or scheduler. CM retains technical
and runtime judgment for its exact slice. If the observed dependencies or
resource conflict require serialization, Root serializes the affected exact
assignments without reprioritizing or reactivating directions. Read-only EM
direction-science lanes remain independent of CM work unless an exact question
depends on an unreturned CM result, which creates a direction-local science
barrier.
