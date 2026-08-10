# Temporary compatibility work

`temp/sessions/<role>/` is a stable compatibility path holding short-lived,
assignment-owned working files. It is not a live session, thread, successor,
cross-task routing protocol or identity layer. A fresh CLI Root task uses only
the exact path named by its assignment.

Cross-owner and cross-task results return to Root; Root performs any permitted
relay to another owner. A long payload may be a plain UTF-8 file in the
writer's exact assignment path, with the parent receiving only that relative
path. A temporary file is a bounded byte payload, not a direct sibling channel,
semantic acceptance record or identity mechanism. Workflow admission never
depends on byte counts, SHA-256, an external identity, or a repository route
table.

Actual temporary payloads are ignored by Git and never enter a commit or push.
Root controls relay and lifecycle; only the assignment owner writes its exact
temporary bytes, and cleanup follows Root's bounded lifecycle decision.
