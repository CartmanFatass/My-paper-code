---
name: hmasd-cm-task
description: Bootstrap or resume an independent direction-scoped HMASD CM task for one frozen engineering slice.
---

# HMASD CM Task

Use only in `CM/<direction-id>/g<generation>` (Sol, high). Load
`hmasd-slice-interface`, `hmasd-cm-engineering-cycle`, `hmasd-result-run`, and
`hmasd-git-integration`.

The packet freezes direction, generation, acceptance refs, base SHA, owned
paths, worktree, and Effects. CM writes engineering state and completes the
full same-scope cycle. It directly owns any Experiment Operator leaf; Root
alone does final main integration.

Return once through the slice interface. Do not ask Clerk to coordinate ordinary
work, create a cross-session handoff from prose, or widen frozen science, caps,
paths, or Effects.
