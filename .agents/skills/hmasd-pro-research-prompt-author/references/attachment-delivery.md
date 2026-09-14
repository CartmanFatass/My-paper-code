# Explicit attachment delivery

Use only when the request explicitly selects `delivery_mode=archive_attachment`
with a nonempty `fallback_reason`. The shared author fields, scientific decision
scope and current Transport routing are defined in [the Author skill](../SKILL.md).
Attachment mode changes delivery format, not scientific authority or executor.

The top-level full commit_or_ref is the default scientific input version. Each
reference may declare a distinct full commit_sha; omission inherits the default.
The manifest prints each effective path/SHA mapping in the one named repository.
Preserve all science card/evidence mappings; newer method sources may be separately
pinned. TASK explicitly adopts only named applicable specification sections at those
versions. Other retrieved content cannot expand scope or the listed dependencies.

## Inputs and rendering

Supply the ordinary author request, exact source and parent task IDs, registered
direction scope, pinned repository evidence, question, deliverable and claim ceiling.
Include only relevant scientific constraints and discussion snapshots. Use
[github-connector-contract.md](github-connector-contract.md) for evidence access.

Run `scripts/render_packet.py REQUEST.json --out-dir <new packet folder>` from the
skill directory, or use its full repository path. The renderer creates:

- `PROMPT_BODY.md`: the sole scientific attachment, containing the question and
  `GITHUB_EVIDENCE_MANIFEST` with fixed repository/version/path references.
- `HANDOFF.json`: source, parent, configured executor, node, binding, exact request
  body path and companion prompt, provider requirement and dispatch fields.

Do not split the manifest into another upload or copy complete evidence files into
the body. Pro retrieves the listed evidence and reports the precise missing paths
or inaccessible discussion. The attachment authorizes read-only scientific analysis;
it does not authorize GitHub response-file writes, Issue comments, code or main changes.
The answer is complete natural-language scientific prose, not a routing envelope.

Commit and push the packet using existing Git rules. For accepted historical attachment work,
preserve its original route and bytes during same-request recovery. New DM-native dispatch uses
the exact child and parent in HANDOFF, not a configured independent app task. Agentify strict
promptPath pastes text and cannot substitute for an upload: absent a contract-conforming available
upload tool, report the capability gap before Send. Do not silently select a new input mode.

## Transport and intake

Transport executes the complete Pro lifecycle in its own task. Upload the validated
`PROMPT_BODY.md` unchanged and supply the exact `companion_prompt` from HANDOFF.
The companion is provider text; internal dispatch and routing fields stay in HANDOFF.
Follow the Transport skill for 6 Pro verification, the exact bound conversation,
one Send, paired-message capture, full response archive and tab cleanup.

DM-owned Transport observes pending requests while DM waits natively under ROOT_OPERATIONS.md.
Each request retains its source, parent, provider identity, archive and Send facts.
A single request's completion does not pause observation needed by another.

After archival, return completion to the declared parent, locally when executor and
parent coincide. Portfolio/DM reads the full original answer, checks the decision
against current specifications and performs scientific intake. A connector or
evidence gap is not a formed decision. Preserve any partial output and the exact
gap; changing delivery mode does not authorize a second Send for an unresolved request.
