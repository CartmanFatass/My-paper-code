# Context Retention Policy

Controlled forgetting excludes stale objects from the active working set. This
version performs no destructive deletion of scientific, technical, portfolio,
audit, or raw-report data.

## Active working set

Includes only the current actor context, open epoch, latest compatible semantic
commit, current checkpoint, open actor-local obligations, unintaken reports,
active packet refs, current epoch navigation/procedure refs, current canonical
refs, a prepared-but-unapplied rollover, and nonterminal promotion proposals.

## Audit-only marking

Older checkpoints, older semantic commits, closed epochs, resolved obligations,
intaken reports, applied packets, applied/rejected promotions, and applied
rollovers may be marked audit-only. They remain queryable.

## Released actors and closed epochs

Released EM/CM actor contexts do not auto-rehydrate. Release does not change
direction allocation. Closed epochs do not auto-rehydrate.

Raw evidence remains `RAW_EVIDENCE_RETAINED`.
