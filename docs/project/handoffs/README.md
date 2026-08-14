# Explorer/CM handoffs

This directory describes the ignored temporary relay surface used by the
Explorer-origin project-validation chain. The goal is a readable, bounded
delivery from one direction EM to one CM and the technical evidence back to the
same EM through their bounded same-direction direct channel.

- `temp/handoffs/explorer_to_code_manager/` holds an EM-approved treatment
  brief. An assigned Writer may write or remove only that approved temporary
  file; EM sends its locator to the named same-direction CM.
- `temp/handoffs/code_manager_to_explorer/` holds CM's technical result. Root
  does not relay it: CM sends its locator directly to the paired EM after
  technical acceptance.

Both owners must match `direction_id` and counterpart canonical task names.
Cross-direction content, user requests, portfolio decisions, resource
allocation, or authority expansion returns to Root.

Each item explains the goal and why it matters, the direction/candidate/question
and comparator, the responsible owner and permitted action, completion evidence,
and return destination. Direction, candidate, revision, isolation, active
authorization, run binding, and receipt may be included as anchors only. They
are not a schema, admission state, or machine transition.

For ordinary B, every concrete run fixes its question, candidate, comparator,
exact code/configuration, seeds, small budget, and interpretation boundary.
Later named B adjustments carry their reason. Missing engineering objects go to
CM; missing scientific choices go to EM. Engineering work is not `BLOCKED`.

These files do not carry a complete Direction Action Map. The only map path is
the conditional **Direction Action Map semantic-delta installation** described
in `docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md`; it carries a small
direction delta through Writer and Root, then EM direction-semantics acceptance
and Root full-map acceptance. The technical path is separately named
**technical-result return and scientific intake**.

Publication and Pro rules are defined by the workflow: publication is Root's
ordinary non-force upstream push of an owner-accepted exact path set, not a
handoff, local commit, intake, or acceptance. Ordinary B does not automatically
contact Pro.
