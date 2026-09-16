# Attachment upload and exact input

For upload mode, start `waitForEvent("filechooser")` before opening the visible
upload control, set the absolute file path, and wait for the explicit file group and
upload completion state. Record file size/hash before upload. Acceptance of a
validated handoff authorizes uploading exactly its validated `prompt_path` and any
validated `reference_paths` to `chatgpt.com` for that request. Do not request
action-time confirmation before upload or immediately before Send. This authorization
does not extend to any other local file, destination, replacement packet, or second
send. An exact retry remains covered only when authoritative state proves the prior
operation was rejected before acceptance and produced no external effect.
If `reference_paths` are present, upload them before Send (in one chooser when
`isMultiple()` is true, or in separate chooser cycles otherwise) and verify every
expected file by its recorded size/hash and conversation association. A provider
filename suffix or other display normalization is informational, not a blocker. If
the upload is still pending, do not send. Do not invent companion text when
file-only Send is disabled; stop and request the exact companion text from the
calling session.

For a canonical packet, preserve the exact body bytes and every supplied reference
hash. Upload the manifest-selected physical files in the recorded order when the
page requires attachments. A provider filename suffix or normalization is an
observation to record, not a reason to rewrite the packet or fail the send.

For a canonical Prompt Author single-body packet, upload only `PROMPT_BODY.md`.
The in-body `GITHUB_EVIDENCE_MANIFEST` is not a second attachment and must not be
split back out for upload.
