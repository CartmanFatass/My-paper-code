# Public Semantic Handoffs

This directory is the neutral, tracked collaboration surface between
Independent Research Explorer and Code Project Manager.

## Ownership

- `explorer_to_code_manager/`: Explorer alone creates, edits, commits and
  deletes its outbound files. Code Manager reads them.
- `code_manager_to_explorer/`: Code Manager alone creates, edits, commits and
  deletes its outbound files. Explorer reads them.
- Workflow Design Manager owns this interface contract but never authors,
  interprets or cleans live handoff content.

Same-file concurrent writes are forbidden. A sender removes an active handoff
after receiver intake; Git preserves history. No permanent duplicate history
tree is maintained.

## Semantic briefs

Markdown, JSON and receiver-readable attachments are allowed. A useful brief
normally makes the target, candidate and version, intended outcome, concrete
inputs, evidence and uncertainty, allowed and excluded effects, authority
boundary, completion evidence and return task understandable. These are
writing cues, not mandatory headings or machine-admission fields.

The receiver uses judgment and bounded safe read-only reconnaissance. It stops
only for a materially missing authority, scientific choice or concrete input
object. A missing schema, `document_kind`, validator receipt, hash, byte count
or fingerprint is never a blocker.

An optional manifest may list public brief paths in their intended order. It is
not a queue, registry, lease or state machine. Work remains one-candidate-at-a-
time and candidate-specific. A result begins with its natural-language
conclusion and then appends the necessary exact evidence; a mechanical envelope
alone is insufficient.
