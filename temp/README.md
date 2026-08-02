# Temporary session work

`temp/sessions/<role>/` holds owner-local, short-lived working files. It is not a
cross-task routing protocol or identity layer.

Cross-task messages use Codex-native `send_message_to_thread` with the current
target task ID and no model or thinking override. When a long payload genuinely
needs a file, the sender may place a plain UTF-8 file in its own session folder
and send only that relative path. Workflow admission never depends on byte
counts, SHA-256, or a repository route table.

Actual temporary payloads are ignored by Git and are never deleted
automatically. Only the owning session removes its temporary files.
