# BrowserMCP Transport Failure — Nested Response Fence

Round: `20260723_causal_audit_quota_shortfall_semantics`
Stage commit: `0eb29c108be054fc060e6f0e97e42b3d80c00e40`
Evidence commit: `240b2065a83fad6844d15f18715c70c5dd9e3215`
Submission status: `BROWSERMCP_PRO_BLOCKED`

## Observed boundary

The immutable v2 submission receipt records one successful bounded dispatch to
the registered Pro conversation. Pro completed naturally. Two distinct stable
BrowserMCP snapshots were captured more than ten seconds apart after completion.

The final assistant turn did not preserve the required single fenced `text`
response. Its first code node began with the correct response marker, but an
inner triple-backtick schema fence terminated that outer node. Later substantive
paragraphs and additional code nodes appeared before `Response actions`.
`archive_browser_pro_raw.ps1` therefore failed closed with
`BrowserMCP code scalar must be a YAML literal or quoted scalar` while rejecting
the additional unquoted code node.

No `21_PRO_OPEN_RAW.md` was published. The archiver deleted both accepted
temporary snapshots in `finally`. The question and immutable receipt are
preserved; no resubmission, receipt mutation, alternate transport, code action
or formal compute occurred.

## Disposition

No scientific content from the malformed rendered response is accepted,
reconciled or applied. The response parser remains strict. Recovery requires a
distinct focused round in the same registered Pro conversation whose canonical
question expressly forbids any triple-backtick sequence or nested fenced block
between its response markers.
